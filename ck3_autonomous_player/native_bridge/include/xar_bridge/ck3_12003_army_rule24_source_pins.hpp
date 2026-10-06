#pragma once
#include "xar_bridge/ck3_12003_daily_assault_roster_admission.hpp"
namespace xar::game {
#include "xar_bridge/army_current_rule24_source_pins_v1.inc.hpp"
}
namespace xar::ck3_12003 {
namespace army_rule24_source_pins_detail {
inline void Reason(game::ArmyCurrentRule24SourcePinsV1 &out, const char *reason) {
  if (out.unavailable_reason.empty()) out.unavailable_reason = reason;
}
template <class T, class Bindings>
inline std::optional<T> Read(const Bindings &b,
    game::ArmyCurrentRule24SourcePinsV1 &out,
    const void *object, std::size_t offset = 0) {
  out.pin_requested_bytes_u32 += static_cast<std::uint32_t>(sizeof(T));
  const auto value = daily_assault_roster_detail::Read<T>(b.common, object, offset);
  if (value) out.pin_captured_bytes_u32 += static_cast<std::uint32_t>(sizeof(T));
  return value;
}
template <class Bindings>
inline std::optional<std::uint32_t> Rva(const Bindings &b, const void *target) {
  const auto address = reinterpret_cast<std::uintptr_t>(target);
  const auto base = b.rule_source_module_base;
  if (base && address >= base && address - base < b.rule_source_image_size)
    return static_cast<std::uint32_t>(address - base);
  return std::nullopt;
}
template <class Bindings>
inline void Pin(const Bindings &b, game::ArmyCurrentRule24SourcePinsV1 &out,
    const void *vtable, std::size_t offset, const char *unavailable_reason,
    std::optional<std::string> &identity,
    std::optional<std::uint32_t> &rva, bool &read_ready) {
  const auto target = Read<const void *>(b, out, vtable, offset);
  read_ready = target.has_value();
  if (!target) {
    Reason(out, unavailable_reason);
    return;
  }
  // Null is a successfully copied pointer value. Neither pin is invoked.
  identity = daily_assault_roster_detail::Identity(*target);
  rva = Rva(b, *target);
}
}
template <class Bindings>
inline game::ArmyCurrentRule24SourcePinsV1 ReadCurrentRule24SourcePins12003(
    const Bindings &b, const void *actual_inline_receiver) noexcept {
  using namespace army_rule24_source_pins_detail;
  game::ArmyCurrentRule24SourcePinsV1 out{};
  try {
    out.unavailable_reason.clear();
    out.rule_receiver_identity =
        daily_assault_roster_detail::Identity(actual_inline_receiver);
    // The current collector already selected provider/array/inline receiver.
    // This capsule adds only mode1 + vptr8 + three function-pointer slots24.
    out.condition_mode_raw_u8 =
        Read<std::uint8_t>(b, out, b.rule_source_mode_slot);
    out.mode_read_ready = out.condition_mode_raw_u8.has_value();
    if (!out.mode_read_ready) Reason(out, "rule24_mode_unavailable");
    const auto vtable = Read<const void *>(b, out, actual_inline_receiver);
    out.vtable_read_ready = vtable.has_value();
    if (!vtable) {
      Reason(out, "rule24_vtable_unavailable");
    } else {
      out.rule_vtable_identity = daily_assault_roster_detail::Identity(*vtable);
      if (!*vtable) {
        Reason(out, "rule24_vtable_null");
      } else {
        Pin(b, out, *vtable, 0x58, "rule24_expected_scope_pin_unavailable",
            out.expected_scope_function_identity, out.expected_scope_function_rva,
            out.expected_scope_pin_read_ready);
        Pin(b, out, *vtable, 0x60, "rule24_scope_mask_pin_unavailable",
            out.scope_mask_function_identity, out.scope_mask_function_rva,
            out.scope_mask_pin_read_ready);
        Pin(b, out, *vtable, 0xC8, "rule24_evaluator_pin_unavailable",
            out.rule_evaluator_function_identity, out.rule_evaluator_function_rva,
            out.rule_evaluator_pin_read_ready);
      }
    }
    out.pins_captured_ready = out.mode_read_ready && out.vtable_read_ready &&
        out.expected_scope_pin_read_ready && out.scope_mask_pin_read_ready &&
        out.rule_evaluator_pin_read_ready;
    out.status = out.pins_captured_ready ? "available" : "partial";
  } catch (...) {
    out.status = "partial"; out.pins_captured_ready = false;
    out.unavailable_reason = "rule24_pin_collection_unavailable";
  }
  return out;
}
}
