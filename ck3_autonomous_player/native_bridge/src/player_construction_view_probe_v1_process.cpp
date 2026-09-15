#include "player_construction_view_probe_v1_process.hpp"

#include "xar_bridge/title_map_navigation_v1_camera.hpp"

#include <windows.h>

#include <cstring>
#include <limits>

namespace xar::ck3::shared {
namespace {

bool Add(std::uintptr_t base, std::uintptr_t offset,
         std::uintptr_t& address) noexcept {
  if (base == 0U || offset >
                        std::numeric_limits<std::uintptr_t>::max() - base) {
    return false;
  }
  address = base + offset;
  return true;
}

bool ReadCurrentProcess(void*, std::uintptr_t address, void* destination,
                        std::size_t bytes) {
  if (address == 0U || destination == nullptr || bytes == 0U) return false;
#if defined(_MSC_VER)
  __try {
    std::memcpy(destination, reinterpret_cast<const void*>(address), bytes);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  std::memcpy(destination, reinterpret_cast<const void*>(address), bytes);
  return true;
#endif
}

bool ReadPointer(std::uintptr_t base, std::uintptr_t offset,
                 std::uintptr_t& pointer) noexcept {
  std::uintptr_t address = 0U;
  return Add(base, offset, address) &&
         ReadCurrentProcess(nullptr, address, &pointer, sizeof(pointer));
}

bool ResolveOwner(void* context, std::uintptr_t module_base,
                  PlayerConstructionViewResolvedOwnerV1& output) noexcept {
  output = {};
  const auto* access =
      static_cast<const PlayerConstructionViewProcessAccessV1*>(context);
  if (access == nullptr || module_base == 0U ||
      access->module_base != module_base) {
    return false;
  }
  std::uintptr_t root = 0U;
  std::uintptr_t idler_base = 0U;
  std::uintptr_t slot = 0U;
  if (!Add(module_base,
           xar::ck3_11906::kTitleMapIngameIdlerRootSlotRva, slot) ||
      !ReadCurrentProcess(nullptr, slot, &root, sizeof(root)) ||
      !ReadPointer(root, 0x10U, idler_base) || root == 0U ||
      idler_base == 0U) {
    return false;
  }

  auto* native_cast = reinterpret_cast<
      xar::ck3_11906::NativeRuntimeDynamicCastV1>(
      module_base + xar::ck3_11906::kTitleMapRuntimeDynamicCastRva);
  const auto* source_type = reinterpret_cast<const void*>(
      module_base + xar::ck3_11906::kTitleMapIdlerBaseTypeDescriptorRva);
  const auto* target_type = reinterpret_cast<const void*>(
      module_base + xar::ck3_11906::kTitleMapIngameIdlerTypeDescriptorRva);
  void* cast_result = nullptr;
#if defined(_MSC_VER)
  __try {
    cast_result = native_cast(reinterpret_cast<void*>(idler_base), 0,
                               source_type, target_type, 0);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  cast_result = native_cast(reinterpret_cast<void*>(idler_base), 0,
                             source_type, target_type, 0);
#endif
  const auto idler_gfx = reinterpret_cast<std::uintptr_t>(cast_result);
  std::uintptr_t handler = 0U;
  if (idler_gfx == 0U || !ReadPointer(idler_gfx, 0x88U, handler) ||
      handler == 0U) {
    return false;
  }
  output.root = root;
  output.idler_base = idler_base;
  output.idler_gfx = idler_gfx;
  output.handler = handler;
  output.exact_idler_rtti_cast = true;
  return true;
}

}  // namespace

PlayerConstructionViewProbeSourceV1
BindCurrentProcessPlayerConstructionViewProbeSourceV1(
    PlayerConstructionViewProcessAccessV1& access) noexcept {
  PlayerConstructionViewProbeSourceV1 source{};
  if (access.module_base != 0U) {
    source.resolve_owner = &ResolveOwner;
    source.owner_context = &access;
    source.read_memory = &ReadCurrentProcess;
  }
  return source;
}

}  // namespace xar::ck3::shared
