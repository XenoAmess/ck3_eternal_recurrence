#include "xar_bridge/conversion_outcome12002_state.hpp"

#include <cstring>
#include <utility>

namespace xar::ck3_12002::religion_conversion::outcome::state {
namespace {
namespace g = religion::conversion_gates;
template <typename T> T Load(const void *p, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(p) + offset, sizeof(value));
  return value;
}
void *ResolveRite(const Bindings &b, std::uint32_t ref) noexcept {
  if (ref == religion::kAbsentReference || !b.rite_storage_slot || !*b.rite_storage_slot) return nullptr;
  auto *storage = *b.rite_storage_slot;
  const auto index = ref & 0xFFFFFFU;
  if (index >= Load<std::uint32_t>(storage, 0x2C)) return nullptr;
  auto *rows = Load<const void *>(storage, 0x20);
  if (!rows) return nullptr;
  auto *rite = Load<void *>(rows, static_cast<std::size_t>(index) * 0x10 + 0x08);
  return rite && Load<std::uint32_t>(rite, religion::kReferenceIdentityOffset) == ref ? rite : nullptr;
}
bool SameCore(const CoreSnapshotPrefix &a, const CoreSnapshotPrefix &b) noexcept {
  return a.clock.date_raw == b.clock.date_raw && a.clock.speed == b.clock.speed &&
      a.clock.paused == b.clock.paused && a.local_player_id == b.local_player_id &&
      a.map_ready == b.map_ready && a.has_played_character == b.has_played_character &&
      a.played_character_id == b.played_character_id && a.played_character_alive == b.played_character_alive;
}

Failure ReadFlags(const Bindings &b, void *actor, Context &out) {
  if (!b.atom_pool || !Load<const void *>(b.atom_pool, 0x10) ||
      Load<std::int32_t>(b.atom_pool, 0x1C) < 0) return Failure::flag_pool_unavailable;
  const char *keys[]{kRecentConversionFlag, kConversionMemoryFlag, kNarrativeRecentConvertFlag};
  FlagObservation *observations[]{&out.faith_conversion_recently_converted,
      &out.conversion_memory_recently_created, &out.recent_convert};
  std::uint32_t atoms[3]{};
  bool any_registered = false;
  for (std::size_t i = 0; i < 3; ++i) {
    const NativeStringView key{keys[i], static_cast<std::int32_t>(std::strlen(keys[i])), 1, {}};
    atoms[i] = religion::kAbsentReference;
    if (b.existing_atom(b.atom_pool, &atoms[i], &key) != &atoms[i]) return Failure::flag_pool_unavailable;
    observations[i]->key_registered = atoms[i] != religion::kAbsentReference;
    observations[i]->present = false;
    any_registered |= atoms[i] != religion::kAbsentReference;
  }
  if (!any_registered || Load<std::uint8_t>(actor, g::kCharacterDummyOffset)) return Failure::none;
  auto *script_data = Load<void *>(actor, g::kCharacterScriptDataOffset);
  if (!script_data) return Failure::none;
  const auto index = Load<std::int32_t>(script_data, 0);
  // Native -1 is the empty default FlagSet. Do not invoke its lazy constructor.
  if (index == -1) return Failure::none;
  if (index < -1) return Failure::flag_collection_unavailable;
  auto *flags = b.character_flag_collection(script_data);
  if (!flags) return Failure::flag_collection_unavailable;
  const auto count = Load<std::int32_t>(flags, g::kFlagCountOffset);
  const auto *rows = Load<const void *>(flags, g::kFlagRowsOffset);
  if (count < 0 || (count && !rows)) return Failure::flag_collection_unavailable;
  const auto current = Load<std::int32_t>(flags, kFlagCurrentCounterOffset);
  for (auto *observation : observations) observation->current_counter_raw = current;
  for (std::int32_t row = 0; row < count; ++row) {
    const auto offset = static_cast<std::size_t>(row) * g::kFlagRowStride;
    const auto key = Load<std::uint32_t>(rows, offset + g::kFlagKeyOffset);
    for (std::size_t i = 0; i < 3; ++i) {
      if (atoms[i] == religion::kAbsentReference || key != atoms[i]) continue;
      auto &observation = *observations[i];
      const auto expiry = Load<std::int32_t>(rows, offset + kFlagExpiryCounterOffset);
      observation.present = true;
      observation.expiry_counter_raw = expiry;
      observation.timed = expiry > -1;
      if (expiry > -1) observation.remaining_updates = static_cast<std::int64_t>(expiry) - current;
    }
  }
  return Failure::none;
}

Failure ReadOnce(const Bindings &b, std::uint32_t target, std::uint64_t epoch, Context &out) {
  CoreSnapshotPrefix before{}, after{};
  if (!ReadCoreSnapshot(b.core, before) || !before.map_ready || !before.has_played_character ||
      !before.played_character_alive) return Failure::played_character_unavailable;
  out.capture_epoch = epoch;
  out.date_raw = before.clock.date_raw;
  out.played_character_id = static_cast<std::uint32_t>(before.played_character_id);
  out.requested_target_rite_id = target;
  if (!before.clock.paused) return Failure::frame_not_paused;
  auto *actor = ResolveCoreCharacter(b.core, before.played_character_id);
  if (!actor) return Failure::played_character_unavailable;
  auto *rite = ResolveRite(b, target);
  if (!rite) return Failure::target_rite_unavailable;
  out.target_rite_id = target;
  std::int64_t knowledge{}, fulfillment{};
  if (b.rite_knowledge(&knowledge, actor, rite) != &knowledge) return Failure::knowledge_unavailable;
  out.knowledge_level_raw = knowledge;
  if (b.character_spiritual_fulfillment(actor, &fulfillment) != &fulfillment) return Failure::fulfillment_unavailable;
  out.spiritual_fulfillment_raw = fulfillment;
  auto *resources = Load<void *>(actor, g::kCharacterScriptDataOffset);
  if (resources) out.baseline_spiritual_fulfillment_raw = Load<std::int64_t>(resources, kBaselineFulfillmentOffset);
  const auto failure = ReadFlags(b, actor, out);
  if (failure != Failure::none) return failure;
  if (!ReadCoreSnapshot(b.core, after) || !SameCore(before, after) ||
      ResolveCoreCharacter(b.core, before.played_character_id) != actor || ResolveRite(b, target) != rite)
    return Failure::state_changed;
  out.available = true;
  out.failure = Failure::none;
  return Failure::none;
}
bool Same(const Context &a, const Context &b) noexcept {
  return a.capture_epoch == b.capture_epoch && a.date_raw == b.date_raw &&
      a.played_character_id == b.played_character_id && a.target_rite_id == b.target_rite_id &&
      a.knowledge_level_raw == b.knowledge_level_raw && a.spiritual_fulfillment_raw == b.spiritual_fulfillment_raw &&
      a.baseline_spiritual_fulfillment_raw == b.baseline_spiritual_fulfillment_raw &&
      a.faith_conversion_recently_converted == b.faith_conversion_recently_converted &&
      a.conversion_memory_recently_created == b.conversion_memory_recently_created && a.recent_convert == b.recent_convert;
}
template <typename T> std::string Number(const std::optional<T> &value) {
  return value ? std::to_string(*value) : "null";
}
std::string Boolean(const std::optional<bool> &value) {
  return value ? (*value ? "true" : "false") : "null";
}
std::string FlagJson(const FlagObservation &f) {
  return "{\"key_registered\":" + Boolean(f.key_registered) + ",\"present\":" + Boolean(f.present) +
      ",\"timed\":" + Boolean(f.timed) + ",\"expiry_counter_raw\":" + Number(f.expiry_counter_raw) +
      ",\"current_counter_raw\":" + Number(f.current_counter_raw) +
      ",\"remaining_updates\":" + Number(f.remaining_updates) + '}';
}
} // namespace

Bindings BindConversionOutcomeStateImage12002(std::uintptr_t base, std::string_view sha) noexcept {
  Bindings b{};
  if (!base || sha != kExecutableSha256) return b;
  b.enabled = true;
  b.core = BindCoreImage(base, sha);
  b.rite_storage_slot = reinterpret_cast<void **>(base + g::kRiteStorageSlotRva);
  b.rite_knowledge = reinterpret_cast<KnowledgeGetter>(base + g::kRiteKnowledgeRva);
  b.existing_atom = reinterpret_cast<ExistingAtomLookup>(base + g::kExistingAtomLookupRva);
  b.atom_pool = reinterpret_cast<void *>(base + g::kAtomPoolRva);
  b.character_flag_collection = reinterpret_cast<religion::ObjectGetter>(base + g::kCharacterFlagCollectionRva);
  b.character_spiritual_fulfillment = reinterpret_cast<religion::FixedPointGetter>(base + religion::kCharacterSpiritualFulfillmentRva);
  return b;
}
bool ReadPlayedConversionOutcomeState12002(const Bindings &b, std::uint32_t target,
                                           std::uint64_t epoch, Context &output) noexcept {
  output = {};
  output.capture_epoch = epoch;
  output.requested_target_rite_id = target;
  if (!b.enabled || !b.core.enabled || !b.rite_storage_slot || !b.rite_knowledge ||
      !b.existing_atom || !b.character_flag_collection || !b.character_spiritual_fulfillment) return false;
  Context first{}, second{};
  auto failure = ReadOnce(b, target, epoch, first);
  if (failure == Failure::none) failure = ReadOnce(b, target, epoch, second);
  if (failure == Failure::none && !Same(first, second)) failure = Failure::state_changed;
  if (failure != Failure::none) {
    output.failure = failure;
    output.date_raw = first.date_raw;
    output.played_character_id = first.played_character_id;
    return false;
  }
  output = std::move(first);
  return true;
}
const char *ConversionOutcomeStateFailureKey(Failure f) noexcept {
  switch (f) {
  case Failure::none: return "none";
  case Failure::bindings_unavailable: return "bindings_unavailable";
  case Failure::played_character_unavailable: return "played_character_unavailable";
  case Failure::frame_not_paused: return "frame_not_paused";
  case Failure::target_rite_unavailable: return "target_rite_unavailable";
  case Failure::knowledge_unavailable: return "knowledge_unavailable";
  case Failure::fulfillment_unavailable: return "fulfillment_unavailable";
  case Failure::flag_pool_unavailable: return "flag_pool_unavailable";
  case Failure::flag_collection_unavailable: return "flag_collection_unavailable";
  case Failure::state_changed: return "state_changed";
  }
  return "bindings_unavailable";
}
std::string SerializePlayedConversionOutcomeState12002(const Context &c) {
  return "{\"schema\":\"ck3_12002_religion_conversion_outcome_state_v1\",\"available\":" +
      std::string(c.available ? "true" : "false") + ",\"unavailable_reason\":" +
      (c.available ? "null" : '"' + std::string(ConversionOutcomeStateFailureKey(c.failure)) + '"') +
      ",\"capture_epoch\":" + std::to_string(c.capture_epoch) + ",\"date_raw\":" + std::to_string(c.date_raw) +
      ",\"played_character_id\":" + std::to_string(c.played_character_id) +
      ",\"requested_target_rite_id\":" + std::to_string(c.requested_target_rite_id) +
      ",\"target_rite_id\":" + Number(c.target_rite_id) +
      ",\"knowledge_level_raw\":" + Number(c.knowledge_level_raw) +
      ",\"spiritual_fulfillment_raw\":" + Number(c.spiritual_fulfillment_raw) +
      ",\"baseline_spiritual_fulfillment_raw\":" + Number(c.baseline_spiritual_fulfillment_raw) +
      ",\"faith_conversion_recently_converted\":" + FlagJson(c.faith_conversion_recently_converted) +
      ",\"conversion_memory_recently_created\":" + FlagJson(c.conversion_memory_recently_created) +
      ",\"recent_convert\":" + FlagJson(c.recent_convert) +
      ",\"raw_scale\":100000,\"flag_expiry_unit\":\"native_flag_updates\",\"is_conversion_gain\":false}";
}
} // namespace xar::ck3_12002::religion_conversion::outcome::state
