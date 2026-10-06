#pragma once

#include "xar_bridge/game_contract.hpp"
#include "xar_bridge/army_daily_assault_active_table_collector_v1.inc.hpp"

#include <charconv>
#include <cstring>
#include <unordered_map>

namespace xar::ck3_12003 {
struct CurrentCandidateDetachmentMapperBindings12003 {
  bool enabled = false;
  CurrentDailyAssaultTableBindings12003 lookup{};
  const void *regi_registry_slot = nullptr, *regi_fallback_slot = nullptr;
};
inline CurrentCandidateDetachmentMapperBindings12003 BindCurrentCandidateDetachmentMapper12003(
    std::uintptr_t base, std::string_view sha) noexcept {
  CurrentCandidateDetachmentMapperBindings12003 out{};
  out.lookup = BindCurrentDailyAssaultTable12003(base, sha);
  out.enabled = out.lookup.enabled;
  if (out.enabled) {
    out.regi_registry_slot = reinterpret_cast<const void *>(base + 0x5D1EB68);
    out.regi_fallback_slot = reinterpret_cast<const void *>(base + 0x5D1EB58);
  }
  return out;
}
namespace candidate_mapper_detail {
using daily_assault_table_detail::At;
using daily_assault_table_detail::Read;
using daily_assault_table_detail::Identity;
using daily_assault_table_detail::Finish;
using daily_assault_table_detail::Reason;
using daily_assault_table_detail::Resolved;

inline const void *CapturedPointer(const std::optional<std::string> &identity) {
  if (!identity || !identity->starts_with("native:")) return nullptr;
  std::uintptr_t value{};
  const auto *start = identity->data() + 7;
  const auto *end = identity->data() + identity->size();
  const auto parsed = std::from_chars(start, end, value);
  return parsed.ec == std::errc{} && parsed.ptr == end
      ? reinterpret_cast<const void *>(value) : nullptr;
}
inline std::optional<std::int32_t> CountValue(const game::ArmyCandidateMapperCountInputV1 &p) {
  if (!p.count_base_128_raw_i32 || p.chunks.size() != 7) return std::nullopt;
  std::uint32_t total = static_cast<std::uint32_t>(*p.count_base_128_raw_i32);
  for (const auto &row : p.chunks) {
    if (!row.maximum_00_raw_i32) return std::nullopt;
    if (*row.maximum_00_raw_i32 == 0) continue;
    if (!row.current_04_raw_i32) return std::nullopt;
    if (*row.current_04_raw_i32 == 0) {
      if (!row.state_18_raw_i32) return std::nullopt;
      if (*row.state_18_raw_i32 == 3) continue;
    }
    total += static_cast<std::uint32_t>(*row.current_04_raw_i32) -
             static_cast<std::uint32_t>(*row.maximum_00_raw_i32);
  }
  std::int32_t result{}; std::memcpy(&result, &total, sizeof(result)); return result;
}
inline game::ArmyCandidateMapperCountInputV1 CountInput(
    const CurrentDailyAssaultTableBindings12003 &b, const void *regi, std::int32_t index) {
  game::ArmyCandidateMapperCountInputV1 out{};
  out.native_index = index; out.regi_identity = Identity(regi);
  out.count_base_128_raw_i32 = Read<std::int32_t>(b, regi, 0x128);
  for (std::int32_t i = 0; i < 7; ++i) {
    game::ArmyCandidateMapperCountChunkV1 row{}; row.physical_index = i;
    const auto chunk = At(regi, 0x18 + static_cast<std::size_t>(i) * 0x24);
    row.maximum_00_raw_i32 = Read<std::int32_t>(b, chunk);
    if (row.maximum_00_raw_i32 && *row.maximum_00_raw_i32 != 0) {
      row.current_04_raw_i32 = Read<std::int32_t>(b, chunk, 4);
      row.state_18_raw_i32 = Read<std::int32_t>(b, chunk, 0x18);
    }
    out.chunks.push_back(std::move(row));
  }
  const bool complete = CountValue(out).has_value();
  if (!complete) out.unavailable_reason = "candidate_mapper_count_operands_unavailable";
  Finish(out, complete); return out;
}

// ArRg fallback identity is sufficient for this getter: it has no ArRg
// tag/full-ID gate. A fallback full-ID observation is extra context, not a gate.
inline Resolved ResolveArRg(const CurrentDailyAssaultTableBindings12003 &b,
    const std::optional<std::uint32_t> &requested) {
  Resolved result{}; auto &out = result.observation; out.requested_full_id_u32 = requested;
  const auto fail = [&](const char *reason) {
    out.unavailable_reason = reason; Finish(out, false); return result;
  };
  if (!requested) return fail("candidate_mapper_arrg_raw_id_unavailable");
  const auto store = Read<const void *>(b, b.arrg_registry_slot);
  if (!store) return fail("candidate_mapper_arrg_registry_unavailable");
  out.registry_loaded = *store != nullptr;
  if (*store) {
    out.registry_index_u32 = *requested & 0xFFFFFFU;
    out.registry_capacity_u32 = Read<std::uint32_t>(b, *store, 0x2C);
    if (!out.registry_capacity_u32) return fail("candidate_mapper_arrg_capacity_unavailable");
    if (*out.registry_index_u32 < *out.registry_capacity_u32) {
      const auto table = Read<const void *>(b, *store, 0x20);
      if (!table || !*table) return fail("candidate_mapper_arrg_table_unavailable");
      const auto object = Read<const void *>(b, *table,
          static_cast<std::size_t>(*out.registry_index_u32) * 16 + 8);
      if (!object) return fail("candidate_mapper_arrg_slot_unavailable");
      if (*object) {
        out.indexed_identity = Identity(*object);
        out.indexed_full_id_u32 = Read<std::uint32_t>(b, *object, 0x10);
        if (!out.indexed_full_id_u32) return fail("candidate_mapper_arrg_full_id_unavailable");
        if (*out.indexed_full_id_u32 == *requested) {
          out.selection = "registry_full_id"; out.used_fallback = false;
          out.object_identity = out.indexed_identity; out.selected_full_id_u32 = out.indexed_full_id_u32;
          result.object = *object; Finish(out, true); return result;
        }
      }
    }
  }
  const auto fallback = Read<const void *>(b, b.arrg_fallback_slot);
  if (!fallback || !*fallback) return fail("candidate_mapper_arrg_fallback_unavailable");
  out.selection = "native_fallback"; out.used_fallback = true; out.object_identity = Identity(*fallback);
  out.selected_full_id_u32 = Read<std::uint32_t>(b, *fallback, 0x10);
  result.object = *fallback; Finish(out, true); return result;
}

inline game::ArmyCandidateDetachmentMapperV1 Mapper(
    const CurrentCandidateDetachmentMapperBindings12003 &b, const void *arrg,
    std::int32_t index, std::vector<game::ArmyCandidateMapperCountInputV1> &counts,
    std::unordered_map<const void *, std::int32_t> &count_aliases) {
  game::ArmyCandidateDetachmentMapperV1 out{};
  out.native_index = index; out.arrg_identity = Identity(arrg);
  const auto fail = [&](const char *reason) {
    out.unavailable_reason = reason; Finish(out, false); return out;
  };
  out.kind_14c_raw_i32 = Read<std::int32_t>(b.lookup, arrg, 0x14C);
  if (!out.kind_14c_raw_i32) return fail("candidate_mapper_kind_unavailable");
  const void *selected_regi = nullptr, *returned = nullptr;
  const auto fallback = [&]() -> const void * {
    const auto pointer = Read<const void *>(b.lookup, b.regi_fallback_slot);
    if (!pointer || !*pointer) return nullptr;
    out.fallback_regi_identity = Identity(*pointer); return *pointer;
  };
  if (*out.kind_14c_raw_i32 != 1 && *out.kind_14c_raw_i32 != 4) {
    returned = fallback(); out.return_selection = "native_fallback";
  } else {
    out.data_count_raw_i32 = Read<std::int32_t>(b.lookup, arrg, 0x2C);
    if (!out.data_count_raw_i32) return fail("candidate_mapper_data_count_unavailable");
    if (*out.data_count_raw_i32 == 0) out.first_regi_full_id_u32 = 0xFFFFFFFFU;
    else {
      const auto data = Read<const void *>(b.lookup, arrg, 0x20);
      if (!data || !*data) return fail("candidate_mapper_first_data_unavailable");
      out.first_data_record_identity = Identity(*data);
      out.first_regi_full_id_u32 = Read<std::uint32_t>(b.lookup, *data, 8);
      if (!out.first_regi_full_id_u32) return fail("candidate_mapper_first_regi_id_unavailable");
    }
    auto resolved = daily_assault_table_detail::Resolve(b.lookup, b.regi_registry_slot,
        b.regi_fallback_slot, out.first_regi_full_id_u32, 0x10);
    out.selected_regi_resolution = resolved.observation;
    if (!resolved.observation.ready) return fail("candidate_mapper_selected_regi_resolution_unavailable");
    selected_regi = resolved.object;
    if (resolved.observation.used_fallback == true) out.fallback_regi_identity = Identity(selected_regi);
    out.selected_regi_magic_14_raw_u32 = Read<std::uint32_t>(b.lookup, selected_regi, 0x14);
    if (!out.selected_regi_magic_14_raw_u32) return fail("candidate_mapper_selected_regi_magic_unavailable");
    out.selected_regi_identity_valid = *out.selected_regi_magic_14_raw_u32 == 0x52656769U &&
        resolved.observation.selected_full_id_u32 != 0xFFFFFFFFU;
    if (!*out.selected_regi_identity_valid) {
      returned = out.fallback_regi_identity ? selected_regi : fallback();
      out.return_selection = "native_fallback";
    } else if (*out.kind_14c_raw_i32 == 4) {
      returned = selected_regi; out.return_selection = "selected_regi";
    } else {
      auto found = count_aliases.find(selected_regi);
      if (found == count_aliases.end()) {
        const auto count_index = static_cast<std::int32_t>(counts.size());
        count_aliases.emplace(selected_regi, count_index);
        counts.push_back(CountInput(b.lookup, selected_regi, count_index));
        out.count_input_index = count_index;
      } else out.count_input_index = found->second;
      const auto value = CountValue(counts[static_cast<std::size_t>(*out.count_input_index)]);
      if (!value) return fail("candidate_mapper_count_unavailable");
      if (*value > 0) {
        returned = out.fallback_regi_identity ? selected_regi : fallback();
        out.return_selection = "native_fallback";
      } else { returned = selected_regi; out.return_selection = "selected_regi"; }
    }
  }
  if (!returned) return fail("candidate_mapper_return_fallback_unavailable");
  out.return_selection_ready = true; out.returned_regi_identity = Identity(returned);
  if (returned == selected_regi && out.selected_regi_resolution) {
    out.returned_regi_full_id_u32 = out.selected_regi_resolution->selected_full_id_u32;
    out.returned_regi_magic_14_raw_u32 = out.selected_regi_magic_14_raw_u32;
  } else {
    out.returned_regi_full_id_u32 = Read<std::uint32_t>(b.lookup, returned, 0x10);
    out.returned_regi_magic_14_raw_u32 = Read<std::uint32_t>(b.lookup, returned, 0x14);
  }
  out.returned_state_138_raw_i32 = Read<std::int32_t>(b.lookup, returned, 0x138);
  if (!out.returned_state_138_raw_i32) return fail("candidate_mapper_return_state_unavailable");
  Finish(out, true); return out;
}
} // namespace candidate_mapper_detail

inline game::ArmyCurrentCandidateDetachmentMapperInputsV1 ReadCurrentCandidateDetachmentMapper12003(
    const CurrentCandidateDetachmentMapperBindings12003 &b,
    const game::ArmyCurrentAssaultRemovalReferenceInputsV1 *existing) noexcept {
  using namespace candidate_mapper_detail;
  game::ArmyCurrentCandidateDetachmentMapperInputsV1 out{};
  const auto fail = [&](const char *reason) {
    out.unavailable_reason = reason; Finish(out, false); return out;
  };
  if (!b.enabled) return fail("current_candidate_mapper_unbound");
  if (!existing || !existing->observed_pending_ids_i32)
    return fail("current_candidate_mapper_current_pending_unavailable");
  const game::ArmyCurrentAssaultRemovalReferenceV1 *candidate = nullptr;
  for (std::size_t i = 0; i < existing->observed_pending_ids_i32->size(); ++i) {
    const auto raw = static_cast<std::uint32_t>((*existing->observed_pending_ids_i32)[i]);
    const auto row = std::find_if(existing->reference_occurrences.begin(), existing->reference_occurrences.end(),
        [&](const auto &p) { return p.reference_scope == "current_pending" &&
            p.pending_native_index == static_cast<std::int32_t>(i) && p.raw_full_id_u32 == raw; });
    if (row == existing->reference_occurrences.end() || !row->native_army_identity_valid)
      return fail("current_candidate_mapper_initial_selection_partial");
    if (*row->native_army_identity_valid) { candidate = &*row; break; }
  }
  out.selection_ready = true;
  if (!candidate) {
    out.selection_branch = "not_called"; out.roster_ready = true; Finish(out, true); return out;
  }
  out.selection_branch = "first_valid_current_receiver";
  out.candidate_reference_native_index = candidate->native_index;
  out.candidate_pending_native_index = candidate->pending_native_index;
  out.candidate_raw_full_id_u32 = candidate->raw_full_id_u32;
  out.candidate_actual_full_id_u32 = candidate->resolution.selected_full_id_u32;
  out.candidate_army_identity = candidate->resolution.object_identity;
  const auto army = CapturedPointer(out.candidate_army_identity);
  if (!army) return fail("current_candidate_mapper_receiver_identity_unavailable");
  const auto data = Read<const void *>(b.lookup, army, 0x38);
  out.roster_count_raw_i32 = Read<std::int32_t>(b.lookup, army, 0x44);
  if (data) {
    out.roster_data_present = *data != nullptr; out.roster_data_identity = Identity(*data);
  }
  if (!out.roster_count_raw_i32 || !data) return fail("current_candidate_mapper_roster_header_unavailable");
  if (*out.roster_count_raw_i32 > 0 && !*data) return fail("current_candidate_mapper_roster_data_unavailable");
  out.roster_ready = true;
  std::unordered_map<const void *, std::int32_t> mapper_aliases, count_aliases;
  for (std::int32_t i = 0; i < *out.roster_count_raw_i32; ++i) {
    game::ArmyCandidateDetachmentOccurrenceV1 row{}; row.native_index = i;
    row.raw_full_id_u32 = Read<std::uint32_t>(b.lookup, *data, static_cast<std::size_t>(i) * 4);
    auto selected = ResolveArRg(b.lookup, row.raw_full_id_u32); row.resolution = selected.observation;
    if (selected.observation.ready) {
      const auto found = mapper_aliases.find(selected.object);
      if (found == mapper_aliases.end()) {
        const auto index = static_cast<std::int32_t>(out.mappers.size());
        mapper_aliases.emplace(selected.object, index); row.mapper_index = index;
        out.mappers.push_back(Mapper(b, selected.object, index, out.count_inputs, count_aliases));
      } else row.mapper_index = found->second;
      const auto &mapper = out.mappers[static_cast<std::size_t>(*row.mapper_index)];
      row.unavailable_reason = mapper.unavailable_reason; Finish(row, mapper.ready);
    } else { row.unavailable_reason = selected.observation.unavailable_reason; Finish(row, false); }
    if (!row.ready) Reason(out.unavailable_reason, row.unavailable_reason);
    out.occurrences.push_back(std::move(row));
  }
  Finish(out, std::all_of(out.occurrences.begin(), out.occurrences.end(), [](const auto &row) { return row.ready; }));
  return out;
}
} // namespace xar::ck3_12003
