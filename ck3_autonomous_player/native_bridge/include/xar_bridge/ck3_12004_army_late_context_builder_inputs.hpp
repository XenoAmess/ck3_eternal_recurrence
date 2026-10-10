#pragma once

#include "xar_bridge/ck3_12004.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string_view>

namespace xar::ck3_12004 {

// Literal source: [2C44580,2C44701), actual .4. This observer reads the
// inputs of that context builder. It never calls the mutating builder or
//373A0F0, and it does not claim that a historical callback reached the builder.
struct ArmyLateContextBuilderBindings12004 {
  bool enabled = false;
  const void *unit_registry_slot = nullptr, *unit_fallback_slot = nullptr;
  const void *province_fallback_slot = nullptr;
  const void *title_registry_slot = nullptr, *title_fallback_slot = nullptr;
  std::array<const void *, 3> named_key_slots{};
  bool (*read_memory)(void *, const void *, void *, std::size_t) noexcept = nullptr;
  void *read_context = nullptr;
};

struct ArmyLateContextOperandSelection12004 {
  std::optional<bool> registry_loaded, used_fallback;
  std::optional<std::uint32_t> requested_full_id_u32, indexed_full_id_u32;
};

struct ArmyLateContextNamedInput12004 {
  std::int32_t kind = 0;
  std::optional<std::uint32_t> name_key_raw_u32;
  // Source MOV EAX zero-extends DWORD input into each QWORD payload.
  std::optional<std::uint64_t> payload_raw_u64;
};

struct ArmyLateContextBuilderInputs12004 {
  bool conditional_builder_demanded = false;
  bool inputs_ready = false;
  bool historical_execution_observed = false;
  const char *unavailable_reason = "not_demanded";
  std::uint16_t root_kind = 27;
  std::optional<std::uint64_t> root_army_full_id_raw_u64;
  // Exactly two independent Unit selections in source order, then one Title.
  std::array<ArmyLateContextOperandSelection12004, 2> units{};
  ArmyLateContextOperandSelection12004 title{};
  std::optional<bool> position_province_used_fallback;
  std::array<ArmyLateContextNamedInput12004, 3> named_inputs{{
      {4, {}, {}}, {5, {}, {}}, {5, {}, {}}}};
};

ArmyLateContextBuilderBindings12004 BindArmyLateContextBuilderInputs12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

// Caller supplies its conditional demand over the actual same-query Army.
// False demand reads nothing and carries no named values. This is not a
// substitute for recording an actual2C44817 invocation or its context return.
ArmyLateContextBuilderInputs12004 ObserveArmyLateContextBuilderInputs12004(
    const ArmyLateContextBuilderBindings12004 &, const void *actual_army,
    bool conditional_builder_demanded) noexcept;

} // namespace xar::ck3_12004
