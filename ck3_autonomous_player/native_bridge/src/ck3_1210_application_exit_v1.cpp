#include "xar_bridge/ck3_1210_hotfix26757580_v1.hpp"
#include "xar_bridge/ck3_1210_application_exit_v1.hpp"
#include <array>
#include <cstring>
#include <windows.h>

namespace xar::ck3_1210 {
namespace {
constexpr std::array<unsigned char,32> kQuitEntry{
  0x4c,0x8b,0xdc,0x53,0x48,0x81,0xec,0x80,0x00,0x00,0x00,0x48,0x8b,0xd9,
  0x48,0x8d,0x05,0xeb,0x3d,0x14,0x01,0x49,0x89,0x43,0xb8,0x49,0xc7,0x43,0xc0,0x1b,0x00,0x00};
constexpr std::array<unsigned char,16> kQuitFlagAndReturn{
  0xc6,0x83,0x89,0x00,0x00,0x00,0x01,0x48,0x81,0xc4,0x80,0x00,0x00,0x00,0x5b,0xc3};
constexpr std::array<unsigned char,32> kHotfixQuitEntry{0x4C,0x8B,0xDC,0x53,0x48,0x81,0xEC,0x80,0x00,0x00,0x00,0x48,0x8B,0xD9,0x48,0x8D,0x05,0xFB,0x44,0x14,0x01,0x49,0x89,0x43,0xB8,0x49,0xC7,0x43,0xC0,0x1B,0x00,0x00};
ApplicationExitStatusV1 Request(const ApplicationExitBindingsV1 &b,
    ApplicationExitSessionV1 &session,BeforeApplicationExitV1 admitted,void *context) noexcept {
  if (!b.enabled || b.application_slot==nullptr || b.request_quit==nullptr || b.expected_application_vtable==0 || admitted==nullptr)
    return ApplicationExitStatusV1::unavailable;
  void *const application=*b.application_slot;
  if (application==nullptr) return ApplicationExitStatusV1::unavailable;
  std::uintptr_t table=0; std::memcpy(&table,application,sizeof(table));
  if (table!=b.expected_application_vtable &&
      (b.alternative_application_vtable==0 || table!=b.alternative_application_vtable))
    return ApplicationExitStatusV1::unavailable;
  auto *const flag=static_cast<const unsigned char *>(application)+kApplicationQuitFlagOffset;
  if (*flag>1) return ApplicationExitStatusV1::unavailable;
  // Fresh owner/prefix/deadline must be rechecked immediately before claiming.
  if (!admitted(context) || *b.application_slot!=application)
    return ApplicationExitStatusV1::admission_rejected;
  bool expected=false;
  if (!session.claimed.compare_exchange_strong(expected,true,std::memory_order_acq_rel))
    return *flag==1 ? ApplicationExitStatusV1::already_requested : ApplicationExitStatusV1::claim_consumed;
  if (*flag==1) return ApplicationExitStatusV1::already_requested;
  b.request_quit(application);
  return *flag==1 ? ApplicationExitStatusV1::requested : ApplicationExitStatusV1::indeterminate;
}
}
ApplicationExitBindingsV1 BindApplicationExitImageV1(
    std::uintptr_t base,std::string_view sha) noexcept {
  const auto build=ImageBuildForSha(sha);
  if (base==0 || build==ImageBuildV1::unknown) return {};
#if defined(_MSC_VER)
  __try {
#endif
    if (std::memcmp(reinterpret_cast<const void *>(base+ImageRva(build,kApplicationQuitRequestRva,hotfix26757580::kQuit)),
          (IsHotfix(build)?kHotfixQuitEntry:kQuitEntry).data(),kQuitEntry.size())!=0 ||
        std::memcmp(reinterpret_cast<const void *>(base+ImageRva(build,0x3F5AE85,hotfix26757580::kQuitTail)),
          kQuitFlagAndReturn.data(),kQuitFlagAndReturn.size())!=0) return {};
    return {true,reinterpret_cast<void *const *>(base+ImageRva(build,kApplicationSingletonRva,hotfix26757580::kApplication)),
        reinterpret_cast<ApplicationQuitRequestV1>(base+ImageRva(build,kApplicationQuitRequestRva,hotfix26757580::kQuit)),
        base+ImageRva(build,0x4AFA620,0x4AFB650),base+ImageRva(build,0x4DC8568,0x4DC95C0)};
#if defined(_MSC_VER)
  } __except(EXCEPTION_EXECUTE_HANDLER) { return {}; }
#endif
}
ApplicationExitStatusV1 RequestApplicationExitV1(const ApplicationExitBindingsV1 &b,
    ApplicationExitSessionV1 &session,BeforeApplicationExitV1 admitted,void *context) noexcept {
#if defined(_MSC_VER)
  __try { return Request(b,session,admitted,context); }
  __except(EXCEPTION_EXECUTE_HANDLER) { return ApplicationExitStatusV1::indeterminate; }
#else
  return Request(b,session,admitted,context);
#endif
}
}
