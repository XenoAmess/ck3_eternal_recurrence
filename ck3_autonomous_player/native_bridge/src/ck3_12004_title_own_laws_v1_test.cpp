#include "xar_bridge/ck3_12004_title_own_laws_v1.hpp"
#include "xar_bridge/ck3_12004_confucian_title_profile.hpp"
#include "xar_bridge/title_own_laws_v1_serializer.hpp"
#include "ck3_12004_foundation_fixture_support.hpp"

#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>

// Production reader, raw title/law leaf, full-ID resolver and serializer linked
// from the actual qualified runtime archive. All object bytes belong to this
// process; only CoreMemory's fixture-owned local-player callback is replaced.
// No native game callback, CK3 process, owner mailbox, pipe or SDK is exercised.
namespace {
namespace current = xar::ck3_12004;
namespace game = xar::game;
using Result = game::ReadTitleOwnLawsV1Result;
constexpr std::int32_t kDate = 53144400;
constexpr std::uint32_t kTitle = 0x81000001U;
constexpr std::uint64_t kRevision = 41;
constexpr std::uintptr_t kImageBase = 0x100000;
static_assert(sizeof(void *) == 8);
int checks = 0;
int scenarios = 0;

void Check(bool condition, std::string_view reason) {
  ++checks;
  if (!condition) throw std::runtime_error(std::string(reason));
}
template <class T> void Put(void *base, std::size_t offset, const T &value) {
  std::memcpy(static_cast<std::byte *>(base) + offset, &value, sizeof(value));
}

struct LawMemory {
  std::array<std::byte, 0x50> bytes{};
  std::string text;
  void Init(std::uint32_t id, std::string_view key) {
    text = key;
    Put(bytes.data(), 0, kImageBase + current::confucian_titles::kCLawPrimaryVtableRva);
    Put(bytes.data(), 0x10, id);
    Put(bytes.data(), 0x38, std::uint32_t{0x4744624F});
    if (text.size() < 16) {
      std::memcpy(bytes.data() + 0x18, text.c_str(), text.size() + 1);
      Put(bytes.data(), 0x30, std::uint64_t{15});
    } else {
      Put(bytes.data(), 0x18, text.c_str());
      Put(bytes.data(), 0x30, static_cast<std::uint64_t>(text.size()));
    }
    Put(bytes.data(), 0x28, static_cast<std::uint64_t>(text.size()));
  }
};

enum class Change { none, date, speed, pause, actor, death, title_generation, title_pointer };
struct Fixture {
  current::fixture::CoreMemory core{kDate, 4, true};
  std::array<std::byte, 0x30> title_storage{};
  std::array<std::byte, 4 * 0x10> title_slots{};
  std::array<std::byte, 0x240> title{};
  std::array<std::byte, 0x240> replacement{};
  std::array<LawMemory, 2> laws;
  std::array<void *, 2> rows{};
  void *storage_slot = title_storage.data();
  current::TitleOwnLawsBindingsV1 bindings{};
  xar::ck3_12002::GetLocalPlayer original_get = nullptr;
  Change change = Change::none;
  std::size_t core_calls = 0;
  std::uint32_t title_id = kTitle;
  static inline Fixture *active = nullptr;

  explicit Fixture(std::uint32_t id = kTitle) : title_id(id) {
    active = this;
    laws[0].Init(17, "partition_succession_law");
    laws[1].Init(5, "single_heir_succession_law");
    rows = {laws[0].bytes.data(), laws[1].bytes.data()};
    Put(title_storage.data(), 0x20, title_slots.data());
    Put(title_storage.data(), 0x2C, std::int32_t{4});
    Put(title_slots.data(), static_cast<std::size_t>(id & 0x00FFFFFFU) * 0x10 + 8,
        title.data());
    Put(title.data(), 0, kImageBase + current::confucian_titles::kCLandedTitlePrimaryVtableRva);
    Put(title.data(), 0x10, id);
    // Raw holder reference is checked for stability by the physical leaf. The
    // new route must not demand a Faith, holder graph or inheritance predicate.
    Put(title.data(), 0x128, std::uint32_t{0xFF000003U});
    Put(title.data(), 0x228, rows.data());
    Put(title.data(), 0x230, std::int32_t{2});
    Put(title.data(), 0x234, std::int32_t{2});
    bindings.enabled = true;
    bindings.core = core.Bindings();
    original_get = bindings.core.get_local_player;
    bindings.core.get_local_player = &GetLocalPlayer;
    bindings.titles.enabled = true;
    bindings.titles.actual4 = true;
    bindings.titles.image_base = kImageBase;
    bindings.titles.primary_title_vtable_rva = current::confucian_titles::kCLandedTitlePrimaryVtableRva;
    bindings.titles.title_holder.enabled = true;
    bindings.titles.title_holder.provinces.enabled = true;
    bindings.titles.title_holder.provinces.landed_title_storage_slot = &storage_slot;
  }
  ~Fixture() { active = nullptr; }
  Fixture(const Fixture &) = delete;
  Fixture &operator=(const Fixture &) = delete;

  static void *GetLocalPlayer(void *jomini) {
    auto &f = *active;
    ++f.core_calls;
    // The production Core reader decodes clock before calling this callback.
    // Change clock after its first decode so the final decode sees the change.
    if (f.core_calls == 1) {
      if (f.change == Change::date) f.core.SetClock(kDate + 24, 4, true);
      if (f.change == Change::speed) f.core.SetClock(kDate, 3, true);
      if (f.change == Change::pause) f.core.SetClock(kDate, 4, false);
    }
    if (f.core_calls == 2) {
      if (f.change == Change::actor)
        f.core.SetPlayingCharacterFullId(current::fixture::CoreMemory::kCharacterId | 0x01000000);
      if (f.change == Change::death) f.core.SetCharacterDead(true);
      if (f.change == Change::title_generation)
        Put(f.title.data(), 0x10, f.title_id ^ 0x01000000U);
      if (f.change == Change::title_pointer) {
        f.replacement = f.title;
        Put(f.title_slots.data(), static_cast<std::size_t>(f.title_id & 0x00FFFFFFU) * 0x10 + 8,
            f.replacement.data());
      }
    }
    return f.original_get(jomini);
  }
};

std::string Step(std::uint32_t id) {
  return std::string(game::kTitleOwnLawsV1StepPrefix) + std::to_string(id);
}
void Wire(const std::filesystem::path &directory, std::string_view name,
          const game::TitleOwnLawsV1 &o, Result result) {
  const auto wire = game::SerializeTitleOwnLawsV1(o, result, 7, kRevision, Step(o.title_id));
  Check(wire.find("\"read_only\":true") != std::string::npos, "wire read-only flag");
  Check(wire.find(current::kExecutableSha256) != std::string::npos, "wire exact4 executable");
  Check(wire.find("xar.ck3.title-own-laws.v1") != std::string::npos, "wire schema");
  if (result == Result::available) {
    Check(wire.find("\"laws\":null") == std::string::npos, "complete available laws serialize");
  } else {
    Check(wire.find("\"laws\":null,\"single_heir_member\":null") != std::string::npos,
          "failed reads never serialize empty/false");
  }
  if (!directory.empty()) {
    std::ofstream file(directory / (std::string(name) + ".json"), std::ios::binary);
    file << wire << '\n';
    if (!file) throw std::runtime_error("wire artifact write failed");
  }
}
void Unavailable(Fixture &f, std::uint32_t id, std::string_view reason) {
  game::TitleOwnLawsV1 o;
  o.available = true; o.native_law_count = 1; o.laws.emplace(); o.single_heir_member = true;
  Check(current::ReadTitleOwnLawsV1(f.bindings, id, o) == Result::unavailable, reason);
  Check(!o.available && !o.native_law_count && !o.laws && !o.single_heir_member,
        "unavailable clears all former material values");
  Check(!o.unavailable_reason.empty(), "unavailable reason present");
  ++scenarios;
}
void Parser() {
  for (const auto id : {std::uint32_t{0}, std::uint32_t{2147483648U}, UINT32_MAX - 1}) {
    std::uint32_t parsed = UINT32_MAX;
    Check(game::ParseTitleOwnLawsStepV1(Step(id), parsed) && parsed == id,
          "canonical unsigned complete title ID accepted");
  }
  for (const std::string_view bad : {"", "0", "query-title-own-laws-v1-", "query-title-own-laws-v1-00",
      "query-title-own-laws-v1-01", "query-title-own-laws-v1-4294967295",
      "query-title-own-laws-v1-4294967296", "query-title-own-laws-v1-999999999999999999999",
      "query-title-own-laws-v1--1", "query-title-own-laws-v1-+1", "query-title-own-laws-v1-1x",
      "query-title-own-laws-v1-1,2", "query-title-own-laws-v1- 1", "query-title-own-laws-v1-1 "}) {
    std::uint32_t parsed = 9;
    Check(!game::ParseTitleOwnLawsStepV1(bad, parsed) && parsed == UINT32_MAX,
          "bad selector grammar rejected and sentinel reset");
  }
  ++scenarios;
}
void Bindings() {
  current::fixture::CoreMemory core;
  const auto b = current::BindTitleOwnLawsImageV1(kImageBase, current::kExecutableSha256, core.Bindings());
  Check(b.enabled && b.titles.enabled && b.titles.actual4, "actual4 pure address binder");
  Check(b.titles.primary_title_vtable_rva == current::confucian_titles::kCLandedTitlePrimaryVtableRva,
        "actual4 title type operand bound");
  Check(!current::BindTitleOwnLawsImageV1(kImageBase, xar::ck3_12003::kExecutableSha256, core.Bindings()).enabled,
        "old build never admitted");
  Check(!current::BindTitleOwnLawsImageV1(0, current::kExecutableSha256, core.Bindings()).enabled,
        "zero image rejected");
  Check(!current::BindTitleOwnLawsImageV1(kImageBase, current::kExecutableSha256, {}).enabled,
        "disabled core rejected");
  ++scenarios;
}
void Physical(const std::filesystem::path &directory) {
  for (const auto id : {std::uint32_t{0}, kTitle}) {
    Fixture f{id}; game::TitleOwnLawsV1 o;
    Check(current::ReadTitleOwnLawsV1(f.bindings, id, o) == Result::available, "physical title query available");
    Check(o.title_id == id && o.date_raw == kDate && o.actor_character_id == current::fixture::CoreMemory::kCharacterId,
          "selector and actual current player scope preserved");
    Check(o.native_law_count == 2 && o.laws && o.laws->size() == 2, "complete two-law count");
    Check((*o.laws)[0].native_definition_id == 17 && (*o.laws)[1].native_definition_id == 5,
          "native law order preserved without sorting");
    Check(o.single_heir_member.has_value() && *o.single_heir_member, "full single-heir key membership");
    Check(f.core_calls == 2, "Core sampled before and after physical leaf");
    Wire(directory, id == 0 ? "title-zero-present" : "title-high-generation-present", o, Result::available);
    ++scenarios;
  }
  {
    Fixture f; Put(f.title.data(), 0x228, static_cast<void *>(nullptr));
    Put(f.title.data(), 0x230, std::int32_t{0}); Put(f.title.data(), 0x234, std::int32_t{0});
    game::TitleOwnLawsV1 o;
    Check(current::ReadTitleOwnLawsV1(f.bindings, kTitle, o) == Result::available, "legitimate empty physical array");
    Check(o.native_law_count == 0 && o.laws && o.laws->empty() && o.single_heir_member == false,
          "empty is complete zero and false membership");
    Wire(directory, "title-empty", o, Result::available); ++scenarios;
  }
  {
    Fixture f; Put(f.title.data(), 0x234, std::int32_t{1}); game::TitleOwnLawsV1 o;
    Check(current::ReadTitleOwnLawsV1(f.bindings, kTitle, o) == Result::available &&
        o.native_law_count == 1 && o.single_heir_member == false, "different full law key is absent");
    Wire(directory, "title-single-heir-absent", o, Result::available); ++scenarios;
  }
  {
    Fixture f; Put(f.laws[0].bytes.data(), 0x38, std::uint32_t{0}); game::TitleOwnLawsV1 o;
    const auto result = current::ReadTitleOwnLawsV1(f.bindings, kTitle, o);
    Check(result == Result::unavailable && !o.laws, "foreign law type unavailable");
    Wire(directory, "title-law-type-unavailable", o, result); ++scenarios;
  }
  for (const auto change : {Change::date, Change::speed, Change::pause, Change::actor,
      Change::death, Change::title_generation, Change::title_pointer}) {
    Fixture f; f.change = change; Unavailable(f, kTitle, "changed scope/complete identity rejected");
  }
  { Fixture f; Unavailable(f, UINT32_MAX, "sentinel is absence, not a title"); }
  { Fixture f; Unavailable(f, kTitle ^ 0x01000000U, "reused low24 with old generation rejected"); }
  { Fixture f; f.bindings.titles.actual4 = false; Unavailable(f, kTitle, "foreign build binding rejected"); }
  { Fixture f; f.core.SetClock(kDate, 4, false); Unavailable(f, kTitle, "unpaused frame rejected"); }
  { Fixture f; f.core.SetCharacterDead(true); Unavailable(f, kTitle, "dead current actor rejected"); }
  { Fixture f; f.core.SetMenu(); Unavailable(f, kTitle, "no current player frame rejected"); }
  { Fixture f; Put(f.title.data(), 0x234, std::int32_t{-1}); Unavailable(f, kTitle, "negative count is failure"); }
  { Fixture f; Put(f.title.data(), 0x234, std::int32_t{257}); Unavailable(f, kTitle, "overbound count is failure"); }
  { Fixture f; Put(f.title.data(), 0x230, std::int32_t{1}); Unavailable(f, kTitle, "count exceeds capacity"); }
  { Fixture f; Put(f.title.data(), 0, std::uintptr_t{0}); Unavailable(f, kTitle, "foreign title vtable rejected"); }
  { Fixture f; f.rows[1] = f.rows[0]; Unavailable(f, kTitle, "duplicate own-law pointer rejected"); }
  { Fixture f; Put(f.laws[1].bytes.data(), 0x10, std::uint32_t{17}); Unavailable(f, kTitle, "duplicate law definition ID rejected"); }
  { Fixture f; f.laws[1].Init(5, "partition_succession_law"); Unavailable(f, kTitle, "duplicate full law key rejected"); }
  { Fixture f; Put(f.laws[1].bytes.data(), 0x28, std::uint64_t{0}); Unavailable(f, kTitle, "empty law key rejected"); }
  { Fixture f; Put(f.laws[1].bytes.data(), 0x30, std::uint64_t{16}); Unavailable(f, kTitle, "key exceeds key capacity"); }
  { Fixture f; f.laws[1].text[0] = '\n'; Unavailable(f, kTitle, "non-key control byte rejected"); }
  {
    game::TitleOwnLawsV1 incomplete; incomplete.available = true; incomplete.title_id = kTitle;
    const auto wire = game::SerializeTitleOwnLawsV1(incomplete, Result::available, 7, kRevision, Step(kTitle));
    Check(wire.find("\"available\":false") != std::string::npos &&
        wire.find("\"laws\":null") != std::string::npos, "partial DTO never becomes available empty");
    ++scenarios;
  }
}
} // namespace

int main(int argc, char **argv) {
  try {
    if (argc > 2) throw std::runtime_error("usage: fixture [new-wire-artifact-directory]");
    const std::filesystem::path directory = argc == 2 ? argv[1] : "";
    if (!directory.empty()) std::filesystem::create_directories(directory);
    Parser(); Bindings(); Physical(directory);
    std::cout << "{\"checks\":" << checks << ",\"scenarios\":" << scenarios
              << ",\"synthetic_components_only\":true,\"actual_game_calls\":0}\n";
    return 0;
  } catch (const std::exception &e) {
    std::cerr << "FAIL: " << e.what() << '\n'; return 1;
  }
}
