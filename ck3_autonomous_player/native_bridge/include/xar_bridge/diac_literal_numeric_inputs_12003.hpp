#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_12003 {

// Independent raw input contract for the source-closed literal subset of
// 325B080. The supplied scope is a whole DWORD ID address, not Character*.
struct DiacLiteralNumericProperties12003 {
  std::optional<std::int32_t> keys_count;
  std::optional<std::int32_t> values_count;
  std::optional<std::vector<std::uint16_t>> keys_u16;
  std::optional<std::vector<std::int64_t>> values_q64;
  friend bool operator==(const DiacLiteralNumericProperties12003 &,
                         const DiacLiteralNumericProperties12003 &) = default;
};

struct DiacLiteralNumericMetadata12003 {
  std::int32_t native_index = 0;
  std::uint16_t key_u16 = 0;
  std::string selection;
  std::optional<std::string> metadata_identity;
  std::optional<std::uint8_t> byte_ba_raw;
  std::optional<std::uint8_t> byte_b8_raw;
  friend bool operator==(const DiacLiteralNumericMetadata12003 &,
                         const DiacLiteralNumericMetadata12003 &) = default;
};

struct DiacLiteralNumericDeclaration12003 {
  std::string status = "partial";
  bool ready = false;
  std::int32_t native_index = 0;
  std::optional<std::string> declaration_identity;
  std::optional<std::uint32_t> scale_gate_280_raw;
  std::optional<DiacLiteralNumericProperties12003> properties;
  std::optional<bool> metadata_provider_loaded;
  std::vector<DiacLiteralNumericMetadata12003> metadata_rows;
  std::string reason;
  friend bool operator==(const DiacLiteralNumericDeclaration12003 &,
                         const DiacLiteralNumericDeclaration12003 &) = default;
};

struct DiacLiteralNumericSnapshot12003 {
  std::string status = "partial";
  bool ready = false;
  std::optional<std::int32_t> scope_character_full_id;
  std::optional<std::string> scope_id_address_identity;
  std::optional<std::string> definition_block_identity;
  std::optional<std::int32_t> declaration_count_raw;
  std::optional<bool> declaration_array_present;
  std::vector<DiacLiteralNumericDeclaration12003> declarations;
  std::string reason;
  friend bool operator==(const DiacLiteralNumericSnapshot12003 &,
                         const DiacLiteralNumericSnapshot12003 &) = default;
};

using DiacLiteralNumericReadMemory12003 =
    bool (*)(void *context, const void *address, void *output,
             std::size_t size) noexcept;

struct DiacLiteralNumericBindings12003 {
  bool enabled = false;
  const void *metadata_provider_slot = nullptr;
  const void *sentinel_metadata = nullptr;
  DiacLiteralNumericReadMemory12003 read_memory = nullptr;
  void *read_context = nullptr;
};

DiacLiteralNumericBindings12003 BindDiacLiteralNumericInputs12003(
    std::uintptr_t image_base, std::string_view executable_sha256);
DiacLiteralNumericSnapshot12003 ReadDiacLiteralNumericInputs12003(
    const DiacLiteralNumericBindings12003 &bindings,
    const void *full_character_id_address,
    const void *selected_definition_block);
std::string SerializeDiacLiteralNumericInputs12003(
    const DiacLiteralNumericSnapshot12003 &snapshot);

} // namespace xar::ck3_12003
