#include "xar_bridge/activity_feast_guest_rule_provenance_v1.hpp"

#include <windows.h>

#include <array>
#include <cassert>
#include <cstdint>
#include <cstring>
#include <memory>
#include <unordered_map>

namespace {

struct Fixture {
  std::unordered_map<std::uintptr_t, std::uint8_t> bytes{};
  xar::bridge::ActivityCostSlot12FrameV1 frame{
      53219928, 29829, GetCurrentThreadId(), true};
};

void PutBytes(Fixture &fixture, std::uintptr_t address,
              const void *source, std::size_t size) {
  const auto *bytes = static_cast<const std::uint8_t *>(source);
  for (std::size_t i = 0; i < size; ++i)
    fixture.bytes[address + i] = bytes[i];
}

template <typename T>
void Put(Fixture &fixture, std::uintptr_t address, const T &value) {
  PutBytes(fixture, address, &value, sizeof(value));
}

bool Read(void *context, std::uintptr_t address, void *output,
          std::size_t size) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  auto *bytes = static_cast<std::uint8_t *>(output);
  for (std::size_t i = 0; i < size; ++i) {
    const auto found = fixture.bytes.find(address + i);
    if (found == fixture.bytes.end()) return false;
    bytes[i] = found->second;
  }
  return true;
}

bool Frame(void *context,
           xar::bridge::ActivityCostSlot12FrameV1 &output) noexcept {
  output = static_cast<Fixture *>(context)->frame;
  return true;
}

} // namespace

int main() {
  using namespace xar::bridge;
  constexpr std::uintptr_t base = 0x10000000;
  constexpr std::uintptr_t planner = 0x20000000;
  constexpr std::uintptr_t type = 0x21000000;
  constexpr std::uintptr_t active_rows = 0x22000000;
  constexpr std::uintptr_t definition = 0x23000000;
  constexpr std::uintptr_t temporary = 0x24000000;
  constexpr std::uintptr_t temporary_rows = 0x25000000;
  constexpr std::uintptr_t typed_items = 0x26000000;
  constexpr std::uintptr_t group_rows = 0x27000000;
  constexpr std::uintptr_t group_ids = 0x28000000;
  constexpr std::uint32_t hash = 0xABCDEF12;
  Fixture fixture{};
  ActivityCostSlot12EnvironmentV1 env{};
  env.enabled = true;
  env.primary_thread_suspended = true;
  env.executable_sha256 = kActivityGuestRuleProvenanceExeSha256V1;
  env.module_base = base;
  env.context = &fixture;
  env.read_memory = &Read;
  env.read_frame = &Frame;

  constexpr std::array<std::uint8_t, 15> refresh{
      0x4C, 0x89, 0x44, 0x24, 0x18, 0x48, 0x89, 0x54,
      0x24, 0x10, 0x48, 0x89, 0x4C, 0x24, 0x08};
  constexpr std::array<std::uint8_t, 18> effect{
      0x48, 0x89, 0x5C, 0x24, 0x10, 0x48, 0x89, 0x74, 0x24,
      0x18, 0x57, 0x48, 0x81, 0xEC, 0x30, 0x04, 0x00, 0x00};
  constexpr std::array<std::uint8_t, 5> refresh_call{
      0xE8, 0x3F, 0xE9, 0x81, 0x01};
  constexpr std::array<std::uint8_t, 5> effect_call{
      0xE8, 0xF6, 0x0E, 0xAB, 0x00};
  PutBytes(fixture, base + kActivityGuestRuleRefreshRvaV1,
           refresh.data(), refresh.size());
  PutBytes(fixture, base + kActivityGuestRuleEffectRvaV1,
           effect.data(), effect.size());
  PutBytes(fixture, base + kActivityGuestRuleRefreshReturnRvaV1 - 5,
           refresh_call.data(), refresh_call.size());
  PutBytes(fixture, base + kActivityGuestRuleEffectReturnRvaV1 - 5,
           effect_call.data(), effect_call.size());
  assert(VerifyActivityGuestRuleProvenanceExactAbiV1(env));
  Put(fixture, base + kActivityGuestRuleEffectReturnRvaV1 - 5,
      std::uint8_t{0x90});
  assert(!VerifyActivityGuestRuleProvenanceExactAbiV1(env));
  PutBytes(fixture, base + kActivityGuestRuleEffectReturnRvaV1 - 5,
           effect_call.data(), effect_call.size());

  Put(fixture, planner, base + 0x41205F0);
  Put(fixture, planner + 0x1530, type);
  Put(fixture, planner + 0x1AB0, std::int32_t{5});
  Put(fixture, type, base + 0x440E308);
  constexpr char feast[] = "activity_feast";
  PutBytes(fixture, type + 0x18, feast, sizeof(feast) - 1);
  Put(fixture, type + 0x28, std::uint64_t{sizeof(feast) - 1});
  Put(fixture, type + 0x30, std::uint64_t{15});
  Put(fixture, planner + 0x1A18, active_rows);
  Put(fixture, planner + 0x1A24, std::int32_t{1});
  Put(fixture, active_rows, definition);
  Put(fixture, active_rows + 8, std::int32_t{1});
  Put(fixture, active_rows + 12, std::uint32_t{0});
  Put(fixture, definition + 0x14, hash);
  Put(fixture, definition + 0x9C, std::uint32_t{7});
  Put(fixture, temporary + 0x100, temporary_rows);
  Put(fixture, temporary + 0x10C, std::int32_t{1});
  Put(fixture, temporary_rows + 8, std::uint32_t{7});
  Put(fixture, temporary_rows + 0x10, typed_items);
  Put(fixture, temporary_rows + 0x1C, std::int32_t{2});
  Put(fixture, typed_items, std::uint16_t{4});
  Put(fixture, typed_items + 8, std::uint32_t{38293});
  Put(fixture, typed_items + 16, std::uint16_t{4});
  Put(fixture, typed_items + 24, std::uint32_t{444});
  Put(fixture, planner + 0x1590, group_rows);
  Put(fixture, planner + 0x159C, std::int32_t{2});
  Put(fixture, group_rows, std::uintptr_t{0});
  Put(fixture, group_rows + 0xC, std::int32_t{0});
  Put(fixture, group_rows + 0x18, group_ids);
  Put(fixture, group_rows + 0x18 + 0xC, std::int32_t{1});
  Put(fixture, group_ids, std::uint32_t{38293});

  auto observer = std::make_unique<ActivityGuestRuleProvenanceObserverV1>();
  observer->environment = env;
  const auto absent = ReadActivityGuestRuleProvenanceV1(
      *observer, fixture.frame, planner, hash, 38293);
  assert(absent.status == ActivityGuestRuleProvenanceStatusV1::no_normal_refresh);
  Put(fixture, planner + 0x1AB0, std::int32_t{4});
  assert(!BeginActivityGuestRuleRefreshV1(
      *observer, base + kActivityGuestRuleRefreshReturnRvaV1, planner,
      planner + 0x1A18, planner + 0x1590));
  const auto diagnostic = DescribeActivityGuestRuleRefreshDiagnosticsV1(
      *observer);
  assert(diagnostic.find("stage_not_five=1") != std::string::npos);
  assert(diagnostic.find("last_stage=4") != std::string::npos);
  Put(fixture, planner + 0x1AB0, std::int32_t{5});
  assert(BeginActivityGuestRuleRefreshV1(
      *observer, base + kActivityGuestRuleRefreshReturnRvaV1, planner,
      planner + 0x1A18, planner + 0x1590));
  RecordActivityGuestRuleEffectReturnV1(
      *observer, base + kActivityGuestRuleEffectReturnRvaV1,
      definition + 0x38, temporary);
  FinishActivityGuestRuleRefreshV1(*observer);
  const auto member = ReadActivityGuestRuleProvenanceV1(
      *observer, fixture.frame, planner, hash, 38293);
  assert(member.status == ActivityGuestRuleProvenanceStatusV1::observed);
  assert(member.normal_refresh_sequence == 1);
  assert(member.raw_rule_character_count == 2);
  assert(member.filtered_rule_character_count == 1);
  assert(member.filtered_ids[0] == 38293);
  assert(member.candidate_membership);
  const auto rejected = ReadActivityGuestRuleProvenanceV1(
      *observer, fixture.frame, planner, hash, 444);
  assert(rejected.status == ActivityGuestRuleProvenanceStatusV1::observed);
  assert(!rejected.candidate_membership);
  const auto no_rule = ReadActivityGuestRuleProvenanceV1(
      *observer, fixture.frame, planner, hash + 1, 38293);
  assert(no_rule.status == ActivityGuestRuleProvenanceStatusV1::rule_unavailable);
  Put(fixture, group_ids, std::uint32_t{444});
  const auto changed = ReadActivityGuestRuleProvenanceV1(
      *observer, fixture.frame, planner, hash, 38293);
  assert(changed.status == ActivityGuestRuleProvenanceStatusV1::frame_changed);
  Put(fixture, group_ids, std::uint32_t{38293});
  Put(fixture, active_rows + 8, std::int32_t{2});
  const auto changed_rule = ReadActivityGuestRuleProvenanceV1(
      *observer, fixture.frame, planner, hash, 38293);
  assert(changed_rule.status ==
         ActivityGuestRuleProvenanceStatusV1::frame_changed);
}
