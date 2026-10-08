#pragma once

#include "xar_bridge/ck3_12004_first_heir_descendants.hpp"
#include "xar_bridge/current_first_heir_reproductive_inputs_v1.hpp"

#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
namespace xar::ck3_12004 {

// Actual named is_pregnant: instance slot D8 at 2B6DAF0 calls 28FD1B0.
// The lookup searches these two native pointer arrays in order, using the
// complete mother Character ID at record+8. This observer makes no native
// factory, trigger, conception or event call.
namespace character_pregnancy_abi {
inline constexpr std::size_t kManagerOffset = 0x2EE40;
inline constexpr std::size_t kFirstRecordsOffset = 0x4EA0;
inline constexpr std::size_t kFirstCountOffset = 0x4EAC;
inline constexpr std::size_t kSecondRecordsOffset = 0x4E88;
inline constexpr std::size_t kSecondCountOffset = 0x4E94;
inline constexpr std::size_t kRecordMotherIdOffset = 0x08;
inline constexpr std::size_t kCharacterMagicOffset = 0x1C;
inline constexpr std::uint32_t kCharacterMagic = 0x43686172;
} // namespace character_pregnancy_abi

inline ck3_11906::CurrentCharacterPregnancyReadV1
ReadCurrentCharacterPregnancyV1(const CoreBindings &core,
                              std::int32_t character_id) noexcept {
  using first_heir_descendants_detail::Load;
  using namespace character_pregnancy_abi;
  ck3_11906::CurrentCharacterPregnancyReadV1 result{};
  if (!core.enabled || core.game_state_slot == nullptr ||
      *core.game_state_slot == nullptr) return result;
  const auto *character = xar::ck3_12004::ResolveCoreCharacter(core, character_id);
  if (character == nullptr ||
      Load<std::uint32_t>(character, kCharacterMagicOffset) != kCharacterMagic) {
    result.unavailable_reason = "native_pregnancy_character_unavailable";
    return result;
  }
  const auto *data = Load<const std::byte *>(*core.game_state_slot,
                                           kGameStateDataOffset);
  if (data == nullptr) return result;
  const auto *manager = data + kManagerOffset;
  const auto scan = [&](std::size_t records_offset,
                        std::size_t count_offset) -> std::optional<bool> {
    const auto count = Load<std::int32_t>(manager, count_offset);
    const auto *records = Load<const std::byte *>(manager, records_offset);
    if (count < 0 || (count > 0 && records == nullptr)) return std::nullopt;
    for (std::int32_t index = 0; index < count; ++index) {
      const auto *record = Load<const void *>(records,
          static_cast<std::size_t>(index) * sizeof(void *));
      if (record == nullptr) return std::nullopt;
      if (Load<std::int32_t>(record, kRecordMotherIdOffset) == character_id)
        return true;
    }
    return false;
  };
  const auto first = scan(kFirstRecordsOffset, kFirstCountOffset);
  if (!first.has_value()) {
    result.unavailable_reason = "native_pregnancy_records_unavailable";
    return result;
  }
  const auto pregnancy = *first ? first :
      scan(kSecondRecordsOffset, kSecondCountOffset);
  if (!pregnancy.has_value()) {
    result.unavailable_reason = "native_pregnancy_records_unavailable";
    return result;
  }
  result.status = "available";
  result.unavailable_reason = {};
  result.is_pregnant = *pregnancy;
  return result;
}

} // namespace xar::ck3_12004
#endif
