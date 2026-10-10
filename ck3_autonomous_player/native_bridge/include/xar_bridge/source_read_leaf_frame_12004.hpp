#pragma once
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>

namespace xar::ck3_12004 {
// An existing caller's copied snapshot identity. This is not a new clock,
// a prisoner role adapter, or a returned-value qualification.
struct SourceReadFrame12004 {
  std::string executable_sha256;
  std::uintptr_t module_base = 0;
  std::uint64_t frame_identity = 0;
  std::string snapshot_identity;
  std::uint64_t native_revision = 0, query_sequence = 0, proof_epoch = 0;
  std::optional<std::int32_t> date_raw;
  std::string caller_domain;
  bool caller_snapshot_confirmed = false;
  friend bool operator==(const SourceReadFrame12004 &, const SourceReadFrame12004 &) = default;
};
struct SourceLeafFrame12004 {
  SourceReadFrame12004 read_frame;
  std::uintptr_t producer_rva = 0, receiver_identity = 0, primary_scope_identity = 0;
  std::optional<std::uint16_t> primary_scope_root_word;
  friend bool operator==(const SourceLeafFrame12004 &, const SourceLeafFrame12004 &) = default;
};
using SourceLeafGuardedRead12004 = bool (*)(void *, const void *, void *, std::size_t) noexcept;
struct SourceLeafReadOnlyAccess12004 {
  void *context = nullptr;
  SourceLeafGuardedRead12004 read_memory = nullptr;
};
inline bool SourceReadFrameReady12004(const SourceReadFrame12004 &f) noexcept {
  return f.executable_sha256 == "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518" &&
      f.module_base != 0 && (f.frame_identity != 0 || !f.snapshot_identity.empty()) &&
      !f.caller_domain.empty() && f.caller_snapshot_confirmed;
}
// This guard admits copied inputs only. A leaf must separately qualify every
// reached getter and its returned output before publishing a truth value.
inline bool SourceLeafFrameReady12004(const SourceLeafFrame12004 &f) noexcept {
  return SourceReadFrameReady12004(f.read_frame) && f.producer_rva != 0 &&
      f.receiver_identity != 0 && f.primary_scope_identity != 0;
}
} // namespace xar::ck3_12004
