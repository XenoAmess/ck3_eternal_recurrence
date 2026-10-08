#include "xar_bridge/ck3_12003_war_occupation.hpp"
#include "xar_bridge/ck3_12003.hpp"

#include <cstring>
#include <limits>

namespace xar::ck3_12003 {
namespace {

template <class T> T Load(const void *object, std::size_t offset) noexcept {
  T value{};
  if (object != nullptr)
    std::memcpy(&value, static_cast<const std::byte *>(object) + offset,
                sizeof value);
  return value;
}

constexpr std::int32_t kMaximumCollection = 1'000'000;
using ReleaseVector = void (*)(void *, void *, std::uint64_t);

bool ValidVector(const WarOccupationPointerVector &value) noexcept {
  return value.count >= 0 && value.capacity >= value.count &&
      value.capacity <= kMaximumCollection &&
      (value.count == 0 || value.data != nullptr);
}

ReleaseVector VectorRelease(void *allocator) noexcept {
  void *vtable = Load<void *>(allocator, 0);
  return vtable != nullptr ? Load<ReleaseVector>(vtable, 0x10) : nullptr;
}

struct OwnedVector {
  WarOccupationPointerVector value{};
  ReleaseVector release = nullptr;
  explicit OwnedVector(void *allocator) noexcept {
    value.allocator = allocator;
    release = VectorRelease(allocator);
  }
  ~OwnedVector() {
    if (value.data != nullptr && release != nullptr)
      release(value.allocator, value.data, 8);
  }
};

void *ResolveCharacter(void **slot, std::int32_t id) noexcept {
  if (id == -1 || slot == nullptr || *slot == nullptr) return nullptr;
  void *objects = Load<void *>(*slot, 0x20);
  const auto capacity = Load<std::int32_t>(*slot, 0x2C);
  const auto index = static_cast<std::uint32_t>(id) & 0xFFFFFFU;
  if (objects == nullptr || capacity <= 0 ||
      capacity > kMaximumCollection ||
      index >= static_cast<std::uint32_t>(capacity)) return nullptr;
  void *character = Load<void *>(objects, static_cast<std::size_t>(index) * 0x10 + 8);
  return character != nullptr && Load<std::int32_t>(character, 0x18) == id &&
      Load<std::uint32_t>(character, 0x1C) == 0x43686172U ? character : nullptr;
}

std::string_view ParticipantSide(const WarOccupationTargetsBindingsV1 &b,
                                void *war, std::int32_t id) noexcept {
  if (id == -1) return "none";
  const bool attacker = b.world.contains_war_participant(
      static_cast<std::byte *>(war) + 0x20, id);
  const bool defender = b.world.contains_war_participant(
      static_cast<std::byte *>(war) + 0x80, id);
  if (attacker && defender) return "unavailable";
  return attacker ? "attacker" : defender ? "defender" : "outside_war";
}

bool ValidateParticipants(const WarOccupationTargetsBindingsV1 &b,
                          const WarOccupationPointerVector &participants) noexcept {
  if (!ValidVector(participants)) return false;
  for (std::int32_t index = 0; index < participants.count; ++index) {
    void *participant = participants.data[index];
    if (participant == nullptr || ResolveCharacter(b.character_storage_slot,
        Load<std::int32_t>(participant, 0x08)) == nullptr) return false;
  }
  return true;
}

} // namespace

WarOccupationTargetsBindingsV1 BindWarOccupationTargetsImageV1(
    std::uintptr_t image_base, std::string_view sha) noexcept {
  WarOccupationTargetsBindingsV1 b{};
  if (image_base == 0 || sha != kExecutableSha256) return b;
  b.enabled = true;
  // Existing .2 world/province bindings are reviewed unchanged in this exact .3
  // build; new collector calls are admitted only by the actual .3 SHA above.
  b.world = ck3_12002::BindWorldImage(image_base, ck3_12002::kExecutableSha256);
  b.provinces = ck3_12002::BindProvinceImage(image_base, ck3_12002::kExecutableSha256);
  b.character_storage_slot = reinterpret_cast<void **>(
      image_base + ck3_12002::kCharacterStorageSlotRva);
  b.vector_allocator = reinterpret_cast<void *>(image_base + 0x54DEBB8);
  b.war_occupation_context_fallback_slot = reinterpret_cast<void **>(
      image_base + 0x5D1DE08);
  b.get_war_occupation_context = reinterpret_cast<decltype(b.get_war_occupation_context)>(
      image_base + 0x2C13840);
  b.collect_territory_participants = reinterpret_cast<decltype(b.collect_territory_participants)>(
      image_base + 0x2C0D390);
  b.collect_holding_titles = reinterpret_cast<decltype(b.collect_holding_titles)>(
      image_base + 0x2BA0DC0);
  b.count_holding = reinterpret_cast<decltype(b.count_holding)>(
      image_base + 0x2C0D5B0);
  b.war_participants_are_liege_related = reinterpret_cast<decltype(b.war_participants_are_liege_related)>(
      image_base + 0x24977C0);
  return b;
}

WarOccupationTargetsReadResultV1 ReadWarOccupationTargetsV1(
    const WarOccupationTargetsBindingsV1 &b,
    const game::Snapshot &scope, std::int32_t war_id,
    game::WarOccupationTargetsV1 &out) noexcept {
  using Result = WarOccupationTargetsReadResultV1;
  out = {};
  out.war_id = war_id;
  out.date_raw = scope.date_raw;
  out.actor_character_id = scope.played_character_id;
  auto fail = [&out](std::string_view reason) {
    out.available = false;
    out.collection_complete = false;
    out.unavailable_reason = reason;
    out.rows.clear();
    out.side_counts.clear();
    return Result::unavailable;
  };
  if (!b.enabled || !b.world.enabled || !b.provinces.enabled ||
      b.world.contains_war_participant == nullptr ||
      b.character_storage_slot == nullptr || b.provinces.title_province == nullptr ||
      b.provinces.is_occupied == nullptr || b.get_war_occupation_context == nullptr ||
      b.collect_territory_participants == nullptr ||
      b.collect_holding_titles == nullptr || b.count_holding == nullptr ||
      b.war_participants_are_liege_related == nullptr)
    return fail("war_occupation_bindings_unavailable");
  if (!scope.paused || !scope.map_ready || !scope.has_played_character ||
      !scope.played_character_alive ||
      ResolveCharacter(b.character_storage_slot, scope.played_character_id) == nullptr)
    return fail("paused_player_scope_unavailable");
  void *war = ck3_12002::ResolveWar(b.world, war_id);
  if (war == nullptr) return fail("war_not_found");
  out.player_side = ParticipantSide(b, war, scope.played_character_id);
  if (out.player_side != "attacker" && out.player_side != "defender")
    return fail("player_not_on_one_war_side");
  out.primary_attacker_character_id = Load<std::int32_t>(war, 0x288);
  out.primary_defender_character_id = Load<std::int32_t>(war, 0x28C);
  if (ResolveCharacter(b.character_storage_slot, out.primary_attacker_character_id) == nullptr ||
      ResolveCharacter(b.character_storage_slot, out.primary_defender_character_id) == nullptr)
    return fail("primary_war_leader_unavailable");
  const auto *attacker = reinterpret_cast<const WarOccupationPointerVector *>(
      static_cast<std::byte *>(war) + 0x28);
  const auto *defender = reinterpret_cast<const WarOccupationPointerVector *>(
      static_cast<std::byte *>(war) + 0x88);
  if (!ValidateParticipants(b, *attacker) || !ValidateParticipants(b, *defender))
    return fail("war_participant_graph_unavailable");
  void *context = b.get_war_occupation_context(war_id);
  // Native no-match lookup returns the exact default object; the native score
  // caller passes it to the same collector without a WarID backlink match.
  void *fallback = b.war_occupation_context_fallback_slot == nullptr ? nullptr
      : *b.war_occupation_context_fallback_slot;
  if (context == nullptr ||
      (context != fallback && Load<std::int32_t>(context, 0x28) != war_id))
    return fail("war_occupation_context_unavailable");
  const bool liege_related = b.war_participants_are_liege_related(war);

  try {
    std::vector<game::ArmySnapshot> known_armies;
    auto include_armies = [&known_armies](const auto &armies) {
      for (const auto &army : armies) {
        bool present = false;
        for (const auto &known : known_armies) {
          if (known.army_id == army.army_id) {
            present = true;
            break;
          }
        }
        if (!present) known_armies.push_back(army);
      }
    };
    include_armies(scope.player_armies);
    for (const auto &active_war : scope.active_wars) {
      include_armies(active_war.allied_armies);
      include_armies(active_war.enemy_armies);
    }
    // The native packed occupation getter processes defender territory first
    // (attacker score), then attacker territory (defender score). Keep that
    // order, and keep each native occurrence without sorting or deduplication.
    for (int pass = 0; pass < 2; ++pass) {
      const bool defender_territory = pass == 0;
      const auto *territory = defender_territory ? defender : attacker;
      const auto *opposing = defender_territory ? attacker : defender;
      const auto primary = defender_territory
          ? out.primary_defender_character_id : out.primary_attacker_character_id;
      const std::string_view side = defender_territory ? "defender" : "attacker";
      const bool skip_holder_filter = !(defender_territory && liege_related);
      OwnedVector selected(b.vector_allocator);
      if (selected.release == nullptr) return fail("native_vector_allocator_unavailable");
      b.collect_territory_participants(context, primary, territory, opposing,
                                      &selected.value);
      if (selected.value.allocator != b.vector_allocator ||
          !ValidateParticipants(b, selected.value))
        return fail("selected_territory_participants_unavailable");
      game::WarOccupationSideCountsV1 counts{};
      counts.territory_side = side;
      for (std::int32_t participant_index = 0;
           participant_index < selected.value.count; ++participant_index) {
        const auto character_id = Load<std::int32_t>(
            selected.value.data[participant_index], 0x08);
        void *character = ResolveCharacter(b.character_storage_slot, character_id);
        if (character == nullptr) return fail("territory_character_generation_changed");
        OwnedVector titles(b.vector_allocator);
        b.collect_holding_titles(character, &titles.value);
        if (titles.value.allocator != b.vector_allocator || !ValidVector(titles.value))
          return fail("native_holding_vector_unavailable");
        if (titles.value.count > kMaximumCollection - counts.native_candidate_count)
          return fail("native_holding_count_unavailable");
        counts.native_candidate_count += titles.value.count;
        for (std::int32_t title_index = 0; title_index < titles.value.count; ++title_index) {
          void *title = titles.value.data[title_index];
          if (title == nullptr) return fail("holding_title_pointer_unavailable");
          const auto title_id = Load<std::int32_t>(title, 0x10);
          if (ck3_12002::ResolveObjectiveTitle(b.provinces, title_id) != title)
            return fail("holding_title_generation_unavailable");
          WarOccupationNativeCounts item{};
          b.count_holding(title, opposing, &selected.value, skip_holder_filter, &item);
          if (item.eligible < 0 || item.eligible > 1 || item.occupied < 0 ||
              item.occupied > item.eligible)
            return fail("native_holding_counter_unavailable");
          counts.eligible += item.eligible;
          counts.occupied += item.occupied;
          if (item.eligible == 0) continue;
          game::WarOccupationTargetRowV1 row{};
          row.holding_title_id = title_id;
          row.territory_side = side;
          row.counted_occupied_by_opposing_side = item.occupied == 1;
          row.legal_holder_character_id = Load<std::int32_t>(title, 0x128);
          if (ResolveCharacter(b.character_storage_slot, row.legal_holder_character_id) == nullptr)
            return fail("legal_holding_holder_unavailable");
          void *definition = Load<void *>(title, 0x48);
          if (definition == nullptr || Load<std::int32_t>(definition, 0x64) != 1)
            return fail("holding_title_template_unavailable");
          // Reuse the reviewed native de-jure-parent seam. An unavailable
          // county mapping does not erase an otherwise valid occupation.
          const auto county_title_id = Load<std::int32_t>(title, 0x108);
          if (county_title_id >= 0) {
            void *county = ck3_12002::ResolveObjectiveTitle(
                b.provinces, county_title_id);
            void *county_definition = Load<void *>(county, 0x48);
            if (county_definition != nullptr &&
                Load<std::int32_t>(county_definition, 0x64) == 2)
              row.county_title_id = county_title_id;
          }
          row.province_id = Load<std::int32_t>(definition, 0x88);
          void *province = ck3_12002::ResolveObjectiveProvince(b.provinces, row.province_id);
          if (province == nullptr || b.provinces.title_province(title) != province ||
              Load<std::int32_t>(province, 0x738) != title_id)
            return fail("holding_province_backlink_unavailable");
          const auto rich = ck3_12002::ReadObjectiveProvince(
              b.provinces, row.province_id, known_armies,
              scope.played_character_id, true);
          row.current_besieging_army_selection = rich.current_besieging_army_selection;
          row.fort_level_observable = rich.fort_level_observable;
          row.fort_level = rich.fort_level;
          row.garrison_size_observable = rich.garrison_size_observable;
          row.garrison_size = rich.garrison_size;
          row.besieging_strength_observable = rich.besieging_strength_observable;
          row.besieging_strength = rich.besieging_strength;
          row.siege_observable = rich.siege_observable;
          row.has_active_siege = rich.has_active_siege;
          auto &siege = row.active_siege;
          siege.siege_id = rich.siege_id;
          siege.besieging_army_id = rich.besieging_army_id;
          siege.player_army_besieging = rich.player_army_besieging;
          siege.progress_fraction_raw = rich.siege_progress_fraction.raw;
          siege.current_work_raw = rich.siege_current_work.raw;
          siege.total_work_raw = rich.siege_total_work.raw;
          siege.days_left_observable = rich.siege_days_left_observable;
          siege.days_left = rich.siege_days_left;
          siege.ordinary_daily_progress_observable =
              rich.siege_ordinary_daily_progress_observable;
          siege.ordinary_daily_progress_raw = rich.siege_ordinary_daily_progress.raw;
          siege.eligible_regiment_siege_work_observable =
              rich.siege_eligible_regiment_siege_work_observable;
          siege.eligible_regiment_siege_work_raw =
              rich.siege_eligible_regiment_siege_work.raw;
          siege.highest_eligible_siege_tier_observable =
              rich.siege_highest_eligible_siege_tier_observable;
          siege.highest_eligible_siege_tier =
              rich.siege_highest_eligible_siege_tier;
          siege.province_unit_occurrences_observable =
              rich.siege_province_unit_occurrences_observable;
          siege.province_unit_occurrences = rich.siege_province_unit_occurrences;
          siege.current_phase_length_observable =
              rich.siege_current_phase_length_observable;
          siege.current_phase_length_raw = rich.siege_current_phase_length.raw;
          siege.prepared_phase_length_observable =
              rich.siege_prepared_phase_length_observable;
          siege.prepared_phase_length_raw = rich.siege_prepared_phase_length.raw;
          siege.phase_counter_observable = rich.siege_phase_counter_observable;
          siege.phase_counter = rich.siege_phase_counter;
          siege.can_advance_observable = rich.siege_can_advance_observable;
          siege.can_advance = rich.siege_can_advance;
          siege.phase_event_breach_level_observable =
              rich.siege_phase_event_breach_level_observable;
          siege.phase_event_breach_level = rich.siege_phase_event_breach_level;
          siege.phase_event_starvation_level_observable =
              rich.siege_phase_event_starvation_level_observable;
          siege.phase_event_starvation_level = rich.siege_phase_event_starvation_level;
          siege.phase_event_disease_level_observable =
              rich.siege_phase_event_disease_level_observable;
          siege.phase_event_disease_level = rich.siege_phase_event_disease_level;
          siege.phase_event_desertion_count_observable =
              rich.siege_phase_event_desertion_count_observable;
          siege.phase_event_desertion_count = rich.siege_phase_event_desertion_count;
          siege.phase_event_stalemate_count_observable =
              rich.siege_phase_event_stalemate_count_observable;
          siege.phase_event_stalemate_count = rich.siege_phase_event_stalemate_count;
          siege.prepared_selected_phase_event_enum_observable =
              rich.siege_prepared_selected_phase_event_enum_observable;
          siege.prepared_selected_phase_event_enum =
              rich.siege_prepared_selected_phase_event_enum;
          siege.assault_observable = rich.assault_observable;
          siege.breach_level = rich.breach_level;
          siege.assault_in_progress = rich.assault_in_progress;
          siege.can_start_assault = rich.can_start_assault;
          siege.can_stop_assault = rich.can_stop_assault;
          siege.assault_daily_progress_raw = rich.assault_daily_progress.raw;
          siege.assault_daily_casualties = rich.assault_daily_casualties;
          row.is_occupied = b.provinces.is_occupied(province);
          if (row.is_occupied) {
            row.occupying_character_id = Load<std::int32_t>(province, 0x73C);
            if (ResolveCharacter(b.character_storage_slot, row.occupying_character_id) == nullptr)
              return fail("occupying_character_generation_unavailable");
            row.occupier_side = ParticipantSide(b, war, row.occupying_character_id);
            if (row.occupier_side == "unavailable")
              return fail("occupier_war_side_unavailable");
          } else {
            row.occupier_side = "none";
          }
          row.occupation_observable = true;
          out.rows.push_back(row);
        }
      }
      counts.collection_complete = true;
      out.side_counts.push_back(counts);
    }
    if (ck3_12002::ResolveWar(b.world, war_id) != war ||
        b.get_war_occupation_context(war_id) != context)
      return fail("war_occupation_identity_changed");
    out.available = true;
    out.collection_complete = true;
    out.unavailable_reason = {};
    return Result::available;
  } catch (...) {
    return fail("war_occupation_projection_unavailable");
  }
}

} // namespace xar::ck3_12003
