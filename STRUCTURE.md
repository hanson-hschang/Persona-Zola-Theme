# Persona Theme Structure Documentation

This document describes the organization and structure of the Persona Zola theme codebase.

## Directory Structure

```
.
├── static/                    # Static assets
│   ├── assets/               # Theme-specific assets
│   │   ├── css/             # Stylesheets
│   │   ├── js/              # JavaScript files
│   │   └── img/             # Images (favicons, backgrounds)
│   └── vendor/              # Third-party libraries
│       ├── bootstrap/       # Bootstrap framework
│       ├── bootstrap-icons/ # Icon library
│       ├── aos/            # Animate On Scroll
│       ├── glightbox/      # Lightbox library
│       ├── swiper/         # Slider library
│       ├── academicons/    # Academic icons
│       └── typed.js/       # Text typing animation
├── templates/               # Zola templates
│   ├── base.html           # Base layout template
│   ├── index.html          # Home page template
│   ├── section.html        # Section page template
│   ├── page.html           # Single page template
│   ├── post.html           # Blog post template
│   ├── 404.html            # Error page template
│   ├── macros/             # Reusable template macros
│   ├── partials/           # Reusable template components
│   ├── shortcodes/         # Content shortcodes
│   ├── categories/         # Category taxonomy templates
│   └── tags/               # Tag taxonomy templates
├── content/                 # Site content (user-created)
├── config.toml             # Site configuration
├── theme.toml              # Theme metadata
└── README.md               # Theme documentation
```

## Template Organization

### Core Templates

Located in `templates/` root:

- **base.html**: Base layout inherited by all pages
  - Defines HTML structure, head section, navigation, footer
  - Includes CSS/JS dependencies
  - Contains blocks for extending

- **index.html**: Home/landing page template
  - Extends base.html
  - Displays hero section
  - Renders all sections with `order > 0` from front matter
  - Shows contact section

- **section.html**: Section page template
  - Handles three section types: plain, category, blog
  - Conditionally loads type-specific CSS and macros

- **page.html**: Single page template
  - For standalone pages
  - Plain content rendering

- **post.html**: Blog post template
  - Dedicated template for blog posts
  - Includes breadcrumbs, widgets, metadata
  - Supports KaTeX for mathematical expressions

- **404.html**: Error page template
  - Custom 404 not found page

### Template Macros

Located in `templates/macros/`:

- **render.html**: Core rendering utilities
  - `post_entry()`: Renders blog post entries
  - `section_title()`: Renders section titles
  - `text_content()`: Renders text content
  - `cards()`: Renders card layouts
  - And more...

- **section.html**: Section rendering logic
  - `populate()`: Populates section content
  - `plain()`: Renders plain sections
  - `category()`: Renders category sections
  - `blog()`: Renders blog sections

- **blog.html**: Blog-specific macros
  - Blog listing and pagination logic

- **debug.html**: Debug utilities
  - Development helpers

### Template Partials

Located in `templates/partials/`:

Reusable UI components:
- **navigation.html**: Main navigation menu
- **hero.html**: Hero section for home page
- **footer.html**: Site footer
- **contact.html**: Contact section wrapper
- **contact-form.html**: Contact form component
- **contact-info.html**: Contact information display
- **head-title.html**: Dynamic page title generation
- **social-icon.html**: Social media icon rendering

### Shortcodes

Located in `templates/shortcodes/`:

Content shortcodes for use in markdown:
- **image.html**: Enhanced image rendering with captions
- **media.html**: Embedded media content

### Taxonomy Templates

**Categories** (`templates/categories/`):
- **list.html**: Category listing page
- **single.html**: Single category page

**Tags** (`templates/tags/`):
- **list.html**: Tag listing page  
- **single.html**: Single tag page

## CSS Organization

### Structure

CSS files in `static/assets/css/`:

```
css/
├── theme.css              # Customization variables (colors, fonts, dimensions)
├── base.css               # Core base styles
├── footer.css             # Footer styles
├── hero.css               # Hero section styles
├── navigation.css         # Navigation menu styles (standard pages)
├── navigation-index.css   # Navigation menu styles (home page)
├── preloader.css          # Page preloader styles
├── breadcrumbs.css        # Breadcrumb navigation styles
├── section.css            # Section container styles
├── plain.css              # Plain section content styles
├── category.css           # Category section styles
├── blog.css               # Blog listing styles
├── post.css               # Blog post content styles
├── contact.css            # Contact section styles
├── widgets.css            # Sidebar widget styles
└── custom.css             # User custom styles (loaded last)
```

### CSS Loading Strategy

CSS files are loaded conditionally based on template type:

**Base Template** (loaded on all pages):
- theme.css
- base.css
- footer.css
- preloader.css
- custom.css

**Home Page** (index.html):
- navigation-index.css
- hero.css
- section.css
- plain.css
- category.css
- contact.css

**Section Pages** (section.html):
- navigation.css
- section.css
- Type-specific: plain.css, category.css, or blog.css + breadcrumbs.css

**Blog Posts** (post.html):
- navigation.css
- post.css
- breadcrumbs.css
- widgets.css

**Regular Pages** (page.html):
- navigation.css
- plain.css
- section.css

**Error Pages** (404.html):
- navigation.css
- section.css
- plain.css
- contact.css

### CSS Variables

All customizable theme values are defined in `theme.css`:

**Color Variables:**
- Global colors (background, text, headings, accent)
- Navigation colors
- Header colors

**Typography:**
- Font families (default, heading, navigation)
- Font sizes (normal, footer, heading, subtitle, title)

**Dimensions:**
- Navigation dimensions
- Border radius
- Button sizes and positions

**Spacing:**
- Consistent spacing scale (--spacing-xxs through --spacing-xxl)

**Animation:**
- Transition timing and effects

## JavaScript Organization

JavaScript files in `static/assets/js/`:

- **home.js**: Home page functionality
  - Smooth scrolling
  - Mobile navigation
  - Preloader
  - AOS initialization
  - Typed.js for text animation

## Customization Guide

### Method 1: Direct Modification
Edit `static/assets/css/theme.css` to change theme defaults.

### Method 2: CSS Override (Recommended)
Use `static/assets/css/custom.css` (included in the theme) to override theme defaults:

```css
/* In static/assets/css/custom.css */
:root {
  --accent-color: #your-color;
  --heading-font: "Your Font", sans-serif;
}
```

The `custom.css` file is automatically loaded after all theme CSS files, so your customizations will take precedence.

## Development Workflow

1. **Check theme**: `zola check`
2. **Build**: `zola build`
3. **Serve locally**: `zola serve`
4. **Test changes**: Navigate to http://127.0.0.1:1111

## Adding New Features

### Adding a New Section Type

1. Create CSS file: `static/assets/css/new-type.css`
2. Add rendering macro in `templates/macros/section.html`
3. Update section.html to include new type
4. Document in README.md

### Adding a New Component

1. Create partial: `templates/partials/component-name.html`
2. Create CSS: `static/assets/css/component-name.css`
3. Include in appropriate template
4. Document usage

### Adding a New Macro

1. Add to appropriate macro file in `templates/macros/`
2. Document parameters and usage
3. Import in templates where needed

## File Naming Conventions

- **Templates**: lowercase with hyphens (e.g., `post.html`)
- **CSS files**: lowercase with hyphens (e.g., `post.css`)
- **JavaScript**: lowercase with hyphens (e.g., `home.js`)
- **Macros**: lowercase, descriptive names
- **Variables**: CSS custom properties with `--` prefix, kebab-case

## Best Practices

1. **Separation of Concerns**: Keep logic in macros, styling in CSS, structure in templates
2. **Reusability**: Use macros and partials for repeated patterns
3. **Conditional Loading**: Only load CSS/JS needed for specific pages
4. **CSS Variables**: Use theme.css for all customizable values
5. **Documentation**: Update this file when adding new components or changing structure
6. **Testing**: Test on multiple devices and browsers after changes

## Dependencies

### Required
- Zola (v0.20.0+)

### Included Vendors
- Bootstrap 5.3.x
- Bootstrap Icons
- AOS (Animate On Scroll)
- GLightbox
- Swiper
- Academicons
- Typed.js
- KaTeX (loaded conditionally for math content)

## Related Documentation

- [README.md](README.md) - Main theme documentation
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- [config.toml](config.toml) - Configuration reference
- [Zola Documentation](https://www.getzola.org/documentation/) - Zola reference
