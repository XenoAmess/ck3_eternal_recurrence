#include "xar_bridge/ck3_12003_context_sources.hpp"
#include "xar_bridge/battle_context_source_inputs_v1_serializer.hpp"

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <limits>
#include <memory>
#include <string_view>
#include <utility>
#include <vector>

namespace {
struct Memory {
  struct Region {
    std::unique_ptr<std::byte[]> data;
    std::size_t size;
  };
  struct Denied {
    std::uintptr_t begin;
    std::size_t size;
    std::size_t attempted = 0;
  };
  std::vector<Region> regions;
  std::vector<Denied> denied;
  std::size_t reads = 0;
  std::size_t failed_reads = 0;

  void *Allocate(std::size_t size) {
    auto data = std::make_unique<std::byte[]>(size);
    void *pointer = data.get();
    regions.push_back({std::move(data), size});
    return pointer;
  }
  template <typename T> void Put(void *pointer, std::size_t offset, T value) {
    std::memcpy(static_cast<std::byte *>(pointer) + offset, &value, sizeof(value));
  }
  void Deny(const void *pointer, std::size_t offset, std::size_t size) {
    denied.push_back({reinterpret_cast<std::uintptr_t>(pointer) + offset, size, 0});
  }
  static bool Read(void *context, const void *address, void *output,
                   std::size_t bytes) noexcept {
    auto &memory = *static_cast<Memory *>(context);
    ++memory.reads;
    const auto begin = reinterpret_cast<std::uintptr_t>(address);
    for (auto &range : memory.denied) {
      if (begin < range.begin + range.size && range.begin < begin + bytes) {
        ++range.attempted;
        ++memory.failed_reads;
        return false;
      }
    }
    for (const auto &region : memory.regions) {
      const auto base = reinterpret_cast<std::uintptr_t>(region.data.get());
      if (begin >= base && begin - base <= region.size &&
          bytes <= region.size - static_cast<std::size_t>(begin - base)) {
        std::memcpy(output, address, bytes);
        return true;
      }
    }
    ++memory.failed_reads;
    return false;
  }
};

void Header(Memory &memory, void *object, std::size_t offset, const void *data,
            std::int32_t count) {
  memory.Put(object, offset, data);
  memory.Put(object, offset + 0xC, count);
}

void *Definition(Memory &memory, std::vector<std::uint16_t> keys,
                 std::vector<std::int64_t> values) {
  void *definition = memory.Allocate(0xC0);
  void *key_data = memory.Allocate(keys.size() * sizeof(std::uint16_t) + 1);
  void *value_data = memory.Allocate(values.size() * sizeof(std::int64_t) + 1);
  for (std::size_t i = 0; i < keys.size(); ++i)
    memory.Put(key_data, i * sizeof(std::uint16_t), keys[i]);
  for (std::size_t i = 0; i < values.size(); ++i)
    memory.Put(value_data, i * sizeof(std::int64_t), values[i]);
  Header(memory, definition, 0x40, key_data, static_cast<std::int32_t>(keys.size()));
  Header(memory, definition, 0xA8, value_data, static_cast<std::int32_t>(values.size()));
  return definition;
}

void WeightedSpan(Memory &memory, void *object, std::size_t offset,
                  const std::vector<std::pair<void *, std::int64_t>> &rows) {
  void *data = memory.Allocate(rows.size() * 0x48 + 1);
  for (std::size_t i = 0; i < rows.size(); ++i) {
    memory.Put(data, i * 0x48, rows[i].first);
    memory.Put(data, i * 0x48 + 0x30, rows[i].second);
  }
  Header(memory, object, offset, data, static_cast<std::int32_t>(rows.size()));
}

void Storage(Memory &memory, void *slot, std::uint32_t index, void *object) {
  void *store = memory.Allocate(0x30);
  void *table = memory.Allocate(8 * 16);
  memory.Put(slot, 0, store);
  memory.Put(store, 0x20, table);
  memory.Put(store, 0x2C, std::uint32_t{8});
  memory.Put(table, static_cast<std::size_t>(index) * 16 + 8, object);
}

struct LookupProbe {
  void *map_header = nullptr;
  void *found_record = nullptr;
  void *miss_record = nullptr;
  void *character = nullptr;
  void *government = nullptr;
  std::size_t lookup_calls = 0;
  std::size_t government_calls = 0;
  bool abi_ok = true;
};
LookupProbe probe;
xar::ck3_12002::ContextSourceTokenCursorV1 *ExistingToken(
    void *map_header, xar::ck3_12002::ContextSourceTokenCursorV1 *output,
    const xar::ck3_12002::ContextSourceTokenSliceV1 *slice) {
  ++probe.lookup_calls;
  probe.abi_ok = probe.abi_ok && map_header == probe.map_header &&
      slice != nullptr && slice->flag == 0 && slice->length >= 0;
  const auto text = std::string_view(slice->data, static_cast<std::size_t>(slice->length));
  probe.abi_ok = probe.abi_ok &&
      ((text == "known" && slice->length == 5) || (text == "missing" && slice->length == 7));
  output->node = text == "known" ? probe.found_record : probe.miss_record;
  return output;
}
void *Government(void *character) {
  ++probe.government_calls;
  probe.abi_ok = probe.abi_ok && character == probe.character;
  return probe.government;
}
void InlineCondition(Memory &memory, void *object, std::size_t offset,
                     std::string_view text) {
  for (std::size_t i = 0; i < text.size(); ++i)
    memory.Put(object, offset + i, static_cast<std::uint8_t>(text[i]));
  memory.Put(object, offset + 0x10, static_cast<std::int32_t>(text.size()));
  memory.Put(object, offset + 0x18, std::uint64_t{15});
}
void Property(Memory &memory, void *object, std::size_t offset,
              std::uint16_t key, std::int64_t value) {
  void *keys = memory.Allocate(2);
  void *values = memory.Allocate(8);
  memory.Put(keys, 0, key);
  memory.Put(values, 0, value);
  Header(memory, object, offset, keys, 1);
  Header(memory, object, offset + 0x68, values, 1);
}
} // namespace

int main() {
  Memory memory;
  void *character = memory.Allocate(0x400);
  void *carrier = memory.Allocate(0x700);
  void *stale_first = memory.Allocate(0x30);
  void *fallback_first = memory.Allocate(0x240);
  void *second = memory.Allocate(0x180);
  void *first_storage_slot = memory.Allocate(8);
  void *first_fallback_slot = memory.Allocate(8);
  void *second_storage_slot = memory.Allocate(8);
  void *second_fallback_slot = memory.Allocate(8);
  void *unused_lifestyle_fallback = memory.Allocate(0x10);
  void *unused_extra_fallback = memory.Allocate(0x10);

  constexpr std::uint32_t first_id = 0x01000003U;
  constexpr std::uint32_t fallback_id = 0x03000004U;
  constexpr std::uint32_t second_id = 0x02000002U;
  memory.Put(character, 0x1B0, carrier);
  memory.Put(character, 0x158, first_id);
  memory.Put(stale_first, 0x10, std::uint32_t{0x02000003U});
  memory.Put(fallback_first, 0x10, fallback_id);
  memory.Put(fallback_first, 0x2C, second_id);
  memory.Put(fallback_first, 0x218, std::uint8_t{1});
  memory.Put(second, 0x10, second_id);
  memory.Put(first_fallback_slot, 0, fallback_first);
  Storage(memory, first_storage_slot, first_id & 0xFFFFFFU, stale_first);
  Storage(memory, second_storage_slot, second_id & 0xFFFFFFU, second);

  void *definition_a = Definition(memory, {44, 3}, {-10, std::numeric_limits<std::int64_t>::min() + 8});
  void *definition_empty = Definition(memory, {}, {});
  void *definition_c = Definition(memory, {7}, {0});
  memory.Deny(definition_empty, 0x40, 8);
  memory.Deny(definition_empty, 0xA8, 8);
  memory.Deny(definition_empty, 0xB4, 4);
  memory.Deny(unused_lifestyle_fallback, 0, 0x10);
  memory.Deny(unused_extra_fallback, 0, 0x10);
  WeightedSpan(memory, carrier, 0x188,
      {{definition_a, std::numeric_limits<std::int64_t>::max()}, {definition_a, 1},
       {definition_empty, 0}, {definition_a, -3}});
  WeightedSpan(memory, second, 0x140, {{definition_a, 5}});
  WeightedSpan(memory, fallback_first, 0x168,
      {{definition_c, -2}, {definition_c, 2}, {definition_a, -1}});
  WeightedSpan(memory, fallback_first, 0x200,
      {{definition_a, 17}, {definition_empty, -4}});

  xar::ck3_12002::ContextSourceBindingsV1 bindings;
  bindings.enabled = true;
  bindings.lifestyle_fallback_header = unused_lifestyle_fallback;
  bindings.house_extra_fallback_header = unused_extra_fallback;
  bindings.first_storage_slot = first_storage_slot;
  bindings.first_fallback_slot = first_fallback_slot;
  bindings.second_storage_slot = second_storage_slot;
  bindings.second_fallback_slot = second_fallback_slot;
  bindings.read_memory = &Memory::Read;
  bindings.read_context = &memory;

  void *source = memory.Allocate(0x600);
  void *source_vector = memory.Allocate(8);
  void *base_values = memory.Allocate(8);
  memory.Put(source_vector, 0, source);
  Header(memory, carrier, 0x220, source_vector, 1);
  memory.Put(source, 0x28C, std::int32_t{0});
  memory.Put(base_values, 0, std::int64_t{-37});
  Header(memory, source, 0x2E8, base_values, 1);
  memory.Put(source, 0x438, std::uint32_t{55});
  void *a_rows = memory.Allocate(0x30);
  void *a_key = memory.Allocate(0x40);
  memory.Put(a_key, 0x10, std::uint32_t{0x01000011U});
  memory.Put(a_key, 0x38, std::uint32_t{0});
  memory.Put(a_rows, 0x20, a_key);
  Header(memory, source, 0x550, a_rows, 1);
  memory.Put(source, 0x574, std::int32_t{0});
  void *fallback_properties = memory.Allocate(0x80);
  Property(memory, fallback_properties, 0, 8, -70);
  bindings.conditional_a_fallback_properties = fallback_properties;

  void *c_rows = memory.Allocate(4 * 0x1D0);
  constexpr std::uint32_t source_keys[] = {0xAA000000U, 0xBB000001U, 0xCC000002U, 0xDD000008U};
  for (std::size_t i = 0; i < 4; ++i) {
    memory.Put(c_rows, i * 0x1D0, source_keys[i]);
    memory.Put(c_rows, i * 0x1D0 + 0x1C8, static_cast<std::uint8_t>(i == 3));
    Property(memory, c_rows, i * 0x1D0 + 8, 9, 42);
  }
  Header(memory, source, 0x580, c_rows, 4);
  void *condition_registry = memory.Allocate(0x40);
  void *conditions = memory.Allocate(3 * 0x20);
  InlineCondition(memory, conditions, 0, "-");
  InlineCondition(memory, conditions, 0x20, "known");
  InlineCondition(memory, conditions, 0x40, "missing");
  memory.Put(condition_registry, 0x30, conditions);
  memory.Put(condition_registry, 0x3C, std::int32_t{3});
  void *condition_fallback = memory.Allocate(0x20);
  InlineCondition(memory, condition_fallback, 0, "-fallback");
  void *registry_guard = memory.Allocate(4);
  void *fallback_guard = memory.Allocate(4);
  memory.Put(registry_guard, 0, std::int32_t{-2});
  memory.Put(fallback_guard, 0, std::int32_t{-2});
  bindings.condition_registry = condition_registry;
  bindings.condition_fallback_object = condition_fallback;
  bindings.condition_registry_guard = registry_guard;
  bindings.condition_fallback_guard = fallback_guard;

  void *token_manager = memory.Allocate(0x10);
  void *token_manager_slot = memory.Allocate(8);
  memory.Put(token_manager_slot, 0, token_manager);
  void *found_record = memory.Allocate(0x30);
  void *miss_record = memory.Allocate(0x30);
  memory.Put(found_record, 4, std::uint8_t{0});
  memory.Put(found_record, 0x28, std::int32_t{-9});
  memory.Put(miss_record, 4, std::uint8_t{0xFF});
  void *classifier_flag = memory.Allocate(4);
  void *classifier_table = memory.Allocate(512);
  void *classifier_table_slot = memory.Allocate(8);
  memory.Put(classifier_table_slot, 0, classifier_table);
  bindings.token_manager_slot = token_manager_slot;
  bindings.prefix_classifier_locale_flag = classifier_flag;
  bindings.prefix_classifier_table_slot = classifier_table_slot;
  bindings.existing_token_lookup = &ExistingToken;

  void *government = memory.Allocate(0x60);
  void *government_tokens = memory.Allocate(8);
  memory.Put(government_tokens, 0, std::int32_t{-9});
  memory.Put(government_tokens, 4, std::int32_t{0});
  Header(memory, government, 0x50, government_tokens, 2);
  bindings.government = &Government;
  probe.map_header = static_cast<std::byte *>(token_manager) + 8;
  probe.found_record = found_record;
  probe.miss_record = miss_record;
  probe.character = character;
  probe.government = government;

  const auto observed = xar::ck3_12002::ReadCurrentContextSourceInputs12003(
      bindings, character, 29829);
  const auto wire = xar::bridge::SerializeBattleCurrentPersonContextSourceInputsV1(observed);
  std::cout << "{\"current_context_source_inputs\":" << wire
            << ",\"fixture_memory_reads\":" << memory.reads
            << ",\"fixture_failed_reads\":" << memory.failed_reads
            << ",\"poison_read_attempts\":[";
  for (std::size_t i = 0; i < memory.denied.size(); ++i) {
    if (i) std::cout << ',';
    std::cout << memory.denied[i].attempted;
  }
  std::cout << "],\"lookup_abi_ok\":" << (probe.abi_ok ? "true" : "false")
            << ",\"lookup_calls\":" << probe.lookup_calls
            << ",\"government_calls\":" << probe.government_calls << "}\n";
  return 0;
}
