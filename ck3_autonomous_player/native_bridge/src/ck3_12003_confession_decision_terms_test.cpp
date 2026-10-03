#include "xar_bridge/ck3_12003_confession_decision_terms.hpp"
#include "xar_bridge/ck3_12003_adapter.hpp"

#include <algorithm>
#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>

namespace d = xar::ck3_12003::religion::confession;
namespace {
template <std::size_t N> using Bytes = std::array<std::byte, N>;
int checks = 0;
void Check(bool value, const char *message) {
  ++checks;
  if (!value) throw std::runtime_error(message);
}
template <typename T> T Get(const void *object, std::size_t at) {
  T value{}; std::memcpy(&value, static_cast<const std::byte *>(object) + at, sizeof(value)); return value;
}
template <typename T> void Put(void *object, std::size_t at, T value) {
  std::memcpy(static_cast<std::byte *>(object) + at, &value, sizeof(value));
}
struct Fixture {
  Bytes<0x40> character{}, definition{};
  std::byte database{}, fallback{}, cost{};
  void *database_ptr = &database;
  const void *fallback_ptr = &fallback;
  static constexpr std::int32_t actor = 0x03000004, date = 53175816;
  static constexpr std::uint64_t epoch = 47;
  bool shown = true, final = false, affordable = true;
  std::array<std::int64_t, 10> quote{};
  std::string reason = "\x16warning_icon!\x15X 忏悔：\"当前条件\"未满足。\n费用由原生评估\t#bold 完整理由#!\x15!";
  int hash = 0, lookup = 0, construct = 0, destroy = 0, cost_reads = 0;
  int quote_reads = 0, shown_reads = 0, final_reads = 0, affordable_reads = 0, reason_destroys = 0;
  Fixture() {
    Put(character.data(), 0x18, actor);
    Put(definition.data(), 0x18, d::kDecisionId.data());
    Put(definition.data(), 0x28, d::kDecisionId.size());
    Put(definition.data(), 0x30, d::kDecisionId.size());
    quote[0] = -12500; quote[6] = 0; quote[1] = 54321; quote[2] = 10012345;
  }
};
Fixture *fixture = nullptr;
void Scope(void *object) {
  Check(Get<std::uint16_t>(object, 0) == 4 && Get<std::int64_t>(object, 8) == Fixture::actor &&
        Get<std::uint64_t>(object, 0x40) == 0xAA112233ULL, "actual scope wrapper preserves constructed object and full player ref");
}
std::uint32_t Hash(void *database, const char *key, std::uint32_t length) {
  Check(database == &fixture->database && std::string_view(key, length) == d::kDecisionId,
        "fixed confession hash input is the full key, not communion or advertised token");
  ++fixture->hash; return 0x719U;
}
const void *Lookup(void *database, std::uint32_t hash) {
  Check(database == &fixture->database && hash == 0x719U, "lookup consumes native hash output");
  ++fixture->lookup; return fixture->definition.data();
}
void *Construct(void *object) {
  std::memset(object, 0, 0x168); Put(object, 0x40, std::uint64_t{0xAA112233ULL});
  ++fixture->construct; return object;
}
void Destroy(void *object) { Scope(object); ++fixture->destroy; }
bool Shown(const void *definition, void *character) {
  Check(definition == fixture->definition.data() && character == fixture->character.data(), "shown uses actual resolved owner and fixed definition");
  ++fixture->shown_reads; return fixture->shown;
}
const void *Cost(const void *definition) {
  Check(definition == fixture->definition.data(), "cost resolves the actual fixed definition");
  ++fixture->cost_reads; return &fixture->cost;
}
void Quote(const void *cost, void *scope, std::int64_t *out) {
  Check(cost == &fixture->cost, "native void cost evaluator receives actual cost object"); Scope(scope);
  std::copy(fixture->quote.begin(), fixture->quote.end(), out); ++fixture->quote_reads;
}
bool Final(const void *definition, void *character, void *scope, const void *budget, void *sink) {
  Check(definition == fixture->definition.data() && character == fixture->character.data() && budget == nullptr && sink,
        "CanTake receives independent native reason sink and null budget"); Scope(scope);
  Check(Get<std::size_t>(sink, 0x10) == 0 && Get<std::size_t>(sink, 0x18) == 15 &&
        *static_cast<const char *>(sink) == '\0', "canonical native empty SSO reason input");
  if (!fixture->reason.empty()) {
    auto *bytes = new char[fixture->reason.size() + 1];
    std::memcpy(bytes, fixture->reason.c_str(), fixture->reason.size() + 1);
    Put(sink, 0, bytes); Put(sink, 0x10, fixture->reason.size()); Put(sink, 0x18, fixture->reason.size());
  }
  ++fixture->final_reads; return fixture->final;
}
bool Affordable(const void *cost, void *scope, void *character, void *reason) {
  Check(cost == &fixture->cost && character == fixture->character.data() && reason == nullptr,
        "affordability stays independent of native CanTake sink and shown"); Scope(scope);
  ++fixture->affordable_reads; return fixture->affordable;
}
void ReasonDestroy(void *sink) {
  Check(Get<std::size_t>(sink, 0x10) == fixture->reason.size(), "native reason is copied without truncation before destruction");
  if (Get<std::size_t>(sink, 0x18) >= 16) delete[] Get<char *>(sink, 0);
  std::memset(sink, 0, 0x20); Put(sink, 0x18, std::size_t{15}); ++fixture->reason_destroys;
}
d::Bindings Bind(Fixture &f) {
  fixture = &f;
  return {true, &f.database_ptr, &f.fallback_ptr, &Hash, &Lookup, &Construct, &Destroy,
      &Shown, &Final, &Cost, &Quote, &Affordable, &ReasonDestroy};
}
void Run(Fixture &f, const std::filesystem::path &directory, const char *name) {
  d::Terms result{};
  Check(d::ReadPlayerConfessionDecisionTerms12003(Bind(f), f.character.data(), Fixture::actor,
      Fixture::date, Fixture::epoch, result), "production fixed reader completed");
  Check(result.available && result.unavailable_reason.empty() && result.is_shown == f.shown &&
      result.can_take == f.final && result.affordable == f.affordable, "three independent native predicates retain legitimate true and false");
  Check(result.capture_epoch == Fixture::epoch && result.played_character_id == Fixture::actor &&
      result.date_raw == Fixture::date, "actual supplied actor/date/epoch retained");
  Check(result.costs_raw && result.costs_raw->gold == f.quote[0] && result.costs_raw->treasury == f.quote[6] &&
      result.costs_raw->prestige == f.quote[1] && result.costs_raw->piety == f.quote[2], "actual void out10 maps signed/zero four currency values without authored default");
  Check(result.reasons_available && result.can_take_reasons == f.reason && f.reason_destroys == 1 &&
      f.destroy == 1, "complete native UTF8 literal and legal empty text survive actual copy and release");
  Check(f.hash == 1 && f.lookup == 1 && f.construct == 1 && f.cost_reads == 1 && f.quote_reads == 1 &&
      f.shown_reads == 1 && f.final_reads == 1 && f.affordable_reads == 1, "each actual native primitive invoked once");
  // A synthetic fixture envelope carries the genuine production leaf serializer.
  // The shared mailbox owner will independently test full Context composition.
  const auto body = d::SerializePlayerConfessionDecisionTerms12003(result);
  const std::string envelope = "{\"game_version\":\"1.20.0.2\",\"executable_sha256\":\"" +
      std::string(xar::ck3_12002::kExecutableSha256) + "\",\"player_confession_decision_terms\":" + body + "}";
  const xar::game::AdapterDescriptor descriptor{xar::ck3_12003::kAdapterId, xar::ck3_12003::kGameVersion,
      xar::ck3_12003::kExecutableSha256, "synthetic-confession-readonly-leaf", {}};
  const auto rendered = xar::game::RenderCrozierBuildIdentity(envelope, descriptor);
  Check(rendered.find("\"game_version\":\"1.20.0.3\"") != std::string::npos &&
      rendered.find(xar::ck3_12003::kExecutableSha256) != std::string::npos &&
      rendered.find(body) != std::string::npos, "actual .3 renderer retains genuine independently serialized confession terms");
  std::ofstream(directory / name, std::ios::binary) << rendered << '\n';
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "output argument");
    const std::filesystem::path directory(argv[1]);
    Fixture false_final;
    Run(false_final, directory, "native-final-false-full-reason.json");
    Fixture true_final;
    true_final.shown = false; true_final.final = true; true_final.affordable = false;
    true_final.quote.fill(0); true_final.reason.clear();
    Run(true_final, directory, "native-final-true-empty-reason.json");
    std::cout << "PASS cases=1 scenarios=2 checks=" << checks
              << " actual_confession_reader=true actual_serializer=true actual_build_identity_renderer=true"
                 " native_callbacks=synthetic game=false mailbox_composition=not_exercised live=false\n";
    return 0;
  } catch (const std::exception &error) { std::cerr << "FAIL " << error.what() << '\n'; return 1; }
}
