#pragma once

#include "xar_bridge/conception_modifier_context_12004.hpp"
#include "xar_bridge/construction_owner_mode3_raw_receiver_12004.hpp"
#include "xar_bridge/construction_scaled_key_2c4d530_12004.hpp"

#include <cstdint>
#include <optional>
#include <string>

namespace xar::ck3_12004::construction_owner_mode3 {

enum class CharacterModifierFailure2C4D1D012004 : std::uint8_t {
  none, exact_build, read_callback, detail_branch_not_supplied,
  character_identity_read, fallback_receiver_unqualified,
  modifier_context, scaled_key, modifier_context_changed,
  fallback_receiver_changed, copy_exception,
};

struct CharacterModifier2C4D1D012004 {
  bool ready = false;
  CharacterModifierFailure2C4D1D012004 failure =
      CharacterModifierFailure2C4D1D012004::none;
  std::string reason;
  std::uintptr_t character_identity = 0;
  std::uint16_t key_raw_u16 = 0;
  std::uintptr_t detail_identity = 0;
  std::int64_t scale_raw_q64 = 0;
  std::optional<std::uint32_t> physical_character_id_raw_u32;
  bool source_qualified_fallback = false;
  std::optional<std::uintptr_t> fallback_character_identity;
  ConceptionModifierContextObservation12004 context;
  ScaledCollectionKey12004 scalar;
  std::optional<std::int64_t> value_raw_q64;
};

// Actual2C4D1D0's reached NULL-detail branch: Character getter28C3AC0,
// then scaled key2C4D530 with selector0. Uses guarded copies from the
// supplied exact-build access; invokes no native getter, initialization,
// formatting or destructor. The caller retains its real receiver/frame
// association. A physical +18 copy and repeated context selection protect
// this read; they do not add a native tag or signed-ID admission rule.
CharacterModifier2C4D1D012004 ReadCharacterModifier2C4D1D012004(
    const RawReceiverAccessV1 &access, std::uintptr_t character,
    std::uint16_t key, std::uintptr_t detail = 0,
    std::int64_t scale = 100000) noexcept;

} // namespace xar::ck3_12004::construction_owner_mode3
