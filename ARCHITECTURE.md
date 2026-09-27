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
│           │   ├── _post.scss        # Article page styles
│           │   ├── _resume.scss      # Resume layout and print styles
│           │   └── _plain.scss       # Plain section content styles
│           ├── components/
│           │   ├── _category.scss    # Category section styles
│           │   ├── _post.scss        # Shared post listing styles
│           │   ├── __old_post.scss   # Archived former blog article styles
│           │   ├── __old_widgets.scss # Archived former blog widget styles
│           │   ├── _share.scss       # Article metadata and sharing controls
│           │   └── _widgets.scss     # Shared sidebar widget shell
│           ├── main.scss             # Entry point: all pages -> main.css
│           ├── home.scss             # Entry point: home page -> home.css
│           ├── page-plain.scss       # Entry point: plain sections -> page-plain.css
│           ├── page-category.scss    # Entry point: category sections -> page-category.css
│           ├── page-post-list.scss   # Entry point: post lists -> page-post-list.css
│           ├── page-post.scss        # Entry point: all articles -> page-post.css
│           ├── page-resume.scss      # Entry point: resumes -> page-resume.css
│           ├── resume-preview.scss   # Entry point: home resume previews -> resume-preview.css
│           ├── __old_post.scss       # Archived entry point; no compiled CSS
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
│   ├── post.html                     # Unified post template
│   ├── resume.html                   # Standalone resume page template
│   ├── __old_post.html               # Archived former blog post template
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
  - Renders sections with `order > 0` from front matter unless `extra.landing_page = false`
  - Omits sections with `extra.landing_page = false` from both home content and home navigation; positive-order sections remain in ordinary page navigation
  - Renders visible resume sections as compact previews using the front matter title, subtitle, and summary with badges; skills and Markdown entries remain on the full resume page
  - Links each resume preview to its section permalink using `extra.summary.button_text`, defaulting to "View full resume"; loads `resume-preview.css` and `resume.js` only when a preview is visible, keeping full-page navigation styles out of the home page
  - Shows contact section

- **section.html**: Section page template
  - Handles plain, category, posts, and resume section types
  - Conditionally loads type-specific CSS and components
  - Contains the logic that previously lived in the root `segment.html` page template

- **page.html**: Single page template
  - For standalone pages
  - Plain content rendering

- **resume.html**: Standalone resume page template
  - Selected with `template = "resume.html"`, or inherited by child pages through section `page_template = "resume.html"`; section resumes use the canonical `section.html` with `extra.type = "resume"`
  - Uses the first Markdown `#` heading as the visible title and native `##`/`###` headings and bullet lists for experience and education
  - Shows optional `extra.skills` categories with `icon_class` and `items` in one tabbed section before the Markdown columns, without an overall Skills heading; hovering or selecting a category reveals its items below
  - Configures the visible summary through `extra.summary.title` and Markdown `description`, with optional `badges.title` and `badges.items` rendered as recognition badges in the theme's accent color; each item accepts a plain label or a `label`/`icon_class` object, with a default award icon and explicit blank icons hidden; the summary appears once at full width above the skill cards
  - Keeps badges in a horizontally scrollable strip, progressively enhanced into a continuous loop that pauses during interaction; reduced-motion preferences and single badges use the static strip, while print wraps each badge once
  - Uses the top-level `description` for search metadata, falling back to `extra.summary.description` and then `config.description`
  - Uses primary and optional secondary columns on desktop, stacking into one column on mobile and in print
  - Loads `page-resume.css` and `resume.js` and omits the page preloader
  - See the [resume Markdown guide](docs/resume.md) and [example resume](content/resume/_index.md)

- **__old_post.html**: Archived former blog post template
  - Preserved for reference; not selected or loaded by current pages

- **post.html**: Unified post template
  - Selected with `template = "post.html"` or the section's `page_template`; reads optional `page.extra.post` data
  - Shows linked tags with the title; publication date, reading time, and Share occupy a separate full-width row after the author byline and before resources, with no Save action
  - Renders authors, affiliations, resource links, teaser, abstract, article, gallery, video, poster, and BibTeX; article images are centered by default
  - Separates Pandoc's appended bibliography at `<!-- persona-bibliography -->` and renders it after the BibTeX Citation section, preserving all citation anchors; legacy `<div id="refs">` output is also supported
  - Generates page metadata and scholarly citation tags
  - Inherits standard navigation and mobile toggle, with breadcrumbs based on section ancestry
  - Names its contents navigation with `config.extra.persona.outline_title`, defaulting to `Outline` for omitted or blank values; the trimmed, escaped plain-text title labels the navigation through `aria-labelledby`
  - Uses native `details`/`summary` for Outline: folded by default below 992px, with a full-width vertical list, 16px links, wrapping labels, and the desktop blue rail; expanded in the compact sticky sidebar at larger widths
  - Styles the mobile outline with a tinted toggle, an arrow beside its label, and a distinct shaded panel with a rounded border instead of a horizontal rule beneath it
  - Gives hovered and keyboard-focused outline links the same accent and background as the current section
  - Displays Related Posts below the left contents navigation; below the content under the `lg` breakpoint. Defaults to up to five other listed pages from the parent section; explicit `post.related` overrides the list and `[]` disables it
  - Overrides the base `preloader` block so research content is available without JavaScript
  - Loads `page-post.css`, `citations.css`, AOS, `home.js`, `share.js`, and `post.js`; retains shared footer and conditional KaTeX support with the existing `[extra.tex.macros]` configuration
  - See the [front matter and component guide](docs/posts.md)
  - The [Field Notes example](content/maps/public-self/field-notes/index.md) lives in Public Self; both demo article sections default to this layout

- **404.html**: Error page template
  - Custom 404 not found page

### Template Components

Located in `templates/components/`:

Tera 2 components are globally registered by component name. They do not need imports. Call them with syntax such as `{{ <render.section_title title={title} /> }}`.

- **render.html**: Core rendering utilities
  - `render.date(value, class_name="")`: Shared semantic date rendering for article metadata, listings, Related Posts, and resume periods; full dates use `%B %d, %Y`, while year and month values retain their precision. The shared `.date-text` class supplies consistent body-font typography without icons.
  - `render.post_entry(page)`: Shared section and taxonomy post entries, with optional thumbnail, date, subtitle, and description
  - `render.article_tags(page)` and `render.article_meta(page)`: Article tags and metadata / sharing controls
  - `render.section_title`: Renders section titles
  - `render.text_content`: Renders text content
  - `render.cards`: Renders card layouts
  - And more...

- **segment.html**: Segment rendering logic
  - `segment.populate`: Populates section content
  - `segment.plain`: Renders plain sections
  - `segment.category(pos, preview=false, limit=3)`: Renders subsection cards, with an optional limited home-page preview
  - `segment.posts(pos, preview=false, limit=3)`: Renders shared post page lists, with an optional limited home-page preview
  - The index passes `config.extra.persona.home_items_limit` (default `3`) through `segment.populate` to both category and page lists; Tera components receive the setting explicitly
  - Preview limits apply after eligibility filtering. Zero shows only a View all link for a nonempty collection; negative limits use the default of three. Full section pages are unlimited
  - `extra.post.draft` pages remain buildable but are excluded from automatic post, taxonomy, and Related Posts lists

- **__old_blog.html**: Archived former blog article components
  - Preserved for reference; current pages use `render.*`, `segment.*`, and `post.*` instead

- **media.html**: Content media components
  - `media.image`: Resizes and renders colocated images
  - `media.block`: Renders image/text media rows
  - Content usage example: `{{ <media.image page={page} path="img/example.png" width={700} alt="Example" /> }}`

- **post.html**: Post components
  - `post.url(page, path)`: Resolves page-relative, site-root, and content URLs while preserving external links and fragments
  - `post.media(page, item, eager=false)`: Renders an image or native video with optional caption
  - `post.gallery(page, items, id="post-gallery", title="Results gallery")`: Renders a scrollable media gallery
  - `post.embed(src, title)`: Renders a responsive iframe using a provider embed URL
  - `post.poster(page, src, title="Research poster")`: Renders a PDF object with a direct-link fallback

- **resume.html**: Resume components
  - Shared rendering for section and standalone resume pages
  - Shares summary rendering with the compact home preview, adjusting heading levels and badge region IDs for multiple sections; the preview uses the front matter title and a customizable link to the full resume
  - Splits rendered Markdown into the document, optional columns, groups, and entries without requiring resume data in front matter
  - Renders optional front matter skills as category links and complete labelled panels, preserving category/item order and omitting empty categories; JavaScript enhances these into tabs, while no-script and print layouts retain every list
  - Renders the nested summary with a customizable heading, Markdown description, and optional badge list with configurable decorative icons; normalizes string/object badge items and omits empty labels, and retains the full summary when skills are absent or empty
  - Supports optional badge `link` values as full-card native anchors with `target="_blank"` and `rel="noopener noreferrer"`; HTTP(S) URLs and site/content paths are accepted, internal paths retain the base URL prefix, and unsupported schemes, protocol-relative URLs, or backslashes leave the badge unlinked
  - Gives the badge strip a named, keyboard-focusable scroll region containing the original list
  - Reads optional period, organization, and location metadata from an entry blockquote; organization aligns left and location right in one italic paragraph by default, joining inline only when that entry's period wraps below its heading; the inline separator defaults to `@` and is customizable through plain-text `extra.location_separator`, with no separator for a missing field; normal Markdown links handle organizations
  - Uses `render.date` and `.date-text` for periods without icons, sharing the date format and typography with article metadata, listings, and Related Posts while preserving year-only and month-only precision; periods align right beside an entry heading and left when wrapped below it

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
│   ├── _post.scss               # Unified post layout
│   ├── _resume.scss             # Resume layout and print styles
│   └── _plain.scss              # Plain section content
│
├── components/
│   ├── _category.scss           # Category card listing
│   ├── _post.scss               # Shared post entries
│   ├── __old_post.scss          # Archived former blog article styles
│   ├── __old_widgets.scss       # Archived former blog widgets
│   ├── _share.scss              # Article metadata and sharing controls
│   └── _widgets.scss            # Shared sidebar widget shell
│
└── [entry points — no _ prefix; each compiles to public/assets/stylesheet/<name>.css]
    ├── main.scss                 # All pages
    ├── home.scss                 # Home / index page
    ├── page-plain.scss           # Plain section + page template
    ├── page-category.scss        # Category section pages
    ├── page-post-list.scss       # Post listing section pages
    ├── page-post.scss            # All post pages
    ├── page-resume.scss          # Resume sections and standalone resume pages
    ├── resume-preview.scss       # Home resume previews, without page navigation styles
    ├── citations.scss            # Citation styling for post pages
    └── page-404.scss             # 404 error page
```

### CSS Loading Strategy

Each template loads only the CSS it needs:

| Template | Entry point loaded | Contents |
|---|---|---|
| `base.html` (all pages) | `main.css` | variables, base, footer, preloader, custom |
| `index.html` | `home.css` | nav-index, hero, segment, plain, category, shared page lists, contact |
| `index.html` (visible resume preview) | `resume-preview.css` | shared resume styles, summary, badge strip, and preview link; no page navigation overrides |
| `section.html` (plain) | `page-plain.css` | navigation, segment, plain |
| `section.html` (category) | `page-category.css` | navigation, segment, category |
| `section.html` (posts) | `page-post-list.css` | navigation, segment, post lists, breadcrumbs |
| `section.html` (resume), `resume.html` | `page-resume.css` | shared design tokens, navigation, resume layout and print styles |
| `post.html` | `page-post.css` | variables, navigation, breadcrumbs, sidebar widgets, article layout/media, sharing, custom |
| `post.html` | `citations.css` | Pandoc citation and bibliography styles |
| `page.html` | `page-plain.css` | navigation, segment, plain |
| `404.html` | `page-404.css` | navigation, segment, plain, contact |

Archived files use the `__old_` prefix and are not referenced by current templates or Sass entry points. The retired Sass entry point, `__old_post.scss`, starts with `_`, so Zola does not compile it. Shared `home.js` navigation and `share.js` controls remain active; neither depends on the archived blog layout. Active article features use `[extra.post]` front matter, `.post` CSS classes, and `post-` fragment IDs. All current templates, components, and content use these post identifiers.

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

- **share.js**: Share menu disclosure
  - Opens the menu and closes it on Escape, outside clicks, or focus leaving the menu
  - Enhances the template's Permalink and social links even when no BibTeX copy action is present; links remain available without JavaScript

- **post.js**: Progressive enhancements for all post pages
  - Sets Outline's expanded state when crossing the 992px breakpoint, preserving manual disclosure choices while staying within the same breakpoint; native disclosure remains usable without JavaScript
  - Enables both Citation and Share's BibTeX copy buttons when nonblank `[extra.post].bibtex` is provided; Share otherwise starts with Permalink
  - Copies the citation's literal text, reports success next to the chosen control, and selects/focuses Citation with an announced manual-copy fallback when clipboard access fails
  - Adds gallery navigation, keyboard controls, and announced slide positions
  - Respects reduced-motion preferences and pauses videos on inactive slides
  - Builds the contents navigation from Pandoc HTML headings and highlights the current section as the reader scrolls
  - Uses native browser APIs; post content, PDF links, video controls, and gallery scrolling remain available without JavaScript

- **resume.js**: Progressive enhancement for resume badges, skill tabs, and entry layout
  - Uses `ResizeObserver` to detect each period wrapping below its heading and synchronize inline organization/location layout with that actual wrap; entries without a period retain separate alignment
  - Loops multiple badges horizontally, with duplicates hidden from assistive technology and duplicate links excluded from the tab order while preserving pointer access and hover animations
  - Pauses on hover, click, touch interaction, or keyboard focus; pointer exit, an outside click, or keyboard focus leaving the strip resumes scrolling
  - Preserves native horizontal scrolling for reduced motion, a single badge, and pages without JavaScript
  - Keeps the original list as the accessible and printable content; print styles hide copies
  - Preserves linked badge keyboard activation while suppressing accidental pointer activation after dragging, scrolling, or holding for at least 500 milliseconds
  - Adds single-panel skill tabs with hover/click selection, arrow/Home/End navigation, and linked ARIA roles
  - Keeps the category row manually scrollable without automatic movement or duplication; the active rounded tab joins its content panel
  - Selects the skill category nearest the visible row's center during manual scrolling on small screens, while retaining desktop hover/click selection

## Development Workflow

For citation-enabled content, author `.src.md` and run `bash scripts/build.sh` before Zola. `scripts/process_post.sh` preserves front matter and mathematical expressions, resolves the bibliography and CSL, runs Pandoc citeproc, moves the bibliography heading inside the references container, and inserts the stable bibliography boundary used by `post.html`. Generated `.md` files remain ordinary Zola content.

The incremental build checks source files, preprocessing scripts, configuration, and bibliography/CSL dependencies. `scripts/watch.sh` watches these inputs while excluding generated Markdown to avoid rebuild loops. When calling the pipeline from an installed theme, use `bash themes/persona/scripts/build.sh` from the site root. Existing article URLs, taxonomy data, and math macros are unaffected by changing their template.

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
- [Posts and academic articles](docs/posts.md) - Front matter, URL rules, media components, and customization
- [Resume and CV](docs/resume.md) - Markdown headings, optional entry metadata, navigation, and printing
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- [theme.toml](theme.toml) - Theme metadata and configuration
- [config.toml](config.toml) - Configuration template for user site
- [Zola Documentation](https://www.getzola.org/documentation/) - Zola reference
