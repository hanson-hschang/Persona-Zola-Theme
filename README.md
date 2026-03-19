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

[Demo](https://hanson-hschang.github.io/Persona-Zola-Theme/) • [Features](#-features) • [Showcase](#-showcase) • [Installation](#-installation) • [Configuration](#%EF%B8%8F-configuration) • [Citation](#-citation-pipeline) • [Structure](STRUCTURE.md) • [Troubleshooting](#-troubleshooting) • [Credits](#-credits)

</div>

## ✨ Features

- 🎨 **Modern Design**: Clean and professional layout easy for customization
- 📱 **Fully Responsive**: Optimized for desktop, tablet, and mobile devices
- ⚡️ **Fast Performance**: Lightweight and optimized for speed
- 📋 **Resume/CV**: Dedicated page for your resume or CV *(--upcoming feature--)*
- 🎭 **Portfolio Showcase**: Showcase your work with elegant project cards *(--upcoming feature--)*
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
Make sure you have [Zola installed](https://www.getzola.org/documentation/getting-started/installation/) before proceeding.

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

[Basic Setup](#basic-setup) • [Segment Configuration](#segment-configuration) • [Build & Serve](#build--serve)

</div>

### Basic Setup

1. **Copy the configuration and the landing page content** from the theme to get started quickly:

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

### Segment Configuration

Each segment can be configured with front matter. 
The theme supports three main segment types:
- **Plain segments** (for static text content like about)
- **Category segments** (for portfolios, projects, showcases)
- **Blog segments** (for blog posts and articles)

Here is how to set them up:

```toml
+++
title = "Title of the Segment"

[extra]
# Segment-specific icon for navigation (Bootstrap Icons)
icon_class = "bi bi-file-earmark-text"
# Display order (lower numbers appear first)
order = 1
# Segment type determines rendering approach
# options include "plain", "category", or "blog"
type = "plain"  
+++
```

For a complete walkthrough of configuration and customization, see the [`Begin with Persona` blog post](https://hanson-hschang.github.io/Persona-Zola-Theme/maps/private-soul/begin-with-persona/).

### Build & Serve

After completing the configuration, build and serve your site with Zola:

- Build the site:
  ```bash
  zola build
  ```

- Serve the site locally with live reload:
  ```bash
  zola serve
  ```

> If you are using the [Citation Pipeline](./README.md#-citation-pipeline), use `make build` and `make serve` instead to also process `.src.md` files.

## 📚 Citation Pipeline

This theme includes a built-in citation pipeline, designed to streamline academic-style writing in `.src.md` source files.

### Overview

The pipeline allows you to write naturally using citation keys (e.g., `[@cite-key]`) while automatically generating properly formatted citations and bibliographies during the build process. It integrates seamlessly with the site workflow, so you can focus on content rather than formatting.

### How It Works

- Write your content in `.src.md` files using Pandoc citation syntax  
- Store your references in a local `references.bib` file  
- A build script processes the source files and converts them into final Markdown file `.md` with formatted citations  
- The output is ready for rendering by Zola without any additional steps  

### Setup

1. Install dependencies:
    ```bash
    # macOS
    brew install pandoc watchexec

    # Ubuntu / Debian
    sudo apt install pandoc
    cargo install watchexec-cli
    ```
2.	Copy the scripts folder to your website root:
    ```bash
    cp -r themes/persona/scripts ./scripts
    ```
3. Create your post using with `.src.md` extension and use citation keys in the content:
    ```markdown
    This is a citation example [@key].
    ```
4. Add a `references.bib` file in the same directory.

### Build & Development
Use the provided script to build or watch for changes:
- Run a one-time build:
  ```bash 
  bash scripts/build.sh
  ```
- For live development:
  ```bash
  bash scripts/watch.sh
  ```
  In a separate terminal:
  ```bash
  zola serve
  ```

For a complete, real example (source + generated output + bibliography), see the [`Citation Pipeline Guide` post](https://hanson-hschang.github.io/Persona-Zola-Theme/maps/private-soul/citation-pipeline-guide/) with the [example source directory](https://github.com/hanson-hschang/Persona-Zola-Theme/tree/main/content/maps/private-soul/citation-pipeline-guide/).
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
- Check [STRUCTURE.md](STRUCTURE.md) for detailed theme architecture and organization
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


---

<div align="center">

**[⭐ Star this repository](https://github.com/hanson-hschang/Persona-Zola-Theme) if you find it helpful!**

</div>
