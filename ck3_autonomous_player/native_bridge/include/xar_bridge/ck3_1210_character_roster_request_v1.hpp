#pragma once
#include "xar_bridge/ck3_1210_actor_readonly_request_v1.hpp"
#include "xar_bridge/ck3_1210_character_roster_frame_v1.hpp"
namespace xar::ck3_1210 {
using CharacterRosterRequestV1 = ActorReadonlyRequestV1;
inline bool ParseCharacterRosterRequestV1(std::string_view json, CharacterRosterRequestV1 &output) noexcept {
  return ParseActorReadonlyRequestV1(json, kCharacterRosterStepV1, ActorReadonlyRevisionV1::positive, output);
}
} // namespace xar::ck3_1210
