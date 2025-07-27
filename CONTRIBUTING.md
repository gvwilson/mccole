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
-   `twine upload --verbose -u __token__ -p your-pypi-access-token dist/*`

## Labels

| Name             | Description                  | Color   |
| ---------------- | ---------------------------- | ------- |
| change           | something different          | #FBCA04 |
| feature          | new feature                  | #B60205 |
| fix              | something broken             | #5319E7 |
| good first issue | newcomers are always welcome | #D4C5F9 |
| talk             | question or discussion       | #0E8A16 |
| task             | one-off task                 | #1D76DB |

Please use [Conventional Commits][conventional] style for pull requests
by using `change:`, `feature:`, `fix:`, or `task:` as the first word
in the title of the commit message.
You may also use `publish:` if the PR just rebuilds the HTML version of the lesson.

## <a id="contributors">Contributors</a>

-   [*Juanan Pereira*][pereira-juanan] is a lecturer in Computer Science
    at the University of the Basque Country (UPV/EHU), where he researches and tries 
    to integrate open source software, software engineering, and LLMs in education.

-   [*Greg Wilson*][wilson-greg] is a programmer, author, and educator based in Toronto.
    He was the co-founder and first Executive Director of Software Carpentry
    and received ACM SIGSOFT's Influential Educator Award in 2020.

[conventional]: https://www.conventionalcommits.org/
[pereira-juanan]: https://ikasten.io/
[repo]: https://github.com/lessonomicon/mccole
[wilson-greg]: https://third-bit.com/
