#include "xar_bridge/ck3_12002_realm_law_components.hpp"

#include <array>
#include <cassert>
#include <cstring>
#include <iostream>

namespace {
using namespace xar::ck3_12002::private_law;
using xar::bridge::RealmLawGovernancePresenceV1;
using xar::bridge::RealmLawGovernanceSuccessionShapeV1;

std::array<std::byte, 0x2108> law{};
std::array<std::byte, 0x200> actor{};
bool have = false;
bool pass = true;
bool keep = true;
int scope_builds = 0;
int trigger_calls = 0;
int scope_destroys = 0;
const void *current_scope = nullptr;

void *Construct(void *scope, const void *character) {
  assert(character == actor.data());
  ++scope_builds;
  current_scope = scope;
  return scope;
}

bool Evaluate(const void *trigger, const void *scope) {
  assert(scope == current_scope);
  ++trigger_calls;
  if (trigger == law.data() + kRealmLawCanHaveOffset) return have;
  if (trigger == law.data() + kRealmLawCanPassOffset) return pass;
  assert(trigger == law.data() + kRealmLawCanKeepOffset);
  return keep;
}

void DestroyTail(void *tail) {
  assert(tail == static_cast<const std::byte *>(current_scope) + 0x118);
  ++scope_destroys;
}
void DestroyRows(void *) { assert(false); }

template <typename T>
void StorePolicy(std::size_t offset, T value) {
  std::memcpy(law.data() + kRealmLawSuccessionPolicyOffset + offset,
              &value, sizeof(value));
}

void TestIndependentPredicates() {
  const RealmLawComponentBindings12002 bindings{
      true, Construct, Evaluate, DestroyTail, DestroyRows};
  have = false;
  pass = true;
  keep = true;
  const auto first = ReadRealmLawComponents12002(law.data(), actor.data(), bindings);
  assert(first.complete && !first.can_have && first.can_pass && first.can_keep);
  assert(scope_builds == 1 && trigger_calls == 3 && scope_destroys == 1);
  have = true;
  pass = false;
  const auto second = ReadRealmLawComponents12002(law.data(), actor.data(), bindings);
  assert(second.complete && second.can_have && !second.can_pass && second.can_keep);
  assert(scope_builds == 2 && trigger_calls == 6 && scope_destroys == 2);
}

void TestCrownAuthorityAbsentShape() {
  law = {};
  StorePolicy(0, std::uint8_t{9});
  StorePolicy(1, std::uint8_t{3});
  StorePolicy(3, std::uint8_t{2});
  StorePolicy(4, std::uint8_t{2});
  StorePolicy(0x60, std::int64_t{0});
  RealmLawGovernanceSuccessionShapeV1 shape{};
  assert(ReadRealmLawSuccessionShape12002(law.data(), shape));
  assert(shape.presence == RealmLawGovernancePresenceV1::absent);
  assert(shape.title_division.presence == RealmLawGovernancePresenceV1::absent);
  assert(shape.traversal_order.presence == RealmLawGovernancePresenceV1::absent);
  assert(shape.rank.presence == RealmLawGovernancePresenceV1::absent);
  assert(shape.primary_heir_minimum_share.presence ==
      RealmLawGovernancePresenceV1::absent);
}

void TestInheritanceShapeAndLegalZeroShare() {
  StorePolicy(0, std::uint8_t{0});
  StorePolicy(1, std::uint8_t{0});
  StorePolicy(3, std::uint8_t{0});
  StorePolicy(4, std::uint8_t{1});
  StorePolicy(0x60, std::int64_t{0});
  RealmLawGovernanceSuccessionShapeV1 shape{};
  assert(ReadRealmLawSuccessionShape12002(law.data(), shape));
  assert(shape.presence == RealmLawGovernancePresenceV1::present);
  assert(std::string_view(shape.order_of_succession.bytes.data(),
                          shape.order_of_succession.size) == "inheritance");
  assert(std::string_view(shape.title_division.value.bytes.data(),
                          shape.title_division.value.size) == "partition");
  assert(shape.primary_heir_minimum_share.presence ==
      RealmLawGovernancePresenceV1::present);
  assert(shape.primary_heir_minimum_share.value_raw == 0);
  StorePolicy(0x60, std::int64_t{50000});
  assert(ReadRealmLawSuccessionShape12002(law.data(), shape));
  assert(shape.primary_heir_minimum_share.value_raw == 50000);
}
} // namespace

int main() {
  TestIndependentPredicates();
  TestCrownAuthorityAbsentShape();
  TestInheritanceShapeAndLegalZeroShare();
  std::cout << "realm-law-components-12002: GREEN (3)\n";
}
