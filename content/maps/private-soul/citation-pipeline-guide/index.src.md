+++
title = 'How to Use Citation in Persona'
date = 2025-03-19
draft = false
[taxonomies]
tags = ['citation', 'pandoc', 'bibtex']
categories = ['private-soul']
[extra]
excerpt = """
A practical guide for writing citation-enabled posts in Persona with Pandoc and BibTeX.
"""
citation_style = "apa"
bibliography = "references.bib"
+++

Persona supports `[@cite]` through a Pandoc preprocessing pipeline.
This post is the working example for authoring and building citation-enabled content [@zolathemes].

## Prerequisites

Install Pandoc and watchexec:

```bash
# macOS
brew install pandoc watchexec

# Ubuntu / Debian
sudo apt install pandoc
cargo install watchexec-cli
```

## File structure

Keep these files in the same folder:

- `index.src.md` (authoring source)
- `references.bib` (BibTeX database)
- `index.md` (generated output, do not edit manually)

## Write citations in `.src.md`

Use Pandoc citation syntax in Markdown:

```markdown
Climate change is accelerating[@ipcc2021].
Multiple studies confirm this[@ipcc2021; @nasa2023].
```

Set optional citation config in frontmatter under `[extra]`:

- `citation_style = "apa"`
- `bibliography = "references.bib"`

## Build and serve

- Generate `*.md` from all `*.src.md` files:

    ```bash
    bash scripts/build.sh
    ```

- Live rebuild + local server:

    ```bash
    # In one terminal, watch for changes and rebuild:
    bash scripts/watch.sh
    ```
    ```bash
    # In a separate terminal, serve with Zola:
    zola serve
    ```

## Citation style resolution order

Priority from highest to lowest:

1. Post frontmatter: `[extra] citation_style = "..."`
2. Site-level `config.toml` `[extra.persona].citation_style`
3. Theme config `themes/persona/config.toml` `[extra.persona].citation_style`

Bundled styles in `citation-style/`: `ieee`, `apa`. 
Custom styles can be added by placing `.csl` files in `citation-style/` and referencing them in frontmatter.

## Output and styling

The pipeline emits HTML citations and bibliography blocks so SCSS can style stable classes:

- `.citation`
- `.references`
- `.csl-entry`
- `.csl-left-margin`
- `.csl-right-inline`

Inline citations anchor to bibliography entries, and the bibliography heading is rendered inside the refs container as "Bibliography".
