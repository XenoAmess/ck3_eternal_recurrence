#include "xar_bridge/activity_pilgrimage_destination_v1.hpp"
#include "xar_bridge/ck3_12002_feast_planner.hpp"

#include <array>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <unordered_map>

namespace {
using namespace xar::bridge;
constexpr std::uintptr_t kBase = 0x140000000;
constexpr std::uintptr_t kPlanner = 0x10004000;
constexpr std::uintptr_t kType = 0x10006000;
constexpr std::uintptr_t kRows = 0x10008000;
constexpr std::uintptr_t kProvince = 0x10009000;
constexpr std::uint32_t kProvinceId = 1234;

#define Expect(x) do { if (!(x)) { \
  std::cerr << "pilgrimage destination candidate failed line " << __LINE__ << '\n'; \
  std::abort(); } } while (false)

struct Fake {
  std::unordered_map<std::uintptr_t, std::uint8_t> bytes{};
  ActivityPilgrimageDestinationStateV1 state{};
  bool eligible = true;
  bool drift_on_predicate = false;
  bool fail_action = false;
  bool fail_post = false;
  bool wrong_destination = false;
  bool charge_gold = false;
  bool replace_option = false;
  int stage_after = 3;
  int predicates = 0;
  int actions = 0;
  template<class T> void Put(std::uintptr_t address, const T &value) {
    const auto *p = reinterpret_cast<const std::uint8_t *>(&value);
    for (std::size_t i = 0; i < sizeof(value); ++i) bytes[address + i] = p[i];
  }
};

bool Read(void *opaque, std::uintptr_t address, void *out, std::size_t count) noexcept {
  const auto &f = *static_cast<Fake *>(opaque);
  auto *p = static_cast<std::uint8_t *>(out);
  for (std::size_t i = 0; i < count; ++i) {
    const auto it = f.bytes.find(address + i);
    if (it == f.bytes.end()) return false;
    p[i] = it->second;
  }
  return true;
}
bool State(void *opaque, ActivityPilgrimageDestinationStateV1 &out) noexcept {
  const auto &f = *static_cast<Fake *>(opaque);
  if (f.fail_post && f.actions) return false;
  out = f.state;
  return true;
}
bool Province(void *, std::uint32_t id, std::uintptr_t &out) noexcept {
  if (id != kProvinceId) return false;
  out = kProvince;
  return true;
}
bool CanSelect(void *opaque, std::uintptr_t planner, std::uintptr_t province,
               bool &out) noexcept {
  auto &f = *static_cast<Fake *>(opaque);
  if (planner != kPlanner || province != kProvince) return false;
  ++f.predicates;
  out = f.eligible;
  if (f.drift_on_predicate) ++f.state.frame.revision;
  return true;
}
bool Select(void *opaque, std::uintptr_t planner, std::uintptr_t province) noexcept {
  auto &f = *static_cast<Fake *>(opaque);
  if (planner != kPlanner || province != kProvince) return false;
  ++f.actions;
  if (f.fail_action) return false;
  f.state.stage = f.stage_after;
  f.state.selection.planning_stage = f.stage_after;
  f.state.province_id = f.wrong_destination ? kProvinceId + 1 : kProvinceId;
  f.state.active_row = 0;
  if (f.charge_gold) ++f.state.gold_raw;
  if (f.replace_option) ++f.state.selection.native_option_id;
  return true;
}

void Populate(Fake &f) {
  f.Put(kBase + 0x11B6F30, std::array<std::uint8_t, 8>{
      0x48,0x89,0x5C,0x24,0x10,0x55,0x56,0x57});
  f.Put(kBase + 0x11B6C60, std::array<std::uint8_t, 9>{
      0x48,0x89,0x5C,0x24,0x08,0x48,0x89,0x6C,0x24});
  f.Put(kBase + 0x11B6C97, std::array<std::uint8_t, 6>{
      0x8B,0x42,0x10,0x89,0x41,0x08});
  f.Put(kBase + 0x11B6CB3, std::array<std::uint8_t, 7>{
      0x40,0x38,0xBD,0xED,0x3B,0,0});
  f.Put(kBase + 0x11B6CC0, std::array<std::uint8_t, 6>{
      0x8B,0x8B,0xEC,0x1A,0,0});
  f.Put(kBase + 0x11B6D31, std::array<std::uint8_t, 8>{
      0xBA,5,0,0,0,0x48,0x8B,0xCB});
  f.Put(kProvince + 0x10, kProvinceId);
  auto &s = f.state;
  s.frame = {7, 53219928, 29829, true, true, true, true};
  s.planner = kPlanner; s.activity_type = kType;
  s.stage = 2; s.previous_stage = 1; s.single_location_flag = 1;
  s.configuration_rows = kRows; s.configuration_row_count = 1;
  s.active_row = kRows; s.phase = 0x1000A000;
  s.phase_kind = 0; s.phase_auto_raw = 1; s.gold_raw = 700000;
  auto &selected = s.selection;
  selected.observed = true; selected.kind = kOrdinaryPilgrimagePiousContractV1.kind;
  selected.frame = s.frame; selected.planner = s.planner;
  selected.activity_type = s.activity_type; selected.planning_stage = 2;
  selected.native_selected_option = 0x1000B000; selected.native_option_id = 42;
  const auto key = kOrdinaryPilgrimagePiousContractV1.special_option_key;
  std::memcpy(selected.option_key.data(), key.data(), key.size());
  selected.option_key_size = static_cast<std::uint16_t>(key.size());
}

ActivityPilgrimageDestinationEnvironmentV1 Env(Fake &f) {
  return {{true, xar::ck3_12004::kExecutableSha256, kBase, &f, &Read,
           nullptr, nullptr, nullptr}, &State, &Province, &CanSelect, &Select};
}
} // namespace

int main() {
  using S = ActivityPilgrimageDestinationStatusV1;
  Fake good{}; Populate(good);
  auto r = ReadActivityPilgrimageDestinationCanSelectV1(Env(good), good.state.frame, kProvinceId);
  Expect(r.status == S::can_select_observed && r.can_select && !r.submitted && good.actions == 0);
  r = SelectActivityPilgrimageDestinationV1(Env(good), good.state.frame, kProvinceId);
  Expect(r.status == S::selection_verified && r.planning_stage_after == 3 &&
         r.row_filled && r.gold_unchanged && !r.needs_recovery && good.actions == 1);

  Fake final_stage{}; Populate(final_stage); final_stage.stage_after = 5;
  r = SelectActivityPilgrimageDestinationV1(Env(final_stage), final_stage.state.frame, kProvinceId);
  Expect(r.status == S::selection_verified && r.planning_stage_after == 5);

  Fake two_rows{}; Populate(two_rows); two_rows.state.configuration_row_count = 2;
  r = SelectActivityPilgrimageDestinationV1(Env(two_rows), two_rows.state.frame, kProvinceId);
  Expect(!r.submitted && two_rows.actions == 0);

  Fake other_option{}; Populate(other_option);
  other_option.state.selection.option_key[0] = 'x';
  r = SelectActivityPilgrimageDestinationV1(Env(other_option), other_option.state.frame, kProvinceId);
  Expect(!r.submitted && other_option.actions == 0);

  Fake refused{}; Populate(refused); refused.eligible = false;
  r = ReadActivityPilgrimageDestinationCanSelectV1(Env(refused), refused.state.frame, kProvinceId);
  Expect(r.status == S::can_select_observed && r.can_select_observed && !r.can_select);
  r = SelectActivityPilgrimageDestinationV1(Env(refused), refused.state.frame, kProvinceId);
  Expect(!r.submitted && refused.actions == 0);

  Fake drift{}; Populate(drift); drift.drift_on_predicate = true;
  r = SelectActivityPilgrimageDestinationV1(Env(drift), drift.state.frame, kProvinceId);
  Expect(!r.submitted && drift.actions == 0);

  Fake unknown{}; Populate(unknown); unknown.fail_action = true;
  r = SelectActivityPilgrimageDestinationV1(Env(unknown), unknown.state.frame, kProvinceId);
  Expect(r.status == S::native_call_failed && r.submitted && r.needs_recovery && unknown.actions == 1);

  Fake missing{}; Populate(missing); missing.fail_post = true;
  r = SelectActivityPilgrimageDestinationV1(Env(missing), missing.state.frame, kProvinceId);
  Expect(r.status == S::postcondition_failed && r.submitted && r.needs_recovery);

  Fake paid{}; Populate(paid); paid.charge_gold = true;
  r = SelectActivityPilgrimageDestinationV1(Env(paid), paid.state.frame, kProvinceId);
  Expect(r.status == S::postcondition_failed && !r.gold_unchanged && r.needs_recovery);

  Fake wrong{}; Populate(wrong); wrong.wrong_destination = true;
  r = SelectActivityPilgrimageDestinationV1(Env(wrong), wrong.state.frame, kProvinceId);
  Expect(r.status == S::postcondition_failed && !r.row_filled && r.needs_recovery);

  Fake replaced{}; Populate(replaced); replaced.replace_option = true;
  r = SelectActivityPilgrimageDestinationV1(Env(replaced), replaced.state.frame, kProvinceId);
  Expect(r.status == S::postcondition_failed && !r.selected_option_retained && r.needs_recovery);
  std::cout << "CANDIDATE exact4 single-predefined pilgrimage destination boundary\n";
}
