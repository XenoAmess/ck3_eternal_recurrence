#pragma once

#include "xar_bridge/ck3_12002.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace xar::ck3_12002 {

inline constexpr std::size_t kSwayTerminationCapacity12002 = 128;
inline constexpr std::array<std::uintptr_t, 3> kSwayTerminationSlotRvas12002{
    0x476EB78, 0x4852270, 0x4852C28};
inline constexpr std::array<std::uintptr_t, 3> kSwayTerminationExecuteRvas12002{
    0x299C340, 0x2D11B50, 0x2D11AF0};

// The exact command body consumes only RCX before replacing RDX itself.
using SwayTerminationNativeCommand12002 = void (*)(const void *secondary_this);
using SwayTerminationNativeEffect12002 = void (*)(const void *effect,
                                                const void *effect_context);
enum class SwayTerminationSourceClass12002 {
  none,
  end_scheme_command_execute,
  authored_end_scheme_false_execute,
  authored_end_scheme_true_execute,
};
enum class SwayTerminationCaptureResult12002 { ignored, unavailable, captured };

struct SwayTerminationBindings12002 {
  bool enabled = false;
  std::uintptr_t image_base = 0;
  CoreBindings core{};
};
SwayTerminationBindings12002 BindSwayTerminationImage12002(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

// Caller-owned copies. No native object, effect, context or storage pointer is
// retained. Source execution and terminal observation have separate flags.
struct SwayTerminationSource12002 {
  SwayTerminationSourceClass12002 source_class = SwayTerminationSourceClass12002::none;
  std::int32_t date_raw = 0;
  std::uint32_t actor_character_id = 0xFFFFFFFFu;
  std::uint32_t target_character_id = 0xFFFFFFFFu;
  std::uint32_t scheme_id = 0xFFFFFFFFu;
  std::uint16_t input_root_scope_kind = 0;
  std::int32_t pre_status = 0;
  std::uint32_t pre_owner = 0xFFFFFFFFu;
  bool executing_source_observed = false;
  bool post_read_succeeded = false;
  bool post_instance_present = false;
  bool post_storage_slot_reused = false;
  bool post_exact_instance_join_ready = false;
  bool post_status_observed = false;
  std::int32_t post_status = 0;
  std::uint32_t post_owner = 0xFFFFFFFFu;
  bool native_terminal_state_observed = false;
  bool native_terminal_transition_observed = false;
};
SwayTerminationCaptureResult12002 CaptureSwayTerminationBefore12002(
    const SwayTerminationBindings12002 &bindings,
    SwayTerminationSourceClass12002 source_class, const void *native_self,
    const void *effect_context, SwayTerminationSource12002 &output) noexcept;
bool CaptureSwayTerminationAfter12002(const SwayTerminationBindings12002 &bindings,
                                    SwayTerminationSource12002 &source) noexcept;

struct SwayTerminationRecord12002 {
  std::uint64_t sequence = 0;
  SwayTerminationSource12002 source;
};
struct SwayTerminationQuery12002 {
  std::uint32_t actor_character_id = 0xFFFFFFFFu;
  std::uint32_t target_character_id = 0xFFFFFFFFu;
  std::uint32_t scheme_id = 0xFFFFFFFFu;
  std::uint64_t after_sequence = 0;
};
struct SwayTerminationQueryResult12002 {
  bool available = false;
  std::string unavailable_reason;
  SwayTerminationQuery12002 request;
  bool observer_attached = false;
  std::uint64_t earliest_sequence = 0;
  std::uint64_t latest_sequence = 0;
  bool retention_gap = false;
  std::vector<SwayTerminationRecord12002> records;
};
// Native entry and query belong to the same owning-thread pump. Records cover
// this observer session; constructing a recorder doesn't grant availability.
class SwayTerminationRecorder12002 {
public:
  void SetObserverAttached(bool attached) noexcept;
  bool ObserverAttached() const noexcept;
  bool Append(const SwayTerminationSource12002 &source) noexcept;
  bool Query(const SwayTerminationQuery12002 &request,
             SwayTerminationQueryResult12002 &output) const noexcept;
private:
  bool attached_ = false;
  std::uint64_t next_sequence_ = 1;
  std::size_t first_ = 0;
  std::size_t count_ = 0;
  std::array<SwayTerminationRecord12002, kSwayTerminationCapacity12002> records_{};
};
const char *SwayTerminationSourceKey12002(SwayTerminationSourceClass12002 source) noexcept;
// Bare JSON body for the coordinator-owned transport serializer to embed.
std::string SerializeSwayCompletionTermination12002(
    const SwayTerminationQueryResult12002 &result);

struct SwayTerminationInstall12002 {
  SwayTerminationBindings12002 bindings{};
  SwayTerminationRecorder12002 *recorder = nullptr;
  std::array<std::uintptr_t *, 3> slots{};
  std::array<std::uintptr_t, 3> originals{};
  std::array<bool, 3> patched{};
  bool attached = false;
  bool fixture_slots = false;
  const char *unavailable_reason = "sway_termination_observer_not_installed";
};
// Exactly three existing vtable function pointers; no generated code detour.
// The root pins the DLL and owns state/originals through process lifetime.
bool InstallSwayCompletionTermination12002(
    std::uintptr_t image_base, std::string_view executable_sha256,
    SwayTerminationRecorder12002 &recorder,
    SwayTerminationInstall12002 &state) noexcept;
bool InstallSwayCompletionTerminationFixture12002(
    const SwayTerminationBindings12002 &bindings,
    const std::array<std::uintptr_t *, 3> &slots,
    const std::array<std::uintptr_t, 3> &expected_originals,
    SwayTerminationRecorder12002 &recorder,
    SwayTerminationInstall12002 &state) noexcept;
bool UninstallSwayCompletionTermination12002(SwayTerminationInstall12002 &state) noexcept;

} // namespace xar::ck3_12002
