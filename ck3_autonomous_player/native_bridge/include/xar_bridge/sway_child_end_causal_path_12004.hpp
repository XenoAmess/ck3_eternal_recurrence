#pragma once

#include "xar_bridge/sway_complete_branch_12004.hpp"
#include "xar_bridge/sway_end_invocation_12004.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>
#include <type_traits>

namespace xar::ck3_12004 {

inline constexpr std::string_view kSwayChildEndSourceContract12004 =
    "sway_child_end_causal_path_12004_v1";
inline constexpr std::uintptr_t kSwayChildEndReturn12004 = 0x2D67C04;
inline constexpr std::uintptr_t kSwayChildDispatcherReturn12004 = 0x3766146;
inline constexpr std::uintptr_t kSwayToastChildReturn12004 = 0x2CC93CC;
inline constexpr std::size_t kSwayChildNativeReturnCapacity12004 = 32;

struct SwayToastParentStamp12004 {
  std::uint64_t observer_session_identity = 0;
  std::uint32_t owner_thread_id = 0;
  std::uint64_t toast_invocation_id = 0;
  std::uint64_t source_sequence = 0;
};

// Root places a scope around EVERY actual Toast original invocation, including
// ignored/unavailable tuples. Those entries are barriers, so an inner Toast
// can never borrow an outer matching branch. The scope itself invokes no native
// function and retains no game pointer. Original forwarding stays with Root.
class SwayToastParentScope12004 {
public:
  SwayToastParentScope12004(const SwayToastParentStamp12004 &stamp,
      const SwayCompleteBranchSource12004 &source, bool source_captured,
      std::string_view executable_sha256,
      std::uintptr_t saved_toast_original_rva) noexcept;
  ~SwayToastParentScope12004() noexcept;
  SwayToastParentScope12004(const SwayToastParentScope12004 &) = delete;
  SwayToastParentScope12004 &operator=(const SwayToastParentScope12004 &) = delete;
private:
  friend bool CaptureSwayChildNativeReturns12004(std::uintptr_t, std::size_t,
      struct SwayChildNativeReturns12004 &) noexcept;
  friend bool JoinSwayChildEndCausalPath12004(const SwayEndInvocation12004 &,
      const struct SwayChildNativeReturns12004 &,
      struct SwayChildEndCausalRelation12004 &) noexcept;
  SwayToastParentScope12004 *previous_ = nullptr;
  SwayToastParentStamp12004 stamp_{};
  std::uint32_t actor_ = 0xFFFFFFFFu;
  std::uint32_t target_ = 0xFFFFFFFFu;
  std::uint32_t scheme_ = 0xFFFFFFFFu;
  bool matched_ = false;
};

// Copied on the original owning-thread end entry, before forwarding the end
// original. Addresses are relative to the admitted native executable only;
// DLL/helper frames are excluded. Root separately captures _ReturnAddress()
// directly in the typed end wrapper for21's stamp, not inside this helper.
struct SwayChildNativeReturns12004 {
  bool observed = false;
  bool native_returns_truncated = false;
  SwayToastParentStamp12004 parent{};
  std::size_t count = 0;
  std::array<std::uintptr_t, kSwayChildNativeReturnCapacity12004> rvas{};
};
bool CaptureSwayChildNativeReturns12004(std::uintptr_t admitted_image_base,
    std::size_t admitted_image_size, SwayChildNativeReturns12004 &output) noexcept;

// The pure join uses copied21/22 facts plus the copied native return witness.
// It emits a parent-to-original invocation association only. Actual terminal
// state/transition and a named cause remain independent consumer23 predicates.
struct SwayChildEndCausalRelation12004 {
  bool relationship_observed = false;
  std::uint32_t source_contract_version = 0;
  std::uint64_t observer_session_identity = 0;
  std::uint32_t owner_thread_id = 0;
  std::uint64_t branch_source_sequence = 0;
  std::uint64_t parent_toast_invocation_id = 0;
  std::uint64_t end_original_invocation_id = 0;
  std::uintptr_t end_original_rva = 0;
  std::uint32_t actor_character_id = 0xFFFFFFFFu;
  std::uint32_t target_character_id = 0xFFFFFFFFu;
  std::uint32_t scheme_id = 0xFFFFFFFFu;
  std::uint32_t scheme_instance_generation = 0;
  SwayChildNativeReturns12004 native_returns{};
};
static_assert(std::is_trivially_copyable_v<SwayChildNativeReturns12004>);
static_assert(std::is_trivially_copyable_v<SwayChildEndCausalRelation12004>);
bool JoinSwayChildEndCausalPath12004(const SwayEndInvocation12004 &invocation,
    const SwayChildNativeReturns12004 &native_returns,
    SwayChildEndCausalRelation12004 &output) noexcept;

} // namespace xar::ck3_12004
