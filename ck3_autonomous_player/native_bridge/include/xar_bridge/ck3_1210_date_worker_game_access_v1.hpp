#pragma once
#include <cstdint>
#include <string_view>

namespace xar::ck3_1210 {
using DateWorkerGameBodyV1 = bool (*)(void *) noexcept;
struct DateWorkerGameAccessSampleV1 {
  std::uintptr_t tls_block=0,application=0;
  std::uint32_t command_scope=0;
  std::uint8_t native_access=0;
};
// Explicit NoGame seam. Runtime binding rejects every fixture callback.
struct DateWorkerGameAccessFixtureV1 {
  void *context=nullptr;
  bool (*sample)(void *,DateWorkerGameAccessSampleV1 &)=nullptr;
  void (*acquire)(void *)=nullptr;
  void (*destroy)(void *,void *)=nullptr;
};
struct DateWorkerGameAccessBindingsV1 {
  bool exact_build_admitted=false,offline_fixture=false;
  std::uintptr_t module_base=0;
  DateWorkerGameAccessFixtureV1 fixture{};
};
DateWorkerGameAccessBindingsV1 BindDateWorkerGameAccessImageV1(
    std::uintptr_t,std::string_view) noexcept;
// Resource scope only: caller must independently prove the native worker epoch.
// Never writes TLS/mutex memory. Uses exact native acquire and native destructor.
bool WithDateWorkerGameAccessV1(void *,DateWorkerGameBodyV1,void *) noexcept;
} // namespace xar::ck3_1210
