#include "native_mandatory_choice_controller_v1.hpp"

#include <Windows.h>
#include <bcrypt.h>

#if defined(_MSC_VER)
#pragma comment(lib, "bcrypt.lib")
#endif

namespace xar::mandatory_choice_v1 {
std::string SecureNativeChoiceNonceV1() {
  unsigned char random[24]{};
  if (BCryptGenRandom(nullptr,random,sizeof(random),
                      BCRYPT_USE_SYSTEM_PREFERRED_RNG) < 0) return {};
  constexpr char hex[] = "0123456789abcdef";
  std::string token; token.reserve(sizeof(random)*2);
  for (auto c : random) {token += hex[c >> 4]; token += hex[c & 15];}
  return token;
}
} // namespace xar::mandatory_choice_v1
