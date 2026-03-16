# Zola Theme Structure

This document describes the organization and structure of the codebase.

## Directory Structure

```
.
├── sass/                      # Sass source files (compiled by Zola natively)
│   └── assets/
│       └── stylesheet/            # Compiled output → public/assets/stylesheet/
│           ├── _variables.scss       # SCSS vars + re-exported CSS custom properties
│           ├── _mixins.scss          # Shared mixins (breakpoints, flex, transitions)
│           ├── _custom.scss          # User custom overrides (included last)
│           ├── base/
│           │   ├── _base.scss        # Core base styles
│           │   ├── _footer.scss      # Footer styles
│           │   └── _preloader.scss   # Page preloader styles
│           ├── layout/
│           │   ├── _navigation.scss        # Navigation (standard pages)
│           │   ├── _navigation-index.scss  # Navigation (home page)
│           │   ├── _section.scss           # Section container styles
│           │   └── _breadcrumbs.scss       # Breadcrumb / page-title styles
│           ├── pages/
│           │   ├── _hero.scss        # Hero section styles (home page)
│           │   ├── _contact.scss     # Contact section styles
│           │   └── _plain.scss       # Plain section content styles
│           ├── components/
│           │   ├── _category.scss    # Category section styles
│           │   ├── _blog.scss        # Blog listing styles
│           │   ├── _post.scss        # Blog post content styles
│           │   └── _widgets.scss     # Sidebar widget styles
│           ├── main.scss             # Entry point: all pages (→ main.css)
│           ├── home.scss             # Entry point: home page (→ home.css)
│           ├── page-plain.scss       # Entry point: plain sections (→ page-plain.css)
│           ├── page-category.scss    # Entry point: category sections (→ page-category.css)
│           ├── page-blog.scss        # Entry point: blog sections (→ page-blog.css)
│           ├── post.scss             # Entry point: blog posts (→ post.css)
│           └── page-404.scss         # Entry point: 404 error page (→ page-404.css)
├── static/                    # Static assets
│   ├── assets/               # Theme-specific assets
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

- **post.html**: Post template
  - Dedicated template for blog and portfolio posts
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

## Sass / CSS Organization

### How Zola Compiles Sass

Zola compiles Sass natively — no external build tool or CLI is needed:

- Any `.scss` file in `sass/` **without** a `_` prefix is compiled to a `.css` file at the same relative path under `public/`.
- Files prefixed with `_` are **partials** — they are never compiled directly; they are included via `@use` from an entry point.
- No `config.toml` changes are needed — compilation happens automatically on `zola build` and `zola serve`.

Entry point files live under `sass/assets/stylesheet/`, so compiled output lands at `public/assets/stylesheet/`. Templates reference them as `/assets/stylesheet/<name>.css`.

### Structure

Sass source files in `sass/assets/stylesheet/`:

```
stylesheet/
├── _variables.scss              # Design tokens: SCSS vars + CSS custom properties (:root)
├── _mixins.scss                 # Shared mixins: respond-to, flex-center, transition
├── _custom.scss                 # User overrides — included last in every entry point
│
├── base/
│   ├── _base.scss               # Core styles (scroll, links, headings, AOS)
│   ├── _footer.scss             # Footer
│   └── _preloader.scss          # Page preloader
│
├── layout/
│   ├── _navigation.scss         # Sticky header + nav menu (standard pages)
│   ├── _navigation-index.scss   # Left-sidebar icon nav (home page only)
│   ├── _section.scss            # Section container and title
│   └── _breadcrumbs.scss        # Page title / breadcrumbs bar
│
├── pages/
│   ├── _hero.scss               # Hero section (home page only)
│   ├── _contact.scss            # Contact form and info
│   └── _plain.scss              # Plain section content
│
├── components/
│   ├── _category.scss           # Category card listing
│   ├── _blog.scss               # Blog post listing
│   ├── _post.scss               # Individual blog post
│   └── _widgets.scss            # Sidebar widgets
│
└── [entry points — no _ prefix; each compiles to public/assets/stylesheet/<name>.css]
    ├── main.scss                 # All pages
    ├── home.scss                 # Home / index page
    ├── page-plain.scss           # Plain section + page template
    ├── page-category.scss        # Category section pages
    ├── page-blog.scss            # Blog listing section pages
    ├── post.scss                 # Individual blog post pages
    └── page-404.scss             # 404 error page
```

### CSS Loading Strategy

Each template loads only the CSS it needs:

| Template | Entry point loaded | Contents |
|---|---|---|
| `base.html` (all pages) | `main.css` | variables, base, footer, preloader, custom |
| `index.html` | `home.css` | nav-index, hero, section, plain, category, contact |
| `section.html` (plain) | `page-plain.css` | navigation, section, plain |
| `section.html` (category) | `page-category.css` | navigation, section, category |
| `section.html` (blog) | `page-blog.css` | navigation, section, blog, breadcrumbs |
| `post.html` | `post.css` | navigation, breadcrumbs, post, widgets |
| `page.html` | `page-plain.css` | navigation, section, plain |
| `404.html` | `page-404.css` | navigation, section, plain, contact |

### Design Tokens

All customizable theme values start in `_variables.scss` as **SCSS variables**, then are re-exported as **CSS custom properties** inside `:root` so they remain accessible at runtime.

**Color variables** (e.g. `$color-accent: #0563bb` → `--accent-color`):
- Global colors: background, text, headings, accent, surface, contrast
- Navigation colors
- Header colors

**Typography** (e.g. `$font-default: "Roboto", …` → `--default-font`):
- Font families: default, heading, navigation
- Font sizes: normal, footer, heading, subtitle, title

**Dimensions** (e.g. `$nav-icon-size: 56px` → `--nav-icon-size`):
- Navigation dimensions, border radius, button sizes and positions

**Spacing** (e.g. `$spacing-md: 1.5rem` → `--spacing-md`):
- Consistent scale: `xxs` · `xs` · `sm` · `md` · `lg` · `xl` · `xxl`

**Animation** (e.g. `$transition-hover-time: 0.3s` → `--transition-hover-time`):
- Transition timing

## JavaScript Organization

JavaScript files in `static/assets/script/`:

- **home.js**: Home page functionality
  - Smooth scrolling
  - Mobile navigation
  - Preloader
  - AOS initialization
  - Typed.js for text animation

## Development Workflow

1. **Check theme**: `zola check`
2. **Build**: `zola build`
3. **Serve locally**: `zola serve`
4. **Test changes**: Navigate to http://127.0.0.1:1111

## Adding New Features

### Adding a New Section Type

1. Create SCSS partial: `sass/assets/stylesheet/components/_new-type.scss`
2. Create a new entry point (e.g. `sass/assets/stylesheet/page-new-type.scss`) that `@use`s the partial
3. Add rendering macro in `templates/macros/section.html`
4. Update `section.html` to load `page-new-type.css` for the new type
5. Document in README.md

### Adding a New Component

1. Create partial: `templates/partials/component-name.html`
2. Create SCSS partial: `sass/assets/stylesheet/components/_component-name.scss`
3. `@use` the new partial in the relevant entry point(s)
4. Include the HTML partial in the appropriate template
5. Document usage

### Adding a New Macro

1. Add to appropriate macro file in `templates/macros/`
2. Document parameters and usage
3. Import in templates where needed

## File Naming Conventions

- **Templates**: lowercase with hyphens (e.g., `post.html`)
- **SCSS partials**: `_` prefix, lowercase with hyphens (e.g., `_post.scss`)
- **SCSS entry points**: no `_` prefix, lowercase with hyphens (e.g., `post.scss`)
- **JavaScript**: lowercase with hyphens (e.g., `home.js`)
- **Macros**: lowercase, descriptive names
- **Variables**: CSS custom properties with `--` prefix, kebab-case

## Best Practices

1. **Separation of Concerns**: Keep logic in macros, styling in CSS, structure in templates
2. **Reusability**: Use macros and partials for repeated patterns
3. **Conditional Loading**: Only load CSS/JS needed for specific pages
4. **Sass Variables**: Define all design tokens in `_variables.scss`; use SCSS vars at compile time and CSS custom properties at runtime
5. **Documentation**: Update this file when adding new components or changing structure
6. **Testing**: Test on multiple devices and browsers after changes

## Dependencies

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
- [theme.toml](theme.toml) - Theme metadata and configuration
- [config.toml](config.toml) - Configuration template for user site
- [Zola Documentation](https://www.getzola.org/documentation/) - Zola reference
