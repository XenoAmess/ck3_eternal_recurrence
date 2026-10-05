#include "xar_bridge/ck3_12003_context_sources.hpp"
#include "xar_bridge/ck3_12003_context_locale.hpp"
#include "xar_bridge/battle_context_source_inputs_v1_serializer.hpp"

#include <cstddef>
#include <bit>
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
  void *crt_state = nullptr;
  std::uint32_t last_error = 77;
  std::size_t value_getter_calls = 0;
  std::size_t get_error_calls = 0;
  std::size_t set_error_calls = 0;
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
void *FakeValueGetter(std::uint32_t index) {
  ++probe.value_getter_calls;
  probe.abi_ok = probe.abi_ok && index == 23;
  probe.last_error = 99;
  return probe.crt_state;
}
std::uint32_t FakeGetLastError() {
  ++probe.get_error_calls;
  return probe.last_error;
}
void FakeSetLastError(std::uint32_t error) {
  ++probe.set_error_calls;
  probe.abi_ok = probe.abi_ok && error == 77;
  probe.last_error = error;
}
void InlineCondition(Memory &memory, void *object, std::size_t offset,
                     std::string_view text) {
  for (std::size_t i = 0; i < text.size(); ++i)
    memory.Put(object, offset + i, static_cast<std::uint8_t>(text[i]));
  memory.Put(object, offset + 0x10, static_cast<std::int32_t>(text.size()));
  memory.Put(object, offset + 0x18, std::uint64_t{15});
}
} // namespace

namespace {
void Properties(Memory &, void *, std::size_t, const std::vector<std::uint16_t> &,
                const std::vector<std::int64_t> &);
void SourceBase(Memory &, void *, const std::vector<std::uint16_t> &,
                const std::vector<std::int64_t> &);
}

int main() {
  Memory memory;
  xar::ck3_12002::ContextSourceBindingsV1 bindings;
  bindings.enabled = true;
  bindings.read_memory = &Memory::Read;
  bindings.read_context = &memory;
  void *character = memory.Allocate(0x400);
  void *carrier = memory.Allocate(0x300);
  memory.Put(character, 0x1B0, carrier);

  // Empty A census establishes its independent readiness without invoking A's emitter.
  void *first_relation = memory.Allocate(0x240);
  void *second_relation = memory.Allocate(0x180);
  memory.Put(character, 0x158, std::uint32_t{0x01000003U});
  memory.Put(first_relation, 0x10, std::uint32_t{0x01000003U});
  memory.Put(first_relation, 0x2C, std::uint32_t{0x02000002U});
  memory.Put(second_relation, 0x10, std::uint32_t{0x02000002U});
  void *first_relation_slot = memory.Allocate(8);
  void *second_relation_slot = memory.Allocate(8);
  Storage(memory, first_relation_slot, 3, first_relation);
  Storage(memory, second_relation_slot, 2, second_relation);
  bindings.first_storage_slot = first_relation_slot;
  bindings.first_fallback_slot = memory.Allocate(8);
  bindings.second_storage_slot = second_relation_slot;
  bindings.second_fallback_slot = memory.Allocate(8);
  bindings.lifestyle_fallback_header = memory.Allocate(0x10);
  bindings.house_extra_fallback_header = memory.Allocate(0x10);

  void *sources[4]{};
  void *source_vector = memory.Allocate(4 * 8);
  for (std::size_t i = 0; i < 4; ++i) {
    sources[i] = memory.Allocate(0x600);
    memory.Put(source_vector, i * 8, sources[i]);
  }
  Header(memory, carrier, 0x220, source_vector, 4);
  SourceBase(memory, sources[0], {3, 9, 65535}, {std::numeric_limits<std::int64_t>::max(), 20, 99});
  SourceBase(memory, sources[1], {}, {-37});
  SourceBase(memory, sources[2], {11}, {2});
  SourceBase(memory, sources[3], {5}, {-2});

  void *a_rows = memory.Allocate(4 * 0x30);
  void *a_keys[4]{};
  for (auto &key : a_keys) key = memory.Allocate(0x40);
  constexpr std::uint32_t a_ids[] = {0x11223344U, 0x11223344U, 0x00556677U, 0xABCDEF01U};
  for (std::size_t i = 0; i < 4; ++i) {
    memory.Put(a_rows, i * 0x30 + 0x20, a_keys[i]);
    memory.Put(a_keys[i], 0x10, a_ids[i]);
    memory.Put(a_keys[i], 0x38, std::uint32_t{i == 2 ? 0U : 0x4744624FU});
  }
  void *first_id_properties = memory.Allocate(0x80);
  Properties(memory, first_id_properties, 0, {3, 7, 65535}, {1, 0, 500});
  void *later_same_id_properties = memory.Allocate(0x80);
  Properties(memory, later_same_id_properties, 0, {600}, {999});
  memory.Put(a_rows, 0x28, first_id_properties);
  memory.Put(a_rows, 0x30 + 0x28, later_same_id_properties);
  Header(memory, sources[0], 0x550, a_rows, 4);
  void *a_fallback_properties = memory.Allocate(0x80);
  Properties(memory, a_fallback_properties, 0, {2}, {-5});
  bindings.conditional_a_fallback_properties = a_fallback_properties;

  constexpr std::uint32_t a_stage1_id = 0x04000003U;
  constexpr std::uint32_t a_stage2_id = 0x05000002U;
  constexpr std::uint32_t a_stage3_id = 0x06000004U;
  void *a_stage1 = memory.Allocate(0x7B0);
  void *a_stage2 = memory.Allocate(0xA0);
  void *a_stale_stage3 = memory.Allocate(0x10);
  void *a_initial_fallback = memory.Allocate(0x7B0);
  memory.Put(character, 0xB4, a_stage1_id);
  memory.Put(a_stage1, 8, a_stage1_id);
  memory.Put(a_stage1, 0x4B8, a_stage2_id);
  memory.Put(a_stage2, 8, a_stage2_id);
  memory.Put(a_stage2, 0x98, a_stage3_id);
  memory.Put(a_stale_stage3, 8, std::uint32_t{0x07000004U});
  memory.Put(a_initial_fallback, 8, std::uint32_t{0x08000005U});
  void *a_membership = memory.Allocate(2 * 8);
  memory.Put(a_membership, 0, a_keys[2]);
  memory.Put(a_membership, 8, a_keys[1]);
  Header(memory, a_initial_fallback, 0x7A0, a_membership, 2);
  void *a_store = memory.Allocate(0x30);
  void *a_table = memory.Allocate(8 * 16);
  void *a_store_slot = memory.Allocate(8);
  memory.Put(a_store_slot, 0, a_store);
  memory.Put(a_store, 0x20, a_table);
  memory.Put(a_store, 0x2C, std::uint32_t{8});
  memory.Put(a_table, 3 * 16 + 8, a_stage1);
  memory.Put(a_table, 4 * 16 + 8, a_stale_stage3);
  void *a_fallback_slot = memory.Allocate(8);
  memory.Put(a_fallback_slot, 0, a_initial_fallback);
  void *a_second_store_slot = memory.Allocate(8);
  Storage(memory, a_second_store_slot, 2, a_stage2);
  bindings.selector_a_storage_slot = a_store_slot;
  bindings.selector_a_initial_fallback_slot = a_fallback_slot;
  bindings.selector_a_second_storage_slot = a_second_store_slot;
  bindings.selector_a_second_fallback_slot = memory.Allocate(8);

  void *b_rows = memory.Allocate(3 * 0x1C8);
  memory.Put(b_rows, 0, std::int32_t{-10});
  Properties(memory, b_rows, 8, {3, 4}, {-1, 0});
  memory.Put(b_rows, 0x1C8, std::int32_t{7});
  Properties(memory, b_rows, 0x1C8 + 8, {9}, {-30});
  memory.Put(b_rows, 2 * 0x1C8, std::int32_t{5});
  // The observer records this inline PC; admitted false excludes it from the composite.
  Properties(memory, b_rows, 2 * 0x1C8 + 8, {401}, {2000});
  Header(memory, sources[0], 0x568, b_rows, 3);
  void *b_selector = memory.Allocate(0x530);
  constexpr std::uint32_t b_id = 0x09000003U;
  memory.Put(character, 0xB0, b_id);
  memory.Put(b_selector, 0x10, b_id);
  void *b_store_slot = memory.Allocate(8);
  Storage(memory, b_store_slot, 3, b_selector);
  bindings.selector_b_storage_slot = b_store_slot;
  bindings.selector_b_fallback_slot = memory.Allocate(8);
  void *b_primary_owner = memory.Allocate(0x130);
  void *b_primary_header = memory.Allocate(0x18);
  void *b_primary_keys = memory.Allocate(3 * 4);
  memory.Put(b_primary_keys, 0, std::int32_t{-10});
  memory.Put(b_primary_keys, 4, std::int32_t{4});
  memory.Put(b_primary_keys, 8, std::int32_t{8});
  Header(memory, b_primary_header, 8, b_primary_keys, 3);
  memory.Put(b_primary_owner, 0x128, b_primary_header);
  memory.Put(b_selector, 0x20, b_primary_owner);
  void *b_nested_object = memory.Allocate(0x1020);
  void *b_nested_keys = memory.Allocate(4);
  memory.Put(b_nested_keys, 0, std::int32_t{7});
  Header(memory, b_nested_object, 0x1010, b_nested_keys, 1);
  void *b_nested_vector = memory.Allocate(8);
  memory.Put(b_nested_vector, 0, b_nested_object);
  Header(memory, b_selector, 0x518, b_nested_vector, 1);

  void *conditions = memory.Allocate(4 * 0x20);
  InlineCondition(memory, conditions, 0, "known");
  InlineCondition(memory, conditions, 0x20, "digit");
  InlineCondition(memory, conditions, 0x40, "-");
  InlineCondition(memory, conditions, 0x60, std::string_view("\xE4\xB8\xAD", 3));
  void *condition_registry = memory.Allocate(0x40);
  memory.Put(condition_registry, 0x30, conditions);
  memory.Put(condition_registry, 0x3C, std::int32_t{4});
  void *condition_guard = memory.Allocate(4);
  memory.Put(condition_guard, 0, std::int32_t{-2});
  bindings.condition_registry = condition_registry;
  bindings.condition_registry_guard = condition_guard;
  void *c_rows = memory.Allocate(3 * 0x1D0);
  for (std::size_t i = 0; i < 3; ++i) {
    memory.Put(c_rows, i * 0x1D0, static_cast<std::uint32_t>(0xAA000000U + i));
    memory.Put(c_rows, i * 0x1D0 + 0x1C8, static_cast<std::uint8_t>(i == 1));
  }
  Properties(memory, c_rows, 8, {6}, {7});
  // Its actual nonempty PC is observed but must never enter the false row's merge.
  Properties(memory, c_rows, 0x1D0 + 8, {400}, {1000});
  // Admitted row2 has a genuine empty PC.
  Header(memory, sources[0], 0x580, c_rows, 3);
  void *unknown_c_row = memory.Allocate(0x1D0);
  memory.Put(unknown_c_row, 0, std::uint32_t{0xBB000003U});
  Properties(memory, unknown_c_row, 8, {12}, {3});
  Header(memory, sources[2], 0x580, unknown_c_row, 1);

  void *token_manager = memory.Allocate(0x10);
  void *token_manager_slot = memory.Allocate(8);
  memory.Put(token_manager_slot, 0, token_manager);
  bindings.token_manager_slot = token_manager_slot;
  bindings.existing_token_lookup = &ExistingToken;
  void *found_record = memory.Allocate(0x30);
  memory.Put(found_record, 4, std::uint8_t{0});
  memory.Put(found_record, 0x28, std::int32_t{-9});
  probe.map_header = static_cast<std::byte *>(token_manager) + 8;
  probe.found_record = found_record;
  probe.miss_record = memory.Allocate(0x30);
  void *government = memory.Allocate(0x60);
  void *government_tokens = memory.Allocate(8);
  memory.Put(government_tokens, 0, std::int32_t{-9});
  memory.Put(government_tokens, 4, std::int32_t{0});
  Header(memory, government, 0x50, government_tokens, 2);
  bindings.government = &Government;
  probe.character = character;
  probe.government = government;

  void *classifier_mode = memory.Allocate(4);
  memory.Put(classifier_mode, 0, std::int32_t{1});
  bindings.prefix_classifier_locale_flag = classifier_mode;
  void *unused_default_table_slot = memory.Allocate(8);
  bindings.prefix_classifier_table_slot = unused_default_table_slot;
  memory.Deny(unused_default_table_slot, 0, 8);
  auto &locale = bindings.current_locale;
  locale.enabled = true;
  void *index_slot = memory.Allocate(4);
  memory.Put(index_slot, 0, std::uint32_t{23});
  locale.crt_index_slot = index_slot;
  constexpr std::uint64_t cookie = 0x1234U;
  void *cookie_slot = memory.Allocate(8);
  memory.Put(cookie_slot, 0, cookie);
  locale.decode_cookie_slot = cookie_slot;
  void *cache_slot = memory.Allocate(8);
  const auto getter_word = static_cast<std::uint64_t>(reinterpret_cast<std::uintptr_t>(&FakeValueGetter));
  memory.Put(cache_slot, 0, std::rotl(getter_word, static_cast<int>(cookie & 63U)) ^ cookie);
  locale.value_api_cache_slot = cache_slot;
  void *get_error_slot = memory.Allocate(8);
  void *set_error_slot = memory.Allocate(8);
  memory.Put(get_error_slot, 0, &FakeGetLastError);
  memory.Put(set_error_slot, 0, &FakeSetLastError);
  locale.get_last_error_iat = get_error_slot;
  locale.set_last_error_iat = set_error_slot;
  void *selected_locale = memory.Allocate(0x10);
  void *alternate_table = memory.Allocate(512);
  memory.Put(alternate_table, static_cast<std::size_t>('d') * 2, std::uint16_t{4});
  memory.Put(selected_locale, 0, alternate_table);
  memory.Put(selected_locale, 8, std::int32_t{2});
  void *global_locale_slot = memory.Allocate(8);
  memory.Put(global_locale_slot, 0, selected_locale);
  locale.global_locale_slot = global_locale_slot;
  void *flags_mask_slot = memory.Allocate(4);
  memory.Put(flags_mask_slot, 0, std::uint32_t{1});
  locale.locale_flags_mask_slot = flags_mask_slot;
  void *crt_state = memory.Allocate(0x3B0);
  memory.Put(crt_state, 0x90, memory.Allocate(0x10));
  // Current locale differs, flags0 chooses exact global locale without native synchronization.
  probe.crt_state = crt_state;

  const auto observed = xar::ck3_12002::ReadCurrentContextSourceInputs12003(bindings, character, 29829);
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
            << ",\"government_calls\":" << probe.government_calls
            << ",\"locale_value_getter_calls\":" << probe.value_getter_calls
            << ",\"locale_get_error_calls\":" << probe.get_error_calls
            << ",\"locale_set_error_calls\":" << probe.set_error_calls
            << ",\"locale_last_error\":" << probe.last_error << "}\n";
  return 0;
}

// V86 native image is assembled only from source-closed inputs before the sole run.
// Admission/classifier-specific memory setup follows frozen DTO/bindings.

namespace {
void Properties(Memory &memory, void *object, std::size_t offset,
                const std::vector<std::uint16_t> &keys,
                const std::vector<std::int64_t> &values) {
  void *key_data = memory.Allocate(keys.size() * sizeof(std::uint16_t) + 1);
  void *value_data = memory.Allocate(values.size() * sizeof(std::int64_t) + 1);
  for (std::size_t i = 0; i < keys.size(); ++i)
    memory.Put(key_data, i * sizeof(std::uint16_t), keys[i]);
  for (std::size_t i = 0; i < values.size(); ++i)
    memory.Put(value_data, i * sizeof(std::int64_t), values[i]);
  Header(memory, object, offset, key_data, static_cast<std::int32_t>(keys.size()));
  Header(memory, object, offset + 0x68, value_data, static_cast<std::int32_t>(values.size()));
}
void SourceBase(Memory &memory, void *source,
                const std::vector<std::uint16_t> &keys,
                const std::vector<std::int64_t> &values) {
  void *key_data = memory.Allocate(keys.size() * sizeof(std::uint16_t) + 1);
  void *value_data = memory.Allocate(values.size() * sizeof(std::int64_t) + 1);
  for (std::size_t i = 0; i < keys.size(); ++i)
    memory.Put(key_data, i * sizeof(std::uint16_t), keys[i]);
  for (std::size_t i = 0; i < values.size(); ++i)
    memory.Put(value_data, i * sizeof(std::int64_t), values[i]);
  Header(memory, source, 0x280, key_data, static_cast<std::int32_t>(keys.size()));
  Header(memory, source, 0x2E8, value_data, static_cast<std::int32_t>(values.size()));
}
} // namespace
