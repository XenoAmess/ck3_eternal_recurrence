#include "xar_bridge/ck3_12002_religion_conversion_cost.hpp"

#include <cstring>

namespace xar::ck3_12002::religion::conversion_cost {
namespace {
template <typename T> T Load(const void *p, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(p) + offset, sizeof(value));
  return value;
}
bool Matches(const void *object, std::uint32_t id) noexcept {
  return object && id != kAbsentReference && Load<std::uint32_t>(object, 8) == id;
}
void *ResolveRite(const Bindings &b, std::uint32_t id) noexcept {
  if (id == kAbsentReference) return nullptr;
  const auto *db = *b.rite_database;
  if (!db) return nullptr;
  const auto index = id & 0xFFFFFFU;
  const auto count = Load<std::uint32_t>(db, 0x2C);
  const auto *slots = Load<const void *>(db, 0x20);
  if (index >= count || !slots) return nullptr;
  auto *rite = Load<void *>(slots, static_cast<std::size_t>(index) * 0x10 + 8);
  return Matches(rite, id) ? rite : nullptr;
}
Failure ReadOnce(const Bindings &b, std::uint32_t target_id, std::uint64_t epoch, Cost &out) {
  CoreSnapshotPrefix frame{};
  if (!ReadCoreSnapshot(b.core, frame) || !frame.map_ready ||
      !frame.has_played_character || !frame.played_character_alive)
    return Failure::played_character_unavailable;
  if (!frame.clock.paused) return Failure::frame_not_paused;
  auto *actor = ResolveCoreCharacter(b.core, frame.played_character_id);
  if (!actor) return Failure::played_character_unavailable;
  auto *rite = ResolveRite(b, target_id);
  if (!rite) return Failure::target_rite_unavailable;
  const auto target_faith_id = Load<std::uint32_t>(rite, kRiteFaithIdOffset);
  if (!Matches(b.rite_faith(rite), target_faith_id)) return Failure::target_faith_unavailable;
  const auto current_rite_id = Load<std::uint32_t>(actor, kCharacterRiteIdOffset);
  auto *current_rite = b.character_rite(actor);
  if (!Matches(current_rite, current_rite_id)) return Failure::current_religion_unavailable;
  const auto current_faith_id = Load<std::uint32_t>(current_rite, kRiteFaithIdOffset);
  if (!Matches(b.character_faith(actor), current_faith_id)) return Failure::current_religion_unavailable;

  NativeCostCommand command{};
  command.primary_vtable = b.command_vtable;
  command.secondary_vtable = b.command_secondary_vtable;
  command.actor_id = frame.played_character_id;
  command.target_rite_id = target_id;
  // Same entry and charge flag as FaithConversionWindow.CalcPietyCost.
  const auto points = b.final_piety_cost(&command, nullptr);
  const auto *resources = Load<const void *>(actor, kResourceExtensionOffset);
  const auto balance = resources ? Load<std::int64_t>(resources, kPietyBalanceOffset) : 0;
  out.capture_epoch = epoch;
  out.date_raw = frame.clock.date_raw;
  out.played_character_id = frame.played_character_id;
  out.target_rite_id = target_id;
  out.target_faith_id = target_faith_id;
  out.same_faith = current_faith_id == target_faith_id;
  out.piety_points = points;
  out.piety_cost_raw = static_cast<std::int64_t>(points) * Cost::raw_scale;
  out.actor_piety_raw = balance;
  out.can_afford_piety = balance >= *out.piety_cost_raw;
  if (ResolveCoreCharacter(b.core, frame.played_character_id) != actor ||
      ResolveRite(b, target_id) != rite) return Failure::state_changed;
  out.available = true;
  out.failure = Failure::none;
  return Failure::none;
}
bool Same(const Cost &a, const Cost &b) noexcept {
  return a.date_raw == b.date_raw && a.played_character_id == b.played_character_id &&
      a.target_rite_id == b.target_rite_id && a.target_faith_id == b.target_faith_id &&
      a.same_faith == b.same_faith && a.piety_points == b.piety_points &&
      a.actor_piety_raw == b.actor_piety_raw;
}
template <typename T> std::string Number(const std::optional<T> &v) {
  return v ? std::to_string(*v) : "null";
}
std::string Boolean(const std::optional<bool> &v) {
  return v ? (*v ? "true" : "false") : "null";
}
} // namespace

Bindings BindReligionConversionCostImage12002(std::uintptr_t base, std::string_view sha) noexcept {
  Bindings b{};
  if (!base || sha != kExecutableSha256) return b;
  b.enabled = true;
  b.core = BindCoreImage(base, sha);
  b.rite_database = reinterpret_cast<void **>(base + kRiteDatabaseGlobalRva);
  b.character_rite = reinterpret_cast<ObjectGetter>(base + kCharacterRiteRva);
  b.character_faith = reinterpret_cast<ObjectGetter>(base + kCharacterFaithRva);
  b.rite_faith = reinterpret_cast<ObjectGetter>(base + kRiteFaithRva);
  b.final_piety_cost = reinterpret_cast<FinalPietyCost>(base + kFinalPietyCostRva);
  b.command_vtable = base + kConversionCommandVtableRva;
  b.command_secondary_vtable = base + kConversionCommandSecondaryVtableRva;
  return b;
}
bool ReadPlayedReligionConversionCost12002(const Bindings &b, std::uint32_t target_id,
                                          std::uint64_t epoch, Cost &out) noexcept {
  out = {};
  out.capture_epoch = epoch;
  out.target_rite_id = target_id;
  if (!b.enabled || !b.core.enabled || !b.rite_database || !b.character_rite ||
      !b.character_faith || !b.rite_faith || !b.final_piety_cost ||
      !b.command_vtable || !b.command_secondary_vtable) return false;
  Cost first{}, second{};
  auto failure = ReadOnce(b, target_id, epoch, first);
  if (failure == Failure::none) failure = ReadOnce(b, target_id, epoch, second);
  if (failure == Failure::none && !Same(first, second)) failure = Failure::state_changed;
  if (failure != Failure::none) { out.failure = failure; return false; }
  out = first;
  return true;
}
const char *ConversionCostFailureKey(Failure f) noexcept {
  switch (f) {
  case Failure::none: return "none";
  case Failure::bindings_unavailable: return "bindings_unavailable";
  case Failure::played_character_unavailable: return "played_character_unavailable";
  case Failure::frame_not_paused: return "frame_not_paused";
  case Failure::current_religion_unavailable: return "current_religion_unavailable";
  case Failure::target_rite_unavailable: return "target_rite_unavailable";
  case Failure::target_faith_unavailable: return "target_faith_unavailable";
  case Failure::state_changed: return "state_changed";
  }
  return "bindings_unavailable";
}
std::string SerializeReligionConversionCost12002(const Cost &c) {
  return "{\"schema\":\"ck3_12002_religion_conversion_cost_v1\",\"available\":" +
      std::string(c.available ? "true" : "false") + ",\"unavailable_reason\":" +
      (c.available ? "null" : std::string("\"") + ConversionCostFailureKey(c.failure) + '"') +
      ",\"capture_epoch\":" + std::to_string(c.capture_epoch) +
      ",\"date_raw\":" + std::to_string(c.date_raw) +
      ",\"played_character_id\":" + std::to_string(c.played_character_id) +
      ",\"target_rite_id\":" + std::to_string(c.target_rite_id) +
      ",\"target_faith_id\":" + Number(c.target_faith_id) +
      ",\"same_faith\":" + Boolean(c.same_faith) +
      ",\"charge_piety\":true,\"piety_points\":" + Number(c.piety_points) +
      ",\"piety_cost_raw\":" + Number(c.piety_cost_raw) +
      ",\"actor_piety_raw\":" + Number(c.actor_piety_raw) +
      ",\"can_afford_piety\":" + Boolean(c.can_afford_piety) +
      ",\"raw_scale\":100000,\"final_conversion_legality_observed\":false}";
}
} // namespace xar::ck3_12002::religion::conversion_cost
