#include "xar_bridge/title_map_navigation_v1.hpp"

#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

namespace {

void TestAssert(bool condition, const char *expression,
                int line) noexcept {
  if (condition) {
    return;
  }
  std::fprintf(stderr, "test assertion failed at line %d: %s\n", line,
               expression);
  std::fflush(stderr);
  std::_Exit(3);
}

#undef assert
#define assert(expression) TestAssert((expression), #expression, __LINE__)

template <typename Value, std::size_t Size>
void Store(std::array<std::byte, Size> &bytes, std::size_t offset,
           const Value &value) {
  assert(offset + sizeof(value) <= bytes.size());
  std::memcpy(bytes.data() + offset, &value, sizeof(value));
}

struct Fixture {
  std::array<std::byte, 0xB0> game_state{};
  std::array<std::byte, 0x160> game_data{};
  std::array<std::byte, 0x30> title_storage{};
  std::array<std::byte, 0x40> title_slots{};
  std::array<std::byte, 0x470> title{};
  std::array<std::byte, 0x90> title_template{};
  std::array<std::byte, 0x20> province{};
  std::array<std::byte, 0x20> fallback{};
  std::vector<void *> province_array = std::vector<void *>(9'823, nullptr);

  void *game_state_pointer = game_state.data();
  void *title_storage_pointer = title_storage.data();
  void *fallback_pointer = fallback.data();
  std::string key = "c_bianzhou";
  std::string template_key = "c_bianzhou";
  std::int32_t title_id = 0x01000002;
  std::int32_t province_id = 9'822;
  xar::game::TitleMapNavigationFrameV1 frame{17, 53'182'008, true,
                                              true};
  std::uint32_t capture_count = 0;
  bool owning_thread = true;
  bool drift_after_first_capture = false;
  bool resolve_to_fallback = false;
  bool resolve_missing = false;
  bool province_missing = false;

  Fixture() {
    void *game_data_pointer = game_data.data();
    Store(game_state, 0xA0, game_data_pointer);

    void *slot_bytes = title_slots.data();
    const std::int32_t title_capacity = 4;
    Store(title_storage, 0x20, slot_bytes);
    Store(title_storage, 0x2C, title_capacity);
    void *title_pointer = title.data();
    Store(title_slots, 2 * 0x10 + 0x08, title_pointer);

    Store(title, 0x10, title_id);
    void *template_pointer = title_template.data();
    Store(title, 0x160, template_pointer);
    const std::int32_t tier = 2;
    Store(title_template, 0x5C, tier);

    Store(province, 0x10, province_id);
    province_array[static_cast<std::size_t>(province_id)] = province.data();
    void *province_array_pointer = province_array.data();
    const auto province_count =
        static_cast<std::int32_t>(province_array.size());
    Store(game_data, 0x140, province_array_pointer);
    Store(game_data, 0x14C, province_count);
  }
};

bool CaptureFrame(void *opaque,
                  xar::game::TitleMapNavigationFrameV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  output = fixture.frame;
  if (fixture.drift_after_first_capture && fixture.capture_count != 0) {
    ++output.date_raw;
  }
  ++fixture.capture_count;
  return true;
}

bool IsOwningThread(void *opaque) noexcept {
  return static_cast<Fixture *>(opaque)->owning_thread;
}

bool ReadString(void *opaque, const void *native_string,
                std::string &output) noexcept {
  const auto &fixture = *static_cast<const Fixture *>(opaque);
  if (native_string != fixture.title_template.data() + 0x18) {
    return false;
  }
  output = fixture.template_key;
  return true;
}

bool ResolveTitle(void *opaque, std::string_view key,
                  void *&output) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  if (fixture.resolve_missing || key != fixture.key) {
    output = fixture.fallback.data();
    return true;
  }
  output = fixture.resolve_to_fallback ? fixture.fallback.data()
                                       : fixture.title.data();
  return true;
}

bool ResolveProvince(void *opaque, void *title, void *&output) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  if (fixture.province_missing || title != fixture.title.data()) {
    output = nullptr;
    return true;
  }
  output = fixture.province.data();
  return true;
}

void *DummyTitleResolver(const void *) { return nullptr; }
void *DummyProvinceResolver(void *) { return nullptr; }

xar::ck3_11906::TitleMapNavigationNativeEnvironmentV1 Environment(
    Fixture &fixture) {
  xar::ck3_11906::TitleMapNavigationNativeEnvironmentV1 output{};
  output.exact_build_admitted = true;
  output.offline_fixture_function_overrides = true;
  output.game_state_slot = &fixture.game_state_pointer;
  output.landed_title_storage_slot = &fixture.title_storage_pointer;
  output.landed_title_fallback_slot = &fixture.fallback_pointer;
  output.resolve_landed_title_by_key = &DummyTitleResolver;
  output.resolve_title_province = &DummyProvinceResolver;
  return output;
}

xar::ck3_11906::TitleMapNavigationAccessV1 Access(Fixture &fixture) {
  xar::ck3_11906::TitleMapNavigationAccessV1 output{};
  output.context = &fixture;
  output.capture_frame = &CaptureFrame;
  output.is_owning_thread = &IsOwningThread;
  output.read_string = &ReadString;
  output.resolve_title_fixture = &ResolveTitle;
  output.resolve_province_fixture = &ResolveProvince;
  return output;
}

xar::game::ResolveLandedTitleMapAnchorResultV1 Run(
    Fixture &fixture,
    xar::game::LandedTitleMapAnchorV1 &anchor) {
  xar::game::TitleMapNavigationFrameV1 binding{};
  const xar::ck3_11906::TitleMapNavigationRequestV1 request{
      fixture.frame.snapshot_revision, fixture.key};
  return xar::ck3_11906::ResolveLandedTitleMapAnchorV1(
      Environment(fixture), Access(fixture), request, binding, anchor);
}

} // namespace

int main() {
  using Result = xar::game::ResolveLandedTitleMapAnchorResultV1;
  using xar::ck3_11906::IsCanonicalLandedTitleKeyV1;

  assert(IsCanonicalLandedTitleKeyV1("b_kaifeng"));
  assert(IsCanonicalLandedTitleKeyV1("c_bianzhou"));
  assert(!IsCanonicalLandedTitleKeyV1(""));
  assert(!IsCanonicalLandedTitleKeyV1("汴州"));
  assert(!IsCanonicalLandedTitleKeyV1("h_china"));
  assert(!IsCanonicalLandedTitleKeyV1("c_Bianzhou"));
  constexpr char embedded_nul[] = "c_bianzhou\0alias";
  assert(!IsCanonicalLandedTitleKeyV1(
      std::string_view(embedded_nul, sizeof(embedded_nul) - 1)));

  Fixture fixture{};
  xar::game::LandedTitleMapAnchorV1 anchor{};
  assert(Run(fixture, anchor) == Result::resolved);
  assert(anchor.key == "c_bianzhou");
  assert(anchor.title_id == fixture.title_id);
  assert(anchor.tier_raw == 2);
  assert(anchor.tier_key == "county");
  assert(anchor.capital_province_id == 9'822);
  assert(anchor.native_title == fixture.title.data());
  assert(anchor.native_capital_province == fixture.province.data());
  assert(fixture.capture_count == 2);

  Fixture missing{};
  missing.resolve_missing = true;
  assert(Run(missing, anchor) == Result::title_key_not_found);

  Fixture generation_mismatch{};
  std::array<std::byte, 0x20> collision_title{};
  const std::int32_t collision_id = 0x02000002;
  Store(collision_title, 0x10, collision_id);
  void *collision_pointer = collision_title.data();
  Store(generation_mismatch.title_slots, 2 * 0x10 + 0x08,
        collision_pointer);
  assert(Run(generation_mismatch, anchor) ==
         Result::title_generation_mismatch);

  Fixture key_mismatch{};
  key_mismatch.template_key = "c_not_bianzhou";
  assert(Run(key_mismatch, anchor) ==
         Result::title_generation_mismatch);

  Fixture not_centerable{};
  not_centerable.province_missing = true;
  assert(Run(not_centerable, anchor) == Result::resolved);
  assert(!anchor.capital_province_id.has_value());
  assert(anchor.native_capital_province == nullptr);

  Fixture drift{};
  drift.drift_after_first_capture = true;
  assert(Run(drift, anchor) == Result::state_changed);

  Fixture wrong_thread{};
  wrong_thread.owning_thread = false;
  assert(Run(wrong_thread, anchor) == Result::requires_owning_thread);

  Fixture running{};
  running.frame.paused = false;
  assert(Run(running, anchor) == Result::requires_paused);

  Fixture loading{};
  loading.frame.map_ready = false;
  assert(Run(loading, anchor) == Result::map_not_ready);

  Fixture zero_revision{};
  zero_revision.frame.snapshot_revision = 0;
  assert(Run(zero_revision, anchor) == Result::resolved);

  Fixture unsupported{};
  auto unsupported_environment = Environment(unsupported);
  unsupported_environment.exact_build_admitted = false;
  auto access = Access(unsupported);
  xar::game::TitleMapNavigationFrameV1 binding{};
  const xar::ck3_11906::TitleMapNavigationRequestV1 request{
      unsupported.frame.snapshot_revision, unsupported.key};
  assert(xar::ck3_11906::ResolveLandedTitleMapAnchorV1(
             unsupported_environment, access, request, binding, anchor) ==
         Result::unsupported_build);

  assert(xar::ck3_11906::TitleMapNavigationRejectionCodeV1(
             Result::title_key_not_found) == "title_key_not_found");
  assert(xar::ck3_11906::TitleMapNavigationRejectionCodeV1(
             Result::resolved)
             .empty());
  return 0;
}
