# Contributing

Thanks for your interest in contributing! This project welcomes issues and pull requests.

Getting started
- Python 3.10+
- Create a virtualenv and install dependencies:
  - Core: `pip install httpx backoff pydantic`
  - Or full set: `pip install -r requirements.txt`
  - Rendering (optional): `python -m playwright install chromium`

Running tests
- Run all tests: `python -m unittest discover -v`
- Or run a specific test: `python -m unittest crawler/tests/test_dedup.py -v`
- Some tests are skipped if optional dependencies are not installed.

Submitting changes
1. Fork the repo and create a feature branch.
2. Add tests for your change where applicable.
3. Ensure tests pass: `python -m unittest discover -v`.
4. Open a Pull Request with a clear description of the change.

Code style
- Keep changes minimal and focused.
- Prefer small, composable functions and explicit error handling.
- Add docstrings or comments for non-trivial logic.

Security
- Please do not include secrets in code or logs.
- If you discover a vulnerability, contact the maintainers privately first.
