#!/usr/bin/env python3
"""Build post fixtures in isolation: python3 tests/test_posts.py.

Requires Zola 0.23+. Uses only the Python standard library and skips external
link checks. Pandoc enables the citation-pipeline fixtures. Media fixtures test
generated markup and URLs, not playback.
"""

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
SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="2" height="2"></svg>'


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

        # Exercise the runtime default independently of the sample config value.
        default_config = re.sub(r"(?m)^home_items_limit\s*=.*\n?", "",
                                (cls.site / "config.toml").read_text(encoding="utf-8"))
        cls.write("config.toml", default_config)
        shutil.rmtree(cls.site / "content/posts", ignore_errors=True)
        cls.write("content/posts/_index.md", '''+++
title = "Fixture posts"
sort_by = "weight"
page_template = "post.html"
[extra]
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
        for weight, (folder, location, description, post) in enumerate(listing_posts, 1):
            title = TITLE if weight == 1 else f"Listing post {weight}"
            date = "date = 2025-03-04" if weight == 1 else ""
            subtitle = ('subtitle = "Shared subtitle should be overridden"' if weight == 1
                        else 'subtitle = "Shared post subtitle"' if weight == 2 else "")
            if weight == 1:
                post += "\nsubtitle = " + json.dumps(SUBTITLE)
            cls.write(f"content/posts/{folder}/index.md", f'''+++
title = {json.dumps(title)}
weight = {weight * 2}
{date}
{location}
{description}
[extra]
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
order = 2
type = "posts"
icon_class = "bi bi-journal"
+++
''')
        cls.write("content/test-blog/full.md", f'''+++
title = {json.dumps(TITLE)}
date = 2025-03-04
[taxonomies]
tags = ["Shared fixture"]
[extra]
excerpt = "Blog listing excerpt"
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
tags = []
[extra]
excerpt = "A text-only blog entry"
+++
Blog fixture without a subtitle or thumbnail.
''')
        for number, date in enumerate(("2025-03-02", "2025-03-01", "2025-02-28"), 3):
            cls.write(f"content/test-blog/entry-{number}.md", f'''+++
title = "Blog entry {number}"
date = {date}
[taxonomies]
tags = []
+++
Another published blog entry.
''')
        for folder, date in (("draft-first", "2025-03-06"),
                             ("draft-middle", "2025-03-03T12:00:00Z")):
            cls.write(f"content/test-blog/{folder}.md", f'''+++
title = "Unlisted blog {folder}"
date = {date}
template = "post.html"
[taxonomies]
tags = ["Shared fixture", "Draft-only fixture"]
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
            cls.write(f"content/test-category/{folder}/_index.md", f'''+++
title = "Card {folder}"
[extra]
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
[extra.post]
draft = true
teaser = {{ src = "thumb.svg", alt = "Unlisted post thumbnail" }}
+++
Draft post body remains available through its direct URL.
''')
            cls.write(f"content/posts/{folder}/thumb.svg", SVG)

        cls.write("content/test-minimal.md", '+++\ntitle = "Minimal post"\ntemplate = "post.html"\n+++\nNo extra table.')
        cls.write("content/test-ordinary.md", '+++\ntitle = "Ordinary page"\ntemplate = "page.html"\n+++\nOrdinary page body.')
        cls.write("content/test-slug/index.md", '''+++
title = "Changed slug"
slug = "changed-slug"
template = "post.html"
[extra.post]
teaser = { src = "plot.svg", alt = "Colocated plot" }
+++
Slug fixture.
''')
        cls.write("content/test-slug/plot.svg", SVG)
        quote = json.dumps
        cls.write("content/test-full/index.md", f'''+++
title = {quote(TITLE)}
description = "Specific post description & metadata"
date = 2025-03-04
slug = "ignored-slug"
path = "research/custom-output"
template = "post.html"
[taxonomies]
tags = ["Research & Methods", "Equations"]
[extra.post]
kind = "Research post"
venue = "Example Conference 2025"
subtitle = {quote(SUBTITLE)}
award = "Example award"
doi = "10.1234/example"
paper = "paper.pdf"
social_image = "plot.svg"
authors = [{{ name = {quote(AUTHOR)}, url = "https://example.test/author?a=1&b=2", affiliations = "1,2", equal = true }}, {{ name = "Second author" }}]
affiliations = [{{ id = "1", name = "Example institute" }}, {{ id = "2", name = "Other institute" }}]
author_note = "Equal contribution."
links = [
  {{ name = "Relative paper", url = "paper.pdf", icon_class = "bi bi-file-earmark-pdf" }},
  {{ name = "Root asset", url = "/test-assets/shared.svg" }},
  {{ name = "Internal page", url = "@/test-ordinary.md" }},
  {{ name = "External HTTPS", url = "https://example.test/code?a=1&b=2" }},
  {{ name = "External HTTP", url = "http://example.test/code" }},
  {{ name = "Protocol relative", url = "//example.test/code" }},
  {{ name = "Email", url = "mailto:research@example.test" }},
  {{ name = "Citation", url = "#post-citation" }}
]
related = [{{ title = "Minimal post", url = "@/test-minimal.md" }}]
abstract = "A **formatted** abstract."
teaser = {{ src = "plot.svg", alt = "Teaser image", width = 2, height = 2, caption = "A **teaser** caption." }}
gallery_title = "Research results"
gallery = [
  {{ src = "/test-assets/shared.svg", alt = "Gallery image", caption = "Image result." }},
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
''')
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
            cls.write("config.toml", default_config.replace(
                "[extra.persona]", f"[extra.persona]\nhome_items_limit = {limit}", 1))
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

    def within_section(self, document, section_id, class_name):
        section = self.single(document, "section", id=section_id)
        return [attrs for _, attrs in document.descendants(section)
                if class_name in attrs.get("class", "").split()]

    def section_links(self, document, section_id, class_name="post-entry__link"):
        return [attrs["href"] for attrs in self.within_section(
            document, section_id, class_name)]

    def view_all_links(self, document, section_id):
        section = self.single(document, "section", id=section_id)
        return [attrs["href"] for tag, attrs in document.descendants(section)
                if tag == "a" and document.text_content(attrs).strip().startswith("View all")]

    def test_minimal_post_needs_no_extra_table(self):
        page = self.document("test-minimal")
        self.single(page, "h1", id="post-title")
        self.assertIn("Minimal post", page.text)
        self.assertFalse(page.with_class("post__byline"))
        self.assertFalse(page.with_class("article-meta__date"))
        self.assertFalse(page.with_class("post__subtitle"))
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
        self.single(page, "button", **{"data-copy-citation": None, "hidden": None})
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
        self.single(page, "meta", name="citation_pdf_url", content=FULL_URL + "paper.pdf")
        self.assertFalse(page.find("img", src="x"))
        self.assertTrue(all("src" in script for script in page.find("script")))
        self.assertFalse(any("onerror" in attributes for _, attributes in page.elements))

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
        tags = page.with_class("article-tags")
        self.assertEqual(len(tags), 1)
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
        self.assertFalse(self.document("test-minimal").with_class("article-tags"))

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
                            ("citation-pipeline-guide", "How to Use Citation in Persona")):
            output = "maps/private-soul/" + slug
            with self.subTest(output=output):
                page = self.document(output)
                heading = self.single(page, "h1", id="post-title")
                self.assertEqual(page.text_content(heading), title)
                self.single(page, "link", rel="canonical", href=BASE + output + "/")
                self.single(page, "article", id="post-main")
                self.assertFalse(page.with_class("blog-post"))
                self.assertEqual(len(page.with_class("article-meta")), 1)
                self.assertTrue(page.with_class("article-tags"))
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
                        ("fixture-posts", "posts", expected_links, "post-entry__link"),
                        ("fixture-blog", "test-blog", blog_links, "post-entry__link"),
                        ("fixture-categories", "test-category", card_links, "post-entry__thumb")):
                    with self.subTest(section=section_id):
                        self.assertEqual(self.section_links(home, section_id, link_class),
                                         expected[:limit])
                        self.assertEqual(self.view_all_links(home, section_id),
                                         [BASE + path + "/"] if limit < len(expected) else [])
                        archive = self.document(path, directory=directory)
                        self.assertEqual(self.section_links(archive, section_id, link_class), expected)
                        self.assertFalse(self.view_all_links(archive, section_id))

    def test_post_listing_thumbnails_and_excerpt_fallback(self):
        archive = self.document("posts")
        self.assertEqual(len(archive.with_class("post-list")), 1)
        self.assertIn("Fixture posts", archive.text)
        self.assertIn("post introduction", archive.text)
        self.assertIn("Explicit thumbnail description", archive.text)
        self.assertNotIn("Fallback listing excerpt 1", archive.text)
        self.assertIn("Fallback listing excerpt 5", archive.text)
        thumbnails = archive.with_class("post-entry__thumbnail")
        self.assertEqual([image["src"] for image in thumbnails], [
            BASE + "research/nested-post/thumb.svg",
            BASE + "posts/renamed-image/thumb.svg",
            BASE + "test-assets/shared.svg",
        ])
        self.assertEqual(thumbnails[0]["alt"], "Explicit thumbnail")
        self.assertTrue(all(image.get("src") for image in thumbnails))
        self.assertTrue((self.site / "public/research/nested-post/thumb.svg").is_file())
        self.assertTrue((self.site / "public/posts/renamed-image/thumb.svg").is_file())

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
        self.assertEqual(len(self.within_section(home, "fixture-posts", "post-entry--row")), 5)
        self.assertFalse(self.view_all_links(home, "fixture-posts"))

    def test_all_draft_collection_has_no_entries_or_view_all(self):
        for output in ("", "posts"):
            with self.subTest(output=output):
                listing = self.document(output, directory="public-all-drafts")
                self.assertFalse(self.within_section(listing, "fixture-posts", "post-entry--row"))
                self.assertFalse(self.within_section(listing, "fixture-posts", "post-entry__link"))
                self.assertFalse(self.view_all_links(listing, "fixture-posts"))
        for output in ("research/nested-post", "posts/renamed-image",
                       "posts/m-video", "posts/b-no-image", "posts/c-excerpt",
                       "research/unlisted-first", "posts/unlisted-middle"):
            page = self.document(output, directory="public-all-drafts")
            self.single(page, "h1", id="post-title")
            self.assertTrue((self.site / "public-all-drafts" / output / "thumb.svg").is_file())

    def test_post_listing_has_one_link_per_row_wrapping_its_thumbnail(self):
        archive = self.document("posts")
        entries = archive.with_class("post-entry--row")
        self.assertEqual(len(entries), 5)
        for entry in entries:
            self.assertTrue(any(tag == "li" and attrs is entry for tag, attrs in archive.elements))
            descendants = archive.descendants(entry)
            links = [attrs for tag, attrs in descendants if tag == "a"]
            self.assertEqual(len(links), 1)
            self.assertIn("post-entry__link", links[0].get("class", "").split())
            linked_elements = archive.descendants(links[0])
            for tag, attrs in descendants:
                if tag == "img":
                    self.assertIn((tag, attrs), linked_elements)
            self.assertTrue(any(tag in ("h2", "h3", "h4") for tag, _ in linked_elements))
        for entry in entries[3:]:
            self.assertFalse(any(tag == "img" for tag, _ in archive.descendants(entry)))

    def test_post_date_and_subtitle_are_consistent_between_detail_and_list(self):
        detail = self.document("research/nested-post")
        date = detail.with_class("article-meta__date")
        self.assertEqual(len(date), 1)
        self.assertEqual(date[0]["datetime"], "2025-03-04")
        self.assertIn("2025", detail.text_content(date[0]))
        self.assertEqual(detail.text_content(detail.with_class("post__subtitle")[0]), SUBTITLE)
        self.assertNotIn("Shared subtitle should be overridden", detail.text)

        fallback = self.document("posts/renamed-image")
        self.assertEqual(fallback.text_content(fallback.with_class("post__subtitle")[0]),
                         "Shared post subtitle")
        self.assertFalse(fallback.with_class("article-meta__date"))

        for output in ("", "posts"):
            with self.subTest(output=output):
                listing = self.document(output)
                dates = self.within_section(listing, "fixture-posts", "post-entry__date")
                self.assertEqual(len(dates), 1)
                self.assertEqual(dates[0]["datetime"], "2025-03-04")
                self.assertEqual(listing.text_content(dates[0]), "Mar 04, 2025")
                self.assertEqual([listing.text_content(subtitle)
                                  for subtitle in self.within_section(
                                      listing, "fixture-posts", "post-entry__subtitle")],
                                 [SUBTITLE, "Shared post subtitle"])
                self.assertNotIn("Shared subtitle should be overridden", listing.text)

    def test_blog_post_and_taxonomy_lists_share_row_markup(self):
        posts = self.document("posts")
        blog = self.document("test-blog")
        taxonomy = self.document("tags/shared-fixture")
        post_row = posts.with_class("post-entry--row")[0]
        blog_row = blog.with_class("post-entry--row")[0]
        taxonomy_row = taxonomy.with_class("post-entry--row")[0]

        def shape(document, row):
            return [(tag, tuple(attrs.get("class", "").split()))
                    for tag, attrs in document.descendants(row)]

        self.assertEqual(shape(posts, post_row), shape(blog, blog_row))
        self.assertEqual(shape(blog, blog_row), shape(taxonomy, taxonomy_row))
        for document, row in ((posts, post_row), (blog, blog_row),
                              (taxonomy, taxonomy_row)):
            with self.subTest(row=row):
                self.assertEqual(set(row["class"].split()),
                                 {"container", "post-entry", "post-entry--row", "border-bottom"})
                lists = document.with_class("post-list")
                self.assertEqual(len(lists), 1)
                self.assertIn("container", lists[0]["class"].split())
                self.assertIn(("li", row), document.descendants(lists[0]))
                self.assertFalse(document.with_class("project-entry"))
                self.assertFalse(document.with_class("project-list"))

        blog_thumbnail = blog.with_class("post-entry__thumbnail")
        self.assertEqual(len(blog_thumbnail), 1)
        self.assertEqual(blog_thumbnail[0]["src"], BASE + "test-assets/shared.svg")
        self.assertEqual(blog_thumbnail[0]["alt"], "Blog listing thumbnail")
        plain_row = blog.with_class("post-entry--row")[1]
        plain_descendants = blog.descendants(plain_row)
        self.assertFalse(any(tag in ("figure", "img") for tag, _ in plain_descendants))
        self.assertFalse(any("post-entry__subtitle" in attrs.get("class", "").split()
                             for _, attrs in plain_descendants))

    def test_blog_subtitle_is_optional_and_escaped_in_details_and_lists(self):
        detail = self.document("test-blog/full")
        subtitles = detail.with_class("post__subtitle")
        self.assertEqual(len(subtitles), 1)
        self.assertEqual(detail.text_content(subtitles[0]), SUBTITLE)
        self.assertFalse(self.document("test-blog/minimal").with_class("post__subtitle"))
        for output in ("research/nested-post", "test-blog/full", "posts",
                       "test-blog", "tags/shared-fixture"):
            with self.subTest(output=output):
                page = self.document(output)
                self.assertIn(TITLE, page.text)
                self.assertIn(SUBTITLE, page.text)
                self.assertFalse(page.find("img", src="x"))
                self.assertFalse(any("onerror" in attributes for _, attributes in page.elements))
                self.assertTrue(all("src" in script for script in page.find("script")))
                if output in ("posts", "test-blog", "tags/shared-fixture"):
                    self.assertEqual(page.text_content(page.with_class("post-entry__subtitle")[0]),
                                     SUBTITLE)

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
