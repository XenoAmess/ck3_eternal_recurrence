#pragma once
#include "xar_bridge/ck3_121003_gui_controls26785313_v2.hpp"
#include <array>
#include <memory>
#include <string>
#include <string_view>

namespace xar::ck3_121003::build26785313 {
// A fixed current Rite operation within the existing Rite/Core contract. These
// constants grant no capability until the fixed bridge/owner path is adopted.
inline constexpr char kRiteDoctrineSchema267V1[]="ck3_121003_rite_doctrine_v1";
inline constexpr char kRiteDoctrineResultSchema267V1[]="ck3_121003_rite_doctrine_result_v1";
inline constexpr char kRiteDoctrineStep267V1[]="current-rite-doctrine-v1";
inline constexpr char kRiteDoctrineCapability267V1[]="game.command.current-rite-doctrine.v1";
inline constexpr char kRiteDoctrineGroup267V1[]="des_dynastic_membership";
inline constexpr char kRiteDoctrineTarget267V1[]="des_doctrine_dynastic";
inline constexpr std::size_t kRiteDoctrineMaximumClaims267V1=64;

enum class RiteDoctrineAction267V1 { query,open_dynastic_category,select_dynastic,confirm_edit };
enum class RiteDoctrineStatus267V1 {
 unavailable,available,expired,stale_core,source_changed,query_consumed,
 claim_consumed,capacity_exhausted,prerequisite_rejected,category_opened,
 draft_selected,confirmation_dispatched,indeterminate
};
struct RiteDoctrineRequest267V1 {
 std::array<char,97> request_id{};
 std::uint8_t request_id_size=0;
 std::string_view id() const noexcept {return {request_id.data(),request_id_size};}
 GuiWindowRequestV1 window{};
 std::uint32_t expected_source_rite_id=0xFFFFFFFFU;
 RiteDoctrineAction267V1 action=RiteDoctrineAction267V1::query;
 // Canonical decimal uint64 strings on wire; no caller pointers or ordinals.
 std::uint64_t provider_generation=0,query_sequence=0;
};
struct RiteDoctrineFacts267V1 {
 bool core_before_verified=false,source_rite_verified=false;
 bool category_available=false,target_available=false;
 bool should_display_evaluated=false,should_display=false;
 bool can_pick_evaluated=false,can_pick=false;
 bool knowledge_evaluated=false,known_doctrine=false;
 bool selected_evaluated=false,selected=false;
 bool can_edit_evaluated=false,can_edit=false;
 std::int64_t piety_cost_raw=0,piety_missing_raw=0;
 std::uint32_t source_rite_id=0xFFFFFFFFU;
 ck3_1210::CoreSnapshotPrefix core{};
 std::uint64_t connection_generation=0,ticket_sequence=0,pump_epoch=0;
 std::uint32_t thread_id=0;
};
struct RiteDoctrineResult267V1 {
 RiteDoctrineAction267V1 action=RiteDoctrineAction267V1::query;
 RiteDoctrineStatus267V1 status=RiteDoctrineStatus267V1::unavailable;
 RiteDoctrineFacts267V1 facts{};
 std::uint64_t provider_generation=0,query_sequence=0,claim_sequence=0;
 bool effect_attempted=false,native_returned=false;
 // Native callback dispatch never independently proves the business persisted.
 bool native_handled=false;
 bool post_selected_evaluated=false,post_selected=false;
 std::string reason;
};
bool RiteDoctrineRequestShape267V1(const RiteDoctrineRequest267V1&) noexcept;
bool ParseRiteDoctrineRequest267V1(std::string_view,RiteDoctrineRequest267V1&) noexcept;
std::string SerializeRiteDoctrineResult267V1(std::string_view,const RiteDoctrineResult267V1&);
bool RiteDoctrineRouteEnabled267V1(const game::AdapterDescriptor&) noexcept;
std::string DispatchRiteDoctrineRequest267V1(const game::GameAdapter&,std::uint64_t,
 std::string_view,std::string_view,std::string_view,ck3_11906::MainThreadQueryMailboxV1&);
class RiteDoctrineSession267V1 {
 public:
  RiteDoctrineSession267V1();
  ~RiteDoctrineSession267V1();
  RiteDoctrineSession267V1(const RiteDoctrineSession267V1&)=delete;
  RiteDoctrineSession267V1&operator=(const RiteDoctrineSession267V1&)=delete;
 private:
  struct State;
  std::unique_ptr<State> state_;
  friend bool ExecuteRiteDoctrineInner267V1(struct RiteDoctrineContext267V1&,
      const ck3_11906::MainThreadExecutionStampV1&) noexcept;
  friend void BlockRiteDoctrineUnknown267V1(RiteDoctrineSession267V1&) noexcept;
};
struct RiteDoctrineContext267V1 {
 ReadonlyBindings bindings{};
 const game::GameAdapter *game=nullptr;
 ck3_11906::MainThreadQueryMailboxV1 *mailbox=nullptr;
 ck3_11906::MainThreadQueryTicketV1 ticket{};
 RiteDoctrineRequest267V1 request{};
 RiteDoctrineSession267V1 *session=nullptr;
 RiteDoctrineResult267V1 result{};
 std::uint64_t connection_generation=0,monotonic_deadline_ms=0;
};
void ArmRiteDoctrineDeadline267V1(RiteDoctrineContext267V1&) noexcept;
void BlockRiteDoctrineUnknown267V1(RiteDoctrineSession267V1&) noexcept;
bool ExecuteRiteDoctrineOnOwner267V1(void*,const ck3_11906::MainThreadExecutionStampV1&) noexcept;
bool ReadRiteDoctrineDraftOnOwner267V1(const ReadonlyBindings&,
 ck3_11906::MainThreadQueryMailboxV1*,const ck3_11906::MainThreadQueryTicketV1&,
 const ck3_11906::MainThreadExecutionStampV1&,void*,const RiteDraftRequestV2&,
 ReadonlyObservation&) noexcept;
} // namespace xar::ck3_121003::build26785313
