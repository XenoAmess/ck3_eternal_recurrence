#include "xar_bridge/ck3_12003_context_sources.hpp"

#include <windows.h>

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <stdexcept>

namespace {

void Require(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}

class NoAccessPage {
public:
  NoAccessPage() : address_(VirtualAlloc(nullptr, 0x1000U,
      MEM_RESERVE | MEM_COMMIT, PAGE_NOACCESS)) {
    Require(address_ != nullptr, "PAGE_NOACCESS allocation failed");
  }
  ~NoAccessPage() { VirtualFree(address_, 0U, MEM_RELEASE); }
  NoAccessPage(const NoAccessPage &) = delete;
  NoAccessPage &operator=(const NoAccessPage &) = delete;
  const void *Address() const noexcept { return address_; }

private:
  void *address_;
};

struct CallbackState {
  const void *operand = nullptr;
  const void *resolved = nullptr;
  bool supply = false;
  std::size_t operand_reads = 0;
  std::size_t operand_width = 0;

  static bool Read(void *context, const void *address, void *output,
                   std::size_t bytes) noexcept {
    auto &state = *static_cast<CallbackState *>(context);
    if (address == state.operand) {
      ++state.operand_reads;
      state.operand_width = bytes;
      if (!state.supply || bytes != sizeof(state.resolved)) return false;
      std::memcpy(output, &state.resolved, bytes);
      return true;
    }
    std::memcpy(output, address, bytes);
    return true;
  }
};

void RequireUnavailable(
    const xar::game::BattleCurrentPersonContextSourceInputsSnapshotV1 &observed) {
  Require(observed.pre_291e210_1640.has_value(),
          "production pre291e210 observer was not evaluated");
  const auto &leaf = *observed.pre_291e210_1640;
  Require(!leaf.ready && leaf.status == "partial",
          "unreadable operand became a ready leaf");
  Require(leaf.unavailable_reason == "army_native_fallback_read_unavailable",
          "unreadable slot did not preserve its existing partial reason");
  Require(!leaf.admitted.has_value(),
          "unreadable slot was substituted with false admission");
}

void RequireReadable(
    const xar::game::BattleCurrentPersonContextSourceInputsSnapshotV1 &observed) {
  Require(observed.pre_291e210_1640.has_value(),
          "production pre291e210 observer was not evaluated");
  const auto &leaf = *observed.pre_291e210_1640;
  Require(leaf.ready && leaf.status == "available",
          "readable operand lost its ready leaf");
  Require(leaf.army_field_120_raw == std::int32_t{-1},
          "normal or callback read changed the observed Army field");
  Require(leaf.admitted.has_value() && !*leaf.admitted,
          "known nonadmitted normal operand changed semantics");
  Require(leaf.unavailable_reason.empty(),
          "readable operand acquired a failure reason");
}

} // namespace

int main() {
  try {
    alignas(void *) std::array<std::byte, 0x1C0> character{};
    alignas(void *) std::array<std::byte, 0x180> army{};
    const std::int32_t field120 = -1;
    std::memcpy(army.data() + 0x120, &field120, sizeof(field120));
    const void *army_pointer = army.data();
    xar::ck3_12002::ContextSourceBindingsV1 bindings{};
    bindings.enabled = true;
    bindings.pre_291e210_1640_enabled = true;

    const NoAccessPage page;
    MEMORY_BASIC_INFORMATION region{};
    Require(VirtualQuery(page.Address(), &region, sizeof(region)) == sizeof(region),
            "PAGE_NOACCESS memory metadata unavailable");
    Require(region.State == static_cast<DWORD>(MEM_COMMIT) &&
                region.Protect == static_cast<DWORD>(PAGE_NOACCESS),
            "fixture operand is not a committed PAGE_NOACCESS allocation");

    bindings.army_internal_fallback_slot = page.Address();
    RequireUnavailable(xar::ck3_12002::ReadCurrentContextSourceInputs12003(
        bindings, character.data(), std::int32_t{29829}));

    bindings.army_internal_fallback_slot = &army_pointer;
    RequireReadable(xar::ck3_12002::ReadCurrentContextSourceInputs12003(
        bindings, character.data(), std::int32_t{29829}));

    CallbackState callback{page.Address(), army.data(), true, 0U, 0U};
    bindings.army_internal_fallback_slot = page.Address();
    bindings.read_memory = &CallbackState::Read;
    bindings.read_context = &callback;
    RequireReadable(xar::ck3_12002::ReadCurrentContextSourceInputs12003(
        bindings, character.data(), std::int32_t{29829}));
    Require(callback.operand_reads == 1U && callback.operand_width == 8U,
            "callback did not take precedence for the inaccessible8B operand");

    callback.supply = false;
    callback.operand_reads = 0U;
    callback.operand_width = 0U;
    RequireUnavailable(xar::ck3_12002::ReadCurrentContextSourceInputs12003(
        bindings, character.data(), std::int32_t{29829}));
    Require(callback.operand_reads == 1U && callback.operand_width == 8U,
            "callback false path changed the requested8B operand");
    std::cout << "Production context source read: PAGE_NOACCESS partial, normal "
                 "read, callback supply and callback false paths passed\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
