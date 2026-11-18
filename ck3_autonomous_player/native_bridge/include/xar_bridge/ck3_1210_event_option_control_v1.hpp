#pragma once
#include "xar_bridge/ck3_1210_event_options_v1.hpp"
#include "xar_bridge/ck3_1210_core_control_v1.hpp"
#include "xar_bridge/game_adapter.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include <string>

namespace xar::ck3_1210 {
inline constexpr char kEventOptionClaimSchemaV1[]="ck3_1210_event_option_control_v1";
inline constexpr char kEventOptionResultSchemaV1[]="ck3_1210_event_option_control_result_v1";
inline constexpr char kEventOptionsQueryStepV1[]="query-current-event-options-v1";
inline constexpr char kEventOptionsQueryCapabilityV1[]="game.query.current-event-options.v1";
inline constexpr char kEventOptionsSelectCapabilityV1[]="game.command.select-event-option-N";
struct EventOptionRequestV1 {
  std::string_view step{};
  std::uint64_t native_revision=0,deadline_unix_ms=0;
  std::int32_t event_instance_id=-1,native_option_index=-1;
  bool select=false;
};
enum class EventOptionStatusV1 { unavailable,available,submitted,expired,stale_full_snapshot,
    no_active_event,event_mismatch,option_missing,option_disabled,rejected,indeterminate };
struct EventOptionResultV1 {
  EventOptionStatusV1 status=EventOptionStatusV1::unavailable;
  bool application_main_observed=false,full_snapshot_before_verified=false,effect_attempted=false;
  EventOptionsObservationV1 observation{};
  std::string_view unavailable_reason="event_option_control_unavailable";
};
using EventOptionClockV1=std::uint64_t (*)(void *) noexcept;
struct EventOptionControlContextV1 {
  const game::GameAdapter *game=nullptr,*native_full_adapter=nullptr;
  const game::Snapshot *expected_full_snapshot=nullptr;
  ck3_11906::MainThreadQueryMailboxV1 *mailbox=nullptr;
  ck3_11906::MainThreadQueryTicketV1 ticket{};
  EventOptionsBindingsV1 bindings{};
  CommandBindings commands{};
  EventOptionRequestV1 request{};
  EventOptionResultV1 result{};
  std::uint64_t monotonic_deadline_ms=0;
  EventOptionClockV1 wall_clock=nullptr,monotonic_clock=nullptr;
  void *clock_context=nullptr;
};
bool ParseEventOptionRequestV1(std::string_view payload,EventOptionRequestV1 &) noexcept;
void ArmEventOptionDeadlineV1(EventOptionControlContextV1 &) noexcept;
bool ExecuteEventOptionControlMailboxV1(void *,const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
std::string SerializeEventOptionCommandResultV1(std::string_view request_id,
    const EventOptionRequestV1 &,const EventOptionResultV1 &);
} // namespace xar::ck3_1210
