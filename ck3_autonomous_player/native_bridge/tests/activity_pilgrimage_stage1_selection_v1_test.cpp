// Derived from the pinned production owned-memory fixture; current exact .4 ABI.
// No game, process reads, production symbol replacement, or world callbacks.
#include "xar_bridge/activity_pilgrimage_stage1_v1.hpp"
#include "xar_bridge/ck3_12002_feast_planner.hpp"

#include <array>
#include <cstdlib>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <string_view>
#include <unordered_map>

namespace {
using xar::bridge::ActivityPlannerDiagFrameV1;
using xar::bridge::ActivityPilgrimageStage1OptionEnvironmentV1;
using xar::bridge::ActivityPilgrimageStage1OptionReadStatusV1;

constexpr std::uintptr_t kBase = 0x140000000;
constexpr std::uintptr_t kRoot = 0x10000000;
constexpr std::uintptr_t kIdler = 0x10001000;
constexpr std::uintptr_t kGfx = 0x10002000;
constexpr std::uintptr_t kHandler = 0x10003000;
constexpr std::uintptr_t kPlanner = 0x10004000;
constexpr std::uintptr_t kWidget = 0x10005000;
constexpr std::uintptr_t kType = 0x10006000;
constexpr std::uintptr_t kCategory = 0x10007000;
constexpr std::uintptr_t kRows = 0x10008000;
constexpr std::uintptr_t kOption = 0x10009000;
constexpr std::uintptr_t kAutoRows = 0x10009500;
constexpr std::uintptr_t kStorage = 0x1000A000;
constexpr std::uintptr_t kSlots = 0x1000B000;
constexpr std::uintptr_t kActor = 0x1000C000;
constexpr std::uintptr_t kHost = 0x1000D000;
constexpr std::int32_t kActorId = 29829;

struct Fake {
  std::unordered_map<std::uintptr_t, std::uint8_t> bytes{};
  ActivityPlannerDiagFrameV1 frame{3, 53219928, kActorId, true, true, true,
                                   true};
  bool shown = true;
  bool valid = true;
  bool progress = true;
  bool drift_on_valid = false;
  bool lose_option_on_transition = false;
  bool auto_row_present = true;
  bool auto_row_out_of_range = false;
  std::string_view key = "pilgrimage_type_pious";
  int stage_two_calls = 0;
  int original_progress_calls = 0;

  template <typename T> void Put(std::uintptr_t at, const T &value) {
    const auto *data = reinterpret_cast<const std::uint8_t *>(&value);
    for (std::size_t index = 0; index < sizeof(value); ++index)
      bytes[at + index] = data[index];
  }
  void PutBytes(std::uintptr_t at, std::string_view value) {
    for (std::size_t index = 0; index < value.size(); ++index)
      bytes[at + index] = static_cast<std::uint8_t>(value[index]);
  }
};

#define Expect(condition) do { \
  if (!(condition)) { \
    std::cerr << "stage1 option test failed at line " << __LINE__ << '\n'; \
    std::abort(); \
  } \
} while (false)

bool Read(void *opaque, std::uintptr_t address, void *output,
          std::size_t size) noexcept {
  const auto &fake = *static_cast<Fake *>(opaque);
  auto *destination = static_cast<std::uint8_t *>(output);
  for (std::size_t index = 0; index < size; ++index) {
    const auto it = fake.bytes.find(address + index);
    if (it == fake.bytes.end()) return false;
    destination[index] = it->second;
  }
  return true;
}

bool Frame(void *opaque, ActivityPlannerDiagFrameV1 &output) noexcept {
  output = static_cast<Fake *>(opaque)->frame;
  return true;
}

std::uintptr_t Cast(void *, std::uintptr_t source,
                    std::uintptr_t source_type,
                    std::uintptr_t target_type) noexcept {
  return source == kIdler && source_type == kBase + 0x5514438 &&
                 target_type == kBase + 0x5514460
             ? kGfx
             : 0;
}

bool Visible(void *, std::uintptr_t planner, std::uintptr_t slot,
             bool &output) noexcept {
  if (planner != kPlanner || slot != kBase + 0x2160380) return false;
  output = true;
  return true;
}

bool Key(void *opaque, std::int32_t identifier,
         std::array<char, 96> &output, std::uint16_t &size) noexcept {
  const auto &fake = *static_cast<Fake *>(opaque);
  if (identifier != 42 || fake.key.empty()) return false;
  std::memcpy(output.data(), fake.key.data(), fake.key.size());
  size = static_cast<std::uint16_t>(fake.key.size());
  return true;
}

bool Selected(void *, std::uintptr_t planner,
              std::uintptr_t &output) noexcept {
  if (planner != kPlanner) return false;
  output = kOption;
  return true;
}

bool Predicate(void *opaque, std::uintptr_t entry,
               std::uintptr_t candidate, std::uintptr_t actor,
               std::uintptr_t selected, bool &output) noexcept {
  auto &fake = *static_cast<Fake *>(opaque);
  if (candidate != kOption || actor != kActor || selected != kOption)
    return false;
  if (entry == kBase + 0x9DEA70) output = fake.shown;
  else if (entry == kBase + 0x9DEB70) {
    output = fake.valid;
    if (fake.drift_on_valid) fake.frame.revision = 4;
  } else return false;
  return true;
}

bool Progress(void *opaque, std::uintptr_t planner,
              bool &output) noexcept {
  if (planner != kPlanner) return false;
  output = static_cast<Fake *>(opaque)->progress;
  return true;
}

bool SetStageTwo(void *opaque, std::uintptr_t planner) noexcept {
  auto &fake = *static_cast<Fake *>(opaque);
  if (planner != kPlanner) return false;
  ++fake.stage_two_calls;
  fake.Put(kPlanner + 0x1AE8, std::int32_t{2});
  fake.Put(kPlanner + 0x1B00, std::uintptr_t{0});
  if (fake.lose_option_on_transition)
    fake.Put(kRows + 8, std::uintptr_t{0});
  return true;
}

bool FindAutoRow(void *opaque, std::uintptr_t planner,
                 std::uintptr_t &output) noexcept {
  if (planner != kPlanner) return false;
  const auto &fake = *static_cast<Fake *>(opaque);
  output = !fake.auto_row_present
      ? 0 : fake.auto_row_out_of_range ? kAutoRows + 0x38 : kAutoRows;
  return true;
}

bool ProgressNonzero(void *opaque, std::uintptr_t planner) noexcept {
  auto &fake = *static_cast<Fake *>(opaque);
  if (planner != kPlanner) return false;
  ++fake.original_progress_calls;
  fake.Put(kPlanner + 0x1AF8, kAutoRows);
  fake.Put(kPlanner + 0x1AF4, std::int32_t{1});
  fake.Put(kAutoRows + 8, std::int32_t{0});
  fake.Put(kPlanner + 0x1B08, std::uint8_t{0});
  fake.Put(kPlanner + 0x1AE8, std::int32_t{2});
  fake.Put(kPlanner + 0x1B00, std::uintptr_t{0});
  if (fake.lose_option_on_transition)
    fake.Put(kRows + 8, std::uintptr_t{0});
  return true;
}

void Populate(Fake &fake) {
  fake.Put(kBase + 0x11B2865,
           std::array<std::uint8_t, 8>{0x49, 0x89, 0xB4, 0x24, 0xA0, 0, 0, 0});
  fake.Put(kBase + 0x216038A,
           std::array<std::uint8_t, 4>{0x48, 0x8B, 0x59, 0x60});
  fake.Put(kBase + 0x11B8673,
           std::array<std::uint8_t, 7>{0x48, 0x63, 0x81, 0xE8, 0x1A, 0, 0});
  fake.Put(kBase + 0x11B64A0,
           std::array<std::uint8_t, 7>{0x48, 0x8B, 0x81, 0x00, 0x15, 0, 0});
  fake.Put(kBase + 0x9DEA70,
           std::array<std::uint8_t, 7>{0x4C, 0x8B, 0xDC, 0x49, 0x89, 0x5B,
                                        0x10});
  fake.Put(kBase + 0x9DEB70,
           std::array<std::uint8_t, 7>{0x4C, 0x8B, 0xDC, 0x49, 0x89, 0x5B,
                                        0x10});
  fake.Put(kBase + 0x11B8650,
           std::array<std::uint8_t, 7>{0x48, 0x89, 0x5C, 0x24, 0x10, 0x48,
                                        0x89});
  fake.Put(kBase + 0x11B95B0,
           std::array<std::uint8_t, 15>{0x40, 0x53, 0x48, 0x81, 0xEC,
                                      0xA0, 0, 0, 0, 0x8B, 0x81, 0xE8, 0x1A, 0, 0});
  fake.Put(kBase + 0x11B5930,
           std::array<std::uint8_t, 13>{0x48, 0x8B, 0x81, 0xB0, 0x15, 0,
                                         0, 0x48, 0x63, 0x89, 0xBC, 0x15, 0});
  fake.Put(kBase + 0x11B8CB0,
           std::array<std::uint8_t, 10>{0x40, 0x53, 0x48, 0x83, 0xEC,
                                         0x20, 0x48, 0x63, 0x81, 0xE8});
  fake.Put(kBase + 0x45325D8, kBase + 0x11B2E10);
  fake.Put(kBase + 0x45325D8 + 7 * 8, kBase + 0x2160380);
  fake.Put(kBase + 0x45325D8 + 11 * 8, kBase + 0xB1F0A0);
  fake.Put(kBase + 0x45325D8 + 12 * 8, kBase + 0x11B5B10);
  fake.Put(kBase + 0x45325D8 + 0xC8, kBase + 0x11B6530);
  fake.Put(kBase + 0x45326B0, kBase + 0x11D33E4);

  fake.Put(kBase + 0x5C6A520, kRoot);
  fake.Put(kRoot + 0x10, kIdler);
  fake.Put(kGfx, kBase + 0x44BC418);
  fake.Put(kGfx + 0x88, kHandler);
  fake.Put(kHandler, kBase + 0x44BA8A0);
  fake.Put(kBase + 0x54DBC00, kActorId);
  fake.Put(kBase + 0x5C67568, kStorage);
  fake.Put(kBase + 0x5C67570, std::uintptr_t{0});
  fake.Put(kStorage + 0x20, kSlots);
  fake.Put(kStorage + 0x2C, std::int32_t{40000});
  fake.Put(kSlots + kActorId * 0x10 + 8, kActor);
  fake.Put(kActor + 0x18, kActorId);

  fake.Put(kHandler + 0x3C0, kPlanner);
  fake.Put(kHandler + 0x3D8, kHost);
  fake.Put(kHost, kBase + 0x457A148);
  fake.Put(kHost + 0x10, kBase + 0x457A120);
  fake.Put(kHost + 0xA0, kHandler);
  fake.Put(kHost + 0xD0, kActorId);
  fake.Put(kHost + 0x238, kType);
  fake.Put(kPlanner, kBase + 0x45325D8);
  fake.Put(kPlanner + 0x10, kBase + 0x45326B0);
  fake.Put(kPlanner + 0xA0, kHandler);
  fake.Put(kPlanner + 0x60, kWidget);
  fake.Put(kPlanner + 0x1AE8, std::int32_t{1});
  fake.Put(kPlanner + 0x1B08, std::uint8_t{0});
  fake.Put(kPlanner + 0x15B0, kAutoRows);
  fake.Put(kPlanner + 0x15BC, std::int32_t{1});
  fake.Put(kAutoRows, kType);
  fake.Put(kAutoRows + 8, std::int32_t{1});
  fake.Put(kPlanner + 0x1500, kType);
  fake.Put(kType, kBase + 0x48BFE60);
  fake.Put(kType + 0x18, std::uintptr_t{0x10011000});
  fake.PutBytes(0x10011000, "activity_pilgrimage");
  fake.Put(kType + 0x28, std::uint64_t{std::string_view{"activity_pilgrimage"}.size()});
  fake.Put(kType + 0x30, std::uint64_t{31});
  fake.Put(kType + 0x960, kCategory);
  fake.Put(kPlanner + 0x1598, kRows);
  fake.Put(kPlanner + 0x15A4, std::int32_t{1});
  fake.Put(kPlanner + 0x1B00, kRows);
  fake.Put(kRows, kCategory);
  fake.Put(kRows + 8, kOption);
  fake.Put(kOption, kBase + 0x48BFD28);
  fake.Put(kOption + 8, std::int32_t{42});
}

ActivityPilgrimageStage1OptionEnvironmentV1 Env(Fake &fake) {
  return {{true, xar::ck3_12004::kExecutableSha256, kBase,
           &fake, &Read, &Frame, &Cast, &Visible},
          &Key, &Selected, &Predicate, &Progress, &SetStageTwo,
          &FindAutoRow, &ProgressNonzero};
}
} // namespace


int main() {
  using namespace xar::bridge;
  constexpr auto contract = kOrdinaryPilgrimagePiousContractV1;
  static_assert(contract.activity_key.size() == 19);
  static_assert(contract.special_option_key.size() == 21);
  Fake fake{};
  Populate(fake);
  const auto frame = fake.frame;
  ActivityTypedPlannerSelectionV1 selected{};
  auto env = Env(fake);
  auto read = [&] { return ReadActivityPilgrimageSelectedOptionV1(env, frame, 1, selected); };
  Expect(read() && selected.observed);

  // Actual Open may leave the separate HostView absent or with an older owner.
  // The original reader reproduces the B8 shape: Stage1 observed/progress true,
  // while its stronger typed selection producer fails solely on HostView.
  fake.Put(kHandler + 0x3D8, std::uintptr_t{0});
  auto diagnostic = ReadActivityPlannerDiagV1(env.diagnostic, frame);
  auto stage1 = ReadActivityPilgrimageStage1OptionV1(env, frame);
  Expect(diagnostic.status == ActivityPlannerDiagStatusV1::observed);
  Expect(!diagnostic.value.host_view_activity_key_known);
  Expect(stage1.status == ActivityPilgrimageStage1OptionReadStatusV1::observed);
  Expect(stage1.can_progress && stage1.pilgrimage_confirm_ready);
#if defined(XAR_B8_EXPECT_BASELINE_HOST_GATE)
  Expect(!read() && !selected.observed);
#else
  Expect(read() && selected.observed);
#endif
  fake.Put(kHandler + 0x3D8, kHost);
  fake.Put(kHost + 0xD0, std::int32_t{kActorId + 1});
#if defined(XAR_B8_EXPECT_BASELINE_HOST_GATE)
  Expect(!read());
#else
  Expect(read());
#endif
  fake.Put(kHost + 0xD0, kActorId);

  // A valid but unrelated HostView activity is still not the current planner.
  constexpr std::uintptr_t other_type = 0x10014000;
  fake.Put(kHost + 0x238, other_type);
  fake.Put(other_type, kBase + 0x48BFE60);
  fake.PutBytes(other_type + 0x18, "activity_feast");
  fake.Put(other_type + 0x28, std::uint64_t{14});
  fake.Put(other_type + 0x30, std::uint64_t{15});
  diagnostic = ReadActivityPlannerDiagV1(env.diagnostic, frame);
  Expect(diagnostic.status == ActivityPlannerDiagStatusV1::observed &&
         diagnostic.value.host_view_activity_key_known);
#if defined(XAR_B8_EXPECT_BASELINE_HOST_GATE)
  Expect(!read());
#else
  Expect(read());
#endif
  fake.Put(kHost + 0x238, kType);

  // Removing a HostView dependency must not remove actual planner identity.
  fake.Put(kType + 0x28, std::uint64_t{18});
  Expect(!read() && !selected.observed);
  fake.Put(kType + 0x28, std::uint64_t{19});
  for (const auto key : {"pilgrimage_type_hajj", "pilgrimage_type_worldly"}) {
    fake.key = key;
#if defined(XAR_B8_EXPECT_BASELINE_HOST_GATE)
    Expect(!read() && !selected.observed);
#else
    Expect(read() && selected.observed);
    Expect(std::string_view(selected.option_key.data(), selected.option_key_size) == key);
    stage1 = ReadActivityPilgrimageStage1OptionV1(env, frame);
    Expect(stage1.pilgrimage_confirm_ready);
#endif
  }
  fake.key = "pilgrimage_type_unknown";
  Expect(!read() && !selected.observed);
  fake.key = "pilgrimage_type_pious";
  fake.Put(kPlanner + 0x1B00, std::uintptr_t{0});
  Expect(!read());
  fake.Put(kPlanner + 0x1B00, kRows);
  fake.Put(kRows + 8, std::uintptr_t{0});
  Expect(!read());
  fake.Put(kRows + 8, kOption);
  env.selected_option = nullptr;
  Expect(!read());
  env = Env(fake);
  env.diagnostic.admitted_executable_sha256 = "UNSUPPORTED";
  Expect(!read());
  env = Env(fake);
  ++fake.frame.revision;
  Expect(!read());
  fake.frame = frame;
  Expect(!ReadActivityPilgrimageSelectedOptionV1(env, frame, 2, selected));
  Expect(read());
  Expect(fake.stage_two_calls == 0 && fake.original_progress_calls == 0);
  std::cout << "B8 owned-memory selected-option/HostView boundary fixture; no world action\n";
  return 0;
}
