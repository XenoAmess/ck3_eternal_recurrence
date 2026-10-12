#include "xar_bridge/prewar_force_bounds12004.hpp"

#include <algorithm>
#include <array>
#include <limits>
#include <map>
#include <set>
#include <utility>

namespace xar::ck3_12004 {
namespace {

using Key = std::pair<std::int32_t, std::int32_t>;

bool Add(std::int64_t &total, std::int64_t value) noexcept {
  if (value < 0 || total < 0 ||
      total > (std::numeric_limits<std::int64_t>::max)() - value) return false;
  total += value;
  return true;
}

bool Int32(std::int64_t value) noexcept {
  return value >= (std::numeric_limits<std::int32_t>::min)() &&
      value <= (std::numeric_limits<std::int32_t>::max)();
}

void Reason(PrewarForceOwnerBounds12004 &out, std::string reason) {
  if (std::find(out.unavailable_reasons.begin(), out.unavailable_reasons.end(),
                reason) == out.unavailable_reasons.end())
    out.unavailable_reasons.push_back(std::move(reason));
}

bool Collection(const PrewarOwnerIdCollection12004 &ids) {
  if (!ids.header_read_complete || !ids.entries_copied_complete ||
      !ids.data_present || !ids.capacity || !ids.count ||
      *ids.capacity < 0 || *ids.count < 0 || *ids.count > *ids.capacity ||
      (*ids.count != 0 && !*ids.data_present) ||
      ids.full_ids.size() != static_cast<std::size_t>(*ids.count)) return false;
  std::set<std::int32_t> seen;
  std::vector<std::int32_t> unique;
  for (const auto id : ids.full_ids)
    if (seen.insert(id).second) unique.push_back(id);
  return unique == ids.unique_full_ids &&
      ids.duplicate_full_id_occurrences >= 0 &&
      static_cast<std::size_t>(ids.duplicate_full_id_occurrences) ==
          ids.full_ids.size() - unique.size();
}

struct Atom {
  std::int32_t current = 0;
  std::int32_t maximum = 0;
  std::int32_t army_regiment_id = -1;
  std::uint8_t pending = 0;
  std::int32_t state = 0;
  bool operator==(const Atom &) const = default;
};

struct Regiment {
  std::int32_t id = -1;
  std::int32_t capacity = 0;
  std::int32_t source_owner = -1;
  std::array<Atom, 7> chunks{};
  bool operator==(const Regiment &) const = default;
};

bool OwnerRegiment(const PrewarOwnerPersistentRegiment12004 &row,
                   Regiment &regiment) {
  if (row.persistent_regiment_id == -1 || !row.full_generation_ready ||
      !row.atoms_read_complete || row.observed_full_id != row.persistent_regiment_id ||
      row.observed_magic != 0x52656769U || !row.native_owner_character_id ||
      !row.native_capacity_raw || *row.native_capacity_raw < 0 || row.chunks.size() != 7)
    return false;
  regiment.id = row.persistent_regiment_id;
  regiment.capacity = *row.native_capacity_raw;
  regiment.source_owner = *row.native_owner_character_id;
  for (std::int32_t i = 0; i < 7; ++i) {
    const auto &chunk = row.chunks[static_cast<std::size_t>(i)];
    if (chunk.chunk_index != i || !chunk.atoms_read_complete ||
        chunk.persistent_regiment_id_raw != regiment.id || chunk.native_ordinal_raw != i ||
        !chunk.current_soldiers_raw || *chunk.current_soldiers_raw < 0 ||
        !chunk.maximum_soldiers_raw || *chunk.maximum_soldiers_raw < 0 ||
        !chunk.army_regiment_id_raw || !chunk.pending_raw || !chunk.state_raw) return false;
    regiment.chunks[static_cast<std::size_t>(i)] = {
        *chunk.current_soldiers_raw, *chunk.maximum_soldiers_raw,
        *chunk.army_regiment_id_raw, *chunk.pending_raw, *chunk.state_raw};
  }
  return true;
}

bool HiredRegiment(const PrewarHiredRegiment12004 &row, Regiment &regiment) {
  if (row.persistent_regiment_id == -1 || !row.available ||
      row.observed_full_id != row.persistent_regiment_id ||
      row.observed_magic != 0x52656769U || !row.persistent_owner_character_id ||
      !row.native_capacity_raw || *row.native_capacity_raw < 0 || row.chunks.size() != 7)
    return false;
  regiment.id = row.persistent_regiment_id;
  regiment.capacity = *row.native_capacity_raw;
  regiment.source_owner = *row.persistent_owner_character_id;
  for (std::int32_t i = 0; i < 7; ++i) {
    const auto &chunk = row.chunks[static_cast<std::size_t>(i)];
    if (chunk.chunk_index != i || !chunk.fields_copied || !chunk.identity_ready ||
        chunk.persistent_regiment_backlink != regiment.id || chunk.native_chunk_index != i ||
        !chunk.current_soldiers_raw || *chunk.current_soldiers_raw < 0 ||
        !chunk.maximum_soldiers_raw || *chunk.maximum_soldiers_raw < 0 ||
        !chunk.army_regiment_id || !chunk.pending_raw || !chunk.state_raw) return false;
    regiment.chunks[static_cast<std::size_t>(i)] = {
        *chunk.current_soldiers_raw, *chunk.maximum_soldiers_raw,
        *chunk.army_regiment_id, *chunk.pending_raw, *chunk.state_raw};
  }
  return true;
}

struct Ledger {
  std::map<std::int32_t, Regiment> regiments;
  std::map<Key, Atom> atoms;
  std::set<std::int32_t> full_lower_sources;
  std::map<Key, std::int64_t> levy_lower_caps;
  std::map<std::int32_t, std::int32_t> source_owners;
  std::map<std::uint32_t, std::int32_t> current_regi_full_ids;
  std::set<Key> conflicting_keys;
  std::set<std::int32_t> conflicting_regiments;
  bool complete = true;

  void InsertFullId(std::int32_t id, PrewarForceOwnerBounds12004 &out) {
    const auto index = static_cast<std::uint32_t>(id) & 0xFFFFFFU;
    const auto [at, inserted] = current_regi_full_ids.emplace(index, id);
    if (!inserted && at->second != id) {
      conflicting_regiments.insert(at->second);
      conflicting_regiments.insert(id);
      complete = false;
      Reason(out, "current_regi_storage_index_generation_conflict");
    }
  }

  void InsertOwner(std::int32_t id, std::int32_t source_owner,
                   PrewarForceOwnerBounds12004 &out) {
    const auto [at, inserted] = source_owners.emplace(id, source_owner);
    if (!inserted && at->second != source_owner) {
      conflicting_regiments.insert(id);
      complete = false;
      Reason(out, "persistent_regiment_source_owner_raw_conflict");
    }
  }

  void InsertAtom(Key key, const Atom &atom, PrewarForceOwnerBounds12004 &out) {
    InsertFullId(key.first, out);
    const auto [at, inserted] = atoms.emplace(key, atom);
    if (!inserted && at->second != atom) {
      conflicting_keys.insert(key);
      complete = false;
      Reason(out, "physical_regi_chunk_raw_conflict");
    }
  }

  void Insert(const Regiment &regiment, bool lower_source,
              PrewarForceOwnerBounds12004 &out) {
    InsertOwner(regiment.id, regiment.source_owner, out);
    const auto [at, inserted] = regiments.emplace(regiment.id, regiment);
    if (!inserted && at->second != regiment) {
      conflicting_regiments.insert(regiment.id);
      complete = false;
      Reason(out, "persistent_regiment_raw_conflict");
    }
    if (lower_source) full_lower_sources.insert(regiment.id);
    for (std::int32_t i = 0; i < 7; ++i)
      InsertAtom({regiment.id, i}, regiment.chunks[static_cast<std::size_t>(i)], out);
  }
};

// The assigned DOMI native leaf wraps signed32 at every delta, regiment and
// cross-regiment addition. A positive final scalar is insufficient proof.
bool AssignedStock(const Regiment &regiment, std::int64_t &value) noexcept {
  value = regiment.capacity;
  if (!Int32(value)) return false;
  for (const auto &chunk : regiment.chunks) {
    if (chunk.maximum == 0) continue;
    const std::int64_t effective = chunk.state == 3 && chunk.current == 0
        ? chunk.maximum : chunk.current;
    const auto delta = effective - chunk.maximum;
    if (!Int32(delta)) return false;
    value += delta; // At most seven signed32 deltas: cannot overflow int64.
    if (!Int32(value)) return false;
  }
  return value >= 0;
}

bool Domicile(const PrewarOwnerDomicile12004 &domicile,
              Ledger &ledger, std::int64_t &upper,
              PrewarForceOwnerBounds12004 &out) {
  if (!domicile.association_read_complete || !domicile.current_ready ||
      !domicile.current_upper_soldiers || *domicile.current_upper_soldiers < 0) return false;
  if (domicile.association_empty) {
    return (domicile.realm_present == false || domicile.domicile_id == -1) &&
        *domicile.current_upper_soldiers == 0;
  }
  if (!domicile.full_generation_ready || !domicile.domicile_id ||
      *domicile.domicile_id == -1 || domicile.observed_full_id != domicile.domicile_id ||
      domicile.observed_magic != 0x446F6D69U || !domicile.native_owner_identity_ready ||
      !domicile.native_owner_character_id || *domicile.native_owner_character_id == -1 ||
      domicile.observed_native_owner_full_id != domicile.native_owner_character_id ||
      domicile.observed_native_owner_magic != 0x43686172U ||
      !domicile.native_owner_type_predicate || !domicile.assigned_branch ||
      !domicile.native_current_call_succeeded ||
      !domicile.native_out_echo_ready || !domicile.native_current_raw_q100000 ||
      *domicile.native_current_raw_q100000 < 0) return false;
  const auto raw = *domicile.native_current_raw_q100000;
  const auto ceil = raw / 100000 + (raw % 100000 != 0 ? 1 : 0);
  if (ceil != *domicile.current_upper_soldiers) return false;
  if (*domicile.native_owner_type_predicate) {
    if (domicile.assigned_owner_military_present != true ||
        !Collection(domicile.assigned_regiment_ids) ||
        *domicile.assigned_branch != (*domicile.assigned_regiment_ids.count != 0) ||
        domicile.assigned_regiments.size() != domicile.assigned_regiment_ids.full_ids.size())
      return false;
  } else if (*domicile.assigned_branch) return false;
  if (*domicile.assigned_branch) {
    if (!domicile.assigned_owner_military_present ||
        !*domicile.assigned_owner_military_present ||
        !domicile.assigned_atoms_read_complete || !domicile.assigned_accumulator_int32_ready ||
        !domicile.assigned_current_accumulator || !Collection(domicile.assigned_regiment_ids) ||
        domicile.assigned_regiments.size() != domicile.assigned_regiment_ids.full_ids.size())
      return false;
    std::int64_t sum = 0;
    for (std::size_t i = 0; i < domicile.assigned_regiments.size(); ++i) {
      const auto &row = domicile.assigned_regiments[i];
      Regiment regiment{};
      std::int64_t current = 0;
      if (row.occurrence_index != static_cast<std::int32_t>(i) ||
          row.persistent_regiment_id != domicile.assigned_regiment_ids.full_ids[i] ||
          !OwnerRegiment(row, regiment) || !AssignedStock(regiment, current) ||
          !Add(sum, current) || !Int32(sum)) return false;
      ledger.Insert(regiment, false, out);
    }
    if (sum != *domicile.assigned_current_accumulator || raw != sum * 100000) return false;
  }
  return Add(upper, ceil);
}

bool ReadyAtom(const Atom &atom) noexcept {
  return atom.pending == 0 && atom.army_regiment_id == -1 && atom.state != 1;
}

bool ProjectPhysical(Ledger &ledger, std::int64_t &lower,
                     std::int64_t &upper, PrewarForceOwnerBounds12004 &out) {
  std::map<std::int32_t, std::int64_t> per_regiment_lower;
  for (const auto &[key, atom] : ledger.atoms) {
    if (ledger.conflicting_keys.contains(key) ||
        ledger.conflicting_regiments.contains(key.first) || !ReadyAtom(atom)) continue;
    std::int64_t floor = 0;
    if (ledger.full_lower_sources.contains(key.first) && atom.maximum > 0)
      floor = atom.current;
    if (const auto at = ledger.levy_lower_caps.find(key); at != ledger.levy_lower_caps.end())
      floor = (std::max)(floor, (std::min)(static_cast<std::int64_t>(atom.current), at->second));
    if (!Add(per_regiment_lower[key.first], floor)) return false;
  }
  for (const auto &[id, regiment] : ledger.regiments) {
    if (ledger.conflicting_regiments.contains(id)) continue;
    std::int64_t maximum = 0, excess = 0;
    for (const auto &chunk : regiment.chunks) {
      if (!Add(maximum, chunk.maximum) || !Add(excess,
          (std::max)(std::int64_t{0}, static_cast<std::int64_t>(chunk.current) - chunk.maximum)))
        return false;
    }
    auto cap = (std::max)(static_cast<std::int64_t>(regiment.capacity), maximum);
    if (!Add(cap, excess) || !Add(upper, cap)) return false;
    // Do not assume capacity128 equals the seven chunk maxima. Positive
    // capacity residual is never added to the observed physical floor.
    auto &floor = per_regiment_lower[id];
    const auto excess_maximum = (std::max)(std::int64_t{0}, maximum - regiment.capacity);
    floor = (std::max)(std::int64_t{0}, floor - excess_maximum);
  }
  for (const auto &[id, floor] : per_regiment_lower) {
    (void)id;
    if (!Add(lower, floor)) return false;
  }
  if (!ledger.complete) Reason(out, "physical_union_partial");
  return true;
}

} // namespace

bool ProjectPrewarForceOwnerBounds12004(
    const PrewarOwnerInventory12004 &owner,
    const PrewarLevyInventorySnapshot12004 &levy,
    const PrewarHiredInventory12004 &hired,
    PrewarForceOwnerBounds12004 &output) noexcept {
  try {
    output = {};
    output.owner_character_id = owner.owner_character_id;
    if (owner.owner_character_id == -1 || !owner.snapshot_revision ||
        !owner.exact_build_ready || !owner.owner_identity_ready ||
        owner.observed_owner_full_id != owner.owner_character_id ||
        owner.observed_owner_magic != 0x43686172U ||
        owner.composition_owner_echo_90 != owner.owner_character_id ||
        !owner.owner_echo_ready || !owner.native_lifetime_ready ||
        !owner.cleanup_succeeded || !owner.source_frame_ready) {
      Reason(output, "owner_inventory_identity_frame_or_lifetime_unavailable");
      return false;
    }
    Ledger ledger;
    bool complete = owner.owner_stock_inventory_complete;
    if (!complete) Reason(output, "owner_stock_inventory_partial");
    std::int64_t lower = 0, upper = 0;
    const bool personal_census = Collection(owner.persistent_regiment_ids) &&
        owner.persistent_regiments.size() == owner.persistent_regiment_ids.full_ids.size();
    if (!personal_census) { complete = false; Reason(output, "persistent_inventory_census_partial"); }
    for (std::size_t i = 0; i < owner.persistent_regiments.size(); ++i) {
      const auto &row = owner.persistent_regiments[i];
      Regiment regiment{};
      if (i >= owner.persistent_regiment_ids.full_ids.size() ||
          row.occurrence_index != static_cast<std::int32_t>(i) ||
          row.persistent_regiment_id != owner.persistent_regiment_ids.full_ids[i] ||
          !OwnerRegiment(row, regiment)) {
        complete = false; Reason(output, "persistent_regiment_atoms_partial"); continue;
      }
      ledger.Insert(regiment, true, output);
    }

    // This whole +38 collection already includes Merc/Holy holder knights.
    // There is no additional company scalar or company knight-count term.
    const bool knight_census = Collection(owner.knight_character_ids) &&
        owner.knights.size() == owner.knight_character_ids.full_ids.size();
    if (!knight_census) { complete = false; Reason(output, "whole_knight_census_partial"); }
    std::map<std::int32_t, PrewarOwnerKnight12004> knights;
    std::set<std::int32_t> conflicting_knights;
    for (std::size_t i = 0; i < owner.knights.size(); ++i) {
      const auto &row = owner.knights[i];
      if (i >= owner.knight_character_ids.full_ids.size() ||
          row.character_id != owner.knight_character_ids.full_ids[i] || row.character_id == -1 ||
          row.occurrence_index != static_cast<std::int32_t>(i) ||
          !row.full_generation_ready || !row.atoms_read_complete ||
          row.observed_full_id != row.character_id || row.observed_magic != 0x43686172U ||
          !row.assignment_component_present ||
          (*row.assignment_component_present && !row.army_regiment_id_raw)) {
        complete = false; Reason(output, "knight_identity_or_assignment_partial"); continue;
      }
      const auto [at, inserted] = knights.emplace(row.character_id, row);
      if (!inserted && (at->second.assignment_component_present != row.assignment_component_present ||
                       at->second.army_regiment_id_raw != row.army_regiment_id_raw)) {
        conflicting_knights.insert(row.character_id);
        complete = false; Reason(output, "knight_assignment_raw_conflict");
      }
    }
    for (const auto &[id, row] : knights) {
      if (conflicting_knights.contains(id)) continue;
      if (!Add(upper, 1)) return false;
      if ((!*row.assignment_component_present || row.army_regiment_id_raw == -1) &&
          !Add(lower, 1)) return false;
    }

    // The ArRg copied scalars may overlap physical chunks/knights. They are
    // conservative upper terms only, never extra physical lower credit.
    const bool raised_census = Collection(owner.raised_army_regiment_ids) &&
        owner.raised_army_regiments.size() == owner.raised_army_regiment_ids.full_ids.size();
    if (!raised_census) { complete = false; Reason(output, "raised_arrg_census_partial"); }
    std::map<std::int32_t, std::pair<std::int32_t, std::int32_t>> raised;
    for (std::size_t i = 0; i < owner.raised_army_regiments.size(); ++i) {
      const auto &row = owner.raised_army_regiments[i];
      if (i >= owner.raised_army_regiment_ids.full_ids.size() ||
          row.army_regiment_id != owner.raised_army_regiment_ids.full_ids[i] ||
          row.occurrence_index != static_cast<std::int32_t>(i) || row.army_regiment_id == -1 ||
          !row.full_generation_ready || !row.atoms_read_complete ||
          row.observed_full_id != row.army_regiment_id || row.observed_magic != 0x41725267U ||
          !row.current_soldiers_raw || *row.current_soldiers_raw < 0 ||
          !row.maximum_soldiers_raw || *row.maximum_soldiers_raw < 0) {
        complete = false; Reason(output, "raised_arrg_scalar_partial"); continue;
      }
      const auto value = std::pair{*row.current_soldiers_raw, *row.maximum_soldiers_raw};
      const auto [at, inserted] = raised.emplace(row.army_regiment_id, value);
      if (!inserted && at->second != value) {
        complete = false; Reason(output, "raised_arrg_scalar_conflict");
      }
    }
    for (const auto &[id, value] : raised) {
      (void)id;
      // Only the actual current scalar contributes. The raised maximum is
      // a future filled roster capacity, not a current inventory component.
      if (!Add(upper, value.first)) return false;
    }

    const bool levy_frame = levy.exact_build_ready && levy.owner_identity_ready &&
        levy.source_frame_ready && levy.cleanup_ready &&
        levy.owner_character_id == owner.owner_character_id &&
        levy.actor_character_id == owner.actor_character_id &&
        levy.snapshot_revision == owner.snapshot_revision && levy.date_raw == owner.date_raw;
    const bool levy_census = levy_frame && levy.collection_complete && levy.source_count &&
        *levy.source_count >= 0 && levy.descriptors.size() == static_cast<std::size_t>(*levy.source_count);
    if (!levy_census) { complete = false; Reason(output, "full_mask_f_levy_census_partial"); }
    if (levy_frame) for (std::size_t i = 0; i < levy.descriptors.size(); ++i) {
      const auto &row = levy.descriptors[i];
      if (row.source_ordinal != static_cast<std::int32_t>(i) ||
          !row.descriptor_identity_ready || row.descriptor_vtable_rva != kPrewarLevyDescriptorVtableRva12004 ||
          !row.physical_fields_ready || !row.native_count_inputs_ready ||
          !row.persistent_regiment_id || *row.persistent_regiment_id == -1 ||
          row.observed_persistent_full_id != row.persistent_regiment_id ||
          !row.chunk_ordinal || *row.chunk_ordinal < 0 || *row.chunk_ordinal >= 7 ||
          row.chunk_persistent_backlink != row.persistent_regiment_id ||
          row.native_chunk_ordinal != row.chunk_ordinal ||
          !row.persistent_owner_character_id ||
          !row.contribution_cap_raw || *row.contribution_cap_raw < 0 ||
          !row.current_soldiers_raw || *row.current_soldiers_raw < 0 ||
          !row.maximum_soldiers_raw || *row.maximum_soldiers_raw < 0 ||
          !row.army_regiment_id || !row.pending_raw || !row.state_raw) {
        complete = false; Reason(output, "levy_descriptor_or_physical_atoms_partial"); continue;
      }
      const Key key{*row.persistent_regiment_id, *row.chunk_ordinal};
      ledger.InsertOwner(key.first, *row.persistent_owner_character_id, output);
      ledger.InsertAtom(key, {*row.current_soldiers_raw, *row.maximum_soldiers_raw,
          *row.army_regiment_id, *row.pending_raw, *row.state_raw}, output);
      auto &cap = ledger.levy_lower_caps[key];
      cap = (std::max)(cap, static_cast<std::int64_t>(*row.contribution_cap_raw));
      // Keep every cap occurrence for the conservative upper. In particular,
      // max0/curr0, state3 fallback, state1 and pending are not discarded.
      if (!Add(upper, *row.contribution_cap_raw)) return false;
    }

    const auto employer = std::find_if(hired.employers.begin(), hired.employers.end(),
        [&](const auto &row) { return row.character_id == owner.owner_character_id; });
    const bool hired_census = hired.exact_build_ready && employer != hired.employers.end() &&
        std::count_if(hired.employers.begin(), hired.employers.end(),
            [&](const auto &row) { return row.character_id == owner.owner_character_id; }) == 1 &&
        employer->identity_ready && employer->mercenary_inventory_complete &&
        employer->holy_order_inventory_complete && employer->physical_hired_rosters_complete &&
        hired.mercenary_registry_complete && hired.holy_order_registry_complete &&
        hired.mercenary_registry_capacity && hired.holy_order_registry_capacity &&
        *hired.mercenary_registry_capacity >= 0 && *hired.holy_order_registry_capacity >= 0 &&
        hired.mercenary_slots_scanned == *hired.mercenary_registry_capacity &&
        hired.holy_order_slots_scanned == *hired.holy_order_registry_capacity;
    if (!hired_census) { complete = false; Reason(output, "selected_employer_hired_census_partial"); }
    if (hired.exact_build_ready) for (const auto &organisation : hired.organisations) {
      if (organisation.employer_character_id != owner.owner_character_id) continue;
      if (!organisation.registry_identity_ready || !organisation.employer_identity_ready ||
          !organisation.selected_employer || !organisation.military_kind) {
        complete = false; Reason(output, "hired_organisation_identity_partial"); continue;
      }
      if (!*organisation.military_kind) continue;
      if (!organisation.persistent_roster_complete || !organisation.source_regiment_capacity ||
          !organisation.source_regiment_count || *organisation.source_regiment_count < 0 ||
          *organisation.source_regiment_capacity < *organisation.source_regiment_count ||
          organisation.regiments.size() != static_cast<std::size_t>(*organisation.source_regiment_count)) {
        complete = false; Reason(output, "hired_physical_roster_partial");
      }
      for (std::size_t i = 0; i < organisation.regiments.size(); ++i) {
        const auto &row = organisation.regiments[i];
        Regiment regiment{};
        if (row.source_index != static_cast<std::int32_t>(i) || !HiredRegiment(row, regiment)) {
          complete = false; Reason(output, "hired_regiment_physical_atoms_partial"); continue;
        }
        ledger.Insert(regiment, true, output);
      }
    }
    if (!Domicile(owner.domicile, ledger, upper, output)) {
      complete = false; Reason(output, "domicile_full_current_or_int32_census_unqualified");
    }
    if (!ProjectPhysical(ledger, lower, upper, output)) {
      Reason(output, "force_bounds_checked_int64_overflow");
      return false;
    }
    output.actor_lower_soldiers = lower;
    output.actor_lower_ready = true;
    complete = complete && ledger.complete;
    if (complete && upper >= lower) {
      output.inventory_upper_soldiers = upper;
      output.inventory_upper_ready = true;
    } else if (complete) Reason(output, "force_bounds_upper_below_known_floor");
    return true;
  } catch (...) {
    output.owner_character_id = owner.owner_character_id;
    output.actor_lower_soldiers.reset();
    output.actor_lower_ready = false;
    output.inventory_upper_soldiers.reset();
    output.inventory_upper_ready = false;
    output.inventory_scope.clear();
    output.unavailable_reasons.clear();
    return false;
  }
}

} // namespace xar::ck3_12004
