#include "xar_bridge/ck3_12003_church_income_profile.hpp"
#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/ck3_12002_religion_context.hpp"

#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>

namespace income = xar::ck3_12003::religion::church_income;
namespace context = xar::ck3_12002::religion;
namespace {
unsigned checks = 0;
void Check(bool condition, const char *message) {
  ++checks;
  if (!condition) throw std::runtime_error(message);
}
struct Fixture {
  std::array<std::byte, 0x28> owner{}, priest{};
  static constexpr std::int32_t owner_id = 29829;
  static constexpr std::int32_t date = 53175816;
  static constexpr std::uint64_t epoch = 17;
  std::int64_t current = -12'345, maximum = 0;
  unsigned calls = 0;
  bool fail_current = false, fail_maximum = false;
  Fixture() {
    const std::int32_t priest_id = 56513;
    std::memcpy(owner.data() + 0x18, &owner_id, sizeof(owner_id));
    std::memcpy(priest.data() + 0x18, &priest_id, sizeof(priest_id));
  }
};
Fixture *f = nullptr;
std::int64_t *Income(std::int64_t *out, void *receiver, bool third,
                     bool maximum, void *breakdown) {
  Check(receiver == f->owner.data() && receiver != f->priest.data(),
        "numeric consumer receives actual played owner, not realm priest");
  Check(!third && breakdown == nullptr && maximum == (f->calls == 1),
        "native GUI argument shape and current then maximum order");
  ++f->calls;
  if ((!maximum && f->fail_current) || (maximum && f->fail_maximum)) return nullptr;
  *out = maximum ? f->maximum : f->current;
  return out;
}
context::Context Context() {
  context::Context out{};
  out.available = true; out.failure = context::Failure::none;
  out.capture_epoch = Fixture::epoch; out.date_raw = Fixture::date;
  out.played_character_id = Fixture::owner_id;
  out.rite_id = 152; out.faith_id = 23; out.religion_id = 8; out.faith_main_rite_id = 152;
  out.faith_key = "catholic"; out.religion_key = "christianity_religion";
  out.faith_fervor_raw = -123'456; out.spiritual_fulfillment_raw = 750'000;
  return out;
}
void WriteWire(const std::filesystem::path &directory, const char *name,
               const income::Terms &terms) {
  const auto old_context = context::SerializePlayedReligionContext12002(Context());
  const auto actual_leaf = income::SerializePlayerChurchIncomeProfile12003(terms);
  // Only this test envelope is assembled here. The leaf, original Context and
  // exact-build renderer are the actual production implementations.
  const std::string envelope = std::string{"{\"type\":\"command_result\",\"protocol_version\":1,"
      "\"request_id\":\"fixture-church-income\",\"ok\":true,\"result\":{"
      "\"step\":\"query-player-religion-context-v1\",\"accepted\":true,"
      "\"status\":\"observed\",\"private_build\":true,\"read_only\":true,\"advertised\":false,"
      "\"game_version\":\"1.20.0.2\",\"executable_sha256\":\""} +
      xar::ck3_12002::kExecutableSha256 + "\",\"domain_key\":\"player_religion_context_v1\","
      "\"backend_id\":\"ck3-1.20.0.2-native-player-religion-context-v1\","
      "\"snapshot_revision\":701,\"date_raw\":" + std::to_string(Fixture::date) +
      ",\"player_religion_context\":" + old_context +
      ",\"player_church_income_profile\":" + actual_leaf + "}}";
  const xar::game::AdapterDescriptor descriptor{xar::ck3_12003::kAdapterId,
      xar::ck3_12003::kGameVersion, xar::ck3_12003::kExecutableSha256,
      "synthetic-church-income-leaf-fixture", {}};
  const auto wire = xar::game::RenderCrozierBuildIdentity(envelope, descriptor);
  Check(wire.find("\"game_version\":\"1.20.0.3\"") != std::string::npos &&
        wire.find(xar::ck3_12003::kExecutableSha256) != std::string::npos &&
        wire.find(actual_leaf) != std::string::npos &&
        wire.find("\"spiritual_fulfillment_raw\":750000") != std::string::npos,
        "actual build renderer preserves independent leaf and old Context values");
  std::ofstream output(directory / name, std::ios::binary);
  output << wire << '\n';
  Check(output.good(), "genuine rendered wire written");
}
void CheckFrame(const income::Terms &terms) {
  Check(terms.capture_epoch == Fixture::epoch && terms.date_raw == Fixture::date &&
        terms.played_character_id == Fixture::owner_id,
        "owner actor/date/epoch preserved by actual leaf");
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "output directory argument");
    const std::filesystem::path directory(argv[1]);
    const auto bound = income::BindPlayerChurchIncomeProfileImage12003(
        0x140000000ULL, xar::ck3_12003::kExecutableSha256);
    Check(bound.enabled && reinterpret_cast<std::uintptr_t>(bound.monthly_income) ==
          0x140000000ULL + income::kMonthlyIncomeRva,
          "exact build numeric consumer binding");
    Check(!income::BindPlayerChurchIncomeProfileImage12003(0,
          xar::ck3_12003::kExecutableSha256).enabled &&
          !income::BindPlayerChurchIncomeProfileImage12003(0x140000000ULL,
          xar::ck3_12002::kExecutableSha256).enabled,
          "existing exact build contract rejects absent image and wrong build");
    Fixture fixture; f = &fixture;
    const income::Bindings bindings{true, &Income};
    income::Terms terms{};
    auto read = [&] {
      fixture.calls = 0;
      return income::ReadPlayerChurchIncomeProfile12003(bindings, fixture.owner.data(),
          Fixture::owner_id, Fixture::date, Fixture::epoch, terms);
    };
    Check(read() && terms.available && fixture.calls == 2 &&
          terms.current_monthly_income_raw == -12'345 && terms.maximum_monthly_income_raw == 0,
          "signed current and zero maximum are complete native observations");
    CheckFrame(terms); WriteWire(directory, "signed-current-zero-maximum.json", terms);
    fixture.current = 0; fixture.maximum = 987'654'321;
    Check(read() && fixture.calls == 2 && terms.current_monthly_income_raw == 0 &&
          terms.maximum_monthly_income_raw == 987'654'321,
          "zero current and non-rounded maximum remain Q100000 integers");
    CheckFrame(terms); WriteWire(directory, "zero-current-positive-maximum.json", terms);
    fixture.fail_current = true;
    Check(!read() && !terms.available && fixture.calls == 1 &&
          terms.unavailable_reason == "current_monthly_income_unavailable" &&
          !terms.current_monthly_income_raw && !terms.maximum_monthly_income_raw,
          "current native read failure clears prior complete pair");
    CheckFrame(terms); WriteWire(directory, "current-read-unavailable.json", terms);
    fixture.fail_current = false; fixture.fail_maximum = true;
    Check(!read() && !terms.available && fixture.calls == 2 &&
          terms.unavailable_reason == "maximum_monthly_income_unavailable" &&
          !terms.current_monthly_income_raw && !terms.maximum_monthly_income_raw,
          "maximum native read failure does not invent a complete profile");
    CheckFrame(terms); WriteWire(directory, "maximum-read-unavailable.json", terms);
    fixture.calls = 0;
    Check(!income::ReadPlayerChurchIncomeProfile12003(bindings, fixture.priest.data(),
          Fixture::owner_id, Fixture::date, Fixture::epoch, terms) && fixture.calls == 0 &&
          terms.unavailable_reason == "played_character_unavailable",
          "realm priest cannot substitute for the actual owner");
    CheckFrame(terms); WriteWire(directory, "owner-unavailable.json", terms);
    Check(!income::ReadPlayerChurchIncomeProfile12003({}, fixture.owner.data(),
          Fixture::owner_id, Fixture::date, Fixture::epoch, terms) &&
          terms.unavailable_reason == "bindings_unavailable",
          "independent absent native binding retains frame and reason");
    CheckFrame(terms); WriteWire(directory, "binding-unavailable.json", terms);
    std::cout << "PASS cases=6 checks=" << checks <<
      " actual_leaf_reader=true actual_leaf_serializer=true actual_context_serializer=true"
      " actual_build_identity_renderer=true actual_mailbox=false synthetic_material=true live=false\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL " << error.what() << '\n'; return 1;
  }
}
