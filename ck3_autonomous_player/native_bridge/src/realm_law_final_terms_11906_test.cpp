#include "xar_bridge/realm_law_final_terms_11906.hpp"

#include <cassert>
#include <cstddef>
#include <cstdint>

using namespace xar::bridge;

namespace {

struct Fixture {
  std::byte law[0xD00]{};
  int actor = 0;
  bool kind_allowed = true;
  bool active = false;
  bool final_allowed = true;
  bool bad_cost_return = false;
  int kind_calls = 0;
  int active_calls = 0;
  int final_calls = 0;
  int cost_calls = 0;
};

Fixture *current = nullptr;

bool Kind(const void *law) {
  assert(law == current->law);
  ++current->kind_calls;
  return current->kind_allowed;
}

bool Active(const void *actor, const void *law) {
  assert(actor == &current->actor && law == current->law);
  ++current->active_calls;
  return current->active;
}

bool Final(const void *law, const void *actor, void *sink) {
  assert(law == current->law && actor == &current->actor && sink == nullptr);
  ++current->final_calls;
  return current->final_allowed;
}

std::int64_t *Cost(std::int64_t *out, const void *block,
                   std::uint32_t actor_id) {
  assert(block == current->law + 0xCD8 && actor_id == 0x1020304);
  ++current->cost_calls;
  out[0] = 1'000'000;
  out[1] = 10'000'000;
  out[7] = 200'000;
  return current->bad_cost_return ? nullptr : out;
}

RealmLawFinalTerms11906Operations Ops() {
  return {Kind, Active, Final, Cost};
}

RealmLawFinalTerms11906Input Input(Fixture &fixture) {
  return {fixture.law, &fixture.actor, 0x1020304};
}

} // namespace

int main() {
  {
    Fixture fixture{};
    current = &fixture;
    const auto result = ReadRealmLawFinalTerms11906(Input(fixture), Ops());
    assert(result.status == RealmLawFinalTerms11906Status::can_enact);
    assert(result.cost_available && result.cost_raw[0] == 1'000'000 &&
           result.cost_raw[1] == 10'000'000 && result.cost_raw[7] == 200'000);
    assert(fixture.kind_calls == 1 && fixture.active_calls == 1 &&
           fixture.final_calls == 1 && fixture.cost_calls == 1);
  }
  {
    Fixture fixture{};
    fixture.kind_allowed = false;
    current = &fixture;
    const auto result = ReadRealmLawFinalTerms11906(Input(fixture), Ops());
    assert(result.status ==
           RealmLawFinalTerms11906Status::candidate_kind_rejected);
    assert(result.cost_available && fixture.active_calls == 0 &&
           fixture.final_calls == 0 && fixture.cost_calls == 1);
  }
  {
    Fixture fixture{};
    fixture.active = true;
    current = &fixture;
    const auto result = ReadRealmLawFinalTerms11906(Input(fixture), Ops());
    assert(result.status == RealmLawFinalTerms11906Status::already_active);
    assert(result.cost_available && fixture.final_calls == 0);
  }
  {
    Fixture fixture{};
    fixture.final_allowed = false;
    current = &fixture;
    const auto result = ReadRealmLawFinalTerms11906(Input(fixture), Ops());
    assert(result.status == RealmLawFinalTerms11906Status::engine_blocked);
    assert(result.cost_available && fixture.final_calls == 1);
  }
  {
    Fixture fixture{};
    fixture.bad_cost_return = true;
    current = &fixture;
    const auto result = ReadRealmLawFinalTerms11906(Input(fixture), Ops());
    assert(result.status == RealmLawFinalTerms11906Status::unavailable);
    assert(!result.cost_available && result.cost_raw[0] == 0);
  }
  {
    Fixture fixture{};
    current = &fixture;
    auto operations = Ops();
    operations.read_cost_q100000 = nullptr;
    const auto result = ReadRealmLawFinalTerms11906(Input(fixture), operations);
    assert(result.status == RealmLawFinalTerms11906Status::unavailable);
    assert(fixture.kind_calls == 0 && fixture.cost_calls == 0);
  }
}
