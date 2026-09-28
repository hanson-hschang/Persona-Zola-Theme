#!/usr/bin/env python3
"""Integration checks for category navigation: python3 -B tests/test_navigation.py."""

from html.parser import HTMLParser
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


THEME = Path(__file__).resolve().parents[1]
BASE = "https://example.test/persona/"


class Element:
    def __init__(self, tag, attributes):
        self.tag = tag
        self.attributes = dict(attributes)
        self.children = []

    def descendants(self, tag=None):
        for child in self.children:
            if tag is None or child.tag == tag:
                yield child
            yield from child.descendants(tag)


class Document(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.root = Element("root", [])
        self.stack = [self.root]
        self.feed(html)

    def handle_starttag(self, tag, attributes):
        element = Element(tag, attributes)
        self.stack[-1].children.append(element)
        if tag not in {"area", "base", "br", "col", "embed", "hr", "img", "input",
                       "link", "meta", "param", "source", "track", "wbr"}:
            self.stack.append(element)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def navigation(self):
        return next(element for element in self.root.descendants("nav")
                    if element.attributes.get("id") == "navmenu")


class CategoryNavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        zola = shutil.which("zola")
        if zola is None:
            raise unittest.SkipTest("Zola 0.23+ is required")
        cls.temporary = tempfile.TemporaryDirectory(prefix="persona-navigation-tests-")
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.site = Path(cls.temporary.name)
        shutil.copy2(THEME / "config.toml", cls.site / "config.toml")
        for directory in ("templates", "sass", "static", "content"):
            shutil.copytree(THEME / directory, cls.site / directory)
        result = subprocess.run([zola, "build", "--base-url", BASE], cwd=cls.site,
                                text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if result.returncode:
            raise AssertionError(f"zola build failed:\n{result.stdout}")

    def document(self, path):
        return Document((self.site / "public" / path / "index.html").read_text(encoding="utf-8"))

    def test_category_dropdown_is_limited_to_interior_navigation(self):
        home_nav = self.document("").navigation()
        self.assertFalse(any("dropdown" in element.attributes.get("class", "").split()
                             for element in home_nav.descendants("li")))

        nav = self.document("maps").navigation()
        category = next(element for element in nav.descendants("li")
                        if "dropdown" in element.attributes.get("class", "").split())
        parent = next(element for element in category.children if element.tag == "a")
        self.assertEqual(parent.attributes["href"], BASE + "maps/")
        self.assertEqual(parent.attributes.get("aria-current"), "page")

        button = next(element for element in category.children if element.tag == "button")
        submenu = next(element for element in category.children if element.tag == "ul")
        self.assertEqual(button.attributes["aria-controls"], submenu.attributes["id"])
        self.assertEqual(button.attributes["aria-expanded"], "false")
        self.assertIn("hidden", button.attributes)
        self.assertEqual([link.attributes["href"] for link in submenu.descendants("a")],
                         [BASE + "maps/public-self/", BASE + "maps/private-soul/"])

    def test_child_section_is_current_on_section_and_post_pages(self):
        for path, current in (("maps/public-self", "page"),
                              ("maps/private-soul/begin-with-persona", "location")):
            with self.subTest(path=path):
                nav = self.document(path).navigation()
                child = next(link for link in nav.descendants("a")
                             if link.attributes.get("href") == BASE + path.split("/")[0]
                             + "/" + path.split("/")[1] + "/")
                self.assertIn("active", child.attributes.get("class", "").split())
                self.assertEqual(child.attributes.get("aria-current"), current)


if __name__ == "__main__":
    unittest.main()
