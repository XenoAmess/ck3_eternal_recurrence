#include <string>
#include <sstream>
#include <stdexcept>
#include <cstdint>
#include <vector>
#include <array>
#include <algorithm>
#include <locale>
#include "xar_bridge/family_marriage_outgoing_storage_12004.hpp"

namespace xar::bridge {

std::string SerializeFamilyOutgoingStorageGroup12004(
    const FamilyOutgoingStorageCopy12004& copy,
    std::uint32_t actual_played_actor) {

  // Validate actual_played_actor
  if (actual_played_actor == 0 || actual_played_actor == UINT32_MAX) {
    throw std::invalid_argument("invalid actual_played_actor");
  }
  if (copy.sender_id == 0 || copy.sender_id == UINT32_MAX) {
    throw std::invalid_argument("invalid sender_id");
  }

  // Validate copy fields
  if (copy.scanned_slots < 0 || copy.scanned_slots > 1000000) {
    throw std::invalid_argument("invalid scanned_slots");
  }
  if (copy.candidates.size() > 256) {
    throw std::invalid_argument("too many candidates");
  }
  if (copy.occupied_ids.size() > 1000000) {
    throw std::invalid_argument("too many occupied_ids");
  }

  // Validate occupied IDs: strictly increasing low24 slots, < capacity, no UINT32_MAX
  std::int32_t previous_slot = -1;
  for (std::uint32_t id : copy.occupied_ids) {
    if (id == UINT32_MAX) {
      throw std::invalid_argument("invalid occupied id sentinel");
    }
    std::uint32_t slot = id & 0x00FFFFFF;
    if (static_cast<std::int32_t>(slot) <= previous_slot) {
      throw std::invalid_argument("occupied ids not strictly increasing by slot");
    }
    if (static_cast<std::int32_t>(slot) >= copy.scanned_slots) {
      throw std::invalid_argument("occupied id slot exceeds capacity");
    }
    previous_slot = static_cast<std::int32_t>(slot);
  }

  // Validate candidates: distinct, contained in occupied, matching definition/sender
  std::vector<std::uint32_t> occupied_set = copy.occupied_ids;
  std::sort(occupied_set.begin(), occupied_set.end());
  std::vector<std::uint32_t> seen_candidate_ids;
  for (const auto& cand : copy.candidates) {
    if (cand.pending_full_id == UINT32_MAX) {
      throw std::invalid_argument("invalid candidate pending_full_id");
    }
    if (cand.definition_hash != copy.definition_hash) {
      throw std::invalid_argument("candidate definition mismatch");
    }
    if (cand.roles[0] != copy.sender_id) {
      throw std::invalid_argument("candidate sender mismatch");
    }
    if (std::find(seen_candidate_ids.begin(), seen_candidate_ids.end(), cand.pending_full_id) != seen_candidate_ids.end()) {
      throw std::invalid_argument("duplicate candidate id");
    }
    if (!std::binary_search(occupied_set.begin(), occupied_set.end(), cand.pending_full_id)) {
      throw std::invalid_argument("candidate not in occupied ids");
    }
    seen_candidate_ids.push_back(cand.pending_full_id);

    // Validate roles
    if (cand.roles[0] == 0 || cand.roles[0] == UINT32_MAX) {
      throw std::invalid_argument("invalid sender role");
    }
    for (std::size_t i = 1; i < cand.roles.size(); ++i) {
      if (cand.roles[i] != UINT32_MAX && (cand.roles[i] == 0)) {
        throw std::invalid_argument("invalid optional role zero");
      }
    }

    // Validate options
    if (cand.options.size() > 4096) {
      throw std::invalid_argument("too many options");
    }
    for (std::size_t i = 0; i < cand.options.size(); ++i) {
      if (cand.options[i].bank_byte > 1) {
        throw std::invalid_argument("invalid bank byte");
      }
    }
  }

  // Serialize
  std::ostringstream os;
  os.imbue(std::locale::classic());
  os << "{\"schema\":\"ck3-family-outgoing-storage-12004-v4\""
     << ",\"status\":\"available\""
     << ",\"source\":\"native_complete_outgoing_pending_storage_1.20.0.4\""
     << ",\"producer_scope\":\"complete_outgoing_storage\""
     << ",\"read_only\":true"
     << ",\"complete\":true"
     << ",\"passes\":2"
     << ",\"scanned_slots\":" << copy.scanned_slots
     << ",\"actor_id\":" << actual_played_actor
     << ",\"sender_character_id\":" << copy.sender_id
     << ",\"interaction_key\":\"arrange_marriage_interaction\""
     << ",\"definition_stable_hash\":" << copy.definition_hash
     << ",\"occupied_pending_full_ids\":[";

  for (std::size_t i = 0; i < copy.occupied_ids.size(); ++i) {
    if (i > 0) os << ",";
    os << copy.occupied_ids[i];
  }
  os << "],\"candidates\":[";

  for (std::size_t i = 0; i < copy.candidates.size(); ++i) {
    if (i > 0) os << ",";
    const auto& c = copy.candidates[i];
    os << "{\"pending_full_id\":" << c.pending_full_id
       << ",\"definition_stable_hash\":" << c.definition_hash
       << ",\"interaction_key\":\"arrange_marriage_interaction\""
       << ",\"route_kind\":" << c.route_kind
       << ",\"age_days\":" << c.age_days
       << ",\"ai_reply_cutoff_days\":" << c.ai_reply_cutoff_days
       << ",\"effective_roles\":{\"actor_id\":" << c.roles[0]
       << ",\"recipient_id\":";
    if (c.roles[1] == UINT32_MAX) os << "null"; else os << c.roles[1];
    os << ",\"secondary_actor_id\":";
    if (c.roles[2] == UINT32_MAX) os << "null"; else os << c.roles[2];
    os << ",\"secondary_recipient_id\":";
    if (c.roles[3] == UINT32_MAX) os << "null"; else os << c.roles[3];
    os << ",\"intermediary_id\":";
    if (c.roles[4] == UINT32_MAX) os << "null"; else os << c.roles[4];
    os << "},\"selected_option_rows\":[";
    for (std::size_t j = 0; j < c.options.size(); ++j) {
      if (j > 0) os << ",";
      os << "{\"declared_ordinal\":" << j
         << ",\"flag_full_u32\":" << c.options[j].flag
         << ",\"bank_value_u8\":" << static_cast<int>(c.options[j].bank_byte) << "}";
    }
    os << "]}";
  }
  os << "],\"unavailable_reason\":null}";

  return os.str();
}

} // namespace xar::bridge
