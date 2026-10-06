#pragma once

#include <cstdint>
#include <optional>
#include <string_view>
#include <vector>

namespace xar::ck3_12002 { struct ArmyBindings; }

namespace xar::game {
struct ArmyStrengthSnapshot;

enum class FixedChunk0PreparationInputStatusV1 : std::uint8_t {
  unavailable, partial, available,
};

constexpr std::string_view FixedChunk0PreparationInputStatusNameV1(
    FixedChunk0PreparationInputStatusV1 status) noexcept {
  switch (status) {
  case FixedChunk0PreparationInputStatusV1::available: return "available";
  case FixedChunk0PreparationInputStatusV1::partial: return "partial";
  default: return "unavailable";
  }
}

struct FixedChunk0PreparationPersistentInputV1 {
  std::int32_t persistent_regiment_id = -1;
  FixedChunk0PreparationInputStatusV1 status =
      FixedChunk0PreparationInputStatusV1::unavailable;
  std::string_view unavailable_reason{};
  std::optional<std::int32_t> containing_guard_138_raw;
  std::optional<std::uint32_t> containing_definition_magic_38;
  std::optional<bool> native_fixed_chunk0_can_replenish;
  std::optional<std::int64_t> fresh_fraction_raw;
  friend bool operator==(const FixedChunk0PreparationPersistentInputV1 &,
                         const FixedChunk0PreparationPersistentInputV1 &) = default;
};

struct FixedChunk0PreparationInputsV1 {
  FixedChunk0PreparationInputStatusV1 status =
      FixedChunk0PreparationInputStatusV1::unavailable;
  std::int32_t subject_army_id = -1;
  std::int32_t subject_carmy_id = -1;
  bool referenced_persistent_ids_complete = false;
  std::string_view unavailable_reason{};
  std::vector<FixedChunk0PreparationPersistentInputV1> persistent_regiments;
  friend bool operator==(const FixedChunk0PreparationInputsV1 &,
                         const FixedChunk0PreparationInputsV1 &) = default;
};
} // namespace xar::game

namespace xar::ck3_12003 {
// Same owning-thread Strength sample, after complete DATA capture. This reads
// current preparation operands only; it never calls262C6A0 or writes148.
game::FixedChunk0PreparationInputsV1 ReadFixedChunk0PreparationInputsV1(
    const ck3_12002::ArmyBindings &, const game::ArmyStrengthSnapshot &) noexcept;
} // namespace xar::ck3_12003
