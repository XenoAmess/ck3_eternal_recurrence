"""Execute frozen production transport functions against a synthetic endpoint."""
import ast
import copy
import json
from pathlib import Path
import threading
import unittest
import uuid

from xar_autoplayer.bridge import native_driver as native
SOURCE = Path(native.__file__).resolve().parent / "current_first_heir_relationship_private_transport.py"
BRIDGE = SOURCE.parent
source = SOURCE.read_text("utf-8")
candidate = source

class QueryError(RuntimeError):
    pass


def load_functions(text):
    tree = ast.parse(text, filename=str(SOURCE))
    selected = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                or isinstance(node, ast.Assign)]
    guard_source = (BRIDGE / "marriage_matchmaking_private_transport.py").read_text(encoding="utf-8")
    guard = next(node for node in ast.parse(guard_source).body
                 if isinstance(node, ast.FunctionDef) and node.name == "_require_same_paused_frame")
    namespace = {"Path": Path, "uuid": uuid, "json": json,
                 "BridgeUnavailableError": QueryError, "UnsupportedStepError": QueryError,
                 "REPRODUCTIVE_INPUTS_LEAF": "absent_reproductive_fixture_leaf",
                 "DESCENDANTS_LEAF": "absent_descendants_fixture_leaf",
                 "private_native_provenance": lambda frame: {"fixture_provenance": True}}
    exec(compile(ast.Module(body=[guard, *selected], type_ignores=[]), str(SOURCE), "exec"), namespace)
    return namespace


BASELINE, CANDIDATE = load_functions(source), load_functions(candidate)


class FakeDriver:
    allow_private_current_first_heir_relationship_query = True

    def __init__(self, *, heir=50123):
        self.heir = heir
        self._request_sequence = 0
        self.snapshot = {"snapshot_id": "native:72", "revision": 73,
                         "native_revision": 72, "date_raw": 53421696,
                         "episode_run_id": "fixture-ordinary-episode",
                         "paused": True, "map_ready": True,
                         "played_character": {"character_id": 40526, "alive": True},
                         "diagnostics": {"bridge_pid": 6068, "connection_generation": 3}}
        self._driver_state_lock = threading.RLock()
        root = self.root(17)
        self._campaign_root_context_query = {
            "query_sequence": 17, "campaign_root_context": root["campaign_root_context"],
            "cache_binding": {"snapshot_id": "native:72", "revision": 73,
                              "native_revision": 72, "date_raw": 53421696,
                              "actor_character_id": 40526, "bridge_pid": 6068,
                              "connection_generation": 3}}
        self.root_calls, self.relation_calls = 0, []
        self.endpoint = self.state = self
        self.relation = {"status": "available", "bilateral_verified": True,
                         "unavailable_reason": None, "betrothed_character_id": None,
                         "primary_spouse_character_id": None, "spouse_character_ids": []}
        self.query_timeout = False

    def root(self, sequence):
        frame = self.snapshot
        partition = [{"primary": True, "title": {"title_id": 2204},
                      "first_heir_character_id": self.heir}]
        context = {"status": "available", "snapshot_revision": frame["native_revision"],
                   "date_raw": frame["date_raw"], "player_character_id": 40526,
                   "held_title_partition": partition}
        return {"status": "available", "query_sequence": sequence,
                "campaign_root_context": context, "held_title_partition": partition,
                "queried_snapshot_id": frame["snapshot_id"],
                "queried_revision": frame["revision"],
                "queried_native_revision": frame["native_revision"]}

    def take_internal_semantic_snapshot(self):
        return copy.deepcopy(self.snapshot)

    def _execute_campaign_root_context_v1_query(self, **kwargs):
        self.root_calls += 1
        return self.root(50)

    def send(self, request):
        self.relation_calls.append(request)

    def wait_for_command_result(self, request_id, timeout):
        if self.query_timeout:
            return None
        return {"ok": True, "result": {
            "step": "query-current-first-heir-relationship-v1-private", "accepted": True,
            "private_build": True, "read_only": True, "advertised": False,
            "native_revision": self.snapshot["native_revision"],
            "subject_source": "public_campaign_root_primary_first_heir",
            "heir_character_id": self.heir if self.heir is not None else -1,
            **copy.deepcopy(self.relation)}}


def query(driver, *, baseline=False, supplied=None):
    if baseline:
        driver._campaign_root_context_query = None
    namespace = BASELINE if baseline else CANDIDATE
    return namespace["query_current_first_heir_relationship_private_v1"](
        driver, expected_native_revision=driver.snapshot["native_revision"],
        **({"campaign_root_result": supplied} if supplied is not None else {}))


class FamilyRootReuseTests(unittest.TestCase):
    def test_actual_transport_path_removes_only_duplicate_root_call(self):
        old, new = FakeDriver(), FakeDriver()
        before, after = query(old, baseline=True), query(new)
        self.assertEqual((old.root_calls, new.root_calls), (1, 0))
        self.assertEqual((len(old.relation_calls), len(new.relation_calls)), (1, 1))
        self.assertEqual(after["root_query_sequence"], 17)
        self.assertEqual(before["root_query_sequence"], 50)
        for key in ("status", "heir_character_id", "bilateral_verified",
                    "betrothed_character_id", "primary_spouse_character_id", "spouse_character_ids"):
            self.assertEqual(before[key], after[key])

    def test_frame_owner_pid_and_generation_mismatch_fall_back(self):
        for key in ("snapshot_id", "revision", "native_revision", "date_raw",
                    "actor_character_id", "bridge_pid", "connection_generation"):
            driver = FakeDriver()
            driver._campaign_root_context_query["cache_binding"][key] = "wrong" if key == "snapshot_id" else 99
            with self.subTest(key=key):
                self.assertEqual(query(driver)["root_query_sequence"], 50)
                self.assertEqual(driver.root_calls, 1)
                self.assertEqual(len(driver.relation_calls), 1)

    def test_missing_failed_unknown_cache_falls_back(self):
        changes = [lambda d: setattr(d, "_campaign_root_context_query", None),
                   lambda d: d._campaign_root_context_query.pop("query_sequence"),
                   lambda d: d._campaign_root_context_query.update(query_sequence=0),
                   lambda d: d._campaign_root_context_query["campaign_root_context"].update(status="unavailable"),
                   lambda d: d._campaign_root_context_query["campaign_root_context"].update(player_character_id=99)]
        for index, change in enumerate(changes):
            driver = FakeDriver()
            change(driver)
            with self.subTest(index=index):
                self.assertEqual(query(driver)["root_query_sequence"], 50)
                self.assertEqual(driver.root_calls, 1)

    def test_explicit_same_frame_root_remains_first_choice(self):
        driver = FakeDriver()
        self.assertEqual(query(driver, supplied=driver.root(23))["root_query_sequence"], 23)
        self.assertEqual(driver.root_calls, 0)

    def test_current_spouse_or_betrothal_changes_are_still_queried(self):
        for relation in ({"primary_spouse_character_id": 700, "spouse_character_ids": [700]},
                         {"primary_spouse_character_id": None, "spouse_character_ids": []},
                         {"betrothed_character_id": 701}):
            driver = FakeDriver()
            driver.relation.update(relation)
            observed = query(driver)
            self.assertEqual(len(driver.relation_calls), 1)
            for key, value in relation.items():
                self.assertEqual(observed[key], value)

    def test_changed_heir_on_new_native_frame_uses_fresh_root(self):
        driver = FakeDriver()
        driver.snapshot.update(native_revision=74, revision=75, snapshot_id="native:74")
        driver.heir = 50124
        self.assertEqual(query(driver)["heir_character_id"], 50124)
        self.assertEqual(driver.root_calls, 1)

    def test_no_heir_still_executes_relation_and_remains_unavailable(self):
        driver = FakeDriver(heir=None)
        driver.relation.update(status="unavailable", bilateral_verified=False,
                               unavailable_reason="no_current_heir", spouse_character_ids=None)
        observed = query(driver)
        self.assertEqual(observed["status"], "unavailable")
        self.assertIsNone(observed["heir_character_id"])
        self.assertEqual(len(driver.relation_calls), 1)

    def test_relation_failure_still_raises_without_retry_or_noop(self):
        driver = FakeDriver()
        driver.query_timeout = True
        with self.assertRaises(QueryError):
            query(driver)
        self.assertEqual(len(driver.relation_calls), 1)
        self.assertEqual(driver.root_calls, 0)


# Appended to the portable family transport tests by the file-only producer.
from types import MethodType


def real_root_producer_driver(cross_frame=False):
    driver = FakeDriver(heir=98765)
    driver._campaign_root_context_query = None
    driver.primitive_queries = []
    fixture = json.loads(Path(__file__).with_name('family-root-cache-synthetic.json').read_bytes())
    if fixture.get('synthetic_contract_fixture') is not True:
        raise RuntimeError('Only explicitly synthetic test input is accepted')
    envelope = fixture['native_result']

    def primitive(step, **kwargs):
        if (step != native.QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP
                or kwargs.get('include_native_command_history') is not False):
            raise RuntimeError('Unexpected actual root-query dispatch contract')
        driver._request_sequence += 1
        request_id = kwargs.get('protocol_request_id')
        if not isinstance(request_id, str) or not request_id.startswith(
                f'step-{driver._request_sequence}-'):
            raise RuntimeError('Root request identity differs from primitive sequence')
        driver.primitive_queries.append((step, kwargs))
        return copy.deepcopy(envelope)

    driver._execute_primitive_step = primitive
    driver._execute_campaign_root_context_v1_query = MethodType(
        native.NativeHeadlessGameplayDriver._execute_campaign_root_context_v1_query, driver)
    if cross_frame:
        calls = [0]

        def take_current():
            calls[0] += 1
            result = copy.deepcopy(driver.snapshot)
            if calls[0] > 1:
                result.update(snapshot_id='native:74', revision=75, native_revision=74)
            return result

        driver.take_internal_semantic_snapshot = take_current
    return driver


class RealRootProducerChainTests(unittest.TestCase):
    def test_actual_public_driver_root_normalizer_cache_to_relationship_transport(self):
        driver = real_root_producer_driver()
        result = driver._execute_campaign_root_context_v1_query(expected_revision=73)
        self.assertEqual(result['query_sequence'], 29)
        self.assertEqual(driver._campaign_root_context_query['query_sequence'], 29)
        relation = query(driver)
        self.assertEqual(relation['root_query_sequence'], 29)
        self.assertEqual(relation['heir_character_id'], 98765)
        self.assertEqual(len(driver.primitive_queries), 1)
        self.assertEqual(driver._request_sequence, 1)
        self.assertRegex(driver.primitive_queries[0][1]['protocol_request_id'],
                         r'\Astep-1-[0-9a-f]{12}\Z')
        self.assertEqual(len(driver.relation_calls), 1)

    def test_actual_public_root_cross_frame_stops_before_cache_and_relationship(self):
        driver = real_root_producer_driver(cross_frame=True)
        with self.assertRaises(native.BridgeUnavailableError):
            driver._execute_campaign_root_context_v1_query(expected_revision=73)
        self.assertIsNone(driver._campaign_root_context_query)
        self.assertEqual(len(driver.primitive_queries), 1)
        self.assertEqual(driver._request_sequence, 1)
        self.assertRegex(driver.primitive_queries[0][1]['protocol_request_id'],
                         r'\Astep-1-[0-9a-f]{12}\Z')
        self.assertEqual(driver.relation_calls, [])

    def test_executed_functions_have_actual_imported_source_filenames(self):
        self.assertEqual(Path(native.NativeHeadlessGameplayDriver._execute_campaign_root_context_v1_query.__code__.co_filename).resolve(), Path(native.__file__).resolve())
        self.assertEqual(Path(CANDIDATE['query_current_first_heir_relationship_private_v1'].__code__.co_filename).resolve(), SOURCE)


if __name__ == '__main__':
    unittest.main(verbosity=2)
