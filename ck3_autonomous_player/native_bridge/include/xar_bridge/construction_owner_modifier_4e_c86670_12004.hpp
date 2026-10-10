#pragma once

#include "xar_bridge/construction_owner_factor_2b9cba0_12004.hpp"
#include "xar_bridge/m4_factor_actor_context_12004.hpp"

#include <array>
#include <cstring>

namespace xar::ck3_12004 {

inline constexpr std::string_view kConstructionModifier4ESha12004 =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
inline constexpr std::uintptr_t kConstructionModifier4EDatabaseSlot12004 =
    0x5D1DD50;

struct ConstructionModifier4EAccess12004 {
  std::uintptr_t module_base = 0;
  std::string_view executable_sha256;
  ConstructionOwnerFactorReadBytes12004 read_bytes = nullptr;
  void *read_context = nullptr;
};

// A supplied source-qualified virtual-output value for this exact stable
// software context. A captured native stack scope is not interchangeable with
// context_input->raw merely because its actor ID matches. Its equivalence
// supplier must construct this token from the separately proved full context.
struct ConstructionModifier4EVirtualOutput12004 {
  const M4FactorActorContext12004 *context_input = nullptr;
  std::uintptr_t context_receiver = 0;
  std::uint64_t frame_key = 0;
  std::uint32_t actor_full_id = 0xFFFFFFFFU;
  std::uintptr_t definition_identity = 0;
  std::uintptr_t expression_receiver = 0;
  std::uintptr_t virtual_slot_30 = 0;
  std::uintptr_t context_alias_00 = 0;
  std::uintptr_t context_alias_08 = 0;
  std::uintptr_t context_alias_10 = 0;
  std::uintptr_t support118_alias_18 = 0;
  std::uintptr_t evaluator_r9 = 0;
  std::uintptr_t name_key_identity = 0;
  std::uint8_t name_descriptor_byte_14 = 0;
  std::uint32_t name_descriptor_dword_18 = 0;
  std::uintptr_t original_output_identity = 0;
  std::uintptr_t temporary_output_identity = 0;
  std::optional<std::int64_t> temporary_q64_after_call;
  bool virtual_call_completed = false;
  bool source_ready = false;
};

enum class ConstructionModifier4EBranch12004 {
  unavailable,
  zero_without_expression,
  literal_without_expression,
  supplied_virtual_output,
};

struct ConstructionModifier4EResult12004 {
  ConstructionOwnerModifier4EInput12004 factor_input;
  std::uintptr_t provider_identity = 0;
  std::uintptr_t slot_table_identity = 0;
  std::uintptr_t definition_identity = 0;
  std::optional<std::uintptr_t> expression_identity;
  std::optional<std::uint8_t> literal_flag_7b;
  ConstructionModifier4EBranch12004 branch =
      ConstructionModifier4EBranch12004::unavailable;
  std::string_view unavailable_reason;
  // Actual C86755 supplies this operand; incoming parent R9 is not inferred.
  std::uintptr_t evaluator_r9 = 0;
  bool observed_native_evaluation = false;
};

namespace construction_modifier_4e_detail {

inline bool ReadBytes(const ConstructionModifier4EAccess12004 &access,
                      std::uintptr_t base, std::size_t offset, void *out,
                      std::size_t size) noexcept {
  const auto maximum = std::numeric_limits<std::uintptr_t>::max();
  if (!access.read_bytes || !base || offset > maximum - base ||
      size > maximum - (base + offset))
    return false;
  return access.read_bytes(access.read_context, base + offset, out, size);
}

template <typename T>
inline bool Read(const ConstructionModifier4EAccess12004 &access,
                 std::uintptr_t base, std::size_t offset, T &out) noexcept {
  return ReadBytes(access, base, offset, &out, sizeof(out));
}

template <typename T>
inline bool ContextField(const M4FactorActorContext12004 &context,
                         std::size_t offset, T &out) noexcept {
  if (offset > context.raw.size() || sizeof(out) > context.raw.size() - offset)
    return false;
  for (std::size_t i = 0; i < sizeof(out); ++i)
    if (!context.defined_bytes[offset + i]) return false;
  std::memcpy(&out, context.raw.data() + offset, sizeof(out));
  return true;
}

inline bool ActorPrefixQualified(
    const M4FactorActorContext12004 &context) noexcept {
  std::uint32_t tag = 0, sentinel = 0;
  std::uint64_t actor = 0;
  return context.actor_identity_qualified && context.context_receiver &&
      context.native_scope_tag == kM4FactorActorTag12004 &&
      ContextField(context, 0, tag) && tag == kM4FactorActorTag12004 &&
      ContextField(context, 8, actor) && actor == context.actor_full_id &&
      ContextField(context, 0x10, sentinel) && sentinel == 0xFFFFFFFFU;
}

// Retained 3F79DD0 stores two big-endian length bytes followed by exact chars.
// Compare supplied interned-key contents to this selected definition's actual
// string. This is a bounded read; it never interns or allocates a property.
inline bool NameKeyMatches(const ConstructionModifier4EAccess12004 &access,
                           std::uintptr_t definition,
                           std::uintptr_t name_key) noexcept {
  std::uint32_t length = 0;
  if (!Read(access, definition, 0x28, length) || length >= 0x80000000U)
    return false;
  if (length == 0 || length >= 0xFFFFU) return name_key == 0;
  if (!name_key) return false;
  std::array<std::uint8_t, 2> prefix{};
  if (!ReadBytes(access, name_key, 0, prefix.data(), prefix.size()) ||
      ((static_cast<std::uint32_t>(prefix[0]) << 8) | prefix[1]) != length)
    return false;
  std::uint64_t capacity = 0;
  if (!Read(access, definition, 0x30, capacity)) return false;
  std::uintptr_t name_data = definition;
  std::size_t name_offset = 0x18;
  if (capacity >= 0x10) {
    if (!Read(access, definition, 0x18, name_data) || !name_data) return false;
    name_offset = 0;
  }
  std::array<std::byte, 128> actual{}, interned{};
  for (std::size_t offset = 0; offset < length;) {
    const auto remaining = static_cast<std::size_t>(length) - offset;
    const auto count = remaining < actual.size() ? remaining : actual.size();
    if (!ReadBytes(access, name_data, name_offset + offset, actual.data(), count) ||
        !ReadBytes(access, name_key, 2 + offset, interned.data(), count) ||
        std::memcmp(actual.data(), interned.data(), count) != 0)
      return false;
    offset += count;
  }
  return true;
}
} // namespace construction_modifier_4e_detail

// Pure current-input equivalent of the C86670(index4E) numerical contract.
// It neither executes native setup/evaluation nor clamps the signed output.
// Zero/constant paths demand only the qualified actor prefix. The expression
// path additionally demands a complete source-equivalent context and supplied
// actual virtual-output operands, never a guessed initialized temporary zero.
inline ConstructionModifier4EResult12004 ReadConstructionOwnerModifier4E12004(
    const ConstructionModifier4EAccess12004 &access,
    const M4FactorActorContext12004 &context,
    const ConstructionModifier4EVirtualOutput12004 *virtual_output =
        nullptr) noexcept {
  using namespace construction_modifier_4e_detail;
  static_assert(sizeof(std::uintptr_t) == 8 && sizeof(std::int64_t) == 8);
  ConstructionModifier4EResult12004 out;
  out.factor_input.context_receiver = context.context_receiver;
  out.factor_input.frame_key = context.frame_key;
  const auto fail = [&](std::string_view reason) {
    out.unavailable_reason = reason;
    return out;
  };
  if (!access.module_base ||
      access.executable_sha256 != kConstructionModifier4ESha12004 ||
      !access.read_bytes)
    return fail("actual4_modifier_binding_unavailable");
  if (!ActorPrefixQualified(context))
    return fail("actual_factor_actor_prefix_unavailable");
  if (!Read(access, access.module_base, kConstructionModifier4EDatabaseSlot12004,
            out.provider_identity) || !out.provider_identity ||
      !Read(access, out.provider_identity, 0xEF0, out.slot_table_identity) ||
      !out.slot_table_identity ||
      !Read(access, out.slot_table_identity,
            static_cast<std::size_t>(kConstructionOwnerFactorModifierIndex12004) * 8,
            out.definition_identity) || !out.definition_identity)
    return fail("actual_modifier_definition_4e_unavailable");
  std::uintptr_t expression = 0;
  if (!Read(access, out.definition_identity, 0x70, expression))
    return fail("modifier_expression_70_unavailable");
  out.expression_identity = expression;
  if (!expression) {
    std::uint8_t flag = 0;
    if (!Read(access, out.definition_identity, 0x7B, flag))
      return fail("modifier_literal_flag_7b_unavailable");
    out.literal_flag_7b = flag;
    std::int64_t scalar = 0;
    if (flag && !Read(access, out.definition_identity, 0x68, scalar))
      return fail("modifier_literal_q64_68_unavailable");
    out.factor_input.returned_q64 = scalar;
    out.factor_input.source_ready = true;
    out.branch = flag ? ConstructionModifier4EBranch12004::literal_without_expression
                      : ConstructionModifier4EBranch12004::zero_without_expression;
    return out;
  }
  if (!context.complete_source)
    return fail("dynamic_modifier_complete_context_unavailable");
  if (!virtual_output || !virtual_output->source_ready ||
      !virtual_output->virtual_call_completed ||
      !virtual_output->temporary_q64_after_call.has_value())
    return fail("dynamic_modifier_virtual_q64_unavailable");
  const auto &w = *virtual_output;
  const auto maximum = std::numeric_limits<std::uintptr_t>::max();
  if (expression > maximum - 8)
    return fail("dynamic_modifier_expression_receiver_unavailable");
  std::uintptr_t vtable = 0, slot = 0;
  if (!Read(access, expression, 8, vtable) || !vtable ||
      !Read(access, vtable, 0x30, slot) || !slot)
    return fail("dynamic_modifier_virtual_slot_30_unavailable");
  const auto aliases = reinterpret_cast<std::uintptr_t>(context.raw.data());
  if (w.context_input != &context ||
      w.context_receiver != context.context_receiver ||
      w.frame_key != context.frame_key || w.actor_full_id != context.actor_full_id ||
      w.definition_identity != out.definition_identity ||
      w.expression_receiver != expression + 8 || w.virtual_slot_30 != slot ||
      w.context_alias_00 != aliases || w.context_alias_08 != 0 ||
      w.context_alias_10 != aliases || !w.support118_alias_18 ||
      w.evaluator_r9 != 0 || w.name_descriptor_byte_14 != 1 ||
      w.name_descriptor_dword_18 != 0xFFFFFFFFU ||
      !w.original_output_identity || !w.temporary_output_identity ||
      w.original_output_identity == w.temporary_output_identity ||
      !NameKeyMatches(access, out.definition_identity, w.name_key_identity))
    return fail("dynamic_modifier_supplied_operand_mismatch");
  out.factor_input.returned_q64 = w.temporary_q64_after_call;
  out.factor_input.source_ready = true;
  out.branch = ConstructionModifier4EBranch12004::supplied_virtual_output;
  return out;
}
} // namespace xar::ck3_12004
