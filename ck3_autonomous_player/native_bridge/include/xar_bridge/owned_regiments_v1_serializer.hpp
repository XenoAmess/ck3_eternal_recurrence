#pragma once

#include "xar_bridge/owned_regiments.hpp"

namespace xar::ck3_12003 {

inline const char *OwnedRegimentsStatusNameV1(
    OwnedRegimentsReadResultV1 status) noexcept {
  switch (status) {
  case OwnedRegimentsReadResultV1::available: return "available";
  case OwnedRegimentsReadResultV1::partial: return "partial";
  case OwnedRegimentsReadResultV1::unavailable: return "unavailable";
  }
  return "unavailable";
}

inline const char *OwnedRegimentTypeStatusNameV1(
    OwnedRegimentTypeStatusV1 status) noexcept {
  switch (status) {
  case OwnedRegimentTypeStatusV1::available: return "available";
  case OwnedRegimentTypeStatusV1::absent: return "absent";
  case OwnedRegimentTypeStatusV1::unavailable: return "unavailable";
  }
  return "unavailable";
}

// This appends only the nested object. The existing army-strength serializer
// owns whether the optional player-row field is present.
template <class Number, class JsonString>
inline void AppendOwnedRegimentsV1(
    std::string &result, const OwnedRegimentsSnapshotV1 &snapshot,
    Number number, JsonString append_json_string) {
  const auto append_optional_integer = [&](const std::optional<std::int32_t> &value) {
    result += value.has_value() ? number(*value) : "null";
  };
  const auto append_optional_string = [&](const std::string &value) {
    if (value.empty()) result += "null";
    else append_json_string(result, value);
  };

  result += "{\"schema\":\"ck3_12003_owned_regiments_v1\","
            "\"scope\":\"current-player-direct-owned-regiments\",\"status\":\"";
  result += OwnedRegimentsStatusNameV1(snapshot.status);
  result += "\",\"actor_character_id\":";
  result += number(snapshot.actor_character_id);
  result += ",\"source_count\":";
  append_optional_integer(snapshot.source_count);
  result += ",\"collection_complete\":";
  result += snapshot.collection_complete ? "true" : "false";
  result += ",\"regiments\":";
  if (snapshot.status == OwnedRegimentsReadResultV1::unavailable) {
    result += "null";
  } else {
    result += '[';
    bool first_record = true;
    for (const auto &regiment : snapshot.regiments) {
      if (!first_record) result += ',';
      first_record = false;
      result += "{\"persistent_regiment_id\":";
      result += number(regiment.persistent_regiment_id);
      result += ",\"available\":";
      result += regiment.available ? "true" : "false";
      result += ",\"owner_character_id\":";
      append_optional_integer(regiment.owner_character_id);
      result += ",\"native_capacity_raw\":";
      append_optional_integer(regiment.native_capacity_raw);
      result += ",\"maa_type_status\":\"";
      result += OwnedRegimentTypeStatusNameV1(regiment.type.status);
      result += "\",\"maa_type_key\":";
      if (regiment.type.status == OwnedRegimentTypeStatusV1::available) {
        append_json_string(result, regiment.type.maa_type_key);
      } else {
        result += "null";
      }
      result += ",\"siege_tier_observable\":";
      result += regiment.type.siege_tier.has_value() ? "true" : "false";
      result += ",\"siege_tier\":";
      append_optional_integer(regiment.type.siege_tier);
      result += ",\"composition_unavailable_reason\":";
      append_optional_string(regiment.type.unavailable_reason);
      result += ",\"chunks\":";
      if (!regiment.available) {
        result += "null";
      } else {
        result += '[';
        bool first_chunk = true;
        for (const auto &chunk : regiment.chunks) {
          if (!first_chunk) result += ',';
          first_chunk = false;
          result += "{\"chunk_index\":";
          result += number(chunk.chunk_index);
          result += ",\"maximum_soldiers\":";
          result += number(chunk.maximum_soldiers);
          result += ",\"current_soldiers\":";
          result += number(chunk.current_soldiers);
          result += ",\"persistent_regiment_id\":";
          result += number(chunk.persistent_regiment_id);
          result += ",\"native_chunk_index\":";
          result += number(chunk.native_chunk_index);
          result += ",\"army_regiment_id\":";
          result += number(chunk.army_regiment_id);
          result += ",\"pending_raw\":";
          result += number(static_cast<std::int32_t>(chunk.pending_raw));
          result += ",\"pending\":";
          result += chunk.pending_raw != 0 ? "true" : "false";
          result += ",\"state_raw\":";
          result += number(chunk.state_raw);
          result += '}';
        }
        result += ']';
      }
      result += ",\"unavailable_reason\":";
      append_optional_string(regiment.unavailable_reason);
      result += '}';
    }
    result += ']';
  }
  result += ",\"unavailable_reason\":";
  append_optional_string(snapshot.unavailable_reason);
  result += '}';
}

} // namespace xar::ck3_12003
