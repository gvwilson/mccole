---
title: Conclusion
---

<section class="slide" markdown="1">

## Key Takeaways

Advance with the right arrow to reveal each point.

<ul>
<li class="next">Keep lessons and slides in the same directory</li>
<li class="next"><code>index.md</code> renders with <code>page.html</code> — full lesson layout</li>
<li class="next"><code>slides.md</code> renders with <code>slides.html</code> — Shower presentation</li>
<li class="next">File inclusions (<code>%inc</code>) resolve relative to the source file in both</li>
</ul>

</section>

<section class="slide" markdown="1">

## A Figure in a Slide

[%figure slug="slide-changes" img="changes.svg" alt="diagram showing changes over time" caption="Changes over time"%]

</section>

<section class="slide" markdown="1">

## Lessons vs. Slides

<div class="row" markdown="1">
<div class="col-6" markdown="1">

**Lessons** (`index.md`)

- Full prose explanations
- Numbered exercises
- Glossary and bibliography links
- Prev/next navigation

</div>
<div class="col-6" markdown="1">

**Slides** (`slides.md`)

- Concise bullet points
- Code samples
- Incremental reveals with `.next`
- Keyboard and touch navigation

</div>
</div>

</section>

<section class="slide" markdown="1">

## What Comes Next

You have everything you need.

<div class="next" markdown="1">

**Create** a new project: `mccole create --dst myproject`

</div>

<div class="next" markdown="1">

**Write** your content in `index.md` and `slides.md`.

</div>

<div class="next" markdown="1">

**Build** and publish: `mccole build --src . --dst docs`

</div>

</section>
