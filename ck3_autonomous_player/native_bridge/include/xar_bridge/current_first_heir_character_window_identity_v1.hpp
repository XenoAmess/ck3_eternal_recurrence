#pragma once

#include "xar_bridge/ck3_12004.hpp"

#include <cstdint>
#include <optional>
#include <string>

namespace xar::ck3_11906 {
struct ZhongguoScoreboardNativeEnvironmentV1;
}

namespace xar::bridge {

struct CurrentFirstHeirCharacterWindowIdentityV1 {
  bool receiver_available{};
  std::string receiver_unavailable_reason;
  std::optional<std::int32_t> raw_character_id;
  bool character_available{};
  std::string character_unavailable_reason;
  std::optional<std::int32_t> character_id;
};

// Reads an already selected complete CCharacterWindow object. Receiver selection
// remains separate from this exact-build object and full Character ID reader.
CurrentFirstHeirCharacterWindowIdentityV1
ReadCurrentFirstHeirCharacterWindowObject12004V1(
    std::uintptr_t module_base, std::uintptr_t image_size,
    const xar::ck3_12004::CoreBindings &core, const void *receiver) noexcept;

// Shared production/fixture candidate selection from an already admitted
// handler; the selected object must still pass the exact CharacterWindow checks.
CurrentFirstHeirCharacterWindowIdentityV1
ReadCurrentFirstHeirCharacterWindowCandidate12004V1(
    std::uintptr_t module_base, std::uintptr_t image_size,
    const xar::ck3_12004::CoreBindings &core,
    const void *admitted_handler) noexcept;

CurrentFirstHeirCharacterWindowIdentityV1
ReadCurrentFirstHeirCharacterWindowIdentity12004V1(
    const xar::ck3_11906::ZhongguoScoreboardNativeEnvironmentV1 &environment,
    const xar::ck3_12004::CoreBindings &core) noexcept;

} // namespace xar::bridge
