#pragma once
#include "xar_bridge/ck3_121003_readonly26785313_v1.hpp"
#include <optional>
namespace xar::ck3_121003::build26785313 {
enum class RmtmInvocationKind267V1:std::uint32_t {transition=1,event=2,decision=3,observation=4};
struct RmtmOwnerInvocation267V1 {std::uint64_t magic=0x524D544D32363731ULL;RmtmInvocationKind267V1 kind;void*context=nullptr;};
struct RmtmPrivateCaseAnchor267V1 {std::uint32_t full_title_id=0xFFFFFFFFU;std::int32_t predecessor=-1;std::optional<std::int32_t>successor;std::uint32_t completed_days=0;};
bool ExecuteRmtmOnOwner267V1(void*,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
bool RmtmCaseAdmitted267V1(const ck3_1210::CoreSnapshotPrefix&,std::uint64_t,std::uintptr_t game,std::uintptr_t jomini)noexcept;
bool ReadRmtmPrivateCaseAnchor267V1(const ck3_1210::CoreSnapshotPrefix&,std::uint64_t,std::uintptr_t,std::uintptr_t,RmtmPrivateCaseAnchor267V1&)noexcept;
}
