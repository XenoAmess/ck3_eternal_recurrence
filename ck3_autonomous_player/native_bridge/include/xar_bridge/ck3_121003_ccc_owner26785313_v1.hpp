#pragma once
#include "xar_bridge/ck3_121003_readonly26785313_v1.hpp"
namespace xar::ck3_121003::build26785313 {
enum class CccInvocationKind267V1:std::uint32_t{transition=1,event=2,decision=3};
struct CccOwnerInvocation267V1{std::uint64_t magic=0x4343433236375631ULL;CccInvocationKind267V1 kind;void*context=nullptr;};
bool ExecuteCccOnOwner267V1(void*,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
bool CccCaseAdmitted267V1(const ck3_1210::CoreSnapshotPrefix&,std::uint64_t,std::uintptr_t game,std::uintptr_t jomini)noexcept;
}
