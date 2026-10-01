#pragma once
#include "xar_bridge/ck3_12002_realm_law_action_mailbox.hpp"
#include "xar_bridge/ck3_12002_nonwar_realm.hpp"

#include <cassert>
#include <cstring>
#include <iostream>
#include <map>
#include <memory>
#include <vector>

using namespace xar::bridge;
using namespace xar::ck3_12002;
namespace law = xar::ck3_12002::private_law;
namespace {
constexpr std::uintptr_t base = 0x140000000, actor = 0x71000000,
    land = 0x71100000, resource = 0x71200000, primary = 0x71300000,
    secondary = 0x71400000, char_storage = 0x71500000,
    char_slots = 0x71600000, title_storage = 0x71700000,
    title_slots = 0x71800000, law_db = 0x71900000,
    crown = 0x71A00000, succession = 0x71B00000;
constexpr std::int32_t actor_id = 0x01000001, first_id = 0x02000002,
    second_id = 0x03000003, primary_id = 0x04000005,
    secondary_id = 0x05000006;


struct Fixture;
Fixture *current = nullptr;
struct Fixture {
  std::map<std::uintptr_t, std::vector<unsigned char>> blocks;
  std::map<std::uintptr_t, int> laws;
  std::uintptr_t allocation = 0x73000000;
  std::uintptr_t active_slots = 0, primary_successors = 0;
  bool allowed = true;
  std::int64_t exotic_cost = 0;
  int queued = 0;
  RealmLawGovernanceFrameV1 frame{40, 40, 20, 53169072, true, true,
                                 actor_id, true, true};
  void Add(std::uintptr_t address, std::size_t size) { blocks[address].resize(size); }
  template <typename T> void Put(std::uintptr_t address, T value) {
    auto it = blocks.upper_bound(address); assert(it != blocks.begin()); --it;
    const auto offset = address - it->first;
    assert(offset + sizeof(value) <= it->second.size());
    std::memcpy(it->second.data() + offset, &value, sizeof(value));
  }
  std::uintptr_t Allocate(std::size_t size) {
    const auto address = allocation; allocation += 0x10000; Add(address, size); return address;
  }
  void Key(std::uintptr_t address, std::string_view key) {
    Put(address + 0x10, static_cast<std::uint64_t>(key.size()));
    Put(address + 0x18, std::uint64_t{key.size() <= 15 ? 15 : key.size()});
    auto bytes = key.size() <= 15 ? address : Allocate(key.size() + 1);
    if (key.size() > 15) Put(address, bytes);
    for (std::size_t i = 0; i < key.size(); ++i) Put(bytes + i, key[i]);
  }
  static bool Memory(void *opaque, std::uintptr_t address, void *out, std::size_t size) noexcept {
    auto &f = *static_cast<Fixture *>(opaque);
    auto it = f.blocks.upper_bound(address);
    if (it == f.blocks.begin()) return false;
    --it; const auto offset = address - it->first;
    if (offset + size > it->second.size()) return false;
    std::memcpy(out, it->second.data() + offset, size); return true;
  }
  static bool Frame(void *opaque, RealmLawGovernanceFrameV1 &out) noexcept {
    out = static_cast<Fixture *>(opaque)->frame; return true;
  }
  static void *Primary(void *character) { assert(character == reinterpret_cast<void *>(actor)); return reinterpret_cast<void *>(primary); }
  static bool Kind(const void *) { return true; }
  static bool Active(const void *, const void *definition) {
    const auto index = current->laws.at(reinterpret_cast<std::uintptr_t>(definition));
    std::uintptr_t first = 0;
    Memory(current, current->active_slots, &first, sizeof(first));
    return reinterpret_cast<std::uintptr_t>(definition) == first || index == 4;
  }
  static bool Final(const void *, const void *, void *) { return current->allowed; }
  static std::int64_t *Cost(std::int64_t *out, const void *block, std::uint32_t id) {
    assert(id == static_cast<std::uint32_t>(actor_id));
    std::fill_n(out, 10, std::int64_t{0});
    const auto index = current->laws.at(reinterpret_cast<std::uintptr_t>(block) - 0xC40);
    if (index > 0 && index < 4) { out[1] = 20'000'000; out[3] = current->exotic_cost; }
    return out;
  }
  static bool Reason(const void *definition, const void *, void *sink) {
    const bool active = Active(nullptr, definition);
    const auto text = active ? std::string_view("already_active")
                            : current->allowed ? std::string_view{}
                                               : std::string_view("engine_blocked");
    const auto size = static_cast<std::uint64_t>(text.size());
    std::memcpy(static_cast<char *>(sink), text.data(), text.size());
    std::memcpy(static_cast<char *>(sink) + 0x10, &size, 8);
    return !active && current->allowed;
  }
  static void DestroyReason(void *) {}
  static void *Scope(void *out, const void *) { return out; }
  static bool Component(const void *, const void *) { return false; }
  static void DestroyScope(void *) {}
  static bool Validate(void *, const law::AddLawCommandV1 &) noexcept { return current->allowed; }
  static bool Clone(void *, const law::AddLawCommandV1 &command, void *&out) noexcept {
    out = new law::AddLawCommandV1(command); return true;
  }
  static bool Queue(void *opaque, std::uintptr_t, void *&owned, std::uint32_t flags) noexcept {
    assert(flags == 0x0E); ++static_cast<Fixture *>(opaque)->queued;
    delete static_cast<law::AddLawCommandV1 *>(owned); owned = nullptr; return true;
  }
  static void DestroyCommand(void *, void *owned) noexcept { delete static_cast<law::AddLawCommandV1 *>(owned); }

  Fixture() {
    current = this;
    for (const auto [address, size] : std::vector<std::pair<std::uintptr_t, std::size_t>>{
        {actor, 0x300}, {land, 0x300}, {resource, 0x300}, {primary, 0x400},
        {secondary, 0x400}, {char_storage, 0x40}, {char_slots, 16 * 16},
        {title_storage, 0x40}, {title_slots, 16 * 16}, {law_db, 0x80},
        {crown, 0x100}, {succession, 0x100}}) Add(address, size);
    auto Global = [&](std::uintptr_t rva, std::uintptr_t value) { Add(base + rva, 8); Put(base + rva, value); };
    Global(kCampaignRootCharacterStorageSlotRva, char_storage);
    Global(kCampaignRootCharacterFallbackSlotRva, 0);
    Global(kCampaignRootLandedTitleStorageSlotRva, title_storage);
    Global(kCampaignRootLandedTitleFallbackSlotRva, 0);
    Global(law::kLawGroupDatabaseSingletonRva12002, law_db);
    Put(actor + 0x18, actor_id); Put(actor + 0x1C0, land); Put(actor + 0x1B0, resource);
    Put(resource + 0x130, std::int64_t{50'000'000});
    Put(resource + 0x100, std::int64_t{8'000'000});
    Put(resource + 0x110, std::int64_t{7'000'000});
    Put(char_storage + 0x20, char_slots); Put(char_storage + 0x2C, std::int32_t{16});
    Put(char_slots + (actor_id & 0xFFFFFF) * 16 + 8, actor);
    for (const auto id : {first_id, second_id}) {
      auto character = Allocate(0x30); Put(character + 0x18, id);
      Put(char_slots + (id & 0xFFFFFF) * 16 + 8, character);
    }
    Put(title_storage + 0x20, title_slots); Put(title_storage + 0x2C, std::int32_t{16});
    Put(title_slots + (primary_id & 0xFFFFFF) * 16 + 8, primary);
    Put(title_slots + (secondary_id & 0xFFFFFF) * 16 + 8, secondary);
    auto held = Allocate(8); Put(held, primary_id); Put(held + 4, secondary_id);
    Put(land + 0x1E0, held); Put(land + 0x1E8, std::int32_t{2}); Put(land + 0x1EC, std::int32_t{2});
    primary_successors = Allocate(8); Put(primary_successors, first_id); Put(primary_successors + 4, second_id);
    auto secondary_successors = Allocate(8); Put(secondary_successors, second_id); Put(secondary_successors + 4, first_id);
    for (const auto [title, id, successors] : std::vector<std::tuple<std::uintptr_t, std::int32_t, std::uintptr_t>>{
        {primary, primary_id, primary_successors}, {secondary, secondary_id, secondary_successors}}) {
      Put(title + 0x10, id); Put(title + 0x128, actor_id); Put(title + 0x150, successors);
      Put(title + 0x158, std::int32_t{2}); Put(title + 0x15C, std::int32_t{2});
    }
    Key(crown + 0x18, "crown_authority"); Key(succession + 0x18, "succession_order_laws");
    auto groups = Allocate(16); Put(groups, crown); Put(groups + 8, succession);
    Put(law_db + 0x50, groups); Put(law_db + 0x5C, std::int32_t{2});
    auto crown_candidates = Allocate(32), succession_candidates = Allocate(32);
    Put(crown + 0x58, crown_candidates); Put(crown + 0x64, std::int32_t{4});
    Put(succession + 0x58, succession_candidates); Put(succession + 0x64, std::int32_t{4});
    const std::array<std::string_view, 8> keys{"crown_authority_0", "crown_authority_1", "crown_authority_2", "crown_authority_3",
      "confederate_partition_succession_law", "partition_succession_law", "high_partition_succession_law", "single_heir_succession_law"};
    std::array<std::uintptr_t, 8> addresses{};
    for (std::size_t i = 0; i < keys.size(); ++i) {
      auto definition = Allocate(0xD00); addresses[i] = definition;
      laws[definition] = static_cast<int>(i); Key(definition + 0x18, keys[i]);
      if (i < 4) {
        Put(definition + 0xBD8, std::uint8_t{9});
        Put(definition + 0xBD9, std::uint8_t{3});
        Put(definition + 0xBDB, std::uint8_t{2});
        Put(definition + 0xBDC, std::uint8_t{2});
      }
      Put(definition + 0x40, i < 4 ? crown : succession);
      Put((i < 4 ? crown_candidates : succession_candidates) + (i % 4) * 8, definition);
    }
    active_slots = Allocate(16); Put(active_slots, addresses[0]); Put(active_slots + 8, addresses[4]);
    Put(land + 0x200, active_slots); Put(land + 0x208, std::int32_t{2}); Put(land + 0x20C, std::int32_t{2});
  }
};

}
