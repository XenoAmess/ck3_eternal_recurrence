#include "xar_bridge/ck3_12002_nonwar_metrics.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <string_view>
#include <utility>

namespace {

template <std::size_t N, typename T>
void Put(std::array<std::byte, N> &blob, std::size_t offset, T value) {
  std::memcpy(blob.data() + offset, &value, sizeof(value));
}

struct Fixture {
  std::array<std::byte, 0x1D0> character{};
  std::array<std::byte, 0x130> land{};
  std::array<std::byte, 0x30> legitimacy{};
  std::int64_t income = -123456;
  std::int64_t health = 450000;
  std::int32_t domain_size = 4;
  std::int32_t domain_limit = 7;
  bool bad_income_pointer = false;
  bool bad_health_pointer = false;
  const void *unreadable = nullptr;
  int calls = 0;
  bool native_arguments_correct = true;

  Fixture() {
    Put(character, 0x1B8, std::uintptr_t{0xBAD001}); // obsolete land offset
    Put(character, 0x1C0, static_cast<void *>(land.data()));
    Put(character, 0x1C8, static_cast<void *>(legitimacy.data()));
    Put(land, 0x12C, std::int32_t{3});
    Put(legitimacy, 0x28, std::int64_t{5600000});
  }
};

Fixture *current = nullptr;

#if defined(_MSC_VER)
#define METRICS_FASTCALL __fastcall
#else
#define METRICS_FASTCALL
#endif

std::int64_t *METRICS_FASTCALL Income(std::int64_t *out, void *character,
                                    void *breakdown, void *context) {
  ++current->calls;
  current->native_arguments_correct &= character == current->character.data() &&
                                       breakdown == nullptr && context == nullptr;
  *out = current->income;
  return current->bad_income_pointer ? nullptr : out;
}

std::int64_t *METRICS_FASTCALL Health(void *character, std::int64_t *out) {
  ++current->calls;
  current->native_arguments_correct &= character == current->character.data();
  *out = current->health;
  return current->bad_health_pointer ? nullptr : out;
}

std::int32_t METRICS_FASTCALL DomainSize(void *character) {
  ++current->calls;
  current->native_arguments_correct &= character == current->character.data();
  return current->domain_size;
}

std::int32_t METRICS_FASTCALL DomainLimit(void *character) {
  ++current->calls;
  current->native_arguments_correct &= character == current->character.data();
  return current->domain_limit;
}

#undef METRICS_FASTCALL

bool Memory(void *context, const void *address, void *out,
            std::size_t size) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  if (address == fixture.unreadable) {
    return false;
  }
  const auto value = reinterpret_cast<std::uintptr_t>(address);
  for (const auto &range : std::array<std::pair<const void *, std::size_t>, 3>{
           std::pair<const void *, std::size_t>{fixture.character.data(),
                                               fixture.character.size()},
           {fixture.land.data(), fixture.land.size()},
           {fixture.legitimacy.data(), fixture.legitimacy.size()}}) {
    const auto begin = reinterpret_cast<std::uintptr_t>(range.first);
    if (value >= begin && value - begin <= range.second &&
        size <= range.second - (value - begin)) {
      std::memcpy(out, address, size);
      return true;
    }
  }
  return false;
}

bool Sample(Fixture &fixture,
            xar::ck3_12002::NonwarMetricsProjection12002 &out,
            std::string_view &failure,
            bool missing_callback = false) {
  current = &fixture;
  xar::ck3_11906::CampaignRootNativeEnvironmentV1 environment;
  environment.monthly_gold_income = Income;
  environment.health = missing_callback ? nullptr : Health;
  environment.domain_size = DomainSize;
  environment.domain_limit = DomainLimit;
  xar::ck3_11906::CampaignRootAccessV1 access;
  access.context = &fixture;
  access.read_memory = Memory;
  return xar::ck3_12002::ReadNonwarMetrics12002(
      environment, access, fixture.character.data(), out, failure);
}

bool Check(bool value, std::string_view message) {
  if (!value) {
    std::cerr << message << '\n';
  }
  return value;
}

bool TestObservedMetrics() {
  Fixture fixture;
  xar::ck3_12002::NonwarMetricsProjection12002 first, second;
  std::string_view failure;
  if (!Check(Sample(fixture, first, failure) && failure.empty() &&
                 first.monthly_gold_income_raw == -123456 &&
                 first.health_raw == 450000 && first.domain_size == 4 &&
                 first.domain_limit == 7 && first.targeting_faction_count == 3 &&
                 first.legitimacy.value ==
                     xar::game::FixedPointValue{5600000, 100000} &&
                 first.legitimacy.unavailable_reason.empty() &&
                 fixture.calls == 4 && fixture.native_arguments_correct,
             "exact new-layout required metrics and legitimacy")) {
    return false;
  }
  if (!Check(Sample(fixture, second, failure) && first == second,
             "repeated projection is comparable")) {
    return false;
  }
  Put(fixture.character, 0x1C0, static_cast<void *>(nullptr));
  Put(fixture.character, 0x1C8, static_cast<void *>(nullptr));
  fixture.domain_size = 0;
  fixture.domain_limit = 1;
  fixture.health = -100000;
  return Check(Sample(fixture, second, failure) &&
                   second.targeting_faction_count == 0 &&
                   second.health_raw == -100000 && second.domain_size == 0 &&
                   second.domain_limit == 1 && !second.legitimacy.value &&
                   second.legitimacy.unavailable_reason == "data_absent" &&
                   first != second,
               "native absent land is zero; absent legitimacy is diagnostic");
}

bool TestRequiredFailures() {
  Fixture fixture;
  xar::ck3_12002::NonwarMetricsProjection12002 out;
  std::string_view failure;
  if (!Check(!Sample(fixture, out, failure, true) && fixture.calls == 0 &&
                 failure == "nonwar_metrics_environment_unavailable",
             "missing callback must stop before native calls")) {
    return false;
  }
  fixture.bad_income_pointer = true;
  if (!Check(!Sample(fixture, out, failure) &&
                 failure == "player_monthly_gold_income_unavailable",
             "income output pointer must roundtrip")) {
    return false;
  }
  fixture.bad_income_pointer = false;
  fixture.bad_health_pointer = true;
  if (!Check(!Sample(fixture, out, failure) &&
                 failure == "player_health_unavailable",
             "health output pointer must roundtrip")) {
    return false;
  }
  fixture.bad_health_pointer = false;
  fixture.domain_size = -1;
  if (!Check(!Sample(fixture, out, failure) &&
                 failure == "player_domain_unavailable",
             "negative domain size is not an observation")) {
    return false;
  }
  fixture.domain_size = 0;
  fixture.domain_limit = 0;
  if (!Check(!Sample(fixture, out, failure) &&
                 failure == "player_domain_unavailable",
             "domain limit follows native minimum of one")) {
    return false;
  }
  fixture.domain_limit = 1;
  fixture.unreadable = fixture.character.data() + 0x1C0;
  if (!Check(!Sample(fixture, out, failure) &&
                 failure == "player_targeting_factions_unavailable",
             "unreadable land pointer is not absent land")) {
    return false;
  }
  fixture.unreadable = nullptr;
  Put(fixture.land, 0x12C, std::int32_t{-1});
  return Check(!Sample(fixture, out, failure) &&
                   failure == "player_targeting_factions_unavailable",
               "negative targeting faction count rejects sample");
}

bool TestLegitimacyDiagnostic() {
  Fixture fixture;
  xar::ck3_12002::NonwarMetricsProjection12002 out;
  std::string_view failure;
  fixture.unreadable = fixture.character.data() + 0x1C8;
  if (!Check(Sample(fixture, out, failure) && !out.legitimacy.value &&
                 out.legitimacy.unavailable_reason == "data_pointer_unreadable",
             "unreadable legitimacy pointer stays optional diagnostic")) {
    return false;
  }
  fixture.unreadable = fixture.legitimacy.data() + 0x28;
  if (!Check(Sample(fixture, out, failure) && !out.legitimacy.value &&
                 out.legitimacy.unavailable_reason == "balance_unreadable",
             "unreadable legitimacy balance stays optional diagnostic")) {
    return false;
  }
  fixture.unreadable = nullptr;
  Put(fixture.legitimacy, 0x28, std::int64_t{-1});
  if (!Check(Sample(fixture, out, failure) && !out.legitimacy.value &&
                 out.legitimacy.unavailable_reason == "balance_invalid",
             "negative legitimacy follows published diagnostic contract")) {
    return false;
  }
  Put(fixture.legitimacy, 0x28, std::int64_t{0});
  return Check(Sample(fixture, out, failure) &&
                   out.legitimacy.value == xar::game::FixedPointValue{0, 100000} &&
                   out.legitimacy.unavailable_reason.empty(),
               "actual zero legitimacy is available");
}

bool TestBoundAddresses() {
  xar::ck3_11906::CampaignRootNativeEnvironmentV1 environment;
  environment.exact_build_admitted = false;
  constexpr std::uintptr_t base = 0x140000000;
  xar::ck3_12002::BindNonwarMetrics12002(environment, base);
  return Check(!environment.exact_build_admitted &&
                   reinterpret_cast<std::uintptr_t>(environment.monthly_gold_income) ==
                       base + 0x2BCA960 &&
                   reinterpret_cast<std::uintptr_t>(environment.health) ==
                       base + 0x28C6500 &&
                   reinterpret_cast<std::uintptr_t>(environment.domain_size) ==
                       base + 0x28B7200 &&
                   reinterpret_cast<std::uintptr_t>(environment.domain_limit) ==
                       base + 0x28B71D0,
               "binder does not override caller build admission");
}

} // namespace

int main() {
  if (!TestObservedMetrics() || !TestRequiredFailures() ||
      !TestLegitimacyDiagnostic() || !TestBoundAddresses()) {
    return 1;
  }
  std::cout << "CK3 1.20.0.2 nonwar metrics fixture GREEN\n";
  return 0;
}
