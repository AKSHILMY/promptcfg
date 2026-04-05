use std::collections::{HashMap, HashSet};
use minijinja::{Environment, context};
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyString};

#[pyclass]
#[derive(Clone, Debug)]
pub struct RustPromptPart {
    id: String,
    text: String,
    variables: Vec<RustVariableDefinition>,
    tags: Vec<String>,
    default: bool,
}

#[derive(Clone, Debug)]
pub struct RustVariableDefinition {
    name: String,
    required: bool,
    default_val: Option<String>,
}

#[pyclass(subclass)]
pub struct RustPromptBuilder {
    prompts: Vec<RustPromptPart>,
}

#[pymethods]
impl RustPromptBuilder {
    #[new]
    fn new(py_prompts: &PyList) -> PyResult<Self> {
        let mut prompts = Vec::new();
        for item in py_prompts {
            let id: String = item.getattr("id")?.extract()?;
            let text: String = item.getattr("text")?.extract()?;
            let default: bool = item.getattr("default")?.extract()?;
            
            let tags_py = item.getattr("tags")?;
            let mut tags = Vec::new();
            if let Ok(py_tags) = tags_py.downcast::<PyList>() {
                for tag in py_tags {
                    tags.push(tag.extract::<String>()?);
                }
            }

            let vars_py = item.getattr("variables")?;
            let mut variables = Vec::new();
            if let Ok(py_vars) = vars_py.downcast::<PyList>() {
                for v in py_vars {
                    let name: String = v.getattr("name")?.extract()?;
                    let required: bool = v.getattr("required")?.extract()?;
                    let default_val: Option<String> = if v.getattr("default")?.is_none() {
                        None
                    } else {
                        // Coerce to string even if Python default is int/bool
                        let obj = v.getattr("default")?;
                        Some(obj.str()?.extract()?)
                    };
                    variables.push(RustVariableDefinition { name, required, default_val });
                }
            }

            prompts.push(RustPromptPart {
                id,
                text,
                variables,
                tags,
                default,
            });
        }

        Ok(RustPromptBuilder { prompts })
    }

    #[pyo3(signature = (tags, variables, include_ids=None, exclude_ids=None, exclude_tags=None))]
    fn build(
        &self,
        py: Python,
        tags: Vec<String>,
        variables: &PyDict,
        include_ids: Option<Vec<String>>,
        exclude_ids: Option<Vec<String>>,
        exclude_tags: Option<Vec<String>>,
    ) -> PyResult<String> {
        // Convert to Sets for fast lookup
        let active_tags: HashSet<String> = tags.into_iter().collect();
        let include_ids_set: HashSet<String> = include_ids.unwrap_or_default().into_iter().collect();
        let exclude_ids_set: HashSet<String> = exclude_ids.unwrap_or_default().into_iter().collect();
        let exclude_tags_set: HashSet<String> = exclude_tags.unwrap_or_default().into_iter().collect();

        // Convert PyDict to Rust HashMap string->string
        let mut py_vars: HashMap<String, String> = HashMap::new();
        for (k, v) in variables {
            py_vars.insert(k.extract::<String>()?, v.str()?.extract::<String>()?);
        }

        // We release the GIL here so other Python threads can execute while we build the prompt
        py.allow_threads(|| {
            let mut env = Environment::new();
            let mut parts = Vec::new();

            for part in &self.prompts {
                if should_include(
                    part,
                    &active_tags,
                    &include_ids_set,
                    &exclude_ids_set,
                    &exclude_tags_set,
                ) {
                    // Check and apply variable defaults/requirements
                    let mut local_vars = py_vars.clone();
                    for var_def in &part.variables {
                        if !local_vars.contains_key(&var_def.name) {
                            if let Some(ref def_val) = var_def.default_val {
                                // IMPORTANT: Minijinja context needs the default value!
                                local_vars.insert(var_def.name.clone(), def_val.clone());
                            } else if var_def.required {
                                return Err(pyo3::exceptions::PyValueError::new_err(format!(
                                    "Missing required variable '{}' for prompt '{}'",
                                    var_def.name, part.id
                                )));
                            }
                        }
                    }

                    // Render with Minijinja
                    env.add_template(&part.id, &part.text).map_err(|e| {
                        pyo3::exceptions::PyRuntimeError::new_err(format!("Template error: {}", e))
                    })?;
                    let tmpl = env.get_template(&part.id).unwrap();
                    let rendered = tmpl.render(&local_vars).map_err(|e| {
                        pyo3::exceptions::PyRuntimeError::new_err(format!("Render error: {}", e))
                    })?;
                    parts.push(rendered);
                }
            }

            Ok(parts.join("\n\n"))
        })
    }
}

fn should_include(
    part: &RustPromptPart,
    active_tags: &HashSet<String>,
    include_ids: &HashSet<String>,
    exclude_ids: &HashSet<String>,
    exclude_tags: &HashSet<String>,
) -> bool {
    if exclude_ids.contains(&part.id) {
        return false;
    }
    if include_ids.contains(&part.id) {
        return true;
    }
    if part.tags.iter().any(|tag| exclude_tags.contains(tag)) {
        return false;
    }
    if part.tags.iter().any(|tag| active_tags.contains(tag)) {
        return true;
    }
    part.default
}

#[pymodule]
fn promptcfg_core(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<RustPromptBuilder>()?;
    Ok(())
}
