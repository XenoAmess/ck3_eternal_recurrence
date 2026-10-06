#include "xar_bridge/army_strength_v1_serializer.hpp"
#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/ck3_12003_army_replenishment_records.hpp"
#include "xar_bridge/ck3_12003_ordered_besieging_fixed_chunk0_preparation.hpp"
#include "xar_bridge/ck3_12003_ordered_besieging_refill_inputs.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace {
using namespace xar;
constexpr std::int32_t kSubjectArRg = (7 << 24) | 11001;
constexpr std::int32_t kTargetArRg = (7 << 24) | 11002;
constexpr std::int32_t kSubjectRegi = (18 << 24) | 50001;
constexpr std::int32_t kTargetRegi = (18 << 24) | 50002;
constexpr std::int32_t kSubjectCArmy = (3 << 24) | 12;
constexpr std::int32_t kTargetCArmy = (3 << 24) | 30;
constexpr std::int32_t kSubjectArmy = (4 << 24) | 11;
constexpr std::int32_t kTargetArmy = (4 << 24) | 21;
constexpr std::uint32_t kRegiMagic = 0x52656769U;
constexpr std::uint32_t kArRgMagic = 0x41725267U;
constexpr std::uint32_t kOrdinaryDefinitionMagic = 0x11111111U;
constexpr std::uint32_t kPermissionDefinitionMagic = 0x4744624FU;

template<std::size_t N> using Blob = std::array<std::byte, N>;
template<class T, class Buffer>
void Store(Buffer &object, std::size_t offset, T value) {
  std::memcpy(object.data() + offset, &value, sizeof value);
}
template<class T>
T Load(const void *object, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof value);
  return value;
}
void Require(bool good, const char *message) {
  if (!good) throw std::runtime_error(message);
}

// Only raw fixture memory and native read bindings are mocked. The DATA, actual
// ordered-B scope, unique target preparation collector and Strength wire body
// below all run their production implementations.
void *subject_persistent = nullptr;
void *target_persistent = nullptr;
void *subject_arrg = nullptr;
void *target_arrg = nullptr;
void *invalid_arrg = nullptr;
void *target_unit = nullptr;
bool preparation_capture = false;
bool fixed_permission = false;
bool fresh_readable = true;
std::int64_t fresh_fraction = 10000;
int fixed_calls = 0;
int fresh_calls = 0;

bool Permission(void *persistent, void *chunk) {
  if (preparation_capture) {
    Require(persistent == target_persistent &&
                Load<std::int32_t>(persistent, 0x10) == kTargetRegi &&
                Load<std::uint32_t>(persistent, 0x14) == kRegiMagic,
            "preparation permission uses the actual target full-generation Regi");
    Require(chunk == static_cast<std::byte *>(target_persistent) + 0x18,
            "preparation permission uses physical chunk0, not DATA ordinal1");
    ++fixed_calls;
    return fixed_permission;
  }
  Require(persistent == subject_persistent || persistent == target_persistent,
          "DATA permission has a registered real persistent receiver");
  Require(chunk == static_cast<std::byte *>(persistent) + 0x18 + 0x24,
          "actual DATA reader selects physical chunk1");
  return true;
}
bool ChunkPermission(void *chunk) {
  Require(chunk == static_cast<std::byte *>(subject_persistent) + 0x18 + 0x24 ||
              chunk == static_cast<std::byte *>(target_persistent) + 0x18 + 0x24,
          "DATA chunk predicate receives its selected physical chunk1");
  return true;
}
std::int64_t *Fraction(void *persistent, std::int64_t *out) {
  if (preparation_capture) {
    Require(persistent == target_persistent &&
                Load<std::int32_t>(persistent, 0x10) == kTargetRegi,
            "fresh getter uses target outside subject DATA and its full generation");
    ++fresh_calls;
    if (!fresh_readable) return nullptr;
    *out = fresh_fraction;
  } else {
    Require(persistent == subject_persistent || persistent == target_persistent,
            "DATA getter has a registered real persistent receiver");
    *out = 10000;
  }
  return out;
}
bool LossWriterSkipped(void *regiment) {
  Require(regiment == subject_arrg || regiment == target_arrg,
          "DATA admission uses the actual subject or target ArRg");
  return false;
}
void *ArRgReference(const void *reference) {
  const auto id = Load<std::int32_t>(reference, 0);
  if (id == kTargetArRg) return target_arrg;
  if (id == kSubjectArRg) return subject_arrg;
  return invalid_arrg;
}
void *UnitReference(const void *reference) {
  Require(Load<std::int32_t>(reference, 0) == kTargetArmy,
          "physical context resolves the target CArmy's actual public unit");
  return target_unit;
}
bool NotInCombat(void *) { return false; }
bool PositionEligible(void *) { return true; }
std::int32_t *Holder(void *, std::int32_t *out) { *out = 777; return out; }

struct Storage {
  Blob<0x30> header{};
  std::vector<std::byte> entries;
  void *pointer = header.data();

  explicit Storage(std::int32_t capacity)
      : entries(static_cast<std::size_t>(capacity) * 16) {
    Store(header, 0x20, static_cast<void *>(entries.data()));
    Store(header, 0x2C, capacity);
  }
  void Add(std::int32_t full_id, void *object) {
    const auto index = static_cast<std::uint32_t>(full_id) & 0xFFFFFFU;
    Store(entries, static_cast<std::size_t>(index) * 16 + 8, object);
  }
};

struct Fixture {
  Blob<0x2A600> game_data{};
  Blob<0xB0> game_state{};
  Blob<0x160> subject_regi{}, target_regi{};
  Blob<0x40> subject_definition{}, target_definition{};
  Blob<0x900> origin_province{}, current_province{};
  Blob<0x180> subject_unit{}, refresh_unit{};
  Blob<0x200> subject_army{}, refresh_army{}, empty_army{};
  Blob<0x150> subject_raised{}, target_raised{};
  Blob<0x20> absent_raised{}, character{}, other_character{};
  Blob<0x20> subject_data{}, target_data{};
  std::array<std::int32_t, 3> refresh_regiment_order{kTargetArRg, -1, kTargetArRg};
  std::array<std::int32_t, 5> persistent_order{90001, kTargetRegi, 90002, kTargetRegi, 90001};
  std::array<std::int32_t, 4> army_order{99, kTargetCArmy, 99, kTargetCArmy};
  Storage persistent_storage{50003};
  Storage army_storage{31};
  Storage arrg_storage{11003};
  Storage character_storage{889};
  void *game_state_pointer = game_state.data();
  void *fallback_character = character.data();
  void *fallback_army = empty_army.data();
  void *fallback_arrg = absent_raised.data();
  void *fallback_persistent = target_regi.data();
  void *fallback_province = origin_province.data();
  ck3_12002::ArmyBindings bindings{};

  Fixture() {
    subject_persistent = subject_regi.data(); target_persistent = target_regi.data();
    subject_arrg = subject_raised.data(); target_arrg = target_raised.data();
    invalid_arrg = absent_raised.data(); target_unit = refresh_unit.data();
    preparation_capture = false; fixed_permission = false;
    fresh_readable = true; fresh_fraction = 10000;
    Store(game_state, 0xA0, static_cast<void *>(game_data.data()));
    Store(game_data, 0x2A570, static_cast<void *>(persistent_order.data()));
    Store(game_data, 0x2A578, std::int32_t{5}); Store(game_data, 0x2A57C, std::int32_t{5});
    Store(game_data, 0x2A590, static_cast<void *>(army_order.data()));
    Store(game_data, 0x2A598, std::int32_t{4}); Store(game_data, 0x2A59C, std::int32_t{4});
    InitPersistent(subject_regi, subject_definition, kSubjectRegi, kSubjectArRg);
    InitPersistent(target_regi, target_definition, kTargetRegi, kTargetArRg);
    InitRaised(subject_raised, subject_data, kSubjectArRg, kSubjectRegi, kSubjectCArmy);
    InitRaised(target_raised, target_data, kTargetArRg, kTargetRegi, kTargetCArmy);
    Store(absent_raised, 0x10, std::int32_t{-1});
    Store(origin_province, 0x10, std::int32_t{1});
    Store(origin_province, 0x788, std::int32_t{-1});
    Store(origin_province, 0x73C, std::int32_t{-1});
    Store(origin_province, 0x85C, std::uint32_t{0x50726F76U});
    Store(current_province, 0x10, std::int32_t{7});
    Store(current_province, 0x788, std::int32_t{77});
    Store(current_province, 0x85C, std::uint32_t{0x50726F76U});
    Store(subject_unit, 0x10, kSubjectArmy);
    Store(subject_unit, 0x20, static_cast<void *>(current_province.data()));
    Store(refresh_unit, 0x10, kTargetArmy);
    Store(refresh_unit, 0x20, static_cast<void *>(current_province.data()));
    Store(refresh_unit, 0x174, std::int32_t{777});
    Store(refresh_unit, 0x178, kTargetCArmy);
    Store(subject_army, 0x10, kSubjectCArmy);
    Store(subject_army, 0x124, kSubjectArmy);
    Store(subject_army, 0x44, std::int32_t{1});
    Store(refresh_army, 0x10, kTargetCArmy);
    Store(refresh_army, 0x124, kTargetArmy);
    Store(refresh_army, 0x38, static_cast<void *>(refresh_regiment_order.data()));
    Store(refresh_army, 0x44, std::int32_t{3});
    Store(empty_army, 0x10, std::int32_t{-1});
    Store(character, 0x18, std::int32_t{777});
    Store(other_character, 0x18, std::int32_t{888});
    persistent_storage.Add(kSubjectRegi, subject_regi.data());
    persistent_storage.Add(kTargetRegi, target_regi.data());
    army_storage.Add(kSubjectCArmy, subject_army.data());
    army_storage.Add(kTargetCArmy, refresh_army.data());
    arrg_storage.Add(kSubjectArRg, subject_raised.data());
    arrg_storage.Add(kTargetArRg, target_raised.data());
    character_storage.Add(777, character.data());
    character_storage.Add(888, other_character.data());
    bindings.enabled = true;
    bindings.game_state_slot = &game_state_pointer;
    bindings.persistent_regiment_storage_slot = &persistent_storage.pointer;
    bindings.internal_army_storage_slot = &army_storage.pointer;
    bindings.regiment_storage_slot = &arrg_storage.pointer;
    bindings.can_regiment_replenish = Permission;
    bindings.can_chunk_replenish = ChunkPermission;
    bindings.get_regiment_monthly_replenishment_fraction = Fraction;
    bindings.is_army_regiment_loss_writer_skipped = LossWriterSkipped;
    bindings.ordered_besieging_refill_bindings.enabled = true;
    bindings.ordered_besieging_refill_bindings.arrg_fallback_slot = &fallback_arrg;
    auto &native = bindings.scoped_ordered_refill_bindings;
    native.enabled = true;
    native.persistent_fallback_slot = &fallback_persistent;
    native.army_fallback_slot = &fallback_army;
    native.character_storage_slot = &character_storage.pointer;
    native.character_fallback_slot = &fallback_character;
    native.unit_position_province_fallback_slot = &fallback_province;
    native.resolve_arrg_reference = ArRgReference;
    native.resolve_unit_reference = UnitReference;
    native.is_army_in_combat = NotInCombat;
    native.is_unit_position_eligible = PositionEligible;
    native.read_province_holder = Holder;
  }

  void InitPersistent(Blob<0x160> &persistent, Blob<0x40> &definition,
                      std::int32_t persistent_id, std::int32_t raised_id) {
    Store(persistent, 0x10, persistent_id); Store(persistent, 0x14, kRegiMagic);
    Store(persistent, 0x118, static_cast<void *>(definition.data()));
    Store(persistent, 0x120, static_cast<void *>(origin_province.data()));
    Store(persistent, 0x138, std::int32_t{0});
    Store(persistent, 0x148, std::int64_t{0});
    Store(definition, 0x38, kOrdinaryDefinitionMagic);
    for (std::int32_t index = 0; index < 7; ++index) {
      const auto base = std::size_t{0x18} + static_cast<std::size_t>(index) * 0x24;
      Store(persistent, base, std::int32_t{index < 2 ? 100 : 0});
      Store(persistent, base + 4, std::int32_t{index < 2 ? 80 : 0});
      Store(persistent, base + 8, persistent_id); Store(persistent, base + 0xC, index);
      Store(persistent, base + 0x10, index < 2 ? raised_id : std::int32_t{-1});
    }
  }
  void InitRaised(Blob<0x150> &raised, Blob<0x20> &data,
                  std::int32_t raised_id, std::int32_t persistent_id,
                  std::int32_t army_id) {
    Store(raised, 0x10, raised_id); Store(raised, 0x14, kArRgMagic);
    Store(raised, 0x20, static_cast<void *>(data.data()));
    Store(raised, 0x28, std::int32_t{2}); Store(raised, 0x2C, std::int32_t{2});
    Store(raised, 0x140, army_id);
    for (std::size_t offset : {std::size_t{0}, std::size_t{0x10}}) {
      Store(data, offset + 8, persistent_id);
      Store(data, offset + 0xC, std::int32_t{1});
    }
  }

  game::ArmyCurrentProvinceBesiegingContributorsV1 Family(
      const game::ArmyRegimentReplenishmentRecordsSnapshotV1 &target_data_snapshot) const {
    game::ArmyCurrentProvinceBesiegingContributorsV1 family{};
    family.status = "available"; family.contributors_ready = true; family.province_id = 7;
    family.native_province_unit_count = 3; family.native_besieging_strength = 640;
    family.native_assault_expected_loss = 64;
    auto &context = family.assault_context;
    context.status = "available"; context.has_active_siege = true; context.siege_id = 77;
    context.breach_level_raw = 1; context.casualty_percentage_count = 3;
    context.casualty_percentage_raw = 1000000;
    for (const auto index : {0, 2}) {
      game::ArmyProvinceBesiegingOccurrenceV1 occurrence{};
      occurrence.stored_index = index;
      occurrence.public_unit_id = kTargetArmy; occurrence.resolved_unit_id = kTargetArmy;
      occurrence.unit_used_fallback = false; occurrence.current_province_used_fallback = false;
      occurrence.current_province_id = 7; occurrence.raw_unit18 = 0;
      occurrence.raw_unit170 = 0; occurrence.raw_unit44 = 0;
      occurrence.native_carmy_id = kTargetCArmy; occurrence.army_used_fallback = false;
      occurrence.eligible = true; occurrence.available = true;
      occurrence.native_whole_current_soldiers = 320;
      for (const auto stored : {0, 1}) {
        game::ArmyProvinceBesiegingRegimentV1 regiment{};
        regiment.stored_index = stored; regiment.army_regiment_id = kTargetArRg;
        regiment.available = true; regiment.current_soldiers = 160;
        regiment.maximum_soldiers = 200;
        regiment.replenishment_records_v1 = target_data_snapshot;
        occurrence.regiments.push_back(std::move(regiment));
      }
      family.occurrences.push_back(std::move(occurrence));
    }
    return family;
  }

  game::ArmyStrengthSnapshot Capture(bool missing_fixed_permission = false) {
    const auto subject_before = subject_regi;
    const auto target_before = target_regi;
    preparation_capture = false;
    const auto subject_records = ck3_12003::ReadArmyRegimentReplenishmentRecordsV1(
        bindings, subject_raised.data(), kSubjectArRg);
    const auto target_records = ck3_12003::ReadArmyRegimentReplenishmentRecordsV1(
        bindings, target_raised.data(), kTargetArRg);
    Require(subject_records.status == game::ArmyRegimentReplenishmentRecordsStatusV1::available &&
                subject_records.records.size() == 2 &&
                subject_records.records[0].persistent_regiment_id == kSubjectRegi &&
                subject_records.records[1].persistent_regiment_id == kSubjectRegi,
            "query subject actual DATA contains only its own persistent");
    auto family = Family(target_records);
    auto scope = ck3_12003::ReadOrderedBesiegingRefillInputs12003(
        bindings, subject_army.data(), subject_unit.data(), family);
    auto preparation_bindings = bindings;
    if (missing_fixed_permission) preparation_bindings.can_regiment_replenish = nullptr;
    fixed_calls = 0; fresh_calls = 0; preparation_capture = true;
    auto preparation = ck3_12003::ReadOrderedBesiegingFixedChunk0PreparationInputs12003(
        preparation_bindings, scope);
    preparation_capture = false;
    Require(subject_regi == subject_before && target_regi == target_before &&
                Load<std::int64_t>(subject_regi.data(), 0x148) == 0 &&
                Load<std::int64_t>(target_regi.data(), 0x148) == 0,
            "both production collectors preserve physical bytes and observed cache148");
    Require(preparation.subject_army_id == scope.subject_army_id &&
                preparation.subject_carmy_id == scope.subject_carmy_id &&
                preparation.province_id == scope.province_id &&
                preparation.target_persistent_ids_complete == scope.target_persistent_ids_complete,
            "same-query target preparation carries the actual subject/province/coverage");
    Require(preparation.persistent_regiments.size() == scope.persistent_regiments.size(),
            "preparation enumerates unique actual B physical IDs");
    for (std::size_t index = 0; index < scope.persistent_regiments.size(); ++index) {
      Require(scope.persistent_regiments[index].persistent_regiment_id == kTargetRegi &&
                  preparation.persistent_regiments[index].persistent_regiment_id == kTargetRegi,
              "actual target union and fresh inputs contain no subject-only persistent");
    }
    const auto expected_reads = static_cast<int>(scope.persistent_regiments.size());
    Require(fresh_calls == expected_reads &&
                fixed_calls == (missing_fixed_permission ? 0 : expected_reads),
            "one fresh target read per unique actual ID; empty scope makes no getter calls");
    game::ArmyStrengthSnapshot row{};
    row.available = true; row.army_id = kSubjectArmy;
    row.native_carmy_id_observable = true; row.native_carmy_id = kSubjectCArmy;
    row.regiment_count = 1; row.current_soldiers = 160; row.maximum_soldiers = 200;
    row.current_supply_change_monthly_raw = 700000;
    row.regiment_strengths.emplace();
    game::ArmyRegimentStrengthSnapshot strength{};
    strength.army_regiment_id = kSubjectArRg;
    strength.current_soldiers = 160; strength.maximum_soldiers = 200;
    row.regiment_strengths->push_back(strength);
    row.regiment_replenishment_records_v1.emplace();
    row.regiment_replenishment_records_v1->push_back(subject_records);
    row.current_province_besieging_contributors_v1 = std::move(family);
    row.ordered_besieging_refill_inputs_v1 = std::move(scope);
    row.ordered_besieging_fixed_chunk0_preparation_inputs_v1 = std::move(preparation);
    return row;
  }
};

const game::FixedChunk0PreparationPersistentInputV1 &TargetPreparation(
    const game::ArmyStrengthSnapshot &row) {
  const auto &family = *row.ordered_besieging_fixed_chunk0_preparation_inputs_v1;
  Require(family.persistent_regiments.size() == 1,
          "one actual target preparation row is present");
  return family.persistent_regiments[0];
}
void Text(std::string &out, std::string_view value) {
  out += '"';
  for (const char character : value) {
    if (character == '"' || character == '\\') out += '\\';
    out += character;
  }
  out += '"';
}
void Wire(const std::filesystem::path &directory, const char *name,
          const game::ArmyStrengthSnapshot &row) {
  const auto number = [](auto value) { return std::to_string(value); };
  std::string output = "{\"status\":\"available\",\"army_strengths\":[";
  game::AppendArmyStrengthV1(output, row, number,
      [&number](std::string &out, const std::vector<std::int32_t> &values) {
        out += '[';
        for (std::size_t index = 0; index < values.size(); ++index) {
          if (index != 0) out += ',';
          out += number(values[index]);
        }
        out += ']';
      }, Text);
  output += "],\"native_readiness\":{\"current_strength\":true,\"full_monthly\":false}}\n";
  Require(output.find("\"ordered_besieging_refill_inputs_v1\":") != std::string::npos &&
              output.find("\"ordered_besieging_fixed_chunk0_preparation_inputs_v1\":") != std::string::npos,
          "whole production Strength serializer emits both independent actual B families");
  std::ofstream stream(directory / name, std::ios::binary);
  stream << output;
  Require(stream.good(), "new standalone native preparation wire was written");
}
} // namespace

int main(int argc, char **argv) {
  try {
    Require(argc == 2, "usage: fixture output_directory");
    const std::filesystem::path directory{argv[1]};
    std::filesystem::create_directories(directory);
    Fixture fixture;
    auto row = fixture.Capture();
    const auto &scope = *row.ordered_besieging_refill_inputs_v1;
    const auto &preparation = TargetPreparation(row);
    Require(scope.status == "available" && scope.target_persistent_ids_complete &&
                scope.refresh_membership_ready && scope.target_army_regiment_ids.size() == 1 &&
                scope.target_army_regiment_ids[0] == kTargetArRg &&
                scope.persistent_regiments.size() == 1 &&
                scope.persistent_regiments[0].chunks.size() == 7 &&
                scope.persistent_regiments[0].prepared_fraction_raw == 0 &&
                scope.persistent_occurrences.size() == 2 &&
                scope.persistent_occurrences[0].stored_index == 1 &&
                scope.persistent_occurrences[1].stored_index == 3 &&
                scope.refresh_occurrences.size() == 2 &&
                scope.refresh_occurrences[0].regiments.size() == 2,
            "actual outside-subject full-generation target scope preserves manager duplicates");
    Require(preparation.status == game::FixedChunk0PreparationInputStatusV1::available &&
                preparation.containing_guard_138_raw == 0 &&
                preparation.containing_definition_magic_38 == kOrdinaryDefinitionMagic &&
                preparation.native_fixed_chunk0_can_replenish == false &&
                preparation.fresh_fraction_raw == 10000,
            "ordinary branch carries fresh10000 independently of nativefalse and observed148 zero");
    Wire(directory, "fresh-target-outside-subject.json", row);

    // Missing later physical context does not undo the real DATA ID union.
    // Valid fresh0 makes that context unused by the source-defined core branch.
    fresh_fraction = 0;
    Store(fixture.target_regi, 0x120, static_cast<void *>(nullptr));
    row = fixture.Capture();
    Require(row.ordered_besieging_refill_inputs_v1->status == "partial" &&
                row.ordered_besieging_refill_inputs_v1->target_persistent_ids_complete &&
                row.ordered_besieging_fixed_chunk0_preparation_inputs_v1->target_persistent_ids_complete &&
                row.ordered_besieging_fixed_chunk0_preparation_inputs_v1->source_scope_status ==
                    game::FixedChunk0PreparationInputStatusV1::partial &&
                row.ordered_besieging_fixed_chunk0_preparation_inputs_v1->status ==
                    game::FixedChunk0PreparationInputStatusV1::available &&
                TargetPreparation(row).fresh_fraction_raw == 0,
            "complete actual union and valid fresh zero survive missing physical context");
    Wire(directory, "complete-union-partial-context-zero.json", row);
    Store(fixture.target_regi, 0x120, static_cast<void *>(fixture.origin_province.data()));
    fresh_fraction = 10000;

    // A raw DATA -1 is a real incomplete union. The first real DATA row still
    // yields the actual target ID and fresh scalar; no subject substitution.
    Store(fixture.target_data, 0x18, std::int32_t{-1});
    row = fixture.Capture();
    Require(row.ordered_besieging_refill_inputs_v1->status == "partial" &&
                !row.ordered_besieging_refill_inputs_v1->target_persistent_ids_complete &&
                row.ordered_besieging_refill_inputs_v1->persistent_regiments.size() == 1 &&
                !row.ordered_besieging_fixed_chunk0_preparation_inputs_v1->target_persistent_ids_complete &&
                row.ordered_besieging_fixed_chunk0_preparation_inputs_v1->status ==
                    game::FixedChunk0PreparationInputStatusV1::partial &&
                TargetPreparation(row).fresh_fraction_raw == 10000 &&
                row.current_province_besieging_contributors_v1->occurrences[0].regiments[0]
                    .replenishment_records_v1->records[0].available &&
                !row.current_province_besieging_contributors_v1->occurrences[0].regiments[0]
                    .replenishment_records_v1->records[1].available,
            "incomplete actual raw DATA retains its known real row and fresh scalar");
    Wire(directory, "incomplete-target-data-known-row.json", row);
    Store(fixture.target_data, 0x18, kTargetRegi);

    Store(fixture.game_data, 0x2A59C, std::int32_t{0});
    row = fixture.Capture();
    Require(row.ordered_besieging_refill_inputs_v1->status == "available" &&
                row.ordered_besieging_refill_inputs_v1->target_persistent_ids_complete &&
                row.ordered_besieging_refill_inputs_v1->persistent_regiments.empty() &&
                row.ordered_besieging_refill_inputs_v1->refresh_occurrences.empty() &&
                row.ordered_besieging_fixed_chunk0_preparation_inputs_v1->target_persistent_ids_complete &&
                row.ordered_besieging_fixed_chunk0_preparation_inputs_v1->status ==
                    game::FixedChunk0PreparationInputStatusV1::available &&
                row.ordered_besieging_fixed_chunk0_preparation_inputs_v1->persistent_regiments.empty() &&
                fixed_calls == 0 && fresh_calls == 0,
            "complete nonrefresh union is empty and does not invent fresh getter calls");
    Wire(directory, "complete-empty-nonrefresh.json", row);
    Store(fixture.game_data, 0x2A59C, std::int32_t{4});

    Store(fixture.target_regi, 0x138, std::int32_t{1});
    Store(fixture.target_definition, 0x38, kPermissionDefinitionMagic);
    row = fixture.Capture(true);
    Require(row.ordered_besieging_fixed_chunk0_preparation_inputs_v1->target_persistent_ids_complete &&
                TargetPreparation(row).containing_guard_138_raw == 1 &&
                !TargetPreparation(row).native_fixed_chunk0_can_replenish.has_value() &&
                TargetPreparation(row).fresh_fraction_raw == 10000 && fixed_calls == 0 && fresh_calls == 1,
            "missing demanded fixed permission is distinct from false and from a known fresh scalar");
    Wire(directory, "demanded-fixed-permission-missing.json", row);

    fresh_readable = false;
    row = fixture.Capture();
    Require(row.ordered_besieging_fixed_chunk0_preparation_inputs_v1->status ==
                game::FixedChunk0PreparationInputStatusV1::partial &&
                TargetPreparation(row).native_fixed_chunk0_can_replenish == false &&
                !TargetPreparation(row).fresh_fraction_raw.has_value(),
            "known false permission and failed unused fresh getter remain separate source values");
    Wire(directory, "known-false-unused-fresh.json", row);

    fresh_readable = true; fresh_fraction = -123;
    Store(fixture.target_regi, 0x138, std::int32_t{0});
    Store(fixture.target_definition, 0x38, kOrdinaryDefinitionMagic);
    row = fixture.Capture();
    Require(TargetPreparation(row).fresh_fraction_raw == -123 &&
                TargetPreparation(row).status == game::FixedChunk0PreparationInputStatusV1::available,
            "actual target fresh getter preserves signed negative fraction without clamping");
    Wire(directory, "signed-negative-fresh.json", row);
    std::cout << "PASS: seven actual ordered-B target preparation wires; physical/cache148 preserved\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
