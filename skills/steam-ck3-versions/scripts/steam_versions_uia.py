"""Windows Steam UIA backend. No coordinates, OCR, keystrokes or config writes."""
from __future__ import annotations

import os
from pathlib import Path
import re
import time

from steam_versions_core import APP_ID, VersionError, label_branch, observe_installation

BETAS_NAMES = {"Betas", "BETAS", "Game Versions & Betas", "游戏版本与测试", "遊戲版本與測試",
               "Game Versions and Betas", "游戏版本及测试版", "遊戲版本及測試版",
               "测试", "測試", "测试版", "測試版"}
OFFLINE_NAMES = {"offline mode", "离线模式", "離線模式"}


class ActionUnavailable(VersionError):
    pass


def dependencies():
    if os.name != "nt":
        raise VersionError("Steam UI Automation currently supports Windows only")
    try:
        import psutil
        from pywinauto import Desktop
    except ImportError as error:
        raise VersionError("UIA requires pywinauto and psutil in this interpreter") from error
    return psutil, Desktop


def local_processes():
    psutil, _ = dependencies()
    rows = []
    for process in psutil.process_iter(["pid", "name", "exe"]):
        if (process.info["name"] or "").casefold() in {"ck3.exe", "steam.exe", "steamwebhelper.exe"}:
            rows.append(process.info)
    return rows


def require_no_ck3():
    running = [row for row in local_processes() if (row["name"] or "").casefold() == "ck3.exe"]
    if running:
        raise VersionError(f"CK3 is running; do not change installed game inputs: {running!r}")


class SteamUI:
    def __init__(self, installation, *, guard, emit, selectors=None, timeout=20,
                 coordinate_mapper=None, receipt_dir=None, budget_check=None):
        _, Desktop = dependencies()
        self.desktop = Desktop(backend="uia")
        self.steam_dir = Path(installation["steam_dir"]).resolve()
        self.installation = installation
        self.guard, self.emit = guard, emit
        self.selectors = selectors or {}
        self.timeout = timeout
        self.root = None
        self.coordinate_mapper, self.receipt_dir = coordinate_mapper, receipt_dir
        self.budget_check = budget_check

    def mapped(self, node, reason):
        if not self.coordinate_mapper:
            raise VersionError("semantic control unsupported/no-effect; explicit --coordinate-mapper required for fallback")
        from steam_versions_mouse import mapped_click
        mapped_click(node, self.root, mapper=self.coordinate_mapper, receipt_dir=self.receipt_dir,
                     guard=self.guard, emit=self.emit, budget_check=self.budget_check, reason=reason)

    def windows(self):
        processes = {row["pid"] for row in local_processes()
                     if (row["name"] or "").casefold() in {"steam.exe", "steamwebhelper.exe"}
                     and row.get("exe") and self.steam_dir in Path(row["exe"]).resolve().parents}
        return [window for window in self.desktop.windows() if window.process_id() in processes]

    @staticmethod
    def nodes(root):
        nodes = [root, *root.descendants()]
        if len(nodes) > 5000:
            raise VersionError("Steam UIA tree exceeds bound; narrow the window selector")
        return nodes

    @staticmethod
    def info(node):
        element = node.element_info
        return {"name": element.name, "control_type": element.control_type,
                "automation_id": element.automation_id, "handle": element.handle,
                "process_id": element.process_id, "enabled": node.is_enabled(),
                "visible": node.is_visible()}

    def dump(self, label):
        rows = []
        for window in self.windows():
            for node in self.nodes(window):
                try:
                    row = self.info(node)
                    if len(row["name"]) > 4096:
                        row["name"] = row["name"][:4096] + "[truncated]"
                    rows.append(row)
                except Exception as error:
                    rows.append({"read_error": str(error)})
        self.emit("uia_tree", label=label, elements=rows)
        return rows

    def act(self, node, *, prefer_invoke=False):
        self.guard()
        if not node.is_enabled():
            raise VersionError("selected Steam UIA control is disabled")
        errors = []
        patterns = [("iface_selection_item", "Select"), ("iface_invoke", "Invoke")]
        if prefer_invoke:
            patterns.reverse()
        for pattern, method in patterns:
            try:
                interface = getattr(node, pattern)
            except Exception as error:
                errors.append(f"{pattern}: {error}")
                continue
            self.emit("uia_action_requested", control=self.info(node), pattern=pattern, method=method)
            try:
                getattr(interface, method)()
            except Exception as error:
                self.emit("uia_action_result_unknown", pattern=pattern, method=method, error=str(error))
                raise VersionError("UIA semantic action result unknown; inspect state before retrying") from error
            self.emit("uia_action_ack", control=self.info(node), pattern=pattern, method=method)
            return
        raise ActionUnavailable("UIA semantic action unavailable: " + "; ".join(errors))

    @staticmethod
    def same_route_actionable(nodes, *, prefer_invoke=False):
        """Steam can expose nested duplicate TabItems for one React route.

        Deduplicate only a nonempty identical AutomationId, not unrelated
        controls that happen to share translated text. Prefer an element
        exposing a real semantic pattern; never trial-invoke alternatives.
        """
        if len(nodes) == 1:
            return nodes[0]
        routes = {node.element_info.automation_id for node in nodes}
        if len(routes) != 1 or not next(iter(routes), ""):
            raise VersionError("multiple distinct Steam controls matched the requested route")
        patterns = ["iface_selection_item", "iface_invoke"]
        if prefer_invoke:
            patterns.reverse()
        for pattern in patterns:
            for node in nodes:
                try:
                    getattr(node, pattern)
                    return node
                except Exception:
                    continue
        raise VersionError("duplicate route controls expose no UIA semantic action")

    def betas_tab(self):
        nodes = [node for node in self.nodes(self.root)
                 if node.element_info.control_type == "TabItem"
                 and node.is_visible() and node.is_enabled()]
        suffix = self.selectors.get("betas_automation_id_suffix", f"/app/{APP_ID}/properties/betas")
        tabs = [node for node in nodes if node.element_info.automation_id.endswith(suffix)]
        if not tabs:
            aliases = set(self.selectors.get("betas_names", BETAS_NAMES))
            tabs = [node for node in nodes if node.window_text().strip() in aliases]
        if not tabs:
            self.dump("betas_tab_not_found")
            raise VersionError("Betas tab not found by CK3 route or localized name")
        try:
            chosen = self.same_route_actionable(tabs, prefer_invoke=True)
        except VersionError:
            self.dump("betas_tab_not_unique")
            raise
        self.emit("betas_tab_resolved", candidate_count=len(tabs), control=self.info(chosen),
                  route_suffix=suffix)
        return chosen

    def open_properties(self):
        self.guard()
        if not any((row["name"] or "").casefold() == "steam.exe" for row in local_processes()):
            raise VersionError("Steam must already be running; this tool never starts/restarts the client")
        expression = re.compile(self.selectors.get("root_title_regex", r"(?i)Crusader Kings III"))
        existing = [window for window in self.windows()
                    if expression.search(window.window_text()) and window.is_visible()]
        if len(existing) == 1:
            self.root = existing[0]
            content = self.betas_content()
            if content is not None:
                self.emit("betas_content_reused", control=self.info(content),
                          properties_control=self.info(self.root))
                return
        os.startfile(f"steam://gameproperties/{APP_ID}")
        self.emit("properties_requested", uri=f"steam://gameproperties/{APP_ID}")
        self.root = None
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            matching = [window for window in self.windows()
                        if expression.search(window.window_text()) and window.is_visible()]
            if len(matching) == 1:
                self.root = matching[0]
                break
            time.sleep(0.3)
        if self.root is None:
            self.dump("properties_not_unique")
            raise VersionError("CK3 properties window did not become uniquely identifiable")
        self.emit("properties_window_observed", control=self.info(self.root))
        tab = self.betas_tab()
        mapped_sent = False
        try:
            self.act(tab, prefer_invoke=True)
        except ActionUnavailable:
            self.mapped(tab, "Betas tab has no UIA semantic action")
            mapped_sent = True
        # Current Steam CEF returns Select ACK on a tab without navigating
        # its React route. Require the actual CK3 Betas content, not that ACK.
        content_suffix = f"/app/{APP_ID}/properties/betas_Content"
        deadline = time.monotonic() + self.timeout
        fallback_after = time.monotonic() + 1.5
        while time.monotonic() < deadline:
            content = [node for node in self.nodes(self.root)
                       if node.element_info.automation_id.endswith(content_suffix) and node.is_visible()]
            if content:
                self.emit("betas_content_observed", route_suffix=content_suffix, control=self.info(content[0]))
                return
            if (not mapped_sent and self.coordinate_mapper and time.monotonic() >= fallback_after):
                # The old General content is directly observable: this is a
                # confirmed no-effect navigation, not an unknown result.
                general = [node for node in self.nodes(self.root)
                           if node.element_info.automation_id.endswith(f"/app/{APP_ID}/properties/general_Content")
                           and node.is_visible()]
                if not general:
                    raise VersionError("navigation state unknown; refusing a second input")
                self.mapped(self.betas_tab(), "Select ACK left actual General content unchanged")
                mapped_sent = True
            time.sleep(0.2)
        self.dump("betas_navigation_ack_not_confirmed")
        raise VersionError("Betas navigation ACK did not produce CK3 Betas content; no branch action attempted")

    def betas_content(self):
        if self.root is None:
            return None
        suffix = f"/app/{APP_ID}/properties/betas_Content"
        matches = [node for node in self.nodes(self.root)
                   if node.element_info.automation_id.endswith(suffix) and node.is_visible()]
        if len(matches) > 1:
            raise VersionError("CK3 Betas content not unique")
        return matches[0] if matches else None

    def version_table(self):
        content = self.betas_content()
        if content is None:
            return None
        tables = [node for node in self.nodes(content)
                  if node.element_info.control_type == "Table" and node.is_visible()]
        if len(tables) > 1:
            raise VersionError("multiple tables in CK3 Betas content; no branch inferred")
        return tables[0] if tables else None

    @staticmethod
    def radio_selected(radio):
        try:
            return bool(radio.iface_selection_item.CurrentIsSelected)
        except Exception:
            pass
        try:
            # MSAA STATE_SYSTEM_CHECKED. This is an actual readback, never
            # inferred from whichever row the tool most recently invoked.
            return bool(int(radio.iface_legacy_iaccessible.CurrentState) & 0x10)
        except Exception as error:
            raise VersionError("version radio exposes no actual checked-state readback") from error

    def table_rows(self, table):
        rows = []
        for row in table.children():
            descendants = self.nodes(row)
            radios = [node for node in descendants if node.element_info.control_type == "RadioButton"]
            texts = [node.window_text().strip() for node in descendants
                     if node.element_info.control_type == "Text" and node.window_text().strip()]
            if not radios and not texts:
                continue
            if len(radios) != 1 or not texts:
                raise VersionError("CK3 version table row is not one radio plus an actual version label")
            if not radios[0].is_enabled():
                continue
            # New Steam exposes every row in this specific table's UIA tree,
            # including clipped/offscreen rows. Do not mix in global library
            # items, and do not mistake clipping for a removed beta branch.
            rows.append({"label": texts[0], "row_text": row.window_text(),
                         "description_texts": texts[1:], "radio": radios[0], "row": row,
                         "selected": self.radio_selected(radios[0])})
        labels = [row["label"] for row in rows]
        if len(labels) != len(set(labels)):
            raise VersionError("duplicate version labels in CK3 table; target would be ambiguous")
        if not rows:
            raise VersionError("CK3 version table had no available branch rows")
        return rows

    def list_table_branches(self, table, network):
        rows = self.table_rows(table)
        selected = [row["label"] for row in rows if row["selected"]]
        if len(selected) != 1:
            raise VersionError(f"CK3 version table checked-state not unique: {selected!r}")
        result = {"selected_label": selected[0], "labels": [row["label"] for row in rows],
                  "rows": [{key: value for key, value in row.items() if key not in {"radio", "row"}}
                           for row in rows], "layout": "version_table",
                  "source": "Steam CK3 Properties Game Versions Betas table UIA",
                  "network_observation": network,
                  "availability": "offline_cached_client_account_view" if network["state"] == "offline"
                  else "client_account_view_server_freshness_unverified",
                  "enumeration_scope": "all_radio_rows_in_actual_CK3_Betas_Table_UIA_tree"}
        self.emit("branch_list_observed", **result)
        return result

    def combo(self):
        identifier = self.selectors.get("combo_automation_id")
        nodes = [node for node in self.nodes(self.root) if node.is_visible() and node.is_enabled()]
        if identifier:
            matches = [node for node in nodes if node.element_info.automation_id == identifier]
        else:
            matches = [node for node in nodes if node.element_info.control_type == "ComboBox"]
        if len(matches) != 1:
            self.dump("branch_selector_not_unique")
            raise VersionError("branch selector not unique; UIA ComboBox or exact combo_automation_id required")
        return matches[0]

    def selected(self, combo):
        identifier = self.selectors.get("selected_automation_id")
        if identifier:
            nodes = [node for node in self.nodes(self.root) if node.element_info.automation_id == identifier]
            if len(nodes) != 1:
                raise VersionError("selected_automation_id did not identify one readback control")
            return nodes[0].window_text().strip()
        try:
            selected = combo.iface_selection.GetCurrentSelection()
            names = [selected.GetElement(index).CurrentName for index in range(selected.Length)]
            if len(names) == 1:
                return names[0].strip()
        except Exception:
            pass
        try:
            value = combo.iface_value.CurrentValue
            if value:
                return str(value).strip()
        except Exception:
            pass
        name = combo.window_text().strip()
        if name and name.casefold() not in {"beta participation", "测试参与", "参与测试"}:
            return name
        raise VersionError("Steam selector exposes no actual selected value")

    def expand(self, combo):
        self.guard()
        try:
            interface = combo.iface_expand_collapse
        except Exception:
            self.act(combo)
        else:
            self.emit("uia_action_requested", control=self.info(combo), pattern="ExpandCollapse", method="Expand")
            try:
                interface.Expand()
            except Exception as error:
                raise VersionError("dropdown expansion result unknown; inspect before retrying") from error
            self.emit("uia_action_ack", control=self.info(combo), pattern="ExpandCollapse", method="Expand")
        time.sleep(0.2)

    def option_nodes(self):
        options = []
        types = set(self.selectors.get("option_control_types", ["ListItem", "MenuItem", "DataItem"]))
        scopes = [self.root]
        popup_expression = self.selectors.get("popup_title_regex")
        if popup_expression:
            expression = re.compile(popup_expression)
            scopes.extend(window for window in self.windows()
                          if window is not self.root and window.is_visible()
                          and expression.fullmatch(window.window_text()))
        for window in scopes:
            for node in self.nodes(window):
                if (node.element_info.control_type in types and node.is_enabled()
                        and node.is_visible() and node.window_text().strip()):
                    options.append(node)
        return options

    def list_branches(self):
        network = self.network_observation()
        table = self.version_table()
        if table is not None:
            return self.list_table_branches(table, network)
        combo = self.combo()
        selected = self.selected(combo)
        self.expand(combo)
        nodes = self.option_nodes()
        labels = list(dict.fromkeys(node.window_text().strip() for node in nodes))
        if not labels or selected not in labels:
            self.dump("branch_options_missing")
            raise VersionError("could not enumerate branches with selected item; no inferred version list")
        try:
            combo.iface_expand_collapse.Collapse()
        except Exception:
            # The next operation can reuse the expanded list. Never Escape or
            # click outside without a semantic target.
            pass
        result = {"selected_label": selected, "labels": labels,
                  "source": "Steam CK3 Properties Betas UIA", "network_observation": network,
                  "availability": "offline_cached_client_account_view" if network["state"] == "offline"
                  else "client_account_view_server_freshness_unverified",
                  "enumeration_scope": "visible_items_in_CK3_properties_or_explicit_popup_selector",
                  "virtualized_offscreen_items_may_be_omitted": True}
        self.emit("branch_list_observed", **result)
        return result

    def choose(self, label):
        table = self.version_table()
        if table is not None:
            return self.choose_table(table, label)
        combo = self.combo()
        before = self.selected(combo)
        if before == label:
            self.emit("branch_already_selected", selected_label=label)
            return {"selected_label": label, "changed": False}
        self.expand(combo)
        options = [node for node in self.option_nodes() if node.window_text().strip() == label]
        if len(options) != 1:
            self.dump("exact_target_option_not_unique")
            raise VersionError("fresh target option is no longer unique; selection not attempted")
        self.act(options[0])
        deadline = time.monotonic() + self.timeout
        observed = None
        while time.monotonic() < deadline:
            observed = self.selected(self.combo())
            if observed == label:
                result = {"selected_label": observed, "changed": True,
                          "previous_label": before, "installed_verified": False}
                self.emit("branch_selection_readback", **result)
                return result
            time.sleep(0.3)
        raise VersionError(f"selection ACK not confirmed; actual={observed!r}; do not resubmit blindly")

    def choose_table(self, table, label):
        rows = self.table_rows(table)
        before = [row["label"] for row in rows if row["selected"]]
        targets = [row for row in rows if row["label"] == label]
        if len(before) != 1 or len(targets) != 1:
            raise VersionError("version table selected/target row not unique; no selection attempted")
        if before[0] == label:
            self.emit("branch_already_selected", selected_label=label, layout="version_table")
            return {"selected_label": label, "changed": False, "layout": "version_table"}
        manifest_before = observe_installation(self.installation)["branch"]
        mapped_sent = False
        try:
            self.act(targets[0]["radio"], prefer_invoke=True)
        except ActionUnavailable:
            target = self.visible_table_target(label)
            self.mapped(target["radio"], "version radio has no UIA semantic action")
            mapped_sent = True
        deadline = time.monotonic() + self.timeout
        fallback_after = time.monotonic() + 1.5
        observed = []
        while time.monotonic() < deadline:
            observed = [row["label"] for row in self.table_rows(self.version_table()) if row["selected"]]
            if observed == [label]:
                result = {"selected_label": label, "previous_label": before[0], "changed": True,
                          "layout": "version_table", "installed_verified": False}
                self.emit("branch_selection_readback", **result)
                return result
            if (not mapped_sent and self.coordinate_mapper and time.monotonic() >= fallback_after):
                branch_now = observe_installation(self.installation)["branch"]
                if observed != before or branch_now != manifest_before or branch_now == label_branch(label):
                    raise VersionError("radio ACK result remains ambiguous; inspect before any second input")
                target = self.visible_table_target(label)
                self.mapped(target["radio"], "radio ACK left actual checked row and manifest branch unchanged")
                mapped_sent = True
            time.sleep(0.3)
        raise VersionError(f"radio selection ACK not confirmed; actual={observed!r}; inspect before retrying")

    def visible_table_target(self, label):
        table = self.version_table()
        rows = self.table_rows(table)
        index = next((index for index, row in enumerate(rows) if row["label"] == label), None)
        if index is None:
            raise VersionError("target row disappeared before mapped selection")
        target = rows[index]
        def usable(radio):
            rectangle = radio.rectangle()
            return radio.is_visible() and rectangle.right > rectangle.left and rectangle.bottom > rectangle.top
        if usable(target["radio"]):
            return target
        for candidate in (target["radio"], target["row"]):
            try:
                interface = candidate.iface_scroll_item
            except Exception:
                continue
            self.guard()
            interface.ScrollIntoView()
            self.emit("version_row_scroll_ack", label=label, method="ScrollItem.ScrollIntoView")
            time.sleep(0.2)
            break
        else:
            candidate = table
            for _ in range(8):
                try:
                    interface = candidate.iface_scroll
                    scrollable = bool(interface.CurrentVerticallyScrollable)
                except Exception:
                    scrollable = False
                if scrollable:
                    percentage = index * 100 / max(1, len(rows) - 1)
                    self.guard()
                    interface.SetScrollPercent(-1, percentage)
                    self.emit("version_row_scroll_ack", label=label, method="Scroll.SetScrollPercent",
                              vertical_percentage=percentage)
                    time.sleep(0.2)
                    break
                if candidate is self.root:
                    break
                candidate = candidate.parent()
        targets = [row for row in self.table_rows(self.version_table()) if row["label"] == label]
        if len(targets) != 1 or not usable(targets[0]["radio"]):
            raise VersionError("target radio remains offscreen; scroll CK3's version table, then retry with a new receipt")
        return targets[0]

    def network_observation(self):
        labels = []
        for window in self.windows():
            for node in self.nodes(window):
                label = node.window_text().strip()
                if label.casefold() in OFFLINE_NAMES:
                    labels.append(label)
        return {"state": "offline" if labels else "unknown", "offline_labels": labels,
                "absence_of_offline_label_is_not_online_proof": True}
