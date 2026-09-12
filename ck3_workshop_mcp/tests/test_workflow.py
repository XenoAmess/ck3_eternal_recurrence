from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from ck3_workshop_mcp.engine import WorkshopService
from ck3_workshop_mcp.errors import GateError, ProviderResultUnknownError, UnsafeRetryError
from ck3_workshop_mcp.models import (
    EulaState,
    GameSessionState,
    OperationKind,
    PublicationPlan,
    SteamMode,
    WorkflowState,
    sha256_file,
)
from ck3_workshop_mcp.providers import FakeWorkshopProvider, PdxLauncherReadOnlyProvider
from ck3_workshop_mcp.wal import OperationStore


class WorkflowFixture:
    def __init__(
        self,
        root: Path,
        operation_id: str,
        operation: OperationKind,
        *,
        target_item_id: str | None = None,
        outer_item_id: str | None = None,
    ) -> None:
        staging = root / "release" / operation_id
        staging.mkdir(parents=True)
        descriptor = 'version="1.0.0"\nname="Fixture"\nsupported_version="1.19.0.6"\n'
        (staging / "descriptor.mod").write_text(descriptor, encoding="utf-8")
        (staging / "content.txt").write_text("fixture\n", encoding="utf-8")
        preview = staging / "thumbnail.png"
        preview.write_bytes(b"fake-png")
        description = root / f"{operation_id}.bbcode"
        description.write_text("[h1]Fixture[/h1]\n", encoding="utf-8")
        outer = root / f"{operation_id}.mod"
        outer_text = descriptor + f'path="{staging.as_posix()}"\n'
        if outer_item_id is not None:
            outer_text += f'remote_file_id="{outer_item_id}"\n'
        outer.write_text(outer_text, encoding="utf-8")

        entries = []
        for path in sorted(item for item in staging.rglob("*") if item.is_file()):
            entries.append(
                {
                    "path": path.relative_to(staging).as_posix(),
                    "size": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
        manifest = root / f"{operation_id}.manifest.json"
        manifest.write_text(
            json.dumps(
                {
                    "format_version": 1,
                    "product_id": "fixture",
                    "workshop_item_id": None,
                    "files": entries,
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        self.plan = PublicationPlan(
            operation_id=operation_id,
            product_key="fixture",
            operation=operation,
            consumer_app_id=1_158_310,
            staging_dir=str(staging),
            staging_manifest=str(manifest),
            staging_manifest_sha256=sha256_file(manifest),
            outer_descriptor=str(outer),
            title="Fixture",
            description_path=str(description),
            description_sha256=sha256_file(description),
            preview_path=str(preview),
            preview_sha256=sha256_file(preview),
            target_item_id=target_item_id,
            forbidden_item_ids=("3596580780",),
            offline_after=True,
        )


class WorkshopWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def service(
        self, fixture: WorkflowFixture, provider: FakeWorkshopProvider
    ) -> WorkshopService:
        service = WorkshopService(OperationStore(self.root / "state"), provider)
        service.create_plan(fixture.plan.to_dict())
        return service

    def authorize(self, service: WorkshopService, fixture: WorkflowFixture) -> str:
        service.begin_online_window(fixture.plan.operation_id)
        service.preflight(fixture.plan.operation_id)
        response = service.issue_submit_token(
            fixture.plan.operation_id, fixture.plan.sha256
        )
        return str(response["submit_token"])

    def test_create_crash_never_calls_create_twice(self) -> None:
        fixture = WorkflowFixture(self.root, "create-crash", OperationKind.CREATE)
        provider = FakeWorkshopProvider(crash_on_create=True)
        service = self.service(fixture, provider)
        token = self.authorize(service, fixture)

        with self.assertRaises(ProviderResultUnknownError):
            service.submit(fixture.plan.operation_id, fixture.plan.sha256, token)
        self.assertEqual(provider.create_calls, 1)
        self.assertEqual(
            service.operation(fixture.plan.operation_id)["state"],
            WorkflowState.AMBIGUOUS_CREATE.value,
        )
        self.assertEqual(provider.steam_mode, SteamMode.OFFLINE)

        with self.assertRaises(UnsafeRetryError):
            service.submit(fixture.plan.operation_id, fixture.plan.sha256, token)
        self.assertEqual(provider.create_calls, 1)

    def test_unknown_submit_result_is_never_retried(self) -> None:
        item_id = "9000000123"
        fixture = WorkflowFixture(
            self.root,
            "update-unknown",
            OperationKind.UPDATE,
            target_item_id=item_id,
            outer_item_id=item_id,
        )
        provider = FakeWorkshopProvider(
            owned_item_ids={item_id}, unknown_on_submit=True
        )
        service = self.service(fixture, provider)
        token = self.authorize(service, fixture)

        with self.assertRaises(ProviderResultUnknownError):
            service.submit(fixture.plan.operation_id, fixture.plan.sha256, token)
        self.assertEqual(provider.submit_calls, 1)
        self.assertEqual(
            service.operation(fixture.plan.operation_id)["state"],
            WorkflowState.SUBMIT_RESULT_UNKNOWN.value,
        )
        with self.assertRaises(UnsafeRetryError):
            service.submit(fixture.plan.operation_id, fixture.plan.sha256, token)
        self.assertEqual(provider.submit_calls, 1)

    def test_eula_needs_action_blocks_and_restores_offline(self) -> None:
        fixture = WorkflowFixture(self.root, "eula-block", OperationKind.CREATE)
        provider = FakeWorkshopProvider(eula=EulaState.NEEDS_ACTION)
        service = self.service(fixture, provider)
        service.begin_online_window(fixture.plan.operation_id)

        with self.assertRaises(GateError) as raised:
            service.preflight(fixture.plan.operation_id)
        self.assertEqual(raised.exception.gate_code, "BLOCKED_WORKSHOP_EULA")
        current = service.operation(fixture.plan.operation_id)
        self.assertEqual(current["state"], WorkflowState.BLOCKED_WORKSHOP_EULA.value)
        self.assertTrue(current["offline_restored"])
        self.assertEqual(provider.steam_mode, SteamMode.OFFLINE)
        self.assertEqual(provider.create_calls, 0)

    def test_successful_update_restores_offline_and_completes(self) -> None:
        item_id = "9000000456"
        fixture = WorkflowFixture(
            self.root,
            "update-success",
            OperationKind.UPDATE,
            target_item_id=item_id,
            outer_item_id=item_id,
        )
        provider = FakeWorkshopProvider(owned_item_ids={item_id})
        service = self.service(fixture, provider)
        token = self.authorize(service, fixture)
        current = service.submit(
            fixture.plan.operation_id, fixture.plan.sha256, token
        )

        self.assertEqual(current["state"], WorkflowState.COMPLETE.value)
        self.assertTrue(current["offline_restored"])
        self.assertEqual(provider.restore_offline_calls, 1)
        self.assertEqual(provider.steam_mode, SteamMode.OFFLINE)

    def test_durable_online_obligation_is_recovered_after_restart(self) -> None:
        fixture = WorkflowFixture(self.root, "offline-recovery", OperationKind.CREATE)
        provider = FakeWorkshopProvider()
        service = self.service(fixture, provider)
        service.begin_online_window(fixture.plan.operation_id)
        self.assertEqual(provider.steam_mode, SteamMode.ONLINE)

        restarted = WorkshopService(service.store, provider)
        response = restarted.recover_offline_obligations()
        self.assertEqual(provider.steam_mode, SteamMode.OFFLINE)
        self.assertTrue(
            restarted.operation(fixture.plan.operation_id)["offline_restored"]
        )
        self.assertEqual(
            response["operations"][0]["operation_id"], fixture.plan.operation_id
        )

    def test_in_game_account_blocks_without_forcing_online(self) -> None:
        fixture = WorkflowFixture(self.root, "account-in-game", OperationKind.CREATE)
        provider = FakeWorkshopProvider(game_session=GameSessionState.IN_GAME)
        service = self.service(fixture, provider)
        with self.assertRaises(GateError) as raised:
            service.begin_online_window(fixture.plan.operation_id)
        self.assertEqual(
            raised.exception.gate_code, "BLOCKED_OTHER_MACHINE_IN_GAME"
        )
        self.assertEqual(provider.go_online_calls, 0)
        self.assertEqual(provider.create_calls, 0)

    def test_outer_and_plan_item_id_mismatch_blocks_before_submit(self) -> None:
        fixture = WorkflowFixture(
            self.root,
            "id-mismatch",
            OperationKind.UPDATE,
            target_item_id="9000000789",
            outer_item_id="9000000790",
        )
        provider = FakeWorkshopProvider(owned_item_ids={"9000000789"})
        service = self.service(fixture, provider)
        with self.assertRaises(GateError) as raised:
            service.begin_online_window(fixture.plan.operation_id)
        self.assertEqual(
            raised.exception.gate_code, "BLOCKED_DESCRIPTOR_ID_MISMATCH"
        )
        self.assertEqual(provider.submit_calls, 0)
        self.assertEqual(provider.steam_mode, SteamMode.OFFLINE)

    def test_forbidden_upstream_id_is_rejected(self) -> None:
        fixture = WorkflowFixture(
            self.root,
            "forbidden-upstream",
            OperationKind.UPDATE,
            target_item_id="3596580780",
            outer_item_id="3596580780",
        )
        provider = FakeWorkshopProvider(owned_item_ids={"3596580780"})
        service = self.service(fixture, provider)
        with self.assertRaises(GateError) as raised:
            service.begin_online_window(fixture.plan.operation_id)
        self.assertEqual(raised.exception.gate_code, "BLOCKED_FORBIDDEN_UPSTREAM_ID")
        self.assertEqual(provider.submit_calls, 0)

    def test_inner_descriptor_remote_id_is_rejected_before_provider(self) -> None:
        fixture = WorkflowFixture(self.root, "inner-id", OperationKind.CREATE)
        inner = Path(fixture.plan.staging_dir) / "descriptor.mod"
        inner.write_text(
            inner.read_text(encoding="utf-8") + 'remote_file_id="3596580780"\n',
            encoding="utf-8",
        )
        provider = FakeWorkshopProvider()
        service = self.service(fixture, provider)
        with self.assertRaises(GateError) as raised:
            service.begin_online_window(fixture.plan.operation_id)
        self.assertEqual(raised.exception.gate_code, "BLOCKED_FORBIDDEN_UPSTREAM_ID")
        self.assertEqual(provider.create_calls, 0)

    def test_staging_bytes_must_match_hash_bound_manifest(self) -> None:
        fixture = WorkflowFixture(self.root, "staging-mismatch", OperationKind.CREATE)
        (Path(fixture.plan.staging_dir) / "content.txt").write_text(
            "changed after build\n", encoding="utf-8"
        )
        provider = FakeWorkshopProvider()
        service = self.service(fixture, provider)
        with self.assertRaises(GateError) as raised:
            service.begin_online_window(fixture.plan.operation_id)
        self.assertEqual(raised.exception.gate_code, "BLOCKED_STAGING_MISMATCH")
        self.assertEqual(provider.create_calls, 0)

    def test_default_real_provider_is_inert(self) -> None:
        provider = PdxLauncherReadOnlyProvider()
        capabilities = provider.capabilities()
        self.assertTrue(capabilities.read_only)
        self.assertFalse(capabilities.create_item)
        self.assertFalse(capabilities.update_item)


if __name__ == "__main__":
    unittest.main()
