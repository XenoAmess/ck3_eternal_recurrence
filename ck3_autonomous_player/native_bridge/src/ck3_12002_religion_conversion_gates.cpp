#include "xar_bridge/ck3_12002_religion_conversion_gates.hpp"

#include <cstring>
#include <utility>

namespace xar::ck3_12002::religion::conversion_gates {
namespace {
template <typename T> T Load(const void *p, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(p) + offset, sizeof(value));
  return value;
}
bool Match(const void *p, std::uint32_t ref) noexcept {
  return p && Load<std::uint32_t>(p, kReferenceIdentityOffset) == ref;
}
void *ResolveRite(const Bindings &b, std::uint32_t ref) noexcept {
  if (ref == kAbsentReference || !b.rite_storage_slot || !*b.rite_storage_slot) return nullptr;
  auto *storage = *b.rite_storage_slot;
  const auto index = ref & 0xFFFFFFU;
  if (index >= Load<std::uint32_t>(storage, 0x2C)) return nullptr;
  auto *rows = Load<const void *>(storage, 0x20);
  if (!rows) return nullptr;
  auto *rite = Load<void *>(rows, static_cast<std::size_t>(index) * 0x10 + 0x08);
  return Match(rite, ref) ? rite : nullptr;
}

Failure ReadRecentFlag(const Bindings &b, void *actor, Context &out) {
  // The native insertion API 0x3F8A4B0 is deliberately not called. Its existing
  // lookup body supplies the exact already-registered key or UINT32_MAX.
  if (!b.atom_pool || !Load<const void *>(b.atom_pool, 0x10) ||
      Load<std::int32_t>(b.atom_pool, 0x1C) < 0) return Failure::flag_pool_unavailable;
  const NativeStringView key{kRecentConversionFlag,
      static_cast<std::int32_t>(sizeof(kRecentConversionFlag) - 1), 1, {}};
  std::uint32_t atom = kAbsentReference;
  if (b.existing_atom(b.atom_pool, &atom, &key) != &atom) return Failure::flag_pool_unavailable;
  out.recent_flag_key_registered = atom != kAbsentReference;
  out.recently_converted = false;
  if (atom == kAbsentReference || Load<std::uint8_t>(actor, kCharacterDummyOffset)) return Failure::none;
  auto *script_data = Load<void *>(actor, kCharacterScriptDataOffset);
  if (!script_data) return Failure::none;
  // Native index -1 resolves the empty default FlagSet (+0x10/+0x18 are zero).
  // Preserve its legal empty result without invoking lazy initialization.
  const auto index = Load<std::int32_t>(script_data, 0);
  if (index == -1) return Failure::none;
  if (index < -1) return Failure::flag_collection_unavailable;
  auto *flags = b.character_flag_collection(script_data);
  if (!flags) return Failure::flag_collection_unavailable;
  const auto count = Load<std::int32_t>(flags, kFlagCountOffset);
  const auto *rows = Load<const void *>(flags, kFlagRowsOffset);
  if (count < 0 || (count && !rows)) return Failure::flag_collection_unavailable;
  for (std::int32_t i = 0; i < count; ++i) {
    if (Load<std::uint32_t>(rows, static_cast<std::size_t>(i) * kFlagRowStride + kFlagKeyOffset) == atom) {
      out.recently_converted = true;
      break;
    }
  }
  return Failure::none;
}

Failure ReadOnce(const Bindings &b, std::uint32_t target, std::uint64_t epoch, Context &out) {
  state_rite::Context state{};
  if (!state_rite::ReadPlayedStateRite12002(b.state, epoch, state)) return Failure::state_rite_unavailable;
  auto *actor = ResolveCoreCharacter(b.state.context.core, static_cast<std::int32_t>(state.played_character_id));
  if (!actor) return Failure::played_character_unavailable;
  auto *rite = ResolveRite(b, target);
  if (!rite) return Failure::target_rite_unavailable;
  out.capture_epoch = epoch;
  out.date_raw = state.date_raw;
  out.played_character_id = state.played_character_id;
  out.requested_target_rite_id = target;
  out.target_rite_id = target;
  out.actor_faith_id = state.actor_faith_id;
  const auto faith_ref = Load<std::uint32_t>(rite, kRiteFaithIdOffset);
  auto *target_faith = b.state.context.rite_faith(rite);
  if (faith_ref == kAbsentReference || !Match(target_faith, faith_ref)) return Failure::target_faith_unavailable;
  out.target_faith_id = faith_ref;
  auto *actor_faith = b.state.context.character_faith(actor);
  if (!state.actor_faith_id || !Match(actor_faith, *state.actor_faith_id)) return Failure::actor_faith_unavailable;
  const auto actor_religion = Load<std::uint32_t>(actor_faith, kFaithReligionIdOffset);
  if (actor_religion == kAbsentReference ||
      !Match(b.state.context.faith_religion(actor_faith), actor_religion)) return Failure::actor_religion_unavailable;
  const auto target_religion = Load<std::uint32_t>(target_faith, kFaithReligionIdOffset);
  if (target_religion == kAbsentReference ||
      !Match(b.state.context.faith_religion(target_faith), target_religion)) return Failure::target_religion_unavailable;
  out.actor_religion_id = actor_religion;
  out.target_religion_id = target_religion;
  out.same_faith = state.actor_faith_id == out.target_faith_id;
  out.same_religion = actor_religion == target_religion;
  out.realm_state_rite_id = state.realm_primary_title.state_rite_id;
  out.realm_state_faith_id = state.realm_primary_title.state_faith_id;
  out.state_rite_target_match = out.realm_state_rite_id && *out.realm_state_rite_id == target;
  out.state_faith_target_match = out.realm_state_faith_id && *out.realm_state_faith_id == faith_ref;
  std::int64_t knowledge{};
  if (b.rite_knowledge(&knowledge, actor, rite) != &knowledge) return Failure::knowledge_unavailable;
  out.knowledge_level_raw = knowledge;
  const auto failure = ReadRecentFlag(b, actor, out);
  if (failure != Failure::none) return failure;
  if (ResolveRite(b, target) != rite ||
      ResolveCoreCharacter(b.state.context.core, static_cast<std::int32_t>(state.played_character_id)) != actor)
    return Failure::state_changed;
  out.available = true;
  out.failure = Failure::none;
  return Failure::none;
}
bool Same(const Context &a, const Context &b) {
  return a.date_raw == b.date_raw && a.played_character_id == b.played_character_id &&
      a.target_rite_id == b.target_rite_id && a.actor_faith_id == b.actor_faith_id &&
      a.target_faith_id == b.target_faith_id && a.actor_religion_id == b.actor_religion_id &&
      a.target_religion_id == b.target_religion_id && a.realm_state_rite_id == b.realm_state_rite_id &&
      a.realm_state_faith_id == b.realm_state_faith_id && a.knowledge_level_raw == b.knowledge_level_raw &&
      a.recently_converted == b.recently_converted && a.recent_flag_key_registered == b.recent_flag_key_registered;
}
template <typename T> std::string Number(const std::optional<T> &value) {
  return value ? std::to_string(*value) : "null";
}
std::string Boolean(const std::optional<bool> &value) {
  return value ? (*value ? "true" : "false") : "null";
}
} // namespace

Bindings BindReligionConversionGatesImage12002(std::uintptr_t base, std::string_view sha) noexcept {
  Bindings b{};
  if (!base || sha != kExecutableSha256) return b;
  b.enabled = true;
  b.state = state_rite::BindStateRiteImage12002(base, sha);
  b.rite_storage_slot = reinterpret_cast<void **>(base + kRiteStorageSlotRva);
  b.rite_knowledge = reinterpret_cast<KnowledgeGetter>(base + kRiteKnowledgeRva);
  b.existing_atom = reinterpret_cast<ExistingAtomLookup>(base + kExistingAtomLookupRva);
  b.atom_pool = reinterpret_cast<void *>(base + kAtomPoolRva);
  b.character_flag_collection = reinterpret_cast<ObjectGetter>(base + kCharacterFlagCollectionRva);
  return b;
}
bool ReadPlayedReligionConversionGates12002(const Bindings &b, std::uint32_t target,
                                          std::uint64_t epoch, Context &output) noexcept {
  output = {};
  output.capture_epoch = epoch;
  output.requested_target_rite_id = target;
  if (!b.enabled || !b.state.enabled || !b.state.context.faith_religion ||
      !b.rite_storage_slot || !b.rite_knowledge || !b.existing_atom || !b.character_flag_collection) return false;
  Context first{}, second{};
  auto failure = ReadOnce(b, target, epoch, first);
  if (failure == Failure::none) failure = ReadOnce(b, target, epoch, second);
  if (failure == Failure::none && !Same(first, second)) failure = Failure::state_changed;
  if (failure != Failure::none) { output.failure = failure; return false; }
  output = std::move(first);
  return true;
}
const char *ReligionConversionGatesFailureKey(Failure f) noexcept {
  switch (f) {
  case Failure::none: return "none";
  case Failure::bindings_unavailable: return "bindings_unavailable";
  case Failure::state_rite_unavailable: return "state_rite_unavailable";
  case Failure::played_character_unavailable: return "played_character_unavailable";
  case Failure::target_rite_unavailable: return "target_rite_unavailable";
  case Failure::actor_faith_unavailable: return "actor_faith_unavailable";
  case Failure::target_faith_unavailable: return "target_faith_unavailable";
  case Failure::actor_religion_unavailable: return "actor_religion_unavailable";
  case Failure::target_religion_unavailable: return "target_religion_unavailable";
  case Failure::knowledge_unavailable: return "knowledge_unavailable";
  case Failure::flag_pool_unavailable: return "flag_pool_unavailable";
  case Failure::flag_collection_unavailable: return "flag_collection_unavailable";
  case Failure::state_changed: return "state_changed";
  }
  return "bindings_unavailable";
}
std::string SerializePlayedReligionConversionGates12002(const Context &c) {
  return "{\"schema\":\"ck3_12002_religion_conversion_gates_v1\",\"available\":" +
      std::string(c.available ? "true" : "false") +
      ",\"unavailable_reason\":" + (c.available ? "null" : '"' + std::string(ReligionConversionGatesFailureKey(c.failure)) + '"') +
      ",\"capture_epoch\":" + std::to_string(c.capture_epoch) +
      ",\"date_raw\":" + std::to_string(c.date_raw) +
      ",\"played_character_id\":" + std::to_string(c.played_character_id) +
      ",\"requested_target_rite_id\":" + std::to_string(c.requested_target_rite_id) +
      ",\"target_rite_id\":" + Number(c.target_rite_id) +
      ",\"actor_faith_id\":" + Number(c.actor_faith_id) +
      ",\"target_faith_id\":" + Number(c.target_faith_id) +
      ",\"actor_religion_id\":" + Number(c.actor_religion_id) +
      ",\"target_religion_id\":" + Number(c.target_religion_id) +
      ",\"realm_state_rite_id\":" + Number(c.realm_state_rite_id) +
      ",\"realm_state_faith_id\":" + Number(c.realm_state_faith_id) +
      ",\"knowledge_level_raw\":" + Number(c.knowledge_level_raw) +
      ",\"recently_converted\":" + Boolean(c.recently_converted) +
      ",\"recent_flag_key_registered\":" + Boolean(c.recent_flag_key_registered) +
      ",\"same_faith\":" + Boolean(c.same_faith) +
      ",\"same_religion\":" + Boolean(c.same_religion) +
      ",\"state_rite_target_match\":" + Boolean(c.state_rite_target_match) +
      ",\"state_faith_target_match\":" + Boolean(c.state_faith_target_match) +
      ",\"raw_scale\":100000}";
}
} // namespace xar::ck3_12002::religion::conversion_gates
