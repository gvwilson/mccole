# McCole Theme

An Ivy theme for books.

## Layout

-   `src/index.md` becomes the site home page `docs/index.html`.
-   `src/slug/index.md` becomes the chapter page `docs/slug/index.html`.
    -   Code fragments and other files go in the same directory `docs/slug`.
    -   Figures go in `docs/slug/figures/name.svg` (for the web) and `docs/slug/figures/name.pdf` (for print).
-   Data files go in the `data/` directory.
    -   `data/bibliography.bib` is a BibTeX-style bibliography.
    -   `data/glossary.yml` is a Glosario-style glossary.
    -   `data/links.yml` contains external links.
-   Site-wide files go in `res`, the contents of which are copied directly into `docs`.
-   LaTeX support files go in `tex`.
-   Support tools go in `bin`.
    -   `bin/single-html.py` generates a single-page HTML file from the chapters' HTML files.
    -   `bin/tex.py` converts that page to LaTeX.
    -   `bin/utils.py` has utilities.

## Configuration

Ivy configuration goes in `./config.py`.
Projects should only change the following values:

-   `title` and `subtitle`: both are required by the templates.
-   `repo`: the URL of the GitHub repository.
-   `logo`: a file from `res` that is copied to the root of `docs`.
-   `lang`: controls which glossary definitions are used.
-   `chapters`: a list of chapter slugs.
-   `appendices`: a list of appendix slugs.
    -   Several are given as starting points.
    -   The overall index is called `"topics"` to avoid collision with the site index page.

## Formatting

Avoid consecutive headings.

### Front Matter

Every chapter page must have:

-   `title: "The Page Title"`
-   `template: page`

### Headings

Do _not_ use level-1 headings in pages: their titles are generated automatically from the frontmatter.

Use level-2 headings with IDs for sections, and use the chapter slug as the first part of the ID.
For example, a section in a chapter whose ID is `file-backup` would be formatted as:

```
## How can we uniquely identify files? {: #file-backup-unique}
```

Only use level-3 headings for callouts (described below) and exercises.
The overall section heading for exercises should be formatted like this:

```
## Exercises {: #file-backup-exercises}
```

and the subsection headings for exercises must have the `.exercise` class, e.g.:

```
### Odds of collision {: .exercise}
```

### Hyperlinks

Always use `[name][key]` for external links
and add an entry to `data/links.yml` with the required key, e.g.,
put this in the text:

```
We can use a parser generator like [Antlr][antlr] to do this.
```

and this in `docs/links.yml`:

```
- key: antlr
  url: https://www.antlr.org/
  title: ANTLR
```

### Cross-references

Use the following shortcodes to insert cross-references:

-   `[% x some-id %]` to refer to a chapter, appendix, or section.
-   `[% f some-id %]` to refer to a figure.
-   `[% t some-id %]` to refer to a table.

### Figures

Use the `figure` shortcode to insert a figure.
All fields are required:

```
[% figure
   slug="some-slug"
   img="figures/filename.svg"
   alt="Short description"
   caption="Full sentence description.." %]
```

As with section headings,
the figure ID should start with the chapter slug,
e.g.,
`file-backup-some-identifier`.

### Tables

Use Markdown tables for short tables that aren't referenced by ID:

```
| Number of Files | Odds of Collision |
| --------------- | ----------------- |
| 1               | 0%                |
| 2               | 25%               |
| 3               | 50%               |
```

Wrap longer tables that are referenced by ID in a `div` as shown below.
Remember to include `class="table"` and `markdown="1"`:

<div class="table" id="chapter-slug-odds" caption="Full-sentence caption." markdown="1">
| Number of Files | Odds of Collision |
| --------------- | ----------------- |
| 1               | 0%                |
| 2               | 25%               |
| 3               | 50%               |
</div>

(A `div` is required because the Markdown parser doesn't allow IDs to be added to Markdown tables.)

### Citations

Format bibliographic citations like this:

```
[% b Key1 Key2 %]
```

The keys do not have to be quoted,
and must match keys in the bibliography file in the `data` directory.

### Glossary and Index

Use the following to create a reference to a glossary entry:

```
[% g hash_function %]hash function[% /g %]
```

Only put a single glossary key in the shortcode opener;
that key must match one in the book's glossary.

Use the following to create an index entry:

```
[% i "Git" "version control system!Git" %]Git[% /i %]
```

One or more index keys can appear in the opening shortcode;
please quote them to avoid problems with embedded spaces.
Use an exclamation mark to create a sub-key, i.e., `"major!minor"`.

Terms that appear in the glossary also often appear in the index.
When this happens,
please put the index shortcode outside the glossary shortcode, e.g.:

```
[% i "CVS" %][% g cvs %]CVS[% /g %][% /i %]
```

### Code Excerpts

The `[% excerpt ... %]` shortcode includes other files or portions of other files:

-   `[% excerpt file="path" %]` includes an entire file.
    The path is relative to the including file.

-   `[% excerpt file="path" keep="key" %]` includes everything
    between lines marked with `[key]` and `[/key]`.
    These markers are usually placed in comments.

-   `[% excerpt file="path" omit="key" %]` omits everything between markers.

-   `[% excerpt file="path" keep="outer" omit="inner" %]`
    selects the lines within the `outer` section,
    then omits lines within that section marked with `inner`.

-   `[% excerpt pat="path.*" fill="one two" %]` includes the files `path.one` and `path.two`,
    i.e., replaces `*` in `pat` with each of the tokens in `fill`,
    then includes all of that file.

### Continuations

If a paragraph is split in two or more pieces
(e.g., because a small code fragment appears in the middle)
add the `.continue` class to the continuation paragraphs:

```
As you can see:

...some interruption...

appears in the middle of a paragraph.
{: .continue}
```

## Colophon

McCole ("muh-COAL") is named after Robert McCole Wilson (1934-2015),
who taught me how to write
and that writing well is important.
Thanks, Dad.

<p align="center"><img src="https://github.com/gvwilson/mccole/raw/main/mccole.jpg" alt="Robert McCole Wilson" /></p>
