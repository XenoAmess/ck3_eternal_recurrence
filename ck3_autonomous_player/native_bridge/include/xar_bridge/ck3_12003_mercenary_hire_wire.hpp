#pragma once

#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_12003::mercenary {
struct HireActionResult;
}

namespace xar::ck3_12003 {

inline constexpr std::string_view kMercenaryHireStepV1 =
    "hire-mercenary-v1";
inline constexpr std::string_view kMercenaryHireCapabilityV1 =
    "game.command.hire-mercenary-v1";
inline constexpr std::string_view kMercenaryHireResultSchemaV1 =
    "ck3_12003_mercenary_hire_action_v1";

struct MercenaryHireRequestV1 {
  std::uint32_t company_id = UINT32_MAX;
  std::uint64_t expected_revision = 0;
};

// Only the company and native snapshot revision enter this typed action.
// The owner executor resolves the actual played character independently.
bool ParseMercenaryHireRequestV1(std::string_view step,
    std::string_view payload, MercenaryHireRequestV1 &) noexcept;

// Native command submission remains pending an independent after-state query.
// This serializer does not synthesize hired/employer/army/cash outcomes.
std::string SerializeMercenaryHireResultV1(
    const mercenary::HireActionResult &, std::string_view request_id,
    std::uint64_t command_sequence, std::uint64_t snapshot_revision,
    std::int32_t date_raw);

} // namespace xar::ck3_12003
