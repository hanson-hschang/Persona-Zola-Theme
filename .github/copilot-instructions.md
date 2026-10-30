# Persona Zola Theme

Persona is a modern, responsive portfolio and blog theme for the Zola static site generator. 
It features Bootstrap components, AOS animations, and a clean design suitable for personal websites, portfolios, resumes, and blogs.

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Working Effectively

### Prerequisites and Setup
- Install Zola static site generator (minimum version 0.23.0):
  ```bash
  wget https://github.com/getzola/zola/releases/download/v0.23.4/zola-v0.23.4-x86_64-unknown-linux-gnu.tar.gz -O /tmp/zola.tar.gz
  tar -xzf /tmp/zola.tar.gz -C /tmp
  sudo mv /tmp/zola /usr/local/bin/
  ```
- Install Python 3.11 or newer for the staged build tools.
- Install Pandoc for citation-enabled posts, including the theme's demo guides.

### Build and Development Commands
- **NEVER CANCEL builds or commands** - they complete quickly but set appropriate timeouts
- Check the theme for errors: `make check`.
- Build the complete theme demo: `make build`.
- Serve the development version: `make serve ZOLA_ARGS="--interface 0.0.0.0 --port 8000"`.
- Clean generated output: `make clean`. Authored files in `content/` are preserved.
- Always use these helpers for pages with mathematics or citations. Bare Zola commands bypass preprocessing.
- Write posts directly in ordinary `.md` files. The build prepares a separate copy for Zola instead of writing generated pages beside the sources.
- Enable mathematics with `[extra.tex]` or `[extra.tex.macros]`. Write `$...$` and `$$...$$` normally, without `<div>` wrappers or extra Markdown escape backslashes.
- Enable citations with `[extra].bibliography` or a local `references.bib`; Persona resolves citation keys with Pandoc while preserving Tera component calls.
- In a consuming site, add `include themes/persona/Makefile` to its Makefile. Do not copy the theme's scripts into that site.

### Content Structure Requirements
This is a **theme repository** with demo content in `content/`. Use that content
for validation and preserve existing pages. To create an isolated test fixture:

1. Create `content/` directory in repository root
2. Create `content/_index.md` with basic frontmatter:
   ```markdown
   +++
   title = "Persona"
   template = "index.html"
   [extra]
   subtitles = "a Portfolio, a Resume, a Blog, a Zola Theme"
   +++
   ```

3. For additional sections, create structured content like:
   ```markdown
   +++
   title = "About"   
   [extra]
   order = 1
   icon_class = "bi bi-person"
   type = "plain"
   +++
   
   Content goes here.
   ```

### Validation and Testing
- **CRITICAL**: Always test theme functionality after making changes by:
  1. Using the existing demo content or an isolated test fixture
  2. Running `make build` to ensure no template errors
  3. Running `make serve` and testing navigation
  4. Verifying sections display correctly with proper metadata
- Always run `make check` before committing changes
- Test both home page (all sections) and individual section pages
- Verify responsive design and navigation functionality

### Template and Content Requirements
**Key template requirements that must be satisfied:**
- Sections displayed in navigation need `extra.icon_class` (Bootstrap Icons)
- Sections need `extra.order` for display ordering
- Sections need `extra.type` matching template type (`"plain"`, `"category"`, or `"blog"`)
- Blog posts need `extra.excerpt` for post listing pages
- Sections with cards need `extra.thumbnail` for image display

### Theme Architecture
- `templates/`: Zola templates (base.html, index.html, etc.)
- `templates/components/`: Tera 2 reusable components
  - `render.html`: Core rendering components (`render.post_entry`, `render.section_title`, `render.text_content`, cards, etc.)
  - `segment.html`: Segment population components (`segment.populate`, `segment.plain`, `segment.category`, `segment.blog`)
  - `blog.html`: Blog-specific components
  - `media.html`: Content media components
  - `taxonomy.html`: Category and tag listing components
  - `debug.html`: Debug utility components
- `templates/partials/`: Page sections (navigation, hero, contact, etc.)
  - `katex-css.html` and `katex-js.html`: Conditional math rendering assets for pages with `page.extra.tex`
- `templates/categories/`: Category page templates
- `templates/tags/`: Tag page templates
- `static/assets/`: Theme CSS, JavaScript, and images
- `static/vendor/`: Third-party libraries (Bootstrap, AOS, etc.)
- `config.toml`: Theme configuration and settings

### Common Tasks
**Repository structure:**
```
.
├── .github/workflows/deploy.yml    # GitHub Pages deployment
├── config.toml                     # Site configuration
├── theme.toml                      # Theme metadata
├── content/                        # Authored Markdown for the theme demo
│   └── _index.md                   # Homepage content
├── Makefile                        # Staged build, preview, and validation commands
├── scripts/                        # Math/citation processing and build tools
├── static/                         # Static assets
│   ├── assets/                     # Theme assets (CSS, JS, images)
│   └── vendor/                     # Third-party libraries
└── templates/                      # Zola templates
    ├── base.html                   # Base template
    ├── index.html                  # Home page template
    ├── 404.html                    # 404 error page
    ├── section.html                # Section/segment template
    ├── page.html                   # Page template
    ├── post.html                   # Blog post template
    ├── categories/                 # Category templates
    │   ├── list.html               # Category list template
    │   └── single.html             # Single category template
    ├── tags/                       # Tag templates
    │   ├── list.html               # Tag list template
    │   └── single.html             # Single tag template
    ├── components/                 # Tera 2 components
    │   ├── render.html             # Core rendering components
    │   ├── segment.html            # Segment components
    │   ├── blog.html               # Blog components
    │   ├── media.html              # Media components
    │   ├── taxonomy.html           # Taxonomy components
    │   └── debug.html              # Debug components
    └── partials/                   # Template partials
        ├── navigation.html         # Navigation component
        ├── hero.html               # Hero section
        ├── footer.html             # Footer component
        ├── contact.html            # Contact section
        ├── contact-form.html       # Contact form
        ├── contact-info.html       # Contact info
        ├── head-title.html         # Head title component
        ├── katex-css.html          # Conditional KaTeX stylesheet
        ├── katex-js.html           # Conditional KaTeX scripts
        └── social-icon.html        # Social icon component
```

**Key configuration files:**
- `config.toml`: Site-wide settings, metadata, and theme configuration
- `theme.toml`: Theme information and requirements
- `.github/workflows/deploy.yml`: Automated deployment to GitHub Pages

### Troubleshooting
**Common template errors:**
- `Variable 'subsection.extra.icon_class' not found`: Add `icon_class` to section frontmatter
- `Variable 'page.extra.excerpt' not found`: Add `excerpt` to page frontmatter  
- `Variable 'pos.extra.type' not found`: Add `type` to section extra metadata

**Build issues:**
- Empty builds (0 pages): Create `content/_index.md` file
- Template rendering errors: Check section frontmatter has required fields
- Missing assets: Verify `static/` directory structure is intact

**Development server issues:**
- "Can't watch `content` for changes": Create `content/` directory
- Navigation not working: Check sections have proper `extra.order` and `icon_class`

### Validation Scenarios
After making template or style changes, always validate by:

1. **Basic functionality test:**
   ```bash
   make build
   make check
   make serve ZOLA_ARGS="--interface 0.0.0.0 --port 8000"
   ```

2. **Full theme test with sections:**
   - Create multiple content sections with proper frontmatter
   - Test navigation between sections
   - Verify responsive design
   - Check contact form display (if configured)

3. **Template validation:**
  - Ensure all Tera components render without errors
   - Test both single-page and multi-section layouts
   - Verify CSS and JavaScript assets load correctly
   - Test blog template with sample posts:
     ```bash
     mkdir -p content/blog
     echo "+++\ntitle = \"Blog\"\ntemplate = \"section.html\"\n\n[extra]\norder = 2\nicon_class = \"bi bi-journal\"\ntype = \"category\"\n+++" > content/blog/_index.md
     echo "+++\ntitle = \"Test Post\"\ndate = 2023-01-01\n\n[extra]\nexcerpt = \"Sample post\"\n+++\n\nTest content" > content/blog/test.md
     make build
     make serve ZOLA_ARGS="--interface 0.0.0.0 --port 8000"
     ```

### Deployment
The theme includes automated GitHub Pages deployment via `.github/workflows/deploy.yml`:
- Triggers on pushes to main branch
- Installs Python and Pandoc, then prepares content with `scripts/persona.py prepare`
- Uses `shalzz/zola-deploy-action@v0.23.4` to build the prepared `.persona-build/` directory
- Deploys to `gh-pages` branch
- **DO NOT** modify deployment workflow without testing

### Performance Notes
- Build time depends on the content and whether citation processing is needed
- Theme includes optimized vendor libraries
- Static assets are properly organized for caching
- No external JavaScript bundler is required
- Zola compiles Sass entry points in `sass/` as part of `make build` and `make serve`
