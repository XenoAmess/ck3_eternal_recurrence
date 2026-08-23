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
from .marriage_contract import (
    ARRANGE_MARRIAGE_CAPABILITY,
    QUERY_ARRANGE_MARRIAGE_CHOICES_STEP,
    arrange_marriage_step,
    normalize_arrange_marriage_choices,
    parse_arrange_marriage_step,
)
from .settlement_contract import (
    ONE_LIFE_SETTLEMENT_CAPABILITY,
    normalize_fixed_score,
    normalize_one_life_settlement,
    parse_completed_tutorial_lessons,
    settlement_ready_for_episode,
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
    "ARRANGE_MARRIAGE_CAPABILITY",
    "EVENT_OPTION_STEP_PREFIX",
    "ONE_LIFE_SETTLEMENT_CAPABILITY",
    "GameplayBridgeDriver",
    "HybridGameplayDriver",
    "ConfiguredHybridFallbackDriver",
    "DEFAULT_PIPE_NAME",
    "MinimizedRejectingVisualDriver",
    "NativeHeadlessGameplayDriver",
    "NativeNamedPipeServer",
    "NativeProtocolState",
    "QUERY_DECLARABLE_WARS_STEP",
    "QUERY_ARRANGE_MARRIAGE_CHOICES_STEP",
    "UnsupportedStepError",
    "choose_event_option_number",
    "arrange_marriage_step",
    "declare_war_step",
    "event_option_step",
    "load_data_mod_driver",
    "normalize_active_event",
    "normalize_fixed_score",
    "normalize_one_life_settlement",
    "normalize_declarable_wars",
    "normalize_arrange_marriage_choices",
    "parse_declare_war_step",
    "parse_arrange_marriage_step",
    "parse_event_option_step",
    "parse_completed_tutorial_lessons",
    "selected_pipe_name",
    "settlement_ready_for_episode",
]
