# Contributing

Contributions are very welcome.
Please file issues or submit pull requests in [our GitHub repository][repo].
All contributors will be acknowledged.

## Setup

-   Use `pip install -r requirements.txt`
    to install the packages required by the helper tools and Python examples.
    You may wish to create a new virtual environment before doing so.
    All code has been tested with Python 3.12.1.

-   Run `make` without arguments to see available commands
    Of these,
    `make build` to rebuild everything in `./docs`
    and `make serve` to run a local preview server
    are the most immediately useful.

| Command      | Action |
| ------------ | ------ |
| `commands`   | show available commands |
| `build`      | rebuild site without running server |
| `serve`      | build site and run server |
| `profile`    | profile compilation |
| `bib`        | rebuild HTML version of bibliography |
| `lint`       | check project |
| `style`      | check Python code style |
| `reformat`   | reformat unstylish Python code |
| `pack`       | create a release |
| `unpack`     | make required files after unzipping mccole.zip |
| `clean`      | clean up stray files |

## Layout

-   This template uses [Ark][ark] to compile Markdown with embedded shortcode directives
    into a static HTML site under `docs/`.

-   The McCole theme lives in `lib/mccole`:
    -   `bin/`: utility scripts
    -   `colophon.yml`: links used in the colophon
    -   `extensions/`: shortcodes and other extensions to Ark used by the theme
    -   `mccole.mk`: targets and commands common to all projects that use this theme
    -   `requirements.txt`: packages common to all projects that use this theme
    -   `resources/`: CSS files and other resources used by this theme
    -   `templates/`: HTML templates used by this theme (the main one being `node.ibis`).

-   The site's configuration lives in `config.py`.
    The lists `chapters` and `appendices` define slugs for the sections, in order.

-   Content lives in `.md` files in subdirectories under `src`
    Each section must be in its own subdirectory except for `src/index.md`,
    which is the site's home page.

-   Please write external links using `[box][notation]`
    and define links in `info/tutorial.yml`
    rather than putting links inline.
    Doing this will help ensure consistency across pages.

-   Use `[%x slug %]` to create a cross-reference to a chapter or appendix,
    where the slug is the name of a subdirectory under `src`.

-   Use `[%g key "text" %]` to link to glossary entries.
    The text is inserted and highlighted;
    the key must identify an entry in `info/glossary.yml`,
    which is in [Glosario][glosario] format.

-   Use `[%b key1 key2 %]` to cite bibliography entries.
    The keys must appear in `info/bibliography.bib`,
    which is stored in BibTeX format
    and compiled to create `tmp/bibliography.html`.

-   Use `[%figure slug="some_slug" img="some_file.ext" caption="the caption" alt="alt text" %]`
    to create a figure and `[%f some_slug %]` to refer to it.

-   Use `[%table slug="some_slug" tbl="some_file.tbl" caption="the caption" %]`
    to create a table and `[%g some_slug %]` to refer to it.

-   Use `[%inc filename %]` to include a text file containing code or sample output
    in a Markdown file.
    If the inclusion contains `mark=label`
    then only code between comments marked `[label]` and `[/label]` will be included.

-   SVG diagrams can be edited using [draw.io][draw_io].
    Please use 14-point Helvetica for text,
    solid 1-point black lines,
    and unfilled objects.

## FAQ

What is this for?
:   I wrote [a short SQL tutorial][sql] in 2024,
    and am currently working on one about [systems programming][sys]
    and another about [research software design][rsdx].
    I was initially going to use the template I built for
    the [JavaScript][sdxjs] and [Python][sdxpy] versions of *Software Design by Example*,
    but realized I could slim it down,
    speed it up,
    and make it prettier.
    Some people knit
    some play video games,
    I like to type…

Why Ark?
:   [Jekyll][jekyll] is the default for [GitHub Pages][ghp],
    but very few data scientists use Ruby
    so previewing changes locally would require them to install and use
    yet another language framework.
    In addition,
    GitHub Pages doesn't allow arbitrary extensions for security reasons,
    so the only way to implement things like bibliography citations and glossary references
    is to use its (rather verbose) inclusions and (rather clumsy) scripting features.

Why Make?
:   It runs everywhere,
    no other build tool is a clear successor,
    and,
    like Jekyll,
    it's uncomfortable enough to use that people won't be tempted to fiddle with it
    when they could be writing content.

Why hand-drawn figures rather than [Graphviz][graphviz] or [Mermaid][mermaid]?
:   Because it's faster to Just Effing Draw than it is
    to try to tweak layout parameters for text-to-diagram systems.
    If you really want to make developers' lives better,
    build a diff-and-merge tool for SVG:
    programmers shouldn't have to use punchard-compatible data formats in the 21st Century
    just to get the benefits of version control.

Why McCole?
:   Because it was my father's middle name.
    He was my high school English teacher for five years (it was a small town),
    and I learned most of what I know about writing from him.

[ark]: https://www.dmulholl.com/docs/ark/main/
[draw_io]: https://www.drawio.com/
[ghp]: https://pages.github.com/
[glosario]: https://glosario.carpentries.org/
[graphviz]: https://graphviz.org/
[jekyll]: https://jekyllrb.com/
[mermaid]: https://mermaid.js.org/
[repo]: https://github.com/gvwilson/mccole/
[rsdx]: https://gvwilson.github.io/rsdx/
[sdxjs]: https://third-bit.com/sdxjs/
[sdxpy]: https://third-bit.com/sdxpy/
[sql]: https://gvwilson.github.io/sql-tutorial/
[sys]: https://gvwilson.github.io/sql-tutorial/
