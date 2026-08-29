#include "xar_bridge/title_map_navigation_v1_serializer.hpp"

#include <algorithm>
#include <array>
#include <bit>
#include <charconv>
#include <cmath>
#include <cstdint>
#include <limits>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {
namespace {

template <typename Value>
bool AppendInteger(std::string &output, Value value) {
  std::array<char, 32> buffer{};
  const auto encoded =
      std::to_chars(buffer.data(), buffer.data() + buffer.size(), value);
  if (encoded.ec != std::errc{}) {
    return false;
  }
  output.append(buffer.data(), encoded.ptr);
  return true;
}

bool AppendFloat(std::string &output, float value) {
  if (!std::isfinite(value)) {
    return false;
  }
  if (value == 0.0F) {
    output += std::signbit(value) ? "-0.0" : "0.0";
    return true;
  }
  std::array<char, 64> buffer{};
  const auto encoded = std::to_chars(
      buffer.data(), buffer.data() + buffer.size(), value,
      std::chars_format::general, std::numeric_limits<float>::max_digits10);
  if (encoded.ec != std::errc{}) {
    return false;
  }
  output.append(buffer.data(), encoded.ptr);
  return true;
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

bool SameFloat(float left, float right) noexcept {
  return std::bit_cast<std::uint32_t>(left) ==
         std::bit_cast<std::uint32_t>(right);
}

template <std::size_t Size>
bool SameFloatArray(const std::array<float, Size> &left,
                    const std::array<float, Size> &right) noexcept {
  for (std::size_t index = 0; index < Size; ++index) {
    if (!SameFloat(left[index], right[index])) {
      return false;
    }
  }
  return true;
}

template <std::size_t Size>
bool AllFinite(const std::array<float, Size> &values) noexcept {
  return std::all_of(values.begin(), values.end(),
                     [](float value) noexcept { return std::isfinite(value); });
}

std::int32_t WrapAdd(std::int32_t left, std::int32_t right) noexcept {
  return std::bit_cast<std::int32_t>(
      static_cast<std::uint32_t>(left) + static_cast<std::uint32_t>(right));
}

std::int32_t WrapSubtract(std::int32_t left,
                          std::int32_t right) noexcept {
  return std::bit_cast<std::int32_t>(
      static_cast<std::uint32_t>(left) - static_cast<std::uint32_t>(right));
}

std::array<float, 3> ExpectedPosition(
    const game::TitleMapNavigationCameraEvidenceV1 &camera) noexcept {
  const auto center_x = WrapAdd(camera.bounds_extent[0],
                                camera.bounds_extent[2]) /
                        2;
  const auto center_z = WrapAdd(camera.bounds_extent[1],
                                camera.bounds_extent[3]) /
                        2;
  return {static_cast<float>(
              WrapSubtract(center_x, camera.map_x_adjustment)),
          0.0F, static_cast<float>(center_z)};
}

bool ValidTier(const game::LandedTitleMapAnchorV1 &title) noexcept {
  switch (title.tier_raw) {
  case 1:
    return title.tier_key == "barony";
  case 2:
    return title.tier_key == "county";
  case 3:
    return title.tier_key == "duchy";
  case 4:
    return title.tier_key == "kingdom";
  case 5:
    return title.tier_key == "empire";
  case 6:
    return title.tier_key == "hegemony";
  default:
    return false;
  }
}

bool ValidSuccess(const game::TitleMapNavigationCommandV1 &command,
                  std::uint64_t dispatch_sequence) noexcept {
  using Status = game::TitleMapNavigationCommandStatusV1;
  const bool centered = command.status == Status::centered;
  const bool already = command.status == Status::already_centered;
  if ((!centered && !already) || !command.initialized ||
      command.binding.snapshot_revision == 0 ||
      command.title.key != command.request.title_key ||
      !IsCanonicalLandedTitleKeyV1(command.title.key) ||
      command.title.title_id <= 0 || !ValidTier(command.title) ||
      (command.title.capital_province_id.has_value() &&
       *command.title.capital_province_id <= 0) ||
      command.camera.bounds_extent[0] > command.camera.bounds_extent[2] ||
      command.camera.bounds_extent[1] > command.camera.bounds_extent[3] ||
      command.camera.zoom_index < 0 ||
      !std::isfinite(command.camera.expected_zoom_value) ||
      !AllFinite(command.camera.expected_position_xyz) ||
      !AllFinite(command.camera.current_state) ||
      !AllFinite(command.camera.target_state) ||
      !command.camera.settled || command.camera.target_write_blocked ||
      !SameFloatArray(command.camera.current_state,
                      command.camera.target_state) ||
      !SameFloat(command.camera.current_state[3],
                 command.camera.expected_zoom_value) ||
      !SameFloat(command.camera.target_state[3],
                 command.camera.expected_zoom_value) ||
      !SameFloatArray(command.camera.expected_position_xyz,
                      ExpectedPosition(command.camera))) {
    return false;
  }
  const std::array<float, 3> target_position{
      command.camera.target_state[0], command.camera.target_state[1],
      command.camera.target_state[2]};
  if (!SameFloatArray(target_position,
                      command.camera.expected_position_xyz)) {
    return false;
  }
  return centered ? command.dispatched && dispatch_sequence > 0
                  : !command.dispatched && dispatch_sequence == 0;
}

template <std::size_t Size>
bool AppendFloatArray(std::string &output,
                      const std::array<float, Size> &values) {
  output.push_back('[');
  for (std::size_t index = 0; index < Size; ++index) {
    if (index != 0) {
      output.push_back(',');
    }
    if (!AppendFloat(output, values[index])) {
      return false;
    }
  }
  output.push_back(']');
  return true;
}

} // namespace

std::string SerializeTitleMapNavigationResultV1(
    const game::TitleMapNavigationCommandV1 &command,
    std::uint64_t dispatch_ticket_sequence) {
  if (!ValidSuccess(command, dispatch_ticket_sequence)) {
    return {};
  }
  const bool centered =
      command.status == game::TitleMapNavigationCommandStatusV1::centered;
  const auto status = centered ? "centered" : "already_centered";

  std::string output;
  output.reserve(1'500);
  output += "{\"schema_version\":1,\"step\":\"";
  output += kTitleMapNavigationV1Step;
  output += "\",\"accepted\":true,\"status\":\"";
  output += status;
  output += "\",\"title\":{\"key\":";
  AppendJsonString(output, command.title.key);
  output += ",\"title_id\":";
  if (!AppendInteger(output, command.title.title_id)) {
    return {};
  }
  output += ",\"tier_raw\":";
  if (!AppendInteger(output, command.title.tier_raw)) {
    return {};
  }
  output += ",\"tier_key\":";
  AppendJsonString(output, command.title.tier_key);
  output += ",\"anchor_kind\":\"title_bounds_center\",";
  output += "\"capital_province_id\":";
  if (command.title.capital_province_id.has_value()) {
    if (!AppendInteger(output, *command.title.capital_province_id)) {
      return {};
    }
  } else {
    output += "null";
  }
  output += ",\"bounds_extent\":[";
  for (std::size_t index = 0; index < command.camera.bounds_extent.size();
       ++index) {
    if (index != 0) {
      output.push_back(',');
    }
    if (!AppendInteger(output, command.camera.bounds_extent[index])) {
      return {};
    }
  }
  output += "],\"map_x_adjustment\":";
  if (!AppendInteger(output, command.camera.map_x_adjustment)) {
    return {};
  }
  output += "},\"binding\":{\"snapshot_id\":\"native:";
  if (!AppendInteger(output, command.binding.snapshot_revision)) {
    return {};
  }
  output += "\",\"revision\":";
  if (!AppendInteger(output, command.binding.snapshot_revision)) {
    return {};
  }
  output += ",\"native_revision\":";
  if (!AppendInteger(output, command.binding.snapshot_revision)) {
    return {};
  }
  output += ",\"date_raw\":";
  if (!AppendInteger(output, command.binding.date_raw)) {
    return {};
  }
  output += "},\"native_action_ack\":{\"sequence\":";
  if (centered) {
    if (!AppendInteger(output, dispatch_ticket_sequence)) {
      return {};
    }
    output += ",\"status\":\"dispatched\"}";
  } else {
    output += "null,\"status\":\"not_needed\"}";
  }
  output += ",\"camera_center\":{\"status\":\"";
  output += status;
  output += "\",\"postcondition_verified\":true,";
  output += "\"expected_position_xyz\":";
  if (!AppendFloatArray(output, command.camera.expected_position_xyz)) {
    return {};
  }
  output += ",\"current_state\":";
  if (!AppendFloatArray(output, command.camera.current_state)) {
    return {};
  }
  output += ",\"target_state\":";
  if (!AppendFloatArray(output, command.camera.target_state)) {
    return {};
  }
  output += ",\"zoom_index\":";
  if (!AppendInteger(output, command.camera.zoom_index)) {
    return {};
  }
  output += ",\"expected_zoom_value\":";
  if (!AppendFloat(output, command.camera.expected_zoom_value)) {
    return {};
  }
  output += ",\"settled\":true,\"target_write_blocked\":false,";
  output += "\"completion_predicate\":\"";
  output += kTitleMapNavigationV1CompletionPredicate;
  output += "\"},\"source\":{\"game_version\":\"";
  output += kTitleMapNavigationV1GameVersion;
  output += "\",\"executable_sha256\":\"";
  output += kTitleMapNavigationV1ExecutableSha256;
  output += "\",\"backend_id\":\"";
  output += kTitleMapNavigationV1BackendId;
  output += "\"}}";
  return output;
}

} // namespace xar::ck3_11906
