#pragma once
#include "xar_bridge/holy_site_relic_action_v1.hpp"
namespace xar::ck3_12004::religion::relic_actions {
bool HasRelicRequestFields12004(std::string_view) noexcept;
bool ParseRelicRequest12004(std::string_view,std::uint32_t operation,std::uint32_t site,Request&) noexcept;
}
