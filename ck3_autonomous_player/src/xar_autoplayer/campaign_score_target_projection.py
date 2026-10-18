"""Small, explicitly selected save records; preserves repeated/anonymous values.

Used when a scalar whitelist cannot establish absence or a paired variable.
Never retains a complete world AST. All filters and discarded paths are audited.
"""
from collections import Counter

from .campaign_score_save_reader import SaveProjection, ROOT_CHARACTER, atom


class TargetProjection(SaveProjection):
    def __init__(self, *, characters, provinces, dynasty, war_characters):
        super().__init__(characters)
        self.province_ids = {str(x) for x in provinces}
        self.dynasty_id = str(dynasty)
        self.war_characters = {str(x) for x in war_characters}
        self.records = {}
        self.excluded_paths = Counter()
        self.dropped_records = Counter()
        self.total_selected_bytes = 0
        self.matched_record_paths = []

    def record_kind(self, path):
        if len(path) == 2 and path[0] in ROOT_CHARACTER and path[1].isdigit():
            if int(path[1]) in self.wanted:
                return "character", int(path[1]), len(path)
        if len(path) == 2 and path[0] == "provinces" and path[1] in self.province_ids:
            return "province", int(path[1]), len(path)
        candidate = super().record_kind(path)
        if candidate and candidate[0] == "dynasty" and str(candidate[1]) == self.dynasty_id:
            return candidate
        if len(path) == 3 and path[:2] in (["wars", "active_wars"], ["sieges", "sieges"]) and path[-1].isdigit():
            return ("war" if path[0] == "wars" else "siege"), int(path[-1]), len(path)
        if len(path) == 2 and path[0] in {"wars", "active_wars"} and path[-1].isdigit():
            return "war", int(path[-1]), len(path)
        return None

    def _append(self, relative, value, anonymous=False):
        kind, identity, _, fields = self.active
        # Histories cannot change current occupancy, wallet, legacies or participants.
        ignored = {"history", "character_history", "title_history", "chronicle", "battle_history",
                   "battles", "genetic_data", "dna", "portrait_info", "secrets", "memories"}
        if any(x in ignored for x in relative):
            self.excluded_paths[kind + "." + next(x for x in relative if x in ignored)] += 1
            return
        self.selected_scalar_count += 1
        if len(fields) >= 12000 or len(value) > 16384:
            raise ValueError(f"target record cap exceeded: {kind}/{identity}")
        self.total_selected_bytes += sum(len(x) for x in relative) + len(value) + 32
        if self.total_selected_bytes > 3 * 1024 * 1024:
            raise ValueError("target projection aggregate cap exceeded")
        fields[len(fields)] = {"path": relative, "value": atom(value), "anonymous": anonymous}

    def scalar(self, key, value):
        if key.startswith("0x"):
            self.unknown_key_fields += 1
        if self.active is not None:
            self._append(self.path[self.active[2]:] + [key], value)
        else:
            self.skipped_scalar_count += 1
            if key in {"date", "version", "meta_date"} and len(self.path) <= 1:
                self.metadata[".".join(self.path + [key])] = atom(value)

    def anonymous(self, token):
        if self.active is not None:
            self._append(self.path[self.active[2]:], token, True)

    def player_wars_presence(self):
        # This collector stores typed path rows, not the scalar adapter's flat markers.
        self._append(["landed_data", "wars", "@present"], "true")

    def finish(self):
        kind, identity, depth, fields = self.active
        self.root_counts[kind] += 1
        rows = list(fields.values())
        self.matched_record_paths.append(list(self.path[:depth]))
        if len(self.matched_record_paths) > 2048 or len(self.records) >= 512:
            raise ValueError("target record/path count cap exceeded")
        keep = True
        if kind == "war":
            keep = any(row["value"] in self.war_characters and any(
                name in {"attacker", "defender", "character", "claimant", "participant"}
                for name in row["path"]) for row in rows)
        elif kind == "siege":
            keep = any(row["path"] == ["province"] and row["value"] in self.province_ids for row in rows)
        if keep:
            key = kind + ":" + str(identity)
            if key in self.records:
                raise ValueError(f"duplicate target entity {key}")
            self.records[key] = {"path": list(self.path[:depth]), "fields": rows}
        else:
            self.dropped_records[kind] += 1
        self.active = None

    def summary(self):
        return {"metadata": self.metadata, "record_counts": dict(self.root_counts),
                "melted_bytes_streamed_not_saved": self.text_bytes, "token_count": self.token_count,
                "unknown_key_fields": self.unknown_key_fields,
                "selected_scalar_count": self.selected_scalar_count,
                "skipped_scalar_count": self.skipped_scalar_count,
                "excluded_paths": dict(self.excluded_paths), "dropped_records": dict(self.dropped_records),
                "matched_record_paths": self.matched_record_paths,
                "war_scan_supported": bool(self.war_containers) and not self.war_layout_unknown,
                "selection": {"characters": sorted(self.wanted), "provinces": sorted(self.province_ids),
                              "dynasty": self.dynasty_id, "war_characters": sorted(self.war_characters)},
                "records": self.records}


def enrich_metrics(metrics, detail, target, dynasty_target, *, actor, source_ref, dynasty_source_ref=None):
    """Use complete selected records; never infer absence from a failed selector."""
    from decimal import Decimal as D
    from .campaign_score_save_reader import observation
    records = target["records"]
    audit = {"occupation_complete": False, "own_rebellion_complete": False,
             "legacy_complete": False, "raw_finance_fields": {}, "unresolved": []}
    complete = target.get("unknown_key_fields") == 0
    # Occupant omission is checked on every completed holding in each retained county.
    # A positive occupant requires hostility attribution; omission proves no occupation.
    absent = complete
    for county in detail["realm_counties"]:
        for holding in county["holding_sources"]:
            if holding["holding_type"] in {None, "none"}:
                continue
            record = records.get("province:" + str(holding["province_id"]))
            if record is None or any(row["path"] == ["occupant"] for row in record["fields"]):
                absent = False
    if absent and metrics["Q_realm"]["availability"] in {"bounded", "observed"}:
        value = metrics["Q_realm"].get("upper", metrics["Q_realm"].get("value"))
        metrics["Q_realm"] = observation("Q_realm", value, source_ref,
            "all completed realm baronies: complete province records omit occupant; q/control unchanged")
        audit["occupation_complete"] = True
    # A revolt inside this player's realm must make this player the CB defender.
    # A player's rebellion against their own liege belongs to the liege's governance set.
    wars = [row for key, row in records.items() if key.startswith("war:")]
    own_defence = any(row["path"] == ["casus_belli", "defender"] and row["value"] == str(actor)
                      for war in wars for row in war["fields"])
    if complete and target.get("war_scan_supported") is True and not own_defence:
        metrics["rebel_share"] = observation("rebel_share", 0, source_ref,
            "complete active_wars scan: no CB-defender player; own anti-liege war excluded")
        audit["own_rebellion_complete"] = True
    dyn = dynasty_target.get("records", {}).get("dynasty:" + str(detail["dynasty_anchor_id"]))
    if dyn is not None and dynasty_target.get("unknown_key_fields") == 0:
        perks = {row["value"] for row in dyn["fields"] if row["path"] == ["perk"] and row["anonymous"]}
        metrics["legacy_ranks"] = observation("legacy_ranks", len(perks), dynasty_source_ref or source_ref,
                                              ".".join(dyn["path"]) + ".perk (deduplicated keys)")
        audit["legacy_complete"] = True
        audit["legacy_keys"] = sorted(perks)
        audit["dynasty_raw_resources"] = [row for row in dyn["fields"] if row["path"][0] == "prestige"]
    char = records.get("character:" + str(actor))
    if char:
        audit["raw_finance_fields"] = {".".join(row["path"]): row["value"] for row in char["fields"]
            if row["path"] in [["alive_data", "income"], ["landed_data", "balance"], ["alive_data", "gold", "value"]]}
        audit["raw_military_fields"] = {".".join(row["path"]): row["value"] for row in char["fields"]
            if len(row["path"]) == 2 and row["path"][0] == "landed_data" and row["path"][1] in
            {"strength", "current_strength", "strength_without_hires", "power", "max_power", "levy"}}
        audit["raw_succession_candidates"] = [row["value"] for row in char["fields"]
            if row["path"] == ["landed_data", "succession"] and row["anonymous"]]
    detail["occupation_semantics_complete"] = audit["occupation_complete"]
    detail["rebel_war_semantics_complete"] = audit["own_rebellion_complete"]
    detail["targeted_adaptation"] = audit
    return metrics, detail
