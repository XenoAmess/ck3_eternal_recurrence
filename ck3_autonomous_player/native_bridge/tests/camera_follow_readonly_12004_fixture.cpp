// AUTHORED_NOTRUN: no compiler/Game/RPC is invoked by this source-only package.
// Focused pending-table fixture includes the production algorithm, not a copy.
// Compile only the genuine pending algorithm here; full reader qualification is
// separate. No Bridge/runtime dependencies or duplicate production cpp object.
#define XAR_CAMERA_FOLLOW_READONLY_PENDING_FIXTURE
#include "../src/camera_follow_readonly_12004.cpp"
#undef XAR_CAMERA_FOLLOW_READONLY_PENDING_FIXTURE
#include <array>
#include <cstring>
#include <vector>

namespace xar::presentation::tracked {
namespace {
template<class T> void Put(void *p, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(p) + offset, &value, sizeof(value));
}
bool PendingCases() {
  std::array<std::byte, 0x30> storage{};
  std::array<std::byte, 0x600> item{};
  std::vector<std::byte> slots(4096 * 0x10);
  const auto address = [](auto &v) { return reinterpret_cast<Address>(v.data()); };
  Put(storage.data(), 0x20, address(slots));
  const auto read = [](Address p, std::size_t o, auto &v) { return Get(p, o, v); };
  int pending_calls = 0, validate_calls = 0;
  bool active = false, valid = true;
  const auto pending = [&](Address, Address) { ++pending_calls; return active; };
  const auto validate = [&](ck3_12002::EventCommand *c) {
    ++validate_calls;
    return valid && c->instance_id == 255 && c->choice == 0 &&
        c->primary_vtable == 11 && c->secondary_vtable == 12;
  };
  Frame f{};
  // Empty high-water capacity 256 is not an active-count 256, and exceeds the
  // rejected proposed 128 cap. Holes must be visited rather than truncated.
  Put(storage.data(), 0x2C, std::int32_t{256});
  if (!PendingClear(address(storage), 7, 1, read, pending, validate, f, 11, 12) ||
      f.pending_slot_capacity != 256 || f.pending_slots_visited != 256 ||
      pending_calls != 0 || validate_calls != 0) return false;
  Put(slots.data(), 255 * 0x10 + 8, address(item));
  Put(item.data(), 0x10, std::int32_t{255});
  Put(item.data(), 0x5C0, std::int32_t{0});
  Put(item.data(), 0x2F4, std::int32_t{7});
  f = {};
  // Occupied historical slot whose native pending predicate is false is clear.
  if (!PendingClear(address(storage), 7, 1, read, pending, validate, f, 11, 12) ||
      pending_calls != 1 || validate_calls != 0) return false;
  active = true;
  f = {};
  // A single eligible interaction at the final slot must preempt.
  if (PendingClear(address(storage), 7, 1, read, pending, validate, f, 11, 12) ||
      f.pending_slots_visited != 256 || validate_calls != 1 ||
      f.reason != Failure::pending_present) return false;
  valid = false;
  f = {};
  if (!PendingClear(address(storage), 7, 1, read, pending, validate, f, 11, 12))
    return false;
  // Notification uses the original no-validator path and also preempts.
  Put(item.data(), 0x5C6, std::uint8_t{1});
  const int prior = validate_calls;
  f = {};
  if (PendingClear(address(storage), 7, 1, read, pending, validate, f, 11, 12) ||
      validate_calls != prior) return false;
  Put(slots.data(), 255 * 0x10 + 8, Address{0});
  Put(storage.data(), 0x2C, std::int32_t{4096});
  f = {};
  if (!PendingClear(address(storage), 7, 1, read, pending, validate, f, 11, 12) ||
      f.pending_slots_visited != 4096) return false;
  int checks = 0;
  const auto yield_after_32 = [](void *context) noexcept {
    return ++*static_cast<int *>(context) < 2;
  };
  f = {};
  if (PendingClear(address(storage), 7, 1, read, pending, validate, f, 11, 12,
      yield_after_32, &checks) || f.pending_slots_visited != 32 || checks != 2 ||
      f.reason != Failure::cooperative_yield || f.complete || f.ui_clear) return false;
  Put(storage.data(), 0x2C, std::int32_t{4097});
  f = {};
  if (PendingClear(address(storage), 7, 1, read, pending, validate, f, 11, 12) ||
      f.pending_slot_capacity != 4097 || f.pending_slots_visited != 0 ||
      f.reason != Failure::pending_capacity) return false;
  Put(storage.data(), 0x2C, std::int32_t{-1});
  f = {};
  if (PendingClear(address(storage), 7, 1, read, pending, validate, f, 11, 12))
    return false;
  Put(storage.data(), 0x2C, std::int32_t{1});
  Put(storage.data(), 0x20, Address{0});
  f = {};
  return !PendingClear(address(storage), 7, 1, read, pending, validate, f, 11, 12);
}
} // namespace
extern "C" __declspec(dllexport) int CameraFollowPendingFixture12004V1() {
  return PendingCases() ? 0 : 1;
}
} // namespace xar::presentation::tracked
#if defined(XAR_CAMERA_FOLLOW_READONLY_FIXTURE_EXE)
int main() {
  return xar::presentation::tracked::CameraFollowPendingFixture12004V1();
}
#endif
