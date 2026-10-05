#include "xar_bridge/diac_literal_numeric_inputs_12003.hpp"

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <memory>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace {
void Require(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}
struct Memory {
  struct Region { std::unique_ptr<std::byte[]> bytes; std::size_t size; };
  struct Denied { std::uintptr_t address; std::size_t size; std::size_t attempts = 0; };
  std::vector<Region> regions;
  std::vector<Denied> denied;
  std::uintptr_t provider_watch = 0;
  std::vector<std::uintptr_t> key_count_watch;
  std::vector<char> literal_read_order;
  void *Allocate(std::size_t size) {
    auto bytes = std::make_unique<std::byte[]>(size);
    void *address = bytes.get();
    regions.push_back({std::move(bytes), size});
    return address;
  }
  template <typename T> void Put(void *address, std::size_t offset, T value) {
    std::memcpy(static_cast<std::byte *>(address) + offset, &value, sizeof(value));
  }
  void Deny(const void *address, std::size_t offset, std::size_t size) {
    denied.push_back({reinterpret_cast<std::uintptr_t>(address) + offset, size});
  }
  void WatchCount(const void *declaration) {
    key_count_watch.push_back(reinterpret_cast<std::uintptr_t>(declaration) + 0xC);
  }
  std::size_t Attempts() const {
    std::size_t count = 0;
    for (const auto &entry : denied) count += entry.attempts;
    return count;
  }
  static bool Read(void *context, const void *address, void *output,
                   std::size_t size) noexcept {
    auto &memory = *static_cast<Memory *>(context);
    const auto begin = reinterpret_cast<std::uintptr_t>(address);
    if (begin == memory.provider_watch && size == 8)
      memory.literal_read_order.push_back('P');
    if (size == 4) {
      for (const auto watched : memory.key_count_watch) {
        if (begin == watched) { memory.literal_read_order.push_back('K'); break; }
      }
    }
    for (auto &entry : memory.denied) {
      if (begin < entry.address + entry.size && entry.address < begin + size) {
        ++entry.attempts;
        return false;
      }
    }
    for (const auto &region : memory.regions) {
      const auto base = reinterpret_cast<std::uintptr_t>(region.bytes.get());
      if (begin >= base && begin - base <= region.size &&
          size <= region.size - static_cast<std::size_t>(begin - base)) {
        std::memcpy(output, address, size);
        return true;
      }
    }
    return false;
  }
};
constexpr std::uint32_t kScopeFullId = 0xAB000001U;
constexpr std::string_view kExecutableSha256 =
    "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";
using Snapshot = xar::ck3_12003::DiacLiteralNumericSnapshot12003;

// The scope is an allocated whole DWORD ID address, not a Character pointer.
// All source bytes are initialized before either complete snapshot. Read-order
// logging records observations only; it never evolves the physical frame.
struct Fixture {
  Memory memory;
  xar::ck3_12003::DiacLiteralNumericBindings12003 bindings{};
  void *scope_id = memory.Allocate(4);
  void *definition_block = memory.Allocate(0x10);
  void *declaration_pointers = memory.Allocate(2 * 8);
  void *declaration = memory.Allocate(0x284);
  void *second_declaration = memory.Allocate(0x284);
  void *provider_slot = memory.Allocate(8);
  void *provider = memory.Allocate(0x58);
  void *metadata_table = memory.Allocate(9 * 0xC8);
  void *sentinel_metadata = memory.Allocate(0xC8);

  void Property(void *pc, const std::vector<std::uint16_t> &keys,
                const std::vector<std::int64_t> &values) {
    Require(keys.size() == values.size(), "Diac literal property pair size");
    memory.Put(pc, 0xC, static_cast<std::int32_t>(keys.size()));
    memory.Put(pc, 0x74, static_cast<std::int32_t>(values.size()));
    if (keys.empty()) return;
    void *key_data = memory.Allocate(keys.size() * 2);
    void *value_data = memory.Allocate(values.size() * 8);
    memory.Put(pc, 0, key_data);
    memory.Put(pc, 0x68, value_data);
    for (std::size_t i = 0; i < keys.size(); ++i) {
      memory.Put(key_data, i * 2, keys[i]);
      memory.Put(value_data, i * 8, values[i]);
    }
  }
  void Flags(std::uint16_t key, std::uint8_t ba, std::uint8_t b8) {
    const auto offset = static_cast<std::size_t>(key) * 0xC8;
    memory.Put(metadata_table, offset + 0xBA, ba);
    memory.Put(metadata_table, offset + 0xB8, b8);
  }
  Fixture() {
    bindings.enabled = true;
    bindings.metadata_provider_slot = provider_slot;
    bindings.sentinel_metadata = sentinel_metadata;
    bindings.read_memory = &Memory::Read;
    bindings.read_context = &memory;
    memory.Put(scope_id, 0, kScopeFullId);
    memory.Put(definition_block, 0, declaration_pointers);
    memory.Put(definition_block, 0xC, std::int32_t{1});
    memory.Put(declaration_pointers, 0, declaration);
    memory.Put(declaration_pointers, 8, second_declaration);
    memory.Put(provider_slot, 0, provider);
    memory.Put(provider, 0x50, metadata_table);
    Property(declaration, {5, 6}, {150000, -150000});
    Flags(5, std::uint8_t{0}, std::uint8_t{0});
    Flags(6, std::uint8_t{1}, std::uint8_t{0});
    Flags(7, std::uint8_t{0}, std::uint8_t{3});
    Flags(8, std::uint8_t{0}, std::uint8_t{2});
    memory.provider_watch = reinterpret_cast<std::uintptr_t>(provider_slot);
    memory.WatchCount(declaration);
    memory.WatchCount(second_declaration);
    memory.Deny(metadata_table, 6 * 0xC8 + 0xB8, 1);
  }
  Snapshot Observe(std::size_t literal_occurrences) {
    const auto first = xar::ck3_12003::ReadDiacLiteralNumericInputs12003(
        bindings, scope_id, definition_block);
    const auto second = xar::ck3_12003::ReadDiacLiteralNumericInputs12003(
        bindings, scope_id, definition_block);
    Require(first == second, "Diac literal whole snapshots differ in fixed frame");
    Require(memory.Attempts() == 0, "Diac literal unused metadata/PC fields were demanded");
    Require(memory.literal_read_order.size() == literal_occurrences * 4,
            "Diac literal provider must be loaded once per literal physical occurrence");
    for (std::size_t i = 0; i < memory.literal_read_order.size(); i += 2)
      Require(memory.literal_read_order.at(i) == 'P' && memory.literal_read_order.at(i + 1) == 'K',
              "Diac literal loaded-provider getter must precede key count even for empty PC");
    Require(first.scope_character_full_id == static_cast<std::int32_t>(kScopeFullId) &&
                first.scope_id_address_identity && first.definition_block_identity,
            "Diac literal scope must retain the actual whole DWORD ID address");
    return first;
  }
};
void Save(const std::filesystem::path &directory, const char *name,
          const Snapshot &snapshot) {
  if (directory.empty()) return;
  std::ofstream output(directory / (std::string("diac-literal-numeric-") + name + ".json"),
                       std::ios::binary);
  output << xar::ck3_12003::SerializeDiacLiteralNumericInputs12003(snapshot);
  if (!output) throw std::runtime_error("Diac literal numeric wire write failed");
}
void RawPC(const auto &row, const std::vector<std::uint16_t> &keys,
           const std::vector<std::int64_t> &values) {
  Require(row.properties && row.properties->keys_u16 && row.properties->values_q64 &&
              *row.properties->keys_u16 == keys && *row.properties->values_q64 == values &&
              row.properties->keys_count == static_cast<std::int32_t>(keys.size()),
          "Diac literal actual paired source operands differ");
  Require(row.properties->values_count == static_cast<std::int32_t>(values.size()),
          "Diac literal actual values count differs");
}
void Metadata(const auto &row, std::size_t index, std::uint16_t key,
              const char *selection, std::uint8_t ba,
              const std::optional<std::uint8_t> &b8) {
  Require(row.metadata_rows.size() > index, "Diac literal metadata ordinal absent");
  const auto &metadata = row.metadata_rows.at(index);
  Require(metadata.native_index == static_cast<std::int32_t>(index) &&
              metadata.key_u16 == key && metadata.selection == selection &&
              metadata.metadata_identity && metadata.byte_ba_raw == ba && metadata.byte_b8_raw == b8,
          "Diac literal physical metadata mapping or BA-before-B8 demand differs");
}
void ExactBindings() {
  constexpr std::uintptr_t base = 0x140000000;
  const auto binding = xar::ck3_12003::BindDiacLiteralNumericInputs12003(base, kExecutableSha256);
  Require(binding.enabled && binding.metadata_provider_slot == reinterpret_cast<const void *>(base + 0x5D1F7B0) &&
              binding.sentinel_metadata == reinterpret_cast<const void *>(base + 0x5451F40),
          "Diac literal exact-build provider/sentinel bindings differ");
  Require(!xar::ck3_12003::BindDiacLiteralNumericInputs12003(base, "wrong-build").enabled,
          "Diac literal factory accepted wrong exact-build pin");
}
void Run(const std::filesystem::path &directory) {
  ExactBindings();
  {
    Fixture f;
    const auto snapshot = f.Observe(1);
    Require(snapshot.ready && snapshot.declarations.size() == 1,
            "Diac literal quantized/BA row not independently complete");
    const auto &row = snapshot.declarations.at(0);
    Require(row.ready && row.scale_gate_280_raw == 0U && row.metadata_provider_loaded == true,
            "Diac literal row must keep actual unit-scale gate and loaded provider");
    RawPC(row, {5, 6}, {150000, -150000});
    Metadata(row, 0, 5, "provider_50_c8", std::uint8_t{0}, std::uint8_t{0});
    Metadata(row, 1, 6, "provider_50_c8", std::uint8_t{1}, std::nullopt);
    Save(directory, "quantized-and-ba-preserved", snapshot);
  }
  {
    Fixture f;
    f.Property(f.declaration, {7, 8}, {-150000, -150000});
    const auto snapshot = f.Observe(1);
    Require(snapshot.ready && snapshot.declarations.at(0).ready,
            "Diac literal B8 flags row unavailable");
    const auto &row = snapshot.declarations.at(0);
    RawPC(row, {7, 8}, {-150000, -150000});
    Metadata(row, 0, 7, "provider_50_c8", std::uint8_t{0}, std::uint8_t{3});
    Metadata(row, 1, 8, "provider_50_c8", std::uint8_t{0}, std::uint8_t{2});
    Save(directory, "b8-bit0-preserved", snapshot);
  }
  {
    Fixture f;
    f.Property(f.declaration, {std::uint16_t{0xFFFFU}}, {150000});
    f.memory.Deny(f.provider, 0x50, 8);
    const auto snapshot = f.Observe(1);
    Require(snapshot.ready && snapshot.declarations.at(0).metadata_provider_loaded == true,
            "Diac FFFF static metadata still requires actual loaded provider getter");
    const auto &row = snapshot.declarations.at(0);
    RawPC(row, {std::uint16_t{0xFFFFU}}, {150000});
    Metadata(row, 0, std::uint16_t{0xFFFFU}, "static_5451f40", std::uint8_t{0}, std::uint8_t{0});
    Save(directory, "sentinel-static", snapshot);
  }
  {
    Fixture f;
    f.memory.Put(f.definition_block, 0xC, std::int32_t{2});
    f.memory.Put(f.declaration_pointers, 8, f.declaration);
    f.Property(f.declaration, {5, 5, 6}, {150000, 250000, -150000});
    const auto snapshot = f.Observe(2);
    Require(snapshot.ready && snapshot.declarations.size() == 2 &&
                snapshot.declarations.at(0).declaration_identity ==
                    snapshot.declarations.at(1).declaration_identity,
            "Diac physical duplicate declaration pointers lost occurrence or identity");
    for (std::size_t i = 0; i < 2; ++i) {
      const auto &row = snapshot.declarations.at(i);
      Require(row.ready && row.native_index == static_cast<std::int32_t>(i),
              "Diac duplicate declaration ordinal differs");
      RawPC(row, {5, 5, 6}, {150000, 250000, -150000});
      Metadata(row, 0, 5, "provider_50_c8", std::uint8_t{0}, std::uint8_t{0});
      Metadata(row, 1, 5, "provider_50_c8", std::uint8_t{0}, std::uint8_t{0});
      Metadata(row, 2, 6, "provider_50_c8", std::uint8_t{1}, std::nullopt);
      Require(row.metadata_rows.at(0).metadata_identity == row.metadata_rows.at(1).metadata_identity,
              "Diac duplicate key metadata identity lost");
    }
    Save(directory, "duplicate-declarations-and-keys", snapshot);
  }
  {
    Fixture f;
    f.memory.Put(f.definition_block, 0xC, std::int32_t{2});
    f.memory.Put(f.declaration, 0x280, std::uint32_t{7});
    f.Property(f.second_declaration, {5, 6}, {150000, -150000});
    f.memory.Deny(f.declaration, 0, 8);
    f.memory.Deny(f.declaration, 0xC, 4);
    f.memory.Deny(f.declaration, 0x68, 8);
    f.memory.Deny(f.declaration, 0x74, 4);
    const auto snapshot = f.Observe(1);
    Require(!snapshot.ready && snapshot.declarations.size() == 2,
            "Diac dynamic source must preserve later independent literal row");
    const auto &dynamic = snapshot.declarations.at(0);
    const auto &literal = snapshot.declarations.at(1);
    Require(!dynamic.ready && dynamic.scale_gate_280_raw == 7U &&
                dynamic.reason == "dynamic_scale_9d7060" && !dynamic.properties &&
                !dynamic.metadata_provider_loaded && dynamic.metadata_rows.empty() &&
                literal.ready && literal.native_index == 1,
            "Diac dynamic scale must not fabricate PC/provider/metadata inputs");
    RawPC(literal, {5, 6}, {150000, -150000});
    Metadata(literal, 0, 5, "provider_50_c8", std::uint8_t{0}, std::uint8_t{0});
    Metadata(literal, 1, 6, "provider_50_c8", std::uint8_t{1}, std::nullopt);
    Save(directory, "dynamic-then-literal", snapshot);
  }
  {
    Fixture f;
    f.Property(f.declaration, {}, {});
    f.memory.Deny(f.declaration, 0, 8);
    f.memory.Deny(f.declaration, 0x68, 8);
    f.memory.Deny(f.provider, 0x50, 8);
    const auto snapshot = f.Observe(1);
    Require(snapshot.ready && snapshot.declarations.at(0).ready &&
                snapshot.declarations.at(0).metadata_provider_loaded == true &&
                snapshot.declarations.at(0).metadata_rows.empty(),
            "Diac actual empty PC still calls loaded-provider getter before count");
    RawPC(snapshot.declarations.at(0), {}, {});
    Save(directory, "empty-literal-loaded-provider", snapshot);
  }
  {
    Fixture f;
    f.memory.Put(f.provider_slot, 0, static_cast<void *>(nullptr));
    f.memory.Deny(f.provider, 0x50, 8);
    f.memory.Deny(f.metadata_table, 0, 9 * 0xC8);
    const auto snapshot = f.Observe(1);
    Require(!snapshot.ready && snapshot.declarations.size() == 1,
            "Diac actual cold provider must retain a specific missing metadata producer");
    const auto &row = snapshot.declarations.at(0);
    Require(!row.ready && row.metadata_provider_loaded == false && row.metadata_rows.empty() &&
                row.reason == "metadata_provider_c85860_unavailable",
            "Diac unloaded provider must not call diagnostic/reload or manufacture flags");
    RawPC(row, {5, 6}, {150000, -150000});
    Save(directory, "missing-mapper-with-raw-pc", snapshot);
  }
  {
    Fixture f;
    f.Property(f.declaration, {5, 6, 7, 8},
               {std::numeric_limits<std::int64_t>::max(), std::numeric_limits<std::int64_t>::min(),
                std::numeric_limits<std::int64_t>::max(), std::int64_t{-150000}});
    f.Flags(8, std::uint8_t{255}, std::uint8_t{0});
    f.memory.Deny(f.metadata_table, 8 * 0xC8 + 0xB8, 1);
    const auto snapshot = f.Observe(1);
    Require(snapshot.ready && snapshot.declarations.at(0).ready,
            "Diac literal signed extreme operands/flags unavailable");
    const auto &row = snapshot.declarations.at(0);
    RawPC(row, {5, 6, 7, 8},
          {std::numeric_limits<std::int64_t>::max(), std::numeric_limits<std::int64_t>::min(),
           std::numeric_limits<std::int64_t>::max(), std::int64_t{-150000}});
    Metadata(row, 0, 5, "provider_50_c8", std::uint8_t{0}, std::uint8_t{0});
    Metadata(row, 1, 6, "provider_50_c8", std::uint8_t{1}, std::nullopt);
    Metadata(row, 2, 7, "provider_50_c8", std::uint8_t{0}, std::uint8_t{3});
    Metadata(row, 3, 8, "provider_50_c8", std::uint8_t{255}, std::nullopt);
    Save(directory, "int64-extremes", snapshot);
  }
}
} // namespace

int main(int argc, char **argv) {
  try {
    Require(argc <= 2, "usage: person_diac_literal_numeric_12003_test [wire_directory]");
    const auto directory = argc > 1 ? std::filesystem::path(argv[1]) : std::filesystem::path{};
    if (!directory.empty()) std::filesystem::create_directories(directory);
    Run(directory);
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
