#include "xar_bridge/sway_completion_causal_observer_12004.hpp"
#include <atomic>
#include <cstring>
#include <windows.h>

namespace xar::ck3_12004 {
namespace {
std::atomic<std::uint64_t> next_session{1};
std::atomic<std::uint64_t> current_session{0};
std::atomic<std::uint64_t> next_invocation{1};
}
std::uint64_t BeginSwayCausalObserverSession12004() noexcept {
  const auto session = next_session.fetch_add(1, std::memory_order_relaxed);
  if (session == 0) return 0;
  std::uint64_t expected = 0;
  return current_session.compare_exchange_strong(expected, session,
      std::memory_order_acq_rel) ? session : 0;
}
std::uint64_t CurrentSwayCausalObserverSession12004() noexcept {
  return current_session.load(std::memory_order_acquire);
}
void EndSwayCausalObserverSession12004(std::uint64_t session) noexcept {
  if (session != 0) (void)current_session.compare_exchange_strong(session, 0,
      std::memory_order_acq_rel);
}
std::uint64_t NextSwayCausalInvocation12004() noexcept {
  return next_invocation.fetch_add(1, std::memory_order_relaxed);
}
std::size_t ReadAdmittedSwayImageSize12004(std::uintptr_t base) noexcept {
  if (base == 0) return 0;
  // Only the admitted loaded image's PE header is copied. No executable scan,
  // disk read, version guess or inferred image boundary is performed.
  __try {
    IMAGE_DOS_HEADER dos{};
    std::memcpy(&dos, reinterpret_cast<const void *>(base), sizeof(dos));
    if (dos.e_magic != IMAGE_DOS_SIGNATURE || dos.e_lfanew <= 0 ||
        dos.e_lfanew > 0x100000) return 0;
    IMAGE_NT_HEADERS64 nt{};
    std::memcpy(&nt, reinterpret_cast<const void *>(base +
        static_cast<std::uintptr_t>(dos.e_lfanew)), sizeof(nt));
    if (nt.Signature != IMAGE_NT_SIGNATURE ||
        nt.OptionalHeader.Magic != IMAGE_NT_OPTIONAL_HDR64_MAGIC) return 0;
    return nt.OptionalHeader.SizeOfImage;
  } __except (EXCEPTION_EXECUTE_HANDLER) { return 0; }
}
}
