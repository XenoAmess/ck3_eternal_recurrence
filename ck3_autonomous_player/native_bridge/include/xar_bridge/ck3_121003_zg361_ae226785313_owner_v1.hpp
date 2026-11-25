#pragma once
#include "xar_bridge/ck3_121003_zg361_ae226785313_v1.hpp"
#include "xar_bridge/ck3_121003_zg361_ae2_controls26785313_private_v1.hpp"
#include "xar_bridge/ck3_121003_letter_set26785313_owner_v1.hpp"
#include "xar_bridge/game_adapter.hpp"
#include "xar_bridge/ck3_121003_zg361_scoreboard26785313_private_v1.hpp"
#include <memory>
namespace xar::ck3_121003::build26785313 {
struct Zg361Ae2Frame267V1 {
 ck3_1210::CoreSnapshotPrefix core{};
 std::uintptr_t game=0,jomini=0,character_storage=0;
 bool facts_verified=false;
 std::optional<zg361_ae2_control::Zg361Ae2ManageFrame267V1>controls;
 std::optional<LetterSetFrame267V1>events;
 std::optional<GuiWindowV1>scoreboard;
};
class Zg361Ae2Raw267V1 {
 public:Zg361Ae2Source267V1 source;
 bool entered=false,cleanup_known=true;
 private:struct State;std::shared_ptr<const State>state_;
 friend bool ReadZg361Ae2Raw267V1(const ReadonlyBindings&,const Zg361Ae2Frame267V1&,
  const Zg361Ae2Request267V1&,std::uint64_t,Zg361Ae2Raw267V1&,std::string&)noexcept;
 friend bool SameZg361Ae2Raw267V1(const Zg361Ae2Raw267V1&,const Zg361Ae2Raw267V1&)noexcept;
 friend struct Zg361Ae2CallAccess267V1;
};
struct Zg361Ae2Call267V1 {bool entered=false,native_returned=false,cleanup_known=true;};
bool ReadZg361Ae2Raw267V1(const ReadonlyBindings&,const Zg361Ae2Frame267V1&,
 const Zg361Ae2Request267V1&,std::uint64_t,Zg361Ae2Raw267V1&,std::string&)noexcept;
bool SameZg361Ae2Raw267V1(const Zg361Ae2Raw267V1&,const Zg361Ae2Raw267V1&)noexcept;
bool SameZg361Ae2LeaseFrame267V1(Zg361Ae2Action267V1,const Zg361Ae2Frame267V1&,
 const Zg361Ae2Raw267V1&,const Zg361Ae2Frame267V1&,const Zg361Ae2Raw267V1&)noexcept;
Zg361Ae2Call267V1 CallZg361Ae2Raw267V1(const ReadonlyBindings&,const Zg361Ae2Frame267V1&,
 const Zg361Ae2Request267V1&,std::uint64_t,const Zg361Ae2Raw267V1&)noexcept;
bool VerifyZg361Ae2Image267V1(std::uintptr_t)noexcept;
class Zg361Ae2Session267V1;
struct Zg361Ae2Context267V1 {
 ReadonlyBindings bindings{};ck3_11906::MainThreadQueryMailboxV1*mailbox=nullptr;
 ck3_11906::MainThreadQueryTicketV1 ticket{};
 Zg361Ae2Request267V1 request;Zg361Ae2Result267V1 result;Zg361Ae2Session267V1*session=nullptr;
 std::uint64_t connection_generation=0,monotonic_deadline_ms=0;
 bool observation_entered=false;
};
class Zg361Ae2Session267V1 {
 public:Zg361Ae2Session267V1();~Zg361Ae2Session267V1();
 Zg361Ae2Session267V1(const Zg361Ae2Session267V1&)=delete;
 Zg361Ae2Session267V1&operator=(const Zg361Ae2Session267V1&)=delete;
 private:struct State;std::unique_ptr<State>state_;
 friend bool ExecuteZg361Ae2Inner267V1(Zg361Ae2Context267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
 friend void BlockZg361Ae2Unknown267V1(Zg361Ae2Session267V1&)noexcept;
};
Zg361Ae2Session267V1&RetainedZg361Ae2Session267V1();
void BlockZg361Ae2Unknown267V1(Zg361Ae2Session267V1&)noexcept;
void ArmZg361Ae2Deadline267V1(Zg361Ae2Context267V1&)noexcept;
bool ExecuteZg361Ae2Inner267V1(Zg361Ae2Context267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
bool ExecuteZg361Ae2OnOwner267V1(void*,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
bool ReadZg361Ae2FrameOnOwner267V1(const ReadonlyBindings&,
 ck3_11906::MainThreadQueryMailboxV1*,const ck3_11906::MainThreadQueryTicketV1&,
 const ck3_11906::MainThreadExecutionStampV1&,void*,const Zg361Ae2Request267V1&,
 std::uint64_t,Zg361Ae2Frame267V1&,std::string&)noexcept;
const game::AdapterDescriptor&Zg361Ae2Descriptor267V1(const game::AdapterDescriptor&)noexcept;
bool Zg361Ae2StepEnabled267V1(const game::AdapterDescriptor&,std::string_view)noexcept;
std::string DispatchZg361Ae2Request267V1(const game::GameAdapter&,std::uint64_t,
 std::string_view,std::string_view,std::string_view,ck3_11906::MainThreadQueryMailboxV1&);
}
