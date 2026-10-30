#include "xar_bridge/raiktor_actual_truce_expiry_v1.hpp"
// D-only optional source-window proof. The ordinary CTest target has no D dependency.
#if defined(XAR_CK3_TRUCE_TEST_BRIDGE_WINDOW)
#include "../bridge-parser-window.cpp.txt"
#endif

#include <cstdlib>
#include <array>
#include <cstdio>
#include <cstring>
#include <limits>
#include "xar_bridge/ck3_12004_actual_truce_expiry.hpp"
#include <cstdint>
#include <string>

namespace {

std::optional<std::int32_t> ParseTruceStepTestRoute(std::string_view step) noexcept {
#if defined(XAR_CK3_TRUCE_TEST_BRIDGE_WINDOW)
  return RaiktorActualTruceExpiryQueryStep(step);
#else
  return xar::ck3_11906::ParseRaiktorActualTruceExpiryStepV1(step);
#endif
}

struct Fixture {
  xar::game::Snapshot snapshot;
  std::int32_t owner = 1;
  std::int32_t toward = 2;
  std::int32_t expiry = 50000;
  bool has_truce = true;
  bool mutate_second_snapshot = false;
  int snapshot_reads = 0;
};

Fixture *g_fixture = nullptr;

void Require(bool condition) {
  if (!condition) std::abort();
}

bool ReadSnapshot(void *context, xar::game::Snapshot &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  output = fixture.snapshot;
  if (++fixture.snapshot_reads == 2 && fixture.mutate_second_snapshot) {
    ++output.date_raw;
  }
  return true;
}

void *ResolveCharacter(void *context, std::int32_t id) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  if (id == fixture.snapshot.played_character_id) return &fixture.owner;
  if (id == fixture.toward) return &fixture.toward;
  return nullptr;
}

bool HasTruce(void *, void *) { return g_fixture->has_truce; }
const void *GetEndDate(void *, void *) { return &g_fixture->expiry; }

xar::ck3_11906::RaiktorActualTruceExpiryAccessV1 Access(Fixture &fixture) {
  g_fixture = &fixture;
  return {true, &fixture, &ReadSnapshot, &ResolveCharacter, &HasTruce,
          &GetEndDate};
}

Fixture ReadyFixture() {
  Fixture fixture{};
  fixture.snapshot.date_raw = 10000;
  fixture.snapshot.paused = true;
  fixture.snapshot.map_ready = true;
  fixture.snapshot.player_id = 0;
  fixture.snapshot.has_played_character = true;
  fixture.snapshot.played_character_id = 1;
  fixture.snapshot.played_character_alive = true;
  return fixture;
}


// Current-build production ResolveCoreCharacter/ReadCoreSnapshot and wrapper
// are exercised on these owned software byte arrays. No image/Game is used.
struct FullIdFixture {
  std::array<std::byte, 0xA8> game{};
  std::array<std::byte, 0x28> jomini{};
  std::array<std::byte, 0x200> players{};
  std::array<std::byte, 0x100> player{};
  std::array<std::byte, 0x22400> data{};
  std::array<std::byte, 0xE0> entry{};
  std::array<void *, 1> entries{};
  std::array<std::byte, 0x30> storage{};
  std::array<std::byte, 18 * 0x10> slots{};
  std::array<std::byte, 0x200> owner{};
  std::array<std::byte, 0x200> toward{};
  void *game_pointer = game.data();
  void *jomini_pointer = jomini.data();
  void *storage_pointer = storage.data();
  std::int32_t expiry = 50000;
  int has_calls = 0;
  int expiry_calls = 0;
  bool wrong_native_pointer = false;
  xar::ck3_12004::ActualTruceExpiryBindings12004 bindings{};
};

FullIdFixture *g_full_id_fixture = nullptr;

template <typename T, std::size_t Size>
void FullIdStore(std::array<std::byte, Size> &bytes, std::size_t offset,
                 const T &value) {
  Require(offset <= bytes.size() && sizeof(value) <= bytes.size() - offset);
  std::memcpy(bytes.data() + offset, &value, sizeof(value));
}

void *FullIdLocalPlayer(void *) { return g_full_id_fixture->player.data(); }

bool FullIdHasTruce(void *owner, void *toward) {
  auto &f = *g_full_id_fixture;
  ++f.has_calls;
  f.wrong_native_pointer = f.wrong_native_pointer ||
      owner != f.owner.data() || toward != f.toward.data();
  return !f.wrong_native_pointer;
}

const void *FullIdExpiry(void *owner, void *toward) {
  auto &f = *g_full_id_fixture;
  ++f.expiry_calls;
  f.wrong_native_pointer = f.wrong_native_pointer ||
      owner != f.owner.data() || toward != f.toward.data();
  return f.wrong_native_pointer ? nullptr : &f.expiry;
}

void InitializeFullId(FullIdFixture &f, std::int32_t owner_id,
                      std::int32_t toward_id) {
  namespace n = xar::ck3_12004;
  g_full_id_fixture = &f;
  FullIdStore(f.game, n::kGameStateDateOffset, std::int32_t{10000});
  FullIdStore(f.game, n::kGameStateSpeedOffset, std::int32_t{0});
  FullIdStore(f.game, n::kGameStateDataOffset,
              static_cast<void *>(f.data.data()));
  FullIdStore(f.jomini, n::kJominiPlayersOffset,
              static_cast<void *>(f.players.data()));
  FullIdStore(f.jomini, n::kJominiPausedOffset, std::uint8_t{1});
  FullIdStore(f.players, n::kPlayersLocalPlayerIdOffset, std::int32_t{0});
  FullIdStore(f.player, n::kPlayerIdOffset, std::int32_t{0});
  f.entries[0] = f.entry.data();
  FullIdStore(f.data,
      n::kPlayerCharacterManagerOffset + n::kPlayerManagerEntriesOffset,
      static_cast<void *>(f.entries.data()));
  FullIdStore(f.data,
      n::kPlayerCharacterManagerOffset + n::kPlayerManagerCountOffset,
      std::int32_t{1});
  FullIdStore(f.entry, n::kPlayerEntryLocalPlayerIdOffset, std::int32_t{0});
  FullIdStore(f.entry, n::kPlayerEntryCharacterIdOffset, owner_id);
  FullIdStore(f.storage, n::kCharacterStorageSlotsOffset,
              static_cast<void *>(f.slots.data()));
  FullIdStore(f.storage, n::kCharacterStorageCapacityOffset, std::int32_t{18});
  FullIdStore(f.owner, n::kCharacterFullIdOffset, owner_id);
  FullIdStore(f.toward, n::kCharacterFullIdOffset, toward_id);
  const auto install_slot = [&f](std::int32_t id, void *character) {
    if (id == -1) return;
    const auto index = static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
    Require(index < 18);
    FullIdStore(f.slots,
        static_cast<std::size_t>(index) * xar::ck3_12004::kCharacterStorageSlotStride +
            xar::ck3_12004::kCharacterStorageObjectOffset, character);
  };
  install_slot(owner_id, f.owner.data());
  install_slot(toward_id, f.toward.data());
  f.bindings.exact_build_admitted = true;
  f.bindings.core.enabled = true;
  f.bindings.core.game_state_slot = &f.game_pointer;
  f.bindings.core.jomini_state_slot = &f.jomini_pointer;
  f.bindings.core.character_storage_slot = &f.storage_pointer;
  f.bindings.core.get_local_player = &FullIdLocalPlayer;
  f.bindings.has_truce = &FullIdHasTruce;
  f.bindings.get_truce_end_date = &FullIdExpiry;
}

int TestAndEmitFullIdCurrentBuild() {
  using Result = xar::game::ReadRaiktorActualTruceExpiryResultV1;
  struct Case { const char *name; std::int32_t owner; std::int32_t toward; bool valid; };
  constexpr std::int32_t minimum = std::numeric_limits<std::int32_t>::min();
  constexpr std::array<Case, 7> cases{{
      {"positive_control", 17, 2, true},
      {"toward_zero_exact_slot", 17, 0, true},
      {"owner_zero_exact_slot", 0, 17, true},
      {"toward_MIN_exact_generation", 17, minimum, true},
      {"owner_MIN_exact_generation", minimum, 17, true},
      {"toward_minus1_sentinel", 17, -1, false},
      {"owner_minus1_sentinel", -1, 17, false}}};
  int failed = 0;
  for (const auto &c : cases) {
    FullIdFixture f{};
    InitializeFullId(f, c.owner, c.toward);

    // Construct complete step string for parser
    const std::string step = std::string(xar::ck3_11906::kRaiktorActualTruceExpiryV1StepPrefix) + std::to_string(c.toward);
    const auto parsed_toward = xar::ck3_11906::ParseRaiktorActualTruceExpiryStepV1(step);
    const bool parser_valid = parsed_toward.has_value();
    const bool parser_matches = parser_valid && parsed_toward.value() == c.toward;

    bool reader_invoked = false;
    xar::game::RaiktorActualTruceExpirySnapshotV1 out{};
    Result result = Result::unavailable;

    if (parser_valid) {
      reader_invoked = true;
      result = xar::ck3_12004::ReadActualTruceExpiry12004(
          f.bindings, parsed_toward.value(), out);
    }

    const bool owner_resolved =
        xar::ck3_12004::ResolveCoreCharacter(f.bindings.core, c.owner) == f.owner.data();
    const bool toward_resolved =
        xar::ck3_12004::ResolveCoreCharacter(f.bindings.core, c.toward) == f.toward.data();

    const bool available = result == Result::available &&
        out.actual_expiry_observable && out.readiness && out.same_frame_stable &&
        out.owner_character_id == c.owner && out.toward_character_id == c.toward &&
        out.current_date_raw == 10000 && out.expiry_date_raw == 50000 &&
        f.has_calls == 2 && f.expiry_calls == 2 && !f.wrong_native_pointer;

    // Pass criteria: Valid cases must parse, resolve, and be available. Invalid cases must fail appropriately.
    bool pass = false;
    if (c.valid) {
      pass = parser_matches && owner_resolved && toward_resolved && available && reader_invoked;
    } else if (c.toward == -1) {
      pass = !parser_valid && !reader_invoked && f.has_calls == 0 &&
          f.expiry_calls == 0 && !out.actual_expiry_observable && !out.readiness;
    } else {
      // The query target is valid; the current played owner is the sentinel.
      pass = parser_matches && reader_invoked &&
          result == Result::no_played_character && f.has_calls == 0 &&
          f.expiry_calls == 0 && !out.actual_expiry_observable && !out.readiness;
    }

    if (!pass) ++failed;
    const auto wire = xar::ck3_12004::SerializeActualTruceExpiry12004(out);
    std::printf("{\"case\":\"%s\",\"owner\":%d,\"toward\":%d,\"parser_valid\":%s,\"reader_invoked\":%s,\"owner_resolved\":%s,\"toward_resolved\":%s,\"result\":%u,\"has_calls\":%d,\"expiry_calls\":%d,\"pass\":%s,\"payload\":%s}\n",
        c.name, static_cast<int>(c.owner), static_cast<int>(c.toward),
        parser_valid ? "true" : "false",
        reader_invoked ? "true" : "false",
        owner_resolved ? "true" : "false", toward_resolved ? "true" : "false",
        static_cast<unsigned>(result), f.has_calls, f.expiry_calls,
        pass ? "true" : "false", wire.c_str());
  }

  return failed == 0 ? 0 : 1;
}


int TestParserReviewContract() {
  struct Case { const char *name; const char *input; bool bridge; bool accepted; std::int32_t expected; };
  constexpr std::array<Case, 8> cases{{
      {"public_full_zero", "query-raiktor-actual-truce-expiry-v1-0", false, true, 0},
      {"public_full_MIN", "query-raiktor-actual-truce-expiry-v1--2147483648", false, true, std::numeric_limits<std::int32_t>::min()},
      {"public_bare_zero_rejected", "0", false, false, 0},
      {"public_bare_negative_zero_rejected", "-0", false, false, 0},
      {"bridge_negative_zero_rejected", "query-raiktor-actual-truce-expiry-v1--0", true, false, 0},
      {"bridge_full_zero", "query-raiktor-actual-truce-expiry-v1-0", true, true, 0},
      {"bridge_full_MIN", "query-raiktor-actual-truce-expiry-v1--2147483648", true, true, std::numeric_limits<std::int32_t>::min()},
      {"bridge_wrong_prefix", "query-else-0", true, false, 0}}};
  int failed = 0;
  for (const auto &c : cases) {
    const auto actual = c.bridge ? ParseTruceStepTestRoute(c.input) :
        xar::ck3_11906::ParseRaiktorActualTruceExpiryStepV1(c.input);
    const bool pass = actual.has_value() == c.accepted &&
        (!actual.has_value() || *actual == c.expected);
    if (!pass) ++failed;
    std::printf("{\"case\":\"%s\",\"accepted\":%s,\"value\":%d,\"pass\":%s}\n",
        c.name, actual.has_value() ? "true" : "false",
        static_cast<int>(actual.value_or(-1)), pass ? "true" : "false");
  }
  return failed == 0 ? 0 : 1;
}


int TestParserBoundaries() {
  struct Case { const char *name; const char *input; bool full_step; bool accepted; std::int32_t expected; };
  const std::array cases{
      Case{"zero", "0", false, true, 0},
      Case{"positive17", "17", false, true, 17},
      Case{"negative2", "-2", false, true, -2},
      Case{"MIN", "-2147483648", false, true, std::numeric_limits<std::int32_t>::min()},
      Case{"MAX", "2147483647", false, true, std::numeric_limits<std::int32_t>::max()},
      Case{"negative_generation", "-16777216", false, true, -16777216},
      Case{"sentinel", "-1", false, false, 0},
      Case{"empty_suffix", "", false, false, 0},
      Case{"plus_zero", "+0", false, false, 0},
      Case{"plus_positive", "+17", false, false, 0},
      Case{"leading_zeros", "00", false, false, 0},
      Case{"leading_positive_zero", "017", false, false, 0},
      Case{"negative_zeros", "-00", false, false, 0},
      Case{"negative_zero", "-0", false, false, 0},
      Case{"negative_leading_zero", "-02", false, false, 0},
      Case{"leading_space", " 17", false, false, 0},
      Case{"trailing_space", "17 ", false, false, 0},
      Case{"tab", "\t17", false, false, 0},
      Case{"newline", "17\n", false, false, 0},
      Case{"bool_true", "true", false, false, 0},
      Case{"bool_false", "false", false, false, 0},
      Case{"null_text", "null", false, false, 0},
      Case{"decimal", "17.0", false, false, 0},
      Case{"exponent", "1e2", false, false, 0},
      Case{"trailing_text", "17x", false, false, 0},
      Case{"overflow", "2147483648", false, false, 0},
      Case{"underflow", "-2147483649", false, false, 0},
      Case{"unsigned_reinterpretation", "4294967294", false, false, 0},
      Case{"very_long_integer", "999999999999999999999999999999999999", false, false, 0},
      Case{"empty_step", "", true, false, 0},
      Case{"wrong_prefix", "query-other-0", true, false, 0},
      Case{"bare_zero", "0", true, false, 0},
      Case{"bare_MIN", "-2147483648", true, false, 0}};
  int failed = 0;
  for (const auto &c : cases) {
    const std::string step = c.full_step ? std::string(c.input) :
        std::string(xar::ck3_11906::kRaiktorActualTruceExpiryV1StepPrefix) + c.input;
    const auto actual = xar::ck3_11906::ParseRaiktorActualTruceExpiryStepV1(step);
    const auto bridge = ParseTruceStepTestRoute(step);
    const bool pass = actual == bridge && actual.has_value() == c.accepted &&
        (!actual.has_value() || *actual == c.expected);
    if (!pass) ++failed;
    std::printf("{\"case\":\"parser_%s\",\"accepted\":%s,\"value\":%d,\"pass\":%s}\n",
        c.name, actual.has_value() ? "true" : "false",
        static_cast<int>(actual.value_or(-1)), pass ? "true" : "false");
  }
  return failed == 0 ? 0 : 1;
}

int TestGenerationMismatch() {
  using Result = xar::game::ReadRaiktorActualTruceExpiryResultV1;
  constexpr auto minimum = std::numeric_limits<std::int32_t>::min();
  int failed = 0;
  for (const bool owner_role : {false, true}) {
    FullIdFixture f{};
    InitializeFullId(f, owner_role ? minimum : 17, owner_role ? 17 : minimum);
    auto &character = owner_role ? f.owner : f.toward;
    const bool resolved_before = xar::ck3_12004::ResolveCoreCharacter(
        f.bindings.core, minimum) == character.data();
    // Both MIN and0 use slot0. The slot pointer is retained; generation differs.
    FullIdStore(character, xar::ck3_12004::kCharacterFullIdOffset, std::int32_t{0});
    const bool stale_rejected = xar::ck3_12004::ResolveCoreCharacter(
        f.bindings.core, minimum) == nullptr;
    const bool replacement_resolved = xar::ck3_12004::ResolveCoreCharacter(
        f.bindings.core, 0) == character.data();
    xar::game::RaiktorActualTruceExpirySnapshotV1 out{};
    const auto result = xar::ck3_12004::ReadActualTruceExpiry12004(
        f.bindings, owner_role ? 17 : minimum, out);
    const bool pass = resolved_before && stale_rejected && replacement_resolved &&
        result == (owner_role ? Result::no_played_character : Result::toward_character_not_found) &&
        f.has_calls == 0 && f.expiry_calls == 0 &&
        !out.actual_expiry_observable && !out.readiness;
    if (!pass) ++failed;
    std::printf("{\"case\":\"generation_%s_MIN_to_zero\",\"resolved_before\":%s,\"stale_rejected\":%s,\"replacement_resolved\":%s,\"result\":%u,\"has_calls\":%d,\"expiry_calls\":%d,\"pass\":%s}\n",
        owner_role ? "owner" : "toward", resolved_before ? "true" : "false",
        stale_rejected ? "true" : "false", replacement_resolved ? "true" : "false",
        static_cast<unsigned>(result), f.has_calls, f.expiry_calls, pass ? "true" : "false");
  }
  return failed == 0 ? 0 : 1;
}

int TestExpiryBoundaries() {
  using Result = xar::game::ReadRaiktorActualTruceExpiryResultV1;
  int failed = 0;
  for (const std::int32_t expiry : {10000, 9999}) {
    FullIdFixture f{};
    InitializeFullId(f, 17, std::numeric_limits<std::int32_t>::min());
    f.expiry = expiry;
    xar::game::RaiktorActualTruceExpirySnapshotV1 out{};
    const auto result = xar::ck3_12004::ReadActualTruceExpiry12004(
        f.bindings, std::numeric_limits<std::int32_t>::min(), out);
    const bool pass = result == Result::unstable_snapshot &&
        f.has_calls == 2 && f.expiry_calls == 2 &&
        !out.actual_expiry_observable && !out.readiness;
    if (!pass) ++failed;
    std::printf("{\"case\":\"MIN_expiry_%d\",\"result\":%u,\"has_calls\":%d,\"expiry_calls\":%d,\"pass\":%s}\n",
        static_cast<int>(expiry), static_cast<unsigned>(result),
        f.has_calls, f.expiry_calls, pass ? "true" : "false");
  }
  return failed == 0 ? 0 : 1;
}

} // namespace

int main(int argc, char **argv) {
  if (argc == 2 && std::strcmp(argv[1], "--parser-boundaries") == 0)
    return TestParserBoundaries();
  if (argc == 2 && std::strcmp(argv[1], "--generation-mismatch") == 0)
    return TestGenerationMismatch();
  if (argc == 2 && std::strcmp(argv[1], "--expiry-boundaries") == 0)
    return TestExpiryBoundaries();
  if (argc == 2 && std::strcmp(argv[1], "--parser-review") == 0)
    return TestParserReviewContract();
  if (argc == 2 && std::strcmp(argv[1], "--emit-full-id") == 0)
    return TestAndEmitFullIdCurrentBuild();
  using namespace xar;
  {
    auto fixture = ReadyFixture();
    game::RaiktorActualTruceExpirySnapshotV1 output{};
    const auto result = ck3_11906::ReadRaiktorActualTruceExpiryV1(
        Access(fixture), fixture.toward, output);
    Require(result == game::ReadRaiktorActualTruceExpiryResultV1::available);
    Require(output.status ==
           game::RaiktorActualTruceExpiryStatusV1::available);
    Require(output.owner_character_id == 1);
    Require(output.toward_character_id == 2);
    Require(output.actual_expiry_observable);
    Require(output.expiry_date_raw == fixture.expiry);
    Require(output.same_frame_stable);
    Require(output.readiness);
    const auto wire = ck3_11906::SerializeRaiktorActualTruceExpiryV1(output);
    Require(wire.find("\"actual_expiry_observable\":true") !=
           std::string::npos);
    Require(wire.find("\"expiry_date_raw\":50000") != std::string::npos);
  }
  {
    auto fixture = ReadyFixture();
    fixture.has_truce = false;
    game::RaiktorActualTruceExpirySnapshotV1 output{};
    const auto result = ck3_11906::ReadRaiktorActualTruceExpiryV1(
        Access(fixture), fixture.toward, output);
    Require(result == game::ReadRaiktorActualTruceExpiryResultV1::no_truce);
    Require(output.same_frame_stable);
    Require(!output.actual_expiry_observable);
    Require(!output.readiness);
    const auto wire = ck3_11906::SerializeRaiktorActualTruceExpiryV1(output);
    Require(wire.find("\"expiry_date_raw\":null") != std::string::npos);
  }
  {
    auto fixture = ReadyFixture();
    fixture.mutate_second_snapshot = true;
    game::RaiktorActualTruceExpirySnapshotV1 output{};
    const auto result = ck3_11906::ReadRaiktorActualTruceExpiryV1(
        Access(fixture), fixture.toward, output);
    Require(result ==
           game::ReadRaiktorActualTruceExpiryResultV1::unstable_snapshot);
    Require(!output.readiness);
  }
  {
    auto fixture = ReadyFixture();
    fixture.snapshot.paused = false;
    game::RaiktorActualTruceExpirySnapshotV1 output{};
    const auto result = ck3_11906::ReadRaiktorActualTruceExpiryV1(
        Access(fixture), fixture.toward, output);
    Require(result ==
           game::ReadRaiktorActualTruceExpiryResultV1::requires_paused);
    Require(!output.readiness);
  }
  {
    auto fixture = ReadyFixture();
    game::RaiktorActualTruceExpirySnapshotV1 output{};
    auto access = Access(fixture);
    access.exact_build_admitted = false;
    const auto result = ck3_11906::ReadRaiktorActualTruceExpiryV1(
        access, fixture.toward, output);
    Require(result == game::ReadRaiktorActualTruceExpiryResultV1::unavailable);
    Require(!output.readiness);
  }
  // The existing CTest target invokes main without arguments; cover new contract there.
  int result = TestAndEmitFullIdCurrentBuild();
  result |= TestParserReviewContract();
  result |= TestParserBoundaries();
  result |= TestGenerationMismatch();
  result |= TestExpiryBoundaries();
  return result;
}
