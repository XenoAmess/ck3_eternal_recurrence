#include "xar_bridge/ck3_12003_repentance_petition_decision_terms.hpp"

#include <algorithm>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>

namespace p = xar::ck3_12003::religion::repentance_petition;
namespace {
template <std::size_t N> using Bytes = std::array<std::byte, N>;
int checks = 0;
void Check(bool value, const char *message) {
  ++checks;
  if (!value) throw std::runtime_error(message);
}
template <typename T> T Get(const void *object, std::size_t offset) {
  T value{}; std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value)); return value;
}
template <typename T> void Put(void *object, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
}
struct Entry {
  Bytes<0x40> definition{};
  std::byte cost{};
  bool shown = false, final = false, affordable = false, missing = false;
  std::array<std::int64_t, 10> costs{};
  std::string reason;
};
struct Fixture {
  Bytes<0x40> actor{};
  std::byte database{}, fallback{};
  void *database_ptr = &database;
  const void *fallback_ptr = &fallback;
  std::array<Entry, 2> entries{};
  static constexpr std::int32_t id = 0x03000004, date = 53175816;
  static constexpr std::uint64_t epoch = 57;
  std::size_t current = 0;
  int hashes = 0, lookups = 0, constructed = 0, destroyed = 0, reason_destroyed = 0;
  int shown_calls = 0, final_calls = 0, cost_calls = 0, evaluated_calls = 0, affordable_calls = 0;
  Fixture() {
    Put(actor.data(), 0x18, id);
    const std::array<std::string_view, 2> keys{p::kHeadOfFaithDecisionId, p::kAntipopeDecisionId};
    for (std::size_t i = 0; i < entries.size(); ++i) {
      Put(entries[i].definition.data(), 0x18, keys[i].data());
      Put(entries[i].definition.data(), 0x28, keys[i].size());
      Put(entries[i].definition.data(), 0x30, keys[i].size());
    }
    entries[0].shown = true; entries[0].affordable = true;
    entries[0].costs = {-10, 0, 12345678, -4, 5, -6, 7, 8, -9, 10};
    entries[0].reason = "\x16warning_icon!\x15X 请愿：\"当前条件\"未满足。\n完整理由\t#bold 原生文本#!\x15!";
    entries[1].final = true;
    entries[1].costs = {10, 20, 30, 40, 50, 60, 70, 80, 90, -100};
  }
};
Fixture *fixture = nullptr;
void Scope(void *scope) {
  Check(Get<std::uint16_t>(scope, 0) == 4 && Get<std::int64_t>(scope, 8) == Fixture::id &&
      Get<std::uint64_t>(scope, 0x40) == 0xAA112233ULL,
      "native constructed player root keeps complete character reference");
  Check(Get<std::uint64_t>(scope, 0x20) == 0 && Get<std::uint64_t>(scope, 0x30) == 0,
      "reader does not fabricate a selected widget option");
}
std::uint32_t Hash(void *database, const char *key, std::uint32_t length) {
  Check(database == &fixture->database, "actual decision database used");
  const std::string_view value(key, length);
  Check(value == p::kHeadOfFaithDecisionId || value == p::kAntipopeDecisionId,
      "only the two fixed petition decision keys are queried");
  ++fixture->hashes;
  return value == p::kHeadOfFaithDecisionId ? 0x501U : 0x502U;
}
const void *Lookup(void *database, std::uint32_t hash) {
  Check(database == &fixture->database && (hash == 0x501U || hash == 0x502U),
      "native lookup consumes native hash");
  fixture->current = hash == 0x501U ? 0U : 1U; ++fixture->lookups;
  return fixture->entries[fixture->current].missing ? fixture->fallback_ptr :
      fixture->entries[fixture->current].definition.data();
}
void *Construct(void *scope) {
  std::memset(scope, 0, 0x168); Put(scope, 0x40, std::uint64_t{0xAA112233ULL});
  ++fixture->constructed; return scope;
}
void Destroy(void *scope) { Scope(scope); ++fixture->destroyed; }
Entry &Current(const void *definition) {
  Check(definition == fixture->entries[fixture->current].definition.data(), "selected fixed definition used");
  return fixture->entries[fixture->current];
}
bool Shown(const void *definition, void *actor) {
  Check(actor == fixture->actor.data(), "shown receives actual player"); ++fixture->shown_calls;
  return Current(definition).shown;
}
const void *Cost(const void *definition) { ++fixture->cost_calls; return &Current(definition).cost; }
void Evaluate(const void *cost, void *scope, std::int64_t *out) {
  Check(cost == &fixture->entries[fixture->current].cost, "native cost object used"); Scope(scope);
  const auto &costs = fixture->entries[fixture->current].costs;
  std::copy(costs.begin(), costs.end(), out); ++fixture->evaluated_calls;
}
bool Final(const void *definition, void *actor, void *scope, const void *context, void *reason) {
  Check(actor == fixture->actor.data() && context == nullptr && reason, "native final uses actual player and own reason sink");
  Scope(scope);
  Check(Get<std::size_t>(reason, 0x10) == 0 && Get<std::size_t>(reason, 0x18) == 15 &&
      *static_cast<const char *>(reason) == '\0', "canonical empty native reason SSO");
  const auto &entry = Current(definition);
  if (entry.reason.size() < 16) {
    std::memcpy(reason, entry.reason.c_str(), entry.reason.size() + 1);
    Put(reason, 0x10, entry.reason.size());
  } else {
    auto *copy = new char[entry.reason.size() + 1];
    std::memcpy(copy, entry.reason.c_str(), entry.reason.size() + 1);
    Put(reason, 0, copy); Put(reason, 0x10, entry.reason.size()); Put(reason, 0x18, entry.reason.size());
  }
  ++fixture->final_calls; return entry.final;
}
bool Affordable(const void *cost, void *scope, void *actor, void *reason) {
  Check(cost == &fixture->entries[fixture->current].cost && actor == fixture->actor.data() && !reason,
      "affordability retains independent predicate and null reason"); Scope(scope);
  ++fixture->affordable_calls; return fixture->entries[fixture->current].affordable;
}
void ReasonDestroy(void *reason) {
  Check(Get<std::size_t>(reason, 0x10) == fixture->entries[fixture->current].reason.size(),
      "complete reason copied before native destroy");
  if (Get<std::size_t>(reason, 0x18) >= 16) delete[] Get<char *>(reason, 0);
  ++fixture->reason_destroyed;
}
p::Bindings Bind(Fixture &f) {
  fixture = &f;
  return {true, &f.database_ptr, &f.fallback_ptr, &Hash, &Lookup, &Construct, &Destroy,
      &Shown, &Final, &Cost, &Evaluate, &Affordable, &ReasonDestroy};
}
void Verify(const Entry &entry, const p::DecisionTerms &terms) {
  Check(terms.available && terms.unavailable_reason.empty() && terms.is_shown == entry.shown &&
      terms.can_take == entry.final && terms.affordable == entry.affordable,
      "native false remains a successful independent observation");
  Check(terms.costs_raw == entry.costs, "all ten signed resource slots are preserved in native order");
  Check(terms.reasons_available && terms.can_take_reasons == entry.reason,
      "complete UTF8 reason and legal empty or SSO text survive serialization source");
}
void Run(Fixture &f, const std::filesystem::path &out, const char *name) {
  p::Terms terms;
  const bool complete = p::ReadPlayerRepentancePetitionDecisionTerms12003(Bind(f), f.actor.data(),
      Fixture::id, Fixture::date, Fixture::epoch, terms);
  Check(complete == !f.entries[1].missing && terms.available == complete, "aggregate status retains row failure");
  Check(terms.played_character_id == Fixture::id && terms.date_raw == Fixture::date &&
      terms.capture_epoch == Fixture::epoch, "same owner frame retained");
  Verify(f.entries[0], terms.head_of_faith);
  if (f.entries[1].missing) {
    Check(!terms.antipope.available && !terms.antipope.costs_raw && !terms.antipope.is_shown &&
        terms.antipope.unavailable_reason == "decision_definition_unavailable",
        "absent second definition retains nulls without losing first successful result");
  } else Verify(f.entries[1], terms.antipope);
  const int reads = f.entries[1].missing ? 1 : 2;
  Check(f.hashes == 2 && f.lookups == 2 && f.constructed == reads && f.destroyed == reads &&
      f.reason_destroyed == reads && f.shown_calls == reads && f.final_calls == reads &&
      f.cost_calls == reads && f.evaluated_calls == reads && f.affordable_calls == reads,
      "each native operation executes once per available fixed definition");
  const auto wire = p::SerializePlayerRepentancePetitionDecisionTerms12003(terms);
  Check(wire.find("\"selection_context\":\"unselected_player_root\"") != std::string::npos &&
      wire.find("\"quote_context\":\"unselected_player_root\",\"repentance_option_quote_ready\":false") != std::string::npos &&
      wire.find("\"resource_order\":[\"gold\",\"prestige\",\"piety\",\"renown\",\"influence\",\"herd\",\"treasury\",\"treasury_or_gold\",\"merit\",\"barter_goods\"]") != std::string::npos,
      "wire states unselected semantics and all ten resource names");
  std::ofstream(out / name, std::ios::binary) << wire << '\n';
}
} // namespace
int main(int argc, char **argv) {
  try {
    Check(argc == 2, "output directory supplied");
    const std::filesystem::path out(argv[1]);
    Fixture ordinary; Run(ordinary, out, "two-fixed-decisions-independent-final.json");
    Fixture empty;
    empty.entries[0].reason.clear(); empty.entries[0].final = true; empty.entries[0].shown = false;
    empty.entries[0].costs.fill(0); empty.entries[1].reason = "X rejected";
    Run(empty, out, "empty-and-sso-reasons-zero-cost.json");
    Fixture missing; missing.entries[1].missing = true;
    Run(missing, out, "missing-antipope-preserves-main.json");
    Fixture wrong; p::Terms terms;
    Check(!p::ReadPlayerRepentancePetitionDecisionTerms12003(Bind(wrong), wrong.actor.data(),
        Fixture::id + 1, Fixture::date, Fixture::epoch, terms) && wrong.hashes == 0 &&
        terms.unavailable_reason == "played_character_unavailable", "actual player mismatch never reaches native evaluation");
    std::ofstream(out / "played-character-mismatch.json", std::ios::binary)
        << p::SerializePlayerRepentancePetitionDecisionTerms12003(terms) << '\n';
    std::cout << "PASS scenarios=4 checks=" << checks
        << " production_leaf=true production_serializer=true native_callbacks=synthetic game=false live=false\n";
    return 0;
  } catch (const std::exception &error) { std::cerr << "FAIL " << error.what() << '\n'; return 1; }
}
