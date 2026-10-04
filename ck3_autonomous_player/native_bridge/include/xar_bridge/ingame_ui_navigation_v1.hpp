#pragma once

#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/zhongguo_scoreboard_state_v1.hpp"
#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_11906 {

inline constexpr std::string_view kIngameUiNavigationV1Step = "navigate-ingame-ui-v1";
inline constexpr std::string_view kIngameUiNavigationV1Capability = "game.command.navigate-ingame-ui-v1";
inline constexpr std::string_view kIngameUiWindowQueryV1Step = "query-ingame-ui-window-v1";
inline constexpr std::string_view kIngameUiWindowQueryV1Capability = "game.command.query-ingame-ui-window-v1";

// Exact 1.19.0.6 EXE registered-GUI paths. The binding never accepts an RVA,
// native pointer, widget name, coordinates, or view enum from the caller.
inline constexpr std::uintptr_t kUiDefaultOnCharacterClickRvaV1 = 0xA04530;
inline constexpr std::uintptr_t kUiSelectUnitRvaV1 = 0xA7F050;
inline constexpr std::uintptr_t kUiOpenViewRvaV1 = 0xA79200;
inline constexpr std::uintptr_t kUiOpenViewDataRvaV1 = 0xA79700;
inline constexpr std::uintptr_t kUiIdAnyTypeGetterRvaV1 = 0x998130;

enum class IngameUiWindowKindV1 : std::uint32_t { character=0, army=1, combat=2, knights=3 };
enum class IngameUiOperationV1 : std::uint32_t { query=0, open_character=1, select_army=2, open_combat=3, open_knights=4,
  hover_left_knights=5, hover_right_knights=6, fit_combat_window=7,
  hover_army_tooltip=8, leave_army_tooltip=9 };
struct UiFloat2V1 { float x=0, y=0; };
struct UiRectV1 { float x=0, y=0, width=0, height=0; };
struct CombatUiGeometryV1 {
  bool available=false;
  bool stock_margin_source_verified=false;
  bool content_inside_viewport=false;
  bool fit_required=false;
  std::uint32_t combat_id=0;
  std::uint32_t widget_count=0;
  UiRectV1 viewport{},window_rect{},content_union{};
  UiFloat2V1 proposed_translation{};
  std::string unavailable_reason;
};
struct IngameUiRequestV1 {
  IngameUiOperationV1 operation = IngameUiOperationV1::query;
  IngameUiWindowKindV1 window_kind = IngameUiWindowKindV1::character;
  std::uint32_t subject_id = 0;
  // Fixed semantic fields only; complete child paths stay provider-private.
  std::string army_tooltip_kind;
  std::string army_tooltip_receipt;
  // Assigned by the bridge after public request parsing, never caller input.
  std::uint64_t connection_generation = 0;
  std::uint64_t native_revision = 0;
};
struct IngameUiGuiOwnerBindingV1 {
  void *context = nullptr;
  void *owner = nullptr;
  friend bool operator==(const IngameUiGuiOwnerBindingV1 &,
                         const IngameUiGuiOwnerBindingV1 &) = default;
};
// Diagnostic raw observations only. A registered hidden receiver does not
// imply a visible modal; no flags are read from caller-supplied game pointers.
struct IngameUiModalReceiverV1 {
  std::uintptr_t address = 0;
  std::uint8_t flags_d0 = 0;
};
struct IngameUiModalAdmissionV1 {
  bool attempted = false;
  bool header_read = false;
  bool receivers_verified = false;
  std::int32_t receiver_count = 0;
  std::uintptr_t vector_address = 0;
  std::uint32_t effective_visible_count = 0;
  std::vector<IngameUiModalReceiverV1> receivers;
  std::string unavailable_reason;
};
// Application-event ownership comes from the original SDL/TLS mailbox proof.
// The global RNG wrapper has its own scoped subsystem owner and is diagnostic.
inline bool IsIngameUiPausedOwnerStampV1(
    const MainThreadQueryMailboxV1 &mailbox,
    const MainThreadExecutionStampV1 &stamp,
    std::uint32_t executing_thread_id) noexcept {
  return stamp.pump_epoch != 0 && stamp.thread_id != 0 &&
      executing_thread_id == stamp.thread_id &&
      mailbox.owner_thread_id.load(std::memory_order_acquire) == stamp.thread_id &&
      stamp.tls_initialized_flag_address != 0 && stamp.tls_initialized == 1 &&
      stamp.tls_context != 0 && stamp.tls_main_thread_marker == 1 &&
      stamp.paused && stamp.jomini_state != 0 && stamp.game_state != 0 &&
      mailbox.owner_verified_pump_epochs.load(std::memory_order_acquire) >=
          kMainThreadQueryMinimumOwnerVerifiedPumpEpochs &&
      mailbox.paused_owner_verified_pump_epochs.load(std::memory_order_acquire) >=
          kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs;
}
// Exact .3 registered SelectUnit path. Current migration is Army-only.
inline constexpr std::uintptr_t kUiSelectUnitRva12003V1 = 0xAF9000;
inline constexpr std::uintptr_t kUiArmyWindowTypeDescriptor12003V1 = 0x57769C0;
inline constexpr std::uintptr_t kUiArmyStorage12003V1 = 0x5D1DE48;
inline constexpr std::uintptr_t kUiUnitStorage12003V1 = 0x5D1E380;
inline constexpr std::size_t kUiArmyWindowSubjectOffset12003V1 = 0xC8;
// Original B0F1E0 returns handler+0x98+view*8, so view6 is handler+0xC8.
inline constexpr std::size_t kUiArmyWindowHandlerSlot12003V1 = 0xC8;
// Original CArmyWindow::OnInit 1345EB0 retains the named widget at +0x60.
inline constexpr std::size_t kUiArmyWindowGuiRootOffset12003V1 = 0x60;
bool IsIngameUiRequestSupportedV1(GuiAbiRevisionV1 revision,
    const IngameUiRequestV1 &request) noexcept;
struct ArmyTooltipObservationV1 {
  bool requested=false;
  bool source_bound=false,hover_matches_source=false,active_stack_read=false;
  bool active_root_available=false,cache_bytes_observed=false,leave_observed=false;
  bool receipt_bound=false,later_owner_epoch_available=false;
  std::string semantic_kind,receipt_id,source_child_path,tooltip_text_child_path;
  std::uint64_t action_owner_epoch=0,later_owner_epoch=0;
  std::int32_t active_count=-1,active_top_index=-1,active_top_locked=-1;
  std::string observed_text,observed_text_sha256;
  std::string status="unavailable",unavailable_reason;
};
struct IngameUiResultV1 {
  GuiAbiRevisionV1 gui_abi_revision = GuiAbiRevisionV1::legacy11906;
  bool available = false;
  bool dispatch_invoked = false;
  bool verification_pending = false;
  bool window_exists = false;
  bool effective_visible = false;
  bool enabled = false;
  bool subject_id_available = false;
  std::uint32_t current_subject_id = 0;
  std::uint32_t native_army_id = 0;
  std::uint32_t owner_character_id = 0;
  bool owner_character_id_available = false;
  std::int32_t date_raw = 0;
  bool paused = false;
  std::int32_t played_character_id = -1;
  std::uint64_t pump_epoch = 0;
  std::uint32_t thread_id = 0;
  bool application_owner_thread_verified = false;
  bool gui_owner_binding_verified = false;
  std::uintptr_t gui_context_address = 0;
  std::uintptr_t gui_owner_address = 0;
  std::uint32_t rng_owner_thread_id = 0;
  IngameUiModalAdmissionV1 modal_admission{};
  bool combat_knights_read_available = false;
  std::int32_t left_knight_count = -1;
  std::int32_t right_knight_count = -1;
  std::string left_knight_breakdown;
  std::string right_knight_breakdown;
  bool hover_state_available = false;
  std::string hovered_widget_name;
  std::string hovered_ui_side;
  std::uint32_t hovered_combat_id = 0;
  CombatUiGeometryV1 combat_geometry{};
  NamedGuiTreeInspectionV1 tree{};
  ArmyTooltipObservationV1 army_tooltip{};
  std::string status = "unavailable";
  std::string unavailable_reason;
};

// Only ExecuteFrontendGuiRouteMailboxV1 calls this, after owner/TLS/epoch and
// fresh paused-map snapshot admission. Direct use is not a public bridge slot.
bool ExecuteIngameUiNavigationV1(
    const ZhongguoScoreboardNativeEnvironmentV1 &environment,
    const IngameUiRequestV1 &request, const game::Snapshot &snapshot,
    const MainThreadExecutionStampV1 &stamp,
    const IngameUiGuiOwnerBindingV1 &gui_binding, IngameUiResultV1 &output) noexcept;
// Two fresh reads of the original GUI singleton chain; caller-supplied native
// pointers and fixture function overrides are never admitted in production.
bool ReadIngameUiGuiOwnerBindingV1(
    const ZhongguoScoreboardNativeEnvironmentV1 &environment,
    IngameUiGuiOwnerBindingV1 &output) noexcept;

bool ParseIngameUiRequestV1(std::string_view json, bool query,
                          IngameUiRequestV1 &output) noexcept;
bool ValidateIngameUiRequestV1(const IngameUiRequestV1 &request) noexcept;
// Pure bounded fit policy; production geometry comes only from original GUI
// getters. A successful policy result is not a pixels/full-panel assertion.
bool ComputeCombatUiFitTranslationV1(const UiRectV1 &viewport,
    const UiRectV1 &content,UiFloat2V1 &translation) noexcept;
std::string_view IngameUiWindowNameV1(IngameUiWindowKindV1 kind) noexcept;
std::string SerializeIngameUiResultV1(const IngameUiRequestV1 &request,
                                    const IngameUiResultV1 &result,
                                    std::uint64_t native_revision);
} // namespace xar::ck3_11906
