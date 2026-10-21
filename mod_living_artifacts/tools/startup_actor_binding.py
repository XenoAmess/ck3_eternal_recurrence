"""Bind this scene's actor to the public, source-bound Robert Start evidence.

History IDs identify bookmark input. Runtime IDs are observed after that Start;
neither a historic run's ID nor a bare current native actor proves selection.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from acceptance_contract import Frame, Object, array, field, integer, json_value, mapping, native_id, pin, read, require, text


def _argument(frozen: object, key: str) -> str:
    argv = [text(item, "original host argv") for item in array(field(frozen, "argv"), "original host argv")]
    require(argv.count(key) == 1 and argv.index(key) + 1 < len(argv), "Exactly one allocated host argument required: " + key)
    return argv[argv.index(key) + 1]


def _hash_file(path: object, digest: object, label: str) -> Path:
    result = Path(text(path, label + " path")).resolve()
    require(pin(result)["sha256"] == text(digest, label + " SHA"), label + " bytes changed")
    return result


@dataclass(frozen=True)
class StartupActorBinding:
    player_id: int
    pid: int
    generation_decimal: str
    date_raw: int
    title_id: int
    policy_sha256: str
    preparation_sha256: str

    @classmethod
    def parse(cls, report: object, *, frozen: object, run_id: str, machine_id: str,
              manifest: object) -> StartupActorBinding:
        require(field(frozen, "run_id") == run_id, "Startup evidence crossed original run")
        policy_input = field(report, "frontend_fixture_start_policy_input")
        source = _hash_file(field(policy_input, "source_path"), field(policy_input, "sha256"), "allocated startup policy")
        require(source == Path(_argument(frozen, "--frontend-fixture-start-policy")).resolve(), "Startup policy differs from original host argv")
        snapshot = _hash_file(field(policy_input, "snapshot_path"), field(policy_input, "sha256"), "host startup policy snapshot")
        policy = field(policy_input, "policy")
        require(read(source) == read(snapshot) == json_value(policy), "Host policy payload differs from original pinned files")
        require(field(policy, "schema") == "ck3-frontend-fixture-start-policy-v1" and
                integer(field(policy, "schema_version"), "policy version", 1, 1) == 1, "Unsupported source-bound startup policy")
        preparation = field(policy, "preparation")
        _hash_file(field(preparation, "path"), field(preparation, "sha256"), "original profile preparation")
        post = field(policy, "post_start")
        require(field(post, "independent") is True and mapping(post, "Robert startup postcondition") == {"government_key": "feudal_government", "primary_title_tier_key": "duchy", "independent": True},
                "Robert source-derived postcondition differs")
        required = tuple(text(item, "required startup marker") for item in array(field(policy, "required_log_markers"), "required startup markers"))
        forbidden = tuple(text(item, "forbidden startup marker") for item in array(field(policy, "forbidden_log_markers"), "forbidden startup markers"))
        require(bool(required) and bool(forbidden) and not set(required) & set(forbidden), "Nonempty disjoint startup qualification markers required")

        start = field(report, "frontend_fixture_start_submission")
        require(field(start, "status") == "SINGLE_START_ACKNOWLEDGED_POST_STATE_PENDING" and field(start, "acknowledged") is True and
                field(start, "retry_allowed") is False, "Original single Start submission evidence missing")
        result = field(start, "result")
        require(field(result, "schema") == "ck3-frontend-fixture-robert-start-submission-v1" and
                integer(field(result, "schema_version"), "Start version", 1, 1) == 1 and field(result, "accepted") is True and
                field(result, "pre_start_identity_proven") is True and field(result, "fixture_target_identity_proven") is False,
                "Actual source-bound Robert selection missing")
        policy_binding = field(result, "policy_binding")
        require(field(policy_binding, "policy_sha256") == field(policy_input, "sha256") and
                field(policy_binding, "preparation_sha256") == field(preparation, "sha256"), "Start used another prepared input")
        candidate = field(result, "selected_candidate")
        expected = {"schema": "ck3-frontend-selected-1066-feudal-candidate-v1", "accepted": True, "status": "ready",
                    "route": "bookmarks", "selected_bookmark_group_key": "bm_group_1066", "selected_bookmark_key": "bm_1066_rags_to_riches",
                    "selected_character_name_key": "bookmark_rags_to_riches_duke_robert", "selected_character_government_key": "feudal_government",
                    "backend_id": "native-headless", "read_only": True}
        for key, wanted in expected.items():
            actual = field(candidate, key)
            require(type(actual) is type(wanted) and actual == wanted, "Actual selected frontend candidate differs: " + key)
        integer(field(candidate, "schema_version"), "candidate version", 1, 1)
        start_date = integer(field(candidate, "selected_bookmark_start_date_raw"), "actual selected bookmark date", 1)
        submitted = field(result, "binding")
        pid = integer(field(submitted, "bridge_pid"), "Start PID", 1, 2**32 - 1)
        generation = integer(field(submitted, "connection_generation"), "Start generation", 1)

        business = field(report, "frontend_fixture_business_context")
        require(field(business, "status") == "ACTUAL_FIXTURE_QUALIFIED_BUSINESS_CONTEXT_BOUND" and
                field(business, "actual_current_actor_bound") is True and field(business, "qualification_observed") is True and
                field(business, "fixture_target_identity_proven") is False and field(business, "product_acceptance_proven") is False and
                field(business, "start_resubmitted") is False, "Independent actual campaign-root startup proof missing")
        binding = field(business, "binding")
        actor = native_id(field(binding, "actor_character_id"), "actual startup actor")
        title = native_id(field(binding, "primary_title_id"), "actual primary title")
        require(integer(field(binding, "bridge_pid"), "bound PID", 1) == pid and
                integer(field(binding, "connection_generation"), "bound generation", 1) == generation and
                integer(field(binding, "date_raw"), "bound date", 1) == start_date and
                field(binding, "government_key") == "feudal_government" and field(binding, "primary_title_tier_key") == "duchy",
                "Campaign binding differs from original Start")
        observations = array(field(business, "observations"), "actual startup observations")
        require(len(observations) >= 2, "Two independent startup observations required")
        pump_epochs: list[int] = []
        for observed in observations[-2:]:
            snapshot_value = field(observed, "snapshot")
            frame = Frame.parse(snapshot_value, run_id=run_id, machine_id=machine_id, manifest=manifest)
            require((frame.player_id, frame.pid, frame.generation_decimal, frame.date_raw) == (actor, pid, str(generation), start_date),
                    "Startup native frame crossed selected process/actor/date")
            root = field(observed, "campaign_root")
            require(field(root, "campaign_root_context_ready") is True and field(root, "backend_id") == "native-headless" and
                    native_id(field(root, "player_character_id"), "root actor") == actor and field(root, "player_character_alive") is True and
                    field(field(root, "government"), "key") == "feudal_government" and field(root, "independent") is True and
                    field(root, "immediate_liege_character_id") is None and native_id(field(root, "top_liege_character_id"), "top liege") == actor and
                    native_id(field(field(root, "primary_title"), "title_id"), "root title") == title and
                    field(field(root, "primary_title"), "tier_key") == "duchy", "Independent native root differs from selected Robert postcondition")
            for root_key, frame_key in (("queried_snapshot_id", "snapshot_id"), ("queried_revision", "revision"), ("queried_native_revision", "native_revision"), ("date_raw", "date_raw")):
                actual = field(root, root_key)
                wanted = field(snapshot_value, frame_key)
                require(type(actual) is type(wanted) and actual == wanted, "Root observation is not from its paired native frame")
            provenance = field(root, "provenance")
            game = field(manifest, "game")
            require(field(provenance, "game_version") == field(game, "version") and
                    text(field(provenance, "executable_sha256"), "root EXE SHA").lower() == text(field(game, "exe_sha256"), "manifest EXE SHA").lower(),
                    "Independent root belongs to another executable")
            row_binding = field(observed, "binding")
            for key in ("actor_character_id", "bridge_pid", "connection_generation", "primary_title_id", "date_raw"):
                actual = field(row_binding, key)
                require(type(actual) is int and actual == field(binding, key), "Startup observation binding drifted")
            pump_epochs.append(integer(field(row_binding, "pump_epoch"), "actual main-thread pump epoch", 1))
            qualification = field(observed, "qualification")
            require(field(qualification, "schema") == "xar.ck3.engine-log-literals/v1" and field(qualification, "exists") is True and
                    field(qualification, "read_only") is True and field(qualification, "case_sensitive") is True and
                    field(qualification, "log_name") == "debug.log", "Actual startup log qualification unavailable")
            matches: dict[str, int] = {}
            for entry in array(field(qualification, "matches"), "startup log matches"):
                literal = text(field(entry, "literal"), "startup literal")
                require(literal not in matches, "Duplicate startup log qualification literal")
                matches[literal] = integer(field(entry, "line_count"), "actual matching log lines")
            require(set(matches) == set(required) | set(forbidden) and all(matches[item] > 0 for item in required) and
                    all(matches[item] == 0 for item in forbidden), "Actual startup qualification does not match original policy")
        require(pump_epochs[1] > pump_epochs[0] and integer(field(binding, "pump_epoch"), "final pump", 1) == pump_epochs[1],
                "Startup root must be read on two advancing main-thread pump epochs")
        return cls(actor, pid, str(generation), start_date, title, text(field(policy_input, "sha256"), "policy SHA"),
                   text(field(preparation, "sha256"), "preparation SHA"))

    def validate_frame(self, frame: Frame) -> None:
        require((frame.player_id, frame.pid, frame.generation_decimal) == (self.player_id, self.pid, self.generation_decimal) and
                frame.date_raw >= self.date_raw, "Current native scene differs from its source-bound startup actor/process")

    def to_json(self) -> Object:
        return {"authority": "original-source-bound-frontend-start-and-two-native-root-observations", "runtime_actor_character_id": self.player_id,
                "pid": self.pid, "connection_generation": self.generation_decimal, "startup_date_raw": self.date_raw,
                "primary_title_id": self.title_id, "policy_sha256": self.policy_sha256, "preparation_sha256": self.preparation_sha256,
                "bookmark_history_id": "1128", "fixture_target_identity_proven": False, "product_acceptance_proven": False}
