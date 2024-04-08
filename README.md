# McCole

A template for [Ark][ark]-based tutorials.

1.  Set up Python environment:
    1.  Create `lib/mccole/`.
    1.  Create `lib/mccole/requirements.txt`.
    1.  Add `ark` and `pymdown-extensions` to `lib/mccole/requirements.txt`.
    1.  Create `requirements.txt` with `-r lib/mccole/requirements.txt`.
    1.  Create conda environment `mccole`.
    1.  Install packages with `pip install -r requirements.txt`.

1.  Set up minimal Ark site:
    1.  Create `config.py`.
    1.  Define `title`, `repo`, and `author`.
    1.  Define `theme` to be `mccole`.
    1.  Define `src_dir` to be `src`.
    1.  Define `out_dir` to be `docs`.
    1.  Define `extension` to be `/`.
    1.  Enable Markdown extensions.
    1.  Create empty `src/index.md`.
    1.  Create `lib/mccole/templates/node.ibis` template with nothing but `{{node.html}}`.

1.  Create license and code of conduct pages:
    1.  Create `LICENSE.md` and `CODE_OF_CONDUCT.md` for GitHub to display.
    1.  Create `src/license/index.md` and `src/conduct/index.md` to generate pages in `docs`.
    1.  Define `rootfile` shortcode in `lib/mccole/extensions/rootfile.py` to include files from the root.
    1.  Create `lib/mccole/extensions/util.py` to hold utilities.
    1.  Add `__pycache__` to `.gitignore` to stop `util.pyc` from being included in Git.

1.  Create glossary.
    1.  Add `src/glossary/index.md` with `[% glossary %]` shortcode.
    1.  Add `[%g ssg "text" %]` to `src/index.md` as test case.
    1.  Create `info/glossary.yml` with [Glosario][glosario]-format glossary.
    1.  Add `lang="en"` to `config.py` to specify language.
    1.  Create `lib/mccole/extensions/glossary.py` with implementation of `glossary` and `g` shortcodes.
    1.  Add test case for `g` shortcode to `src/index.md`.
    1.  Add `markdownify` function to `lib/mccole/extensions/util.py` for Markdown conversion.

1.  Automation.
    1.  Create `Makefile` that includes `lib/mccole/mccole.mk`.
    1.  Create `lib/mccole/mccole.mk` with targets to rebuild and check.
    1.  Add `ruff` to `lib/mccole/requirements.txt` and install it.

1.  Style pages.
    1.  Create `lib/mccole/resources/mccole.css` with beginnings of (unresponsive) styling.
    1.  Add HTML layout to `lib/mccole/templates/node.ibis`.
    1.  Add `head.html` and `foot.html` to `lib/mccole/templates` directory.
    1.  Add `lib/mccole/resources/logo.svg` for use as favicon.
    1.  Add `.nojekyll` file to prevent GitHub from re-rendering pages.

1.  Add front matter to `index.md` pages with titles.

1.  Add cross-referencing and table of contents.
    1.  Add `chapters` and `appendices` to `config.py` to define order.
    1.  Add `_number_contents` and `_collect_titles` to `lib/mccole/extensions/init.py` to gather information.
    1.  Create `lib/mccole/extensions/toc.py` for cross-references and table of contents.
    1.  Add `x` shortcode to cross-reference chapters and appendices.
    1.  Add `toc` shortcode to create table of contents.
    1.  Add `src/intro/index.md` and `src/finale/index.md` as test cases.

1.  Add bibliography.
    1.  Modify `lib/mccole/requirements.txt` to install `pybtex` package.
    1.  Add `info/bibliography.bib` (BibTeX-formatted bibliography).
    1.  Add `lib/mccole/bin/make_bibliography.py` to translate BibTeX into HTML in `tmp/bibliography.html`.
    1.  Modify `lib/mccole/mccole.mk` to build HTML version of bibliography.
    1.  Modify `lib/mccole/resources/mccole.mk` to display bibliography.
    1.  Add `bibliography` shortcode to include bibliography in page.
    1.  Add `b` shortcode to reference bibliography entries.
    1.  Add `src/bib/index.md` to show bibliography.
    1.  Modify `config.py` to include `bib` as appendix.

1.  Add figures and tables.
    1.  Add `lib/mccole/extensions/figure.py` with shortcode `f` and figure inclusion `figure`.
    1.  Add `lib/mccole/extensions/table.py` with shortcode `t` and figure inclusion `table`.
    1.  Rename `lib/mccole/extensions/init.py` to `lib/mccole/extensions/batch.py` to reflect purpose.
    1.  Add startup task in `lib/mccole/extensions/batch.py` to find and number all figures and tables.
    1.  Add `copy` field to `config.py` with globs of files to copy directly (just `*.svg` for now).
    1.  Add finalization code to `lib/mccole/extensions/batch.py` to copy files.
    1.  Add examples of figures and tables (and references) to `src/intro/index.md` and `src/finale/index.md`.
    1.  Move localization into `lib/mccole/extensions/util.py`.

1.  Add navigation links and a proper title.
    1.  Collect all metadata in `lib/mccole/extensions/batch.py`.
    1.  Add `lib/mccole/templates/title.html` to format title and prev/next navigation links.
    1.  Include `title.html` in `lib/mccole/templates/node.ibis`.
    1.  Add `lib/mccole/extensions/filters.py` with various filters required by template additions.
    1.  Add flex grid to `lib/mccole/resources/mccole.css`.
    1.  Modify `src/license/index.md` and `src/conduct/index.md` to strip inherited title of root pages.

1.  Add links to pages.
    1.  Add `info/links.yml` with link definitions.
    1.  Add `ensure_links` function to `lib/mccole/extensions/util.py` to load and format links.
    1.  Add `_append_links` function to `lib/mccole/extensions/batch.py` to append link text to files.
    1.  Add `src/colophon/index.md` to display credits.

1.  Add list of defined terms to pages.
    1.  Move glossary loading to `lib/mccole/extensions/util.py` and cache.
    1.  Refactor shortcode collection in `lib/mccole/extensions/batch.py`.
    1.  Add collection of glossary keys in `lib/mccole/extensions/batch.py`.
    1.  Add filter `termdefs` in `lib/mccole/extensions/filters.py` to display defined terms.
    1.  Move glossary reference test into `src/intro/index.md`.
    1.  Modify `lib/mccole/templates/node.ibis` to show defined terms.

1.  Refactor.
    1.  Move larger filters like `termdefs` into files of their own.
    1.  Add hooks to exclude directories and files.
    1.  Add `copy` and `exclude` keys to `config.py`.
    1.  Add `fixme` shortcode for notes.
    1.  Add target to `lib/mccole/mccole.mk` to build zip file and to check things after unpacking it.

1.  Add features after trying it out.
    1.  Add contributors' guide in `CONTRIBUTING.md` and page in `src/contrib/index.md`.
    1.  Add MathJax to `lib/mccole/templates/head.html`.
    1.  Add link to home page to `lib/mccole/templates/foot.html`.
    1.  Add colored sidebars to `lib/mccole/resources/mccole.css`.
    1.  Add stamp colors and Danielle Navarro to colophon.

1.  Add thanks.
    1.  Add `lib/mccole/extensions/thanks.py` to read and format `info/thanks.yml`.
    1.  Add usage to `src/intro/index.md` to test.

1.  Add index.
    1.  Add `lib/mccole/extensions/index.py` to format index and index references.
    1.  Modify `lib/mccole/extensions/batch.py` to collect index references.
    1.  Add `src/contents/index.md` to display index (using `contents` instead of `index` to avoid confusion).
    1.  Modify `lib/mccole/mccole.mk` to include `src/contents/index.md` in zip file.

1.  Add linting.
    1.  Add `lib/mccole/bin/lint.py` and `lib/mccole/bin/lint_svg.py` to check project features.
    1.  Add targets to `lib/mccole/mccole.mk` to run them.

1.  CSS improvements.
    1.  Responsive layout.
    1.  Reduce indentation of bullet lists.
    1.  Label navigation controls with `<nav>` element.
    1.  Unify colors and borders of code inclusions.
    1.  Syntax highlighting.

1.  Add profiling.
    1.  Add `lib/mccole/bin/run_profile.py` to profile build.
    1.  Add target to `lib/mccole/mccole.mk` to run it.

1.  Improve contribution guide.

[ark]: https://www.dmulholl.com/docs/ark/main/
[glosario]: https://glosario.carpentries.org/
