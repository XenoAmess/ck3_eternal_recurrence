#pragma once
#include "xar_bridge/ck3_1210_gui_control_v1.hpp"
#include "xar_bridge/ck3_1210_toast_objects_v1.hpp"

namespace xar::ck3_1210 {
inline constexpr char kToastQueryStepV1[]="query-current-interface-toast-v1";
inline constexpr char kToastQueryCapabilityV1[]="game.query.current-interface-toast.v1";
inline constexpr char kToastQueryRootV1[]="toast_container_widget";
inline constexpr char kToastQueryResultSchemaV1[]="ck3_1210_current_interface_toast_result_v1";
struct ToastQueryOwnerIdentityV1 {
  std::uint64_t connection_generation=0;
  std::uint32_t thread_id=0,tls_initialized=0,tls_main_thread_marker=0;
  std::uintptr_t tls_context=0,game_state=0,jomini_state=0;
  std::int32_t date_raw=0,played_character_id=-1;
  bool operator==(const ToastQueryOwnerIdentityV1 &) const=default;
};
struct ToastQueryProviderV1 {
  bool owner_bound=false;
  ToastQueryOwnerIdentityV1 owner{};
  ToastObjectProviderV1 objects{};
};
struct ToastQueryResultV1 {
  bool available=false,application_main_observed=false,full_snapshot_before_verified=false;
  bool full_snapshot_after_verified=false,source_abi_pins_verified=false;
  std::uint64_t connection_generation=0,query_sequence=0;
  std::uint32_t owner_thread_id=0;
  ToastObjectObservationV1 observation{};
  std::string unavailable_reason;
};
struct ToastQueryContextV1 {
  GuiControlRequestV1 request{};
  CoreBindings core{};
  ToastObjectBindingsV1 bindings{};
  const game::GameAdapter *game=nullptr,*native_full_adapter=nullptr;
  const game::Snapshot *expected_full_snapshot=nullptr;
  ck3_11906::MainThreadQueryMailboxV1 *mailbox=nullptr;
  ck3_11906::MainThreadQueryTicketV1 ticket{};
  ToastQueryProviderV1 *provider=nullptr;
  std::uint64_t connection_generation=0,monotonic_deadline_ms=0;
  ToastQueryResultV1 result{};
};
void ArmToastQueryDeadlineV1(ToastQueryContextV1 &) noexcept;
bool ExecuteToastQueryMailboxV1(void *,const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
std::string SerializeToastQueryResultV1(std::string_view,const GuiControlRequestV1 &,const ToastQueryResultV1 &);
} // namespace xar::ck3_1210
