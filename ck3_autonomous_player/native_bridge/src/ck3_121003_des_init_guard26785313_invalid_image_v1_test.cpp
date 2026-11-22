#include "xar_bridge/ck3_121003_des_init_guard26785313_owner_v1.hpp"
#include <stdexcept>
using namespace xar::ck3_121003::build26785313;
// Explicit NoGame traps: invalid image must reject before any Core/native call.
static unsigned forbidden_core_calls=0;
namespace xar::ck3_1210 {
void*ResolveCoreCharacter(const CoreBindings&,std::int32_t)noexcept{++forbidden_core_calls;return nullptr;}
bool ReadCoreSnapshot(const CoreBindings&,CoreSnapshotPrefix&)noexcept{++forbidden_core_calls;return false;}
}
int main(){ReadonlyBindings b;DesInitGuardFrame267V1 f;DesInitGuardRaw267V1 out;std::string why;if(VerifyDesInitGuardImage267V1(0)||ReadDesInitGuardRaw267V1(b,f,1,1,out,why)||out.entered||!out.cleanup_known||forbidden_core_calls)throw std::runtime_error("ON invalid image entered native");return 0;}
