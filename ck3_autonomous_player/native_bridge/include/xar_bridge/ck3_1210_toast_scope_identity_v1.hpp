#pragma once
#include "xar_bridge/ck3_1210.hpp"
#include <array>

namespace xar::ck3_1210 {
struct ToastObjectMemoryReaderV1;
// Private operand decoder only. A caller must already hold the public query's
// exact Full/application-owner/TLS custody and a stable saved-context capture.
// It accepts no role/name/expected character or financial fact from the caller.
enum class ToastScopeKindV1 { unsupported,character,story };
enum class ToastScopeIdentityStatusV1 { unavailable,unsupported,available };
struct ToastScopeIdentityBindingsV1 {
  std::uintptr_t module_base=0;
  bool exact_build_admitted=false;
};
struct ToastScopeIdentityWitnessV1 {
  std::uintptr_t storage=0,slots=0,object=0;
  std::uint32_t capacity=0,full_id=0,magic=0;
  bool operator==(const ToastScopeIdentityWitnessV1 &) const=default;
};
struct ToastScopeIdentityV1 {
  ToastScopeIdentityStatusV1 status=ToastScopeIdentityStatusV1::unavailable;
  ToastScopeKindV1 kind=ToastScopeKindV1::unsupported;
  std::uint16_t observed_tag=0;
  std::uint32_t full_id=0;
  // Memory operands remain private; no pointer is a public identity.
  ToastScopeIdentityWitnessV1 witness{};
  std::string_view unavailable_reason;
  bool operator==(const ToastScopeIdentityV1 &) const=default;
};
ToastScopeIdentityBindingsV1 BindToastScopeIdentityImageV1(std::uintptr_t,std::string_view) noexcept;
// Resolves only tag4 Character/tag0x16 Story using the canonical storage and
// complete generation-bearing ID plus type marker. Unknown tags remain unknown.
// The low-word tag rule follows the exact native decoder; upper token header
// bytes are retained by the caller's complete capture, never reinterpreted.
bool ReadToastScopeIdentityV1(const ToastScopeIdentityBindingsV1 &,
    const std::array<std::byte,16> &,const ToastObjectMemoryReaderV1 &,ToastScopeIdentityV1 &) noexcept;
} // namespace xar::ck3_1210
