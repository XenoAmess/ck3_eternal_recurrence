#include "xar_bridge/raiktor_actual_truce_expiry_v1.hpp"

#include <windows.h>

#include <cstring>
#include <limits>
#include <string>

namespace xar::ck3_11906 {
namespace {

bool GuardedHasTruce(RaiktorHasTruceV1 function, void *owner,
                     void *toward, bool &output) noexcept {
  if (function == nullptr || owner == nullptr || toward == nullptr) {
    return false;
  }
#if defined(_MSC_VER)
  __try {
    output = function(owner, toward);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  output = function(owner, toward);
  return true;
#endif
}

bool GuardedEndDate(RaiktorGetTruceEndDateV1 function, void *owner,
                    void *toward, std::int32_t &output) noexcept {
  if (function == nullptr || owner == nullptr || toward == nullptr) {
    return false;
  }
#if defined(_MSC_VER)
  __try {
    const void *const value = function(owner, toward);
    if (value == nullptr) return false;
    std::memcpy(&output, value, sizeof(output));
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  const void *const value = function(owner, toward);
  if (value == nullptr) return false;
  std::memcpy(&output, value, sizeof(output));
  return true;
#endif
}

void AppendJsonString(std::string &output, std::string_view value) {
  output.push_back('"');
  for (const unsigned char character : value) {
    switch (character) {
    case '"': output += "\\\""; break;
    case '\\': output += "\\\\"; break;
    case '\n': output += "\\n"; break;
    case '\r': output += "\\r"; break;
    case '\t': output += "\\t"; break;
    default:
      if (character >= 0x20) output.push_back(static_cast<char>(character));
      break;
    }
  }
  output.push_back('"');
}

std::string_view StatusName(
    game::RaiktorActualTruceExpiryStatusV1 status) noexcept {
  switch (status) {
  case game::RaiktorActualTruceExpiryStatusV1::available:
    return "available";
  case game::RaiktorActualTruceExpiryStatusV1::no_truce:
    return "no_truce";
  case game::RaiktorActualTruceExpiryStatusV1::unavailable:
    return "unavailable";
  }
  return "unavailable";
}

} // namespace

game::ReadRaiktorActualTruceExpiryResultV1 ReadRaiktorActualTruceExpiryV1(
    const RaiktorActualTruceExpiryAccessV1 &access,
    std::int32_t toward_character_id,
    game::RaiktorActualTruceExpirySnapshotV1 &output) noexcept {
  output = {};
  output.toward_character_id = toward_character_id;
  if (!access.exact_build_admitted || access.read_snapshot == nullptr ||
      access.resolve_character == nullptr || access.has_truce == nullptr ||
      access.get_truce_end_date == nullptr || toward_character_id <= 0) {
    output.unavailable_reason = "exact_build_or_native_binding_unavailable";
    return game::ReadRaiktorActualTruceExpiryResultV1::unavailable;
  }

  game::Snapshot before{};
  if (!access.read_snapshot(access.context, before)) {
    output.unavailable_reason = "snapshot_read_failed";
    return game::ReadRaiktorActualTruceExpiryResultV1::unavailable;
  }
  output.current_date_raw = before.date_raw;
  output.owner_character_id = before.played_character_id;
  if (!before.paused || !before.map_ready) {
    output.unavailable_reason = "paused_map_required";
    return game::ReadRaiktorActualTruceExpiryResultV1::requires_paused;
  }
  if (!before.has_played_character || !before.played_character_alive ||
      before.played_character_id <= 0) {
    output.unavailable_reason = "living_played_character_required";
    return game::ReadRaiktorActualTruceExpiryResultV1::no_played_character;
  }

  void *const owner =
      access.resolve_character(access.context, before.played_character_id);
  void *const toward =
      access.resolve_character(access.context, toward_character_id);
  if (owner == nullptr) {
    output.unavailable_reason = "played_character_resolution_failed";
    return game::ReadRaiktorActualTruceExpiryResultV1::no_played_character;
  }
  if (toward == nullptr) {
    output.unavailable_reason = "toward_character_not_found";
    return game::ReadRaiktorActualTruceExpiryResultV1::
        toward_character_not_found;
  }

  bool has_before = false;
  bool has_after = false;
  std::int32_t expiry_before = 0;
  std::int32_t expiry_after = 0;
  if (!GuardedHasTruce(access.has_truce, owner, toward, has_before) ||
      (has_before &&
       !GuardedEndDate(access.get_truce_end_date, owner, toward,
                       expiry_before)) ||
      !GuardedHasTruce(access.has_truce, owner, toward, has_after) ||
      (has_after &&
       !GuardedEndDate(access.get_truce_end_date, owner, toward,
                       expiry_after))) {
    output.unavailable_reason = "native_truce_read_failed";
    return game::ReadRaiktorActualTruceExpiryResultV1::unavailable;
  }

  game::Snapshot after{};
  if (!access.read_snapshot(access.context, after) || after != before) {
    output.unavailable_reason = "snapshot_changed_during_query";
    return game::ReadRaiktorActualTruceExpiryResultV1::unstable_snapshot;
  }
  output.same_frame_stable = true;
  output.native_has_truce = has_before && has_after;
  if (!has_before && !has_after) {
    output.status = game::RaiktorActualTruceExpiryStatusV1::no_truce;
    output.unavailable_reason = "native_has_truce_false";
    return game::ReadRaiktorActualTruceExpiryResultV1::no_truce;
  }
  if (!has_before || !has_after || expiry_before != expiry_after ||
      expiry_before <= before.date_raw) {
    output.unavailable_reason = "native_truce_state_unstable_or_expired";
    return game::ReadRaiktorActualTruceExpiryResultV1::unstable_snapshot;
  }

  output.status = game::RaiktorActualTruceExpiryStatusV1::available;
  output.actual_expiry_observable = true;
  output.expiry_date_raw = expiry_before;
  output.readiness = true;
  return game::ReadRaiktorActualTruceExpiryResultV1::available;
}

std::string SerializeRaiktorActualTruceExpiryV1(
    const game::RaiktorActualTruceExpirySnapshotV1 &snapshot) {
  std::string result = "{\"schema_version\":1,\"backend_id\":";
  AppendJsonString(result, kRaiktorActualTruceExpiryV1BackendId);
  result += ",\"status\":";
  AppendJsonString(result, StatusName(snapshot.status));
  result += ",\"snapshot_revision\":" +
            std::to_string(snapshot.snapshot_revision);
  result += ",\"current_date_raw\":" +
            std::to_string(snapshot.current_date_raw);
  result += ",\"owner_character_id\":" +
            std::to_string(snapshot.owner_character_id);
  result += ",\"toward_character_id\":" +
            std::to_string(snapshot.toward_character_id);
  result += ",\"native_has_truce\":";
  result += snapshot.native_has_truce ? "true" : "false";
  result += ",\"actual_expiry_observable\":";
  result += snapshot.actual_expiry_observable ? "true" : "false";
  result += ",\"expiry_date_raw\":";
  if (snapshot.actual_expiry_observable) {
    result += std::to_string(snapshot.expiry_date_raw);
  } else {
    result += "null";
  }
  result += ",\"same_frame_stable\":";
  result += snapshot.same_frame_stable ? "true" : "false";
  result += ",\"readiness\":";
  result += snapshot.readiness ? "true" : "false";
  result += ",\"temporal_semantics\":";
  AppendJsonString(result, snapshot.temporal_semantics);
  result += ",\"unavailable_reason\":";
  if (snapshot.unavailable_reason.empty()) {
    result += "null";
  } else {
    AppendJsonString(result, snapshot.unavailable_reason);
  }
  result.push_back('}');
  return result;
}

} // namespace xar::ck3_11906
