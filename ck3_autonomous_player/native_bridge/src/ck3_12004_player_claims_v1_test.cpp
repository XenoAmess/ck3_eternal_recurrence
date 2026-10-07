#include "xar_bridge/ck3_12004_player_claims_v1.hpp"
#include "xar_bridge/ck3_12004_war_cash_claim_terms.hpp"
#include "xar_bridge/player_claims_v1_serializer.hpp"
#include "ck3_12004_foundation_fixture_support.hpp"

#include <array>
#include <cstring>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <map>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

// This standalone leaf target retains the province resolver TU, whose other
// functions refer to army helpers. The actual link requires these two symbols
// even with /Gy and /OPT:REF. Claims must never call either helper: a reachable
// seam is an explicit failing process, not fabricated army data or ABI credit.
namespace xar::ck3_12002 {
ArmyBindings BindArmyImage(std::uintptr_t, std::string_view) noexcept {
  std::fputs("FAIL: claims fixture reached unsupported army image binding\n", stderr);
  std::abort();
}
void *ResolveInternalArmy(const ArmyBindings &, std::int32_t) noexcept {
  std::fputs("FAIL: claims fixture reached unsupported internal army resolution\n", stderr);
  std::abort();
}
} // namespace xar::ck3_12002

// Caller-owned component memory and a synthetic getter, never a CK3 module.
// The getter writes the independently qualified Crozier optional layout.
// Reader, full-ID resolvers, parser and serializer are the production functions.
// This fixture does not exercise a live getter, bridge route, or owner mailbox.
namespace {
namespace current = xar::ck3_12004;
namespace old_layout = xar::ck3_12002;
namespace game = xar::game;
using Result = game::ReadPlayerClaimsV1Result;
constexpr std::int32_t kDate = 53288256;
constexpr std::int32_t kActor = current::fixture::CoreMemory::kCharacterId;
constexpr std::int32_t kNextActor = kActor | 0x01000000;
constexpr std::int32_t kAbsent = 0;
constexpr std::int32_t kStrongExplicit = 0x01000001;
constexpr std::int32_t kStrongImplicit = 0x03000002;
constexpr std::int32_t kWeakImplicit = 0x7F000003;
constexpr std::int32_t kWeakExplicit = 0x06000004;
constexpr std::int32_t kMissing = 0x05000005;
constexpr std::uint64_t kRevision = 73;

static_assert(sizeof(void *) == 8, "This fixture exercises the qualified x64 layout");
static_assert(sizeof(old_layout::ClaimTermsStorage) == 0x20);

int checks = 0;
int scenarios = 0;
std::uint64_t wire_sequence = 0;
void Check(bool condition, std::string_view message) {
  ++checks;
  if (!condition) throw std::runtime_error(std::string(message));
}
template <class T> void Put(void *object, std::size_t offset, const T &value) {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
}
template <class T> T Get(const void *object, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value));
  return value;
}

enum class Fault {
  none, wrong_return, invalid_present, wrong_vtable, wrong_claim_generation,
  invalid_strong, invalid_implicit, row_changes_on_second_read,
  played_character_changes, title_pointer_changes,
  title_generation_changes_after_second_read, date_changes, pause_changes,
  speed_changes
};
struct ClaimRow {
  bool present;
  std::uint8_t strong;
  std::uint8_t implicit;
};

struct Fixture {
  current::fixture::CoreMemory core{kDate, 4, true};
  std::array<std::byte, 0x30> title_storage{};
  std::array<std::byte, 8 * 0x10> title_slots{};
  std::map<std::int32_t, std::array<std::byte, 0x20>> titles;
  std::map<std::int32_t, ClaimRow> rows;
  std::array<std::byte, 0x20> replacement_title{};
  std::array<void *, 1> vtable{};
  std::array<void *, 1> foreign_vtable{};
  void *title_storage_slot = title_storage.data();
  current::PlayerClaimsBindingsV1 bindings{};
  Fault fault = Fault::none;
  std::size_t getter_calls = 0;
  std::size_t destructor_calls = 0;
  bool bad_destructor_call = false;
  void *last_optional = nullptr;
  std::map<std::int32_t, std::size_t> row_reads;
  std::vector<std::int32_t> observed_actors;
  static inline Fixture *active = nullptr;

  Fixture() {
    active = this;
    vtable[0] = reinterpret_cast<void *>(&DestroyClaim);
    Put(title_storage.data(), 0x20, static_cast<void *>(title_slots.data()));
    Put(title_storage.data(), 0x2C, std::int32_t{8});
    AddTitle(kAbsent, {false, 0xFF, 0xFF});
    AddTitle(kStrongExplicit, {true, 1, 0});
    AddTitle(kStrongImplicit, {true, 1, 1});
    AddTitle(kWeakImplicit, {true, 0, 1});
    AddTitle(kWeakExplicit, {true, 0, 0});
    bindings.enabled = true;
    bindings.core = core.Bindings();
    bindings.provinces.enabled = true;
    bindings.provinces.landed_title_storage_slot = &title_storage_slot;
    bindings.read_character_claim = &ReadClaim;
    bindings.character_claim_vtable = reinterpret_cast<std::uintptr_t>(vtable.data());
  }
  ~Fixture() { active = nullptr; }
  Fixture(const Fixture &) = delete;
  Fixture &operator=(const Fixture &) = delete;

  void AddTitle(std::int32_t id, ClaimRow row) {
    auto &bytes = titles[id];
    Put(bytes.data(), 0x10, id);
    const auto index = static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
    Put(title_slots.data(), static_cast<std::size_t>(index) * 0x10 + 8,
        static_cast<void *>(bytes.data()));
    rows[id] = row;
  }
  static void *DestroyClaim(void *claim, std::int32_t delete_flags) {
    auto &f = *active;
    ++f.destructor_calls;
    f.bad_destructor_call = f.bad_destructor_call || delete_flags != 0 ||
        claim != f.last_optional || Get<std::uint8_t>(claim, 0x18) != 1;
    return claim;
  }
  static void *ReadClaim(void *output, void *claimant, void *title) {
    auto &f = *active;
    ++f.getter_calls;
    const auto title_id = Get<std::int32_t>(title, 0x10);
    const auto found = f.rows.find(title_id);
    if (found == f.rows.end()) return nullptr;
    auto row = found->second;
    const auto visit = ++f.row_reads[title_id];
    f.observed_actors.push_back(Get<std::int32_t>(claimant, 0x18));
    f.last_optional = output;
    if (f.fault == Fault::row_changes_on_second_read && visit == 2)
      row.strong = static_cast<std::uint8_t>(row.strong == 0 ? 1 : 0);

    // Literals come from the already qualified 0x20 return object, rather than
    // computing an oracle from the decoder's current field constants.
    std::memset(output, 0xCC, 0x20);
    Put(output, 0x00, f.fault == Fault::wrong_vtable ? f.foreign_vtable.data()
                                                     : f.vtable.data());
    Put(output, 0x08, f.fault == Fault::wrong_claim_generation
                         ? title_id ^ 0x01000000 : title_id);
    Put(output, 0x0C, std::uint32_t{0x436C6169});
    Put(output, 0x10, f.fault == Fault::invalid_strong ? std::uint8_t{2} : row.strong);
    Put(output, 0x11, f.fault == Fault::invalid_implicit ? std::uint8_t{2} : row.implicit);
    Put(output, 0x18, f.fault == Fault::invalid_present ? std::uint8_t{2}
                                                     : std::uint8_t(row.present));
    // Exercise the last four bytes of the qualified optional object as well.
    Put(output, 0x1C, std::uint32_t{0xA5A5A5A5});

    if (f.getter_calls == 1) {
      switch (f.fault) {
      case Fault::played_character_changes:
        f.core.SetPlayingCharacterFullId(kNextActor);
        break;
      case Fault::title_pointer_changes:
        f.replacement_title = f.titles.at(title_id);
        Put(f.title_slots.data(),
            static_cast<std::size_t>(static_cast<std::uint32_t>(title_id) &
                                     0x00FFFFFFU) * 0x10 + 8,
            static_cast<void *>(f.replacement_title.data()));
        break;
      case Fault::date_changes: f.core.SetClock(kDate + 24, 4, true); break;
      case Fault::pause_changes: f.core.SetClock(kDate, 4, false); break;
      case Fault::speed_changes: f.core.SetClock(kDate, 3, true); break;
      default: break;
      }
    }
    if (f.fault == Fault::title_generation_changes_after_second_read &&
        f.getter_calls == 2)
      Put(title, 0x10, title_id ^ 0x01000000);
    return f.fault == Fault::wrong_return ? nullptr : output;
  }
};

std::string Step(std::span<const std::int32_t> ids) {
  std::string step(game::kPlayerClaimsV1StepPrefix);
  for (std::size_t i = 0; i < ids.size(); ++i) {
    if (i != 0) step += ',';
    step += std::to_string(ids[i]);
  }
  return step;
}

void WriteWire(const std::filesystem::path &directory, std::string_view name,
               const game::PlayerClaimsV1 &observation, Result result,
               std::span<const std::int32_t> ids) {
  const auto step = Step(ids);
  const auto wire = game::SerializePlayerClaimsV1(observation, result,
      ++wire_sequence, kRevision, step);
  Check(wire.find("\"read_only\":true") != std::string::npos &&
            wire.find("\"snapshot_revision\":73") != std::string::npos &&
            wire.find("\"game_version\":\"1.20.0.4\"") != std::string::npos &&
            wire.find(current::kExecutableSha256) != std::string::npos,
        "production serializer lost read-only/current-build frame provenance");
  if (result == Result::unavailable) {
    Check(wire.find("\"claims\":null") != std::string::npos &&
              wire.find("\"available\":false") != std::string::npos &&
              wire.find("\"claims\":[]") == std::string::npos,
          "unavailable native rows became an empty or absent claim inventory");
  }
  const auto path = directory / (std::string(name) + ".json");
  Check(!std::filesystem::exists(path), "refusing to replace previous wire evidence");
  std::ofstream output(path, std::ios::binary);
  output << "{\"type\":\"command_result\",\"protocol_version\":1,"
            "\"request_id\":\"synthetic-player-claims-" << wire_sequence <<
            "\",\"ok\":true,\"result\":" << wire << "}\n";
  Check(output.good(), "production claim wire could not be preserved");
}

void BindingAndRequestBoundary() {
  Fixture f;
  constexpr std::uintptr_t base = 0x140000000ULL;
  const auto bound = current::BindPlayerClaimsImageV1(
      base, current::kExecutableSha256, f.core.Bindings(), f.bindings.provinces);
  Check(bound.enabled && reinterpret_cast<std::uintptr_t>(bound.read_character_claim) ==
            base + current::kClaimTermsGetterRva &&
            bound.character_claim_vtable == base + current::kClaimTermsClaimVtableRva,
        "actual4 pure binder did not select the qualified getter/vtable");
  Check(!current::BindPlayerClaimsImageV1(base, old_layout::kExecutableSha256,
            f.core.Bindings(), f.bindings.provinces).enabled &&
            !current::BindPlayerClaimsImageV1(0, current::kExecutableSha256,
            f.core.Bindings(), f.bindings.provinces).enabled,
        "actual4 claim binder accepted another image");
  std::vector<std::int32_t> ids;
  Check(game::ParsePlayerClaimsStepV1("query-player-claims-v1-2147483647,0,16777217", ids) &&
            ids == std::vector<std::int32_t>({2147483647, 0, 16777217}),
        "native parser narrowed or reordered full int32 request IDs");
  for (const auto text : {"query-player-claims-v1-", "query-player-claims-v1-01",
                         "query-player-claims-v1-1,1", "query-player-claims-v1-1,",
                         "query-player-claims-v1--1", "query-player-claims-v1-2147483648"}) {
    ids = {5};
    Check(!game::ParsePlayerClaimsStepV1(text, ids) && ids.empty(),
          "native parser accepted an ambiguous or overflowing request");
  }
  std::vector<std::int32_t> maximum;
  for (std::int32_t i = 0; i < 4096; ++i) maximum.push_back(i);
  Check(game::ParsePlayerClaimsStepV1(Step(maximum), ids) && ids == maximum,
        "finite native request upper bound rejected");
  maximum.push_back(4096);
  Check(!game::ParsePlayerClaimsStepV1(Step(maximum), ids) && ids.empty(),
        "native request exceeded its finite upper bound");
  // Invalid typed inputs must fail before the fake native getter is reached.
  for (const auto &bad : {std::vector<std::int32_t>{},
                         std::vector<std::int32_t>{1, 1},
                         std::vector<std::int32_t>{-1}}) {
    game::PlayerClaimsV1 output{};
    Check(current::ReadPlayerClaimsV1(f.bindings, bad, output) == Result::unavailable &&
              output.claims.empty() && f.getter_calls == 0,
          "invalid typed request reached a getter or manufactured claim absence");
  }
  ++scenarios;
}

void OrderedOptionalStates(const std::filesystem::path &wire) {
  Fixture f;
  const std::vector<std::int32_t> ids{kWeakImplicit, kAbsent, kStrongExplicit,
                                      kStrongImplicit, kWeakExplicit};
  const std::array<std::string_view, 5> states{
      "weak_implicit", "absent", "strong_explicit", "strong_implicit", "weak_explicit"};
  game::PlayerClaimsV1 output{};
  const auto result = current::ReadPlayerClaimsV1(f.bindings, ids, output);
  Check(result == Result::available && output.available && output.title_ids == ids &&
            output.claims.size() == 5 && output.actor_character_id == kActor &&
            output.date_raw == kDate,
        "ordered current-player observation is not available in an empty war fixture");
  for (std::size_t i = 0; i < states.size(); ++i)
    Check(output.claims[i].title_id == ids[i] && output.claims[i].state == states[i],
          "native optional state or complete requested TitleID changed");
  Check(f.getter_calls == 10 && f.destructor_calls == 8 && !f.bad_destructor_call,
        "present optional lifetime or second requested-row read is incorrect");
  const auto text = game::SerializePlayerClaimsV1(output, result, 1, kRevision, Step(ids));
  Check(text.find("\"title_id\":0,\"present\":false,\"state\":\"absent\",\"strong\":null,\"implicit\":null") !=
            std::string::npos,
        "available absent claim lost its explicit null optional flags");
  WriteWire(wire, "ordered-five-states-no-war", output, result, ids);
  ++scenarios;
}

void CurrentPlayerAndAdmission(const std::filesystem::path &wire) {
  {
    Fixture f;
    f.core.SetPlayingCharacterFullId(kNextActor);
    const std::vector<std::int32_t> ids{kStrongExplicit};
    game::PlayerClaimsV1 output{};
    const auto result = current::ReadPlayerClaimsV1(f.bindings, ids, output);
    Check(result == Result::available && output.actor_character_id == kNextActor &&
              f.observed_actors == std::vector<std::int32_t>({kNextActor, kNextActor}),
          "reader queried a cached former actor or narrowed current full CharacterID");
    WriteWire(wire, "stable-new-current-player-generation", output, result, ids);
    ++scenarios;
  }
  for (int mutation = 0; mutation != 3; ++mutation) {
    Fixture f;
    if (mutation == 0) f.core.SetClock(kDate, 4, false);
    if (mutation == 1) f.core.SetCharacterDead(true);
    if (mutation == 2) f.core.SetCharacterFullId(kNextActor);
    game::PlayerClaimsV1 output{};
    Check(current::ReadPlayerClaimsV1(f.bindings, std::array{kStrongExplicit}, output) ==
              Result::unavailable && !output.available && output.claims.empty() &&
              f.getter_calls == 0,
          "unpaused/dead/unresolved current actor reached the native claim getter");
    ++scenarios;
  }
}

void MissingAndStaleTitle(const std::filesystem::path &wire) {
  {
    Fixture f;
    const std::vector<std::int32_t> ids{kStrongExplicit, kMissing};
    game::PlayerClaimsV1 output{};
    const auto result = current::ReadPlayerClaimsV1(f.bindings, ids, output);
    Check(result == Result::unavailable && !output.available && output.claims.empty() &&
              output.title_ids == ids && f.getter_calls == 1 && f.destructor_calls == 1,
          "one unreadable requested title became absent or leaked a partial row list");
    WriteWire(wire, "partial-rows-cleared-on-missing-title", output, result, ids);
    ++scenarios;
  }
  {
    Fixture f;
    const std::vector<std::int32_t> ids{kStrongExplicit ^ 0x01000000};
    game::PlayerClaimsV1 output{};
    const auto result = current::ReadPlayerClaimsV1(f.bindings, ids, output);
    Check(result == Result::unavailable && output.claims.empty() && f.getter_calls == 0,
          "same low24 slot with a stale full TitleID reached the claim getter");
    WriteWire(wire, "same-slot-wrong-title-generation", output, result, ids);
    ++scenarios;
  }
}

void MalformedOptionalLifetime(const std::filesystem::path &wire) {
  struct Scene { const char *name; Fault fault; std::size_t destructors; };
  const std::array scenes{
      Scene{"wrong-getter-return", Fault::wrong_return, 0},
      Scene{"invalid-presence-byte", Fault::invalid_present, 0},
      Scene{"foreign-claim-vtable", Fault::wrong_vtable, 0},
      Scene{"claim-full-id-mismatch", Fault::wrong_claim_generation, 1},
      Scene{"nonboolean-strong", Fault::invalid_strong, 1},
      Scene{"nonboolean-implicit", Fault::invalid_implicit, 1}};
  for (const auto &scene : scenes) {
    Fixture f;
    f.fault = scene.fault;
    const std::vector<std::int32_t> ids{kStrongExplicit};
    game::PlayerClaimsV1 output{};
    const auto result = current::ReadPlayerClaimsV1(f.bindings, ids, output);
    Check(result == Result::unavailable && !output.available && output.claims.empty() &&
              f.getter_calls == 1 && f.destructor_calls == scene.destructors &&
              !f.bad_destructor_call,
          "malformed optional was accepted, treated as absent, or destructed with delete flags");
    WriteWire(wire, scene.name, output, result, ids);
    ++scenarios;
  }
}

void ChangesBetweenObservations(const std::filesystem::path &wire) {
  struct Scene { const char *name; Fault fault; std::string_view reason; };
  const std::array scenes{
      Scene{"claim-row-changes-on-reread", Fault::row_changes_on_second_read,
            "player_claim_rows_changed"},
      Scene{"played-character-changes-during-read", Fault::played_character_changes,
            "player_claim_identity_changed"},
      Scene{"same-id-title-component-replaced", Fault::title_pointer_changes,
            "player_claim_identity_changed"},
      Scene{"title-generation-changes-after-reread", Fault::title_generation_changes_after_second_read,
            "player_claim_identity_changed"},
      Scene{"date-changes-during-read", Fault::date_changes, "player_claim_frame_changed"},
      Scene{"pause-changes-during-read", Fault::pause_changes, "player_claim_frame_changed"},
      Scene{"speed-changes-during-read", Fault::speed_changes, "player_claim_frame_changed"}};
  for (const auto &scene : scenes) {
    Fixture f;
    f.fault = scene.fault;
    const std::vector<std::int32_t> ids{kStrongExplicit};
    game::PlayerClaimsV1 output{};
    const auto result = current::ReadPlayerClaimsV1(f.bindings, ids, output);
    Check(result == Result::unavailable && !output.available && output.claims.empty() &&
              output.unavailable_reason == scene.reason && !f.bad_destructor_call,
          "changed current actor/row/paused frame was published as a stable claim observation");
    WriteWire(wire, scene.name, output, result, ids);
    ++scenarios;
  }
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "usage: xar_ck3_12004_player_claims_v1_test <new-wire-output-dir>");
    const std::filesystem::path wire(argv[1]);
    Check(!std::filesystem::exists(wire), "preserve previous fixture attempt; choose a new output directory");
    Check(std::filesystem::create_directories(wire), "new wire output directory was not created");
    BindingAndRequestBoundary();
    OrderedOptionalStates(wire);
    CurrentPlayerAndAdmission(wire);
    MissingAndStaleTitle(wire);
    MalformedOptionalLifetime(wire);
    ChangesBetweenObservations(wire);
    std::cout << "PASS checks=" << checks << " scenarios=" << scenarios
              << " wires=" << wire_sequence
              << "; synthetic component/getter memory, production reader/resolvers/parser/serializer"
                 "; no live ABI, owner mailbox, bridge route, game or G2 credit\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL: " << error.what() << '\n';
    return 1;
  }
}
