"""Consume actual shared CLI restore evidence; never fabricate a startup actor."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from acceptance_contract import Frame, Object, array, field, integer, native_id, pin, require, text
from startup_actor_binding import _argument


def _exact(value: object, wanted: object, label: str) -> None:
    require(type(value) is type(wanted) and value == wanted, label + " differs or has a false-equal type")


def _pump(snapshot: object, *, pid: int) -> tuple[int, int]:
    heartbeat = field(field(snapshot, "diagnostics"), "last_heartbeat")
    _exact(field(heartbeat, "pid"), pid, "Native heartbeat PID")
    mailbox = field(heartbeat, "main_thread_query_mailbox_v1")
    observer = field(heartbeat, "snapshot_observer_12002")
    require(field(mailbox, "ready") is True and field(mailbox, "stamp_read_success") is True,
            "Actual main-thread query pump is not ready")
    epoch = integer(field(mailbox, "pump_epochs"), "native pump", 1, 2**64 - 1)
    owner = integer(field(mailbox, "owner_tid"), "native owner thread", 1, 2**32 - 1)
    _exact(field(mailbox, "owner_verified_pump_epochs"), epoch, "Verified pump epoch")
    _exact(field(mailbox, "current_tid"), owner, "Native current owner thread")
    require(field(observer, "read_in_progress") is False and
            integer(field(observer, "completed_ms"), "completed snapshot", 0, 2**64 - 1) >=
            integer(field(observer, "started_ms"), "started snapshot", 0, 2**64 - 1),
            "Original native snapshot is incomplete")
    return epoch, owner


@dataclass(frozen=True)
class SavedCampaignActorBinding:
    player_id: int
    pid: int
    generation_decimal: str
    date_raw: int
    pump_epoch_decimal: str
    owner_tid: int
    source_sha256: str
    inventory_sha256: str

    @classmethod
    def parse(cls, report: object, *, frozen: object, run_id: str, machine_id: str,
              manifest: object) -> SavedCampaignActorBinding:
        require(field(frozen, "run_id") == run_id and field(manifest, "machine_id") == machine_id,
                "Cold startup crossed the allocated run/machine")
        copied = field(report, "saved_campaign_input")
        require(field(copied, "status") == "IMMUTABLE_SAVE_COPIED_TO_FRESH_PRODUCT_ONLY_PROFILE" and
                field(copied, "profile_inventory_schema") == "ck3-saved-campaign-profile-inventory-v2" and
                field(copied, "source_game_state_claimed") is False and field(copied, "product_acceptance_proven") is False,
                "Actual formal v2 saved-input preparation missing")
        source = Path(_argument(frozen, "--saved-campaign-save")).resolve()
        require(source == Path(text(field(copied, "source_path"), "restore source")).resolve(),
                "Actual restore source differs from frozen argv")
        source_pin = pin(source)
        _exact(field(copied, "bytes"), source_pin["bytes"], "Copied source bytes")
        _exact(field(copied, "sha256"), source_pin["sha256"], "Copied source SHA")
        require(_argument(frozen, "--saved-campaign-save-bytes") == str(source_pin["bytes"]) and
                _argument(frozen, "--saved-campaign-save-sha256").lower() == source_pin["sha256"], "Frozen source identity differs")
        actor = native_id(field(copied, "actor_character_id"), "restored player")
        date_raw = integer(field(copied, "date_raw"), "restored date", 1, 2**31 - 1)
        require(_argument(frozen, "--saved-campaign-player-id") == str(actor) and
                _argument(frozen, "--saved-campaign-date-raw") == str(date_raw), "Frozen actor/date differs")
        state = Path(_argument(frozen, "--state-dir")).resolve()
        profile = state / "profile"
        target = profile / "save games/restored_campaign.ck3"
        require(Path(text(field(copied, "profile_path"), "prepared profile")).resolve() == profile and
                Path(text(field(copied, "copied_save_path"), "actual copied save")).resolve() == target and
                field(copied, "load_save_name") == "restored_campaign", "Restore used another profile/save name")
        target_pin = pin(target)
        require(target_pin["bytes"] == source_pin["bytes"] and target_pin["sha256"] == source_pin["sha256"],
                "Actual CLI restore copy differs from original source")
        inventory = Path(_argument(frozen, "--saved-campaign-product-inventory")).resolve()
        require(Path(text(field(copied, "product_inventory_path"), "inventory path")).resolve() == inventory and
                pin(inventory)["sha256"] == field(copied, "product_inventory_sha256"), "Restore inventory differs from frozen input")
        launch = field(report, "saved_campaign_launch")
        require(field(launch, "status") == "ACTUAL_SINGLE_CLI_RESTORE_LAUNCHED" and field(launch, "argv_admitted") is True and
                field(launch, "continue_last_save") is False and field(launch, "load_save_name") == "restored_campaign",
                "Actual single CLI restore launch is missing")
        command = [text(item, "actual launch argument") for item in array(field(launch, "command"), "actual launch argv")]
        require(command.count("-loadsave=restored_campaign") == 1 and "-continuelastsave" not in command,
                "Actual launch is not one explicit CLI restore")
        pid = integer(field(launch, "ck3_pid"), "actual launched PID", 1, 2**32 - 1)
        restore = field(report, "saved_campaign_restore")
        require(field(restore, "status") == "ACTUAL_SAVED_CAMPAIGN_CURRENT_CONTEXT_BOUND" and
                field(restore, "actual_current_actor_bound") is True and
                field(restore, "new_game_requested") is False and field(restore, "start_requested") is False and
                field(restore, "fixture_setup_requested") is False and field(restore, "product_acceptance_proven") is False and
                field(restore, "load_provider") == "runtime.launch(load_save_name):single_-loadsave",
                "Actual shared saved-campaign binding is unavailable")
        expected = field(restore, "expected")
        for name in ("source_path", "bytes", "sha256", "actor_character_id", "date_raw"):
            _exact(field(expected, name), field(copied, name), "Restore expected " + name)
        final = field(restore, "binding")
        require(field(final, "actual_current_actor_bound") is True and field(final, "saved_campaign_identity_proven") is True and
                field(final, "product_acceptance_proven") is False, "Shared restore binding lacks actual identity proof")
        generation = integer(field(final, "connection_generation"), "restore generation", 1, 2**64 - 1)
        observed = field(restore, "observed_process_binding")
        for value in (final, observed):
            _exact(field(value, "bridge_pid"), pid, "Restored process")
            _exact(field(value, "connection_generation"), generation, "Restored generation")
        epochs: list[int] = []
        bound_roots = 0
        for row in array(field(restore, "observations"), "actual restore observations"):
            if field(row, "frame") is None:
                continue
            snapshot = field(row, "snapshot")
            frame = Frame.parse(snapshot, run_id=run_id, machine_id=machine_id, manifest=manifest)
            integer(field(snapshot, "local_player_id"), "restored local player", 1, 2**32 - 1)
            text(field(snapshot, "snapshot_id"), "actual restored snapshot ID")
            require((frame.player_id, frame.pid, frame.generation_decimal, frame.date_raw) == (actor, pid, str(generation), date_raw),
                    "Restore observation crossed actual actor/process/date")
            epoch, owner = _pump(snapshot, pid=pid)
            epochs.append(epoch)
            if field(row, "binding") is None:
                continue
            root = field(row, "campaign_root")
            bound_roots += 1
            require(field(root, "campaign_root_context_ready") is True and field(root, "backend_id") == "native-headless" and
                    native_id(field(root, "player_character_id"), "actual campaign root player") == actor and
                    field(root, "player_character_alive") is True, "Actual restored campaign root is unavailable")
            for root_key, frame_key in (("queried_snapshot_id", "snapshot_id"), ("queried_revision", "revision"),
                                        ("queried_native_revision", "native_revision"), ("date_raw", "date_raw")):
                _exact(field(root, root_key), field(snapshot, frame_key), "Restored root/frame " + root_key)
            provenance = field(root, "provenance")
            game = field(manifest, "game")
            require(field(provenance, "game_version") == field(game, "version") and
                    text(field(provenance, "executable_sha256"), "root EXE").lower() == text(field(game, "exe_sha256"), "selected EXE").lower(),
                    "Restored native root belongs to another executable")
            _exact(field(row, "binding"), final, "Final restored observation binding")
            _exact(field(final, "actor_character_id"), actor, "Final restored player")
            _exact(field(final, "date_raw"), date_raw, "Final restored date")
            _exact(field(final, "pump_epoch"), epoch, "Final restored pump")
            _exact(field(final, "owner_tid"), owner, "Final restored owner thread")
            for name in ("snapshot_id", "revision", "native_revision", "local_player_id"):
                _exact(field(final, name), field(snapshot, name), "Final restored " + name)
        require(bound_roots == 1 and len(epochs) >= 2 and epochs[-1] > epochs[-2],
                "One actual root and two advancing native owner pump observations required")
        final_epoch = integer(field(final, "pump_epoch"), "final native pump", 1, 2**64 - 1)
        require(final_epoch == epochs[-1], "Final root binding must be the last actual pump observation")
        return cls(actor, pid, str(generation), date_raw, str(final_epoch),
                   integer(field(final, "owner_tid"), "final owner thread", 1, 2**32 - 1), source_pin["sha256"], pin(inventory)["sha256"])

    def validate_frame(self, frame: Frame) -> None:
        require((frame.player_id, frame.pid, frame.generation_decimal) == (self.player_id, self.pid, self.generation_decimal) and
                frame.date_raw >= self.date_raw, "Current native frame differs from its actual restored actor/process")

    def to_json(self) -> Object:
        return {"authority": "actual-shared-saved-campaign-restore-and-native-root", "runtime_actor_character_id": self.player_id,
                "pid": self.pid, "connection_generation": self.generation_decimal, "startup_date_raw": self.date_raw,
                "pump_epoch_decimal": self.pump_epoch_decimal, "owner_tid": self.owner_tid, "source_sha256": self.source_sha256,
                "inventory_sha256": self.inventory_sha256, "product_acceptance_proven": False}
