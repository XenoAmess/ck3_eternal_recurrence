"""Explicit debugger class replacement candidate; importing changes no live object.

The three repair methods are exact copies of the production candidate.
ROOT must separately select the original service object and replace its class.
No SDK call, process attach, injection, reconnection, or receipt write occurs on import.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

class RetainedLateAttachMethods:
    def _verify_retained_attach(self) -> dict:
        """Explicitly verify the original connected driver after one loading timeout."""
        original = self._attach_result
        loading_reason = ("BridgeUnavailableError: native game state is not available yet; "
                          "CK3 may still be loading or may not have entered a map")
        if (original.get("status") != "RED" or original.get("reason") != loading_reason
                or self.driver is None or self.profile["game_version"] != "1.20.0.3"):
            return original
        injected = original.get("injector")
        if (not isinstance(injected, dict) or type(injected.get("returncode")) is not int
                or injected["returncode"] != 0 or injected.get("complete_process_tree_proven") is not True):
            return original

        original_path = Path(original["receipt_path"])
        original_raw = original_path.read_bytes()
        original_ref = {"path": str(original_path), "bytes": len(original_raw),
                        "sha256": hashlib.sha256(original_raw).hexdigest()}
        facts = {"original_attach_receipt": original_ref, "injector": injected,
                 "attachment_verification": "late_retained_connection",
                 "reinjected": False, "reconnected": False,
                 "uses_ocr": False, "uses_desktop_input": False}
        try:
            directory = Path(self.profile["evidence_directory"]) / self.session_id
            if (original_path.parent.resolve() != directory.resolve()
                    or not original_path.name.endswith("-attach.json")
                    or json.loads(original_raw) != original
                    or original.get("schema") != "ck3.native-profile-receipt.v1"
                    or original.get("session_id") != self.session_id
                    or original.get("pipe_name") != self.pipe_name
                    or original.get("profile_sha256") != self.profile["profile_sha256"]):
                raise RuntimeError("original failed attach receipt does not bind this retained service")
            target = self.profile["guard"]["target"]
            claim = json.loads((Path(self.profile["evidence_directory"]) / "attach-claim.json").read_bytes())
            if claim != {"session_id": self.session_id, "profile_sha256": self.profile["profile_sha256"],
                         "pipe_name": self.pipe_name, "target": target}:
                raise RuntimeError("original attach claim does not bind this retained service")
            argv = injected.get("argv")
            if (not isinstance(argv, list) or len(argv) != 5
                    or Path(argv[0]).resolve() != Path(self.profile["injector"]["path"]).resolve()
                    or argv[1:4] != ["--pipe", self.pipe_name, str(target["pid"])]
                    or Path(argv[4]).resolve() != Path(self.profile["dll"]["path"]).resolve()):
                raise RuntimeError("original successful injector does not bind this pipe and target")
            for name in ("dll", "injector"):
                row = self.profile[name]
                if hashlib.sha256(Path(row["path"]).read_bytes()).hexdigest() != row["sha256"].lower():
                    raise RuntimeError(f"frozen {name} artifact SHA-256 changed")

            facts["observation_before"] = self.guard()
            facts["native_clock_before"] = self.backend.read_clock(self.profile)
            self.guard()
            before = facts["native_clock_before"]
            if (type(before.get("date_raw")) is not int or before["date_raw"] <= 0
                    or before.get("paused") is not True or type(before.get("speed")) is not int):
                raise RuntimeError("late attach requires a known paused native clock")
            self._validate_retained_attach_connection()
            snapshot = self._snapshot()
            diagnostics = snapshot["diagnostics"]
            if (diagnostics.get("connected") is not True or diagnostics.get("pipe_name") != self.pipe_name
                    or type(diagnostics.get("connection_generation")) is not int
                    or diagnostics["connection_generation"] != 1
                    or diagnostics["hello"].get("connection_generation") != 1
                    or type(diagnostics["hello"].get("connection_generation")) is not int
                    or diagnostics["hello"].get("game_adapter_id") != "ck3-1.20.0.3-msvc-x64"
                    or snapshot.get("map_ready") is not True or snapshot.get("paused") is not True
                    or any(snapshot.get(key) != before[key] for key in ("date_raw", "paused", "speed"))):
                raise RuntimeError("late attach snapshot does not match the retained .3 connection and paused clock")
            facts["snapshot"] = snapshot
            facts["native_clock_after"] = self.backend.read_clock(self.profile)
            facts["observation_after"] = self.guard()
            after = facts["native_clock_after"]
            if (type(after.get("date_raw")) is not int or type(after.get("speed")) is not int
                    or after.get("paused") is not True
                    or any(after.get(key) != before[key] for key in ("date_raw", "paused", "speed"))):
                raise RuntimeError("native clock changed during explicit late attach verification")
            self._validate_retained_attach_connection()
            if original_path.read_bytes() != original_raw:
                raise RuntimeError("original failed attach receipt changed during late verification")
            facts["connection_generation"] = 1
            result = self._retained_attach_receipt({"status": "attached_snapshot_verified", **facts})
            self._attach_result = result
            return result
        except Exception as error:
            # Keep the initial RED cached. Only another explicit attach call can
            # request another observation; no injector or reconnect is replayed.
            return self._retained_attach_receipt({"status": "RED",
                "reason": f"{type(error).__name__}: {error}", **facts})

    def _validate_retained_attach_connection(self) -> None:
        driver = self.driver
        if (driver.pipe_name != self.pipe_name or driver.state.pipe_name != self.pipe_name
                or driver.endpoint.pipe_name != self.pipe_name):
            raise RuntimeError("late attach no longer owns the original driver pipe")
        diagnostics = driver.state.diagnostics()
        if (diagnostics.get("connected") is not True
                or diagnostics.get("pipe_name") != self.pipe_name
                or type(diagnostics.get("connection_generation")) is not int
                or diagnostics["connection_generation"] != 1
                or diagnostics.get("bridge_pid") != self.profile["guard"]["target"]["pid"]):
            raise RuntimeError("late attach requires the original live generation-one connection")

    def _retained_attach_receipt(self, value: dict) -> dict:
        path = (Path(self.profile["evidence_directory"]) / self.session_id
                / f"{self._sequence + 1:04d}-attach-late-verification.json")
        if path.exists():
            raise RuntimeError("late attach receipt already exists; immutable evidence cannot be overwritten")
        return self._receipt("attach-late-verification", value)

    def attach(self) -> dict:
        with self._lock:
            if self._attach_result is not None:
                return self._verify_retained_attach()
            return super().attach()

def replacement_class(original_class):
    """Construct a subclass only; the caller performs any explicit class replacement."""
    if original_class.__name__ != 'NativeProfileService':
        raise TypeError('candidate requires the original NativeProfileService class')
    return type('NativeProfileServiceLateAttachCandidate',
                (RetainedLateAttachMethods, original_class), {'__module__': __name__})
