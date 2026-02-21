<div align="center">

# `Persona` [Zola](https://www.getzola.org/) Theme

![code-size](https://img.shields.io/github/languages/code-size/hanson-hschang/Persona-Zola-Theme)
![repo-size](https://img.shields.io/github/repo-size/hanson-hschang/Persona-Zola-Theme)
![GitHub Issues](https://img.shields.io/github/issues/hanson-hschang/Persona-Zola-Theme)
![GitHub Created At](https://img.shields.io/github/created-at/hanson-hschang/Persona-Zola-Theme)
![activity](https://img.shields.io/github/last-commit/hanson-hschang/Persona-Zola-Theme)
![Website](https://img.shields.io/website?url=https%3A%2F%2Fhanson-hschang.github.io%2FPersona-Zola-Theme)
![GitHub Release](https://img.shields.io/github/v/release/hanson-hschang/Persona-Zola-Theme)

**a modern, responsive and lightweight theme for resume, portfolio, and blog**

[![pagespeed report](pagespeed-report.svg)](https://pagespeed.web.dev/)

[Demo](https://hanson-hschang.github.io/Persona-Zola-Theme/) • [Features](#-features) • [Showcase](#-showcase) • [Installation](#-installation) • [Configuration](#%EF%B8%8F-configuration) • [Structure](STRUCTURE.md) • [Troubleshooting](#-troubleshooting) • [Credits](#-credits)

</div>

## ✨ Features

- 🎨 **Modern Design**: Clean and professional layout easy for customization
- 📱 **Fully Responsive**: Optimized for desktop, tablet, and mobile devices
- ⚡️ **Fast Performance**: Lightweight and optimized for speed
- 📋 **Resume/CV Section**: Dedicated section for your resume or CV *(--upcoming feature--)*
- 🎭 **Portfolio Showcase**: Showcase your work with elegant project sections *(--upcoming feature--)*
- 📝 **Blog with $\TeX$**: Built-in blog functionality with KaTeX support
- 📧 **Contact Forms**: Integrated contact form support with Web3Forms
- 🔍 **Search Ready**: Built-in search index generation *(--upcoming feature--)*


## 🌟 Showcase

Using `Persona` for your site? 
We'd love to see it! 
Submit a PR to add your site to our showcase.

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

3. **Customization**:

  - Configure site settings in your `config.toml`:

    ```toml
    # The URL this site will be built for
    base_url = "https://yourdomain.com"

    # The basic site information
    title = "Your Site Name"
    author = "Your Name"
    description = "Your personal resume, portfolio and blog"

    [extra]

    [extra.persona]
    # Note: landing page title and subtitles are configured in `content/_index.md`

    # Social links
    social_links = [
      { name = "GitHub", url = "https://github.com/yourusername", icon_class = "bi bi-github" },
      { name = "LinkedIn", url = "https://linkedin.com/in/yourprofile", icon_class = "bi bi-linkedin" },
      { name = "Twitter-X", url = "https://x.com/yourusername", icon_class = "bi bi-twitter-x" },
    ]

    # Contact information
    contact_infos = [
      { item = "_navigation", content = "Contact", icon_class = "bi bi-chat-text" }, # Special item for header navigation (REQUIRED)
      { item = "Name", content = "Your Name", icon_class = "bi bi-person" },
      { item = "Location", content = "Your City, Country", icon_class = "bi bi-geo-alt" },
      { item = "Email", content = "your.email@example.com", icon_class = "bi bi-envelope" },
      { item = "Phone", content = "+0 (123) 456-7890", icon_class = "bi bi-phone" },
    ]
    ```

  - Modify landing page content in `content/_index.md`:

    ```toml
    +++
    title = "Presented Site Name"
    template = "index.html"
    
    [extra]
    subtitles = "Item 1, Item 2, Item 3"
    +++
    ```

  - Update your assets in `static/assets/img/`:
    - [hero image](https://en.wiktionary.org/wiki/hero_image): `background.jpg`
    - [favicon](https://en.wikipedia.org/wiki/Favicon): `favicon.ico`
    - [apple touch icon](https://developer.apple.com/library/archive/documentation/AppleApplications/Reference/SafariWebContent/ConfiguringWebApplications/ConfiguringWebApplications.html): `apple-touch-icon.png`

### Section Configuration

Each section can be configured with front matter. 
The theme supports three main section types:
- **Plain sections** (for static text content like about)
- **Category sections** (for portfolios, projects, showcases)
- **Blog sections** (for blog posts and articles)

Here is how to set them up:

```toml
+++
title = "Title of the Section"

[extra]
# Section-specific icon for navigation (Bootstrap Icons)
icon_class = "bi bi-person"
# Display order (lower numbers appear first)
order = 1
# Section type determines rendering approach
type = "type"  # "plain", "category", or "blog"
+++
```

### Theme Customization

The theme provides extensive options to customize colors and fonts through overriding CSS variables in `static/assets/css/custom.css` without modifying the core theme files.
For example, to change the accent color, heading color, and title font size, you can use the following CSS:

```css
/* static/assets/css/custom.css */
:root {
  --accent-color: #FF5F05;   /* Override accent color to vibrant orange */
  --heading-color: #13294B;  /* Override heading color to dark blue */
  --title-font-size: 72px;   /* Increase title font size for more impact */
}
```

<details>
<summary>Available Customization Variables</summary>

**Colors:**
- `--background-color`: Background color for the entire website
- `--default-color`: Default text color
- `--heading-color`: Color for headings and titles
- `--accent-color`: Brand color for buttons, links, and highlights
- `--surface-color`: Background for cards and boxed elements
- `--contrast-color`: Text color for use against accent colors


**Typography:**
- Font Families
  - `--default-font`: Main font family for body text
  - `--heading-font`: Font family for headings
  - `--nav-font`: Font family for navigation
- Font Sizes
  - `--footer-font-size`: Footer text size (default: 14px)
  - `--normal-font-size`: Base font size (default: 16px)
  - `--subtitle-font-size`: Subtitle font size (default: 24px)
  - `--heading-font-size`: Base font size for heading (default: 32px)
  - `--title-font-size`: Base font size for title (default: 64px)

See `static/assets/css/theme.css` for the complete list of customizable variables with detailed descriptions.

</details>

## 🆘 Troubleshooting

### Common Issues

- **Theme not loading:**
  - Ensure `theme = "persona"` is set at the first line of `config.toml`
  - Check that the theme is in the correct directory: `themes/persona/`

- **Navigation not working:**
  - Ensure sections have proper front matter with `order` field
  - Check that section metadata `extra.type` is correctly specified

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
- [**Bootstrap Icons**](https://icons.getbootstrap.com/) - Icon library
- [**Academicons**](https://jpswalsh.github.io/academicons/) - Academic icons
- [**AOS (Animate On Scroll)**](https://michalsnik.github.io/aos/) - Animation library
- [**Google Fonts**](https://fonts.google.com/) - Font library
- [**Dynamic Badges**](https://shields.io/) - Customizable badges
- [**PageSpeed Insights**](https://github.com/lowlighter/metrics/tree/master/source/plugins/pagespeed) - Automated performance reporting
- [**GitHub**](https://github.com/features) - [Actions (CI/CD)](https://github.com/features/actions) • [Pages (Hosting Website)](https://docs.github.com/en/pages/getting-started-with-github-pages) • [Copilot (AI Agent)](https://docs.github.com/en/copilot/get-started/what-is-github-copilot)
- [**BootstrapMade Templates**](https://bootstrapmade.com/) - [Active](https://bootstrapmade.com/demo/Active) • [MyResume](https://bootstrapmade.com/demo/MyResume) • [UpConstruction](https://bootstrapmade.com/demo/UpConstruction)
- [**Zola Themes**](https://www.getzola.org/themes/) - [Mabuya](https://mabuya.vercel.app/) • [Vonge](https://pascal-berrang.de/vonge-zola-theme/) • [Zluinav](https://harrymkt.github.io/zluinav/)


---

<div align="center">

**[⭐ Star this repository](https://github.com/hanson-hschang/Persona-Zola-Theme) if you find it helpful!**

</div>
