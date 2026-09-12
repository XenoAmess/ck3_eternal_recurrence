"""Provider contracts and deliberately inert real-provider skeletons."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Protocol

from .errors import ProviderResultUnknownError, ProviderUnavailableError
from .models import (
    AccountSnapshot,
    CreateItemResult,
    EulaState,
    GameSessionState,
    PublicationPlan,
    SteamMode,
    SubmitItemResult,
)


@dataclass(frozen=True, slots=True)
class ProviderCapabilities:
    provider: str
    read_only: bool
    account_state_observable: bool
    owned_items_observable: bool
    legal_status_observable: bool
    online_control: bool
    create_item: bool
    update_item: bool
    visibility: bool
    change_note: bool
    update_language: bool
    remote_readback: bool
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        result = asdict(self)
        result["notes"] = list(self.notes)
        return result


class WorkshopProvider(Protocol):
    """The minimum provider surface required by the workflow engine."""

    def capabilities(self) -> ProviderCapabilities: ...

    def inspect_account(self) -> AccountSnapshot: ...

    def inspect_eula(self, consumer_app_id: int) -> EulaState: ...

    def go_online(self) -> None: ...

    def restore_offline(self) -> None: ...

    def create_item(self, plan: PublicationPlan) -> CreateItemResult: ...

    def submit_item_update(
        self, plan: PublicationPlan, item_id: str
    ) -> SubmitItemResult: ...


class PdxLauncherReadOnlyProvider:
    """Capability-only skeleton for the private Launcher/Greenworks path.

    This class intentionally does not discover, start, attach to, or send IPC to
    Steam or the Paradox Launcher.  A future provider must pin the Launcher and
    ASAR identity before adding those separately reviewed operations.
    """

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            provider="pdx-launcher-readonly",
            read_only=True,
            account_state_observable=False,
            owned_items_observable=False,
            legal_status_observable=False,
            online_control=False,
            create_item=False,
            update_item=False,
            visibility=False,
            change_note=False,
            update_language=False,
            remote_readback=False,
            notes=(
                "Known protocol: Electron @IPC_MODS_UPLOAD/UPLOAD_MOD wraps Greenworks ISteamUGC.",
                "No external IPC transport or legal-agreement status is implemented.",
                "This provider never touches a running Steam or Launcher process.",
            ),
        )

    def inspect_account(self) -> AccountSnapshot:
        return AccountSnapshot(SteamMode.UNKNOWN, GameSessionState.UNKNOWN)

    def inspect_eula(self, consumer_app_id: int) -> EulaState:
        del consumer_app_id
        return EulaState.UNKNOWN

    def _unavailable(self) -> None:
        raise ProviderUnavailableError(
            "the PDX provider is a read-only capability skeleton; external writes are disabled"
        )

    def go_online(self) -> None:
        self._unavailable()

    def restore_offline(self) -> None:
        self._unavailable()

    def create_item(self, plan: PublicationPlan) -> CreateItemResult:
        del plan
        self._unavailable()
        raise AssertionError("unreachable")

    def submit_item_update(
        self, plan: PublicationPlan, item_id: str
    ) -> SubmitItemResult:
        del plan, item_id
        self._unavailable()
        raise AssertionError("unreachable")


class SteamworksReadOnlyProvider(PdxLauncherReadOnlyProvider):
    """Capability-only skeleton for a future direct ``ISteamUGC`` adapter."""

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            provider="steamworks-readonly",
            read_only=True,
            account_state_observable=False,
            owned_items_observable=False,
            legal_status_observable=False,
            online_control=False,
            create_item=False,
            update_item=False,
            visibility=False,
            change_note=False,
            update_language=False,
            remote_readback=False,
            notes=(
                "Target API: CreateItem, StartItemUpdate, SetItem*, SubmitItemUpdate.",
                "A supported Steam launch/AppID context has not been implemented.",
                "No steam_appid.txt bypass, credential handling, DLL loading, or network call occurs.",
            ),
        )

    def _unavailable(self) -> None:
        raise ProviderUnavailableError(
            "the Steamworks provider is a read-only capability skeleton; ISteamUGC is not loaded"
        )


class FakeWorkshopProvider:
    """Deterministic provider used for contract and crash-recovery tests."""

    def __init__(
        self,
        *,
        steam_mode: SteamMode = SteamMode.OFFLINE,
        game_session: GameSessionState = GameSessionState.IDLE,
        eula: EulaState = EulaState.CLEAR,
        owned_item_ids: set[str] | None = None,
        next_item_id: str = "9000000001",
        crash_on_create: bool = False,
        unknown_on_submit: bool = False,
        eula_on_create: EulaState = EulaState.CLEAR,
        eula_on_submit: EulaState = EulaState.CLEAR,
        fail_restore_offline: bool = False,
    ) -> None:
        self.steam_mode = steam_mode
        self.game_session = game_session
        self.eula = eula
        self.owned_item_ids = set(owned_item_ids or ())
        self.next_item_id = next_item_id
        self.crash_on_create = crash_on_create
        self.unknown_on_submit = unknown_on_submit
        self.eula_on_create = eula_on_create
        self.eula_on_submit = eula_on_submit
        self.fail_restore_offline = fail_restore_offline
        self.go_online_calls = 0
        self.restore_offline_calls = 0
        self.create_calls = 0
        self.submit_calls = 0

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            provider="fake",
            read_only=False,
            account_state_observable=True,
            owned_items_observable=True,
            legal_status_observable=True,
            online_control=True,
            create_item=True,
            update_item=True,
            visibility=True,
            change_note=True,
            update_language=False,
            remote_readback=True,
            notes=("In-memory test double; it never contacts Steam or Paradox.",),
        )

    def inspect_account(self) -> AccountSnapshot:
        return AccountSnapshot(
            self.steam_mode,
            self.game_session,
            frozenset(self.owned_item_ids),
        )

    def inspect_eula(self, consumer_app_id: int) -> EulaState:
        del consumer_app_id
        return self.eula

    def go_online(self) -> None:
        self.go_online_calls += 1
        self.steam_mode = SteamMode.ONLINE

    def restore_offline(self) -> None:
        self.restore_offline_calls += 1
        if self.fail_restore_offline:
            raise ProviderResultUnknownError("fake offline restoration failed")
        self.steam_mode = SteamMode.OFFLINE

    def create_item(self, plan: PublicationPlan) -> CreateItemResult:
        del plan
        self.create_calls += 1
        if self.crash_on_create:
            raise ProviderResultUnknownError(
                "fake provider crashed after CreateItem may have reached Steam"
            )
        self.owned_item_ids.add(self.next_item_id)
        return CreateItemResult(self.next_item_id, self.eula_on_create)

    def submit_item_update(
        self, plan: PublicationPlan, item_id: str
    ) -> SubmitItemResult:
        del plan
        self.submit_calls += 1
        if self.unknown_on_submit:
            raise ProviderResultUnknownError(
                "fake provider lost the SubmitItemUpdate callback"
            )
        self.owned_item_ids.add(item_id)
        return SubmitItemResult(item_id, self.eula_on_submit)
