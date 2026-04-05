import streamlit as st
import yaml
import os
import sys
import copy
from pathlib import Path

from promptcfg.config import PromptConfig, PromptPart, VariableDefinition
from promptcfg.builder import PromptBuilder


class MultilineDumper(yaml.Dumper):
    pass

def _str_representer(dumper, data):
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

MultilineDumper.add_representer(str, _str_representer)

TAG_COLORS = [
    "#667eea", "#764ba2", "#00d4aa", "#ffb347", "#ff6b6b",
    "#4ecdc4", "#45b7d1", "#96ceb4", "#e056a0", "#a29bfe",
]


def load_css():
    css_path = Path(__file__).parent / "style.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


def save_current_config():
    if st.session_state.get("config"):
        path = os.path.join(os.getcwd(), "promptcfg.yaml")
        try:
            save_cfg(st.session_state.config, path)
            st.session_state.config_path = path
        except Exception:
            pass

def init_state():
    defaults = {
        "config": None, "config_path": None, "editing_idx": None,
        "show_add": False, "built_prompt": None, "yv": 0,
        "builder_dnd_state": None,
    }

    if "config" not in st.session_state:
        default_path = os.path.join(os.getcwd(), "promptcfg.yaml")
        if os.path.exists(default_path):
            try:
                cfg = PromptConfig.load(default_path)
                defaults["config"] = cfg
                defaults["config_path"] = default_path
            except Exception:
                pass
        else:
            defaults["config"] = PromptConfig(version="1.0", prompts=[])
            defaults["config_path"] = default_path

    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    if not os.path.exists(os.path.join(os.getcwd(), "promptcfg.yaml")) and st.session_state.get("config"):
        save_current_config()


def cfg_to_dict(cfg):
    prompts = []
    for p in cfg.prompts:
        d = {"id": p.id, "text": p.text}
        if p.default:
            d["default"] = True
        if p.tags:
            d["tags"] = p.tags
        if p.variables:
            vl = []
            for v in p.variables:
                vd = {"name": v.name}
                if v.description:
                    vd["description"] = v.description
                vd["required"] = v.required
                if v.default is not None:
                    vd["default"] = v.default
                vl.append(vd)
            d["variables"] = vl
        prompts.append(d)
    return {"version": cfg.version, "prompts": prompts}


def cfg_to_yaml(cfg):
    return yaml.dump(cfg_to_dict(cfg), Dumper=MultilineDumper,
                     default_flow_style=False, sort_keys=False, allow_unicode=True)


def get_tags(cfg):
    t = set()
    for p in cfg.prompts:
        t.update(p.tags)
    return sorted(t)


def get_ids(cfg):
    return [p.id for p in cfg.prompts]


def tag_color(tag):
    return TAG_COLORS[hash(tag) % len(TAG_COLORS)]


def tag_pills(tags):
    if not tags:
        return ""
    return "".join(
        f'<span style="background:{tag_color(t)};color:#fff;padding:3px 12px;'
        f'border-radius:20px;font-size:0.73rem;margin-right:5px;font-weight:500;'
        f'letter-spacing:0.3px;">{t}</span>'
        for t in tags
    )


def load_from_yaml_str(text):
    data = yaml.safe_load(text)
    if not data or "prompts" not in data:
        raise ValueError("Invalid config: missing 'prompts' key.")
    prompts, seen = [], set()
    for p in data.get("prompts", []):
        part = PromptPart(**p)
        if part.id in seen:
            raise ValueError(f"Duplicate prompt ID: '{part.id}'")
        seen.add(part.id)
        prompts.append(part)
    return PromptConfig(version=data.get("version", "1.0"), prompts=prompts)


def save_cfg(cfg, path):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        yaml.dump(cfg_to_dict(cfg), f, Dumper=MultilineDumper,
                  default_flow_style=False, sort_keys=False)


def parse_vars_yaml(text):
    if not text or not text.strip():
        return []
    parsed = yaml.safe_load(text)
    return parsed if parsed else []


def vars_to_yaml_str(variables):
    lines = []
    for v in variables:
        lines.append(f"- name: {v.name}")
        if v.description:
            lines.append(f'  description: "{v.description}"')
        lines.append(f"  required: {'true' if v.required else 'false'}")
        if v.default is not None:
            lines.append(f'  default: "{v.default}"')
    return "\n".join(lines)


# ━━━━━━━━━━━━━━━━━━━━━━ SIDEBAR ━━━━━━━━━━━━━━━━━━━━━━

def render_sidebar():
    with st.sidebar:
        st.markdown(
            '<div style="text-align:center;margin-bottom:0.5rem;">'
            '<span style="font-size:2.2rem;">⚡</span></div>',
            unsafe_allow_html=True,
        )
        st.markdown("## Configuration")
        
        cfg = st.session_state.config
        if not cfg:
            return

        c1, c2, c3 = st.columns(3)
        c1.metric("Prompts", len(cfg.prompts))
        c2.metric("Tags", len(get_tags(cfg)))
        c3.metric("Ver", cfg.version)

        if st.session_state.config_path:
            st.caption(f"📄 `{os.path.basename(st.session_state.config_path)}`")


# ━━━━━━━━━━━━━━━━━━━━━━ PROMPT MANAGER ━━━━━━━━━━━━━━━━━━━━━━

def render_prompt_card(prompt, idx):
    db = (
        '<span style="background:linear-gradient(135deg,#00d4aa,#00b894);color:#0e1117;'
        'padding:2px 10px;border-radius:12px;font-size:0.7rem;font-weight:700;'
        'margin-left:8px;">DEFAULT</span>'
        if prompt.default else ""
    )
    vc = len(prompt.variables)
    vi = (f'<span style="color:#999;font-size:0.8rem;">📎 {vc} var{"s" if vc != 1 else ""}</span>' if vc else "")
    prev = prompt.text.replace("\n", " ").strip()
    if len(prev) > 120:
        prev = prev[:120] + "…"

    st.markdown(
        f'<div class="prompt-card">'
        f'<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">'
        f'<div><span class="prompt-id">{prompt.id}</span>{db}</div>{vi}</div>'
        f'<div style="margin-bottom:8px;">{tag_pills(prompt.tags)}</div>'
        f'<div class="prompt-preview">{prev}</div></div>',
        unsafe_allow_html=True,
    )

    with st.expander("Details & Actions", expanded=(st.session_state.editing_idx == idx)):
        st.code(prompt.text, language="markdown")
        if prompt.variables:
            st.markdown("**Variables**")
            for v in prompt.variables:
                r = "🔴 Required" if v.required else "🟢 Optional"
                d = f"  ·  default: `{v.default}`" if v.default is not None else ""
                desc = f"  ·  {v.description}" if v.description else ""
                st.markdown(f"- `{v.name}` {r}{d}{desc}")

        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            if st.button("✏️ Edit", key=f"e_{idx}", use_container_width=True):
                st.session_state.editing_idx = idx
                st.rerun()
        with c2:
            if st.button("📋 Clone", key=f"c_{idx}", use_container_width=True):
                nid = f"{prompt.id}_copy"
                n = 1
                while any(p.id == nid for p in st.session_state.config.prompts):
                    n += 1
                    nid = f"{prompt.id}_copy{n}"
                clone = PromptPart(
                    id=nid, text=prompt.text, tags=list(prompt.tags),
                    default=prompt.default,
                    variables=[{"name": v.name, "description": v.description,
                                "required": v.required, "default": v.default}
                               for v in prompt.variables],
                )
                st.session_state.config.prompts.insert(idx + 1, clone)
                save_current_config()
                st.rerun()
        with c3:
            if st.button("⬆", key=f"u_{idx}", use_container_width=True, disabled=idx == 0):
                ps = st.session_state.config.prompts
                ps[idx], ps[idx - 1] = ps[idx - 1], ps[idx]
                save_current_config()
                st.rerun()
        with c4:
            if st.button("⬇", key=f"d_{idx}", use_container_width=True,
                         disabled=idx == len(st.session_state.config.prompts) - 1):
                ps = st.session_state.config.prompts
                ps[idx], ps[idx + 1] = ps[idx + 1], ps[idx]
                save_current_config()
                st.rerun()
        with c5:
            if st.button("🗑️", key=f"x_{idx}", use_container_width=True):
                st.session_state.config.prompts.pop(idx)
                save_current_config()
                if st.session_state.editing_idx == idx:
                    st.session_state.editing_idx = None
                st.rerun()

    if st.session_state.editing_idx == idx:
        render_edit_form(prompt, idx)


def render_edit_form(prompt, idx):
    st.markdown(f"#### ✏️ Editing `{prompt.id}`")
    with st.form(f"ef_{idx}"):
        nid = st.text_input("ID", value=prompt.id)
        ntxt = st.text_area("Text", value=prompt.text, height=180)
        c1, c2 = st.columns(2)
        with c1:
            ntags = st.text_input("Tags (comma-sep)", value=", ".join(prompt.tags))
        with c2:
            ndef = st.checkbox("Default", value=prompt.default)
        nvars = st.text_area("Variables (YAML)", value=vars_to_yaml_str(prompt.variables), height=120)

        c1, c2 = st.columns(2)
        ok = c1.form_submit_button("💾 Save", type="primary", use_container_width=True)
        cancel = c2.form_submit_button("Cancel", use_container_width=True)

        if ok:
            try:
                tags = [t.strip() for t in ntags.split(",") if t.strip()]
                variables = parse_vars_yaml(nvars)
                dup = [p.id for i, p in enumerate(st.session_state.config.prompts) if i != idx]
                if nid in dup:
                    st.error(f"ID '{nid}' already exists.")
                else:
                    st.session_state.config.prompts[idx] = PromptPart(
                        id=nid, text=ntxt, tags=tags, default=ndef, variables=variables
                    )
                    st.session_state.editing_idx = None
                    save_current_config()
                    st.session_state.yv += 1
                    st.rerun()
            except Exception as e:
                st.error(str(e))
        if cancel:
            st.session_state.editing_idx = None
            st.rerun()


def render_add_form():
    st.markdown("#### ➕ New Prompt Block")
    with st.form("add"):
        nid = st.text_input("ID", placeholder="my_prompt_id")
        ntxt = st.text_area(
            "Text",
            placeholder="You are a {{ role }} assistant.\nProvide {{ style }} responses.",
            height=180,
        )
        c1, c2 = st.columns(2)
        with c1:
            ntags = st.text_input("Tags (comma-sep)", placeholder="coding, python")
        with c2:
            ndef = st.checkbox("Default")
        nvars = st.text_area(
            "Variables (YAML)",
            placeholder="- name: role\n  required: true\n- name: style\n  required: false\n  default: concise",
            height=120,
        )
        c1, c2 = st.columns(2)
        ok = c1.form_submit_button("➕ Add", type="primary", use_container_width=True)
        cancel = c2.form_submit_button("Cancel", use_container_width=True)

        if ok:
            if not nid:
                st.error("ID is required.")
            elif any(p.id == nid for p in st.session_state.config.prompts):
                st.error(f"ID '{nid}' already exists.")
            else:
                try:
                    tags = [t.strip() for t in ntags.split(",") if t.strip()]
                    variables = parse_vars_yaml(nvars)
                    st.session_state.config.prompts.append(
                        PromptPart(id=nid, text=ntxt, tags=tags, default=ndef, variables=variables)
                    )
                    st.session_state.show_add = False
                    save_current_config()
                    st.session_state.yv += 1
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
        if cancel:
            st.session_state.show_add = False
            st.rerun()


def render_prompt_manager():
    cfg = st.session_state.config
    if not cfg:
        st.markdown(
            '<div class="empty-state"><div class="icon">📂</div>'
            '<div class="title">No Configuration Loaded</div>'
            '<div>Load or create a config from the sidebar.</div></div>',
            unsafe_allow_html=True,
        )
        return

    c1, c2 = st.columns([4, 1])
    with c1:
        st.markdown(f"Managing **{len(cfg.prompts)}** prompt block{'s' if len(cfg.prompts) != 1 else ''}")
    with c2:
        if st.button("➕ Add", use_container_width=True, type="primary"):
            st.session_state.show_add = not st.session_state.show_add
            st.rerun()

    if st.session_state.show_add:
        render_add_form()
        st.markdown("---")

    if not cfg.prompts:
        st.markdown(
            '<div class="empty-state"><div class="icon">📝</div>'
            '<div class="title">No prompts yet</div>'
            '<div>Click ➕ Add to create your first prompt block.</div></div>',
            unsafe_allow_html=True,
        )
        return

    search = st.text_input("🔍 Search", placeholder="Filter by ID, tag, or text…", label_visibility="collapsed")
    for i, p in enumerate(cfg.prompts):
        if search:
            sl = search.lower()
            if sl not in p.id.lower() and sl not in p.text.lower() and not any(sl in t.lower() for t in p.tags):
                continue
        render_prompt_card(p, i)


# ━━━━━━━━━━━━━━━━━━━━━━ BUILDER ━━━━━━━━━━━━━━━━━━━━━━

def render_builder():
    cfg = st.session_state.config
    if not cfg:
        st.markdown(
            '<div class="empty-state"><div class="icon">🔧</div>'
            '<div class="title">No Configuration Loaded</div>'
            '<div>Load or create a config from the sidebar.</div></div>',
            unsafe_allow_html=True,
        )
        return

    st.markdown("### 🔧 Interactive Prompt Builder")
    try:
        from streamlit_sortables import sort_items
    except ImportError:
        st.warning("Please install drag-and-drop dependencies: pip install prompt-config[dashboard]")
        return
        
    all_pids = get_ids(cfg)
    
    state = st.session_state.get("builder_dnd_state")
    if not state or state[0]["items"] + state[1]["items"] != all_pids:
        # Reset state if the config changed underneath
        st.session_state.builder_dnd_state = [
            {"header": "📦 Available Parts", "items": all_pids},
            {"header": "🏗️ Built Prompt (Drag here)", "items": []}
        ]
        
    st.markdown("Drag parts from the available list into the builder in the desired order.")
    sorted_items = sort_items(st.session_state.builder_dnd_state, multi_containers=True, direction="vertical")
    
    if sorted_items:
        st.session_state.builder_dnd_state = sorted_items
        
    selected_ids = st.session_state.builder_dnd_state[1]["items"]
    
    included = []
    seen = set()
    for pid in selected_ids:
        # Avoid duplicate rendering if the list acts up
        if pid in seen: continue
        seen.add(pid)
        for p in cfg.prompts:
            if p.id == pid:
                included.append(p)
                break

    st.markdown("---")
    if not included:
        st.info("No prompts selected. Drag blocks into the builder above.")

    st.markdown("### 📝 Variables")
    all_vars = {}
    for p in included:
        for v in p.variables:
            if v.name not in all_vars:
                all_vars[v.name] = v

    variables = {}
    if all_vars:
        cols = st.columns(2)
        for i, (name, vdef) in enumerate(all_vars.items()):
            with cols[i % 2]:
                icon = "🔴" if vdef.required else "🟢"
                label = f"{icon} {name}"
                if vdef.description:
                    label += f" — {vdef.description}"
                default = str(vdef.default) if vdef.default else ""
                val = st.text_input(label, value=default, key=f"bv_{name}")
                if val:
                    variables[name] = val
    else:
        st.caption("No variables needed for selected prompts.")

    st.markdown("---")
    if st.button("🚀 Build Prompt", type="primary", use_container_width=True):
        try:
            v_copy = dict(variables)
            # Create a localized temporary config with the exact user layout constraints
            ordered_prompts = []
            for p in included:
                ordered_prompts.append(PromptPart(
                    id=p.id, text=p.text, tags=[], default=True, variables=p.variables
                ))
            tmp_cfg = PromptConfig(version=cfg.version, prompts=ordered_prompts)
            tmp_builder = PromptBuilder(tmp_cfg)
            result = tmp_builder.build(tags=[], variables=v_copy)
            st.session_state.built_prompt = result
        except ValueError as e:
            st.error(f"Build error: {e}")
            st.session_state.built_prompt = None

    if st.session_state.built_prompt:
        st.markdown("### 📤 Generated Prompt")
        st.code(st.session_state.built_prompt, language="markdown")
        txt = st.session_state.built_prompt
        c1, c2, c3 = st.columns(3)
        c1.metric("Characters", f"{len(txt):,}")
        c2.metric("Words", f"{len(txt.split()):,}")
        c3.metric("Lines", len(txt.splitlines()))


# ━━━━━━━━━━━━━━━━━━━━━━ YAML EDITOR ━━━━━━━━━━━━━━━━━━━━━━

def render_yaml_editor():
    cfg = st.session_state.config
    if not cfg:
        st.markdown(
            '<div class="empty-state"><div class="icon">📝</div>'
            '<div class="title">No Configuration Loaded</div>'
            '<div>Load or create a config from the sidebar.</div></div>',
            unsafe_allow_html=True,
        )
        return

    st.markdown("### 📝 Raw YAML Editor")
    st.caption("Edit the raw YAML directly. Click **Apply** to validate and update.")

    yaml_str = cfg_to_yaml(cfg)
    edited = st.text_area(
        "yaml", value=yaml_str, height=500,
        label_visibility="collapsed", key=f"ye_{st.session_state.yv}",
    )

    c1, c2 = st.columns(2)
    with c1:
        if st.button("✅ Apply Changes", type="primary", use_container_width=True):
            try:
                new_cfg = load_from_yaml_str(edited)
                st.session_state.config = new_cfg
                save_current_config()
                st.session_state.yv += 1
                st.toast("Config updated!", icon="✅")
                st.rerun()
            except yaml.YAMLError as e:
                st.error(f"YAML syntax error:\n```\n{e}\n```")
            except Exception as e:
                st.error(f"Validation error: {e}")
    with c2:
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.yv += 1
            st.rerun()


# ━━━━━━━━━━━━━━━━━━━━━━ OVERVIEW ━━━━━━━━━━━━━━━━━━━━━━

def render_overview():
    cfg = st.session_state.config
    if not cfg:
        st.markdown(
            '<div class="empty-state"><div class="icon">ℹ️</div>'
            '<div class="title">No Configuration Loaded</div>'
            '<div>Load or create a config from the sidebar.</div></div>',
            unsafe_allow_html=True,
        )
        return

    st.markdown("### ℹ️ Configuration Overview")

    all_tags = get_tags(cfg)
    all_vars, req_vars = set(), set()
    for p in cfg.prompts:
        for v in p.variables:
            all_vars.add(v.name)
            if v.required:
                req_vars.add(v.name)
    defaults = sum(1 for p in cfg.prompts if p.default)

    cols = st.columns(4)
    for col, (val, label) in zip(cols, [
        (len(cfg.prompts), "Total Prompts"),
        (len(all_tags), "Unique Tags"),
        (len(all_vars), "Variables"),
        (defaults, "Default Prompts"),
    ]):
        col.markdown(
            f'<div class="stat-card"><div class="value">{val}</div>'
            f'<div class="label">{label}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("#### 🏷️ Tag Distribution")
        tc = {}
        for p in cfg.prompts:
            for t in p.tags:
                tc[t] = tc.get(t, 0) + 1
        if tc:
            import pandas as pd
            df = pd.DataFrame(list(tc.items()), columns=["Tag", "Count"]).sort_values("Count", ascending=False)
            st.bar_chart(df.set_index("Tag"))
        else:
            st.caption("No tags defined.")

    with c2:
        st.markdown("#### 📎 Variable Summary")
        if all_vars:
            for vn in sorted(all_vars):
                used = [p.id for p in cfg.prompts for v in p.variables if v.name == vn]
                icon = "🔴" if vn in req_vars else "🟢"
                st.markdown(f"{icon} `{vn}` → {', '.join(f'`{x}`' for x in used)}")
        else:
            st.caption("No variables defined.")

    st.markdown("---")
    st.markdown("#### 🗺️ Prompt × Tag Matrix")
    if cfg.prompts and all_tags:
        import pandas as pd
        rows = [{"Prompt": p.id, **{t: "✅" if t in p.tags else "" for t in all_tags}} for p in cfg.prompts]
        st.dataframe(pd.DataFrame(rows).set_index("Prompt"), use_container_width=True)
    else:
        st.caption("Not enough data for matrix view.")


# ━━━━━━━━━━━━━━━━━━━━━━ MAIN ━━━━━━━━━━━━━━━━━━━━━━

def main():
    st.set_page_config(
        page_title="PromptCfg Dashboard",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    load_css()
    init_state()

    st.markdown(
        '<div class="main-header">'
        '<h1>⚡ PromptCfg Dashboard</h1>'
        '<p>Manage, build, and export your LLM prompts</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    render_sidebar()

    t1, t2, t3, t4 = st.tabs(["📋 Prompt Manager", "🔧 Builder", "📝 YAML Editor", "ℹ️ Overview"])
    with t1:
        render_prompt_manager()
    with t2:
        render_builder()
    with t3:
        render_yaml_editor()
    with t4:
        render_overview()


if __name__ == "__main__":
    main()
