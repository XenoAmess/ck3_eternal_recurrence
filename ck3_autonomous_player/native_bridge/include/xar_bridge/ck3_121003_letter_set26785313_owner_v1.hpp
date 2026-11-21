#pragma once
#include "xar_bridge/ck3_121003_letter26785313_owner_v1.hpp"
#include "xar_bridge/ck3_121003_letter_set26785313_raw_v1.hpp"
namespace xar::ck3_121003::build26785313 {
struct LetterSetFrame267V1{bool facts_verified=false;ck3_1210::CoreSnapshotPrefix core{};LetterSetScene267V1 scene{};std::vector<GuiWindowNodeV1>witness;};
struct LetterSetContext267V1{
 ReadonlyBindings bindings{};ck3_11906::MainThreadQueryMailboxV1*mailbox=nullptr;ck3_11906::MainThreadQueryTicketV1 ticket{};
 LetterSetRequest267V1 request{};LetterSetResult267V1 result{};LetterSession267V1*session=nullptr;
 std::uint64_t connection_generation=0,monotonic_deadline_ms=0;bool native_observation_entered=false;
};
void ArmLetterSetDeadline267V1(LetterSetContext267V1&)noexcept;
bool ExecuteLetterSetInner267V1(LetterSetContext267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
bool ExecuteLetterSetOnOwner267V1(void*,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
bool ReadLetterSetFrameOnOwner267V1(const ReadonlyBindings&,ck3_11906::MainThreadQueryMailboxV1*,const ck3_11906::MainThreadQueryTicketV1&,const ck3_11906::MainThreadExecutionStampV1&,void*,std::uint64_t,std::uint64_t,LetterSetFrame267V1&,std::string&)noexcept;
bool LetterSetStepEnabled267V1(const game::AdapterDescriptor&,std::string_view)noexcept;
std::string DispatchLetterSetRequest267V1(const game::GameAdapter&,std::uint64_t,std::string_view,std::string_view,std::string_view,ck3_11906::MainThreadQueryMailboxV1&);
}
