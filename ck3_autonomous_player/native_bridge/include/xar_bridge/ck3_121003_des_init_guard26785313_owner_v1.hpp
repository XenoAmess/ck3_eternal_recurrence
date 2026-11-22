#pragma once
#include "xar_bridge/ck3_121003_des_init_guard26785313_v1.hpp"
#include "xar_bridge/game_adapter.hpp"
#include <memory>
namespace xar::ck3_121003::build26785313 {
struct DesInitGuardFrame267V1 {bool facts_verified=false;ck3_1210::CoreSnapshotPrefix core{};void*game=nullptr,*jomini=nullptr,*storage=nullptr,*data=nullptr,*players=nullptr,*player=nullptr,*actor=nullptr;};
struct DesInitGuardRaw267V1 {DesInitGuardSource267V1 source{};std::uintptr_t definition=0;std::array<std::byte,64>definition_header{};bool entered=false,cleanup_known=true;friend bool operator==(const DesInitGuardRaw267V1&,const DesInitGuardRaw267V1&)=default;};
struct DesInitGuardContext267V1;
class DesInitGuardSession267V1 {
 public:DesInitGuardSession267V1();~DesInitGuardSession267V1();DesInitGuardSession267V1(const DesInitGuardSession267V1&)=delete;DesInitGuardSession267V1&operator=(const DesInitGuardSession267V1&)=delete;
 private:struct State;std::unique_ptr<State>state_;friend bool ExecuteDesInitGuardInner267V1(DesInitGuardContext267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;friend void BlockDesInitGuardUnknown267V1(DesInitGuardSession267V1&)noexcept;
};
struct DesInitGuardContext267V1 {ReadonlyBindings bindings{};ck3_11906::MainThreadQueryMailboxV1*mailbox=nullptr;ck3_11906::MainThreadQueryTicketV1 ticket{};DesInitGuardRequest267V1 request{};DesInitGuardResult267V1 result{};DesInitGuardSession267V1*session=nullptr;std::uint64_t connection_generation=0,monotonic_deadline_ms=0;bool native_observation_entered=false;};
DesInitGuardSession267V1&RetainedDesInitGuardSession267V1();
void ArmDesInitGuardDeadline267V1(DesInitGuardContext267V1&)noexcept;
void BlockDesInitGuardUnknown267V1(DesInitGuardSession267V1&)noexcept;
bool ExecuteDesInitGuardInner267V1(DesInitGuardContext267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
bool ExecuteDesInitGuardOnOwner267V1(void*,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
bool ReadDesInitGuardFrameOnOwner267V1(const ReadonlyBindings&,ck3_11906::MainThreadQueryMailboxV1*,const ck3_11906::MainThreadQueryTicketV1&,const ck3_11906::MainThreadExecutionStampV1&,void*,std::uint64_t,std::uint64_t,DesInitGuardFrame267V1&,std::string&)noexcept;
bool VerifyDesInitGuardImage267V1(std::uintptr_t)noexcept;
bool ReadDesInitGuardRaw267V1(const ReadonlyBindings&,const DesInitGuardFrame267V1&,std::uint64_t,std::uint64_t,DesInitGuardRaw267V1&,std::string&)noexcept;
bool DesInitGuardStepEnabled267V1(const game::AdapterDescriptor&,std::string_view)noexcept;
std::string DispatchDesInitGuardRequest267V1(const game::GameAdapter&,std::uint64_t,std::string_view,std::string_view,std::string_view,ck3_11906::MainThreadQueryMailboxV1&);
}
