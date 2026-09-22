#include "xar_bridge/player_epidemic_treatment_presence_v1.hpp"

#include <array>
#include <cstdlib>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <string>

namespace {
void Require(bool value) {
  if (!value) std::abort();
}
}

int main() {
  using namespace xar::ck3_11906;
  std::array<std::byte, 0x200> extension{};
  std::array<std::byte, 0x90> rows{};
  int wanted_definition = 1;
  int other_definition = 2;
  void *wanted = &wanted_definition;
  void *other = &other_definition;
  bool present = true;

  // A missing extension is a known empty modifier set, unlike a malformed
  // non-null row span or an unresolved definition.
  Require(ScanPlayerModifierRowsV1(nullptr, wanted, present) && !present);
  Require(!ScanPlayerModifierRowsV1(nullptr, nullptr, present));
  void *row_data = rows.data();
  std::int32_t count = 2;
  std::memcpy(extension.data() + 0x188, &row_data, sizeof(row_data));
  std::memcpy(extension.data() + 0x194, &count, sizeof(count));
  std::memcpy(rows.data(), &other, sizeof(other));
  std::memcpy(rows.data() + 0x48, &wanted, sizeof(wanted));
  Require(ScanPlayerModifierRowsV1(extension.data(), wanted, present) &&
         present);
  Require(ScanPlayerModifierRowsV1(extension.data(), rows.data(), present) &&
         !present);

  count = -1;
  std::memcpy(extension.data() + 0x194, &count, sizeof(count));
  Require(!ScanPlayerModifierRowsV1(extension.data(), wanted, present));
  count = 1;
  row_data = nullptr;
  std::memcpy(extension.data() + 0x188, &row_data, sizeof(row_data));
  std::memcpy(extension.data() + 0x194, &count, sizeof(count));
  Require(!ScanPlayerModifierRowsV1(extension.data(), wanted, present));

  PlayerEpidemicTreatmentPresenceV1 result{};
  result.snapshot_revision = 171;
  result.date_raw = 53350560;
  result.played_character_id = 36403;
  result.available = true;
  result.present = true;
  const auto json = SerializePlayerEpidemicTreatmentPresenceV1(result);
  Require(json.find("\"modifier_key\":\"ce1_unorthodox_epidemic_treatment\"") !=
         std::string::npos);
  Require(json.find("\"present\":true") != std::string::npos);
  Require(json.find("\"remaining_days\":{\"status\":\"unavailable\"") !=
         std::string::npos);
  result.available = false;
  result.present = false;
  result.unavailable_reason = "modifier_rows_unavailable";
  Require(SerializePlayerEpidemicTreatmentPresenceV1(result).find(
             "\"present\":null") != std::string::npos);
  return 0;
}
