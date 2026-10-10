#include "army_monthfirst_cleanup_stage_12004.hpp"

#include <algorithm>
#include <bit>
#include <iterator>
#include <limits>
#include <unordered_map>

namespace xar::game {
namespace {
constexpr std::uint32_t kRegiMagic = 0x52656769U;
constexpr std::uint64_t kResetDate = 0xFFFFFFFF029C77F8ULL;
std::int32_t SignedLow32(std::uint64_t value) {
  return std::bit_cast<std::int32_t>(static_cast<std::uint32_t>(value));
}
bool HasPair(const ArmyMonthfirstCleanupRecord12004 &record) {
  return record.requested_full_id.has_value() && record.ordinal.has_value();
}
bool Overlap(std::uintptr_t a, std::size_t length, std::uintptr_t b,
             std::size_t other_length) {
  // Local representability check, not an invented native bounds predicate.
  if (length == 0 || other_length == 0) return false;
  if (a > std::numeric_limits<std::uintptr_t>::max() - length ||
      b > std::numeric_limits<std::uintptr_t>::max() - other_length) return true;
  return a < b + other_length && b < a + length;
}
} // namespace

ArmyMonthfirstCleanupResult12004 EvaluateArmyMonthfirstCleanupStage12004(
    const ArmyMonthfirstCleanupInputs12004 &in) {
  ArmyMonthfirstCleanupResult12004 out{};
  out.backing_records_after_prefix = in.queue.records;
  out.count_after_known_prefix = in.queue.count;
  const auto unavailable = [&](const char *reason) {
    out.unavailable_reason = reason;
    return out;
  };
  if (!in.exact_build_enabled || in.known_mode0_callback == 0)
    return unavailable("cleanup_exact4_binding_unavailable");
  if (in.frame != ArmyMonthfirstCleanupFrame12004::conditional_cleanup_entry)
    return unavailable("cleanup_current_context_is_not_entry_frame");
  if (!in.saved_mask2 || (*in.saved_mask2 != 0 && *in.saved_mask2 != 2))
    return unavailable("cleanup_saved_mask2_unavailable_or_invalid");
  if (*in.saved_mask2 == 0) {
    out.ready = out.returned = out.caller_skipped = out.other_fields_unchanged = true;
    // No source read is required on this caller-skipped leg. An uncaptured
    // unchanged queue remains uncaptured rather than becoming an empty queue.
    out.queue_postimage_ready = in.queue_capture_bounded && in.queue.count &&
        *in.queue.count >= 0 &&
        in.queue.records.size() == static_cast<std::size_t>(*in.queue.count);
    if (out.queue_postimage_ready) out.returned_count = in.queue.count;
    return out;
  }
  if (!in.queue_capture_bounded || !in.queue.count || !in.queue.buffer_address)
    return unavailable("cleanup_queue_header_or_bound_unavailable");
  const auto initial_count = *in.queue.count;
  if (initial_count < 0)
    return unavailable("cleanup_negative_count_native_cursor_not_materialized");
  if (in.queue.records.size() != static_cast<std::size_t>(initial_count))
    return unavailable("cleanup_original_physical_slots_unavailable");
  if (initial_count > 0 && *in.queue.buffer_address == 0)
    return unavailable("cleanup_nonempty_buffer_null");
  std::int32_t live_count = initial_count;
  std::unordered_map<std::uintptr_t, std::uint64_t> date_values;
  std::unordered_map<std::uintptr_t, std::uint64_t> original_dates;
  // The native RBX endpoint is fixed at entry; removed slots remain materialized.
  for (std::int32_t outer = initial_count; outer > 0;) {
    --outer;
    out.visited_outer_physical_indices.push_back(outer);
    auto &record = out.backing_records_after_prefix[static_cast<std::size_t>(outer)];
    if (!HasPair(record)) return unavailable("cleanup_outer_raw_pair_unavailable");
    const auto requested = *record.requested_full_id;
    const auto ordinal = *record.ordinal;
    const auto selected = std::find_if(in.regi.begin(), in.regi.end(),
        [requested](const auto &row) { return row.requested_full_id == requested; });
    if (selected == in.regi.end() || !selected->selection_ready ||
        selected->selected_address == 0 || !selected->magic_14)
      return unavailable("cleanup_regi_selection_or_magic_unavailable");
    if (!selected->used_native_fallback &&
        (!selected->indexed_full_id || *selected->indexed_full_id != requested))
      return unavailable("cleanup_registry_generation_evidence_unavailable");
    bool invalid = *selected->magic_14 != kRegiMagic;
    if (!invalid) {
      if (!selected->selected_full_id)
        return unavailable("cleanup_selected_full_id_unavailable");
      invalid = *selected->selected_full_id == 0xFFFFFFFFU;
    }
    if (!invalid) {
      const auto chunk = std::find_if(in.chunks.begin(), in.chunks.end(),
          [requested, ordinal](const auto &row) {
            return row.requested_full_id == requested && row.ordinal == ordinal;
          });
      if (chunk == in.chunks.end() || !chunk->computed_address)
        return unavailable("cleanup_computed_chunk_pointer_unavailable");
      const auto expected = selected->selected_address + std::uintptr_t{0x18} +
          static_cast<std::uintptr_t>(static_cast<std::int64_t>(ordinal) * 36);
      if (*chunk->computed_address != expected)
        return unavailable("cleanup_computed_chunk_address_disagrees_with_source");
      // Source has no ordinal range gate, including its literal null-address leg.
      if (*chunk->computed_address != 0) {
        const auto address = *chunk->computed_address;
        if (Overlap(address + 0x1C, 8, *in.queue.buffer_address,
                    static_cast<std::size_t>(initial_count) * 16) ||
            Overlap(address + 0x1C, 8, in.primary_address + 0x468, 0x10))
          return unavailable("cleanup_date_queue_storage_overlap_not_materialized");
        if (chunk->date_1c_raw64) {
          const auto [it, inserted] = original_dates.emplace(address, *chunk->date_1c_raw64);
          if (!inserted && it->second != *chunk->date_1c_raw64)
            return unavailable("cleanup_alias_entry_dates_disagree");
        }
        auto date = date_values.find(address);
        if (date == date_values.end()) {
          if (!chunk->date_1c_raw64)
            return unavailable("cleanup_chunk_date_unavailable");
          date = date_values.emplace(address, *chunk->date_1c_raw64).first;
        }
        if (!in.passed_date_raw64)
          return unavailable("cleanup_passed_date_unavailable");
        if (SignedLow32(*in.passed_date_raw64) < SignedLow32(date->second)) continue;
        // Signed ordinals are preserved; these concrete overlaps would modify
        // captured generation/magic or manager fields which this narrow date
        // overlay cannot then use unchanged at the next source read.
        for (const auto &regi : in.regi) {
          if (regi.selected_address && Overlap(address + 0x1C, 8,
                                               regi.selected_address + 0x10, 8))
            return unavailable("cleanup_date_resolution_storage_overlap_not_materialized");
        }
        for (const auto offset : {std::uintptr_t{0x30}, std::uintptr_t{0x3C},
                                  std::uintptr_t{0x148}, std::uintptr_t{0x158},
                                  std::uintptr_t{0x164}}) {
          if (Overlap(address + 0x1C, 8, in.primary_address + offset, 8))
            return unavailable("cleanup_date_manager_storage_overlap_not_materialized");
        }
        out.date_writes_before_block.push_back({outer, address, date->second, kResetDate});
        date->second = kResetDate;
      }
    }
    const auto old_count = live_count;
    std::int32_t position = 0, shrunk_count = live_count;
    while (position != shrunk_count) {
      auto &row = out.backing_records_after_prefix[static_cast<std::size_t>(position)];
      if (!HasPair(row)) return unavailable("cleanup_removal_scan_raw_pair_unavailable");
      if (*row.requested_full_id == requested && *row.ordinal == ordinal) {
        --shrunk_count;
        const auto &last = out.backing_records_after_prefix[static_cast<std::size_t>(shrunk_count)];
        if (!HasPair(last)) return unavailable("cleanup_swap_last_raw_pair_unavailable");
        // Actual source copies only DWORD08/C. Physical record/vtable identities
        // and targets stay in their original slots, including removed backing slots.
        row.requested_full_id = last.requested_full_id;
        row.ordinal = last.ordinal;
      } else {
        ++position;
      }
    }
    // Literal resize2634C80(start=newCount,end=oldCount). No tail-copy leg is
    // reached here. Unknown callbacks stop before the helper's count store.
    for (auto slot = shrunk_count; slot < old_count; ++slot) {
      const auto &removed = out.backing_records_after_prefix[static_cast<std::size_t>(slot)];
      if (!removed.actual_slot0_target ||
          *removed.actual_slot0_target != in.known_mode0_callback) {
        out.blocked_callback_physical_index = slot;
        out.blocked_callback_target = removed.actual_slot0_target;
        return unavailable("cleanup_reached_record_callback_effect_unavailable");
      }
      out.completed_mode0_callback_physical_indices.push_back(slot);
    }
    live_count = shrunk_count;
    out.count_after_known_prefix = live_count;
  }
  out.ready = out.returned = out.queue_postimage_ready = out.other_fields_unchanged = true;
  out.returned_count = live_count;
  return out;
}
} // namespace xar::game

namespace xar::ck3_12004 {
namespace {
constexpr std::string_view kExactSha =
    "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";
template<class T> std::optional<T> Read(const ArmyMonthfirstCleanupReadView12004 &m,
                                      std::uintptr_t address) {
  T value{};
  if (!address || !m.read_bytes ||
      !m.read_bytes(m.context, address, &value, sizeof(value))) return std::nullopt;
  return value;
}
game::ArmyMonthfirstCleanupRegi12004 CaptureRegi(
    const ArmyMonthfirstCleanupBindings12004 &b,
    const ArmyMonthfirstCleanupReadView12004 &m, std::uint32_t requested) {
  game::ArmyMonthfirstCleanupRegi12004 out{};
  out.requested_full_id = requested;
  const auto registry = Read<std::uintptr_t>(m, b.regi_registry_slot);
  if (!registry) { out.unavailable_reason = "cleanup_registry_unavailable"; return out; }
  if (*registry) {
    const auto count = Read<std::uint32_t>(m, *registry + 0x2C);
    if (!count) { out.unavailable_reason = "cleanup_registry_count_unavailable"; return out; }
    const auto index = requested & 0xFFFFFFU;
    if (index < *count) {
      const auto data = Read<std::uintptr_t>(m, *registry + 0x20);
      if (!data || !*data) { out.unavailable_reason = "cleanup_registry_table_unavailable"; return out; }
      const auto payload = Read<std::uintptr_t>(m, *data + index * std::uintptr_t{16} + 8);
      if (!payload) { out.unavailable_reason = "cleanup_registry_payload_unavailable"; return out; }
      if (*payload) {
        out.indexed_full_id = Read<std::uint32_t>(m, *payload + 0x10);
        if (!out.indexed_full_id) { out.unavailable_reason = "cleanup_registry_generation_unavailable"; return out; }
        if (*out.indexed_full_id == requested) out.selected_address = *payload;
      }
    }
  }
  if (!out.selected_address) {
    out.used_native_fallback = true;
    const auto fallback = Read<std::uintptr_t>(m, b.regi_fallback_slot);
    if (!fallback || !*fallback) { out.unavailable_reason = "cleanup_fallback_unavailable_or_null"; return out; }
    out.selected_address = *fallback;
  }
  out.magic_14 = Read<std::uint32_t>(m, out.selected_address + 0x14);
  if (!out.magic_14) { out.unavailable_reason = "cleanup_regi_magic_unavailable"; return out; }
  if (*out.magic_14 == 0x52656769U) {
    out.selected_full_id = Read<std::uint32_t>(m, out.selected_address + 0x10);
    if (!out.selected_full_id) { out.unavailable_reason = "cleanup_selected_full_id_unavailable"; return out; }
  }
  out.selection_ready = true;
  return out;
}
} // namespace

ArmyMonthfirstCleanupBindings12004 BindArmyMonthfirstCleanupStage12004(
    std::uintptr_t image_base, std::string_view sha) noexcept {
  ArmyMonthfirstCleanupBindings12004 out{};
  if (!image_base || sha != kExactSha ||
      image_base > std::numeric_limits<std::uintptr_t>::max() - 0x5D1EB68U) return out;
  out.enabled = true;
  out.image_base = image_base;
  out.regi_registry_slot = image_base + 0x5D1EB68U;
  out.regi_fallback_slot = image_base + 0x5D1EB58U;
  out.known_mode0_callback = image_base + 0x8863D0U;
  return out;
}

game::ArmyMonthfirstCleanupInputs12004 ReadArmyMonthfirstCleanupStage12004(
    const ArmyMonthfirstCleanupBindings12004 &b,
    const ArmyMonthfirstCleanupReadView12004 &m,
    const ArmyMonthfirstCleanupEntry12004 &entry,
    const game::ArmyMonthfirstCleanupQueue12004 *seed) {
  game::ArmyMonthfirstCleanupInputs12004 out{};
  out.frame = entry.frame;
  out.exact_build_enabled = b.enabled;
  out.primary_address = entry.primary_address;
  out.known_mode0_callback = b.known_mode0_callback;
  out.saved_mask2 = entry.saved_mask2;
  out.passed_date_raw64 = entry.passed_date_raw64;
  if (!b.enabled || !m.read_bytes || !entry.primary_address) {
    out.unavailable_reason = "cleanup_read_bindings_or_primary_unavailable";
    return out;
  }
  if (entry.saved_mask2 && *entry.saved_mask2 == 0) return out;
  if (seed) {
    out.queue.buffer_address = seed->buffer_address;
    out.queue.count = seed->count;
    out.reused_same_frame_queue_seed = true;
  } else {
    out.queue.buffer_address = Read<std::uintptr_t>(m, entry.primary_address + 0x468);
    out.queue.count = Read<std::int32_t>(m, entry.primary_address + 0x474);
  }
  if (!out.queue.count || !out.queue.buffer_address || *out.queue.count < 0 ||
      static_cast<std::size_t>(*out.queue.count) > b.kMaximumCapturedRecords) {
    out.unavailable_reason = "cleanup_queue_header_or_capture_bound_unavailable";
    return out;
  }
  const auto count = static_cast<std::size_t>(*out.queue.count);
  if (count && !*out.queue.buffer_address) {
    out.unavailable_reason = "cleanup_nonempty_queue_buffer_null";
    return out;
  }
  if (seed) {
    if (seed->records.size() != count) {
      out.unavailable_reason = "cleanup_same_frame_seed_shape_unavailable";
      return out;
    }
    out.queue.records = seed->records;
    for (std::size_t i = 0; i < count; ++i) {
      if (out.queue.records[i].record_address != *out.queue.buffer_address + i * 16) {
        out.unavailable_reason = "cleanup_same_frame_seed_physical_slots_disagree";
        return out;
      }
    }
  } else {
    for (std::size_t i = 0; i < count; ++i) {
      game::ArmyMonthfirstCleanupRecord12004 record{};
      record.record_address = *out.queue.buffer_address + i * 16;
      const auto vtable = Read<std::uintptr_t>(m, record.record_address);
      if (vtable) {
        record.vtable_address = *vtable;
        if (*vtable) record.actual_slot0_target = Read<std::uintptr_t>(m, *vtable);
      }
      record.requested_full_id = Read<std::uint32_t>(m, record.record_address + 8);
      record.ordinal = Read<std::int32_t>(m, record.record_address + 0xC);
      out.queue.records.push_back(record);
    }
  }
  if (out.queue.records.size() != count) {
    out.unavailable_reason = "cleanup_same_frame_seed_shape_unavailable";
    return out;
  }
  out.queue_capture_bounded = true;
  std::unordered_map<std::uintptr_t, std::optional<std::uint64_t>> captured_dates;
  for (const auto &record : out.queue.records) {
    if (!record.requested_full_id || !record.ordinal) continue;
    const auto requested = *record.requested_full_id;
    auto selected = std::find_if(out.regi.begin(), out.regi.end(),
        [requested](const auto &row) { return row.requested_full_id == requested; });
    if (selected == out.regi.end()) {
      out.regi.push_back(CaptureRegi(b, m, requested));
      selected = std::prev(out.regi.end());
    }
    if (!selected->selection_ready || !selected->magic_14 ||
        *selected->magic_14 != 0x52656769U || !selected->selected_full_id ||
        *selected->selected_full_id == 0xFFFFFFFFU) continue;
    const auto ordinal = *record.ordinal;
    if (std::any_of(out.chunks.begin(), out.chunks.end(),
        [requested, ordinal](const auto &row) {
          return row.requested_full_id == requested && row.ordinal == ordinal;
        })) continue;
    game::ArmyMonthfirstCleanupChunk12004 chunk{};
    chunk.requested_full_id = requested;
    chunk.ordinal = ordinal;
    const auto address = selected->selected_address + std::uintptr_t{0x18} +
        static_cast<std::uintptr_t>(static_cast<std::int64_t>(ordinal) * 36);
    chunk.computed_address = address;
    if (address) {
      auto date = captured_dates.find(address);
      if (date == captured_dates.end())
        date = captured_dates.emplace(address, Read<std::uint64_t>(m, address + 0x1C)).first;
      chunk.date_1c_raw64 = date->second;
    }
    out.chunks.push_back(chunk);
  }
  return out;
}
} // namespace xar::ck3_12004
