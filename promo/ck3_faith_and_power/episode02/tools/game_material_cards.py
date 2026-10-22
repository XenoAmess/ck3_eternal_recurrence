"""Author episode02 mechanism cards with exact, unmodified CK3 game artwork.

This is a static plate author, not a capture or video-render entry point. Outputs
are review candidates; source rules do not become recorded gameplay evidence.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Sequence

from PIL import Image, ImageDraw, ImageFont


WIDTH = 2560
HEIGHT = 1440
OUTPUT_CAP = 8 * 1024 * 1024
BG = "#211813"
PANEL = "#32251d"
ACTIVE = "#49371f"
GOLD = "#d5b26b"
TEXT = "#f0e5cf"
MUTED = "#b9a98f"
LINE = "#69533c"


@dataclass(frozen=True)
class SourcePin:
    path: str
    bytes: int
    sha256: str


@dataclass(frozen=True)
class Material:
    key: str
    source: SourcePin
    crop: tuple[int, int, int, int] | None
    representation: str


@dataclass(frozen=True)
class Delivery:
    schema: str
    machine_id: str
    observed_at_utc: str
    source_build: str
    source_rules: tuple[SourcePin, ...]
    source_font: SourcePin
    author: SourcePin
    materials: tuple[Material, ...]
    outputs: tuple[SourcePin, ...]
    output_cap_bytes: int
    new_capture: bool
    video_updated: bool
    live_trait_coexistence_verified: bool


RULE_CONTRACTS = (
    ("common/traits/00_traits.txt", "93ad0316b733aa474d34841bd92fb3fc9336c111e9f06e7910178e74482185aa"),
    ("common/on_action/traits_on_actions.txt", "ea49e5a202918e7e794507b80f7726282dd07450ea07ab52ba7465b0f7ec7cda"),
    ("common/religion/tenet_types/00_tenet_types.txt", "d9e18a077d81f18f030d795ef45cb4aa5b7db246007043d5b0fe401baaf88abd"),
    ("common/scripted_effects/00_pilgrimage_effects.txt", "4374f9917e58a98e7b51ece5848d3540534f39fe60152f48342a79c3b2dc6f80"),
    ("common/activities/activity_types/pilgrimage.txt", "24153043485b035cb0477de7306649027cb68c039e4a9d903776eddd870d8b9f"),
)


def pin(path: Path) -> SourcePin:
    data = path.read_bytes()
    return SourcePin(str(path.resolve()), len(data), hashlib.sha256(data).hexdigest())


def load_materials(game_root: Path) -> tuple[Material, ...]:
    # Pilgrim uses the default base texture. Its GUI stars are a separate native
    # getter; numbered legacy DDS filenames do not prove the current tier icon.
    names = (
        ("pilgrim", "icons/traits/pilgrim.dds"),
        ("hajjaj", "icons/traits/hajjaj.dds"),
        ("scholar", "icons/traits/lifestyle_scholar.dds"),
        ("mystic", "icons/traits/mystic.dds"),
        ("gnosticism", "icons/faith_tenets/tenet_gnosticism.dds"),
        ("prowess", "icons/icon_prowess.dds"),
        ("temple", "icons/culture_tradition/4-items/temple.dds"),
        ("warrior_monk", "icons/culture_tradition/4-items/warrior_monk.dds"),
    )
    root = game_root / "gfx/interface"
    materials = [Material(key, pin(root / name), None, "original game texture") for key, name in names]
    # GUI learning UV 0.667..0.833 maps to the fifth 60px cell of the 360px atlas.
    materials.append(Material("learning", pin(root / "icons/icon_skills.dds"),
                              (240, 0, 300, 60), "learning cell from original six-skill atlas"))
    return tuple(materials)


class Plate:
    def __init__(self, title: str, subtitle: str, font: Path, materials: tuple[Material, ...]) -> None:
        self.image = Image.new("RGBA", (WIDTH, HEIGHT), BG)
        self.draw = ImageDraw.Draw(self.image)
        self.font = font
        self.materials = {material.key: material for material in materials}
        self.text((110, 46), "信仰引擎  /  朝圣在奖励什么？", 30, MUTED)
        self.text((2020, 46), "规则图解 · 原版素材", 30, GOLD)
        self.text((110, 118), title, 64, TEXT)
        self.text((110, 220), subtitle, 34, GOLD)
        self.draw.line((110, 285, 2450, 285), fill=LINE, width=2)

    def text(self, position: tuple[int, int], value: str, size: int = 38, color: str = TEXT) -> None:
        font = ImageFont.truetype(str(self.font), size)
        x, y = position
        for line in value.splitlines():
            if self.draw.textlength(line, font=font) + x > WIDTH - 90:
                raise ValueError(f"Text exceeds plate: {line}")
            self.draw.text((x, y), line, font=font, fill=color)
            y += round(size * 1.5)

    def box(self, bounds: tuple[int, int, int, int], active: bool = False) -> None:
        self.draw.rounded_rectangle(bounds, radius=22, fill=ACTIVE if active else PANEL,
                                    outline=GOLD if active else LINE, width=2)

    def icon(self, key: str, bounds: tuple[int, int, int, int]) -> None:
        material = self.materials[key]
        source = Path(material.source.path)
        if pin(source) != material.source:
            raise ValueError(f"Material changed after pinning: {source}")
        with Image.open(source) as raw:
            texture = raw.convert("RGBA")
        if material.crop is not None:
            texture = texture.crop(material.crop)
        x, y, width, height = bounds
        ratio = min(width / texture.width, height / texture.height)
        texture = texture.resize((max(1, round(texture.width * ratio)),
                                  max(1, round(texture.height * ratio))), Image.Resampling.LANCZOS)
        self.image.alpha_composite(texture, (x + (width - texture.width) // 2,
                                              y + (height - texture.height) // 2))

    def save(self, path: Path) -> SourcePin:
        self.image.convert("RGB").save(path, optimize=True)
        return pin(path)


def relationship(font: Path, materials: tuple[Material, ...]) -> Plate:
    p = Plate("朝觐者与朝圣者：两项特质可以共存", "完成朝觐后，再走普通朝圣路径；仍须满足地点、费用与冷却资格。", font, materials)
    p.box((110, 330, 820, 970))
    p.box((925, 330, 1635, 970))
    p.box((1740, 330, 2450, 970), active=True)
    p.icon("hajjaj", (320, 365, 280, 280))
    p.icon("pilgrim", (1135, 365, 280, 280))
    p.icon("hajjaj", (1810, 390, 240, 240))
    p.icon("pilgrim", (2135, 390, 240, 240))
    p.text((205, 670), "首次朝觐完成", 46)
    p.text((205, 755), "获得朝觐者／朝觐妇", 38)
    p.text((205, 830), "它没有普通朝圣者经验轨道。", 32, MUTED)
    p.text((1020, 670), "之后普通朝圣抵达圣地", 42)
    p.text((1020, 755), "另行获得朝圣者", 38)
    p.text((1020, 830), "不会因此删除原有朝觐者。", 32, MUTED)
    p.text((1850, 670), "同一人物，两项特质", 42)
    p.text((1820, 755), "不是转换，也不是升级替代", 36, GOLD)
    p.text((1820, 830), "已持朝圣者再朝觐，\n还能按表现增长朝圣者经验。", 32, MUTED)
    p.text((842, 585), "→", 60, GOLD)
    p.text((1655, 585), "→", 60, GOLD)
    p.text((110, 1030), "注意：跨宗教改信会触发朝圣者移除规则；不能拿改宗当成自然保留双特质的例子。", 34, MUTED)
    p.text((110, 1110), "图中是源码关系示意；三处均使用原版特质图标，未冒充本轮实机获得记录。", 28, MUTED)
    return p


def attributes(font: Path, materials: tuple[Material, ...]) -> Plate:
    p = Plate("朝圣者的额外属性，确实要看条件", "这些是指定来源的累计贡献；同一特质的经验等级与当前礼仪、文化分别判断。", font, materials)
    columns = ((110, "朝圣者", "经验不足 50", "0", "+2"),
               (910, "老道的朝圣者", "经验 50 至不足 100", "+1", "+5"),
               (1710, "高效的朝圣者", "经验 100", "+3", "+8"))
    for x, title, xp, learning, prowess in columns:
        p.box((x, 330, x + 740, 1005), active=x == 1710)
        p.icon("pilgrim", (x + 50, 360, 170, 170))
        p.text((x + 245, 385), title, 40)
        p.text((x + 245, 465), xp, 30, MUTED)
        p.icon("learning", (x + 48, 610, 88, 88))
        p.text((x + 160, 612), "学识", 40)
        p.text((x + 540, 595), learning, 64, GOLD)
        p.text((x + 55, 710), "当前礼仪提供对应朝圣奖励时", 30, MUTED)
        p.icon("prowess", (x + 48, 800, 88, 88))
        p.text((x + 160, 802), "勇武", 40)
        p.text((x + 540, 785), prowess, 64, GOLD)
        p.text((x + 55, 900), "拥有战斗祭司／僧兵文化传统时", 30, MUTED)
    p.icon("temple", (115, 1050, 78, 78))
    p.icon("warrior_monk", (205, 1050, 78, 78))
    p.text((320, 1063), "战斗祭司／僧兵：提供上述勇武条件。朝觐者满足同一条件时为勇武 +2。", 32, MUTED)
    p.text((110, 1155), "三档均展示原版朝圣者基础图标；等级用经验文字标明。文化图示取自原版图层。", 27, MUTED)
    return p


def gnostic(font: Path, materials: tuple[Material, ...]) -> Plate:
    p = Plate("诺斯替主义：获得朝圣者还能触发什么？", "检查的是个人信条，以及获得朝圣者这一刻；额外特质仍需满足自身资格。", font, materials)
    p.box((110, 330, 820, 1035))
    p.icon("gnosticism", (310, 370, 300, 430))
    p.text((225, 840), "诺斯替主义", 50)
    p.text((190, 935), "个人信条条件已满足", 34, MUTED)
    p.box((925, 330, 1635, 1035))
    p.icon("pilgrim", (1135, 390, 280, 280))
    p.text((1060, 725), "获得朝圣者", 48)
    p.text((1000, 830), "角色在世，且无三天触发冷却。", 32, MUTED)
    p.text((1000, 915), "升级经验不是再次获得特质。", 32, MUTED)
    p.box((1740, 330, 2450, 1035), active=True)
    p.icon("scholar", (1780, 380, 180, 180))
    p.text((1990, 397), "经文研习者", 42)
    p.text((1990, 475), "本体学识 +1", 34, GOLD)
    p.icon("mystic", (1780, 640, 180, 180))
    p.text((1990, 657), "神秘主义者", 42)
    p.text((1990, 735), "本体学识 +1", 34, GOLD)
    p.text((1800, 875), "未持有：尝试授予对应特质\n已持有：各请求 10 点基础经验", 31)
    p.text((842, 635), "＋", 56, GOLD)
    p.text((1655, 635), "→", 60, GOLD)
    p.text((110, 1090), "原先两者均无且授予成功时，额外两项特质本体合计学识 +2；各自资格与后续效果另核。", 32, MUTED)
    p.text((110, 1170), "学者采用原版默认图；基督教有另一图示。朝觐者没有这项获得触发标记。", 27, MUTED)
    return p


def main(arguments: Sequence[str]) -> int:
    if len(arguments) != 4:
        raise ValueError("Usage: game_material_cards.py GAME_ROOT NEW_OUTPUT_ROOT FONT MACHINE_ID")
    game_root, output, font = (Path(value).resolve() for value in arguments[:3])
    machine_id = arguments[3]
    if not machine_id or any(char.isspace() for char in machine_id):
        raise ValueError("A stable, explicit machine ID is required")
    rules = tuple(pin(game_root / relative) for relative, _ in RULE_CONTRACTS)
    for rule, (_, expected) in zip(rules, RULE_CONTRACTS, strict=True):
        if rule.sha256 != expected:
            raise ValueError(f"The 1.20.0.4 source contract changed: {rule.path}")
    materials = load_materials(game_root)
    source_font = pin(font)
    output.mkdir(parents=True, exist_ok=False)
    results: list[SourcePin] = []
    for name, author in (("01-hajj-pilgrim", relationship), ("02-pilgrim-attributes", attributes),
                         ("03-gnostic-trigger", gnostic)):
        results.append(author(font, materials).save(output / f"{name}.png"))
        if sum(item.bytes for item in results) > OUTPUT_CAP:
            raise ValueError("Static review plates exceeded their bounded output cap")
    delivery = Delivery("ck3-episode02-game-material-plates-v1", machine_id,
                        datetime.now(timezone.utc).isoformat(), "1.20.0.4", rules,
                        source_font, pin(Path(__file__)), materials, tuple(results),
                        OUTPUT_CAP, False, False, False)
    (output / "DELIVERY.actual.json").write_text(
        json.dumps(asdict(delivery), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "plates": len(results),
                      "png_bytes": sum(item.bytes for item in results)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
