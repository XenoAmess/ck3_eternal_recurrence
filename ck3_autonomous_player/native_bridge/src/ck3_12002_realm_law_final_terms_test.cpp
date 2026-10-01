#include "xar_bridge/ck3_12002_realm_law_final_terms.hpp"

#include <array>
#include <cassert>
#include <cstring>
#include <iostream>
#include <string>

using namespace xar::ck3_12002::private_law;
namespace {
std::array<std::byte, 0xD00> law{};
int actor = 0;
bool kind = true, active = false, allowed = true, reason_allowed = true;
std::string reason;
std::size_t destroys = 0, final_calls = 0, cost_calls = 0;
bool Kind(const void *value) { assert(value == law.data()); return kind; }
bool Active(const void *value, const void *definition) {
  assert(value == &actor && definition == law.data()); return active;
}
bool Final(const void *, const void *, void *sink) {
  assert(sink == nullptr); ++final_calls; return allowed;
}
std::int64_t *Cost(std::int64_t *out, const void *block, std::uint32_t actor_id) {
  assert(block == law.data() + 0xC40); // Catch accidental use of old +0xCD8.
  assert(actor_id == 0x01000123u); ++cost_calls;
  for (std::size_t i = 0; i < 10; ++i) out[i] = static_cast<std::int64_t>(i) * 100001 - 300000;
  return out;
}
bool Reason(const void *, const void *, void *sink) {
  auto *bytes = static_cast<std::byte *>(sink);
  std::uint64_t initial = 0;
  std::memcpy(&initial, bytes + 0x18, 8); assert(initial == 15);
  const auto size = static_cast<std::uint64_t>(reason.size());
  const auto capacity = size <= 15 ? std::uint64_t{15} : size;
  std::memcpy(bytes + 0x10, &size, 8); std::memcpy(bytes + 0x18, &capacity, 8);
  if (size <= 15) std::memcpy(bytes, reason.data(), reason.size());
  else { const auto *characters = reason.c_str(); std::memcpy(bytes, &characters, sizeof(characters)); }
  return reason_allowed;
}
void Destroy(void *) { ++destroys; }
RealmLawFinalTerms12002Operations Operations() {
  return {{&Kind, &Active, &Final, &Cost}, &Reason, &Destroy};
}
auto Read() { return ReadRealmLawFinalTerms12002({law.data(), &actor, 0x01000123u}, Operations()); }
}

int main() {
  assert(BindRealmLawFinalTermsImage12002(0x140000000, "legacy").terms.read_cost_q100000 == nullptr);
  const auto bound = BindRealmLawFinalTermsImage12002(0x140000000, kRealmLawFinalTermsExecutableSha256);
  assert(reinterpret_cast<std::uintptr_t>(bound.terms.read_cost_q100000) == 0x140000000 + kRealmLawNumericCostRva);
  reason = "";
  auto result = Read();
  assert(result.terms.status == RealmLawFinalTerms12002Status::can_enact && result.native_reason_available);
  assert(result.terms.cost_raw.front() == -300000 && result.terms.cost_raw.back() == 600009);
  assert(final_calls == 1 && cost_calls == 1 && destroys == 1);
  allowed = reason_allowed = false; reason = "Not enough prestige; the council refuses.";
  result = Read();
  assert(result.terms.status == RealmLawFinalTerms12002Status::engine_blocked);
  assert(result.terms.cost_available && result.native_reason == reason && destroys == 2);
  active = true; reason = "Already enacted";
  result = Read();
  assert(result.terms.status == RealmLawFinalTerms12002Status::already_active);
  assert(final_calls == 2 && cost_calls == 3 && destroys == 3);
  active = false; kind = false; reason = "Wrong law kind";
  result = Read();
  assert(result.terms.status == RealmLawFinalTerms12002Status::candidate_kind_rejected);
  assert(final_calls == 2 && cost_calls == 4 && destroys == 4);
  kind = allowed = true; reason_allowed = false;
  result = Read();
  assert(result.terms.status == RealmLawFinalTerms12002Status::unavailable && !result.native_reason_available);
  assert(destroys == 5);
  std::cout << "PASS: 1.20 law changed cost layout, ten signed costs, gates, copied native inline/heap reason\n";
}
