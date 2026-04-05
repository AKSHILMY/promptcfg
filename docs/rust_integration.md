# Rust PyO3 Acceleration for `prompt-config`

Completed the implementation of a high-performance Rust backend for prompt rendering across Python applications.

## High-Level Changes
When handling massive API throughput, string concatenation and Jinja2 templating in Python can become a bottleneck due to the GIL (Global Interpreter Lock). 

This update solves that by:
1. Creating a `promptcfg-core` Rust extension wrapper using PyO3.
2. Converting the Python `PromptConfig` models into raw memory objects in `RustPromptBuilder.new()`.
3. Offloading iterating, tag filtering, default substitution, and template rendering to `minijinja` inside `src/lib.rs`.
4. Wrapping all of this seamlessly into the existing Python library build. If the target machine can't compile/run the Rust extension, it safely falls back to pure Python `jinja2`.

## Verification & Benchmarking
The [examples/benchmark_rust.py](file:///Users/akshilmy-m4-pro/career/prompter/examples/benchmark_rust.py) script generates exactly 100 logical prompt blocks and measures how long it takes to process, filter, and render them all into a single string.

> [!TIP]
> The Rust core achieved an **~82.4x Speedup** compared to Python Jinja2!

```text
--- PERFORMANCE RESULTS (100 prompts built and concatenated) ---
Pure Python Jinja2 Time : 9.7386 ms per build
Rust PyO3 Minijinja Time: 0.1182 ms per build
Speedup                 : 82.4x faster in Rust!
```

### Full Compatibility
We preserved 100% of the original unit testing logic. When `python -m unittest discover tests` runs:
1. Python still handles converting `default` values into the underlying `Dictionary` for code using pass-by-reference.
2. The Rust engine properly releases the Python GIL using `py.allow_threads` during execution, allowing FastAPI servers to handle other active async network requests simultaneously while rendering heavy prompts.
3. If users dynamically append `.prompts.append()` to the configuration during runtime, the `build()` interceptor detects the array length change and forces PyO3 to rebuild the Rust memory cache safely.

### Build Compatibility (Python 3.11 & 3.12)
The PyPI package `Prompt-Config` now uses `setuptools-rust` inside `setup.py` instead of purely `maturin`. 
When a user attempts `pip install prompt-config`, the `setup.py` checks their environment:
- If the user is running **Python 3.11 or 3.12**, it automatically attempts to invoke the Rust compiler (`Cargo`) and build the `.so` PyO3 bindings natively for their architecture.
- If the user is on **Python 3.10 or older**, they will seamlessly fall back to downloading and installing the purely Python/Jinja2 version of the package.
