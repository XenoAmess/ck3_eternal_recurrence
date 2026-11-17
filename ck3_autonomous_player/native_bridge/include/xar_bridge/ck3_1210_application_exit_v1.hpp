#pragma once
#include "xar_bridge/ck3_1210.hpp"
#include <atomic>

namespace xar::ck3_1210 {
inline constexpr std::uintptr_t kApplicationSingletonRva=0x6A640B8;
inline constexpr std::uintptr_t kApplicationQuitRequestRva=0x3F5ADC0;
inline constexpr std::size_t kApplicationQuitFlagOffset=0x89;
using ApplicationQuitRequestV1=void (*)(void *);
struct ApplicationExitBindingsV1 {
  bool enabled=false;
  void *const *application_slot=nullptr;
  ApplicationQuitRequestV1 request_quit=nullptr;
  std::uintptr_t expected_application_vtable=0, alternative_application_vtable=0;
};
struct ApplicationExitSessionV1 {
  // Bridge/process lifetime; reconnect, timeout and a failed ACK never reset it.
  std::atomic<bool> claimed{false};
};
enum class ApplicationExitStatusV1 {
  unavailable, admission_rejected, already_requested, requested, indeterminate, claim_consumed
};
using BeforeApplicationExitV1=bool (*)(void *) noexcept;
ApplicationExitBindingsV1 BindApplicationExitImageV1(
    std::uintptr_t image_base,std::string_view executable_sha256) noexcept;
// This is a native application request only. Natural process termination and
// cleanup belong to Runtime; no GUI, OS message, save, or forced termination.
ApplicationExitStatusV1 RequestApplicationExitV1(
    const ApplicationExitBindingsV1 &,ApplicationExitSessionV1 &,
    BeforeApplicationExitV1,void *) noexcept;
}
