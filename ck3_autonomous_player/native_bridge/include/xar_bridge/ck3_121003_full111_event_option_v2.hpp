#pragma once

#include "xar_bridge/ck3_121003_lyd26785313_v1.hpp"

namespace xar::ck3_121003::build26785313 {
inline constexpr std::array<std::string_view, 3> kFull111EventOptionSteps267V2{
    "prepare-current-ordinary-event-option-26785313-v2",
    "select-current-ordinary-event-option-26785313-v2",
    "query-current-ordinary-event-queue-26785313-v2"};
inline constexpr std::array<std::string_view, 3> kFull111EventOptionCapabilities267V2{
    "game.query.prepare-current-ordinary-event-option.26785313.v2",
    "game.command.select-current-ordinary-event-option.26785313.v2",
    "game.query.current-ordinary-event-queue.26785313.v2"};
inline constexpr std::string_view kFull111EventOptionRequestSchema267V2 =
    "ck3.full111.ordinary_event_option_request.v2";
inline constexpr std::string_view kFull111EventOptionResultSchema267V2 =
    "ck3.full111.ordinary_event_option_result.v2";

enum class Full111EventOptionAction267V2 { prepare, select, query_queue };
struct Full111EventOptionTarget267V2 {
    std::int32_t instance_id = 0, recipient_character_id = -1;
    std::string definition_key;
    std::int32_t authored_option_index = -1;
    friend bool operator==(const Full111EventOptionTarget267V2 &, const Full111EventOptionTarget267V2 &) = default;
};
struct Full111EventOptionLineage267V2 {
    std::uint64_t source_revision = 0;
    std::string renderer_request_id;
    std::uint64_t renderer_provider_generation = 0, renderer_query_sequence = 0;
    std::optional<std::string> prepare_request_id;
    std::uint64_t lease_sequence = 0;
    std::optional<std::string> effect_request_id;
    std::uint64_t claim_sequence = 0;
    friend bool operator==(const Full111EventOptionLineage267V2 &, const Full111EventOptionLineage267V2 &) = default;
};
struct Full111EventOptionRequest267V2 {
    Full111EventOptionAction267V2 action = Full111EventOptionAction267V2::prepare;
    std::string request_id;
    ck3_1210::CoreSnapshotPrefix expected{};
    std::uint64_t expected_revision = 0, deadline_unix_ms = 0;
    Full111EventOptionTarget267V2 target;
    Full111EventOptionLineage267V2 lineage;
};
struct Full111EventQueue267V2 {
    std::vector<std::int32_t> instance_ids;
    bool target_present = false;
};
struct Full111EventOptionResult267V2 {
    std::optional<Full111EventOptionTarget267V2> target;
    std::optional<Full111EventOptionLineage267V2> lineage;
    std::optional<Full111EventQueue267V2> queue;
};

bool ParseFull111EventOptionRequest267V2(std::string_view, Full111EventOptionRequest267V2 &) noexcept;
std::string SerializeFull111EventOptionResult267V2(std::string_view, Full111EventOptionAction267V2,
    const LydResult267V1 &, const Full111EventOptionResult267V2 &);
}
