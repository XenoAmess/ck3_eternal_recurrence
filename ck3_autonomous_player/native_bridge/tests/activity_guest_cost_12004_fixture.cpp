#include "xar_bridge/ck3_12002_activity_feast_costs.hpp"
#include "xar_bridge/ck3_12002_feast_guests_abi.hpp"
#include "xar_bridge/activity_stage5_feast_full_cost_v1.hpp"
#include "xar_bridge/activity_feast_guest_rule_toggle_v1.hpp"
#include "xar_bridge/ck3_12004_gift_opinion.hpp"

#include <windows.h>

#include <array>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string_view>
#include <unordered_map>

// One new migration fixture. It uses caller-owned memory and code only;
// it neither loads a game image nor contacts a CK3 process.
namespace {
using namespace xar::bridge;
constexpr std::string_view kSha =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
constexpr std::uintptr_t kRoot = 0x10000000;
constexpr std::uintptr_t kIdler = 0x10001000;
constexpr std::uintptr_t kGfx = 0x10002000;
constexpr std::uintptr_t kHandler = 0x10003000;
constexpr std::uintptr_t kPlanner = 0x10004000;
constexpr std::uintptr_t kWidget = 0x10005000;
constexpr std::uintptr_t kType = 0x10007000;
constexpr std::uintptr_t kStorage = 0x10008000;
constexpr std::uintptr_t kSlots = 0x10009000;
constexpr std::uintptr_t kActor = 0x1000A000;
constexpr std::uintptr_t kExtension = 0x1000B000;
constexpr std::uintptr_t kDatabase = 0x1000C000;
constexpr std::uintptr_t kDefinition = 0x1000D000;
constexpr std::uintptr_t kRules = 0x1000E000;
constexpr std::uintptr_t kActiveRules = 0x1000F000;
constexpr std::uintptr_t kWindow = 0x10010000;
constexpr std::int32_t kActorId = 29829;
constexpr std::array<std::int64_t, 4> kNamedCosts{18500000, 0, -100000, 3500000};
constexpr std::array<std::uint32_t, 4> kIndices{0, 3, 5, 8};

bool Fail(const char *label) {
  std::fprintf(stderr, "Activity guest/cost actual4 fixture: %s\n", label);
  return false;
}

struct ShortString {
  char data[16]{};
  std::uint64_t length = 0;
  std::uint64_t capacity = 15;
};

// Marker lookup and configured lookup remain separate, like the native ABI.
std::int64_t *__fastcall NamedCostLeaf(
    std::int64_t *out, const void *breakdown, const ShortString *key) {
  const std::string_view name(key->data, static_cast<std::size_t>(key->length));
  std::size_t ordinal = 0;
  for (; ordinal < kActivityFeastCostKeysV1.size(); ++ordinal)
    if (name == kActivityFeastCostKeysV1[ordinal]) break;
  if (ordinal == kActivityFeastCostKeysV1.size()) return nullptr;
  *out = reinterpret_cast<std::uintptr_t>(breakdown) == kPlanner + 0x1B10
      ? kNamedCosts[ordinal]
      : static_cast<const std::int64_t *>(breakdown)[kIndices[ordinal]];
  return out;
}

std::int64_t *__fastcall JoinLeaf(std::int64_t *out, void *planner, void *guest) {
  if (reinterpret_cast<std::uintptr_t>(planner) != kPlanner ||
      reinterpret_cast<std::uintptr_t>(guest) != kActor) return nullptr;
  *out = -200000; // Signed final native result, not a proxy or clamp.
  return out;
}
void *__fastcall ActivityLeaf(void *planner) {
  return reinterpret_cast<std::uintptr_t>(planner) == kPlanner
      ? reinterpret_cast<void *>(0x10020000) : nullptr;
}
std::int32_t __fastcall TravelLeaf(void *guest, void *destination) {
  return reinterpret_cast<std::uintptr_t>(guest) == kActor &&
      reinterpret_cast<std::uintptr_t>(destination) == kType ? 27 : INT32_MAX;
}

struct Fixture {
  std::unordered_map<std::uintptr_t, std::uint8_t> bytes{};
  ActivityPlannerDiagFrameV1 frame{14, 53224008, kActorId, true, true, true, true};
  ActivityCostSlot12ObserverV1 observer{};
  std::uintptr_t base = 0;
  bool active = false;
  int toggles = 0;

  Fixture() {
    // Reserve address space; only four callback pages are committed.
    base = reinterpret_cast<std::uintptr_t>(VirtualAlloc(
        nullptr, 0x4000000, MEM_RESERVE, PAGE_NOACCESS));
  }
  ~Fixture() {
    if (base != 0) VirtualFree(reinterpret_cast<void *>(base), 0, MEM_RELEASE);
  }

  template <typename T> void Put(std::uintptr_t address, const T &value) {
    const auto *source = reinterpret_cast<const std::uint8_t *>(&value);
    for (std::size_t i = 0; i < sizeof(value); ++i) bytes[address + i] = source[i];
  }
  void Fill(std::uintptr_t address, std::size_t count) {
    for (std::size_t i = 0; i < count; ++i) bytes[address + i] = 0;
  }
  void Key(std::uintptr_t object, std::string_view key) {
    for (std::size_t i = 0; i < key.size(); ++i)
      Put(object + 0x18 + i, static_cast<std::uint8_t>(key[i]));
    Put(object + 0x28, static_cast<std::uint64_t>(key.size()));
    Put(object + 0x30, std::uint64_t{15});
  }
  std::uintptr_t M(std::uintptr_t old_rva) const {
    return base + Activity12004RvaV1(kSha, old_rva);
  }
  bool Thunk(std::uintptr_t actual4_rva, std::uintptr_t callback) const {
    const auto address = base + actual4_rva;
    const auto page = address & ~std::uintptr_t{0xFFF};
    if (VirtualAlloc(reinterpret_cast<void *>(page), 0x1000, MEM_COMMIT,
                     PAGE_EXECUTE_READWRITE) == nullptr) return false;
    std::array<std::uint8_t, 12> code{0x48, 0xB8};
    std::memcpy(code.data() + 2, &callback, sizeof(callback));
    code[10] = 0xFF;
    code[11] = 0xE0;
    std::memcpy(reinterpret_cast<void *>(address), code.data(), code.size());
    return FlushInstructionCache(GetCurrentProcess(),
        reinterpret_cast<const void *>(address), code.size()) != 0;
  }

  static bool Read(void *opaque, std::uintptr_t address, void *out,
                   std::size_t count) noexcept {
    const auto &self = *static_cast<Fixture *>(opaque);
    auto *destination = static_cast<std::uint8_t *>(out);
    for (std::size_t i = 0; i < count; ++i) {
      const auto found = self.bytes.find(address + i);
      if (found == self.bytes.end()) return false;
      destination[i] = found->second;
    }
    return true;
  }
  static bool Frame(void *opaque, ActivityPlannerDiagFrameV1 &out) noexcept {
    out = static_cast<Fixture *>(opaque)->frame;
    return true;
  }
  static bool CostFrame(void *opaque, ActivityCostSlot12FrameV1 &out) noexcept {
    const auto &frame = static_cast<Fixture *>(opaque)->frame;
    out = {static_cast<std::int32_t>(frame.date_raw), frame.actor_character_id,
           GetCurrentThreadId(), frame.paused};
    return true;
  }
  static std::uintptr_t Cast(void *opaque, std::uintptr_t source,
      std::uintptr_t from, std::uintptr_t to) noexcept {
    const auto &self = *static_cast<Fixture *>(opaque);
    return source == kIdler && from == self.M(0x5514438) && to == self.M(0x5514460)
        ? kGfx : 0;
  }
  static bool Visible(void *opaque, std::uintptr_t planner,
      std::uintptr_t entry, bool &out) noexcept {
    const auto &self = *static_cast<Fixture *>(opaque);
    out = planner == kPlanner && entry == self.M(0x21603A0);
    return out;
  }

  void Populate() {
    Put(M(0x11B2885),
        std::array<std::uint8_t, 8>{0x49,0x89,0xB4,0x24,0xA0,0,0,0});
    Put(M(0x21603AA), std::array<std::uint8_t, 4>{0x48,0x8B,0x59,0x60});
    Put(M(0x11B8693),
        std::array<std::uint8_t, 7>{0x48,0x63,0x81,0xE8,0x1A,0,0});
    Put(M(0x45325C8), M(0x11B2E30));
    Put(M(0x45325C8) + 7 * 8, M(0x21603A0));
    Put(M(0x45325C8) + 11 * 8, M(0xB1F0A0));
    Put(M(0x45325C8) + 12 * 8, base + 0x11B5B10);
    Put(M(0x45326A0), M(0x11D3404));
    // Literal addresses/bytes are the frozen actual4 consumer operands.
    Put(base + 0x310ADF0,
        std::array<std::uint8_t, 13>{0x48,0x89,0x5C,0x24,0x18,0x56,0x57,
                                    0x41,0x56,0x48,0x83,0xEC,0x30});
    Put(base + 0x310AEC5, std::array<std::uint8_t, 4>{0x49,0x8B,0x0C,0xC6});
    Put(base + 0xC86146, std::array<std::uint8_t, 7>{0x48,0x8B,0x80,0,1,0,0});
    Put(base + 0x11BA6B0,
        std::array<std::uint8_t, 14>{0x48,0x89,0x5C,0x24,0x20,0x55,0x56,
                                    0x57,0x41,0x54,0x41,0x55,0x41,0x56});
    Put(base + 0x11B5B3A, std::array<std::uint8_t, 5>{0xE8,0x71,0x4B,0,0});
    Put(M(0x5C6A520), kRoot);
    Put(kRoot + 0x10, kIdler);
    Put(kGfx, M(0x44BC408));
    Put(kGfx + 0x88, kHandler);
    Put(kHandler, M(0x44BA890));
    Put(M(0x54DBC00), kActorId);
    Put(M(0x5C67568), kStorage);
    Put(M(0x5C67570), std::uintptr_t{0});
    Put(kStorage + 0x20, kSlots);
    Put(kStorage + 0x2C, std::int32_t{40000});
    Put(kSlots + static_cast<std::size_t>(kActorId) * 16 + 8, kActor);
    Put(kActor + 0x18, kActorId);
    Put(kActor + 0x1B0, kExtension);
    Put(kExtension + 0x100, std::int64_t{134000000});
    Put(kHandler + 0x3C0, kPlanner);
    Put(kHandler + 0x3D8, std::uintptr_t{0});
    Fill(kPlanner + 0x1500, 0x1B10 - 0x1500);
    Put(kPlanner, M(0x45325C8));
    Put(kPlanner + 0x10, M(0x45326A0));
    Put(kPlanner + 0xA0, kHandler);
    Put(kPlanner + 0x60, kWidget);
    Put(kPlanner + 0x1500, kType);
    Put(kPlanner + 0x1AE8, std::int32_t{5});
    for (std::size_t i = 0; i < 10; ++i)
      Put(kPlanner + 0x1B10 + 0x50 + i * 0x90 + 0x78,
          std::int64_t{i == 0 ? 99900000 : 0});
    Put(kType, M(0x48BFE50));
    Key(kType, "activity_feast");
    observer.environment = {true, true, kSha, base, this, &Read, &CostFrame};
  }

  static ActivityPlannerDiagResultV1 RuleDiag(
      void *opaque, const ActivityPlannerDiagFrameV1 &expected) noexcept {
    const auto &self = *static_cast<Fixture *>(opaque);
    ActivityPlannerDiagResultV1 out{};
    out.frame = self.frame;
    if (expected != self.frame) return out;
    out.status = ActivityPlannerDiagStatusV1::observed;
    out.value.planner_present = true;
    out.value.widget_attached = true;
    out.value.widget_visible = true;
    out.value.stage = 5;
    out.value.host_view_activity_key_known = true;
    constexpr char key[] = "activity_feast";
    std::memcpy(out.value.host_view_activity_key.data(), key, sizeof(key) - 1);
    out.value.host_view_activity_key_size = sizeof(key) - 1;
    return out;
  }
  static bool Capture(void *opaque, const ActivityPlannerDiagFrameV1 &expected,
                      ActivityCostSlot12CaptureV1 &out) noexcept {
    const auto &self = *static_cast<Fixture *>(opaque);
    if (self.frame != expected) return false;
    out = self.observer.latest;
    return out.sequence != 0;
  }
  static std::uint32_t Hash(void *, std::uintptr_t, std::string_view) noexcept {
    return 0x1234;
  }
  static std::uintptr_t Lookup(void *, std::uintptr_t, std::uint32_t hash) noexcept {
    return hash == 0x1234 ? kDefinition : 0;
  }
  static bool Active(void *opaque, std::uintptr_t, std::uintptr_t,
                     std::uintptr_t, bool &out) noexcept {
    out = static_cast<Fixture *>(opaque)->active;
    return true;
  }
  static bool Toggle(void *opaque, std::uintptr_t, std::uintptr_t,
                     std::uintptr_t) noexcept {
    auto &self = *static_cast<Fixture *>(opaque);
    ++self.toggles;
    self.active = true;
    self.Put(kActiveRules, kDefinition);
    self.Put(kPlanner + 0x1A5C, std::int32_t{1});
    return true;
  }
  void PopulateRule() {
    Put(base + 0x3F7E220,
        std::array<std::uint8_t, 8>{0x89,0x4C,0x24,0x08,0x53,0x48,0x83,0xEC});
    Put(base + 0x3057BA0,
        std::array<std::uint8_t, 8>{0x48,0x83,0xEC,0x38,0x48,0x8B,0x05,0x3D});
    Put(base + 0x305A260,
        std::array<std::uint8_t, 8>{0x48,0x89,0x5C,0x24,0x08,0x45,0x33,0xC0});
    Put(base + 0x165A9B0,
        std::array<std::uint8_t, 8>{0x40,0x57,0x41,0x55,0x48,0x83,0xEC,0x38});
    Put(base + 0x165AB70,
        std::array<std::uint8_t, 8>{0x48,0x89,0x5C,0x24,0x08,0x48,0x89,0x74});
    Put(base + 0x5D33EE8, kDatabase);
    Put(base + 0x5D34048, std::uintptr_t{0});
    Put(kDatabase, base + 0x48B2F30);
    Put(kDatabase + 0x38, base + 0x48B2ED0);
    Put(kHandler + 0x3F0, kWindow);
    Put(kPlanner + 0x1508, kActorId);
    Put(kPlanner + 0x1A50, kActiveRules);
    Put(kPlanner + 0x1A5C, std::int32_t{0});
    Put(kPlanner + 0x15C8, std::uintptr_t{0});
    Put(kPlanner + 0x15D4, std::int32_t{0});
    Put(kWindow, M(0x457B1A0));
    Put(kWindow + 0xD0, kPlanner);
    Put(kWindow + 0xC8, std::int32_t{-1});
    Put(kType + 0xBC8, kRules);
    Put(kType + 0xBD4, std::int32_t{1});
    Put(kRules, kDefinition);
    Put(kRules + 8, std::uint32_t{1});
  }
};

// Catches a wrong address selection as a fixture failure, not a process crash.
bool GuestNativeLeaves(std::uintptr_t base) noexcept {
  std::string_view sha = kSha;
  std::int64_t join = 0;
  std::int32_t travel = 0;
  __try {
    return InvokeActivityFeastNativePlannerGuestJoin12002V1(
               &sha, base, kPlanner, kActor, join) && join == -200000 &&
           InvokeActivityFeastNativePlannerActivity12002V1(
               &sha, base, kPlanner) == 0x10020000 &&
           InvokeActivityFeastNativeTravelDays12002V1(
               &sha, base, kActor, kType, travel) && travel == 27;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
}

struct OpinionFixture {
  static constexpr std::uint32_t recipient_id = 0x01000001;
  static constexpr std::uint32_t actor_id = 0x02000002;
  std::array<std::byte, 0x40> storage{};
  std::array<std::byte, 3 * 16> slots{};
  std::array<std::byte, 0x20> recipient{};
  std::array<std::byte, 0x20> actor{};
  void *storage_pointer = storage.data();
  int calls = 0;
  bool wrong_direction = false;
  bool unstable_value = false;
  bool replace_full_id = false;

  template <typename T, std::size_t N>
  static void Store(std::array<std::byte, N> &bytes, std::size_t offset,
                    const T &value) {
    std::memcpy(bytes.data() + offset, &value, sizeof(value));
  }
  OpinionFixture() {
    Store(storage, 0x20, static_cast<void *>(slots.data()));
    Store(storage, 0x2C, std::int32_t{3});
    Store(slots, 16 + 8, static_cast<void *>(recipient.data()));
    Store(slots, 32 + 8, static_cast<void *>(actor.data()));
    Store(recipient, 0x18, recipient_id);
    Store(actor, 0x18, actor_id);
  }
};
OpinionFixture *opinion_fixture = nullptr;

std::int32_t OpinionLeaf(void *owner, void *toward) {
  auto &f = *opinion_fixture;
  ++f.calls;
  if (owner != f.recipient.data() || toward != f.actor.data()) {
    f.wrong_direction = true;
    return 777;
  }
  if (f.replace_full_id)
    OpinionFixture::Store(f.recipient, 0x18, std::uint32_t{0x03000001});
  return f.unstable_value && f.calls == 2 ? -26 : -27;
}

bool ActualOpinionBindingsAndRead(std::uintptr_t base) {
  const auto native = xar::ck3_12004::BindGiftOpinionImage(base, kSha);
  const auto old = xar::ck3_12004::BindGiftOpinionImage(base,
      xar::ck3_12002::kExecutableSha256);
  if (!native.enabled || !native.core.enabled || old.enabled ||
      xar::ck3_12004::BindGiftOpinionImage(0, kSha).enabled ||
      reinterpret_cast<std::uintptr_t>(native.core.character_storage_slot) !=
          base + 0x5C67568 ||
      reinterpret_cast<std::uintptr_t>(native.core.get_local_player) !=
          base + 0x383E290 ||
      reinterpret_cast<std::uintptr_t>(native.read_opinion) != base + 0x28BC470 ||
      reinterpret_cast<std::uintptr_t>(native.lookup_modifier) != base + 0x25A2EE0 ||
      reinterpret_cast<std::uintptr_t>(native.find_group) != base + 0x2949A80 ||
      reinterpret_cast<std::uintptr_t>(native.sum_modifier) != base + 0x2596290 ||
      reinterpret_cast<std::uintptr_t>(native.modifier_database_slot) != base + 0x5D207E0 ||
      native.modifier_primary_vtable != base + 0x48C5380 ||
      native.modifier_secondary_vtable != base + 0x48C5348 ||
      native.active_opinion_vtable != base + 0x473DE18 ||
      native.temporary_opinion_vtable != base + 0x473DDE0)
    return false;

  OpinionFixture f;
  opinion_fixture = &f;
  auto bindings = native;
  bindings.core.character_storage_slot = &f.storage_pointer;
  bindings.read_opinion = &OpinionLeaf;
  std::int32_t value = 123;
  if (!xar::ck3_12004::ReadCharacterOpinion(bindings,
          OpinionFixture::recipient_id, OpinionFixture::actor_id, value) ||
      value != -27 || f.calls != 2 || f.wrong_direction)
    return false;
  f.calls = 0;
  f.unstable_value = true;
  if (xar::ck3_12004::ReadCharacterOpinion(bindings,
          OpinionFixture::recipient_id, OpinionFixture::actor_id, value) ||
      value != 0 || f.calls != 2)
    return false;
  f.calls = 0;
  f.unstable_value = false;
  f.replace_full_id = true;
  if (xar::ck3_12004::ReadCharacterOpinion(bindings,
          OpinionFixture::recipient_id, OpinionFixture::actor_id, value) ||
      value != 0 || f.calls != 2)
    return false;
  f.calls = 0;
  if (xar::ck3_12004::ReadCharacterOpinion(bindings,
          OpinionFixture::recipient_id, OpinionFixture::actor_id, value) ||
      f.calls != 0)
    return false;
  opinion_fixture = nullptr;
  return true;
}
} // namespace

bool RunActivityGuestCost12004Fixture() {
  Fixture f;
  if (f.base == 0) return Fail("fixture address space unavailable");
  if (!f.Thunk(0x310ADF0, reinterpret_cast<std::uintptr_t>(&NamedCostLeaf)) ||
      !f.Thunk(0x11B8330, reinterpret_cast<std::uintptr_t>(&JoinLeaf)) ||
      !f.Thunk(0x11D8EA0, reinterpret_cast<std::uintptr_t>(&ActivityLeaf)) ||
      !f.Thunk(0x2BBADC0, reinterpret_cast<std::uintptr_t>(&TravelLeaf)))
    return Fail("fixture callback pages unavailable");
  f.Populate();
  if (!VerifyActivityCostSlot12ExactAbiV1(f.observer.environment))
    return Fail("actual4 passive ABI");
  ActivityStage5FeastFullCostEnvironmentV1 cost{};
  cost.enabled = true;
  cost.gold.enabled = true;
  cost.gold.diagnostic = {true, kSha, f.base, &f, &Fixture::Read,
      &Fixture::Frame, &Fixture::Cast, &Fixture::Visible};
  cost.gold.passive_cost = &f.observer;
  // No named override: production default forwards SHA to the native wrapper.
  const auto absent = ReadActivityStage5FeastFullCostV1(cost, f.frame);
  if (absent.gold_gate_status != ActivityStage5GoldCostStatusV1::no_normal_refresh)
    return Fail("no native names without actual normal refresh");
  if (RecordActivityCostSlot12NormalReturnV1(f.observer,
          f.base + 0x11B5B5F, kPlanner))
    return Fail("historical .2 return accepted by actual4 observer");
  if (!RecordActivityCostSlot12NormalReturnV1(f.observer,
          f.base + 0x11B5B3F, kPlanner))
    return Fail("actual4 normal-return capture");
  const auto result = ReadActivityStage5FeastFullCostV1(cost, f.frame);
  if (result.status != ActivityStage5FeastFullCostStatusV1::observed ||
      result.configured_cost_raw != kNamedCosts || result.resource_indices != kIndices ||
      result.actor_gold_raw != 134000000 || result.scale != 100000 ||
      result.configured_cost_raw[0] == f.observer.latest.raw_aggregate[0])
    return Fail("native named costs, signed zero/negative and current actor Gold");
  if (!GuestNativeLeaves(f.base)) return Fail("actual SHA guest callback forwarding");
  if (!ActualOpinionBindingsAndRead(f.base))
    return Fail("actual4 opinion binding, native direction and stable full identity");

  f.PopulateRule();
  ActivityFeastGuestRuleEnvironmentV1 rule{};
  rule.enabled = true;
  rule.diagnostic = cost.gold.diagnostic;
  rule.context = &f;
  rule.capture = &Fixture::Capture;
  rule.read_diagnostic = &Fixture::RuleDiag;
  rule.hash_key = &Fixture::Hash;
  rule.lookup_rule = &Fixture::Lookup;
  rule.read_active = &Fixture::Active;
  rule.toggle = &Fixture::Toggle;
  constexpr std::string_view key = "activity_invite_rule_vassals";
  const auto inactive = ReadActivityFeastGuestRuleV1(rule, f.frame, key);
  if (inactive.status != ActivityFeastGuestRuleStatusV1::observed_inactive ||
      inactive.invoked || inactive.native_key_hash != 0x1234 || f.toggles != 0)
    return Fail("actual4 rule source and nullable native missing sentinel");
  const auto activated = ActivateActivityFeastGuestRuleV1(rule, f.frame, key, true);
  if (activated.status != ActivityFeastGuestRuleStatusV1::activated ||
      !activated.invoked || !activated.active || activated.active_rule_count != 1 ||
      f.toggles != 1)
    return Fail("actual4 rule independent vector/getter postcondition");
  const auto active = ActivateActivityFeastGuestRuleV1(rule, f.frame, key, true);
  if (active.status != ActivityFeastGuestRuleStatusV1::observed_active ||
      active.invoked || f.toggles != 1)
    return Fail("already active native rule is not toggled twice");
  return true;
}
