"""Configured, language-independent visual routing. Pixels provide no game truth.

Templates remain in the testing project's external evidence directory. This
module contains no CK3/mod artwork, text, actor, resolution, or window positions.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageStat

from .evidence import NeedsOperator, checked_file, require


def glyph_bands(crop: Image.Image, minimum: int = 100, maximum: int = 130) -> list[dict]:
    bands: list[dict] = []
    for y in range(crop.height):
        count = sum(min(rgb) >= minimum and max(rgb) >= maximum
                    for rgb in (crop.getpixel((x, y)) for x in range(crop.width)))
        if count < 5:
            continue
        if not bands or y - bands[-1]["last_y"] > 2:
            bands.append({"first_y": y, "last_y": y, "pixels": count})
        else:
            bands[-1]["last_y"] = y
            bands[-1]["pixels"] += count
    return [b for b in bands if 5 <= b["last_y"] - b["first_y"] <= 22 and b["pixels"] >= 35]


def text_shape(crop: Image.Image, dark: bool = False) -> dict:
    """Connected glyph-sized pixel masks, without recognizing any characters."""
    w, h = crop.size
    candidates = set()
    for y in range(h):
        for x in range(w):
            rgb = crop.getpixel((x, y))
            if (max(rgb) <= 95 if dark else min(rgb) >= 130 and max(rgb) >= 145
                    and max(rgb) - min(rgb) < 90):
                candidates.add(y * w + x)
    kept = set()
    while candidates:
        seed = candidates.pop()
        group, pending = [seed], [seed]
        while pending:
            i = pending.pop()
            x, y = i % w, i // w
            for j in (i - 1 if x else -1, i + 1 if x + 1 < w else -1,
                      i - w if y else -1, i + w if y + 1 < h else -1):
                if j in candidates:
                    candidates.remove(j)
                    pending.append(j)
                    group.append(j)
        xs, ys = [i % w for i in group], [i // w for i in group]
        if (2 <= max(xs) - min(xs) + 1 <= 40
                and 5 <= max(ys) - min(ys) + 1 <= 32 and len(group) >= 9):
            kept.update(group)
    raw = bytearray((w * h + 7) // 8)
    for i in kept:
        raw[i // 8] |= 1 << (i % 8)
    return {"width": w, "height": h, "pixels": len(kept), "mask_hex": raw.hex(),
            "sha256": hashlib.sha256(raw).hexdigest()}


def shape_close(a: dict, b: dict) -> bool:
    if (a["width"], a["height"]) != (b["width"], b["height"]):
        return False
    aa, bb = bytes.fromhex(a["mask_hex"]), bytes.fromhex(b["mask_hex"])
    union = sum((x | y).bit_count() for x, y in zip(aa, bb))
    delta = sum((x ^ y).bit_count() for x, y in zip(aa, bb))
    return union >= 50 and delta <= max(8, int(union * .035))


def same_window(a: dict, b: dict) -> bool:
    return (a["variant"] == b["variant"] and a["kind"] == b["kind"]
            and a["option_count"] == b["option_count"]
            and all(shape_close(a["shapes"][key], b["shapes"][key])
                    for key in a["shapes"]))


def same_action(a: dict, b: dict) -> bool:
    # Victory/defeat captions and close buttons recur. A different war body is
    # a different result; normal event body animation cannot release a key.
    keys = ("title", "body", "action") if a["kind"] == "WAR_OUTCOME" else ("title", "action")
    return (a["variant"] == b["variant"] and a["kind"] == b["kind"]
            and a["option_count"] == b["option_count"]
            and all(shape_close(a["shapes"][key], b["shapes"][key]) for key in keys))


class PixelRouter:
    def __init__(self, configuration: dict):
        self.configuration = configuration
        self.size = tuple(configuration["frame_size"])
        require(len(self.size) == 2 and min(self.size) > 0, "invalid configured frame size")
        self.templates = {}
        self.buttons = {}
        require(configuration["variants"], "no reviewed window variants")
        for variant in configuration["variants"]:
            require(variant["kind"] in {"STANDARD_EVENT", "WAR_OUTCOME", "MAP_WAIT", "STOP"},
                    "unsupported window kind")
            require(variant.get("reviewed_as") == variant["kind"], "window review kind missing")
            require(len(variant["patterns"]) >= 2, "window requires multiple reviewed shell regions")
            for pattern in variant["patterns"]:
                rect = self.rect(pattern["rect"])
                template = Image.open(checked_file(pattern)).convert("RGB")
                require(template.size == (rect[2] - rect[0], rect[3] - rect[1]), "template geometry differs")
                self.templates[(variant["id"], pattern["path"])] = template
            for strip in variant.get("button_geometry", {}).get("strips", []):
                self.templates[(variant["id"], strip["path"])] = Image.open(checked_file(strip)).convert("RGB")

    def rect(self, value: list[int]) -> tuple[int, int, int, int]:
        require(len(value) == 4 and all(type(v) is int for v in value), "integer rectangle required")
        x, y, right, bottom = value
        require(0 <= x < right <= self.size[0] and 0 <= y < bottom <= self.size[1],
                "rectangle outside exact original frame")
        return x, y, right, bottom

    def matches(self, image: Image.Image, variant: dict) -> bool:
        for pattern in variant["patterns"]:
            delta = ImageStat.Stat(ImageChops.difference(
                image.crop(self.rect(pattern["rect"])),
                self.templates[(variant["id"], pattern["path"])]
            )).mean
            if max(delta) > pattern.get("max_delta", 3):
                return False
        if variant.get("button_geometry"):
            try:
                button = self.war_button(image, variant["button_geometry"])
            except NeedsOperator:
                return False
            for strip in variant["button_geometry"]["strips"]:
                dx, dy, right, bottom = strip["relative_rect"]
                crop = image.crop((button[0] + dx, button[1] + dy,
                                   button[0] + right, button[1] + bottom))
                template = self.templates[(variant["id"], strip["path"])]
                if crop.size != template.size or max(ImageStat.Stat(ImageChops.difference(crop, template)).mean) > strip.get("max_delta", 3):
                    return False
            self.buttons[variant["id"]] = button
        return True

    def war_button(self, image: Image.Image, geometry: dict) -> list[int]:
        """Locate one actual rectangular close button inside the reviewed range.

        Button height can move when the result body grows. Its four borders
        must still match external templates at the observed position.
        """
        left, top, right, bottom = self.rect(geometry["search_rect"])
        min_w, max_w = geometry["width_range"]
        min_h, max_h = geometry["height_range"]
        lines = []
        for y in range(top, bottom):
            hits = [x for x in range(left, right) if self.gold(image.getpixel((x, y)))]
            groups = []
            for x in hits:
                if not groups or x - groups[-1][-1] > 3:
                    groups.append([x])
                else:
                    groups[-1].append(x)
            for group in groups:
                width = group[-1] - group[0] + 1
                if min_w <= width <= max_w and len(group) / width >= .9:
                    lines.append({"y": y, "left": group[0], "right": group[-1] + 1})
        clusters = []
        for line in lines:
            if not clusters or line["y"] - clusters[-1][-1]["y"] > 2:
                clusters.append([line])
            else:
                clusters[-1].append(line)
        candidates = []
        for upper in clusters:
            for lower in clusters:
                y1, y2 = upper[0]["y"], lower[-1]["y"] + 1
                x1 = min(row["left"] for row in upper + lower)
                x2 = max(row["right"] for row in upper + lower)
                if not (min_h <= y2-y1 <= max_h and min_w <= x2-x1 <= max_w):
                    continue
                def side(xstart, xend):
                    return sum(any(self.gold(image.getpixel((x, y)), weak=True)
                                   for x in range(xstart, xend)) for y in range(y1, y2)) / (y2-y1)
                if min(side(x1, x1+5), side(x2-5, x2)) >= .85:
                    candidates.append([x1, y1, x2, y2])
        require(len(candidates) == 1, "unique reviewed war-result close button not found")
        return candidates[0]

    @staticmethod
    def gold(rgb: tuple[int, int, int], weak: bool = False) -> bool:
        r, g, b = rgb
        return r > (45 if weak else 70) and r > g > b and r-b > (10 if weak else 20) and r-g < 40

    def line_strength(self, image: Image.Image, slot: dict, y: int, weak: bool = False) -> float:
        left, right = slot["line_x"]
        threshold, spread = (45, 10) if weak else (70, 25)
        return sum(r > threshold and r > g > b and r - b > spread and r - g < 35
                   for r, g, b in (image.getpixel((x, y)) for x in range(left, right))) / (right - left)

    def slot(self, image: Image.Image, slot: dict) -> dict:
        self.rect(slot["glyph_rect"])
        left, right = slot["line_x"]
        require(0 <= left < right <= self.size[0] and 0 <= slot["top"] < slot["bottom"] < self.size[1],
                "button line outside frame")
        return {**slot, "strong": min(self.line_strength(image, slot, y) for y in (slot["top"], slot["bottom"])),
                "possible": max(self.line_strength(image, slot, y, True) for y in (slot["top"], slot["bottom"])),
                "bands": glyph_bands(image.crop(slot["glyph_rect"]))}

    def route(self, path: Path) -> dict:
        with Image.open(path) as source:
            image = source.convert("RGB")
        require(image.size == self.size, "source dimensions differ; no scaling inferred")
        matches = [v for v in self.configuration["variants"] if self.matches(image, v)]
        # Explicit STOP (e.g. succession) wins over any ordinary shell.
        require(not any(v["kind"] == "STOP" for v in matches), "reviewed stop window; operator required")
        require(len(matches) == 1, "unknown or ambiguous window; operator required")
        variant = matches[0]
        kind = variant["kind"]
        if kind == "MAP_WAIT":
            return {"kind": kind, "variant": variant["id"], "action": None, "routing_only": True,
                    "state_truth": "NOT_READ", "option_count": 0, "shapes": {}}
        first = None
        if kind == "STANDARD_EVENT":
            slots = [self.slot(image, s) for s in variant["option_slots"]]
            require(len(slots) == 5, "ordinary route supports exactly five physical slots")
            for excluded in variant.get("excluded_slots", []):
                row = self.slot(image, excluded)
                require(row["possible"] < .55 and not row["bands"], "earlier/sixth option or body overlaps slot")
            indices = [i for i, s in enumerate(slots) if s["strong"] >= .78]
            require(indices and indices == list(range(indices[0], 5)), "buttons missing/noncontiguous/ambiguous")
            require(not any(s["possible"] >= .55 or s["bands"] for s in slots[:indices[0]]),
                    "possible earlier disabled option; never skip to a later row")
            require(all(len(s["bands"]) == 1 for s in slots[indices[0]:]), "option text wrapped/obscured")
            first = slots[indices[0]]
            require(len(glyph_bands(image.crop(first["glyph_rect"]), 175, 205)) == 1,
                    "physical first option dim/disabled; operator required")
            option_count, action_rect, action = len(indices), first["glyph_rect"], "Shift+1"
        else:
            require(variant.get("unique_close_button_reviewed") is True,
                    "war result close control was not reviewed")
            action_rect = variant.get("action_rect")
            if variant.get("button_geometry"):
                button = self.buttons[variant["id"]]
                left, top, right, bottom = variant["button_geometry"]["action_inset"]
                action_rect = [button[0]+left, button[1]+top, button[2]-right, button[3]-bottom]
            option_count, action = 1, "Escape"
        rois = {**variant["identity_rois"], "action": {"rect": action_rect}}
        if first is not None:
            # Body text must end before the physical first option, independent
            # of whether the window has one, two, three, four or five buttons.
            body = list(rois["body"]["rect"])
            body[3] = min(body[3], first["top"] - 8)
            rois["body"] = {**rois["body"], "rect": body}
        shapes = {key: text_shape(image.crop(self.rect(row["rect"])), row.get("dark", False))
                  for key, row in rois.items()}
        require(set(shapes) == {"title", "body", "action"} and all(s["pixels"] >= 50 for s in shapes.values()),
                "title/body/action shape insufficient")
        fingerprint = hashlib.sha256(json.dumps({"variant": variant["id"], "count": option_count,
            "shapes": {k: v["sha256"] for k, v in shapes.items()}}, sort_keys=True).encode()).hexdigest()
        return {"kind": kind, "variant": variant["id"], "option_count": option_count, "action": action,
                "shapes": shapes, "fingerprint": fingerprint, "routing_only": True,
                "native_enabled": "NOT_QUERIED", "state_truth": "NOT_READ"}
