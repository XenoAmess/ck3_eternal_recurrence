#include "xar_bridge/ck3_12003_current_commander_martial.hpp"

namespace xar::ck3_12003 {

CurrentCommanderTotalMartialSnapshot ReadCurrentCommanderTotalMartial(
    std::int32_t actual_character_id, void *validated_current_character,
    std::int32_t (*get_total_skill)(void *, std::int32_t)) noexcept {
  CurrentCommanderTotalMartialSnapshot output{};
  if (actual_character_id == -1) {
    output.unavailable_reason = "current_commander_absent";
    return output;
  }
  output.source_character_id = actual_character_id;
  if (validated_current_character == nullptr) {
    output.unavailable_reason = "current_commander_identity_unavailable";
    return output;
  }
  if (get_total_skill == nullptr) {
    output.unavailable_reason = "current_commander_skill_reader_unavailable";
    return output;
  }
  output.value = get_total_skill(validated_current_character, 1);
  output.status = "available";
  output.unavailable_reason = {};
  return output;
}

} // namespace xar::ck3_12003
