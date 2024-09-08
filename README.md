# McCole

A tool for building very simple static websites.
All of the material is available under an [open license](./LICENSE.md),
and contributions through our [GitHub repository][repo] are welcome:
please see [the contributors guide](./CONTRIBUTING.md) for instructions.
All contributors are required to respect our [Code of Conduct](./CODE_OF_CONDUCT.md).

1.  `pip install mccole` to install.
2.  `mccole install` to copy the following tools into the current directory:
    -   `static/page.css`: styling for regular pages
    -   `static/slides.css`: styling for slides
    -   `static/slides.js`: JavaScript to make slides interactive
    -   `templates/page.html`: Jinja template for pages
    -   `templates/slides.html`: Jinja template for slides

After installation, the following commands will be available:

-   `mccole lint`: internal project check
-   `mccole render`: Markdown-to-HTML translator
-   `mccole stats`: site statistics

[repo]: https://github.com/lessonomicon/mccole
