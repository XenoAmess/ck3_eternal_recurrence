#include "xar_bridge/army_assault_group_release_observer_12004.hpp"
#include "xar_bridge/ck3_12004.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <stdexcept>
#include <string>

namespace {
using namespace xar::ck3_12004;
alignas(8) std::array<std::byte, 0x80> g_owned_slots{};
std::array<std::uint32_t, 3> g_owned_army_ids{42, UINT32_MAX, 42};
void *g_owned_manager = nullptr;
unsigned g_original_calls = 0;
bool g_block_post_capacity = false;
constexpr std::uint64_t kOpaqueRax = 0xF123456789ABCDEFULL;

void Require(bool value, const char *reason) {
  if (!value) throw std::runtime_error(reason);
}
template <typename V> void Store(void *object, std::size_t offset, V value) {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
}
bool ReadOwned(void *, const void *address, void *out, std::size_t bytes) noexcept {
  if (g_block_post_capacity && g_original_calls != 0 &&
      address == g_owned_slots.data() + 0x18) return false;
  std::memcpy(out, address, bytes); return true;
}
std::uint64_t __fastcall OwnedOriginal(const void *record_const) {
  ++g_original_calls;
  auto *record = const_cast<void *>(record_const);
  // The owned body mirrors only the source-defined two header branches.
  // It does not call an allocator or touch pending/manager state.
  for (const auto offset : {std::size_t{0x18}, std::size_t{0}}) {
    std::uint64_t data = 0;
    std::memcpy(&data, static_cast<std::byte *>(record) + offset, sizeof(data));
    if (data == 0) continue;
    Store(record, offset + 12, std::int32_t{0});
    Store(record, offset, std::uint64_t{0});
    Store(record, offset + 8, std::int32_t{0});
  }
  return kOpaqueRax;
}
void ResetOwnedRecord(std::uintptr_t image) {
  g_owned_slots.fill(std::byte{}); g_original_calls = 0;
  Store(g_owned_slots.data(), 4, std::uint8_t{2});
  Store(g_owned_slots.data(), 0x10, reinterpret_cast<std::uintptr_t>(g_owned_army_ids.data()));
  Store(g_owned_slots.data(), 0x18, std::int32_t{8});
  Store(g_owned_slots.data(), 0x1C, std::int32_t{3});
  Store(g_owned_slots.data(), 0x20, image + 0x54E0570);
  Store(g_owned_slots.data(), 0x28, std::uint64_t{0});
  Store(g_owned_slots.data(), 0x30, std::int32_t{91});
  Store(g_owned_slots.data(), 0x34, std::int32_t{17});
  // This unconsumed null-vector allocator is deliberately noncanonical.
  Store(g_owned_slots.data(), 0x38, image + 0x123);
  Store(g_owned_manager, 0x178, reinterpret_cast<std::uintptr_t>(g_owned_slots.data()));
  Store(g_owned_manager, 0x180, std::int32_t{1});
}
} // namespace

// central33/37 call this once against their OWNED manager before the parent
// invocation. Default bindings use the real37TLS and shared13/33clock adapter.
void PrepareArmySiegeChildNaturalFocus12004(void *owned_manager) {
  using namespace xar::ck3_12004;
  g_owned_manager = owned_manager; g_block_post_capacity = false;
  Require(g_owned_manager != nullptr, "owned manager missing");
  auto binding = BindArmyAssaultGroupReleaseImage12004(0x140000000ULL, kExecutableSha256);
  binding.read_memory = &ReadOwned;
  Require(InitializeArmyAssaultGroupReleaseFixture12004(binding, &OwnedOriginal), "release fixture initialization failed");
  ResetOwnedRecord(binding.image_base);
}

// Must run INSIDE37b's genuine active extent, called by its owned original.
// No TLS, parent token, date or clock event is injected into production scope.
void RunArmySiegeChildNaturalFocus12004() {
  using namespace xar::ck3_12004;
  ArmyAssaultConsumerParent12004 parent;
  Require(CopyActiveArmyAssaultConsumerParent12004(parent), "real consumer parent inactive");
  Require(parent.exact_post_date_parent && parent.manager_identity == reinterpret_cast<std::uintptr_t>(g_owned_manager), "wrong natural parent manager");
  const auto returned = InvokeArmyAssaultGroupReleaseFixture12004(0x2A981AE, g_owned_slots.data() + 0x10);
  Require(returned == kOpaqueRax && g_original_calls == 1, "original RAX bits or call count changed");
  const auto captured = ReadArmyAssaultGroupReleaseObservations12004(42);
  Require(captured && captured->events.size() == 1, "actual pre Army membership not captured");
  const auto &e = captured->events[0];
  Require(e.same_parent_at_return && e.same_clock_thread_order == true, "parent/shared clock relation missing");
  Require(e.parent.entry_event.clock_identity == parent.entry_event.clock_identity &&
      e.parent.entry_event.sequence == parent.entry_event.sequence, "consumer stage identity changed");
  Require(e.parent.phase_entry_event.sequence == parent.phase_entry_event.sequence &&
      e.parent.date_raw == parent.date_raw && e.parent.absolute_day_raw == parent.absolute_day_raw, "outer phase/date provenance changed");
  Require(e.entry_event.sequence > parent.entry_event.sequence && e.returned_event.sequence > e.entry_event.sequence, "child event order wrong");
  Require(e.capture_failure_flags == (xar::game::assault_release_capture_payload_before |
      xar::game::assault_release_capture_payload_after) && e.physical_slot == 0, "null-positive payload partial flags wrong");
  Require(e.armies_before.payload_count == 3 && e.armies_before.payload_complete &&
      e.armies_before.raw_full_ids_u32[0] == 42 && e.armies_before.raw_full_ids_u32[1] == UINT32_MAX &&
      e.armies_before.raw_full_ids_u32[2] == 42, "raw duplicate DWORD membership changed");
  Require(e.armies_after.data_address == 0 && e.armies_after.count_raw_i32 == 0 && e.armies_after.capacity_raw_i32 == 0,
      "nonnull Army header postimage missing");
  Require(e.arrgs_before.data_address == 0 && e.arrgs_after.count_raw_i32 == 17 && e.arrgs_after.capacity_raw_i32 == 91,
      "null branch raw fields were invented/cleared");
  Require(e.control_at_record_return == 2 && e.occupied_count_at_record_return == 1,
      "caller bookkeeping claimed before hook returns");
  Require(!captured->observer_installed && !captured->current_session_guard, "fixture gained live install credit");
  Require(ReadArmyAssaultGroupReleaseObservations12004(UINT32_MAX)->events.size() == 1, "raw full ID high bits lost");
  Require(ReadArmyAssaultGroupReleaseObservations12004(7)->events.empty(), "later query invented Army membership");
  std::string json;
  xar::game::AppendArmyAssaultGroupReleaseObservations12004(json, *captured);
  Require(json.find("after_record_return_before_caller_bookkeeping") != std::string::npos &&
      json.find("\"actual\":false") != std::string::npos, "wire boundary/fixture guard absent");

  // A different caller still executes original once, with no child event.
  ResetOwnedRecord(0x140000000ULL);
  const auto ignored_return = InvokeArmyAssaultGroupReleaseFixture12004(0x2A9FE76, g_owned_slots.data() + 0x10);
  Require(ignored_return == kOpaqueRax && g_original_calls == 1 &&
      ReadArmyAssaultGroupReleaseObservations12004(42)->latest_sequence == 1, "other caller labeled assault cleanup");

  // A reached noncanonical nonnull receiver forwards once and remains outside
  // this source-bound canonical observer's event set.
  ResetOwnedRecord(0x140000000ULL);
  Store(g_owned_slots.data(), 0x20, std::uintptr_t{0x140000123ULL});
  Require(InvokeArmyAssaultGroupReleaseFixture12004(0x2A981AE, g_owned_slots.data() + 0x10) == kOpaqueRax && g_original_calls == 1,
      "noncanonical original forwarding changed");
  const auto ignored = ReadArmyAssaultGroupReleaseObservations12004(42);
  Require(ignored->latest_sequence == 1 && ignored->ignored_noncanonical_receivers == 1, "noncanonical receiver acquired event credit");

  // A genuine return with one failed post-header read is retained as partial,
  // using the captured pre-membership. No earlier buffer is reread after free.
  ResetOwnedRecord(0x140000000ULL); g_block_post_capacity = true;
  Require(InvokeArmyAssaultGroupReleaseFixture12004(0x2A981AE, g_owned_slots.data() + 0x10) == kOpaqueRax && g_original_calls == 1,
      "partial capture altered original execution");
  const auto partial = ReadArmyAssaultGroupReleaseObservations12004(42);
  Require(partial->events.size() == 2 && !partial->events.back().armies_after.capacity_raw_i32 &&
      (partial->events.back().capture_failure_flags & xar::game::assault_release_capture_header_after) != 0,
      "failed post read filled from expected postimage");
  g_block_post_capacity = false;
  // Owned fake caller bookkeeping executes after producer return, permitting
  //37b's natural consumer-return capture to observe this separate later stage.
  Store(g_owned_slots.data(), 4, std::uint8_t{0});
  Store(g_owned_manager, 0x180, std::int32_t{0});
}

void VerifyArmySiegeChildNaturalFocus12004() {
  using namespace xar::ck3_12004;
  ArmyAssaultConsumerParent12004 parent;
  Require(!CopyActiveArmyAssaultConsumerParent12004(parent), "consumer TLS survived original return");
  const auto before = ReadArmyAssaultGroupReleaseObservations12004(42)->latest_sequence;
  ResetOwnedRecord(0x140000000ULL);
  Require(InvokeArmyAssaultGroupReleaseFixture12004(0x2A981AE, g_owned_slots.data() + 0x10) == kOpaqueRax && g_original_calls == 1,
      "out-of-parent forwarding changed");
  Require(ReadArmyAssaultGroupReleaseObservations12004(42)->latest_sequence == before, "inactive parent manufactured an event");
}
