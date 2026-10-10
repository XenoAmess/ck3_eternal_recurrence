#include "xar_bridge/army_position_relation_28bc250_12004.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <stdexcept>
#include <string>

namespace {
using xar::ck3_12004::ArmyRegularCoreReadonlyAccess12004;
using xar::ck3_12004::ReadArmyPositionRelation28BC25012004;

struct RelationScene24 {
  std::array<std::byte, 0x1B8> owner{};
  std::array<std::byte, 0x20> toward{};
  std::array<std::byte, 0x30> map{};
  std::array<std::byte, 48> rows{};
  std::array<std::byte, 0x24> matched{};
  std::array<std::byte, 0x24> fallback{};
  std::uintptr_t fallback_pointer = 0;
  std::uintptr_t image_base = 0x100000;
  std::size_t shared_read_count = 0;
  bool read_war_field = true;
};

template <class T, std::size_t N>
void Put24(std::array<std::byte, N> &buffer, std::size_t offset, T value) {
  std::memcpy(buffer.data() + offset, &value, sizeof(value));
}

template <std::size_t N>
bool CopyOwned24(const std::array<std::byte, N> &buffer,
                 std::uintptr_t address, void *out, std::size_t size) {
  const auto base = reinterpret_cast<std::uintptr_t>(buffer.data());
  if (address < base || size > N || address - base > N - size) return false;
  std::memcpy(out, buffer.data() + (address - base), size);
  return true;
}

bool Read24(void *opaque, std::uintptr_t address,
            void *out, std::size_t size) noexcept {
  auto &scene = *static_cast<RelationScene24 *>(opaque);
  ++scene.shared_read_count;
  if (address == scene.image_base +
                     xar::ck3_12004::kArmyPositionRelationFallbackSlot12004 &&
      size == sizeof(scene.fallback_pointer)) {
    std::memcpy(out, &scene.fallback_pointer, size);
    return true;
  }
  if (!scene.read_war_field &&
      address == reinterpret_cast<std::uintptr_t>(scene.matched.data()) + 0x20)
    return false;
  return CopyOwned24(scene.owner, address, out, size) ||
      CopyOwned24(scene.toward, address, out, size) ||
      CopyOwned24(scene.map, address, out, size) ||
      CopyOwned24(scene.rows, address, out, size) ||
      CopyOwned24(scene.matched, address, out, size) ||
      CopyOwned24(scene.fallback, address, out, size);
}

void Require24(bool condition, const char *description) {
  if (!condition) throw std::runtime_error(description);
}
} // namespace

// Exactly one newly connected leaf case;33b invokes this once in its new argv.
void RunArmyPositionRelationNaturalFocus12004() {
  RelationScene24 scene{};
  const auto owner = reinterpret_cast<std::uintptr_t>(scene.owner.data());
  const auto toward = reinterpret_cast<std::uintptr_t>(scene.toward.data());
  const auto map = reinterpret_cast<std::uintptr_t>(scene.map.data());
  const auto rows = reinterpret_cast<std::uintptr_t>(scene.rows.data());
  const auto matched = reinterpret_cast<std::uintptr_t>(scene.matched.data());
  const auto fallback = reinterpret_cast<std::uintptr_t>(scene.fallback.data());
  Put24(scene.owner, 0x1B0, map);
  Put24(scene.map, 0x20, rows);
  Put24(scene.map, 0x2C, std::int32_t{3});
  Put24(scene.toward, 0x18, std::uint32_t{0x81000042});
  Put24(scene.rows, 0, std::uint32_t{0x02000005});
  Put24(scene.rows, 16, std::uint32_t{0x81000042});
  Put24(scene.rows, 24, matched);
  Put24(scene.rows, 32, std::uint32_t{0xF2000001});
  Put24(scene.matched, 0x20, std::int32_t{0x75000008});
  Put24(scene.fallback, 0x20, std::int32_t{-1});
  scene.fallback_pointer = fallback;
  ArmyRegularCoreReadonlyAccess12004 access{};
  access.image_base = scene.image_base;
  access.read_context = &scene;
  access.read = Read24;
  access.maximum_occurrences = 3;

  const auto present = ReadArmyPositionRelation28BC25012004(access, owner, toward);
  Require24(present.relation_identity == matched &&
                present.war_id == std::int32_t{0x75000008} &&
                present.unavailable_reason.empty(),
            "24c unsigned full-ID lower bound must select the actual matched record");
  Require24(scene.shared_read_count != 0,
            "24c must use the collector's shared guarded read callback");

  Put24(scene.toward, 0x18, std::uint32_t{0x81000043});
  const auto missing = ReadArmyPositionRelation28BC25012004(access, owner, toward);
  Require24(missing.relation_identity == fallback && missing.war_id == -1 &&
                missing.unavailable_reason.empty(),
            "24c missing full-ID key must preserve the actual fallback and -1 sentinel");

  Put24(scene.owner, 0x1B0, std::uintptr_t{0});
  const auto null_map = ReadArmyPositionRelation28BC25012004(access, owner, toward);
  Require24(null_map.relation_identity == fallback && null_map.war_id == -1 &&
                null_map.unavailable_reason.empty(),
            "24c native null-map branch must return the same stock fallback");

  Put24(scene.owner, 0x1B0, map);
  Put24(scene.toward, 0x18, std::uint32_t{0x81000042});
  scene.read_war_field = false;
  const auto partial = ReadArmyPositionRelation28BC25012004(access, owner, toward);
  Require24(partial.relation_identity == matched && !partial.war_id.has_value() &&
                partial.unavailable_reason == "relation_war_id_unreadable",
            "24c unavailable guarded field read must not become observed -1 or false");
}
