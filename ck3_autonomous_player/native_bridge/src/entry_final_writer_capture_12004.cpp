#include "xar_bridge/entry_final_writer_capture_12004.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/person_natural_lineage_clock_12004.hpp"

#include <cstring>
#include <limits>
#include <mutex>

namespace xar::ck3_12004 {
namespace {
static_assert(sizeof(std::uintptr_t) == 8);
std::mutex g_bindings_mutex;
EntryFinalWriterCaptureBindings12004 g_bindings;
thread_local EntryFinalWriterCaptureScope12004 *g_current = nullptr;

std::optional<std::uintptr_t> Add(std::uintptr_t base,
                                std::uintptr_t offset) noexcept {
  if (base == 0 || base > std::numeric_limits<std::uintptr_t>::max() - offset)
    return std::nullopt;
  return base + offset;
}

template <class T> std::optional<T> Copy(
    const EntryFinalWriterCaptureBindings12004 &bindings,
    std::uintptr_t base, std::uintptr_t offset) noexcept {
  const auto address = Add(base, offset);
  T value{};
  if (!address || !Add(*address, sizeof(T) - 1) || !bindings.read_memory ||
      !bindings.read_memory(bindings.read_context,
                            reinterpret_cast<const void *>(*address),
                            &value, sizeof(value)))
    return std::nullopt;
  return value;
}

template <class T> std::optional<T> EntryField(
    const EntryFinalWriterCaptureBindings12004 &bindings,
    std::uintptr_t entry, const std::optional<EntryFinalCacheImage12004> &image,
    std::size_t offset) noexcept {
  if (!image) return Copy<T>(bindings, entry, offset);
  T value{};
  std::memcpy(&value, image->data() + offset, sizeof(value));
  return value;
}

bool EventEqual(const PersonInstalledTransferEvent12004 &a,
                const PersonInstalledTransferEvent12004 &b) noexcept {
  return a.clock_identity == b.clock_identity && a.sequence == b.sequence &&
         a.thread_id == b.thread_id;
}

std::optional<bool> Ordered(const PersonInstalledTransferEvent12004 &before,
                            const PersonInstalledTransferEvent12004 &after) noexcept {
  if (before.clock_identity == 0 || after.clock_identity == 0 ||
      before.sequence == 0 || after.sequence == 0 ||
      !before.thread_id || !after.thread_id)
    return std::nullopt;
  return before.clock_identity == after.clock_identity &&
         before.thread_id == after.thread_id && after.sequence > before.sequence;
}

bool SideEqual(const EntryFinalSideIdentity12004 &a,
               const EntryFinalSideIdentity12004 &b) noexcept {
  return EventEqual(a.occurrence, b.occurrence) &&
         a.side_identity == b.side_identity &&
         a.province_identity == b.province_identity &&
         a.caller_return_rva == b.caller_return_rva &&
         a.caller_return_slot == b.caller_return_slot &&
         a.source_side_index == b.source_side_index;
}

bool SlotEqual(const EntryFinalSidePhysicalSlot12004 &a,
               const EntryFinalSidePhysicalSlot12004 &b) noexcept {
  return a.bucket == b.bucket && a.bucket_index == b.bucket_index &&
         a.traversal_ordinal == b.traversal_ordinal &&
         a.entry_identity == b.entry_identity &&
         a.writer_return_rva == b.writer_return_rva && a.raw_before == b.raw_before;
}

bool ScopeEqual(const EntryFinalWriterActiveScope12004 &a,
                const EntryFinalWriterActiveScope12004 &b) noexcept {
  if (a.parent_identity.has_value() != b.parent_identity.has_value() ||
      a.side_writer.has_value() != b.side_writer.has_value()) return false;
  if (a.parent_identity && !SideEqual(*a.parent_identity, *b.parent_identity))
    return false;
  if (a.side_writer &&
      (!SideEqual(a.side_writer->side, b.side_writer->side) ||
       !SlotEqual(a.side_writer->slot, b.side_writer->slot) ||
       !EventEqual(a.side_writer->begin_event, b.side_writer->begin_event)))
    return false;
  return a.image_base == b.image_base && a.entry_identity == b.entry_identity &&
         a.province_identity == b.province_identity &&
         a.writer_return_rva == b.writer_return_rva && EventEqual(a.begin_event, b.begin_event);
}

bool FieldsComplete(const EntryFinalSixCacheRaw12004 &fields) noexcept {
  return fields.max_size_bits.has_value() && fields.siege_bits.has_value() &&
         fields.damage_bits.has_value() && fields.toughness_bits.has_value() &&
         fields.pursuit_bits.has_value() && fields.screen_bits.has_value();
}

template <class T> std::optional<bool> Equal(const std::optional<T> &a,
                                           const std::optional<T> &b) noexcept {
  if (!a || !b) return std::nullopt;
  return *a == *b;
}
} // namespace

EntryFinalWriterCaptureBindings12004 BindEntryFinalWriterCapture12004(
    std::uintptr_t image_base, std::string_view executable_sha256,
    void *read_context, EntryFinalWriterRead12004 read_memory) noexcept {
  if (image_base == 0 || executable_sha256 != kExecutableSha256) return {};
  return {true, image_base, read_context, read_memory};
}

void ConfigureEntryFinalWriterCapture12004(
    const EntryFinalWriterCaptureBindings12004 &bindings) noexcept {
  try {
    const std::lock_guard lock(g_bindings_mutex);
    g_bindings = bindings;
  } catch (...) {
    // Observation failure does not alter the already owned native original.
  }
}

EntryFinalWriterCaptureScope12004::EntryFinalWriterCaptureScope12004(
    void *entry, void *province, std::uintptr_t caller_return_address) noexcept
    : previous_(g_current) {
  g_current = this;
  record_.writer_scope.entry_identity = reinterpret_cast<std::uintptr_t>(entry);
  record_.writer_scope.province_identity = reinterpret_cast<std::uintptr_t>(province);
  record_.caller_return_address = caller_return_address;
  if (const auto *parent = PeekActiveEntryFinalSideScope12004())
    record_.writer_scope.parent_identity = parent->identity;
  try {
    const std::lock_guard lock(g_bindings_mutex);
    bindings_ = g_bindings;
  } catch (...) {
    record_.reason = "entry_final_writer_bindings_unavailable";
    return;
  }
  record_.exact_build_bound = bindings_.exact_build_bound;
  record_.writer_scope.image_base = bindings_.image_base;
  if (!bindings_.exact_build_bound) {
    record_.reason = "entry_final_writer_exact_build_unbound";
    return;
  }
  record_.writer_scope.begin_event = NextPersonNaturalLineageEvent12004();
  if (caller_return_address != 0 && caller_return_address >= bindings_.image_base)
    record_.writer_scope.writer_return_rva = caller_return_address - bindings_.image_base;
  if (record_.writer_scope.writer_return_rva) {
    try {
      side_slot_scope_.emplace(record_.writer_scope.entry_identity,
          record_.writer_scope.province_identity,
          *record_.writer_scope.writer_return_rva, record_.writer_scope.begin_event);
      if (const auto *scope = PeekActiveEntryFinalSideWriterScope12004();
          scope && record_.writer_scope.parent_identity &&
          SideEqual(scope->side, *record_.writer_scope.parent_identity) &&
          scope->slot.entry_identity == record_.writer_scope.entry_identity &&
          scope->side.province_identity == record_.writer_scope.province_identity &&
          scope->slot.writer_return_rva == *record_.writer_scope.writer_return_rva &&
          EventEqual(scope->begin_event, record_.writer_scope.begin_event))
        record_.writer_scope.side_writer = *scope;
    } catch (...) {
      record_.reason = "entry_final_writer_slot_association_unavailable";
    }
  }
  record_.side_slot_associated = record_.writer_scope.side_writer.has_value();
  record_.entry_before = Copy<EntryFinalCacheImage12004>(
      bindings_, record_.writer_scope.entry_identity, 0);
  record_.requested_regiment_id_before = EntryField<std::uint32_t>(bindings_,
      record_.writer_scope.entry_identity, record_.entry_before, 8);
  record_.final_province_id = Copy<std::int32_t>(
      bindings_, record_.writer_scope.province_identity, 0x10);
  record_.copied_fallback_source_identity = Copy<std::uintptr_t>(
      bindings_, bindings_.image_base, kEntryFinalFallbackSlotRva12004);
}

EntryFinalWriterCaptureScope12004::~EntryFinalWriterCaptureScope12004() {
  g_current = previous_;
}

void EntryFinalWriterCaptureScope12004::EnterOriginal() noexcept {
  if (completed_ || original_active_) return;
  record_.original_called = true;
  original_active_ = true;
}

const EntryFinalWriterActiveScope12004 *
PeekActiveEntryFinalWriterScope12004() noexcept {
  if (!g_current || !g_current->original_active_ ||
      !g_current->record_.exact_build_bound) return nullptr;
  return &g_current->record_.writer_scope;
}

bool NotifyEntryFinalWriterReturnedRecord12004(
    const EntryFinalGetterReturnedRecord12004 &child) noexcept {
  const auto *active = PeekActiveEntryFinalWriterScope12004();
  if (!active) return false;
  auto &record = g_current->record_;
  if (record.returned_record || !child.original_called || !child.original_returned ||
      child.caller_return_rva != kEntryFinalGetterReturnRva12004 ||
      child.actual_province_identity != active->province_identity ||
      !ScopeEqual(child.writer_scope, *active) ||
      !Ordered(active->begin_event, child.begin_event).value_or(false) ||
      !Ordered(child.begin_event, child.completed_event).value_or(false)) {
    ++record.child_records_rejected;
    return false;
  }
  record.returned_record = child;
  ++record.child_records_accepted;
  record.actual_resolved_regiment_full_id = Copy<std::uint32_t>(
      g_current->bindings_, child.actual_resolved_regiment_identity, 0x10);
  if (record.copied_fallback_source_identity)
    record.resolved_identity_matches_copied_fallback =
        child.actual_resolved_regiment_identity == *record.copied_fallback_source_identity;
  record.resolved_full_id_matches_requested = Equal(
      record.actual_resolved_regiment_full_id, record.requested_regiment_id_before);
  return true;
}

void EntryFinalWriterCaptureScope12004::Complete(
    std::uint64_t original_return_bits) noexcept {
  if (completed_ || !original_active_) return;
  original_active_ = false;
  completed_ = true;
  record_.original_returned = true;
  record_.original_return_bits = original_return_bits;
  if (bindings_.exact_build_bound) {
    record_.completed_event = NextPersonNaturalLineageEvent12004();
    record_.entry_after = Copy<EntryFinalCacheImage12004>(
        bindings_, record_.writer_scope.entry_identity, 0);
    record_.requested_regiment_id_after = EntryField<std::uint32_t>(bindings_,
        record_.writer_scope.entry_identity, record_.entry_after, 8);
    auto &cache = record_.entry_cache_after;
    cache.max_size_bits = EntryField<std::uint32_t>(bindings_,
        record_.writer_scope.entry_identity, record_.entry_after, 0x30);
    cache.siege_bits = EntryField<std::uint64_t>(bindings_,
        record_.writer_scope.entry_identity, record_.entry_after, 0x38);
    cache.damage_bits = EntryField<std::uint64_t>(bindings_,
        record_.writer_scope.entry_identity, record_.entry_after, 0x40);
    cache.toughness_bits = EntryField<std::uint64_t>(bindings_,
        record_.writer_scope.entry_identity, record_.entry_after, 0x48);
    cache.pursuit_bits = EntryField<std::uint64_t>(bindings_,
        record_.writer_scope.entry_identity, record_.entry_after, 0x50);
    cache.screen_bits = EntryField<std::uint64_t>(bindings_,
        record_.writer_scope.entry_identity, record_.entry_after, 0x58);
  }
  record_.entry_images_copy_complete = record_.entry_before.has_value() && record_.entry_after.has_value();
  record_.entry_cache_after_copy_complete = FieldsComplete(record_.entry_cache_after);
  record_.requested_handle_preserved = Equal(record_.requested_regiment_id_before,
                                             record_.requested_regiment_id_after);
  record_.writer_event_order_proven = Ordered(record_.writer_scope.begin_event, record_.completed_event);
  if (record_.returned_record) {
    const auto &child = *record_.returned_record;
    const auto &source = child.returned_fields;
    const auto &cache = record_.entry_cache_after;
    record_.returned_fields_copy_complete = FieldsComplete(source);
    record_.returned_fields_match_entry_after = {
        Equal(source.max_size_bits, cache.max_size_bits), Equal(source.siege_bits, cache.siege_bits),
        Equal(source.damage_bits, cache.damage_bits), Equal(source.toughness_bits, cache.toughness_bits),
        Equal(source.pursuit_bits, cache.pursuit_bits), Equal(source.screen_bits, cache.screen_bits)};
    bool known = true, equal = true;
    for (const auto &match : record_.returned_fields_match_entry_after) {
      known = known && match.has_value();
      equal = equal && match.value_or(false);
    }
    if (known) record_.all_returned_fields_match_entry_after = equal;
    record_.original_return_matches_returned_screen = Equal(record_.original_return_bits, source.screen_bits);
    record_.getter_completed_before_writer_return = Ordered(child.completed_event, record_.completed_event);
  }
  const auto *parent = PeekActiveEntryFinalSideScope12004();
  if (record_.writer_scope.parent_identity)
    record_.parent_identity_matches_completion_scope = parent &&
        SideEqual(*record_.writer_scope.parent_identity, parent->identity);
  record_.six_cache_writeback_observed = record_.returned_fields_copy_complete &&
      record_.entry_cache_after_copy_complete &&
      record_.writer_event_order_proven.value_or(false) &&
      record_.getter_completed_before_writer_return.value_or(false) &&
      record_.all_returned_fields_match_entry_after.value_or(false);
  record_.side_slot_six_cache_writeback_observed = record_.six_cache_writeback_observed &&
      record_.side_slot_associated && record_.parent_identity_matches_completion_scope.value_or(false);
  if (!record_.exact_build_bound) record_.reason = "entry_final_writer_exact_build_unbound";
  else if (!bindings_.read_memory) record_.reason = "entry_final_writer_reader_unavailable";
  else if (!record_.writer_scope.parent_identity) record_.reason = "entry_final_writer_side_parent_unobserved";
  else if (!record_.side_slot_associated) record_.reason = "entry_final_writer_physical_slot_unassociated";
  else if (!record_.returned_record) record_.reason = "entry_final_writer_getter_return_unobserved";
  else if (!record_.all_returned_fields_match_entry_after) record_.reason = "entry_final_writer_cache_copy_partial";
  else if (!*record_.all_returned_fields_match_entry_after) record_.reason = "entry_final_writer_cache_postimage_differs";
  else if (!record_.writer_event_order_proven.value_or(false) ||
           !record_.getter_completed_before_writer_return.value_or(false))
    record_.reason = "entry_final_writer_clock_order_unproven";
  else if (!record_.entry_images_copy_complete) record_.reason = "entry_final_writer_images_partial";
  else record_.reason = "entry_final_writer_returned_cache_copies_match";
  if (record_.parent_identity_matches_completion_scope.value_or(false))
    AppendEntryFinalSideWriterRecord12004(record_);
}

} // namespace xar::ck3_12004
