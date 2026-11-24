"""Opt-in, local-only full semantic comparison of h1/list/item/b Change Notes.

No fetching, old-verifier replacement, global stripping or whitespace collapse.
The four BBCode layout adjustments below model verified Steam block boundaries;
every other text character, space, line break and format node is compared.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys


@dataclass(frozen=True)
class Node:
    kind: str
    text: str = ""
    children: tuple["Node", ...] = ()


@dataclass
class _Builder:
    kind: str
    children: list[Node] = field(default_factory=list)

    def finish(self) -> Node:
        return Node(self.kind, children=tuple(self.children))


def _text(builder: _Builder, value: str) -> None:
    """Preserve every character; HTML entities have already been decoded once."""
    if "\r" in value:
        raise ValueError("bare/CRLF text is outside this LF structured-notes profile")
    for index, part in enumerate(value.split("\n")):
        if index:
            builder.children.append(Node("break"))
        if part:
            if builder.children and builder.children[-1].kind == "text":
                old = builder.children.pop()
                builder.children.append(Node("text", old.text + part))
            else:
                builder.children.append(Node("text", part))


_BB_TAG = re.compile(r"\[(/?)([A-Za-z][A-Za-z0-9]*|\*)\]")


def _bb_tree(value: str) -> Node:
    stack = [_Builder("notes")]
    end = 0
    for match in _BB_TAG.finditer(value):
        _text(stack[-1], value[end:match.start()])
        closing, name = bool(match[1]), match[2].lower()
        if name not in {"h1", "list", "*", "b"}:
            raise ValueError(f"unsupported BBCode tag: {name}")
        if name == "*":
            if closing:
                raise ValueError("item ends only at the next item or list close")
            if stack[-1].kind == "item":
                stack[-2].children.append(stack.pop().finish())
            if stack[-1].kind != "list":
                raise ValueError("item must belong directly to a list")
            stack.append(_Builder("item"))
        elif closing:
            kind = {"h1": "heading1", "list": "list", "b": "bold"}[name]
            if kind == "list" and stack[-1].kind == "item":
                stack[-2].children.append(stack.pop().finish())
            if len(stack) == 1 or stack[-1].kind != kind:
                raise ValueError(f"unbalanced BBCode close: {name}")
            stack[-2].children.append(stack.pop().finish())
        else:
            kind = {"h1": "heading1", "list": "list", "b": "bold"}[name]
            if kind in {"heading1", "list"} and stack[-1].kind != "notes":
                raise ValueError("this opt-in profile permits only top-level headings and lists")
            if kind == "bold" and stack[-1].kind not in {"notes", "heading1", "item", "bold"}:
                raise ValueError("bold is an inline node")
            stack.append(_Builder(kind))
        end = match.end()
    _text(stack[-1], value[end:])
    if len(stack) != 1:
        raise ValueError("incomplete BBCode structure")
    return stack[0].finish()


def _canonical(tree: Node, *, bbcode: bool) -> tuple[Node, list[str]]:
    """Adjust only exact, verified structural LF boundaries, never text/spaces."""
    adjustments: list[str] = []

    def visit(node: Node, path: str) -> Node:
        if node.kind in {"text", "break"}:
            return node
        children = [visit(child, f"{path}/{i}") for i, child in enumerate(node.children)]
        if node.kind == "list":
            # Steam consumes the LF directly after [list], not inline item text.
            if bbcode and children and children[0].kind == "break":
                children.pop(0)
                adjustments.append(path + ":list-opening-one-LF")
            if any(child.kind != "item" for child in children):
                raise ValueError("list contains text or unverified layout outside its items")
            if bbcode and children and children[-1].children and children[-1].children[-1].kind == "break":
                last = children[-1]
                children[-1] = Node("item", children=last.children[:-1])
                adjustments.append(path + ":final-item-one-LF-before-list-close")
        if node.kind == "notes" and bbcode:
            selected: list[Node] = []
            for child in children:
                if child.kind == "break" and selected and selected[-1].kind == "heading1":
                    # A block heading consumes exactly one following source LF.
                    # A second LF remains and must match the actual HTML <br>.
                    selected.append(Node("heading-layout-consumed"))
                    adjustments.append(path + ":heading-following-one-LF")
                else:
                    selected.append(child)
            children = [child for child in selected if child.kind != "heading-layout-consumed"]
            if len(children) >= 2 and children[-2].kind == "list" and children[-1].kind == "break":
                children.pop()
                adjustments.append(path + ":final-list-file-one-LF")
        return Node(node.kind, children=tuple(children))

    return visit(tree, "notes"), adjustments


def parse_bbcode_notes(value: str) -> tuple[Node, list[str]]:
    return _canonical(_bb_tree(value), bbcode=True)


class _SteamNotes(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, _Builder]] = [("", _Builder("notes"))]

    def handle_data(self, data: str) -> None:
        _text(self.stack[-1][1], data)

    def handle_comment(self, data: str) -> None:
        raise ValueError("comments are not approved structured-notes markup")

    def handle_decl(self, decl: str) -> None:
        raise ValueError("declarations are not notes content")

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if len({key for key, _ in attrs}) != len(attrs):
            raise ValueError("duplicate notes HTML attribute")
        attributes = dict(attrs)
        parent = self.stack[-1][1].kind
        if tag == "br" and not attributes:
            if parent not in {"notes", "heading1", "item", "bold"}:
                raise ValueError("line break outside inline notes content")
            self.stack[-1][1].children.append(Node("break"))
            return
        if tag in {"b", "strong"} and not attributes:
            kind = "bold"
        elif (tag == "div" and attributes == {"class": "bb_h1"}) or (tag == "h1" and not attributes):
            kind = "heading1"
        elif tag == "ul" and attributes == {"class": "bb_ul"}:
            kind = "list"
        elif tag == "li" and not attributes:
            kind = "item"
        else:
            raise ValueError(f"unsupported or decorated notes HTML: {tag}")
        if kind in {"heading1", "list"} and parent != "notes":
            raise ValueError("heading/list must belong directly to notes")
        if kind == "item" and parent != "list":
            raise ValueError("list item lacks its actual list")
        if kind == "bold" and parent not in {"notes", "heading1", "item", "bold"}:
            raise ValueError("bold is not valid in this block position")
        self.stack.append((tag, _Builder(kind)))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "br":
            raise ValueError("only a line break may be self closing")
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        if len(self.stack) == 1 or self.stack[-1][0] != tag:
            raise ValueError(f"unbalanced notes HTML close: {tag}")
        node = self.stack.pop()[1].finish()
        self.stack[-1][1].children.append(node)

    def result(self) -> Node:
        if len(self.stack) != 1:
            raise ValueError("incomplete notes HTML")
        return _canonical(self.stack[0][1].finish(), bbcode=False)[0]


def parse_steam_notes_html(body: str) -> Node:
    parser = _SteamNotes()
    parser.feed(body)
    parser.close()
    return parser.result()


class _Entries(HTMLParser):
    """Capture literal p[id] bodies without browser repair of Steam's div-in-p."""
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.entry_id: str | None = None
        self.parts: list[str] = []
        self.entries: list[tuple[str, str]] = []
        self.ids: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self.entry_id is not None:
            if tag == "p":
                raise ValueError("nested/unclosed changelog paragraph")
            self.parts.append(self.get_starttag_text())
        elif tag == "p":
            values = [value for key, value in attrs if key == "id"]
            if len(values) > 1:
                raise ValueError("duplicate changelog ID attribute")
            if len(values) == 1 and values[0] is not None and re.fullmatch(r"[1-9][0-9]*", values[0], re.ASCII):
                if len(attrs) != 1:
                    raise ValueError("unverified attributes decorate a changelog paragraph")
                if values[0] in self.ids:
                    raise ValueError("duplicate public changelog entry ID")
                self.ids.add(values[0])
                self.entry_id = values[0]
                self.parts = []

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self.entry_id is not None:
            self.parts.append(self.get_starttag_text())

    def handle_endtag(self, tag: str) -> None:
        if self.entry_id is None:
            return
        if tag == "p":
            self.entries.append((self.entry_id, "".join(self.parts)))
            self.entry_id = None
            self.parts = []
        else:
            self.parts.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        if self.entry_id is not None:
            self.parts.append(data)

    def handle_entityref(self, name: str) -> None:
        if self.entry_id is not None:
            self.parts.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        if self.entry_id is not None:
            self.parts.append(f"&#{name};")

    def handle_comment(self, data: str) -> None:
        if self.entry_id is not None:
            self.parts.append("<!--" + data + "-->")

    def finish(self) -> list[tuple[str, str]]:
        if self.entry_id is not None:
            raise ValueError("incomplete changelog paragraph")
        return self.entries


def _tree_data(node: Node) -> dict[str, object]:
    result: dict[str, object] = {"kind": node.kind}
    if node.kind == "text":
        result["text"] = node.text
    elif node.children:
        result["children"] = [_tree_data(child) for child in node.children]
    return result


def _tree_hash(node: Node) -> str:
    data = json.dumps(_tree_data(node), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _counts(node: Node) -> dict[str, int]:
    result = {name: 0 for name in ("heading1", "list", "item", "bold", "break", "text")}
    def visit(value: Node) -> None:
        if value.kind in result:
            result[value.kind] += 1
        for child in value.children:
            visit(child)
    visit(node)
    return result


def verify_structured_notes(*, expected_change_notes: str, changelog_html: str,
                            item_api: dict[str, object], item_id: str) -> dict[str, object]:
    """Explicit opt-in API. This adds only Notes semantics, not other release qualifications."""
    if re.fullmatch(r"[1-9][0-9]*", item_id, re.ASCII) is None:
        raise ValueError("canonical item ID must be positive decimal ASCII")
    try:
        details = item_api["response"]["publishedfiledetails"]
        if not isinstance(details, list) or len(details) != 1:
            raise ValueError("exactly one actual API item required")
        item = details[0]
        if (not isinstance(item, dict) or item.get("publishedfileid") != item_id
                or type(item.get("result")) is not int or item.get("result") != 1):
            raise ValueError("public item API identity/result differs")
    except (KeyError, TypeError, IndexError) as error:
        raise ValueError("actual public API shape missing") from error
    expected, layout = parse_bbcode_notes(expected_change_notes)
    extractor = _Entries()
    extractor.feed(changelog_html)
    extractor.close()
    entries = extractor.finish()
    matches: list[tuple[str, Node]] = []
    diagnostics: list[dict[str, object]] = []
    for entry_id, body in entries:
        try:
            actual = parse_steam_notes_html(body)
        except ValueError as error:
            diagnostics.append({"entry_id": entry_id, "supported_structure": False, "reason": str(error)})
            continue
        equal = actual == expected
        diagnostics.append({"entry_id": entry_id, "supported_structure": True, "full_semantics_equal": equal,
                            "semantic_sha256": _tree_hash(actual)})
        if equal:
            matches.append((entry_id, actual))
    if len(matches) > 1:
        raise ValueError("multiple complete public Change Notes entries match")
    result: dict[str, object] = {
        "schema": "xar.workshop.structured-bbcode-notes-verification.v1",
        "mode": "EXPLICIT_LOCAL_STRUCTURED_BBCODE_H1_LIST_ITEM_B",
        "canonical_item_id": item_id,
        "public_api_time_updated": item.get("time_updated"),
        "change_notes_exact": len(matches) == 1,
        "changelog_entry_id": matches[0][0] if matches else None,
        "complete_semantic_match_count": len(matches),
        "expected_full_semantic_sha256": _tree_hash(expected),
        "public_full_semantic_sha256": _tree_hash(matches[0][1]) if matches else None,
        "expected_full_semantic_tree": _tree_data(expected),
        "public_full_semantic_tree": _tree_data(matches[0][1]) if matches else None,
        "expected_structure_counts": _counts(expected),
        "expected_block_layout_adjustments": layout,
        "entry_diagnostics": diagnostics,
        "layout_policy": "Only four verified expected-BBCode block LF boundaries; no global strip/collapse, no text/space/inline LF or format loss.",
        "qualification": "Full saved Notes semantic comparison only; no new HTTP, upload, owner/gallery/title/body or business qualification.",
    }
    result["ok"] = result["change_notes_exact"]
    return result


def _input(path: Path, maximum: int) -> tuple[bytes, dict[str, object]]:
    with path.open("rb") as stream:
        data = stream.read(maximum + 1)
    if len(data) > maximum:
        raise ValueError("local input exceeds bounded profile")
    return data, {"path": str(path.resolve()), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--structured-bbcode-notes", action="store_true", required=True)
    parser.add_argument("--item-id", required=True)
    parser.add_argument("--item-api-file", type=Path, required=True)
    parser.add_argument("--change-notes-file", type=Path, required=True)
    parser.add_argument("--changelog-html-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        api, api_pin = _input(args.item_api_file, 1024 * 1024)
        notes, notes_pin = _input(args.change_notes_file, 16384)
        page, page_pin = _input(args.changelog_html_file, 5 * 1024 * 1024)
        result = verify_structured_notes(expected_change_notes=notes.decode("utf-8"), changelog_html=page.decode("utf-8"),
                                         item_api=json.loads(api.decode("utf-8-sig")), item_id=args.item_id)
        result["actual_readonly_inputs"] = {"API": api_pin, "expected_notes": notes_pin, "changelog_HTML": page_pin}
        if not args.output.parent.is_dir():
            raise ValueError("output parent must already exist")
        with args.output.open("x", encoding="utf-8", newline="\n") as output:
            json.dump(result, output, ensure_ascii=False, indent=2)
            output.write("\n")
        print(json.dumps({"ok": result["ok"], "report": str(args.output), "entry_id": result["changelog_entry_id"]}))
        return 0 if result["ok"] else 1
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as error:
        print(f"LOCAL STRUCTURED NOTES VERIFICATION REFUSED: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
