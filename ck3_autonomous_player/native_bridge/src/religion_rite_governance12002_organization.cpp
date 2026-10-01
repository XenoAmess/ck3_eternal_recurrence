#include "xar_bridge/religion_rite_governance12002_organization.hpp"

#include <cstring>

namespace xar::ck3_12002::religion::organization {
namespace {
template <typename T> T Load(const void *object, std::size_t at) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + at, sizeof(value));
  return value;
}
Failure ReadOnce(const Bindings &b, std::uint64_t epoch, Counts &out) {
  CoreSnapshotPrefix frame{};
  if (!ReadCoreSnapshot(b.core, frame) || !frame.map_ready ||
      !frame.has_played_character || !frame.played_character_alive)
    return Failure::played_character_unavailable;
  if (!frame.clock.paused) return Failure::frame_not_paused;
  auto *character = ResolveCoreCharacter(b.core, frame.played_character_id);
  if (!character) return Failure::played_character_unavailable;
  out.capture_epoch = epoch;
  out.date_raw = frame.clock.date_raw;
  out.played_character_id = frame.played_character_id;
  const auto rite_id = Load<std::uint32_t>(character, kCharacterRiteIdOffset);
  if (rite_id != kAbsentReference) {
    auto *rite = b.character_rite(character);
    if (!rite || Load<std::uint32_t>(rite, kReferenceIdentityOffset) != rite_id)
      return Failure::rite_unavailable;
    out.rite_id = rite_id;
    out.county_count = b.county_count(rite);
    out.character_follower_count = b.character_follower_count(rite);
  }
  out.available = true;
  out.failure = Failure::none;
  return Failure::none;
}
template <typename T> std::string Number(const std::optional<T> &value) {
  return value ? std::to_string(*value) : "null";
}
} // namespace

Bindings BindOrganizationImage12002(std::uintptr_t base, std::string_view sha) noexcept {
  Bindings b{};
  if (!base || sha != kExecutableSha256) return b;
  b.enabled = true;
  b.core = BindCoreImage(base, sha);
  b.character_rite = reinterpret_cast<ObjectGetter>(base + kCharacterRiteRva);
  b.county_count = reinterpret_cast<CountGetter>(base + kCountyCountRva);
  b.character_follower_count = reinterpret_cast<CountGetter>(base + kCharacterFollowerCountRva);
  return b;
}
bool ReadPlayedOrganizationCounts12002(const Bindings &b, std::uint64_t epoch,
                                      Counts &output) noexcept {
  output = {};
  output.capture_epoch = epoch;
  if (!b.enabled || !b.core.enabled || !b.character_rite || !b.county_count ||
      !b.character_follower_count) return false;
  Counts first{}, second{};
  auto failure = ReadOnce(b, epoch, first);
  if (failure == Failure::none) failure = ReadOnce(b, epoch, second);
  if (failure == Failure::none &&
      (first.date_raw != second.date_raw || first.played_character_id != second.played_character_id ||
       first.rite_id != second.rite_id || first.county_count != second.county_count ||
       first.character_follower_count != second.character_follower_count))
    failure = Failure::state_changed;
  if (failure != Failure::none) { output.failure = failure; return false; }
  output = std::move(first);
  return true;
}
const char *OrganizationFailureKey(Failure f) noexcept {
  switch (f) {
  case Failure::none: return "none";
  case Failure::bindings_unavailable: return "bindings_unavailable";
  case Failure::played_character_unavailable: return "played_character_unavailable";
  case Failure::frame_not_paused: return "frame_not_paused";
  case Failure::rite_unavailable: return "rite_unavailable";
  case Failure::state_changed: return "state_changed";
  }
  return "bindings_unavailable";
}
std::string SerializePlayedOrganizationCounts12002(const Counts &c) {
  return "{\"schema\":\"ck3_12002_rite_organization_counts_v1\",\"game_version\":\"1.20.0.2\","
      "\"executable_sha256\":\"" + std::string(kExecutableSha256) + "\","
      "\"scope\":\"current_player_rite\",\"values\":\"native_cached_counts\","
      "\"available\":" + (c.available ? "true" : "false") +
      ",\"unavailable_reason\":" + (c.available ? std::string("null") :
                                          "\"" + std::string(OrganizationFailureKey(c.failure)) + "\"") +
      ",\"capture_epoch\":" + std::to_string(c.capture_epoch) +
      ",\"date_raw\":" + std::to_string(c.date_raw) +
      ",\"played_character_id\":" + std::to_string(c.played_character_id) +
      ",\"rite_id\":" + Number(c.rite_id) +
      ",\"county_count\":" + Number(c.county_count) +
      ",\"character_follower_count\":" + Number(c.character_follower_count) + "}";
}
} // namespace xar::ck3_12002::religion::organization
