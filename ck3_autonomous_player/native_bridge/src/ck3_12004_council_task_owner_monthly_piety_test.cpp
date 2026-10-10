#include "xar_bridge/ck3_12004_council_task_owner_monthly_piety.hpp"
#include "xar_bridge/ck3_12004.hpp"

#include <array>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <string_view>

namespace {
using namespace xar::ck3_12004;
using Failure = CouncilTaskOwnerMonthlyPietyFailure12004;
void Require(bool condition, const char *message) {
  if (!condition) { std::cerr << message << '\n'; std::exit(1); }
}
struct Fixture;
Fixture *active = nullptr;
struct Fixture {
  std::array<std::byte, 32> scopes{}, keyword{};
  std::array<std::byte, 8> type{};
  std::int64_t raw = 45000;
  unsigned build_calls = 0, value_calls = 0, destroy_calls = 0;
  void *owned = nullptr;
  bool numeric_returns_output = true, builder_returns_storage = true;
  Fixture() {
    active = this;
    // Preserve every original scope byte, including the native target context.
    scopes.fill(std::byte{0x3A});
    const std::int32_t incumbent = 32440, owner = 29829;
    std::memcpy(scopes.data(), &incumbent, sizeof(incumbent));
    std::memcpy(scopes.data() + 4, &owner, sizeof(owner));
    SetKeyword("monthly_piety");
  }
  void SetKeyword(std::string_view text) {
    Require(text.size() <= 15, "fixture inline native CString only");
    keyword.fill(std::byte{});
    std::memcpy(keyword.data(), text.data(), text.size());
    const std::uint64_t size = text.size(), capacity = 15;
    std::memcpy(keyword.data() + 0x10, &size, sizeof(size));
    std::memcpy(keyword.data() + 0x18, &capacity, sizeof(capacity));
  }
  static bool Memory(void *, const void *at, void *out, std::size_t size) noexcept {
    if (!at || !out || !size) return false;
    std::memcpy(out, at, size); return true;
  }
  static const std::string *Keyword(std::int32_t token) {
    Require(token == 11117, "actual4 named monthly-piety keyword ID");
    return reinterpret_cast<const std::string *>(active->keyword.data());
  }
  static void *Build(const void *type, void *storage, const void *scopes) {
    Require(type == active->type.data(), "actual TaskType receiver");
    Require(std::memcmp(scopes, active->scopes.data(), 32) == 0,
            "unmodified original incumbent/owner/target scopes");
    Require(reinterpret_cast<std::uintptr_t>(storage) % 8 == 0,
            "native output alignment");
    ++active->build_calls; active->owned = storage;
    return active->builder_returns_storage ? storage : nullptr;
  }
  static std::int64_t *Value(const void *whole, std::int64_t *out, std::uint16_t id) {
    Require(whole == active->owned && id == 97,
            "whole standalone receiver and actual4 uint16 modifier ID");
    ++active->value_calls; *out = active->raw;
    return active->numeric_returns_output ? out : nullptr;
  }
  static void Destroy(void *whole) {
    Require(whole == active->owned, "release original owned aggregate");
    ++active->destroy_calls; active->owned = nullptr;
  }
  CouncilTaskOwnerMonthlyPietyObservation12004 Execute() {
    active = this;
    return ReadCouncilTaskOwnerMonthlyPiety12004(
        {Build, Value, Destroy, Keyword}, type.data(), scopes.data(), Memory, this);
  }
};
} // namespace

int main() {
  const auto valid = BindCouncilTaskOwnerMonthlyPiety12004(0x140000000, kExecutableSha256);
  Require(reinterpret_cast<std::uintptr_t>(valid.build) == 0x1431ABDF0 &&
          reinterpret_cast<std::uintptr_t>(valid.value) == 0x1423036E0,
          "exact4 common lifecycle bindings");
  Require(!BindCouncilTaskOwnerMonthlyPiety12004(0x140000000, "other-build").build &&
          !BindCouncilTaskOwnerMonthlyPiety12004(0, kExecutableSha256).build,
          "only exact4 nonzero image binds");
  for (const auto raw : {std::int64_t{45000}, std::int64_t{0}, std::int64_t{-5000}}) {
    Fixture fixture; fixture.raw = raw;
    const auto out = fixture.Execute();
    Require(out.raw == raw && out.unavailable_reason == Failure::none &&
            out.incumbent_character_id == 32440 && out.owner_character_id == 29829 &&
            std::string_view(out.observed_keyword_key.data()) == "monthly_piety",
            "native signed/zero component and actual scope identities");
    Require(fixture.build_calls == 1 && fixture.value_calls == 1 &&
            fixture.destroy_calls == 1 && !fixture.owned, "owned native lifetime");
  }
  {
    Fixture fixture; fixture.SetKeyword("other_modifier");
    const auto out = fixture.Execute();
    Require(!out.raw && out.unavailable_reason == Failure::keyword_mismatch &&
            !fixture.build_calls && !fixture.destroy_calls,
            "keyword mismatch does not invoke evaluator");
  }
  for (const bool wrong_builder : {false, true}) {
    Fixture fixture;
    fixture.builder_returns_storage = !wrong_builder;
    fixture.numeric_returns_output = false;
    const auto out = fixture.Execute();
    Require(!out.raw && out.unavailable_reason == Failure::numeric_unavailable &&
            fixture.destroy_calls == 1 && !fixture.owned &&
            fixture.value_calls == (wrong_builder ? 0U : 1U),
            "failed numeric/builder return still releases original aggregate");
  }
  {
    Fixture fixture;
    const auto out = ReadCouncilTaskOwnerMonthlyPiety12004({}, fixture.type.data(),
        fixture.scopes.data(), Fixture::Memory, &fixture);
    Require(!out.raw && out.unavailable_reason == Failure::native_bindings_unavailable,
            "missing native bindings remain optional unavailable");
  }
  std::cout << "GREEN task-owner monthly-piety direct leaf: 7 cases; no game/SDK calls\n";
}
