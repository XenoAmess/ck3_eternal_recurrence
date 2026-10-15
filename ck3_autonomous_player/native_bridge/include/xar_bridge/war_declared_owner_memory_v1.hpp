#pragma once

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <limits>

namespace xar::ck3_11906::detail {

// The application-owner executor reads its own process. This uses the same
// SEH-guarded memcpy admission as ReadGuiWidgetRuntimeV1, avoiding a kernel
// ReadProcessMemory round trip for every child/header field. A fault is unknown.
inline bool ReadWarDeclaredOwnerBytesV1(const void *address, void *output,
                                      std::size_t size) noexcept {
  if (!address || !output || !size) return false;
#if defined(_MSC_VER)
  __try { std::memcpy(output, address, size); return true; }
  __except (1) { return false; }
#else
  return false;
#endif
}

template<class T>
inline bool ReadWarDeclaredOwnerValueV1(std::uintptr_t base, std::size_t offset,
                                      T &value) noexcept {
  if (!base || offset > (std::numeric_limits<std::uintptr_t>::max)() - base) return false;
  return ReadWarDeclaredOwnerBytesV1(reinterpret_cast<const void *>(base + offset),
                                    &value, sizeof(value));
}

} // namespace xar::ck3_11906::detail
