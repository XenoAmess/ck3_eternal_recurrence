#pragma once

#include "xar_bridge/active_scheme_state_v1_private_observer.hpp"

#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::bridge {

// These native views are call-local leases. They may be passed only to the
// callbacks below and are never copied into the observation or retained by
// the adapter between calls.
struct ActiveSchemeStateV1PrivateSourceFrame {
  std::uint64_t capture_epoch = 0;
  std::int64_t date_raw = 0;
  std::int64_t played_character_id = 0;
  bool paused = false;
};

struct ActiveSchemeStateV1PrivateSourceRoot {
  bool identity_round_trip = false;
  std::uintptr_t native_address = 0;
  std::uint64_t identity = 0;
  std::uint64_t generation = 0;
};

struct ActiveSchemeStateV1PrivateSourceContainer {
  bool identity_round_trip = false;
  std::uintptr_t native_address = 0;
  std::uint64_t identity = 0;
  std::uint64_t generation = 0;
  std::int64_t owner_character_id = 0;
  std::size_t row_count = 0;
};

enum class ActiveSchemeStateV1PrivateSourceFailure : std::uint8_t {
  none,
  exact_build_mismatch,
  callbacks_unavailable,
  not_application_main_thread,
  frame_unavailable,
  not_paused,
  frame_invalid,
  root_unavailable,
  container_unavailable,
  row_count_invalid,
  row_unavailable,
  root_drift,
  container_drift,
  row_drift,
  frame_drift,
  core_rejected,
};

using CaptureActiveSchemeStateV1PrivateSourceFrame = bool (*)(
    void *context,
    ActiveSchemeStateV1PrivateSourceFrame &output) noexcept;
using ResolveActiveSchemeStateV1PrivateSourceRoot = bool (*)(
    void *context, std::int64_t played_character_id,
    ActiveSchemeStateV1PrivateSourceRoot &output) noexcept;
using ResolveActiveSchemeStateV1PrivateSourceContainer = bool (*)(
    void *context, const ActiveSchemeStateV1PrivateSourceRoot &root,
    std::int64_t played_character_id,
    ActiveSchemeStateV1PrivateSourceContainer &output) noexcept;
using ReadActiveSchemeStateV1PrivateSourceRow = bool (*)(
    void *context, const ActiveSchemeStateV1PrivateSourceRoot &root,
    const ActiveSchemeStateV1PrivateSourceContainer &container,
    std::size_t index,
    ActiveSchemeStateV1PrivateCapturedRow &output) noexcept;

struct ActiveSchemeStateV1PrivateSourceAccess {
  bool exact_build_admitted = false;
  std::string_view admitted_executable_sha256{};
  std::uint32_t current_thread_id = 0;
  std::uint32_t application_main_thread_id = 0;
  void *context = nullptr;
  CaptureActiveSchemeStateV1PrivateSourceFrame capture_frame = nullptr;
  ResolveActiveSchemeStateV1PrivateSourceRoot resolve_root = nullptr;
  ResolveActiveSchemeStateV1PrivateSourceContainer resolve_container =
      nullptr;
  ReadActiveSchemeStateV1PrivateSourceRow read_row = nullptr;
};

struct ActiveSchemeStateV1PrivateSourceResult {
  ActiveSchemeStateV1PrivateSourceFailure failure =
      ActiveSchemeStateV1PrivateSourceFailure::callbacks_unavailable;
  ActiveSchemeStateV1PrivateFailure core_failure =
      ActiveSchemeStateV1PrivateFailure::source_adapter_unavailable;
  ActiveSchemeStateV1PrivateObservation observation{};
};

// Performs one synchronous, paused, application-main transaction. Root and
// container resolution are repeated after enumeration; every row is then
// copied a second time through the newly resolved lease. No native address is
// cached or published. Shared bridge glue must supply the exact-build callback
// bindings before this private adapter can be used against CK3.
bool ObserveActiveSchemeStateV1PrivateSource(
    const ActiveSchemeStateV1PrivateSourceAccess &access,
    ActiveSchemeStateV1PrivateSourceResult &output) noexcept;

std::string_view ActiveSchemeStateV1PrivateSourceFailureName(
    ActiveSchemeStateV1PrivateSourceFailure failure) noexcept;

} // namespace xar::bridge
