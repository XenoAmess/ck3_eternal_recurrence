#pragma once

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <optional>
#include <string>
#include <vector>

namespace xar::game {

struct KnightQueuedModelOccurrenceV1 {
  std::int32_t occurrence = 0;
  std::optional<bool> old_model_matches_installed;
  std::optional<bool> old_owner_matches_selected;
  std::optional<bool> paired_model_present;
  std::optional<bool> paired_model_matches_old;
  std::optional<bool> paired_model_matches_installed;
  std::optional<bool> paired_owner_matches_selected;
  bool operator==(const KnightQueuedModelOccurrenceV1 &) const = default;
};

// Current physical identities in one query, never a historical preparation stage.
struct KnightCurrentModelAssociationV1 {
  std::int32_t selected_character_id = -1;
  std::string current_status = "unavailable";
  std::optional<bool> carrier_present, installed_model_present, owner_present;
  std::optional<bool> owner_matches_selected, getter_receiver_matches_model_inline;
  std::optional<std::string> context_source;
  std::string current_reason = "selected_model_reads_unavailable";
  std::string queue_status = "unavailable";
  std::optional<std::int32_t> old_count_raw, pair_count_raw;
  std::vector<KnightQueuedModelOccurrenceV1> relevant_occurrences;
  std::optional<std::int32_t> first_unread_occurrence;
  std::string queue_reason = "modifier_manager_reads_unavailable";
  bool operator==(const KnightCurrentModelAssociationV1 &) const = default;
};

} // namespace xar::game

namespace xar::ck3_12002 {

using KnightModelReadMemoryV1 = bool (*)(void *, const void *, void *, std::size_t) noexcept;
struct KnightModelReadAccessV1 {
  void *context = nullptr;
  KnightModelReadMemoryV1 read = nullptr;
};

inline bool CopyKnightModelBytesV1(void *, const void *source, void *out,
                                   std::size_t bytes) noexcept {
  if (!source || !out) return false;
#if defined(_WIN32) && defined(_MSC_VER)
  __try { std::memcpy(out, source, bytes); }
  __except (1) { return false; }
#else
  std::memcpy(out, source, bytes);
#endif
  return true;
}

template<class T>
inline bool ReadKnightModelAtV1(const KnightModelReadAccessV1 &access,
                               std::uintptr_t address, std::size_t offset,
                               T &out) noexcept {
  if (!address) return false;
  const auto read = access.read ? access.read : CopyKnightModelBytesV1;
  return read(access.context, reinterpret_cast<const void *>(address + offset),
              &out, sizeof(out));
}

// Exact .3: selected1B0->carrier258, model8; *5C68C50->A0->CBD8 manager.
// No native preparation/sort/exchange helper is called. Present rows keep order.
inline game::KnightCurrentModelAssociationV1 ReadKnightCurrentModelAssociationV1(
    const void *selected, std::int32_t selected_id, const void *getter_receiver,
    const void *game_state_slot, KnightModelReadAccessV1 access = {}) {
  game::KnightCurrentModelAssociationV1 out{};
  out.selected_character_id = selected_id;
  const auto character = reinterpret_cast<std::uintptr_t>(selected);
  std::uintptr_t carrier = 0, installed = 0, owner = 0;
  bool installed_known = false;
  if (ReadKnightModelAtV1(access, character, 0x1B0, carrier)) {
    out.carrier_present = carrier != 0;
    if (!carrier || ReadKnightModelAtV1(access, carrier, 0x258, installed)) {
      installed_known = true;
      out.installed_model_present = installed != 0;
      if (!installed || ReadKnightModelAtV1(access, installed, 8, owner)) {
        if (installed) {
          out.owner_present = owner != 0;
          out.owner_matches_selected = owner == character;
          out.getter_receiver_matches_model_inline =
              reinterpret_cast<std::uintptr_t>(getter_receiver) == installed + 0x10;
        } else {
          out.getter_receiver_matches_model_inline = false;
        }
        out.context_source = installed && owner == character
            ? "model_inline" : "fallback_static";
        out.current_status = "available";
        out.current_reason.clear();
      }
    }
  }

  std::uintptr_t root = 0, world = 0, old_data = 0, pair_data = 0;
  if (!ReadKnightModelAtV1(access, reinterpret_cast<std::uintptr_t>(game_state_slot), 0, root) ||
      !root || !ReadKnightModelAtV1(access, root, 0xA0, world) || !world) return out;
  const auto manager = world + 0xCBD8;
  std::int32_t old_count = 0, pair_count = 0;
  const bool old_header = ReadKnightModelAtV1(access, manager, 0x98, old_data) &&
      ReadKnightModelAtV1(access, manager, 0xA4, old_count);
  if (old_header) out.old_count_raw = old_count;
  const bool pair_header = ReadKnightModelAtV1(access, manager, 0x78, pair_data) &&
      ReadKnightModelAtV1(access, manager, 0x84, pair_count);
  if (pair_header) out.pair_count_raw = pair_count;
  if (!old_header) return out;
  // This is a bounded diagnostic census, independent of the scalar/stat result.
  if (old_count < 0 || old_count > 4096 || (old_count && !old_data)) {
    out.queue_status = "partial";
    out.queue_reason = "old_queue_census_unreadable";
    return out;
  }
  const bool pair_usable = pair_header && pair_count >= 0 &&
      pair_count <= 4096 && (!pair_count || pair_data);
  out.queue_status = pair_usable ? "available" : "partial";
  out.queue_reason = pair_usable ? "" : "paired_queue_census_unreadable";
  for (std::int32_t i = 0; i != old_count; ++i) {
    std::uintptr_t old_model = 0, old_owner = 0;
    if (!ReadKnightModelAtV1(access, old_data, static_cast<std::size_t>(i) * 8, old_model) ||
        (old_model && !ReadKnightModelAtV1(access, old_model, 8, old_owner))) {
      out.queue_status = "partial";
      out.queue_reason = "old_queue_occurrence_unreadable";
      out.first_unread_occurrence = i;
      break;
    }
    if (!old_model || (old_owner != character &&
        !(installed_known && installed && old_model == installed))) continue;
    game::KnightQueuedModelOccurrenceV1 row{};
    row.occurrence = i;
    if (installed_known) row.old_model_matches_installed = installed && old_model == installed;
    row.old_owner_matches_selected = old_owner == character;
    if (pair_usable) {
      if (i >= pair_count) {
        row.paired_model_present = false;
      } else {
        std::uintptr_t paired = 0, paired_owner = 0;
        if (!ReadKnightModelAtV1(access, pair_data,
              static_cast<std::size_t>(i) * 16 + 8, paired)) {
          out.queue_status = "partial";
          out.queue_reason = "paired_model_pointer_unreadable";
        } else {
          row.paired_model_present = paired != 0;
          if (paired) {
            row.paired_model_matches_old = paired == old_model;
            if (installed_known)
              row.paired_model_matches_installed = installed && paired == installed;
            if (ReadKnightModelAtV1(access, paired, 8, paired_owner))
              row.paired_owner_matches_selected = paired_owner == character;
            else {
              out.queue_status = "partial";
              out.queue_reason = "paired_model_owner_unreadable";
            }
          }
        }
      }
    }
    out.relevant_occurrences.push_back(row);
  }
  return out;
}

inline std::string KnightModelMaybeBoolV1(const std::optional<bool> &value) {
  return value ? (*value ? "true" : "false") : "null";
}
inline std::string KnightModelMaybeIntV1(const std::optional<std::int32_t> &value) {
  return value ? std::to_string(*value) : "null";
}
inline std::string SerializeKnightCurrentModelAssociationV1(
    const game::KnightCurrentModelAssociationV1 &out) {
  std::string json = "{\"schema\":\"ck3_12003_knight_current_model_association_v1\","
      "\"read_scope\":\"frozen_current_character_values\",\"selected_character_id\":" +
      std::to_string(out.selected_character_id) + ",\"current_installed\":{\"status\":\"" +
      out.current_status + "\",\"carrier_present\":" + KnightModelMaybeBoolV1(out.carrier_present) +
      ",\"installed_model_present\":" + KnightModelMaybeBoolV1(out.installed_model_present) +
      ",\"owner_present\":" + KnightModelMaybeBoolV1(out.owner_present) +
      ",\"owner_matches_selected\":" + KnightModelMaybeBoolV1(out.owner_matches_selected) +
      ",\"getter_receiver_matches_model_inline\":" + KnightModelMaybeBoolV1(out.getter_receiver_matches_model_inline) +
      ",\"context_source\":" + (out.context_source ? "\"" + *out.context_source + "\"" : "null") +
      ",\"unavailable_reason\":" + (out.current_reason.empty() ? "null" : "\"" + out.current_reason + "\"") +
      "},\"queue_census\":{\"status\":\"" + out.queue_status +
      "\",\"old_count_raw\":" + KnightModelMaybeIntV1(out.old_count_raw) +
      ",\"pair_count_raw\":" + KnightModelMaybeIntV1(out.pair_count_raw) +
      ",\"first_unread_occurrence\":" + KnightModelMaybeIntV1(out.first_unread_occurrence) +
      ",\"relevant_occurrences\":[";
  for (std::size_t i = 0; i != out.relevant_occurrences.size(); ++i) {
    if (i) json += ',';
    const auto &row = out.relevant_occurrences[i];
    json += "{\"occurrence\":" + std::to_string(row.occurrence) +
        ",\"old_model_matches_installed\":" + KnightModelMaybeBoolV1(row.old_model_matches_installed) +
        ",\"old_owner_matches_selected\":" + KnightModelMaybeBoolV1(row.old_owner_matches_selected) +
        ",\"paired_model_present\":" + KnightModelMaybeBoolV1(row.paired_model_present) +
        ",\"paired_model_matches_old\":" + KnightModelMaybeBoolV1(row.paired_model_matches_old) +
        ",\"paired_model_matches_installed\":" + KnightModelMaybeBoolV1(row.paired_model_matches_installed) +
        ",\"paired_owner_matches_selected\":" + KnightModelMaybeBoolV1(row.paired_owner_matches_selected) + "}";
  }
  json += "],\"unavailable_reason\":" +
      (out.queue_reason.empty() ? "null" : "\"" + out.queue_reason + "\"") + "}}";
  return json;
}

} // namespace xar::ck3_12002
