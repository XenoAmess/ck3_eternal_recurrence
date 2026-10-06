#include "xar_bridge/ck3_12003_player_tenet_knowledge_catalogue.hpp"
#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/religion_doctrine12002_tenet_rows.hpp"

#include <cstring>
#include <string_view>
#include <utility>

namespace xar::ck3_12003::religion::tenet_knowledge {
namespace {
namespace core = ck3_12002;
namespace tenets = ck3_12002::religion::doctrine12002;

template <class T> T Load(const void *object, std::size_t offset = 0) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value));
  return value;
}
const std::byte *At(const void *object, std::size_t offset) noexcept {
  return static_cast<const std::byte *>(object) + offset;
}

struct Collection {
  const void *object{};
  const std::byte *data{};
  std::int32_t count{}, capacity{};
  std::vector<const void *> definitions;
  bool operator==(const Collection &) const = default;
};

bool ReadCollection(const void *object, Collection &out) {
  if (!object) return false;
  out.object = object;
  out.data = Load<const std::byte *>(object);
  out.count = Load<std::int32_t>(object, 0xC);
  out.capacity = Load<std::int32_t>(object, 8);
  if (out.count < 0 || out.count > 8192 || out.count > out.capacity ||
      (out.count && !out.data)) return false;
  for (std::int32_t i = 0; i < out.count; ++i)
    out.definitions.push_back(Load<const void *>(out.data,
        static_cast<std::size_t>(i) * sizeof(void *)));
  return true;
}

bool Unchanged(const Collection &value) {
  if (Load<const std::byte *>(value.object) != value.data ||
      Load<std::int32_t>(value.object, 0xC) != value.count ||
      Load<std::int32_t>(value.object, 8) != value.capacity) return false;
  for (std::size_t i = 0; i < value.definitions.size(); ++i)
    if (Load<const void *>(value.data, i * sizeof(void *)) != value.definitions[i])
      return false;
  return true;
}

struct Observation {
  Catalogue value;
  void *actor{};
  const void *extension{}, *tenet_database{}, *perk_database{}, *prophet{};
  Collection loaded, extra, perks;
};

Failure ReadOnce(const Bindings &b, std::uint64_t epoch,
    Observation &out, Catalogue *owner) {
  core::CoreSnapshotPrefix frame{};
  if (!core::ReadCoreSnapshot(b.context.core, frame))
    return Failure::played_character_unavailable;
  out.value.capture_epoch = epoch;
  out.value.date_raw = frame.clock.date_raw;
  out.value.played_character_id = static_cast<std::uint32_t>(frame.played_character_id);
  if (owner) {
    owner->date_raw = out.value.date_raw;
    owner->played_character_id = out.value.played_character_id;
  }
  if (!frame.map_ready || !frame.has_played_character || !frame.played_character_alive)
    return Failure::played_character_unavailable;
  if (!frame.clock.paused) return Failure::frame_not_paused;
  out.actor = core::ResolveCoreCharacter(b.context.core, frame.played_character_id);
  if (!out.actor) return Failure::played_character_unavailable;
  out.extension = Load<const void *>(out.actor, 0x1C8);

  out.tenet_database = *b.tenet_database_global;
  if (!out.tenet_database) return Failure::tenet_database_unavailable;
  if (!ReadCollection(At(out.tenet_database, 0xEF0), out.loaded))
    return Failure::tenet_definition_collection_unavailable;

  // The accessor also supplies the native default collection when extension
  // storage is absent. Absence alone is not evidence of an empty collection.
  if (!ReadCollection(b.actor_extra_collection(out.actor), out.extra))
    return Failure::actor_extra_collection_unavailable;
  std::vector<std::string> extra_keys;
  for (const auto *definition : out.extra.definitions) {
    std::string key;
    if (!tenets::CopyTenetDefinitionKey12002(definition, key))
      return Failure::extra_tenet_definition_key_unavailable;
    extra_keys.push_back(std::move(key));
  }

  out.perk_database = *b.perk_database_global;
  out.prophet = out.perk_database ? Load<const void *>(out.perk_database, 0xEF0) : nullptr;
  if (!out.prophet) return Failure::prophet_definition_unavailable;
  if (!ReadCollection(b.actor_perks_collection(out.actor), out.perks))
    return Failure::actor_perks_collection_unavailable;
  // Both Contains calls receive the actual definition-pointer argument used
  // by the native predicate, never a key-derived substitute.
  const bool has_prophet = b.contains(out.perks.object, &out.prophet);
  std::vector<Row> rows;
  for (std::size_t i = 0; i < out.loaded.definitions.size(); ++i) {
    const auto *definition = out.loaded.definitions[i];
    Row row{};
    row.source_index = static_cast<std::uint32_t>(i);
    if (!tenets::CopyTenetDefinitionKey12002(definition, row.tenet_key))
      return Failure::tenet_definition_key_unavailable;
    row.native_extra_knowledge = b.contains(out.extra.object, &definition);
    row.knowledge = row.native_extra_knowledge || has_prophet;
    rows.push_back(std::move(row));
  }

  core::CoreSnapshotPrefix after{};
  if (!core::ReadCoreSnapshot(b.context.core, after) || !after.map_ready ||
      !after.has_played_character || !after.played_character_alive || !after.clock.paused ||
      after.clock.date_raw != frame.clock.date_raw ||
      after.played_character_id != frame.played_character_id ||
      core::ResolveCoreCharacter(b.context.core, frame.played_character_id) != out.actor ||
      Load<const void *>(out.actor, 0x1C8) != out.extension ||
      *b.tenet_database_global != out.tenet_database ||
      *b.perk_database_global != out.perk_database ||
      Load<const void *>(out.perk_database, 0xEF0) != out.prophet ||
      !Unchanged(out.loaded) || !Unchanged(out.extra) || !Unchanged(out.perks))
    return Failure::state_changed;

  out.value.has_character_extension = out.extension != nullptr;
  out.value.extra_collection_source = out.extension
      ? ExtraCollectionSource::character_extension_c8
      : ExtraCollectionSource::native_default_collection;
  out.value.extra_collection_complete = true;
  out.value.extra_tenet_keys = std::move(extra_keys);
  out.value.loaded_registry_complete = true;
  out.value.loaded_definition_count = static_cast<std::uint32_t>(out.loaded.count);
  out.value.native_has_prophet = has_prophet;
  out.value.knowledge_inputs_complete = true;
  out.value.rows = std::move(rows);
  return Failure::none;
}

bool Same(const Observation &a, const Observation &b) {
  return a.actor == b.actor && a.extension == b.extension &&
      a.tenet_database == b.tenet_database && a.perk_database == b.perk_database &&
      a.prophet == b.prophet && a.loaded == b.loaded && a.extra == b.extra &&
      a.perks == b.perks && a.value.date_raw == b.value.date_raw &&
      a.value.played_character_id == b.value.played_character_id &&
      a.value.extra_tenet_keys == b.value.extra_tenet_keys &&
      a.value.native_has_prophet == b.value.native_has_prophet &&
      a.value.rows == b.value.rows;
}

bool Fail(Catalogue &out, Failure failure) noexcept {
  out.available = false;
  out.failure = failure;
  out.has_character_extension.reset();
  out.extra_collection_source.reset();
  out.extra_collection_complete = false;
  out.extra_tenet_keys.reset();
  out.loaded_registry_complete = false;
  out.loaded_definition_count.reset();
  out.native_has_prophet.reset();
  out.knowledge_inputs_complete = false;
  out.rows.reset();
  return false;
}

bool ReadTwice(const Bindings &b, std::uint64_t epoch, Catalogue &out) {
  Observation first{}, second{};
  auto failure = ReadOnce(b, epoch, first, &out);
  if (failure == Failure::none) failure = ReadOnce(b, epoch, second, nullptr);
  if (failure == Failure::none && !Same(first, second)) failure = Failure::state_changed;
  if (failure != Failure::none) return Fail(out, failure);
  out = std::move(first.value);
  out.available = true;
  out.failure = Failure::none;
  return true;
}

std::string Quote(std::string_view value) {
  constexpr char hex[] = "0123456789abcdef";
  std::string result = "\"";
  for (const unsigned char c : value) {
    if (c == '\\' || c == '"') { result += '\\'; result += static_cast<char>(c); }
    else if (c < 32) { result += "\\u00"; result += hex[c >> 4]; result += hex[c & 15]; }
    else result += static_cast<char>(c);
  }
  return result + '"';
}
std::string Bool(bool value) { return value ? "true" : "false"; }
std::string Bool(const std::optional<bool> &value) {
  return value ? Bool(*value) : "null";
}
std::string Keys(const std::optional<std::vector<std::string>> &keys) {
  if (!keys) return "null";
  std::string result = "[";
  for (const auto &key : *keys) {
    if (result.size() > 1) result += ',';
    result += Quote(key);
  }
  return result + ']';
}
std::string Rows(const std::optional<std::vector<Row>> &rows) {
  if (!rows) return "null";
  std::string result = "[";
  for (const auto &row : *rows) {
    if (result.size() > 1) result += ',';
    result += "{\"source_index\":" + std::to_string(row.source_index) +
        ",\"tenet_key\":" + Quote(row.tenet_key) +
        ",\"native_extra_knowledge\":" + Bool(row.native_extra_knowledge) +
        ",\"knowledge\":" + Bool(row.knowledge) + '}';
  }
  return result + ']';
}
} // namespace

bool ReadPlayedTenetKnowledgeCatalogue12003(const Bindings &b,
    std::uint64_t epoch, Catalogue &out) noexcept {
  out = {};
  out.capture_epoch = epoch;
  try {
    if (!b.context.enabled || !b.context.core.enabled || !b.tenet_database_global ||
        !b.perk_database_global || !b.actor_extra_collection ||
        !b.actor_perks_collection || !b.contains)
      return Fail(out, Failure::bindings_unavailable);
#if defined(_WIN32) && defined(_MSC_VER)
    auto guarded = [](const Bindings &bindings, std::uint64_t capture,
        Catalogue &output) -> bool {
      __try { return ReadTwice(bindings, capture, output); }
      __except (1) { return Fail(output, Failure::knowledge_native_read_unavailable); }
    };
    return guarded(b, epoch, out);
#else
    return ReadTwice(b, epoch, out);
#endif
  } catch (...) {
    return Fail(out, Failure::knowledge_native_read_unavailable);
  }
}

const char *TenetKnowledgeCatalogueFailureKey(Failure failure) noexcept {
  switch (failure) {
  case Failure::none: return "none";
  case Failure::bindings_unavailable: return "bindings_unavailable";
  case Failure::played_character_unavailable: return "played_character_unavailable";
  case Failure::frame_not_paused: return "frame_not_paused";
  case Failure::tenet_database_unavailable: return "tenet_database_unavailable";
  case Failure::tenet_definition_collection_unavailable: return "tenet_definition_collection_unavailable";
  case Failure::tenet_definition_key_unavailable: return "tenet_definition_key_unavailable";
  case Failure::actor_extra_collection_unavailable: return "actor_extra_collection_unavailable";
  case Failure::extra_tenet_definition_key_unavailable: return "extra_tenet_definition_key_unavailable";
  case Failure::prophet_definition_unavailable: return "prophet_definition_unavailable";
  case Failure::actor_perks_collection_unavailable: return "actor_perks_collection_unavailable";
  case Failure::state_changed: return "state_changed";
  case Failure::knowledge_native_read_unavailable: return "knowledge_native_read_unavailable";
  }
  return "bindings_unavailable";
}

std::string SerializePlayedTenetKnowledgeCatalogue12003(const Catalogue &v) {
  const bool ready = v.available && v.extra_collection_complete &&
      v.loaded_registry_complete && v.knowledge_inputs_complete;
  std::string source = "null";
  if (ready && v.extra_collection_source)
    source = Quote(*v.extra_collection_source == ExtraCollectionSource::character_extension_c8
        ? "character_extension_c8" : "native_default_collection");
  return std::string{"{\"schema\":"} + Quote(kSchema) +
      ",\"game_version\":" + Quote(ck3_12003::kGameVersion) +
      ",\"executable_sha256\":" + Quote(ck3_12003::kExecutableSha256) +
      ",\"scope\":\"actual_played_character_extra_c8_and_prophet_inputs\"" +
      ",\"available\":" + Bool(v.available) +
      ",\"unavailable_reason\":" + (v.available ? "null" : Quote(TenetKnowledgeCatalogueFailureKey(v.failure))) +
      ",\"capture_epoch\":" + std::to_string(v.capture_epoch) +
      ",\"date_raw\":" + std::to_string(v.date_raw) +
      ",\"played_character_id\":" + std::to_string(v.played_character_id) +
      ",\"has_character_extension\":" + (ready ? Bool(v.has_character_extension) : "null") +
      ",\"extra_collection_source\":" + source +
      ",\"extra_collection_complete\":" + Bool(ready) +
      ",\"extra_tenet_keys\":" + (ready ? Keys(v.extra_tenet_keys) : "null") +
      ",\"loaded_registry_complete\":" + Bool(ready) +
      ",\"loaded_definition_count\":" + (ready && v.loaded_definition_count ? std::to_string(*v.loaded_definition_count) : "null") +
      ",\"native_has_prophet\":" + (ready ? Bool(v.native_has_prophet) : "null") +
      ",\"knowledge_inputs_complete\":" + Bool(ready) +
      ",\"knowledge_formula\":\"extra_c8_membership_or_prophet_perk\"" +
      ",\"rows\":" + (ready ? Rows(v.rows) : "null") + '}';
}

} // namespace xar::ck3_12003::religion::tenet_knowledge
