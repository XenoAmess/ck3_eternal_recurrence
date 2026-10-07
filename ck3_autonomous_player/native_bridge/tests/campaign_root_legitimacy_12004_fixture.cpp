// Offline source-authored fixture. No CK3, SDK, or process access.
// Only fake-memory setup/callbacks are reused from ck3_12002_campaign_test.cpp;
// no historical test case, main, serializer, or reader implementation is copied.
#include "xar_bridge/ck3_12004_campaign.hpp"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <string>
#include <string_view>
#include <system_error>
#include <unordered_map>
#include <utility>
#include <vector>

namespace {

// Sizes follow parent-published actual4 offsets; no legacy layout default.
constexpr std::size_t kPlayerCharacterFixtureBytes = std::max(
    std::size_t{0x1D8},
    xar::ck3_12004::kCampaignRootCharacterLegitimacyDataOffset12004 +
        sizeof(void *));
constexpr std::size_t kLegitimacyDataFixtureBytes =
    xar::ck3_12004::kCampaignRootLegitimacyBalanceOffset12004 +
    sizeof(std::int64_t);

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

#if defined(_MSC_VER)
#pragma warning(push)
// Owned native-memory blobs intentionally add alignment padding.
#pragma warning(disable : 4324)
#endif
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
  alignas(void *) Blob<0x22400> game_data{};
  alignas(void *) Blob<0xE0> player_entry{};
  alignas(void *) Blob<0x08> player_entries{};

  alignas(void *) Blob<0x30> character_storage{};
  alignas(void *) Blob<0xA0> character_slots{};
  alignas(void *) Blob<kPlayerCharacterFixtureBytes> player_character{};
  alignas(void *) Blob<kLegitimacyDataFixtureBytes> player_legitimacy_data{};
  alignas(void *) Blob<0x1D8> immediate_liege{};
  alignas(void *) Blob<0x1D8> top_liege{};
  alignas(void *) Blob<0x1D8> direct_vassal{};
  alignas(void *) Blob<0x1D8> landless_direct_vassal{};
  alignas(void *) Blob<0x1D8> dead_direct_vassal{};
  alignas(void *) Blob<0x1D8> external_province_holder{};
  alignas(void *) Blob<0x1D8> first_successor{};
  alignas(void *) Blob<0x1D8> second_successor{};
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
  alignas(void *) Blob<0x70> title_template{};
  alignas(void *) Blob<0x70> secondary_title_template{};
  alignas(void *) Blob<0x70> barony_title_template{};
  alignas(void *) Blob<0x30> title_fallback{};
  std::array<std::int32_t, 2> primary_title_successors{
      kFirstSuccessorId, kSecondSuccessorId};
  std::array<std::int32_t, 1> secondary_title_successors{kSecondSuccessorId};
  std::array<std::int32_t, 3> held_title_ids{
      kSecondaryTitleId, kPrimaryTitleId, kBaronyTitleId};

  alignas(void *) Blob<0x860> province{};
  alignas(void *) Blob<0x860> external_province{};
  alignas(void *) Blob<0x860> direct_vassal_province{};
  alignas(void *) Blob<0x860> unowned_province{};
  alignas(void *) Blob<0x860> null_county_province{};
  alignas(void *) Blob<0x48> provinces{};
  alignas(void *) Blob<0x60> player_province_map_node{};
  alignas(void *) Blob<0x60> direct_vassal_province_map_node{};
  alignas(void *) Blob<0xC0> player_province_adjacency_rows{};

  alignas(void *) Blob<0x68> government{};
  alignas(void *) Blob<0x68> government_fallback{};
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
  std::int64_t monthly_piety_raw = -125'000;
  std::uint32_t monthly_piety_calls = 0;
  bool health_available = true;
  std::int64_t health_raw = 275'000;
  std::uint32_t health_calls = 0;
  bool domain_available = true;
  bool title_province_available = true;
  bool family_county_null = false;
  bool family_key_changes_between_samples = false;
  std::uint32_t family_key_reads = 0;
  const void *failed_read_address = nullptr;
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
    Put(game_data, 0x222E8 + 0x58, entry = Address(player_entries));
    const std::int32_t player_count = 1;
    Put(game_data, 0x222E8 + 0x64, player_count);
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
    void *legitimacy_data_pointer = Address(player_legitimacy_data);
    Put(player_character,
        xar::ck3_12004::kCampaignRootCharacterLegitimacyDataOffset12004,
        legitimacy_data_pointer);
    Put(player_legitimacy_data,
        xar::ck3_12004::kCampaignRootLegitimacyBalanceOffset12004,
        std::int64_t{8'000'000});
    Put(immediate_liege, 0x18, kImmediateLiegeId);
    Put(top_liege, 0x18, kTopLiegeId);
    Put(direct_vassal, 0x18, kDirectVassalId);
    Put(landless_direct_vassal, 0x18, kLandlessDirectVassalId);
    Put(dead_direct_vassal, 0x18, kDeadDirectVassalId);
    Put(external_province_holder, 0x18, kExternalProvinceHolderId);
    Put(first_successor, 0x18, kFirstSuccessorId);
    Put(second_successor, 0x18, kSecondSuccessorId);
    void *no_death_marker = nullptr;
    Put(player_character, 0x1D0, no_death_marker);
    Put(immediate_liege, 0x1D0, no_death_marker);
    Put(top_liege, 0x1D0, no_death_marker);
    Put(direct_vassal, 0x1D0, no_death_marker);
    Put(landless_direct_vassal, 0x1D0, no_death_marker);
    Put(external_province_holder, 0x1D0, no_death_marker);
    Put(first_successor, 0x1D0, no_death_marker);
    Put(second_successor, 0x1D0, no_death_marker);
    void *player_land_state_pointer = Address(player_land_state);
    Put(player_character, 0x1C0, player_land_state_pointer);
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
    Put(dead_direct_vassal, 0x1D0, death_marker);

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
      Put(*task, 0x40, incumbent_id);
      Put(*task, 0x44, council_owner_id);
    }
    const std::uint8_t not_frozen = 0;
    const std::uint8_t frozen = 1;
    Put(chancellor_active_task, 0x39, not_frozen);
    Put(steward_active_task, 0x39, frozen);
    Put(spymaster_active_task, 0x39, not_frozen);
    const std::uint16_t county_target_tag = 8;
    const std::uint16_t character_target_tag = 4;
    const std::int32_t county_target = 5;
    const std::int32_t character_target = kExternalProvinceHolderId;
    Put(steward_active_task, 0x48, county_target_tag);
    Put(steward_active_task, 0x50, county_target);
    Put(spymaster_active_task, 0x48, character_target_tag);
    Put(spymaster_active_task, 0x50, character_target);
    const std::int64_t percentage_current = 5'000'000;
    Put(spymaster_active_task, 0x20, percentage_current);

    void *chancellor_position_type_pointer = Address(chancellor_position_type);
    void *steward_position_type_pointer = Address(steward_position_type);
    void *spymaster_position_type_pointer = Address(spymaster_position_type);
    Put(chancellor_task_type, 0x40, chancellor_position_type_pointer);
    Put(steward_task_type, 0x40, steward_position_type_pointer);
    Put(spymaster_task_type, 0x40, spymaster_position_type_pointer);
    const std::int32_t general_task = 0;
    const std::int32_t county_task = 1;
    const std::int32_t court_task = 2;
    const std::int32_t infinite_progress = 0;
    const std::int32_t percentage_progress = 1;
    const std::int32_t value_progress = 2;
    Put(chancellor_task_type, 0x48, general_task);
    Put(steward_task_type, 0x48, county_task);
    Put(spymaster_task_type, 0x48, court_task);
    Put(chancellor_task_type, 0x54, infinite_progress);
    Put(steward_task_type, 0x54, value_progress);
    Put(spymaster_task_type, 0x54, percentage_progress);

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
    Put(primary_title, 0x48, title_template_pointer);
    const std::int32_t player_holder_id = kPlayerCharacterId;
    Put(primary_title, 0x128, player_holder_id);
    void *successor_data = primary_title_successors.data();
    Put(primary_title, 0x150, successor_data);
    const std::int32_t successor_count =
        static_cast<std::int32_t>(primary_title_successors.size());
    Put(primary_title, 0x158, successor_count);
    Put(primary_title, 0x15C, successor_count);
    void *secondary_template_pointer = Address(secondary_title_template);
    Put(secondary_title, 0x48, secondary_template_pointer);
    Put(secondary_title, 0x128, player_holder_id);
    void *secondary_successor_data = secondary_title_successors.data();
    Put(secondary_title, 0x150, secondary_successor_data);
    const std::int32_t secondary_successor_count = 1;
    Put(secondary_title, 0x158, secondary_successor_count);
    Put(secondary_title, 0x15C, secondary_successor_count);
    void *barony_template_pointer = Address(barony_title_template);
    Put(barony_title, 0x48, barony_template_pointer);
    Put(barony_title, 0x128, player_holder_id);
    void *no_successors = nullptr;
    const std::int32_t no_successor_count = 0;
    Put(barony_title, 0x150, no_successors);
    Put(barony_title, 0x158, no_successor_count);
    Put(barony_title, 0x15C, no_successor_count);
    Put(direct_vassal_title, 0x48, title_template_pointer);
    Put(external_province_holder_title, 0x48, title_template_pointer);
    const std::int32_t hegemony_tier = 6;
    Put(title_template, 0x64, hegemony_tier);
    const std::int32_t county_tier = 2;
    Put(secondary_title_template, 0x64, county_tier);
    const std::int32_t barony_tier = 1;
    Put(barony_title_template, 0x64, barony_tier);

    const std::int32_t province_id = 5;
    const std::int32_t external_province_id = 6;
    const std::int32_t direct_vassal_province_id = 7;
    const std::int32_t unowned_province_id = 8;
    Put(province, 0x10, province_id);
    Put(external_province, 0x10, external_province_id);
    Put(direct_vassal_province, 0x10, direct_vassal_province_id);
    Put(unowned_province, 0x10, unowned_province_id);
    for (auto *observed_province : {&province, &external_province,
                                   &direct_vassal_province, &unowned_province}) {
      Put(*observed_province, 0x85C, std::uint32_t{0x50726F76U});
    }
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
    Put(government, 0x50, government_flags);
    const std::int32_t flag_count =
        static_cast<std::int32_t>(government_flag_ids.size());
    Put(government, 0x50 + 0x0C, flag_count);

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

#if defined(_MSC_VER)
#pragma warning(pop)
#endif

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
  if (g_fixture->family_county_null &&
      title == Address(g_fixture->secondary_title)) {
    return Address(g_fixture->null_county_province);
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

// Synthetic engine output using the observed Crozier numeric ABI. No live piety
// observation is represented by this offline fixture.
std::int64_t *__fastcall ResolveMonthlyPiety(
    const void *scope, std::int64_t *output, void *optional_tooltip) noexcept {
  if (g_fixture == nullptr || scope == nullptr || output == nullptr ||
      optional_tooltip != nullptr) {
    return nullptr;
  }
  void *character = nullptr;
  std::uint8_t tag = 0xff;
  std::memcpy(&character, scope, sizeof(character));
  std::memcpy(&tag, static_cast<const std::byte *>(scope) + 8, sizeof(tag));
  if (character != Address(g_fixture->player_character) || tag != 0) {
    return nullptr;
  }
  ++g_fixture->monthly_piety_calls;
  *output = g_fixture->monthly_piety_raw;
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
      task_scopes != Address(g_fixture->steward_active_task, 0x40) ||
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
      task_scopes != Address(g_fixture->steward_active_task, 0x40) ||
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

bool ReadMemory(void *opaque, const void *address, void *output,
                std::size_t size) noexcept {
  const auto &fixture = *static_cast<Fixture *>(opaque);
  if (address == nullptr || output == nullptr || size == 0 ||
      address == fixture.failed_read_address) {
    return false;
  }
  std::memcpy(output, address, size);
  return true;
}

bool ReadString(void *opaque, const void *address,
                std::string &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  const auto found = fixture.native_strings.find(address);
  if (found == fixture.native_strings.end()) {
    output.clear();
    return false;
  }
  output = found->second;
  if (fixture.family_key_changes_between_samples &&
      address == Address(fixture.secondary_title_template, 0x18) &&
      ++fixture.family_key_reads > 1) {
    output = "c_changed_family";
  }
  return true;
}

xar::ck3_12004::CampaignRootNativeEnvironmentV1 Environment(Fixture &fixture) {
  xar::ck3_12004::CampaignRootNativeEnvironmentV1 environment{};
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
  environment.monthly_piety = &ResolveMonthlyPiety;
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

xar::ck3_12004::CampaignRootAccessV1 Access(Fixture &fixture) {
  xar::ck3_12004::CampaignRootAccessV1 access{};
  access.context = &fixture;
  access.capture_frame = &CaptureFrame;
  access.is_main_thread = &IsMainThread;
  access.read_memory = &ReadMemory;
  access.read_string = &ReadString;
  return access;
}

enum class LegitimacyCase { positive, zero, absent_data, negative_raw, changed_frame };

struct LegitimacyCaseSpec {
  LegitimacyCase kind;
  std::string_view file_name;
  std::int64_t raw;
  std::string_view unavailable_reason;
};

constexpr std::array<LegitimacyCaseSpec, 5> kCases{{
    {LegitimacyCase::positive, "positive.json", 8'000'000, {}},
    {LegitimacyCase::zero, "zero.json", 0, {}},
    {LegitimacyCase::absent_data, "absent-data.json", 8'000'000, "data_absent"},
    {LegitimacyCase::negative_raw, "negative-raw.json", -1, "balance_invalid"},
    {LegitimacyCase::changed_frame, "changed-frame.json", 8'000'000, {}},
}};

bool WriteWire(const std::filesystem::path &directory,
               std::string_view file_name, std::string_view wire) {
  std::ofstream stream(directory / std::string(file_name),
                       std::ios::binary | std::ios::trunc);
  if (!stream) return false;
  stream.write(wire.data(), static_cast<std::streamsize>(wire.size()));
  stream.put('\n');
  stream.close();
  return !stream.fail();
}

bool ProduceCase(const std::filesystem::path &directory,
                 const LegitimacyCaseSpec &spec,
                 xar::game::CampaignRootReadinessV1 &baseline_readiness,
                 bool &baseline_set) {
  Fixture fixture;
  Put(fixture.player_legitimacy_data,
      xar::ck3_12004::kCampaignRootLegitimacyBalanceOffset12004, spec.raw);
  if (spec.kind == LegitimacyCase::absent_data) {
    void *absent = nullptr;
    Put(fixture.player_character,
        xar::ck3_12004::kCampaignRootCharacterLegitimacyDataOffset12004, absent);
  }
  fixture.change_frame_on_second_capture =
      spec.kind == LegitimacyCase::changed_frame;

  xar::ck3_12004::CampaignRootContextRequestV1 request{};
  request.expected_snapshot_revision = fixture.frame.snapshot_revision;
  xar::game::CampaignRootContextV1 context{};
  const auto result = xar::ck3_12004::ReadCampaignRootContextV1(
      Environment(fixture), Access(fixture), request, context);
  const std::string wire =
      xar::ck3_12004::SerializeCampaignRootContextV1(context);
  // Preserve a serializable failed first attempt for Root's producer diagnostics.
  if (wire.empty() || !WriteWire(directory, spec.file_name, wire)) {
    std::cerr << spec.file_name << ": actual4 whole serializer/write failed; root="
              << context.unavailable_reason << '\n';
    return false;
  }
  const std::string version_pin =
      std::string("\"game_version\":\"") +
      std::string(xar::ck3_12004::kGameVersion) + "\"";
  if (wire.find(version_pin) == std::string::npos ||
      wire.find(xar::ck3_12004::kExecutableSha256) == std::string::npos ||
      wire.find("ck3-1.20.0.4-native-campaign-root-context-v1") ==
          std::string::npos ||
      fixture.capture_calls != 2 ||
      context.snapshot_revision != fixture.frame.snapshot_revision ||
      context.date_raw != fixture.frame.date_raw) {
    std::cerr << spec.file_name << ": complete actual4 frame/pins differ\n";
    return false;
  }

  if (spec.kind == LegitimacyCase::changed_frame) {
    if (result != xar::game::ReadCampaignRootContextResultV1::unavailable ||
        context.status != xar::game::CampaignRootContextStatusV1::unavailable ||
        context.unavailable_reason != "state_changed" ||
        context.player_legitimacy_v1.has_value() ||
        context.readiness != xar::game::CampaignRootReadinessV1{} ||
        wire.find("\"player_legitimacy_v1\":null") == std::string::npos) {
      std::cerr << spec.file_name << ": changed-frame material was retained\n";
      return false;
    }
    return true;
  }
  if (result != xar::game::ReadCampaignRootContextResultV1::available ||
      context.status != xar::game::CampaignRootContextStatusV1::available ||
      !context.unavailable_reason.empty() ||
      context.player_character_id != Fixture::kPlayerCharacterId ||
      !context.player_legitimacy_v1.has_value()) {
    std::cerr << spec.file_name << ": complete root is unavailable; root="
              << context.unavailable_reason << '\n';
    return false;
  }
  const auto &legitimacy = *context.player_legitimacy_v1;
  if (spec.unavailable_reason.empty()) {
    if (!legitimacy.value.has_value() || legitimacy.value->raw != spec.raw ||
        legitimacy.value->scale != 100'000 ||
        !legitimacy.unavailable_reason.empty()) {
      std::cerr << spec.file_name << ": positive/zero legitimacy differs; optional="
                << legitimacy.unavailable_reason << '\n';
      return false;
    }
  } else if (legitimacy.value.has_value() ||
             legitimacy.unavailable_reason != spec.unavailable_reason) {
    std::cerr << spec.file_name << ": unavailable optional became a value\n";
    return false;
  }
  if (!baseline_set) {
    baseline_readiness = context.readiness;
    baseline_set = true;
  } else if (context.readiness != baseline_readiness) {
    std::cerr << spec.file_name << ": optional legitimacy changed root readiness\n";
    return false;
  }
  return true;
}

} // namespace

int main(int argc, char **argv) {
  if (argc != 2) {
    std::cerr << "usage: campaign_root_legitimacy_12004_first_fixture output_dir\n";
    return 2;
  }
  const std::filesystem::path directory(argv[1]);
  std::error_code error;
  std::filesystem::create_directories(directory, error);
  if (error) {
    std::cerr << "cannot create fixture wire directory: " << error.message() << '\n';
    return 2;
  }
  xar::game::CampaignRootReadinessV1 baseline_readiness{};
  bool baseline_set = false;
  for (const auto &spec : kCases) {
    if (!ProduceCase(directory, spec, baseline_readiness, baseline_set)) return 1;
  }
  const std::string manifest =
      std::string("{\"producer\":\"campaign-root-legitimacy-12004-first\","
                  "\"evidence_kind\":\"offline-native-fixture\","
                  "\"game_version\":\"") +
      std::string(xar::ck3_12004::kGameVersion) +
      "\",\"executable_sha256\":\"" +
      std::string(xar::ck3_12004::kExecutableSha256) +
      "\",\"whole_wires\":[\"positive.json\",\"zero.json\","
      "\"absent-data.json\",\"negative-raw.json\",\"changed-frame.json\"]}";
  if (!WriteWire(directory, "producer-manifest.json", manifest)) return 2;
  std::cout << "actual4 campaign root legitimacy: five offline whole wires emitted\n";
  return 0;
}
