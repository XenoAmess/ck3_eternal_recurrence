#include "xar_bridge/diac_literal_numeric_inputs_12003.hpp"
#include "xar_bridge/ck3_12003.hpp"

#include <charconv>
#include <limits>
#include <utility>

namespace xar::ck3_12003 {
namespace {
static_assert(sizeof(void *) == 8, "The frozen Diac ABI requires x64 pointers");

const void *Address(const void *base, std::uintptr_t offset) {
  if (!base) return nullptr;
  const auto raw = reinterpret_cast<std::uintptr_t>(base);
  if (offset > std::numeric_limits<std::uintptr_t>::max() - raw) return nullptr;
  return reinterpret_cast<const void *>(raw + offset);
}

template <typename T>
bool Read(const DiacLiteralNumericBindings12003 &b, const void *base,
          std::uintptr_t offset, T &value) {
  const auto address = Address(base, offset);
  return address && b.read_memory &&
         b.read_memory(b.read_context, address, &value, sizeof(value));
}

std::optional<std::string> Identity(const void *address) {
  if (!address) return std::nullopt;
  char buffer[2 * sizeof(std::uintptr_t)]{};
  const auto result = std::to_chars(buffer, buffer + sizeof(buffer),
                                  reinterpret_cast<std::uintptr_t>(address), 16);
  return std::string("0x") + std::string(buffer, result.ptr);
}

void Missing(std::string &reason, const char *value) {
  if (reason.empty()) reason = value;
}

template <typename T>
std::optional<std::vector<T>> Array(const DiacLiteralNumericBindings12003 &b,
                                  const void *base, std::uintptr_t pointer_offset,
                                  const std::optional<std::int32_t> &count) {
  if (!count || *count < 0) return std::nullopt;
  std::vector<T> values;
  if (*count == 0) return values;
  const void *data = nullptr;
  if (!Read(b, base, pointer_offset, data) || !data) return std::nullopt;
  for (std::int32_t i = 0; i < *count; ++i) {
    T value{};
    if (!Read(b, data, static_cast<std::uintptr_t>(i) * sizeof(T), value)) {
      return std::nullopt;
    }
    values.push_back(value);
  }
  return values;
}

DiacLiteralNumericDeclaration12003 Declaration(
    const DiacLiteralNumericBindings12003 &b, const void *declaration,
    std::int32_t native_index) {
  DiacLiteralNumericDeclaration12003 out{};
  out.native_index = native_index;
  out.declaration_identity = Identity(declaration);
  std::uint32_t gate = 0;
  if (!Read(b, declaration, 0x280U, gate)) {
    out.reason = "declaration_scale_gate_280_unread";
    return out;
  }
  out.scale_gate_280_raw = gate;
  if (gate != 0U) {
    out.reason = "dynamic_scale_9d7060";
    return out;
  }

  // C85860 is invoked by the actual finalizer before testing keycount, even
  // for a copied empty modifier. Observe its slot once for this occurrence.
  const void *provider = nullptr;
  if (Read(b, b.metadata_provider_slot, 0U, provider)) {
    out.metadata_provider_loaded = provider != nullptr;
  }
  if (!out.metadata_provider_loaded.value_or(false)) {
    out.reason = "metadata_provider_c85860_unavailable";
  }

  auto &pc = out.properties.emplace();
  std::int32_t count = 0;
  if (Read(b, declaration, 0xCU, count)) pc.keys_count = count;
  if (Read(b, declaration, 0x74U, count)) pc.values_count = count;
  pc.keys_u16 = Array<std::uint16_t>(b, declaration, 0U, pc.keys_count);
  pc.values_q64 = Array<std::int64_t>(b, declaration, 0x68U, pc.values_count);
  const bool complete_pc = pc.keys_count && pc.values_count &&
      *pc.keys_count >= 0 && *pc.values_count >= 0 &&
      *pc.keys_count == *pc.values_count && pc.keys_u16 && pc.values_q64;
  if (!complete_pc) Missing(out.reason, "declaration_properties_unread_or_mismatched");

  bool complete_metadata = out.metadata_provider_loaded.value_or(false);
  if (complete_metadata && pc.keys_u16) {
    for (std::size_t i = 0; i < pc.keys_u16->size(); ++i) {
      DiacLiteralNumericMetadata12003 metadata{};
      metadata.native_index = static_cast<std::int32_t>(i);
      metadata.key_u16 = (*pc.keys_u16)[i];
      const void *descriptor = nullptr;
      if (metadata.key_u16 == std::uint16_t{0xFFFFU}) {
        metadata.selection = "static_5451f40";
        descriptor = b.sentinel_metadata;
      } else {
        metadata.selection = "provider_50_c8";
        const void *mapper = nullptr;
        if (Read(b, provider, 0x50U, mapper)) {
          descriptor = Address(mapper,
              static_cast<std::uintptr_t>(metadata.key_u16) * 0xC8U);
        }
      }
      metadata.metadata_identity = Identity(descriptor);
      std::uint8_t byte = 0;
      if (Read(b, descriptor, 0xBAU, byte)) {
        metadata.byte_ba_raw = byte;
        // The actual BA branch bypasses B8 entirely when BA is nonzero.
        if (byte == 0U) {
          if (Read(b, descriptor, 0xB8U, byte)) metadata.byte_b8_raw = byte;
          else complete_metadata = false;
        }
      } else {
        complete_metadata = false;
      }
      if (!metadata.byte_ba_raw ||
          (*metadata.byte_ba_raw == 0U && !metadata.byte_b8_raw)) {
        Missing(out.reason, "property_metadata_bytes_unread");
      }
      out.metadata_rows.push_back(std::move(metadata));
    }
  } else if (!pc.keys_u16) {
    complete_metadata = false;
  }
  out.ready = complete_pc && complete_metadata;
  if (out.ready) {
    out.status = "available";
    out.reason.clear();
  }
  return out;
}

void String(std::string &out, std::string_view value) {
  static constexpr char hex[] = "0123456789abcdef";
  out += '"';
  for (const char ch : value) {
    switch (ch) {
    case '"': out += "\\\""; break;
    case '\\': out += "\\\\"; break;
    case '\n': out += "\\n"; break;
    case '\r': out += "\\r"; break;
    case '\t': out += "\\t"; break;
    default: {
      const auto byte = static_cast<unsigned char>(ch);
      if (byte < 0x20U) {
        out += "\\u00";
        out += hex[byte >> 4U];
        out += hex[byte & 0xFU];
      } else out += ch;
    }
    }
  }
  out += '"';
}

template <typename T>
void Number(std::string &out, const std::optional<T> &value) {
  if (value) out += std::to_string(*value);
  else out += "null";
}

void OptionalString(std::string &out, const std::optional<std::string> &value) {
  if (value) String(out, *value);
  else out += "null";
}

void Boolean(std::string &out, const std::optional<bool> &value) {
  if (value) out += *value ? "true" : "false";
  else out += "null";
}

void Reason(std::string &out, const std::string &value) {
  if (value.empty()) out += "null";
  else String(out, value);
}

template <typename T>
void Numbers(std::string &out, const std::optional<std::vector<T>> &values) {
  if (!values) { out += "null"; return; }
  out += '[';
  bool first = true;
  for (const auto value : *values) {
    if (!first) out += ',';
    first = false;
    out += std::to_string(value);
  }
  out += ']';
}

void PropertiesJson(std::string &out, const DiacLiteralNumericProperties12003 &pc) {
  out += "{\"keys_count\":";
  Number(out, pc.keys_count);
  out += ",\"values_count\":";
  Number(out, pc.values_count);
  out += ",\"keys_u16\":";
  Numbers(out, pc.keys_u16);
  out += ",\"values_q64\":";
  Numbers(out, pc.values_q64);
  out += '}';
}

void MetadataJson(std::string &out, const DiacLiteralNumericMetadata12003 &row) {
  out += "{\"native_index\":" + std::to_string(row.native_index);
  out += ",\"key_u16\":" + std::to_string(row.key_u16);
  out += ",\"selection\":";
  String(out, row.selection);
  out += ",\"metadata_identity\":";
  OptionalString(out, row.metadata_identity);
  out += ",\"byte_ba_raw\":";
  Number(out, row.byte_ba_raw);
  out += ",\"byte_b8_raw\":";
  Number(out, row.byte_b8_raw);
  out += '}';
}

void DeclarationJson(std::string &out, const DiacLiteralNumericDeclaration12003 &row) {
  out += "{\"status\":";
  String(out, row.status);
  out += ",\"ready\":";
  out += row.ready ? "true" : "false";
  out += ",\"native_index\":" + std::to_string(row.native_index);
  out += ",\"declaration_identity\":";
  OptionalString(out, row.declaration_identity);
  out += ",\"scale_gate_280_raw\":";
  Number(out, row.scale_gate_280_raw);
  out += ",\"properties\":";
  if (row.properties) PropertiesJson(out, *row.properties);
  else out += "null";
  out += ",\"metadata_provider_loaded\":";
  Boolean(out, row.metadata_provider_loaded);
  out += ",\"metadata_rows\":[";
  bool first = true;
  for (const auto &metadata : row.metadata_rows) {
    if (!first) out += ',';
    first = false;
    MetadataJson(out, metadata);
  }
  out += "],\"reason\":";
  Reason(out, row.reason);
  out += '}';
}
} // namespace

DiacLiteralNumericBindings12003 BindDiacLiteralNumericInputs12003(
    std::uintptr_t image_base, std::string_view executable_sha256) {
  DiacLiteralNumericBindings12003 out{};
  if (!image_base || executable_sha256 != kExecutableSha256) return out;
  out.enabled = true;
  out.metadata_provider_slot = reinterpret_cast<const void *>(image_base + 0x5D1F7B0U);
  out.sentinel_metadata = reinterpret_cast<const void *>(image_base + 0x5451F40U);
  return out;
}

DiacLiteralNumericSnapshot12003 ReadDiacLiteralNumericInputs12003(
    const DiacLiteralNumericBindings12003 &b, const void *full_character_id_address,
    const void *selected_definition_block) {
  DiacLiteralNumericSnapshot12003 out{};
  out.scope_id_address_identity = Identity(full_character_id_address);
  out.definition_block_identity = Identity(selected_definition_block);
  if (!b.enabled || !b.read_memory) {
    out.reason = "diac_literal_numeric_binding_unavailable";
    return out;
  }
  std::int32_t full_id = 0;
  if (Read(b, full_character_id_address, 0U, full_id)) out.scope_character_full_id = full_id;
  else Missing(out.reason, "scope_character_full_id_unread");
  const void *array = nullptr;
  if (Read(b, selected_definition_block, 0U, array)) out.declaration_array_present = array != nullptr;
  else Missing(out.reason, "declaration_array_pointer_unread");
  std::int32_t count = 0;
  if (Read(b, selected_definition_block, 0xCU, count)) out.declaration_count_raw = count;
  else Missing(out.reason, "declaration_count_unread");
  if (!out.declaration_count_raw || !out.declaration_array_present) return out;
  if (count < 0) {
    Missing(out.reason, "negative_declaration_count");
    return out;
  }
  if (count > 0 && !array) {
    Missing(out.reason, "declaration_array_missing");
    return out;
  }
  for (std::int32_t i = 0; i < count; ++i) {
    const void *declaration = nullptr;
    DiacLiteralNumericDeclaration12003 row{};
    if (Read(b, array, static_cast<std::uintptr_t>(i) * 8U, declaration)) {
      row = Declaration(b, declaration, i);
    } else {
      row.native_index = i;
      row.reason = "declaration_pointer_unread";
    }
    if (!row.ready) {
      if (out.reason.empty()) out.reason = row.reason;
    }
    out.declarations.push_back(std::move(row));
    // An unread physical pointer does not prevent observing later slots.
  }
  out.ready = out.reason.empty() && out.scope_character_full_id.has_value() &&
      out.scope_id_address_identity.has_value() && out.definition_block_identity.has_value();
  if (out.ready) out.status = "available";
  return out;
}

std::string SerializeDiacLiteralNumericInputs12003(
    const DiacLiteralNumericSnapshot12003 &snapshot) {
  std::string out = "{\"status\":";
  String(out, snapshot.status);
  out += ",\"ready\":";
  out += snapshot.ready ? "true" : "false";
  out += ",\"scope_character_full_id\":";
  Number(out, snapshot.scope_character_full_id);
  out += ",\"scope_id_address_identity\":";
  OptionalString(out, snapshot.scope_id_address_identity);
  out += ",\"definition_block_identity\":";
  OptionalString(out, snapshot.definition_block_identity);
  out += ",\"declaration_count_raw\":";
  Number(out, snapshot.declaration_count_raw);
  out += ",\"declaration_array_present\":";
  Boolean(out, snapshot.declaration_array_present);
  out += ",\"declarations\":[";
  bool first = true;
  for (const auto &row : snapshot.declarations) {
    if (!first) out += ',';
    first = false;
    DeclarationJson(out, row);
  }
  out += "],\"reason\":";
  Reason(out, snapshot.reason);
  out += '}';
  return out;
}

} // namespace xar::ck3_12003
