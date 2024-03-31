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

[ark]: https://www.dmulholl.com/docs/ark/main/
