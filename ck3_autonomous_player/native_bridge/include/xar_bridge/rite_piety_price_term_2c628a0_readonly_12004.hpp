#pragma once

#include <cstdint>
#include <optional>

#include "xar_bridge/piety_price_numeric_access_12004.hpp"

namespace xar::ck3_12004::piety_price_raw_inputs {

// Numeric projection of actual 2C628A0, reached by 2C62CC0 at 2C62D04
// with mode=0 and detail=null. This never invokes a native function.
enum class RitePietyPriceTermRoute12004 : std::uint8_t {
    unavailable,
    definition_disabled_zero,
    evaluator_flag_zero,
    evaluator_literal,
    dynamic_expression_value_unavailable,
};

struct RitePietyPriceTerm2C628A012004 {
    bool source_ready = false;
    bool actual_original_consumed_values = false;
    std::optional<std::int64_t> native_term_raw_q64;
    RitePietyPriceTermRoute12004 route = RitePietyPriceTermRoute12004::unavailable;
    const char* reason = "numeric_source_not_read";

    // Original caller carriers. Revision is metadata, not an identity or gate.
    std::uintptr_t current_rite = 0;
    std::uintptr_t actor = 0;
    std::uint64_t revision = 0;
    std::uintptr_t provider = 0;
    std::uintptr_t definition_table = 0;
    std::uintptr_t definition = 0;
    std::optional<std::uint8_t> definition_enabled_byte_7c;
    std::optional<std::uint8_t> literal_flag_byte_7b;
    std::uintptr_t expression = 0;
    std::uintptr_t expression_receiver = 0;
    std::uintptr_t expression_vtable = 0;
    std::uintptr_t expression_virtual_30 = 0;

    // Only the dynamic numeric branch consumes the constructed context.
    // These are copied raw DWORDs; no generation mask or semantic conversion.
    std::optional<std::uint32_t> actor_full_id_raw_u32;
    std::optional<std::uint32_t> actor_context_key_raw_u32;
    std::optional<std::uint32_t> rite_full_id_raw_u32;
    std::optional<std::uint32_t> rite_context_key_raw_u32;
    std::optional<std::uint32_t> rite_link_full_id_raw_u32;
    std::optional<std::uint32_t> rite_link_context_key_raw_u32;
    bool dynamic_context_operands_copied = false;
};

inline RitePietyPriceTerm2C628A012004 ReadRitePietyPriceTerm2C628A012004(
    const PietyPriceNumericAccess12004& access,
    std::uintptr_t current_rite,
    std::uintptr_t actor,
    std::uint64_t revision) noexcept {
    static_assert(sizeof(std::uintptr_t) == 8, "CK3 1.20.0.4 has 64-bit pointers");
    RitePietyPriceTerm2C628A012004 result;
    result.current_rite = current_rite;
    result.actor = actor;
    result.revision = revision;

    if (!ReadPietyPriceNumericField12004(access, access.module_base,
            0x5D1DD50, result.provider)) {
        result.reason = "loaded_provider_slot_unreadable";
        return result;
    }
    if (result.provider == 0) {
        // Actual A07970 would enter diagnostic 3F8B640 before loading again.
        // A readonly projection does not invoke it or manufacture a provider.
        result.reason = "loaded_provider_unavailable_native_diagnostic_not_called";
        return result;
    }
    if (!ReadPietyPriceNumericField12004(access, result.provider,
            0xEF0, result.definition_table)) {
        result.reason = "definition_table_unreadable";
        return result;
    }
    if (!ReadPietyPriceNumericField12004(access, result.definition_table,
            0x110, result.definition)) {
        result.reason = "definition_slot_22_unreadable";
        return result;
    }
    std::uint8_t enabled = 0;
    if (!ReadPietyPriceNumericField12004(access, result.definition, 0x7C, enabled)) {
        result.reason = "definition_enabled_byte_unreadable";
        return result;
    }
    result.definition_enabled_byte_7c = enabled;
    if (enabled == 0) {
        // Actual 2C628E7..2C628F1 precedes every actor/Rite/context/name demand.
        result.native_term_raw_q64 = std::int64_t{0};
        result.source_ready = true;
        result.route = RitePietyPriceTermRoute12004::definition_disabled_zero;
        result.reason = "definition_disabled_zero";
        return result;
    }

    if (!ReadPietyPriceNumericField12004(access, result.definition,
            0x70, result.expression)) {
        result.reason = "definition_expression_unreadable";
        return result;
    }
    if (result.expression == 0) {
        // Actual 375439B..37543A5 does not consume R8 context or R9 name.
        // The numeric projection therefore needs no constructor/name/actor gate.
        std::uint8_t flag = 0;
        if (!ReadPietyPriceNumericField12004(access, result.definition, 0x7B, flag)) {
            result.reason = "literal_flag_unreadable";
            return result;
        }
        result.literal_flag_byte_7b = flag;
        std::int64_t term = 0;
        if (flag != 0 && !ReadPietyPriceNumericField12004(access,
                result.definition, 0x68, term)) {
            result.reason = "literal_signed_q64_unreadable";
            return result;
        }
        result.native_term_raw_q64 = term;
        result.source_ready = true;
        result.route = flag == 0 ? RitePietyPriceTermRoute12004::evaluator_flag_zero
                                : RitePietyPriceTermRoute12004::evaluator_literal;
        result.reason = flag == 0 ? "evaluator_flag_zero" : "evaluator_signed_q64_literal";
        return result;
    }

    result.route = RitePietyPriceTermRoute12004::dynamic_expression_value_unavailable;
    std::uint32_t raw = 0;
    if (!ReadPietyPriceNumericField12004(access, actor, 0x18, raw)) {
        result.reason = "dynamic_actor_full_id_unreadable";
        return result;
    }
    result.actor_full_id_raw_u32 = raw;
    if (!ReadPietyPriceNumericField12004(access, access.module_base, 0x5D4BF0C, raw)) {
        result.reason = "dynamic_actor_context_key_unreadable";
        return result;
    }
    result.actor_context_key_raw_u32 = raw;
    if (!ReadPietyPriceNumericField12004(access, current_rite, 0x8, raw)) {
        result.reason = "dynamic_rite_full_id_unreadable";
        return result;
    }
    result.rite_full_id_raw_u32 = raw;
    if (!ReadPietyPriceNumericField12004(access, access.module_base, 0x5D4C2CC, raw)) {
        result.reason = "dynamic_rite_context_key_unreadable";
        return result;
    }
    result.rite_context_key_raw_u32 = raw;
    if (!ReadPietyPriceNumericField12004(access, current_rite, 0x4B8, raw)) {
        result.reason = "dynamic_rite_link_full_id_unreadable";
        return result;
    }
    result.rite_link_full_id_raw_u32 = raw;
    if (!ReadPietyPriceNumericField12004(access, access.module_base, 0x5D4BE98, raw)) {
        result.reason = "dynamic_rite_link_context_key_unreadable";
        return result;
    }
    result.rite_link_context_key_raw_u32 = raw;
    result.dynamic_context_operands_copied = true;

    if (!ReadPietyPriceNumericField12004(access, result.expression,
            0x8, result.expression_vtable)) {
        result.reason = "dynamic_expression_vtable_unreadable";
        return result;
    }
    result.expression_receiver = result.expression + 0x8;
    if (!ReadPietyPriceNumericField12004(access, result.expression_vtable,
            0x30, result.expression_virtual_30)) {
        result.reason = "dynamic_expression_virtual_30_unreadable";
        return result;
    }
    // Copied receiver/vtable addresses do not supply the returned Q64.
    // Never fall back to literal+68 on this branch or actively evaluate it.
    result.reason = "actual_virtual_expression_q64_source_unavailable";
    return result;
}

} // namespace xar::ck3_12004::piety_price_raw_inputs
