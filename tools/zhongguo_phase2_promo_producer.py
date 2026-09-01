"""Dependency-injected hand-off for the ZhongGuo phase-two promo producer.

This module intentionally stops at the boundary between the acceptance runner
and a future *real* gameplay choreography.  It does not launch CK3, invoke
FFmpeg, inspect the desktop, call any recorder lifecycle method, or write an
artifact.  A caller supplies a read-only runtime probe and a choreography
delegate; the scaffold forwards a typed context to those dependencies and
checks the phase-two capture contract on the way back.

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
    return repr(value)


class Phase2PromoProducerError(RuntimeError):
    """A typed RED at the producer hand-off boundary.

    ``reason_code`` is intentionally stable for runner/report consumers while
    ``evidence`` remains a small, JSON-compatible partial record.  No error
    path writes that record; the acceptance runner may decide how to retain it.
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


@dataclass(frozen=True, slots=True)
class Phase2PromoCaptureContext:
    """Immutable parameter bundle passed to injected producer dependencies."""

    stream: object
    artifacts: Path
    recorder: object
    title_navigation_service: object
    tracked_ck3_pid: int
    native_bridge: object
    preflight_bridge_identity: Mapping[str, object]
    contract: Mapping[str, object]


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


ProducerErrorFactory: TypeAlias = Callable[[str], BaseException]
RunnerRegistrar: TypeAlias = Callable[[Callable[..., dict[str, object]]], None]


def _canonical_contract(value: Mapping[str, object]) -> dict[str, object]:
    """Validate and copy a contract without normalizing or filling fields."""

    if not isinstance(value, Mapping):
        raise Phase2PromoProducerContractError(
            "contract_not_mapping",
            "phase-two capture contract must be a mapping",
            evidence={"actual_type": type(value).__name__},
        )
    actual = deepcopy(dict(value))
    expected = canonical_phase2_capture_contract()
    if actual != expected:
        raise Phase2PromoProducerContractError(
            "contract_mismatch",
            "phase-two capture contract differs from the canonical v1 contract",
            evidence={"expected_contract": expected, "actual_contract": actual},
        )
    return actual


def _recorder_contract(recorder: object) -> Mapping[str, object] | None:
    """Read a runner ``PromoRecorder`` contract without touching its lifecycle."""

    value = getattr(recorder, "contract", None)
    if value is None:
        return None
    to_mapping = getattr(value, "to_mapping", None)
    if callable(to_mapping):
        value = to_mapping()
    if not isinstance(value, Mapping):
        return None
    return value


@dataclass(frozen=True, slots=True)
class Phase2PromoProducerScaffold:
    """Strict, side-effect-free adapter around future runtime dependencies.

    The object itself is the callable accepted by
    ``register_phase2_promo_capture_producer``.  It deliberately does not
    implement any CK3 action or visual operation.  Those remain in the
    injected ``runtime_probe`` and ``choreography`` functions.
    """

    contract: Mapping[str, object]
    runtime_probe: RuntimeProbe | None = None
    choreography: Choreography | None = None
    error_factory: ProducerErrorFactory | None = None

    def __post_init__(self) -> None:
        # Store a private-by-convention copy so a caller cannot mutate the
        # contract after construction and silently change the hand-off.
        object.__setattr__(self, "contract", _canonical_contract(self.contract))
        if self.runtime_probe is not None and not callable(self.runtime_probe):
            raise TypeError("runtime_probe must be callable or None")
        if self.choreography is not None and not callable(self.choreography):
            raise TypeError("choreography must be callable or None")
        if self.error_factory is not None and not callable(self.error_factory):
            raise TypeError("error_factory must be callable or None")

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
        except Exception:
            # An error adapter must never hide the original typed RED.
            raise local_error
        if not isinstance(adapted, BaseException):
            raise local_error
        # RunnerError has no structured fields, so attach them opportunistically
        # while retaining its established exception type for the caller.
        for name, value in (
            ("reason_code", local_error.reason_code),
            ("reason", local_error.reason),
            ("code", local_error.code),
            ("result", local_error.result),
            ("evidence", local_error.evidence),
        ):
            try:
                setattr(adapted, name, value)
            except Exception:
                pass
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
        if actual_contract is None or dict(actual_contract) != dict(self.contract):
            self._red(
                "recorder_contract_mismatch",
                "recorder is not bound to the canonical phase-two contract",
                evidence={
                    "expected_contract": deepcopy(dict(self.contract)),
                    "actual_contract": deepcopy(
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
        return Phase2PromoCaptureContext(
            stream=stream,
            artifacts=artifacts,
            recorder=recorder,
            title_navigation_service=title_navigation_service,
            tracked_ck3_pid=tracked_ck3_pid,
            native_bridge=native_bridge,
            preflight_bridge_identity=deepcopy(dict(preflight_bridge_identity)),
            contract=deepcopy(dict(self.contract)),
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
        if evidence["capture_mode"] != PHASE2_PROMO_CAPTURE_MODE:
            self._red(
                "producer_mode_mismatch",
                "choreography returned a non-canonical capture mode",
                evidence={"capture_mode": evidence["capture_mode"]},
                unavailable=False,
            )
        if (
            evidence["capture_contract_version"]
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
            or returned_contract != dict(self.contract)
        ):
            self._red(
                "producer_contract_mismatch",
                "choreography returned a non-canonical capture contract",
                evidence={
                    "expected_contract": deepcopy(dict(self.contract)),
                    "actual_contract": deepcopy(
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


def make_phase2_promo_capture_scaffold(
    *,
    contract: Mapping[str, object] | None = None,
    runtime_probe: RuntimeProbe | None = None,
    choreography: Choreography | None = None,
    error_factory: ProducerErrorFactory | None = None,
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
    "RuntimeProbe",
    "canonical_phase2_capture_contract",
    "install_phase2_promo_capture_scaffold",
    "make_phase2_promo_capture_scaffold",
]
