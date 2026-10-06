#pragma once

#include "xar_bridge/game_contract.hpp"
#include "xar_bridge/ck3_12003_current_candidate_detachment_mapper.hpp"

#include <algorithm>
#include <cstring>
#include <cstdint>
#include <optional>
#include <unordered_map>
#include <utility>

namespace xar::ck3_12003 {
struct CurrentDetachmentDataBindings12003 {
  using CapitalGetter = const void *(*)(const void *);
  using DateConstructor = const void *(*)(std::int64_t *, const void *, const void *,
                                        const void *, const std::int64_t *);
  CurrentDailyAssaultTableBindings12003 common{};
  const void *regi_registry_slot = nullptr, *regi_fallback_slot = nullptr;
  const void *unit_registry_slot = nullptr, *unit_fallback_slot = nullptr;
  const void *character_registry_slot = nullptr, *character_fallback_slot = nullptr;
  const void *province_fallback_slot = nullptr, *static_context = nullptr;
  const void *canonical_pending_vtable = nullptr, *ready_pending_callback = nullptr;
  CapitalGetter get_capital = nullptr;
  DateConstructor compute_date = nullptr;
};
inline CurrentDetachmentDataBindings12003 BindCurrentDetachmentData12003(
    std::uintptr_t base, std::string_view sha) noexcept {
  CurrentDetachmentDataBindings12003 out{};
  if (!base || sha != kExecutableSha256) return out;
  out.common = BindCurrentDailyAssaultTable12003(base, sha);
  out.common.enabled = false;
  const auto at = [base](std::uintptr_t rva) { return reinterpret_cast<const void *>(base + rva); };
  out.regi_registry_slot = at(0x5D1EB68); out.regi_fallback_slot = at(0x5D1EB58);
  out.unit_registry_slot = at(0x5D1E380); out.unit_fallback_slot = at(0x5D1E378);
  out.character_registry_slot = at(0x5C67568); out.character_fallback_slot = at(0x5C67570);
  out.province_fallback_slot = at(0x5D1E390); out.static_context = at(0x5459D38);
  out.canonical_pending_vtable = at(0x44DEFA8); out.ready_pending_callback = at(0x8863D0);
  out.get_capital = reinterpret_cast<CurrentDetachmentDataBindings12003::CapitalGetter>(base + 0x28B1CD0);
  out.compute_date = reinterpret_cast<CurrentDetachmentDataBindings12003::DateConstructor>(base + 0x2C54340);
  out.common.enabled = true;
  return out;
}
namespace detachment_data_detail {
using daily_assault_table_detail::Read;
using daily_assault_table_detail::Identity;
using daily_assault_table_detail::Finish;
using daily_assault_table_detail::Reason;
using daily_assault_table_detail::Resolved;
using candidate_mapper_detail::CapturedPointer;

inline const void *Offset(const void *object, std::int64_t offset) {
  return reinterpret_cast<const void *>(reinterpret_cast<std::uintptr_t>(object) +
                                       static_cast<std::uintptr_t>(offset));
}
// Same registry/generation selection as the closed callers. The fallback's
// full ID is context unless a caller subsequently tests that ID explicitly.
// DATA calls supply the held fallback register; invalid records do not reload it.
inline Resolved Resolve(const CurrentDetachmentDataBindings12003 &b,
    const void *registry_slot, const void *fallback_slot,
    const std::optional<std::uint32_t> &requested, std::size_t full_offset,
    bool use_held = false, std::optional<const void *> held = std::nullopt) {
  Resolved result{}; auto &out = result.observation; out.requested_full_id_u32 = requested;
  const auto fail = [&](const char *reason) {
    out.unavailable_reason = reason; Finish(out, false); return result;
  };
  if (!requested) return fail("detachment_requested_id_unavailable");
  const auto registry = Read<const void *>(b.common, registry_slot);
  if (!registry) return fail("detachment_registry_unavailable");
  out.registry_loaded = *registry != nullptr;
  if (*registry) {
    out.registry_index_u32 = *requested & 0xFFFFFFU;
    out.registry_capacity_u32 = Read<std::uint32_t>(b.common, *registry, 0x2C);
    if (!out.registry_capacity_u32) return fail("detachment_registry_count_unavailable");
    if (*out.registry_index_u32 < *out.registry_capacity_u32) {
      const auto table = Read<const void *>(b.common, *registry, 0x20);
      if (!table || !*table) return fail("detachment_registry_data_unavailable");
      const auto selected = Read<const void *>(b.common, *table,
          static_cast<std::size_t>(*out.registry_index_u32) * 16 + 8);
      if (!selected) return fail("detachment_registry_payload_unavailable");
      if (*selected) {
        out.indexed_identity = Identity(*selected);
        out.indexed_full_id_u32 = Read<std::uint32_t>(b.common, *selected, full_offset);
        if (!out.indexed_full_id_u32) return fail("detachment_registry_generation_unavailable");
        if (*out.indexed_full_id_u32 == *requested) {
          out.selection = "registry_full_id"; out.used_fallback = false;
          out.object_identity = out.indexed_identity; out.selected_full_id_u32 = out.indexed_full_id_u32;
          result.object = *selected; Finish(out, true); return result;
        }
      }
    }
  }
  const auto fallback = use_held ? held : Read<const void *>(b.common, fallback_slot);
  if (!fallback) return fail("detachment_fallback_unavailable");
  out.selection = "native_fallback"; out.used_fallback = true;
  if (!*fallback) return fail("detachment_fallback_null");
  out.object_identity = Identity(*fallback);
  out.selected_full_id_u32 = Read<std::uint32_t>(b.common, *fallback, full_offset);
  result.object = *fallback; Finish(out, true); return result;
}
inline game::ArmyDetachmentPhysicalChunkV1 Chunk(const CurrentDetachmentDataBindings12003 &b,
    const void *chunk, std::int32_t index) {
  game::ArmyDetachmentPhysicalChunkV1 out{}; out.native_index = index; out.chunk_identity = Identity(chunk);
  out.maximum_00_raw_i32 = Read<std::int32_t>(b.common, chunk);
  out.current_04_raw_i32 = Read<std::int32_t>(b.common, chunk, 4);
  out.owner_08_raw_u32 = Read<std::uint32_t>(b.common, chunk, 8);
  out.ordinal_0c_raw_i32 = Read<std::int32_t>(b.common, chunk, 0xC);
  out.association_10_raw_u32 = Read<std::uint32_t>(b.common, chunk, 0x10);
  out.flag_14_raw_u8 = Read<std::uint8_t>(b.common, chunk, 0x14);
  out.date_1c_raw64 = Read<std::int64_t>(b.common, chunk, 0x1C);
  const bool complete = out.maximum_00_raw_i32 && out.current_04_raw_i32 && out.owner_08_raw_u32 &&
      out.ordinal_0c_raw_i32 && out.association_10_raw_u32 && out.flag_14_raw_u8 && out.date_1c_raw64;
  if (!complete) out.unavailable_reason = "detachment_physical_fields_unavailable";
  Finish(out, complete); return out;
}
inline game::ArmyDetachmentAssociationInputV1 Association(const CurrentDetachmentDataBindings12003 &b,
    std::uint32_t requested) {
  game::ArmyDetachmentAssociationInputV1 out{}; out.requested_full_id_u32 = requested;
  const auto fail = [&](const char *reason) { out.unavailable_reason = reason; Finish(out, false); return out; };
  auto arrg = Resolve(b, b.common.arrg_registry_slot, b.common.arrg_fallback_slot, requested, 0x10);
  out.arrg_resolution = arrg.observation;
  if (!arrg.observation.ready) return fail("detachment_association_arrg_unavailable");
  out.army_full_id_140_u32 = Read<std::uint32_t>(b.common, arrg.object, 0x140);
  auto army = Resolve(b, b.common.army_registry_slot, b.common.army_fallback_slot, out.army_full_id_140_u32, 0x10);
  out.army_resolution = army.observation;
  if (!army.observation.ready) return fail("detachment_association_army_unavailable");
  out.unit_full_id_124_u32 = Read<std::uint32_t>(b.common, army.object, 0x124);
  auto unit = Resolve(b, b.unit_registry_slot, b.unit_fallback_slot, out.unit_full_id_124_u32, 0x10);
  out.unit_resolution = unit.observation;
  if (!unit.observation.ready) return fail("detachment_association_unit_unavailable");
  out.character_full_id_174_u32 = Read<std::uint32_t>(b.common, unit.object, 0x174);
  auto character = Resolve(b, b.character_registry_slot, b.character_fallback_slot, out.character_full_id_174_u32, 0x18);
  out.character_resolution = character.observation;
  if (!character.observation.ready) return fail("detachment_association_character_unavailable");
  const auto context = Read<const void *>(b.common, character.object, 0x1C0);
  if (!context) return fail("detachment_predicate_context_unavailable");
  const auto selected = *context ? Offset(*context, 0x318) : b.static_context;
  out.context_pointer_identity = Identity(selected);
  out.context_count_0c_raw_u32 = Read<std::uint32_t>(b.common, selected, 0xC);
  if (!out.context_count_0c_raw_u32) return fail("detachment_predicate_count_unavailable");
  Finish(out, true); return out;
}
inline game::ArmyDetachmentOwnerInputV1 Owner(const CurrentDetachmentDataBindings12003 &b,
    std::uint32_t requested) {
  game::ArmyDetachmentOwnerInputV1 out{}; out.requested_full_id_u32 = requested;
  auto regi = Resolve(b, b.regi_registry_slot, b.regi_fallback_slot, requested, 0x10);
  out.resolution = regi.observation;
  if (!regi.observation.ready) {
    out.unavailable_reason = "detachment_owner_resolution_unavailable"; Finish(out, false); return out;
  }
  out.state_138_raw_i32 = Read<std::int32_t>(b.common, regi.object, 0x138);
  // Only state zero can demand definition magic in the special pair clear.
  if (out.state_138_raw_i32 == 0) {
    const auto definition = Read<const void *>(b.common, regi.object, 0x118);
    if (definition) {
      out.definition_identity = Identity(*definition);
      out.definition_magic_38_raw_u32 = Read<std::uint32_t>(b.common, *definition, 0x38);
    }
  }
  const auto origin = Read<const void *>(b.common, regi.object, 0x120);
  if (origin) {
    out.origin_identity = Identity(*origin);
    out.origin_magic_85c_raw_u32 = Read<std::uint32_t>(b.common, *origin, 0x85C);
  }
  // Optional unused origin/definition fields do not become a family gate.
  Finish(out, true); return out;
}
inline game::ArmyDetachmentDateInputV1 Date(const CurrentDetachmentDataBindings12003 &b,
    const game::ArmyDetachmentAssociationInputV1 &association,
    const game::ArmyDetachmentOwnerInputV1 &owner, const void *passed_province,
    const std::optional<std::int64_t> &current_date) {
  game::ArmyDetachmentDateInputV1 out{};
  out.association_full_id_u32 = association.requested_full_id_u32;
  out.owner_full_id_u32 = owner.requested_full_id_u32;
  out.unit_identity = association.unit_resolution.object_identity;
  out.source_origin_identity = owner.origin_identity;
  out.source_origin_magic_85c_raw_u32 = owner.origin_magic_85c_raw_u32;
  const auto fail = [&](const char *reason) { out.unavailable_reason = reason; Finish(out, false); return out; };
  if (!association.ready || !owner.resolution.ready || !owner.origin_magic_85c_raw_u32)
    return fail("detachment_date_source_roles_unavailable");
  const void *origin = CapturedPointer(owner.origin_identity);
  if (*owner.origin_magic_85c_raw_u32 != 0x50726F76U) {
    const auto character = CapturedPointer(association.character_resolution.object_identity);
    if (!character || !b.get_capital) return fail("detachment_date_capital_unavailable");
    origin = b.get_capital(character);
    out.capital_origin_identity = Identity(origin);
    out.capital_origin_magic_85c_raw_u32 = Read<std::uint32_t>(b.common, origin, 0x85C);
    if (!out.capital_origin_magic_85c_raw_u32) return fail("detachment_date_capital_tag_unavailable");
    if (*out.capital_origin_magic_85c_raw_u32 != 0x50726F76U) {
      if (!current_date) return fail("detachment_current_date_unavailable");
      out.output_date_raw64 = current_date; out.basis = "source2658180_two_nonProv_origins_copy_full_current_date";
      Finish(out, true); return out;
    }
  }
  const auto unit = CapturedPointer(out.unit_identity);
  if (!current_date || !passed_province || !origin || !unit || !b.compute_date)
    return fail("detachment_native_computed_date_unavailable");
  std::int64_t output{};
  const std::int64_t input = *current_date;
  // Only the already source-closed readonly native date constructor is called.
  // No 2658050/2658180, setter, pending, record virtual, or allocator is executed.
  b.compute_date(&output, unit, passed_province, origin, &input);
  out.output_date_raw64 = output; out.basis = "current_input_native2C54340_fullQWORD";
  Finish(out, true); return out;
}
inline game::ArmyDetachmentPendingInputsV1 Pending(const CurrentDetachmentDataBindings12003 &b,
    const void *primary) {
  game::ArmyDetachmentPendingInputsV1 out{};
  const auto header = primary ? Offset(primary, 0x468) : nullptr;
  if (!header) { out.unavailable_reason = "detachment_primary_receiver_unavailable"; Finish(out, false); return out; }
  out.header_identity = Identity(header);
  const auto buffer = Read<const void *>(b.common, header);
  if (buffer) out.buffer_identity = Identity(*buffer);
  out.capacity_08_raw_i32 = Read<std::int32_t>(b.common, header, 8);
  out.count_0c_raw_i32 = Read<std::int32_t>(b.common, header, 0xC);
  const auto allocator = Read<const void *>(b.common, header, 0x10);
  if (allocator) out.allocator_identity = Identity(*allocator);
  bool complete = buffer.has_value() && out.capacity_08_raw_i32.has_value() &&
                  out.count_0c_raw_i32.has_value() && allocator.has_value();
  if (out.count_0c_raw_i32 && *out.count_0c_raw_i32 > 0) {
    if (!buffer || !*buffer) complete = false;
    else for (std::int64_t i = 0; i < *out.count_0c_raw_i32; ++i) {
      game::ArmyDetachmentPendingRecordV1 row{}; row.native_index = static_cast<std::int32_t>(i);
      const auto record = Offset(*buffer, i * 16); row.record_identity = Identity(record);
      const auto vtable = Read<const void *>(b.common, record);
      if (vtable) {
        row.vtable_identity = Identity(*vtable);
        const auto target = Read<const void *>(b.common, *vtable);
        if (target) row.slot0_target_identity = Identity(*target);
      }
      row.owner_08_raw_u32 = Read<std::uint32_t>(b.common, record, 8);
      row.ordinal_0c_raw_i32 = Read<std::int32_t>(b.common, record, 0xC);
      const bool raw_ready = vtable && row.owner_08_raw_u32 && row.ordinal_0c_raw_i32;
      if (!raw_ready) { row.unavailable_reason = "detachment_pending_record_unavailable"; complete = false; }
      Finish(row, raw_ready); out.records.push_back(std::move(row));
    }
  }
  if (!complete) out.unavailable_reason = "detachment_pending_inputs_partial";
  Finish(out, complete); return out;
}
inline void CharacterSuffix(const CurrentDetachmentDataBindings12003 &b, const void *arrg,
    game::ArmyCurrentDetachmentIncomingV1 &out) {
  out.character_full_id_148_u32 = Read<std::uint32_t>(b.common, arrg, 0x148);
  if (!out.character_full_id_148_u32 || *out.character_full_id_148_u32 == 0xFFFFFFFFU) return;
  auto character = Resolve(b, b.character_registry_slot, b.character_fallback_slot,
                           out.character_full_id_148_u32, 0x18);
  out.character_resolution = character.observation;
  if (!character.observation.ready) return;
  const auto context = Read<const void *>(b.common, character.object, 0x1B8);
  if (context) {
    out.character_pointer_1b8_present = *context != nullptr;
    out.character_pointer_1b8_identity = Identity(*context);
  }
}
inline game::ArmyCurrentDetachmentIncomingV1 Incoming(const CurrentDetachmentDataBindings12003 &b,
    const void *arrg, std::int32_t index, const void *primary,
    const std::optional<std::int64_t> &current_date) {
  game::ArmyCurrentDetachmentIncomingV1 out{};
  out.native_index = index; out.arrg_identity = Identity(arrg);
  out.arrg_full_id_u32 = Read<std::uint32_t>(b.common, arrg, 0x10);
  out.army_full_id_140_u32 = Read<std::uint32_t>(b.common, arrg, 0x140);
  auto army = Resolve(b, b.common.army_registry_slot, b.common.army_fallback_slot,
                      out.army_full_id_140_u32, 0x10);
  out.army_resolution = army.observation;
  if (army.observation.ready) {
    out.unit_full_id_124_u32 = Read<std::uint32_t>(b.common, army.object, 0x124);
    auto unit = Resolve(b, b.unit_registry_slot, b.unit_fallback_slot, out.unit_full_id_124_u32, 0x10);
    out.unit_resolution = unit.observation;
    if (unit.observation.ready) {
      auto province = Read<const void *>(b.common, unit.object, 0x20);
      if (province && !*province) province = Read<const void *>(b.common, b.province_fallback_slot);
      if (province) out.passed_province_identity = Identity(*province);
    }
  }
  const auto data = Read<const void *>(b.common, arrg, 0x20);
  out.data_count_raw_i32 = Read<std::int32_t>(b.common, arrg, 0x2C);
  if (data) {
    out.data_pointer_identity = Identity(*data); out.captured_cursor_identity = Identity(*data);
    if (out.data_count_raw_i32)
      out.captured_end_identity = Identity(Offset(*data, static_cast<std::int64_t>(*out.data_count_raw_i32) * 16));
  }
  std::unordered_map<const void *, std::int32_t> chunk_aliases;
  auto held_fallback = Read<const void *>(b.common, b.regi_fallback_slot);
  out.data_ready = data.has_value() && out.data_count_raw_i32.has_value();
  if (!out.data_ready) Reason(out.unavailable_reason, "detachment_DATA_header_unavailable");
  else if (*out.data_count_raw_i32 < 0) {
    // Captured negative endpoint remains distinct from a ready empty sequence.
    out.data_ready = false; Reason(out.unavailable_reason, "detachment_DATA_negative_count_sequence_partial");
  } else if (*out.data_count_raw_i32 > 0 && !*data) {
    out.data_ready = false; Reason(out.unavailable_reason, "detachment_DATA_storage_unavailable");
  } else for (std::int64_t i = 0; i < *out.data_count_raw_i32; ++i) {
    game::ArmyDetachmentDataOccurrenceV1 row{}; row.native_index = static_cast<std::int32_t>(i);
    const auto record = Offset(*data, i * 16); row.record_identity = Identity(record);
    row.raw_regi_full_id_u32 = Read<std::uint32_t>(b.common, record, 8);
    row.data_ordinal_raw_i32 = Read<std::int32_t>(b.common, record, 0xC);
    if (held_fallback) row.held_fallback_regi_identity = Identity(*held_fallback);
    auto regi = Resolve(b, b.regi_registry_slot, b.regi_fallback_slot,
                        row.raw_regi_full_id_u32, 0x10, true, held_fallback);
    row.resolution = regi.observation;
    bool complete = row.raw_regi_full_id_u32.has_value() && regi.observation.ready;
    if (regi.observation.ready) {
      row.magic_14_raw_u32 = Read<std::uint32_t>(b.common, regi.object, 0x14);
      complete = complete && row.magic_14_raw_u32.has_value();
      if (row.magic_14_raw_u32) {
        if (*row.magic_14_raw_u32 != 0x52656769U) row.identity_valid = false;
        else if (regi.observation.selected_full_id_u32)
          row.identity_valid = *regi.observation.selected_full_id_u32 != 0xFFFFFFFFU;
        else complete = false;
      }
      if (row.identity_valid == true) {
        if (!row.data_ordinal_raw_i32) complete = false;
        else {
          const auto chunk = Offset(regi.object, 0x18 + static_cast<std::int64_t>(*row.data_ordinal_raw_i32) * 0x24);
          row.physical_chunk_present = chunk != nullptr;
          if (chunk) {
            const auto found = chunk_aliases.find(chunk);
            if (found == chunk_aliases.end()) {
              const auto chunk_index = static_cast<std::int32_t>(out.physical_chunks.size());
              chunk_aliases.emplace(chunk, chunk_index); row.physical_chunk_index = chunk_index;
              out.physical_chunks.push_back(Chunk(b, chunk, chunk_index));
            } else row.physical_chunk_index = found->second;
            complete = complete && out.physical_chunks[static_cast<std::size_t>(*row.physical_chunk_index)].ready;
            held_fallback = Read<const void *>(b.common, b.regi_fallback_slot);
          }
        }
      }
    }
    if (!complete) { row.unavailable_reason = "detachment_DATA_occurrence_partial"; out.data_ready = false; Reason(out.unavailable_reason, row.unavailable_reason); }
    Finish(row, complete); out.data_occurrences.push_back(std::move(row));
  }
  // Pure variants for the initial and source-cleared association. Observations
  // are shared by ID; ordered DATA occurrences and their aliases remain intact.
  for (const auto &chunk : out.physical_chunks) {
    if (chunk.association_10_raw_u32) for (const auto requested : {*chunk.association_10_raw_u32, 0xFFFFFFFFU}) {
      if (std::none_of(out.association_inputs.begin(), out.association_inputs.end(),
          [requested](const auto &p) { return p.requested_full_id_u32 == requested; }))
        out.association_inputs.push_back(Association(b, requested));
    }
    if (chunk.owner_08_raw_u32 && std::none_of(out.owner_inputs.begin(), out.owner_inputs.end(),
        [&](const auto &p) { return p.requested_full_id_u32 == *chunk.owner_08_raw_u32; }))
      out.owner_inputs.push_back(Owner(b, *chunk.owner_08_raw_u32));
  }
  const auto passed = CapturedPointer(out.passed_province_identity);
  bool pending_used_variant = false;
  for (const auto &chunk : out.physical_chunks) {
    if (!chunk.owner_08_raw_u32 || !chunk.association_10_raw_u32) continue;
    const auto owner = std::find_if(out.owner_inputs.begin(), out.owner_inputs.end(),
        [&](const auto &p) { return p.requested_full_id_u32 == *chunk.owner_08_raw_u32; });
    if (owner == out.owner_inputs.end()) continue;
    for (const auto requested : {*chunk.association_10_raw_u32, 0xFFFFFFFFU}) {
      const auto association = std::find_if(out.association_inputs.begin(), out.association_inputs.end(),
          [requested](const auto &p) { return p.requested_full_id_u32 == requested; });
      if (association == out.association_inputs.end() || !association->context_count_0c_raw_u32 ||
          *association->context_count_0c_raw_u32 == 0) continue;
      if (std::any_of(out.date_inputs.begin(), out.date_inputs.end(), [&](const auto &p) {
          return p.association_full_id_u32 == requested && p.owner_full_id_u32 == *chunk.owner_08_raw_u32; })) continue;
      out.date_inputs.push_back(Date(b, *association, *owner, passed, current_date));
      const auto &date = out.date_inputs.back();
      if (!date.output_date_raw64 || !current_date) pending_used_variant = true;
      else {
        const auto low = [](std::int64_t value) {
          const auto bits = static_cast<std::uint32_t>(static_cast<std::uint64_t>(value));
          std::int32_t signed_value{}; std::memcpy(&signed_value, &bits, sizeof(bits)); return signed_value;
        };
        if (low(*date.output_date_raw64) > low(*current_date)) pending_used_variant = true;
      }
    }
  }
  if (pending_used_variant) out.pending = Pending(b, primary);
  CharacterSuffix(b, arrg, out);
  // Whole raw DATA and copied entry provenance, not universal branch readiness.
  if (!out.passed_province_identity) Reason(out.unavailable_reason, "detachment_passed_Province_unavailable");
  Finish(out, out.data_ready && out.passed_province_identity.has_value());
  return out;
}
} // namespace detachment_data_detail

inline game::ArmyCurrentDetachmentDataInputsV1 ReadCurrentDetachmentDataInputs12003(
    const CurrentDetachmentDataBindings12003 &b,
    const game::ArmyCurrentCandidateDetachmentMapperInputsV1 *mapper,
    const game::ArmyMonthlyCallerEffectInputsV1 *monthly) noexcept {
  using namespace detachment_data_detail;
  game::ArmyCurrentDetachmentDataInputsV1 out{};
  const auto fail = [&](const char *reason) { out.unavailable_reason = reason; Finish(out, false); return out; };
  if (!b.common.enabled) return fail("current_detachment_data_unbound");
  if (monthly) out.current_date_storage_raw64 = monthly->current_date_storage_raw64;
  if (b.canonical_pending_vtable) out.canonical_pending_vtable_identity = Identity(b.canonical_pending_vtable);
  if (b.ready_pending_callback) out.ready_pending_callback_identity = Identity(b.ready_pending_callback);
  if (!mapper || !mapper->selection_ready) return fail("current_detachment_candidate_selection_unavailable");
  out.selection_ready = true; out.roster_ready = mapper->roster_ready;
  if (!mapper->roster_ready) return fail("current_detachment_candidate_roster_unavailable");
  // Current manager is inline GameData+2A540. It is not the queried Army.
  const void *primary = nullptr;
  const auto state = Read<const void *>(b.common, b.common.game_state_slot);
  if (state && *state) {
    const auto game_data = Read<const void *>(b.common, *state, 0xA0);
    if (game_data && *game_data) { primary = Offset(*game_data, 0x2A540); out.primary_receiver_identity = Identity(primary); }
  }
  std::unordered_map<const void *, std::int32_t> incoming_aliases;
  for (const auto &candidate : mapper->occurrences) {
    game::ArmyCurrentDetachmentCandidateOccurrenceV1 row{};
    row.native_index = candidate.native_index; row.raw_full_id_u32 = candidate.raw_full_id_u32;
    auto arrg = Resolve(b, b.common.arrg_registry_slot, b.common.arrg_fallback_slot, row.raw_full_id_u32, 0x10);
    row.resolution = arrg.observation;
    bool complete = arrg.observation.ready;
    if (complete) {
      row.magic_14_raw_u32 = Read<std::uint32_t>(b.common, arrg.object, 0x14);
      complete = row.magic_14_raw_u32.has_value();
      if (row.magic_14_raw_u32) {
        if (*row.magic_14_raw_u32 != 0x41725267U) row.incoming_valid = false;
        else if (arrg.observation.selected_full_id_u32) row.incoming_valid = *arrg.observation.selected_full_id_u32 != 0xFFFFFFFFU;
        else complete = false;
      }
      if (row.incoming_valid == true) {
        const auto found = incoming_aliases.find(arrg.object);
        if (found == incoming_aliases.end()) {
          const auto index = static_cast<std::int32_t>(out.incoming.size());
          incoming_aliases.emplace(arrg.object, index); row.incoming_index = index;
          out.incoming.push_back(Incoming(b, arrg.object, index, primary, out.current_date_storage_raw64));
        } else row.incoming_index = found->second;
        complete = complete && out.incoming[static_cast<std::size_t>(*row.incoming_index)].ready;
      }
    }
    if (!complete) { row.unavailable_reason = "current_detachment_incoming_capture_partial"; Reason(out.unavailable_reason, row.unavailable_reason); }
    Finish(row, complete); out.candidate_occurrences.push_back(std::move(row));
  }
  Finish(out, std::all_of(out.candidate_occurrences.begin(), out.candidate_occurrences.end(),
      [](const auto &row) { return row.ready; }));
  return out;
}
} // namespace xar::ck3_12003
