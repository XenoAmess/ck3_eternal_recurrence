#include "xar_bridge/h2743_stock_predicate_reader_v1.hpp"

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <limits>

#ifndef XAR_CK3_ENABLE_H2743_STOCK_PREDICATE_READER_V1
#define XAR_CK3_ENABLE_H2743_STOCK_PREDICATE_READER_V1 0
#endif

// Native calls below are the MSVC x64 ABI of the frozen 1.19.0.6 executable.
// Other platforms/toolchains keep the binding disabled, including macro ON.
#if XAR_CK3_ENABLE_H2743_STOCK_PREDICATE_READER_V1 && defined(_WIN32) &&       \
    defined(_MSC_VER) && defined(_M_X64)
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#endif

namespace xar::game {
namespace {

#if XAR_CK3_ENABLE_H2743_STOCK_PREDICATE_READER_V1 && defined(_WIN32) &&       \
    defined(_MSC_VER) && defined(_M_X64)

constexpr std::uintptr_t kLookupIdentifierRvaV1 = 0x3B588E0;
constexpr std::uintptr_t kIdentifierNameRvaV1 = 0x3B58970;
constexpr std::uintptr_t kIdentifierNameFallbackRvaV1 = 0x585F058;
constexpr std::uintptr_t kStableNameHashRvaV1 = 0x3B8B000;
constexpr std::int32_t kMissingIdentifierV1 = 12;
constexpr std::size_t kMaximumNativeNameBytesV1 = 512;

// Exactly 16 bytes: the lookup takes signed length at +8 and ownership flags
// at +0xC. A caller-owned bounded view always has flags zero.
struct NativeIdentifierViewV1 {
  const char *data;
  std::int32_t length;
  std::uint32_t flags;
};
static_assert(sizeof(NativeIdentifierViewV1) == 0x10);
static_assert(offsetof(NativeIdentifierViewV1, length) == 0x08);
static_assert(offsetof(NativeIdentifierViewV1, flags) == 0x0C);

// Borrowed engine MSVC string; no std::string methods or ownership transfer.
struct NativeStringHeaderV1 {
  unsigned char storage[0x10];
  std::uint64_t size;
  std::uint64_t capacity;
};
static_assert(sizeof(NativeStringHeaderV1) == 0x20);
static_assert(offsetof(NativeStringHeaderV1, size) == 0x10);
static_assert(offsetof(NativeStringHeaderV1, capacity) == 0x18);

struct LocalNameV1 {
  char bytes[kMaximumNativeNameBytesV1 + 1]{};
  std::uint32_t length = 0;
};

bool HasExtentV1(std::uintptr_t address, std::size_t size) noexcept {
  return address != 0 && size != 0 &&
         size <= (std::numeric_limits<std::uintptr_t>::max)() - address;
}

bool ContextAllowedV1(const H2743StockNativeContextV1 *context) noexcept {
  if (context == nullptr || context->module_base == 0 ||
      !context->exact_build_verified ||
      context->application_main_thread_id == 0 ||
      context->application_main_thread_id != GetCurrentThreadId() ||
      context->observe_stamp == nullptr ||
      context->module_base !=
          reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)))
    return false;
  return HasExtentV1(context->module_base, kIdentifierNameFallbackRvaV1 + 1);
}

bool ReadBytesV1(void *opaque, std::uintptr_t address, void *output,
                 std::size_t size) noexcept {
  const auto *context = static_cast<H2743StockNativeContextV1 *>(opaque);
  if (!ContextAllowedV1(context) || output == nullptr ||
      !HasExtentV1(address, size))
    return false;
  SIZE_T read = 0;
  return ReadProcessMemory(GetCurrentProcess(),
                           reinterpret_cast<const void *>(address), output,
                           size, &read) != FALSE &&
         read == size;
}

bool ValidUtf8V1(const char *bytes, std::size_t size) noexcept {
  const auto *data = reinterpret_cast<const unsigned char *>(bytes);
  for (std::size_t i = 0; i < size;) {
    const auto lead = data[i];
    if (lead == 0)
      return false;
    if (lead <= 0x7F) {
      ++i;
      continue;
    }
    const std::size_t continuation =
        lead >= 0xC2 && lead <= 0xDF ? 1 :
        lead >= 0xE0 && lead <= 0xEF ? 2 :
        lead >= 0xF0 && lead <= 0xF4 ? 3 : 0;
    if (continuation == 0 || continuation >= size - i)
      return false;
    const auto second = data[i + 1];
    if ((lead == 0xE0 && second < 0xA0) ||
        (lead == 0xED && second >= 0xA0) ||
        (lead == 0xF0 && second < 0x90) ||
        (lead == 0xF4 && second >= 0x90))
      return false;
    for (std::size_t j = 1; j <= continuation; ++j)
      if (data[i + j] < 0x80 || data[i + j] > 0xBF)
        return false;
    i += continuation + 1;
  }
  return true;
}

bool CopyNameV1(H2743StockNativeContextV1 &context, std::string_view name,
                LocalNameV1 &copy) noexcept {
  if (name.empty() || name.data() == nullptr ||
      name.size() > kMaximumNativeNameBytesV1 ||
      !ReadBytesV1(&context, reinterpret_cast<std::uintptr_t>(name.data()),
                   copy.bytes, name.size()) ||
      !ValidUtf8V1(copy.bytes, name.size()))
    return false;
  copy.length = static_cast<std::uint32_t>(name.size());
  copy.bytes[copy.length] = '\0';
  return true;
}

// SEH is restricted to leaf functions with only pointers and POD arguments.
// No C++ object requiring unwinding is created inside an __try region.
bool ProtectedLookupV1(std::uintptr_t address,
                       const NativeIdentifierViewV1 *view,
                       std::int32_t &identifier) noexcept {
  using NativeLookup =
      std::int32_t(__fastcall *)(const NativeIdentifierViewV1 *);
  __try {
    identifier = reinterpret_cast<NativeLookup>(address)(view);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
}

bool ProtectedIdentifierNameV1(std::uintptr_t address,
                               std::int32_t identifier,
                               std::uintptr_t &name) noexcept {
  using NativeName = const void *(__fastcall *)(std::int32_t);
  __try {
    name = reinterpret_cast<std::uintptr_t>(
        reinterpret_cast<NativeName>(address)(identifier));
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
}

bool ProtectedHashV1(std::uintptr_t address, const char *bytes,
                     std::uint32_t length, std::uint32_t &hash) noexcept {
  using NativeHash =
      std::uint32_t(__fastcall *)(void *, const char *, std::uint32_t);
  __try {
    hash = reinterpret_cast<NativeHash>(address)(nullptr, bytes, length);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
}

bool IdentifierRoundTripV1(H2743StockNativeContextV1 &context,
                           std::int32_t identifier,
                           const LocalNameV1 &expected) noexcept {
  std::uintptr_t name = 0;
  if (!ProtectedIdentifierNameV1(context.module_base + kIdentifierNameRvaV1,
                                 identifier, name) ||
      name == 0 || name == context.module_base + kIdentifierNameFallbackRvaV1)
    return false;
  NativeStringHeaderV1 header{};
  if (!ReadBytesV1(&context, name, &header, sizeof(header)) ||
      header.size != expected.length ||
      header.size > kMaximumNativeNameBytesV1 ||
      header.capacity < header.size)
    return false;
  std::uintptr_t bytes = name;
  if (header.capacity >= 0x10)
    std::memcpy(&bytes, header.storage, sizeof(bytes));
  char actual[kMaximumNativeNameBytesV1 + 1]{};
  const auto extent = static_cast<std::size_t>(header.size) + 1;
  if (!ReadBytesV1(&context, bytes, actual, extent) ||
      actual[expected.length] != '\0' ||
      std::memcmp(actual, expected.bytes, expected.length) != 0)
    return false;
  NativeStringHeaderV1 after{};
  return ReadBytesV1(&context, name, &after, sizeof(after)) &&
         std::memcmp(&header, &after, sizeof(header)) == 0 &&
         ContextAllowedV1(&context);
}

bool LookupIdentifierV1(void *opaque, std::string_view name,
                        std::int32_t &output) noexcept {
  output = -1;
  auto *context = static_cast<H2743StockNativeContextV1 *>(opaque);
  if (!ContextAllowedV1(context))
    return false;
  LocalNameV1 copy{};
  if (!CopyNameV1(*context, name, copy))
    return false;
  const NativeIdentifierViewV1 view{
      copy.bytes, static_cast<std::int32_t>(copy.length), 0};
  std::int32_t identifier = -1;
  if (!ProtectedLookupV1(context->module_base + kLookupIdentifierRvaV1,
                         &view, identifier) ||
      identifier < 0 || identifier == kMissingIdentifierV1 ||
      !IdentifierRoundTripV1(*context, identifier, copy))
    return false;
  output = identifier;
  return true;
}

bool HashNameV1(void *opaque, std::string_view name,
                std::uint32_t &output) noexcept {
  output = 0;
  auto *context = static_cast<H2743StockNativeContextV1 *>(opaque);
  if (!ContextAllowedV1(context))
    return false;
  LocalNameV1 copy{};
  if (!CopyNameV1(*context, name, copy))
    return false;
  std::uint32_t hash = 0;
  if (!ProtectedHashV1(context->module_base + kStableNameHashRvaV1,
                       copy.bytes, copy.length, hash) ||
      !ContextAllowedV1(context))
    return false;
  output = hash;
  return true;
}

bool ReadStampV1(void *opaque,
                 H2743StockPredicateStampV1 &output) noexcept {
  output = {};
  auto *context = static_cast<H2743StockNativeContextV1 *>(opaque);
  if (!ContextAllowedV1(context))
    return false;
  H2743StockPredicateStampV1 observed{};
  if (!context->observe_stamp(context->stamp_opaque, observed) ||
      !ContextAllowedV1(context))
    return false;
  output = observed;
  return true;
}

#endif

} // namespace

H2743StockPredicateBindingsV1 BindH2743StockNativeSourcesV1(
    H2743StockNativeContextV1 &context) noexcept {
  H2743StockPredicateBindingsV1 bindings{};
#if XAR_CK3_ENABLE_H2743_STOCK_PREDICATE_READER_V1 && defined(_WIN32) &&       \
    defined(_MSC_VER) && defined(_M_X64)
  if (!ContextAllowedV1(&context))
    return bindings;
  bindings.opaque = &context;
  bindings.module_base = context.module_base;
  bindings.enabled = true;
  bindings.exact_build_verified = true;
  bindings.application_main_verified = true;
  bindings.read_bytes = &ReadBytesV1;
  bindings.lookup_identifier = &LookupIdentifierV1;
  bindings.hash_name = &HashNameV1;
  bindings.read_stamp = &ReadStampV1;
#else
  (void)context;
#endif
  return bindings;
}

} // namespace xar::game
