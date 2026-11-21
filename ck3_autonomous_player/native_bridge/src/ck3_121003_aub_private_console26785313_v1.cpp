#include "xar_bridge/ck3_121003_aub_private_console26785313_v1.hpp"
#include "xar_bridge/ck3_121003_aub_private_console26785313_pins_v1.hpp"
#include <array>
#include <cstring>
#include <limits>
#include <windows.h>
namespace xar::ck3_121003::build26785313 {namespace {
[[maybe_unused]] bool Copy(std::uintptr_t p,void*out,std::size_t n) noexcept {
 if(!p||!out||!n||n-1>(std::numeric_limits<std::uintptr_t>::max)()-p)return false;
 __try{std::memcpy(out,reinterpret_cast<const void*>(p),n);return true;}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
constexpr std::uintptr_t slot=0x68B3B68,execute=0x3EB41B0,assign=0x896BB0,destroy=0x897460,enter=0x3F6C7F0,exit=0xFAD920;
static_assert(kRngWrapperSlotRva==0x5D559B8);
static_assert(sizeof(ck3_12002::kPrivateFixtureInboxCommand)-1==21);
} // namespace
bool VerifyAubPrivateInboxImage267V1([[maybe_unused]]std::uintptr_t image) noexcept {
#if defined(XAR_CK3_ENABLE_121003_26785313_AUB_PRIVATE_FIXTURE_V1) && XAR_CK3_ENABLE_121003_26785313_AUB_PRIVATE_FIXTURE_V1
 if(!image||image!=reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr))||!VerifyReadonlyImage(image))return false;
 std::array<unsigned char,256>b{};
 for(const auto&p:aub_private_console_pins::kPins)if(p.bytes.empty()||p.bytes.size()>b.size()||p.rva>kImageSize-p.bytes.size()||!Copy(image+p.rva,b.data(),p.bytes.size())||std::memcmp(b.data(),p.bytes.data(),p.bytes.size()))return false;
 for(const auto&p:aub_private_console_pins::kPointers){std::uintptr_t v=0;if(!Copy(image+p.slot,&v,8)||v!=image+p.target)return false;}
 return true;
#else
 return false;
#endif
}
ck3_12002::ConsoleFixtureBindings BindAubPrivateInboxFixture267V1([[maybe_unused]]std::uintptr_t image,[[maybe_unused]]std::string_view sha) noexcept {
 ck3_12002::ConsoleFixtureBindings b;
#if defined(XAR_CK3_ENABLE_121003_26785313_AUB_PRIVATE_FIXTURE_V1) && XAR_CK3_ENABLE_121003_26785313_AUB_PRIVATE_FIXTURE_V1
 if(!BindReadonlyImage(image,sha).exact_image_admitted||!VerifyAubPrivateInboxImage267V1(image))return b;
 b.console_slot=reinterpret_cast<void**>(image+slot);b.execute=reinterpret_cast<ck3_12002::ConsoleFixtureExecute>(image+execute);
 b.assign_string=reinterpret_cast<ck3_12002::ConsoleFixtureStringAssign>(image+assign);b.destroy_string=reinterpret_cast<ck3_12002::ConsoleFixtureStringDestroy>(image+destroy);
 b.random_wrapper_slot=reinterpret_cast<void**>(image+kRngWrapperSlotRva);b.enter_random_scope=reinterpret_cast<ck3_12002::ConsoleFixtureRandomScopeEnter>(image+enter);b.exit_random_scope=reinterpret_cast<ck3_12002::ConsoleFixtureRandomScopeExit>(image+exit);b.enabled=true;
#endif
 return b;
}
bool ReadBoundAubPrivateInboxConsole267V1([[maybe_unused]]const ReadonlyBindings&core,[[maybe_unused]]const ck3_12002::ConsoleFixtureBindings&b,std::uintptr_t&out) noexcept {
 out=0;
#if defined(XAR_CK3_ENABLE_121003_26785313_AUB_PRIVATE_FIXTURE_V1) && XAR_CK3_ENABLE_121003_26785313_AUB_PRIVATE_FIXTURE_V1
#if defined(XAR_CK3_26785313_OFFLINE_FIXTURE)
 if(core.offline_fixture)return false;
#endif
 const auto image=core.module_base;
 if(!core.exact_image_admitted||!core.core.enabled||!b.enabled||!VerifyAubPrivateInboxImage267V1(image)||
    reinterpret_cast<std::uintptr_t>(b.console_slot)!=image+slot||reinterpret_cast<std::uintptr_t>(b.execute)!=image+execute||
    reinterpret_cast<std::uintptr_t>(b.assign_string)!=image+assign||reinterpret_cast<std::uintptr_t>(b.destroy_string)!=image+destroy||
    reinterpret_cast<std::uintptr_t>(b.random_wrapper_slot)!=image+kRngWrapperSlotRva||reinterpret_cast<std::uintptr_t>(b.enter_random_scope)!=image+enter||reinterpret_cast<std::uintptr_t>(b.exit_random_scope)!=image+exit)return false;
 std::uintptr_t a=0,z=0,av=0,zv=0;
 if(!Copy(image+slot,&a,8)||!a||!Copy(a,&av,8)||av!=image+0x50A3110||!Copy(image+slot,&z,8)||z!=a||!Copy(z,&zv,8)||zv!=av||!VerifyAubPrivateInboxImage267V1(image))return false;
 out=a;return true;
#else
 return false;
#endif
}
} // namespace xar::ck3_121003::build26785313
