#!/usr/bin/env python3
"""Build post fixtures in isolation: python3 tests/test_posts.py.

Requires Zola 0.23+. Uses only the Python standard library and skips external
link checks. Pandoc enables the citation-pipeline fixtures. Media fixtures test
generated markup and URLs, not playback.
"""

import base64
import json
from html.parser import HTMLParser
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest
from urllib.parse import parse_qs, urlparse


THEME = Path(__file__).resolve().parents[1]
BASE = "https://example.test/persona/"
FULL_URL = BASE + "research/custom-output/"
TITLE = 'Research <script>alert("title")</script> & "quotes"'
SUBTITLE = 'A subtitle <img src=x onerror=alert(2)> & "quotes"'
AUTHOR = 'A <img src=x onerror=alert(1)> & B'
BIBTEX = '@misc{example, title={<script>alert("citation")</script> & Research}}'
OUTLINE_TITLE = 'Sections <img src=x onerror=alert("outline")> & "details"'
GALLERY_CATEGORY = 'Controls & Robotics / "Soft" [arm]'
CARD_DESCRIPTION = 'Blog card description <img src=x onerror=alert(3)> & details.'
COPY_RESOURCE_NAME = 'Citation <img src=x onerror=alert(4)> & details'
PAGE_BREADCRUMB_TITLE = 'Short <img src=x onerror=alert(5)> & "breadcrumb"'
SECTION_BREADCRUMB_TITLE = 'Notes <img src=x onerror=alert(6)> & "writing"'
MEDIA_ALT = 'Figure <img src=x onerror=alert(7)> & "alt"'
# Quoted titles use the normal internal-link renderer. Zola 0.23.4's optional
# external-link renderer does not escape titles; external URL/query coverage
# remains separate so this fixture tests the figure renderer's behavior.
MEDIA_CAPTION = 'A **bold** caption and [source](/test-assets/shared.svg?a=1&b=2 \'Quoted "title"\'), [external source](https://example.test/figure?a=1&b=2), with `<img src=x onerror=alert(7)>` and `\\commands`.'
SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="2" height="2"></svg>'
# A valid 8-by-4 RGBA PNG supplies real pixels for Zola's resizing path.
PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAgAAAAECAYAAACzzX7wAAAAEklEQVR4nGP4z8DwHx9moL0CAHD0P8F+ACg+AAAAAElFTkSuQmCC')


class Document(HTMLParser):
    """Collect decoded attributes and text without third-party HTML libraries."""
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.elements = []
        self.ancestors = []
        self._stack = []
        self._text_nodes = []
        self.text = ""
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        self.elements.append((tag, attributes))
        self.ancestors.append(tuple(self._stack))
        if tag not in {"area", "base", "br", "col", "embed", "hr", "img", "input",
                       "link", "meta", "param", "source", "track", "wbr"}:
            self._stack.append((tag, attributes))

    def handle_endtag(self, tag):
        for index in range(len(self._stack) - 1, -1, -1):
            if self._stack[index][0] == tag:
                del self._stack[index:]
                break

    def handle_data(self, data):
        self.text += data
        self._text_nodes.append((tuple(self._stack), data))

    def find(self, tag=None, **attributes):
        return [attrs for element_tag, attrs in self.elements
                if (tag is None or tag == element_tag)
                and all(key in attrs and attrs[key] == value for key, value in attributes.items())]

    def with_class(self, name):
        return [attrs for _, attrs in self.elements
                if name in attrs.get("class", "").split()]

    def descendants(self, attributes):
        return [element for element, ancestors in zip(self.elements, self.ancestors)
                if any(parent is attributes for _, parent in ancestors)]

    def text_content(self, attributes):
        return "".join(data for ancestors, data in self._text_nodes
                       if any(parent is attributes for _, parent in ancestors))


class PostIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        zola = shutil.which("zola")
        if zola is None:
            raise unittest.SkipTest("Zola 0.23+ is required for integration tests")
        cls.temporary = tempfile.TemporaryDirectory(prefix="persona-post-tests-")
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.site = Path(cls.temporary.name)
        shutil.copy2(THEME / "config.toml", cls.site / "config.toml")
        for directory in ("templates", "sass", "static", "content"):
            shutil.copytree(THEME / directory, cls.site / directory)

        # Exercise runtime defaults independently of sample config values.
        default_config = re.sub(r"(?m)^(?:home_items_limit|outline_title)\s*=.*\n?", "",
                                (cls.site / "config.toml").read_text(encoding="utf-8"))
        cls.write("config.toml", default_config)
        shutil.rmtree(cls.site / "content/posts", ignore_errors=True)
        cls.write("content/posts/_index.md", f'''+++
title = "Fixture posts"
sort_by = "weight"
page_template = "post.html"
[extra]
breadcrumb_title = {json.dumps('  ' + SECTION_BREADCRUMB_TITLE + '  ')}
order = 1
type = "posts"
icon_class = "bi bi-journal-richtext"
+++
A short **post introduction**.
''')
        listing_posts = [
            ("z-explicit", 'path = "research/nested-post"',
             'description = "Explicit thumbnail description"',
             'thumbnail = "thumb.svg"\nthumbnail_alt = "Explicit thumbnail"\n'
             'teaser = { src = "unused.svg", alt = "Unused teaser" }'),
            ("a-image", 'slug = "renamed-image"',
             'description = "Image teaser description"',
             'teaser = { src = "thumb.svg", alt = "Image teaser thumbnail" }'),
            ("m-video", "", 'description = "Video poster description"',
             'teaser = { type = "video", src = "clip.mp4", '
             'poster = "/test-assets/shared.svg", title = "Video poster" }'),
            ("b-no-image", "", 'description = "Post without a thumbnail"',
             'teaser = { type = "video", src = "clip.mp4", title = "No poster" }'),
            ("c-excerpt", "", "", "draft = false"),
        ]
        listing_categories = [
            ["Research & Methods", GALLERY_CATEGORY],
            ["Research & Methods"],
            ["Sequence modeling"],
            ["Archive only"],
            [],
        ]
        for weight, (folder, location, description, post) in enumerate(listing_posts, 1):
            title = TITLE if weight == 1 else f"Listing post {weight}"
            date = "date = 2025-03-04" if weight == 1 else ""
            subtitle = ('subtitle = "Shared subtitle should be overridden"' if weight == 1
                        else 'subtitle = "Shared post subtitle"' if weight == 2 else "")
            if weight == 1:
                post += "\nsubtitle = " + json.dumps(SUBTITLE)
            breadcrumb = 'breadcrumb_title = "  Short research note  "' if weight == 1 else ""
            cls.write(f"content/posts/{folder}/index.md", f'''+++
title = {json.dumps(title)}
weight = {weight * 2}
{date}
{location}
{description}
[taxonomies]
categories = {json.dumps(listing_categories[weight - 1])}
[extra]
{breadcrumb}
excerpt = "Fallback listing excerpt {weight}"
{subtitle}
[extra.post]
{post}
+++
Fixture post body.
''')
            cls.write(f"content/posts/{folder}/thumb.svg", SVG)
            cls.write(f"content/posts/{folder}/unused.svg", SVG)
            cls.write(f"content/posts/{folder}/clip.mp4", "structural video fixture")

        cls.write("content/test-blog/_index.md", '''+++
title = "Fixture blog"
sort_by = "date"
page_template = "post.html"
[extra]
breadcrumb_title = ""
order = 2
type = "posts"
icon_class = "bi bi-journal"
+++
''')
        cls.write("content/test-blog/full.md", f'''+++
title = {json.dumps(TITLE)}
date = 2025-03-04
description = {json.dumps('  ' + CARD_DESCRIPTION + '  ')}
[taxonomies]
tags = ["Shared fixture", "Description behavior"]
categories = {json.dumps(listing_categories[0])}
[extra]
excerpt = "Legacy blog excerpt must not appear"
subtitle = {json.dumps(SUBTITLE)}
thumbnail = "/test-assets/shared.svg"
thumbnail_alt = "Blog listing thumbnail"
+++
Blog fixture body.
''')
        cls.write("content/test-blog/minimal.md", '''+++
title = "Blog without optional fields"
date = 2025-03-03
[taxonomies]
tags = ["Description behavior"]
categories = ["Personal writing"]
[extra]
excerpt = "Legacy blog excerpt must not appear"
+++
Generated summary preview without a description.

<!-- more -->

Generated body preview without a description.
''')
        for number, date in enumerate(("2025-03-02", "2025-03-01", "2025-02-28"), 3):
            description = {3: 'description = ""',
                           4: 'description = ' + json.dumps(" \t\n ")}.get(number, "")
            body = (f"Generated body preview {number} without a description." if number == 5
                    else f"Generated summary preview {number} without a description.\n\n"
                         f"<!-- more -->\n\nGenerated body preview {number} without a description.")
            thumbnail = ('[extra.post]\nthumbnail = "/test-assets/shared.svg"' if number == 3 else "")
            cls.write(f"content/test-blog/entry-{number}.md", f'''+++
title = "Blog entry {number}"
date = {date}
{description}
[taxonomies]
tags = ["Description behavior"]
categories = {json.dumps(["Research & Methods"] if number == 3 else [])}
{thumbnail}
+++
{body}
''')
        for folder, date in (("draft-first", "2025-03-06"),
                             ("draft-middle", "2025-03-03T12:00:00Z")):
            cls.write(f"content/test-blog/{folder}.md", f'''+++
title = "Unlisted blog {folder}"
date = {date}
template = "post.html"
[taxonomies]
tags = ["Shared fixture", "Draft-only fixture"]
categories = ["Draft-only gallery"]
[extra.post]
draft = true
+++
Unlisted post in a normal blog collection.
''')

        cls.write("content/test-category/_index.md", '''+++
title = "Fixture categories"
[extra]
type = "category"
order = 3
icon_class = "bi bi-collection"
+++
''')
        for folder, order in (("z-first", 10), ("a-second", 20), ("m-third", 30),
                              ("b-fourth", 40), ("c-fifth", 50), ("hidden-zero", 0),
                              ("hidden-missing", None)):
            order_field = f"order = {order}" if order is not None else ""
            breadcrumb = 'breadcrumb_title = ' + json.dumps(" \t\n ") if folder == "z-first" else ""
            cls.write(f"content/test-category/{folder}/_index.md", f'''+++
title = "Card {folder}"
[extra]
{breadcrumb}
type = "posts"
thumbnail = "thumb.svg"
{order_field}
+++
''')
            cls.write(f"content/test-category/{folder}/thumb.svg", SVG)

        # Put drafts before and between published posts so filtering must
        # happen before the homepage limit is applied.
        for folder, weight, location in (
                ("draft-first", 1, 'path = "research/unlisted-first"'),
                ("draft-middle", 5, 'slug = "unlisted-middle"')):
            cls.write(f"content/posts/{folder}/index.md", f'''+++
title = "Unlisted {folder}"
weight = {weight}
{location}
[taxonomies]
categories = ["Draft-only gallery"]
[extra.post]
draft = true
teaser = {{ src = "thumb.svg", alt = "Unlisted post thumbnail" }}
+++
Draft post body remains available through its direct URL.
''')
            cls.write(f"content/posts/{folder}/thumb.svg", SVG)

        cls.write("content/test-minimal.md", '+++\ntitle = "Minimal post"\ntemplate = "post.html"\n+++\nNo extra table.')
        cls.write("content/test-category-only.md", '''+++
title = "Categorized post"
template = "post.html"
[taxonomies]
categories = ["Personal reflections"]
+++
A post with a category and no publication venue.
''')
        cls.write("content/test-venue-only.md", '''+++
title = "Published post"
template = "post.html"
[taxonomies]
categories = []
[extra.post]
venue = "Example Journal"
+++
A publication venue without category labels.
''')
        cls.write("content/test-legacy-kind.md", '''+++
title = "Post with an obsolete label"
template = "post.html"
[extra.post]
kind = "Obsolete kind label"
+++
A legacy label does not appear in the post header.
''')
        for name, bibtex in (("empty", ""), ("whitespace", " \n\t ")):
            cls.write(f"content/test-bibtex-{name}.md", f'''+++
title = "Post with {name} BibTeX"
template = "post.html"
[extra.post]
bibtex = {json.dumps(bibtex)}
links = [{{ name = "Copy reference", action = "copy-bibtex", icon_class = "bi bi-clipboard" }}]
+++
No usable citation has been provided.
''')
        cls.write("content/test-resource-no-bibtex.md", '''+++
title = "Copy resource without BibTeX"
template = "post.html"
[extra.post]
links = [{ name = "Copy reference", action = "copy-bibtex", icon_class = "bi bi-clipboard" }]
+++
An unconfigured copy action has no resource control.
''')
        cls.write("content/test-resource-mixed.md", '''+++
title = "Ordinary resource beside an unconfigured copy"
template = "post.html"
[extra.post]
links = [
  { name = "Copy reference", action = "copy-bibtex", icon_class = "bi bi-clipboard" },
  { name = "BibTeX", url = "https://example.test/bibtex", icon_class = "bi bi-box-arrow-up-right" }
]
+++
URL resources do not infer actions from their names.
''')
        cls.write("content/test-ordinary.md", '+++\ntitle = "Ordinary page"\ntemplate = "page.html"\n+++\nOrdinary page body.')
        cls.write("content/test-slug/index.md", '''+++
title = "Changed slug"
slug = "changed-slug"
template = "post.html"
[extra.post]
thumbnail = "   "
teaser = { src = "plot.svg", alt = "Colocated plot" }
+++
Slug fixture.
''')
        cls.write("content/test-slug/plot.svg", SVG)
        for name, social_image in (("empty", ""), ("whitespace", " \t\n "),
                                   ("external", "  https://images.example.test/social.png?a=1&b=2  ")):
            breadcrumb = ('[extra]\nbreadcrumb_title = ' + json.dumps(
                "" if name == "empty" else " \t\n ")) if name != "external" else ""
            cls.write(f"content/test-social-{name}.md", f'''+++
title = "Social image {name}"
template = "post.html"
{breadcrumb}
[extra.post]
thumbnail = "/test-assets/shared.svg"
social_image = {json.dumps(social_image)}
+++
Social image metadata fixture.
''')
        cls.write("content/test-social-details/index.md", f'''+++
title = "Dedicated social image"
template = "post.html"
path = "research/social-details"
[extra.post]
social_image = "social.png?v=new&source=card"
social_image_width = 8
social_image_height = 4
social_image_type = "image/png"
social_image_alt = {json.dumps(MEDIA_ALT)}
thumbnail = "/test-assets/shared.svg"
teaser = {{ src = "/test-assets/shared.svg", alt = "Different article image", width = 2, height = 2 }}
+++
The social image has different dimensions from the article image.
''')
        cls.write("content/test-social-details/social.png", PNG)
        quote = json.dumps
        cls.write("content/test-full/index.md", f'''+++
title = {quote(TITLE)}
description = "Specific post description & metadata"
date = 2025-03-04
slug = "ignored-slug"
path = "research/custom-output"
template = "post.html"
[taxonomies]
categories = ["Research post", "Research & Methods"]
tags = ["Research & Methods", "Equations"]
[extra]
breadcrumb_title = {quote('  ' + PAGE_BREADCRUMB_TITLE + '  ')}
[extra.post]
venue = "Example Conference 2025"
subtitle = {quote(SUBTITLE)}
award = "Example award"
doi = "10.1234/example"
paper = "paper.pdf"
social_image = "plot.svg"
thumbnail = "/test-assets/shared.svg"
authors = [{{ name = {quote(AUTHOR)}, url = "https://example.test/author?a=1&b=2", affiliations = "1,2", equal = true }}, {{ name = "Second author" }}]
affiliations = [{{ id = "1", name = "Example institute" }}, {{ id = "2", name = "Other institute" }}]
author_note = "Equal contribution."
links = [
  {{ name = "Relative paper", url = "paper.pdf", icon_class = "bi bi-file-earmark-pdf" }},
  {{ name = {quote(COPY_RESOURCE_NAME)}, action = "copy-bibtex", icon_class = "bi bi-clipboard" }},
  {{ name = "Root asset", url = "/test-assets/shared.svg" }},
  {{ name = "Internal page", url = "@/test-ordinary.md" }},
  {{ name = "External HTTPS", url = "https://example.test/code?a=1&b=2" }},
  {{ name = "External HTTP", url = "http://example.test/code" }},
  {{ name = "Protocol relative", url = "//example.test/code" }},
  {{ name = "Email", url = "mailto:research@example.test" }},
  {{ name = "BibTeX", url = "https://example.test/bibtex", icon_class = "bi bi-box-arrow-up-right" }},
  {{ name = "Citation", url = "#post-citation" }}
]
related = [{{ title = "Minimal post", url = "@/test-minimal.md", date = "2024-11-09" }}]
abstract = "A **formatted** abstract."
teaser = {{ src = "plot.svg", alt = "Teaser image", width = 2, height = 2, caption = "A **teaser** caption.", full_size = true }}
gallery_title = "Research results"
gallery = [
  {{ src = "/test-assets/shared.svg", alt = "Gallery image", caption = "Image result.", full_size = true }},
  {{ type = "video", src = "clip.mp4", mime = "video/mp4", poster = "plot.svg", title = "Video result", captions = "captions.vtt", lang = "en", caption_label = "English", caption = "Video result caption." }}
]
video = {{ src = "https://www.youtube-nocookie.com/embed/example", title = "Presentation video" }}
poster = {{ src = "poster.pdf", title = "Conference poster" }}
bibtex = {quote(BIBTEX)}
+++
## Method

The post body supports normal Markdown.
''')
        cls.write("content/test-full/plot.svg", SVG)
        cls.write("static/test-assets/shared.svg", SVG)
        # These files exercise asset copying/URL generation only.
        cls.write("content/test-full/clip.mp4", "structural video fixture")
        cls.write("content/test-full/paper.pdf", "%PDF-1.4\nstructural PDF fixture")
        cls.write("content/test-full/poster.pdf", "%PDF-1.4\nstructural PDF fixture")
        cls.write("content/test-full/captions.vtt", "WEBVTT\n\n00:00.000 --> 00:01.000\nCaption.\n")
        cls.write("templates/test-legacy-breadcrumbs.html", '''{% extends "base.html" %}
{% block main %}{{ <render.breadcrumbs crumbs={["posts", "legacy"]} /> }}{% endblock main %}
''')
        cls.write("content/test-legacy-breadcrumbs.md", '''+++
title = "Legacy breadcrumbs"
template = "test-legacy-breadcrumbs.html"
+++
''')
        cls.write("content/test-media/index.md", f'''+++
title = "Shared image renderer"
template = "post.html"
path = "research/media-fixture"
[extra]
vector = {{ src = "vector.svg", alt = "Canonical SVG", width = 2, height = 2, caption = "Canonical **figure**.", full_size = false }}
+++
{{{{ <media.image page={{page}} path="raster.png" width={{4}} alt={json.dumps(MEDIA_ALT)} caption={json.dumps(MEDIA_CAPTION)} full_size={{true}} /> }}}}

{{{{ <media.image page={{page}} path="raster.png" alt="Original bitmap" full_size={{false}} eager={{true}} /> }}}}

{{{{ <media.image page={{page}} path="raster.png" width={{4}} alt="Legacy resized bitmap" /> }}}}

{{{{ <media.figure page={{page}} item={{page.extra.vector}} /> }}}}
''')
        cls.write("content/test-media/raster.png", PNG)
        cls.write("content/test-media/vector.svg", SVG)
        cls.write("content/test-media-slug/index.md", '''+++
title = "SVG media with a custom slug"
template = "post.html"
slug = "media-custom-slug"
+++
{{ <media.image page={page} path="vector.svg" alt="Original SVG" full_size={true} /> }}
''')
        cls.write("content/test-media-slug/vector.svg", SVG)
        cls.pandoc = shutil.which("pandoc")
        if cls.pandoc:
            for folder, has_bibtex in (("test-citations", True),
                                       ("test-references-only", False)):
                citation = 'bibtex = "@article{this-post, title={This post}}"' if has_bibtex else ""
                cls.write(f"content/{folder}/index.src.md", r'''+++
title = "Citation and math fixture"
date = 2025-04-05
template = "post.html"
[taxonomies]
tags = ["Equations"]
[extra]
bibliography = "references.bib"
[extra.tex.macros]
'\RR' = '\mathbb{R}'
[extra.post]
gallery = [{ src = "/test-assets/shared.svg", alt = "Result after the prose" }]
''' + citation + r'''
+++
## Cited method

This method builds on prior research [@fixture2025].
Its domain is $x \in \RR$ and its display equation is:

$$\int_0^1 x\,dx = \frac{1}{2}.$$

### Implementation details

A note preserves the original explanation.[^detail]

[^detail]: This is the explanatory footnote.

```{=html}
{{ <media.image page={page} path="raster.png" width={4} alt="Pandoc figure" caption="A **Pandoc** figure." full_size={true} /> }}
```
''')
                cls.write(f"content/{folder}/raster.png", PNG)
                cls.write(f"content/{folder}/references.bib", '''@article{fixture2025,
  title = {A cited fixture for post pages},
  author = {Example, Ada},
  journal = {Journal of Reproducible Fixtures},
  year = {2025}
}
''')
                cls.process_source(folder)
            cls.write("content/test-pandoc-without-references/index.src.md", '''+++
title = "Pandoc without references"
template = "post.html"
+++
## Frontmatter example

```toml
+++
title = "An example inside the body"
+++
```

The explanation after the example must remain in the page.
''')
            cls.process_source("test-pandoc-without-references")
        # Previously generated pages must remain usable until next preprocessing.
        cls.write("content/test-legacy-bibliography.md", '''+++
title = "Previously generated citation page"
template = "post.html"
[extra.post]
bibtex = "@misc{legacy, title={Legacy post}}"
+++
<h2 id="old-method">Old method</h2>
<p>A <span class="citation" data-cites="old"><a href="#ref-old" role="doc-biblioref">citation</a></span>.</p>
<div id="refs" class="references csl-bib-body" role="doc-bibliography">
<h2 id="bibliography" class="unnumbered">Bibliography</h2>
<div id="ref-old" class="csl-entry">Existing reference.</div>
</div>
''')
        for arguments in (("check", "--skip-external-links"),
                          ("build", "--base-url", BASE)):
            result = subprocess.run([zola, *arguments], cwd=cls.site, text=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    timeout=60, check=False)
            if result.returncode:
                raise AssertionError(f"zola {' '.join(arguments)} failed:\n{result.stdout}")
        for limit in (2, 0, 5, -1):
            # Reuse the limit builds to exercise site-wide outline labels.
            outline_titles = {2: "  Contents & context  ", 0: " \t ", 5: OUTLINE_TITLE}
            settings = f"home_items_limit = {limit}"
            if limit in outline_titles:
                settings += "\noutline_title = " + json.dumps(outline_titles[limit])
            cls.write("config.toml", default_config.replace(
                "[extra.persona]", f"[extra.persona]\n{settings}", 1))
            result = subprocess.run(
                [zola, "build", "--base-url", BASE, "--output-dir", f"public-limit-{limit}"],
                cwd=cls.site, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                timeout=60, check=False)
            if result.returncode:
                raise AssertionError(f"zola build with limit {limit} failed:\n{result.stdout}")
        cls.write("config.toml", default_config)

        # A normal build must still emit every direct post URL when the
        # complete collection is unlisted.
        for folder, *_ in listing_posts:
            fixture = cls.site / f"content/posts/{folder}/index.md"
            contents = fixture.read_text(encoding="utf-8")
            if "draft = false" in contents:
                contents = contents.replace("draft = false", "draft = true")
            else:
                contents = contents.replace("[extra.post]", "[extra.post]\ndraft = true", 1)
            fixture.write_text(contents, encoding="utf-8")
        result = subprocess.run(
            [zola, "build", "--base-url", BASE, "--output-dir", "public-all-drafts"],
            cwd=cls.site, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            timeout=60, check=False)
        if result.returncode:
            raise AssertionError(f"zola build with all drafts failed:\n{result.stdout}")

    @classmethod
    def write(cls, relative, contents):
        destination = cls.site / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(contents, bytes):
            destination.write_bytes(contents)
        else:
            destination.write_text(contents, encoding="utf-8")

    @classmethod
    def process_source(cls, folder):
        result = subprocess.run([
            "bash", str(THEME / "scripts/process_post.sh"),
            str(cls.site / f"content/{folder}/index.src.md"),
            str(THEME / "citation-style/ieee.csl"),
            str(THEME / "citation-style"),
        ], cwd=cls.site, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, timeout=60, check=False)
        if result.returncode:
            raise AssertionError(f"Pandoc post fixture failed:\n{result.stdout}")

    def document(self, output, directory="public"):
        return Document((self.site / directory / output / "index.html").read_text(encoding="utf-8"))

    def single(self, document, tag, **attributes):
        matches = document.find(tag, **attributes)
        self.assertEqual(len(matches), 1, (tag, attributes, matches))
        return matches[0]

    def copy_buttons_within(self, document, container):
        return [attrs for tag, attrs in document.descendants(container)
                if tag == "button" and "data-copy-citation" in attrs]

    def figure_for_image(self, document, image):
        figures = [figure for figure in document.with_class("post__figure")
                   if ("img", image) in document.descendants(figure)]
        self.assertEqual(len(figures), 1)
        self.assertFalse(any(tag == "pre" for tag, _ in document.descendants(figures[0])),
                         "Generated media must remain HTML, rather than escaped Markdown code")
        return figures[0]

    def within_section(self, document, section_id, class_name):
        section = self.single(document, "section", id=section_id)
        return [attrs for _, attrs in document.descendants(section)
                if class_name in attrs.get("class", "").split()]

    def section_links(self, document, section_id, class_name="post-card__link"):
        return [attrs["href"] for attrs in self.within_section(
            document, section_id, class_name)]

    def view_all_links(self, document, section_id):
        section = self.single(document, "section", id=section_id)
        return [attrs["href"] for tag, attrs in document.descendants(section)
                if tag == "a" and document.text_content(attrs).strip().startswith("View all")]

    def section_gallery(self, document, section_id):
        galleries = self.within_section(document, section_id, "post-gallery")
        self.assertEqual(len(galleries), 1)
        return galleries[0]

    def gallery_filter_values(self, document, gallery):
        return [attrs["data-post-filter"] for tag, attrs in document.descendants(gallery)
                if tag == "button" and "data-post-filter" in attrs]

    def test_minimal_post_needs_no_extra_table(self):
        page = self.document("test-minimal")
        self.single(page, "h1", id="post-title")
        self.assertIn("Minimal post", page.text)
        self.assertFalse(page.with_class("post__byline"))
        self.assertFalse(page.with_class("article-meta__date"))
        self.assertFalse(page.with_class("post__subtitle"))
        self.assertFalse(page.with_class("post__eyebrow"))
        self.assertFalse(page.with_class("post__contents"))
        self.assertFalse(page.find(id="post-citation"))
        self.assertFalse(page.find(id="preloader"))
        self.assertEqual(len(page.with_class("nav-toggle")), 1)
        self.single(page, "header", id="header")
        self.assertFalse(page.with_class("post-bar"))
        self.single(page, "nav", **{"aria-label": "Breadcrumb"})
        self.single(page, "script", src=BASE + "assets/script/home.js")
        self.single(page, "script", src=BASE + "vendor/aos/aos.js")
        self.single(page, "link", rel="canonical", href=BASE + "test-minimal/")
        self.single(page, "link", href=BASE + "assets/stylesheet/page-post.css")
        self.single(page, "script", src=BASE + "assets/script/post.js")
        self.assertTrue((self.site / "public/assets/stylesheet/page-post.css").is_file())

    def test_category_labels_link_to_taxonomies_and_preserve_the_venue(self):
        page = self.document("research/custom-output")
        eyebrow = self.single(page, "div", **{"class": "post__eyebrow"})
        categories = self.single(page, "ul", **{
            "class": "taxonomy-labels taxonomy-labels--categories", "aria-label": "Categories"})
        self.assertIn(("ul", categories), page.descendants(eyebrow))
        items = [attrs for tag, attrs in page.descendants(categories)
                 if tag == "li" and attrs.get("class") == "taxonomy-labels__item"]
        self.assertEqual(len(items), 2)
        links = [attrs for tag, attrs in page.descendants(categories) if tag == "a"]
        self.assertTrue(all(link.get("class") == "taxonomy-labels__link" for link in links))
        for item, link in zip(items, links):
            self.assertEqual(page.descendants(item), [("a", link)])
        self.assertEqual([link["href"] for link in links], [
            BASE + "categories/research-post/", BASE + "categories/research-methods/"])
        self.assertEqual([page.text_content(link) for link in links],
                         ["Research post", "Research & Methods"])
        self.assertNotIn(",", page.text_content(categories))
        venue = self.single(page, "span", **{"class": "post__venue"})
        self.assertIn(("span", venue), page.descendants(eyebrow))
        self.assertEqual(" ".join(page.text_content(venue).split()), "/ Example Conference 2025")

        category_only = self.document("test-category-only")
        eyebrow = self.single(category_only, "div", **{"class": "post__eyebrow"})
        self.assertEqual(" ".join(category_only.text_content(eyebrow).split()), "Personal reflections")
        self.single(category_only, "a", **{"class": "taxonomy-labels__link",
                    "href": BASE + "categories/personal-reflections/"})
        self.assertFalse(category_only.with_class("post__venue"))

    def test_venue_without_categories_has_no_invented_label_or_separator(self):
        page = self.document("test-venue-only")
        eyebrow = self.single(page, "div", **{"class": "post__eyebrow"})
        self.assertEqual(page.text_content(eyebrow).strip(), "Example Journal")
        venue = self.single(page, "span", **{"class": "post__venue"})
        self.assertEqual(page.descendants(eyebrow), [("span", venue)])
        self.assertFalse(page.with_class("taxonomy-labels--categories"))
        self.single(page, "meta", name="citation_conference_title", content="Example Journal")

    def test_obsolete_kind_does_not_supply_a_header_label(self):
        page = self.document("test-legacy-kind")
        self.assertFalse(page.with_class("post__eyebrow"))
        self.assertNotIn("Obsolete kind label", page.text)

    def test_generated_pages_load_only_current_post_assets(self):
        obsolete = {"project.js", "page-project.css", "post.css", "page-blog.css"}
        public = self.site / "public"
        self.assertTrue((public / "assets/script/post.js").is_file())
        self.assertTrue((public / "assets/stylesheet/page-post.css").is_file())
        self.assertFalse((public / "assets/script/project.js").exists())
        self.assertFalse((public / "assets/stylesheet/page-project.css").exists())
        for path in public.rglob("*.html"):
            page = Document(path.read_text(encoding="utf-8"))
            for _, attrs in page.elements:
                with self.subTest(page=str(path.relative_to(public)), element=attrs):
                    self.assertNotIn("project", attrs.get("class", ""))
                    self.assertNotIn("project", attrs.get("id", ""))
                    self.assertFalse(any(name.startswith("data-project") for name in attrs))
            loaded = [attrs["src"] for attrs in page.find("script") if "src" in attrs]
            loaded.extend(attrs["href"] for attrs in page.find("link", rel="stylesheet"))
            for url in loaded:
                with self.subTest(page=str(path.relative_to(public)), asset=url):
                    segments = urlparse(url).path.split("/")
                    self.assertFalse(any(segment.startswith("__old_") for segment in segments))
                    self.assertNotIn(segments[-1], obsolete)

    def test_outline_title_uses_site_config_with_an_accessible_plain_text_label(self):
        for directory, expected in (("public", "Outline"),
                                    ("public-limit-2", "Contents & context"),
                                    ("public-limit-0", "Outline"),
                                    ("public-limit-5", OUTLINE_TITLE)):
            with self.subTest(directory=directory):
                page = self.document("research/custom-output", directory)
                navigation = self.single(page, "nav", **{"aria-labelledby": "post-outline-title"})
                disclosure = self.single(page, "details", **{"data-post-outline": None})
                toggle = self.single(page, "summary", **{"class": "post__outline-toggle"})
                title = self.single(page, "span", id="post-outline-title")
                self.assertNotIn("open", disclosure, "The native outline starts folded without JavaScript")
                self.assertIn(("summary", toggle), page.descendants(disclosure))
                self.assertIn(("nav", navigation), page.descendants(disclosure))
                self.assertIn(("span", title), page.descendants(toggle))
                self.assertEqual(page.text_content(title).strip(), expected)
                self.assertFalse(page.descendants(title), "Outline titles must remain plain text")
                self.assertIn(FULL_URL + "#method", [attrs.get("href") for tag, attrs in
                                                   page.descendants(navigation) if tag == "a"])
                self.assertFalse(any("onerror" in attrs for _, attrs in page.elements))

    def test_full_optional_sections_and_media(self):
        page = self.document("research/custom-output")
        for section in ("post-abstract", "method", "post-results",
                        "post-video", "post-poster", "post-citation"):
            self.assertTrue(page.find(id=section), section)
        self.assertEqual(len(page.with_class("post__authors")), 1)
        self.assertEqual(len(page.with_class("post__slide")), 2)
        self.single(page, "img", alt="Teaser image", src=FULL_URL + "plot.svg",
                    loading="eager", width="2", height="2")
        self.single(page, "img", alt="Gallery image", src=BASE + "test-assets/shared.svg",
                    loading="lazy")
        video = self.single(page, "video", poster=FULL_URL + "plot.svg")
        self.assertIn("controls", video)
        self.assertIn("playsinline", video)
        self.single(page, "source", src=FULL_URL + "clip.mp4", type="video/mp4")
        self.single(page, "track", src=FULL_URL + "captions.vtt", kind="captions", srclang="en")
        self.single(page, "iframe", src="https://www.youtube-nocookie.com/embed/example",
                    title="Presentation video", loading="lazy")
        self.single(page, "object", data=FULL_URL + "poster.pdf", type="application/pdf")
        self.single(page, "div", **{"data-gallery-controls": None, "hidden": None})
        for container in (page.with_class("share-menu")[0],
                          self.single(page, "section", id="post-citation")):
            copy_buttons = self.copy_buttons_within(page, container)
            self.assertEqual(len(copy_buttons), 1)
            button = copy_buttons[0]
            self.assertIn("hidden", button)
            self.assertEqual(button.get("aria-controls"), "post-bibtex")
            self.assertEqual(button.get("data-copy-feedback"), "BibTex Copied!")
            labels = [attrs for tag, attrs in page.descendants(button)
                      if tag == "span" and "data-copy-label" in attrs]
            self.assertEqual(len(labels), 1)
            self.assertEqual(page.text_content(labels[0]), "Copy BibTeX")
            self.assertFalse(page.descendants(labels[0]))
            icons = [attrs for tag, attrs in page.descendants(button) if tag == "i"]
            self.assertEqual(icons, [{"class": "bi bi-copy", "aria-hidden": "true"}])
            statuses = [attrs for tag, attrs in page.descendants(container)
                        if tag == "p" and attrs.get("role") == "status"]
            self.assertEqual(len(statuses), 1)
            self.assertIn("visually-hidden", statuses[0].get("class", "").split())
            self.assertEqual(statuses[0].get("aria-live"), "polite")
            self.assertNotIn("hidden", statuses[0])
            self.assertEqual(page.text_content(statuses[0]), "")
        self.assertNotIn("BibTex Copied!", page.text, "Success feedback appears only after copying")
        for asset in ("plot.svg", "clip.mp4", "captions.vtt", "paper.pdf", "poster.pdf"):
            self.assertTrue((self.site / "public/research/custom-output" / asset).is_file(), asset)

    def test_base_path_custom_path_slug_and_link_resolution(self):
        page = self.document("research/custom-output")
        self.single(page, "link", rel="canonical", href=FULL_URL)
        hrefs = {attributes.get("href") for attributes in page.find("a")}
        for expected in (BASE.rstrip("/"), FULL_URL + "paper.pdf", BASE + "test-assets/shared.svg",
                         BASE + "test-ordinary/", BASE + "test-minimal/",
                         "https://example.test/code?a=1&b=2", "http://example.test/code",
                         "//example.test/code", "mailto:research@example.test", "#post-citation"):
            self.assertIn(expected, hrefs)
        slug_page = self.document("changed-slug")
        self.single(slug_page, "img", src=BASE + "changed-slug/plot.svg")
        self.assertTrue((self.site / "public/changed-slug/plot.svg").is_file())

    def test_media_images_keep_original_lightbox_links_and_render_rich_captions(self):
        page = self.document("research/media-fixture")
        image = self.single(page, "img", alt=MEDIA_ALT)
        figure = self.figure_for_image(page, image)
        triggers = [attrs for tag, attrs in page.descendants(figure)
                    if tag == "a" and "data-post-lightbox-trigger" in attrs]
        self.assertEqual(len(triggers), 1)
        trigger = triggers[0]
        self.assertEqual(trigger["href"], BASE + "research/media-fixture/raster.png")
        self.assertEqual(trigger["aria-label"], "View full-size image: " + MEDIA_ALT)
        self.assertEqual(page.descendants(trigger), [("img", image)])
        self.assertNotIn("hidden", trigger)
        self.assertNotEqual(image["src"], trigger["href"])
        self.assertTrue(image["src"].startswith(BASE + "processed_images/"))
        self.assertTrue((self.site / "public" / image["src"].removeprefix(BASE)).is_file())
        self.assertEqual((image.get("width"), image.get("height")), ("4", "2"))
        self.assertEqual(image.get("loading"), "lazy")
        self.assertEqual(image.get("decoding"), "async")
        self.assertEqual((self.site / "public/research/media-fixture/raster.png").read_bytes(), PNG)

        captions = [attrs for tag, attrs in page.descendants(figure) if tag == "figcaption"]
        self.assertEqual(len(captions), 1)
        caption = captions[0]
        bold = [attrs for tag, attrs in page.descendants(caption) if tag == "strong"]
        self.assertEqual([page.text_content(item) for item in bold], ["bold"])
        source = self.single(page, "a", href="/test-assets/shared.svg?a=1&b=2", title='Quoted "title"')
        self.assertIn(("a", source), page.descendants(caption))
        external = self.single(page, "a", href="https://example.test/figure?a=1&b=2")
        self.assertIn(("a", external), page.descendants(caption))
        code = [attrs for tag, attrs in page.descendants(caption) if tag == "code"]
        self.assertEqual([page.text_content(item) for item in code],
                         ["<img src=x onerror=alert(7)>", "\\commands"])
        self.assertFalse(page.find("img", src="x"))
        self.assertFalse(any("onerror" in attrs for _, attrs in page.elements))

        populated = self.document("research/custom-output")
        for alt, original, loading in (("Teaser image", FULL_URL + "plot.svg", "eager"),
                                       ("Gallery image", BASE + "test-assets/shared.svg", "lazy")):
            with self.subTest(alt=alt):
                image = self.single(populated, "img", alt=alt)
                figure = self.figure_for_image(populated, image)
                triggers = [attrs for tag, attrs in populated.descendants(figure)
                            if tag == "a" and "data-post-lightbox-trigger" in attrs]
                self.assertEqual(len(triggers), 1)
                self.assertEqual(triggers[0]["href"], original)
                self.assertEqual(populated.descendants(triggers[0]), [("img", image)])
                self.assertEqual(image.get("loading"), loading)
                self.assertEqual(len([attrs for tag, attrs in populated.descendants(figure)
                                      if tag == "figcaption"]), 1)

    def test_media_image_defaults_preserve_legacy_resizing_and_original_svg_assets(self):
        page = self.document("research/media-fixture")
        original = self.single(page, "img", alt="Original bitmap")
        figure = self.figure_for_image(page, original)
        self.assertEqual(original["src"], BASE + "research/media-fixture/raster.png")
        self.assertEqual(original.get("loading"), "eager")
        self.assertEqual(original.get("decoding"), "async")
        self.assertNotIn("width", original)
        self.assertNotIn("height", original)
        self.assertFalse(any(tag in ("a", "figcaption") for tag, _ in page.descendants(figure)))

        legacy = self.single(page, "img", alt="Legacy resized bitmap")
        figure = self.figure_for_image(page, legacy)
        self.assertEqual(legacy["src"], self.single(page, "img", alt=MEDIA_ALT)["src"])
        self.assertEqual((legacy.get("width"), legacy.get("height")), ("4", "2"))
        self.assertEqual(legacy.get("loading"), "lazy")
        self.assertFalse(any(tag in ("a", "figcaption") for tag, _ in page.descendants(figure)))

        canonical = self.single(page, "img", alt="Canonical SVG")
        figure = self.figure_for_image(page, canonical)
        self.assertEqual(canonical["src"], BASE + "research/media-fixture/vector.svg")
        self.assertEqual((canonical.get("width"), canonical.get("height")), ("2", "2"))
        self.assertFalse(any(tag == "a" for tag, _ in page.descendants(figure)))

        slug_page = self.document("media-custom-slug")
        svg = self.single(slug_page, "img", alt="Original SVG")
        figure = self.figure_for_image(slug_page, svg)
        self.assertEqual(svg["src"], BASE + "media-custom-slug/vector.svg")
        self.assertNotIn("width", svg)
        self.assertNotIn("height", svg)
        self.assertEqual(svg.get("loading"), "lazy")
        link = self.single(slug_page, "a", href=svg["src"])
        self.assertIn(("a", link), slug_page.descendants(figure))
        self.assertEqual(slug_page.descendants(link), [("img", svg)])
        self.assertIn("data-post-lightbox-trigger", link)
        self.assertTrue((self.site / "public/media-custom-slug/vector.svg").is_file())

    def test_pandoc_raw_html_media_calls_survive_citation_preprocessing(self):
        if not self.pandoc:
            self.skipTest("Pandoc is required for source/media integration")
        for folder in ("test-citations", "test-references-only"):
            with self.subTest(folder=folder):
                generated = (self.site / f"content/{folder}/index.md").read_text(encoding="utf-8")
                self.assertIn('{{ <media.image page={page} path="raster.png"', generated)
                page = self.document(folder)
                image = self.single(page, "img", alt="Pandoc figure")
                figure = self.figure_for_image(page, image)
                link = self.single(page, "a", href=BASE + folder + "/raster.png")
                self.assertIn(("a", link), page.descendants(figure))
                self.assertEqual(page.descendants(link), [("img", image)])
                self.assertTrue(image["src"].startswith(BASE + "processed_images/"))
                self.assertEqual((image.get("width"), image.get("height")), ("4", "2"))
                self.assertEqual(image.get("loading"), "lazy")
                bold = [attrs for tag, attrs in page.descendants(figure) if tag == "strong"]
                self.assertEqual([page.text_content(item) for item in bold], ["Pandoc"])

    def test_metadata_and_plain_text_are_escaped(self):
        page = self.document("research/custom-output")
        self.assertIn(TITLE, page.text)
        self.assertIn(SUBTITLE, page.text)
        self.assertIn(BIBTEX, page.text)
        self.single(page, "meta", name="description", content="Specific post description & metadata")
        self.single(page, "meta", property="og:title", content=TITLE)
        self.single(page, "meta", property="og:image", content=FULL_URL + "plot.svg")
        self.single(page, "meta", name="twitter:card", content="summary_large_image")
        self.single(page, "meta", name="citation_author", content=AUTHOR)
        self.single(page, "meta", name="citation_publication_date", content="2025/03/04")
        self.single(page, "meta", name="citation_conference_title", content="Example Conference 2025")
        self.single(page, "meta", name="citation_doi", content="10.1234/example")
        self.assertFalse(page.find("meta", name="citation_pdf_url"))
        self.single(page, "a", href=FULL_URL + "paper.pdf")
        self.assertFalse(page.find("img", src="x"))
        self.assertTrue(all("src" in script for script in page.find("script")))
        self.assertFalse(any("onerror" in attributes for _, attributes in page.elements))

    def test_social_images_default_to_thumbnail_or_teaser_with_resolved_urls(self):
        expected_images = {
            "research/custom-output": FULL_URL + "plot.svg",
            "research/nested-post": BASE + "research/nested-post/thumb.svg",
            "posts/renamed-image": BASE + "posts/renamed-image/thumb.svg",
            "changed-slug": BASE + "changed-slug/plot.svg",
            "test-blog/full": BASE + "test-assets/shared.svg",
            "posts/m-video": BASE + "test-assets/shared.svg",
            "test-social-empty": BASE + "test-assets/shared.svg",
            "test-social-whitespace": BASE + "test-assets/shared.svg",
            "test-social-external": "https://images.example.test/social.png?a=1&b=2",
        }
        for output, expected in expected_images.items():
            with self.subTest(output=output):
                page = self.document(output)
                self.single(page, "meta", property="og:image", content=expected)
                self.single(page, "meta", name="twitter:card", content="summary_large_image")
                self.single(page, "meta", name="twitter:image", content=expected)

        # The populated fixture's explicit social image differs from its thumbnail.
        override = self.document("research/custom-output")
        self.assertFalse(override.find("meta", property="og:image", content=BASE + "test-assets/shared.svg"))

    def test_social_image_details_describe_the_shared_image_and_preserve_query(self):
        page = self.document("research/social-details")
        expected = BASE + "research/social-details/social.png?v=new&source=card"
        self.single(page, "meta", property="og:image", content=expected)
        self.single(page, "meta", property="og:image:width", content="8")
        self.single(page, "meta", property="og:image:height", content="4")
        self.single(page, "meta", property="og:image:type", content="image/png")
        self.single(page, "meta", property="og:image:alt", content=MEDIA_ALT)
        self.single(page, "meta", name="twitter:image", content=expected)
        self.single(page, "meta", name="twitter:image:alt", content=MEDIA_ALT)
        self.single(page, "img", src=BASE + "test-assets/shared.svg", width="2", height="2")
        self.assertEqual((self.site / "public/research/social-details/social.png").read_bytes(), PNG)
        self.assertFalse(any("onerror" in attrs for _, attrs in page.elements))

    def test_posts_without_a_usable_image_keep_summary_social_cards(self):
        for output in ("test-minimal", "posts/b-no-image", "posts/c-excerpt", "test-blog/minimal"):
            with self.subTest(output=output):
                page = self.document(output)
                self.assertFalse(page.find("meta", property="og:image"))
                self.assertFalse(page.find("meta", name="twitter:image"))
                self.single(page, "meta", name="twitter:card", content="summary")

    def test_thumbnails_remain_previews_without_supplying_article_media(self):
        listing = self.document("test-blog")
        for output in ("test-blog/full", "test-blog/entry-3"):
            with self.subTest(output=output):
                page = self.document(output)
                self.assertFalse(page.with_class("post__teaser"))
                self.assertFalse(page.find("img", src=BASE + "test-assets/shared.svg"))
                self.single(page, "meta", property="og:image", content=BASE + "test-assets/shared.svg")
                self.single(page, "meta", name="twitter:card", content="summary_large_image")
                card_link = self.single(listing, "a", href=BASE + output + "/")
                images = [attrs for tag, attrs in listing.descendants(card_link) if tag == "img"]
                self.assertEqual([image["src"] for image in images], [BASE + "test-assets/shared.svg"])

        image_page = self.document("changed-slug")
        teaser = self.single(image_page, "div", **{"class": "post__teaser"})
        image = self.single(image_page, "img", src=BASE + "changed-slug/plot.svg")
        self.assertIn(("img", image), image_page.descendants(teaser))

        video_page = self.document("posts/m-video")
        teaser = self.single(video_page, "div", **{"class": "post__teaser"})
        video = self.single(video_page, "video", poster=BASE + "test-assets/shared.svg")
        source = self.single(video_page, "source", src=BASE + "posts/m-video/clip.mp4")
        self.assertIn(("video", video), video_page.descendants(teaser))
        self.assertIn(("source", source), video_page.descendants(teaser))

    def test_post_metadata_tags_and_share_are_integrated_without_bookmark(self):
        page = self.document("research/custom-output")
        metadata = page.with_class("article-meta")
        self.assertEqual(len(metadata), 1)
        hero = page.with_class("post__hero")
        self.assertEqual(len(hero), 1)
        children = [attrs for (_, attrs), ancestors in zip(page.elements, page.ancestors)
                    if ancestors and ancestors[-1][1] is hero[0]]
        byline = page.with_class("post__byline")[0]
        resources = page.with_class("post__resources")[0]
        self.assertIn(metadata[0], children, "Metadata belongs directly to the hero")
        self.assertLess(children.index(byline), children.index(metadata[0]))
        self.assertLess(children.index(metadata[0]), children.index(resources))
        heading = page.with_class("post__heading")[0]
        self.assertNotIn(metadata[0], [attrs for _, attrs in page.descendants(heading)])
        self.single(page, "time", datetime="2025-03-04")
        reading = page.with_class("article-meta__reading-time")
        self.assertEqual(len(reading), 1)
        self.assertRegex(page.text_content(reading[0]), r"\d+\s+min")
        tags = page.with_class("taxonomy-labels--tags")
        self.assertEqual(len(tags), 1)
        self.assertEqual(tags[0].get("aria-label"), "Tags")
        tag_links = [attrs["href"] for tag, attrs in page.descendants(tags[0]) if tag == "a"]
        self.assertEqual(tag_links, [BASE + "tags/research-methods/", BASE + "tags/equations/"])
        self.assertIn("research & methods", page.text_content(tags[0]).lower())
        self.assertFalse(page.find(id="bookmark-button"))
        self.assertFalse(any("bookmark" in attrs.get("aria-label", "").lower()
                             for attrs in page.find("button")))
        self.single(page, "script", src=BASE + "assets/script/share.js")
        self.single(page, "link", href=BASE + "assets/stylesheet/citations.css")
        toggle = self.single(page, "button", **{"data-share-toggle": None})
        self.assertEqual(toggle.get("aria-expanded"), "false")
        menu = self.single(page, "nav", id=toggle["aria-controls"])
        self.assertNotIn("hidden", menu, "Share links must be usable without JavaScript")
        links = [attrs for tag, attrs in page.descendants(menu) if tag == "a"]
        twitter = next(link for link in links if "twitter.com/intent/tweet" in link["href"]
                       or "x.com/intent" in link["href"])
        query = parse_qs(urlparse(twitter["href"]).query)
        self.assertEqual(query["url"], [FULL_URL])
        self.assertEqual(query["text"], [TITLE])
        self.assertTrue(any(link["href"] == FULL_URL for link in links))
        self.assertFalse(self.document("test-minimal").with_class("taxonomy-labels"))

    def test_share_menu_copies_available_bibtex_and_otherwise_starts_with_permalink(self):
        for output, has_bibtex in (("research/custom-output", True),
                                   ("test-minimal", False),
                                   ("test-bibtex-empty", False),
                                   ("test-bibtex-whitespace", False)):
            with self.subTest(output=output):
                page = self.document(output)
                menu = page.with_class("share-menu")[0]
                actions = [(tag, attrs) for tag, attrs in page.descendants(menu)
                           if tag in {"a", "button"}]
                first_tag, first = actions[0]
                self.assertEqual(page.text_content(first).strip(),
                                 "Copy BibTeX" if has_bibtex else "Permalink")
                self.assertEqual(first_tag, "button" if has_bibtex else "a")
                copies = self.copy_buttons_within(page, menu)
                self.assertEqual(len(copies), 1 if has_bibtex else 0)
                self.assertFalse(page.find(**{"data-share-copy": None}))
                self.assertNotIn("Copy link", page.text_content(menu))
                if has_bibtex:
                    self.assertIn("hidden", first, "Copy needs JavaScript; links do not")
                    self.assertEqual(first.get("aria-controls"), "post-bibtex")
                    code = self.single(page, "code", id="post-bibtex")
                    self.assertEqual(page.text_content(code).strip(), BIBTEX)
                    self.assertEqual(page.text_content(actions[1][1]).strip(), "Permalink")
                    citation = self.single(page, "section", id="post-citation")
                    self.assertEqual(len(self.copy_buttons_within(page, citation)), 1)
                else:
                    self.assertEqual(first["href"], BASE + output + "/")
                    self.assertFalse(page.find(id="post-citation"))
                    self.assertFalse(page.find("a", href="#post-citation"))

    def test_explicit_bibtex_resource_has_a_native_copy_control_and_link_fallback(self):
        page = self.document("research/custom-output")
        resources = self.single(page, "nav", **{"class": "post__resources"})
        groups = [attrs for _, attrs in page.descendants(resources) if "data-copy-resource" in attrs]
        self.assertEqual(len(groups), 1)
        copies = self.copy_buttons_within(page, resources)
        self.assertEqual(len(copies), 1)
        button = copies[0]
        self.assertEqual(button.get("type"), "button")
        self.assertIn("hidden", button)
        self.assertEqual(button.get("aria-controls"), "post-bibtex")
        self.assertEqual(button.get("data-copy-feedback"), "BibTex Copied!")
        self.assertEqual(page.text_content(button).strip(), COPY_RESOURCE_NAME)
        self.assertIn(("button", button), page.descendants(groups[0]))

        labels = [attrs for tag, attrs in page.descendants(button)
                  if tag == "span" and "data-copy-label" in attrs]
        self.assertEqual(len(labels), 1)
        self.assertEqual(page.text_content(labels[0]), COPY_RESOURCE_NAME)
        self.assertFalse(page.descendants(labels[0]), "Resource labels remain escaped plain text")
        fallbacks = [attrs for tag, attrs in page.descendants(resources)
                     if tag == "a" and "data-copy-citation-fallback" in attrs]
        self.assertEqual(len(fallbacks), 1)
        fallback = fallbacks[0]
        self.assertEqual(fallback.get("href"), "#post-citation")
        self.assertNotIn("hidden", fallback)
        self.assertEqual(page.text_content(fallback).strip(), COPY_RESOURCE_NAME)
        self.assertIn(("a", fallback), page.descendants(groups[0]))
        for control in (button, fallback):
            icons = [attrs for tag, attrs in page.descendants(control) if tag == "i"]
            self.assertEqual(icons, [{"class": "bi bi-clipboard", "aria-hidden": "true"}])

        statuses = [attrs for tag, attrs in page.descendants(resources)
                    if tag == "p" and "data-copy-status" in attrs]
        self.assertEqual(len(statuses), 1)
        self.assertEqual(statuses[0].get("role"), "status")
        self.assertEqual(statuses[0].get("aria-live"), "polite")
        self.assertIn("visually-hidden", statuses[0].get("class", "").split())
        self.assertEqual(page.text_content(statuses[0]), "")
        code = self.single(page, "code", id="post-bibtex")
        self.assertEqual(page.text_content(code).strip(), BIBTEX)

        ordinary = {page.text_content(attrs).strip(): attrs for tag, attrs in page.descendants(resources)
                    if tag == "a" and "data-copy-citation-fallback" not in attrs}
        self.assertEqual(ordinary["Citation"]["href"], "#post-citation")
        self.assertEqual(ordinary["BibTeX"]["href"], "https://example.test/bibtex")
        self.assertEqual(ordinary["Relative paper"]["href"], FULL_URL + "paper.pdf")
        self.assertFalse(any("data-copy-label" in attrs
                             for _, attrs in page.descendants(ordinary["BibTeX"])))

    def test_unavailable_bibtex_resources_are_omitted_without_affecting_url_links(self):
        for output in ("test-resource-no-bibtex", "test-bibtex-empty", "test-bibtex-whitespace"):
            with self.subTest(output=output):
                page = self.document(output)
                self.assertFalse(page.with_class("post__resources"))
                self.assertFalse(page.find("button", **{"data-copy-citation": None}))
                self.assertFalse(page.find("a", **{"data-copy-citation-fallback": None}))
                self.assertFalse(page.find(id="post-bibtex"))

        mixed = self.document("test-resource-mixed")
        resources = self.single(mixed, "nav", **{"class": "post__resources"})
        links = [attrs for tag, attrs in mixed.descendants(resources) if tag == "a"]
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0]["href"], "https://example.test/bibtex")
        self.assertEqual(mixed.text_content(links[0]).strip(), "BibTeX")
        self.assertIn("post__button--primary", links[0].get("class", "").split())
        self.assertFalse(self.copy_buttons_within(mixed, resources))
        self.assertFalse(any("data-copy-status" in attrs or "data-copy-resource" in attrs
                             for _, attrs in mixed.descendants(resources)))
        self.assertNotIn("Copy reference", mixed.text_content(resources))

    def assert_bibliography_at_end(self, page, preceding_section):
        bibliography = self.single(page, "section", id="post-bibliography")
        refs = self.single(page, "div", id="refs")
        self.single(page, "h2", id="bibliography")
        self.assertIn(("div", refs), page.descendants(bibliography))
        body = page.with_class("post__body")[0]
        sections = [attrs for tag, attrs in page.descendants(body)
                    if tag == "section" and "post__section" in attrs.get("class", "").split()]
        self.assertIs(sections[-1], bibliography)
        previous = self.single(page, "section", id=preceding_section)
        positions = {id(attrs): index for index, (_, attrs) in enumerate(page.elements)}
        self.assertGreater(positions[id(bibliography)], positions[id(previous)])
        prose = page.with_class("post__prose")[0]
        self.assertNotIn(("div", refs), page.descendants(prose))
        self.assertTrue(page.find("a", href="#post-bibliography"))
        return refs

    def test_citation_pipeline_preserves_math_macros_and_moves_references_after_citation(self):
        if not self.pandoc:
            self.skipTest("Pandoc is required for citation-pipeline fixtures")
        for output, predecessor in (("test-citations", "post-citation"),
                                    ("test-references-only", "post-results")):
            with self.subTest(output=output):
                generated = (self.site / "content" / output / "index.md").read_text(encoding="utf-8")
                self.assertEqual(generated.count("<!-- persona-bibliography -->"), 1)
                page = self.document(output)
                refs = self.assert_bibliography_at_end(page, predecessor)
                self.assertEqual(bool(page.find(id="post-citation")), output == "test-citations")
                entry = self.single(page, "div", id="ref-fixture2025")
                self.assertIn(("div", entry), page.descendants(refs))
                self.assertIn("A cited fixture for post pages", page.text_content(entry))
                self.assertTrue(page.find("a", href="#ref-fixture2025"))
                self.assertNotIn("[@fixture2025]", page.text)
                self.single(page, "h2", id="cited-method")
                self.single(page, "h3", id="implementation-details")
                self.assertEqual(len(page.with_class("post__contents")), 1)
                self.single(page, "link", href="https://cdn.jsdelivr.net/npm/katex@0.16.10/dist/katex.min.css")
                self.single(page, "script", src="https://cdn.jsdelivr.net/npm/katex@0.16.10/dist/katex.min.js")
                self.single(page, "script", src="https://cdn.jsdelivr.net/npm/katex@0.16.10/dist/contrib/auto-render.min.js")
                initialization = [page.text_content(script) for script in page.find("script")
                                  if "src" not in script]
                self.assertEqual(len(initialization), 1)
                macro_data = re.search(r"const katexMacros\s*=\s*(\{.*?\});", initialization[0])
                self.assertIsNotNone(macro_data)
                self.assertEqual(json.loads(macro_data[1]), {r"\RR": r"\mathbb{R}"})
                self.assertIn(r"\RR", page.text_content(page.with_class("post__prose")[0]))
                self.assertTrue(page.with_class("math"))
                # Footnote references and backreferences retain their original IDs.
                self.single(page, "li", id="fn1")
                self.assertTrue(page.find("a", href="#fn1"))
                self.assertTrue(page.find("a", href="#fnref1"))

    def test_previous_citation_output_is_relocated_without_regenerating(self):
        page = self.document("test-legacy-bibliography")
        refs = self.assert_bibliography_at_end(page, "post-citation")
        self.assertIn("Existing reference.", page.text_content(refs))
        self.single(page, "div", id="ref-old")
        self.assertTrue(page.find("a", href="#ref-old"))

    def test_pandoc_without_references_preserves_frontmatter_examples(self):
        if not self.pandoc:
            self.skipTest("Pandoc is required for citation-pipeline fixtures")
        page = self.document("test-pandoc-without-references")
        self.assertFalse(page.find(id="post-bibliography"))
        self.assertFalse(page.find(id="refs"))
        code = page.find("code")
        self.assertEqual(len(code), 1)
        self.assertEqual(page.text_content(code[0]).strip(),
                         '+++\ntitle = "An example inside the body"\n+++')
        self.assertIn("The explanation after the example must remain in the page.", page.text)
        self.single(page, "h2", id="frontmatter-example")

    def test_related_posts_include_published_siblings_and_exclude_current_page(self):
        page = self.document("research/nested-post")
        related = self.single(page, "aside", **{"aria-labelledby": "post-related-title"})
        links = [attrs["href"] for tag, attrs in page.descendants(related) if tag == "a"]
        self.assertEqual(links, [BASE + "posts/" + name + "/" for name in
                                ("renamed-image", "m-video", "b-no-image", "c-excerpt")])
        self.assertEqual(page.text_content(self.single(page, "h2", id="post-related-title")),
                         "Related Posts")

        explicit = self.document("research/custom-output")
        related = self.single(explicit, "aside", **{"aria-labelledby": "post-related-title"})
        self.assertEqual([attrs["href"] for tag, attrs in explicit.descendants(related) if tag == "a"],
                         [BASE + "test-minimal/"])

    def test_related_dates_share_article_format_and_style(self):
        for output, expected in (
                ("test-blog/full", (("2025-03-03", "March 03, 2025"),
                                    ("2025-03-02", "March 02, 2025"),
                                    ("2025-03-01", "March 01, 2025"),
                                    ("2025-02-28", "February 28, 2025"))),
                ("research/custom-output", (("2024-11-09", "November 09, 2024"),))):
            with self.subTest(output=output):
                page = self.document(output)
                related = self.single(page, "aside", **{"aria-labelledby": "post-related-title"})
                dates = [attrs for tag, attrs in page.descendants(related) if tag == "time"]
                self.assertEqual([(date["datetime"], page.text_content(date)) for date in dates],
                                 list(expected))
                self.assertTrue(all("date-text" in date.get("class", "").split()
                                    for date in dates))

        timestamp = self.document("test-blog/draft-middle")
        dates = timestamp.with_class("article-meta__date")
        self.assertEqual(len(dates), 1)
        date = dates[0]
        self.assertEqual(date["datetime"], "2025-03-03")
        self.assertEqual(timestamp.text_content(date), "March 03, 2025")
        self.assertIn("date-text", date.get("class", "").split())

    def test_theme_content_uses_canonical_post_frontmatter(self):
        for path in (THEME / "content").rglob("*.md"):
            source = path.read_text(encoding="utf-8")
            if not source.startswith("+++"):
                continue
            frontmatter = source.split("+++", 2)[1]
            with self.subTest(content=str(path.relative_to(THEME))):
                self.assertNotRegex(frontmatter, r"\[extra\.project(?:\.|\])")
                self.assertNotRegex(frontmatter, r'(?:page_template|template)\s*=\s*"(?:project|__old_post)\.html"')
                self.assertNotRegex(frontmatter, r'(?m)^type\s*=\s*"(?:blog|projects)"')

    def test_migrated_theme_posts_use_canonical_post_layout_at_existing_urls(self):
        for slug, title in (("begin-with-persona", "Begin with Persona"),
                            ("citation-pipeline-guide", "Writing Citation-Enabled Posts in Persona")):
            output = "maps/private-soul/" + slug
            with self.subTest(output=output):
                page = self.document(output)
                heading = self.single(page, "h1", id="post-title")
                self.assertEqual(page.text_content(heading), title)
                self.single(page, "link", rel="canonical", href=BASE + output + "/")
                self.single(page, "article", id="post-main")
                self.assertFalse(page.with_class("blog-post"))
                self.assertEqual(len(page.with_class("article-meta")), 1)
                self.assertTrue(page.with_class("taxonomy-labels--tags"))
                self.single(page, "section", id="post-bibliography")
                self.single(page, "div", id="refs")
                self.assertTrue(page.find("a", href="#ref-zolathemes"))
                self.assertFalse(page.find(id="bookmark-button"))
                if slug == "begin-with-persona":
                    self.assertIn("From first installation to a personal website", page.text)

    def test_ordinary_page_keeps_base_defaults(self):
        page = self.document("test-ordinary")
        self.single(page, "div", id="preloader")
        self.assertEqual(len(page.with_class("nav-toggle")), 1)
        self.single(page, "header", id="header")
        self.single(page, "meta", name="author", content="Persona, Zola Theme")
        self.single(page, "script", src=BASE + "assets/script/home.js")
        self.assertFalse(page.with_class("post"))
        self.assertFalse(page.find("script", src=BASE + "assets/script/post.js"))

    def test_home_item_limit_defaults_to_three_and_applies_to_every_list(self):
        expected_links = [BASE + "research/nested-post/",
                          BASE + "posts/renamed-image/",
                          BASE + "posts/m-video/",
                          BASE + "posts/b-no-image/",
                          BASE + "posts/c-excerpt/"]
        blog_links = [BASE + "test-blog/" + name + "/" for name in
                      ("full", "minimal", "entry-3", "entry-4", "entry-5")]
        card_links = [BASE + "test-category/" + name + "/" for name in
                      ("z-first", "a-second", "m-third", "b-fourth", "c-fifth")]
        for directory, limit in (("public", 3), ("public-limit-2", 2),
                                 ("public-limit-0", 0), ("public-limit-5", 5),
                                 ("public-limit--1", 3)):
            with self.subTest(limit=limit):
                home = self.document("", directory=directory)
                self.assertFalse(home.find("nav", **{"aria-label": "Breadcrumb"}))
                for section_id, path, expected, link_class in (
                        ("fixture-posts", "posts", expected_links, "post-card__link"),
                        ("fixture-blog", "test-blog", blog_links, "post-card__link"),
                        ("fixture-categories", "test-category", card_links, "post-entry__thumb")):
                    with self.subTest(section=section_id):
                        self.assertEqual(self.section_links(home, section_id, link_class),
                                         expected[:limit])
                        self.assertEqual(self.view_all_links(home, section_id),
                                         [BASE + path + "/"] if limit < len(expected) else [])
                        archive = self.document(path, directory=directory)
                        self.assertEqual(self.section_links(archive, section_id, link_class), expected)
                        self.assertFalse(self.view_all_links(archive, section_id))

    def test_post_cards_preserve_thumbnails_and_explicit_descriptions(self):
        archive = self.document("posts")
        self.assertEqual(len(archive.with_class("post-grid")), 1)
        self.assertIn("Fixture posts", archive.text)
        self.assertIn("post introduction", archive.text)
        self.assertIn("Explicit thumbnail description", archive.text)
        self.assertNotIn("Fallback listing excerpt 1", archive.text)
        self.assertNotIn("Fallback listing excerpt 5", archive.text)
        self.assertEqual(len(archive.with_class("post-card__description")), 4)
        thumbnails = archive.with_class("post-card__image")
        self.assertEqual([image["src"] for image in thumbnails], [
            BASE + "research/nested-post/thumb.svg",
            BASE + "posts/renamed-image/thumb.svg",
            BASE + "test-assets/shared.svg",
        ])
        self.assertEqual(thumbnails[0]["alt"], "Explicit thumbnail")
        self.assertTrue(all(image.get("src") for image in thumbnails))
        self.assertTrue((self.site / "public/research/nested-post/thumb.svg").is_file())
        self.assertTrue((self.site / "public/posts/renamed-image/thumb.svg").is_file())

        blog = self.document("test-blog")
        descriptions = blog.with_class("post-card__description")
        self.assertEqual(len(descriptions), 1)
        self.assertEqual(blog.text_content(descriptions[0]), CARD_DESCRIPTION)

    def test_card_descriptions_require_nonblank_top_level_description(self):
        expected = {
            "research/nested-post": "Explicit thumbnail description",
            "test-blog/full": CARD_DESCRIPTION,
            "posts/c-excerpt": None,
            "test-blog/minimal": None,
            "test-blog/entry-3": None,
            "test-blog/entry-4": None,
            "test-blog/entry-5": None,
        }
        surfaces = (
            ("", "public", ["research/nested-post", "test-blog/full",
                              "test-blog/minimal", "test-blog/entry-3"]),
            ("", "public-limit-5", list(expected)),
            ("posts", "public", ["research/nested-post", "posts/c-excerpt"]),
            ("test-blog", "public", [name for name in expected if name.startswith("test-blog/")]),
            ("tags/description-behavior", "public",
             [name for name in expected if name.startswith("test-blog/")]),
            ("categories/research-methods", "public",
             ["research/nested-post", "test-blog/full", "test-blog/entry-3"]),
        )
        ignored = ("Fallback listing excerpt", "Legacy blog excerpt",
                   "Generated summary preview", "Generated body preview", "Fixture post body.")
        for output, directory, required in surfaces:
            with self.subTest(output=output, directory=directory):
                document = self.document(output, directory=directory)
                tested = set()
                for card in document.with_class("post-card"):
                    descendants = document.descendants(card)
                    links = [attrs for tag, attrs in descendants if tag == "a"]
                    self.assertEqual(len(links), 1)
                    name = links[0]["href"].removeprefix(BASE).removesuffix("/")
                    for text in ignored:
                        self.assertNotIn(text, document.text_content(card))
                    if name not in expected:
                        continue
                    tested.add(name)
                    descriptions = [attrs for _, attrs in descendants
                                    if "post-card__description" in attrs.get("class", "").split()]
                    if expected[name] is None:
                        self.assertFalse(descriptions, name)
                    else:
                        self.assertEqual(len(descriptions), 1, name)
                        self.assertEqual(document.text_content(descriptions[0]), expected[name])
                self.assertTrue(set(required).issubset(tested), (required, tested))

    def test_post_gallery_filters_preserve_exact_categories_and_exclude_drafts(self):
        archive = self.document("posts")
        gallery = self.section_gallery(archive, "fixture-posts")
        filters = self.gallery_filter_values(archive, gallery)
        expected = {"", "Research & Methods", GALLERY_CATEGORY,
                    "Sequence modeling", "Archive only"}
        self.assertEqual(set(filters), expected)
        self.assertEqual(len(filters), len(expected), "Repeated category labels need one filter")
        self.assertEqual(filters[0], "")
        self.assertNotIn("Draft-only gallery", filters)

        for tag, button in archive.descendants(gallery):
            if tag == "button" and "data-post-filter" in button:
                self.assertEqual(button.get("type"), "button")
                self.assertEqual(archive.text_content(button).strip(),
                                 button["data-post-filter"] or "All")
        cards = archive.with_class("post-card")
        expected_categories = [["Research & Methods", GALLERY_CATEGORY],
                               ["Research & Methods"], ["Sequence modeling"],
                               ["Archive only"], []]
        self.assertEqual([json.loads(card["data-post-categories"]) for card in cards],
                         expected_categories)
        self.assertFalse(any("hidden" in card for card in cards))
        filters_roots = [attrs for _, attrs in archive.descendants(gallery)
                         if "data-post-filters" in attrs]
        self.assertEqual(len(filters_roots), 1)
        self.assertIn("hidden", filters_roots[0], "Controls are enhanced only after JavaScript loads")

        for card, categories in zip(cards, expected_categories):
            labels = [attrs for _, attrs in archive.descendants(card)
                      if "post-card__category" in attrs.get("class", "").split()]
            self.assertEqual([archive.text_content(label) for label in labels], categories)
            self.assertFalse(any(tag == "a" for label in labels
                                 for tag, _ in archive.descendants(label)))

    def test_home_gallery_filters_are_scoped_to_the_visible_preview(self):
        category_sets = {
            "fixture-posts": [
                ["Research & Methods", GALLERY_CATEGORY], ["Research & Methods"],
                ["Sequence modeling"], ["Archive only"], []],
            "fixture-blog": [
                ["Research & Methods", GALLERY_CATEGORY], ["Personal writing"],
                ["Research & Methods"], [], []],
        }
        for directory, limit in (("public", 3), ("public-limit-2", 2),
                                 ("public-limit-0", 0), ("public-limit-5", 5),
                                 ("public-limit--1", 3)):
            home = self.document("", directory=directory)
            for section_id, category_lists in category_sets.items():
                with self.subTest(directory=directory, section=section_id):
                    if limit == 0:
                        self.assertFalse(self.within_section(home, section_id, "post-gallery"))
                        continue
                    gallery = self.section_gallery(home, section_id)
                    expected = {"", *(category for categories in category_lists[:limit]
                                      for category in categories)}
                    self.assertEqual(set(self.gallery_filter_values(home, gallery)), expected)
                    self.assertNotIn("Draft-only gallery", self.gallery_filter_values(home, gallery))
                    if section_id == "fixture-posts":
                        self.assertNotIn("Personal writing", self.gallery_filter_values(home, gallery))
                    else:
                        self.assertNotIn("Sequence modeling", self.gallery_filter_values(home, gallery))
            self.assertFalse(self.within_section(home, "fixture-categories", "post-gallery"))

    def test_gallery_scripts_load_on_gallery_pages(self):
        for output in ("", "posts", "test-blog", "tags/shared-fixture", "maps/public-self"):
            with self.subTest(output=output):
                self.single(self.document(output), "script", src=BASE + "assets/script/post-gallery.js")
        for output in ("test-blog/full", "test-minimal", "tags", "test-category"):
            with self.subTest(output=output):
                self.assertFalse(self.document(output).find(
                    "script", src=BASE + "assets/script/post-gallery.js"))

    def test_draft_posts_are_unlisted_but_keep_direct_urls_and_assets(self):
        draft_outputs = ("research/unlisted-first", "posts/unlisted-middle")
        for directory in ("public", "public-limit-2", "public-limit-0", "public-limit-5", "public-limit--1"):
            with self.subTest(directory=directory):
                for output in ("", "posts"):
                    listing = self.document(output, directory=directory)
                    self.assertNotIn("Unlisted draft-first", listing.text)
                    self.assertNotIn("Unlisted draft-middle", listing.text)
                    for draft_output in draft_outputs:
                        self.assertFalse(listing.find("a", href=BASE + draft_output + "/"))
                for draft_output in draft_outputs:
                    page = self.document(draft_output, directory=directory)
                    self.assertIn("Draft post body remains available", page.text)
                    self.single(page, "link", rel="canonical", href=BASE + draft_output + "/")
                    self.single(page, "img", src=BASE + draft_output + "/thumb.svg")
                    self.assertTrue((self.site / directory / draft_output / "thumb.svg").is_file())

    def test_draft_posts_in_blog_collections_stay_out_of_all_automatic_lists(self):
        drafts = [BASE + "test-blog/" + name + "/" for name in
                  ("draft-first", "draft-middle")]
        for directory in ("public", "public-limit-2", "public-limit-0", "public-limit-5"):
            for output in ("", "test-blog", "tags/shared-fixture", "test-blog/full"):
                with self.subTest(directory=directory, output=output):
                    page = self.document(output, directory=directory)
                    self.assertNotIn("Unlisted blog draft-first", page.text)
                    self.assertNotIn("Unlisted blog draft-middle", page.text)
                    for draft in drafts:
                        self.assertFalse(page.find("a", href=draft))
            for name in ("draft-first", "draft-middle"):
                page = self.document("test-blog/" + name, directory=directory)
                self.single(page, "h1", id="post-title")
                self.assertIn("Unlisted post in a normal blog collection", page.text)
            post = self.document("test-blog/full", directory=directory)
            recent = self.single(post, "aside", **{"aria-labelledby": "post-related-title"})
            links = [attrs["href"] for tag, attrs in post.descendants(recent) if tag == "a"]
            self.assertEqual(links, [BASE + "test-blog/" + name + "/" for name in
                                    ("minimal", "entry-3", "entry-4", "entry-5")])

    def test_taxonomy_overview_counts_only_published_entries_and_hides_draft_only_terms(self):
        overview = self.document("tags")
        shared_url = BASE + "tags/shared-fixture/"
        draft_url = BASE + "tags/draft-only-fixture/"
        fixture_terms = {}
        for row in overview.with_class("post-entry"):
            descendants = overview.descendants(row)
            links = [attrs["href"] for tag, attrs in descendants if tag == "a"]
            counts = [overview.text_content(attrs).strip() for _, attrs in descendants
                      if "post-entry__date" in attrs.get("class", "").split()]
            if links and links[0] in (shared_url, draft_url):
                fixture_terms[links[0]] = counts
        self.assertEqual(fixture_terms, {shared_url: ["1 item"]})

    def test_example_post_lives_under_public_self(self):
        self.assertFalse((THEME / "content/posts").exists())
        self.assertTrue((THEME / "content/maps/public-self/field-notes/index.md").is_file())
        self.assertFalse((self.site / "public/posts/field-notes/index.html").exists())
        output = "maps/public-self/field-notes"
        page = self.document(output)
        self.single(page, "h1", id="post-title")
        self.single(page, "link", rel="canonical", href=BASE + output + "/")
        breadcrumbs = self.single(page, "nav", **{"aria-label": "Breadcrumb"})
        links = [attrs["href"] for tag, attrs in page.descendants(breadcrumbs) if tag == "a"]
        self.assertEqual(links, [BASE.rstrip("/"), BASE + "maps/", BASE + "maps/public-self/"])
        for asset in ("workflow.svg", "evidence.svg"):
            self.assertTrue(page.find("img", src=BASE + output + "/" + asset))
            self.assertTrue((self.site / "public" / output / asset).is_file())
        header = self.single(page, "header", id="header")
        self.assertFalse(any(tag == "a" and page.text_content(attrs).strip() == "Posts"
                             for tag, attrs in page.descendants(header)))
        listing = self.document("maps/public-self")
        self.assertIn(BASE + output + "/", self.section_links(listing, "public-self"))

    def test_view_all_counts_only_published_posts(self):
        home = self.document("", directory="public-limit-5")
        self.assertEqual(len(self.within_section(home, "fixture-posts", "post-card")), 5)
        self.assertFalse(self.view_all_links(home, "fixture-posts"))

    def test_all_draft_collection_has_no_entries_or_view_all(self):
        for output in ("", "posts"):
            with self.subTest(output=output):
                listing = self.document(output, directory="public-all-drafts")
                self.assertFalse(self.within_section(listing, "fixture-posts", "post-card"))
                self.assertFalse(self.within_section(listing, "fixture-posts", "post-card__link"))
                self.assertFalse(self.view_all_links(listing, "fixture-posts"))
        for output in ("research/nested-post", "posts/renamed-image",
                       "posts/m-video", "posts/b-no-image", "posts/c-excerpt",
                       "research/unlisted-first", "posts/unlisted-middle"):
            page = self.document(output, directory="public-all-drafts")
            self.single(page, "h1", id="post-title")
            self.assertTrue((self.site / "public-all-drafts" / output / "thumb.svg").is_file())

    def test_post_cards_have_one_link_wrapping_their_content_and_read_more_cue(self):
        archive = self.document("posts")
        entries = archive.with_class("post-card")
        self.assertEqual(len(entries), 5)
        for entry in entries:
            self.assertTrue(any(tag == "li" and attrs is entry for tag, attrs in archive.elements))
            descendants = archive.descendants(entry)
            links = [attrs for tag, attrs in descendants if tag == "a"]
            self.assertEqual(len(links), 1)
            self.assertIn("post-card__link", links[0].get("class", "").split())
            linked_elements = archive.descendants(links[0])
            for tag, attrs in descendants:
                if tag == "img":
                    self.assertIn((tag, attrs), linked_elements)
            self.assertTrue(any(tag in ("h2", "h3", "h4") for tag, _ in linked_elements))
            more = [attrs for _, attrs in linked_elements
                    if "post-card__more" in attrs.get("class", "").split()]
            self.assertEqual(len(more), 1)
            self.assertIn("Read more", archive.text_content(more[0]))
            self.assertFalse(any(tag == "button" for tag, _ in descendants))
        for entry in entries[3:]:
            self.assertFalse(any(tag == "img" for tag, _ in archive.descendants(entry)))

    def test_post_dates_match_cards_while_subtitles_stay_on_details(self):
        detail = self.document("research/nested-post")
        date = detail.with_class("article-meta__date")
        self.assertEqual(len(date), 1)
        self.assertEqual(date[0]["datetime"], "2025-03-04")
        self.assertEqual(detail.text_content(date[0]), "March 04, 2025")
        self.assertEqual(detail.text_content(detail.with_class("post__subtitle")[0]), SUBTITLE)
        self.assertNotIn("Shared subtitle should be overridden", detail.text)

        fallback = self.document("posts/renamed-image")
        self.assertEqual(fallback.text_content(fallback.with_class("post__subtitle")[0]),
                         "Shared post subtitle")
        self.assertFalse(fallback.with_class("article-meta__date"))

        for output in ("", "posts"):
            with self.subTest(output=output):
                listing = self.document(output)
                dates = self.within_section(listing, "fixture-posts", "post-card__date")
                self.assertEqual(len(dates), 1)
                self.assertEqual(dates[0]["datetime"], "2025-03-04")
                self.assertEqual(listing.text_content(dates[0]), "March 04, 2025")
                self.assertFalse(self.within_section(listing, "fixture-posts", "post-card__subtitle"))
                self.assertNotIn(SUBTITLE, listing.text)
                self.assertNotIn("Shared post subtitle", listing.text)
                self.assertNotIn("Shared subtitle should be overridden", listing.text)

    def test_post_and_listing_dates_share_format_and_style_without_calendar_icons(self):
        for output in ("research/nested-post", "test-blog/full", "", "posts",
                       "test-blog", "tags/shared-fixture"):
            with self.subTest(output=output):
                page = self.document(output)
                dates = page.find("time", datetime="2025-03-04")
                self.assertTrue(dates, "Published dates must remain semantic time elements")
                self.assertTrue(all(page.text_content(date) == "March 04, 2025"
                                    for date in dates))
                self.assertTrue(all("date-text" in date.get("class", "").split()
                                    for date in dates))
                self.assertFalse(any("calendar" in name
                                     for _, attrs in page.elements
                                     for name in attrs.get("class", "").split()))
                if output in ("research/nested-post", "test-blog/full"):
                    self.assertEqual(len(page.with_class("bi-hourglass-split")), 1,
                                     "The reading-time icon is unrelated to publication dates")

    def test_blog_post_and_taxonomy_lists_share_card_gallery_markup(self):
        posts = self.document("posts")
        blog = self.document("test-blog")
        taxonomy = self.document("tags/shared-fixture")
        post_row = posts.with_class("post-card")[0]
        blog_row = blog.with_class("post-card")[0]
        taxonomy_row = taxonomy.with_class("post-card")[0]

        def shape(document, row):
            return [(tag, tuple(attrs.get("class", "").split()))
                    for tag, attrs in document.descendants(row)]

        self.assertEqual(shape(posts, post_row), shape(blog, blog_row))
        self.assertEqual(shape(blog, blog_row), shape(taxonomy, taxonomy_row))
        for document, row in ((posts, post_row), (blog, blog_row),
                              (taxonomy, taxonomy_row)):
            with self.subTest(row=row):
                self.assertEqual(set(row["class"].split()),
                                 {"post-card"})
                lists = document.with_class("post-grid")
                self.assertEqual(len(lists), 1)
                self.assertEqual(lists[0].get("role"), "list")
                self.assertIn("data-post-grid", lists[0])
                self.assertIn(("li", row), document.descendants(lists[0]))
                galleries = document.with_class("post-gallery")
                self.assertEqual(len(galleries), 1)
                self.assertIn("container", galleries[0]["class"].split())
                self.assertIn("data-post-gallery", galleries[0])
                self.assertFalse(document.with_class("project-entry"))
                self.assertFalse(document.with_class("project-list"))

        blog_thumbnail = blog.with_class("post-card__image")
        self.assertEqual([image["src"] for image in blog_thumbnail], [BASE + "test-assets/shared.svg"] * 2)
        self.assertEqual(blog_thumbnail[0]["alt"], "Blog listing thumbnail")
        plain_row = blog.with_class("post-card")[1]
        plain_descendants = blog.descendants(plain_row)
        self.assertFalse(any(tag in ("figure", "img") for tag, _ in plain_descendants))
        self.assertFalse(any("post-card__subtitle" in attrs.get("class", "").split()
                             for _, attrs in plain_descendants))

    def test_blog_subtitles_are_optional_on_details_and_absent_from_cards(self):
        detail = self.document("test-blog/full")
        subtitles = detail.with_class("post__subtitle")
        self.assertEqual(len(subtitles), 1)
        self.assertEqual(detail.text_content(subtitles[0]), SUBTITLE)
        self.assertFalse(self.document("test-blog/minimal").with_class("post__subtitle"))
        for output in ("research/nested-post", "test-blog/full", "", "posts",
                       "test-blog", "tags/shared-fixture", "categories/research-methods"):
            with self.subTest(output=output):
                page = self.document(output)
                self.assertIn(TITLE, page.text)
                self.assertFalse(page.find("img", src="x"))
                self.assertFalse(any("onerror" in attributes for _, attributes in page.elements))
                self.assertTrue(all("src" in script for script in page.find("script")))
                if output in ("research/nested-post", "test-blog/full"):
                    self.assertIn(SUBTITLE, page.text)
                else:
                    self.assertFalse(page.with_class("post-card__subtitle"))
                    for card in page.with_class("post-card"):
                        self.assertNotIn(SUBTITLE, page.text_content(card))
                        self.assertNotIn("Shared post subtitle", page.text_content(card))
                    self.assertTrue(page.with_class("post-card__description"))

    def test_breadcrumb_overrides_preserve_post_titles_metadata_and_card_urls(self):
        for output, label, archive, ancestors in (
                ("research/nested-post", "Short research note", "posts",
                 [("Home", BASE.rstrip("/")), (SECTION_BREADCRUMB_TITLE, BASE + "posts/")]),
                ("research/custom-output", PAGE_BREADCRUMB_TITLE, "categories/research-methods",
                 [("Home", BASE.rstrip("/"))])):
            with self.subTest(output=output):
                page = self.document(output)
                breadcrumb = self.single(page, "nav", **{"aria-label": "Breadcrumb"})
                links = [attrs for tag, attrs in page.descendants(breadcrumb) if tag == "a"]
                self.assertEqual([(page.text_content(link), link["href"]) for link in links], ancestors)
                self.assertTrue(all(not page.descendants(link) for link in links))
                current = self.single(page, "li", **{"aria-current": "page"})
                self.assertIn(("li", current), page.descendants(breadcrumb))
                self.assertEqual(page.text_content(current), label)
                self.assertFalse(page.descendants(current))
                title = self.single(page, "h1", id="post-title")
                self.assertEqual(page.text_content(title), TITLE)
                self.single(page, "meta", property="og:title", content=TITLE)
                self.single(page, "link", rel="canonical", href=BASE + output + "/")
                self.assertFalse(page.find("img", src="x"))
                self.assertFalse(any("onerror" in attrs for _, attrs in page.elements))

                gallery = self.document(archive)
                card = self.single(gallery, "a", href=BASE + output + "/")
                titles = [attrs for _, attrs in gallery.descendants(card)
                          if "post-card__title" in attrs.get("class", "").split()]
                self.assertEqual(len(titles), 1)
                self.assertEqual(gallery.text_content(titles[0]), TITLE)

        section = self.document("posts")
        breadcrumb = self.single(section, "nav", **{"aria-label": "Breadcrumb"})
        current = self.single(section, "li", **{"aria-current": "page"})
        self.assertIn(("li", current), section.descendants(breadcrumb))
        self.assertEqual(section.text_content(current), SECTION_BREADCRUMB_TITLE)
        self.assertFalse(section.descendants(current))
        headings = [section.text_content(attrs) for tag, attrs in section.elements if tag == "h2"]
        self.assertIn("Fixture posts", headings)

    def test_breadcrumb_labels_fall_back_to_full_page_and_section_titles(self):
        for output, title in (("test-minimal", "Minimal post"),
                              ("test-social-empty", "Social image empty"),
                              ("test-social-whitespace", "Social image whitespace"),
                              ("changed-slug", "Changed slug"),
                              ("test-blog", "Fixture blog"),
                              ("test-category/z-first", "Card z-first"),
                              ("test-category/a-second", "Card a-second")):
            with self.subTest(output=output):
                page = self.document(output)
                breadcrumb = self.single(page, "nav", **{"aria-label": "Breadcrumb"})
                current = self.single(page, "li", **{"aria-current": "page"})
                self.assertIn(("li", current), page.descendants(breadcrumb))
                self.assertEqual(page.text_content(current), title)
                self.assertFalse(page.descendants(current))
                links = [attrs for tag, attrs in page.descendants(breadcrumb) if tag == "a"]
                self.assertEqual(links[0]["href"], BASE.rstrip("/"))
                if output.startswith("test-category/"):
                    self.assertEqual([(page.text_content(link), link["href"]) for link in links],
                                     [("Home", BASE.rstrip("/")),
                                      ("Fixture categories", BASE + "test-category/")])

    def test_explicit_crumbs_api_keeps_legacy_labels_and_prefixed_links(self):
        page = self.document("test-legacy-breadcrumbs")
        breadcrumb = self.single(page, "nav", **{"aria-label": "Breadcrumb"})
        links = [attrs for tag, attrs in page.descendants(breadcrumb) if tag == "a"]
        self.assertEqual([(page.text_content(link), link["href"]) for link in links],
                         [("Home", BASE.rstrip("/")), ("Posts", BASE + "posts")])
        current = page.with_class("current")
        self.assertEqual(len(current), 1)
        self.assertEqual(page.text_content(current[0]), "Legacy")

    def test_post_breadcrumbs_follow_sections_with_custom_output_paths(self):
        page = self.document("research/nested-post")
        breadcrumbs = self.single(page, "nav", **{"aria-label": "Breadcrumb"})
        links = [attrs["href"] for tag, attrs in page.descendants(breadcrumbs) if tag == "a"]
        self.assertEqual(links, [BASE.rstrip("/"), BASE + "posts/"])
        self.single(page, "li", **{"aria-current": "page"})
        self.assertFalse(page.find("a", href=BASE + "research/"))

        full = self.document("research/custom-output")
        related = self.single(full, "aside", **{"aria-labelledby": "post-related-title"})
        body = full.with_class("post__body")[0]
        self.assertNotIn(("aside", related), full.descendants(body))
        body_index = next(i for i, (_, attrs) in enumerate(full.elements) if attrs is body)
        related_index = next(i for i, (_, attrs) in enumerate(full.elements) if attrs is related)
        self.assertGreater(related_index, body_index)
        self.assertEqual(len(full.with_class("post__related")), 1)
        self.assertFalse(full.with_class("post-bar"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
