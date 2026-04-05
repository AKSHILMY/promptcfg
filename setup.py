import sys
from setuptools import setup

setup_kwargs = {}

# Only build Rust extension conditionally for Python 3.11 and 3.12
if sys.version_info[:2] in [(3, 11), (3, 12)]:
    try:
        from setuptools_rust import Binding, RustExtension
        setup_kwargs["rust_extensions"] = [
            RustExtension("promptcfg.promptcfg_core", binding=Binding.PyO3, debug=False)
        ]
        setup_kwargs["zip_safe"] = False
    except ImportError:
        print("setuptools-rust not installed. Building pure Python package instead.")

setup(**setup_kwargs)
