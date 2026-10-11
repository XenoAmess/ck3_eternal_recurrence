#pragma once

#include "xar_bridge/piety_price_numeric_access_12004.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string_view>
#include <vector>

namespace xar::ck3_12004 {

inline constexpr std::string_view kRiteDynamicJournalSourcePin12004 =
    "3803b0efcfa6cef62c6f86ba7471a0abeed05f6bf5af74544f702f33bb06ce36";
inline constexpr std::uintptr_t kRiteDynamicOriginalCallRva12004 = 0x375438F;
inline constexpr std::uintptr_t kRiteDynamicNormalReturnRva12004 = 0x3754392;
inline constexpr std::uintptr_t kRiteDynamicParentReturnRva12004 = 0x2C62A3D;

// Exact original registers at375437C, before the two displaced MOVs.
struct RiteDynamicPrecallRegisters12004 {
  std::uintptr_t helper_rbp = 0;
  std::uintptr_t expression_receiver_rcx = 0;
  std::uintptr_t vptr_rax = 0;
  std::uintptr_t target_r10 = 0;
  std::uintptr_t definition_rsi = 0;
  std::uintptr_t native_context_r12 = 0;
  std::uintptr_t native_r9_r15 = 0;
  std::uintptr_t helper_out_rdi = 0;
};
using RiteDynamicPrecallCapture12004 =
    void (*)(void *, const RiteDynamicPrecallRegisters12004 &) noexcept;
using RiteDynamicPostcallCapture12004 =
    void (*)(void *, std::uintptr_t helper_rbp,
             std::uint64_t raw_returned_rax) noexcept;

struct RiteDynamicResolvedIdentity12004 {
  bool ready = false;
  std::optional<std::uintptr_t> selected_identity;
  std::optional<std::uint32_t> resolved_full_id;
  bool operator==(const RiteDynamicResolvedIdentity12004 &) const = default;
};

// Original mailbox facts copied by47. Revision/ticket/epoch are metadata;
// none is a native call counter, scope identity or manufactured clock.
struct RiteDynamicQueryBinding12004 {
  bool actual_application_query = false;
  bool mailbox_before_accepted = false;
  std::uint64_t snapshot_revision = 0;
  std::uint64_t query_sequence = 0;
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::int32_t stamp_date_raw = 0;
  bool stamp_paused = false;
  std::uint32_t played_character_id = 0;
  std::uint32_t owning_thread_id = 0;
  std::uintptr_t actual_window = 0;
  std::optional<std::uintptr_t> price_payload_identity;
  RiteDynamicResolvedIdentity12004 first_actor;
  RiteDynamicResolvedIdentity12004 current_rite;
  RiteDynamicResolvedIdentity12004 second_actor;
  bool operator==(const RiteDynamicQueryBinding12004 &) const = default;
};

struct RiteDynamicCallOccurrence12004 {
  // Zero-based index in this owned vector; not an event clock/native sequence.
  std::size_t occurrence_index = 0;
  std::uintptr_t borrowed_scope_identity = 0;
  std::uint32_t pre_thread_id = 0;
  std::optional<std::uint32_t> post_thread_id;
  RiteDynamicPrecallRegisters12004 pre;
  std::optional<std::uintptr_t> description_pointer;
  std::optional<std::uintptr_t> parent_return_address;
  std::optional<std::uintptr_t> parent_actor;
  std::optional<std::uintptr_t> parent_current_rite;
  std::optional<std::uintptr_t> parent_term_output;
  std::optional<std::uintptr_t> parent_detail;
  std::optional<std::uint32_t> actor_full_id_raw_u32;
  std::optional<std::uint32_t> rite_full_id_raw_u32;
  // Same literal cells used by the existing parent readonly prefix. These are
  // copied operands; they do not stand in for the physical R12 context bytes.
  std::optional<std::uint32_t> actor_context_key_raw_u32;
  std::optional<std::uint32_t> rite_context_key_raw_u32;
  std::optional<std::uint32_t> rite_link_full_id_raw_u32;
  std::optional<std::uint32_t> rite_link_context_key_raw_u32;
  std::optional<std::uint32_t> post_actor_full_id_raw_u32;
  std::optional<std::uint32_t> post_rite_full_id_raw_u32;
  bool pairing_ambiguous = false;
  bool normal_return_observed = false;
  std::uintptr_t observed_normal_return_rva = 0;
  // Opaque virtual-return bits are independent of the signed local output.
  std::optional<std::uint64_t> raw_returned_rax;
  std::optional<std::int64_t> local_output_raw_q64;
};

struct RiteDynamicCallJournalSnapshot12004 {
  std::string_view source_pin = kRiteDynamicJournalSourcePin12004;
  RiteDynamicQueryBinding12004 binding;
  std::uintptr_t module_base = 0;
  // Address identity is borrowed only while the exact scope is alive. Retained
  // provenance must never dereference it or use it as a durable unique token.
  std::uintptr_t borrowed_scope_identity = 0;
  std::uint32_t scope_thread_id = 0;
  bool scope_started = false;
  bool scope_closed = false;
  bool allocation_failed = false;
  bool capacity_exceeded = false;
  bool reentrant_callback_rejected = false;
  bool thread_mismatch_observed = false;
  std::size_t dropped_pre_count = 0;
  std::size_t unmatched_post_count = 0;
  std::vector<RiteDynamicCallOccurrence12004> occurrences;
};

// One automatic object surrounds the already existing ordinary quote and its
// readonly source completion. It owns copied records and borrows the reader.
// Nested scopes restore the previous TLS pointer; copy/move is prohibited.
class RiteDynamicCallJournalScope12004 {
public:
  static constexpr std::size_t maximum_occurrences = 256;
  RiteDynamicCallJournalScope12004(
      const piety_price_raw_inputs::PietyPriceNumericAccess12004 &,
      const RiteDynamicQueryBinding12004 &) noexcept;
  ~RiteDynamicCallJournalScope12004() noexcept;
  RiteDynamicCallJournalScope12004(const RiteDynamicCallJournalScope12004 &) = delete;
  RiteDynamicCallJournalScope12004 &operator=(const RiteDynamicCallJournalScope12004 &) = delete;
  RiteDynamicCallJournalScope12004(RiteDynamicCallJournalScope12004 &&) = delete;
  RiteDynamicCallJournalScope12004 &operator=(RiteDynamicCallJournalScope12004 &&) = delete;

  const RiteDynamicCallJournalSnapshot12004 &Snapshot() const noexcept;
  // Closes TLS capture before moving owned records. Call only on owning thread.
  RiteDynamicCallJournalSnapshot12004 TakeSnapshot() noexcept;
  void Close() noexcept;
  bool IsBorrowedCurrentScope() const noexcept;

private:
  friend void CaptureRiteDynamicPrecall12004(
      void *, const RiteDynamicPrecallRegisters12004 &) noexcept;
  friend void CaptureRiteDynamicPostcall12004(
      void *, std::uintptr_t, std::uint64_t) noexcept;
  friend bool IsBorrowedRiteDynamicSnapshot12004(
      const RiteDynamicCallJournalSnapshot12004 &) noexcept;
  void CapturePre(const RiteDynamicPrecallRegisters12004 &) noexcept;
  void CapturePost(std::uintptr_t, std::uint64_t) noexcept;

  piety_price_raw_inputs::PietyPriceNumericAccess12004 access_;
  RiteDynamicCallJournalSnapshot12004 snapshot_;
  RiteDynamicCallJournalScope12004 *previous_ = nullptr;
  std::array<bool, maximum_occurrences> pending_{};
  bool attached_ = false;
  bool in_callback_ = false;
};

// Process-lifetime function addresses; observer capture_context may be nullptr.
// They consult only the current owning-thread borrowed TLS scope. With no scope
// they return immediately and never read game memory or invoke a native call.
void CaptureRiteDynamicPrecall12004(
    void *, const RiteDynamicPrecallRegisters12004 &) noexcept;
void CaptureRiteDynamicPostcall12004(
    void *, std::uintptr_t helper_rbp, std::uint64_t raw_returned_rax) noexcept;
bool IsBorrowedRiteDynamicSnapshot12004(
    const RiteDynamicCallJournalSnapshot12004 &) noexcept;

} // namespace xar::ck3_12004
