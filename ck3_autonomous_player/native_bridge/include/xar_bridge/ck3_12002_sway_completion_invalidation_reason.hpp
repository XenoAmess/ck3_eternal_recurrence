#pragma once

#include "xar_bridge/ck3_12002.hpp"

#include <array>
#include <cstdint>
#include <string>
#include <vector>

namespace xar::ck3_12002 {
struct SwayInvalidationToken12002 {
  std::uint16_t kind = 0;
  std::uint16_t subtype = 0;
  std::uint32_t reserved = 0;
  std::uint64_t payload = 0;
};
static_assert(sizeof(SwayInvalidationToken12002) == 0x10);
using SwayInvalidationNativeLookup12002 = SwayInvalidationToken12002 *(*)(
    const void *environment, SwayInvalidationToken12002 *out, std::int32_t identifier);
using SwayInvalidationGlobalKey12002 = const std::string *(*)(std::int32_t key);
struct SwayInvalidationReasonBindings12002 {
  bool enabled = false;
  std::uintptr_t image_base = 0;
  CoreBindings core{};
  SwayInvalidationNativeLookup12002 lookup = nullptr;
  SwayInvalidationGlobalKey12002 global_key = nullptr;
  const std::int32_t *scheme_identifier = nullptr;
  const std::int32_t *owner_identifier = nullptr;
  const std::int32_t *target_identifier = nullptr;
};
SwayInvalidationReasonBindings12002 BindSwayInvalidationReasonImage12002(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;
enum class SwayInvalidationNotificationBranch12002 {
  none, target_dead_notification_source, out_of_range_notification_source,
  opaque_existing_stock_notification_source,
};
enum class SwayInvalidationReasonCapture12002 { ignored, unavailable, captured };
struct SwayInvalidationReasonSource12002 {
  SwayInvalidationNotificationBranch12002 branch = SwayInvalidationNotificationBranch12002::none;
  std::int32_t date_raw = 0;
  std::uint32_t actor_character_id = 0xFFFFFFFFu;
  std::uint32_t target_character_id = 0xFFFFFFFFu;
  std::uint32_t scheme_id = 0xFFFFFFFFu;
  SwayInvalidationToken12002 root;
  SwayInvalidationToken12002 scheme;
  SwayInvalidationToken12002 owner;
  SwayInvalidationToken12002 target;
  bool selected_notification_branch_observed = false;
};
// Called synchronously from the one already installed native notification
// Execute wrapper. This reader installs no pointer hook and retains no pointers.
SwayInvalidationReasonCapture12002 CaptureSwayInvalidationReason12002(
    const SwayInvalidationReasonBindings12002 &bindings, const void *effect,
    const void *effect_context, SwayInvalidationReasonSource12002 &output) noexcept;
struct SwayInvalidationReasonRecord12002 {
  std::uint64_t sequence = 0;
  SwayInvalidationReasonSource12002 source;
};
struct SwayInvalidationReasonQuery12002 {
  std::uint32_t actor_character_id = 0xFFFFFFFFu;
  std::uint32_t target_character_id = 0xFFFFFFFFu;
  std::uint32_t scheme_id = 0xFFFFFFFFu;
  std::uint64_t after_sequence = 0;
};
struct SwayInvalidationReasonQueryResult12002 {
  bool available = false;
  std::string unavailable_reason;
  SwayInvalidationReasonQuery12002 request;
  bool observer_attached = false;
  std::uint64_t earliest_sequence = 0;
  std::uint64_t latest_sequence = 0;
  bool retention_gap = false;
  std::vector<SwayInvalidationReasonRecord12002> records;
};
class SwayInvalidationReasonRecorder12002 {
public:
  void SetObserverAttached(bool attached) noexcept;
  bool ObserverAttached() const noexcept;
  bool Append(const SwayInvalidationReasonSource12002 &source) noexcept;
  bool Query(const SwayInvalidationReasonQuery12002 &request,
             SwayInvalidationReasonQueryResult12002 &result) const noexcept;
private:
  bool attached_ = false;
  std::uint64_t next_sequence_ = 1;
  std::size_t first_ = 0;
  std::size_t count_ = 0;
  std::array<SwayInvalidationReasonRecord12002, 128> records_{};
};
SwayInvalidationReasonCapture12002 CaptureAndRecordSwayInvalidationReason12002(
    const SwayInvalidationReasonBindings12002 &bindings, const void *effect,
    const void *effect_context, SwayInvalidationReasonRecorder12002 &recorder) noexcept;
const char *SwayInvalidationNotificationBranchKey12002(SwayInvalidationNotificationBranch12002 branch) noexcept;
const char *SwayInvalidationAuthoredReasonKey12002(SwayInvalidationNotificationBranch12002 branch) noexcept;
std::string SerializeSwayInvalidationReason12002(const SwayInvalidationReasonQueryResult12002 &result);
} // namespace xar::ck3_12002
