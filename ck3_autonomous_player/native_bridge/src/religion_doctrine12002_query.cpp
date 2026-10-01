#include "xar_bridge/religion_doctrine12002_query.hpp"

namespace xar::ck3_12002::religion::doctrine12002 {
namespace {
std::string Quote(std::string_view text) {
  constexpr char hex[] = "0123456789abcdef";
  std::string result = "\"";
  for (const unsigned char byte : text) {
    if (byte == '"' || byte == '\\') {
      result += '\\'; result += static_cast<char>(byte);
    } else if (byte < 0x20) {
      result += "\\u00"; result += hex[byte >> 4]; result += hex[byte & 15];
    } else result += static_cast<char>(byte);
  }
  return result + '"';
}
bool SameFrame(const CurrentDoctrineContext &value) noexcept {
  const auto &rite = value.current_rite;
  const auto &faith = value.faith_main_rite;
  const auto &parameters = value.boolean_parameters;
  const auto parameter_rite = parameters.current_rite
      ? std::optional<std::uint32_t>{parameters.current_rite->rite_id} : std::nullopt;
  const auto parameter_main_rite = parameters.faith_main_rite
      ? std::optional<std::uint32_t>{parameters.faith_main_rite->rite_id} : std::nullopt;
  return rite.capture_epoch == value.capture_epoch &&
      faith.capture_epoch == value.capture_epoch && parameters.capture_epoch == value.capture_epoch &&
      rite.played_character_id == faith.played_character_id &&
      static_cast<std::uint32_t>(rite.played_character_id) == parameters.played_character_id &&
      rite.date_raw == faith.date_raw && rite.date_raw == parameters.date_raw &&
      rite.rite_id == faith.rite_id && rite.faith_id == faith.faith_id &&
      rite.faith_id == parameters.faith_id && rite.rite_id == parameter_rite &&
      faith.main_rite_id == parameter_main_rite;
}
} // namespace

CurrentDoctrineBindings BindCurrentDoctrineImage12002(
    std::uintptr_t base, std::string_view sha) noexcept {
  return {religion::BindReligionContextImage12002(base, sha),
          BindTenetParameters12002(base, sha)};
}

bool ReadPlayedCurrentDoctrines12002(const CurrentDoctrineBindings &bindings,
    std::uint64_t epoch, CurrentDoctrineContext &output) noexcept {
  output = {};
  output.capture_epoch = epoch;
  try {
    CurrentDoctrineContext observed{};
    observed.capture_epoch = epoch;
    if (!ReadPlayedRiteDoctrines12002(bindings.context, epoch, observed.current_rite)) {
      output.unavailable_reason = "current_rite:" + observed.current_rite.unavailable_reason;
      return false;
    }
    if (!ReadPlayedFaithMainRiteDoctrines12002(bindings.context, epoch, observed.faith_main_rite)) {
      output.unavailable_reason = "faith_main_rite:" + observed.faith_main_rite.unavailable_reason;
      return false;
    }
    if (!ReadPlayedTenetParameters12002(bindings.context, bindings.parameters,
                                      epoch, observed.boolean_parameters)) {
      output.unavailable_reason = "boolean_parameters:" + observed.boolean_parameters.failure;
      return false;
    }
    if (!SameFrame(observed)) {
      output.unavailable_reason = "current_doctrine_scope_changed";
      return false;
    }
    observed.available = true;
    observed.unavailable_reason.clear();
    observed.date_raw = observed.current_rite.date_raw;
    observed.played_character_id = observed.current_rite.played_character_id;
    output = std::move(observed);
    return true;
  } catch (...) {
    output.unavailable_reason = "current_doctrine_native_read_exception";
    return false;
  }
}

std::string SerializePlayedCurrentDoctrines12002(const CurrentDoctrineContext &value) {
  return "{\"schema\":\"ck3_12002_current_doctrines_v1\",\"game_version\":\"1.20.0.2\","
      "\"executable_sha256\":" + Quote(kExecutableSha256) +
      ",\"available\":" + (value.available ? "true" : "false") +
      ",\"unavailable_reason\":" + (value.available ? "null" : Quote(value.unavailable_reason)) +
      ",\"capture_epoch\":" + std::to_string(value.capture_epoch) +
      ",\"date_raw\":" + std::to_string(value.date_raw) +
      ",\"played_character_id\":" + std::to_string(value.played_character_id) +
      ",\"current_rite\":" + SerializeRiteDoctrines12002(value.current_rite) +
      ",\"faith_main_rite\":" + SerializeFaithMainRiteDoctrines12002(value.faith_main_rite) +
      ",\"boolean_parameters\":" + SerializeTenetParameters12002(value.boolean_parameters) + "}";
}

} // namespace xar::ck3_12002::religion::doctrine12002
