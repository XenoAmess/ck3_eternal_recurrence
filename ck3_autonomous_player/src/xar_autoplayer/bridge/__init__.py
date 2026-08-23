"""Backend-neutral CK3 gameplay bridge primitives."""

from .driver import (
    BridgeGameplayStepExecutor,
    BridgeUnavailableError,
    CallbackGameplayDriver,
    DevelopmentReportDriver,
    GameplayBridgeDriver,
    HybridGameplayDriver,
    UnsupportedStepError,
)
from .event_contract import (
    EVENT_OPTION_STEP_PREFIX,
    choose_event_option_number,
    event_option_step,
    normalize_active_event,
    parse_event_option_step,
)
from .mod_driver import DataModGameplayDriver, load_data_mod_driver
from .native_driver import (
    ConfiguredHybridFallbackDriver,
    DEFAULT_PIPE_NAME,
    MinimizedRejectingVisualDriver,
    NativeHeadlessGameplayDriver,
    NativeNamedPipeServer,
    NativeProtocolState,
    selected_pipe_name,
)
from .session_driver import DevelopmentSessionDriver

__all__ = [
    "BridgeUnavailableError",
    "BridgeGameplayStepExecutor",
    "CallbackGameplayDriver",
    "DataModGameplayDriver",
    "DevelopmentReportDriver",
    "DevelopmentSessionDriver",
    "EVENT_OPTION_STEP_PREFIX",
    "GameplayBridgeDriver",
    "HybridGameplayDriver",
    "ConfiguredHybridFallbackDriver",
    "DEFAULT_PIPE_NAME",
    "MinimizedRejectingVisualDriver",
    "NativeHeadlessGameplayDriver",
    "NativeNamedPipeServer",
    "NativeProtocolState",
    "UnsupportedStepError",
    "choose_event_option_number",
    "event_option_step",
    "load_data_mod_driver",
    "normalize_active_event",
    "parse_event_option_step",
    "selected_pipe_name",
]
