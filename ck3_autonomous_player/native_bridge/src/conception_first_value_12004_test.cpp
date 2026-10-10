#include "xar_bridge/conception_first_value_12004.hpp"
#include "xar_bridge/ck3_12004.hpp"

#include <algorithm>
#include <cstring>
#include <iostream>
#include <map>
#include <stdexcept>
#include <utility>
#include <vector>

namespace {
using namespace xar::ck3_12004;
constexpr std::uintptr_t kBase = 0x100000000ULL;
constexpr std::uintptr_t kCharacter = 0x100000ULL;
constexpr std::uintptr_t kFamily = 0x200000ULL;
constexpr std::uintptr_t kExtended = 0x300000ULL;
constexpr std::uintptr_t kModel = 0x400000ULL;
constexpr std::uintptr_t kKeys = 0x500000ULL;
constexpr std::uintptr_t kValues = 0x600000ULL;
constexpr std::uintptr_t kThresholds = 0x700000ULL;
constexpr std::uintptr_t kMultipliers = 0x800000ULL;

struct Fixture {
  std::map<std::uintptr_t, std::vector<std::byte>> memory;
  std::vector<std::pair<std::uintptr_t, std::size_t>> copies;
  std::uintptr_t denied = 0;
  void Region(std::uintptr_t base, std::size_t size) {
    memory.emplace(base, std::vector<std::byte>(size));
  }
  template <typename T> void Store(std::uintptr_t address, T value) {
    auto found = memory.upper_bound(address);
    if (found == memory.begin()) throw std::runtime_error("missing fixture region");
    --found;
    const auto offset = address - found->first;
    if (offset > found->second.size() || sizeof(value) > found->second.size() - offset)
      throw std::runtime_error("fixture write out of bounds");
    std::memcpy(found->second.data() + offset, &value, sizeof(value));
  }
  template <typename T> void Cell(std::uintptr_t address, T value) {
    Region(address, sizeof(value));
    Store(address, value);
  }
};

bool ReadFixture(void *context, const void *source, void *output,
                 std::size_t size) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  const auto address = reinterpret_cast<std::uintptr_t>(source);
  fixture.copies.emplace_back(address, size);
  if (address == fixture.denied) return false;
  auto found = fixture.memory.upper_bound(address);
  if (found == fixture.memory.begin()) return false;
  --found;
  const auto offset = address - found->first;
  if (offset > found->second.size() || size > found->second.size() - offset)
    return false;
  std::memcpy(output, found->second.data() + offset, size);
  return true;
}

void Require(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}

bool Copied(const Fixture &fixture, std::uintptr_t address, std::size_t size) {
  return std::find(fixture.copies.begin(), fixture.copies.end(),
      std::make_pair(address, size)) != fixture.copies.end();
}

Fixture MakeFixture() {
  Fixture fixture;
  fixture.Region(kCharacter, 0x1D0);
  fixture.Region(kFamily, 0x50);
  fixture.Region(kExtended, 0x260);
  fixture.Region(kModel, 0xE8);
  fixture.Region(kKeys, 6);
  fixture.Region(kValues, 24);
  fixture.Region(kThresholds, 8);
  fixture.Region(kMultipliers, 24);
  fixture.Store(kCharacter + 0x18, std::uint32_t{38822});
  fixture.Store(kCharacter + 0x1C, std::uint32_t{0x43686172U});
  fixture.Store(kCharacter + 0x6C, std::int16_t{-1});
  fixture.Store(kCharacter + 0x1A8, kFamily);
  fixture.Store(kCharacter + 0x1B0, kExtended);
  fixture.Store(kFamily + 0x44, std::int32_t{2});
  // High adjacent DWORD must not widen the actual signed child-count read.
  fixture.Store(kFamily + 0x48, std::uint32_t{0xF1234567U});
  fixture.Store(kExtended + 0x258, kModel);
  fixture.Store(kModel + 8, kCharacter);
  fixture.Store(kModel + 0x10 + 0x68, kKeys);
  fixture.Store(kModel + 0x10 + 0x74, std::int32_t{3});
  fixture.Store(kModel + 0x10 + 0xD0, kValues);
  fixture.Store(kKeys, std::uint16_t{0xBE});
  fixture.Store(kKeys + 2, std::uint16_t{0xBF});
  fixture.Store(kKeys + 4, std::uint16_t{0xC0});
  fixture.Store(kValues + 8, std::int64_t{149999});
  fixture.Store(kThresholds, std::int32_t{45});
  fixture.Store(kThresholds + 4, std::int32_t{30});
  fixture.Store(kMultipliers, std::int64_t{100000});
  fixture.Store(kMultipliers + 8, std::int64_t{75000});
  fixture.Store(kMultipliers + 16, std::int64_t{0});
  fixture.Cell(kBase + 0x5C69ED8, std::int64_t{10000});
  fixture.Cell(kBase + 0x544FC04, (std::uint64_t{1} << 40) | 2);
  fixture.Cell(kBase + 0x544FBF8, kThresholds);
  fixture.Cell(kBase + 0x544FCA8, kMultipliers);
  fixture.Cell(kBase + 0x5C69E10, std::int64_t{50000});
  fixture.Cell(kBase + 0x5459588 + 0xC, std::int32_t{0});
  return fixture;
}

xar::ck3_12002::family_value::CharacterValue CurrentValue() {
  xar::ck3_12002::family_value::CharacterValue value;
  value.character_id = 38822;
  value.fertility.available = true;
  value.fertility.effective_raw = 80000;
  value.age_raw = 35;
  value.scorer_age_override_raw = std::int16_t{-1};
  return value;
}

void RunConnectedFirstSourceFixture() {
  auto fixture = MakeFixture();
  auto value = CurrentValue();
  const auto original = fixture.memory;
  const auto bindings = BindConceptionFirstValue12004(
      kGameVersion, kExecutableSha256, kBase, ReadFixture, &fixture);
  std::string_view reason;
  auto input = ReadConceptionFirstValueInputsForCharacter12004(
      bindings, kCharacter, 38822, value, &reason);
  auto read = EvaluateConceptionFirstValue12004(input);
  Require(input && reason.empty() && read.status == "available" &&
      input->modifier_bf_raw == 149999 && input->age_threshold_count_low32 == 2 &&
      read.seed_after_children_raw == 60000 && read.adjusted_age_raw == 34 &&
      read.selected_age_band_index == 1 && read.age_product_raw == 45000 &&
      read.first_output_raw == 22500,
      "actual first-source child decrement/BF rounding/age band/final multiply join failed");
  Require(Copied(fixture, kFamily + 0x44, 4) &&
      !Copied(fixture, kFamily + 0x44, 8) &&
      Copied(fixture, kBase + 0x544FC04, 8) &&
      Copied(fixture, kValues + 8, 8) && !Copied(fixture, kCharacter + 0x2E0, 8),
      "actual first operands or qualified Family seed reuse changed");
  Require(fixture.memory == original, "readonly collector changed source memory");

  value.fertility.effective_raw = 10000;
  input = ReadConceptionFirstValueInputsForCharacter12004(
      bindings, kCharacter, 38822, value, &reason);
  read = EvaluateConceptionFirstValue12004(input);
  Require(read.status == "available" && read.seed_after_children_raw == -10000 &&
      read.age_product_raw == -7500 && read.first_output_raw == -3750,
      "negative first output qword was clamped or replaced with unavailable");
  value.fertility.effective_raw = 80000;

  fixture.Store(kValues + 8, std::int64_t{-50000});
  input = ReadConceptionFirstValueInputsForCharacter12004(
      bindings, kCharacter, 38822, value, &reason);
  read = EvaluateConceptionFirstValue12004(input);
  Require(read.adjusted_age_raw == 36 && read.first_output_raw == 22500,
      "negative BF half-step rounding did not change the selected raw age");

  // A real nonnegative age override, including zero, replaces the current age.
  value.scorer_age_override_raw = std::int16_t{0};
  input = ReadConceptionFirstValueInputsForCharacter12004(
      bindings, kCharacter, 38822, value, &reason);
  read = EvaluateConceptionFirstValue12004(input);
  Require(read.adjusted_age_raw == 1 && read.selected_age_band_index == 2 &&
      read.first_output_raw == 0 && read.status == "available",
      "source-proved zero selected factor became unavailable or wrong age override");

  value.scorer_age_override_raw = std::int16_t{-1};
  fixture.Store(kKeys + 2, std::uint16_t{0xC0});
  fixture.Store(kKeys + 4, std::uint16_t{0xC1});
  fixture.denied = kValues;
  input = ReadConceptionFirstValueInputsForCharacter12004(
      bindings, kCharacter, 38822, value, &reason);
  read = EvaluateConceptionFirstValue12004(input);
  Require(input && input->modifier_bf_raw == 0 && read.adjusted_age_raw == 35,
      "unsigned BF key miss did not yield the actual known-zero modifier");
  fixture.denied = 0;

  fixture.Store(kCharacter + 0x1A8, std::uintptr_t{0});
  fixture.Store(kCharacter + 0x1C8, std::uint64_t{1} << 40);
  fixture.denied = kBase + 0x5C69E10;
  fixture.copies.clear();
  input = ReadConceptionFirstValueInputsForCharacter12004(
      bindings, kCharacter, 38822, value, &reason);
  read = EvaluateConceptionFirstValue12004(input);
  Require(input && input->children_count_raw == 0 &&
      !input->final_multiplier_applies && read.first_output_raw == 60000 &&
      Copied(fixture, kBase + 0x5459588 + 0xC, 4) &&
      !Copied(fixture, kCharacter + 0x1C0, 8) &&
      !Copied(fixture, kBase + 0x5C69E10, 8),
      "null child owner fallback or actual final short circuit failed");

  fixture.Store(kCharacter + 0x1A8, kFamily);
  fixture.Store(kCharacter + 0x1C8, std::uint64_t{0});
  fixture.denied = kFamily + 0x44;
  input = ReadConceptionFirstValueInputsForCharacter12004(
      bindings, kCharacter, 38822, value, &reason);
  read = EvaluateConceptionFirstValue12004(input);
  Require(!input && reason == "native_conception_first_children_decrement_unread" &&
      read.status == "unavailable" && !read.first_output_raw,
      "failed first-specific count read became a zero output");

  fixture.denied = 0;
  fixture.Store(kModel + 8, std::uintptr_t{0x1234});
  input = ReadConceptionFirstValueInputsForCharacter12004(
      bindings, kCharacter, 38822, value, &reason);
  Require(!input && reason == "native_conception_first_modifier_owner_mismatch",
      "foreign modifier model produced a first output or used lazy default fallback");
  fixture.Store(kModel + 8, kCharacter);
  fixture.Store(kCharacter + 0x1B0, std::uintptr_t{0});
  input = ReadConceptionFirstValueInputsForCharacter12004(
      bindings, kCharacter, 38822, value, &reason);
  Require(!input && reason == "native_conception_first_owned_modifier_model_unavailable",
      "missing owned model silently fabricated default modifier inputs");

  fixture.copies.clear();
  const auto wrong_build = BindConceptionFirstValue12004(
      kGameVersion, "wrong", kBase, ReadFixture, &fixture);
  input = ReadConceptionFirstValueInputsForCharacter12004(
      wrong_build, kCharacter, 38822, value, &reason);
  Require(!wrong_build.enabled && !input && fixture.copies.empty(),
      "unadmitted build read native field addresses");

  input = ReadConceptionFirstValueInputsForCharacter12004(
      bindings, kCharacter, 38823, value, &reason);
  Require(!input && fixture.copies.empty(),
      "mismatched current household full ID read unrelated source memory");
  read = EvaluateConceptionFirstValue12004(std::nullopt);
  Require(read.status == "unavailable" && !read.first_output_raw,
      "unread input object became available zero");
  auto partial = ConceptionFirstValue12004Inputs{};
  partial.seed_raw = -20000;
  partial.age_threshold_count_low32 = 1;
  read = EvaluateConceptionFirstValue12004(partial);
  Require(read.status == "unavailable" && !read.first_output_raw &&
      read.unavailable_reason == "native_conception_first_age_threshold_unread",
      "missing consumed age threshold became selected factor zero");
}
} // namespace

int main() {
  try {
    RunConnectedFirstSourceFixture();
    std::cout << "{\"check\":\"conception_first_value_12004_connected_source\","
        "\"status\":\"GREEN\",\"first_specific_source_join\":true,"
        "\"family_seed_reused\":true,\"default_initializer_called\":false,"
        "\"read_failures_distinct\":true,\"game_or_sdk\":false}\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
