#include "xar_bridge/ck3_12002_war_cash_treasury.hpp"

#include <cstring>

#if defined(_MSC_VER)
#include <windows.h>
#endif

namespace xar::ck3_12002 {
namespace {
bool ReadGold(const void *character, std::int64_t &value) noexcept {
#if defined(_MSC_VER)
  __try {
#endif
    void *extension = nullptr;
    std::memcpy(&extension,
                static_cast<const std::byte *>(character) +
                    kWarCashCharacterLivingExtensionOffset,
                sizeof(extension));
    if (extension == nullptr) {
      value = 0;
    } else {
      std::memcpy(&value,
                  static_cast<const std::byte *>(extension) +
                      kWarCashCharacterGoldOffset,
                  sizeof(value));
    }
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#endif
}
} // namespace

bool ReadWarCashTreasury(const CoreBindings &bindings,
                         std::int32_t character_id,
                         std::int64_t &gold_raw) noexcept {
  gold_raw = 0;
  void *character = ResolveCoreCharacter(bindings, character_id);
  if (character == nullptr) return false;
  std::int64_t value = 0;
  if (!ReadGold(character, value)) return false;
  gold_raw = value;
  return true;
}

} // namespace xar::ck3_12002
