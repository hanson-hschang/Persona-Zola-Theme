#!/usr/bin/env python3
"""Build Markdown resume fixtures: python3 -B tests/test_resume.py.

Requires Zola 0.23+ and only the Python standard library. External links are
not fetched. These checks cover generated documents, not browser layout.
"""

from html import escape
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from test_posts import Document


THEME = Path(__file__).resolve().parents[1]
BASE = "https://example.test/persona/"
TITLE = 'Resume <script>alert("title")</script> & "quotes"'
NAME = 'Example <script>alert("name")</script> & Researcher'
LABEL = 'Research <img src=x onerror=alert(1)> & Development'
SUMMARY = "I earned a **Bachelor of Science** and work on *robotics*."
SKILL_LABEL = 'Programming <img src=x onerror=alert(1)> & "languages"'
SKILL_ITEM = 'C++ <script>alert("skill")</script> & Python'
SKILL_ICON = 'bi bi-code-slash" onerror="alert(1)'
BADGE_TITLE = 'Awards <img src=x onerror=alert(1)> & Honors'
BADGE_ITEM = 'Scholar <script>alert("badge")</script> & Award'
BADGE_ICON = 'bi bi-trophy" onerror="alert(1)'
BADGE_LINK = 'https://example.org/award?recipient="Researcher"&year=2026'
BADGE_LINK_CASES = (
    ("External award", "  " + BADGE_LINK + "  ", BADGE_LINK),
    ("HTTP award", "http://example.org/award", "http://example.org/award"),
    ("Uppercase HTTPS award", "HTTPS://example.org/award", "HTTPS://example.org/award"),
    ("Root-relative award", "/about/", BASE + "about/"),
    ("Site-relative award", "about/", BASE + "about/"),
    ("Content-reference award", "@/about/_index.md", BASE + "about/"),
    ("Blank link", "  ", None),
    ("Script scheme", "javascript:alert(1)", None),
    ("Mixed-case script scheme", "JaVaScRiPt:alert(1)", None),
    ("Data scheme", "data:text/html,<script>alert(1)</script>", None),
    ("Email scheme", "mailto:someone@example.org", None),
    ("Protocol-relative URL", "//example.org/award", None),
    ("Backslash URL", "\\\\example.org/award", None),
    ("HTTPS URL with backslash", "https://example.org\\award", None),
)
BUTTON_TEXT = 'Explore <img src=x onerror=alert(1)> & experience'
HARD_BREAK = "  "


class ResumeIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        zola = shutil.which("zola")
        if zola is None:
            raise unittest.SkipTest("Zola 0.23+ is required for integration tests")
        temporary = tempfile.TemporaryDirectory(prefix="persona-resume-tests-")
        cls.addClassCleanup(temporary.cleanup)
        cls.site = Path(temporary.name)
        for directory in ("templates", "sass", "static"):
            shutil.copytree(THEME / directory, cls.site / directory)
        cls.write("config.toml", f'''base_url = "{BASE}"
title = "Resume fixture site"
author = "Fixture author"
description = "An isolated resume test site."
compile_sass = true
[extra.persona]
social_links = []
quote = "Fixture quote"
copyright = "Fixture copyright"
credits = "Fixture credits"
''')
        cls.write("content/_index.md", '''+++
title = "Home"
[extra]
icon_class = "bi bi-house"
+++
''')
        cls.write("content/about/_index.md", '''+++
title = "About"
[extra]
type = "plain"
order = 10
icon_class = "bi bi-person"
+++
A plain section remains independent of the resume stylesheet.
''')
        cls.write("content/resume/_index.md", f'''+++
title = "Resume"
[extra]
type = "resume"
order = 20
landing_page = false
icon_class = "bi bi-file-earmark-person"
subtitle = {json.dumps(LABEL)}
[extra.summary]
title = ""
description = {json.dumps(SUMMARY)}
+++
# {escape(NAME)}

## Research Experience

### {escape(LABEL)}

> Period: 2019-07 / 2024-12{HARD_BREAK}
> Organization: [Lab: Robotics](@/about/_index.md){HARD_BREAK}
> Location: Urbana, IL

A **bold description** with `code`.

- A *measurable result*.
- A [reference](https://example.org/work).

### Full-date appointment

> Period: 2020-01-02 / 2024-05-31

- A precise appointment period.

### Continuing appointment

> Period: 2024 / Present

- Work in progress.

---

## Education

### Degree

> Organization: [External university](https://example.org/university?a=1&b=2){HARD_BREAK}
> Location: Taipei, Taiwan

- A [local reference](group/).
''')
        cls.write("content/cv.md", f'''+++
title = {json.dumps(TITLE)}
description = "Standalone SEO description."
template = "resume.html"
[extra.summary]
title = ""
description = "A standalone **summary**."
+++
## Experience

### Title-only role

- A role without optional metadata.

### Quoted role

> A conventional **blockquote** belongs to the description.

- Its quote must survive.

### Prose before quote

A contextual paragraph precedes this quote.

> Period: this is ordinary quoted prose, not entry metadata.

### Mixed quote

> Period: 2024 / Present
> Team notes: preserve this entire quote as ordinary prose.

### Empty metadata

> Period:
> Organization:
> Location:

- A result without metadata placeholders.
''')
        cls.write("content/minimal.md", '''+++
title = "Minimal CV"
template = "resume.html"
+++
A **body-only resume** without extra data.
''')
        cls.write("content/skills.md", f'''+++
title = "Skills CV"
template = "resume.html"
[extra]
skills = [
  {{ category = "  Languages  ", icon_class = "  bi bi-code-slash  ", items = [" Python ", "", "  ", "C/C++"] }},
  {{ category = "Tools", items = ["Git"] }},
  {{ category = "Hardware", icon_class = "  ", items = ["Arduino"] }},
  {{ category = {json.dumps(SKILL_LABEL)}, icon_class = {json.dumps(SKILL_ICON)}, items = [{json.dumps(SKILL_ITEM)}] }},
  {{ category = "  ", items = ["No category"] }},
  {{ items = ["Missing category"] }},
  {{ category = "Empty items", items = ["", "  "] }},
  {{ category = "Missing items" }},
]
[extra.summary]
title = "Professional <summary>"
description = {json.dumps(SUMMARY)}
[extra.summary.badges]
title = {json.dumps(BADGE_TITLE)}
items = [
  "  Dr. Sandra J. Finley Scholar  ",
  {{ label = "  Gauthier Fellowship Award  ", icon_class = "  bi bi-trophy  " }},
  {{ label = "Service Honor" }},
  {{ label = "Text-only distinction", icon_class = "  " }},
  {{ label = {json.dumps(BADGE_ITEM)}, icon_class = {json.dumps(BADGE_ICON)} }},
  "", "  ", {{ label = "  ", icon_class = "bi bi-star" }},
  {{ icon_class = "bi bi-star" }},
]
+++
## Experience

### Skills in practice

- A relevant project.
''')
        for output, skills in (
                ("empty-skills", "[]"),
                ("invalid-skills", '[{ category = " ", items = ["Unused"] }, '
                 '{ category = "Empty", items = ["", " "] }, '
                 '{ items = ["Missing category"] }, { category = "Missing items" }]')):
            cls.write(f"content/{output}.md", f'''+++
title = "Summary fallback"
template = "resume.html"
[extra]
skills = {skills}
[extra.summary]
description = {json.dumps(SUMMARY)}
+++
A resume with no usable skill categories.
''')
        cls.write("content/skills-only.md", '''+++
title = "Skills without a description"
template = "resume.html"
[extra]
skills = [{ category = "Tools", items = ["Git"] }]
+++
''')
        cls.write("content/skills-defaults.md", f'''+++
title = "Default skills headings"
template = "resume.html"
[extra]
skills = [{{ category = "Tools", items = ["Git"] }}]
[extra.summary]
description = {json.dumps(SUMMARY)}
+++
''')
        cls.write("content/seo-only.md", '''+++
title = "Metadata is not a visible summary"
description = "SEO description only."
template = "resume.html"
+++
''')
        cls.write("content/empty-summary.md", '''+++
title = "Summary without content"
template = "resume.html"
[extra.summary]
title = "A title needs content"
description = "  "
[extra.summary.badges]
title = "Empty awards"
items = ["", "  ", { label = " " }, { icon_class = "bi bi-star" }]
+++
''')
        for output, skills, title in (
                ("badges-only", 'skills = [{ category = "Tools", items = ["Git"] }]',
                 'title = "  "'),
                ("badges-no-skills", "", "")):
            cls.write(f"content/{output}.md", f'''+++
title = "Awards without summary prose"
template = "resume.html"
[extra]
{skills}
[extra.summary]
{title}
[extra.summary.badges]
title = "Awards and Honors"
items = ["Dr. Sandra J. Finley Scholar", "Gauthier Fellowship Award"]
+++
''')
        for output, title in (("badges-missing-title", ""),
                              ("badges-blank-title", 'title = "  "')):
            cls.write(f"content/{output}.md", f'''+++
title = "Awards without a badge heading"
template = "resume.html"
[extra.summary]
title = ""
[extra.summary.badges]
{title}
items = ["Dr. Sandra J. Finley Scholar"]
+++
''')
        linked_badges = ",\n".join(
            f"  {{ label = {json.dumps(label)}, link = {json.dumps(link)} }}"
            for label, link, _ in BADGE_LINK_CASES)
        cls.write("content/badge-links.md", f'''+++
title = "Optional badge links"
template = "resume.html"
[extra.summary]
title = ""
[extra.summary.badges]
items = [
  "Plain string",
  {{ label = "Missing link", icon_class = "bi bi-trophy" }},
{linked_badges},
]
+++
''')
        # Exercise every optional-field combination without placeholders. Each
        # fixture still consists entirely of ordinary headings and Markdown.
        combinations = []
        for mask in range(8):
            metadata = []
            if mask & 1:
                metadata.append("Period: 2021-06 / Present")
            if mask & 2:
                metadata.append("Organization: [Group: Controls](@/about/_index.md)")
            if mask & 4:
                metadata.append("Location: Room: 204, Urbana")
            quote = "  \n".join("> " + field for field in metadata)
            combinations.append(f"### Optional {mask}\n\n{quote}\n\n- Achievement {mask}.\n")
        cls.write("content/optional.md", '''+++
title = "Optional metadata"
template = "resume.html"
+++
## Experience

''' + "\n".join(combinations))
        cls.build_site(zola)
        cls.home_without_resume = (cls.site / "public/index.html").read_text(encoding="utf-8")
        for output, title, order, landing, summary_title, button in (
                ("preview", TITLE, 30, "", "Professional Summary",
                 "button_text = " + json.dumps(BUTTON_TEXT)),
                ("preview-default", "A second resume", 40, "landing_page = true", "", ""),
                ("preview-blank-button", "A third resume", 50, "", "Profile",
                 'button_text = "  "'),
                ("unordered-resume", "Unordered resume", 0, "", "Profile", "")):
            cls.write(f"content/{output}/_index.md", f'''+++
title = {json.dumps(title)}
[extra]
type = "resume"
order = {order}
{landing}
subtitle = {json.dumps(LABEL)}
icon_class = "bi bi-person-vcard"
skills = [{{ category = "Preview skills stay on the full page", items = ["Python"] }}]
[extra.summary]
title = {json.dumps(summary_title)}
description = {json.dumps(SUMMARY)}
{button}
[extra.summary.badges]
title = "Recognition"
items = [{{ label = "Research award", icon_class = "bi bi-trophy", link = {json.dumps(BADGE_LINK)} }}, "Teaching award"]
+++
# Full-page name for {output}

## Full-page experience

### A full-page role

- Full-page achievement.
''')
        cls.build_site(zola)

    @classmethod
    def build_site(cls, zola):
        for arguments in (("check", "--skip-external-links"), ("build",)):
            result = subprocess.run([zola, *arguments], cwd=cls.site, text=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    timeout=60, check=False)
            if result.returncode:
                raise AssertionError(f"zola {' '.join(arguments)} failed:\n{result.stdout}")

    @classmethod
    def write(cls, relative, content):
        destination = cls.site / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")

    def document(self, output):
        return Document((self.site / "public" / output / "index.html").read_text(encoding="utf-8"))

    def entry(self, document, title):
        for entry in document.with_class("resume__entry"):
            headings = [attrs for tag, attrs in document.descendants(entry) if tag == "h3"]
            if any(document.text_content(heading).strip() == title for heading in headings):
                return entry
        self.fail(f"No resume entry for {title!r}")

    def descendants_with_class(self, document, ancestor, class_name):
        return [attrs for _, attrs in document.descendants(ancestor)
                if class_name in attrs.get("class", "").split()]

    def test_markdown_name_and_extra_summary_form_the_header(self):
        document = self.document("resume")
        heading = document.find("h1", id="resume-title")
        self.assertEqual(len(document.find("h1")), 1)
        self.assertEqual(document.text_content(heading[0]).strip(), NAME)
        self.assertFalse(document.with_class("resume__name"))
        summary = document.with_class("resume__summary")[0]
        self.assertIn("I earned a Bachelor of Science", document.text_content(summary))
        self.assertTrue(any(tag == "strong" for tag, _ in document.descendants(summary)))
        self.assertEqual(document.find("meta", name="description")[0]["content"],
                         "I earned a Bachelor of Science and work on robotics.")
        standalone = self.document("cv")
        self.assertEqual(standalone.find("meta", name="description")[0]["content"],
                         "Standalone SEO description.")
        self.assertIn("A standalone summary.", standalone.text)
        self.assertNotIn("Standalone SEO description.", standalone.text)

    def test_heading_hierarchy_and_markdown_bodies_are_preserved(self):
        document = self.document("resume")
        self.assertEqual([document.text_content(attrs).strip() for attrs in document.find("h2")],
                         ["Research Experience", "Education"])
        self.assertEqual(len(document.with_class("resume__entry")), 4)
        entry = self.entry(document, LABEL)
        children = document.descendants(entry)
        self.assertTrue(any(tag == "ul" for tag, _ in children))
        self.assertEqual([document.text_content(attrs) for tag, attrs in children if tag == "li"],
                         ["A measurable result.", "A reference."])
        self.assertTrue(any(tag == "strong" and document.text_content(attrs) == "bold description"
                            for tag, attrs in children))
        self.assertTrue(any(tag == "code" and document.text_content(attrs) == "code"
                            for tag, attrs in children))
        self.assertTrue(document.find("a", href="https://example.org/work"))

    def test_skills_integrate_summary_once_and_support_a_custom_title(self):
        document = self.document("skills")
        skills = document.with_class("resume__skills")[0]
        summary = self.descendants_with_class(document, skills, "resume__skills-summary")
        self.assertEqual(len(summary), 1)
        self.assertFalse(document.with_class("resume__summary"))
        article = document.find("article", id="resume-main")[0]
        self.assertEqual(document.text_content(article).count("I earned a Bachelor of Science"), 1)
        children = document.descendants(summary[0])
        self.assertTrue(any(tag == "strong" and document.text_content(attrs) == "Bachelor of Science"
                            for tag, attrs in children))
        self.assertTrue(any(tag == "em" and document.text_content(attrs) == "robotics"
                            for tag, attrs in children))
        self.assertFalse(document.find(id="resume-skills-title"))
        self.assertEqual([document.text_content(attrs) for tag, attrs in children if tag == "h2"],
                         ["Professional <summary>"])
        self.assertFalse(any(tag == "summary" for tag, _ in children))

    def test_skill_tabs_link_to_complete_panels_without_javascript(self):
        document = self.document("skills")
        cards = document.with_class("resume__skill-card")
        tabs = document.with_class("resume__skill-tab")
        self.assertEqual(len(cards), 4)
        self.assertEqual(len(tabs), 4)
        self.assertTrue(document.find("nav", **{"aria-label": "Skill categories"}))
        expected = [("Languages", ["Python", "C/C++"]), ("Tools", ["Git"]),
                    ("Hardware", ["Arduino"]), (SKILL_LABEL, [SKILL_ITEM])]
        for tab, card, (category, items) in zip(tabs, cards, expected):
            with self.subTest(category=category):
                self.assertTrue(any(attrs is tab for attrs in document.find("a")))
                self.assertTrue(any(attrs is card for attrs in document.find("section")))
                self.assertEqual(tab["href"], "#" + card["id"])
                self.assertEqual(card["aria-labelledby"], tab["id"])
                self.assertEqual(document.text_content(tab).strip(), category)
                self.assertEqual(len(document.find(id=tab["id"])), 1)
                self.assertEqual(len(document.find(id=card["id"])), 1)
                self.assertNotIn("hidden", card)
                children = document.descendants(card)
                heading = [attrs for tag, attrs in children if tag == "h2"]
                self.assertEqual(len(heading), 1)
                self.assertEqual(document.text_content(heading[0]).strip(), category)
                lists = [attrs for tag, attrs in children if tag == "ul"]
                self.assertEqual(len(lists), 1)
                self.assertEqual([document.text_content(attrs)
                                  for tag, attrs in document.descendants(lists[0]) if tag == "li"], items)
        icon = self.descendants_with_class(document, tabs[0], "resume__skill-icon")
        self.assertEqual(len(icon), 1)
        self.assertIn("bi-code-slash", icon[0]["class"].split())
        self.assertEqual(icon[0]["aria-hidden"], "true")
        for tab in tabs[1:3]:
            self.assertFalse(self.descendants_with_class(document, tab, "resume__skill-icon"))
        self.assertFalse(document.find("progress"))
        self.assertFalse(document.find(role="progressbar"))

    def test_skill_text_and_icon_classes_are_escaped(self):
        document = self.document("skills")
        unsafe_card = document.with_class("resume__skill-card")[-1]
        unsafe_tab = document.with_class("resume__skill-tab")[-1]
        icon = self.descendants_with_class(document, unsafe_tab, "resume__skill-icon")[0]
        self.assertEqual(icon["class"], "resume__skill-icon " + SKILL_ICON)
        self.assertIn(SKILL_LABEL, document.text_content(unsafe_card))
        self.assertIn(SKILL_ITEM, document.text_content(unsafe_card))
        self.assertFalse(document.find("img", src="x"))
        self.assertFalse(any("onerror" in attrs for _, attrs in document.elements))
        self.assertTrue(all("src" in attrs for attrs in document.find("script")))

    def test_empty_skills_retain_the_standalone_summary(self):
        for output in ("empty-skills", "invalid-skills"):
            with self.subTest(output=output):
                document = self.document(output)
                self.assertFalse(document.with_class("resume__skills"))
                self.assertFalse(document.with_class("resume__skills-summary"))
                self.assertFalse(document.find(id="resume-skills-title"))
                summary = document.with_class("resume__summary")
                self.assertEqual(len(summary), 1)
                self.assertIn("I earned a Bachelor of Science", document.text_content(summary[0]))
                self.assertTrue(any(tag == "strong" for tag, _ in document.descendants(summary[0])))

    def test_skills_use_default_headings_and_allow_no_description(self):
        document = self.document("skills-defaults")
        self.assertFalse(document.find(id="resume-skills-title"))
        summary = document.with_class("resume__skills-summary")[0]
        self.assertEqual([document.text_content(attrs) for tag, attrs in document.descendants(summary)
                          if tag == "h2"], ["Professional Summary"])
        without_description = self.document("skills-only")
        self.assertEqual(len(without_description.with_class("resume__skill-card")), 1)
        self.assertFalse(without_description.with_class("resume__skills-summary"))
        self.assertFalse(without_description.with_class("resume__summary"))

    def test_summary_badges_are_an_ordered_collection_of_escaped_text(self):
        document = self.document("skills")
        summary = document.with_class("resume__skills-summary")[0]
        children = document.descendants(summary)
        self.assertEqual([document.text_content(attrs) for tag, attrs in children if tag == "h3"],
                         [BADGE_TITLE])
        badges = self.descendants_with_class(document, summary, "resume__summary-badges")
        self.assertEqual(len(badges), 1)
        self.assertTrue(any(tag == "ul" and attrs is badges[0] for tag, attrs in children))
        self.assertEqual([document.text_content(attrs).strip()
                          for tag, attrs in document.descendants(badges[0]) if tag == "li"],
                         ["Dr. Sandra J. Finley Scholar", "Gauthier Fellowship Award",
                          "Service Honor", "Text-only distinction", BADGE_ITEM])
        self.assertFalse(document.find("img", src="x"))
        self.assertTrue(all("src" in attrs for attrs in document.find("script")))

    def test_badge_icons_support_defaults_custom_classes_and_explicit_omission(self):
        document = self.document("skills")
        badges = document.with_class("resume__summary-badges")[0]
        items = [attrs for tag, attrs in document.descendants(badges) if tag == "li"]
        self.assertEqual(len(items), 5)
        for item, expected in zip(items, ("bi bi-award", "bi bi-trophy", "bi bi-award",
                                           None, BADGE_ICON)):
            with self.subTest(label=document.text_content(item).strip()):
                icons = [attrs for tag, attrs in document.descendants(item) if tag == "i"]
                if expected is None:
                    self.assertFalse(icons)
                else:
                    self.assertEqual(len(icons), 1)
                    self.assertEqual(icons[0]["class"], expected)
                    self.assertEqual(icons[0]["aria-hidden"], "true")
        self.assertFalse(any("onerror" in attrs for _, attrs in document.elements))

    def test_badge_strip_preserves_native_content_in_a_named_focusable_region(self):
        for output, expected_name in (
                ("skills", BADGE_TITLE), ("badges-only", "Awards and Honors"),
                ("badges-no-skills", "Awards and Honors"),
                ("badges-missing-title", "Resume highlights"),
                ("badges-blank-title", "Resume highlights")):
            with self.subTest(output=output):
                document = self.document(output)
                highlights = document.with_class("resume__summary-highlights")
                self.assertEqual(len(highlights), 1)
                self.assertIn("data-badge-marquee", highlights[0])
                children = document.descendants(highlights[0])
                regions = [attrs for _, attrs in children if attrs.get("role") == "region"]
                self.assertEqual(len(regions), 1)
                region = regions[0]
                self.assertEqual(region.get("tabindex"), "0")
                self.assertTrue(region.get("id"))
                self.assertNotIn("hidden", region)
                if "aria-labelledby" in region:
                    labels = [document.find(id=identifier)[0]
                              for identifier in region["aria-labelledby"].split()]
                    name = " ".join(document.text_content(label).strip() for label in labels)
                else:
                    name = region.get("aria-label")
                self.assertEqual(name, expected_name)

                badges = document.with_class("resume__summary-badges")
                self.assertEqual(len(badges), 1)
                self.assertTrue(any(attrs is badges[0]
                                    for _, attrs in document.descendants(region)))
                for tag, attrs in document.descendants(region):
                    self.assertNotIn("hidden", attrs)
                    if tag != "i":
                        self.assertNotEqual(attrs.get("aria-hidden"), "true")

                identifiers = [attrs["id"] for _, attrs in document.elements if "id" in attrs]
                self.assertEqual(len(identifiers), len(set(identifiers)))

    def test_badge_links_are_optional_native_links_with_safe_urls(self):
        document = self.document("badge-links")
        badges = document.with_class("resume__summary-badges")[0]
        cards = self.descendants_with_class(document, badges, "resume__badge")
        expected = [("Plain string", None), ("Missing link", None)] + [
            (label, href) for label, _, href in BADGE_LINK_CASES]
        self.assertEqual(len(cards), len(expected))
        self.assertFalse(document.with_class("resume__badges-title"))
        self.assertFalse(document.find("h2"))
        for card, (label, href) in zip(cards, expected):
            with self.subTest(label=label):
                self.assertEqual(document.text_content(card).strip(), label)
                if href:
                    self.assertTrue(any(attrs is card for attrs in document.find("a")))
                    self.assertEqual(card.get("href"), href)
                    self.assertEqual(card.get("target"), "_blank")
                    self.assertTrue({"noopener", "noreferrer"}.issubset(card.get("rel", "").split()))
                    self.assertNotEqual(card.get("tabindex"), "-1")
                else:
                    self.assertTrue(any(attrs is card for attrs in document.find("div")))
                    self.assertNotIn("href", card)
                    self.assertNotIn("tabindex", card)
        self.assertFalse(any("onerror" in attrs or "onclick" in attrs
                             for _, attrs in document.elements))

    def test_linked_badges_are_preserved_in_home_preview_and_full_resume(self):
        home = self.document("")
        for output, preview in zip(("preview", "preview-default", "preview-blank-button"),
                                   home.with_class("resume-preview")):
            for document, ancestor in ((home, preview), (self.document(output), None)):
                with self.subTest(output=output, preview=ancestor is not None):
                    cards = (self.descendants_with_class(document, ancestor, "resume__badge")
                             if ancestor is not None else document.with_class("resume__badge"))
                    self.assertEqual(len(cards), 2)
                    self.assertEqual(document.text_content(cards[0]).strip(), "Research award")
                    self.assertEqual(cards[0].get("href"), BADGE_LINK)
                    self.assertEqual(cards[0].get("target"), "_blank")
                    self.assertTrue({"noopener", "noreferrer"}.issubset(cards[0].get("rel", "").split()))
                    self.assertFalse(cards[1].get("href"))

    def test_badges_without_description_use_the_appropriate_summary_and_heading(self):
        for output, summary_class, expected in (
                ("badges-only", "resume__skills-summary", [("h2", "Awards and Honors")]),
                ("badges-no-skills", "resume__summary",
                 [("h2", "Professional Summary"), ("h3", "Awards and Honors")])):
            with self.subTest(output=output):
                document = self.document(output)
                summaries = document.with_class(summary_class)
                self.assertEqual(len(summaries), 1)
                children = document.descendants(summaries[0])
                self.assertEqual([(tag, document.text_content(attrs))
                                  for tag, attrs in children if tag in ("h2", "h3")], expected)
                self.assertEqual([document.text_content(attrs).strip()
                                  for tag, attrs in children if tag == "li"],
                                 ["Dr. Sandra J. Finley Scholar", "Gauthier Fellowship Award"])
                self.assertFalse(any(tag == "p" for tag, _ in children))

    def test_optional_badge_titles_and_empty_summary_content_leave_no_placeholders(self):
        for output in ("badges-missing-title", "badges-blank-title"):
            with self.subTest(output=output):
                document = self.document(output)
                summary = document.with_class("resume__summary")[0]
                children = document.descendants(summary)
                self.assertFalse(any(tag in ("h2", "h3") for tag, _ in children))
                self.assertEqual([document.text_content(attrs).strip()
                                  for tag, attrs in children if tag == "li"],
                                 ["Dr. Sandra J. Finley Scholar"])
        for output in ("empty-summary", "seo-only"):
            with self.subTest(output=output):
                document = self.document(output)
                self.assertFalse(document.with_class("resume__skills-summary"))
                self.assertFalse(document.with_class("resume__summary"))
                self.assertFalse(document.with_class("resume__summary-badges"))
                self.assertFalse(document.with_class("resume__summary-highlights"))
                self.assertFalse(document.find("h2"))
        self.assertEqual(self.document("seo-only").find("meta", name="description")[0]["content"],
                         "SEO description only.")
        for output in ("skills-only", "empty-summary"):
            self.assertEqual(self.document(output).find("meta", name="description")[0]["content"],
                             "An isolated resume test site.")

    def test_dates_follow_article_style_without_inventing_precision(self):
        document = self.document("resume")
        expected = ((LABEL, ("July 2019", "December 2024")),
                    ("Full-date appointment", ("January 02, 2020", "May 31, 2024")),
                    ("Continuing appointment", ("2024", "Present")))
        for title, labels in expected:
            with self.subTest(title=title):
                entry = self.entry(document, title)
                period = self.descendants_with_class(document, entry, "resume__period")
                self.assertEqual(len(period), 1)
                period_text = document.text_content(period[0])
                for label in labels:
                    self.assertIn(label, period_text)
                self.assertTrue(self.descendants_with_class(document, period[0], "bi-calendar-event"))
                self.assertNotIn("Period:", document.text_content(entry))
        self.assertTrue(document.find("time", datetime="2020-01-02"))
        self.assertTrue(document.find("time", datetime="2024-05-31"))
        month_entry = self.entry(document, LABEL)
        self.assertNotIn("July 01", document.text_content(month_entry))
        self.assertNotIn("December 01", document.text_content(month_entry))

    def test_all_optional_metadata_combinations_omit_empty_fields(self):
        document = self.document("optional")
        self.assertEqual(len(document.with_class("resume__entry")), 8)
        for mask in range(8):
            with self.subTest(mask=mask):
                entry = self.entry(document, f"Optional {mask}")
                period = self.descendants_with_class(document, entry, "resume__period")
                details = self.descendants_with_class(document, entry, "resume__details")
                organization = self.descendants_with_class(document, entry, "resume__organization")
                location = self.descendants_with_class(document, entry, "resume__location")
                self.assertEqual(bool(period), bool(mask & 1))
                self.assertEqual(bool(details), bool(mask & 6))
                self.assertEqual(bool(organization), bool(mask & 2))
                self.assertEqual(bool(location), bool(mask & 4))
                text = document.text_content(entry)
                self.assertIn(f"Achievement {mask}.", text)
                if mask & 1:
                    self.assertIn("June 2021", text)
                    self.assertIn("Present", text)
                if mask & 2:
                    self.assertIn("Group: Controls", text)
                    self.assertTrue(any(tag == "a" and attrs.get("href") == BASE + "about/"
                                        for tag, attrs in document.descendants(entry)))
                if mask & 4:
                    self.assertIn("Room: 204, Urbana", text)
                for label in ("Period:", "Organization:", "Location:"):
                    self.assertNotIn(label, text)

    def test_unrecognized_quotes_and_metadata_after_prose_are_preserved(self):
        document = self.document("cv")
        quoted = self.entry(document, "Quoted role")
        quote = [attrs for tag, attrs in document.descendants(quoted) if tag == "blockquote"]
        self.assertEqual(len(quote), 1)
        self.assertIn("A conventional blockquote belongs to the description.",
                      document.text_content(quote[0]))
        prose = self.entry(document, "Prose before quote")
        self.assertIn("Period: this is ordinary quoted prose", document.text_content(prose))
        self.assertTrue(any(tag == "blockquote" for tag, _ in document.descendants(prose)))
        self.assertFalse(self.descendants_with_class(document, prose, "resume__period"))
        mixed = self.entry(document, "Mixed quote")
        self.assertIn("Period: 2024 / Present", document.text_content(mixed))
        self.assertIn("Team notes: preserve this entire quote", document.text_content(mixed))
        self.assertTrue(any(tag == "blockquote" for tag, _ in document.descendants(mixed)))
        self.assertFalse(self.descendants_with_class(document, mixed, "resume__period"))
        empty = self.entry(document, "Empty metadata")
        self.assertIn("A result without metadata placeholders.", document.text_content(empty))
        self.assertFalse(self.descendants_with_class(document, empty, "resume__period"))
        self.assertFalse(self.descendants_with_class(document, empty, "resume__details"))
        self.assertFalse(any(tag == "blockquote" for tag, _ in document.descendants(empty)))

    def test_markdown_escaped_headings_and_plain_frontmatter_are_not_executed(self):
        document = self.document("resume")
        self.assertEqual(document.text_content(document.find("h3")[0]).strip(), LABEL)
        self.assertEqual(document.text_content(document.with_class("resume__subtitle")[0]).strip(), LABEL)
        fallback = self.document("cv")
        self.assertEqual(fallback.text_content(fallback.find("h1", id="resume-title")[0]).strip(), TITLE)
        for fixture in (document, fallback):
            self.assertFalse(fixture.find("img", src="x"))
            self.assertFalse(any("onerror" in attrs for _, attrs in fixture.elements))
            self.assertTrue(all("src" in attrs for attrs in fixture.find("script")))

    def test_column_breaks_and_minimal_pages_remain_readable(self):
        for output, columns in (("resume", 2), ("cv", 1), ("optional", 1)):
            with self.subTest(output=output):
                document = self.document(output)
                self.assertEqual(len(document.with_class("resume__column")), columns)
                self.assertEqual(bool(document.with_class("resume__columns--split")), columns == 2)
                for section in document.with_class("resume__section"):
                    headings = [attrs for tag, attrs in document.descendants(section) if tag == "h2"]
                    self.assertEqual(len(headings), 1)
                    self.assertTrue(headings[0].get("id"))
        minimal = self.document("minimal")
        self.assertIn("body-only resume", minimal.text)
        self.assertTrue(minimal.find("strong"))
        self.assertFalse(minimal.with_class("resume__summary"))
        self.assertFalse(minimal.with_class("resume__entry"))
        self.assertFalse(minimal.with_class("resume__period"))

    def test_site_prefix_and_native_markdown_links_are_preserved(self):
        document = self.document("resume")
        self.assertTrue(document.find("a", href=BASE + "about/"))
        self.assertTrue(document.find("a", href=BASE + "resume/group/"))
        self.assertTrue(document.find("a", href="https://example.org/university?a=1&b=2"))
        self.assertTrue(document.find("a", href=BASE.rstrip("/")))
        for output in ("resume", "cv", "optional", "minimal", "skills", "badges-only"):
            with self.subTest(output=output):
                document = self.document(output)
                self.assertTrue(document.find("link", href=BASE + "assets/stylesheet/page-resume.css"))
                self.assertFalse(document.find("link", href=BASE + "assets/stylesheet/resume-preview.css"))
                self.assertTrue(document.find("script", src=BASE + "assets/script/home.js"))
                self.assertTrue(document.find("script", src=BASE + "assets/script/resume.js"))
                for tag, attrs in document.elements:
                    for key in ("href", "src"):
                        self.assertFalse(attrs.get(key, "").startswith("/"), (tag, attrs))

    def test_resume_content_is_available_without_javascript_or_animations(self):
        for output in ("resume", "cv", "optional", "minimal"):
            with self.subTest(output=output):
                document = self.document(output)
                self.assertFalse(document.find(id="preloader"))
                article = document.find("article", id="resume-main")[0]
                self.assertEqual(article["aria-labelledby"], "resume-title")
                self.assertTrue(document.find("a", href="#resume-main"))
                self.assertTrue(document.find("button", type="button", **{
                    "aria-label": "Toggle navigation", "aria-controls": "navmenu",
                    "aria-expanded": "false"}))
                self.assertNotIn("hidden", article)
                for tag, attrs in document.descendants(article):
                    self.assertNotIn("data-aos", attrs)
                    self.assertNotIn("hidden", attrs)
                    if tag != "i":
                        self.assertNotEqual(attrs.get("aria-hidden"), "true")

    def test_landing_page_false_removes_home_navigation_entry_only(self):
        home = Document(self.home_without_resume)
        navigation = home.find("nav", id="navmenu")[0]
        links = [attrs["href"] for tag, attrs in home.descendants(navigation) if tag == "a"]
        self.assertNotIn(BASE + "resume/", links)
        self.assertNotIn("#resume", links)
        self.assertIn("#about", links)
        self.assertFalse(home.with_class("bi-file-earmark-person"))
        self.assertFalse(home.with_class("resume"))
        for output in ("about", "resume"):
            document = self.document(output)
            navigation = document.find("nav", id="navmenu")[0]
            self.assertTrue(any(tag == "a" and attrs.get("href") == BASE + "resume/"
                                for tag, attrs in document.descendants(navigation)))
        for document in (home, self.document("about")):
            self.assertFalse(document.find(
                "link", href=BASE + "assets/stylesheet/page-resume.css"))
            self.assertFalse(document.find(
                "link", href=BASE + "assets/stylesheet/resume-preview.css"))
            self.assertFalse(document.find(
                "script", src=BASE + "assets/script/resume.js"))
        self.assertTrue((self.site / "public/assets/stylesheet/page-resume.css").is_file())
        self.assertTrue((self.site / "public/assets/script/resume.js").is_file())

    def test_landing_resume_previews_include_only_heading_subtitle_and_summary(self):
        home = self.document("")
        previews = home.with_class("resume-preview")
        self.assertEqual(len(previews), 3)
        for preview, title, summary_title in zip(
                previews, (TITLE, "A second resume", "A third resume"),
                ("Professional Summary", "", "Profile")):
            with self.subTest(title=title):
                children = home.descendants(preview)
                self.assertEqual([home.text_content(attrs).strip()
                                  for tag, attrs in children if tag == "h2"], [title])
                self.assertIn(LABEL, home.text_content(preview))
                self.assertIn("I earned a Bachelor of Science", home.text_content(preview))
                self.assertTrue(any(tag == "strong" and home.text_content(attrs) == "Bachelor of Science"
                                    for tag, attrs in children))
                expected = [("h3", summary_title), ("h4", "Recognition")] if summary_title else [
                    ("h3", "Recognition")]
                self.assertEqual([(tag, home.text_content(attrs).strip())
                                  for tag, attrs in children if tag in ("h3", "h4")], expected)
                self.assertFalse(any(tag == "h1" for tag, _ in children))
                self.assertNotIn("Full-page", home.text_content(preview))
                self.assertFalse(self.descendants_with_class(home, preview, "resume__skills-grid"))
                self.assertFalse(self.descendants_with_class(home, preview, "resume__columns"))
                badges = self.descendants_with_class(home, preview, "resume__summary-badges")
                self.assertEqual(len(badges), 1)
                self.assertEqual([home.text_content(attrs).strip()
                                  for tag, attrs in home.descendants(badges[0]) if tag == "li"],
                                 ["Research award", "Teaching award"])
        self.assertFalse(home.find("img", src="x"))
        self.assertFalse(any("onerror" in attrs for _, attrs in home.elements))

    def test_landing_resume_buttons_use_custom_text_or_default_and_section_permalink(self):
        home = self.document("")
        for preview, output, label in zip(
                home.with_class("resume-preview"),
                ("preview", "preview-default", "preview-blank-button"),
                (BUTTON_TEXT, "View full resume", "View full resume")):
            with self.subTest(output=output):
                more = self.descendants_with_class(home, preview, "resume-preview__more")
                self.assertEqual(len(more), 1)
                links = [attrs for tag, attrs in home.descendants(more[0]) if tag == "a"]
                self.assertEqual(len(links), 1)
                self.assertEqual(links[0]["href"], BASE + output + "/")
                self.assertEqual(home.text_content(links[0]).strip(), label)
                full = self.document(output)
                self.assertFalse(full.with_class("resume-preview__more"))
                self.assertEqual(full.text_content(full.find("h1", id="resume-title")[0]).strip(),
                                 "Full-page name for " + output)
                self.assertTrue(full.with_class("resume__skills-grid"))
                self.assertIn("Full-page achievement.", full.text)

    def test_multiple_home_resumes_have_unique_badge_regions_and_load_assets_once(self):
        home = self.document("")
        identifiers = [attrs["id"] for _, attrs in home.elements if "id" in attrs]
        self.assertEqual(len(identifiers), len(set(identifiers)))
        self.assertEqual(len(home.find("link", href=BASE + "assets/stylesheet/resume-preview.css")), 1)
        self.assertFalse(home.find("link", href=BASE + "assets/stylesheet/page-resume.css"))
        self.assertEqual(len(home.find("script", src=BASE + "assets/script/resume.js")), 1)
        for preview in home.with_class("resume-preview"):
            regions = self.descendants_with_class(home, preview, "resume__badges-viewport")
            self.assertEqual(len(regions), 1)
            self.assertEqual(regions[0].get("tabindex"), "0")
            self.assertTrue(regions[0].get("id"))
        navigation = home.find("nav", id="navmenu")[0]
        links = [attrs["href"] for tag, attrs in home.descendants(navigation) if tag == "a"]
        for preview in home.with_class("resume-preview"):
            self.assertIn("#" + preview["id"], links)
        for output in ("resume", "unordered-resume"):
            self.assertNotIn("#" + output, links)
            self.assertNotIn(BASE + output + "/", links)
        self.assertNotIn("Unordered resume", home.text)

    def test_preview_styles_do_not_override_home_navigation(self):
        stylesheet = (self.site / "public/assets/stylesheet/resume-preview.css").read_text(
            encoding="utf-8")
        self.assertIn(".resume__summary", stylesheet)
        self.assertIn(".resume__badges-viewport", stylesheet)
        self.assertIn(".resume-preview__more", stylesheet)
        self.assertNotRegex(stylesheet, r"(?<![\w-])\.(?:header|navmenu|nav-toggle)(?![\w-])")


if __name__ == "__main__":
    unittest.main(verbosity=2)
