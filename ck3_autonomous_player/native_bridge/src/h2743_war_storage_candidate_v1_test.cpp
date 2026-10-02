#include "xar_bridge/h2743_war_storage_candidate_v1.hpp"

#include <cstddef>
#include <cstdint>

using xar::bridge::h2743::AdmitStableWarStorageCandidate;
using xar::bridge::h2743::CompleteScan;
using xar::bridge::h2743::SlotState;
using xar::bridge::h2743::WarSlot;

namespace {

CompleteScan Sample(bool matching) {
  CompleteScan scan{};
  scan.capacity = 17;
  for (std::int32_t index = 0; index < scan.capacity; ++index) {
    WarSlot row{};
    row.index = index;
    scan.slots.push_back(row);
  }
  auto &target = scan.slots[15];
  target.state = SlotState::active;
  target.war_id = 16'777'231;
  target.object_address = 0x1000;
  target.primary_attacker = 30'097;
  target.primary_defender = 29'829;
  target.cb_index = 17;
  target.cb_address = 0x2000;
  target.cb_key = "individual_county_de_jure_cb";
  target.primary_attacker_in_participants = true;
  target.primary_defender_in_participants = true;
  auto &other = scan.slots[16];
  other.state = SlotState::active;
  other.war_id = 16'777'232;
  other.object_address = 0x3000;
  other.primary_attacker = 30'097;
  other.primary_defender = 29'829;
  other.cb_index = matching ? 21 : 22;
  other.cb_address = 0x4000;
  other.cb_key = matching ? "fp2_border_raid" : "claim_cb";
  other.primary_attacker_in_participants = true;
  other.primary_defender_in_participants = true;
  return scan;
}

auto Admit(const CompleteScan &first, const CompleteScan &second) {
  return AdmitStableWarStorageCandidate(
      first, second, 16'777'231, 0x1000, 30'097, 29'829, 17,
      "individual_county_de_jure_cb");
}

}  // namespace

int main() {
  const auto yes = Sample(true);
  const auto no = Sample(false);
  const auto positive = Admit(yes, yes);
  const auto negative = Admit(no, no);
  if (!positive || !positive->border_raid_pair ||
      positive->matching_wars != 1 || positive->active_wars != 2 ||
      !negative || negative->border_raid_pair ||
      negative->matching_wars != 0 || Admit(yes, no)) return 1;

  auto partial = no;
  partial.slots.pop_back();
  if (Admit(partial, partial)) return 2;
  auto wrong_generation = no;
  wrong_generation.slots[16].war_id = 17;
  if (Admit(wrong_generation, wrong_generation)) return 3;
  auto ended_raid = yes;
  ended_raid.slots[16].state = SlotState::ended;
  const auto ended_result = Admit(ended_raid, ended_raid);
  if (!ended_result || ended_result->border_raid_pair ||
      ended_result->active_wars != 1 || ended_result->matching_wars != 0)
    return 8;
  auto recycled_generation = no;
  recycled_generation.slots[16].war_id += 0x01000000;
  if (Admit(no, recycled_generation)) return 9;
  auto changed_target_cb = no;
  changed_target_cb.slots[15].cb_address = 0x5000;
  if (Admit(no, changed_target_cb)) return 10;
  changed_target_cb = no;
  changed_target_cb.slots[15].cb_key = "other_cb";
  if (Admit(no, changed_target_cb)) return 11;
  auto missing_target = no;
  missing_target.slots[15] = WarSlot{.index = 15};
  if (Admit(missing_target, missing_target)) return 4;
  auto wrong_pointer = no;
  wrong_pointer.slots[15].object_address = 0x5000;
  if (Admit(wrong_pointer, wrong_pointer)) return 5;
  auto missing_participant = no;
  missing_participant.slots[16].primary_attacker_in_participants = false;
  if (Admit(missing_participant, missing_participant)) return 6;
  auto hidden_pair = no;
  hidden_pair.slots[16].cb_key = "fp2_border_raid";
  hidden_pair.slots[16].cb_address = 0;
  if (Admit(hidden_pair, hidden_pair)) return 7;
  return 0;
}
