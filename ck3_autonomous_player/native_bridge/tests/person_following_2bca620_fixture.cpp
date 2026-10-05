#include "xar_bridge/ck3_12003_context_sources.hpp"
#include "xar_bridge/ck3_12003.hpp"
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
void Require(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}
struct Memory {
  struct Region { std::unique_ptr<std::byte[]> bytes; std::size_t size; };
  struct Denied { std::uintptr_t address; std::size_t size; std::size_t attempts = 0; };
  std::vector<Region> regions;
  std::vector<Denied> denied;
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
  std::size_t Attempts() const {
    std::size_t result = 0;
    for (const auto &entry : denied) result += entry.attempts;
    return result;
  }
  static bool Read(void *context, const void *address, void *output,
                   std::size_t size) noexcept {
    auto &memory = *static_cast<Memory *>(context);
    const auto begin = reinterpret_cast<std::uintptr_t>(address);
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
void *At(void *address, std::size_t offset) {
  return static_cast<std::byte *>(address) + offset;
}
using Snapshot = xar::game::BattleCurrentPersonContextSourceInputsSnapshotV1;

// The minimum nonnegative classifier uses this fixed frame only. No native
// income/evaluator/getter/initializer callback is installed. Two full queries
// read identical source bytes and the actual complete DTO is serialized.
struct Fixture {
  Memory memory;
  xar::ck3_12002::ContextSourceBindingsV1 bindings{};
  void *character = memory.Allocate(0x1D8);
  void *component = memory.Allocate(0x580);
  void *provider = memory.Allocate(0x16A0);
  void *provider_slot = memory.Allocate(8);
  void *provider_fallback_slot = memory.Allocate(8);
  void *sentinel = memory.Allocate(0xB8);
  void *fallback = memory.Allocate(0xB8);

  void Property(void *pc, const std::vector<std::uint16_t> &keys,
                const std::vector<std::int64_t> &values) {
    Require(keys.size() == values.size(), "following2bca620 property pair size");
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
  Fixture() {
    bindings.enabled = true;
    bindings.read_memory = &Memory::Read;
    bindings.read_context = &memory;
    auto &b = bindings.following_2bca620;
    b.enabled = true;
    b.provider_slot = provider_slot;
    b.provider_fallback_slot = provider_fallback_slot;
    memory.Put(character, 0x18, std::int32_t{29829});
    memory.Put(character, 0x1C, std::uint32_t{0x43686172U});
    memory.Put(character, 0x1B0, component);
    memory.Put(component, 0x100, std::int64_t{900000});
    memory.Put(provider_slot, 0, provider);
    memory.Put(provider, 0x126C, std::int32_t{3});
    memory.Put(provider, 0x1690, sentinel);
    memory.Put(provider_fallback_slot, 0, fallback);
    memory.Put(sentinel, 0x38, std::uint32_t{0x4744624FU});
    memory.Put(fallback, 0x38, std::uint32_t{0x4744624FU});
    memory.Put(fallback, 0x10, std::int32_t{-1});
    Property(At(sentinel, 0x40), {42}, {4200});
    Property(At(fallback, 0x40), {41}, {4100});

    // Actual empty headers for the already collected source branches.
    void *first = memory.Allocate(0x220);
    void *second = memory.Allocate(0x150);
    bindings.first_storage_slot = memory.Allocate(8);
    bindings.first_fallback_slot = memory.Allocate(8);
    bindings.second_storage_slot = memory.Allocate(8);
    bindings.second_fallback_slot = memory.Allocate(8);
    memory.Put(const_cast<void *>(bindings.first_fallback_slot), 0, first);
    memory.Put(const_cast<void *>(bindings.second_fallback_slot), 0, second);
    bindings.lifestyle_fallback_header = memory.Allocate(0x10);
    bindings.house_extra_fallback_header = memory.Allocate(0x10);
    bindings.source_fallback_header = memory.Allocate(0x10);
    // Indexed provider1260 is unreachable in the sealed minimum classifier.
    memory.Deny(provider, 0x1260, 8);
  }
  Snapshot Observe() {
    Require(bindings.enabled && bindings.following_2bca620.enabled,
            "following2bca620 source binding disabled");
    Require(!bindings.gated_temporary_tail.enabled && !bindings.after_gated_tail.enabled &&
                !bindings.provider192_and2920850.enabled && !bindings.following_2920b50.enabled &&
                !bindings.pre_291e210_1640_enabled && !bindings.later_direct_enabled &&
                !bindings.helper_291f0a0_enabled && !bindings.remaining_helpers_enabled &&
                !bindings.tail_direct_enabled && !bindings.post_291d7e0_sources_enabled &&
                !bindings.trait_stage.enabled && !bindings.middle_helpers.enabled &&
                !bindings.tail_prefix_enabled && !bindings.helper_2922070_enabled,
            "other optional source leaf enabled");
    Require(!bindings.provider && !bindings.government && !bindings.existing_token_lookup,
            "following2bca620 fixture must not install native callbacks");
    const auto first = xar::ck3_12002::ReadCurrentContextSourceInputs12003(
        bindings, character, 29829);
    const auto second = xar::ck3_12002::ReadCurrentContextSourceInputs12003(
        bindings, character, 29829);
    Require(first == second, "following2bca620 whole snapshots differ in fixed frame");
    Require(first.following_2bca620.has_value(), "following2bca620 source leaf absent");
    Require(memory.Attempts() == 0, "following2bca620 unused numeric operands were demanded");
    return first;
  }
};
void Save(const std::filesystem::path &directory, const char *name,
          const Snapshot &snapshot) {
  if (directory.empty()) return;
  std::ofstream output(directory / (std::string("following2bca620-") + name + ".json"),
                       std::ios::binary);
  output << xar::bridge::SerializeBattleCurrentPersonContextSourceInputsV1(snapshot);
  if (!output) throw std::runtime_error("following2bca620 wire write failed");
}
void PCValue(const auto &pc, std::uint16_t key, std::int64_t value) {
  Require(pc.property_identity && pc.property_block && pc.property_block->keys_u16 &&
              pc.property_block->values_q64 && pc.property_block->keys_u16->size() == 1 &&
              pc.property_block->values_q64->size() == 1 &&
              pc.property_block->keys_u16->at(0) == key &&
              pc.property_block->values_q64->at(0) == value,
          "following2bca620 raw paired property differs");
}
void EmptyPC(const auto &pc) {
  Require(pc.property_identity && pc.property_block && pc.property_block->keys_count == 0 &&
              !pc.property_block->values_count && pc.property_block->keys_u16 &&
              pc.property_block->keys_u16->empty() && pc.property_block->values_q64 &&
              pc.property_block->values_q64->empty(),
          "following2bca620 empty PC must retain its outer request without value reads");
}
void KnownNonnegative(const auto &leaf, std::int64_t numeric_balance) {
  Require(leaf.ready && leaf.balance_source.numeric_balance_q64 == numeric_balance &&
              leaf.classifier.ready && leaf.classifier.selection == "nonnegative_balance_minus_one" &&
              leaf.classifier.index_raw_i32 == -1 && leaf.classifier.reason.empty() &&
              leaf.provider_selection.ready && leaf.provider_selection.provider_loaded == true,
          "following2bca620 minimum classifier must produce minus-one from actual nonnegative balance");
}
void ExactBindings() {
  constexpr std::uintptr_t base = 0x140000000;
  const auto bindings = xar::ck3_12002::BindContextSourceInputs12003(
      base, xar::ck3_12003::kExecutableSha256);
  const auto &b = bindings.following_2bca620;
  const auto address = [base](std::uintptr_t rva) {
    return reinterpret_cast<const void *>(base + rva);
  };
  Require(bindings.enabled && b.enabled && b.provider_slot == address(0x5C670F8) &&
              b.provider_fallback_slot == address(0x5D1E0B0),
          "following2bca620 exact-build bindings differ");
  Require(!xar::ck3_12002::BindContextSourceInputs12003(base, "wrong-build").following_2bca620.enabled,
          "following2bca620 exact-build factory accepted wrong build");
}
void Run(const std::filesystem::path &directory) {
  ExactBindings();
  {
    Fixture f;
    f.memory.Deny(f.provider, 0x1690, 8);
    f.memory.Deny(f.fallback, 0x10, 4);
    const auto snapshot = f.Observe();
    const auto &leaf = *snapshot.following_2bca620;
    Require(snapshot.ready && leaf.balance_source.component_present == true &&
                leaf.balance_source.balance_raw_q64 == 900000 &&
                leaf.provider_selection.count_raw == 3 &&
                leaf.provider_selection.selection == "global_fallback_5d1e0b0" &&
                leaf.provider_selection.admitted == true,
            "following2bca620 nonnegative balance must use fallback without ID gate");
    KnownNonnegative(leaf, 900000);
    PCValue(leaf.provider_selection.pc, 41, 4100);
    Save(directory, "nonnegative-fallback", snapshot);
  }
  {
    Fixture f;
    f.memory.Put(f.component, 0x100, std::int64_t{0});
    f.memory.Put(f.provider, 0x126C, std::int32_t{-1});
    f.memory.Deny(f.provider_fallback_slot, 0, 8);
    const auto snapshot = f.Observe();
    const auto &leaf = *snapshot.following_2bca620;
    Require(snapshot.ready && leaf.provider_selection.count_raw == -1 &&
                leaf.provider_selection.selection == "provider_1690_equality_sentinel" &&
                leaf.provider_selection.admitted == true,
            "following2bca620 minus-one equality must precede negative index fallback");
    KnownNonnegative(leaf, 0);
    PCValue(leaf.provider_selection.pc, 42, 4200);
    Save(directory, "count-minus-one-equality", snapshot);
  }
  {
    Fixture f;
    f.memory.Put(f.character, 0x1B0, static_cast<void *>(nullptr));
    f.memory.Put(f.provider, 0x126C, std::int32_t{1});
    f.Property(At(f.fallback, 0x40), {43}, {4300});
    f.memory.Deny(f.component, 0x100, 8);
    f.memory.Deny(f.provider, 0x1690, 8);
    const auto snapshot = f.Observe();
    const auto &leaf = *snapshot.following_2bca620;
    Require(snapshot.ready && leaf.balance_source.component_present == false &&
                !leaf.balance_source.balance_raw_q64 &&
                leaf.provider_selection.selection == "global_fallback_5d1e0b0",
            "following2bca620 absent component must preserve source-defined numeric zero");
    KnownNonnegative(leaf, 0);
    PCValue(leaf.provider_selection.pc, 43, 4300);
    Save(directory, "absent-carrier-zero", snapshot);
  }
  {
    Fixture f;
    f.memory.Put(f.component, 0x100, std::numeric_limits<std::int64_t>::max());
    f.memory.Put(f.provider, 0x126C, std::int32_t{0});
    f.Property(At(f.fallback, 0x40), {}, {});
    f.memory.Deny(f.provider, 0x1690, 8);
    f.memory.Deny(f.fallback, 0x40, 8);
    f.memory.Deny(f.fallback, 0x40 + 0x68, 8);
    f.memory.Deny(f.fallback, 0x40 + 0x74, 4);
    const auto snapshot = f.Observe();
    const auto &leaf = *snapshot.following_2bca620;
    Require(snapshot.ready && leaf.provider_selection.selection == "global_fallback_5d1e0b0" &&
                leaf.provider_selection.admitted == true,
            "following2bca620 actual empty PC must retain one admitted occurrence");
    KnownNonnegative(leaf, std::numeric_limits<std::int64_t>::max());
    EmptyPC(leaf.provider_selection.pc);
    Save(directory, "empty-pc", snapshot);
  }
  {
    Fixture f;
    f.memory.Put(f.component, 0x100, std::int64_t{0});
    f.memory.Put(f.provider, 0x126C, std::int32_t{-1});
    f.memory.Put(f.sentinel, 0x38, std::uint32_t{0});
    f.memory.Deny(f.sentinel, 0x40, 0x78);
    f.memory.Deny(f.provider_fallback_slot, 0, 8);
    const auto snapshot = f.Observe();
    const auto &leaf = *snapshot.following_2bca620;
    Require(snapshot.ready && leaf.provider_selection.selection == "provider_1690_equality_sentinel" &&
                leaf.provider_selection.definition_magic_u32 == 0U &&
                leaf.provider_selection.admitted == false &&
                !leaf.provider_selection.pc.property_identity && !leaf.provider_selection.pc.property_block,
            "following2bca620 magic rejection must be known zero without PC demand");
    KnownNonnegative(leaf, 0);
    Save(directory, "wrong-magic-skip", snapshot);
  }
  {
    Fixture f;
    f.memory.Put(f.component, 0x100, std::int64_t{-1});
    f.memory.Deny(f.provider, 0x126C, 4);
    f.memory.Deny(f.provider, 0x1690, 8);
    f.memory.Deny(f.provider_fallback_slot, 0, 8);
    const auto snapshot = f.Observe();
    const auto &leaf = *snapshot.following_2bca620;
    const auto &p = leaf.provider_selection;
    Require(!snapshot.ready && !leaf.ready && leaf.balance_source.component_present == true &&
                leaf.balance_source.balance_raw_q64 == -1 &&
                leaf.balance_source.numeric_balance_q64 == -1 && !leaf.classifier.ready &&
                leaf.classifier.selection == "negative_balance_income_unobserved" &&
                !leaf.classifier.index_raw_i32 &&
                leaf.classifier.reason == "negative_balance_income_2bca4e0" &&
                p.provider_loaded == true && !p.ready && !p.count_raw && !p.selection &&
                !p.definition_identity && !p.definition_magic_u32 && !p.admitted &&
                !p.pc.property_identity && !p.pc.property_block,
            "following2bca620 negative balance must preserve the exact missing income input");
    Save(directory, "negative-balance-partial", snapshot);
  }
}
} // namespace

void RunFollowing2bca620Fixture(const std::filesystem::path &directory) {
  if (!directory.empty()) std::filesystem::create_directories(directory);
  Run(directory);
}
