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
void UncachedRequire(bool value, const char *label) {
  if (!value) throw std::runtime_error(label);
}
struct UncachedMemory {
  struct Region { std::unique_ptr<std::byte[]> data; std::size_t size; };
  std::vector<Region> regions;
  void *Allocate(std::size_t size) {
    auto data = std::make_unique<std::byte[]>(size);
    auto *address = data.get();
    regions.push_back({std::move(data), size});
    return address;
  }
  template <typename T> void Put(void *address, std::size_t offset, T value) {
    std::memcpy(static_cast<std::byte *>(address) + offset, &value, sizeof(value));
  }
  static bool Read(void *context, const void *address, void *output, std::size_t bytes) noexcept {
    auto &memory = *static_cast<UncachedMemory *>(context);
    const auto begin = reinterpret_cast<std::uintptr_t>(address);
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
void *UncachedAt(void *address, std::size_t offset) {
  return static_cast<std::byte *>(address) + offset;
}
std::uint64_t UncachedWord(const void *address) {
  return static_cast<std::uint64_t>(reinterpret_cast<std::uintptr_t>(address));
}
struct UncachedSourceRow {
  void *key;
  std::int64_t value;
  std::uint8_t marker = 2;
};
struct UncachedFixture {
  UncachedMemory memory;
  xar::ck3_12002::ContextSourceBindingsV1 bindings{};
  void *character = memory.Allocate(0x1D0);
  void *associated = memory.Allocate(0x948);
  void *first = memory.Allocate(0x90);
  void *second = memory.Allocate(0x28);
  void *definition = memory.Allocate(0xA00);
  void *key = memory.Allocate(0x18);
  void *active = memory.Allocate(0x1100);
  void *removed = memory.Allocate(0x900);
  void *positive_fallback = memory.Allocate(0x40);
  void *negative_fallback = memory.Allocate(0x40);
  void *membership_header = memory.Allocate(0x10);
  void *membership_guard = memory.Allocate(4);
  void *aggregate = memory.Allocate(0xD8);
  void *aggregate_guard = memory.Allocate(4);

  void *Slot(const void *value) {
    auto *slot = memory.Allocate(8);
    memory.Put(slot, 0, value);
    return slot;
  }
  template <typename T> void *Scalar(T value) {
    auto *slot = memory.Allocate(sizeof(value));
    memory.Put(slot, 0, value);
    return slot;
  }
  void SetFamily(void *family, const std::vector<UncachedSourceRow> &first_rows,
                 const std::vector<UncachedSourceRow> &second_rows = {}) {
    std::size_t offset = 0;
    for (const auto *rows : {&first_rows, &second_rows}) {
      memory.Put(family, offset + 0xC, static_cast<std::int32_t>(rows->size()));
      if (!rows->empty()) {
        auto *data = memory.Allocate(rows->size() * 40);
        memory.Put(family, offset, data);
        for (std::size_t i = 0; i < rows->size(); ++i) {
          memory.Put(data, i * 40 + 8, rows->at(i).key);
          memory.Put(data, i * 40 + 0x14, rows->at(i).marker);
          memory.Put(data, i * 40 + 0x20, rows->at(i).value);
        }
      }
      offset = 0x168;
    }
  }
  void Traits(const std::vector<std::uint32_t> &ids) {
    memory.Put(character, 0x104, static_cast<std::int32_t>(ids.size()));
    if (!ids.empty()) {
      auto *values = memory.Allocate(ids.size() * 4);
      memory.Put(character, 0xF8, values);
      for (std::size_t i = 0; i < ids.size(); ++i) memory.Put(values, i * 4, ids[i]);
    }
  }
  void Members(const std::vector<std::uint64_t> &ids) {
    memory.Put(membership_header, 0xC, static_cast<std::int32_t>(ids.size()));
    if (!ids.empty()) {
      auto *values = memory.Allocate(ids.size() * 8);
      memory.Put(membership_header, 0, values);
      for (std::size_t i = 0; i < ids.size(); ++i) memory.Put(values, i * 8, ids[i]);
    }
  }
  void Active(std::int64_t value, std::uint8_t flag = 4) {
    auto *objects = memory.Allocate(8);
    memory.Put(objects, 0, active);
    memory.Put(associated, 0x770, objects);
    memory.Put(associated, 0x77C, std::int32_t{1});
    auto *context = memory.Allocate(2 * 16);
    memory.Put(context, 0, active);
    memory.Put(context, 8, flag);
    memory.Put(context, 16, active);
    memory.Put(context, 24, std::uint8_t{1});
    memory.Put(associated, 0x788, context);
    memory.Put(associated, 0x794, std::int32_t{2});
    SetFamily(UncachedAt(active, 0xF70), {{key, value}});
  }
  void Removed(std::int64_t value, bool kind2) {
    auto *objects = memory.Allocate(8);
    memory.Put(objects, 0, removed);
    memory.Put(associated, 0x7A0, objects);
    memory.Put(associated, 0x7AC, std::int32_t{1});
    if (kind2) SetFamily(UncachedAt(removed, 0x728), {}, {{key, value}});
    else SetFamily(UncachedAt(removed, 0x728), {{key, value}});
  }
  void ManagedRange() {
    bindings.helper_291f0a0_enabled = true;
    bindings.selector_a_storage_slot = bindings.absent_recipient.associated_storage_slot;
    bindings.selector_a_initial_fallback_slot = bindings.absent_recipient.associated_fallback_slot;
    bindings.selector_a_second_storage_slot = bindings.uncached_recipient.first_registry_slot;
    bindings.selector_a_second_fallback_slot = bindings.uncached_recipient.first_fallback_slot;
    bindings.helper_third_storage_slot = bindings.uncached_recipient.second_registry_slot;
    bindings.helper_third_fallback_slot = bindings.uncached_recipient.second_fallback_slot;
    void *manager = memory.Allocate(0xEF8);
    void *managed = memory.Allocate(0x78);
    void *ranges = memory.Allocate(0x218);
    void *keys = Scalar(std::uint16_t{5});
    void *values = Scalar(std::int64_t{777});
    bindings.helper_manager_slot = Slot(manager);
    memory.Put(manager, 0xEF0, managed);
    memory.Put(managed, 0x58, ranges);
    memory.Put(managed, 0x64, std::int32_t{1});
    memory.Put(ranges, 0, keys);
    memory.Put(ranges, 0xC, std::int32_t{1});
    memory.Put(ranges, 0x68, values);
    memory.Put(ranges, 0x74, std::int32_t{1});
    bindings.helper_range_first_threshold_slot = Scalar(std::int64_t{2000000});
    bindings.helper_range_last_threshold_slot = Scalar(std::int64_t{3000000});
    bindings.helper_source_pointer_fallback_header = membership_header;
    bindings.helper_source_pointer_fallback_guard_slot = membership_guard;
  }
  UncachedFixture() {
    bindings.enabled = true;
    bindings.read_memory = &UncachedMemory::Read;
    bindings.read_context = &memory;
    auto &a = bindings.absent_recipient;
    a.enabled = true;
    a.associated_storage_slot = Slot(nullptr);
    a.associated_fallback_slot = Slot(associated);
    a.membership_inline_header = membership_header;
    a.membership_guard_slot = membership_guard;
    a.aggregate_inline_context = aggregate;
    a.aggregate_guard_slot = aggregate_guard;
    a.member_multiplier_slot = Scalar(std::int64_t{200000});
    a.clamp_lower_slot = Scalar(std::numeric_limits<std::int64_t>::min());
    a.clamp_upper_slot = Scalar(std::numeric_limits<std::int64_t>::max());
    auto &b = bindings.uncached_recipient;
    b.enabled = true;
    b.first_registry_slot = Slot(nullptr);
    b.first_fallback_slot = Slot(first);
    b.second_registry_slot = Slot(nullptr);
    b.second_fallback_slot = Slot(second);
    b.fallback_key_slot = Slot(key);
    b.cap_slot = Scalar(std::int32_t{2});
    b.active_flag4_multiplier_slot = Scalar(std::int64_t{150000});
    b.active_other_multiplier_slot = Scalar(std::int64_t{50000});
    b.seed_boost_multiplier_slot = Scalar(std::int64_t{25000});
    b.positive_fallback_slot = Slot(positive_fallback);
    b.negative_fallback_slot = Slot(negative_fallback);
    memory.Put(character, 0x18, std::int32_t{29829});
    memory.Put(character, 0x1C, std::uint32_t{0x43686172});
    memory.Put(character, 0xB4, std::uint32_t{0xAB000001});
    memory.Put(character, 0x15C, std::int32_t{-1});
    memory.Put(associated, 8, std::uint32_t{0xAB000001});
    memory.Put(associated, 0x4B8, std::uint32_t{0xCD000001});
    memory.Put(first, 8, std::uint32_t{0xCD000002});
    memory.Put(first, 0x8C, std::uint32_t{0xEF000001});
    memory.Put(second, 8, std::uint32_t{0xEF000002});
    memory.Put(second, 0x20, definition);
    memory.Put(key, 0x10, std::int32_t{17});
    memory.Put(active, 0x38, std::uint32_t{0x4744624F});
    memory.Put(removed, 0x38, std::uint32_t{0x4744624F});
    SetFamily(UncachedAt(definition, 0x648), {});
    Traits({17});
    Members({});
    memory.Put(membership_guard, 0, std::int32_t{-2});
    memory.Put(aggregate_guard, 0, std::int32_t{-2});
    auto *keys = Scalar(std::uint16_t{0x25D});
    auto *values = Scalar(std::int64_t{10000});
    memory.Put(aggregate, 0x68, keys);
    memory.Put(aggregate, 0x74, std::int32_t{1});
    memory.Put(aggregate, 0xD0, values);
  }
  auto Observe() {
    UncachedRequire(!bindings.provider && !bindings.government && !bindings.existing_token_lookup,
                    "uncached fixture assigned native callback");
    auto snapshot = xar::ck3_12002::ReadCurrentContextSourceInputs12003(bindings, character, 29829);
    UncachedRequire(snapshot.uncached_recipient_inputs.has_value(), "uncached current query leaf missing");
    return snapshot;
  }
};
void UncachedSave(const std::filesystem::path &directory, const char *name,
    const xar::game::BattleCurrentPersonContextSourceInputsSnapshotV1 &snapshot) {
  if (directory.empty()) return;
  std::ofstream out(directory / (std::string(name) + ".json"), std::ios::binary);
  out << xar::bridge::SerializeBattleCurrentPersonContextSourceInputsV1(snapshot);
  if (!out) throw std::runtime_error("uncached production wire write failed");
}
void UncachedScalar(const xar::game::ContextSourceUncachedRecipientInputsV1 &out, std::int64_t value) {
  UncachedRequire(out.ready && out.status == "available" && out.calculated_recipient_q64 == value,
                  "uncached production scalar differs");
}
}

// The coordinating target owns main, build and execution. No earlier fixture
// is invoked by this hook.
void RunUncachedRecipientFixture(const std::filesystem::path &directory) {
  constexpr std::uintptr_t base = 0x140000000ULL;
  const auto b = xar::ck3_12002::BindUncachedRecipientSources12003(base);
  UncachedRequire(b.enabled && b.first_registry_slot == reinterpret_cast<const void *>(base + 0x5D1E300) &&
      b.first_fallback_slot == reinterpret_cast<const void *>(base + 0x5D1E2E0) &&
      b.second_registry_slot == reinterpret_cast<const void *>(base + 0x5D1DE88) &&
      b.second_fallback_slot == reinterpret_cast<const void *>(base + 0x5D1DE00) &&
      b.fallback_key_slot == reinterpret_cast<const void *>(base + 0x5D1E318) &&
      b.cap_slot == reinterpret_cast<const void *>(base + 0x5C697EC) &&
      b.active_flag4_multiplier_slot == reinterpret_cast<const void *>(base + 0x5C68CD0) &&
      b.active_other_multiplier_slot == reinterpret_cast<const void *>(base + 0x5C69708) &&
      b.seed_boost_multiplier_slot == reinterpret_cast<const void *>(base + 0x5C69710) &&
      b.positive_fallback_slot == reinterpret_cast<const void *>(base + 0x5D1F6C0) &&
      b.negative_fallback_slot == reinterpret_cast<const void *>(base + 0x5D1E288), "uncached exact RVA binding differs");
  {
    UncachedFixture f;
    f.SetFamily(UncachedAt(f.definition, 0x648), {{f.key, 100000}});
    f.Active(200000);
    f.Removed(300000, false);
    f.Members({UncachedWord(f.active)});
    f.ManagedRange();
    const auto s = f.Observe();
    const auto &leaf = *s.uncached_recipient_inputs;
    UncachedScalar(leaf, 660000);
    UncachedRequire(leaf.seed_receiver.first_used_fallback == true &&
        leaf.seed_receiver.first_full_id == 0xCD000001U &&
        leaf.seed_receiver.first_resolved_full_id == 0xCD000002U &&
        leaf.active_context.entries->at(0).flag_u8 == 4 &&
        leaf.active_context.entries->at(1).flag_u8 == 1,
        "uncached actual receiver/context order lost");
    UncachedRequire(s.helper_291f0a0 && s.helper_291f0a0->ready &&
        s.helper_291f0a0->recipient_source == "absent_1c8_2bfac30_uncached" &&
        s.helper_291f0a0->recipient_q64 == 660000 && s.helper_291f0a0->manager_range.ready &&
        s.helper_291f0a0->manager_range.rows &&
        s.helper_291f0a0->manager_range.rows->at(0).property_block->values_q64->at(0) == 777,
        "uncached scalar did not unlock actual manager-range property block");
    UncachedSave(directory, "uncached-seed-active-member", s);
  }
  {
    UncachedFixture f;
    auto *other = f.memory.Allocate(0x18);
    f.memory.Put(other, 0x10, std::int32_t{18});
    f.memory.Put(const_cast<void *>(f.bindings.uncached_recipient.cap_slot), 0, std::int32_t{1});
    f.memory.Put(const_cast<void *>(f.bindings.uncached_recipient.seed_boost_multiplier_slot), 0, std::int64_t{0});
    f.SetFamily(UncachedAt(f.definition, 0x648), {{f.key, 100000}, {other, 100000}});
    const auto s = f.Observe();
    UncachedScalar(*s.uncached_recipient_inputs, 10000);
    UncachedRequire(!s.uncached_recipient_inputs->downstream_inputs.trait_ids.count &&
        !s.uncached_recipient_inputs->downstream_inputs.membership_header_guard_raw,
        "tie-group empty output demanded trait/membership");
    UncachedSave(directory, "uncached-tie-group-empty", s);
  }
  {
    UncachedFixture f;
    f.SetFamily(UncachedAt(f.definition, 0x648), {{f.key, 100000}});
    f.Removed(400000, true);
    const auto s = f.Observe();
    UncachedScalar(*s.uncached_recipient_inputs, -390000);
    UncachedSave(directory, "uncached-removed-kind-switch", s);
  }
  {
    UncachedFixture f;
    f.memory.Put(f.key, 0x10, std::int32_t{-1});
    f.memory.Put(const_cast<void *>(f.bindings.uncached_recipient.seed_boost_multiplier_slot), 0, std::int64_t{0});
    f.SetFamily(UncachedAt(f.definition, 0x648), {{nullptr, 120000, 0}});
    f.Traits({0xFFFFFFFFU});
    const auto s = f.Observe();
    UncachedScalar(*s.uncached_recipient_inputs, 130000);
    UncachedRequire(s.uncached_recipient_inputs->seed_family.first.records->at(0).key_object == 0ULL &&
        s.uncached_recipient_inputs->fallback_key_id_i32 == -1,
        "marker fallback replaced actual raw key");
    UncachedSave(directory, "uncached-marker-fallback", s);
  }
  {
    UncachedFixture f;
    f.memory.Put(const_cast<void *>(f.bindings.uncached_recipient.cap_slot), 0, std::int32_t{100});
    f.memory.Put(const_cast<void *>(f.bindings.uncached_recipient.seed_boost_multiplier_slot), 0, std::int64_t{0});
    std::vector<UncachedSourceRow> rows;
    std::vector<std::uint32_t> traits;
    for (std::int32_t i = 39; i >= 0; --i) {
      auto *key = f.memory.Allocate(0x18);
      f.memory.Put(key, 0x10, i - 20);
      rows.push_back({key, 100000 + i});
      traits.push_back(static_cast<std::uint32_t>(i - 20));
    }
    f.SetFamily(UncachedAt(f.definition, 0x648), rows);
    f.Traits(traits);
    const auto s = f.Observe();
    UncachedScalar(*s.uncached_recipient_inputs, 4010780);
    UncachedRequire(s.uncached_recipient_inputs->seed_family.first.count == 40 &&
        s.uncached_recipient_inputs->seed_family.first.records->at(0).key_id_i32 == 19 &&
        s.uncached_recipient_inputs->seed_family.first.records->at(39).key_id_i32 == -20,
        "large intrinsic family raw order lost");
    UncachedSave(directory, "uncached-large-forty", s);
  }
  {
    UncachedFixture f;
    f.memory.Put(const_cast<void *>(f.bindings.uncached_recipient.seed_boost_multiplier_slot), 0, std::int64_t{0});
    f.SetFamily(UncachedAt(f.definition, 0x648), {{f.key, 100000}}, {{f.key, 100000}});
    const auto s = f.Observe();
    UncachedScalar(*s.uncached_recipient_inputs, 110000);
    UncachedSave(directory, "uncached-equal-vector-kind-one", s);
  }
  {
    UncachedFixture f;
    f.memory.Put(const_cast<void *>(f.bindings.uncached_recipient.seed_boost_multiplier_slot), 0, std::int64_t{100003});
    f.SetFamily(UncachedAt(f.definition, 0x648), {{f.key, 4611686018427387921LL}});
    const auto s = f.Observe();
    UncachedScalar(*s.uncached_recipient_inputs, -9223233686274212953LL);
    UncachedSave(directory, "uncached-decomposed-maximum-operand", s);
  }
  {
    UncachedFixture f;
    f.SetFamily(UncachedAt(f.definition, 0x648), {{f.key, 100000}});
    f.Active(200000);
    f.Members({UncachedWord(f.active)});
    f.memory.Put(f.membership_guard, 0, std::int32_t{0});
    const auto s = f.Observe();
    UncachedRequire(!s.uncached_recipient_inputs->ready &&
        !s.uncached_recipient_inputs->calculated_recipient_q64 &&
        s.uncached_recipient_inputs->downstream_inputs.membership_header_guard_raw == 0 &&
        s.uncached_recipient_inputs->downstream_inputs.membership_ids.count == 1,
        "uncached membership guard zero lost actual header bytes");
    UncachedSave(directory, "uncached-membership-guard-zero", s);
  }
  {
    UncachedFixture f;
    f.bindings.uncached_recipient.cap_slot = nullptr;
    f.SetFamily(UncachedAt(f.definition, 0x648), {{f.key, 100000}});
    const auto s = f.Observe();
    UncachedRequire(!s.uncached_recipient_inputs->ready &&
        !s.uncached_recipient_inputs->calculated_recipient_q64 &&
        !s.uncached_recipient_inputs->cap_i32 && s.uncached_recipient_inputs->seed_family.ready,
        "uncached missing capacity declared numeric ready");
    UncachedSave(directory, "uncached-capacity-read-partial", s);
  }
  for (const bool present : {false, true}) {
    UncachedFixture f;
    if (present) f.memory.Put(f.character, 0x1C8, f.active);
    else f.memory.Put(f.associated, 0x440, std::uint32_t{1});
    const auto s = f.Observe();
    UncachedRequire(s.uncached_recipient_inputs->ready &&
        s.uncached_recipient_inputs->status == "not_applicable" &&
        !s.uncached_recipient_inputs->seed_family.first.count &&
        !s.uncached_recipient_inputs->calculated_recipient_q64,
        "uncached present/cached branch skip differs");
    UncachedSave(directory, present ? "uncached-present-carrier-skip" : "uncached-cache-nonzero-skip", s);
  }
}
