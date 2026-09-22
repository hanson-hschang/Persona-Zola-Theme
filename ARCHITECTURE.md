# Codebase Architecture

This document describes the architecture and organization of the Zola 0.23+ theme codebase, including Tera 2 templates, Sass, JavaScript, and development workflow.
It serves as a guide for contributors to understand how the theme is structured and how to add new features or make changes.

## Directory Structure

```
.
├── sass/                             # Sass source files (compiled by Zola natively)
│   └── assets/
│       └── stylesheet/               # Compiled output → public/assets/stylesheet/
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
│           │   ├── _segment.scss           # Segment container styles
│           │   └── _breadcrumbs.scss       # Breadcrumb / page-title styles
│           ├── pages/
│           │   ├── _hero.scss        # Hero section styles (home page)
│           │   ├── _contact.scss     # Contact section styles
│           │   ├── _project.scss     # Academic project page styles
│           │   └── _plain.scss       # Plain section content styles
│           ├── components/
│           │   ├── _category.scss    # Category section styles
│           │   ├── _blog.scss        # Shared blog/project listing styles
│           │   ├── _post.scss        # Blog post content styles
│           │   └── _widgets.scss     # Sidebar widget styles
│           ├── main.scss             # Entry point: all pages -> main.css
│           ├── home.scss             # Entry point: home page -> home.css
│           ├── page-plain.scss       # Entry point: plain sections -> page-plain.css
│           ├── page-category.scss    # Entry point: category sections -> page-category.css
│           ├── page-blog.scss        # Entry point: blog sections -> page-blog.css
│           ├── post.scss             # Entry point: blog posts -> post.css
│           ├── page-project.scss     # Entry point: academic projects -> page-project.css
│           ├── citations.scss        # Entry point: Pandoc citation output -> citations.css
│           └── page-404.scss         # Entry point: 404 error page -> page-404.css
├── static/                           # Static assets
│   ├── assets/                       # Theme-specific assets
│   │   ├── script/                   # JavaScript files
│   │   └── img/                      # Images (favicons, backgrounds)
│   └── vendor/                       # Third-party libraries
│       ├── bootstrap/                # Bootstrap framework
│       ├── bootstrap-icons/          # Icon library
│       ├── aos/                      # Animate On Scroll
│       ├── academicons/              # Academic icons
│       └── typed.js/                 # Text typing animation
├── templates/                        # Zola templates
│   ├── base.html                     # Base layout template
│   ├── index.html                    # Home page template
│   ├── section.html                  # Section page template
│   ├── page.html                     # Single page template
│   ├── post.html                     # Blog post template
│   ├── project.html                  # Academic project template
│   ├── 404.html                      # Error page template
│   ├── components/                   # Tera 2 reusable components
│   ├── partials/                     # Reusable template partials
│   ├── categories/                   # Category taxonomy templates
│   └── tags/                         # Tag taxonomy templates
├── content/                          # Site content (user-created)
├── config.toml                       # Site configuration
├── theme.toml                        # Theme metadata
└── README.md                         # Theme documentation
```

## Template Organization

### Core Templates

Located in `templates/` root:

- **base.html**: Base layout inherited by all pages
  - Defines HTML structure, head section, navigation, footer
  - Includes CSS/JS dependencies
  - Loads KaTeX CSS/JS through `partials/katex-css.html` and `partials/katex-js.html` when `page.extra.tex` is present
  - Contains blocks for extending

- **index.html**: Home/landing page template
  - Extends base.html
  - Displays hero section
  - Renders all sections with `order > 0` from front matter
  - Shows contact section

- **section.html**: Section page template
  - Handles plain, category, and blog section types, with projects retained as an alias for blog lists
  - Conditionally loads type-specific CSS and components
  - Contains the logic that previously lived in the root `segment.html` page template

- **page.html**: Single page template
  - For standalone pages
  - Plain content rendering

- **post.html**: Post template
  - Dedicated template for blog and portfolio posts
  - Includes breadcrumbs, widgets, metadata
  - Supports KaTeX for mathematical expressions
  - Loads `citations.css` for Pandoc citeproc output

- **project.html**: Academic project template
  - Selected with `template = "project.html"`; reads optional `page.extra.project` data
  - Renders authors, affiliations, resource links, teaser, abstract, article, gallery, video, poster, and BibTeX
  - Generates page metadata and scholarly citation tags
  - Inherits standard navigation and mobile toggle, with breadcrumbs based on section ancestry
  - Displays optional related-work links in a shared sidebar widget below the left contents navigation; below the content under the `lg` breakpoint
  - Overrides the base `preloader` block so research content is available without JavaScript
  - Loads `page-project.css`, AOS, `home.js`, and `project.js`; retains shared footer and conditional KaTeX support
  - See the [front matter and component guide](docs/academic-projects.md)
  - The [Field Notes example](content/maps/public-self/field-notes/index.md) lives alongside ordinary posts in Public Self; its explicit template overrides that section's default post template

- **404.html**: Error page template
  - Custom 404 not found page

### Template Components

Located in `templates/components/`:

Tera 2 components are globally registered by component name. They do not need imports. Call them with syntax such as `{{ <render.section_title title={title} /> }}`.

- **render.html**: Core rendering utilities
  - `render.post_entry(page)`: Shared blog, project, and taxonomy page entries, with optional thumbnail, date, subtitle, and description
  - `render.section_title`: Renders section titles
  - `render.text_content`: Renders text content
  - `render.cards`: Renders card layouts
  - And more...

- **segment.html**: Segment rendering logic
  - `segment.populate`: Populates section content
  - `segment.plain`: Renders plain sections
  - `segment.category(pos, preview=false, limit=3)`: Renders subsection cards, with an optional limited home-page preview
  - `segment.blog(pos, preview=false, limit=3)`: Renders shared blog/project page lists, with an optional limited home-page preview
  - `segment.projects`: Thin compatibility alias for `segment.blog`
  - The index passes `config.extra.persona.home_items_limit` (default `3`) through `segment.populate` to both category and page lists; Tera components receive the setting explicitly
  - Preview limits apply after eligibility filtering. Zero shows only a View all link for a nonempty collection; negative limits use the default of three. Full section pages are unlimited
  - `extra.project.draft` pages remain buildable but are excluded from automatic blog/project, taxonomy, and Recent Posts lists

- **blog.html**: Blog-specific components
  - Blog listing and pagination logic

- **media.html**: Content media components
  - `media.image`: Resizes and renders colocated images
  - `media.block`: Renders image/text media rows
  - Content usage example: `{{ <media.image page={page} path="img/example.png" width={700} alt="Example" /> }}`

- **project.html**: Academic project components
  - `project.url(page, path)`: Resolves page-relative, site-root, and content URLs while preserving external links and fragments
  - `project.media(page, item, eager=false)`: Renders an image or native video with optional caption
  - `project.gallery(page, items, id="project-gallery", title="Results gallery")`: Renders a scrollable media gallery
  - `project.embed(src, title)`: Renders a responsive iframe using a provider embed URL
  - `project.poster(page, src, title="Research poster")`: Renders a PDF object with a direct-link fallback

- **debug.html**: Debug utilities
  - Development helpers

- **taxonomy.html**: Taxonomy page components
  - `taxonomy.list`: Renders category and tag index pages
  - `taxonomy.term`: Renders a single category or tag page

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
- **katex-css.html**: Conditional KaTeX stylesheet
- **katex-js.html**: Conditional KaTeX scripts and macro initialization
- **social-icon.html**: Social media icon rendering

### Taxonomy Templates

**Categories** (`templates/categories/`):
- **list.html**: Category listing page
- **single.html**: Single category page
- Both templates use `taxonomy.*` components for shared rendering

**Tags** (`templates/tags/`):
- **list.html**: Tag listing page  
- **single.html**: Single tag page
- Both templates use `taxonomy.*` components for shared rendering

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
│   ├── _segment.scss            # Segment container and title
│   └── _breadcrumbs.scss        # Page title / breadcrumbs bar
│
├── pages/
│   ├── _hero.scss               # Hero section (home page only)
│   ├── _contact.scss            # Contact form and info
│   ├── _project.scss            # Academic project layout and components
│   └── _plain.scss              # Plain section content
│
├── components/
│   ├── _category.scss           # Category card listing
│   ├── _blog.scss               # Shared blog/project post entries
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
    ├── page-project.scss         # Academic project pages
    ├── citations.scss            # Citation styling for post pages
    └── page-404.scss             # 404 error page
```

### CSS Loading Strategy

Each template loads only the CSS it needs:

| Template | Entry point loaded | Contents |
|---|---|---|
| `base.html` (all pages) | `main.css` | variables, base, footer, preloader, custom |
| `index.html` | `home.css` | nav-index, hero, segment, plain, category, shared page lists, contact |
| `section.html` (plain) | `page-plain.css` | navigation, segment, plain |
| `section.html` (category) | `page-category.css` | navigation, segment, category |
| `section.html` (blog) | `page-blog.css` | navigation, segment, blog, breadcrumbs |
| `section.html` (projects, compatibility alias) | `page-blog.css` | same shared listing as blog sections |
| `post.html` | `post.css` | navigation, breadcrumbs, post, widgets |
| `post.html` | `citations.css` | Pandoc citation and bibliography styles |
| `project.html` | `page-project.css` | variables, navigation, breadcrumbs, sidebar widgets, project layout/media, custom |
| `page.html` | `page-plain.css` | navigation, segment, plain |
| `404.html` | `page-404.css` | navigation, segment, plain, contact |

### Design Tokens

All customizable theme values start in `_variables.scss` as **SCSS variables**, then are re-exported as **CSS custom properties** inside `:root` so they remain accessible at runtime.

**Color variables**:
- Global colors: background, text, headings, accent, surface, contrast
- Navigation colors
- Header colors

**Typography**:
- Font families: default, heading, navigation
- Font sizes: normal, footer, heading, subtitle, title

**Spatial and temporal values**:
- Navigation dimensions, border radius, button sizes and positions
- Consistent screen sizes: mobile, tablet, desktop breakpoints
- Transition timing

## JavaScript Organization

JavaScript files in `static/assets/script/`:

- **home.js**: Home page functionality
  - Smooth scrolling
  - Mobile navigation
  - Preloader
  - AOS initialization
  - Typed.js for text animation

- **share.js**: Social sharing functionality
  - Generates share URLs for Twitter, Facebook, LinkedIn
  - Opens share menu when share button is clicked

- **project.js**: Progressive enhancements for academic project pages
  - Enables BibTeX clipboard copying with selection and status-message fallback
  - Adds gallery navigation, keyboard controls, and announced slide positions
  - Respects reduced-motion preferences and pauses videos on inactive slides
  - Uses native browser APIs; project content, PDF links, video controls, and gallery scrolling remain available without JavaScript

## Development Workflow

1. **Check theme**: `zola check`
2. **Build**: `zola build`
3. **Serve locally**: `zola serve`
4. **Test changes**: Navigate to http://127.0.0.1:1111

## Adding New Features

### Adding a New Section Type

1. Create SCSS partial: `sass/assets/stylesheet/components/_new-type.scss`
2. Create a new entry point (e.g. `sass/assets/stylesheet/page-new-type.scss`) that `@use`s the partial
3. Add rendering component in `templates/components/segment.html`
4. Update `section.html` to load `page-new-type.css` for the new type
5. Document in README.md

### Adding a New Partial

1. Create partial: `templates/partials/component-name.html`
2. Create SCSS partial: `sass/assets/stylesheet/components/_component-name.scss`
3. `@use` the new partial in the relevant entry point(s)
4. Include the HTML partial in the appropriate template
5. Document usage

### Adding a New Tera Component

1. Add to the appropriate component file in `templates/components/`
2. Document parameters and usage
3. Call it by its global component name, for example `{{ <render.section_title title={title} /> }}`

## Best Practices

1. **Separation of Concerns**: Keep reusable rendering in components, styling in SCSS, structure in templates
2. **Reusability**: Use components and partials for repeated patterns
3. **Conditional Loading**: Only load SCSS/JS needed for specific pages
4. **Documentation**: Update this file when adding new components or changing structure
5. **Testing**: Test on multiple devices and browsers after changes

## Dependencies

### Included Vendors
- Bootstrap 5.3.x
- Bootstrap Icons
- AOS (Animate On Scroll)
- Academicons
- Typed.js
- KaTeX (loaded conditionally for math content)

## Related Documentation

- [README.md](README.md) - Main theme documentation
- [Academic project pages](docs/academic-projects.md) - Front matter, URL rules, media components, and customization
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- [theme.toml](theme.toml) - Theme metadata and configuration
- [config.toml](config.toml) - Configuration template for user site
- [Zola Documentation](https://www.getzola.org/documentation/) - Zola reference
