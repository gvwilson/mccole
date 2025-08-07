# Contributing

Contributions are very welcome.
Please file issues or submit pull requests in our [GitHub repository][repo].
All contributors will be acknowledged,
but must abide by our [Code of Conduct](./CODE_OF_CONDUCT.md).

-   Setup:
    -   `uv venv` (once)
    -   `source .venv/bin/activate`
    -   `uv sync --extra dev`
-   Check package: `make lint`
-   Build package: `make build` or `python -m build`
-   Publish package: `twine upload --verbose -u __token__ -p your-pypi-access-token dist/*`

[repo]: https://github.com/gvwilson/mccole
