#pragma once
#include "xar_bridge/battle_person_rule43_diac_v1.hpp"
#include <cstdint>
#include <string_view>

namespace xar::ck3_12003 {
struct Rule43DiacBindingsV1 {
  bool enabled = false;
  std::uintptr_t image_base = 0;
  const void *diac_storage_slot = nullptr, *diac_fallback_slot = nullptr;
  const void *character_storage_slot = nullptr, *character_fallback_slot = nullptr;
  const void *rule_provider_slot = nullptr, *rule_mode_slot = nullptr;
  const void *root_registry_header = nullptr, *root_fallback_descriptor = nullptr;
  DiacLiteralNumericBindings12003 numeric{};
  DiacLiteralNumericReadMemory12003 read_memory = nullptr;
  void *read_context = nullptr;
};
Rule43DiacBindingsV1 BindRule43DiacSources12003(std::uintptr_t, std::string_view);
game::FollowingDiac2920d60V1 ReadRule43DiacSources12003(
    const Rule43DiacBindingsV1 &, const void *character, std::int32_t character_id);
} // namespace xar::ck3_12003
