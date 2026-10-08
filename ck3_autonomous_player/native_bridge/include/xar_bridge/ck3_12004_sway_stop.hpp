#pragma once

#include "xar_bridge/ck3_12004_commands.hpp"
#include "xar_bridge/ck3_12004_sway_terminal.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::ck3_12004 {

// Root paired642B capture 2026-10-08T06:23:42Z. Constructor RIP operands,
// clone agreement and the actual clone/execute vtable slots supplied these.
struct SwayStopCommandProfile12004 {
  std::string_view executable_sha256;
  std::uintptr_t primary_vtable_rva = 0;
  std::uintptr_t secondary_vtable_rva = 0;
};
inline constexpr SwayStopCommandProfile12004 kSwayStopCommandProfile12004{
    kExecutableSha256, 74902848, 74902400}; // 0x476ED40 / 0x476EB80
inline constexpr std::uintptr_t kSwayStopCloneRva12004 = 43633056; // 0x299C9A0
inline constexpr std::uintptr_t kSwayStopExecuteRva12004 = 43631392; // 0x299C320
inline constexpr std::string_view kSwayStopStep12004 =
    "stop-active-scheme-sway-v1-private";

struct SwayStopBindings12004 {
  bool enabled = false;
  ck3_12002::CommandBindings commands{};
  ck3_12002::SwayCompletionBindings12002 terminal{};
  std::uintptr_t primary_vtable = 0;
  std::uintptr_t secondary_vtable = 0;
};

struct SwayStopRequest12004 {
  ck3_12002::SwayCompletionRequestV1 instance{};
  std::uint32_t scheme_instance_generation = 0;
  std::int32_t expected_date_raw = 0;
};
struct SwayStopMailboxContext12004 {
  ck3_12002::QueryMailboxEnvelope envelope{};
  SwayStopBindings12004 bindings{};
  SwayStopRequest12004 request{};
  ck3_12002::SwayCompletionStateV1 before{};
  ck3_12002::CommandSubmitResult result = ck3_12002::CommandSubmitResult::unavailable;
  std::string action_id{};
  bool completed = false;
  std::string failure{};
};

// Native CCancelSchemeConfirmation's caller-owned source, not a game allocation.
struct alignas(8) SelectedEndSchemeCommand12004 {
  std::uintptr_t primary_vtable = 0;
  std::uint8_t flags = 0;
  std::array<std::byte, 15> metadata{};
  std::uintptr_t secondary_vtable = 0;
  std::uint32_t scheme_id = 0xFFFFFFFFu;
  std::uint32_t padding = 0;
};
static_assert(sizeof(SelectedEndSchemeCommand12004) == 0x28);
static_assert(offsetof(SelectedEndSchemeCommand12004, secondary_vtable) == 0x18);
static_assert(offsetof(SelectedEndSchemeCommand12004, scheme_id) == 0x20);

SwayStopBindings12004 BindSwayStopImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256,
    const SwayStopCommandProfile12004 &profile = kSwayStopCommandProfile12004) noexcept;

// Call in the existing owning mailbox stamp. A submitted result is pending
// only; the existing independent terminal read must establish the later state.
ck3_12002::CommandSubmitResult SubmitSelectedSwayStop12004(
    const SwayStopBindings12004 &bindings,
    const SwayStopRequest12004 &request,
    ck3_12002::SwayCompletionStateV1 &before) noexcept;

bool ExecuteSelectedSwayStop12004(void *,
    const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
std::string SerializeSelectedSwayStop12004(const SwayStopMailboxContext12004 &,
    std::string_view request_id, const game::AdapterDescriptor &);
bool HandleSelectedSwayStop12004(const game::GameAdapter &,
    ck3_11906::MainThreadQueryMailboxV1 &, const game::Snapshot &published,
    std::uint64_t revision, std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized, std::string &failure) noexcept;

} // namespace xar::ck3_12004
