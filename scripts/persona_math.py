"""Protect Markdown-body math before either Pandoc or Zola processes it.

The returned HTML spans contain numeric character references, including the
original delimiters. Browsers decode their text for KaTeX's existing auto-render
step, without Markdown or Tera interpreting TeX punctuation. Call only on the
body of posts with ``extra.tex`` enabled; front matter is the caller's concern.

This is a scoped Markdown scanner, not a Markdown renderer. It leaves code,
HTML attributes/comments/raw-text elements, and Tera tags alone. Math in Tera
component arguments must be handled by the component, not this body transform.
"""

import re


_FENCE = re.compile(r" {0,3}(`{3,}|~{3,})([^\n]*)(?:\n|$)")
_HTML_TAG = re.compile(r"</?([A-Za-z][A-Za-z0-9:-]*)\b")
_RAW_TAGS = {"code", "pre", "script", "style", "textarea"}
_LIST_ITEM = re.compile(r" {0,3}(?:[-+*]|[0-9]{1,9}[.)])(?:[ \t]+|$)")


def _unquote(line: str) -> str:
    """Remove blockquote container markers for block classification only."""
    while match := re.match(r" {0,3}>[ \t]?", line):
        line = line[match.end():]
    return line


def _fence_end(text: str, start: int, marker: str, indent: int) -> int:
    closing = re.compile(r" {0,3}" + re.escape(marker[0])
                         + "{" + str(len(marker)) + r",}[ \t]*(?:\n|$)")
    while start < len(text):
        end = text.find("\n", start)
        end = len(text) if end < 0 else end + 1
        line = _unquote(text[start:end])
        if indent and line.startswith(" " * indent):
            line = line[indent:]
        if closing.fullmatch(line):
            return end
        start = end
    return len(text)


def _link_end(text: str, start: int) -> int | None:
    """Skip a Markdown link destination and optional quoted title."""
    depth = 1
    quote = None
    index = start + 1
    while index < len(text):
        character = text[index]
        if character == "\\":
            index += 2
            continue
        if quote:
            if character == quote:
                quote = None
        elif character in "\"'" and text[index - 1].isspace():
            quote = character
        elif character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
            if not depth:
                return index + 1
        index += 1
    return None


def _quoted_end(text: str, start: int, closing: str) -> int:
    """Find a delimiter outside quoted HTML/Tera strings."""
    quote = None
    index = start
    while index < len(text):
        character = text[index]
        if quote:
            if character == "\\":
                index += 2
                continue
            if character == quote:
                quote = None
        elif text.startswith(closing, index):
            return index + len(closing)
        elif character in "\"'":
            quote = character
        index += 1
    return len(text)


def _math_end(text: str, start: int, opening: str, closing: str) -> int | None:
    index = start + len(opening)
    if opening == "$" and (index == len(text) or text[index].isspace()):
        return None
    while index < len(text):
        if opening == "$" and text[index] == "\n":
            if re.match(r"\n[ \t]*\n", text[index:]):
                return None
        if text.startswith(closing, index):
            end = index + len(closing)
            if opening == "$":
                # The first unescaped dollar must be a valid closer. This
                # prevents common currency amounts from consuming later math.
                if (text[index - 1].isspace() or text.startswith("$$", index)
                        or (end < len(text) and text[end].isdigit())):
                    return None
            return end
        if text[index] == "\\":
            index += 2
        else:
            index += 1
    return None


def _span(math: str) -> str:
    encoded = "".join(f"&#{ord(character)};" for character in math)
    return f'<span class="persona-math">{encoded}</span>'


def _math_in_container(text: str, start: int, end: int) -> str:
    """Strip enclosing Markdown quote markers, keeping TeX comparison signs."""
    prefix = text[text.rfind("\n", 0, start) + 1:start]
    depth = 0
    while match := re.match(r" {0,3}>[ \t]?", prefix):
        prefix = prefix[match.end():]
        depth += 1
    lines = text[start:end].splitlines(keepends=True)
    if depth:
        for index in range(1, len(lines)):
            line = lines[index]
            for _ in range(depth):
                match = re.match(r" {0,3}>[ \t]?", line)
                if not match:
                    break
                line = line[match.end():]
            lines[index] = line
    return "".join(lines)


def protect_math(text: str) -> str:
    """Preserve complete $, $$, \\(, and \\[ math regions in Markdown text.

    Inline dollar delimiters must touch non-whitespace; a closing dollar cannot
    be followed by a digit. Escaped dollars and incomplete regions are retained.
    Display math may span lines, including blank lines. Code and markup remain
    byte-for-byte unchanged. The transform is idempotent.
    """
    result = []
    index = 0
    list_indent = 0
    while index < len(text):
        if index == 0 or text[index - 1] == "\n":
            line_end = text.find("\n", index)
            line_end = len(text) if line_end < 0 else line_end + 1
            line = _unquote(text[index:line_end]).expandtabs(4)
            indent = len(line) - len(line.lstrip(" "))
            list_item = _LIST_ITEM.match(line)
            if list_item:
                list_indent = list_item.end()
                content = line[list_indent:]
            else:
                if line.strip() and indent < list_indent:
                    list_indent = 0
                content = line[min(indent, list_indent):]
            fence = _FENCE.match(content)
            if fence and not (fence[1][0] == "`" and "`" in fence[2]):
                marker = fence[1]
                end = _fence_end(text, line_end, marker, list_indent)
                result.append(text[index:end])
                index = end
                continue
            if content.startswith("    ") or re.match(r" {0,3}\[[^\]\n]+\]:", content):
                result.append(text[index:line_end])
                index = line_end
                continue

        if text.startswith("<!--", index):
            end = text.find("-->", index + 4)
            end = len(text) if end < 0 else end + 3
        elif text[index:index + 2] in {"{{", "{%", "{#"}:
            opener = text[index:index + 2]
            closer = {"{{": "}}", "{%": "%}", "{#": "#}"}[opener]
            if opener == "{#":
                # Markdown heading IDs also start with {# but end in }, not
                # #}. They must not consume the remainder as a Tera comment.
                heading_id = re.match(r"\{#[^{}\s]+\}", text[index:])
                if heading_id:
                    end = index + heading_id.end()
                else:
                    found = text.find(closer, index + 2)
                    end = index + 2 if found < 0 else found + 2
            else:
                end = _quoted_end(text, index + 2, closer)
            if opener == "{%" and re.fullmatch(r"\{%\s*raw\s*%\}", text[index:end]):
                closing_raw = re.search(r"\{%\s*endraw\s*%\}", text[end:])
                end = end + closing_raw.end() if closing_raw else len(text)
        elif text[index] == "<" and (tag := _HTML_TAG.match(text, index)):
            end = _quoted_end(text, tag.end(), ">")
            if not text[index:end].endswith(">"):
                end = index + 1
            elif tag[1].lower() in _RAW_TAGS and not text.startswith("</", index):
                close = re.search(r"</" + re.escape(tag[1]) + r"\s*>", text[end:], re.I)
                end = end + close.end() if close else len(text)
        elif text[index] == "`":
            run_end = index + 1
            while run_end < len(text) and text[run_end] == "`":
                run_end += 1
            marker = text[index:run_end]
            close = re.search(r"(?<!`)" + re.escape(marker) + r"(?!`)", text[run_end:])
            end = run_end + close.end() if close else run_end
        elif text[index] == "(" and index > 0 and text[index - 1] == "]":
            end = _link_end(text, index) or index + 1
        else:
            opening = next((delimiter for delimiter in ("$$", "$", r"\(", r"\[")
                            if text.startswith(delimiter, index)), None)
            if opening:
                closing = {r"\(": r"\)", r"\[": r"\]"}.get(opening, opening)
                math_end = _math_end(text, index, opening, closing)
                if math_end is not None:
                    result.append(_span(_math_in_container(text, index, math_end)))
                    index = math_end
                    continue
                # An incomplete $$ must not be retried as single-dollar math.
                end = index + len(opening)
            elif text[index] == "\\":
                end = min(index + 2, len(text))
            else:
                end = index + 1
        result.append(text[index:end])
        index = end
    return "".join(result)
