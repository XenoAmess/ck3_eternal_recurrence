#pragma once
#include "xar_bridge/ck3_1210_core_frame_v1.hpp"
#include "xar_bridge/ck3_1210_commands.hpp"
#include "xar_bridge/ck3_1210_application_exit_v1.hpp"

namespace xar::ck3_1210 {
inline constexpr char kCoreControlSchemaV1[] = "ck3_1210_core_clock_control_v1";
inline constexpr char kCoreControlResultSchemaV1[] = "ck3_1210_core_clock_control_result_v1";
inline constexpr char kCoreControlCapabilityV1[] = "game.command.core-clock-control.v1";
inline constexpr char kApplicationExitSchemaV1[] = "ck3_1210_application_exit_v1";
inline constexpr char kApplicationExitResultSchemaV1[] = "ck3_1210_application_exit_result_v1";
inline constexpr char kApplicationExitCapabilityV1[] = "game.command.normal-exit-application-v1";
inline constexpr char kApplicationExitStepV1[] = "normal-exit-application-v1";
inline constexpr char kCoreBackendV1[] = "ck3-1.21.0-native-headless-main-thread";
enum class CoreControlOperationV1 { unavailable, pause, resume, speed, save, application_exit };
struct CoreControlRequestV1 {
  CoreControlOperationV1 operation = CoreControlOperationV1::unavailable;
  std::string_view step;
  CoreSnapshotPrefix expected{};
  std::int32_t public_speed = 0;
  std::uint64_t deadline_unix_ms = 0;
};
enum class CoreControlStatusV1 {
  unavailable, expired, stale, requires_map, requires_paused,
  already_satisfied, rejected, submitted, indeterminate, exit_requested, exit_already_requested, exit_claim_consumed
};
struct CoreControlResultV1 {
  CoreControlStatusV1 status = CoreControlStatusV1::unavailable;
  bool effect_attempted = false;
  CoreSnapshotPrefix observed{};
};
using CoreControlClockV1 = std::uint64_t (*)(void *) noexcept;
struct CoreControlContextV1 {
  const game::GameAdapter *game = nullptr;
  CoreBindings core{};
  CommandBindings commands{};
  ApplicationExitBindingsV1 application_exit{};
  ApplicationExitSessionV1 *application_exit_session=nullptr;
  CoreControlRequestV1 request{};
  ck3_11906::MainThreadQueryMailboxV1 *mailbox = nullptr;
  ck3_11906::MainThreadQueryTicketV1 ticket{};
  CoreControlResultV1 result{};
  CoreControlClockV1 wall_clock = nullptr, monotonic_clock = nullptr;
  void *clock_context = nullptr;
  std::uint64_t monotonic_deadline_ms = 0;
};
// Strict version-specific scalar object grammar. No full Snapshot/Permit,
// connection authority, lease, or observation timestamp is fabricated here.
bool ParseCoreControlRequestV1(std::string_view payload,
    CoreControlRequestV1 &output) noexcept;
bool EqualCorePrefixV1(const CoreSnapshotPrefix &, const CoreSnapshotPrefix &) noexcept;
void ArmCoreControlDeadlineV1(CoreControlContextV1 &) noexcept;
bool ExecuteCoreControlMailboxV1(void *,
    const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
std::string SerializeCoreControlCommandResultV1(std::string_view request_id,
    std::string_view step, const CoreControlResultV1 &result);
} // namespace xar::ck3_1210
