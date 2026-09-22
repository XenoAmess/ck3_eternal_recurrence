#include "xar_bridge/player_epidemic_recovery_v1.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

namespace {
void Require(bool value) { if (!value) std::abort(); }

template <typename T>
void Put(std::byte *base, std::size_t offset, const T &value) {
  std::memcpy(base + offset, &value, sizeof(value));
}
} // namespace

int main() {
  using namespace xar::ck3_11906;
  std::int32_t title_id = -1;
  Require(ParsePlayerEpidemicRecoveryStepV1(
      "query-player-epidemic-recovery-v1", title_id) && title_id == 0);
  Require(ParsePlayerEpidemicRecoveryStepV1(
      "query-player-epidemic-recovery-v1-title-524", title_id) &&
      title_id == 524);
  Require(!ParsePlayerEpidemicRecoveryStepV1(
      "query-player-epidemic-recovery-v1-title-0", title_id));
  Require(!ParsePlayerEpidemicRecoveryStepV1(
      "query-player-epidemic-recovery-v1-title-524x", title_id));
  Require(!ParsePlayerEpidemicRecoveryStepV1(
      "query-player-epidemic-recovery-v1-title-2147483648", title_id));

  std::array<std::byte, 0x48> context{};
  std::array<std::byte, 0x48> row{};
  std::array<std::byte, 0x20> elements{};
  void *rows = row.data();
  const std::int32_t row_count = 1;
  const std::int32_t key = 42;
  void *element_data = elements.data();
  std::int32_t element_count = 2;
  Put(context.data(), 0x30, rows);
  Put(context.data(), 0x3C, row_count);
  Put(row.data(), 0x08, key);
  Put(row.data(), 0x10, element_data);
  Put(row.data(), 0x1C, element_count);
  const std::uint16_t kind = 5;
  const std::int64_t first_id = 524;
  const std::int64_t second_id = 525;
  Put(elements.data(), 0x00, kind);
  Put(elements.data(), 0x08, first_id);
  Put(elements.data(), 0x10, kind);
  Put(elements.data(), 0x18, second_id);
  std::vector<std::int32_t> titles;
  Require(ReadEpidemicRecoveryListRowsV1(context.data(), key, titles));
  Require(titles == std::vector<std::int32_t>({524, 525}));
  Require(ReadEpidemicRecoveryListRowsV1(context.data(), 43, titles));
  Require(titles.empty());
  const std::uint16_t wrong_kind = 4;
  Put(elements.data(), 0x10, wrong_kind);
  Require(!ReadEpidemicRecoveryListRowsV1(context.data(), key, titles));
  Put(elements.data(), 0x10, kind);
  element_count = -1;
  Put(row.data(), 0x1C, element_count);
  Require(!ReadEpidemicRecoveryListRowsV1(context.data(), key, titles));

  PlayerEpidemicRecoveryV1 result{};
  result.snapshot_revision = 237;
  result.date_raw = 53376672;
  result.played_character_id = 36403;
  result.requested_title_id = 524;
  result.available = true;
  result.counties.push_back({524, true, false});
  const auto serialized = SerializePlayerEpidemicRecoveryV1(result);
  Require(serialized.find("\"landed_title_id\":524") != std::string::npos);
  Require(serialized.find("\"minor_present\":true") != std::string::npos);
  Require(serialized.find("\"requested_title_id\":524") != std::string::npos);
  result.counties.front().landed_title_id = 525;
  Require(SerializePlayerEpidemicRecoveryV1(result).empty());
  return 0;
}
