# McCole

A tool for building very simple static websites.

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
