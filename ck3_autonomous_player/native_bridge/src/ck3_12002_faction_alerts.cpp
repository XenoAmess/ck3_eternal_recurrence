#include "xar_bridge/ck3_12002_faction_alerts.hpp"

#include <algorithm>
#include <cstring>
#include <limits>
#include <utility>

#if defined(_WIN32)
#include <windows.h>
#endif

namespace xar::ck3_12002 {
namespace {

using Failure = game::PlayerFactionAlertsFailureReasonV1;
using Result = game::ReadPlayerFactionAlertsResultV1;
using SourceSample = ck3_11906::PlayerFactionAlertsSourceSampleV1;
constexpr std::size_t kMaximumRows = 64;
constexpr std::size_t kMaximumMembers = 16'384;

bool DirectRead(const void *address, void *output, std::size_t size) noexcept {
  if (!address || !output || !size) return false;
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(output, address, size);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#endif
}

template <typename Value>
bool Read(const PlayerFactionAlertsAccessV1 &access, const void *base,
          std::size_t offset, Value &output) noexcept {
  output = {};
  if (!base) return false;
  const auto address = static_cast<const std::byte *>(base) + offset;
  return access.read_memory
             ? access.read_memory(access.context, address, &output, sizeof output)
             : DirectRead(address, &output, sizeof output);
}

bool ReadBytes(const PlayerFactionAlertsAccessV1 &access, const void *base,
               void *output, std::size_t size) noexcept {
  return access.read_memory
             ? access.read_memory(access.context, base, output, size)
             : DirectRead(base, output, size);
}

bool Resolve(const PlayerFactionAlertsAccessV1 &access, void **storage_slot,
             void **fallback_slot, std::int32_t id, std::size_t identity_offset,
             void *&object) noexcept {
  object = nullptr;
  void *storage = nullptr;
  void *fallback = nullptr;
  void *slots = nullptr;
  std::int32_t capacity = 0;
  if (!storage_slot || !Read(access, storage_slot, 0, storage) || !storage ||
      (fallback_slot && !Read(access, fallback_slot, 0, fallback)) ||
      !Read(access, storage, 0x20, slots) ||
      !Read(access, storage, 0x2C, capacity) || capacity < 0 ||
      capacity > 0x01000000 || (capacity && !slots)) return false;
  const auto index = static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
  if (id <= 0 || index >= static_cast<std::uint32_t>(capacity)) return true;
  void *candidate = nullptr;
  std::int32_t round_trip = -1;
  if (!Read(access, slots, static_cast<std::size_t>(index) * 0x10 + 8, candidate))
    return false;
  if (!candidate || candidate == fallback) return true;
  if (!Read(access, candidate, identity_offset, round_trip)) return false;
  if (round_trip == id) object = candidate;
  return true;
}

bool StableKey(std::string_view key) noexcept {
  if (key.empty()) return false;
  for (const char byte : key)
    if (!((byte >= 'a' && byte <= 'z') || (byte >= '0' && byte <= '9') ||
          byte == '_')) return false;
  return true;
}

bool ReadKey(const PlayerFactionAlertsAccessV1 &access, const void *string,
             std::string &output) {
  output.clear();
  if (!string) return false;
  if (access.read_string)
    return access.read_string(access.context, string, output) && StableKey(output);
  std::size_t length = 0;
  std::size_t capacity = 0;
  if (!Read(access, string, 0x10, length) || !Read(access, string, 0x18, capacity) ||
      !length || length > 1024 || capacity < length) return false;
  const void *bytes = string;
  if (capacity > 15 && (!Read(access, string, 0, bytes) || !bytes)) return false;
  output.resize(length);
  return ReadBytes(access, bytes, output.data(), length) && StableKey(output);
}

bool InvokeFactionFixed(NativeFactionFixedPoint12002 function, void *faction,
                        std::int64_t &output) noexcept {
  output = 0;
  if (!function) return false;
#if defined(_MSC_VER)
  __try {
#endif
    return function(faction, &output) == &output;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#endif
}

bool InvokeInt(NativeFactionInt32_12002 function,
               void *faction, std::int32_t &output) noexcept {
  output = 0;
  if (!function) return false;
#if defined(_MSC_VER)
  __try {
#endif
    output = function(faction);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#endif
}

bool InvokeFactionBool(NativeFactionBool12002 function,
                       void *faction, bool &output) noexcept {
  output = false;
  if (!function) return false;
#if defined(_MSC_VER)
  __try {
#endif
    output = function(faction);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#endif
}

bool InvokeDanger(NativeFactionDanger12002 function, void *faction,
                  bool &output) noexcept {
  output = false;
  if (!function) return false;
#if defined(_MSC_VER)
  __try {
#endif
    output = function(faction, faction);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#endif
}

bool InvokeHuman(NativeFactionCharacterBool12002 function, std::int32_t character_id,
                 bool &output) noexcept {
  output = false;
  if (!function || character_id <= 0) return false;
#if defined(_MSC_VER)
  __try {
#endif
    output = function(static_cast<std::uint32_t>(character_id));
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#endif
}

bool InvokeLiege(NativeCampaignRootCharacterResolverV1 function,
                 void *character, void *&output) noexcept {
  output = nullptr;
  if (!function || !character) return false;
#if defined(_MSC_VER)
  __try {
#endif
    output = function(character);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#endif
}

bool ReadMembers(const PlayerFactionAlertsNativeEnvironmentV1 &environment,
                  const PlayerFactionAlertsAccessV1 &access, void *faction,
                  std::int32_t faction_id, std::size_t span_offset,
                  bool county, std::vector<std::int32_t> &output,
                  std::vector<game::PlayerFactionCountyMemberObservationV1> *observations = nullptr) {
  output.clear();
  if (observations) observations->clear();
  void *data = nullptr;
  std::int32_t count = 0;
  if (!Read(access, faction, span_offset, data) ||
      !Read(access, faction, span_offset + 0x0C, count) || count < 0 ||
      static_cast<std::size_t>(count) > kMaximumMembers || (count && !data))
    return false;
  for (std::int32_t index = 0; index < count; ++index) {
    const auto offset = static_cast<std::size_t>(index) * (county ? 0x18 : 0x20);
    std::int32_t member_id = -1;
    std::int32_t owner_id = -1;
    void *member = nullptr;
    void *owner = nullptr;
    if (!Read(access, data, offset + 8, member_id) ||
        (county ? (!Read(access, data, offset + 0x10, owner) || owner != faction)
                : (!Read(access, data, offset + 0x0C, owner_id) || owner_id != faction_id)) ||
        member_id <= 0 ||
        !Resolve(access,
                 county ? environment.landed_title_storage_slot
                        : environment.character_storage_slot,
                 county ? environment.landed_title_fallback_slot
                        : environment.character_fallback_slot,
                 member_id, county ? 0x10 : 0x18, member) || !member)
      return false;
    output.push_back(member_id);
    if (county && environment.county_observations_12003 && observations) {
      game::PlayerFactionCountyMemberObservationV1 observation{};
      observation.county_title_id = member_id;
      FactionCountyOpinionMaterial12003 opinion{};
      const bool opinion_available = ReadCountyMemberOpinion12003(
          environment, access, member_id, opinion);
      if (opinion.capital_province_id > 0)
        observation.capital_province_id = opinion.capital_province_id;
      if (opinion.holder_character_id > 0)
        observation.holder_character_id = opinion.holder_character_id;
      if (opinion_available) {
        observation.county_opinion = opinion.county_opinion;
        observation.opinion_status = "available";
      }
      CountyFactionFinalObservation12003 finals{};
      const bool finals_available = ReadCountyFactionFinals12003(
          environment.county_faction_finals, access, faction, member,
          static_cast<const std::byte *>(data) + offset, finals);
      observation.native_county_join_score_raw = finals.join_score_raw;
      observation.can_add_county = finals.can_add_county;
      observation.removal_queued = finals.removal_queued;
      observation.native_leave_score_threshold = finals.leave_score_threshold;
      if (finals_available) observation.native_final_status = "available";
      observations->push_back(std::move(observation));
    }
  }
  std::sort(output.begin(), output.end());
  if (observations)
    std::sort(observations->begin(), observations->end(), [](const auto &left, const auto &right) {
      return left.county_title_id < right.county_title_id;
    });
  return std::adjacent_find(output.begin(), output.end()) == output.end();
}

void DeriveDanger(game::PlayerTargetingFactionV1 &row) {
  if (row.leader_is_human) {
    row.dangerous_by_stock_rule = true;
    row.danger_reason = "human_faction_leader";
  } else if (row.faction_type_key == "peasant_faction") {
    row.dangerous_by_stock_rule = row.months_until_max_discontent &&
                                *row.months_until_max_discontent <= 12;
    row.danger_reason = row.dangerous_by_stock_rule
                           ? "peasant_ultimatum_within_12_months"
                           : "peasant_ultimatum_not_within_12_months";
  } else {
    row.dangerous_by_stock_rule = row.discontent_per_month.raw > 0;
    row.danger_reason = row.dangerous_by_stock_rule
                           ? "non_peasant_discontent_increasing"
                           : "non_peasant_discontent_not_increasing";
  }
}

ReadFactionEntityResult12002 ReadEntitySample(
    const PlayerFactionAlertsNativeEnvironmentV1 &environment,
    const PlayerFactionAlertsAccessV1 &access, std::int32_t faction_id,
    game::PlayerTargetingFactionV1 &output) {
  output = {};
  void *faction = nullptr;
  if (!Resolve(access, environment.faction_storage_slot,
               environment.faction_fallback_slot, faction_id, 0x10, faction))
    return ReadFactionEntityResult12002::unavailable;
  if (!faction) return ReadFactionEntityResult12002::known_absent;
  std::uintptr_t vtable = 0;
  if (!Read(access, faction, 0, vtable) ||
      vtable != environment.expected_faction_vtable)
    return ReadFactionEntityResult12002::unavailable;
  game::PlayerTargetingFactionV1 row{};
  row.faction_id = faction_id;
  void *type = nullptr;
  void *target = nullptr;
  if (!Read(access, faction, 0x20, type) || !type ||
      !ReadKey(access, static_cast<const std::byte *>(type) + 0x18,
               row.faction_type_key) ||
      !Read(access, faction, 0x40, row.target_character_id) ||
      !Resolve(access, environment.character_storage_slot,
               environment.character_fallback_slot, row.target_character_id,
               0x18, target) || !target)
    return ReadFactionEntityResult12002::unavailable;
  std::int32_t leader_id = -1;
  void *leader = nullptr;
  if (!Read(access, faction, 0x44, leader_id) ||
      !Resolve(access, environment.character_storage_slot,
               environment.character_fallback_slot, leader_id, 0x18, leader))
    return ReadFactionEntityResult12002::unavailable;
  if (leader) {
    row.leader_character_id = leader_id;
    if (!InvokeHuman(environment.character_is_human, leader_id, row.leader_is_human))
      return ReadFactionEntityResult12002::unavailable;
  }
  if (!ReadMembers(environment, access, faction, faction_id, 0x48, false,
                   row.character_member_ids) ||
      !ReadMembers(environment, access, faction, faction_id, 0x60, true,
                   row.county_member_title_ids, &row.county_member_observations))
    return ReadFactionEntityResult12002::unavailable;
  std::int32_t months = 0;
  if (!InvokeFactionFixed(environment.power, faction, row.power.raw) ||
      !InvokeFactionFixed(environment.power_threshold, faction, row.power_threshold.raw) ||
      !Read(access, faction, 0x28, row.discontent.raw) ||
      !InvokeFactionFixed(environment.discontent_per_month, faction,
                   row.discontent_per_month.raw) ||
      !InvokeInt(environment.months_until_max_discontent, faction, months) ||
      !InvokeFactionBool(environment.at_war, faction, row.faction_at_war) ||
      row.power.raw < 0 || row.power_threshold.raw < 0 || row.discontent.raw < 0)
    return ReadFactionEntityResult12002::unavailable;
  if (months >= 0) row.months_until_max_discontent = months;
  if (row.faction_at_war) {
    std::int32_t war_id = -1;
    void *war = nullptr;
    if (!Read(access, faction, 0x8C, war_id) || war_id <= 0 ||
        !Resolve(access, environment.war_storage_slot,
                 environment.war_fallback_slot, war_id, 8, war) || !war)
      return ReadFactionEntityResult12002::unavailable;
    row.faction_war_id = war_id;
  }
  DeriveDanger(row);
  bool native_danger = false;
  if (!InvokeDanger(environment.dangerous, faction, native_danger) ||
      native_danger != row.dangerous_by_stock_rule)
    return ReadFactionEntityResult12002::unavailable;
  output = std::move(row);
  return ReadFactionEntityResult12002::available;
}

bool ReadTargetingIds(const PlayerFactionAlertsAccessV1 &access, void *character,
                      std::vector<std::int32_t> &output) {
  output.clear();
  void *land = nullptr;
  if (!Read(access, character, 0x1C0, land)) return false;
  if (!land) return true;
  void *data = nullptr;
  std::int32_t count = 0;
  if (!Read(access, land, 0x120, data) || !Read(access, land, 0x12C, count) ||
      count < 0 || static_cast<std::size_t>(count) > kMaximumRows ||
      (count && !data)) return false;
  for (std::int32_t index = 0; index < count; ++index) {
    std::int32_t id = -1;
    if (!Read(access, data, static_cast<std::size_t>(index) * 4, id) || id <= 0)
      return false;
    output.push_back(id);
  }
  std::sort(output.begin(), output.end());
  return std::adjacent_find(output.begin(), output.end()) == output.end();
}

bool ReadIdSpan(const PlayerFactionAlertsAccessV1 &access, void *object,
                std::size_t offset, std::vector<std::int32_t> &output) {
  output.clear();
  void *data = nullptr;
  std::int32_t count = 0;
  if (!Read(access, object, offset, data) ||
      !Read(access, object, offset + 0x0C, count) || count < 0 ||
      count > 16'384 || (count && !data)) return false;
  for (std::int32_t index = 0; index < count; ++index) {
    std::int32_t id = -1;
    if (!Read(access, data, static_cast<std::size_t>(index) * 4, id) || id <= 0)
      return false;
    output.push_back(id);
  }
  return true;
}

bool ReadSubrealmCountyIds(
    const PlayerFactionAlertsNativeEnvironmentV1 &environment,
    const PlayerFactionAlertsAccessV1 &access, std::int32_t actor_id,
    std::vector<std::int32_t> &output) {
  output.clear();
  std::vector<std::int32_t> characters{actor_id};
  for (std::size_t cursor = 0; cursor < characters.size(); ++cursor) {
    if (characters.size() > 16'384) return false;
    void *character = nullptr;
    void *land = nullptr;
    if (!Resolve(access, environment.character_storage_slot,
                 environment.character_fallback_slot, characters[cursor], 0x18,
                 character) || !character ||
        !Read(access, character, 0x1C0, land)) return false;
    if (!land) continue;
    std::vector<std::int32_t> ids;
    if (!ReadIdSpan(access, land, 0x1E0, ids)) return false;
    for (const auto title_id : ids) {
      void *title = nullptr;
      void *definition = nullptr;
      std::int32_t tier = -1;
      std::int32_t de_jure_children = 0;
      if (!Resolve(access, environment.landed_title_storage_slot,
                   environment.landed_title_fallback_slot, title_id, 0x10,
                   title) || !title || !Read(access, title, 0x48, definition) ||
          !definition || !Read(access, definition, 0x64, tier)) return false;
      if (tier != 2) continue;
      // CLandedTitlesBuilder<0> invokes stock 0x230D850. Its exact county
      // branch accepts a title iff its de-jure child count is nonzero.
      if (!Read(access, title, 0x11C, de_jure_children) || de_jure_children < 0)
        return false;
      if (de_jure_children) output.push_back(title_id);
    }
    if (!ReadIdSpan(access, land, 0x218, ids)) return false;
    for (const auto contract_id : ids) {
      void *contract = nullptr;
      void *vassal = nullptr;
      void *round_trip = nullptr;
      std::int32_t vassal_id = -1;
      if (!Resolve(access, environment.vassal_contract_storage_slot,
                   environment.vassal_contract_fallback_slot, contract_id, 8,
                   contract) || !contract || !Read(access, contract, 0x20, vassal) ||
          !vassal || !Read(access, vassal, 0x18, vassal_id) ||
          !Resolve(access, environment.character_storage_slot,
                   environment.character_fallback_slot, vassal_id, 0x18,
                   round_trip) || round_trip != vassal) return false;
      if (std::find(characters.begin(), characters.end(), vassal_id) == characters.end())
        characters.push_back(vassal_id);
    }
  }
  std::sort(output.begin(), output.end());
  output.erase(std::unique(output.begin(), output.end()), output.end());
  return true;
}

void SortUnique(std::vector<std::int32_t> &ids) {
  std::sort(ids.begin(), ids.end());
  ids.erase(std::unique(ids.begin(), ids.end()), ids.end());
}

bool ReadSurrenderTitle(
    const PlayerFactionAlertsNativeEnvironmentV1 &environment,
    const PlayerFactionAlertsAccessV1 &access, std::int32_t title_id,
    game::FactionSurrenderTitleV1 &output) {
  output = {};
  output.title_id = title_id;
  std::vector<std::int32_t> visited;
  auto current_id = title_id;
  for (int depth = 0; depth < 8; ++depth) {
    if (std::find(visited.begin(), visited.end(), current_id) != visited.end())
      return false;
    visited.push_back(current_id);
    void *title = nullptr, *definition = nullptr;
    std::int32_t tier = -1, parent_id = -1;
    if (!Resolve(access, environment.landed_title_storage_slot,
                 environment.landed_title_fallback_slot, current_id, 0x10, title) ||
        !title || !Read(access, title, 0x48, definition) || !definition ||
        !Read(access, definition, 0x64, tier) || tier < 1 || tier > 5 ||
        !Read(access, title, 0x108, parent_id)) return false;
    if (depth == 0) {
      output.tier_raw = tier;
      if (parent_id > 0) output.de_jure_parent_title_id = parent_id;
      std::int32_t holder_id = -1;
      if (!Read(access, title, 0x128, holder_id)) return false;
      if (holder_id > 0) {
        void *holder = nullptr;
        if (!Resolve(access, environment.character_storage_slot,
                     environment.character_fallback_slot, holder_id, 0x18, holder) ||
            !holder) return false;
        output.holder_character_id = holder_id;
        std::vector<std::int32_t> lieges;
        for (int hop = 0; hop < 64; ++hop) {
          if (std::find(lieges.begin(), lieges.end(), holder_id) != lieges.end())
            return false;
          lieges.push_back(holder_id);
          void *liege = nullptr;
          std::int32_t liege_id = -1;
          if (!InvokeLiege(environment.immediate_liege, holder, liege) ||
              (liege && !Read(access, liege, 0x18, liege_id))) return false;
          // Native 1.20.0.3 RVA 0x28BFC70 returns self for a landed
          // independent character; campaign ReadLieges uses the same terminal.
          if (!liege || liege == holder || liege_id == -1) {
            output.top_liege_character_id = holder_id;
            break;
          }
          void *round_trip = nullptr;
          if (!Resolve(access, environment.character_storage_slot,
                       environment.character_fallback_slot, liege_id, 0x18,
                       round_trip) || round_trip != liege) return false;
          holder = liege; holder_id = liege_id;
        }
        if (!output.top_liege_character_id) return false;
      }
    }
    if (tier == 3) output.duchy_title_id = current_id;
    if (tier == 4) output.kingdom_title_id = current_id;
    if (parent_id <= 0) return true;
    current_id = parent_id;
  }
  return false;
}

bool ReadDeJureCountyIds(
    const PlayerFactionAlertsNativeEnvironmentV1 &environment,
    const PlayerFactionAlertsAccessV1 &access, std::int32_t title_id,
    std::vector<std::int32_t> &output) {
  output.clear();
  std::vector<std::int32_t> pending{title_id};
  for (std::size_t cursor = 0; cursor < pending.size(); ++cursor) {
    if (pending.size() > kMaximumMembers) return false;
    void *title = nullptr, *definition = nullptr;
    std::int32_t tier = -1;
    if (!Resolve(access, environment.landed_title_storage_slot,
                 environment.landed_title_fallback_slot, pending[cursor], 0x10,
                 title) || !title || !Read(access, title, 0x48, definition) ||
        !definition || !Read(access, definition, 0x64, tier)) return false;
    if (tier == 2) { output.push_back(pending[cursor]); continue; }
    if (tier < 2 || tier > 5) return false;
    std::vector<std::int32_t> children;
    if (!ReadIdSpan(access, title, 0x110, children)) return false;
    for (auto child : children) {
      void *object = nullptr;
      std::int32_t parent = -1;
      if (!Resolve(access, environment.landed_title_storage_slot,
                   environment.landed_title_fallback_slot, child, 0x10, object) ||
          !object || !Read(access, object, 0x108, parent) ||
          parent != pending[cursor] ||
          std::find(pending.begin(), pending.end(), child) != pending.end())
        return false;
      pending.push_back(child);
    }
  }
  SortUnique(output);
  return true;
}

bool InvokeSurrenderPredicates(
    const PlayerFactionAlertsNativeEnvironmentV1 &environment,
    const PlayerFactionAlertsAccessV1 &access, void *actor, void *leader,
    game::FactionSurrenderImpactV1 &output) noexcept {
  if (!environment.government || !environment.government_allows_mask ||
      !environment.state_faith_identifier || !environment.pair_relation || !leader)
    return false;
  std::int32_t identifier = -1;
  if (!Read(access, environment.state_faith_identifier, 0, identifier) ||
      identifier < 0) return false;
  void *government = nullptr, *relation = nullptr;
  std::uint64_t mask = 0;
#if defined(_MSC_VER)
  __try {
#endif
    government = environment.government(actor);
    mask = environment.government_allows_mask(&identifier);
    relation = environment.pair_relation(leader, actor);
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
  std::uint64_t features = 0;
  std::int32_t war_id = -1;
  if (!government || !mask || !Read(access, government, 0x40, features) ||
      !relation || !Read(access, relation, 0x20, war_id)) return false;
  output.government_allows_state_faith = (features & mask) == mask;
  if (war_id == -1) {
    output.leader_at_war_with_target = false;
    return true;
  }
  void *war = nullptr;
  std::uint8_t ended = 0;
  if (war_id <= 0 || !Resolve(access, environment.war_storage_slot,
                              environment.war_fallback_slot, war_id, 8, war) ||
      !war || !Read(access, war, 0x358, ended) || ended > 1) return false;
  output.leader_at_war_with_target = ended == 0;
  return true;
}

bool ReadSurrenderImpact(
    const PlayerFactionAlertsNativeEnvironmentV1 &environment,
    const PlayerFactionAlertsAccessV1 &access, void *actor,
    const game::PlayerTargetingFactionV1 &faction,
    game::FactionSurrenderImpactV1 &output) {
  output = {};
  output.unavailable_reason = "surrender_title_collection_unavailable";
  if (!faction.leader_character_id) return false;
  void *leader = nullptr;
  if (!Resolve(access, environment.character_storage_slot,
               environment.character_fallback_slot, *faction.leader_character_id,
               0x18, leader) || !leader) return false;
  if (!InvokeSurrenderPredicates(environment, access, actor, leader, output)) {
    output.unavailable_reason = "surrender_branch_predicates_unavailable";
    return false;
  }
  if (!ReadSubrealmCountyIds(environment, access, faction.target_character_id,
                            output.player_subrealm_county_title_ids)) return false;
  std::vector<std::int32_t> duchies, seized_ids, kingdom_ids;
  for (const auto county_id : faction.county_member_title_ids) {
    game::FactionSurrenderTitleV1 title;
    if (!ReadSurrenderTitle(environment, access, county_id, title) ||
        title.tier_raw != 2 || !title.duchy_title_id) return false;
    duchies.push_back(*title.duchy_title_id);
    output.member_counties.push_back(std::move(title));
  }
  SortUnique(duchies);
  for (const auto duchy_id : duchies) {
    game::FactionSurrenderTitleV1 title;
    std::vector<std::int32_t> counties;
    if (!ReadSurrenderTitle(environment, access, duchy_id, title) ||
        title.tier_raw != 3 ||
        !ReadDeJureCountyIds(environment, access, duchy_id, counties)) return false;
    if (title.kingdom_title_id) kingdom_ids.push_back(*title.kingdom_title_id);
    if (title.holder_character_id == faction.target_character_id)
      output.player_direct_title_loss_ids.push_back(duchy_id);
    output.seized_duchies.push_back(std::move(title));
    for (auto county_id : counties)
      if (std::binary_search(output.player_subrealm_county_title_ids.begin(),
                             output.player_subrealm_county_title_ids.end(), county_id))
        seized_ids.push_back(county_id);
  }
  SortUnique(seized_ids); SortUnique(kingdom_ids);
  for (const auto county_id : seized_ids) {
    game::FactionSurrenderTitleV1 title;
    if (!ReadSurrenderTitle(environment, access, county_id, title) ||
        title.tier_raw != 2 ||
        title.top_liege_character_id != faction.target_character_id) return false;
    if (title.holder_character_id == faction.target_character_id)
      output.player_direct_title_loss_ids.push_back(county_id);
    output.seized_counties.push_back(std::move(title));
  }
  for (const auto county_id : output.player_subrealm_county_title_ids) {
    game::FactionSurrenderTitleV1 title;
    if (!ReadSurrenderTitle(environment, access, county_id, title)) return false;
    if (title.holder_character_id == faction.target_character_id &&
        !std::binary_search(seized_ids.begin(), seized_ids.end(), county_id))
      output.player_remaining_direct_county_title_ids.push_back(county_id);
  }
  SortUnique(output.player_direct_title_loss_ids);
  for (const auto kingdom_id : kingdom_ids) {
    game::FactionSurrenderKingdomV1 kingdom;
    if (!ReadSurrenderTitle(environment, access, kingdom_id, kingdom.title) ||
        kingdom.title.tier_raw != 4 ||
        !ReadDeJureCountyIds(environment, access, kingdom_id,
                            kingdom.de_jure_county_title_ids)) return false;
    for (auto county_id : kingdom.de_jure_county_title_ids)
      if (std::binary_search(seized_ids.begin(), seized_ids.end(), county_id))
        kingdom.seized_county_title_ids.push_back(county_id);
    kingdom.strict_majority_from_seized_counties =
        kingdom.seized_county_title_ids.size() * 2 >
        kingdom.de_jure_county_title_ids.size();
    output.kingdoms.push_back(std::move(kingdom));
  }
  output.ordinary_branch_title_sets_ready = true;
  output.county_loss_complete = output.government_allows_state_faith == false &&
                               output.leader_at_war_with_target == false;
  if (output.government_allows_state_faith == true)
    output.unresolved_branches.push_back("state_faith_ruler_and_title_transfer");
  if (output.leader_at_war_with_target == true)
    output.unresolved_branches.push_back("leader_war_occupation_county_expansion");
  output.unresolved_branches.push_back("kingdom_receiver_capital_and_existing_direct_counties");
  output.status = "available";
  output.unavailable_reason.reset();
  return true;
}

bool ReadCountyExposures(
    const PlayerFactionAlertsNativeEnvironmentV1 &environment,
    const PlayerFactionAlertsAccessV1 &access, std::int32_t actor_id,
    SourceSample &output) {
  std::vector<std::int32_t> county_ids;
  if (!ReadSubrealmCountyIds(environment, access, actor_id, county_ids)) return false;
  for (const auto title_id : county_ids) {
    void *title = nullptr;
    if (!Resolve(access, environment.landed_title_storage_slot,
                 environment.landed_title_fallback_slot, title_id, 0x10,
                 title) || !title) return false;
    void *province = nullptr;
    std::uint32_t province_type = 0;
    void *county = nullptr;
    if (!InvokeLiege(environment.title_province, title, province) || !province ||
        !Read(access, province, 0x85C, province_type) || province_type != 0x50726F76U ||
        !Read(access, province, 0x848, county) || !county) return false;
    void *joined = nullptr;
    std::int32_t count = 0;
    if (!Read(access, county, 0x3B0, joined) ||
        !Read(access, county, 0x3BC, count) || count < 0 ||
        static_cast<std::size_t>(count) > kMaximumRows || (count && !joined))
      return false;
    std::vector<std::int32_t> ids;
    for (std::int32_t member = 0; member < count; ++member) {
      std::int32_t id = -1;
      if (!Read(access, joined, static_cast<std::size_t>(member) * 4, id) || id <= 0)
        return false;
      ids.push_back(id);
    }
    std::sort(ids.begin(), ids.end());
    if (std::adjacent_find(ids.begin(), ids.end()) != ids.end()) return false;
    // The stock action is existential per county. The stable first matching
    // faction is sufficient for the existing one-row-per-county projection.
    for (const auto id : ids) {
      game::PlayerTargetingFactionV1 row{};
      if (ReadEntitySample(environment, access, id, row) !=
          ReadFactionEntityResult12002::available) return false;
      if (row.faction_type_key != "populist_faction" ||
          row.target_character_id == actor_id ||
          row.power.raw <= row.power_threshold.raw) continue;
      ck3_11906::PlayerFactionCountyExposureSourceRowV1 exposure{};
      exposure.row.county_title_id = title_id;
      exposure.row.faction_id = id;
      exposure.row.faction_type_key = row.faction_type_key;
      exposure.row.target_character_id = row.target_character_id;
      exposure.row.power = row.power;
      exposure.row.power_threshold = row.power_threshold;
      exposure.county_identity_round_trip = true;
      exposure.faction_identity_round_trip = true;
      exposure.target_identity_round_trip = true;
      output.county_exposures.push_back(std::move(exposure));
      break;
    }
  }
  return true;
}

bool ReadSample(const PlayerFactionAlertsNativeEnvironmentV1 &environment,
                const PlayerFactionAlertsAccessV1 &access, std::int32_t actor_id,
                SourceSample &output) {
  output = {};
  void *actor = nullptr;
  if (!Resolve(access, environment.character_storage_slot,
               environment.character_fallback_slot, actor_id, 0x18, actor) ||
      !actor) return false;
  output.player_character_id = actor_id;
  output.player_identity_round_trip = true;
  std::vector<std::int32_t> ids;
  if (!ReadTargetingIds(access, actor, ids)) return false;
  output.targeting_faction_count = static_cast<std::int32_t>(ids.size());
  for (const auto id : ids) {
    ck3_11906::PlayerTargetingFactionSourceRowV1 source{};
    if (ReadEntitySample(environment, access, id, source.row) !=
            ReadFactionEntityResult12002::available ||
        source.row.target_character_id != actor_id) return false;
    source.faction_identity_round_trip = true;
    source.target_identity_round_trip = true;
    source.leader_identity_round_trip = source.row.leader_character_id.has_value();
    source.war_identity_round_trip = source.row.faction_war_id.has_value();
    source.member_identities_round_trip = true;
    if (environment.surrender_observations_12003 &&
        source.row.faction_type_key == "populist_faction") {
      game::FactionSurrenderImpactV1 impact;
      if (!ReadSurrenderImpact(environment, access, actor, source.row, impact)) {
        const auto reason = impact.unavailable_reason;
        const auto state_faith = impact.government_allows_state_faith;
        const auto pair_war = impact.leader_at_war_with_target;
        impact = {};
        impact.unavailable_reason = reason;
        impact.government_allows_state_faith = state_faith;
        impact.leader_at_war_with_target = pair_war;
      }
      source.row.surrender_impact = std::move(impact);
    }
    output.targeting_factions.push_back(std::move(source));
  }
  return ReadCountyExposures(environment, access, actor_id, output);
}

bool Admitted(const PlayerFactionAlertsNativeEnvironmentV1 &environment,
              const PlayerFactionAlertsAccessV1 &access) noexcept {
  return environment.exact_build_admitted &&
         (environment.module_base != 0 || environment.offline_fixture_function_overrides) &&
         access.is_main_thread && access.is_main_thread(access.context);
}

} // namespace

PlayerFactionAlertsNativeEnvironmentV1 BindPlayerFactionAlertsNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept {
  PlayerFactionAlertsNativeEnvironmentV1 environment{};
  environment.module_base = module_base;
  environment.exact_build_admitted = exact_build_admitted && module_base != 0;
  if (!environment.exact_build_admitted) return environment;
  environment.character_storage_slot = reinterpret_cast<void **>(
      module_base + kCampaignRootCharacterStorageSlotRva);
  environment.character_fallback_slot = reinterpret_cast<void **>(
      module_base + kCampaignRootCharacterFallbackSlotRva);
  environment.faction_storage_slot = reinterpret_cast<void **>(
      module_base + kFactionAlertsStorageSlotRva12002);
  environment.faction_fallback_slot = reinterpret_cast<void **>(
      module_base + kFactionAlertsFallbackSlotRva12002);
  environment.landed_title_storage_slot = reinterpret_cast<void **>(
      module_base + kCampaignRootLandedTitleStorageSlotRva);
  environment.landed_title_fallback_slot = reinterpret_cast<void **>(
      module_base + kCampaignRootLandedTitleFallbackSlotRva);
  environment.war_storage_slot = reinterpret_cast<void **>(module_base + 0x5D1DE58);
  environment.war_fallback_slot = reinterpret_cast<void **>(module_base + 0x5D1DE40);
  environment.vassal_contract_storage_slot = reinterpret_cast<void **>(module_base + 0x5D1EB88);
  environment.vassal_contract_fallback_slot = reinterpret_cast<void **>(module_base + 0x5D1EB40);
  environment.expected_faction_vtable = module_base + kFactionAlertsVtableRva12002;
  environment.immediate_liege = reinterpret_cast<NativeCampaignRootCharacterResolverV1>(
      module_base + kCampaignRootImmediateLiegeRva);
  environment.title_province = reinterpret_cast<NativeCampaignRootCharacterResolverV1>(
      module_base + 0x230F900);
  environment.character_is_human = reinterpret_cast<NativeFactionCharacterBool12002>(
      module_base + 0x2BAA710);
  environment.power = reinterpret_cast<NativeFactionFixedPoint12002>(
      module_base + 0x2601EF0);
  environment.power_threshold = reinterpret_cast<NativeFactionFixedPoint12002>(
      module_base + 0x26021A0);
  environment.discontent_per_month = reinterpret_cast<NativeFactionFixedPoint12002>(
      module_base + 0x2601B50);
  environment.months_until_max_discontent = reinterpret_cast<NativeFactionInt32_12002>(
      module_base + 0x2601C60);
  environment.at_war = reinterpret_cast<NativeFactionBool12002>(
      module_base + 0x2603AB0);
  environment.dangerous = reinterpret_cast<NativeFactionDanger12002>(
      module_base + 0x1D65BF0);
  return environment;
}

void BindCountyMemberObservations12003(
    PlayerFactionAlertsNativeEnvironmentV1 &environment) noexcept {
  environment.county_observations_12003 =
      environment.exact_build_admitted && environment.module_base != 0;
  environment.county_opinion = environment.county_observations_12003
      ? reinterpret_cast<NativeCountyOpinionInt32_12003>(environment.module_base + 0x24D4CB0)
      : nullptr;
  environment.county_faction_finals = BindCountyFactionFinals12003(
      environment.module_base, environment.county_observations_12003);
  environment.surrender_observations_12003 = environment.county_observations_12003;
  if (environment.surrender_observations_12003) {
    environment.government = reinterpret_cast<NativeCampaignRootCharacterResolverV1>(
        environment.module_base + 0x28C2E10);
    environment.pair_relation = reinterpret_cast<NativeFactionRelation12003>(
        environment.module_base + 0x28BC270);
    environment.government_allows_mask = reinterpret_cast<NativeGovernmentAllowsMask12003>(
        environment.module_base + 0x22CA060);
    environment.state_faith_identifier = reinterpret_cast<const std::int32_t *>(
        environment.module_base + 0x5C78AC0);
  }
}

bool ReadCountyMemberOpinion12003(
    const PlayerFactionAlertsNativeEnvironmentV1 &environment,
    const PlayerFactionAlertsAccessV1 &access, std::int32_t county_title_id,
    FactionCountyOpinionMaterial12003 &output) noexcept {
  output = {};
  try {
    if (!Admitted(environment, access) || county_title_id <= 0) return false;
    void *title = nullptr, *province = nullptr, *county = nullptr, *holder = nullptr;
    FactionCountyOpinionMaterial12003 row{};
    row.county_title_id = county_title_id;
    std::int32_t county_identity = -1;
    std::uint32_t province_tag = 0;
    if (!Resolve(access, environment.landed_title_storage_slot,
                 environment.landed_title_fallback_slot, county_title_id, 0x10, title) ||
        !title || !InvokeLiege(environment.title_province, title, province) || !province ||
        !Read(access, province, 0x10, row.capital_province_id) ||
        row.capital_province_id <= 0 ||
        !Read(access, province, 0x85C, province_tag) || province_tag != 0x50726F76U ||
        !Read(access, province, 0x848, county) || !county ||
        !Read(access, county, 0x18, county_identity) || county_identity != county_title_id ||
        !Read(access, title, 0x128, row.holder_character_id) ||
        !Resolve(access, environment.character_storage_slot,
                 environment.character_fallback_slot, row.holder_character_id, 0x18, holder) ||
        !holder) return false;
    output = row;
    // Signed whole-point final opinion: negative and zero are material.
    return InvokeInt(environment.county_opinion, county, output.county_opinion);
  } catch (...) { return false; }
}

ReadFactionEntityResult12002 ReadFactionEntityV1(
    const PlayerFactionAlertsNativeEnvironmentV1 &environment,
    const PlayerFactionAlertsAccessV1 &access, std::int32_t faction_id,
    game::PlayerTargetingFactionV1 &output) noexcept {
  output = {};
  try {
    if (!Admitted(environment, access) || faction_id <= 0)
      return ReadFactionEntityResult12002::unavailable;
    game::PlayerTargetingFactionV1 first{}, second{};
    const auto result = ReadEntitySample(environment, access, faction_id, first);
    const auto repeated = ReadEntitySample(environment, access, faction_id, second);
    if (result != repeated || first != second)
      return ReadFactionEntityResult12002::unavailable;
    if (result == ReadFactionEntityResult12002::available) output = std::move(first);
    return result;
  } catch (...) { return ReadFactionEntityResult12002::unavailable; }
}

game::ReadPlayerFactionAlertsResultV1 ReadPlayerFactionAlertsV1(
    const PlayerFactionAlertsNativeEnvironmentV1 &environment,
    const PlayerFactionAlertsAccessV1 &access,
    const PlayerFactionAlertsRequestV1 &request,
    game::PlayerFactionAlertsV1 &output) noexcept {
  output = {};
  output.snapshot_revision = request.expected_snapshot_revision;
  const auto reject = [&](Failure reason) {
    output = {};
    output.snapshot_revision = request.expected_snapshot_revision;
    output.unavailable_reason = reason;
    return Result::unavailable;
  };
  try {
    if (!request.expected_snapshot_revision) return reject(Failure::invalid_request);
    if (!environment.exact_build_admitted) return reject(Failure::exact_build_not_admitted);
    if (!Admitted(environment, access)) return reject(Failure::application_main_thread_required);
    game::PlayerFactionAlertsFrameV1 before{}, after{};
    if (!access.capture_frame || !access.capture_frame(access.context, before))
      return reject(Failure::frame_capture_failed);
    if (before.snapshot_revision != request.expected_snapshot_revision)
      return reject(Failure::snapshot_revision_mismatch);
    if (!before.paused || !before.map_ready || !before.has_played_character ||
        !before.played_character_alive || before.played_character_id <= 0)
      return reject(Failure::paused_player_unavailable);
    SourceSample first{}, second{};
    if (!ReadSample(environment, access, before.played_character_id, first) ||
        !ReadSample(environment, access, before.played_character_id, second))
      return reject(Failure::identity_round_trip_failed);
    if (first != second) return reject(Failure::native_sample_drift);
    if (!access.capture_frame(access.context, after) || before != after)
      return reject(Failure::same_frame_drift);
    return ck3_11906::ProjectPlayerFactionAlertsSourceSampleV1(first, before, output);
  } catch (...) { return reject(Failure::reader_exception); }
}

std::string SerializePlayerFactionAlertsV1(const game::PlayerFactionAlertsV1 &snapshot) {
  return ck3_11906::SerializePlayerFactionAlertsWithProvenanceV1(
      snapshot, kPlayerFactionAlertsV1GameVersion,
      kPlayerFactionAlertsV1ExecutableSha256, kPlayerFactionAlertsV1BackendId);
}

} // namespace xar::ck3_12002
