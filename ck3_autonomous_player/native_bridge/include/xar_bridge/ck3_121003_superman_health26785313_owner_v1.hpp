#pragma once
#include "xar_bridge/ck3_121003_superman_health26785313_raw_v1.hpp"
#include "xar_bridge/ck3_121003_superman_health26785313_v1.hpp"
#include "xar_bridge/game_adapter.hpp"
#include <memory>
namespace xar::ck3_121003::build26785313 {
struct SupermanHealthFrame267V1{bool facts_verified=false,native_read_entered=false,cleanup_known=true;ck3_1210::CoreSnapshotPrefix core{};SupermanHealthScene267V1 scene{};std::vector<GuiWindowNodeV1>witness;};
struct SupermanHealthContext267V1;
class SupermanHealthSession267V1{
 public:SupermanHealthSession267V1();~SupermanHealthSession267V1();SupermanHealthSession267V1(const SupermanHealthSession267V1&)=delete;SupermanHealthSession267V1&operator=(const SupermanHealthSession267V1&)=delete;
 private:struct State;std::unique_ptr<State>state_;
 friend bool ExecuteSupermanHealthInner267V1(SupermanHealthContext267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
 friend void BlockSupermanHealthUnknown267V1(SupermanHealthSession267V1&)noexcept;
};
struct SupermanHealthContext267V1{
 ReadonlyBindings bindings{};ck3_11906::MainThreadQueryMailboxV1*mailbox=nullptr;ck3_11906::MainThreadQueryTicketV1 ticket{};
 SupermanHealthRequest267V1 request{};SupermanHealthResult267V1 result{};SupermanHealthSession267V1*session=nullptr;
 std::uint64_t connection_generation=0,monotonic_deadline_ms=0;bool native_observation_entered=false;
};
SupermanHealthSession267V1& RetainedSupermanHealthSession267V1();
void ArmSupermanHealthDeadline267V1(SupermanHealthContext267V1&)noexcept;
void BlockSupermanHealthUnknown267V1(SupermanHealthSession267V1&)noexcept;
bool ExecuteSupermanHealthOnOwner267V1(void*,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
bool ReadSupermanHealthFrameOnOwner267V1(const ReadonlyBindings&,ck3_11906::MainThreadQueryMailboxV1*,const ck3_11906::MainThreadQueryTicketV1&,
 const ck3_11906::MainThreadExecutionStampV1&,void*,std::uint64_t,std::uint64_t,SupermanHealthFrame267V1&,std::string&)noexcept;
bool SupermanHealthStepEnabled267V1(const game::AdapterDescriptor&,std::string_view)noexcept;
std::string DispatchSupermanHealthRequest267V1(const game::GameAdapter&,std::uint64_t,std::string_view,std::string_view,std::string_view,ck3_11906::MainThreadQueryMailboxV1&);
} // namespace
