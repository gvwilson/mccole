---
title: Introduction
---

<section class="slide" markdown="1">

## What This Course Covers

mccole turns Markdown files into a polished tutorial site with
separate lesson pages and matching slide decks.

- Static site generation from plain Markdown
- Shortcodes for figures, code inclusions, and more
- Shower.js for keyboard-driven presentations

Click a slide or press Enter to enter presentation mode.
Press Escape to return to this overview.

</section>

<section class="slide" markdown="1">

## Step by Step

Press the right arrow (or N, L, J, Space) to reveal each step.

<ul>
<li class="next">Install mccole: <code>pip install mccole</code></li>
<li class="next">Create a project: <code>mccole create --dst myproject</code></li>
<li class="next">Write lessons in <code>index.md</code></li>
<li class="next">Write slides in <code>slides.md</code> — same directory</li>
<li class="next">Build: <code>mccole build --src myproject --dst myproject/docs</code></li>
</ul>

</section>

<section class="slide" markdown="1">

## A Simple Example

Every Python programmer starts here:

```python
def greet(name):
    """Return a greeting."""
    return f"Hello, {name}!"

print(greet("world"))
```

<div class="next" markdown="1">

Output: `Hello, world!`

</div>

<div class="next" markdown="1">

That's all there is to it — the rest is just details.

</div>

</section>
