#include "xar_bridge/death_succession_modal_continue_v1.hpp"

#include <windows.h>

#include <charconv>
#include <cstddef>
#include <cstdint>
#include <limits>

namespace xar::ck3_11906 {
namespace {

using Status = xar::game::DeathSuccessionModalContinueStatusV1;

constexpr std::uintptr_t kIdlerRootSlotRva = 0x570F7B8;
constexpr std::ptrdiff_t kIdlerBaseOffset = 0x10;
constexpr std::uintptr_t kRuntimeDynamicCastRva = 0x3E631F4;
constexpr std::uintptr_t kIdlerBaseTypeDescriptorRva = 0x501EF28;
constexpr std::uintptr_t kIngameIdlerTypeDescriptorRva = 0x501EF50;
constexpr std::ptrdiff_t kIngameHandlerOffset = 0x88;
constexpr std::uintptr_t kIngameHandlerPrimaryVtableRva = 0x40AF630;
constexpr std::ptrdiff_t kSuccessionControllerOffset = 0x260;
constexpr std::uintptr_t kSuccessionControllerPrimaryVtableRva = 0x4111E80;
constexpr std::ptrdiff_t kControllerCloseVslot = 0x20;
constexpr std::ptrdiff_t kControllerOpenVslot = 0x38;
constexpr std::uintptr_t kControllerCloseTargetRva = 0x1006FB0;
constexpr std::uintptr_t kControllerOpenTargetRva = 0xFD4B00;

using RuntimeDynamicCastV1 = void *(__cdecl *)(void *, long, void *, void *,
                                               int);
using ControllerOpenV1 = bool(__fastcall *)(void *);
using ControllerCloseV1 = void(__fastcall *)(void *);

struct NativeContextV1 {
  std::uintptr_t module_base = 0;
};

void Fail(const DeathSuccessionModalContinueRequestV1 &request,
          xar::game::DeathSuccessionModalContinueReceiptV1 &receipt,
          std::string_view reason) {
  receipt.status = Status::unavailable;
  receipt.snapshot_revision = request.expected_snapshot_revision;
  receipt.date_raw = request.expected_date_raw;
  receipt.played_character_id = request.expected_played_character_id;
  receipt.unavailable_reason.assign(reason);
}

bool ReadCurrent(const void *address, void *output, std::size_t size) noexcept {
  SIZE_T read = 0;
  return address != nullptr && output != nullptr && size > 0 &&
         ReadProcessMemory(GetCurrentProcess(), address, output, size, &read) !=
             FALSE &&
         read == size;
}

bool ReadPointer(std::uintptr_t address, std::uintptr_t &output) noexcept {
  output = 0;
  return address != 0 &&
         ReadCurrent(reinterpret_cast<const void *>(address), &output,
                     sizeof(output));
}

bool ResolveNative(void *opaque, void *&output) noexcept {
  output = nullptr;
  const auto *context = static_cast<const NativeContextV1 *>(opaque);
  if (context == nullptr || context->module_base == 0) return false;
  const auto module = context->module_base;
  std::uintptr_t idler_root = 0;
  std::uintptr_t idler_base = 0;
  if (!ReadPointer(module + kIdlerRootSlotRva, idler_root) ||
      idler_root == 0 ||
      !ReadPointer(idler_root + kIdlerBaseOffset, idler_base) ||
      idler_base == 0) {
    return false;
  }
  const auto runtime_dynamic_cast = reinterpret_cast<RuntimeDynamicCastV1>(
      module + kRuntimeDynamicCastRva);
  void *const ingame = runtime_dynamic_cast(
      reinterpret_cast<void *>(idler_base), 0,
      reinterpret_cast<void *>(module + kIdlerBaseTypeDescriptorRva),
      reinterpret_cast<void *>(module + kIngameIdlerTypeDescriptorRva), 0);
  if (ingame == nullptr) return false;
  std::uintptr_t handler = 0;
  std::uintptr_t handler_vtable = 0;
  std::uintptr_t controller = 0;
  std::uintptr_t controller_vtable = 0;
  if (!ReadPointer(reinterpret_cast<std::uintptr_t>(ingame) +
                       kIngameHandlerOffset,
                   handler) ||
      handler == 0 || !ReadPointer(handler, handler_vtable) ||
      handler_vtable != module + kIngameHandlerPrimaryVtableRva ||
      !ReadPointer(handler + kSuccessionControllerOffset, controller) ||
      controller == 0 || !ReadPointer(controller, controller_vtable) ||
      controller_vtable !=
          module + kSuccessionControllerPrimaryVtableRva) {
    return false;
  }
  output = reinterpret_cast<void *>(controller);
  return true;
}

bool ReadControllerOpenNative(void *opaque, void *controller,
                              bool &open) noexcept {
  open = false;
  const auto *context = static_cast<const NativeContextV1 *>(opaque);
  if (context == nullptr || context->module_base == 0 || controller == nullptr)
    return false;
  std::uintptr_t vtable = 0;
  std::uintptr_t target = 0;
  if (!ReadPointer(reinterpret_cast<std::uintptr_t>(controller), vtable) ||
      vtable !=
          context->module_base + kSuccessionControllerPrimaryVtableRva ||
      !ReadPointer(vtable + kControllerOpenVslot, target) ||
      target != context->module_base + kControllerOpenTargetRva) {
    return false;
  }
  open = reinterpret_cast<ControllerOpenV1>(target)(controller);
  return true;
}

bool CloseControllerNative(void *opaque, void *controller) noexcept {
  const auto *context = static_cast<const NativeContextV1 *>(opaque);
  if (context == nullptr || context->module_base == 0 || controller == nullptr)
    return false;
  std::uintptr_t vtable = 0;
  std::uintptr_t target = 0;
  if (!ReadPointer(reinterpret_cast<std::uintptr_t>(controller), vtable) ||
      vtable !=
          context->module_base + kSuccessionControllerPrimaryVtableRva ||
      !ReadPointer(vtable + kControllerCloseVslot, target) ||
      target != context->module_base + kControllerCloseTargetRva) {
    return false;
  }
  reinterpret_cast<ControllerCloseV1>(target)(controller);
  return true;
}

bool ParseUnsigned(std::string_view json, std::string_view key,
                   std::uint64_t &output) noexcept {
  output = 0;
  const auto at = json.find(key);
  if (at == std::string_view::npos ||
      json.find(key, at + key.size()) != std::string_view::npos) {
    return false;
  }
  auto begin = at + key.size();
  while (begin < json.size() &&
         (json[begin] == ' ' || json[begin] == '\t' ||
          json[begin] == '\r' || json[begin] == '\n'))
    ++begin;
  auto end = begin;
  while (end < json.size() && json[end] >= '0' && json[end] <= '9') ++end;
  if (end == begin || (json[begin] == '0' && end - begin != 1)) return false;
  const auto parsed =
      std::from_chars(json.data() + begin, json.data() + end, output);
  if (parsed.ec != std::errc{} || parsed.ptr != json.data() + end) return false;
  while (end < json.size() &&
         (json[end] == ' ' || json[end] == '\t' || json[end] == '\r' ||
          json[end] == '\n'))
    ++end;
  return end < json.size() && (json[end] == ',' || json[end] == '}');
}

bool ParseSigned(std::string_view json, std::string_view key,
                 std::int64_t &output) noexcept {
  output = 0;
  const auto at = json.find(key);
  if (at == std::string_view::npos ||
      json.find(key, at + key.size()) != std::string_view::npos) {
    return false;
  }
  auto begin = at + key.size();
  while (begin < json.size() &&
         (json[begin] == ' ' || json[begin] == '\t' ||
          json[begin] == '\r' || json[begin] == '\n'))
    ++begin;
  auto end = begin;
  if (end < json.size() && json[end] == '-') ++end;
  const auto digits = end;
  while (end < json.size() && json[end] >= '0' && json[end] <= '9') ++end;
  if (end == digits || (json[digits] == '0' && end - digits != 1)) return false;
  const auto parsed =
      std::from_chars(json.data() + begin, json.data() + end, output);
  if (parsed.ec != std::errc{} || parsed.ptr != json.data() + end) return false;
  while (end < json.size() &&
         (json[end] == ' ' || json[end] == '\t' || json[end] == '\r' ||
          json[end] == '\n'))
    ++end;
  return end < json.size() && (json[end] == ',' || json[end] == '}');
}

} // namespace

Status ExecuteDeathSuccessionModalContinueV1(
    const DeathSuccessionModalContinueRequestV1 &request,
    const xar::game::CurrentTimelineBlockerContextV1 &timeline,
    const DeathSuccessionModalContinueSourceV1 &source,
    xar::game::DeathSuccessionModalContinueReceiptV1 &receipt) noexcept {
  receipt = {};
  try {
    if (request.expected_snapshot_revision == 0 ||
        request.expected_played_character_id <= 0 ||
        timeline.snapshot_revision != request.expected_snapshot_revision ||
        timeline.date_raw != request.expected_date_raw) {
      Fail(request, receipt, "frame_binding_changed");
      return Status::unavailable;
    }
    if (timeline.status !=
            xar::game::CurrentTimelineBlockerStatusV1::available ||
        timeline.identity != xar::game::CurrentTimelineBlockerIdentityV1::
                                 death_succession_modal) {
      Fail(request, receipt, "death_succession_modal_not_fresh");
      return Status::unavailable;
    }
    receipt.identity_verified = true;
    if (!timeline.can_continue.available || !timeline.can_continue.value) {
      Fail(request, receipt, "death_succession_modal_cannot_continue");
      return Status::unavailable;
    }
    receipt.can_continue_verified = true;
    if (!timeline.blocks_simulation.available ||
        !timeline.blocks_simulation.value) {
      Fail(request, receipt, "not_paused_by_succession");
      return Status::unavailable;
    }
    receipt.paused_by_succession_verified = true;
    if (!timeline.has_open_succession.available ||
        !timeline.has_open_succession.value) {
      Fail(request, receipt, "played_character_has_no_open_succession");
      return Status::unavailable;
    }
    receipt.has_open_succession_verified = true;
    if (source.resolve_controller == nullptr ||
        source.read_controller_open == nullptr ||
        source.close_controller == nullptr) {
      Fail(request, receipt, "typed_controller_source_unavailable");
      return Status::unavailable;
    }
    void *controller = nullptr;
    if (!source.resolve_controller(source.context, controller) ||
        controller == nullptr) {
      Fail(request, receipt, "succession_controller_resolution_failed");
      return Status::unavailable;
    }
    receipt.controller_vtable_verified = true;
    bool controller_open = false;
    if (!source.read_controller_open(source.context, controller,
                                     controller_open) ||
        !controller_open) {
      Fail(request, receipt, "succession_controller_not_open");
      return Status::unavailable;
    }
    receipt.controller_open_verified = true;
    if (!source.close_controller(source.context, controller)) {
      Fail(request, receipt, "succession_controller_close_dispatch_failed");
      return Status::unavailable;
    }
    receipt.close_invocations = 1;
    receipt.status = Status::submitted;
    receipt.snapshot_revision = request.expected_snapshot_revision;
    receipt.date_raw = request.expected_date_raw;
    receipt.played_character_id = request.expected_played_character_id;
    receipt.unavailable_reason.clear();
    return Status::submitted;
  } catch (...) {
    Fail(request, receipt, "internal_error");
    return Status::unavailable;
  }
}

Status ExecuteDeathSuccessionModalContinueNativeV1(
    const ZhongguoScoreboardNativeEnvironmentV1 &environment,
    const DeathSuccessionModalContinueRequestV1 &request,
    const xar::game::CurrentTimelineBlockerContextV1 &timeline,
    xar::game::DeathSuccessionModalContinueReceiptV1 &receipt) noexcept {
  if (!environment.exact_build_admitted || environment.module_base == 0 ||
      environment.offline_fixture_function_overrides) {
    receipt = {};
    Fail(request, receipt, "exact_build_not_admitted");
    return Status::unavailable;
  }
  NativeContextV1 context{environment.module_base};
  DeathSuccessionModalContinueSourceV1 source{
      &context, &ResolveNative, &ReadControllerOpenNative,
      &CloseControllerNative};
  return ExecuteDeathSuccessionModalContinueV1(request, timeline, source,
                                               receipt);
}

bool ParseDeathSuccessionModalContinueV1Step(std::string_view step) noexcept {
  return step == kDeathSuccessionModalContinueV1Step;
}

bool ParseDeathSuccessionModalContinueRequestV1(
    std::string_view json,
    DeathSuccessionModalContinueRequestV1 &output) noexcept {
  output = {};
  std::uint64_t revision = 0;
  std::int64_t date = 0;
  std::int64_t character = 0;
  if (!ParseUnsigned(json, "\"expected_revision\":", revision) ||
      revision == 0 ||
      !ParseSigned(json, "\"expected_date_raw\":", date) ||
      date < std::numeric_limits<std::int32_t>::min() ||
      date > std::numeric_limits<std::int32_t>::max() ||
      !ParseSigned(json, "\"expected_played_character_id\":", character) ||
      character <= 0 || character > std::numeric_limits<std::int32_t>::max()) {
    return false;
  }
  output.expected_snapshot_revision = revision;
  output.expected_date_raw = static_cast<std::int32_t>(date);
  output.expected_played_character_id = static_cast<std::int32_t>(character);
  return true;
}

} // namespace xar::ck3_11906
