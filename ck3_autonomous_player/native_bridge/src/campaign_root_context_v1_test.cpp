#include "xar_bridge/campaign_root_context_v1.hpp"

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

  alignas(void *) Blob<0xA8> game_state{};
  alignas(void *) Blob<0x20> jomini_state{};
  alignas(void *) Blob<0x1F8> players{};
  alignas(void *) Blob<0x1D600> game_data{};
  alignas(void *) Blob<0xE0> player_entry{};
  alignas(void *) Blob<0x08> player_entries{};

  alignas(void *) Blob<0x30> character_storage{};
  alignas(void *) Blob<0x80> character_slots{};
  alignas(void *) Blob<0x1D0> player_character{};
  alignas(void *) Blob<0x1D0> immediate_liege{};
  alignas(void *) Blob<0x1D0> top_liege{};
  alignas(void *) Blob<0x1D0> direct_vassal{};
  alignas(void *) Blob<0x1D0> landless_direct_vassal{};
  alignas(void *) Blob<0x1D0> dead_direct_vassal{};
  alignas(void *) Blob<0x1D0> external_province_holder{};
  alignas(void *) Blob<0x30> character_fallback{};

  alignas(void *) Blob<0x30> title_storage{};
  alignas(void *) Blob<0x40> title_slots{};
  alignas(void *) Blob<0x168> primary_title{};
  alignas(void *) Blob<0x168> direct_vassal_title{};
  alignas(void *) Blob<0x168> external_province_holder_title{};
  alignas(void *) Blob<0x64> title_template{};
  alignas(void *) Blob<0x30> title_fallback{};

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
    const std::int32_t character_capacity = 8;
    Put(character_storage, 0x2C, character_capacity);
    void *player_character_pointer = Address(player_character);
    void *immediate_liege_pointer = Address(immediate_liege);
    void *top_liege_pointer = Address(top_liege);
    void *direct_vassal_pointer = Address(direct_vassal);
    void *landless_direct_vassal_pointer = Address(landless_direct_vassal);
    void *dead_direct_vassal_pointer = Address(dead_direct_vassal);
    void *external_province_holder_pointer =
        Address(external_province_holder);
    Put(character_slots, 1 * 0x10 + 0x08, player_character_pointer);
    Put(character_slots, 2 * 0x10 + 0x08, immediate_liege_pointer);
    Put(character_slots, 3 * 0x10 + 0x08, top_liege_pointer);
    Put(character_slots, 4 * 0x10 + 0x08, direct_vassal_pointer);
    Put(character_slots, 5 * 0x10 + 0x08, landless_direct_vassal_pointer);
    Put(character_slots, 6 * 0x10 + 0x08, dead_direct_vassal_pointer);
    Put(character_slots, 7 * 0x10 + 0x08,
        external_province_holder_pointer);
    Put(player_character, 0x18, kPlayerCharacterId);
    Put(immediate_liege, 0x18, kImmediateLiegeId);
    Put(top_liege, 0x18, kTopLiegeId);
    Put(direct_vassal, 0x18, kDirectVassalId);
    Put(landless_direct_vassal, 0x18, kLandlessDirectVassalId);
    Put(dead_direct_vassal, 0x18, kDeadDirectVassalId);
    Put(external_province_holder, 0x18, kExternalProvinceHolderId);
    void *no_death_marker = nullptr;
    Put(player_character, 0x1C8, no_death_marker);
    Put(immediate_liege, 0x1C8, no_death_marker);
    Put(top_liege, 0x1C8, no_death_marker);
    Put(direct_vassal, 0x1C8, no_death_marker);
    Put(landless_direct_vassal, 0x1C8, no_death_marker);
    Put(external_province_holder, 0x1C8, no_death_marker);
    void *death_marker = Address(dead_direct_vassal);
    Put(dead_direct_vassal, 0x1C8, death_marker);

    slots = Address(title_slots);
    Put(title_storage, 0x20, slots);
    const std::int32_t title_capacity = 4;
    Put(title_storage, 0x2C, title_capacity);
    Put(title_slots, 1 * 0x10 + 0x08, resolved_primary_title);
    void *direct_vassal_title_pointer = Address(direct_vassal_title);
    Put(title_slots, 2 * 0x10 + 0x08, direct_vassal_title_pointer);
    void *external_title_pointer = Address(external_province_holder_title);
    Put(title_slots, 3 * 0x10 + 0x08, external_title_pointer);
    Put(primary_title, 0x10, kPrimaryTitleId);
    Put(direct_vassal_title, 0x10, kDirectVassalTitleId);
    Put(external_province_holder_title, 0x10,
        kExternalProvinceHolderTitleId);
    void *title_template_pointer = Address(title_template);
    Put(primary_title, 0x160, title_template_pointer);
    Put(direct_vassal_title, 0x160, title_template_pointer);
    Put(external_province_holder_title, 0x160, title_template_pointer);
    const std::int32_t hegemony_tier = 6;
    Put(title_template, 0x5C, hegemony_tier);

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
  environment.game_rule_selection_service_slot =
      &fixture.selection_service_slot;
  environment.game_rule_token_fallback_slot =
      &fixture.rule_token_fallback_slot;
  environment.primary_title = &ResolvePrimaryTitle;
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
         value.primary_title_ready == expected &&
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
  if (xar::ck3_11906::ReadCampaignRootContextV1(
          environment, access, request, result) !=
          xar::game::ReadCampaignRootContextResultV1::available ||
      result.status != xar::game::CampaignRootContextStatusV1::available ||
      result.snapshot_revision != 41 || result.date_raw != 12'345 ||
      result.local_player_id != 7 ||
      result.player_character_id != Fixture::kPlayerCharacterId ||
      result.player_character_alive != true || !result.primary_title ||
      result.primary_title->title_id != Fixture::kPrimaryTitleId ||
      result.primary_title->tier_raw != 6 ||
      result.primary_title->tier_key != "hegemony" ||
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

  const auto json =
      xar::ck3_11906::SerializeCampaignRootContextV1(result);
  const std::string expected =
      "{\"schema_version\":1,\"status\":\"available\","
      "\"snapshot_revision\":41,\"date_raw\":12345,"
      "\"local_player_id\":7,\"player_character_id\":33554433,"
      "\"player_character_alive\":true,\"primary_title\":{"
      "\"title_id\":83886081,\"tier_raw\":6,"
      "\"tier_key\":\"hegemony\"},\"capital_province_id\":5,"
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
      "\"primary_title_ready\":true,\"capital_ready\":true,"
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
      "\"primary_title_rva\":\"0x25F3350\","
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

  constexpr std::array<std::string_view, 6> tier_keys{
      "barony", "county", "duchy", "kingdom", "empire", "hegemony"};
  for (std::int32_t tier = 1; tier <= 6; ++tier) {
    Put(fixture.title_template, 0x5C, tier);
    fixture.capture_calls = 0;
    result = {};
    if (xar::ck3_11906::ReadCampaignRootContextV1(
            environment, access, request, result) !=
            xar::game::ReadCampaignRootContextResultV1::available ||
        !result.primary_title || result.primary_title->tier_raw != tier ||
        result.primary_title->tier_key !=
            tier_keys[static_cast<std::size_t>(tier - 1)]) {
      return false;
    }
  }
  return true;
}

bool TestLegitimateAbsenceAndGovernmentPointerSlot() {
  Fixture fixture;
  fixture.resolved_primary_title = Address(fixture.title_fallback);
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
         !result.immediate_liege_character_id &&
         result.top_liege_character_id == Fixture::kPlayerCharacterId &&
         result.independent == true && !result.government &&
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
  if (!TestStateChangedAndUnsupportedBuild()) {
    std::cerr << "frame/build fixture failed\n";
    return 1;
  }
  std::cout << "campaign-root-context-v1 reader fixture passed\n";
  return 0;
}
