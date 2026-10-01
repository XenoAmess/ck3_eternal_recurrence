#pragma once

#include "xar_bridge/ck3_12002_event_window_context.hpp"

#include <array>
#include <cstdint>
#include <string>
#include <vector>

namespace xar::ck3_12002 {

inline constexpr std::size_t kSwayExecutionRecordCapacity12002 = 128;
inline constexpr std::uintptr_t kSwayExecutionMessageVtableRva12002 = 0x4837280;
inline constexpr std::uintptr_t kSwayExecutionToastVtableRva12002 = 0x4837428;
inline constexpr std::uintptr_t kSwayExecutionPopupVtableRva12002 = 0x4837360;
inline constexpr std::uintptr_t kSwayExecutionTitleWrapperVtableRva12002 = 0x48BD0B0;
inline constexpr std::uintptr_t kSwayExecutionScalarLocalizationVtableRva12002 = 0x4929F08;
inline constexpr std::uintptr_t kSwayExecutionGlobalCommandKeyGetterRva12002 = 0x3F4F900;

// Effect+8 with Effect+C == 0 belongs to the global command-key domain.
// Named scope and authored type identifiers retain their separate registry.
using SwayExecutionGlobalCommandKeyGetter12002 =
    const std::string *(*)(std::int32_t command_key_id);

enum class SwayExecutionSourceBranch12002 {
  none,
  hidden_phase_success_source,
  hidden_phase_failure_source,
};
enum class SwayExecutionCaptureResult12002 {
  ignored,
  captured,
  unavailable,
};

struct SwayExecutionScopeToken12002 {
  std::uint16_t type = 0;
  std::uint16_t subtype = 0;
  std::uint32_t reserved = 0;
  std::uint64_t payload = 0;
  friend bool operator==(const SwayExecutionScopeToken12002 &,
                         const SwayExecutionScopeToken12002 &) = default;
};
static_assert(sizeof(SwayExecutionScopeToken12002) == 0x10);
static_assert(offsetof(SwayExecutionScopeToken12002, payload) == 0x08);

struct SwayExecutionBindings12002 {
  bool enabled = false;
  std::uintptr_t image_base = 0;
  CoreBindings core;
  SwayExecutionGlobalCommandKeyGetter12002 get_global_command_key = nullptr;
  EventGetRegistry get_script_identifier_table = nullptr;
  EventResolveIdentifierName resolve_script_identifier_name = nullptr;
};

SwayExecutionBindings12002 BindSwayExecutionImage12002(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

// All values are copied at native Execute entry. No engine pointer survives.
// A captured source is an executing hidden outcome branch, not an observed
// message enqueue, material effect, or terminal state.
struct SwayExecutionSource12002 {
  SwayExecutionSourceBranch12002 branch = SwayExecutionSourceBranch12002::none;
  std::string unavailable_reason;
  std::int32_t date_raw = 0;
  std::uint32_t actor_character_id = 0xFFFFFFFFu;
  std::uint32_t target_character_id = 0xFFFFFFFFu;
  std::uint32_t scheme_id = 0xFFFFFFFFu;
  SwayExecutionScopeToken12002 root;
  SwayExecutionScopeToken12002 owner;
  SwayExecutionScopeToken12002 target;
  SwayExecutionScopeToken12002 scheme;
  friend bool operator==(const SwayExecutionSource12002 &,
                         const SwayExecutionSource12002 &) = default;
};

// Called synchronously at the real message-effect Execute entry, on its owning
// thread. RCX supplies effect; RDX supplies EffectContext. A context can be
// unpaused: natural effects execute while the simulation advances.
SwayExecutionCaptureResult12002 CaptureSwayCompletionExecution12002(
    const SwayExecutionBindings12002 &bindings, const void *effect,
    const void *effect_context, SwayExecutionSource12002 &output) noexcept;

struct SwayExecutionRecord12002 {
  std::uint64_t sequence = 0;
  SwayExecutionSource12002 source;
};
struct SwayExecutionQuery12002 {
  std::uint32_t actor_character_id = 0xFFFFFFFFu;
  std::uint32_t target_character_id = 0xFFFFFFFFu;
  std::uint32_t scheme_id = 0xFFFFFFFFu;
  std::uint64_t after_sequence = 0;
};
struct SwayExecutionQueryResult12002 {
  bool available = false;
  std::string unavailable_reason;
  SwayExecutionQuery12002 request;
  bool observer_attached = false;
  std::uint64_t earliest_sequence = 0;
  std::uint64_t latest_sequence = 0;
  bool retention_gap = false;
  std::vector<SwayExecutionRecord12002> records;
};

// Current observer session only. Entry capture and query run on the same owner
// thread. The root installer must set attached only after the real observation
// entry is installed; constructing this recorder does not grant availability.
class SwayExecutionRecorder12002 {
public:
  void SetObserverAttached(bool attached) noexcept;
  bool ObserverAttached() const noexcept;
  bool Append(const SwayExecutionSource12002 &source) noexcept;
  bool Query(const SwayExecutionQuery12002 &request,
             SwayExecutionQueryResult12002 &output) const noexcept;
private:
  bool attached_ = false;
  std::uint64_t next_sequence_ = 1;
  std::size_t first_ = 0;
  std::size_t count_ = 0;
  std::array<SwayExecutionRecord12002, kSwayExecutionRecordCapacity12002> records_{};
};

SwayExecutionCaptureResult12002 CaptureAndRecordSwayCompletionExecution12002(
    const SwayExecutionBindings12002 &bindings, const void *effect,
    const void *effect_context, SwayExecutionRecorder12002 &recorder) noexcept;

const char *SwayExecutionBranchKey12002(SwayExecutionSourceBranch12002 branch) noexcept;
// A real copied-record query wire, with independent false material/terminal
// flags. The existing completion mailbox can embed this object unchanged.
std::string SerializeSwayCompletionExecution12002(
    const SwayExecutionQueryResult12002 &result);

} // namespace xar::ck3_12002
