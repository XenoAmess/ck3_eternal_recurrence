"""Managed-runtime hand-off for the ZhongGuo phase-two promo producer.

This module does not launch CK3, invoke FFmpeg directly, inspect the desktop,
or write an artifact.  It supplies a strict dependency-injected scaffold plus
an adapter that reuses the acceptance runner's live gates and delegates the
fixed eight-span ordering to the producer-neutral choreography executor.  Only
after those gates and all real visual handlers are ready does the adapter ask
the runner-owned recorder to start and create clean holds.

The factory is useful before the gameplay implementation exists: invoking a
scaffold with an unconfigured or unavailable runtime raises a structured RED
error instead of returning placeholder gates.  The explicit install helper is
the only function that registers a producer with the acceptance runner.  It is
not called at import time and should only be used once a real choreography
delegate is available.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Final, NoReturn, Protocol, TypeAlias


PHASE2_PROMO_CAPTURE_MODE: Final = "zhongguo-361-phase2"
PHASE2_PROMO_CAPTURE_CONTRACT_VERSION: Final = 1
PHASE2_PROMO_CAPTURE_PRODUCER_ID: Final = (
    "zhongguo-361-phase2-visual-producer-v1"
)
PHASE2_PROMO_CLEAN_SPANS: Final = (
    "phase2_fact_quota_calibration",
    "phase2_receipt_appeal_pip",
    "phase2_manager_governance",
    "phase2_promotion_compensation",
    "phase2_hc_workforce",
    "phase2_projects_metrics",
    "phase2_incidents_operations",
    "phase2_cross_cycle_endgame",
)
PHASE2_PROMO_CAPTURE_SPAN_MAP: Final = (
    ("phase2_fact_quota_calibration", "facts-quota-calibration"),
    ("phase2_receipt_appeal_pip", "receipts-appeals-pip"),
    ("phase2_manager_governance", "manager-governance"),
    ("phase2_promotion_compensation", "promotion-compensation"),
    ("phase2_hc_workforce", "hc-workforce"),
    ("phase2_projects_metrics", "projects-metrics"),
    ("phase2_incidents_operations", "incidents-operations"),
    ("phase2_cross_cycle_endgame", "cross-cycle-endgame"),
)


def canonical_phase2_capture_contract() -> dict[str, object]:
    """Return a fresh copy of the exact v1 runner/preset contract."""

    return {
        "mode": PHASE2_PROMO_CAPTURE_MODE,
        "version": PHASE2_PROMO_CAPTURE_CONTRACT_VERSION,
        "producer_id": PHASE2_PROMO_CAPTURE_PRODUCER_ID,
        "span_ids": list(PHASE2_PROMO_CLEAN_SPANS),
        "span_map": [
            {"chapter_id": chapter_id, "producer_key": producer_key}
            for chapter_id, producer_key in PHASE2_PROMO_CAPTURE_SPAN_MAP
        ],
    }


def _json_safe(value: object) -> object:
    """Project diagnostic values onto JSON-compatible primitives.

    Runtime probes may carry native wrapper objects in a failure payload.  A
    diagnostic must remain serializable without asking the scaffold to inspect
    or otherwise mutate those objects.
    """

    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    try:
        return repr(value)
    except BaseException:
        return f"<{type(value).__name__}>"


def _strict_equal(expected: object, actual: object) -> bool:
    """Compare the JSON contract with exact container and scalar types."""

    if type(expected) is not type(actual):
        return False
    if isinstance(expected, dict):
        if expected.keys() != actual.keys():  # type: ignore[union-attr]
            return False
        return all(
            _strict_equal(expected[key], actual[key])  # type: ignore[index]
            for key in expected
        )
    if isinstance(expected, list):
        if len(expected) != len(actual):  # type: ignore[arg-type]
            return False
        return all(
            _strict_equal(left, right)
            for left, right in zip(expected, actual)  # type: ignore[arg-type]
        )
    return expected == actual


class Phase2PromoProducerError(RuntimeError):
    """A typed RED at the producer hand-off boundary.

    ``reason_code`` is intentionally stable for direct callers while
    ``evidence`` remains a small, JSON-compatible partial record.  The
    acceptance runner preserves this envelope as
    ``phase2_promo_producer_error`` when the hand-off reaches its report
    boundary.  The scaffold also rejects an explicitly reported non-GREEN
    producer result; omitting that optional field leaves the runner's outer
    result in charge.
    """

    result: Final = "RED"

    def __init__(
        self,
        reason_code: str,
        message: str,
        *,
        evidence: Mapping[str, object] | None = None,
    ) -> None:
        self.reason_code = reason_code
        # ``reason`` and ``code`` are convenient compatibility aliases for
        # callers that use the terminology from other typed bridge cells.
        self.reason = reason_code
        self.code = reason_code
        diagnostic = _json_safe(dict(evidence or {}))
        self.evidence = {
            **(diagnostic if isinstance(diagnostic, dict) else {}),
            # Keep the typed envelope authoritative even if a dependency
            # supplied colliding diagnostic keys.
            "result": "RED",
            "reason_code": reason_code,
        }
        super().__init__(
            f"phase-two promo producer typed RED [{reason_code}]: {message}"
        )


class Phase2PromoProducerUnavailable(Phase2PromoProducerError):
    """The producer cannot run because a real runtime dependency is absent."""


class Phase2PromoProducerContractError(Phase2PromoProducerError):
    """The producer or its delegate violated the canonical contract."""


def phase2_promo_producer_typed_error_payload(
    error: BaseException,
) -> dict[str, object] | None:
    """Project a producer exception onto the stable JSON RED envelope.

    The acceptance runner may adapt a :class:`Phase2PromoProducerError` to
    its own ``RunnerError`` class, so it cannot rely on the concrete exception
    type.  Only the typed ``reason_code`` plus an optional exact ``RED``
    result qualify; ordinary runner failures remain represented solely by
    ``error_reason``.  Evidence is projected through the same JSON-safe
    routine used by the producer error itself, keeping report serialization
    deterministic without inspecting native bridge objects.
    """

    try:
        reason_code = getattr(error, "reason_code", None)
        result = getattr(error, "result", None)
        evidence = getattr(error, "evidence", None)
    except BaseException:
        return None
    if type(reason_code) is not str or not reason_code:
        return None
    if result is not None and (type(result) is not str or result != "RED"):
        return None
    if evidence is None:
        diagnostic: object = {}
    elif isinstance(evidence, Mapping):
        try:
            diagnostic = _json_safe(dict(evidence))
        except BaseException:
            diagnostic = {}
    else:
        diagnostic = {"value": _json_safe(evidence)}
    if not isinstance(diagnostic, dict):
        diagnostic = {"value": diagnostic}
    return {
        "result": "RED",
        "reason_code": reason_code,
        "evidence": diagnostic,
    }


@dataclass(frozen=True, slots=True)
class Phase2PromoCaptureContext:
    """Parameter snapshot passed to injected producer dependencies.

    The dataclass prevents rebinding its top-level fields.  The injected
    dependencies still own the referenced runner/bridge objects; this type is
    a hand-off boundary, not a claim that those external objects are immutable.
    """

    stream: object
    artifacts: Path
    recorder: object
    title_navigation_service: object
    tracked_ck3_pid: int
    native_bridge: object
    preflight_bridge_identity: Mapping[str, object]
    contract: Mapping[str, object]
    # The phase-two acceptance runner supplies these snapshots only after it
    # has installed the canonical paused seed and passed the managed loader
    # gate.  Defaults deliberately keep the original hand-off ABI valid for
    # callers that construct the context through the legacy argument set.
    seed_contract: Mapping[str, object] | None = None
    seed_install: Mapping[str, object] | None = None
    native_session_binding: Mapping[str, object] | None = None
    loader_gate: Mapping[str, object] | None = None
    source_checkpoint_registry: Mapping[str, object] | None = None
    isolated_userdir: Path | None = None
    runtime_bootstrap: Mapping[str, object] | None = None
    endgame_product_switch_title_key: str | None = None


class RuntimeProbe(Protocol):
    """Read-only runtime readiness probe supplied by a future live producer."""

    def __call__(
        self, context: Phase2PromoCaptureContext
    ) -> Mapping[str, object]: ...


class Choreography(Protocol):
    """Real gameplay/UI choreography supplied by a future live producer."""

    def __call__(
        self,
        context: Phase2PromoCaptureContext,
        runtime: Mapping[str, object],
    ) -> Mapping[str, object]: ...


ProducerErrorFactory: TypeAlias = Callable[[str], Exception]
RunnerRegistrar: TypeAlias = Callable[[Callable[..., dict[str, object]]], None]
Phase2PromoPausedSnapshotProbe: TypeAlias = Callable[
    [Phase2PromoCaptureContext], Mapping[str, object]
]
Phase2PromoSeedProofProbe: TypeAlias = Callable[
    [Phase2PromoCaptureContext, Mapping[str, object]], Mapping[str, object]
]
Phase2PromoVisualPrimitive: TypeAlias = Callable[
    [Phase2PromoCaptureContext, Mapping[str, object], str, str],
    Mapping[str, object],
]
Phase2SpanDriverFactory: TypeAlias = Callable[
    [Phase2PromoCaptureContext], object
]


def _canonical_contract(value: Mapping[str, object]) -> dict[str, object]:
    """Validate and copy a contract without normalizing or filling fields."""

    if not isinstance(value, Mapping):
        raise Phase2PromoProducerContractError(
            "contract_not_mapping",
            "phase-two capture contract must be a mapping",
            evidence={"actual_type": type(value).__name__},
        )
    try:
        actual = deepcopy(dict(value))
    except BaseException as error:
        raise Phase2PromoProducerContractError(
            "contract_unreadable",
            "phase-two capture contract could not be copied",
            evidence={"exception_type": type(error).__name__},
        ) from error
    expected = canonical_phase2_capture_contract()
    if not _strict_equal(actual, expected):
        raise Phase2PromoProducerContractError(
            "contract_mismatch",
            "phase-two capture contract differs from the canonical v1 contract",
            evidence={"expected_contract": expected, "actual_contract": actual},
        )
    return actual


def _recorder_contract(recorder: object) -> Mapping[str, object] | None:
    """Read a runner ``PromoRecorder`` contract without touching its lifecycle."""

    try:
        value = getattr(recorder, "contract", None)
    except BaseException:
        return None
    if value is None:
        return None
    try:
        to_mapping = getattr(value, "to_mapping", None)
        if callable(to_mapping):
            value = to_mapping()
    except BaseException:
        return None
    if not isinstance(value, Mapping):
        return None
    return value


class Phase2PromoProducerScaffold:
    """Strict, side-effect-free adapter around future runtime dependencies.

    The object itself is the callable accepted by
    ``register_phase2_promo_capture_producer``.  It deliberately does not
    implement any CK3 action or visual operation.  Those remain in the
    injected ``runtime_probe`` and ``choreography`` functions.
    """

    __slots__ = (
        "_contract_snapshot",
        "runtime_probe",
        "choreography",
        "error_factory",
        "span_session_contract_version",
    )

    def __init__(
        self,
        contract: Mapping[str, object],
        runtime_probe: RuntimeProbe | None = None,
        choreography: Choreography | None = None,
        error_factory: ProducerErrorFactory | None = None,
        span_session_contract_version: int | None = None,
    ) -> None:
        # Store a private-by-convention copy so a caller cannot mutate the
        # contract after construction and silently change the hand-off.
        self._contract_snapshot = _canonical_contract(contract)
        self.runtime_probe = runtime_probe
        self.choreography = choreography
        self.error_factory = error_factory
        self.span_session_contract_version = span_session_contract_version
        if runtime_probe is not None and not callable(runtime_probe):
            raise TypeError("runtime_probe must be callable or None")
        if choreography is not None and not callable(choreography):
            raise TypeError("choreography must be callable or None")
        if error_factory is not None and not callable(error_factory):
            raise TypeError("error_factory must be callable or None")

    @property
    def contract(self) -> dict[str, object]:
        """Return a copy so callers cannot mutate the validation snapshot."""

        return deepcopy(self._contract_snapshot)

    def _red(
        self,
        reason_code: str,
        message: str,
        *,
        evidence: Mapping[str, object] | None = None,
        unavailable: bool = True,
    ) -> NoReturn:
        error_class = (
            Phase2PromoProducerUnavailable
            if unavailable
            else Phase2PromoProducerContractError
        )
        local_error = error_class(reason_code, message, evidence=evidence)
        if self.error_factory is None:
            raise local_error
        try:
            adapted = self.error_factory(str(local_error))
        except BaseException:
            # An error adapter must never hide the original typed RED.
            raise local_error
        if not isinstance(adapted, Exception):
            raise local_error
        # RunnerError has no structured fields, so attach them opportunistically
        # while retaining its established exception type for the caller.
        adaptation_failed = False
        for name, value in (
            ("reason_code", local_error.reason_code),
            ("reason", local_error.reason),
            ("code", local_error.code),
            ("result", local_error.result),
            ("evidence", local_error.evidence),
        ):
            try:
                setattr(adapted, name, value)
            except BaseException:
                adaptation_failed = True
        if adaptation_failed:
            raise local_error
        raise adapted

    def _build_context(
        self,
        stream: object,
        artifacts: Path,
        recorder: object,
        *,
        title_navigation_service: object,
        tracked_ck3_pid: int,
        native_bridge: object,
        preflight_bridge_identity: Mapping[str, object],
        seed_contract: Mapping[str, object] | None = None,
        seed_install: Mapping[str, object] | None = None,
        native_session_binding: Mapping[str, object] | None = None,
        loader_gate: Mapping[str, object] | None = None,
        source_checkpoint_registry: Mapping[str, object] | None = None,
        isolated_userdir: Path | None = None,
        runtime_bootstrap: Mapping[str, object] | None = None,
        endgame_product_switch_title_key: str | None = None,
    ) -> Phase2PromoCaptureContext:
        if not isinstance(artifacts, Path):
            self._red(
                "invalid_artifacts_path",
                "artifacts must be a pathlib.Path",
                evidence={"actual_type": type(artifacts).__name__},
            )
        if (
            isinstance(tracked_ck3_pid, bool)
            or not isinstance(tracked_ck3_pid, int)
            or tracked_ck3_pid <= 0
        ):
            self._red(
                "runtime_pid_unavailable",
                "a positive tracked CK3 PID is required for a live hand-off",
                evidence={"tracked_ck3_pid": tracked_ck3_pid},
            )
        if not isinstance(preflight_bridge_identity, Mapping):
            self._red(
                "bridge_identity_unavailable",
                "preflight bridge identity must be a mapping",
                evidence={
                    "actual_type": type(preflight_bridge_identity).__name__
                },
            )
        if recorder is None:
            self._red("recorder_unavailable", "a PromoRecorder is required")
        actual_contract = _recorder_contract(recorder)
        if actual_contract is None or not _strict_equal(
            dict(actual_contract), self._contract_snapshot
        ):
            self._red(
                "recorder_contract_mismatch",
                "recorder is not bound to the canonical phase-two contract",
                evidence={
                    "expected_contract": self._contract_snapshot,
                    "actual_contract": (
                        dict(actual_contract) if actual_contract is not None else {}
                    ),
                },
                unavailable=False,
            )
        missing = [
            name
            for name, value in (
                ("title_navigation_service", title_navigation_service),
                ("native_bridge", native_bridge),
            )
            if value is None
        ]
        if missing:
            self._red(
                "runtime_dependency_unavailable",
                "required runtime dependency is None: " + ", ".join(missing),
                evidence={"missing_dependencies": missing},
            )
        try:
            bridge_identity = deepcopy(dict(preflight_bridge_identity))
        except BaseException as error:
            self._red(
                "bridge_identity_unavailable",
                "preflight bridge identity could not be copied",
                evidence={"exception_type": type(error).__name__},
            )

        optional_snapshots: dict[str, Mapping[str, object] | None] = {}
        for name, value in (
            ("seed_contract", seed_contract),
            ("seed_install", seed_install),
            ("native_session_binding", native_session_binding),
            ("loader_gate", loader_gate),
            ("source_checkpoint_registry", source_checkpoint_registry),
        ):
            if value is None:
                optional_snapshots[name] = None
                continue
            if not isinstance(value, Mapping):
                self._red(
                    f"{name}_invalid",
                    f"{name} must be a mapping when supplied",
                    evidence={"actual_type": type(value).__name__},
                )
            try:
                optional_snapshots[name] = deepcopy(dict(value))
            except BaseException as error:
                self._red(
                    f"{name}_unavailable",
                    f"{name} could not be copied",
                    evidence={"exception_type": type(error).__name__},
                )
        if isolated_userdir is not None and not isinstance(isolated_userdir, Path):
            self._red(
                "isolated_userdir_invalid",
                "isolated_userdir must be a pathlib.Path when supplied",
                evidence={"actual_type": type(isolated_userdir).__name__},
            )
        if runtime_bootstrap is not None and not isinstance(
            runtime_bootstrap, Mapping
        ):
            self._red(
                "runtime_bootstrap_invalid",
                "runtime_bootstrap must be a mapping when supplied",
                evidence={"actual_type": type(runtime_bootstrap).__name__},
            )
        if endgame_product_switch_title_key is not None and (
            not isinstance(endgame_product_switch_title_key, str)
            or not endgame_product_switch_title_key
        ):
            self._red(
                "endgame_product_switch_title_key_invalid",
                "the product Switch Character title key must be non-empty",
                evidence={
                    "actual_type": type(
                        endgame_product_switch_title_key
                    ).__name__
                },
            )
        return Phase2PromoCaptureContext(
            stream=stream,
            artifacts=artifacts,
            recorder=recorder,
            title_navigation_service=title_navigation_service,
            tracked_ck3_pid=tracked_ck3_pid,
            native_bridge=native_bridge,
            preflight_bridge_identity=bridge_identity,
            contract=deepcopy(self._contract_snapshot),
            seed_contract=optional_snapshots["seed_contract"],
            seed_install=optional_snapshots["seed_install"],
            native_session_binding=optional_snapshots["native_session_binding"],
            loader_gate=optional_snapshots["loader_gate"],
            source_checkpoint_registry=optional_snapshots[
                "source_checkpoint_registry"
            ],
            isolated_userdir=(
                isolated_userdir.resolve()
                if isinstance(isolated_userdir, Path)
                else None
            ),
            runtime_bootstrap=(
                deepcopy(dict(runtime_bootstrap))
                if isinstance(runtime_bootstrap, Mapping)
                else None
            ),
            endgame_product_switch_title_key=(
                endgame_product_switch_title_key
            ),
        )

    def _validate_runtime(
        self,
        context: Phase2PromoCaptureContext,
    ) -> dict[str, object]:
        if self.runtime_probe is None:
            self._red(
                "runtime_probe_unconfigured",
                "no read-only real-runtime probe was supplied",
                evidence={"tracked_ck3_pid": context.tracked_ck3_pid},
            )
        try:
            observed = self.runtime_probe(context)
        except Phase2PromoProducerError:
            raise
        except Exception as error:
            self._red(
                "runtime_probe_failed",
                "runtime probe raised before choreography could start",
                evidence={
                    "exception_type": type(error).__name__,
                    "exception": str(error),
                },
            )
        if not isinstance(observed, Mapping):
            self._red(
                "runtime_probe_invalid",
                "runtime probe must return a mapping",
                evidence={"actual_type": type(observed).__name__},
            )
        # Keep the delegate's runtime payload intact for hand-off.  Only
        # diagnostic copies are projected through ``_json_safe`` by the error
        # type; a native wrapper in a successful payload is not inspected here.
        runtime = dict(observed)
        if runtime.get("ready") is not True:
            self._red(
                "runtime_unavailable",
                "real CK3 runtime is not ready for visual choreography",
                evidence={"runtime": runtime},
            )
        return runtime

    def _validate_result(self, result: object) -> dict[str, object]:
        if not isinstance(result, Mapping):
            self._red(
                "producer_evidence_invalid",
                "choreography must return a mapping evidence object",
                evidence={"actual_type": type(result).__name__},
                unavailable=False,
            )
        # Do not reinterpret or synthesize producer evidence.  A shallow copy
        # protects the caller's top-level mapping while preserving any native
        # values the downstream runner knows how to retain.
        evidence = dict(result)
        required = ("capture_mode", "capture_contract_version", "capture_contract")
        missing = [name for name in required if name not in evidence]
        if missing:
            self._red(
                "producer_contract_fields_missing",
                "choreography omitted canonical contract fields: "
                + ", ".join(missing),
                evidence={"missing_fields": missing},
                unavailable=False,
            )
        if "result" in evidence and (
            type(evidence["result"]) is not str
            or evidence["result"] != "GREEN"
        ):
            self._red(
                "producer_result_not_green",
                "an explicitly reported producer result must be GREEN",
                evidence={"result": evidence["result"]},
                unavailable=False,
            )
        if (
            type(evidence["capture_mode"]) is not str
            or evidence["capture_mode"] != PHASE2_PROMO_CAPTURE_MODE
        ):
            self._red(
                "producer_mode_mismatch",
                "choreography returned a non-canonical capture mode",
                evidence={"capture_mode": evidence["capture_mode"]},
                unavailable=False,
            )
        if (
            type(evidence["capture_contract_version"]) is not int
            or isinstance(evidence["capture_contract_version"], bool)
            or evidence["capture_contract_version"]
            != PHASE2_PROMO_CAPTURE_CONTRACT_VERSION
        ):
            self._red(
                "producer_contract_version_mismatch",
                "choreography returned an unsupported contract version",
                evidence={
                    "capture_contract_version": evidence[
                        "capture_contract_version"
                    ]
                },
                unavailable=False,
            )
        returned_contract = evidence["capture_contract"]
        if (
            not isinstance(returned_contract, dict)
            or not _strict_equal(returned_contract, self._contract_snapshot)
        ):
            self._red(
                "producer_contract_mismatch",
                "choreography returned a non-canonical capture contract",
                evidence={
                    "expected_contract": self._contract_snapshot,
                    "actual_contract": (
                        dict(returned_contract)
                        if isinstance(returned_contract, Mapping)
                        else {}
                    ),
                },
                unavailable=False,
            )
        return evidence

    def __call__(
        self,
        stream: object,
        artifacts: Path,
        recorder: object,
        *,
        title_navigation_service: object,
        tracked_ck3_pid: int,
        native_bridge: object,
        preflight_bridge_identity: Mapping[str, object],
        seed_contract: Mapping[str, object] | None = None,
        seed_install: Mapping[str, object] | None = None,
        native_session_binding: Mapping[str, object] | None = None,
        loader_gate: Mapping[str, object] | None = None,
        source_checkpoint_registry: Mapping[str, object] | None = None,
        isolated_userdir: Path | None = None,
        runtime_bootstrap: Mapping[str, object] | None = None,
        endgame_product_switch_title_key: str | None = None,
    ) -> dict[str, object]:
        """Perform only dependency validation and evidence hand-off.

        No recorder method is called here.  In particular, a RED path cannot
        accidentally create a raw recording or clean-frame gate.
        """

        context = self._build_context(
            stream,
            artifacts,
            recorder,
            title_navigation_service=title_navigation_service,
            tracked_ck3_pid=tracked_ck3_pid,
            native_bridge=native_bridge,
            preflight_bridge_identity=preflight_bridge_identity,
            seed_contract=seed_contract,
            seed_install=seed_install,
            native_session_binding=native_session_binding,
            loader_gate=loader_gate,
            source_checkpoint_registry=source_checkpoint_registry,
            isolated_userdir=isolated_userdir,
            runtime_bootstrap=runtime_bootstrap,
            endgame_product_switch_title_key=(
                endgame_product_switch_title_key
            ),
        )
        runtime = self._validate_runtime(context)
        if self.choreography is None:
            self._red(
                "choreography_unconfigured",
                "no real phase-two gameplay choreography was supplied",
                evidence={"tracked_ck3_pid": context.tracked_ck3_pid},
            )
        try:
            result = self.choreography(context, runtime)
        except Phase2PromoProducerError:
            raise
        except Exception as error:
            self._red(
                "choreography_failed",
                "real choreography raised before a complete evidence object",
                evidence={
                    "exception_type": type(error).__name__,
                    "exception": str(error),
                },
            )
        return self._validate_result(result)


def make_managed_phase2_runtime_probe(
    *,
    paused_snapshot_probe: Phase2PromoPausedSnapshotProbe,
    seed_proof_probe: Phase2PromoSeedProofProbe,
) -> RuntimeProbe:
    """Bind the producer to the runner's real managed phase-two live gates.

    The returned probe is intentionally an adapter, not a second readiness
    implementation.  The acceptance runner injects its existing paused-map
    and loaded-seed primitives, while this function checks the snapshots that
    were already produced by seed installation, native-session startup and
    the loader gate.  No recorder method is reachable until every check is
    GREEN and the paused snapshot is bound to the tracked CK3 PID.
    """

    if not callable(paused_snapshot_probe):
        raise TypeError("paused_snapshot_probe must be callable")
    if not callable(seed_proof_probe):
        raise TypeError("seed_proof_probe must be callable")

    def probe(context: Phase2PromoCaptureContext) -> Mapping[str, object]:
        seed_contract = context.seed_contract
        seed_install = context.seed_install
        native_binding = context.native_session_binding
        loader_gate = context.loader_gate
        missing = [
            name
            for name, value in (
                ("seed_contract", seed_contract),
                ("seed_install", seed_install),
                ("native_session_binding", native_binding),
                ("loader_gate", loader_gate),
            )
            if not isinstance(value, Mapping)
        ]
        if missing:
            reason_code = (
                "seed_not_ready"
                if "seed_contract" in missing
                else "live_gate_unavailable"
            )
            raise Phase2PromoProducerUnavailable(
                reason_code,
                "managed phase-two live-gate snapshots are incomplete",
                evidence={"missing_snapshots": missing},
            )

        assert isinstance(seed_contract, Mapping)
        assert isinstance(seed_install, Mapping)
        assert isinstance(native_binding, Mapping)
        assert isinstance(loader_gate, Mapping)
        install_contract = seed_install.get("contract")
        checks = {
            "seed_contract_ready": seed_contract.get("ready") is True
            and seed_contract.get("status") == "ready",
            "seed_install_green": seed_install.get("result") == "GREEN",
            "seed_install_contract_matches": isinstance(
                install_contract, Mapping
            )
            and _strict_equal(dict(install_contract), dict(seed_contract)),
            "native_session_pid_matches": native_binding.get("bridge_pid")
            == context.tracked_ck3_pid,
            "native_session_generation_positive": type(
                native_binding.get("connection_generation")
            )
            is int
            and int(native_binding["connection_generation"]) > 0,
            "loader_gate_green": loader_gate.get("result") == "GREEN",
            "loader_gate_mode": loader_gate.get("mode")
            == "phase2_promo_capture",
            "loader_completion_authorized": loader_gate.get(
                "same_pid_gameplay_continuation_authorized"
            )
            is True,
        }
        failed = [name for name, passed in checks.items() if passed is not True]
        if failed:
            blocker_order = (
                ("seed_contract_ready", "seed_not_ready"),
                ("seed_install_green", "seed_not_installed"),
                ("seed_install_contract_matches", "seed_not_installed"),
                ("native_session_pid_matches", "native_session_not_bound"),
                (
                    "native_session_generation_positive",
                    "native_session_not_bound",
                ),
                ("loader_gate_green", "loader_gate_not_green"),
                ("loader_gate_mode", "loader_gate_not_green"),
                (
                    "loader_completion_authorized",
                    "loader_gate_not_green",
                ),
            )
            reason_code = next(
                code for name, code in blocker_order if name in failed
            )
            raise Phase2PromoProducerUnavailable(
                reason_code,
                "managed phase-two loader/seed/session gate is not GREEN",
                evidence={"checks": checks, "failed_checks": failed},
            )
        snapshot = paused_snapshot_probe(context)
        if not isinstance(snapshot, Mapping):
            raise Phase2PromoProducerUnavailable(
                "paused_snapshot_invalid",
                "paused snapshot primitive returned a non-mapping value",
                evidence={"actual_type": type(snapshot).__name__},
            )
        proof = seed_proof_probe(context, snapshot)
        if not isinstance(proof, Mapping) or proof.get("result") != "GREEN":
            raise Phase2PromoProducerUnavailable(
                "seed_load_proof_red",
                "loaded-seed primitive did not return GREEN evidence",
                evidence={"seed_load_proof": proof},
            )
        snapshot_diagnostics = snapshot.get("diagnostics")
        snapshot_pid = (
            snapshot_diagnostics.get("bridge_pid")
            if isinstance(snapshot_diagnostics, Mapping)
            else None
        )
        if snapshot_pid != context.tracked_ck3_pid:
            raise Phase2PromoProducerUnavailable(
                "paused_snapshot_pid_mismatch",
                "paused snapshot is not bound to the tracked CK3 PID",
                evidence={
                    "tracked_ck3_pid": context.tracked_ck3_pid,
                    "snapshot_bridge_pid": snapshot_pid,
                },
            )
        return {
            "ready": True,
            "gate": "managed_phase2_loader_completion_and_paused_seed",
            "checks": checks,
            "paused_snapshot": dict(snapshot),
            "seed_load_proof": dict(proof),
        }

    return probe


def make_eight_span_phase2_choreography(
    visual_primitives: Mapping[str, Phase2PromoVisualPrimitive] | None = None,
    *,
    reviewed_history_id: str,
    hold_seconds: float = 2.5,
    span_driver_factory: Phase2SpanDriverFactory | None = None,
) -> Choreography:
    """Adapt the visual primitive registry to the shared eight-span executor."""

    if visual_primitives is None:
        visual_primitives = {}
    if not isinstance(visual_primitives, Mapping):
        raise TypeError("visual_primitives must be a mapping")
    if span_driver_factory is not None and not callable(span_driver_factory):
        raise TypeError("span_driver_factory must be callable")
    if type(reviewed_history_id) is not str or not reviewed_history_id:
        raise TypeError("reviewed_history_id must be a non-empty string")
    if isinstance(hold_seconds, bool) or not isinstance(hold_seconds, (int, float)):
        raise TypeError("hold_seconds must be a number")
    if hold_seconds <= 0:
        raise ValueError("hold_seconds must be positive")

    def choreography(
        context: Phase2PromoCaptureContext,
        runtime: Mapping[str, object],
    ) -> Mapping[str, object]:
        # Local import avoids a module cycle: the producer contract is the
        # type owner imported by the producer-neutral choreography module.
        from zhongguo_phase2_capture_choreography import (
            PHASE2_CAPTURE_SCENARIOS,
            Phase2ChoreographyBlocked,
            phase2_choreography_readiness,
            run_phase2_capture_choreography,
        )

        class RegistrySpanDriver:
            def available_handlers(self) -> tuple[str, ...]:
                return tuple(
                    scenario.handler
                    for scenario in PHASE2_CAPTURE_SCENARIOS
                    if callable(visual_primitives.get(scenario.producer_key))
                )

            def run_span(
                self,
                scenario: object,
                live_context: Phase2PromoCaptureContext,
                live_runtime: Mapping[str, object],
            ) -> Mapping[str, object]:
                producer_key = getattr(scenario, "producer_key")
                span_id = getattr(scenario, "span_id")
                primitive = visual_primitives[producer_key]
                return primitive(
                    live_context,
                    live_runtime,
                    span_id,
                    producer_key,
                )

        driver = (
            RegistrySpanDriver()
            if span_driver_factory is None
            else span_driver_factory(context)
        )
        if not callable(getattr(driver, "available_handlers", None)) or not callable(
            getattr(driver, "run_span", None)
        ):
            raise Phase2PromoProducerUnavailable(
                "span_driver_unavailable",
                "phase-two span driver factory returned an invalid driver",
                evidence={"actual_type": type(driver).__name__},
            )
        readiness = phase2_choreography_readiness(context, runtime, driver)
        if readiness.get("ready") is not True:
            reason_code = str(readiness.get("reason_code"))
            raise Phase2PromoProducerUnavailable(
                reason_code,
                "shared phase-two capture choreography is not ready",
                evidence={"readiness": readiness},
            )
        recorder = context.recorder
        try:
            resolve_subject = getattr(recorder, "resolve_reviewed_subject")
            start = getattr(recorder, "start")
            clean_hold = getattr(recorder, "clean_hold")
        except (AttributeError, TypeError) as error:
            raise Phase2PromoProducerUnavailable(
                "recorder_lifecycle_unavailable",
                "phase-two recorder lacks its real capture lifecycle",
                evidence={"exception_type": type(error).__name__},
            ) from error
        if not all(callable(value) for value in (resolve_subject, start, clean_hold)):
            raise Phase2PromoProducerUnavailable(
                "recorder_lifecycle_unavailable",
                "phase-two recorder lifecycle attributes are not callable",
            )

        resolve_subject(reviewed_history_id)
        start()
        try:
            evidence = run_phase2_capture_choreography(
                context,
                runtime,
                driver,
                clean_hold_seconds=float(hold_seconds),
            )
        except Phase2ChoreographyBlocked as error:
            raise Phase2PromoProducerContractError(
                error.reason_code,
                "shared phase-two capture choreography returned RED",
                evidence={"choreography": error.evidence},
            ) from error
        seed_chain_provider = getattr(
            recorder, "phase2_seed_chain_provider", None
        )
        capture_lineage = getattr(recorder, "phase2_capture_lineage", None)
        if seed_chain_provider is not None or capture_lineage is not None:
            if not callable(seed_chain_provider) or not isinstance(
                capture_lineage, Mapping
            ):
                raise Phase2PromoProducerUnavailable(
                    "span_session_receipt_source_incomplete",
                    "phase-two v2 seed/lineage receipt source is incomplete",
                )
            seed_load_proof = runtime.get("seed_load_proof")
            if not isinstance(seed_load_proof, Mapping):
                raise Phase2PromoProducerUnavailable(
                    "seed_load_proof_red",
                    "phase-two v2 receipt requires the real loaded-seed proof",
                )
            seed_chain = seed_chain_provider(seed_load_proof)
            if not isinstance(seed_chain, Mapping) or seed_chain.get(
                "result"
            ) != "GREEN":
                raise Phase2PromoProducerUnavailable(
                    "seed_generation_loaded_chain_red",
                    "phase-two seed generation/load lineage receipt is RED",
                    evidence={
                        "seed_chain": (
                            dict(seed_chain)
                            if isinstance(seed_chain, Mapping)
                            else None
                        )
                    },
                )
            evidence["capture_lineage"] = dict(capture_lineage)
            evidence["seed_generation_loaded_chain"] = dict(seed_chain)
        evidence.update(
            {
                "producer_id": PHASE2_PROMO_CAPTURE_PRODUCER_ID,
                "runtime_gate": runtime.get("gate"),
                "reviewed_history_id": reviewed_history_id,
            }
        )
        return evidence

    return choreography


def make_managed_phase2_promo_capture_producer(
    *,
    paused_snapshot_probe: Phase2PromoPausedSnapshotProbe,
    seed_proof_probe: Phase2PromoSeedProofProbe,
    visual_primitives: Mapping[str, Phase2PromoVisualPrimitive] | None = None,
    reviewed_history_id: str,
    error_factory: ProducerErrorFactory | None = None,
    hold_seconds: float = 2.5,
    span_driver_factory: Phase2SpanDriverFactory | None = None,
) -> Phase2PromoProducerScaffold:
    """Build the concrete managed-runtime/eight-span producer adapter."""

    return make_phase2_promo_capture_scaffold(
        runtime_probe=make_managed_phase2_runtime_probe(
            paused_snapshot_probe=paused_snapshot_probe,
            seed_proof_probe=seed_proof_probe,
        ),
        choreography=make_eight_span_phase2_choreography(
            visual_primitives,
            reviewed_history_id=reviewed_history_id,
            hold_seconds=hold_seconds,
            span_driver_factory=span_driver_factory,
        ),
        error_factory=error_factory,
        span_session_contract_version=2,
    )


def make_phase2_promo_capture_scaffold(
    *,
    contract: Mapping[str, object] | None = None,
    runtime_probe: RuntimeProbe | None = None,
    choreography: Choreography | None = None,
    error_factory: ProducerErrorFactory | None = None,
    span_session_contract_version: int | None = None,
) -> Phase2PromoProducerScaffold:
    """Build an unregistered scaffold for tests or a future live producer."""

    return Phase2PromoProducerScaffold(
        contract=(
            canonical_phase2_capture_contract()
            if contract is None
            else contract
        ),
        runtime_probe=runtime_probe,
        choreography=choreography,
        error_factory=error_factory,
        span_session_contract_version=span_session_contract_version,
    )


def install_phase2_promo_capture_scaffold(
    registrar: RunnerRegistrar,
    *,
    contract: Mapping[str, object] | None = None,
    runtime_probe: RuntimeProbe | None = None,
    choreography: Choreography | None = None,
    error_factory: ProducerErrorFactory | None = None,
) -> Phase2PromoProducerScaffold:
    """Explicitly register a fully wired scaffold with the acceptance runner.

    Registration is intentionally refused until both real-runtime dependencies
    are supplied.  This keeps the runner's existing *unregistered producer*
    preflight RED intact while the phase-two gameplay implementation is absent.
    The helper accepts the runner's
    ``register_phase2_promo_capture_producer`` callable, so importing this
    module alone has no registration or process side effect.
    """

    if not callable(registrar):
        raise TypeError("registrar must be callable")
    if runtime_probe is None or choreography is None:
        raise Phase2PromoProducerUnavailable(
            "dependencies_unconfigured",
            "install requires both a real runtime probe and choreography",
            evidence={
                "runtime_probe_configured": runtime_probe is not None,
                "choreography_configured": choreography is not None,
            },
        )
    scaffold = make_phase2_promo_capture_scaffold(
        contract=contract,
        runtime_probe=runtime_probe,
        choreography=choreography,
        error_factory=error_factory,
    )
    registrar(scaffold)
    return scaffold


__all__ = [
    "Choreography",
    "PHASE2_PROMO_CAPTURE_CONTRACT_VERSION",
    "PHASE2_PROMO_CAPTURE_MODE",
    "PHASE2_PROMO_CAPTURE_PRODUCER_ID",
    "PHASE2_PROMO_CAPTURE_SPAN_MAP",
    "PHASE2_PROMO_CLEAN_SPANS",
    "Phase2PromoCaptureContext",
    "Phase2PromoProducerContractError",
    "Phase2PromoProducerError",
    "Phase2PromoProducerScaffold",
    "Phase2PromoProducerUnavailable",
    "Phase2PromoPausedSnapshotProbe",
    "Phase2PromoSeedProofProbe",
    "Phase2PromoVisualPrimitive",
    "Phase2SpanDriverFactory",
    "RuntimeProbe",
    "canonical_phase2_capture_contract",
    "install_phase2_promo_capture_scaffold",
    "make_eight_span_phase2_choreography",
    "make_managed_phase2_promo_capture_producer",
    "make_managed_phase2_runtime_probe",
    "make_phase2_promo_capture_scaffold",
    "phase2_promo_producer_typed_error_payload",
]
