# McCole

A template for [Ark][ark]-based tutorials.

1.  Set up Python environment:
    1.  Create `./lib/mccole/`.
    1.  Create `./lib/mccole/requirements.txt`.
    1.  Add `ark` and `pymdown-extensions` to `./lib/mccole/requirements.txt`.
    1.  Create `./requirements.txt` with `-r lib/mccole/requirements.txt`.
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
    1.  Create `./LICENSE.md` and `./CODE_OF_CONDUCT.md` for GitHub to display.
    1.  Create `./src/license/index.md` and `./src/conduct/index.md` to generate pages in `./docs`.
    1.  Define `rootfile` shortcode in `./lib/mccole/extensions/rootfile.py` to include files from the root.
    1.  Create `./lib/mccole/extensions/util.py` to hold utilities.
    1.  Add `__pycache__` to `.gitignore` to stop `util.pyc` from being included in Git.

1.  Create glossary.
    1.  Add `./src/glossary/index.md` with `[% glossary %]` shortcode.
    1.  Add `[%g ssg "text" %]` to `./src/index.md` as test case.
    1.  Create `./info/glossary.yml` with [Glosario][glosario]-format glossary.
    1.  Add `lang="en"` to `./config.py` to specify language.
    1.  Create `./lib/mccole/extensions/glossary.py` with implementation of `glossary` and `g` shortcodes.
    1.  Add test case for `g` shortcode to `./src/index.md`.
    1.  Add `markdownify` function to `./lib/mccole/extensions/util.py` for Markdown conversion.

[ark]: https://www.dmulholl.com/docs/ark/main/
[glosario]: https://glosario.carpentries.org/
