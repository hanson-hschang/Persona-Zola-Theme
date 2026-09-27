# Resume and CV

Persona's resume layout uses ordinary Markdown headings, paragraphs, and bullet lists. The first `#` heading becomes the page title, and the remaining headings organize experience and education. A configurable professional summary with an optional badge list spans the full width above skill rows and the experience columns. Optional periods, organizations, and locations sit beside the entry headings. The layout uses Persona's shared design tokens, works without JavaScript, and stacks its experience columns on small screens and printed pages.

Start with the [example resume](../content/resume/_index.md). Replace its sample content with your own information.

## Create a resume section

Create `content/resume/_index.md` in your site:

```markdown
+++
title = "Resume"
page_template = "resume.html"

[extra]
type = "resume"
subtitle = "Research and education"
icon_class = "bi bi-file-earmark-person"
order = 15

[extra.summary]
title = "Professional Summary"
button_text = "Explore my experience"
description = """
Write a short professional summary here. **Markdown** is supported.

A second paragraph can introduce your teaching, projects, or other work.
"""
+++

# Example Researcher

## Research Experience

### Example research role

> Period: 2024-01 / Present  
> Organization: [Example Research Group](https://example.org/)  
> Location: Example City

A short description of the research area and role.

- Describe a project or responsibility.
- Add a result or a link to relevant work.

---

## Education

### Example degree

> Period: 2020 / 2024  
> Organization: Example University

- Describe your field of study or a relevant achievement.
```

The canonical `section.html` template selects the resume layout using `extra.type = "resume"`. The optional `page_template = "resume.html"` sets the default template for child Markdown pages in this section; it does not select the section's own layout.

With a positive `order`, the home page shows a compact resume preview: the front matter `title`, `extra.subtitle`, and the configured summary, including its badges. Skills and the Markdown experience and education remain on the full resume page. The preview ends with a link to that page. Set `extra.summary.button_text` to customize its label; an omitted or blank value uses **View full resume**. This link appears only in the home preview.

Set `landing_page = false` to hide both the preview and its navigation icon/link on the home page. A positive `order` still includes the section in navigation on ordinary pages. The front matter `title` supplies the navigation label and preview heading, so it can remain `"Resume"` while the full resume title is your name. Omitting `landing_page` or setting it to `true` enables the preview again.

The first `#` heading in the Markdown body supplies the visible title at `resume-title`. If it is absent, the layout uses the front matter `title`. `extra.subtitle` appears below the title. The optional `[extra.summary]` supplies the visible summary, which appears once at full width above the skills. There is no separate name field.

The top-level `description` is optional search metadata, separate from the visible summary. If it is omitted, the page's metadata uses `extra.summary.description`, then the site's `config.description`. Markdown formatting is removed for the metadata value.

### Standalone and child pages

For a standalone page such as `content/resume/index.md`, add `template = "resume.html"` at the top level of its front matter and use the same Markdown structure. Do not create both `index.md` and `_index.md` for the same resume route.

When a section specifies `page_template = "resume.html"`, child pages can use this layout without repeating `template`. Each child supplies its own title, optional summary and subtitle, and Markdown body. Automatic navigation entries come from sections; use the section setup above when you want a resume link in the ordinary page navigation.

## Organize the Markdown body

Use one `#` heading for your name, `##` headings for groups such as Research Experience or Education, and `###` headings for individual roles, degrees, or projects. Write ordinary paragraphs and bullet lists below each entry. Links, emphasis, and other Markdown formatting work within the content. Keep experience and education in the Markdown body; optional skills, summary, and badges use structured data in `[extra]`.

Place a standalone `---` between groups to start the second desktop column. Use this column break at most once. Without it, the resume uses one column. Both columns retain Markdown source order when stacked on small screens and in print. Leave blank lines around the rule so Markdown treats it as a horizontal rule rather than a heading underline.

## Optional skills, summary, and badges

Add `skills` inside the existing `[extra]` table to show a tabbed skills section before the experience columns. Use a nested `[extra.summary]` table for the summary panel and an optional `[extra.summary.badges]` table for awards, honors, or other short labels:

```toml
[extra]
type = "resume"
skills = [
  { category = "Programming languages", icon_class = "bi bi-code-slash", items = ["Python", "C/C++", "JavaScript"] },
  { category = "Development tools", icon_class = "bi bi-tools", items = ["Git", "Docker"] },
]

[extra.summary]
title = "Professional Summary"
description = """
Write a short professional summary here. **Markdown** is supported.
"""

[extra.summary.badges]
title = "Awards and Honors"
items = [
  { label = "Example Research Fellowship", icon_class = "bi bi-award", link = "https://example.org/fellowship" },
  { label = "Example Teaching Award", icon_class = "bi bi-trophy" },
]
```

Keep `skills` and other direct `[extra]` settings **before** the nested table headers. In TOML, settings after `[extra.summary]` belong to that table until another table header appears.

Each category has a `category` heading and an `items` list. Add or remove categories and items as needed; their order in the array is their display order. Each category becomes a tab, with the first category selected initially. Hover over or click a tab to show its items in the shared content area below. Only one category is visible at a time. Keyboard users can switch with Left/Right Arrow, Home, and End, then press Tab to enter the selected panel. When the category row overflows, visitors can scroll it manually with a wheel, trackpad, touch gesture, or keyboard navigation. It never scrolls automatically or repeats categories. There are no percentages, progress bars, or overall Skills heading. Categories and items are plain text, so Markdown or HTML formatting is not needed.

Use the optional `icon_class` on each category to choose an icon from the theme's included icon fonts, such as `"bi bi-code-slash"` or `"bi bi-tools"`. Omit it or set it to an empty string to show that category without an icon. Category icons are decorative; the category heading supplies their meaning.

The summary appears above the full-width tabbed section on every screen size. Each tab contains its category name and optional icon. Without JavaScript, category links jump to the complete lists below; printing includes every category and its items. The summary's `description` supports Markdown. Its `title` defaults to **Professional Summary**; customize it or use `title = ""` to hide the heading. Omit `[extra.summary]` to leave the summary out. A title alone does not create an empty panel: the summary needs a nonblank description or at least one nonblank badge.

Badges appear below the summary description in a single horizontal strip using the theme's accent color. With two or more badges, the strip scrolls continuously so long lists fit without widening the page. Hover over or click the strip to pause it; move the pointer away or click elsewhere to resume. Keyboard focus also pauses the strip until focus moves away. On a touch screen, tap or swipe the strip to pause it, then tap elsewhere to resume. A single badge stays still. Visitors who prefer reduced motion see a static strip they can scroll themselves. Without JavaScript, all badges remain available in that same scrollable strip.

Set the badges' optional `title` to a heading such as **Awards and Honors**, or omit it for an unheaded list. Each item can specify a `label` and an `icon_class`, such as `"bi bi-award"` or `"bi bi-trophy"`, using the theme's included icon fonts. Omit `icon_class` to use the award icon, or set it to `""` to hide the icon. Icons are decorative; the label supplies their meaning.

For a shorter configuration, a plain string such as `"Example Research Fellowship"` also works and uses the default award icon. String and object items can be mixed in display order. Labels and icon classes are trimmed; blank strings and objects with missing or blank labels are ignored. Badge labels and headings are plain text. Badges can also appear without a summary description.

Add an optional `link` to a badge object to make the entire badge a link. It opens in a new tab and supports ordinary keyboard activation. Missing or blank links keep the badge as plain content. Links appear in both the home preview and the full resume. With JavaScript enabled, dragging, scrolling, or holding a badge for at least 500 milliseconds does not open its link; a short click or tap does. Without JavaScript, linked badges retain their normal browser link behavior.

Use an absolute `https://` or `http://` URL, a site path such as `"/about/"` or `"about/"`, or a Zola content reference such as `"@/about/_index.md"`. Site paths resolve from the site root and preserve any `base_url` path prefix. Other URL schemes, protocol-relative URLs beginning with `//`, and paths containing backslashes are ignored, leaving the badge unlinked.

Omit `skills` or use `skills = []` to leave the tabs out and retain the full-width summary, including its heading and badges. Blank skill items and categories without a label or any nonblank items are ignored; if no valid categories remain, the layout uses the same full-width summary. On the full resume page, summary headings and category headings in the no-script and print layouts use level two. A badge heading uses level three beneath a summary heading, or level two when that heading is hidden. The home preview nests its summary at level three beneath the section title, with a level-four badge heading, or level three when the summary heading is hidden.

## Optional entry metadata

An optional blockquote immediately below a `###` entry heading supplies its details. Use the labels `Period:`, `Organization:`, and `Location:`. End each metadata line except the last with **two spaces** so Markdown inserts a hard line break. Omit unused lines, and omit the entire blockquote when the entry has no metadata.

```markdown
### Independent project

> Organization: [Example Lab](https://example.org/)  
> Location: Remote

- An entry does not need a period.

### Open-source contributions

- An entry can also consist of just a heading and bullet points.
```

Organizations support either plain text or a normal Markdown link. Organization and location appear on one italic line, aligned left and right when space allows. Either can appear on its own. Long text wraps on narrow screens.

Write periods with ISO-style dates. Use only the precision you know: `2024` for a year, `2024-07` for a month, or `2024-07-15` for a full date. Separate range endpoints with ` / `, and use `Present` for an ongoing role. A single date is also supported.

| Markdown value | Display |
| --- | --- |
| `2020 / 2024` | 2020 – 2024 |
| `2019-07 / 2024-12` | July 2019 – December 2024 |
| `2024-07-15 / Present` | July 15, 2024 – Present |
| `2024-07` | July 2024 |

Periods use the same calendar icon and long-month date convention as article metadata. Full dates use the article format `%B %d, %Y`; month-only and year-only values retain their original precision. Do not add an arbitrary day to a date when you know only its month. The entry title aligns left and the period aligns right on the same row when there is room, with wrapping for smaller screens.

Use normal Markdown link syntax for organizations and content. Zola content references such as `[About](@/about/_index.md)` resolve to the content permalink; relative links can point to colocated assets. Avoid filesystem prefixes such as `static/` or `content/` in public URLs.

## Styling and print

The implementation lives in `templates/resume.html`, `templates/components/resume.html`, and `sass/assets/stylesheet/pages/_resume.scss`. The canonical section template also selects the resume component. Full resume pages and sections load `page-resume.css`, including their navigation styles. A home page with a visible resume preview loads `resume-preview.css` instead, sharing the resume styles while preserving the home page's navigation layout. Both stylesheets use Persona's shared design tokens.

`static/assets/script/resume.js` enhances the badge strip with continuous scrolling that pauses during interaction, and the skill categories with accessible tabs and a manually scrollable category row. It loads on resume pages and sections, and on the home page when it includes a visible resume preview.

Use the browser's Print command to print or save a PDF. The print stylesheet arranges sections in one column and shows all skill lists in current browsers, including categories that are inactive on screen. Badges wrap onto as many lines as needed, with each badge printed once. Preview the result with your own content before sharing, since pagination depends on content length and printer settings.
