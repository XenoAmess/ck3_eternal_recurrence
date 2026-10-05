#pragma once

#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_12003::religion::holy_order {
struct HireActionResult;
}

namespace xar::ck3_12003 {

inline constexpr std::string_view kHolyOrderHireStepV1 =
    "hire-holy-order-v1";
inline constexpr std::string_view kHolyOrderHireCapabilityV1 =
    "game.command.hire-holy-order-v1";
inline constexpr std::string_view kHolyOrderHireResultSchemaV1 =
    "ck3_12003_holy_order_hire_action_v1";

struct HolyOrderHireRequestV1 {
  std::uint32_t holy_order_id = UINT32_MAX;
  std::uint64_t expected_revision = 0;
};

// Only the holy order and native snapshot revision enter this typed action.
// The owner executor resolves the actual played character independently.
bool ParseHolyOrderHireRequestV1(std::string_view step,
    std::string_view payload, HolyOrderHireRequestV1 &) noexcept;

// Native command submission remains pending an independent after-state query.
// This serializer does not synthesize hired/employer/army/cash outcomes.
std::string SerializeHolyOrderHireResultV1(
    const religion::holy_order::HireActionResult &, std::string_view request_id,
    std::uint64_t command_sequence, std::uint64_t snapshot_revision,
    std::int32_t date_raw);

} // namespace xar::ck3_12003
