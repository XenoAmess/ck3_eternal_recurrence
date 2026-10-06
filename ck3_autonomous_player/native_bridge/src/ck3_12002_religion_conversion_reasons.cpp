#include "xar_bridge/ck3_12002_religion_conversion_reasons.hpp"

#include <cstring>
#include <utility>

namespace xar::ck3_12002::religion_conversion::reasons {
namespace {
template <typename T> T Load(const void *object, std::size_t at) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + at, sizeof(value));
  return value;
}
void *ResolveRite(const religion_conversion_rite::Bindings &b, std::uint32_t id) {
  if (!b.rite_storage_slot || !*b.rite_storage_slot || id == 0xFFFFFFFFU) return nullptr;
  const auto *storage = *b.rite_storage_slot;
  const auto index = id & 0xFFFFFFU;
  if (index >= Load<std::uint32_t>(storage, 0x2C)) return nullptr;
  const auto *slots = Load<const std::byte *>(storage, 0x20);
  if (!slots) return nullptr;
  auto *object = Load<void *>(slots, static_cast<std::size_t>(index) * 0x10 + 8);
  return object && Load<std::uint32_t>(object, 8) == id ? object : nullptr;
}
bool CopyNativeString(const NativeReasonString &native, std::string &text) {
  if (native.size > native.capacity) return false;
  const auto *data = native.capacity < 16 ? reinterpret_cast<const char *>(native.storage.data())
                                        : Load<const char *>(&native, 0);
  if (native.size && !data) return false;
  text = native.size ? std::string(data, static_cast<std::size_t>(native.size)) : std::string{};
  return true;
}
std::string Quote(std::string_view text) {
  std::string out = "\"";
  constexpr char hex[] = "0123456789abcdef";
  for (const auto character : text) {
    const auto byte = static_cast<unsigned char>(character);
    if (character == '"' || character == '\\') { out += '\\'; out += character; }
    else if (byte < 32) {
      out += "\\u00"; out += hex[byte >> 4]; out += hex[byte & 15];
    } else out += character;
  }
  return out + '"';
}
std::string Text(const std::optional<std::string> &text) {
  return text ? Quote(*text) : "null";
}
} // namespace

Bindings BindReligionConversionReasonsImage12002(std::uintptr_t base,
                                                std::string_view sha) noexcept {
  Bindings b{};
  b.rite = religion_conversion_rite::BindRiteConversionImage12002(base, sha);
  if (b.rite.enabled) b.destroy_string = reinterpret_cast<NativeStringDestroy>(base + kNativeStringDestroyRva);
  return b;
}

bool ReadPlayedReligionConversionReasons12002(const Bindings &b,
    std::uint32_t target_id, std::uint64_t epoch, Reasons &out) noexcept {
  out = {}; out.capture_epoch = epoch; out.target_rite_id = target_id;
  const auto &r = b.rite;
  if (!r.enabled || !r.module_base || !r.core.enabled || !r.validate ||
      !r.rite_storage_slot || !b.destroy_string) return false;
  CoreSnapshotPrefix frame{};
  if (!ReadCoreSnapshot(r.core, frame) || !frame.map_ready ||
      !frame.has_played_character || !frame.played_character_alive) {
    out.failure = Failure::played_character_unavailable; return false;
  }
  if (!frame.clock.paused) { out.failure = Failure::frame_not_paused; return false; }
  auto *character = ResolveCoreCharacter(r.core, frame.played_character_id);
  if (!character) { out.failure = Failure::played_character_unavailable; return false; }
  out.played_character_id = frame.played_character_id; out.date_raw = frame.clock.date_raw;
  const auto current_id = Load<std::uint32_t>(character, 0xB4);
  auto *current = ResolveRite(r, current_id);
  if (!current) { out.failure = Failure::current_rite_unavailable; return false; }
  auto *target = ResolveRite(r, target_id);
  if (!target) { out.failure = Failure::target_rite_unavailable; return false; }
  out.current_rite_id = current_id;
  const auto factory = r.read_only_value_factory ? r.read_only_value_factory
      : &religion_conversion_rite::MakeReadOnlyConvertRiteValue12002;
  auto command = factory(
      r.module_base, frame.played_character_id, target_id, true);
  NativeReasonString native{};
  const bool accepted = r.validate(&command, &native);
  std::string copied;
  const bool copied_ok = CopyNativeString(native, copied);
  // The DLL never frees the game's allocation through its own C++ allocator.
  // Match the real reflection caller after copying the byte string.
  b.destroy_string(&native);
  if (!copied_ok) { out.failure = Failure::native_text_unavailable; return false; }
  CoreSnapshotPrefix after{};
  if (!ReadCoreSnapshot(r.core, after) || !after.clock.paused || !after.map_ready ||
      !after.has_played_character || !after.played_character_alive ||
      after.played_character_id != frame.played_character_id ||
      after.clock.date_raw != frame.clock.date_raw ||
      ResolveCoreCharacter(r.core, frame.played_character_id) != character ||
      Load<std::uint32_t>(character, 0xB4) != current_id ||
      ResolveRite(r, current_id) != current || ResolveRite(r, target_id) != target) {
    out.failure = Failure::state_changed; return false;
  }
  out.native_paid_validator_passes = accepted;
  out.raw_native_text = copied;
  if (!copied.empty() && copied.back() != '\n') copied += '\n';
  out.ui_blocker_text = std::move(copied);
  out.available = true; out.failure = Failure::none; return true;
}

const char *ReligionConversionReasonsFailureKey(Failure failure) noexcept {
  switch (failure) {
  case Failure::none: return "none";
  case Failure::bindings_unavailable: return "bindings_unavailable";
  case Failure::played_character_unavailable: return "played_character_unavailable";
  case Failure::frame_not_paused: return "frame_not_paused";
  case Failure::current_rite_unavailable: return "current_rite_unavailable";
  case Failure::target_rite_unavailable: return "target_rite_unavailable";
  case Failure::native_text_unavailable: return "native_text_unavailable";
  case Failure::state_changed: return "state_changed";
  }
  return "bindings_unavailable";
}
std::string SerializeReligionConversionReasons12002(const Reasons &r) {
  return "{\"schema\":\"ck3_12002_religion_conversion_reasons_v1\","
      "\"game_version\":\"1.20.0.2\",\"executable_sha256\":" + Quote(kExecutableSha256) +
      ",\"read_only\":true,\"available\":" + (r.available ? "true" : "false") +
      ",\"unavailable_reason\":" + (r.available ? std::string{"null"} :
                                          Quote(ReligionConversionReasonsFailureKey(r.failure))) +
      ",\"capture_epoch\":" + std::to_string(r.capture_epoch) +
      ",\"date_raw\":" + std::to_string(r.date_raw) +
      ",\"played_character_id\":" + std::to_string(r.played_character_id) +
      ",\"current_rite_id\":" + std::to_string(r.current_rite_id) +
      ",\"target_rite_id\":" + std::to_string(r.target_rite_id) +
      ",\"native_paid_validator_passes\":" + (r.native_paid_validator_passes ?
          (*r.native_paid_validator_passes ? "true" : "false") : "null") +
      ",\"native_blocker_text_available\":" + (r.ui_blocker_text ? "true" : "false") +
      ",\"raw_native_text\":" + Text(r.raw_native_text) +
      ",\"ui_blocker_text\":" + Text(r.ui_blocker_text) +
      ",\"reason_codes_available\":false}";
}
} // namespace xar::ck3_12002::religion_conversion::reasons
