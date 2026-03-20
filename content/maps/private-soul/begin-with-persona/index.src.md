+++
title = 'Begin with Persona'
date = 2025-03-17
draft = false
[taxonomies]
tags = ['website', 'blog']
categories = ['blogs', 'private-soul']
[extra]
excerpt = """
A step-by-step tutorial on how to start a website using the Persona theme: from installation and configuration to segment setup and full theme customization.
"""
bibliography = "references.bib"
+++


This is a step-by-step tutorial on how to start a website using the Persona, a Zola theme [@zolathemes].
It covers the basics of setting up your site, creating content, and customizing the appearance to make it your own.

## Setting Up Your Site

After [installing Persona](https://github.com/hanson-hschang/Persona-Zola-Theme#-installation), configure your `config.toml`:

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

Modify the landing page content in `content/_index.md`:

```toml
+++
title = "Presented Site Name"
template = "index.html"
[extra]
icon_class = "bi bi-house"
subtitles = "Item 1, Item 2, Item 3"
+++
```

Also update your assets in `static/assets/img/`:

- [hero image](https://en.wiktionary.org/wiki/hero_image): `background.jpg`
- [favicon](https://en.wikipedia.org/wiki/Favicon): `favicon.ico`
- [apple touch icon](https://developer.apple.com/library/archive/documentation/AppleApplications/Reference/SafariWebContent/ConfiguringWebApplications/ConfiguringWebApplications.html): `apple-touch-icon.png`

## Creating Content

Once your site is configured, you can start creating content by adding Markdown files to the `content` directory.
Each file represents a page or blog post, and you can use frontmatter to specify metadata such as the title, date, tags, and categories.

## Customizing Appearance

The Persona theme provides extensive options to customize colors and fonts by overriding CSS variables in `sass/assets/stylesheet/_custom.scss` without modifying the core theme files.
For example, to change the accent color, heading color, and title font size, you can use the following CSS:

```css
/* sass/assets/stylesheet/_custom.scss */
:root {
  --color-accent: #FF5F05;   /* Override accent color to vibrant orange */
  --color-heading: #13294B;  /* Override heading color to dark blue */
  --font-size-title: 72px;   /* Increase title font size for more impact */
}
```

**Available Customization Variables:**

Colors:

- `--background-color`: Background color for the entire website
- `--default-color`: Default text color
- `--heading-color`: Color for headings and titles
- `--accent-color`: Brand color for buttons, links, and highlights
- `--surface-color`: Background for cards and boxed elements
- `--contrast-color`: Text color for use against accent colors

Typography:

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

See `sass/assets/stylesheet/_variables.scss` for the complete list of customizable variables with detailed descriptions (the compiled CSS is emitted under `public/assets/stylesheet/` at build time).

## Conclusion

Starting a website with the Persona theme is a great way to share your thoughts and ideas with the world.
With its user-friendly setup and extensive customization options, you can create a unique and engaging site that reflects your personality and style.
