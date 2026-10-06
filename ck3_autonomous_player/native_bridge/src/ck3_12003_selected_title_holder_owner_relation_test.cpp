#include "xar_bridge/ck3_12003_selected_title_holder_owner_relation.hpp"
#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/army_strength_v1_serializer.hpp"
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <initializer_list>
#include <iostream>
#include <memory>
#include <optional>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace {
using namespace xar;
void Check(bool value, const char *message) { if (!value) throw std::runtime_error(message); }

struct Memory {
  struct Region { std::unique_ptr<std::byte[]> bytes; std::size_t size; };
  struct Range { const void *address; std::size_t size; };
  std::vector<Region> regions;
  std::vector<Range> denied, relation_reads;
  std::size_t denied_attempts = 0;
  bool in_relation = false;
  void *Allocate(std::size_t size) {
    auto bytes = std::make_unique<std::byte[]>(size); auto *object = bytes.get();
    regions.push_back({std::move(bytes), size}); return object;
  }
  template <class T> void Put(void *object, std::size_t offset, T value) {
    std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
  }
  static const void *At(const void *object, std::size_t offset) {
    return static_cast<const std::byte *>(object) + offset;
  }
  void Deny(const void *object, std::size_t offset, std::size_t size) { denied.push_back({At(object, offset), size}); }
  std::size_t Reads(const void *object, std::size_t offset, std::size_t size) const {
    const auto address = At(object, offset);
    return static_cast<std::size_t>(std::count_if(relation_reads.begin(), relation_reads.end(),
        [&](const auto &read) { return read.address == address && read.size == size; }));
  }
  std::vector<std::vector<std::byte>> Snapshot() const {
    std::vector<std::vector<std::byte>> out;
    for (const auto &region : regions) out.emplace_back(region.bytes.get(), region.bytes.get() + region.size);
    return out;
  }
  static bool Read(void *context, const void *address, void *out, std::size_t size) noexcept {
    auto &memory = *static_cast<Memory *>(context); const auto begin = reinterpret_cast<std::uintptr_t>(address);
    for (const auto &range : memory.denied) {
      const auto denied = reinterpret_cast<std::uintptr_t>(range.address);
      if (memory.in_relation && begin < denied + range.size && denied < begin + size) {
        ++memory.denied_attempts; return false;
      }
    }
    for (const auto &region : memory.regions) {
      const auto base = reinterpret_cast<std::uintptr_t>(region.bytes.get());
      if (begin >= base && begin - base <= region.size && size <= region.size - (begin - base)) {
        std::memcpy(out, address, size); return true;
      }
    }
    return false;
  }
  static bool RelationRead(void *context, const void *address, void *out, std::size_t size) noexcept {
    auto &memory = *static_cast<Memory *>(context); memory.in_relation = true;
    memory.relation_reads.push_back({address, size});
    const bool copied = Read(context, address, out, size); memory.in_relation = false; return copied;
  }
};
struct Registry {
  Memory &memory;
  void *slot, *fallback_slot, *store, *rows;
  std::size_t full_id_offset;
  explicit Registry(Memory &m, std::size_t full_offset = 0x10) : memory(m), slot(m.Allocate(8)),
      fallback_slot(m.Allocate(8)), store(m.Allocate(0x30)), rows(m.Allocate(16 * 16)), full_id_offset(full_offset) {
    m.Put(slot, 0, store); m.Put(store, 0x20, rows); m.Put(store, 0x2C, std::uint32_t{16});
  }
  void Add(std::uint32_t id, void *object) {
    memory.Put(rows, static_cast<std::size_t>(id & 0xFFFFFFU) * 16 + 8, object);
    memory.Put(object, full_id_offset, id);
  }
};
struct Fixture;
Fixture *active = nullptr;
bool Relation(const void *, std::uint32_t);
std::int32_t Current(void *, std::uint8_t);
std::int32_t Maximum(void *);

struct Fixture {
  static constexpr std::uint32_t kArmy = 0xAB000001U, kUnit = 0x88000001U;
  static constexpr std::uint32_t kTitle = 0xCA000002U, kHolder = 0xEF000003U, kOwner = 0xA9000004U;
  static constexpr std::uint32_t kParent = 0xBB000005U;
  static constexpr std::uint32_t kSubjectUnit = 11, kSubjectArmy = 12, kSubjectArRg = 13;
  Memory memory;
  Registry armies{memory}, units{memory}, titles{memory}, characters{memory, 0x18};
  Registry strength_armies{memory}, subject_units{memory}, arrgs{memory};
  void *army = memory.Allocate(0x200), *unit = memory.Allocate(0x180);
  void *province = memory.Allocate(0x880), *province_fallback_slot = memory.Allocate(8);
  void *title = memory.Allocate(0x130), *parent_title = memory.Allocate(0x130);
  void *definition = memory.Allocate(0x70), *holder = memory.Allocate(0x20);
  void *state_slot = memory.Allocate(8), *state = memory.Allocate(0xA8);
  void *data = memory.Allocate(0x2A540 + 0x190), *manager = static_cast<std::byte *>(data) + 0x2A540;
  void *subject_unit = memory.Allocate(0x180), *subject_army = memory.Allocate(0x200);
  void *subject_arrg = memory.Allocate(0x150);
  ck3_12003::CurrentSelectedTitleHolderOwnerRelationBindings12003 bindings{};
  ck3_12002::ArmyBindings query_bindings{};
  std::vector<game::ArmyStrengthSnapshot> whole_rows;
  std::uint32_t requested = kArmy, expected_owner = kOwner;
  const void *expected_holder = holder;
  bool relation_value = true, null_inner_stores = false;
  std::int32_t relation_calls = 0;

  Fixture() {
    armies.Add(kArmy, army); memory.Put(armies.fallback_slot, 0, army);
    units.Add(kUnit, unit); memory.Put(units.fallback_slot, 0, unit);
    titles.Add(kTitle, title); titles.Add(kParent, parent_title); memory.Put(titles.fallback_slot, 0, title);
    characters.Add(kHolder, holder); memory.Put(characters.fallback_slot, 0, holder);
    memory.Put(army, 0x124, kUnit); memory.Put(army, 0x1D4, std::uint8_t{1});
    memory.Put(army, 0x20, std::uint8_t{187}); memory.Put(unit, 0x18, std::uint32_t{1});
    memory.Put(unit, 0x20, province); memory.Put(unit, 0x174, kOwner);
    memory.Put(province_fallback_slot, 0, province);
    memory.Put(province, 0x85C, std::uint32_t{0x50726F76}); memory.Put(province, 0x738, kTitle);
    memory.Put(title, 0x128, kHolder); memory.Put(title, 0x48, definition);
    memory.Put(title, 0xE8, kParent); memory.Put(definition, 0x64, std::uint32_t{1});
    memory.Put(parent_title, 0x128, kHolder);
    strength_armies.Add(kSubjectArmy, subject_army);
    subject_units.Add(kSubjectUnit, subject_unit); arrgs.Add(kSubjectArRg, subject_arrg);
    memory.Put(subject_unit, 0x178, kSubjectArmy); memory.Put(subject_army, 0x124, kSubjectUnit);
    memory.Put(subject_arrg, 0x14, std::uint32_t{0x41725267});
    memory.Put(subject_arrg, 0x38, std::int32_t{20}); memory.Put(subject_arrg, 0x3C, std::int32_t{40});
    memory.Put(subject_arrg, 0x40, std::int64_t{4000000});
    memory.Put(state_slot, 0, state); memory.Put(state, 0xA0, data);
    Roster(requested); Ids(static_cast<std::byte *>(manager) + 0x68, {});
    Ids(static_cast<std::byte *>(army) + 0x38, {});
    Ids(static_cast<std::byte *>(subject_army) + 0x38, {kSubjectArRg});
    auto &common = bindings.common; common.enabled = true; common.game_state_slot = state_slot;
    common.army_registry_slot = armies.slot; common.army_fallback_slot = armies.fallback_slot;
    common.unit_registry_slot = units.slot; common.unit_fallback_slot = units.fallback_slot;
    common.character_registry_slot = characters.slot; common.character_fallback_slot = characters.fallback_slot;
    common.province_fallback_slot = province_fallback_slot; common.read_memory = Memory::Read; common.read_context = &memory;
    bindings.title_registry_slot = titles.slot; bindings.title_fallback_slot = titles.fallback_slot;
    bindings.get_relation = Relation;
    query_bindings.enabled = true; query_bindings.game_state_slot = static_cast<void **>(state_slot);
    query_bindings.unit_storage_slot = static_cast<void **>(subject_units.slot);
    query_bindings.internal_army_storage_slot = static_cast<void **>(strength_armies.slot);
    query_bindings.regiment_storage_slot = static_cast<void **>(arrgs.slot);
    query_bindings.get_army_current_soldiers = Current; query_bindings.get_army_maximum_soldiers = Maximum;
    query_bindings.current_daily_assault_roster_admission_bindings = common;
    auto &refresh = query_bindings.current_post_admission_refresh_bindings;
    refresh.common = common; refresh.arrg_registry_slot = arrgs.slot; refresh.arrg_fallback_slot = arrgs.fallback_slot;
    // Denials concern only the new collector, not the genuine same-query source producer.
    bindings.common.read_memory = Memory::RelationRead;
  }
  void Ids(void *header, std::initializer_list<std::uint32_t> ids) {
    memory.Put(header, 8, static_cast<std::int32_t>(ids.size()));
    memory.Put(header, 0xC, static_cast<std::int32_t>(ids.size()));
    void *raw = ids.size() ? memory.Allocate(ids.size() * 4) : nullptr;
    std::size_t index = 0; for (auto id : ids) memory.Put(raw, index++ * 4, id);
    memory.Put(header, 0, raw);
  }
  void Roster(std::uint32_t id) { requested = id; Ids(static_cast<std::byte *>(manager) + 0x50, {id, id}); }
  void Owner(std::uint32_t id) { expected_owner = id; memory.Put(unit, 0x174, id); }
  game::ArmyCurrentSelectedTitleHolderOwnerRelationV1 Observe() {
    active = this; const auto before = memory.Snapshot();
    query_bindings.current_selected_title_holder_owner_relation_bindings = bindings;
    const std::array<ck3_12002::ArmyStrengthScope, 2> scopes{{
        {static_cast<std::int32_t>(kSubjectUnit), game::ArmyStrengthScopeRole::player, {}},
        {static_cast<std::int32_t>(kSubjectUnit), game::ArmyStrengthScopeRole::active_war_ally, {7}}}};
    Check(ck3_12002::ReadArmyStrengthsForScope(query_bindings, scopes, whole_rows) ==
              game::ReadArmyStrengthsResult::available && whole_rows.size() == std::size_t{2},
          "selected holder requires genuine whole-query source route");
    for (const auto &row : whole_rows) {
      Check(row.available && row.current_soldiers == 20 && row.maximum_soldiers == 40 &&
                row.regiment_count == 1 && row.ai_base_power_raw == 4000000,
            "selected holder optional family must retain independent current strength");
      Check(row.current_post_admission_refresh_inputs_v1 && row.current_selected_title_holder_owner_relation_v1,
            "selected holder must borrow genuine same-query source through Root hook");
    }
    Check(whole_rows[0].current_selected_title_holder_owner_relation_v1 ==
              whole_rows[1].current_selected_title_holder_owner_relation_v1,
          "selected holder global capture must be shared by both scope rows");
    auto out = *whole_rows[0].current_selected_title_holder_owner_relation_v1;
    Check(before == memory.Snapshot(), "selected holder collector/callback wrote world memory");
    Check(memory.denied_attempts == std::size_t{0}, "selected holder read an undemanded source field");
    Check(out.occurrences.size() == std::size_t{2} && out.original_roster.occurrences.size() == std::size_t{2},
          "selected holder filtered duplicate original-roster occurrences");
    for (std::size_t i = 0; i < out.occurrences.size(); ++i) {
      const auto &row = out.occurrences[i];
      Check(row.native_index == static_cast<std::int32_t>(i) && row.raw_full_id_u32 == requested &&
                out.original_roster.occurrences[i].native_index == static_cast<std::int32_t>(i) &&
                out.original_roster.occurrences[i].raw_full_id_u32 == requested && row.same_query_army_selection_matched,
            "selected holder lost source occurrence order/full generation bits/physical selection");
      for (std::size_t j = 0; j < row.unit_selections.size(); ++j) {
        constexpr std::array<std::string_view, 3> purposes{"province_tag", "title_province", "unit_owner"};
        Check(j < purposes.size() && row.unit_selections[j].native_index == static_cast<std::int32_t>(j) &&
                  row.unit_selections[j].purpose == purposes[j], "selected holder Unit selection source order changed");
      }
    }
    Check(memory.Reads(units.slot, 0, 8) == std::size_t{2} &&
              memory.Reads(units.fallback_slot, 0, 8) == std::size_t{2},
          "selected holder must hold Unit store/fallback once per occurrence, not per selection");
    Check(!out.actual_refresh_execution_ready && !out.actual_next_occurrence_ready && !out.changed_selection_context_ready &&
              !out.changed_relationship_context_ready && !out.full_callback_ready && !out.full_daily_assault_ready && !out.full_monthly_ready,
          "selected holder current source observation raised future execution readiness");
    return out;
  }
};
std::int32_t Current(void *receiver, std::uint8_t flags) {
  Check(active && flags == std::uint8_t{0} && receiver == static_cast<std::byte *>(active->subject_army) + 0x38,
        "selected holder whole current-strength getter arguments changed"); return 20;
}
std::int32_t Maximum(void *receiver) {
  Check(active && receiver == active->subject_army, "selected holder whole maximum-strength receiver changed"); return 40;
}
bool Relation(const void *holder, std::uint32_t owner) {
  Check(active && holder == active->expected_holder && owner == active->expected_owner,
        "selected holder callback must receive actual Character pointer and full uint32 owner ID");
  ++active->relation_calls;
  // Replacement callable verifies production plumbing; no native leaf tree is transplanted or executed.
  return active->relation_value;
}
void Ready(const Fixture &fixture, const game::ArmyCurrentSelectedTitleHolderOwnerRelationV1 &out,
           std::uint8_t tail, std::optional<bool> native, std::size_t unit_steps) {
  Check(out.ready && out.original_army_selections_ready && out.current_shared_tail_inputs_ready,
        "selected holder source inputs did not unlock current shared tail");
  Check(fixture.relation_calls == (native.has_value() ? std::int32_t{2} : std::int32_t{0}),
        "selected holder native callback must execute once per unequal original occurrence");
  for (const auto &row : out.occurrences) {
    Check(row.ready && row.unit_selections.size() == unit_steps && row.derived_current_shared_tail_raw_u8 == tail &&
              row.current_shared_tail_inputs_ready && row.native_holder_owner_relation == native &&
              row.native_relation_demanded == native.has_value() && row.native_relation_returned == native.has_value(),
          "selected holder direct tail/native bool/demand distinction changed");
    if (unit_steps == std::size_t{3}) {
      Check(row.selected_unit_owner_174_raw_u32 == fixture.expected_owner && row.holder_character_full_id_u32 &&
                row.holder_owner_equal == (fixture.expected_owner == *row.holder_character_full_id_u32),
            "selected holder real owner/holder full ID evidence was lost");
      Check(!row.unit_selections[1].province_magic_85c_raw_u32,
            "selected holder second Province selection must not add another tag gate");
    }
  }
  Check(fixture.memory.Reads(fixture.army, 0x124, 4) ==
            (fixture.null_inner_stores ? std::size_t{0} : unit_steps * std::size_t{2}),
        "selected holder three native Unit selections were collapsed or added under null store");
  Check(fixture.memory.Reads(fixture.province, 0x85C, 4) == std::size_t{2},
        "selected holder first Province tag check must occur once per occurrence");
}
void SourceReadOrder(const Fixture &fixture) {
  std::size_t cursor = 0;
  const auto next = [&](const void *object, std::size_t offset, std::size_t size) {
    const auto address = Memory::At(object, offset);
    while (cursor < fixture.memory.relation_reads.size()) {
      const auto &read = fixture.memory.relation_reads[cursor++];
      if (read.address == address && read.size == size) return;
    }
    throw std::runtime_error("selected holder source pointer/store load order changed");
  };
  for (std::size_t occurrence = 0; occurrence < std::size_t{2}; ++occurrence) {
    next(fixture.unit, 0x20, 8); next(fixture.province_fallback_slot, 0, 8);
    next(fixture.province, 0x85C, 4); next(fixture.unit, 0x20, 8);
    next(fixture.titles.fallback_slot, 0, 8); next(fixture.titles.slot, 0, 8);
    next(fixture.unit, 0x174, 4);
  }
}
std::string Serialize(const Fixture &fixture) {
  std::string wire;
  game::AppendArmyStrengthV1(wire, fixture.whole_rows[0], [](auto value) { return std::to_string(value); },
      [](std::string &text, const std::vector<std::int32_t> &values) {
        text += '[';
        for (std::size_t i = 0; i < values.size(); ++i) { if (i) text += ','; text += std::to_string(values[i]); }
        text += ']';
      }, [](std::string &text, std::string_view value) { text += '"'; text += value; text += '"'; });
  return wire;
}
}

int main(int argc, char **argv) {
  try {
    const auto bound = xar::ck3_12003::BindCurrentSelectedTitleHolderOwnerRelation12003(0x140000000ULL,
        "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6");
    Check(bound.common.enabled && reinterpret_cast<std::uintptr_t>(bound.get_relation) == 0x1428B2820ULL &&
              reinterpret_cast<std::uintptr_t>(bound.title_registry_slot) == 0x145D1DAF8ULL &&
              reinterpret_cast<std::uintptr_t>(bound.title_fallback_slot) == 0x145D1DAE0ULL,
          "selected holder exact .3 binder addresses changed");
    std::vector<std::pair<std::string, std::string>> samples;
    { Fixture f; f.memory.Put(f.province, 0x85C, std::uint32_t{0}); f.bindings.get_relation = nullptr;
      f.memory.Deny(f.province, 0x738, 4); f.memory.Deny(f.title, 0x128, 4); f.memory.Deny(f.unit, 0x174, 4);
      auto out = f.Observe(); Ready(f, out, std::uint8_t{0}, std::nullopt, std::size_t{1});
      Check(!out.occurrences[0].province_title_738_raw_u32 && !out.occurrences[0].holder_requested_full_id_u32 &&
                !out.occurrences[0].holder_character_full_id_u32 && !out.occurrences[0].selected_unit_owner_174_raw_u32 &&
                out.occurrences[0].title_resolution.selection == "not_demanded",
            "selected holder invalid first tag demanded title/holder/owner inputs");
      samples.emplace_back("invalid-first-province-undemanded", Serialize(f)); }
    { Fixture f; f.Owner(Fixture::kHolder); f.bindings.get_relation = nullptr;
      auto out = f.Observe(); Ready(f, out, std::uint8_t{1}, std::nullopt, std::size_t{3}); SourceReadOrder(f);
      Check(out.occurrences[0].holder_owner_equal == true, "selected holder direct equality branch not retained");
      samples.emplace_back("direct-equal", Serialize(f)); }
    { Fixture f; f.Owner(std::uint32_t{0}); f.relation_value = false;
      auto out = f.Observe(); Ready(f, out, std::uint8_t{0}, false, std::size_t{3});
      Check(out.occurrences[0].selected_unit_owner_174_raw_u32 == std::uint32_t{0}, "selected holder rejected legal owner zero");
      samples.emplace_back("native-false-owner-zero", Serialize(f)); }
    { Fixture f; f.characters.Add(std::uint32_t{0}, f.holder); f.memory.Put(f.title, 0x128, std::uint32_t{0});
      auto out = f.Observe(); Ready(f, out, std::uint8_t{1}, true, std::size_t{3});
      Check(out.occurrences[0].holder_requested_full_id_u32 == std::uint32_t{0} &&
                out.occurrences[0].holder_character_full_id_u32 == std::uint32_t{0} &&
                out.occurrences[0].holder_character_resolution.used_fallback == false,
            "selected holder rejected legal holder request zero");
      samples.emplace_back("native-true-holder-zero", Serialize(f)); }
    { Fixture f; auto out = f.Observe(); Ready(f, out, std::uint8_t{1}, true, std::size_t{3});
      Check(out.occurrences[0].raw_full_id_u32 == Fixture::kArmy &&
                out.occurrences[0].holder_requested_full_id_u32 == Fixture::kHolder &&
                out.occurrences[0].selected_unit_owner_174_raw_u32 == Fixture::kOwner &&
                out.occurrences[0].unit_selections[0].unit_resolution.requested_full_id_u32 == Fixture::kUnit &&
                out.occurrences[0].title_resolution.requested_full_id_u32 == Fixture::kTitle,
            "selected holder discarded high bit or generation bits"); SourceReadOrder(f);
      samples.emplace_back("native-true-highbit-fullgen", Serialize(f)); }
    { Fixture f; f.Roster(0xCD000001U); f.memory.Put(f.army, 0x124, std::uint32_t{0xDD000001});
      f.memory.Put(f.province, 0x738, std::uint32_t{0xDD000002}); f.memory.Put(f.title, 0x128, std::uint32_t{0xDD000003});
      auto out = f.Observe(); Ready(f, out, std::uint8_t{1}, true, std::size_t{3});
      const auto &row = out.occurrences[0];
      Check(row.original_army_resolution.used_fallback == true && row.title_resolution.used_fallback == true &&
                row.holder_character_resolution.used_fallback == true && row.holder_character_full_id_u32 == Fixture::kHolder,
            "selected holder requested-generation mismatch lost native physical fallbacks");
      for (const auto &unit : row.unit_selections) Check(unit.unit_resolution.used_fallback == true,
            "selected holder each Unit selection must retain requested generation mismatch");
      samples.emplace_back("requested-generation-fallbacks", Serialize(f)); }
    { Fixture f; f.memory.Put(f.title, 0x128, std::uint32_t{0xFFFFFFFF});
      auto out = f.Observe(); Ready(f, out, std::uint8_t{1}, true, std::size_t{3});
      Check(out.occurrences[0].title_definition_64_raw_u32 == std::uint32_t{1} &&
                out.occurrences[0].parent_title_e8_raw_u32 == Fixture::kParent &&
                out.occurrences[0].parent_holder_128_raw_u32 == Fixture::kHolder &&
                out.occurrences[0].holder_requested_full_id_u32 == Fixture::kHolder,
            "selected holder FF tier-one branch did not select parent Title+E8 holder");
      samples.emplace_back("missing-holder-parent-tier-one", Serialize(f)); }
    { Fixture f; f.memory.Put(f.title, 0x128, std::uint32_t{0xFFFFFFFF});
      f.memory.Put(f.definition, 0x64, std::uint32_t{2}); f.memory.Deny(f.title, 0xE8, 4);
      auto out = f.Observe(); Ready(f, out, std::uint8_t{1}, true, std::size_t{3});
      Check(!out.occurrences[0].parent_title_e8_raw_u32 &&
                out.occurrences[0].holder_requested_full_id_u32 == std::uint32_t{0xFFFFFFFF} &&
                out.occurrences[0].holder_character_resolution.used_fallback == true,
            "selected holder FF other-tier branch must request native Character fallback, not parent");
      samples.emplace_back("missing-holder-other-tier", Serialize(f)); }
    { Fixture f; f.null_inner_stores = true;
      f.memory.Put(f.armies.slot, 0, static_cast<void *>(nullptr)); f.memory.Put(f.units.slot, 0, static_cast<void *>(nullptr));
      f.memory.Put(f.titles.slot, 0, static_cast<void *>(nullptr)); f.memory.Put(f.characters.slot, 0, static_cast<void *>(nullptr));
      f.memory.Put(f.unit, 0x20, static_cast<void *>(nullptr)); f.memory.Put(f.title, 0x128, std::uint32_t{0xFFFFFFFF});
      f.memory.Deny(f.army, 0x124, 4); f.memory.Deny(f.province, 0x738, 4); f.memory.Deny(f.title, 0xE8, 4);
      auto out = f.Observe(); Ready(f, out, std::uint8_t{1}, true, std::size_t{3});
      const auto &row = out.occurrences[0];
      Check(row.original_army_resolution.used_fallback == true && !row.province_title_738_raw_u32 &&
                !row.parent_title_e8_raw_u32 && row.title_resolution.registry_loaded == false &&
                row.parent_title_resolution.used_fallback == true && row.holder_character_resolution.registry_loaded == false,
            "selected holder null inner stores fabricated requested IDs or skipped native fallback branch");
      for (const auto &step : row.unit_selections) Check(!step.army_124_raw_u32 &&
                step.unit_resolution.registry_loaded == false && step.unit_resolution.used_fallback == true,
            "selected holder null Unit store demanded Army124");
      Check(row.unit_selections[0].province_used_fallback == true && row.unit_selections[1].province_used_fallback == true,
            "selected holder both Province selections must use the held native fallback");
      samples.emplace_back("null-inner-stores-undemanded", Serialize(f)); }
    { Fixture f; f.bindings.get_relation = nullptr; auto out = f.Observe();
      Check(!out.ready && f.relation_calls == std::int32_t{0}, "selected holder missing callable became a native false");
      for (const auto &row : out.occurrences) Check(row.unit_selections.size() == std::size_t{3} &&
                row.native_relation_demanded && !row.native_relation_returned && !row.native_holder_owner_relation &&
                !row.derived_current_shared_tail_raw_u8 && row.holder_character_full_id_u32 == Fixture::kHolder &&
                row.selected_unit_owner_174_raw_u32 == Fixture::kOwner && row.holder_owner_equal == false,
            "selected holder missing callable must retain real operand IDs and unknown tail");
      samples.emplace_back("missing-callable", Serialize(f)); }
    Check(samples.size() == std::size_t{10}, "selected holder wire sample count changed");
    if (argc == 3 && std::string_view(argv[1]) == "--wire-dir") {
      const std::filesystem::path directory(argv[2]); std::filesystem::create_directories(directory);
      std::ofstream file(directory / "ck3_12003_selected_title_holder_owner_relation_wire.json", std::ios::binary);
      file << "{\"samples\":{";
      for (std::size_t i = 0; i < samples.size(); ++i) {
        if (i) file << ',';
        file << '"' << samples[i].first << "\":" << samples[i].second;
      }
      file << "},\"qualification\":\"genuine whole ReadArmyStrengthsForScope + AppendArmyStrengthV1; synthetic world and replacement28B callable; no native leaf transplant or game execution\"}\n";
      Check(static_cast<bool>(file), "selected holder wire write failed");
    }
    std::cout << "NEW selected-title holder-owner relation: ten whole-query samples passed; synthetic callback, no game execution\n";
    return 0;
  } catch (const std::exception &error) { std::cerr << error.what() << '\n'; return 1; }
}
