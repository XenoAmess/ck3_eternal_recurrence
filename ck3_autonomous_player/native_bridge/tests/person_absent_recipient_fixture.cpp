#include "xar_bridge/ck3_12003_context_sources.hpp"
#include "xar_bridge/battle_context_source_inputs_v1_serializer.hpp"

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <limits>
#include <memory>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace {
void AbsentRequire(bool value, const char *label) {
  if (!value) throw std::runtime_error(label);
}
struct AbsentMemory {
  struct Region { std::unique_ptr<std::byte[]> data; std::size_t size; };
  struct Denied { std::uintptr_t begin; std::size_t size; std::size_t attempts = 0; };
  std::vector<Region> regions;
  std::vector<Denied> denied;
  void *Allocate(std::size_t size) {
    auto data = std::make_unique<std::byte[]>(size);
    auto *address = data.get();
    regions.push_back({std::move(data), size});
    return address;
  }
  template <typename T> void Put(void *address, std::size_t offset, T value) {
    std::memcpy(static_cast<std::byte *>(address) + offset, &value, sizeof(value));
  }
  void Deny(const void *address, std::size_t offset, std::size_t bytes) {
    denied.push_back({reinterpret_cast<std::uintptr_t>(address) + offset, bytes});
  }
  std::size_t Attempts() const {
    std::size_t result = 0;
    for (const auto &entry : denied) result += entry.attempts;
    return result;
  }
  static bool Read(void *context, const void *address, void *output,
                   std::size_t bytes) noexcept {
    auto &memory = *static_cast<AbsentMemory *>(context);
    const auto begin = reinterpret_cast<std::uintptr_t>(address);
    for (auto &entry : memory.denied) {
      if (begin < entry.begin + entry.size && entry.begin < begin + bytes) {
        ++entry.attempts;
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
    return false;
  }
};
void *AbsentAt(void *address, std::size_t offset) {
  return static_cast<std::byte *>(address) + offset;
}
std::uint64_t AbsentWord(const void *address) {
  return static_cast<std::uint64_t>(reinterpret_cast<std::uintptr_t>(address));
}
std::uint32_t AbsentHash(std::uint64_t key) {
  std::uint32_t hash = 0x811C9DC5U;
  for (unsigned shift = 0; shift < 64; shift += 8) {
    hash ^= static_cast<std::uint32_t>((key >> shift) & 0xFFU);
    hash *= 0x1000193U;
  }
  return hash;
}
struct AbsentFixture {
  static constexpr std::uint32_t associated_id = 0xAB000001U;
  static constexpr std::uint32_t trait_id = 0xCD000011U;
  AbsentMemory memory;
  xar::ck3_12002::ContextSourceBindingsV1 bindings{};
  void *character = memory.Allocate(0x1D0);
  void *associated = memory.Allocate(0x948);
  void *storage_slot = memory.Allocate(8);
  void *fallback_slot = memory.Allocate(8);
  void *map430 = memory.Allocate(9 * 24);
  void *map458 = memory.Allocate(5 * 24);
  void *key_a = memory.Allocate(0x18);
  void *key_b = memory.Allocate(0x18);
  void *key_c = memory.Allocate(0x18);
  void *member = memory.Allocate(0xA28);
  void *trait_values = memory.Allocate(4);
  void *membership_header = memory.Allocate(0x10);
  void *membership_guard = memory.Allocate(4);
  void *membership_values = memory.Allocate(8);
  void *inline_context = memory.Allocate(0xD8);
  void *aggregate_guard = memory.Allocate(4);
  void *aggregate_keys = memory.Allocate(3 * 2);
  void *aggregate_values = memory.Allocate(3 * 8);
  void *multiplier = memory.Allocate(8);
  void *lower = memory.Allocate(8);
  void *upper = memory.Allocate(8);

  void Bucket(void *buckets, std::size_t index, std::uint64_t key,
              std::uint64_t value, std::uint8_t probe = 1) {
    const auto offset = index * 24;
    memory.Put(buckets, offset, AbsentHash(key));
    memory.Put(buckets, offset + 4, probe);
    memory.Put(buckets, offset + 8, key);
    memory.Put(buckets, offset + 0x10, value);
  }
  void MapHeader(std::size_t offset, void *buckets, std::int32_t count,
                 std::int32_t mask) {
    memory.Put(associated, offset + 8, buckets);
    memory.Put(associated, offset + 0x10, count);
    memory.Put(associated, offset + 0x14, mask);
    memory.Put(associated, offset + 0x18, std::uint8_t{2});
  }
  AbsentFixture() {
    bindings.enabled = true;
    bindings.absent_recipient.enabled = true;
    auto &b = bindings.absent_recipient;
    b.associated_storage_slot = storage_slot;
    b.associated_fallback_slot = fallback_slot;
    b.membership_inline_header = membership_header;
    b.membership_guard_slot = membership_guard;
    b.aggregate_inline_context = inline_context;
    b.aggregate_guard_slot = aggregate_guard;
    b.member_multiplier_slot = multiplier;
    b.clamp_lower_slot = lower;
    b.clamp_upper_slot = upper;
    bindings.read_memory = &AbsentMemory::Read;
    bindings.read_context = &memory;
    memory.Put(character, 0x18, std::int32_t{29829});
    memory.Put(character, 0x1C, std::uint32_t{0x43686172});
    memory.Put(character, 0xB4, associated_id);
    memory.Put(character, 0x15C, std::int32_t{-1});
    memory.Put(associated, 8, associated_id);
    void *storage = memory.Allocate(0x30);
    void *table = memory.Allocate(2 * 16);
    memory.Put(storage_slot, 0, storage);
    memory.Put(fallback_slot, 0, associated);
    memory.Put(storage, 0x20, table);
    memory.Put(storage, 0x2C, std::uint32_t{2});
    memory.Put(table, 24, associated);
    memory.Put(key_a, 0x10, trait_id);
    memory.Put(key_b, 0x10, trait_id);
    memory.Put(key_c, 0x10, std::uint32_t{0xEF000022U});
    memory.Put(character, 0xF8, trait_values);
    memory.Put(character, 0x104, std::int32_t{1});
    memory.Put(trait_values, 0, trait_id);
    MapHeader(0x430, map430, 3, 7);
    Bucket(map430, 1, AbsentWord(key_a), 300000, 1);
    Bucket(map430, 3, AbsentWord(key_b), 700000, 2);
    Bucket(map430, 7, AbsentWord(key_c), 900000, 1);
    memory.Put(map430, 8 * 24 + 4, std::uint8_t{0xFF});
    MapHeader(0x458, map458, 2, 3);
    Bucket(map458, 0, AbsentWord(key_a), AbsentWord(member), 1);
    // Same low DWORD as the member is insufficient for QWORD membership.
    Bucket(map458, 2, AbsentWord(key_b), AbsentWord(member) ^ (1ULL << 32), 1);
    memory.Put(map458, 4 * 24 + 4, std::uint8_t{0xFF});
    memory.Put(membership_header, 0, membership_values);
    memory.Put(membership_header, 0xC, std::int32_t{1});
    memory.Put(membership_values, 0, AbsentWord(member));
    memory.Put(membership_guard, 0, std::int32_t{-2});
    memory.Put(inline_context, 0x68, aggregate_keys);
    memory.Put(inline_context, 0x74, std::int32_t{3});
    memory.Put(inline_context, 0xD0, aggregate_values);
    memory.Put(aggregate_keys, 0, std::uint16_t{0x100});
    memory.Put(aggregate_keys, 2, std::uint16_t{0x25D});
    memory.Put(aggregate_keys, 4, std::uint16_t{0x300});
    memory.Put(aggregate_values, 0, std::int64_t{99});
    memory.Put(aggregate_values, 8, std::int64_t{50000});
    memory.Put(aggregate_values, 16, std::int64_t{88});
    memory.Put(aggregate_guard, 0, std::int32_t{-2});
    memory.Put(multiplier, 0, std::int64_t{200000});
    memory.Put(lower, 0, std::int64_t{-10000000});
    memory.Put(upper, 0, std::int64_t{1300000});
  }
  auto Observe() {
    AbsentRequire(!bindings.provider && !bindings.government && !bindings.existing_token_lookup,
                  "absent fixture native callback assigned");
    const auto first = xar::ck3_12002::ReadCurrentContextSourceInputs12003(bindings, character, 29829);
    const auto second = xar::ck3_12002::ReadCurrentContextSourceInputs12003(bindings, character, 29829);
    AbsentRequire(first == second, "absent same-frame whole snapshot differs");
    AbsentRequire(first.absent_recipient_inputs.has_value(), "absent leaf missing");
    AbsentRequire(memory.Attempts() == 0, "absent undemanded bytes read");
    return first;
  }
  void ManagedRange() {
    bindings.helper_291f0a0_enabled = true;
    bindings.selector_a_storage_slot = storage_slot;
    bindings.selector_a_initial_fallback_slot = fallback_slot;
    bindings.selector_a_second_storage_slot = memory.Allocate(8);
    bindings.selector_a_second_fallback_slot = memory.Allocate(8);
    bindings.helper_third_storage_slot = memory.Allocate(8);
    bindings.helper_third_fallback_slot = memory.Allocate(8);
    void *second = memory.Allocate(0x90);
    void *third = memory.Allocate(0x28);
    memory.Put(const_cast<void *>(bindings.selector_a_second_fallback_slot), 0, second);
    memory.Put(const_cast<void *>(bindings.helper_third_fallback_slot), 0, third);
    bindings.helper_manager_slot = memory.Allocate(8);
    void *manager = memory.Allocate(0xEF8);
    void *definition = memory.Allocate(0x78);
    void *ranges = memory.Allocate(0x218);
    void *keys = memory.Allocate(2);
    void *values = memory.Allocate(8);
    memory.Put(const_cast<void *>(bindings.helper_manager_slot), 0, manager);
    memory.Put(manager, 0xEF0, definition);
    memory.Put(definition, 0x58, ranges);
    memory.Put(definition, 0x64, std::int32_t{1});
    memory.Put(ranges, 0, keys);
    memory.Put(ranges, 0xC, std::int32_t{1});
    memory.Put(ranges, 0x68, values);
    memory.Put(ranges, 0x74, std::int32_t{1});
    memory.Put(keys, 0, std::uint16_t{5});
    memory.Put(values, 0, std::int64_t{777});
    bindings.helper_range_first_threshold_slot = memory.Allocate(8);
    bindings.helper_range_last_threshold_slot = memory.Allocate(8);
    memory.Put(const_cast<void *>(bindings.helper_range_first_threshold_slot), 0, std::int64_t{2000000});
    memory.Put(const_cast<void *>(bindings.helper_range_last_threshold_slot), 0, std::int64_t{3000000});
    bindings.helper_source_pointer_fallback_header = membership_header;
    bindings.helper_source_pointer_fallback_guard_slot = membership_guard;
  }
};
void AbsentSave(const std::filesystem::path &directory, const char *name,
               const xar::game::BattleCurrentPersonContextSourceInputsSnapshotV1 &snapshot) {
  if (directory.empty()) return;
  std::ofstream output(directory / (std::string(name) + ".json"), std::ios::binary);
  output << xar::bridge::SerializeBattleCurrentPersonContextSourceInputsV1(snapshot);
  if (!output) throw std::runtime_error("absent recipient wire write failed");
}
void AbsentScalar(const xar::game::ContextSourceAbsentRecipientInputsV1 &leaf,
                  std::int64_t value) {
  AbsentRequire(leaf.ready && leaf.status == "available" &&
                    leaf.calculated_recipient_q64 == value,
                "absent native recipient scalar differs");
}
}

// The coordinating target owns main, build and test invocation.
void RunAbsentRecipientFixture(const std::filesystem::path &directory) {
  constexpr std::uintptr_t base = 0x140000000ULL;
  const auto exact = xar::ck3_12002::BindAbsentRecipientSources12003(base);
  AbsentRequire(exact.enabled && exact.associated_storage_slot == reinterpret_cast<const void *>(base + 0x5D1E2F8) &&
      exact.associated_fallback_slot == reinterpret_cast<const void *>(base + 0x5C67670) &&
      exact.membership_inline_header == reinterpret_cast<const void *>(base + 0x5D67E40) &&
      exact.membership_guard_slot == reinterpret_cast<const void *>(base + 0x5D67E38) &&
      exact.aggregate_inline_context == reinterpret_cast<const void *>(base + 0x5D67B90) &&
      exact.aggregate_guard_slot == reinterpret_cast<const void *>(base + 0x5D67B80) &&
      exact.member_multiplier_slot == reinterpret_cast<const void *>(base + 0x5C696F8) &&
      exact.clamp_lower_slot == reinterpret_cast<const void *>(base + 0x5C68E00) &&
      exact.clamp_upper_slot == reinterpret_cast<const void *>(base + 0x5C68DF8), "absent exact RVA binding");
  {
    AbsentFixture f;
    f.ManagedRange();
    const auto s = f.Observe();
    const auto &leaf = *s.absent_recipient_inputs;
    AbsentScalar(leaf, 1300000);
    AbsentRequire(leaf.associated_full_id == AbsentFixture::associated_id &&
        leaf.associated_resolved_full_id == AbsentFixture::associated_id &&
        leaf.associated_used_fallback == false && leaf.cached_map_430.entries &&
        leaf.cached_map_430.entries->at(0).bucket_index == 1 &&
        leaf.cached_map_430.entries->at(1).bucket_index == 3 &&
        leaf.cached_map_430.entries->at(2).bucket_index == 7 &&
        leaf.cached_map_430.entries->at(0).trait_id_u32 == AbsentFixture::trait_id &&
        leaf.cached_map_430.entries->at(1).key_object != leaf.cached_map_430.entries->at(0).key_object,
        "absent raw ID/pointer/order metadata changed");
    AbsentRequire(s.helper_291f0a0 && s.helper_291f0a0->ready && s.helper_291f0a0->manager_range.ready &&
        s.helper_291f0a0->recipient_source == "absent_1c8_2bfac30_cached" &&
        s.helper_291f0a0->recipient_q64 == 1300000 && s.helper_291f0a0->range_native_index == 0 &&
        s.helper_291f0a0->manager_range.rows && s.helper_291f0a0->manager_range.rows->at(0).admitted == true &&
        s.helper_291f0a0->manager_range.rows->at(0).property_block->values_q64->at(0) == 777,
        "absent scalar failed to unlock actual managed range PC");
    AbsentSave(directory, "absent-member-managed-range", s);
  }
  {
    AbsentFixture f;
    f.memory.Put(f.membership_values, 0, AbsentWord(f.member) ^ (1ULL << 40));
    f.memory.Deny(f.multiplier, 0, 8);
    const auto s = f.Observe();
    AbsentScalar(*s.absent_recipient_inputs, 1050000);
    AbsentRequire(!s.absent_recipient_inputs->member_multiplier_q64, "nonmember demanded multiplier");
    AbsentSave(directory, "absent-full-qword-nonmember", s);
  }
  {
    AbsentFixture f;
    f.memory.Put(f.membership_header, 0xC, std::int32_t{0});
    f.memory.Deny(f.associated, 0x458, 0x28);
    f.memory.Deny(f.membership_header, 0, 8);
    f.memory.Deny(f.multiplier, 0, 8);
    const auto s = f.Observe();
    AbsentScalar(*s.absent_recipient_inputs, 1050000);
    AbsentRequire(!s.absent_recipient_inputs->cached_map_458.count, "empty membership demanded map458");
    AbsentSave(directory, "absent-membership-empty", s);
  }
  {
    AbsentFixture f;
    f.memory.Put(f.associated, 0x440, std::int32_t{-2});
    f.memory.Deny(f.associated, 0x438, 8);
    f.memory.Deny(f.associated, 0x458, 0x28);
    f.memory.Deny(f.character, 0xF8, 0x10);
    f.memory.Deny(f.membership_guard, 0, 4);
    f.memory.Deny(f.membership_header, 0, 0x10);
    f.memory.Deny(f.multiplier, 0, 8);
    const auto s = f.Observe();
    AbsentScalar(*s.absent_recipient_inputs, 50000);
    AbsentRequire(s.absent_recipient_inputs->cached_map_430.count == -2 &&
        s.absent_recipient_inputs->cached_map_430.entries->empty() &&
        !s.absent_recipient_inputs->trait_ids.count, "nonpositive cached copier demand differs");
    AbsentSave(directory, "absent-cached-empty", s);
  }
  {
    AbsentFixture f;
    f.memory.Put(f.associated, 0x440, std::uint32_t{0});
    f.memory.Deny(f.associated, 0x430, 0x10);
    f.memory.Deny(f.associated, 0x444, 0x44);
    f.memory.Deny(f.character, 0xF8, 0x10);
    f.memory.Deny(f.aggregate_guard, 0, 4);
    const auto s = f.Observe();
    AbsentRequire(!s.absent_recipient_inputs->ready && !s.absent_recipient_inputs->calculated_recipient_q64 &&
        s.absent_recipient_inputs->associated_cache_440 == 0U && !s.absent_recipient_inputs->cached_map_430.count,
        "uncached branch read stale cached maps");
    AbsentSave(directory, "absent-cache-zero-derived-partial", s);
  }
  {
    AbsentFixture f;
    f.memory.Put(f.character, 0x1C8, f.member);
    f.memory.Deny(f.character, 0xB4, 4);
    f.memory.Deny(f.associated, 0x430, 0x58);
    const auto s = f.Observe();
    AbsentRequire(s.absent_recipient_inputs->ready && s.absent_recipient_inputs->status == "not_applicable" &&
        !s.absent_recipient_inputs->calculated_recipient_q64 && !s.absent_recipient_inputs->associated_cache_440,
        "present1C8 skip demanded absent receiver");
    AbsentSave(directory, "absent-present-carrier-skip", s);
  }
  for (const std::int32_t guard : {0, -1}) {
    AbsentFixture f;
    f.memory.Put(f.aggregate_guard, 0, guard);
    const auto s = f.Observe();
    AbsentRequire(!s.absent_recipient_inputs->ready && !s.absent_recipient_inputs->calculated_recipient_q64 &&
        s.absent_recipient_inputs->aggregate_context_guard_raw == guard &&
        s.absent_recipient_inputs->aggregate_properties.values_q64->at(1) == 50000,
        "inline aggregate current bytes or uninitialized guard lost");
    AbsentSave(directory, guard == 0 ? "absent-inline-aggregate-guard-zero" : "absent-inline-aggregate-guard-minus-one", s);
  }
  {
    AbsentFixture f;
    f.memory.Put(f.membership_guard, 0, std::int32_t{-1});
    const auto s = f.Observe();
    AbsentRequire(!s.absent_recipient_inputs->ready && !s.absent_recipient_inputs->calculated_recipient_q64 &&
        s.absent_recipient_inputs->membership_header_guard_raw == -1 && s.absent_recipient_inputs->membership_ids.count == 1,
        "membership inprogress guard declared ready");
    AbsentSave(directory, "absent-membership-guard-minus-one", s);
  }
  {
    AbsentFixture f;
    void *scratch = f.memory.Allocate(0x260);
    void *model = f.memory.Allocate(0xE8);
    f.memory.Put(f.character, 0x1B0, scratch);
    f.memory.Put(scratch, 0x258, model);
    f.memory.Put(model, 8, f.character);
    f.memory.Put(model, 0x78, f.aggregate_keys);
    f.memory.Put(model, 0x84, std::int32_t{3});
    f.memory.Put(model, 0xE0, f.aggregate_values);
    f.memory.Put(f.aggregate_guard, 0, std::int32_t{0});
    f.memory.Deny(f.aggregate_guard, 0, 4);
    f.memory.Deny(f.inline_context, 0, 0xD8);
    const auto s = f.Observe();
    AbsentScalar(*s.absent_recipient_inputs, 1300000);
    AbsentRequire(s.absent_recipient_inputs->aggregate_context_selection == "owned_model_10" &&
        !s.absent_recipient_inputs->aggregate_context_guard_raw, "owned model demanded unrelated inline guard");
    AbsentSave(directory, "absent-owned-current-model", s);
  }
  {
    AbsentFixture f;
    f.memory.Put(f.map430, 1 * 24 + 0x10, std::numeric_limits<std::int64_t>::min());
    f.memory.Put(f.multiplier, 0, std::int64_t{-200000});
    f.memory.Put(f.lower, 0, std::numeric_limits<std::int64_t>::min());
    f.memory.Put(f.upper, 0, std::numeric_limits<std::int64_t>::max());
    const auto s = f.Observe();
    AbsentScalar(*s.absent_recipient_inputs, 750000);
    AbsentSave(directory, "absent-decomposed-min64-product", s);
  }
  {
    AbsentFixture f;
    f.memory.Put(f.lower, 0, std::int64_t{1400000});
    f.memory.Put(f.upper, 0, std::int64_t{1000000});
    const auto s = f.Observe();
    AbsentScalar(*s.absent_recipient_inputs, 1400000);
    AbsentSave(directory, "absent-signed-lower-first-clamp", s);
  }
}
