#pragma once
#include "xar_bridge/ck3_121003_readonly26785313_v1.hpp"
namespace xar::ck3_121003::build26785313 {
enum class LivingInvocationKind267V1:std::uint32_t {inventory_query=1,ui=2,entry=3};
struct LivingOwnerInvocation267V1 {
 std::uint64_t magic=0x4C49564932363731ULL;
 LivingInvocationKind267V1 kind=LivingInvocationKind267V1::inventory_query;
 void*context=nullptr;
};
// This exact new callback must be explicitly attached under the independent
// current flag. A nonempty existing mechanical slot is never overwritten.
// The slot's historical field name grants no12004 or artifact action permission.
bool ExecuteLivingOnOwner267V1(void*,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
std::uint64_t LivingOwnerConnection267V1(const LivingOwnerInvocation267V1*)noexcept;
bool LivingFamilyUnknown267V1()noexcept;
void BlockLivingFamilyUnknown267V1()noexcept;
}
