#pragma once
#include "xar_bridge/ck3_1210.hpp"
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
  ImageBuildV1 image_build=ImageBuildV1::original26622941;
};
DateWorkerGameAccessBindingsV1 BindDateWorkerGameAccessImageV1(
    std::uintptr_t,std::string_view) noexcept;
enum class DateWorkerAcquisitionV2 : std::uint8_t { none,borrowed,owned,unknown };
enum class DateWorkerReleaseV2 : std::uint8_t { not_required,borrowed_preserved,owned_released,unknown };
enum class DateWorkerBodyV2 : std::uint8_t { not_called,failed,succeeded };
// Resource proof is independent of the body's result. UNKNOWN is sticky in
// the sentinel consumer and never permits a retry of the native destructor.
struct DateWorkerGameAccessResultV2 {
  DateWorkerAcquisitionV2 acquisition=DateWorkerAcquisitionV2::none;
  DateWorkerReleaseV2 release=DateWorkerReleaseV2::not_required;
  DateWorkerBodyV2 body=DateWorkerBodyV2::not_called;
  bool scope_verified=false;
  constexpr bool CleanupKnown() const noexcept {
    switch(acquisition) {
      case DateWorkerAcquisitionV2::none:
        return release==DateWorkerReleaseV2::not_required && body==DateWorkerBodyV2::not_called;
      case DateWorkerAcquisitionV2::borrowed:return release==DateWorkerReleaseV2::borrowed_preserved;
      case DateWorkerAcquisitionV2::owned:return release==DateWorkerReleaseV2::owned_released;
      case DateWorkerAcquisitionV2::unknown:return false;
    }
    return false;
  }
  constexpr bool Succeeded() const noexcept {
    return scope_verified && body==DateWorkerBodyV2::succeeded &&
        acquisition!=DateWorkerAcquisitionV2::none && CleanupKnown();
  }
};
using DateWorkerGameAccessV2=DateWorkerGameAccessResultV2 (*)(
    void *,DateWorkerGameBodyV1,void *) noexcept;
DateWorkerGameAccessResultV2 WithDateWorkerGameAccessV2(
    void *,DateWorkerGameBodyV1,void *) noexcept;
// V1 remains a source-compatible adapter; the new bridge uses V2 so a
// failed body and an unknown native release cannot collapse to the same bool.
// Resource scope only: caller must independently prove the native worker epoch.
// Never writes TLS/mutex memory. Uses exact native acquire and native destructor.
bool WithDateWorkerGameAccessV1(void *,DateWorkerGameBodyV1,void *) noexcept;
} // namespace xar::ck3_1210
