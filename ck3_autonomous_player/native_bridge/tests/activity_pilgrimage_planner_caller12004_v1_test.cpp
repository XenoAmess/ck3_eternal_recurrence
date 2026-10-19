#include "xar_bridge/activity_pilgrimage_planner_caller12004_v1.hpp"
#include "xar_bridge/ck3_12004.hpp"

#include <cstdlib>
#include <iostream>

namespace {
using namespace xar;
using namespace xar::ck3_12002;
using Status = ActivityPilgrimagePlannerStatus12004V1;
using Op = ActivityPilgrimagePlannerOperation12004V1;

struct Fake {
  game::Snapshot snapshot{};
  int snapshot_reads = 0;
  bool drift = false;
};

bool ReadSnapshot(void *opaque, game::Snapshot &out) noexcept {
  auto &f = *static_cast<Fake *>(opaque);
  ++f.snapshot_reads;
  out = f.snapshot;
  if (f.drift) ++out.date_raw;
  return true;
}
bool ResolveKey(void *, std::int32_t, std::string_view &) noexcept { return false; }
bool TrapMemory(void *, std::uintptr_t, void *, std::size_t) noexcept { std::abort(); }

void Expect(bool value) { if (!value) std::abort(); }

void Populate(Fake &f, ActivityPlanner12002NativeV1 &native,
              ck3_11906::MainThreadExecutionStampV1 &stamp,
              ActivityPilgrimagePlannerRequest12004V1 &request) {
  f.snapshot.date_raw = 53219928;
  f.snapshot.played_character_id = 29829;
  f.snapshot.has_played_character = true;
  f.snapshot.played_character_alive = true;
  f.snapshot.paused = true;
  f.snapshot.map_ready = true;
  Expect(BindActivityPlanner12002V1(
      native, 0x140000000, ck3_12004::kExecutableSha256, &f,
      &ReadSnapshot, &TrapMemory, &ResolveKey, 7, GetCurrentThreadId(), 0x30000000));
  stamp.pump_epoch = 4;
  stamp.thread_id = GetCurrentThreadId();
  stamp.tls_initialized_flag_address = 0x40000000;
  stamp.tls_initialized = 1;
  stamp.tls_context = 0x40001000;
  stamp.tls_main_thread_marker = 1;
  stamp.jomini_state = 0x40002000;
  stamp.game_state = native.game_state;
  stamp.date_raw = f.snapshot.date_raw;
  stamp.paused = true;
  request.expected_frame = {7, f.snapshot.date_raw, 29829, true, true, true, true};
}
} // namespace

int main() {
  // All invalid-owner/frame fixtures arm a memory trap. A guard regression
  // must fail before the first native builder/read/call is reached.
  Fake f{};
  ActivityPlanner12002NativeV1 native{};
  ck3_11906::MainThreadExecutionStampV1 stamp{};
  ActivityPilgrimagePlannerRequest12004V1 request{};
  ActivityPilgrimagePlannerResult12004V1 result{};
  Populate(f, native, stamp, request);

  const auto owner = native.owner_thread_id;
  native.owner_thread_id = owner + 1;
  Expect(ExecuteActivityPilgrimagePlannerOperation12004V1(native, stamp, f.snapshot, request, result));
  Expect(result.status == Status::context_rejected && f.snapshot_reads == 0 && !result.invoked);
  native.owner_thread_id = owner;

  stamp.tls_main_thread_marker = 0;
  ExecuteActivityPilgrimagePlannerOperation12004V1(native, stamp, f.snapshot, request, result);
  Expect(result.status == Status::context_rejected && f.snapshot_reads == 0);
  stamp.tls_main_thread_marker = 1;

  ++request.expected_frame.revision;
  ExecuteActivityPilgrimagePlannerOperation12004V1(native, stamp, f.snapshot, request, result);
  Expect(result.status == Status::context_rejected && f.snapshot_reads == 0);
  --request.expected_frame.revision;

  native.executable_sha256 = bridge::kActivityPlanner12002ExeSha256V1;
  ExecuteActivityPilgrimagePlannerOperation12004V1(native, stamp, f.snapshot, request, result);
  Expect(result.status == Status::context_rejected && f.snapshot_reads == 0);
  native.executable_sha256 = ck3_12004::kExecutableSha256;

  request.operation = static_cast<Op>(255);
  ExecuteActivityPilgrimagePlannerOperation12004V1(native, stamp, f.snapshot, request, result);
  Expect(result.status == Status::operation_rejected && f.snapshot_reads == 0);
  request.operation = Op::can_select;
  request.province_id = 0;
  ExecuteActivityPilgrimagePlannerOperation12004V1(native, stamp, f.snapshot, request, result);
  Expect(result.status == Status::operation_rejected && f.snapshot_reads == 0);
  request.operation = Op::read;

  f.drift = true;
  ExecuteActivityPilgrimagePlannerOperation12004V1(native, stamp, f.snapshot, request, result);
  Expect(result.status == Status::frame_changed && f.snapshot_reads == 1 &&
         result.pre_snapshot_observed && !result.invoked);
  f.drift = false;

#if !defined(XAR_CK3_ENABLE_PILGRIMAGE_PIOUS_PLANNER_PRIVATE_V1)
  request.operation = Op::open;
  ExecuteActivityPilgrimagePlannerOperation12004V1(native, stamp, f.snapshot, request, result);
  Expect(result.status == Status::private_action_disabled && !result.invoked);
#endif
  std::cout << "CANDIDATE pilgrimage owner/TLS/current-frame caller rejection boundaries\n";
}
