+++
template = "post.html"
title = 'Writing Citation-Enabled Posts in Persona'
date = 2025-03-19
draft = false
description = """
A practical guide for writing citation-enabled posts in Persona with Pandoc and BibTeX.
"""
[taxonomies]
tags = ['citation', 'pandoc', 'bibtex']
categories = ['Citation', 'Tutorial']
[extra]
citation_style = "apa"
bibliography = "references.bib"

[extra.tex.macros]
'\Real' = '\mathbb{R}^{#1}'
'\norm' = '\left\lVert #1 \right\rVert'

[extra.post]
bibtex = '''
@misc{persona_citation_guide,
  title = {Writing Citation-Enabled Posts in Persona},
  year = {2025},
  note = {Demonstration guide for the Persona theme; not a research publication}
}
'''
+++

`Persona` uses Pandoc to turn citation keys into linked, formatted citations and
a bibliography during the build. This guide covers setup, authoring, and
previewing a citation-enabled post [@zolathemes]. The workflow suits technical,
research, and reference-heavy writing.

## Requirements and setup

Install Zola 0.23 or newer and Python 3.11 or newer. Citation-enabled posts also
require Pandoc. The preview watcher is included; no separate watcher is needed.

```bash
# macOS
brew install zola python pandoc

# Ubuntu / Debian
sudo apt install python3 pandoc
```

In your site's `Makefile`, include Persona's build targets:

```make
include themes/persona/Makefile
```

This uses the scripts from the installed theme, so theme updates also update
the build tools. You can also run `make -f themes/persona/Makefile build` from
the site root without creating a Makefile.

Add this to `config.toml` so Zola skips citation data and any legacy source
files retained while migrating an older site:

```toml
ignored_content = ["*.src.md", "*.bib", "*.csl"]
```

## Write a post

Keep the post and its bibliography in the same folder:

- `index.md` is the authoring source.
- `references.bib` stores the BibTeX entries.

The build prepares a separate copy for Zola and leaves the files in `content/`
unchanged. There is no second source filename or generated Markdown to maintain
beside your post. Pages without citations use the same authoring workflow.

## Write citations {#write-citations-in-.src.md}

Use [Pandoc citation syntax](https://pandoc.org/demo/example33/8.20-citation-syntax.html) in Markdown:

```markdown
Climate change is accelerating[@ipcc2021].
Multiple studies confirm this[@ipcc2021; @nasa2023].
```

Add citation settings to the post's `[extra]` front matter:

- `citation_style = "apa"`
- `bibliography = "references.bib"`

Set the citation style once for the site if you want it to apply to posts by
default.

## Mathematics and LaTeX macros

Define reusable KaTeX macros in `[extra.tex.macros]`. TOML literal strings preserve backslashes:

```toml
[extra.tex.macros]
'\Real' = '\mathbb{R}^{#1}'
'\norm' = '\left\lVert #1 \right\rVert'
```

For a vector $x \in \Real{n}$, the Euclidean norm is

$$
\norm{x}_2 = \sqrt{\sum_{i=1}^{n} x_i^2}.
$$

Write inline mathematics between `$` delimiters and display mathematics between
`$$` delimiters. With `[extra.tex]` or `[extra.tex.macros]` enabled, Persona
preserves the expressions before Markdown processing, including backslashes,
underscores, and page-specific macros. You do not need to wrap equations in
`<div>` elements or add backslashes to compensate for Markdown escaping.
Citation references and mathematics can appear together in the same article
[@zolathemes].

For example, write a multiline equation directly in Markdown:

```latex
$$
\begin{aligned}
a_i &= b_i + c_i \\
S &= \{x, y\}
\end{aligned}
$$
```

Code examples keep their literal dollar signs. Escape a dollar sign in prose
as `\$` when you mean currency rather than the start of an equation.

## Build and preview

Use the Makefile to build or preview your site:

```bash
make build
make serve
```

`make build` prepares the content and builds the complete site into `public/`.
`make serve` prepares the content, starts Zola's preview server, and watches for
changes to posts, bibliography and CSL files, configuration, templates, and
assets. Save the authored `index.md` to update the preview.

Use these commands instead of bare `zola build` and `zola serve`, which bypass
Persona's math and citation processing. Zola options can be passed through
`ZOLA_ARGS`, for example `make serve ZOLA_ARGS="--port 2222"`.

## Citation style resolution order

The preprocessor selects a CSL style in this order:

1. The post's `[extra].citation_style`, resolved from `citation-style/<name>.csl`.
2. A `style.csl` beside the `.md` file.
3. Site `config.toml`: `[extra].citation_style` or `[extra.persona].citation_style`.
4. Theme `themes/persona/theme.toml` `[extra].citation_style`, or `themes/persona/config.toml` `[extra.persona].citation_style`.

Persona includes the `ieee` and `apa` styles. Add custom CSL files to your
site's `citation-style/` directory or place a `style.csl` beside a post source.
If an explicitly configured style cannot be found, the build reports an error
so you can correct its name or path. Citation processing requires a resolvable
CSL style; posts without citations do not require a citation style.

## Output and styling

Pandoc emits HTML citations and a bibliography with stable classes that the theme styles:

- `.citation`
- `.references`
- `.csl-entry`
- `.csl-left-margin`
- `.csl-right-inline`

Inline citations link to their bibliography entries. The bibliography appears
inside the `references` container under **Bibliography**, after the optional
**Citation** section. That section displays the post's `[extra.post].bibtex`;
the bibliography lists works cited in the text. This guide includes a sample
BibTeX record to demonstrate both.

For the complete example, see this guide's [source directory](https://github.com/hanson-hschang/Persona-Zola-Theme/tree/main/content/maps/private-soul/citation-pipeline-guide/).
