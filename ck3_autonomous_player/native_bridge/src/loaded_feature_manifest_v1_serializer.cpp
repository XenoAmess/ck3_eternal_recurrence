#include "xar_bridge/loaded_feature_manifest_v1.hpp"

#include <algorithm>
#include <array>
#include <charconv>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {
namespace {

std::string Number(std::uint64_t value) {
  std::array<char, 32> buffer{};
  const auto result =
      std::to_chars(buffer.data(), buffer.data() + buffer.size(), value);
  return result.ec == std::errc{}
             ? std::string(buffer.data(), result.ptr)
             : std::string{};
}

std::string SignedNumber(std::int64_t value) {
  std::array<char, 32> buffer{};
  const auto result =
      std::to_chars(buffer.data(), buffer.data() + buffer.size(), value);
  return result.ec == std::errc{}
             ? std::string(buffer.data(), result.ptr)
             : std::string{};
}

void AppendJsonString(std::string &output, std::string_view value) {
  constexpr char hex[] = "0123456789ABCDEF";
  output.push_back('"');
  for (const unsigned char character : value) {
    if (character == '"' || character == '\\') {
      output.push_back('\\');
      output.push_back(static_cast<char>(character));
    } else if (character < 0x20U) {
      output += "\\u00";
      output.push_back(hex[(character >> 4U) & 0x0FU]);
      output.push_back(hex[character & 0x0FU]);
    } else {
      output.push_back(static_cast<char>(character));
    }
  }
  output.push_back('"');
}

bool Utf8BytewiseLess(const std::string &left,
                      const std::string &right) noexcept {
  return std::lexicographical_compare(
      left.begin(), left.end(), right.begin(), right.end(),
      [](char left_byte, char right_byte) noexcept {
        return static_cast<unsigned char>(left_byte) <
               static_cast<unsigned char>(right_byte);
      });
}

bool ValidAvailable(const game::LoadedFeatureManifestV1 &manifest) {
  if (!manifest.unavailable_reason.empty() ||
      manifest.effective_feature_flags.status !=
          game::LoadedFeatureComponentStatusV1::available ||
      !manifest.effective_feature_flags.unavailable_reason.empty() ||
      !manifest.effective_feature_flags.native_count.has_value() ||
      manifest.effective_feature_flags.native_count.value() !=
          static_cast<std::int32_t>(kLoadedFeatureNativeCount) ||
      manifest.effective_feature_flags.items.size() !=
          kLoadedFeatureNativeCount ||
      manifest.script_dlc_keys.status !=
          game::LoadedFeatureComponentStatusV1::available ||
      !manifest.script_dlc_keys.unavailable_reason.empty() ||
      !manifest.script_dlc_keys.enumerated_count.has_value() ||
      manifest.script_dlc_keys.enumerated_count.value() !=
          static_cast<std::int32_t>(manifest.script_dlc_keys.keys.size()) ||
      !std::is_sorted(manifest.script_dlc_keys.keys.begin(),
                      manifest.script_dlc_keys.keys.end(),
                      Utf8BytewiseLess) ||
      std::adjacent_find(manifest.script_dlc_keys.keys.begin(),
                         manifest.script_dlc_keys.keys.end()) !=
          manifest.script_dlc_keys.keys.end() ||
      !manifest.readiness.effective_feature_flags_ready ||
      !manifest.readiness.script_dlc_keys_ready ||
      manifest.readiness.entitlements_ready ||
      !manifest.readiness.same_frame_ready ||
      !manifest.readiness.actionable_ready) {
    return false;
  }
  for (std::size_t index = 0; index < kLoadedFeatureNativeCount; ++index) {
    const auto &item = manifest.effective_feature_flags.items[index];
    if (item.native_index != static_cast<std::int32_t>(index) ||
        item.cstring_id == 0 || item.key.empty()) {
      return false;
    }
  }
  return true;
}

bool ValidUnavailable(const game::LoadedFeatureManifestV1 &manifest) {
  const auto &features = manifest.effective_feature_flags;
  const auto &dlcs = manifest.script_dlc_keys;
  return !manifest.unavailable_reason.empty() &&
         features.status ==
             game::LoadedFeatureComponentStatusV1::unavailable &&
         !features.native_count.has_value() && features.items.empty() &&
         features.unavailable_reason == manifest.unavailable_reason &&
         dlcs.status == game::LoadedFeatureComponentStatusV1::unavailable &&
         !dlcs.enumerated_count.has_value() && dlcs.keys.empty() &&
         dlcs.unavailable_reason == manifest.unavailable_reason &&
         !manifest.readiness.effective_feature_flags_ready &&
         !manifest.readiness.script_dlc_keys_ready &&
         !manifest.readiness.entitlements_ready &&
         !manifest.readiness.same_frame_ready &&
         !manifest.readiness.actionable_ready;
}

} // namespace

std::string SerializeLoadedFeatureManifestV1(
    const game::LoadedFeatureManifestV1 &manifest) {
  if (manifest.snapshot_revision == 0) {
    return {};
  }
  const bool available =
      manifest.status == game::LoadedFeatureManifestStatusV1::available;
  if ((available && !ValidAvailable(manifest)) ||
      (!available && !ValidUnavailable(manifest))) {
    return {};
  }

  std::string output;
  output.reserve(8'192);
  output +=
      "{\"schema\":\"loaded-feature-manifest-v1\","
      "\"schema_version\":1,\"status\":";
  AppendJsonString(output, available ? "available" : "unavailable");
  output += ",\"snapshot_revision\":";
  output += Number(manifest.snapshot_revision);
  output += ",\"date_raw\":";
  output += SignedNumber(manifest.date_raw);
  output += ",\"unavailable_reason\":";
  if (available) {
    output += "null";
  } else {
    AppendJsonString(output, manifest.unavailable_reason);
  }
  output +=
      ",\"build\":{\"version\":\"1.19.0.6\","
      "\"exe_sha256\":"
      "\"2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86\"},"
      "\"effective_feature_flags\":{\"status\":";
  AppendJsonString(output, available ? "available" : "unavailable");
  output += ",\"unavailable_reason\":";
  if (available) {
    output += "null,\"native_count\":44,\"items\":[";
    for (std::size_t index = 0;
         index < manifest.effective_feature_flags.items.size(); ++index) {
      if (index != 0) {
        output.push_back(',');
      }
      const auto &item = manifest.effective_feature_flags.items[index];
      output += "{\"native_index\":";
      output += SignedNumber(item.native_index);
      output += ",\"cstring_id\":";
      output += Number(item.cstring_id);
      output += ",\"key\":";
      AppendJsonString(output, item.key);
      output += ",\"enabled\":";
      output += item.enabled ? "true" : "false";
      output.push_back('}');
    }
    output.push_back(']');
  } else {
    AppendJsonString(output,
                     manifest.effective_feature_flags.unavailable_reason);
    output += ",\"native_count\":null,\"items\":null";
  }
  output += "},\"script_dlc_keys\":{\"status\":";
  AppendJsonString(output, available ? "available" : "unavailable");
  output += ",\"unavailable_reason\":";
  if (available) {
    output += "null,\"enumerated_count\":";
    output += SignedNumber(
        manifest.script_dlc_keys.enumerated_count.value());
    output += ",\"keys\":[";
    for (std::size_t index = 0;
         index < manifest.script_dlc_keys.keys.size(); ++index) {
      if (index != 0) {
        output.push_back(',');
      }
      AppendJsonString(output, manifest.script_dlc_keys.keys[index]);
    }
    output.push_back(']');
  } else {
    AppendJsonString(output, manifest.script_dlc_keys.unavailable_reason);
    output += ",\"enumerated_count\":null,\"keys\":null";
  }
  output +=
      "},\"entitlements\":{\"status\":\"unavailable\","
      "\"unavailable_reason\":\"store_verdict_provenance_unclosed\","
      "\"items\":null},\"readiness\":{"
      "\"effective_feature_flags_ready\":";
  output += manifest.readiness.effective_feature_flags_ready ? "true" : "false";
  output += ",\"script_dlc_keys_ready\":";
  output += manifest.readiness.script_dlc_keys_ready ? "true" : "false";
  output += ",\"entitlements_ready\":";
  output += manifest.readiness.entitlements_ready ? "true" : "false";
  output += ",\"same_frame_ready\":";
  output += manifest.readiness.same_frame_ready ? "true" : "false";
  output += ",\"actionable_ready\":";
  output += manifest.readiness.actionable_ready ? "true" : "false";
  output +=
      "},\"provenance\":{\"feature_root_slot_rva\":\"0x576CC68\","
      "\"feature_bitset_rva\":\"root+0x2B0\","
      "\"feature_enum_table_rva\":\"0x42F7850..0x42F7900\","
      "\"script_dlc_set_rva\":\"0x5762590\","
      "\"backend_id\":\"ck3-1.19.0.6-native-loaded-feature-manifest-v1\"}}";
  return output;
}

} // namespace xar::ck3_11906
