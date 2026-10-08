#pragma once

#include "xar_bridge/ck3_12002_declarations.hpp"
#include <array>
#include <optional>
#include <string>

namespace xar::ck3_12002 {
namespace religion::holy_war_defender_join {
struct Bindings;
struct Context;
}
inline constexpr std::string_view kOrdinaryHolyWarExactSha12003 =
    "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";
inline constexpr std::string_view kOrdinaryHolyWarDeclarationContextSchemaV1 =
    "player_ordinary_holy_war_declaration_context_v1";
inline constexpr std::array<std::string_view, 10> kOrdinaryHolyWarResourceKeysV1{
    "gold", "prestige", "piety", "renown", "influence", "herd", "treasury",
    "treasury_or_gold", "merit", "barter_goods"};
inline constexpr std::int64_t kOrdinaryHolyWarRawScaleV1 = 100000;
inline constexpr std::size_t kOrdinaryHolyWarScopeSizeV1 = 0x168;
inline constexpr std::size_t kOrdinaryHolyWarCompiledCostOffsetV1 = 0xA80;
inline constexpr std::uintptr_t kOrdinaryHolyWarScopeCtorRvaV1 = 0x889F60;
inline constexpr std::uintptr_t kOrdinaryHolyWarScopePopulateRvaV1 = 0x2A81500;
inline constexpr std::uintptr_t kOrdinaryHolyWarScopeDtorRvaV1 = 0x87E0E0;
inline constexpr std::uintptr_t kOrdinaryHolyWarCostEvaluatorRvaV1 = 0x310CEE0;
inline constexpr std::uintptr_t kOrdinaryHolyWarFallbackSlotRvaV1 = 0x5C67570;
using OrdinaryHolyWarScopeCtorV1 = void (*)(void *);
using OrdinaryHolyWarScopePopulateV1 = void (*)(void *, void *, void *, void *, const void *, std::int32_t);
using OrdinaryHolyWarScopeDtorV1 = void (*)(void *);
using OrdinaryHolyWarCostEvaluatorV1 = void (*)(const void *, const void *, std::int64_t *);
struct OrdinaryHolyWarCbCostBindingsV1 {
  bool enabled = false;
  OrdinaryHolyWarScopeCtorV1 construct_scope = nullptr;
  OrdinaryHolyWarScopePopulateV1 populate_scope = nullptr;
  OrdinaryHolyWarScopeDtorV1 destroy_scope = nullptr;
  OrdinaryHolyWarCostEvaluatorV1 evaluate_cost = nullptr;
  void **native_character_fallback_slot = nullptr;
};
struct OrdinaryHolyWarCbCostV1 {
  bool available = false;
  std::string unavailable_reason = "cb_cost_bindings_unavailable";
  std::optional<std::array<std::int64_t, 10>> resource_costs_raw;
};
struct OrdinaryHolyWarDeclarationContextV1 {
  bool available = false;
  std::string unavailable_reason = "declaration_context_unavailable";
  std::uint64_t capture_epoch = 0, native_revision = 0, public_revision = 0;
  std::int32_t date_raw = 0, played_character_id = -1;
  std::string declaration_id;
  game::DeclarableWarSnapshot selected;
  std::optional<std::int32_t> context_actor_character_id;
  std::optional<std::int32_t> context_recipient_character_id;
  std::optional<std::int32_t> context_additional_role_character_id;
  std::optional<std::int32_t> context_claimant_character_id;
  bool recipient_uses_native_fallback = false;
  bool additional_role_uses_native_fallback = false;
  bool claimant_uses_native_fallback = false;
  std::optional<bool> final_can_send;
  OrdinaryHolyWarCbCostV1 cb_cost;
};
bool IsOrdinaryHolyWarKeyV1(std::string_view) noexcept;
OrdinaryHolyWarCbCostBindingsV1 BindOrdinaryHolyWarCbCostImageV1(std::uintptr_t, std::string_view) noexcept;
// Uses the finalized context's dedicated CB scope and actual native title array.
bool ReadOrdinaryHolyWarCbCostV1(const OrdinaryHolyWarCbCostBindingsV1 &, const void *selected_cb,
    void *additional, void *recipient, void *claimant, const void *native_titles, OrdinaryHolyWarCbCostV1 &) noexcept;
// Re-evaluates the full selected row and constructs one observation context, without a command.
bool ReadSelectedOrdinaryHolyWarDeclarationContextV1(const DeclarationsBindings &,
    const OrdinaryHolyWarCbCostBindingsV1 &, const game::DeclarableWarSnapshot &, OrdinaryHolyWarDeclarationContextV1 &) noexcept;
bool ReadSelectedOrdinaryHolyWarDeclarationContextV1(const DeclarationsBindings &,
    const OrdinaryHolyWarCbCostBindingsV1 &, const game::DeclarableWarSnapshot &, OrdinaryHolyWarDeclarationContextV1 &,
    const religion::holy_war_defender_join::Bindings &, religion::holy_war_defender_join::Context &) noexcept;
std::string SerializeOrdinaryHolyWarSelectedDeclarationV1(const game::DeclarableWarSnapshot &);
std::string SerializeOrdinaryHolyWarDeclarationContextV1(const OrdinaryHolyWarDeclarationContextV1 &);
} // namespace xar::ck3_12002
