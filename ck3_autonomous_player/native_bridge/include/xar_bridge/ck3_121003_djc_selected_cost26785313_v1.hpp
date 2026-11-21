#pragma once
#include "xar_bridge/ck3_121003_djc_declaration_ui26785313_v1.hpp"
#include <array>
#include <optional>
namespace xar::ck3_121003::build26785313 {
inline constexpr char kDjcSelectedCostStep267V1[]="query-current-djc-selected-cost-v1";
inline constexpr char kDjcSelectedCostCapability267V1[]="game.query.current-djc-selected-cost.v1";
inline constexpr char kDjcSelectedCostRequestSchema267V1[]="ck3.djc_selected_cost.current267_request.v1";
inline constexpr char kDjcSelectedCostResultSchema267V1[]="ck3.djc_selected_cost.current267_result.v1";
inline constexpr char kDjcSelectedCostSourceSchema267V1[]="ck3.djc_selected_cost.current267_source.v1";
inline constexpr char kDjcSelectedCostBackend267V1[]="ck3-1.21.0.3-native-application-main-djc-selected-cost";
inline constexpr std::array<std::string_view,5>kDjcSelectedCostCurrencies267V1{"piety","prestige","renown","influence","gold"};
// A readonly request bound to an existing genuine private v23 UI-query lease.
// The underlying action stays query_ui for internal Core/target/CB storage only;
// its shape is checked by this family's dedicated parser, not the v23 parser.
using DjcSelectedCostRequest267V1=DjcUiRequest267V1;
struct DjcSelectedCostValues267V1 {
 std::array<std::optional<std::int64_t>,5>raw{};
 std::uint32_t native_getter_calls=0;
 bool available=false,cleanup_known=true;
};
struct DjcSelectedCostResult267V1 {
 DjcUiResult267V1 witness{};
 DjcSelectedCostValues267V1 values{};
};
bool DjcSelectedCostRequestShape267V1(const DjcSelectedCostRequest267V1&)noexcept;
bool ParseDjcSelectedCostRequest267V1(std::string_view,DjcSelectedCostRequest267V1&)noexcept;
std::string SerializeDjcSelectedCostResult267V1(std::string_view,const DjcSelectedCostResult267V1&);
} // namespace
