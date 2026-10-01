#include "xar_bridge/religion_doctrine12002_choices.hpp"

#include <cstring>

namespace xar::ck3_12002::religion::doctrine12002 {
namespace {
template <typename T> T Load(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value));
  return value;
}

bool Frame(const KnowledgeBindings &b, CoreSnapshotPrefix &frame, void *&character,
           std::string &reason) {
  if (!ReadCoreSnapshot(b.context.core, frame) || !frame.map_ready ||
      !frame.has_played_character || !frame.played_character_alive) {
    reason = "played_character_unavailable"; return false;
  }
  if (!frame.clock.paused) { reason = "frame_not_paused"; return false; }
  character = ResolveCoreCharacter(b.context.core, frame.played_character_id);
  if (!character) { reason = "played_character_unavailable"; return false; }
  return true;
}

bool CanRead(const KnowledgeBindings &b) noexcept {
  return b.context.enabled && b.context.core.enabled &&
      b.context.character_rite && b.knows_doctrine;
}

bool ReadKnowledgeOnce(const KnowledgeBindings &b, std::uint64_t epoch,
                       PlayedDoctrineKnowledge &out) {
  CoreSnapshotPrefix frame{};
  void *character = nullptr;
  if (!Frame(b, frame, character, out.unavailable_reason)) return false;
  out.capture_epoch = epoch;
  out.date_raw = frame.clock.date_raw;
  out.played_character_id = frame.played_character_id;
  const auto rite_id = Load<std::uint32_t>(character, religion::kCharacterRiteIdOffset);
  if (rite_id != religion::kAbsentReference) out.rite_id = rite_id;

  const auto *extension = Load<const void *>(character, kCharacterKnowledgeExtensionOffset);
  const void *collection_owner = extension;
  std::size_t array_offset = kLearnedDoctrineArrayOffset;
  std::size_t count_offset = kLearnedDoctrineCountOffset;
  out.knowledge_source = "character_extension";
  if (!extension) {
    // The native predicate follows the actual actor Rite, including its native
    // absent-reference object. Reading that object is different from inventing
    // an empty default when the object getter fails.
    collection_owner = b.context.character_rite(character);
    if (!collection_owner || Load<std::uint32_t>(collection_owner,
        religion::kReferenceIdentityOffset) != rite_id) {
      out.unavailable_reason = "rite_unavailable"; return false;
    }
    array_offset = kMainRiteDoctrineArrayOffset;
    count_offset = kMainRiteDoctrineCountOffset;
    out.knowledge_source = "rite_default";
  }
  const auto *definitions = Load<const void *const *>(collection_owner, array_offset);
  const auto count = Load<std::int32_t>(collection_owner, count_offset);
  if (count < 0 || (count != 0 && !definitions)) {
    out.unavailable_reason = "knowledge_collection_unavailable"; return false;
  }
  for (std::int32_t i = 0; i < count; ++i) {
    KnownDoctrineRow row{};
    if (!CopyDoctrineDefinition12002(definitions[i], row.definition)) {
      out.unavailable_reason = "doctrine_definition_unavailable"; return false;
    }
    row.definition.source = out.knowledge_source;
    row.native_knows_doctrine = b.knows_doctrine(character, definitions[i]);
    out.learned_rows.push_back(std::move(row));
  }
  if (ResolveCoreCharacter(b.context.core, frame.played_character_id) != character) {
    out.unavailable_reason = "state_changed"; return false;
  }
  out.available = true;
  out.unavailable_reason.clear();
  return true;
}

bool ReadLookupOnce(const KnowledgeBindings &b, std::string_view key,
                    std::uint64_t epoch, PlayedDoctrineKnowledgeLookup &out) {
  CoreSnapshotPrefix frame{};
  void *character = nullptr;
  if (!Frame(b, frame, character, out.unavailable_reason)) return false;
  out.capture_epoch = epoch;
  out.date_raw = frame.clock.date_raw;
  out.played_character_id = frame.played_character_id;
  out.requested_doctrine_key = key;
  const auto *database = *b.definition_database_global;
  if (!database) { out.unavailable_reason = "definition_registry_unavailable"; return false; }
  const auto *definitions = Load<const void *const *>(database, kDefinitionRegistryArrayOffset);
  const auto count = Load<std::int32_t>(database, kDefinitionRegistryCountOffset);
  if (count < 0 || (count != 0 && !definitions)) {
    out.unavailable_reason = "definition_registry_unavailable"; return false;
  }
  for (std::int32_t i = 0; i < count; ++i) {
    DoctrineRow definition{};
    if (!CopyDoctrineDefinition12002(definitions[i], definition)) {
      out.unavailable_reason = "doctrine_definition_unavailable"; return false;
    }
    if (definition.doctrine_key != key) continue;
    definition.source = "definition_registry";
    out.native_knows_doctrine = b.knows_doctrine(character, definitions[i]);
    out.definition = std::move(definition);
    break;
  }
  if (ResolveCoreCharacter(b.context.core, frame.played_character_id) != character) {
    out.unavailable_reason = "state_changed"; return false;
  }
  out.available = true;
  out.unavailable_reason.clear();
  return true;
}

std::string Quoted(std::string_view value) {
  std::string out = "\"";
  constexpr char hex[] = "0123456789abcdef";
  for (const auto c : value) {
    const auto byte = static_cast<unsigned char>(c);
    if (c == '\\' || c == '"') { out += '\\'; out += c; }
    else if (byte < 32) { out += "\\u00"; out += hex[byte >> 4]; out += hex[byte & 15]; }
    else out += c;
  }
  return out + '"';
}
std::string Row(const DoctrineRow &row) {
  return "{\"doctrine_key\":" + Quoted(row.doctrine_key) +
      ",\"group_key\":" + Quoted(row.group_key) + ",\"source\":" + Quoted(row.source) + "}";
}
std::string Prefix(std::string_view schema, bool available, std::string_view reason,
                   std::uint64_t epoch, std::int32_t date, std::int32_t actor) {
  return "{\"schema\":" + Quoted(schema) + ",\"game_version\":\"1.20.0.2\","
      "\"executable_sha256\":" + Quoted(kExecutableSha256) +
      ",\"available\":" + (available ? "true" : "false") +
      ",\"unavailable_reason\":" + (available ? "null" : Quoted(reason)) +
      ",\"capture_epoch\":" + std::to_string(epoch) +
      ",\"date_raw\":" + std::to_string(date) +
      ",\"played_character_id\":" + std::to_string(actor);
}
} // namespace

KnowledgeBindings BindDoctrineKnowledgeImage12002(std::uintptr_t base,
    std::string_view sha) noexcept {
  KnowledgeBindings b{};
  if (!base || sha != kExecutableSha256) return b;
  b.context = religion::BindReligionContextImage12002(base, sha);
  b.knows_doctrine = reinterpret_cast<NativeKnowsDoctrine>(base + kCharacterKnowsDoctrineRva);
  b.definition_database_global = reinterpret_cast<void *const *>(base + kDoctrineDatabasePointerRva);
  return b;
}

bool ReadPlayedDoctrineKnowledge12002(const KnowledgeBindings &b, std::uint64_t epoch,
    PlayedDoctrineKnowledge &output) noexcept {
  output = {}; output.capture_epoch = epoch;
  if (!CanRead(b)) return false;
  PlayedDoctrineKnowledge first{}, second{};
  if (!ReadKnowledgeOnce(b, epoch, first)) { output.unavailable_reason = first.unavailable_reason; return false; }
  if (!ReadKnowledgeOnce(b, epoch, second)) { output.unavailable_reason = second.unavailable_reason; return false; }
  if (first.date_raw != second.date_raw || first.played_character_id != second.played_character_id ||
      first.rite_id != second.rite_id || first.knowledge_source != second.knowledge_source ||
      first.learned_rows != second.learned_rows) {
    output.unavailable_reason = "state_changed"; return false;
  }
  output = std::move(first);
  return true;
}

bool ReadPlayedDoctrineKnowledgeByKey12002(const KnowledgeBindings &b,
    std::string_view key, std::uint64_t epoch, PlayedDoctrineKnowledgeLookup &output) noexcept {
  output = {}; output.capture_epoch = epoch; output.requested_doctrine_key = key;
  if (!CanRead(b) || !b.definition_database_global) return false;
  PlayedDoctrineKnowledgeLookup first{}, second{};
  if (!ReadLookupOnce(b, key, epoch, first)) { output.unavailable_reason = first.unavailable_reason; return false; }
  if (!ReadLookupOnce(b, key, epoch, second)) { output.unavailable_reason = second.unavailable_reason; return false; }
  if (first.date_raw != second.date_raw || first.played_character_id != second.played_character_id ||
      first.definition != second.definition || first.native_knows_doctrine != second.native_knows_doctrine) {
    output.unavailable_reason = "state_changed"; return false;
  }
  output = std::move(first);
  return true;
}

std::string SerializePlayedDoctrineKnowledge12002(const PlayedDoctrineKnowledge &value) {
  std::string out = Prefix("ck3_12002_played_doctrine_knowledge_v1", value.available,
      value.unavailable_reason, value.capture_epoch, value.date_raw, value.played_character_id) +
      ",\"rite_id\":" + (value.rite_id ? std::to_string(*value.rite_id) : "null") +
      ",\"knowledge_source\":" + (value.available ? Quoted(value.knowledge_source) : "null") +
      ",\"learned_rows\":[";
  bool comma = false;
  for (const auto &row : value.learned_rows) {
    if (comma) out += ',';
    comma = true;
    const auto definition = Row(row.definition);
    out += definition.substr(0, definition.size() - 1) + ",\"native_knows_doctrine\":" +
        (row.native_knows_doctrine ? "true" : "false") + "}";
  }
  return out + "]}";
}

std::string SerializePlayedDoctrineKnowledgeLookup12002(const PlayedDoctrineKnowledgeLookup &value) {
  return Prefix("ck3_12002_played_doctrine_knowledge_lookup_v1", value.available,
      value.unavailable_reason, value.capture_epoch, value.date_raw, value.played_character_id) +
      ",\"requested_doctrine_key\":" + Quoted(value.requested_doctrine_key) +
      ",\"definition_found\":" + (value.definition ? "true" : "false") +
      ",\"definition\":" + (value.definition ? Row(*value.definition) : "null") +
      ",\"native_knows_doctrine\":" + (value.native_knows_doctrine ?
        (*value.native_knows_doctrine ? "true" : "false") : "null") + "}";
}

} // namespace xar::ck3_12002::religion::doctrine12002
