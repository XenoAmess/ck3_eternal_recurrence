#include "xar_bridge/ck3_1210_hotfix26757580_v1.hpp"
#include "xar_bridge/ck3_1210_date_worker_game_access_v1.hpp"
#include "xar_bridge/ck3_1210.hpp"
#include <Windows.h>
#include <intrin.h>
#include <array>
#include <cstring>
#include <limits>

namespace xar::ck3_1210 {
namespace {
constexpr std::uintptr_t kAcquire=0x3E64890,kDestroy=0x3E64BA0,kApplication=0x6A640B8;
constexpr std::array<unsigned char,32> kAcquireEntry{
  0x40,0x53,0x48,0x83,0xEC,0x20,0x48,0x8D,0x0D,0x03,0xDE,0xED,0x01,0xFF,0x15,0x0D,
  0x3E,0xB7,0x00,0x48,0x8D,0x0D,0x06,0xDE,0xED,0x01,0xFF,0x15,0x00,0x3E,0xB7,0x00};
constexpr std::array<unsigned char,32> kDestroyEntry{
  0x48,0x83,0xEC,0x28,0x80,0x79,0x20,0x00,0x4C,0x8B,0xC1,0x74,0x16,0x48,0x8B,0x41,
  0x08,0x0F,0x10,0x41,0x10,0x0F,0x10,0x08,0x0F,0x11,0x00,0x0F,0x11,0x49,0x10,0xC6};
constexpr std::array<unsigned char,32> kHotfixAcquireEntry{0x40,0x53,0x48,0x83,0xEC,0x20,0x48,0x8D,0x0D,0x83,0xE1,0xED,0x01,0xFF,0x15,0x8D,0x41,0xB7,0x00,0x48,0x8D,0x0D,0x86,0xE1,0xED,0x01,0xFF,0x15,0x80,0x41,0xB7,0x00};
bool Model(const DateWorkerGameAccessBindingsV1 &b) noexcept {
  return b.offline_fixture && b.module_base==0 && b.fixture.sample &&
      b.fixture.acquire && b.fixture.destroy;
}
bool Production(const DateWorkerGameAccessBindingsV1 &b) noexcept {
  return !b.offline_fixture && b.exact_build_admitted && b.module_base!=0 &&
      !b.fixture.context && !b.fixture.sample && !b.fixture.acquire && !b.fixture.destroy &&
      b.module_base<=std::numeric_limits<std::uintptr_t>::max()-ImageRva(b.image_build,kApplication,hotfix26757580::kApplication) &&
      reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr))==b.module_base &&
      std::memcmp(reinterpret_cast<const void *>(b.module_base+ImageRva(b.image_build,kAcquire,hotfix26757580::kAcquire)),(IsHotfix(b.image_build)?kHotfixAcquireEntry:kAcquireEntry).data(),32)==0 &&
      std::memcmp(reinterpret_cast<const void *>(b.module_base+ImageRva(b.image_build,kDestroy,hotfix26757580::kDestroy)),kDestroyEntry.data(),32)==0;
}
bool Sample(const DateWorkerGameAccessBindingsV1 &b,DateWorkerGameAccessSampleV1 &s) {
  if(Model(b))return b.fixture.sample(b.fixture.context,s);
  const auto vector=*reinterpret_cast<const std::uintptr_t *>(__readgsqword(0x58));
  if(!vector)return false;
  s.tls_block=vector;
  std::memcpy(&s.command_scope,reinterpret_cast<const void *>(vector+0x140),4);
  std::memcpy(&s.native_access,reinterpret_cast<const void *>(vector+0x6E0),1);
  std::memcpy(&s.application,reinterpret_cast<const void *>(b.module_base+ImageRva(b.image_build,kApplication,hotfix26757580::kApplication)),8);
  return s.application!=0;
}
bool Same(const DateWorkerGameAccessSampleV1 &s,const DateWorkerGameAccessSampleV1 &a,
    std::uint8_t access) noexcept {
  return a.tls_block && a.application && s.tls_block==a.tls_block &&
      s.application==a.application && s.command_scope==1 && s.native_access==access;
}
void Acquire(const DateWorkerGameAccessBindingsV1 &b) {
  if(Model(b))b.fixture.acquire(b.fixture.context);
  else reinterpret_cast<void (*)()>(b.module_base+ImageRva(b.image_build,kAcquire,hotfix26757580::kAcquire))();
}
void Destroy(const DateWorkerGameAccessBindingsV1 &b,void *descriptor) {
  if(Model(b))b.fixture.destroy(b.fixture.context,descriptor);
  else reinterpret_cast<void (*)(void *)>(b.module_base+ImageRva(b.image_build,kDestroy,hotfix26757580::kDestroy))(descriptor);
}
// Trivial storage permits SEH finally to preserve the resource outcome even
// when acquire/body/destructor faults. No unknown native operation is retried.
void RunV2(const DateWorkerGameAccessBindingsV1 &b,DateWorkerGameBodyV1 body,
    void *context,DateWorkerGameAccessResultV2 &outcome) {
  if(!body || (!Model(b) && !Production(b)))return;
  DateWorkerGameAccessSampleV1 before{},now{};
  if(!Sample(b,before) || !before.tls_block || !before.application ||
      before.command_scope!=1 || before.native_access>1)return;
  alignas(16) unsigned char descriptor[0x48]{};
  bool attempted=false;
  if(before.native_access==1) {
    outcome.acquisition=DateWorkerAcquisitionV2::borrowed;
    outcome.release=DateWorkerReleaseV2::unknown;
  }
  __try {
    if(before.native_access==0) {
      attempted=true;
      // A fault can occur between native lock operations and the TLS commit;
      // observing access=0 afterwards alone does not prove no acquisition.
      outcome.acquisition=DateWorkerAcquisitionV2::unknown;
      outcome.release=DateWorkerReleaseV2::unknown;
      Acquire(b);
      if(!Sample(b,now) || !Same(now,before,1))__leave;
      descriptor[0]=1;
      outcome.acquisition=DateWorkerAcquisitionV2::owned;
    }
    if(!Sample(b,now) || !Same(now,before,1))__leave;
    outcome.body=DateWorkerBodyV2::failed; // Also retained on a body SEH.
    if(body(context))outcome.body=DateWorkerBodyV2::succeeded;
    outcome.scope_verified=Sample(b,now) && Same(now,before,1);
  } __finally {
    // A committed native acquisition may be established after a trace fault,
    // but a changed/unreadable epoch never fabricates the owned descriptor.
    if(!descriptor[0] && attempted && Sample(b,now) && Same(now,before,1)) {
      descriptor[0]=1;
      outcome.acquisition=DateWorkerAcquisitionV2::owned;
    }
    if(descriptor[0]) {
      // Keep UNKNOWN through the destructor call itself. A pre-release SEH
      // must not be mistaken for one completed release or retried blindly.
      outcome.release=DateWorkerReleaseV2::unknown;
      Destroy(b,descriptor);
      if(Sample(b,now) && Same(now,before,0))
        outcome.release=DateWorkerReleaseV2::owned_released;
    } else if(outcome.acquisition==DateWorkerAcquisitionV2::borrowed) {
      if(Sample(b,now) && Same(now,before,1))
        outcome.release=DateWorkerReleaseV2::borrowed_preserved;
    }
  }
}
} // namespace
DateWorkerGameAccessBindingsV1 BindDateWorkerGameAccessImageV1(
    std::uintptr_t base,std::string_view sha) noexcept {
  DateWorkerGameAccessBindingsV1 b{};
  b.image_build=ImageBuildForSha(sha);
  if(base && b.image_build!=ImageBuildV1::unknown && base<=std::numeric_limits<std::uintptr_t>::max()-ImageRva(b.image_build,kApplication,hotfix26757580::kApplication)) {
    b.module_base=base;b.exact_build_admitted=true;
    // Cold preparation reads code only, never native manager/TLS/world state.
    // Reject before ARM if this process does not contain the paired entries.
    __try {if(!Production(b))b={};}
    __except(EXCEPTION_EXECUTE_HANDLER) {b={};}
  }
  return b;
}
DateWorkerGameAccessResultV2 WithDateWorkerGameAccessV2(
    void *opaque,DateWorkerGameBodyV1 body,void *context) noexcept {
  DateWorkerGameAccessResultV2 outcome{};
  if(!opaque)return outcome;
  __try {RunV2(*static_cast<const DateWorkerGameAccessBindingsV1 *>(opaque),body,context,outcome);}
  __except(EXCEPTION_EXECUTE_HANDLER) {outcome.scope_verified=false;}
  return outcome;
}
bool WithDateWorkerGameAccessV1(void *opaque,DateWorkerGameBodyV1 body,void *context) noexcept {
  return WithDateWorkerGameAccessV2(opaque,body,context).Succeeded();
}
} // namespace xar::ck3_1210
