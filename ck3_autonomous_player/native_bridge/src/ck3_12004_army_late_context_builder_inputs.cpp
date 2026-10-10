#include "xar_bridge/ck3_12004_army_late_context_builder_inputs.hpp"

#include <cstring>

namespace xar::ck3_12004 {
namespace {
template <typename T>
std::optional<T> Read(const ArmyLateContextBuilderBindings12004 &b,
    const void *object, std::size_t offset = 0) noexcept {
  if (!object) return {};
  const auto *address = reinterpret_cast<const void *>(
      reinterpret_cast<std::uintptr_t>(object) + offset);
  T value{};
  if (b.read_memory)
    return b.read_memory(b.read_context, address, &value, sizeof(value))
        ? std::optional<T>{value} : std::nullopt;
#if defined(_WIN32) && defined(_MSC_VER)
  __try {
#endif
    std::memcpy(&value, address, sizeof(value));
    return value;
#if defined(_WIN32) && defined(_MSC_VER)
  } __except (1) { return {}; }
#endif
}

// A missing observer read is unknown. Native null/out-of-range/full-ID
// mismatch selects fallback; it does not require fallback identity metadata.
const void *Select(const ArmyLateContextBuilderBindings12004 &b,
    const void *registry_slot, const void *fallback_slot,
    const void *reference_object, std::size_t reference_offset,
    ArmyLateContextOperandSelection12004 &out) noexcept {
  const auto registry = Read<const void *>(b, registry_slot);
  if (!registry) return nullptr;
  out.registry_loaded = *registry != nullptr;
  if (*registry) {
    out.requested_full_id_u32 = Read<std::uint32_t>(b, reference_object, reference_offset);
    const auto capacity = Read<std::uint32_t>(b, *registry, 0x2C);
    if (!out.requested_full_id_u32 || !capacity) return nullptr;
    const auto index = *out.requested_full_id_u32 & 0xFFFFFFU;
    if (index < *capacity) {
      const auto rows = Read<const void *>(b, *registry, 0x20);
      if (!rows || !*rows) return nullptr;
      const auto object = Read<const void *>(b, *rows, static_cast<std::size_t>(index) * 16 + 8);
      if (!object) return nullptr;
      if (*object) {
        out.indexed_full_id_u32 = Read<std::uint32_t>(b, *object, 0x10);
        if (!out.indexed_full_id_u32) return nullptr;
        if (*out.indexed_full_id_u32 == *out.requested_full_id_u32) {
          out.used_fallback = false;
          return *object;
        }
      }
    }
  }
  out.used_fallback = true;
  const auto fallback = Read<const void *>(b, fallback_slot);
  return fallback ? *fallback : nullptr;
}
} // namespace

ArmyLateContextBuilderBindings12004 BindArmyLateContextBuilderInputs12004(
    std::uintptr_t base, std::string_view sha) noexcept {
  ArmyLateContextBuilderBindings12004 out{};
  if (!base || sha != kExecutableSha256) return out;
  const auto at = [base](std::uintptr_t rva) {
    return reinterpret_cast<const void *>(base + rva);
  };
  out.enabled = true;
  out.unit_registry_slot = at(0x5D1E380);
  out.unit_fallback_slot = at(0x5D1E378);
  out.province_fallback_slot = at(0x5D1E390);
  out.title_registry_slot = at(0x5D1DAF8);
  out.title_fallback_slot = at(0x5D1DAE0);
  out.named_key_slots = {at(0x5D4C27C), at(0x5D4BE20), at(0x5D4BE1C)};
  return out;
}

ArmyLateContextBuilderInputs12004 ObserveArmyLateContextBuilderInputs12004(
    const ArmyLateContextBuilderBindings12004 &b, const void *army,
    bool demanded) noexcept {
  ArmyLateContextBuilderInputs12004 out{};
  out.conditional_builder_demanded = demanded;
  if (!demanded) return out;
  const auto fail = [&](const char *reason) {
    out.unavailable_reason = reason;
    return out;
  };
  if (!b.enabled || !army) return fail("late_context_builder_inputs_unbound");
  const auto army_id = Read<std::uint32_t>(b, army, 0x10);
  if (!army_id) return fail("late_context_root_army_id_unavailable");
  out.root_army_full_id_raw_u64 = *army_id;
  const auto *owner_unit = Select(b, b.unit_registry_slot, b.unit_fallback_slot,
      army, 0x124, out.units[0]);
  if (!owner_unit) return fail("late_context_owner_unit_unavailable");
  const auto owner = Read<std::uint32_t>(b, owner_unit, 0x174);
  out.named_inputs[0].name_key_raw_u32 = Read<std::uint32_t>(b, b.named_key_slots[0]);
  if (!owner || !out.named_inputs[0].name_key_raw_u32)
    return fail("late_context_named_owner_unavailable");
  out.named_inputs[0].payload_raw_u64 = *owner;

  // Source reloads Unit registry and Army124 after its first named save.
  const auto *position_unit = Select(b, b.unit_registry_slot, b.unit_fallback_slot,
      army, 0x124, out.units[1]);
  if (!position_unit) return fail("late_context_position_unit_unavailable");
  const auto position = Read<const void *>(b, position_unit, 0x20);
  if (!position) return fail("late_context_position_province_unavailable");
  const void *province = *position;
  out.position_province_used_fallback = province == nullptr;
  if (!province) {
    const auto fallback = Read<const void *>(b, b.province_fallback_slot);
    if (!fallback || !*fallback) return fail("late_context_position_fallback_unavailable");
    province = *fallback;
  }
  const auto *title = Select(b, b.title_registry_slot, b.title_fallback_slot,
      province, 0x738, out.title);
  if (!title) return fail("late_context_title_unavailable");
  const auto title_id = Read<std::uint32_t>(b, title, 0x10);
  out.named_inputs[1].name_key_raw_u32 = Read<std::uint32_t>(b, b.named_key_slots[1]);
  if (!title_id || !out.named_inputs[1].name_key_raw_u32)
    return fail("late_context_named_title_unavailable");
  out.named_inputs[1].payload_raw_u64 = *title_id;
  const auto title_108 = Read<std::uint32_t>(b, title, 0x108);
  out.named_inputs[2].name_key_raw_u32 = Read<std::uint32_t>(b, b.named_key_slots[2]);
  if (!title_108 || !out.named_inputs[2].name_key_raw_u32)
    return fail("late_context_named_title108_unavailable");
  out.named_inputs[2].payload_raw_u64 = *title_108;
  out.inputs_ready = true;
  out.unavailable_reason = "none";
  return out;
}
} // namespace xar::ck3_12004
