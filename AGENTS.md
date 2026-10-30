# AGENTS.md

Guidance for agents working on Persona, a Zola theme.

## Project Context

Persona is a reusable Zola theme, not only one website. Prefer changes that work for a site mounted at a domain root and for a site mounted under a path such as `https://example.com/project/`.

Before changing templates, run enough local checks to understand the current structure:

```bash
make build
make check ZOLA_ARGS=--skip-external-links
```

Use `make serve` for live preview. The shared pipeline stages authored Markdown before Zola, preserving math and rendering citations. Bare Zola commands bypass this step.

## Zola Template Practices

- Target Zola 0.23+ and Tera 2 syntax.
- Use `templates/components/` for reusable rendering logic.
- Use `templates/partials/` for included page fragments and asset includes.
- Do not reintroduce old `{% import ... as ... %}` macro syntax.
- Do not add old-style shortcode templates unless the theme intentionally restores shortcode support.
- Use `get_url(path=...)`, `page.permalink`, or `section.permalink` for internal links and assets so `base_url` path prefixes are respected.
- Use `page is defined` and `section is defined` guards in shared templates that may render on taxonomy or special pages.
- Keep `section.html` as the canonical section page template. The reusable segment renderer belongs in `templates/components/segment.html`.
- Load page-specific CSS and scripts from the templates that need them. Keep `base.html` limited to shared assets.
- Keep KaTeX assets conditional on `page.extra.tex`.

## Website Design Practices

- Build the actual page experience, not a landing-page wrapper around it.
- Keep the theme quiet, readable, and content-first. Persona is for personal sites, portfolios, and blogs, so the design should make sections, writing, and contact information easy to scan.
- Use semantic HTML before generic `div` wrappers:
  - `header` for page and article headers
  - `nav` for navigation, breadcrumbs, social links, and share menus
  - `main` for the primary page content
  - `section` for standalone document sections
  - `article` for complete posts or post cards
  - `aside` for sidebars and secondary controls
  - `figure` for meaningful images
  - `time datetime="YYYY-MM-DD"` for dates
- Preserve useful class names when changing tags so existing Sass remains stable.
- Add `aria-label` where an icon-only or repeated navigation region needs a clear name.
- Use real `alt` text for meaningful images. Use empty `alt=""` only for decorative images.
- Keep heading order coherent. Avoid footer or widget headings that compete with the main document outline unless they describe a real section.
- Avoid visual regressions after semantic tag changes; browser-default margins on tags such as `figure`, `address`, `ul`, and `nav` may need small CSS resets.
- Ensure text remains readable on mobile and desktop. Do not rely on viewport-scaled font sizes.
- Keep controls familiar: buttons for actions, links for navigation, lists for collections, and forms for user input.

## Sass And Assets

- Zola compiles Sass directly from non-underscore files in `sass/`.
- Use `@use`, not Sass `@import`.
- Keep shared design tokens in `_variables.scss`.
- Prefer existing mixins and classes over creating one-off styles.
- Avoid globally loading vendor CSS/JS unless most pages need it.

## Markdown, Math, and Citation Pipeline

- Author all posts as ordinary `*.md`. Generated input belongs in the isolated staging directory, never beside authored content.
- Keep `ignored_content = ["*.src.md", "*.bib", "*.csl"]` to exclude bibliography assets and support legacy source naming.
- Preserve TeX math before Markdown and Tera processing so KaTeX receives the original expressions and page macros.
- Use the shared `scripts/persona.py` entry point for build, preview, checks, and CI preparation. Consuming sites should delegate to this runner instead of maintaining their own preprocessing logic.
- Keep legacy `.src.md` compatibility, but migrate examples to ordinary `.md`. Never let cleanup delete authored Markdown.
- CSL resolution order should remain:
  1. per-post `[extra].citation_style`
  2. local `style.csl` beside the post
  3. site-level `config.toml`
  4. theme-level fallback
  5. clear error when citation processing needs a CSL and none is available

## Git Commit Messages

Use a gitmoji followed by a conventional commit style:

```text
<gitmoji> type(scope): short imperative description
```

Examples:

```text
✨ feat(template): add taxonomy list component
🐛 fix(navigation): respect base_url in breadcrumbs
♻️ refactor(template): migrate macros to Tera components
📝 docs(readme): document citation pipeline setup
🎨 style(stylesheet): refine post metadata spacing
✅ test(build): add theme validation fixture
🔧 chore(config): update Zola deploy action
```

Common types:

- `feat`: user-facing feature
- `fix`: bug fix
- `refactor`: code restructuring without intended behavior change
- `docs`: documentation-only change
- `style`: visual or formatting change
- `test`: validation or test change
- `chore`: maintenance

Keep commits focused. If a change touches both the Persona submodule and a parent site that consumes it, commit the submodule first, then commit the parent site submodule pointer separately.
