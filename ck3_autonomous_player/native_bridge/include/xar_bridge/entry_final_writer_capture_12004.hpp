#pragma once

#include "xar_bridge/entry_final_cache_postimage_12004.hpp"
#include "xar_bridge/entry_final_side_scope_12004.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace xar::ck3_12004 {

inline constexpr std::uintptr_t kEntryFinalGetterReturnRva12004 = 0x2657AF4;
inline constexpr std::uintptr_t kEntryFinalFallbackSlotRva12004 = 0x5D1F338;

using EntryFinalWriterRead12004 = bool (*)(
    void *, const void *, void *, std::size_t) noexcept;

struct EntryFinalWriterCaptureBindings12004 {
  bool exact_build_bound = false;
  std::uintptr_t image_base = 0;
  void *read_context = nullptr;
  EntryFinalWriterRead12004 read_memory = nullptr;
};

struct EntryFinalSixCacheRaw12004 {
  std::optional<std::uint32_t> max_size_bits;
  std::optional<std::uint64_t> siege_bits;
  std::optional<std::uint64_t> damage_bits;
  std::optional<std::uint64_t> toughness_bits;
  std::optional<std::uint64_t> pursuit_bits;
  std::optional<std::uint64_t> screen_bits;
};

// A real writer occurrence on this thread. Optional Side/slot association
// stays unknown independently of the actual writer and child returned fields.
struct EntryFinalWriterActiveScope12004 {
  std::optional<EntryFinalSideIdentity12004> parent_identity;
  std::optional<EntryFinalSideWriterScope12004> side_writer;
  std::uintptr_t image_base = 0;
  std::uintptr_t entry_identity = 0;
  std::uintptr_t province_identity = 0;
  std::optional<std::uintptr_t> writer_return_rva;
  PersonInstalledTransferEvent12004 begin_event;
};

// Filled only by the natural26344A0 once observer. Fields are copied from the
// actual returned RAX buffer, not from the requested Regiment or a new getter.
struct EntryFinalGetterReturnedRecord12004 {
  EntryFinalWriterActiveScope12004 writer_scope;
  std::uintptr_t actual_resolved_regiment_identity = 0;
  std::uintptr_t actual_output_identity = 0;
  std::uintptr_t actual_province_identity = 0;
  std::uintptr_t caller_return_rva = 0;
  PersonInstalledTransferEvent12004 begin_event;
  PersonInstalledTransferEvent12004 completed_event;
  bool original_called = false;
  bool original_returned = false;
  std::uint64_t raw_return_bits = 0;
  EntryFinalSixCacheRaw12004 returned_fields;
};

struct EntryFinalWriterCaptureRecord12004 {
  EntryFinalWriterActiveScope12004 writer_scope;
  std::uintptr_t caller_return_address = 0;
  bool exact_build_bound = false;
  bool original_called = false;
  bool original_returned = false;
  PersonInstalledTransferEvent12004 completed_event;
  std::optional<std::uint64_t> original_return_bits;
  std::optional<EntryFinalCacheImage12004> entry_before;
  std::optional<EntryFinalCacheImage12004> entry_after;
  std::optional<std::uint32_t> requested_regiment_id_before;
  std::optional<std::uint32_t> requested_regiment_id_after;
  std::optional<std::int32_t> final_province_id;
  std::optional<std::uintptr_t> copied_fallback_source_identity;
  std::optional<std::uint32_t> actual_resolved_regiment_full_id;
  // Pointer equality with a copied fallback is diagnostic; it does not prove
  // which branch selected an aliased Regiment object.
  std::optional<bool> resolved_identity_matches_copied_fallback;
  std::optional<bool> resolved_full_id_matches_requested;
  std::optional<EntryFinalGetterReturnedRecord12004> returned_record;
  std::uint32_t child_records_accepted = 0;
  std::uint32_t child_records_rejected = 0;
  EntryFinalSixCacheRaw12004 entry_cache_after;
  std::array<std::optional<bool>, 6> returned_fields_match_entry_after;
  std::optional<bool> all_returned_fields_match_entry_after;
  std::optional<bool> original_return_matches_returned_screen;
  std::optional<bool> requested_handle_preserved;
  std::optional<bool> parent_identity_matches_completion_scope;
  std::optional<bool> writer_event_order_proven;
  std::optional<bool> getter_completed_before_writer_return;
  bool entry_images_copy_complete = false;
  bool returned_fields_copy_complete = false;
  bool entry_cache_after_copy_complete = false;
  bool side_slot_associated = false;
  bool six_cache_writeback_observed = false;
  bool side_slot_six_cache_writeback_observed = false;
  std::string_view reason = "entry_final_writer_unobserved";
};

EntryFinalWriterCaptureBindings12004 BindEntryFinalWriterCapture12004(
    std::uintptr_t image_base, std::string_view executable_sha256,
    void *read_context, EntryFinalWriterRead12004 read_memory) noexcept;
void ConfigureEntryFinalWriterCapture12004(
    const EntryFinalWriterCaptureBindings12004 &) noexcept;

// Visible only between EnterOriginal and Complete on the actual writer's
// current thread. Nested writers restore their previous lexical scope.
const EntryFinalWriterActiveScope12004 *
PeekActiveEntryFinalWriterScope12004() noexcept;
bool NotifyEntryFinalWriterReturnedRecord12004(
    const EntryFinalGetterReturnedRecord12004 &) noexcept;

class EntryFinalWriterCaptureScope12004 {
public:
  EntryFinalWriterCaptureScope12004(void *entry, void *province,
                                  std::uintptr_t caller_return_address) noexcept;
  ~EntryFinalWriterCaptureScope12004();
  void EnterOriginal() noexcept;
  void Complete(std::uint64_t original_return_bits) noexcept;
  EntryFinalWriterCaptureScope12004(const EntryFinalWriterCaptureScope12004 &) = delete;
  EntryFinalWriterCaptureScope12004 &operator=(const EntryFinalWriterCaptureScope12004 &) = delete;

private:
  EntryFinalWriterCaptureScope12004 *previous_ = nullptr;
  EntryFinalWriterCaptureBindings12004 bindings_;
  std::optional<EntryFinalSideWriterSlotScope12004> side_slot_scope_;
  EntryFinalWriterCaptureRecord12004 record_;
  bool original_active_ = false;
  bool completed_ = false;
  friend const EntryFinalWriterActiveScope12004 *
  PeekActiveEntryFinalWriterScope12004() noexcept;
  friend bool NotifyEntryFinalWriterReturnedRecord12004(
      const EntryFinalGetterReturnedRecord12004 &) noexcept;
};

// Used by the31 owned immutable Side wire; all missing copied facts stay null.
std::string SerializeEntryFinalWriterCapture12004(
    const EntryFinalWriterCaptureRecord12004 &);

} // namespace xar::ck3_12004
