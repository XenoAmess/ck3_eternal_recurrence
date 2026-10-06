#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12004_frontend_bookmark.hpp"
#include "xar_bridge/frontend_bookmark_model_probe_v1.hpp"
#include "xar_bridge/frontend_bookmark_model_result_v1.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#if !defined(XAR_CK3_FEUDAL_1066_TARGET_ROBERT_V1) || \
    XAR_CK3_FEUDAL_1066_TARGET_ROBERT_V1 != 1
#error This actual-1.20.0.4 fixture requires the configured Robert target.
#endif

namespace {

using xar::ck3_11906::FrontendBookmarkChangeV1;
using xar::ck3_11906::FrontendBookmarkModelProbeV1;
using xar::ck3_11906::FrontendBookmarkSeedTargetV1;
using xar::ck3_11906::FrontendBookmarkSelectionV1;
using xar::ck3_11906::GuiAbiRevisionV1;
using xar::ck3_11906::ZhongguoScoreboardAccessV1;
using xar::ck3_11906::ZhongguoScoreboardNativeEnvironmentV1;

constexpr std::uintptr_t kModuleBase = 0x140000000;
constexpr std::uintptr_t kGuiSlot = kModuleBase + 0x5CB87F8;
constexpr std::uintptr_t kDatabaseSlot = kModuleBase + 0x5C67210;
constexpr std::uintptr_t kApplication = 0x1000;
constexpr std::uintptr_t kBookmarksRoot = 0x2000;
constexpr std::uintptr_t kGuiHost = 0x3000;
constexpr std::uintptr_t kGuiContext = 0x4000;
constexpr std::uintptr_t kIdler = 0x5000;
constexpr std::uintptr_t kGfx = 0x6000;
constexpr std::uintptr_t kHandler = 0x7000;
constexpr std::uintptr_t kView = 0x8000;
constexpr std::uintptr_t kRobertBookmark = 0x9000;
constexpr std::uintptr_t kRobertCharacter = 0xA000;
constexpr std::uintptr_t kGroup1066 = 0xD000;
constexpr std::uintptr_t kRobertGovernment = 0xE000;
constexpr std::uintptr_t kRegistry = 0x11000;
constexpr std::uintptr_t kRurikBookmark = 0x14000;
constexpr std::uintptr_t kRurikCharacter = 0x15000;
constexpr std::uintptr_t kRurikGovernment = 0x18000;
constexpr std::uintptr_t kGroup867 = 0x1B000;
constexpr std::uintptr_t kDatabase = 0x1C000;
constexpr std::uintptr_t kDatabaseEntries = 0x1D000;
constexpr std::uintptr_t kGroupEntries = 0x1A000;
constexpr std::uintptr_t kDefault1066Bookmark = 0x1F000;
constexpr std::uint64_t kRobertDate = 0xFFFFFFFF032AEB08ULL;
constexpr std::string_view kRobertKey =
    "bookmark_rags_to_riches_duke_robert";
constexpr std::string_view kOldExecutableSha256 =
    "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";
constexpr std::string_view kProbeStep = "probe-frontend-bookmark-model-v1";

void Require(bool condition, std::string_view message) {
  if (!condition) throw std::runtime_error(std::string(message));
}

struct Region {
  std::uintptr_t base;
  std::vector<std::byte> bytes;
};

struct Fixture {
  std::vector<Region> regions;
  int character_setter_calls = 0;
  int bookmark_setter_calls = 0;
  int group_setter_calls = 0;
  std::string setter_order;

  void Add(std::uintptr_t base, std::size_t size) {
    regions.push_back(Region{base, std::vector<std::byte>(size)});
  }

  bool Store(std::uintptr_t address, const void *source,
             std::size_t size) noexcept {
    for (auto &region : regions) {
      if (address >= region.base && size <= region.bytes.size() &&
          address - region.base <= region.bytes.size() - size) {
        std::memcpy(region.bytes.data() + address - region.base, source, size);
        return true;
      }
    }
    return false;
  }

  template <typename Value> void Put(std::uintptr_t address, Value value) {
    Require(Store(address, &value, sizeof(value)),
            "fixture write outside synthetic region");
  }

  void PutBytes(std::uintptr_t address, std::string_view bytes) {
    Require(Store(address, bytes.data(), bytes.size()),
            "fixture string write outside synthetic region");
  }
};

bool ReadFixture(void *opaque, const void *address, void *output,
                 std::size_t size) noexcept {
  const auto &fixture = *static_cast<const Fixture *>(opaque);
  const auto target = reinterpret_cast<std::uintptr_t>(address);
  for (const auto &region : fixture.regions) {
    if (target >= region.base && size <= region.bytes.size() &&
        target - region.base <= region.bytes.size() - size) {
      std::memcpy(output, region.bytes.data() + target - region.base, size);
      return true;
    }
  }
  return false;
}

void PutScriptKey(Fixture &fixture, std::uintptr_t owner,
                  std::size_t offset, std::uintptr_t storage,
                  std::string_view key) {
  if (key.size() < 16) {
    fixture.PutBytes(owner + offset, key);
  } else {
    fixture.Put(owner + offset, storage);
    fixture.PutBytes(storage, key);
  }
  fixture.Put(owner + offset + 0x10,
              static_cast<std::uint64_t>(key.size()));
  fixture.Put(owner + offset + 0x18,
              static_cast<std::uint64_t>(key.size()));
}

struct RttiFixture {
  std::uintptr_t vtable_rva;
  std::uintptr_t locator_rva;
  std::uint32_t type_rva;
};

Fixture MakeFixture(std::int32_t selected_index = 0) {
  Fixture fixture{};
  fixture.Add(kGuiSlot, sizeof(std::uintptr_t));
  // These objects are synthetic addresses read only through ReadFixture.
  // The image RVAs below are independently frozen actual 1.20.0.4 pins.
  for (std::uintptr_t base = 0x1000; base <= 0x11000; base += 0x1000) {
    fixture.Add(base, 1024);
  }
  for (const auto item : std::array<RttiFixture, 4>{{
           {0x44D5F40, 0x4A84A28, 0x56B9FA8},
           {0x4500670, 0x4ACC380, 0x5519DC0},
           {0x45008C0, 0x4ACC9A8, 0x5702BC0},
           {0x451B948, 0x4AEC470, 0x57201F8}}}) {
    fixture.Add(kModuleBase + item.vtable_rva - 8, 8);
    fixture.Put(kModuleBase + item.vtable_rva - 8,
                kModuleBase + item.locator_rva);
    fixture.Add(kModuleBase + item.locator_rva, 24);
    fixture.Put(kModuleBase + item.locator_rva, std::uint32_t{1});
    fixture.Put(kModuleBase + item.locator_rva + 4, std::uint32_t{0});
    fixture.Put(kModuleBase + item.locator_rva + 0xC, item.type_rva);
  }

  fixture.Put(kGuiSlot, kApplication);
  fixture.Put(kApplication, kModuleBase + 0x449BDB8);
  fixture.Put(kApplication + 0x1B8, kGuiHost);
  fixture.Put(kGuiHost + 0x58, kGuiContext);
  // GUI host/context first qwords are readable but are not image vtables.
  fixture.Put(kApplication + 0x78, kIdler);
  fixture.Put(kIdler, kModuleBase + 0x44D5F40);
  fixture.Put(kIdler + 0x10, kGfx);
  fixture.Put(kGfx, kModuleBase + 0x4500670);
  fixture.Put(kGfx + 0x08, kHandler);
  fixture.Put(kHandler, kModuleBase + 0x45008C0);
  fixture.Put(kHandler + 0x30, kView);
  fixture.Put(kView, kModuleBase + 0x451B948);
  fixture.Put(kView + 0x60, kBookmarksRoot);
  fixture.Put(kView + 0xD8, kGroup1066);
  fixture.Put(kView + 0x120, kRobertBookmark);
  fixture.Put(kView + 0x128, selected_index);
  fixture.Put(kView + 0x12C, std::int32_t{-1});

  PutScriptKey(fixture, kGroup1066, 0x18, 0,
               "bm_group_1066");
  PutScriptKey(fixture, kRobertBookmark, 0x18, 0xB000,
               "bm_1066_rags_to_riches");
  fixture.Put(kRobertBookmark + 0x40, kRobertDate);
  fixture.Put(kRobertBookmark + 0x150, kGroup1066);
  fixture.Put(kRobertBookmark + 0x160, kRobertCharacter);
  fixture.Put(kRobertBookmark + 0x168, std::uint32_t{5});
  fixture.Put(kRobertBookmark + 0x16C, std::uint32_t{1});
  fixture.Put(kRobertBookmark + 0x170, std::int32_t{-1});
  PutScriptKey(fixture, kRobertCharacter, 0x08, 0xC000, kRobertKey);
  fixture.Put(kRobertCharacter + 0x130, kRobertBookmark);
  PutScriptKey(fixture, kRobertGovernment, 0x18, 0xF000,
               "feudal_government");
  return fixture;
}

ZhongguoScoreboardNativeEnvironmentV1 Environment(
    std::string_view sha256 = xar::ck3_12004::kExecutableSha256) {
  ZhongguoScoreboardNativeEnvironmentV1 environment{};
  environment.module_base = kModuleBase;
  environment.exact_build_admitted = true;
  environment.offline_fixture_function_overrides = true;
  environment.gui_global_slot = reinterpret_cast<void **>(kGuiSlot);
  environment.gui_abi_revision = GuiAbiRevisionV1::crozier12004;
  environment.executable_sha256 = sha256;
  return environment;
}

ZhongguoScoreboardAccessV1 Access(Fixture &fixture) {
  ZhongguoScoreboardAccessV1 access{};
  access.context = &fixture;
  access.read_memory = &ReadFixture;
  return access;
}

void *FakeFinalGovernment(void *, const void *character) noexcept {
  const auto address = reinterpret_cast<std::uintptr_t>(character);
  if (address == kRobertCharacter) {
    return reinterpret_cast<void *>(kRobertGovernment);
  }
  return address == kRurikCharacter
             ? reinterpret_cast<void *>(kRurikGovernment) : nullptr;
}

bool FakeCharacterSetter(void *opaque, void *view,
                         const void *character) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  if (reinterpret_cast<std::uintptr_t>(view) != kView ||
      reinterpret_cast<std::uintptr_t>(character) != kRobertCharacter) {
    return false;
  }
  constexpr std::int32_t index = 0;
  if (!fixture.Store(kView + 0x128, &index, sizeof(index))) return false;
  ++fixture.character_setter_calls;
  return true;
}

bool FakeBookmarkSetter(void *opaque, void *view,
                        const void *bookmark) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  if (reinterpret_cast<std::uintptr_t>(view) != kView ||
      reinterpret_cast<std::uintptr_t>(bookmark) != kRobertBookmark) {
    return false;
  }
  constexpr std::int32_t unselected = -1;
  if (!fixture.Store(kView + 0x120, &kRobertBookmark,
                     sizeof(kRobertBookmark)) ||
      !fixture.Store(kView + 0x128, &unselected, sizeof(unselected)) ||
      !fixture.Store(kView + 0x12C, &unselected, sizeof(unselected))) {
    return false;
  }
  ++fixture.bookmark_setter_calls;
  fixture.setter_order += 'B';
  return true;
}

bool FakeGroupSetter(void *opaque, void *view, const void *group) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  if (reinterpret_cast<std::uintptr_t>(view) != kView ||
      reinterpret_cast<std::uintptr_t>(group) != kGroup1066) return false;
  // The native Group setter picks its default Bookmark; the subsequent
  // Bookmark setter must still resolve and select Robert's target Bookmark.
  constexpr std::int32_t unselected = -1;
  if (!fixture.Store(kView + 0xD8, &kGroup1066, sizeof(kGroup1066)) ||
      !fixture.Store(kView + 0x120, &kDefault1066Bookmark,
                     sizeof(kDefault1066Bookmark)) ||
      !fixture.Store(kView + 0x128, &unselected, sizeof(unselected)) ||
      !fixture.Store(kView + 0x12C, &unselected, sizeof(unselected))) {
    return false;
  }
  ++fixture.group_setter_calls;
  fixture.setter_order += 'G';
  return true;
}

class FrameWriter {
public:
  explicit FrameWriter(std::filesystem::path directory)
      : directory_(std::move(directory)) {
    if (!directory_.empty()) std::filesystem::create_directories(directory_);
  }

  void Write(std::string_view name, const FrontendBookmarkModelProbeV1 &probe) {
    // This is the complete production command_result serializer, not a
    // fixture-specific projection or a handwritten consumer input.
    const auto frame =
        xar::ck3_11906::FrontendBookmarkModelPrivateResultFrameV1(
            name, kProbeStep, probe);
    Require(frame.starts_with("{\"type\":\"command_result\",") &&
                frame.ends_with("}}") &&
                frame.find("\"protocol_version\":1") != std::string::npos &&
                frame.find("\"step\":\"probe-frontend-bookmark-model-v1\"") !=
                    std::string::npos,
            "production serializer did not emit a complete probe frame");
    if (!directory_.empty()) {
      const auto path = directory_ / (std::string(name) + ".json");
      std::ofstream output(path, std::ios::binary | std::ios::trunc);
      output << frame << '\n';
      output.close();
      Require(static_cast<bool>(output), "native probe frame write failed");
    }
    ++frame_count_;
  }

  std::size_t FrameCount() const noexcept { return frame_count_; }

private:
  std::filesystem::path directory_;
  std::size_t frame_count_ = 0;
};

FrontendBookmarkModelProbeV1 Probe(
    Fixture &fixture, FrameWriter &writer, std::string_view name,
    const ZhongguoScoreboardNativeEnvironmentV1 &environment = Environment()) {
  FrontendBookmarkModelProbeV1 output{};
  Require(xar::ck3_11906::ProbeFrontendBookmarkModelV1(
              environment, Access(fixture),
              reinterpret_cast<void *>(kBookmarksRoot), output,
              &FakeFinalGovernment),
          "production bookmark model probe failed");
  writer.Write(name, output);
  return output;
}

FrontendBookmarkSelectionV1 Select(
    Fixture &fixture,
    const ZhongguoScoreboardNativeEnvironmentV1 &environment = Environment()) {
  FrontendBookmarkSelectionV1 output{};
  Require(xar::ck3_11906::SelectSupportedFeudalBookmarkCharacterV1(
              environment, Access(fixture),
              reinterpret_cast<void *>(kBookmarksRoot), output,
              &FakeFinalGovernment, &FakeCharacterSetter),
          "production Robert selection failed");
  return output;
}

void RequireRobertIdentity(const FrontendBookmarkModelProbeV1 &probe,
                           std::int32_t selected_index) {
  Require(probe.candidate_identity_ready &&
              probe.setup_view_matches_bookmarks_root &&
              probe.setup_view_vtable_rva == 0x451B948 &&
              probe.selected_bookmark_key_available &&
              probe.selected_bookmark_key == "bm_1066_rags_to_riches" &&
              probe.selected_bookmark_group_key_available &&
              probe.selected_bookmark_group_key == "bm_group_1066" &&
              probe.selected_date_raw == kRobertDate &&
              probe.selected_date_low_raw == 0x032AEB08 &&
              probe.bookmark_character_keys_available &&
              probe.bookmark_character_count == 1 &&
              probe.bookmark_character_keys[0] == kRobertKey &&
              probe.government_type_keys_available &&
              probe.government_type_keys[0] == "feudal_government" &&
              probe.supported_1066_candidate_present &&
              probe.supported_1066_candidate_index == 0 &&
              probe.supported_1066_candidate_feudal &&
              probe.supported_1066_date_matches &&
              probe.selected_character_index == selected_index &&
              probe.unavailable_reason.empty(),
          "actual-1.20.0.4 Robert identity did not match native model");
}

void SelectedCase(FrameWriter &writer) {
  auto fixture = MakeFixture();
  const auto probe = Probe(fixture, writer, "selected_robert_ready");
  RequireRobertIdentity(probe, 0);
  Require(probe.verified_owner_route == "app_idler_chain" &&
              probe.interface_application_chain_level == 0 &&
              probe.gui_chain_vtable_rvas[0] == 0x449BDB8 &&
              probe.owner_chain_vtable_rvas ==
                  std::array<std::uint64_t, 4>{
                      0x44D5F40, 0x4500670, 0x45008C0, 0x451B948} &&
              probe.owner_chain_rtti_type_rvas ==
                  std::array<std::uint64_t, 4>{
                      0x56B9FA8, 0x5519DC0, 0x5702BC0, 0x57201F8},
          "actual-1.20.0.4 direct owner pins did not match");
  const auto selection = Select(fixture);
  Require(selection.already_selected && !selection.setter_invoked &&
              selection.same_frame_index_matches &&
              fixture.character_setter_calls == 0,
          "already-selected Robert unexpectedly invoked a setter");
}

void UnselectedCase(FrameWriter &writer) {
  auto fixture = MakeFixture(-1);
  const auto before = Probe(fixture, writer, "unselected_robert");
  RequireRobertIdentity(before, -1);
  const auto selection = Select(fixture);
  Require(selection.owner_resolved && selection.target_resolved &&
              !selection.already_selected && selection.setter_invoked &&
              selection.same_frame_index_matches &&
              selection.before.selected_character_index == -1 &&
              selection.unavailable_reason.empty() &&
              fixture.character_setter_calls == 1,
          "unselected Robert did not receive exactly one native setter");
  // New output and a separate production call provide the following frame;
  // selection.same_frame_index_matches is never used as selection evidence.
  const auto following =
      Probe(fixture, writer, "following_selected_robert");
  RequireRobertIdentity(following, 0);
  Require(fixture.character_setter_calls == 1,
          "independent following probe invoked a character setter");
}

void RegistryCase(FrameWriter &writer) {
  auto fixture = MakeFixture(-1);
  fixture.Put(kApplication + 0x78, std::uintptr_t{0});
  fixture.Put(kGuiContext + 0x230, kRegistry);
  fixture.Put(kGuiContext + 0x238, std::uint32_t{1});
  fixture.Put(kGuiContext + 0x23C, std::uint32_t{1});
  fixture.Put(kRegistry, kHandler);
  const auto before = Probe(fixture, writer, "registry_handler_ready");
  RequireRobertIdentity(before, -1);
  Require(before.verified_owner_route == "gui_context_registry" &&
              before.registry_owner_match_count == 1 &&
              before.direct_owner_unavailable_reason ==
                  "frontend_idler_pointer_null" &&
              before.registry_owner_unavailable_reason.empty(),
          "actual-1.20.0.4 registry handler fallback did not resolve");
  const auto selection = Select(fixture);
  Require(selection.owner_resolved && selection.target_resolved &&
              selection.setter_invoked &&
              selection.unavailable_reason.empty() &&
              fixture.character_setter_calls == 1,
          "registry owner did not support one Robert selection");
  const auto following =
      Probe(fixture, writer, "following_registry_handler_robert");
  RequireRobertIdentity(following, 0);
  Require(following.verified_owner_route == "gui_context_registry",
          "following registry frame lost its verified owner route");
}

void RejectedCases(FrameWriter &writer) {
  auto fixture = MakeFixture(-1);
  const auto old_environment = Environment(kOldExecutableSha256);
  const auto old_sha = Probe(fixture, writer, "old_sha_rejected",
                             old_environment);
  Require(!old_sha.candidate_identity_ready &&
              old_sha.unavailable_reason == "frontend_bookmark_build_unbound",
          "old executable identity was admitted by the actual-.4 probe");
  const auto old_selection = Select(fixture, old_environment);
  Require(!old_selection.setter_invoked &&
              old_selection.unavailable_reason ==
                  "frontend_bookmark_build_unbound" &&
              fixture.character_setter_calls == 0,
          "old executable identity reached the character setter");

  fixture.Put(kApplication, kModuleBase + 0x449BDA8);
  const auto old_vtable = Probe(fixture, writer, "old_vtable_rejected");
  Require(!old_vtable.candidate_identity_ready &&
              old_vtable.unavailable_reason == "interface_application_unverified",
          "old application vtable was admitted as actual 1.20.0.4");
  const auto old_vtable_selection = Select(fixture);
  Require(!old_vtable_selection.setter_invoked &&
              fixture.character_setter_calls == 0,
          "old application vtable reached the character setter");
}

void BookmarkDatabaseCase(FrameWriter &writer) {
  auto fixture = MakeFixture();
  for (std::uintptr_t base = 0x14000; base <= 0x20000; base += 0x1000) {
    fixture.Add(base, 1024);
  }
  fixture.Add(kDatabaseSlot, sizeof(std::uintptr_t));
  const auto &rurik = xar::ck3_11906::GetFrontendBookmarkTargetProfileV1(
      FrontendBookmarkSeedTargetV1::rurik_867);
  PutScriptKey(fixture, kRurikBookmark, 0x18, 0x16000,
               rurik.bookmark_key);
  fixture.Put(kRurikBookmark + 0x40,
              std::uint64_t{0xFFFFFFFF00000000ULL | rurik.date_low_raw});
  fixture.Put(kRurikBookmark + 0x150, kGroup867);
  fixture.Put(kRurikBookmark + 0x160, kRurikCharacter);
  fixture.Put(kRurikBookmark + 0x168, std::uint32_t{1});
  fixture.Put(kRurikBookmark + 0x16C, std::uint32_t{1});
  fixture.Put(kRurikBookmark + 0x170, std::int32_t{-1});
  PutScriptKey(fixture, kRurikCharacter, 0x08, 0x17000,
               rurik.character_key);
  fixture.Put(kRurikCharacter + 0x130, kRurikBookmark);
  PutScriptKey(fixture, kRurikGovernment, 0x18, 0x19000,
               rurik.government_key);
  PutScriptKey(fixture, kGroup867, 0x18, 0, "bm_group_867");
  PutScriptKey(fixture, kDefault1066Bookmark, 0x18, 0x20000,
               "bm_1066_fixture_default");
  fixture.Put(kDefault1066Bookmark + 0x40, kRobertDate);
  fixture.Put(kDefault1066Bookmark + 0x150, kGroup1066);

  // The ordinary SetupView collection holds Group pointers. The separate
  // actual-.4 BookmarkDB+0x50 supplies Bookmark pointers, including target.
  fixture.Put(kGroupEntries, kGroup867);
  fixture.Put(kGroupEntries + 8, kGroup1066);
  fixture.Put(kView + 0xC0, kGroupEntries);
  fixture.Put(kView + 0xC8, std::uint32_t{2});
  fixture.Put(kView + 0xCC, std::uint32_t{2});
  fixture.Put(kView + 0xD8, kGroup867);
  fixture.Put(kView + 0x120, kRurikBookmark);
  fixture.Put(kDatabaseSlot, kDatabase);
  fixture.Put(kDatabase, kModuleBase + 0x48D0210);
  fixture.Put(kDatabase + 0x50, kDatabaseEntries);
  fixture.Put(kDatabase + 0x58, std::uint32_t{3});
  fixture.Put(kDatabase + 0x5C, std::uint32_t{3});
  fixture.Put(kDatabaseEntries, kRurikBookmark);
  fixture.Put(kDatabaseEntries + 8, kRobertBookmark);
  fixture.Put(kDatabaseEntries + 16, kDefault1066Bookmark);

  const auto before =
      Probe(fixture, writer, "before_bookmark_db_switch");
  Require(!before.candidate_identity_ready &&
              before.selected_bookmark_group_key == "bm_group_867" &&
              before.selected_bookmark_key == rurik.bookmark_key &&
              before.selected_date_low_raw == rurik.date_low_raw,
          "BookmarkDB fixture did not begin on its separate 867 model");
  FrontendBookmarkChangeV1 change{};
  Require(xar::ck3_11906::SelectSupportedBookmarkV1(
              Environment(), Access(fixture),
              reinterpret_cast<void *>(kBookmarksRoot), change,
              FrontendBookmarkSeedTargetV1::configured_1066,
              &FakeBookmarkSetter, &FakeGroupSetter),
          "production BookmarkDB selection failed");
  Require(change.owner_resolved && change.target_resolved &&
              change.group_setter_invoked && change.setter_invoked &&
              !change.already_selected && change.same_frame_bookmark_matches &&
              change.unavailable_reason.empty() &&
              fixture.group_setter_calls == 1 &&
              fixture.bookmark_setter_calls == 1 &&
              fixture.setter_order == "GB",
          "actual-.4 Group/BookmarkDB selection did not submit in native order");
  const auto switched =
      Probe(fixture, writer, "after_bookmark_db_switch");
  RequireRobertIdentity(switched, -1);
  const auto selection = Select(fixture);
  Require(selection.setter_invoked &&
              selection.unavailable_reason.empty() &&
              fixture.character_setter_calls == 1,
          "BookmarkDB target did not support one Robert selection");
  const auto following =
      Probe(fixture, writer, "following_bookmark_db_robert");
  RequireRobertIdentity(following, 0);
}

} // namespace

int main(int argc, char **argv) {
  try {
    std::filesystem::path output_directory;
    if (argc == 2 &&
        std::string_view(argv[1]) != "--output-directory") {
      output_directory = argv[1];
    } else if (argc == 3 &&
               std::string_view(argv[1]) == "--output-directory") {
      output_directory = argv[2];
    } else if (argc != 1) {
      std::fprintf(stderr,
                   "usage: frontend_bookmark_12004_fixture "
                   "[output-directory | --output-directory output-directory]\n");
      return 2;
    }
    const auto *abi = xar::ck3_12004::BindFrontendBookmarkModel12004(
        kModuleBase, xar::ck3_12004::kExecutableSha256);
    Require(abi != nullptr && abi->application_vtable == 0x449BDB8 &&
                abi->view_vtable == 0x451B948 &&
                abi->bookmark_database_slot == 0x5C67210 &&
                abi->bookmark_database_vtable == 0x48D0210 &&
                abi->final_government_getter == 0x321D180,
            "actual-.4 binder did not return independently frozen pins");
    Require(xar::ck3_12004::BindFrontendBookmarkModel12004(
                kModuleBase, kOldExecutableSha256) == nullptr,
            "actual-.4 binder admitted the old executable SHA");
    Require(xar::ck3_11906::GetFrontendBookmarkTargetProfileV1(
                FrontendBookmarkSeedTargetV1::configured_1066).character_key ==
                kRobertKey,
            "fixture and production probe were not both compiled for Robert");

    FrameWriter writer(std::move(output_directory));
    SelectedCase(writer);
    UnselectedCase(writer);
    RegistryCase(writer);
    RejectedCases(writer);
    BookmarkDatabaseCase(writer);
    std::printf("PASS: actual 1.20.0.4 native bookmark fixture; "
                "%zu complete production frames; "
                "synthetic memory only, no newgame/Start dispatch proof\n",
                writer.FrameCount());
    return 0;
  } catch (const std::exception &error) {
    std::fprintf(stderr, "FAIL: %s\n", error.what());
    return 1;
  }
}
