<div align="center">

# `Persona` [Zola](https://www.getzola.org/) Theme

**a modern, responsive and lightweight theme for resume, portfolio, and blog**

[![pagespeed report](pagespeed-report.svg)](https://pagespeed.web.dev/)

<img alt="code-size" src="https://img.shields.io/github/languages/code-size/hanson-hschang/Persona-Zola-Theme">
<img alt="repo-size" src="https://img.shields.io/github/repo-size/hanson-hschang/Persona-Zola-Theme">
<img alt="GitHub Issues" src="https://img.shields.io/github/issues/hanson-hschang/Persona-Zola-Theme">
<img alt="GitHub Created At" src="https://img.shields.io/github/created-at/hanson-hschang/Persona-Zola-Theme">
<img alt="activity" src="https://img.shields.io/github/last-commit/hanson-hschang/Persona-Zola-Theme">
<img alt="Website" src="https://img.shields.io/website?url=https%3A%2F%2Fhanson-hschang.github.io%2FPersona-Zola-Theme">
<img alt="GitHub Release" src="https://img.shields.io/github/v/release/hanson-hschang/Persona-Zola-Theme">

[Demo](https://hanson-hschang.github.io/Persona-Zola-Theme/) • [Features](#-features) • [Showcase](#-showcase) • [Installation](#-installation) • [Configuration](#%EF%B8%8F-configuration) • [Academic Projects](docs/academic-projects.md) • [Citation](#-citation-pipeline) • [Architecture](ARCHITECTURE.md) • [Troubleshooting](#-troubleshooting) • [Credits](#-credits)

</div>

## ✨ Features

- 🎨 **Modern Design**: Clean and professional layout easy for customization
- 📱 **Fully Responsive**: Optimized for desktop, tablet, and mobile devices
- ⚡️ **Fast Performance**: Lightweight and optimized for speed
- 📋 **Resume/CV**: Dedicated page for your resume or CV *(--upcoming feature--)*
- 🎭 **Portfolio Showcase**: Showcase your work with elegant project cards *(--upcoming feature--)*
- 🔬 **Academic Project Pages**: Research landing pages with authors, resource links, media galleries, posters, and copyable BibTeX
- 📝 **Blog with $\TeX$ and Citations**: Built-in blog functionality with equation and bibliography support
- 📧 **Contact Forms**: Integrated contact form email support
- 🔍 **Search Ready**: Built-in search index generation *(--upcoming feature--)*


## 🌟 Showcase

Using `Persona` for your site? 
We'd love to see it! 
Submit a Pull Request to add your site to our showcase.

- [Show Your Site](#-showcase) - Add your site with us!
- [Hanson.HSChang](https://hanson-hschang.github.io/) - Personal website of Heng-Sheng Chang

## 🚀 Installation

This is a Zola theme.
Make sure you have [Zola 0.23 or newer installed](https://www.getzola.org/documentation/getting-started/installation/) before proceeding.

After [initializing your Zola site](https://www.getzola.org/documentation/getting-started/overview/#initialize-site), the easiest way to install the theme is to add it as a git submodule to your `themes` directory:

```bash
# Navigate to your Zola site directory
cd your-zola-site

# Add the theme as a submodule
git submodule add https://github.com/hanson-hschang/Persona-Zola-Theme.git themes/persona
```

To update the theme:

```bash
# Update the submodule
git submodule update --init --recursive
```

## ⚙️ Configuration

<div align="center">

[Basic Setup](#basic-setup) • [Segment Front Matter](#segment-front-matter) • [Build & Serve](#build--serve)

</div>



### Basic Setup

1. **Copy the configuration and the landing page content** from the theme to your website root to get started quickly:

    ```bash
    # Copy the configuration
    cp themes/persona/config.toml config.toml

    # Copy the landing page content
    cp themes/persona/content/_index.md content/_index.md
    ```

2. **Enable the theme** by adding the following line at the beginning of your `config.toml` file:

    ```toml
    theme = "persona"
    ```

3. **Use Persona media components** inside Markdown content when you need theme-provided image handling.
   Persona targets Zola 0.23+ and uses Tera 2 components, so component calls use angle-bracket syntax:

    ```tera
    {{ <media.image page={page} path="img/example.png" width={700} alt="Example image" /> }}
    ```

### Segment Front Matter

The theme supports three main segment types:
- **Plain segments** (for static text content like about)
- **Category segments** (for portfolios, projects, showcases)
- **Blog segments** (shared lists for blog posts, articles, and academic project pages)

The `projects` segment type remains available as an alias for the shared blog list.

<details>
<summary>
Each segment is configured with front matter. 
Expand to see the details. 
</summary>

```toml
+++
title = "Title of the Segment"

[extra]
# Segment-specific icon for navigation (Bootstrap Icons)
icon_class = "bi bi-file-earmark-text"
# Display order (lower numbers appear first)
order = 1
# Segment type determines rendering approach
# options include "plain", "category", or "blog" ("projects" is a blog alias)
type = "plain"  
+++
```

</details>

> [!TIP]
> For a complete walkthrough of configuration and customization, see the [Begin with Persona](https://hanson-hschang.github.io/Persona-Zola-Theme/maps/private-soul/begin-with-persona/) blog post.



### Build & Serve

After completing the setup, build and serve your site with Zola:

| |terminal command| note|
|---|---|---|
|Build the site|```zola build```|site build under `public/`|
|Serve the site|```zola serve```|locally with live reload|

> [!NOTE]
> If you are using the [Citation Pipeline](#-citation-pipeline), use `make build` and `make serve` instead to also process `.src.md` files.

### Academic Project Pages

Set `template = "project.html"` on a Markdown page to create a dedicated research page. Add optional research details under `[extra.project]`; write the main article in Markdown below the front matter.

```toml
+++
title = "Your research project"
description = "A short summary for search results and link previews."
date = 2026-09-21
template = "project.html"

[extra.project]
subtitle = "A concise statement of the contribution"
venue = "Conference 2026"
authors = [{ name = "Alex Researcher", affiliations = "1" }]
affiliations = [{ id = "1", name = "Example University" }]
links = [{ name = "Paper", url = "paper.pdf", icon_class = "bi bi-file-earmark-pdf" }]
abstract = "Explain the research question, approach, and findings."
+++

## Method

Describe your work here.
```

Use a page bundle such as `content/maps/public-self/my-project/index.md` and put its images and PDFs alongside it. A project page can live alongside ordinary posts in a blog section; its explicit `template` selects the research layout. Relative resource paths follow the rendered page URL; `/` paths respect the site's configured base URL, including deployment subpaths.

The [academic project guide](docs/academic-projects.md) covers every field, reusable media components, and URL rules. The [Field Notes example](content/maps/public-self/field-notes/index.md) in [Public Self](content/maps/public-self/_index.md) provides a complete starting point. The layout and Sass are original Persona implementations, using the theme's existing typography, colors, spacing, and breakpoints.

Use `type = "blog"` in the parent section's `[extra]` table to list posts and projects with the shared entry template. The home page shows up to three items in each list and links to the complete section when more are available. This limit applies to category subsection cards and blog/project entry lists. Change it in your site's `config.toml`:

```toml
[extra.persona]
home_items_limit = 3
```

The default is `3` when the setting is omitted or negative. Set it to `0` to show only the **View all** link for each nonempty collection. Full section pages remain unlimited. Set each page's `[extra.project].thumbnail` to a colocated image, or let the listing use its teaser image (or video poster). See the guide for the section setup and ordering.

Projects and blog posts share one entry template with optional thumbnails, dates, and subtitles. The top-level `date` appears on project pages as well as in their lists. Set `subtitle` under `[extra.project]` for projects or under `[extra]` for blog posts to show it on both the detail page and its list entry. Blog entries also accept `thumbnail` and `thumbnail_alt` under `[extra]`.

To keep a project accessible by its URL but hide it from automatic home-page, blog/project, taxonomy, and Recent Posts lists, set `draft = true` under `[extra.project]` in its Markdown front matter. Omit it or set it to `false` to list the project. Use this theme flag rather than Zola's top-level draft flag, which excludes a page from normal builds.

## 📚 Citation Pipeline

<div align="center">

[How It Works](#how-it-works) • [Setup](#setup) • [Build & Write](#build--write)

</div>

The pipeline allows you to write naturally using citation keys from the bibliography file while automatically generating properly formatted references during the build process. 
It integrates seamlessly with the site workflow, so you can focus on content rather than formatting.

### How It Works

- Write your post content in `.src.md` files using [Pandoc citation syntax](https://pandoc.org/demo/example33/8.20-citation-syntax.html)  
- Store your references in the `references.bib` file in the same directory as your post
- A build script processes the source files and converts them into final Markdown file `.md` with formatted citations  
- The output is ready for rendering without any additional steps  

### Setup

1. Install dependencies:
    ```bash
    # macOS
    brew install pandoc watchexec

    # Ubuntu / Debian
    sudo apt install pandoc
    cargo install watchexec-cli
    ```
2.	Change directory to your website root and copy the `scripts` folder and `Makefile` from the theme:
    ```bash
    cp -r themes/persona/{scripts,Makefile} .
    ```
3. Ensure source and bibliography files are ignored by Zola in `config.toml` to prevent them from being processed as regular content:
    ```toml
    ignored_content = ["*.src.md", "*.bib", "*.csl"]
    ```
4. Create your post with a `.src.md` extension and use citation keys in the content:
    ```markdown
    This is a citation example [@cite-key].
    ```
5. Add a `references.bib` file in the same directory.

The citation preprocessor resolves CSL files in this priority order:

1. Per-post `[extra].citation_style`, resolved as `citation-style/<value>.csl`
2. Local `style.csl` in the same directory as the `.src.md` file
3. Site-level `config.toml` `[extra].citation_style`, or Persona-compatible `[extra.persona].citation_style`
4. Theme-level `themes/persona/theme.toml` `[extra].citation_style`, or `themes/persona/config.toml` `[extra.persona].citation_style`
5. Exit with an error when citation processing needs a CSL and none can be resolved

### Build & Write
Use the provided `Makefile` to build or serve your site locally with automatic processing of `.src.md` files:

| |terminal command| note|
|---|---|---|
|Build the site|`make build`|site build under `public/`|
|Serve the site|`make serve`|locally with live reload|


> [!TIP]
> For a complete example (source + bibliography + generated output), see the [Citation Pipeline Guide](https://hanson-hschang.github.io/Persona-Zola-Theme/maps/private-soul/citation-pipeline-guide/) blog post with the [example source directory](https://github.com/hanson-hschang/Persona-Zola-Theme/tree/main/content/maps/private-soul/citation-pipeline-guide/).
This pipeline is ideal for writing technical, research-oriented, or reference-heavy content with minimal friction.

## 🆘 Troubleshooting

### Common Issues

- **Theme not loading:**
  - Ensure `theme = "persona"` is set at the first line of `config.toml`
  - Check that the theme is in the correct directory: `themes/persona/`

- **Navigation not working:**
  - Ensure `[extra].order` field is set correctly in the front matter
  - Check `[extra].type` is correctly specified in the front matter

- **Contact form not working:**
  - Verify `web3form_public_key` is set in configuration
  - Check [Web3Forms documentation](https://docs.web3forms.com/) for setup

### Getting Help
- Read the [Zola documentation](https://www.getzola.org/documentation/)
- Check [ARCHITECTURE.md](ARCHITECTURE.md) for detailed theme architecture and organization
- Report issues or request features by [contributing](CONTRIBUTING.md) on GitHub


## 🙏 Credits

`Persona` is built with and inspired by:

- [**Zola**](https://www.getzola.org/) - A fast static site generator
- [**Bootstrap**](https://getbootstrap.com/) - CSS framework for responsive design
- [**Web3Forms**](https://web3forms.com/) - Contact form service
- [**KaTeX**](https://katex.org/) - Fast math typesetting library
- [**Pandoc**](https://pandoc.org/) - Universal document converter for citation processing
- [**Bootstrap Icons**](https://icons.getbootstrap.com/) - Icon library
- [**Academicons**](https://jpswalsh.github.io/academicons/) - Academic icons
- [**AOS (Animate On Scroll)**](https://michalsnik.github.io/aos/) - Animation library
- [**Google Fonts**](https://fonts.google.com/) - Font library
- [**Dynamic Badges**](https://shields.io/) - Customizable badges
- [**PageSpeed Insights**](https://github.com/lowlighter/metrics/tree/master/source/plugins/pagespeed) - Automated performance reporting
- [**GitHub**](https://github.com/features) - [Actions (CI/CD)](https://github.com/features/actions) • [Pages (Hosting Website)](https://docs.github.com/en/pages/getting-started-with-github-pages) • [Copilot (AI Agent)](https://docs.github.com/en/copilot/get-started/what-is-github-copilot)
- [**Anthropic**](https://www.anthropic.com/) - [Claude](https://claude.ai/) • [Claude Code](https://code.claude.com/docs/en/overview)
- [**Google**](https://cloud.google.com/ai/gemini) - [Gemini](https://gemini.google.com/) • [Gemini CLI](https://geminicli.com/)
- [**OpenAI**](https://openai.com/) - [ChatGPT](https://chat.openai.com/) • [Codex](https://openai.com/codex/)
- [**BootstrapMade Templates**](https://bootstrapmade.com/) - [Active](https://bootstrapmade.com/demo/Active) • [MyResume](https://bootstrapmade.com/demo/MyResume) • [UpConstruction](https://bootstrapmade.com/demo/UpConstruction)
- [**Zola Themes**](https://www.getzola.org/themes/) - [Mabuya](https://mabuya.vercel.app/) • [Vonge](https://pascal-berrang.de/vonge-zola-theme/) • [Zluinav](https://harrymkt.github.io/zluinav/)
- [**Academic Project Page Template**](https://github.com/eliahuhorwitz/Academic-project-page-template) - Feature inspiration for academic project pages; Persona's layout, styling, and interactions are implemented independently


---

<div align="center">

**[⭐ Star this repository](https://github.com/hanson-hschang/Persona-Zola-Theme) if you find it helpful!**

</div>
