#include "xar_bridge/campaign_root_context_v1.hpp"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <map>
#include <string>
#include <string_view>
#include <unordered_map>
#include <utility>
#include <vector>

namespace {

template <std::size_t Size>
using Blob = std::array<std::byte, Size>;

template <std::size_t Size, typename Value>
void Put(Blob<Size> &blob, std::size_t offset, const Value &value) {
  if (offset + sizeof(value) > blob.size()) {
    std::abort();
  }
  std::memcpy(blob.data() + offset, &value, sizeof(value));
}

template <std::size_t Size>
void *Address(Blob<Size> &blob, std::size_t offset = 0) noexcept {
  return blob.data() + offset;
}

std::string NonAsciiRule() {
  return std::string("\xC3\xA9", 2) + "_rule";
}

std::string NonAsciiFlag() {
  return std::string("\xE4\xB8\xAD", 3) + "_flag";
}

struct Fixture;
Fixture *g_fixture = nullptr;

struct Fixture {
  static constexpr std::int32_t kPlayerCharacterId = 0x02000001;
  static constexpr std::int32_t kImmediateLiegeId = 0x03000002;
  static constexpr std::int32_t kTopLiegeId = 0x04000003;
  static constexpr std::int32_t kPrimaryTitleId = 0x05000001;
  static constexpr std::int32_t kDirectVassalId = 0x06000004;
  static constexpr std::int32_t kLandlessDirectVassalId = 0x07000005;
  static constexpr std::int32_t kDeadDirectVassalId = 0x08000006;
  static constexpr std::int32_t kDirectVassalTitleId = 0x09000002;
  static constexpr std::int32_t kExternalProvinceHolderId = 0x0A000007;
  static constexpr std::int32_t kExternalProvinceHolderTitleId = 0x0B000003;
  static constexpr std::int32_t kFirstSuccessorId = 0x0C000008;
  static constexpr std::int32_t kSecondSuccessorId = 0x0D000009;
  static constexpr std::int32_t kSecondaryTitleId = 0x0E000004;
  static constexpr std::int32_t kBaronyTitleId = 0x0F000005;
  static constexpr std::int32_t kChancellorTaskId = 0x10000001;
  static constexpr std::int32_t kStewardTaskId = 0x11000002;
  static constexpr std::int32_t kSpymasterTaskId = 0x12000003;

  alignas(void *) Blob<0xA8> game_state{};
  alignas(void *) Blob<0x20> jomini_state{};
  alignas(void *) Blob<0x1F8> players{};
  alignas(void *) Blob<0x1D600> game_data{};
  alignas(void *) Blob<0xE0> player_entry{};
  alignas(void *) Blob<0x08> player_entries{};

  alignas(void *) Blob<0x30> character_storage{};
  alignas(void *) Blob<0xA0> character_slots{};
  alignas(void *) Blob<0x1D0> player_character{};
  alignas(void *) Blob<0x1D0> immediate_liege{};
  alignas(void *) Blob<0x1D0> top_liege{};
  alignas(void *) Blob<0x1D0> direct_vassal{};
  alignas(void *) Blob<0x1D0> landless_direct_vassal{};
  alignas(void *) Blob<0x1D0> dead_direct_vassal{};
  alignas(void *) Blob<0x1D0> external_province_holder{};
  alignas(void *) Blob<0x1D0> first_successor{};
  alignas(void *) Blob<0x1D0> second_successor{};
  alignas(void *) Blob<0x30> character_fallback{};
  alignas(void *) Blob<0x240> player_land_state{};
  alignas(void *) Blob<0x30> active_task_storage{};
  alignas(void *) Blob<0x40> active_task_slots{};
  alignas(void *) Blob<0x58> chancellor_active_task{};
  alignas(void *) Blob<0x58> steward_active_task{};
  alignas(void *) Blob<0x58> spymaster_active_task{};
  alignas(void *) Blob<0x20> active_task_fallback{};
  alignas(void *) Blob<0x58> chancellor_task_type{};
  alignas(void *) Blob<0x58> steward_task_type{};
  alignas(void *) Blob<0x58> spymaster_task_type{};
  alignas(void *) Blob<0x40> chancellor_position_type{};
  alignas(void *) Blob<0x40> steward_position_type{};
  alignas(void *) Blob<0x40> spymaster_position_type{};
  std::array<std::int32_t, 3> active_task_ids{
      kChancellorTaskId, kStewardTaskId, kSpymasterTaskId};

  alignas(void *) Blob<0x30> title_storage{};
  alignas(void *) Blob<0x60> title_slots{};
  alignas(void *) Blob<0x290> primary_title{};
  alignas(void *) Blob<0x290> secondary_title{};
  alignas(void *) Blob<0x290> barony_title{};
  alignas(void *) Blob<0x168> direct_vassal_title{};
  alignas(void *) Blob<0x168> external_province_holder_title{};
  alignas(void *) Blob<0x64> title_template{};
  alignas(void *) Blob<0x64> secondary_title_template{};
  alignas(void *) Blob<0x64> barony_title_template{};
  alignas(void *) Blob<0x30> title_fallback{};
  std::array<std::int32_t, 2> primary_title_successors{
      kFirstSuccessorId, kSecondSuccessorId};
  std::array<std::int32_t, 1> secondary_title_successors{kSecondSuccessorId};
  std::array<std::int32_t, 3> held_title_ids{
      kSecondaryTitleId, kPrimaryTitleId, kBaronyTitleId};

  alignas(void *) Blob<0x18> province{};
  alignas(void *) Blob<0x18> external_province{};
  alignas(void *) Blob<0x18> direct_vassal_province{};
  alignas(void *) Blob<0x18> unowned_province{};
  alignas(void *) Blob<0x48> provinces{};
  alignas(void *) Blob<0x60> player_province_map_node{};
  alignas(void *) Blob<0x60> direct_vassal_province_map_node{};
  alignas(void *) Blob<0xC0> player_province_adjacency_rows{};

  alignas(void *) Blob<0x58> government{};
  alignas(void *) Blob<0x58> government_fallback{};
  std::array<std::int32_t, 4> government_flag_ids{10, 20, 30, 40};
  std::map<std::int32_t, std::string> identifier_names;

  alignas(void *) Blob<0x08> selection_service{};
  std::array<void *, 3> selection_service_vtable{};
  alignas(void *) Blob<0x20> selected_rule_set{};
  std::array<void *, 4> selected_rule_tokens{};
  std::array<Blob<0x40>, 4> rule_tokens{};
  alignas(void *) Blob<0x40> rule_token_fallback{};

  void *game_state_slot = nullptr;
  void *jomini_state_slot = nullptr;
  void *character_storage_slot = nullptr;
  void *character_fallback_slot = nullptr;
  void *title_storage_slot = nullptr;
  void *title_fallback_slot = nullptr;
  void *government_fallback_slot = nullptr;
  void *active_task_storage_slot = nullptr;
  void *active_task_fallback_slot = nullptr;
  void *selection_service_slot = nullptr;
  void *rule_token_fallback_slot = nullptr;

  void *resolved_primary_title = nullptr;
  void *resolved_capital = nullptr;
  void *resolved_immediate_liege = nullptr;
  void *resolved_top_liege = nullptr;
  void *resolved_government = nullptr;
  void *resolved_selected_rule_set = nullptr;

  xar::game::CampaignRootFrameV1 frame{};
  bool main_thread = true;
  bool change_frame_on_second_capture = false;
  bool monthly_income_available = true;
  std::int64_t monthly_income_raw = 570'772;
  std::uint32_t monthly_income_calls = 0;
  bool health_available = true;
  std::int64_t health_raw = 275'000;
  std::uint32_t health_calls = 0;
  bool domain_available = true;
  bool title_province_available = true;
  std::int32_t domain_size = 6;
  std::int32_t domain_limit = 7;
  std::uint32_t domain_size_calls = 0;
  std::uint32_t domain_limit_calls = 0;
  bool council_value_progress_available = true;
  bool council_value_progress_changes_between_samples = false;
  std::uint32_t council_value_current_calls = 0;
  std::uint32_t council_value_maximum_calls = 0;
  std::uint32_t capture_calls = 0;
  std::unordered_map<const void *, std::string> native_strings;

  Fixture() {
    game_state_slot = Address(game_state);
    jomini_state_slot = Address(jomini_state);
    character_storage_slot = Address(character_storage);
    character_fallback_slot = Address(character_fallback);
    title_storage_slot = Address(title_storage);
    title_fallback_slot = Address(title_fallback);
    government_fallback_slot = Address(government_fallback);
    active_task_storage_slot = Address(active_task_storage);
    active_task_fallback_slot = Address(active_task_fallback);
    selection_service_slot = Address(selection_service);
    rule_token_fallback_slot = Address(rule_token_fallback);

    resolved_primary_title = Address(primary_title);
    resolved_capital = Address(province);
    resolved_immediate_liege = Address(immediate_liege);
    resolved_top_liege = Address(top_liege);
    resolved_government = Address(government);
    resolved_selected_rule_set = Address(selected_rule_set);

    void *game_data_pointer = Address(game_data);
    Put(game_state, 0xA0, game_data_pointer);
    void *players_pointer = Address(players);
    Put(jomini_state, 0x18, players_pointer);
    const std::int32_t local_player_id = 7;
    Put(players, 0x1F0, local_player_id);
    void *entry = Address(player_entry);
    Put(player_entries, 0, entry);
    Put(game_data, 0x1D4F0 + 0x58, entry = Address(player_entries));
    const std::int32_t player_count = 1;
    Put(game_data, 0x1D4F0 + 0x64, player_count);
    Put(player_entry, 0xB0, kPlayerCharacterId);
    Put(player_entry, 0xD8, local_player_id);

    void *slots = Address(character_slots);
    Put(character_storage, 0x20, slots);
    const std::int32_t character_capacity = 10;
    Put(character_storage, 0x2C, character_capacity);
    void *player_character_pointer = Address(player_character);
    void *immediate_liege_pointer = Address(immediate_liege);
    void *top_liege_pointer = Address(top_liege);
    void *direct_vassal_pointer = Address(direct_vassal);
    void *landless_direct_vassal_pointer = Address(landless_direct_vassal);
    void *dead_direct_vassal_pointer = Address(dead_direct_vassal);
    void *external_province_holder_pointer =
        Address(external_province_holder);
    void *first_successor_pointer = Address(first_successor);
    void *second_successor_pointer = Address(second_successor);
    // A non-null reusable slot from another generation must be skipped. This
    // mirrors the stock exact-build Character storage enumerators and prevents
    // one stale row from making the complete current-generation scan unknown.
    Put(character_slots, 0 * 0x10 + 0x08, immediate_liege_pointer);
    Put(character_slots, 1 * 0x10 + 0x08, player_character_pointer);
    Put(character_slots, 2 * 0x10 + 0x08, immediate_liege_pointer);
    Put(character_slots, 3 * 0x10 + 0x08, top_liege_pointer);
    Put(character_slots, 4 * 0x10 + 0x08, direct_vassal_pointer);
    Put(character_slots, 5 * 0x10 + 0x08, landless_direct_vassal_pointer);
    Put(character_slots, 6 * 0x10 + 0x08, dead_direct_vassal_pointer);
    Put(character_slots, 7 * 0x10 + 0x08,
        external_province_holder_pointer);
    Put(character_slots, 8 * 0x10 + 0x08, first_successor_pointer);
    Put(character_slots, 9 * 0x10 + 0x08, second_successor_pointer);
    Put(player_character, 0x18, kPlayerCharacterId);
    Put(immediate_liege, 0x18, kImmediateLiegeId);
    Put(top_liege, 0x18, kTopLiegeId);
    Put(direct_vassal, 0x18, kDirectVassalId);
    Put(landless_direct_vassal, 0x18, kLandlessDirectVassalId);
    Put(dead_direct_vassal, 0x18, kDeadDirectVassalId);
    Put(external_province_holder, 0x18, kExternalProvinceHolderId);
    Put(first_successor, 0x18, kFirstSuccessorId);
    Put(second_successor, 0x18, kSecondSuccessorId);
    void *no_death_marker = nullptr;
    Put(player_character, 0x1C8, no_death_marker);
    Put(immediate_liege, 0x1C8, no_death_marker);
    Put(top_liege, 0x1C8, no_death_marker);
    Put(direct_vassal, 0x1C8, no_death_marker);
    Put(landless_direct_vassal, 0x1C8, no_death_marker);
    Put(external_province_holder, 0x1C8, no_death_marker);
    Put(first_successor, 0x1C8, no_death_marker);
    Put(second_successor, 0x1C8, no_death_marker);
    void *player_land_state_pointer = Address(player_land_state);
    Put(player_character, 0x1B8, player_land_state_pointer);
    const std::int32_t targeting_faction_count = 2;
    Put(player_land_state, 0x12C, targeting_faction_count);
    void *held_title_data = held_title_ids.data();
    Put(player_land_state, 0x1E0, held_title_data);
    const std::int32_t held_title_count =
        static_cast<std::int32_t>(held_title_ids.size());
    Put(player_land_state, 0x1E8, held_title_count);
    Put(player_land_state, 0x1EC, held_title_count);
    void *active_task_id_data = active_task_ids.data();
    Put(player_land_state, 0x230, active_task_id_data);
    const std::int32_t active_task_count =
        static_cast<std::int32_t>(active_task_ids.size());
    Put(player_land_state, 0x23C, active_task_count);
    void *death_marker = Address(dead_direct_vassal);
    Put(dead_direct_vassal, 0x1C8, death_marker);

    void *active_task_slots_pointer = Address(active_task_slots);
    Put(active_task_storage, 0x20, active_task_slots_pointer);
    const std::int32_t active_task_capacity = 4;
    Put(active_task_storage, 0x2C, active_task_capacity);
    void *chancellor_task_pointer = Address(chancellor_active_task);
    void *steward_task_pointer = Address(steward_active_task);
    void *spymaster_task_pointer = Address(spymaster_active_task);
    Put(active_task_slots, 1 * 0x10 + 0x08, chancellor_task_pointer);
    Put(active_task_slots, 2 * 0x10 + 0x08, steward_task_pointer);
    Put(active_task_slots, 3 * 0x10 + 0x08, spymaster_task_pointer);
    Put(chancellor_active_task, 0x10, kChancellorTaskId);
    Put(steward_active_task, 0x10, kStewardTaskId);
    Put(spymaster_active_task, 0x10, kSpymasterTaskId);
    void *chancellor_task_type_pointer = Address(chancellor_task_type);
    void *steward_task_type_pointer = Address(steward_task_type);
    void *spymaster_task_type_pointer = Address(spymaster_task_type);
    Put(chancellor_active_task, 0x18, chancellor_task_type_pointer);
    Put(steward_active_task, 0x18, steward_task_type_pointer);
    Put(spymaster_active_task, 0x18, spymaster_task_type_pointer);
    const std::int32_t incumbent_id = kDirectVassalId;
    const std::int32_t council_owner_id = kPlayerCharacterId;
    for (auto *task : {&chancellor_active_task, &steward_active_task,
                       &spymaster_active_task}) {
      Put(*task, 0x38, incumbent_id);
      Put(*task, 0x3C, council_owner_id);
    }
    const std::uint8_t not_frozen = 0;
    const std::uint8_t frozen = 1;
    Put(chancellor_active_task, 0x35, not_frozen);
    Put(steward_active_task, 0x35, frozen);
    Put(spymaster_active_task, 0x35, not_frozen);
    const std::uint16_t county_target_tag = 8;
    const std::uint16_t character_target_tag = 4;
    const std::int32_t county_target = 5;
    const std::int32_t character_target = kExternalProvinceHolderId;
    Put(steward_active_task, 0x40, county_target_tag);
    Put(steward_active_task, 0x48, county_target);
    Put(spymaster_active_task, 0x40, character_target_tag);
    Put(spymaster_active_task, 0x48, character_target);
    const std::int64_t percentage_current = 5'000'000;
    Put(spymaster_active_task, 0x20, percentage_current);

    void *chancellor_position_type_pointer = Address(chancellor_position_type);
    void *steward_position_type_pointer = Address(steward_position_type);
    void *spymaster_position_type_pointer = Address(spymaster_position_type);
    Put(chancellor_task_type, 0x38, chancellor_position_type_pointer);
    Put(steward_task_type, 0x38, steward_position_type_pointer);
    Put(spymaster_task_type, 0x38, spymaster_position_type_pointer);
    const std::int32_t general_task = 0;
    const std::int32_t county_task = 1;
    const std::int32_t court_task = 2;
    const std::int32_t infinite_progress = 0;
    const std::int32_t percentage_progress = 1;
    const std::int32_t value_progress = 2;
    Put(chancellor_task_type, 0x40, general_task);
    Put(steward_task_type, 0x40, county_task);
    Put(spymaster_task_type, 0x40, court_task);
    Put(chancellor_task_type, 0x4C, infinite_progress);
    Put(steward_task_type, 0x4C, value_progress);
    Put(spymaster_task_type, 0x4C, percentage_progress);

    slots = Address(title_slots);
    Put(title_storage, 0x20, slots);
    const std::int32_t title_capacity = 6;
    Put(title_storage, 0x2C, title_capacity);
    Put(title_slots, 1 * 0x10 + 0x08, resolved_primary_title);
    void *direct_vassal_title_pointer = Address(direct_vassal_title);
    Put(title_slots, 2 * 0x10 + 0x08, direct_vassal_title_pointer);
    void *external_title_pointer = Address(external_province_holder_title);
    Put(title_slots, 3 * 0x10 + 0x08, external_title_pointer);
    void *secondary_title_pointer = Address(secondary_title);
    void *barony_title_pointer = Address(barony_title);
    Put(title_slots, 4 * 0x10 + 0x08, secondary_title_pointer);
    Put(title_slots, 5 * 0x10 + 0x08, barony_title_pointer);
    Put(primary_title, 0x10, kPrimaryTitleId);
    Put(direct_vassal_title, 0x10, kDirectVassalTitleId);
    Put(external_province_holder_title, 0x10,
        kExternalProvinceHolderTitleId);
    Put(secondary_title, 0x10, kSecondaryTitleId);
    Put(barony_title, 0x10, kBaronyTitleId);
    void *title_template_pointer = Address(title_template);
    Put(primary_title, 0x160, title_template_pointer);
    const std::int32_t player_holder_id = kPlayerCharacterId;
    Put(primary_title, 0x258, player_holder_id);
    void *successor_data = primary_title_successors.data();
    Put(primary_title, 0x278, successor_data);
    const std::int32_t successor_count =
        static_cast<std::int32_t>(primary_title_successors.size());
    Put(primary_title, 0x280, successor_count);
    Put(primary_title, 0x284, successor_count);
    void *secondary_template_pointer = Address(secondary_title_template);
    Put(secondary_title, 0x160, secondary_template_pointer);
    Put(secondary_title, 0x258, player_holder_id);
    void *secondary_successor_data = secondary_title_successors.data();
    Put(secondary_title, 0x278, secondary_successor_data);
    const std::int32_t secondary_successor_count = 1;
    Put(secondary_title, 0x280, secondary_successor_count);
    Put(secondary_title, 0x284, secondary_successor_count);
    void *barony_template_pointer = Address(barony_title_template);
    Put(barony_title, 0x160, barony_template_pointer);
    Put(barony_title, 0x258, player_holder_id);
    void *no_successors = nullptr;
    const std::int32_t no_successor_count = 0;
    Put(barony_title, 0x278, no_successors);
    Put(barony_title, 0x280, no_successor_count);
    Put(barony_title, 0x284, no_successor_count);
    Put(direct_vassal_title, 0x160, title_template_pointer);
    Put(external_province_holder_title, 0x160, title_template_pointer);
    const std::int32_t hegemony_tier = 6;
    Put(title_template, 0x5C, hegemony_tier);
    const std::int32_t county_tier = 2;
    Put(secondary_title_template, 0x5C, county_tier);
    const std::int32_t barony_tier = 1;
    Put(barony_title_template, 0x5C, barony_tier);

    const std::int32_t province_id = 5;
    const std::int32_t external_province_id = 6;
    const std::int32_t direct_vassal_province_id = 7;
    const std::int32_t unowned_province_id = 8;
    Put(province, 0x10, province_id);
    Put(external_province, 0x10, external_province_id);
    Put(direct_vassal_province, 0x10, direct_vassal_province_id);
    Put(unowned_province, 0x10, unowned_province_id);
    void *province_array = Address(provinces);
    Put(game_data, 0x140, province_array);
    const std::int32_t province_count = 9;
    Put(game_data, 0x14C, province_count);
    Put(provinces, province_id * 8, resolved_capital);
    void *external_province_pointer = Address(external_province);
    void *direct_vassal_province_pointer = Address(direct_vassal_province);
    void *unowned_province_pointer = Address(unowned_province);
    Put(provinces, external_province_id * 8, external_province_pointer);
    Put(provinces, direct_vassal_province_id * 8,
        direct_vassal_province_pointer);
    Put(provinces, unowned_province_id * 8, unowned_province_pointer);

    void *player_map_node = Address(player_province_map_node);
    void *direct_vassal_map_node =
        Address(direct_vassal_province_map_node);
    Put(province, 0x08, player_map_node);
    Put(direct_vassal_province, 0x08, direct_vassal_map_node);
    void *adjacency_rows = Address(player_province_adjacency_rows);
    Put(player_province_map_node, 0x50, adjacency_rows);
    const std::int32_t adjacency_count = 4;
    Put(player_province_map_node, 0x5C, adjacency_count);
    void *empty_adjacency_rows = nullptr;
    Put(direct_vassal_province_map_node, 0x50, empty_adjacency_rows);
    const std::int32_t no_adjacencies = 0;
    Put(direct_vassal_province_map_node, 0x5C, no_adjacencies);
    const std::array<std::pair<std::int32_t, std::int32_t>, 4>
        adjacency_targets{{{0, external_province_id},
                           {1, direct_vassal_province_id},
                           {2, unowned_province_id},
                           {3, external_province_id}}};
    for (std::size_t index = 0; index < adjacency_targets.size(); ++index) {
      Put(player_province_adjacency_rows, index * 0x30,
          adjacency_targets[index].first);
      Put(player_province_adjacency_rows, index * 0x30 + 0x04,
          adjacency_targets[index].second);
    }

    native_strings.emplace(Address(government, 0x18),
                           "feudal_government");
    native_strings.emplace(Address(chancellor_task_type, 0x18),
                           "task_foreign_affairs");
    native_strings.emplace(Address(steward_task_type, 0x18),
                           "task_develop_county");
    native_strings.emplace(Address(spymaster_task_type, 0x18),
                           "task_find_secrets");
    native_strings.emplace(Address(chancellor_position_type, 0x18),
                           "councillor_chancellor");
    native_strings.emplace(Address(steward_position_type, 0x18),
                           "councillor_steward");
    native_strings.emplace(Address(spymaster_position_type, 0x18),
                           "councillor_spymaster");
    identifier_names.emplace(10, NonAsciiFlag());
    identifier_names.emplace(20, "a_flag");
    identifier_names.emplace(30, "a_flag");
    identifier_names.emplace(40, std::string("\xC3\xA9", 2) + "_flag");
    for (auto &[identifier, name] : identifier_names) {
      (void)identifier;
      native_strings.emplace(&name, name);
    }
    void *government_flags = government_flag_ids.data();
    Put(government, 0x48, government_flags);
    const std::int32_t flag_count =
        static_cast<std::int32_t>(government_flag_ids.size());
    Put(government, 0x48 + 0x0C, flag_count);

    selection_service_vtable[2] =
        reinterpret_cast<void *>(&ResolveSelectedRuleSet);
    void *vtable = selection_service_vtable.data();
    Put(selection_service, 0, vtable);
    void *rule_array = selected_rule_tokens.data();
    Put(selected_rule_set, 0x08, rule_array);
    const std::int32_t rule_count =
        static_cast<std::int32_t>(selected_rule_tokens.size());
    Put(selected_rule_set, 0x14, rule_count);
    const std::array<std::string, 4> rule_names{
        "z_rule", NonAsciiRule(), "a_rule", "a_rule"};
    for (std::size_t index = 0; index < rule_tokens.size(); ++index) {
      selected_rule_tokens[index] = Address(rule_tokens[index]);
      native_strings.emplace(Address(rule_tokens[index], 0x18),
                             rule_names[index]);
    }

    frame.snapshot_revision = 41;
    frame.date_raw = 12'345;
    frame.paused = true;
    frame.map_ready = true;
    frame.has_played_character = true;
    frame.played_character_alive = true;
    frame.played_character_id = kPlayerCharacterId;
    g_fixture = this;
  }

  static void *ResolveSelectedRuleSet(void *) noexcept {
    return g_fixture == nullptr ? nullptr
                                : g_fixture->resolved_selected_rule_set;
  }
};

void *__fastcall ResolvePrimaryTitle(void *character) noexcept {
  if (g_fixture == nullptr) {
    return nullptr;
  }
  if (character == Address(g_fixture->player_character)) {
    return g_fixture->resolved_primary_title;
  }
  if (character == Address(g_fixture->direct_vassal) ||
      character == Address(g_fixture->dead_direct_vassal)) {
    return Address(g_fixture->direct_vassal_title);
  }
  if (character == Address(g_fixture->external_province_holder)) {
    return Address(g_fixture->external_province_holder_title);
  }
  return nullptr;
}

void *__fastcall ResolveTitleProvince(void *title) noexcept {
  if (g_fixture == nullptr || !g_fixture->title_province_available) {
    return nullptr;
  }
  if (title == Address(g_fixture->primary_title) ||
      title == Address(g_fixture->secondary_title)) {
    return g_fixture->resolved_capital;
  }
  return nullptr;
}

std::int64_t *__fastcall ResolveMonthlyGoldIncome(
    std::int64_t *output, void *character, void *optional_breakdown,
    void *evaluation_context) noexcept {
  if (g_fixture == nullptr || output == nullptr ||
      character != Address(g_fixture->player_character) ||
      optional_breakdown != nullptr || evaluation_context != nullptr ||
      !g_fixture->monthly_income_available) {
    return nullptr;
  }
  ++g_fixture->monthly_income_calls;
  *output = g_fixture->monthly_income_raw;
  return output;
}

std::int64_t *__fastcall ResolveHealth(void *character,
                                       std::int64_t *output) noexcept {
  if (g_fixture == nullptr || output == nullptr ||
      character != Address(g_fixture->player_character) ||
      !g_fixture->health_available) {
    return nullptr;
  }
  ++g_fixture->health_calls;
  *output = g_fixture->health_raw;
  return output;
}

std::int32_t __fastcall ResolveDomainSize(void *character) noexcept {
  if (g_fixture == nullptr ||
      character != Address(g_fixture->player_character) ||
      !g_fixture->domain_available) {
    return -1;
  }
  ++g_fixture->domain_size_calls;
  return g_fixture->domain_size;
}

std::int32_t __fastcall ResolveDomainLimit(void *character) noexcept {
  if (g_fixture == nullptr ||
      character != Address(g_fixture->player_character) ||
      !g_fixture->domain_available) {
    return 0;
  }
  ++g_fixture->domain_limit_calls;
  return g_fixture->domain_limit;
}

std::int64_t *__fastcall ResolveCouncilValueProgressCurrent(
    void *task_type, std::int64_t *output, void *task_scopes) noexcept {
  if (g_fixture == nullptr || output == nullptr ||
      task_type != Address(g_fixture->steward_task_type) ||
      task_scopes != Address(g_fixture->steward_active_task, 0x38) ||
      !g_fixture->council_value_progress_available) {
    return nullptr;
  }
  ++g_fixture->council_value_current_calls;
  *output = 4'200'000 +
            (g_fixture->council_value_progress_changes_between_samples &&
                     g_fixture->council_value_current_calls > 1
                 ? 1
                 : 0);
  return output;
}

std::int64_t *__fastcall ResolveCouncilValueProgressMaximum(
    void *task_type, std::int64_t *output, void *task_scopes) noexcept {
  if (g_fixture == nullptr || output == nullptr ||
      task_type != Address(g_fixture->steward_task_type) ||
      task_scopes != Address(g_fixture->steward_active_task, 0x38) ||
      !g_fixture->council_value_progress_available) {
    return nullptr;
  }
  ++g_fixture->council_value_maximum_calls;
  *output = 10'000'000;
  return output;
}

void *__fastcall ResolveCapital(void *character) noexcept {
  if (g_fixture == nullptr) {
    return nullptr;
  }
  if (character == Address(g_fixture->player_character)) {
    return g_fixture->resolved_capital;
  }
  if (character == Address(g_fixture->direct_vassal)) {
    return Address(g_fixture->direct_vassal_province);
  }
  if (character == Address(g_fixture->external_province_holder)) {
    return Address(g_fixture->external_province);
  }
  return nullptr;
}

void *__fastcall ResolveImmediateLiege(void *character) noexcept {
  if (g_fixture == nullptr) {
    return nullptr;
  }
  if (character == Address(g_fixture->player_character)) {
    return g_fixture->resolved_immediate_liege;
  }
  if (character == Address(g_fixture->direct_vassal) ||
      character == Address(g_fixture->landless_direct_vassal) ||
      character == Address(g_fixture->dead_direct_vassal)) {
    return Address(g_fixture->player_character);
  }
  if (character == Address(g_fixture->external_province_holder)) {
    return character;
  }
  return nullptr;
}

std::int32_t *__fastcall ResolveProvinceHolderCharacterId(
    void *province, std::int32_t *output) noexcept {
  if (g_fixture == nullptr || output == nullptr) {
    return nullptr;
  }
  if (province == Address(g_fixture->province)) {
    *output = Fixture::kPlayerCharacterId;
  } else if (province == Address(g_fixture->external_province)) {
    *output = Fixture::kExternalProvinceHolderId;
  } else if (province == Address(g_fixture->direct_vassal_province)) {
    *output = Fixture::kDirectVassalId;
  } else if (province == Address(g_fixture->unowned_province)) {
    *output = -1;
  } else {
    return nullptr;
  }
  return output;
}

void *__fastcall ResolveTopLiege(void *character) noexcept {
  if (g_fixture == nullptr) {
    return nullptr;
  }
  if (character == Address(g_fixture->player_character) ||
      character == Address(g_fixture->direct_vassal)) {
    return g_fixture->resolved_top_liege;
  }
  if (character == Address(g_fixture->external_province_holder)) {
    return character;
  }
  return nullptr;
}

void *__fastcall ResolveGovernment(void *character) noexcept {
  return g_fixture != nullptr && character == Address(g_fixture->player_character)
             ? g_fixture->resolved_government
             : nullptr;
}

const std::string *__fastcall ResolveIdentifierName(
    std::int32_t identifier) noexcept {
  if (g_fixture == nullptr) {
    return nullptr;
  }
  const auto found = g_fixture->identifier_names.find(identifier);
  return found == g_fixture->identifier_names.end() ? nullptr
                                                     : &found->second;
}

bool CaptureFrame(void *opaque,
                  xar::game::CampaignRootFrameV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  ++fixture.capture_calls;
  output = fixture.frame;
  if (fixture.change_frame_on_second_capture && fixture.capture_calls >= 2) {
    ++output.date_raw;
  }
  return true;
}

bool IsMainThread(void *opaque) noexcept {
  return static_cast<Fixture *>(opaque)->main_thread;
}

bool ReadMemory(void *, const void *address, void *output,
                std::size_t size) noexcept {
  if (address == nullptr || output == nullptr || size == 0) {
    return false;
  }
  std::memcpy(output, address, size);
  return true;
}

bool ReadString(void *opaque, const void *address,
                std::string &output) noexcept {
  const auto &fixture = *static_cast<Fixture *>(opaque);
  const auto found = fixture.native_strings.find(address);
  if (found == fixture.native_strings.end()) {
    output.clear();
    return false;
  }
  output = found->second;
  return true;
}

xar::ck3_11906::CampaignRootNativeEnvironmentV1 Environment(Fixture &fixture) {
  xar::ck3_11906::CampaignRootNativeEnvironmentV1 environment{};
  environment.exact_build_admitted = true;
  environment.offline_fixture_function_overrides = true;
  environment.game_state_slot = &fixture.game_state_slot;
  environment.jomini_state_slot = &fixture.jomini_state_slot;
  environment.character_storage_slot = &fixture.character_storage_slot;
  environment.character_fallback_slot = &fixture.character_fallback_slot;
  environment.landed_title_storage_slot = &fixture.title_storage_slot;
  environment.landed_title_fallback_slot = &fixture.title_fallback_slot;
  environment.government_fallback_slot = &fixture.government_fallback_slot;
  environment.active_council_task_storage_slot =
      &fixture.active_task_storage_slot;
  environment.active_council_task_fallback_slot =
      &fixture.active_task_fallback_slot;
  environment.game_rule_selection_service_slot =
      &fixture.selection_service_slot;
  environment.game_rule_token_fallback_slot =
      &fixture.rule_token_fallback_slot;
  environment.monthly_gold_income = &ResolveMonthlyGoldIncome;
  environment.health = &ResolveHealth;
  environment.domain_size = &ResolveDomainSize;
  environment.domain_limit = &ResolveDomainLimit;
  environment.council_value_progress_current =
      &ResolveCouncilValueProgressCurrent;
  environment.council_value_progress_maximum =
      &ResolveCouncilValueProgressMaximum;
  environment.primary_title = &ResolvePrimaryTitle;
  environment.title_province = &ResolveTitleProvince;
  environment.capital_province = &ResolveCapital;
  environment.immediate_liege = &ResolveImmediateLiege;
  environment.top_liege = &ResolveTopLiege;
  environment.government = &ResolveGovernment;
  environment.province_holder_character_id =
      &ResolveProvinceHolderCharacterId;
  environment.script_identifier_name = &ResolveIdentifierName;
  return environment;
}

xar::ck3_11906::CampaignRootAccessV1 Access(Fixture &fixture) {
  xar::ck3_11906::CampaignRootAccessV1 access{};
  access.context = &fixture;
  access.capture_frame = &CaptureFrame;
  access.is_main_thread = &IsMainThread;
  access.read_memory = &ReadMemory;
  access.read_string = &ReadString;
  return access;
}

bool AllReadiness(const xar::game::CampaignRootReadinessV1 &value,
                  bool expected) {
  return value.player_identity_ready == expected &&
         value.player_monthly_gold_income_ready == expected &&
         value.player_health_ready == expected &&
         value.player_domain_ready == expected &&
         value.player_targeting_factions_ready == expected &&
         value.primary_title_ready == expected &&
         value.primary_title_succession_ready == expected &&
         value.held_title_partition_ready == expected &&
         value.capital_ready == expected &&
         value.lieges_ready == expected &&
         value.direct_landed_vassals_ready == expected &&
         value.adjacent_external_province_holders_ready == expected &&
         value.related_character_contexts_ready == expected &&
         value.government_ready == expected &&
         value.selected_game_rule_tokens_ready == expected &&
         value.same_frame_ready == expected && value.ready == expected;
}

bool ClearedUnavailable(const xar::game::CampaignRootContextV1 &value,
                        std::string_view reason) {
  return value.status ==
             xar::game::CampaignRootContextStatusV1::unavailable &&
         value.snapshot_revision == 41 && value.date_raw == 12'345 &&
         !value.local_player_id && !value.player_character_id &&
         !value.player_character_alive && !value.primary_title &&
         !value.player_monthly_gold_income &&
         !value.player_health &&
         !value.player_domain_size && !value.player_domain_limit &&
         !value.player_targeting_faction_count &&
         !value.council &&
         value.primary_title_succession_character_ids.empty() &&
         value.held_title_partition.empty() &&
          !value.capital_province_id && !value.immediate_liege_character_id &&
         !value.top_liege_character_id && !value.independent &&
         value.direct_landed_vassal_character_ids.empty() &&
         value.adjacent_external_province_holder_character_ids.empty() &&
         value.related_character_contexts.empty() &&
         !value.government && value.selected_game_rule_tokens.empty() &&
         value.native_selected_game_rule_token_count == 0 &&
         AllReadiness(value.readiness, false) &&
         value.unavailable_reason == reason;
}

bool TestAvailableAndSerializer() {
  Fixture fixture;
  const auto environment = Environment(fixture);
  const auto access = Access(fixture);
  const xar::ck3_11906::CampaignRootContextRequestV1 request{41};
  xar::game::CampaignRootContextV1 result{};
  const std::vector<xar::game::CampaignRootRelatedCharacterV1>
      expected_related{
          {Fixture::kDirectVassalId,
           "direct_landed_vassal",
           {Fixture::kDirectVassalTitleId, 6, "hegemony"},
           7,
           Fixture::kPlayerCharacterId,
           Fixture::kTopLiegeId,
           false},
          {Fixture::kExternalProvinceHolderId,
           "adjacent_external_province_holder",
           {Fixture::kExternalProvinceHolderTitleId, 6, "hegemony"},
           6,
           std::nullopt,
           Fixture::kExternalProvinceHolderId,
           true}};
  const std::vector<xar::game::CampaignRootHeldTitleSuccessionV1>
      expected_partition{
          {{Fixture::kPrimaryTitleId, 6, "hegemony"},
           Fixture::kFirstSuccessorId,
           std::nullopt,
           true},
          {{Fixture::kSecondaryTitleId, 2, "county"},
           Fixture::kSecondSuccessorId,
           5,
           false}};
  if (xar::ck3_11906::ReadCampaignRootContextV1(
          environment, access, request, result) !=
          xar::game::ReadCampaignRootContextResultV1::available ||
      result.status != xar::game::CampaignRootContextStatusV1::available ||
      result.snapshot_revision != 41 || result.date_raw != 12'345 ||
      result.local_player_id != 7 ||
      result.player_character_id != Fixture::kPlayerCharacterId ||
      result.player_character_alive != true ||
      result.player_monthly_gold_income !=
          xar::game::FixedPointValue{570'772, 100'000} ||
      fixture.monthly_income_calls != 2 ||
      result.player_health != xar::game::FixedPointValue{275'000, 100'000} ||
      fixture.health_calls != 2 || result.player_domain_size != 6 ||
      result.player_domain_limit != 7 || fixture.domain_size_calls != 2 ||
      fixture.domain_limit_calls != 2 ||
      result.player_targeting_faction_count != 2 || !result.council ||
      result.council->status !=
          xar::game::CampaignRootCouncilStatusV1::available ||
      result.council->owner_character_id != Fixture::kPlayerCharacterId ||
      result.council->coverage_key !=
          "standard_landed_non_nomadic_core_v1" ||
      result.council->auxiliary_vacancies_complete ||
      result.council->positions.size() != 5 ||
      fixture.council_value_current_calls != 2 ||
      fixture.council_value_maximum_calls != 2 ||
      !result.readiness.council_ready || !result.primary_title ||
      result.primary_title->title_id != Fixture::kPrimaryTitleId ||
      result.primary_title->tier_raw != 6 ||
      result.primary_title->tier_key != "hegemony" ||
      result.primary_title_succession_character_ids !=
          std::vector<std::int32_t>{Fixture::kFirstSuccessorId,
                                    Fixture::kSecondSuccessorId} ||
      result.held_title_partition != expected_partition ||
      result.capital_province_id != 5 ||
      result.immediate_liege_character_id != Fixture::kImmediateLiegeId ||
      result.top_liege_character_id != Fixture::kTopLiegeId ||
      result.independent != false || !result.government ||
      result.direct_landed_vassal_character_ids !=
          std::vector<std::int32_t>{Fixture::kDirectVassalId} ||
      result.adjacent_external_province_holder_character_ids !=
          std::vector<std::int32_t>{Fixture::kExternalProvinceHolderId} ||
      result.related_character_contexts != expected_related ||
      result.government->key != "feudal_government" ||
      result.government->native_flag_count != 4 ||
      result.native_selected_game_rule_token_count != 4 ||
      !AllReadiness(result.readiness, true) ||
      !result.unavailable_reason.empty()) {
    return false;
  }
  const std::vector<std::string> expected_flags{
      "a_flag", "a_flag", std::string("\xC3\xA9", 2) + "_flag",
      NonAsciiFlag()};
  const std::vector<std::string> expected_rules{
      "a_rule", "a_rule", "z_rule", NonAsciiRule()};
  if (result.government->flags != expected_flags ||
      result.selected_game_rule_tokens != expected_rules) {
    return false;
  }
  const auto &council = result.council->positions;
  if (council[0].position_key != "councillor_chancellor" ||
      council[0].incumbent_character_id != Fixture::kDirectVassalId ||
      council[0].task_key != "task_foreign_affairs" ||
      council[0].task_type !=
          xar::game::CampaignRootCouncilTaskTypeV1::general ||
      council[0].target.has_value() || council[0].frozen != false ||
      !council[0].progress ||
      council[0].progress->kind !=
          xar::game::CampaignRootCouncilProgressKindV1::infinite ||
      council[0].progress->current.has_value() ||
      council[0].progress->maximum.has_value() ||
      council[1].position_key != "councillor_court_chaplain" ||
      council[1].incumbent_character_id.has_value() ||
      council[2].position_key != "councillor_marshal" ||
      council[2].incumbent_character_id.has_value() ||
      council[3].position_key != "councillor_spymaster" ||
      !council[3].target ||
      council[3].target->character_id !=
          Fixture::kExternalProvinceHolderId ||
      !council[3].progress ||
      council[3].progress->kind !=
          xar::game::CampaignRootCouncilProgressKindV1::percentage ||
      council[3].progress->current !=
          xar::game::FixedPointValue{5'000'000, 100'000} ||
      council[3].progress->maximum !=
          xar::game::FixedPointValue{10'000'000, 100'000} ||
      council[4].position_key != "councillor_steward" ||
      !council[4].target || council[4].target->province_id != 5 ||
      council[4].frozen != true || !council[4].progress ||
      council[4].progress->kind !=
          xar::game::CampaignRootCouncilProgressKindV1::value ||
      council[4].progress->current !=
          xar::game::FixedPointValue{4'200'000, 100'000} ||
      council[4].progress->maximum !=
          xar::game::FixedPointValue{10'000'000, 100'000}) {
    return false;
  }

  const auto json =
      xar::ck3_11906::SerializeCampaignRootContextV1(result);
  const std::string expected =
      "{\"schema_version\":1,\"status\":\"available\","
      "\"snapshot_revision\":41,\"date_raw\":12345,"
      "\"local_player_id\":7,\"player_character_id\":33554433,"
      "\"player_character_alive\":true,"
      "\"player_monthly_gold_income\":{\"raw\":570772,"
      "\"scale\":100000},\"player_health\":{\"raw\":275000,"
      "\"scale\":100000},\"player_domain_size\":6,"
      "\"player_domain_limit\":7,"
      "\"player_targeting_faction_count\":2,\"council\":{"
      "\"status\":\"available\",\"coverage_key\":"
      "\"standard_landed_non_nomadic_core_v1\","
      "\"owner_character_id\":33554433,\"positions\":[{"
      "\"position_key\":\"councillor_chancellor\","
      "\"incumbent_character_id\":100663300,\"task_key\":"
      "\"task_foreign_affairs\",\"task_type\":\"general\","
      "\"target\":null,\"frozen\":false,\"progress\":{"
      "\"kind\":\"infinite\",\"current\":null,\"maximum\":null}},{"
      "\"position_key\":\"councillor_court_chaplain\","
      "\"incumbent_character_id\":null,\"task_key\":null,"
      "\"task_type\":null,\"target\":null,\"frozen\":null,"
      "\"progress\":null},{\"position_key\":\"councillor_marshal\","
      "\"incumbent_character_id\":null,\"task_key\":null,"
      "\"task_type\":null,\"target\":null,\"frozen\":null,"
      "\"progress\":null},{\"position_key\":\"councillor_spymaster\","
      "\"incumbent_character_id\":100663300,\"task_key\":"
      "\"task_find_secrets\",\"task_type\":\"court\",\"target\":{"
      "\"kind\":\"character\",\"character_id\":167772167},"
      "\"frozen\":false,\"progress\":{\"kind\":\"percentage\","
      "\"current\":{\"raw\":5000000,\"scale\":100000},"
      "\"maximum\":{\"raw\":10000000,\"scale\":100000}}},{"
      "\"position_key\":\"councillor_steward\","
      "\"incumbent_character_id\":100663300,\"task_key\":"
      "\"task_develop_county\",\"task_type\":\"county\",\"target\":{"
      "\"kind\":\"province\",\"province_id\":5},\"frozen\":true,"
      "\"progress\":{\"kind\":\"value\",\"current\":{"
      "\"raw\":4200000,\"scale\":100000},\"maximum\":{"
      "\"raw\":10000000,\"scale\":100000}}}],"
      "\"auxiliary_vacancies_complete\":false,"
      "\"unavailable_reason\":null},\"primary_title\":{"
      "\"title_id\":83886081,\"tier_raw\":6,"
      "\"tier_key\":\"hegemony\"},"
      "\"primary_title_succession_character_ids\":[201326600,218103817],"
      "\"held_title_partition\":[{\"title\":{\"title_id\":83886081,"
      "\"tier_raw\":6,\"tier_key\":\"hegemony\"},"
      "\"first_heir_character_id\":201326600,"
      "\"capital_province_id\":null,\"primary\":true},{"
      "\"title\":{\"title_id\":234881028,\"tier_raw\":2,"
      "\"tier_key\":\"county\"},\"first_heir_character_id\":"
      "218103817,\"capital_province_id\":5,\"primary\":false}],"
      "\"capital_province_id\":5,"
      "\"immediate_liege_character_id\":50331650,"
      "\"top_liege_character_id\":67108867,\"independent\":false,"
      "\"direct_landed_vassal_character_ids\":[100663300],"
      "\"adjacent_external_province_holder_character_ids\":[167772167],"
      "\"related_character_contexts\":[{\"character_id\":100663300,"
      "\"relationship_role\":\"direct_landed_vassal\","
      "\"primary_title\":{\"title_id\":150994946,\"tier_raw\":6,"
      "\"tier_key\":\"hegemony\"},\"capital_province_id\":7,"
      "\"immediate_liege_character_id\":33554433,"
      "\"top_liege_character_id\":67108867,\"independent\":false},{"
      "\"character_id\":167772167,\"relationship_role\":"
      "\"adjacent_external_province_holder\",\"primary_title\":{"
      "\"title_id\":184549379,\"tier_raw\":6,"
      "\"tier_key\":\"hegemony\"},\"capital_province_id\":6,"
      "\"immediate_liege_character_id\":null,"
      "\"top_liege_character_id\":167772167,\"independent\":true}],"
      "\"government\":{\"key\":\"feudal_government\",\"flags\":["
      "\"a_flag\",\"a_flag\",\"" +
      std::string("\xC3\xA9", 2) + "_flag\",\"" + NonAsciiFlag() +
      "\"],\"native_flag_count\":4},"
      "\"selected_game_rule_tokens\":[\"a_rule\",\"a_rule\","
      "\"z_rule\",\"" + NonAsciiRule() +
      "\"],\"native_selected_game_rule_token_count\":4,"
      "\"readiness\":{\"player_identity_ready\":true,"
      "\"player_monthly_gold_income_ready\":true,"
      "\"player_health_ready\":true,"
      "\"player_domain_ready\":true,"
      "\"player_targeting_factions_ready\":true,"
      "\"primary_title_ready\":true,"
      "\"primary_title_succession_ready\":true,"
      "\"held_title_partition_ready\":true,"
      "\"council_ready\":true,"
      "\"capital_ready\":true,"
      "\"lieges_ready\":true,\"direct_landed_vassals_ready\":true,"
      "\"adjacent_external_province_holders_ready\":true,"
      "\"related_character_contexts_ready\":true,"
      "\"government_ready\":true,"
      "\"selected_game_rule_tokens_ready\":true,"
      "\"same_frame_ready\":true,\"ready\":true},"
      "\"unavailable_reason\":null,\"provenance\":{"
      "\"game_version\":\"1.19.0.6\",\"executable_sha256\":"
      "\"2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86\","
      "\"backend_id\":\"ck3-1.19.0.6-native-campaign-root-context-v1\","
      "\"monthly_gold_income_rva\":\"0x28DBE90\","
      "\"character_health_rva\":\"0x2619AD0\","
      "\"domain_size_rva\":\"0x260BA50\","
      "\"domain_limit_rva\":\"0x260BA20\","
      "\"has_targeting_faction_trigger_rva\":\"0x283FAE0\","
      "\"council_position_lookup_rva\":\"0x23F7800\","
      "\"council_active_task_ids_enumerator_rva\":\"0x2666CD0\","
      "\"council_active_task_storage_slot_rva\":\"0x570C778\","
      "\"council_value_progress_current_rva\":\"0x2D650A0\","
      "\"council_value_progress_maximum_rva\":\"0x2D65390\","
      "\"primary_title_rva\":\"0x25F3350\","
      "\"held_title_ids_offset\":\"0x1E0\","
      "\"title_province_rva\":\"0x20B6B20\","
      "\"capital_province_rva\":\"0x2606760\","
      "\"immediate_liege_rva\":\"0x2613480\","
      "\"top_liege_rva\":\"0x2613600\","
      "\"government_rva\":\"0x26165B0\","
      "\"province_holder_character_id_rva\":\"0x220C3F0\","
      "\"selected_game_rule_service_slot_rva\":\"0x5754B48\"}}";
  if (json != expected) {
    return false;
  }
  auto unsorted = result;
  std::swap(unsorted.selected_game_rule_tokens.front(),
            unsorted.selected_game_rule_tokens.back());
  if (!xar::ck3_11906::SerializeCampaignRootContextV1(unsorted).empty()) {
    return false;
  }

  constexpr std::array<std::string_view, 5> tier_keys{
      "county", "duchy", "kingdom", "empire", "hegemony"};
  for (std::int32_t tier = 2; tier <= 6; ++tier) {
    Put(fixture.title_template, 0x5C, tier);
    fixture.capture_calls = 0;
    result = {};
    if (xar::ck3_11906::ReadCampaignRootContextV1(
            environment, access, request, result) !=
            xar::game::ReadCampaignRootContextResultV1::available ||
        !result.primary_title || result.primary_title->tier_raw != tier ||
        result.primary_title->tier_key !=
            tier_keys[static_cast<std::size_t>(tier - 2)]) {
      return false;
    }
  }
  return true;
}

bool TestLegitimateAbsenceAndGovernmentPointerSlot() {
  Fixture fixture;
  fixture.resolved_primary_title = Address(fixture.title_fallback);
  const std::int32_t no_held_titles = 0;
  Put(fixture.player_land_state, 0x1EC, no_held_titles);
  fixture.resolved_capital = nullptr;
  fixture.resolved_immediate_liege = Address(fixture.character_fallback);
  fixture.resolved_top_liege = Address(fixture.player_character);
  fixture.resolved_government = Address(fixture.government_fallback);
  const auto environment = Environment(fixture);
  const auto access = Access(fixture);
  const xar::ck3_11906::CampaignRootContextRequestV1 request{41};
  xar::game::CampaignRootContextV1 result{};
  return xar::ck3_11906::ReadCampaignRootContextV1(
             environment, access, request, result) ==
             xar::game::ReadCampaignRootContextResultV1::available &&
         !result.primary_title && !result.capital_province_id &&
         result.primary_title_succession_character_ids.empty() &&
         result.held_title_partition.empty() &&
         !result.immediate_liege_character_id &&
         result.top_liege_character_id == Fixture::kPlayerCharacterId &&
         result.independent == true && !result.government &&
         result.council.has_value() &&
         result.council->status ==
             xar::game::CampaignRootCouncilStatusV1::unavailable &&
         !result.readiness.council_ready &&
         AllReadiness(result.readiness, true) &&
         !xar::ck3_11906::SerializeCampaignRootContextV1(result).empty();
}

bool TestTypedUnavailableClearsPartialObservation() {
  Fixture fixture;
  fixture.frame.played_character_id = Fixture::kPlayerCharacterId +
                                      0x01000000;
  const auto environment = Environment(fixture);
  const auto access = Access(fixture);
  const xar::ck3_11906::CampaignRootContextRequestV1 request{41};
  xar::game::CampaignRootContextV1 result{};
  if (xar::ck3_11906::ReadCampaignRootContextV1(
          environment, access, request, result) !=
          xar::game::ReadCampaignRootContextResultV1::unavailable ||
      !ClearedUnavailable(result,
                          "player_character_generation_mismatch")) {
    return false;
  }
  const auto json =
      xar::ck3_11906::SerializeCampaignRootContextV1(result);
  return !json.empty() &&
         json.find("\"local_player_id\":null") != std::string::npos &&
         json.find("\"selected_game_rule_tokens\":[]") !=
             std::string::npos &&
         json.find("\"unavailable_reason\":"
                   "\"player_character_generation_mismatch\"") !=
             std::string::npos;
}

bool TestMalformedSuccessionIsTypedUnavailable() {
  Fixture fixture;
  fixture.primary_title_successors[1] = 0x0E00000A;
  const auto environment = Environment(fixture);
  const auto access = Access(fixture);
  const xar::ck3_11906::CampaignRootContextRequestV1 request{41};
  xar::game::CampaignRootContextV1 result{};
  return xar::ck3_11906::ReadCampaignRootContextV1(
             environment, access, request, result) ==
             xar::game::ReadCampaignRootContextResultV1::unavailable &&
         ClearedUnavailable(result,
                            "primary_title_succession_unavailable");
}

bool TestMalformedHeldTitlePartitionIsTypedUnavailable() {
  Fixture fixture;
  Put(fixture.secondary_title, 0x258, Fixture::kTopLiegeId);
  const auto environment = Environment(fixture);
  const auto access = Access(fixture);
  const xar::ck3_11906::CampaignRootContextRequestV1 request{41};
  xar::game::CampaignRootContextV1 result{};
  if (xar::ck3_11906::ReadCampaignRootContextV1(
          environment, access, request, result) !=
          xar::game::ReadCampaignRootContextResultV1::unavailable ||
      !ClearedUnavailable(result, "held_title_partition_unavailable")) {
    return false;
  }

  Fixture missing_county_capital;
  missing_county_capital.title_province_available = false;
  const auto missing_environment = Environment(missing_county_capital);
  const auto missing_access = Access(missing_county_capital);
  result = {};
  return xar::ck3_11906::ReadCampaignRootContextV1(
             missing_environment, missing_access, request, result) ==
             xar::game::ReadCampaignRootContextResultV1::unavailable &&
         ClearedUnavailable(result, "held_title_partition_unavailable");
}

bool TestMonthlyIncomeFailureIsTypedUnavailable() {
  Fixture fixture;
  fixture.monthly_income_available = false;
  const auto environment = Environment(fixture);
  const auto access = Access(fixture);
  const xar::ck3_11906::CampaignRootContextRequestV1 request{41};
  xar::game::CampaignRootContextV1 result{};
  return xar::ck3_11906::ReadCampaignRootContextV1(
             environment, access, request, result) ==
             xar::game::ReadCampaignRootContextResultV1::unavailable &&
         ClearedUnavailable(
             result, "player_monthly_gold_income_unavailable");
}

bool TestHealthFailureIsTypedUnavailable() {
  Fixture fixture;
  fixture.health_available = false;
  const auto environment = Environment(fixture);
  const auto access = Access(fixture);
  const xar::ck3_11906::CampaignRootContextRequestV1 request{41};
  xar::game::CampaignRootContextV1 result{};
  return xar::ck3_11906::ReadCampaignRootContextV1(
             environment, access, request, result) ==
             xar::game::ReadCampaignRootContextResultV1::unavailable &&
         ClearedUnavailable(result, "player_health_unavailable");
}

bool TestDomainFailureIsTypedUnavailable() {
  Fixture fixture;
  fixture.domain_available = false;
  const auto environment = Environment(fixture);
  const auto access = Access(fixture);
  const xar::ck3_11906::CampaignRootContextRequestV1 request{41};
  xar::game::CampaignRootContextV1 result{};
  return xar::ck3_11906::ReadCampaignRootContextV1(
             environment, access, request, result) ==
             xar::game::ReadCampaignRootContextResultV1::unavailable &&
         ClearedUnavailable(result, "player_domain_unavailable");
}

bool TestCouncilDynamicPositionAndFailureBoundaries() {
  {
    Fixture fixture;
    fixture.native_strings[Address(fixture.chancellor_position_type, 0x18)] =
        "modded_councillor";
    const auto environment = Environment(fixture);
    const auto access = Access(fixture);
    const xar::ck3_11906::CampaignRootContextRequestV1 request{41};
    xar::game::CampaignRootContextV1 result{};
    if (xar::ck3_11906::ReadCampaignRootContextV1(
            environment, access, request, result) !=
            xar::game::ReadCampaignRootContextResultV1::available ||
        !result.council || result.council->positions.size() != 6 ||
        std::none_of(result.council->positions.begin(),
                     result.council->positions.end(),
                     [](const auto &position) {
                       return position.position_key == "modded_councillor" &&
                              position.incumbent_character_id.has_value();
                     }) ||
        std::none_of(result.council->positions.begin(),
                     result.council->positions.end(),
                     [](const auto &position) {
                       return position.position_key ==
                                  "councillor_chancellor" &&
                              !position.incumbent_character_id.has_value();
                     })) {
      return false;
    }
  }
  for (const int failure_case : {0, 1}) {
    Fixture fixture;
    if (failure_case == 0) {
      const std::uint16_t wrong_target_tag = 4;
      Put(fixture.steward_active_task, 0x40, wrong_target_tag);
    } else {
      fixture.active_task_ids[0] += 0x01000000;
    }
    const auto environment = Environment(fixture);
    const auto access = Access(fixture);
    const xar::ck3_11906::CampaignRootContextRequestV1 request{41};
    xar::game::CampaignRootContextV1 result{};
    if (xar::ck3_11906::ReadCampaignRootContextV1(
            environment, access, request, result) !=
            xar::game::ReadCampaignRootContextResultV1::unavailable ||
        !ClearedUnavailable(result, "council_unavailable")) {
      return false;
    }
  }
  Fixture drift;
  drift.council_value_progress_changes_between_samples = true;
  const auto environment = Environment(drift);
  const auto access = Access(drift);
  const xar::ck3_11906::CampaignRootContextRequestV1 request{41};
  xar::game::CampaignRootContextV1 result{};
  return xar::ck3_11906::ReadCampaignRootContextV1(
             environment, access, request, result) ==
             xar::game::ReadCampaignRootContextResultV1::unavailable &&
         ClearedUnavailable(result, "state_changed");
}

bool TestStoredVacantCouncilTasksPreserveRoot() {
  Fixture fixture;
  const std::int32_t absent_incumbent = -1;
  const std::int32_t zero_incumbent = 0;
  Put(fixture.steward_active_task, 0x38, absent_incumbent);
  Put(fixture.spymaster_active_task, 0x38, zero_incumbent);
  fixture.native_strings[Address(fixture.spymaster_position_type, 0x18)] =
      "councillor_spouse";
  const auto environment = Environment(fixture);
  const auto access = Access(fixture);
  const xar::ck3_11906::CampaignRootContextRequestV1 request{41};
  xar::game::CampaignRootContextV1 result{};
  if (xar::ck3_11906::ReadCampaignRootContextV1(
          environment, access, request, result) !=
          xar::game::ReadCampaignRootContextResultV1::available ||
      !result.council || result.council->positions.size() != 6 ||
      !AllReadiness(result.readiness, true)) {
    return false;
  }
  const auto vacant = [&result](std::string_view key) {
    return std::any_of(
        result.council->positions.begin(), result.council->positions.end(),
        [key](const auto &position) {
          return position.position_key == key &&
                 !position.incumbent_character_id.has_value() &&
                 !position.task_key.has_value() &&
                 !position.task_type.has_value() &&
                 !position.target.has_value() &&
                 !position.frozen.has_value() &&
                 !position.progress.has_value();
        });
  };
  if (!vacant("councillor_steward") || !vacant("councillor_spouse") ||
      xar::ck3_11906::SerializeCampaignRootContextV1(result).empty()) {
    return false;
  }
  Fixture malformed;
  const std::int32_t malformed_incumbent = -2;
  Put(malformed.steward_active_task, 0x38, malformed_incumbent);
  const auto malformed_environment = Environment(malformed);
  const auto malformed_access = Access(malformed);
  xar::game::CampaignRootContextV1 malformed_result{};
  if (xar::ck3_11906::ReadCampaignRootContextV1(
          malformed_environment, malformed_access, request,
          malformed_result) !=
          xar::game::ReadCampaignRootContextResultV1::unavailable ||
      !ClearedUnavailable(malformed_result, "council_unavailable")) {
    return false;
  }
  Fixture wrong_owner;
  Put(wrong_owner.steward_active_task, 0x38, absent_incumbent);
  Put(wrong_owner.steward_active_task, 0x3C, Fixture::kTopLiegeId);
  const auto wrong_owner_environment = Environment(wrong_owner);
  const auto wrong_owner_access = Access(wrong_owner);
  xar::game::CampaignRootContextV1 wrong_owner_result{};
  return xar::ck3_11906::ReadCampaignRootContextV1(
             wrong_owner_environment, wrong_owner_access, request,
             wrong_owner_result) ==
             xar::game::ReadCampaignRootContextResultV1::unavailable &&
         ClearedUnavailable(wrong_owner_result, "council_unavailable");
}

bool TestCelestialCouncilIsOutsideStandardScope() {
  Fixture fixture;
  const auto identifier = fixture.identifier_names.find(20);
  if (identifier == fixture.identifier_names.end()) {
    return false;
  }
  fixture.native_strings[&identifier->second] = "government_is_celestial";
  // A celestial ministry does not use the standard five-seat council layout.
  // Keep an invalid standard task behind the scope gate to prove that the
  // reader does not dereference the incompatible representation.
  fixture.active_task_ids[0] += 0x01000000;
  const auto environment = Environment(fixture);
  const auto access = Access(fixture);
  const xar::ck3_11906::CampaignRootContextRequestV1 request{41};
  xar::game::CampaignRootContextV1 result{};
  return xar::ck3_11906::ReadCampaignRootContextV1(
             environment, access, request, result) ==
             xar::game::ReadCampaignRootContextResultV1::available &&
         result.government.has_value() &&
         std::find(result.government->flags.begin(),
                   result.government->flags.end(),
                   "government_is_celestial") !=
             result.government->flags.end() &&
         result.council.has_value() &&
         result.council->status ==
             xar::game::CampaignRootCouncilStatusV1::unavailable &&
         result.council->unavailable_reason ==
             "outside_standard_landed_non_nomadic_core_scope" &&
         !result.readiness.council_ready &&
         AllReadiness(result.readiness, true);
}

bool TestUnavailableRuleTokensPreserveRootObservation() {
  Fixture fixture;
  fixture.resolved_selected_rule_set = nullptr;
  const auto environment = Environment(fixture);
  const auto access = Access(fixture);
  const xar::ck3_11906::CampaignRootContextRequestV1 request{41};
  xar::game::CampaignRootContextV1 result{};
  if (xar::ck3_11906::ReadCampaignRootContextV1(
          environment, access, request, result) !=
          xar::game::ReadCampaignRootContextResultV1::available ||
      result.status !=
          xar::game::CampaignRootContextStatusV1::available ||
      !result.selected_game_rule_tokens.empty() ||
      result.native_selected_game_rule_token_count != 0 ||
      result.readiness.selected_game_rule_tokens_ready ||
      result.readiness.ready || !result.readiness.same_frame_ready ||
      !result.unavailable_reason.empty()) {
    return false;
  }
  auto complete_readiness = result.readiness;
  complete_readiness.selected_game_rule_tokens_ready = true;
  complete_readiness.ready = true;
  return AllReadiness(complete_readiness, true) &&
         !xar::ck3_11906::SerializeCampaignRootContextV1(result).empty();
}

bool TestTargetingFactionCountSemantics() {
  Fixture normal;
  auto environment = Environment(normal);
  auto access = Access(normal);
  std::int32_t focused_count = -1;
  if (!xar::ck3_11906::ReadCampaignRootTargetingFactionCountV1(
          environment, access, Fixture::kPlayerCharacterId, focused_count) ||
      focused_count != 2 ||
      xar::ck3_11906::ReadCampaignRootTargetingFactionCountV1(
          environment, access, Fixture::kImmediateLiegeId, focused_count)) {
    return false;
  }

  Fixture no_land_state;
  void *null_land_state = nullptr;
  Put(no_land_state.player_character, 0x1B8, null_land_state);
  no_land_state.resolved_primary_title = Address(no_land_state.title_fallback);
  environment = Environment(no_land_state);
  access = Access(no_land_state);
  const xar::ck3_11906::CampaignRootContextRequestV1 request{41};
  xar::game::CampaignRootContextV1 result{};
  if (xar::ck3_11906::ReadCampaignRootContextV1(
          environment, access, request, result) !=
          xar::game::ReadCampaignRootContextResultV1::available ||
      result.player_targeting_faction_count != 0) {
    return false;
  }
  if (!xar::ck3_11906::ReadCampaignRootTargetingFactionCountV1(
          environment, access, Fixture::kPlayerCharacterId, focused_count) ||
      focused_count != 0) {
    return false;
  }

  Fixture malformed;
  const std::int32_t negative_count = -1;
  Put(malformed.player_land_state, 0x12C, negative_count);
  environment = Environment(malformed);
  access = Access(malformed);
  result = {};
  return xar::ck3_11906::ReadCampaignRootContextV1(
             environment, access, request, result) ==
             xar::game::ReadCampaignRootContextResultV1::unavailable &&
         ClearedUnavailable(result,
                            "player_targeting_factions_unavailable") &&
         !xar::ck3_11906::ReadCampaignRootTargetingFactionCountV1(
             environment, access, Fixture::kPlayerCharacterId,
             focused_count);
}

bool TestStateChangedAndUnsupportedBuild() {
  Fixture changed_fixture;
  changed_fixture.change_frame_on_second_capture = true;
  auto environment = Environment(changed_fixture);
  auto access = Access(changed_fixture);
  const xar::ck3_11906::CampaignRootContextRequestV1 request{41};
  xar::game::CampaignRootContextV1 result{};
  if (xar::ck3_11906::ReadCampaignRootContextV1(
          environment, access, request, result) !=
          xar::game::ReadCampaignRootContextResultV1::unavailable ||
      !ClearedUnavailable(result, "state_changed")) {
    return false;
  }

  Fixture unsupported_fixture;
  environment = Environment(unsupported_fixture);
  environment.exact_build_admitted = false;
  access = Access(unsupported_fixture);
  result = {};
  return xar::ck3_11906::ReadCampaignRootContextV1(
             environment, access, request, result) ==
             xar::game::ReadCampaignRootContextResultV1::unavailable &&
         ClearedUnavailable(result, "unsupported_build");
}

} // namespace

int main() {
  if (!TestAvailableAndSerializer()) {
    std::cerr << "available reader/serializer fixture failed\n";
    return 1;
  }
  if (!TestLegitimateAbsenceAndGovernmentPointerSlot()) {
    std::cerr << "legitimate absence/pointer-slot fixture failed\n";
    return 1;
  }
  if (!TestTypedUnavailableClearsPartialObservation()) {
    std::cerr << "typed unavailable fixture failed\n";
    return 1;
  }
  if (!TestMalformedSuccessionIsTypedUnavailable()) {
    std::cerr << "malformed succession fixture failed\n";
    return 1;
  }
  if (!TestMalformedHeldTitlePartitionIsTypedUnavailable()) {
    std::cerr << "malformed held-title partition fixture failed\n";
    return 1;
  }
  if (!TestMonthlyIncomeFailureIsTypedUnavailable()) {
    std::cerr << "monthly income fixture failed\n";
    return 1;
  }
  if (!TestHealthFailureIsTypedUnavailable()) {
    std::cerr << "player health fixture failed\n";
    return 1;
  }
  if (!TestDomainFailureIsTypedUnavailable()) {
    std::cerr << "domain capacity fixture failed\n";
    return 1;
  }
  if (!TestCouncilDynamicPositionAndFailureBoundaries()) {
    std::cerr << "council dynamic/failure fixture failed\n";
    return 1;
  }
  if (!TestStoredVacantCouncilTasksPreserveRoot()) {
    std::cerr << "stored vacant council task fixture failed\n";
    return 1;
  }
  if (!TestCelestialCouncilIsOutsideStandardScope()) {
    std::cerr << "celestial council scope fixture failed\n";
    return 1;
  }
  if (!TestUnavailableRuleTokensPreserveRootObservation()) {
    std::cerr << "optional selected-rule-token fixture failed\n";
    return 1;
  }
  if (!TestTargetingFactionCountSemantics()) {
    std::cerr << "targeting faction count fixture failed\n";
    return 1;
  }
  if (!TestStateChangedAndUnsupportedBuild()) {
    std::cerr << "frame/build fixture failed\n";
    return 1;
  }
  std::cout << "campaign-root-context-v1 reader fixture passed\n";
  return 0;
}
