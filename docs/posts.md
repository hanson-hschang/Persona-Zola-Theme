# Posts and academic articles

Persona's `post.html` is the unified layout for all posts and articles, using the theme's existing design tokens and an original layout. It includes tags, publication date, estimated reading time, Share, citations, and mathematics. Optional research features include authors and affiliations, resource links, a teaser, galleries, an embedded presentation, a PDF poster, and BibTeX. Each optional section appears only when configured; an ordinary article needs no `[extra.post]` table.

See the [Field Notes example](../content/maps/public-self/field-notes/index.md) in [Public Self](../content/maps/public-self/_index.md). Copy the example directory into a post section such as your site's `content/maps/public-self/` directory, replace the text and assets, and run `zola serve`. The demo sections default to `post.html`, and an explicit `template = "post.html"` also works. The former blog layout is archived under filenames prefixed with `__old_` and is no longer used. Zola 0.23+ is required, as with the rest of Persona.

## Page setup

The page is ordinary Markdown with a title and template. Include a date for sections sorted by date, such as Public Self:

```toml
+++
title = "A research post"
date = 2026-09-21
template = "post.html"
+++

## Overview

Write the article here.
```

The `[extra.post]` table is optional. Set `description` at the top level for search and social metadata, and `date` for the publication date. Existing `[extra].tex` support is available for mathematics. Posts share Persona's standard navigation and mobile menu. Breadcrumbs link Home and the parent sections, followed by the current post title; they follow content ancestry even when a post has a custom output path.

Use a page bundle such as `content/maps/public-self/my-post/index.md` so images, videos, caption files, and PDFs can live alongside the page.

## Post listings and home-page preview

Group posts in a section with a shared listing. For example, `content/maps/public-self/_index.md` uses:

```toml
+++
title = "Public Self"
sort_by = "date"
page_template = "post.html"

[extra]
type = "posts"
order = 10
+++
```

This creates a complete listing at `/maps/public-self/` and uses the shared article layout for its pages. Section and taxonomy page lists use the same `render.post_entry(page)` template and shared styles. Each entry can display a thumbnail on the left, a title and date, a subtitle below the title, and a description. The image and text form one link. Section Markdown, if supplied, appears above the entries.

For this date-sorted section, give **every page** a top-level `date` to list newest first. Zola excludes pages without dates from a section sorted by date. Alternatively, use `sort_by = "weight"` and give every page a `weight`; lower values appear first. All posts follow the section's ordering.

Add the limit under your existing `[extra.persona]` table in `config.toml`:

```toml
[extra.persona]
home_items_limit = 3
```

The setting applies to every list preview on the home page: category subsection cards and post entry lists. It defaults to `3` when omitted. Use a non-negative integer. `0` hides preview items while retaining the **View all** link for each nonempty collection. Negative values fall back to `3`. Full section pages show all eligible cards or non-draft entries. A **View all** link appears whenever a home-page preview omits eligible items. In the demo, the home page previews subsection cards under Maps; Public Self contains the full mixed list.

Configure an entry in its page front matter:

```toml
title = "Your research post"
description = "A short summary of the article."
date = 2026-09-21
template = "post.html"

[extra.post]
subtitle = "A concise statement of the contribution"
thumbnail = "thumbnail.jpg"
thumbnail_alt = "Overview of the proposed method"
```

Thumbnails follow the resource URL rules below. If `extra.post.thumbnail` is omitted, the listing tries `extra.thumbnail`, then the teaser image or a video teaser's `poster`. An entry without an image uses the full text width. `thumbnail_alt` defaults to empty because the adjacent title already names the linked post. Entry descriptions use the page's `description`, falling back to `extra.excerpt` when empty.

The top-level `date` appears in the full-width metadata row after the author byline on the detail page and beside the title in listings. Omit it to hide the date. Post subtitles appear on both the detail page and listings; `extra.post.subtitle` takes precedence over `extra.subtitle`.

Existing optional fields under `[extra]` remain supported: `subtitle`, `thumbnail`, and `thumbnail_alt`. A subtitle also appears below the title on the detail page. Use the top-level `description` or the existing `extra.excerpt` for a separate summary. Thumbnails are optional; an `extra.thumbnail` also supplies the article's hero image when no teaser is configured.

### Tags, metadata, citations, and mathematics

Keep tags in the standard `[taxonomies]` table and the date at the top level. Linked tags appear with the title. The publication date, estimated reading time, and Share menu occupy a separate row after the author byline and before the resource buttons, aligned to the same full width as the resources. The row still appears when authors or resources are omitted. It has no Save action.

```toml
date = 2026-09-21

[taxonomies]
tags = ["research", "mathematics"]

[extra.tex.macros]
'\Real' = '\mathbb{R}^{#1}'
```

Use `$x \in \Real{n}$` for inline mathematics and `$$ ... $$` for display mathematics. Adding `[extra.tex.macros]` enables KaTeX, including page-specific macros. An empty `[extra.tex]` table enables mathematics without custom macros.

For citations, author `index.src.md` using `[@citation-key]`, place `references.bib` beside it, and run the [citation pipeline](../README.md#-citation-pipeline) before building with Zola. Optional `[extra].bibliography` and `[extra].citation_style` keep their existing behavior. The preprocessor inserts a `<!-- persona-bibliography -->` boundary before its generated references, allowing the article to place **Bibliography** after the optional **Citation** section. Citation displays `[extra.post].bibtex` for readers who want to cite this article; Bibliography lists works cited in its text. Existing generated references without the marker remain supported.

The [Citation Pipeline Guide source](../content/maps/private-soul/citation-pipeline-guide/index.src.md) demonstrates citations, macro-based mathematics, and a sample BibTeX record together. Rebuild generated `.md` files after editing source, bibliography, CSL, or pipeline scripts. No source conversion is needed for an ordinary Markdown article without Pandoc citations.

### Draft posts with accessible URLs

Set `draft = true` inside the post's `[extra.post]` table to hide it from automatic home-page, post, taxonomy, and Related Posts lists:

```toml
+++
title = "Work in progress"
template = "post.html"
date = 2026-09-21

[extra.post]
draft = true
+++
```

The post and its assets still build at their normal URLs with `zola build` and `zola serve`. Drafts are filtered before applying the preview limit, so they do not take slots from listed pages or trigger an empty **View all** link. Set the flag to `false`, or omit it, to list the post again.

This theme flag is separate from Zola's top-level `draft = true`, which excludes the page from a normal build. Keep it under `[extra.post]` for an accessible, unlisted post. It controls automatic page listings; direct links and manually authored links remain usable.

## Front matter reference

All fields below belong to `[extra.post]` unless another location is shown. Omit fields you do not need.

| Field | Type | Rendering |
| --- | --- | --- |
| `draft` | Boolean | Defaults to `false`. When `true`, hides the entry from automatic post, taxonomy, and Related Posts lists while preserving its generated URL. |
| `kind` | String | Small label above the title; defaults to `Research post` when `venue` is present. |
| `venue` | String | Conference or publication label and citation metadata. |
| `subtitle` | String | Supporting text below the title on the post page and in listings; falls back to `extra.subtitle`. |
| Top-level `date` | Date | Visible publication date on the post page and in listings; also used for scholarly metadata. |
| `thumbnail` | URL string | Small image on the left of the post entry in listings. |
| `thumbnail_alt` | String | Alternative text for the listing image; defaults to empty. |
| `award` | String | Award note with an icon. |
| `authors` | Array of author tables | Authors in the supplied order; also used in citation metadata. |
| `affiliations` | Array of affiliation tables | Institution names below the authors. |
| `author_note` | String | Note below the byline, such as an explanation of equal contribution. Requires authors or affiliations. |
| `links` | Array of resource tables | Resource buttons in the supplied order; the first has accent styling. |
| `abstract` | String | Markdown rendered in the Abstract section. |
| `teaser` | Media table | Image or local video below the post header. |
| `gallery` | Array of media tables | Scrollable results gallery after the article. |
| `gallery_title` | String | Gallery heading; defaults to `Results gallery`. |
| `video` | Embed table | Embedded video after the gallery. |
| `poster` | Poster table | PDF viewer and a direct link after the video. |
| `related` | Array of related-work tables | Related Posts widget below On this page on the left; below the article on screens narrower than 992px. When omitted, shows up to five other listed pages from the parent section. Set `[]` to hide it. |
| `bibtex` | String | Literal BibTeX displayed in a code block with a copy button. |
| `paper` | URL string | PDF URL for `citation_pdf_url` metadata. Add a resource link separately to show a Paper button. |
| `doi` | String | DOI for citation metadata. |
| `social_image` | URL string | Open Graph image; enables the large-image Twitter card. |

The main Markdown content appears after the abstract and before the gallery. Its top-level table-of-contents headings appear in `On this page`, alongside configured sections. JavaScript also adds headings from Pandoc-generated HTML. Bibliography appears after Citation, with its original citation anchors preserved. Avoid custom heading IDs beginning with `post-`, which are reserved for the template.

All posts use the same responsive container widths: 540px from 576px, 720px from 768px, 960px from 992px, 1140px from 1200px, and 1320px from 1400px. Below 576px, the container fills the available width with space at both edges.

On screens at least 992px wide, `On this page` and Related Posts stick together below the main navigation as the reader scrolls. Long sidebars scroll within the available window height. JavaScript highlights the current section and groups the related widget with the contents; on smaller screens, it restores Related Posts below the article and citation. Without JavaScript, the links remain usable and the related widget keeps its static responsive placement.

### Authors, affiliations, and links

```toml
[extra.post]
kind = "Research paper"
venue = "Example Conference 2026"
subtitle = "A concise explanation of the contribution"
award = "Best paper award"
author_note = "* Equal contribution."
authors = [
  { name = "Alex Researcher", url = "https://example.org/alex", affiliations = "1,2", equal = true },
  { name = "Sam Researcher", affiliations = "2", equal = true },
]
affiliations = [
  { id = "1", name = "Example University" },
  { id = "2", name = "Research Institute" },
]
links = [
  { name = "Paper", url = "paper.pdf", icon_class = "bi bi-file-earmark-pdf" },
  { name = "Code", url = "https://github.com/example/post", icon_class = "bi bi-github" },
  { name = "Citation", url = "#post-citation" },
]
related = [
  { title = "Another post", url = "@/maps/public-self/another-post/index.md" },
]
```

An author requires `name`; `url`, `affiliations`, and `equal` are optional. `affiliations` is a display string such as `"1,2"`, not an array or an automatic lookup. `equal = true` adds an asterisk. An affiliation requires `name`; its displayed `id` is optional. A resource requires `name` and `url`; `icon_class` is optional and can use Persona's existing Bootstrap Icons or Academicons. A related-work entry requires `title` and `url`.

### Images and local videos

The teaser and gallery use the same media schema. Images require `src` and `alt`. Set `type = "video"` for a local video; omitting `type` renders an image. `caption` supports Markdown.

```toml
[extra.post.teaser]
src = "overview.svg"
alt = "Three stages of the proposed method, from input to prediction."
width = 1440
height = 800
caption = "**Overview.** A short explanation of the method."

[[extra.post.gallery]]
src = "comparison.png"
alt = "Side-by-side comparison of baseline and proposed results."
caption = "Comparison on the evaluation set."

[[extra.post.gallery]]
type = "video"
src = "demonstration.mp4"
title = "Method demonstration"
mime = "video/mp4"
poster = "demonstration-preview.jpg"
captions = "demonstration.en.vtt"
lang = "en"
caption_label = "English"
caption = "The method running on a sample sequence."
```

Article images are centered by default while respecting their intrinsic size and the available width. For images, `width` and `height` are optional intrinsic pixel dimensions. Use descriptive alt text, or an empty `alt` for a purely decorative image. The teaser image loads eagerly; gallery images load lazily. Videos expose native playback controls and do not autoplay. `title`, `mime`, `poster`, and the caption-track fields are optional. If `captions` is set, `lang` defaults to `en` and `caption_label` defaults to `English`.

The gallery supports touch and native horizontal scrolling. JavaScript adds previous/next buttons beside the results heading, an announced position, and left/right arrow keys when the gallery track has focus. It respects reduced-motion preferences and pauses videos when another slide becomes active. The gallery remains scrollable without JavaScript.

### Embedded video and PDF poster

```toml
[extra.post.video]
title = "Post presentation"
src = "https://www.youtube-nocookie.com/embed/VIDEO_ID"

[extra.post.poster]
title = "Conference poster"
src = "poster.pdf"
```

An embedded video requires `src` and `title`. Use the provider's embeddable URL, not a regular watch-page URL. Embed URLs are used verbatim and are not passed through the resource URL resolver. To display a local video, use a teaser, gallery item, or the `post.media` component.

A poster requires `src`; its section title defaults to `Poster`. The viewer includes a direct PDF link so the file remains available on browsers without inline PDF support.

### Abstract, citation, and metadata

```toml
title = "A research post"
description = "A one-sentence summary for link previews."
date = 2026-09-21
template = "post.html"

[extra.post]
abstract = """
Explain the question and contribution. **Markdown** is supported here.
"""
paper = "paper.pdf"
doi = "10.1234/example"
social_image = "social-preview.png"
bibtex = '''
@inproceedings{researcher2026post,
  title = {A research post},
  author = {Researcher, Alex},
  year = {2026}
}
'''
```

The template provides a canonical URL, description, Open Graph tags, Twitter card type, and scholarly citation tags for the title, authors, date, venue, DOI, and paper URL when supplied. The page description falls back to `config.description`.

BibTeX is rendered as text, without a citation-processing dependency. Long lines wrap to fit the screen while preserving the original citation text and line breaks for copying. JavaScript enables its copy button; if clipboard access fails, it selects the citation for manual copying and announces the fallback. Without JavaScript, the code block remains selectable. Use the separate [Citation Pipeline](../README.md#-citation-pipeline) if you need formatted references within the article itself.

## Resource URL rules

The `post.url` component resolves author links, resource links, related-work links, media sources, video posters and caption tracks, poster PDFs, `paper`, and `social_image`:

| Input | Resolution |
| --- | --- |
| `figure.png` or `media/clip.mp4` | Relative to the page's rendered permalink, including custom slugs. Use colocated assets. |
| `/assets/img/figure.png` | Through Zola's `get_url`; respects the configured site base URL and deployment subpath. Put this file in `static/assets/img/`. |
| `@/maps/public-self/other/index.md` | Through Zola's `get_url`; resolves a content page to its permalink. |
| `https://…`, `http://…`, `//…`, or `mailto:…` | Preserved as supplied. |
| `#post-citation` | Preserved as a same-page fragment. |

These rules apply to post front matter and components, not ordinary Markdown links. Use Zola's normal content-link syntax within Markdown. Do not put filesystem paths such as `static/` or `content/` into asset URLs.

## Reusable components

Tera 2 registers these components globally. On a post page, use them directly in Markdown where you want media within the article:

```tera
{{ <post.media page={page} item={page.extra.post.teaser} /> }}

{{ <post.gallery page={page} items={page.extra.post.gallery} id="method-gallery" title="Method comparison" /> }}

{{ <post.embed src="https://www.youtube-nocookie.com/embed/VIDEO_ID" title="Method walkthrough" /> }}

{{ <post.poster page={page} src="poster.pdf" title="Conference poster" /> }}
```

The first two examples reuse front matter already rendered by the template; use separate data under `extra` if you want an additional figure or gallery. Give each gallery a unique `id` when displaying more than one on a page. Set `heading_id="method-gallery-title"` on `post.gallery` to show its title beside the controls; otherwise the controls appear above the gallery without a visible heading. `post.media` accepts `eager={true}` when immediate image loading is appropriate. Other templates can use these components inside a `.post` wrapper by also loading `page-post.css` and, for gallery controls, `post.js`.

## Customization

The public template and component names are `post.html` and `post.*`; configure optional article features under `[extra.post]`. Styles use `.post` classes and reserved `post-` fragment IDs. The implementation lives in `templates/post.html`, `templates/components/post.html`, `sass/assets/stylesheet/pages/_post.scss`, and `static/assets/script/post.js`. `page-post.scss` compiles through Zola and includes the shared variables and final custom overrides. Adjust Persona's existing tokens or your `_custom.scss` overrides to change the post styling alongside the rest of your site.

The [Academic Project Page Template](https://github.com/eliahuhorwitz/Academic-project-page-template) informed the feature set. Persona's post layout, Sass, and JavaScript are original implementations; no upstream stylesheet is copied.

## Development checks

From the theme directory, run `python3 tests/test_posts.py` to build isolated minimal and populated examples and check their rendered output. The tests require Zola and Python 3, and leave the theme's content unchanged. They cover template rendering and URL handling; check actual media playback and responsive interactions in a browser when changing the media components or script.
