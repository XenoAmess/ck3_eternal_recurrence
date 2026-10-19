#include "xar_bridge/camera_tracking_v1.hpp"
#include <cassert>
#include <cstring>
using namespace xar::presentation::tracked;
int main() {
  RequestV1 r{};
  r.request_sequence = 2; r.province_count = 1; r.owner_epoch = 1;
  r.scope_generation = 0x100000001ULL; r.actor = 40526; r.fullarmy_id = 33554800;
  r.start_date_raw = 1000; r.max_date_raw = 1240;
  r.provinces[0].id = 2615; std::strcpy(r.provinces[0].title_key, "b_fixture");
  assert(ValidRequestV1(r, 2));
  assert(!ValidRequestV1(r, 4)); assert(!ValidRequestV1(r, 3));
  auto changed = r; changed.province_count = 33; assert(!ValidRequestV1(changed, 2));
  changed = r; changed.province_count = 2; changed.provinces[1] = changed.provinces[0];
  assert(!ValidRequestV1(changed, 2));
  Frame f{};
  f.complete = f.alive = f.map_ready = f.ui_clear = f.full_id_valid = f.scope_armed = true;
  f.actor = f.subject_owner = r.actor; f.date_raw = 1024;
  f.scope_generation = r.scope_generation;
  f.scope_start_date_raw = r.start_date_raw; f.scope_target_date_raw = r.max_date_raw;
  assert(ValidateFrameV1(r, f) == State::tracking);
  f.current_province_id = 1; f.battle_province_id = 2;
  f.combat_id = -1; assert(ObservedProvinceV1(f) == 1);
  f.combat_id = 0; assert(ObservedProvinceV1(f) == 2);
  f.combat_id = -16777216; assert(ObservedProvinceV1(f) == 2);
  f.combat_id = 123; assert(ObservedProvinceV1(f) == 2);
  auto negative = f; negative.ui_clear = false;
  assert(ValidateFrameV1(r, negative) == State::ui_or_identity_unknown);
  negative = f; negative.subject_owner += 1;
  assert(ValidateFrameV1(r, negative) == State::ui_or_identity_unknown);
  negative = f; negative.full_id_valid = false;
  assert(ValidateFrameV1(r, negative) == State::ui_or_identity_unknown);
  negative = f; negative.retreating = true;
  assert(ValidateFrameV1(r, negative) == State::ui_or_identity_unknown);
  negative = f; negative.scope_generation += 1;
  assert(ValidateFrameV1(r, negative) == State::scope_ended);
  negative = f; negative.scope_armed = false;
  assert(ValidateFrameV1(r, negative) == State::scope_ended);
  negative = f; negative.date_raw = r.max_date_raw;
  assert(ValidateFrameV1(r, negative) == State::scope_ended);
  negative = f; negative.paused = true;
  assert(ValidateFrameV1(r, negative) == State::scope_ended);
  SetConnectionActiveV1(true); const auto before = ReadConnectionV1();
  assert(before.active && before.epoch != 0);
  SetConnectionActiveV1(false); const auto after = ReadConnectionV1();
  assert(!after.active && after.epoch != before.epoch);
  SetConnectionActiveV1(true); assert(ReadConnectionV1().epoch != before.epoch);
  return 0;
}
