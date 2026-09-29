#include "xar_bridge/activity_feast_guest_rule_toggle_v1.hpp"

#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <unordered_map>

using namespace xar::bridge;

namespace {

struct Fixture {
  static constexpr std::uintptr_t base = 0x100000000ULL;
  static constexpr std::uintptr_t owner = 0x200000000ULL;
  static constexpr std::uintptr_t planner = 0x200010000ULL;
  static constexpr std::uintptr_t window = 0x200020000ULL;
  static constexpr std::uintptr_t type = 0x200030000ULL;
  static constexpr std::uintptr_t database = 0x200040000ULL;
  static constexpr std::uintptr_t definition = 0x200050000ULL;
  static constexpr std::uintptr_t rows = 0x200060000ULL;
  static constexpr std::uintptr_t active_rows = 0x200070000ULL;
  std::unordered_map<std::uintptr_t, std::uint8_t> bytes{};
  ActivityPlannerDiagFrameV1 frame{7, 12345, 100, true, true, true, true};
  bool active = false;
  bool toggle_changes_vector = true;
  int toggles = 0;
  ActivityFeastGuestRuleEnvironmentV1 environment{};

  template <typename T> void Put(std::uintptr_t address, const T &value) {
    const auto *data = reinterpret_cast<const std::uint8_t *>(&value);
    for (std::size_t i = 0; i < sizeof(value); ++i) bytes[address + i] = data[i];
  }
  template <std::size_t N>
  void Put(std::uintptr_t address, const std::array<std::uint8_t, N> &value) {
    for (std::size_t i = 0; i < N; ++i) bytes[address + i] = value[i];
  }
  static bool Read(void *opaque, std::uintptr_t address, void *output,
                   std::size_t size) noexcept {
    auto &self = *static_cast<Fixture *>(opaque);
    auto *target = static_cast<std::uint8_t *>(output);
    for (std::size_t i = 0; i < size; ++i) {
      const auto found = self.bytes.find(address + i);
      if (found == self.bytes.end()) return false;
      target[i] = found->second;
    }
    return true;
  }
  static bool Frame(void *opaque, ActivityPlannerDiagFrameV1 &output) noexcept {
    output = static_cast<Fixture *>(opaque)->frame;
    return true;
  }
  static ActivityPlannerDiagResultV1 Diag(
      void *opaque, const ActivityPlannerDiagFrameV1 &expected) noexcept {
    ActivityPlannerDiagResultV1 result{};
    auto &self = *static_cast<Fixture *>(opaque);
    result.frame = self.frame;
    if (self.frame != expected) {
      result.status = ActivityPlannerDiagStatusV1::frame_changed;
      return result;
    }
    result.status = ActivityPlannerDiagStatusV1::observed;
    result.value.planner_present = true;
    result.value.widget_attached = true;
    result.value.widget_visible = true;
    result.value.stage = 5;
    result.value.host_view_activity_key_known = true;
    constexpr char key[] = "activity_feast";
    std::memcpy(result.value.host_view_activity_key.data(), key,
                sizeof(key) - 1);
    result.value.host_view_activity_key_size = sizeof(key) - 1;
    return result;
  }
  static bool Capture(void *opaque, const ActivityPlannerDiagFrameV1 &expected,
                      ActivityCostSlot12CaptureV1 &output) noexcept {
    auto &self = *static_cast<Fixture *>(opaque);
    if (expected != self.frame) return false;
    output.sequence = 1;
    output.frame.date_raw = static_cast<std::int32_t>(expected.date_raw);
    output.frame.actor_character_id = expected.actor_character_id;
    output.planner = planner;
    output.owner = owner;
    output.activity_type = type;
    output.planning_stage = 5;
    return true;
  }
  static std::uint32_t Hash(void *, std::uintptr_t, std::string_view) noexcept {
    return 0x1234;
  }
  static std::uintptr_t Lookup(void *, std::uintptr_t,
                               std::uint32_t hash) noexcept {
    return hash == 0x1234 ? definition : 0;
  }
  static bool Active(void *opaque, std::uintptr_t, std::uintptr_t,
                     std::uintptr_t, bool &output) noexcept {
    output = static_cast<Fixture *>(opaque)->active;
    return true;
  }
  static bool Toggle(void *opaque, std::uintptr_t, std::uintptr_t,
                     std::uintptr_t) noexcept {
    auto &self = *static_cast<Fixture *>(opaque);
    ++self.toggles;
    self.active = true;
    if (self.toggle_changes_vector) {
      self.Put(active_rows, definition);
      self.Put(planner + 0x1A24, std::int32_t{1});
    }
    return true;
  }
  Fixture() {
    Put(base + 0x3B8B000,
        std::array<std::uint8_t, 8>{0x89, 0x4C, 0x24, 0x08, 0x53, 0x48, 0x83, 0xEC});
    Put(base + 0x2C19210,
        std::array<std::uint8_t, 8>{0x48, 0x83, 0xEC, 0x38, 0x48, 0x8B, 0x05, 0xDD});
    Put(base + 0x2C1B800,
        std::array<std::uint8_t, 8>{0x48, 0x89, 0x5C, 0x24, 0x08, 0x45, 0x33, 0xC0});
    Put(base + 0x151C110,
        std::array<std::uint8_t, 8>{0x40, 0x57, 0x41, 0x57, 0x48, 0x83, 0xEC, 0x28});
    Put(base + 0x151C2B0,
        std::array<std::uint8_t, 8>{0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x74});
    Put(base + 0x4FE7EE0, std::uint32_t{100});
    Put(base + 0x57D35F8, database);
    Put(base + 0x57D3618, std::uintptr_t{0x200080000ULL});
    Put(database, base + 0x4400678);
    Put(database + 0x38, base + 0x4400660);
    Put(owner + 0x3C0, planner);
    Put(owner + 0x3F0, window);
    Put(planner + 0xD0, owner);
    Put(planner + 0x1538, std::int32_t{100});
    Put(planner + 0x1A18, active_rows);
    Put(planner + 0x1A24, std::int32_t{0});
    Put(planner + 0x1590, std::uintptr_t{0});
    Put(planner + 0x159C, std::int32_t{0});
    Put(window, base + 0x41676E8);
    Put(window + 0x100, planner);
    Put(window + 0xF8, std::int32_t{-1});
    Put(type, base + 0x440E308);
    constexpr char feast[] = "activity_feast";
    for (std::size_t i = 0; i < sizeof(feast) - 1; ++i)
      Put(type + 0x18 + i, static_cast<std::uint8_t>(feast[i]));
    Put(type + 0x28, std::uint64_t{sizeof(feast) - 1});
    Put(type + 0x30, std::uint64_t{15});
    Put(type + 0xD20, rows);
    Put(type + 0xD2C, std::int32_t{1});
    Put(rows, definition);
    Put(rows + 8, std::uint32_t{1});
    environment.enabled = true;
    environment.diagnostic = {true, kActivityPlannerDiagExeSha256V1,
                              base, this, &Read, &Frame, nullptr, nullptr};
    environment.context = this;
    environment.capture = &Capture;
    environment.read_diagnostic = &Diag;
    environment.hash_key = &Hash;
    environment.lookup_rule = &Lookup;
    environment.read_active = &Active;
    environment.toggle = &Toggle;
  }
};

} // namespace

int main() {
  constexpr std::string_view key = "activity_invite_rule_close_family";
  {
    Fixture f;
    const auto read = ReadActivityFeastGuestRuleV1(f.environment, f.frame, key);
    assert(read.status == ActivityFeastGuestRuleStatusV1::observed_inactive);
    assert(read.native_key_hash == 0x1234 && read.ordered_rule_count == 1);
    assert(f.toggles == 0);
    const auto denied = ActivateActivityFeastGuestRuleV1(
        f.environment, f.frame, key, false);
    assert(denied.status == ActivityFeastGuestRuleStatusV1::observed_inactive);
    assert(f.toggles == 0);
    const auto activated = ActivateActivityFeastGuestRuleV1(
        f.environment, f.frame, key, true);
    assert(activated.status == ActivityFeastGuestRuleStatusV1::activated);
    assert(activated.invoked && activated.active &&
           activated.active_rule_count == 1 && f.toggles == 1);
    const auto again = ActivateActivityFeastGuestRuleV1(
        f.environment, f.frame, key, true);
    assert(again.status == ActivityFeastGuestRuleStatusV1::observed_active);
    assert(!again.invoked && f.toggles == 1);
  }
  {
    Fixture f;
    f.Put(Fixture::window + 0x100, std::uintptr_t{0});
    assert(ReadActivityFeastGuestRuleV1(f.environment, f.frame, key).status ==
           ActivityFeastGuestRuleStatusV1::window_unbound);
    f.Put(Fixture::window + 0x100, Fixture::planner);
    f.Put(Fixture::type + 0xD2C, std::int32_t{2});
    f.Put(Fixture::rows + 16, Fixture::definition);
    assert(ReadActivityFeastGuestRuleV1(f.environment, f.frame, key).status ==
           ActivityFeastGuestRuleStatusV1::ambiguous_rule);
  }
  {
    Fixture f;
    f.toggle_changes_vector = false;
    const auto result = ActivateActivityFeastGuestRuleV1(
        f.environment, f.frame, key, true);
    assert(result.invoked &&
           result.status == ActivityFeastGuestRuleStatusV1::postcondition_failed);
  }
  {
    Fixture f;
    f.environment.enabled = false;
    assert(ReadActivityFeastGuestRuleV1(f.environment, f.frame, key).status ==
           ActivityFeastGuestRuleStatusV1::exact_build_rejected);
  }
}
