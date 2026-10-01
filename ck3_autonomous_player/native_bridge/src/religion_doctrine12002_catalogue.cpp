#include "xar_bridge/religion_doctrine12002_catalogue.hpp"

#include <cstring>

namespace xar::ck3_12002::religion::doctrine12002 {
namespace {
template<class T> T Load(const void *object, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value));
  return value;
}
bool Fail(DoctrineCatalogue &out, const char *reason) {
  out.unavailable_reason = reason; return false;
}
bool ReadLoadedRows(const CatalogueBindings &b, std::vector<DoctrineRow> &rows,
    std::vector<const void *> *definitions, std::string &failure) {
  rows.clear(); if (definitions) definitions->clear(); failure.clear();
  if (!b.enabled || !b.database_slot) { failure = "bindings_unavailable"; return false; }
  const auto *database = *b.database_slot;
  if (!database) { failure = "doctrine_database_unavailable"; return false; }
  const auto count = Load<std::int32_t>(database, kDoctrineDatabaseCountOffset);
  auto **data = Load<const void **>(database, kDoctrineDatabaseArrayOffset);
  if (count < 0 || (count && !data)) { failure = "doctrine_registry_unavailable"; return false; }
  for (std::int32_t i = 0; i < count; ++i) {
    DoctrineRow row{};
    if (!CopyDoctrineDefinition12002(data[i], row)) {
      failure = "doctrine_definition_unavailable"; return false;
    }
    row.source = "loaded_doctrine_registry";
    rows.push_back(std::move(row));
    if (definitions) definitions->push_back(data[i]);
  }
  if (*b.database_slot != database || Load<std::int32_t>(database, kDoctrineDatabaseCountOffset) != count ||
      Load<const void **>(database, kDoctrineDatabaseArrayOffset) != data) {
    failure = "doctrine_registry_changed"; return false;
  }
  return true;
}
bool ReadOnce(const CatalogueBindings &b, std::uint64_t epoch, DoctrineCatalogue &out) {
  CoreSnapshotPrefix frame{};
  if (!ReadCoreSnapshot(b.core, frame) || !frame.map_ready || !frame.has_played_character ||
      !frame.played_character_alive) return Fail(out, "played_character_unavailable");
  if (!frame.clock.paused) return Fail(out, "frame_not_paused");
  out.capture_epoch = epoch;
  out.date_raw = frame.clock.date_raw;
  out.played_character_id = frame.played_character_id;
  if (!ReadLoadedRows(b, out.rows, nullptr, out.unavailable_reason)) return false;
  out.catalogue_complete = true;
  out.available = true;
  return true;
}
std::string Quote(std::string_view v) {
  std::string out = "\""; constexpr char hex[] = "0123456789abcdef";
  for (const unsigned char byte : v) {
    if (byte == '"' || byte == '\\') { out += '\\'; out += static_cast<char>(byte); }
    else if (byte < 32) { out += "\\u00"; out += hex[byte >> 4]; out += hex[byte & 15]; }
    else out += static_cast<char>(byte);
  }
  return out + '"';
}
} // namespace

CatalogueBindings BindDoctrineCatalogueImage12002(std::uintptr_t base, std::string_view sha) noexcept {
  CatalogueBindings b{};
  if (!base || sha != kExecutableSha256) return b;
  b.enabled = true; b.core = BindCoreImage(base, sha);
  b.database_slot = reinterpret_cast<void **>(base + kDoctrineDatabasePointerRva);
  return b;
}

bool ReadPlayedDoctrineCatalogue12002(const CatalogueBindings &b,
    std::uint64_t epoch, DoctrineCatalogue &out) noexcept {
  out = {}; out.capture_epoch = epoch;
  if (!b.enabled || !b.core.enabled) return false;
  try {
    DoctrineCatalogue a{}, z{};
    if (!ReadOnce(b, epoch, a)) { out.unavailable_reason = a.unavailable_reason; return false; }
    if (!ReadOnce(b, epoch, z)) { out.unavailable_reason = z.unavailable_reason; return false; }
    if (a.played_character_id != z.played_character_id || a.date_raw != z.date_raw || a.rows != z.rows)
      return Fail(out, "state_changed");
    out = std::move(a); return true;
  } catch (...) { return Fail(out, "doctrine_copy_failed"); }
}

bool ResolveDoctrineDefinitionByStableKey12002(const CatalogueBindings &b,
    std::string_view key, const void *&definition, std::string &failure) noexcept {
  definition = nullptr; failure.clear();
  try {
    std::vector<DoctrineRow> rows; std::vector<const void *> definitions;
    if (!ReadLoadedRows(b, rows, &definitions, failure)) return false;
    for (std::size_t i = 0; i < rows.size(); ++i) {
      if (rows[i].doctrine_key == key) { definition = definitions[i]; break; }
    }
    return true;
  } catch (...) { definition = nullptr; failure = "doctrine_copy_failed"; return false; }
}

std::string SerializeDoctrineCatalogue12002(const DoctrineCatalogue &v) {
  std::string rows = "[";
  for (const auto &row : v.rows) {
    if (rows.size() > 1) rows += ',';
    rows += "{\"doctrine_key\":" + Quote(row.doctrine_key) + ",\"group_key\":" + Quote(row.group_key) +
        ",\"source\":" + Quote(row.source) + '}';
  }
  rows += ']';
  return "{\"schema\":\"ck3_12002_loaded_doctrine_catalogue_v1\",\"available\":" +
      std::string(v.available ? "true" : "false") + ",\"unavailable_reason\":" +
      (v.available ? "null" : Quote(v.unavailable_reason)) +
      ",\"catalogue_complete\":" + (v.catalogue_complete ? "true" : "false") +
      ",\"source\":" + Quote(v.source) + ",\"capture_epoch\":" + std::to_string(v.capture_epoch) +
      ",\"date_raw\":" + std::to_string(v.date_raw) +
      ",\"played_character_id\":" + std::to_string(v.played_character_id) +
      ",\"rows\":" + rows + '}';
}
} // namespace xar::ck3_12002::religion::doctrine12002
