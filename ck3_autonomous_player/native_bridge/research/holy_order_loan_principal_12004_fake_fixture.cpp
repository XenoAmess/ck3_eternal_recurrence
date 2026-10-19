// Isolated synthetic source-path fixture. Never link this TU into Native/SDK.
#include "holy_order_loan_principal_12004.hpp"
#include "xar_bridge/ck3_12004_religion_context_addons.hpp"

#include <array>
#include <cstring>
#include <intrin.h>
#include <string>

namespace {
namespace loan = xar::ck3_12004::religion::loan_principal;
namespace mc = xar::ck3_12003::religion::mystical_communion;
using xar::ck3_12004::CoreBindings;
using xar::ck3_12004::CoreSnapshotPrefix;
using xar::ck3_12004::PrisonerNamedBindings12004;
enum class Path { quote, missing_definition, first_failed, second_failed,
                  eval_failed, eval_seh, bookend_changed, cleanup_seh };

template <typename T> T Load(const void *p, std::size_t offset) noexcept {
  T result{};
  std::memcpy(&result, static_cast<const std::byte *>(p) + offset, sizeof(result));
  return result;
}
template <typename T> void Store(void *p, std::size_t offset, T value) noexcept {
  std::memcpy(static_cast<std::byte *>(p) + offset, &value, sizeof(value));
}
struct FakeAllocator { const std::uintptr_t *vptr = nullptr; };
struct Fixture {
  Path path = Path::quote;
  std::int64_t raw = 0;
  std::array<std::byte, 0xA0> definition{};
  std::array<std::byte, 16> character{}, first_data{}, second_data{}, intern{};
  std::array<std::uintptr_t, 3> allocator_vtable{};
  FakeAllocator first_allocator{}, second_allocator{};
  void *root = nullptr, *first = nullptr, *second = nullptr;
  int database = 0, intern_database = 0;
  int snapshots = 0, factory_calls = 0, evaluations = 0;
  int roots = 0, firsts = 0, seconds = 0, clear_seconds = 0;
  int free_firsts = 0, free_seconds = 0, destroy_roots = 0;
  bool invariants = true, packet_checked = false, packet_ok = false;
  std::uint8_t mode = 1;
  std::array<char, 32> events{};
  std::size_t event_count = 0;
};
Fixture *active = nullptr;
constexpr std::uint32_t kHash = 0x45AB12CD;
constexpr std::uintptr_t kPrimary = 0x12345000, kSecondary = 0x12345100;
constexpr std::int32_t kCharacter = 31254, kDate = 53145048;
void Event(char event) noexcept {
  auto &s = *active;
  if (s.event_count < s.events.size() - 1) s.events[s.event_count++] = event;
  else s.invariants = false;
}
void Free(void *allocator, void *data, std::size_t alignment) noexcept {
  auto &s = *active;
  if (allocator == &s.second_allocator) {
    Event('b'); ++s.free_seconds;
    s.invariants &= data == s.second_data.data() && alignment == 8 &&
        s.free_seconds == 1 && Load<std::int32_t>(s.second, 0xC) == 0;
  } else if (allocator == &s.first_allocator) {
    Event('a'); ++s.free_firsts;
    s.invariants &= data == s.first_data.data() && alignment == 8 &&
        s.free_firsts == 1 && Load<std::int32_t>(s.first, 0xC) == 0;
  } else s.invariants = false;
}
void *Root(void *p) noexcept {
  auto &s = *active;
  Event('R'); ++s.roots; s.root = p;
  Store(p, 0x40, std::uint64_t{0x123456789ABC});
  return p;
}
void DestroyRoot(void *p) noexcept {
  auto &s = *active;
  Event('r'); ++s.destroy_roots;
  s.invariants &= p == s.root && s.destroy_roots == 1 &&
      Load<std::uint64_t>(p, 0x40) == 0x123456789ABC &&
      Load<std::uint16_t>(p, 0) == 4 &&
      Load<std::uint64_t>(p, 8) == static_cast<std::uint32_t>(kCharacter);
}
void InitVector(void *p, void *data, FakeAllocator *allocator) noexcept {
  Store(p, 0, data); Store(p, 8, std::int32_t{1});
  Store(p, 0xC, std::int32_t{1}); Store(p, 0x10, allocator);
}
void *First(void *p) noexcept {
  auto &s = *active;
  Event('A'); ++s.firsts; s.first = p;
  InitVector(p, s.first_data.data(), &s.first_allocator);
  return s.path == Path::first_failed ? nullptr : p;
}
void *Second(void *p) noexcept {
  auto &s = *active;
  Event('B'); ++s.seconds; s.second = p;
  InitVector(p, s.second_data.data(), &s.second_allocator);
  return s.path == Path::second_failed ? nullptr : p;
}
void ClearSecond(void *p) noexcept {
  auto &s = *active;
  Event('C'); ++s.clear_seconds;
  s.invariants &= p == s.second && s.clear_seconds == 1;
  if (s.path == Path::cleanup_seh) __ud2();
  Store(p, 0xC, std::int32_t{0});
}
void *Database() noexcept { return &active->database; }
const void *Lookup(void *database, std::uint32_t hash) noexcept {
  auto &s = *active;
  s.invariants &= database == &s.database && hash == kHash;
  return s.path == Path::missing_definition ? nullptr : s.definition.data();
}
std::uint32_t Hash(void *database, const char *key, std::uint32_t size) noexcept {
  auto &s = *active;
  s.invariants &= database == &s.database && size == loan::kValueKey.size() &&
      std::memcmp(key, loan::kValueKey.data(), size) == 0;
  return kHash;
}
void *InternDatabase() noexcept { return &active->intern_database; }
const void *Intern(void *database, const void *view) noexcept {
  auto &s = *active;
  s.invariants &= database == &s.intern_database &&
      Load<std::uint32_t>(view, 8) == loan::kValueKey.size() &&
      std::memcmp(Load<const char *>(view, 0), loan::kValueKey.data(),
                  loan::kValueKey.size()) == 0;
  return s.intern.data();
}
std::int64_t *Evaluate(const void *definition, std::int64_t *out,
    void *context, void *optional, const void *source) noexcept {
  auto &s = *active;
  Event('E'); ++s.evaluations; s.packet_checked = true;
  s.packet_ok = definition == s.definition.data() && out && context && source &&
      !optional && Load<void *>(context, 0) == s.root &&
      Load<void *>(context, 8) == nullptr && Load<void *>(context, 0x10) == s.root &&
      Load<void *>(context, 0x18) == s.first &&
      Load<std::uint8_t>(context, 0x20) == s.mode &&
      static_cast<std::byte *>(s.first) + 0x128 == s.second &&
      Load<void *>(s.first, 0x3D0) == s.root &&
      Load<std::uint16_t>(s.root, 0) == 4 &&
      Load<std::uint64_t>(s.root, 8) == static_cast<std::uint32_t>(kCharacter) &&
      Load<const void *>(source, 0) == s.intern.data() &&
      Load<std::uint8_t>(source, 0x14) == 1 &&
      Load<std::int32_t>(source, 0x18) == -1;
  if (!s.packet_ok) return nullptr;
  if (s.path == Path::eval_seh) __ud2();
  if (s.path == Path::eval_failed) return nullptr;
  *out = s.raw;
  return out;
}
CoreBindings Core() noexcept { CoreBindings b{}; b.enabled = true; return b; }
PrisonerNamedBindings12004 Named() noexcept {
  PrisonerNamedBindings12004 b{};
  b.enabled = true; b.core = Core();
  b.named_database = &Database; b.lookup_named = &Lookup;
  b.construct_support_118 = &First; b.construct_support_2a8 = &Second;
  b.intern_database = &InternDatabase; b.intern_string = &Intern;
  b.evaluate_fixed = &Evaluate; b.destroy_support_rows = &ClearSecond;
  b.evaluation_flag = &active->mode;
  b.named_primary_vtable = kPrimary; b.named_secondary_vtable = kSecondary;
  return b;
}
mc::Bindings RootBindings() noexcept {
  mc::Bindings b{}; b.enabled = true;
  b.decision_hash = &Hash; b.root_construct = &Root; b.root_destroy = &DestroyRoot;
  return b;
}
} // namespace

// The actual compiled object has exactly these five project undefined symbols.
namespace xar::ck3_12004 {
CoreBindings BindCoreImage(std::uintptr_t, std::string_view) noexcept {
  ++active->factory_calls; return Core();
}
void *ResolveCoreCharacter(const CoreBindings &b, std::int32_t id) noexcept {
  return b.enabled && id == kCharacter ? active->character.data() : nullptr;
}
bool ReadCoreSnapshot(const CoreBindings &b, CoreSnapshotPrefix &out) noexcept {
  if (!b.enabled) return false;
  auto &s = *active; ++s.snapshots; out = {};
  out.local_player_id = 7; out.map_ready = true; out.has_played_character = true;
  out.played_character_id = kCharacter; out.played_character_alive = true;
  out.clock = {kDate, 1, true};
  if (s.path == Path::bookend_changed && s.snapshots > 1) ++out.clock.date_raw;
  return true;
}
PrisonerNamedBindings12004 BindPrisonerNamedImage12004(
    std::uintptr_t, std::string_view) noexcept {
  ++active->factory_calls; return Named();
}
namespace religion {
ContextAddonBindings BindReligionContextAddonsImage12004(
    std::uintptr_t, std::string_view) noexcept {
  ++active->factory_calls; ContextAddonBindings b{};
  b.mystical_communion_bindings = RootBindings(); return b;
}
} // namespace religion
} // namespace xar::ck3_12004

namespace {
struct Case {
  const char *name; Path path; std::int64_t raw;
  bool available, released; const char *reason, *sequence; int evaluations;
};
std::string Quote(std::string_view value) {
  std::string out = "\"";
  for (char c : value) {
    if (c == '\\' || c == '"') out += '\\';
    out += c;
  }
  out += '"'; return out;
}
std::string RunCase(const Case &test, bool &all_passed) {
  Fixture s{}; s.path = test.path; s.raw = test.raw; active = &s;
  s.allocator_vtable[2] = reinterpret_cast<std::uintptr_t>(&Free);
  s.first_allocator.vptr = s.second_allocator.vptr = s.allocator_vtable.data();
  Store(s.definition.data(), 0, kPrimary);
  Store(s.definition.data(), 0x88, kSecondary);
  Store(s.definition.data(), 0x14, kHash);
  Store(s.definition.data(), 0x18, loan::kValueKey.data());
  Store(s.definition.data(), 0x28, static_cast<std::uint64_t>(loan::kValueKey.size()));
  Store(s.definition.data(), 0x30, std::uint64_t{31});
  Store(s.definition.data(), 0x38, std::uint32_t{0x4744624F});
  const auto bindings = loan::BindHolyOrderLoanPrincipalImage12004(
      0x180000000, xar::ck3_12004::kExecutableSha256);
  loan::Observation observation{};
  const bool result = loan::ReadPlayerHolyOrderLoanPrincipal12004(bindings, 77, observation);
  const std::string_view events(s.events.data(), s.event_count);
  const bool raw_ok = test.available ? observation.prospective_principal_raw == test.raw
                                    : !observation.prospective_principal_raw.has_value();
  const bool passed = bindings.enabled && s.factory_calls == 3 && s.invariants &&
      result == test.available && observation.available == test.available && raw_ok &&
      observation.owned_temporaries_released == test.released &&
      observation.unavailable_reason == test.reason && events == test.sequence &&
      s.evaluations == test.evaluations &&
      (test.evaluations == 0 ? !s.packet_checked : s.packet_checked && s.packet_ok);
  all_passed &= passed;
  std::string out = "{\"name\":" + Quote(test.name) + ",\"passed\":" + (passed ? "true" : "false");
  out += ",\"available\":"; out += observation.available ? "true" : "false";
  out += ",\"cleanup_verified\":"; out += observation.owned_temporaries_released ? "true" : "false";
  out += ",\"raw\":" + (observation.prospective_principal_raw
      ? std::to_string(*observation.prospective_principal_raw) : "null");
  out += ",\"eval_calls\":" + std::to_string(s.evaluations);
  out += ",\"events\":" + Quote(events) + ",\"reason\":" + Quote(observation.unavailable_reason);
  out += ",\"root_ctor\":" + std::to_string(s.roots) + ",\"first_ctor\":" + std::to_string(s.firsts);
  out += ",\"second_ctor\":" + std::to_string(s.seconds) + ",\"second_clear\":" + std::to_string(s.clear_seconds);
  out += ",\"second_free\":" + std::to_string(s.free_seconds) + ",\"first_free\":" + std::to_string(s.free_firsts);
  out += ",\"root_destroy\":" + std::to_string(s.destroy_roots) + "}";
  active = nullptr; return out;
}
} // namespace

extern "C" __declspec(dllexport) const char *RunHolyOrderLoanPrincipalFixture12004() noexcept {
  static bool called = false;
  static std::string report;
  if (called) return "{\"passed\":false,\"error\":\"export_called_more_than_once\"}";
  called = true;
  try {
    const std::array<Case, 9> cases{{
      {"positive_quote", Path::quote, 41'500'000, true, true, "", "RABECbar", 1},
      {"zero_quote", Path::quote, 0, true, true, "", "RABECbar", 1},
      {"definition_unavailable", Path::missing_definition, 0, false, true,
       "holy_order_value_definition_unavailable", "", 0},
      {"first_constructor_failed", Path::first_failed, 0, false, true,
       "numeric_scratch_construction_failed", "RAar", 0},
      {"second_constructor_failed", Path::second_failed, 0, false, true,
       "numeric_scratch_construction_failed", "RABCbar", 0},
      {"evaluation_wrong_out", Path::eval_failed, 0, false, true,
       "native_principal_evaluation_failed", "RABECbar", 1},
      {"evaluation_seh", Path::eval_seh, 0, false, true,
       "native_principal_evaluation_failed", "RABECbar", 1},
      {"bookend_changed", Path::bookend_changed, 41'500'000, false, true,
       "principal_source_or_player_frame_changed", "RABECbar", 1},
      {"cleanup_seh_unknown", Path::cleanup_seh, 41'500'000, false, false,
       "native_temporary_cleanup_unverified", "RABECar", 1},
    }};
    bool passed = true;
    report = "{\"schema\":\"xar.holy-order-loan-principal-synthetic-fixture.v1\",\"cases\":[";
    bool first = true;
    for (const auto &test : cases) {
      if (!first) report += ',';
      first = false; report += RunCase(test, passed);
    }
    report += "],\"passed\":"; report += passed ? "true}" : "false}";
    return report.c_str();
  } catch (...) {
    active = nullptr;
    return "{\"passed\":false,\"error\":\"fixture_cpp_exception\"}";
  }
}
