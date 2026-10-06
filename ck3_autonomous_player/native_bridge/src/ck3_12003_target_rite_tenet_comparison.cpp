#include "xar_bridge/ck3_12003_target_rite_tenet_comparison.hpp"
#include "xar_bridge/religion_doctrine12002_hostility.hpp"

#include <algorithm>
#include <cstring>
#include <utility>

namespace xar::ck3_12003::religion::target_tenet {
namespace {
namespace core = ck3_12002;
namespace religion = ck3_12002::religion;
namespace tenets = ck3_12002::religion::doctrine12002;

template <typename T> T Load(const void *object, std::size_t offset = 0) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value));
  return value;
}

bool Matches(const void *object, std::uint32_t id) noexcept {
  return object && id != religion::kAbsentReference &&
      Load<std::uint32_t>(object, religion::kReferenceIdentityOffset) == id;
}

bool RiteMatches(const void *object, std::uint32_t id) noexcept {
  return Matches(object, id) &&
      Load<std::uint32_t>(object, 0x0C) == tenets::kHostilityRiteTypeTag;
}

// Same full-reference resolver as the existing hostility producer: mask only
// the storage index, then compare the entire returned reference and Rite tag.
void *ResolveRite(const Bindings &b, std::uint32_t id) noexcept {
  if (id == religion::kAbsentReference || !b.rite_storage_global ||
      !*b.rite_storage_global) return nullptr;
  const auto *storage = *b.rite_storage_global;
  const auto index = id & 0xFFFFFFU;
  const auto count = Load<std::uint32_t>(storage, 0x2C);
  if (index >= count) return nullptr;
  const auto *slots = Load<const std::byte *>(storage, 0x20);
  if (!slots) return nullptr;
  auto *object = Load<void *>(slots, static_cast<std::size_t>(index) * 0x10 + 8);
  return RiteMatches(object, id) ? object : nullptr;
}

struct RiteObjects {
  void *rite{}, *faith{}, *main_rite{};
  std::uint32_t rite_id{religion::kAbsentReference};
  std::uint32_t faith_id{religion::kAbsentReference};
  std::uint32_t main_rite_id{religion::kAbsentReference};
};

Failure ReadObjects(const Bindings &b, void *rite, std::uint32_t rite_id,
    bool actor, RiteObjects &out) {
  out.rite = rite;
  out.rite_id = rite_id;
  out.faith_id = Load<std::uint32_t>(rite, religion::kRiteFaithIdOffset);
  out.faith = b.context.rite_faith(rite);
  if (!Matches(out.faith, out.faith_id))
    return actor ? Failure::actor_faith_unavailable : Failure::target_faith_unavailable;
  out.main_rite_id = Load<std::uint32_t>(out.faith, religion::kFaithMainRiteIdOffset);
  out.main_rite = b.context.faith_main_rite(out.faith);
  if (!RiteMatches(out.main_rite, out.main_rite_id))
    return actor ? Failure::actor_main_rite_unavailable : Failure::target_main_rite_unavailable;
  return Failure::none;
}

Failure CoreCollection(const void *rite, Failure unavailable,
    std::vector<const void *> &definitions, std::vector<std::string> &keys) {
  const auto *collection = static_cast<const std::byte *>(rite) +
      tenets::kRiteCoreTenetsOffset;
  const auto count = Load<std::int32_t>(collection, 0x0C);
  const auto *data = Load<const std::byte *>(collection);
  if (count < 0 || count > 8192 || (count && !data)) return unavailable;
  for (std::int32_t i = 0; i < count; ++i) {
    const auto *definition = Load<const void *>(data,
        static_cast<std::size_t>(i) * sizeof(void *));
    std::string key;
    if (!tenets::CopyTenetDefinitionKey12002(definition, key))
      return Failure::tenet_definition_key_unavailable;
    // Append every native occurrence; no union, sorting or key deduplication.
    definitions.push_back(definition);
    keys.push_back(std::move(key));
  }
  if (Load<const std::byte *>(collection) != data ||
      Load<std::int32_t>(collection, 0x0C) != count)
    return Failure::state_changed;
  return Failure::none;
}

struct LoadedDefinition {
  const void *database{}, *definition{};
  const std::byte *array{}, *data{};
  std::int32_t count{}, capacity{};
};

Failure NamedDefinition(const Bindings &b, std::string_view requested,
    LoadedDefinition &out) {
  out.database = *b.tenet_database_global;
  if (!out.database) return Failure::tenet_database_unavailable;
  // Existing TenetSources loaded definition array; no draft reader is used.
  out.array = static_cast<const std::byte *>(out.database) + 0xEF0;
  out.data = Load<const std::byte *>(out.array);
  out.count = Load<std::int32_t>(out.array, 0x0C);
  out.capacity = Load<std::int32_t>(out.array, 8);
  if (out.count < 0 || out.count > 8192 || out.count > out.capacity ||
      (out.count && !out.data)) return Failure::tenet_definitions_unavailable;
  for (std::int32_t i = 0; i < out.count; ++i) {
    const auto *definition = Load<const void *>(out.data,
        static_cast<std::size_t>(i) * sizeof(void *));
    std::string key;
    if (!tenets::CopyTenetDefinitionKey12002(definition, key))
      return Failure::tenet_definition_key_unavailable;
    if (std::string_view{key} == requested) {
      out.definition = definition;
      return Failure::none;
    }
  }
  return Failure::tenet_definition_unavailable;
}

bool ObjectsUnchanged(const Bindings &b, const RiteObjects &objects) {
  return RiteMatches(objects.rite, objects.rite_id) &&
      Load<std::uint32_t>(objects.rite, religion::kRiteFaithIdOffset) == objects.faith_id &&
      b.context.rite_faith(objects.rite) == objects.faith &&
      Matches(objects.faith, objects.faith_id) &&
      Load<std::uint32_t>(objects.faith, religion::kFaithMainRiteIdOffset) == objects.main_rite_id &&
      b.context.faith_main_rite(objects.faith) == objects.main_rite &&
      RiteMatches(objects.main_rite, objects.main_rite_id);
}

bool Member(const std::vector<const void *> &definitions, const void *named) {
  return std::find(definitions.begin(), definitions.end(), named) != definitions.end();
}

Failure ReadOnce(const Bindings &b, std::uint32_t target_id,
    std::string_view key, std::uint64_t epoch, Comparison &out) {
  out.capture_epoch = epoch;
  out.requested_target_rite_id = target_id;
  out.tenet_key = key;
  core::CoreSnapshotPrefix frame{};
  if (!core::ReadCoreSnapshot(b.context.core, frame))
    return Failure::played_character_unavailable;
  out.date_raw = frame.clock.date_raw;
  out.played_character_id = static_cast<std::uint32_t>(frame.played_character_id);
  if (!frame.map_ready || !frame.has_played_character || !frame.played_character_alive)
    return Failure::played_character_unavailable;
  if (!frame.clock.paused) return Failure::frame_not_paused;
  auto *character = core::ResolveCoreCharacter(b.context.core, frame.played_character_id);
  if (!character) return Failure::played_character_unavailable;
  const auto actor_id = Load<std::uint32_t>(character, religion::kCharacterRiteIdOffset);
  auto *actor_rite = b.context.character_rite(character);
  if (!RiteMatches(actor_rite, actor_id)) return Failure::actor_rite_unavailable;
  auto *target_rite = ResolveRite(b, target_id);
  if (!target_rite) return Failure::target_rite_unavailable;

  RiteObjects actor{}, target{};
  auto failure = ReadObjects(b, actor_rite, actor_id, true, actor);
  if (failure != Failure::none) return failure;
  failure = ReadObjects(b, target_rite, target_id, false, target);
  if (failure != Failure::none) return failure;
  if (b.context.character_faith(character) != actor.faith)
    return Failure::actor_faith_unavailable;

  RiteObservation actor_out{}, target_out{};
  std::vector<const void *> actor_core, actor_main_core, target_core, target_main_core;
  // Four independently copied provenance collections, including when an
  // object is shared. Each retains its native order and duplicate entries.
  failure = CoreCollection(actor.rite, Failure::actor_core_tenets_unavailable,
      actor_core, actor_out.core_tenet_keys);
  if (failure != Failure::none) return failure;
  failure = CoreCollection(actor.main_rite, Failure::actor_main_core_tenets_unavailable,
      actor_main_core, actor_out.faith_main_core_tenet_keys);
  if (failure != Failure::none) return failure;
  failure = CoreCollection(target.rite, Failure::target_core_tenets_unavailable,
      target_core, target_out.core_tenet_keys);
  if (failure != Failure::none) return failure;
  failure = CoreCollection(target.main_rite, Failure::target_main_core_tenets_unavailable,
      target_main_core, target_out.faith_main_core_tenet_keys);
  if (failure != Failure::none) return failure;

  LoadedDefinition named{};
  failure = NamedDefinition(b, key, named);
  if (failure != Failure::none) return failure;
  const auto actor_state = b.tenet_state(actor.rite, named.definition);
  if (actor_state > 4) return Failure::actor_tenet_state_unavailable;
  const auto target_state = b.tenet_state(target.rite, named.definition);
  if (target_state > 4) return Failure::target_tenet_state_unavailable;

  core::CoreSnapshotPrefix after{};
  if (!core::ReadCoreSnapshot(b.context.core, after) || !after.map_ready ||
      !after.has_played_character || !after.played_character_alive || !after.clock.paused ||
      after.clock.date_raw != frame.clock.date_raw ||
      after.played_character_id != frame.played_character_id ||
      core::ResolveCoreCharacter(b.context.core, frame.played_character_id) != character ||
      Load<std::uint32_t>(character, religion::kCharacterRiteIdOffset) != actor_id ||
      b.context.character_rite(character) != actor.rite ||
      b.context.character_faith(character) != actor.faith ||
      ResolveRite(b, target_id) != target.rite ||
      !ObjectsUnchanged(b, actor) || !ObjectsUnchanged(b, target) ||
      *b.tenet_database_global != named.database ||
      Load<const std::byte *>(named.array) != named.data ||
      Load<std::int32_t>(named.array, 0x0C) != named.count ||
      Load<std::int32_t>(named.array, 8) != named.capacity)
    return Failure::state_changed;

  actor_out.rite_id = actor.rite_id;
  actor_out.faith_id = actor.faith_id;
  actor_out.faith_main_rite_id = actor.main_rite_id;
  actor_out.current_is_main = actor.rite_id == actor.main_rite_id;
  actor_out.core_tenets_complete = true;
  actor_out.faith_main_core_tenets_complete = true;
  actor_out.named_tenet_core_member = Member(actor_core, named.definition);
  actor_out.named_tenet_faith_main_core_member = Member(actor_main_core, named.definition);
  actor_out.named_tenet_status = actor_state;
  target_out.rite_id = target.rite_id;
  target_out.faith_id = target.faith_id;
  target_out.faith_main_rite_id = target.main_rite_id;
  target_out.current_is_main = target.rite_id == target.main_rite_id;
  target_out.core_tenets_complete = true;
  target_out.faith_main_core_tenets_complete = true;
  target_out.named_tenet_core_member = Member(target_core, named.definition);
  target_out.named_tenet_faith_main_core_member = Member(target_main_core, named.definition);
  target_out.named_tenet_status = target_state;
  out.actor_rite = std::move(actor_out);
  out.target_rite = std::move(target_out);
  out.same_rite = actor.rite_id == target.rite_id;
  out.same_faith = actor.faith_id == target.faith_id;
  return Failure::none;
}

bool Same(const Comparison &a, const Comparison &b) {
  return a.date_raw == b.date_raw && a.played_character_id == b.played_character_id &&
      a.actor_rite == b.actor_rite && a.target_rite == b.target_rite &&
      a.same_rite == b.same_rite && a.same_faith == b.same_faith;
}

bool Fail(Comparison &out, Failure failure) {
  out.available = false;
  out.failure = failure;
  out.actor_rite.reset();
  out.target_rite.reset();
  out.same_rite.reset();
  out.same_faith.reset();
  out.named_comparison_ready = false;
  return false;
}

bool ReadTwice(const Bindings &b, std::uint32_t target,
    std::string_view key, std::uint64_t epoch, Comparison &out) {
  Comparison first{}, second{};
  auto failure = ReadOnce(b, target, key, epoch, first);
  out.date_raw = first.date_raw;
  out.played_character_id = first.played_character_id;
  if (failure == Failure::none) failure = ReadOnce(b, target, key, epoch, second);
  if (failure == Failure::none && !Same(first, second)) failure = Failure::state_changed;
  if (failure != Failure::none) return Fail(out, failure);
  out = std::move(first);
  out.available = true;
  out.failure = Failure::none;
  out.named_comparison_ready = true;
  return true;
}

std::string Quote(std::string_view value) {
  constexpr char hex[] = "0123456789abcdef";
  std::string out = "\"";
  for (const unsigned char byte : value) {
    if (byte == '"' || byte == '\\') {
      out += '\\'; out += static_cast<char>(byte);
    } else if (byte < 0x20) {
      out += "\\u00"; out += hex[byte >> 4]; out += hex[byte & 0x0F];
    } else {
      out += static_cast<char>(byte);
    }
  }
  return out + '"';
}

std::string Bool(bool value) { return value ? "true" : "false"; }
std::string Bool(const std::optional<bool> &value) {
  return value.has_value() ? Bool(*value) : "null";
}
std::string Keys(const std::vector<std::string> &keys) {
  std::string out = "[";
  for (std::size_t i = 0; i < keys.size(); ++i) {
    if (i) out += ',';
    out += Quote(keys[i]);
  }
  return out + ']';
}
std::string Scope(const std::optional<RiteObservation> &scope) {
  if (!scope) return "null";
  const auto &r = *scope;
  return "{\"rite_id\":" + std::to_string(r.rite_id) +
      ",\"faith_id\":" + std::to_string(r.faith_id) +
      ",\"faith_main_rite_id\":" + std::to_string(r.faith_main_rite_id) +
      ",\"current_is_main\":" + Bool(r.current_is_main) +
      ",\"core_tenets_complete\":" + Bool(r.core_tenets_complete) +
      ",\"core_tenet_keys\":" + Keys(r.core_tenet_keys) +
      ",\"faith_main_core_tenets_complete\":" + Bool(r.faith_main_core_tenets_complete) +
      ",\"faith_main_core_tenet_keys\":" + Keys(r.faith_main_core_tenet_keys) +
      ",\"named_tenet_core_member\":" + Bool(r.named_tenet_core_member) +
      ",\"named_tenet_faith_main_core_member\":" + Bool(r.named_tenet_faith_main_core_member) +
      ",\"named_tenet_status\":" + std::to_string(r.named_tenet_status) + "}";
}
} // namespace

bool ReadPlayedTargetRiteTenetComparison12003(const Bindings &b,
    std::uint32_t target, std::string_view key, std::uint64_t epoch,
    Comparison &out) noexcept {
  out = {};
  out.capture_epoch = epoch;
  out.requested_target_rite_id = target;
  try {
    out.tenet_key = key;
    if (!b.context.enabled || !b.context.core.enabled ||
        !b.context.character_rite || !b.context.character_faith ||
        !b.context.rite_faith || !b.context.faith_main_rite ||
        !b.rite_storage_global || !b.tenet_database_global || !b.tenet_state)
      return Fail(out, Failure::bindings_unavailable);
#if defined(_WIN32) && defined(_MSC_VER)
    auto guarded = [](const Bindings &bindings, std::uint32_t requested,
        std::string_view named_key, std::uint64_t capture, Comparison &output) -> bool {
      __try { return ReadTwice(bindings, requested, named_key, capture, output); }
      __except (1) { return Fail(output, Failure::tenet_native_read_unavailable); }
    };
    return guarded(b, target, key, epoch, out);
#else
    return ReadTwice(b, target, key, epoch, out);
#endif
  } catch (...) {
    return Fail(out, Failure::tenet_native_read_unavailable);
  }
}

const char *TargetRiteTenetComparisonFailureKey(Failure failure) noexcept {
  switch (failure) {
  case Failure::none: return "none";
  case Failure::bindings_unavailable: return "bindings_unavailable";
  case Failure::played_character_unavailable: return "played_character_unavailable";
  case Failure::frame_not_paused: return "frame_not_paused";
  case Failure::actor_rite_unavailable: return "actor_rite_unavailable";
  case Failure::target_rite_unavailable: return "target_rite_unavailable";
  case Failure::actor_faith_unavailable: return "actor_faith_unavailable";
  case Failure::target_faith_unavailable: return "target_faith_unavailable";
  case Failure::actor_main_rite_unavailable: return "actor_main_rite_unavailable";
  case Failure::target_main_rite_unavailable: return "target_main_rite_unavailable";
  case Failure::actor_core_tenets_unavailable: return "actor_core_tenets_unavailable";
  case Failure::actor_main_core_tenets_unavailable: return "actor_main_core_tenets_unavailable";
  case Failure::target_core_tenets_unavailable: return "target_core_tenets_unavailable";
  case Failure::target_main_core_tenets_unavailable: return "target_main_core_tenets_unavailable";
  case Failure::tenet_database_unavailable: return "tenet_database_unavailable";
  case Failure::tenet_definitions_unavailable: return "tenet_definitions_unavailable";
  case Failure::tenet_definition_key_unavailable: return "tenet_definition_key_unavailable";
  case Failure::tenet_definition_unavailable: return "tenet_definition_unavailable";
  case Failure::actor_tenet_state_unavailable: return "actor_tenet_state_unavailable";
  case Failure::target_tenet_state_unavailable: return "target_tenet_state_unavailable";
  case Failure::state_changed: return "state_changed";
  case Failure::tenet_native_read_unavailable: return "tenet_native_read_unavailable";
  }
  return "bindings_unavailable";
}

std::string SerializeTargetRiteTenetComparison12003(const Comparison &out) {
  return std::string{"{\"schema\":"} + Quote(kSchema) +
      ",\"read_only\":true,\"available\":" + Bool(out.available) +
      ",\"unavailable_reason\":" +
          (out.available ? std::string{"null"} : Quote(TargetRiteTenetComparisonFailureKey(out.failure))) +
      ",\"capture_epoch\":" + std::to_string(out.capture_epoch) +
      ",\"date_raw\":" + std::to_string(out.date_raw) +
      ",\"played_character_id\":" + std::to_string(out.played_character_id) +
      ",\"requested_target_rite_id\":" + std::to_string(out.requested_target_rite_id) +
      ",\"tenet_key\":" + Quote(out.tenet_key) +
      ",\"actor_rite\":" + (out.available ? Scope(out.actor_rite) : "null") +
      ",\"target_rite\":" + (out.available ? Scope(out.target_rite) : "null") +
      ",\"same_rite\":" + (out.available ? Bool(out.same_rite) : "null") +
      ",\"same_faith\":" + (out.available ? Bool(out.same_faith) : "null") +
      ",\"named_comparison_ready\":" + Bool(out.available && out.named_comparison_ready) +
      ",\"status_values\":{\"unknown\":0,\"known\":1,\"prohibited\":2,\"permitted\":3,\"core\":4}}";
}

} // namespace xar::ck3_12003::religion::target_tenet
