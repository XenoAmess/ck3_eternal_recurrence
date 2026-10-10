#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12004_activity_migration_v1.hpp"
#include "xar_bridge/ck3_12002_feast_guests_abi.hpp"
#include "xar_bridge/activity_stage5_feast_full_cost_v1.hpp"
#include "xar_bridge/activity_stage5_feast_guest_join_v1.hpp"
#include "xar_bridge/activity_stage5_canstart_read_v1.hpp"
#include "ck3_12002_activity_feast_cost_private_transport_v1.hpp"
#include "activity_feast_stage5_start_private_transport_v1.hpp"

#include <windows.h>
#include <array>
#include <cstring>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
using namespace xar::bridge;
constexpr std::uintptr_t kBase = 0x180000000ULL;
constexpr std::uintptr_t kRoot = 0x700010000ULL, kIdler = 0x700020000ULL;
constexpr std::uintptr_t kGfx = 0x700030000ULL, kHandler = 0x700040000ULL;
constexpr std::uintptr_t kPlanner = 0x700050000ULL, kType = 0x700060000ULL;
constexpr std::uintptr_t kStorage = 0x700070000ULL, kSlots = 0x700080000ULL;
constexpr std::uintptr_t kActor = 0x700090000ULL, kGuest = 0x7000A0000ULL;
constexpr std::uintptr_t kGold = 0x7000B0000ULL, kWorld = 0x7000C0000ULL;
constexpr std::uintptr_t kProvinceTable = 0x7000D0000ULL, kLocation = 0x7000E0000ULL;
constexpr std::uintptr_t kRows = 0x7000F0000ULL, kCache = 0x700100000ULL;
constexpr std::uintptr_t kActivity = 0x700110000ULL, kDestination = 0x700120000ULL;
constexpr std::uintptr_t kProvinces = 0x700130000ULL, kSelectedDestination = 0x700140000ULL;
constexpr std::uint32_t kActorId = 0x01000001, kGuestId = 0x01000002;
constexpr std::int64_t kActorGold = 123456789;
constexpr std::array<std::int64_t, 4> kCosts{1200000, -250000, 0, 700000};

void Require(bool value, const char *message) {
  if (!value) throw std::runtime_error(message);
}

struct Fixture {
  std::map<std::uintptr_t, unsigned char> memory{};
  std::vector<std::pair<std::uintptr_t, std::size_t>> reads{};
  ActivityPlannerDiagFrameV1 frame{74, 43800000, static_cast<std::int32_t>(kActorId),
                                  true, true, true, true};
  ActivityCostSlot12ObserverV1 passive{};
  std::uintptr_t unreadable = 0;
  std::uintptr_t last_destination = 0;
  std::uint32_t destroy_calls = 0;
  xar::ck3_11906::ActivityStage5FailureDisplayV1 display{};

  void Bytes(std::uintptr_t address, const void *data, std::size_t size) {
    auto *bytes = static_cast<const unsigned char *>(data);
    for (std::size_t i = 0; i < size; ++i) memory[address + i] = bytes[i];
  }
  template<class T> void Put(std::uintptr_t address, const T &value) {
    Bytes(address, &value, sizeof(value));
  }
  void Zero(std::uintptr_t address, std::size_t size) {
    for (std::size_t i = 0; i < size; ++i) memory[address + i] = 0;
  }
  void Code(std::uintptr_t rva, std::initializer_list<unsigned char> bytes) {
    Bytes(kBase + rva, bytes.begin(), bytes.size());
  }
  std::size_t ReadCount(std::uintptr_t address, std::size_t width) const {
    std::size_t count = 0;
    for (const auto &read : reads) if (read.first == address && read.second == width) ++count;
    return count;
  }
  Fixture();
  ActivityPlannerDiagEnvironmentV1 Diagnostic();
  ActivityStage5FeastFullCostResultV1 Cost();
  ActivityFeastGuestJoinResultV1 Guests();
  ActivityStage5CanStartResultV1 CanStart();
  void Record() {
    Require(RecordActivityCostSlot12NormalReturnV1(passive, kBase + 0x11B5B3F, kPlanner),
            "new fixture normal-return capture unavailable");
  }
};

bool Read(void *opaque, std::uintptr_t address, void *output, std::size_t size) noexcept {
  auto &f = *static_cast<Fixture *>(opaque);
  try {
    f.reads.emplace_back(address, size);
    if (address == f.unreadable || !output || !size) return false;
    auto *bytes = static_cast<unsigned char *>(output);
    for (std::size_t i = 0; i < size; ++i) {
      const auto found = f.memory.find(address + i);
      if (found == f.memory.end()) return false;
      bytes[i] = found->second;
    }
    return true;
  } catch (...) { return false; }
}
bool Frame(void *opaque, ActivityPlannerDiagFrameV1 &value) noexcept {
  value = static_cast<Fixture *>(opaque)->frame; return true;
}
bool CostFrame(void *opaque, ActivityCostSlot12FrameV1 &value) noexcept {
  const auto &f = *static_cast<Fixture *>(opaque);
  value = {static_cast<std::int32_t>(f.frame.date_raw), f.frame.actor_character_id,
           GetCurrentThreadId(), true}; return true;
}
std::uintptr_t Cast(void *, std::uintptr_t source, std::uintptr_t from,
                    std::uintptr_t to) noexcept {
  return source == kIdler && from == kBase + 0x5514438 && to == kBase + 0x5514460 ? kGfx : 0;
}
bool Visible(void *, std::uintptr_t planner, std::uintptr_t entry, bool &value) noexcept {
  if (planner != kPlanner || entry != kBase + 0x2160380) return false;
  value = true; return true;
}
bool NamedCost(void *, std::uintptr_t base, std::uintptr_t breakdown,
               std::string_view key, std::uint32_t &index, std::int64_t &value) noexcept {
  if (base != kBase || breakdown != kPlanner + 0x1B10) return false;
  constexpr std::array<std::uint32_t, 4> indices{0, 2, 3, 4};
  for (std::size_t i = 0; i < kActivityFeastCostKeysV1.size(); ++i) {
    if (key == kActivityFeastCostKeysV1[i]) { index = indices[i]; value = kCosts[i]; return true; }
  }
  return false;
}
bool Join(void *, std::uintptr_t base, std::uintptr_t planner,
          std::uintptr_t character, std::int64_t &value) noexcept {
  if (base != kBase || planner != kPlanner || character != kGuest) return false;
  value = 150000; return true;
}
std::uintptr_t Activity(void *, std::uintptr_t base, std::uintptr_t planner) noexcept {
  return base == kBase && planner == kPlanner ? kActivity : 0;
}
bool Travel(void *opaque, std::uintptr_t base, std::uintptr_t character,
            std::uintptr_t destination, std::int32_t &days) noexcept {
  auto &f = *static_cast<Fixture *>(opaque);
  if (base != kBase || character != kGuest ||
      (destination != kDestination && destination != kSelectedDestination)) return false;
  f.last_destination = destination; days = 1; return true;
}

// Typed caller-owned callbacks exercise the existing display helper. No native
// executable function is invoked. The accepted address is literal source input.
struct OwnedDisplayString { char bytes[16]{}; std::uint64_t size = 0, capacity = 15; };
static_assert(sizeof(OwnedDisplayString) == 32);
thread_local Fixture *active_display_fixture = nullptr;
bool Denied(void *planner, void *string) {
  Require(reinterpret_cast<std::uintptr_t>(planner) == kPlanner && active_display_fixture,
          "wrong current CanStart fixture arguments");
  auto &value = *static_cast<OwnedDisplayString *>(string);
  std::memcpy(value.bytes, "cannot host", 11); value.size = 11; return false;
}
void Destroy(void *string) {
  Require(active_display_fixture != nullptr, "missing display fixture");
  ++active_display_fixture->destroy_calls;
  std::memset(string, 0xA5, sizeof(OwnedDisplayString));
}
bool Evaluate(void *opaque, std::uintptr_t planner, bool &allowed) noexcept {
  auto &f = *static_cast<Fixture *>(opaque);
  const auto rva = Activity12004RvaV1(xar::ck3_12004::kExecutableSha256, 0x856050);
  const auto destroy = kBase + rva == kBase + 0x856050 ? &Destroy : nullptr;
  active_display_fixture = &f;
  const bool ok = xar::ck3_11906::InvokeActivityStage5CanStartWithDisplayV1(
      reinterpret_cast<void *>(planner), &Denied, destroy, f.display);
  active_display_fixture = nullptr;
  if (ok) allowed = f.display.allowed;
  return ok;
}

Fixture::Fixture() {
  // These literal actual4 operands deliberately do not call the mapper.
  Code(0x11B2865, {0x49,0x89,0xB4,0x24,0xA0,0,0,0});
  Code(0x216038A, {0x48,0x8B,0x59,0x60});
  Code(0x11B8673, {0x48,0x63,0x81,0xE8,0x1A,0,0});
  Code(0x11B8650, {0x48,0x89,0x5C,0x24,0x10,0x48,0x89});
  Code(0x11B88C8, {0x48,0x8D,0x91,0x00,0x15,0,0});
  Code(0x310ADF0, {0x48,0x89,0x5C,0x24,0x18,0x56,0x57,0x41,0x56,0x48,0x83,0xEC,0x30});
  Code(0x310AEC5, {0x49,0x8B,0x0C,0xC6});
  Code(0xC86146, {0x48,0x8B,0x80,0,1,0,0});
  Code(0x11B5BC0, {0x48,0x8B,0x83,0xB0,0x16,0,0});
  Code(0x11B5C26, {0xE8,0x05,0x27,0,0});
  Code(0x11B5C38, {0x88,0x0C,0x07,0x48});
  Code(0x9DFF87, {0xE8,0x34,0xAE,0x1D,0x02});
  Code(0x9E002A, {0x48,0x89,0x4B,0x04});
  Put(kBase+0x45325D8, kBase+0x11B2E10);
  Put(kBase+0x45325D8+7*8, kBase+0x2160380);
  Put(kBase+0x45325D8+11*8, kBase+0xB1F0A0);
  Put(kBase+0x45325D8+12*8, kBase+0x11B5B10);
  Put(kBase+0x45326B0, kBase+0x11D33E4);
  Put(kBase+0x5C6A520, kRoot); Put(kRoot+0x10, kIdler);
  Put(kGfx, kBase+0x44BC418); Put(kGfx+0x88, kHandler);
  Put(kHandler, kBase+0x44BA8A0); Put(kHandler+0x3C0, kPlanner);
  Put(kHandler+0x3D8, std::uintptr_t{0});
  Put(kBase+0x54DBC00, kActorId);
  Put(kBase+0x5C67568, kStorage); Put(kBase+0x5C67570, std::uintptr_t{0x7FFFFFFFFULL});
  Put(kStorage+0x20, kSlots); Put(kStorage+0x2C, std::int32_t{3});
  Put(kSlots+0x10+8, kActor); Put(kSlots+0x20+8, kGuest);
  Put(kActor+0x18, kActorId); Put(kGuest+0x18, kGuestId);
  Put(kActor+0x1B0, kGold); Put(kGold+0x100, kActorGold);
  Zero(kPlanner+0x1500, 0x1B10-0x1500);
  Put(kPlanner, kBase+0x45325D8); Put(kPlanner+0x10, kBase+0x45326B0);
  Put(kPlanner+0x60, std::uintptr_t{0x700150000ULL}); Put(kPlanner+0xA0, kHandler);
  Put(kPlanner+0x1500, kType); Put(kPlanner+0x1508, static_cast<std::int32_t>(kActorId));
  Put(kPlanner+0x1520, static_cast<std::int32_t>(frame.date_raw+48));
  Put(kPlanner+0x15B0, kLocation); Put(kPlanner+0x15BC, std::int32_t{1});
  Put(kPlanner+0x16B0, kRows); Put(kPlanner+0x16BC, std::int32_t{1});
  Put(kPlanner+0x1A68, kCache); Put(kPlanner+0x1AE8, std::int32_t{5});
  Zero(kLocation, 0x38); Put(kLocation+8, std::int32_t{-1});
  Zero(kRows, 16); Put(kRows+8, static_cast<std::int32_t>(kGuestId));
  Put(kCache, std::uint8_t{1});
  Put(kType, kBase+0x48BFE60); Bytes(kType+0x18, "activity_feast", 14);
  Put(kType+0x28, std::uint64_t{14}); Put(kType+0x30, std::uint64_t{15});
  for(std::size_t i=0;i<10;++i) Put(kPlanner+0x1B10+0x50+i*0x90+0x78, std::int64_t{0});
  Put(kBase+0x5C68C50, kWorld); Put(kWorld+8, static_cast<std::int32_t>(frame.date_raw));
  Put(kWorld+0x9C, std::int32_t{900}); Put(kWorld+0xA0, kProvinceTable);
  Put(kProvinceTable+0x14C, std::int32_t{2}); Put(kProvinceTable+0x140, kProvinces);
  Put(kProvinces+8, kSelectedDestination);
  Put(kBase+0x5D1E390, kDestination);
  Put(kActivity+0x10, std::uintptr_t{0}); Put(kActivity+0x1C, std::int32_t{0});
  passive.environment = {true, false, xar::ck3_12004::kExecutableSha256, kBase, this, &Read, &CostFrame};
  passive.installed = true;
  Record();
  reads.clear();
}
ActivityPlannerDiagEnvironmentV1 Fixture::Diagnostic() {
  return {true, xar::ck3_12004::kExecutableSha256, kBase, this, &Read, &Frame, &Cast, &Visible};
}
ActivityStage5FeastFullCostResultV1 Fixture::Cost() {
  ActivityStage5FeastFullCostEnvironmentV1 env{};
  env.enabled=true; env.gold.enabled=true; env.gold.diagnostic=Diagnostic();
  env.gold.passive_cost=&passive; env.invoke_named_cost=&NamedCost; env.named_context=this;
  return ReadActivityStage5FeastFullCostV1(env,frame);
}
ActivityFeastGuestJoinResultV1 Fixture::Guests() {
  ActivityFeastGuestJoinEnvironmentV1 env{true,Diagnostic(),&passive,&Join,this,&Activity,&Travel,this};
  return ReadActivityFeastGuestJoinV1(env,frame);
}
ActivityStage5CanStartResultV1 Fixture::CanStart() {
  return ReadActivityStage5CanStartV1({Diagnostic(),&Evaluate},frame);
}

std::string CostWire(Fixture &f, const ActivityStage5FeastFullCostResultV1 &cost,
                     const ActivityStage5CanStartResultV1 &can_start) {
  xar::ck3_12002::ActivityStage5FeastFullCostPrivateQueryV1 query{};
  query.cost=cost; query.can_start=can_start; query.can_start_failure_display=f.display; query.completed=true;
  return xar::ck3_12002::SerializeActivityStage5FeastFullCostPrivateV1(query);
}
std::string GuestWire(Fixture &f, const ActivityStage5FeastFullCostResultV1 &cost,
                     const ActivityStage5CanStartResultV1 &can_start,
                     const ActivityFeastGuestJoinResultV1 &guests) {
  xar::ck3_11906::ActivityFeastStage5PrivateQueryV1 query{};
  query.completed=true;
  auto &input=query.inputs;
  input.frame={f.frame.revision,f.frame.date_raw,f.frame.actor_character_id,true,true,true,true};
  input.normal_cost_refresh_sequence=cost.normal_refresh_sequence;
  input.four_costs_observed=cost.status==ActivityStage5FeastFullCostStatusV1::observed;
  input.cost_resource_indices=cost.resource_indices; input.cost_raw=cost.configured_cost_raw;
  input.final_can_start_observed=can_start.status==ActivityStage5CanStartStatusV1::observed;
  input.final_can_start=can_start.final_can_start;
  // This narrow fixture provides no hosted/balance observation. The serializer
  // receives an explicit empty owned fixture extent, never live hosted credit.
  input.hosted_identities_observed=true; input.hosted_count=0; input.selected_guests=guests;
  query.guest_status=guests.status; query.selected_nonhost_count=guests.selected_nonhost_count;
  query.positive_join_count=guests.positive_join_count;
  query.timely_positive_join_count=guests.timely_positive_join_count;
  query.arrival_time_observed=guests.arrival_time_observed;
  query.guest_route_qualified=guests.status==ActivityFeastGuestJoinStatusV1::observed &&
      guests.selected_nonhost_count>0 && guests.timely_positive_join_count>0;
  return xar::ck3_11906::SerializeActivityFeastStage5PrivateV1(query);
}
} // namespace

// One new focused compound export; the caller owns main/output. No Game calls.
std::string RunActivityActualThreeBindingsConnected12004() {
  Fixture f;
  const auto cost=f.Cost(); const auto can_start=f.CanStart(); const auto guests=f.Guests();
  Require(cost.status==ActivityStage5FeastFullCostStatusV1::observed && cost.actor_gold_raw==kActorGold &&
          cost.configured_cost_raw==kCosts, "literal playedID does not reach existing fullcost reader");
  Require(f.ReadCount(kBase+0x54DBC00,4)>0 && f.ReadCount(kBase,4)==0,
          "playedID exact4-byte operand was not used");
  Require(can_start.status==ActivityStage5CanStartStatusV1::observed && !can_start.final_can_start &&
          f.destroy_calls==1 && f.display.size==11 &&
          std::memcmp(f.display.bytes.data(),"cannot host",11)==0,
          "source-bound destructor/lifetime/display propagation failed");
  Require(guests.status==ActivityFeastGuestJoinStatusV1::observed && guests.selected_nonhost_count==1 &&
          guests.timely_positive_join_count==1 && f.last_destination==kDestination &&
          f.ReadCount(kBase+0x5D1E390,8)>0 && f.ReadCount(kBase,8)==0,
          "literal fallback does not reach existing guest arrival callback");
  const auto cost_wire=CostWire(f,cost,can_start);
  const auto fallback_wire=GuestWire(f,cost,can_start,guests);
  Require(!cost_wire.empty()&&!fallback_wire.empty(),"existing private wire unavailable");

  Fixture mismatch;
  mismatch.Put(kBase+0x54DBC00,kActorId^0x02000000u);
  Require(mismatch.Cost().status!=ActivityStage5FeastFullCostStatusV1::observed &&
          mismatch.Guests().status!=ActivityFeastGuestJoinStatusV1::observed,
          "wrong played fullID was accepted");
  Fixture unread_played; unread_played.unreadable=kBase+0x54DBC00;
  Require(unread_played.Cost().status!=ActivityStage5FeastFullCostStatusV1::observed &&
          unread_played.Guests().status!=ActivityFeastGuestJoinStatusV1::observed,
          "unreadable playedID was accepted");
  Fixture generation; generation.Put(kActor+0x18,kActorId^0x02000000u);
  Require(generation.Cost().status!=ActivityStage5FeastFullCostStatusV1::observed,
          "same-index other-generation actor was accepted");

  Fixture unread_fallback; unread_fallback.unreadable=kBase+0x5D1E390;
  const auto unavailable_guests=unread_fallback.Guests();
  Require(unavailable_guests.status==ActivityFeastGuestJoinStatusV1::arrival_source_unavailable &&
          unread_fallback.last_destination==0,"unreadable fallback became observed");
  const auto unavailable_wire=GuestWire(unread_fallback,cost,can_start,unavailable_guests);
  Fixture null_fallback; null_fallback.Put(kBase+0x5D1E390,std::uintptr_t{0});
  Require(null_fallback.Guests().status==ActivityFeastGuestJoinStatusV1::arrival_source_unavailable &&
          null_fallback.last_destination==0,"null fallback became observed");
  Fixture selected; selected.Put(kLocation+8,std::int32_t{1}); selected.Record(); selected.reads.clear();
  selected.unreadable=kBase+0x5D1E390;
  const auto selected_guests=selected.Guests();
  Require(selected_guests.status==ActivityFeastGuestJoinStatusV1::observed &&
          selected.last_destination==kSelectedDestination && selected.ReadCount(kBase+0x5D1E390,8)==0,
          "selected province incorrectly depended on fallback");
  const auto selected_wire=GuestWire(selected,cost,can_start,selected_guests);
  Require(Activity12004RvaV1(xar::ck3_12004::kExecutableSha256,0x856051)==0,
          "unknown actual operand admitted");

  return "{\"fixture_schema\":\"activity-actual-three-bindings-connected-12004\","
    "\"owned_memory_only\":true,\"live_abi_credit\":false,\"native_checks\":10,"
    "\"cost\":"+cost_wire+",\"fallback_guest\":"+fallback_wire+
    ",\"unavailable_guest\":"+unavailable_wire+",\"selected_guest\":"+selected_wire+"}";
}
