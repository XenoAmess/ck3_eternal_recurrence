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
from .declaration_contract import (
    DECLARE_WAR_CAPABILITY,
    QUERY_DECLARABLE_WARS_STEP,
    declare_war_step,
    normalize_declarable_wars,
    parse_declare_war_step,
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
    "DECLARE_WAR_CAPABILITY",
    "EVENT_OPTION_STEP_PREFIX",
    "GameplayBridgeDriver",
    "HybridGameplayDriver",
    "ConfiguredHybridFallbackDriver",
    "DEFAULT_PIPE_NAME",
    "MinimizedRejectingVisualDriver",
    "NativeHeadlessGameplayDriver",
    "NativeNamedPipeServer",
    "NativeProtocolState",
    "QUERY_DECLARABLE_WARS_STEP",
    "UnsupportedStepError",
    "choose_event_option_number",
    "declare_war_step",
    "event_option_step",
    "load_data_mod_driver",
    "normalize_active_event",
    "normalize_declarable_wars",
    "parse_declare_war_step",
    "parse_event_option_step",
    "selected_pipe_name",
]
