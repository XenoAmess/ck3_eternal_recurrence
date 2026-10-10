#include "xar_bridge/army_position_helper_2c09360_12004.hpp"
#include <cstring>
#include <stdexcept>
#include <unordered_map>
#include <vector>

namespace {
using namespace xar::ck3_12004;

struct OwnedMemory {
  std::unordered_map<std::uintptr_t, std::vector<unsigned char>> fields;
  std::vector<std::uintptr_t> consumed_addresses;

  template <class T> void Put(std::uintptr_t address, const T &value) {
    auto &bytes = fields[address];
    bytes.resize(sizeof(value));
    std::memcpy(bytes.data(), &value, sizeof(value));
  }
  static bool Read(void *context, std::uintptr_t address, void *out,
      std::size_t count) noexcept {
    auto &self = *static_cast<OwnedMemory *>(context);
    try {
      self.consumed_addresses.push_back(address);
      if (self.consumed_addresses.size() > 1024) return false;
      const auto found = self.fields.find(address);
      if (found == self.fields.end() || found->second.size() != count) return false;
      std::memcpy(out, found->second.data(), count);
      return true;
    } catch (...) { return false; }
  }
};

void Require(bool result, const char *message) {
  if (!result) throw std::runtime_error(message);
}
} // namespace

// One owned frame exercises the reached null-R8 relation path and its failures.
// Central 33 owns main/argv; this export has no main and invokes no native code.
void RunArmyPositionHelperNaturalFocus12004() {
  constexpr std::uintptr_t image = 0x100000000ULL;
  constexpr std::uintptr_t holder = 0x200000;
  constexpr std::uintptr_t actor = 0x300000;
  constexpr std::uintptr_t pair_map = 0x400000;
  constexpr std::uintptr_t relation_rows = 0x500000;
  constexpr std::uintptr_t relation = 0x600000;
  constexpr std::uintptr_t holder_domain = 0x700000;
  constexpr std::uintptr_t war_manager = 0x800000;
  constexpr std::uintptr_t war_slots = 0x900000;
  constexpr std::uintptr_t war = 0xA00000;
  constexpr std::uintptr_t fallback_war = 0xB00000;
  constexpr std::int32_t war_id = 0x01000002;
  OwnedMemory memory;
  memory.Put(holder + 0x18, std::int32_t{11});
  memory.Put(actor + 0x18, std::int32_t{22});
  // Prefix direction is holder -> actor. An empty holder War descriptor makes
  // that prefix false; the relation gate remains actually reached in this frame.
  memory.Put(holder + 0x1C0, holder_domain);
  memory.Put(holder_domain + 0x318, std::uintptr_t{0});
  memory.Put(holder_domain + 0x324, std::int32_t{0});
  memory.Put(image + 0x5D1DE58, war_manager);
  memory.Put(image + 0x5D1DE40, fallback_war);
  memory.Put(holder + 0x1B0, pair_map);
  memory.Put(pair_map + 0x2C, std::int32_t{1});
  memory.Put(pair_map + 0x20, relation_rows);
  memory.Put(relation_rows, std::uint32_t{22});
  memory.Put(relation_rows + 8, relation);
  memory.Put(relation + 0x20, war_id);
  memory.Put(war_manager + 0x2C, std::uint32_t{3});
  memory.Put(war_manager + 0x20, war_slots);
  memory.Put(war_slots + 2 * 16 + 8, war);
  memory.Put(war + 8, war_id);
  memory.Put(war + 0x358, std::uint8_t{0});
  ArmyRegularCoreReadonlyAccess12004 access;
  access.image_base = image;
  access.read_context = &memory;
  access.read = &OwnedMemory::Read;
  access.maximum_occurrences = 8;

  const auto allowed = ReadArmyPosition2C0936012004(access, holder, actor, 0);
  Require(allowed.value.has_value() && *allowed.value,
      "null-R8 helper must retain the non-ended reached War condition");
  memory.Put(war + 0x358, std::uint8_t{1});
  const auto ended = ReadArmyPosition2C0936012004(access, holder, actor, 0);
  Require(ended.value.has_value() && !*ended.value,
      "null-R8 must not bypass the actual War ended-byte condition");
  memory.fields.erase(war + 0x358);
  const auto absent = ReadArmyPosition2C0936012004(access, holder, actor, 0);
  Require(!absent.value.has_value() && !absent.unavailable_reason.empty(),
      "a missing reached War field must remain unavailable");

  // Only the two original ID fields exist: the native first return must not
  // require any prefix/relation/War fields or a nonzero image binding.
  memory.fields.clear();
  memory.consumed_addresses.clear();
  memory.Put(holder + 0x18, std::int32_t{11});
  memory.Put(actor + 0x18, std::int32_t{11});
  access.image_base = 0;
  const auto same_id = ReadArmyPosition2C0936012004(access, holder, actor, 0);
  Require(same_id.value.has_value() && *same_id.value &&
      memory.consumed_addresses.size() == 2 &&
      memory.consumed_addresses[0] == holder + 0x18 &&
      memory.consumed_addresses[1] == actor + 0x18,
      "same original full ID must return true before any dependency read");
}
