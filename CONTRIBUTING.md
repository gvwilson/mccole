# Contributing

Contributions are very welcome.
Please file issues or submit pull requests in [our GitHub repository][repo].
All contributors will be acknowledged.

## In Brief

-   Use `pip install -r requirements.txt`
    to install the packages required by the helper tools and Python examples.
    You may wish to create a new virtual environment before doing so.
    All code has been tested with Python 3.12.1.

-   Content lives in the `.md` files under the `src` directory
    and is translated into a static website using [Ark][ark].
    Each page must be in its own sub-directory except for `src/index.md`,
    which becomes the site's home page.

-   `Makefile` references `lib/mccole/mccole.mk`;
    typing `make` by itself on the command line will list available targets.

-   All external links are written using `[box][notation]` inline
    and defined in `info/tutorial.yml`.

-   Use `[%x slug %]` to create a cross-reference to a chapter or appendix,
    where the slug is the name of a sub-directory under `src`.

-   Use `[%g key "text" %]` to link to glossary entries.
    The text is inserted and highlighted;
    the key must identify an entry in `info/glossary.yml`,
    which is in [Glosario][glosario] format.

-   Use `[%b key1 key2 %]` to cite bibliography entries,
    which are stored in BibTeX format in `info/bibliography.bib`.

-   Use `[%inc filename %]` to include a text file containing code or sample output
    in a Markdown file.

-   Use `[%figure slug="some_slug" img="some_file.ext" caption="the caption" alt="alt text" %]`
    to create a figure and `[%f some_slug %]` to refer to it.

-   Use `[%table slug="some_slug" tbl="some_file.tbl" caption="the caption" %]`
    to create a table and `[%g some_slug %]` to refer to it.

-   SVG diagrams can be edited using [draw.io][draw_io].
    Please use 14-point Helvetica for text,
    solid 1-point black lines,
    and unfilled objects.

## FAQ

[ark]: https://www.dmulholl.com/docs/ark/main/
[draw_io]: https://www.drawio.com/
[glosario]: https://glosario.carpentries.org/
[repo]: https://github.com/gvwilson/mccole/
