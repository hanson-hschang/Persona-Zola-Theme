#!/usr/bin/env python3
"""Exercise literal TeX preservation through Markdown and Tera processing."""

from html.parser import HTMLParser
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


THEME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(THEME / "scripts"))
from persona_math import protect_math


class MathText(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.math = []
        self.capture = False
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        if tag == "span" and "persona-math" in dict(attrs).get("class", "").split():
            self.capture = True
            self.math.append("")

    def handle_endtag(self, tag):
        if tag == "span":
            self.capture = False

    def handle_data(self, data):
        if self.capture:
            self.math[-1] += data


class MathProtectionTests(unittest.TestCase):
    def test_exact_tex_with_markdown_html_and_tera_punctuation(self):
        equations = [
            r"$a_i + b_j < c & \{x, y\} + {{not_a_template}}$",
            "$$\n\\begin{aligned}\na_i &= b_j \\\\\n\n c &= \\Real{x} \\{y\\}\n\\end{aligned}\n$$",
            r"\(x_i + y_j\)",
            "\\[\n\\{1,2\\} \\quad x < 4\n\\]",
        ]
        source = "Before.\n\n" + "\n\n".join(equations) + "\n\nAfter."
        processed = protect_math(source)
        self.assertEqual(MathText(processed).math, equations)
        self.assertNotIn("{{not_a_template}}", processed)
        self.assertEqual(protect_math(processed), processed)

    def test_ordinary_markdown_is_unchanged(self):
        source = "# Heading\n\n**Bold** and [link](https://example.test/).\n\n- List\n"
        self.assertEqual(protect_math(source), source)

    def test_heading_ids_do_not_consume_following_math(self):
        source = "## A heading {#custom-id}\n\n$x_i$\n\n{# A real comment #}\n"
        self.assertEqual(MathText(protect_math(source)).math, ["$x_i$"])

    def test_less_than_prose_does_not_hide_following_math(self):
        source = "The plain text x<y precedes $a_i$."
        self.assertEqual(protect_math(source),
                         "The plain text x<y precedes " + protect_math("$a_i$") + ".")

    def test_citation_guide_math_is_protected(self):
        source = (THEME / "content/maps/private-soul/citation-pipeline-guide/index.md").read_text()
        body = source.split("+++", 2)[2]
        math = MathText(protect_math(body)).math
        self.assertIn(r"$x \in \Real{n}$", math)
        self.assertTrue(any(r"\norm{x}_2" in equation for equation in math))

    def test_code_examples_are_unchanged(self):
        source = r"""Inline `$x_i$` and ``a `$y$` b``.

```latex
$$
\{x\} \\
$$
```

~~~~markdown
$not_math$
~~~
still $not_math$
~~~~

    $indented_code$
"""
        source += "\t$tab_indented$\n"
        self.assertEqual(protect_math(source), source)

    def test_quoted_and_list_fences_are_unchanged(self):
        for source in ("> ~~~latex\n> $x_i$\n> ~~~\n",
                       "- ```latex\n  $x_i$\n  ```\n",
                       "> > ```\n> > $x_i$\n> > ```\n"):
            with self.subTest(source=source):
                self.assertEqual(protect_math(source), source)

    def test_list_prose_is_protected_but_list_code_is_unchanged(self):
        source = "- First\n\n    $\\{x\\}$\n\n      $code$\n"
        processed = protect_math(source)
        self.assertEqual(MathText(processed).math, [r"$\{x\}$"])
        self.assertIn("      $code$", processed)

    def test_link_destinations_and_reference_definitions_are_unchanged(self):
        source = ('[Link](https://example.org/$foo$ "A $title$")\n'
                  '[Nested](https://example.org/(a)/$foo$)\n'
                  '[ref]: https://example.org/$foo$ "$title$"\n')
        self.assertEqual(protect_math(source), source)

    def test_unclosed_fence_remains_code(self):
        source = "```latex\n$$x$$\n"
        self.assertEqual(protect_math(source), source)

    def test_escaped_dollars_currency_and_incomplete_math_are_unchanged(self):
        for source in (r"\$x\$ and \$5", "$5 and $10", "$20.00 or $30.00",
                       "$ unspaced $", "$x $", "$unfinished", "$$unfinished",
                       "$x\n\ny$", r"\\(not math\\)"):
            with self.subTest(source=source):
                self.assertEqual(protect_math(source), source)

    def test_escaped_dollars_inside_math_and_numeric_equations(self):
        equations = [r"$\text{price: \$5}$", "$2x + 3$", r"$x \\$", "$x$ and $y$"]
        for source in equations:
            with self.subTest(source=source):
                self.assertTrue(MathText(protect_math(source)).math)

    def test_currency_before_math_is_not_accidentally_captured(self):
        source = r"Prices $5 and $10, or escaped \$20; the equation is $2x$."
        self.assertEqual(MathText(protect_math(source)).math, ["$2x$"])

    def test_tera_and_html_markup_are_unchanged(self):
        source = '''{{ <media.image path="a.svg" caption="$x_i$ and '}}'" /> }}
{% set value = "$x$ and '%}'" %}
{# $x$ #}
{% raw %}$x$ {{ literal }}{% endraw %}
<!-- $x$ -->
<img alt="$x_i$ > $y$" src="example.svg">
<pre>$x$</pre><code>$y$</code>
<script>const price = "$20";</script>
<style>.x::after { content: "$x$"; }</style>
<textarea>$x$</textarea>
'''
        self.assertEqual(protect_math(source), source)

    def test_html_body_math_is_protected(self):
        source = '<div class="equation">\n$$x_i < y_j$$\n</div>'
        self.assertEqual(MathText(protect_math(source)).math, ["$$x_i < y_j$$"])

    def test_display_math_in_blockquotes_preserves_tex_not_quote_markers(self):
        for prefix in ("> ", "> > "):
            source = prefix + "$$\n" + prefix + r"x_i > y_j \\ z &= \{a\}" + "\n" + prefix + "$$\n"
            expected = "$$\n" + r"x_i > y_j \\ z &= \{a\}" + "\n$$"
            self.assertEqual(MathText(protect_math(source)).math, [expected])
            self.assertTrue(protect_math(source).startswith(prefix))


@unittest.skipUnless(shutil.which("zola"), "Zola is required")
class MathRenderingTests(unittest.TestCase):
    EQUATIONS = [
        r"$a_i + b_j < c & \{x\} + {{unknown}}$",
        "$$\n\\begin{aligned}\na &= b \\\\\n c &= \\Real{x} & \\{x\\}\n\\end{aligned}\n$$",
        r"\(x_i + y_j\)",
        "\\[\nx < y & \\{a\\}\n\\]",
    ]

    def build(self, body):
        with tempfile.TemporaryDirectory(prefix="persona-math-") as directory:
            root = Path(directory)
            (root / "content").mkdir()
            (root / "templates").mkdir()
            (root / "config.toml").write_text('base_url = "https://example.test"\n')
            (root / "templates/index.html").write_text("Home")
            (root / "templates/page.html").write_text("{{ page.content | safe }}")
            (root / "content/math.md").write_text('+++\ntitle = "Math"\n+++\n' + body)
            build = subprocess.run(["zola", "build"], cwd=root, text=True,
                                   capture_output=True)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            return (root / "public/math/index.html").read_text()

    def source(self):
        return ("A **bold** introduction with plain x<y.\n\n" + "\n\n".join(self.EQUATIONS)
                + "\n\nA final paragraph.\n")

    def test_zola_preserves_exact_decoded_math(self):
        rendered = self.build(protect_math(self.source()))
        self.assertEqual(MathText(rendered).math, self.EQUATIONS)
        self.assertIn("<strong>bold</strong>", rendered)
        self.assertNotIn("<em>", rendered)

if __name__ == "__main__":
    unittest.main()
