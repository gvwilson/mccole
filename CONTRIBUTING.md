# Contributing

Contributions are very welcome.
Please file issues or submit pull requests in our [GitHub repository][repo].
All contributors will be acknowledged,
but must abide by our [Code of Conduct](./CODE_OF_CONDUCT.md).

## Site Structure

-   `README.md`: overview
-   `LICENSE.md`: content license
-   `CODE_OF_CONDUCT.md`: code of conduct
-   `CONTRIBUTING.md`: this contributors' guide
-   `pyproject.toml`: Python package description
-   `Makefile`: repeatable commands
-   `mccole/`: Python source

## Build and Release

-   `pip install build twine`
-   `python -m build`
-   `twine upload --verbose -u __token__ -p pypi-your-access-token dist/*`

## <a id="contributors">Contributors</a>

-   [*Juanan Pereira*][pereira-juanan] is a lecturer in Computer Science
    at the University of the Basque Country (UPV/EHU), where he researches and tries 
    to integrate open source software, software engineering, and LLMs in education.

-   [*Greg Wilson*][wilson-greg] is a programmer, author, and educator based in Toronto.
    He was the co-founder and first Executive Director of Software Carpentry
    and received ACM SIGSOFT's Influential Educator Award in 2020.

[pereira-juanan]: https://ikasten.io/
[repo]: https://github.com/gvwilson/mccole
[wilson-greg]: https://third-bit.com/
