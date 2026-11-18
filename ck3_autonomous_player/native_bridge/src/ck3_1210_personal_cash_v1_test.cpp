#include "xar_bridge/ck3_1210_personal_cash_v1.hpp"

#include <array>
#include <bit>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <limits>
#include <map>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#if defined(_MSC_VER)
#include <windows.h>
#endif

namespace {
using namespace xar::ck3_1210;
constexpr auto kActor = std::bit_cast<std::int32_t>(std::uint32_t{0x81000001});
constexpr auto kContext = std::bit_cast<std::int32_t>(std::uint32_t{0x82000002});
constexpr std::uint64_t kRevision = (std::numeric_limits<std::uint64_t>::max)();
void Require(bool condition, const char *why) {
  if (!condition) { std::cerr << "FAIL " << why << '\n'; std::exit(1); }
}
template<class Buffer, class T>
void Store(Buffer &buffer, std::size_t offset, T value) {
  Require(offset <= buffer.size() && sizeof(T) <= buffer.size() - offset,
      "fixture memory write bounded");
  std::memcpy(buffer.data() + offset, &value, sizeof(value));
}

// Test-only independent recursive JSON reader: rejects duplicate keys,
// malformed numbers/escapes/trailing data. Assertions inspect parsed fields,
// rather than accepting substring matches as a valid producer document.
struct Json {
  enum class Kind { object, array, text, number, boolean, null_value };
  Kind kind = Kind::null_value;
  std::string value;
  std::map<std::string, Json> members;
  std::vector<Json> elements;
  const Json &At(std::string_view key) const {
    Require(kind == Kind::object, "JSON object expected");
    const auto found = members.find(std::string(key));
    Require(found != members.end(), "required producer field exists");
    return found->second;
  }
  bool IsNull() const { return kind == Kind::null_value; }
  bool Flag() const {
    Require(kind == Kind::boolean, "JSON boolean expected"); return value == "true";
  }
  const std::string &Text() const {
    Require(kind == Kind::text, "JSON text expected"); return value;
  }
  const std::string &Number() const {
    Require(kind == Kind::number, "JSON exact integer expected"); return value;
  }
};
class JsonReader {
 public:
  explicit JsonReader(std::string_view text) : text_(text) { }
  Json Document() { auto result = Value(0); Space(); Require(pos_ == text_.size(), "JSON end"); return result; }
 private:
  std::string_view text_;
  std::size_t pos_ = 0;
  void Space() { while (pos_ < text_.size() && (text_[pos_] == ' ' || text_[pos_] == '\r' ||
      text_[pos_] == '\n' || text_[pos_] == '\t')) ++pos_; }
  bool Take(char c) { Space(); if (pos_ == text_.size() || text_[pos_] != c) return false; ++pos_; return true; }
  void Need(char c) { Require(Take(c), "JSON punctuation"); }
  static bool Digit(char c) { return c >= '0' && c <= '9'; }
  std::string String() {
    Need('"'); std::string out;
    while (pos_ < text_.size()) {
      const auto c = static_cast<unsigned char>(text_[pos_++]);
      if (c == '"') return out;
      Require(c >= 0x20 && c < 0x80, "JSON fixture string ASCII/control rules");
      if (c != '\\') { out += static_cast<char>(c); continue; }
      Require(pos_ < text_.size(), "JSON complete escape");
      const char escape = text_[pos_++];
      switch (escape) {
        case '"': case '\\': case '/': out += escape; break;
        case 'b': out += '\b'; break; case 'f': out += '\f'; break;
        case 'n': out += '\n'; break; case 'r': out += '\r'; break; case 't': out += '\t'; break;
        case 'u': {
          unsigned code = 0;
          for (unsigned i = 0; i < 4; ++i) {
            Require(pos_ < text_.size(), "JSON four hex digits"); const char h = text_[pos_++];
            const int nibble = h >= '0' && h <= '9' ? h - '0' :
                h >= 'a' && h <= 'f' ? h - 'a' + 10 : h >= 'A' && h <= 'F' ? h - 'A' + 10 : -1;
            Require(nibble >= 0, "JSON valid hex digit"); code = code * 16 + static_cast<unsigned>(nibble);
          }
          Require(code < 0x80, "fixture escape stays ASCII"); out += static_cast<char>(code); break;
        }
        default: Require(false, "JSON known escape");
      }
    }
    Require(false, "JSON terminated string"); return {};
  }
  bool Literal(std::string_view value) {
    if (text_.substr(pos_, value.size()) != value) return false;
    pos_ += value.size(); return true;
  }
  Json Value(unsigned depth) {
    Require(depth < 32, "JSON bounded nesting"); Space();
    Require(pos_ < text_.size(), "JSON value exists"); Json out;
    if (Take('{')) {
      out.kind = Json::Kind::object; if (Take('}')) return out;
      do {
        const auto key = String(); Need(':');
        Require(out.members.emplace(key, Value(depth + 1)).second, "JSON keys unique");
        if (Take('}')) return out;
      } while (Take(','));
      Require(false, "JSON object close");
    }
    if (Take('[')) {
      out.kind = Json::Kind::array; if (Take(']')) return out;
      do { out.elements.push_back(Value(depth + 1)); if (Take(']')) return out; } while (Take(','));
      Require(false, "JSON array close");
    }
    if (text_[pos_] == '"') { out.kind = Json::Kind::text; out.value = String(); return out; }
    if (Literal("null")) return out;
    if (Literal("true")) { out.kind = Json::Kind::boolean; out.value = "true"; return out; }
    if (Literal("false")) { out.kind = Json::Kind::boolean; out.value = "false"; return out; }
    const auto start = pos_;
    if (text_[pos_] == '-') ++pos_;
    Require(pos_ < text_.size() && Digit(text_[pos_]), "JSON signed integer");
    if (text_[pos_] == '0') ++pos_;
    else while (pos_ < text_.size() && Digit(text_[pos_])) ++pos_;
    Require(pos_ == text_.size() || (!Digit(text_[pos_]) && text_[pos_] != '.' &&
        text_[pos_] != 'e' && text_[pos_] != 'E'), "JSON canonical integer token");
    out.kind = Json::Kind::number; out.value = std::string(text_.substr(start, pos_ - start)); return out;
  }
};

enum class Mode { normal, full_before_fail, full_after_fail, revision_before,
  revision_after, war_after, army_after, wallet_after, wallet_after_full,
  date_gross, pause_gross, actor_generation, null_context, throw_gross,
  fault_expenses, wrong_output, published_basis_after, request_revision_after,
  full_throw_before, full_throw_after, full_fault_after };
struct Fixture;
Fixture *active = nullptr;
void *LocalPlayer(void *);
void *Context(void *);
std::int64_t *Gross(std::int64_t *, void *, std::int64_t *, void *);
std::int64_t *Expenses(std::int64_t *, void *, void *, std::int64_t, bool, void *);
bool CurrentFull(void *, xar::game::Snapshot &, std::uint64_t &);
struct FixtureException {};
void Fault() {
#if defined(_MSC_VER)
  RaiseException(EXCEPTION_ACCESS_VIOLATION, 0, 0, nullptr);
#else
  throw FixtureException{};
#endif
}

struct Fixture {
  std::array<std::byte, 0xA8> state{};
  std::array<std::byte, 0x21> jomini{};
  std::array<std::byte, 0x200> players{};
  std::array<std::byte, 0x78> player{};
  std::vector<std::byte> data = std::vector<std::byte>(kPlayerCharacterManagerOffset + 0x70);
  std::array<std::byte, 0xE0> entry{};
  std::array<void *, 1> entries{entry.data()};
  std::array<std::byte, 0x1D8> actor{}, borrowed{};
  std::array<std::byte, 0x108> living{};
  std::array<std::byte, 0x30> storage{};
  std::array<std::byte, 0x30> slots{};
  void *state_pointer = state.data(), *jomini_pointer = jomini.data(),
      *storage_pointer = storage.data();
  PersonalCashBindingsV1 bindings{};
  PersonalCashReadContextV1 request{};
  // Independent test world and retained published object. No fixture here
  // constitutes an actual nonempty Full adapter qualification.
  xar::game::Snapshot world{}, published{};
  std::int32_t actor_id = kActor;
  std::int64_t wallet = -450000, gross = 500000, expenses = 720000, secondary = -71;
  std::int64_t other_output = 0;
  std::int64_t *gross_output = nullptr, *secondary_output = nullptr;
  unsigned core_calls = 0, full_calls = 0, context_calls = 0, gross_calls = 0, expense_calls = 0;
  std::uint64_t revision = kRevision;
  Mode mode = Mode::normal;
  void (*gross_before_return)(void *) noexcept = nullptr;
  void *gross_hook_context = nullptr;

  Fixture() {
    active = this;
    Store(state, 8, std::int32_t{123456}); Store(state, 0x70, std::int32_t{4});
    Store(state, 0xA0, data.data()); Store(jomini, 0x18, players.data());
    jomini[0x20] = std::byte{1}; Store(players, 0x1F0, std::int32_t{7});
    Store(player, 0x70, std::int32_t{7});
    Store(data, kPlayerCharacterManagerOffset + 0x58, entries.data());
    Store(data, kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Store(entry, 0xD8, std::int32_t{7}); Store(entry, 0xB0, actor_id);
    Store(actor, 0x18, actor_id); Store(actor, 0x1C, std::uint32_t{0x43686172});
    Store(actor, 0x1B0, living.data()); Store(living, 0x100, wallet);
    Store(borrowed, 0x18, kContext); Store(borrowed, 0x1C, std::uint32_t{0x43686172});
    Store(storage, 0x20, slots.data()); Store(storage, 0x2C, std::int32_t{3});
    Store(slots, 0x18, actor.data()); Store(slots, 0x28, borrowed.data());
    bindings = BindPersonalCashImageV1(0x140000000, kExecutableSha256);
    Require(bindings.exact_build_admitted && !bindings.integration_native_calls_permitted &&
        !bindings.monthly.integration_native_calls_permitted, "exact binding keeps both gates closed");
    const CoreBindings core{true, &state_pointer, &jomini_pointer, &storage_pointer, &LocalPlayer};
    bindings.gold.core = bindings.monthly.core = core;
    bindings.monthly.context = &Context; bindings.monthly.gross = &Gross;
    bindings.monthly.expenses = &Expenses;
    // Fixture-only admission after replacing all native callback addresses.
    bindings.integration_native_calls_permitted = true;
    bindings.monthly.integration_native_calls_permitted = true;
    Require(ReadCoreSnapshot(core, request.expected_core), "construct actual fake-memory Core");
    const auto &p = request.expected_core;
    world.date_raw = p.clock.date_raw; world.speed = p.clock.speed; world.paused = p.clock.paused;
    world.player_id = p.local_player_id; world.map_ready = p.map_ready;
    world.has_played_character = p.has_played_character;
    world.played_character_id = p.played_character_id;
    world.played_character_alive = p.played_character_alive;
    world.played_character_gold = {wallet, 100000};
    xar::game::ActiveWarSnapshot first{}, second{}; first.war_id = 17; second.war_id = 3;
    world.active_wars = {first, second};
    xar::game::ArmySnapshot army{}, other{}; army.army_id = 0; other.army_id = 23;
    army.owner_character_id = other.owner_character_id = actor_id;
    world.player_armies = {army, other}; published = world;
    request.paused_application_main_owner_admitted = true;
    request.published_native_revision = revision; request.published_full = &published;
    request.read_current_full = &CurrentFull; request.read_current_full_context = this;
    ResetCalls();
  }
  void ResetCalls() { core_calls = full_calls = context_calls = gross_calls = expense_calls = 0; }
  void ActorId(std::int32_t id) {
    Require((static_cast<std::uint32_t>(id) & 0x00FFFFFFU) <= 1, "fixture ID uses slot0 or1");
    actor_id = id; Store(actor, 0x18, id); Store(entry, 0xB0, id);
    Store(slots, 8, static_cast<void *>(nullptr)); Store(slots, 0x18, static_cast<void *>(nullptr));
    const auto index = static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
    Store(slots, static_cast<std::size_t>(index) * 0x10 + 8, actor.data());
    request.expected_core.played_character_id = id;
    world.played_character_id = published.played_character_id = id;
  }
};

void *LocalPlayer(void *) { ++active->core_calls; return active->player.data(); }
void *Context(void *actor) {
  auto &f = *active; ++f.context_calls;
  Require(actor == f.actor.data(), "monthly context receives actual actor");
  return f.mode == Mode::null_context ? nullptr : f.borrowed.data();
}
std::int64_t *Gross(std::int64_t *out, void *actor, std::int64_t *secondary, void *breakdown) {
  auto &f = *active; ++f.gross_calls;
  Require(actor == f.actor.data() && out && secondary && out != secondary && breakdown == nullptr,
      "real Monthly gross seam nullable-breakdown ABI");
  f.gross_output = out; f.secondary_output = secondary;
  *out = f.gross; *secondary = f.secondary;
  if (f.mode == Mode::throw_gross) throw FixtureException{};
  if (f.mode == Mode::date_gross) Store(f.state, 8, std::int32_t{123457});
  if (f.mode == Mode::pause_gross) f.jomini[0x20] = std::byte{};
  if (f.mode == Mode::actor_generation)
    Store(f.actor, 0x18, std::bit_cast<std::int32_t>(std::uint32_t{0x83000001}));
  if (f.mode == Mode::war_after) f.world.active_wars[0].war_id = 18;
  if (f.mode == Mode::army_after) f.world.player_armies[0].army_id = 1;
  if (f.mode == Mode::wallet_after) Store(f.living, 0x100, f.wallet + 1);
  if (f.mode == Mode::published_basis_after) ++f.published.played_character_gold.raw;
  if (f.mode == Mode::request_revision_after) --f.request.published_native_revision;
  if (f.gross_before_return != nullptr) f.gross_before_return(f.gross_hook_context);
  return f.mode == Mode::wrong_output ? &f.other_output : out;
}
std::int64_t *Expenses(std::int64_t *out, void *actor, void *context,
    std::int64_t secondary, bool exclude_military, void *breakdown) {
  auto &f = *active; ++f.expense_calls;
  Require(out && out != f.gross_output && out != f.secondary_output && actor == f.actor.data() &&
      context == f.borrowed.data() && secondary == f.secondary && !exclude_military &&
      breakdown == nullptr, "real Monthly expenses seam borrowed context/secondary/false/null ABI");
  if (f.mode == Mode::fault_expenses) Fault();
  *out = f.expenses; return out;
}
bool CurrentFull(void *context, xar::game::Snapshot &current, std::uint64_t &revision) {
  auto &f = *static_cast<Fixture *>(context); ++f.full_calls;
  if ((f.mode == Mode::full_before_fail && f.full_calls == 1) ||
      (f.mode == Mode::full_after_fail && f.full_calls == 2)) return false;
  if ((f.mode == Mode::full_throw_before && f.full_calls == 1) ||
      (f.mode == Mode::full_throw_after && f.full_calls == 2)) throw FixtureException{};
  if (f.mode == Mode::full_fault_after && f.full_calls == 2) Fault();
  CoreSnapshotPrefix p{};
  if (!ReadCoreSnapshot(f.bindings.gold.core, p)) return false;
  PersonalGoldObservationV1 gold{};
  if (!ReadPersonalGoldV1(f.bindings.gold, p, gold) || !gold.personal_gold_raw) return false;
  current = f.world;
  current.date_raw = p.clock.date_raw; current.speed = p.clock.speed; current.paused = p.clock.paused;
  current.player_id = p.local_player_id; current.map_ready = p.map_ready;
  current.has_played_character = p.has_played_character;
  current.played_character_id = p.played_character_id;
  current.played_character_alive = p.played_character_alive;
  current.played_character_gold = {*gold.personal_gold_raw, 100000};
  revision = f.revision;
  if ((f.mode == Mode::revision_before && f.full_calls == 1) ||
      (f.mode == Mode::revision_after && f.full_calls == 2)) --revision;
  // Independent final Gold check must still catch a changed wallet after the
  // callback sampled its Full object, rather than trusting cached amounts.
  if (f.mode == Mode::wallet_after_full && f.full_calls == 2)
    Store(f.living, 0x100, f.wallet + 1);
  return true;
}

Json Cash(const PersonalCashObservationV1 &out) {
  const auto root = JsonReader(SerializePersonalCashV1(out)).Document();
  Require(root.At("step").Text() == kPersonalCashStepV1 && root.At("accepted").Flag() &&
      root.At("private_build").Flag() && root.At("read_only").Flag() &&
      !root.At("advertised").Flag(), "legacy original result envelope");
  return root.At("war_cash_current_resources");
}
void Fixed(const Json &cash, std::string_view key, std::int64_t raw) {
  const auto &fixed = cash.At(key);
  Require(fixed.At("raw").Number() == std::to_string(raw) &&
      fixed.At("scale").Number() == "100000", "exact signed fixed-point scalar");
}
void UnknownScope(const PersonalCashObservationV1 &out, const Json &cash) {
  Require(out.partial && !out.full_snapshot_available && !out.root_ready && !out.formal_action_ready &&
      !out.true_treasury_observed && !out.military_categories_observed && !out.tax_categories_observed &&
      !out.prosperity_observed && !out.zero_native_side_effects_verified &&
      !out.native_unwind_cleanup_verified, "no Full/Root/action or unknown lifecycle grants");
  const auto &ready = cash.At("readiness");
  for (const auto name : {"current", "all_raised"}) {
    const auto &row = cash.At("military_expenses").At(name);
    Require(row.At("status").Text() == "unavailable" && row.At("gold_raw").IsNull() &&
        row.At("treasury_raw").IsNull() && row.At("resource_raw_native").IsNull() &&
        row.At("unavailable_reason").Text() == kPersonalCashMilitaryUnknownV1 &&
        !row.At("future_war_cost_upper_ready").Flag(), "military unknown is not fake zero/vector");
    Require(row.At("resource_kind").Text() == std::string("actor_military_") + name + "_maintenance" &&
        row.At("resource_id").Text() == std::to_string(out.frame.played_character_id) &&
        row.At("owner_character_id").Number() == std::to_string(out.frame.played_character_id) &&
        row.At("war_ids").elements.size() == out.active_war_ids.size() &&
        row.At("source_scope").Text() == "actor_owned_military_once_across_all_wars" &&
        row.At("time_basis").Text() == "month" && row.At("raw_scale").Number() == "100000",
        "military owner/frame/scope descriptors preserved");
  }
  Require(!ready.At("current_military_expenses_ready").Flag() &&
      !ready.At("all_raised_military_expenses_ready").Flag() &&
      !cash.At("true_treasury_observed").Flag() && !cash.At("complete_snapshot").Flag() &&
      !cash.At("native_getter_diagnostics").At("zero_native_side_effects_verified").Flag() &&
      !cash.At("native_getter_diagnostics").At("native_unwind_cleanup_verified").Flag(),
      "wire never claims military/Treasury/Full or lifecycle qualification");
  Require(!cash.members.contains("queried_snapshot_id") && !cash.members.contains("queried_revision") &&
      !cash.members.contains("queried_native_revision") && !cash.members.contains("current_raw_context_v1") &&
      !cash.members.contains("holy_order_loan_observation_v1") &&
      !cash.members.contains("war_payment_observations_v1"), "no receipt roles or unsupported finance extensions invented");
}
void Attempts(const Fixture &f, const PersonalCashObservationV1 &out) {
  Require(out.current_full_call_attempts == f.full_calls && out.context_call_attempts == f.context_calls &&
      out.gross_call_attempted == (f.gross_calls != 0) &&
      out.expenses_call_attempted == (f.expense_calls != 0), "actual callback attempts retained");
}
PersonalCashObservationV1 Read(Fixture &f) {
  PersonalCashObservationV1 out{};
  Require(ReadPersonalCashV1(f.bindings, f.request, out) && out.completed && out.same_frame_ready,
      "coherent personal cash observation completed");
  Require(out.personal_gold_raw == f.wallet && out.native_revision == kRevision &&
      out.frame.played_character_id == f.actor_id && out.frame.clock.date_raw == 123456 &&
      out.frame.clock.speed == 5, "retained actual Core/revision/wallet identity");
  Attempts(f, out); return out;
}
void Failure(Fixture &f) {
  PersonalCashObservationV1 out{};
  out.completed = out.same_frame_ready = true;
  out.personal_gold_raw = out.monthly_gross_income_raw = out.monthly_total_expenses_raw =
      out.monthly_net_income_raw = 777;
  out.current_full_call_attempts = out.context_call_attempts = 99;
  out.gross_call_attempted = out.expenses_call_attempted = true;
  Require(!ReadPersonalCashV1(f.bindings, f.request, out) && !out.completed && !out.same_frame_ready &&
      !out.personal_gold_raw && !out.monthly_gross_income_raw && !out.monthly_total_expenses_raw &&
      !out.monthly_net_income_raw && !out.unavailable_reason.empty(), "failed owner/frame read clears stale amounts");
  Attempts(f, out);
  const auto cash = Cash(out);
  Require(cash.At("status").Text() == "unavailable" && cash.At("current_treasury").IsNull() &&
      cash.At("player_monthly_gross_income").IsNull() &&
      cash.At("player_monthly_total_expenses").IsNull() &&
      cash.At("player_monthly_net_income").IsNull() &&
      !cash.At("readiness").At("same_frame_ready").Flag(), "failure serializes explicit unknown, never stale data");
  UnknownScope(out, cash);
}
void WalletOnly(Fixture &f) {
  const auto out = Read(f); const auto cash = Cash(out);
  Require(!out.monthly_gross_income_raw && !out.monthly_total_expenses_raw && !out.monthly_net_income_raw &&
      cash.At("status").Text() == "partial" && cash.At("readiness").At("same_frame_ready").Flag() &&
      cash.At("readiness").At("current_treasury_ready").Flag(), "stable wallet survives genuinely unavailable monthly group");
  Fixed(cash, "current_treasury", f.wallet);
  for (const auto stem : {"gross_income", "total_expenses", "net_income"}) {
    Require(cash.At(std::string("player_monthly_") + stem).IsNull() &&
        !cash.At("readiness").At(std::string("monthly_") + stem + "_ready").Flag() &&
        !cash.At(std::string("monthly_") + stem + "_unavailable_reason").Text().empty(),
        "monthly group null with explicit reasons/readiness, never invented zeros");
  }
  UnknownScope(out, cash);
}
struct CashAdmissionTrace { unsigned calls = 0, deny_at = 0; };
bool AdmitCashMonthlyTestOwner(void *opaque) noexcept {
  auto &trace = *static_cast<CashAdmissionTrace *>(opaque);
  return ++trace.calls != trace.deny_at;
}
} // namespace

int main(int argc, char **argv) {
  using namespace xar::ck3_1210;
  constexpr auto minimum = (std::numeric_limits<std::int64_t>::min)();
  constexpr auto maximum = (std::numeric_limits<std::int64_t>::max)();
  if (argc == 2) {
    Fixture f;
    const std::string_view option = argv[1];
    if (option == "--emit-overflow-json") { f.gross = minimum; f.expenses = 1; }
    else if (option == "--emit-wallet-only-json") f.mode = Mode::null_context;
    else if (option == "--emit-empty-scope-json") {
      f.world.active_wars.clear(); f.world.player_armies.clear(); f.published = f.world;
    } else Require(option == "--emit-json", "known fixture emission mode");
    std::cout << SerializePersonalCashV1(Read(f)) << '\n'; return 0;
  }
  Require(argc == 1, "no unexpected fixture arguments");
  {
    const auto b = BindPersonalCashImageV1(0x140000000, kExecutableSha256);
    Require(b.exact_build_admitted && !b.integration_native_calls_permitted &&
        !b.monthly.integration_native_calls_permitted &&
        !BindPersonalCashImageV1(0, kExecutableSha256).exact_build_admitted &&
        !BindPersonalCashImageV1(0x140000000, "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518").exact_build_admitted,
        "exact new binder rejects old SHA and does not open invocation gates");
  }
  for (unsigned gate = 0; gate < 3; ++gate) {
    Fixture f;
    if (gate == 0) f.bindings.integration_native_calls_permitted = false;
    if (gate == 1) f.bindings.monthly.integration_native_calls_permitted = false;
    if (gate == 2) f.request.paused_application_main_owner_admitted = false;
    Failure(f);
    Require(f.core_calls == 0 && f.full_calls == 0 && f.context_calls == 0 &&
        f.gross_calls == 0 && f.expense_calls == 0, "closed admission makes zero callbacks");
  }
  {
    Fixture f; const auto out = Read(f); const auto cash = Cash(out);
    Require(f.full_calls == 2 && f.context_calls == 2 && f.gross_calls == 1 && f.expense_calls == 1 &&
        cash.At("schema").Text() == kPersonalCashSchemaV1 && cash.At("game_version").Text() == "1.21.0" &&
        cash.At("executable_sha256").Text() == kExecutableSha256 && cash.At("status").Text() == "partial" &&
        cash.At("snapshot_revision").Number() == "18446744073709551615" &&
        cash.At("played_character_id").Number() == std::to_string(kActor), "exact original new-build source and full signed identity");
    Require(cash.At("active_war_ids").elements.size() == 2 &&
        cash.At("active_war_ids").elements[0].Number() == "17" &&
        cash.At("active_war_ids").elements[1].Number() == "3" &&
        cash.At("player_army_ids").elements[0].Number() == "0" &&
        cash.At("player_army_ids").elements[1].Number() == "23", "actual full scope/order including valid ArmyID0");
    Fixed(cash, "current_treasury", f.wallet); Fixed(cash, "player_monthly_gross_income", f.gross);
    Fixed(cash, "player_monthly_total_expenses", f.expenses);
    Fixed(cash, "player_monthly_net_income", -220000);
    const auto &semantics = cash.At("monthly_income_semantics");
    Require(semantics.members.size() == 6 &&
        semantics.At("version").Text() == "ck3-1.21.0-native-income-minus-total-expenses-v2" &&
        semantics.At("source_scope").Text() == "played_character_personal_gold" &&
        semantics.At("income_source").Text() == "native_character_monthly_gold_income" &&
        semantics.At("expense_source").Text() == "native_character_monthly_total_gold_expenses" &&
        semantics.At("time_basis").Text() == "month" && semantics.At("military_expenses_included").Flag(),
        "complete real monthly semantics marker");
    UnknownScope(out, cash);
  }
  for (const auto mode : {Mode::full_before_fail, Mode::full_after_fail, Mode::revision_before,
      Mode::revision_after, Mode::war_after, Mode::army_after, Mode::wallet_after,
      Mode::wallet_after_full, Mode::date_gross, Mode::pause_gross, Mode::actor_generation,
      Mode::published_basis_after, Mode::request_revision_after, Mode::full_throw_before,
      Mode::full_throw_after, Mode::full_fault_after}) {
    Fixture f; f.mode = mode; Failure(f);
  }
  for (const auto mode : {Mode::null_context, Mode::throw_gross, Mode::fault_expenses, Mode::wrong_output}) {
    Fixture f; f.mode = mode; WalletOnly(f);
  }
  {
    Fixture f; f.request.published_native_revision = 0; Failure(f);
    Require(f.full_calls == 0 && f.context_calls == 0, "zero published revision rejects before calls");
  }
  {
    Fixture f; f.published.played_character_gold.scale = 1; Failure(f);
    Require(f.full_calls == 0, "wrong wallet scale rejects before native calls");
  }
  {
    Fixture f; ++f.published.date_raw; Failure(f);
    Require(f.full_calls == 0, "Full/Core mismatch rejects before native calls");
  }
  {
    Fixture f; f.bindings.monthly.core.character_storage_slot = nullptr; Failure(f);
    Require(f.core_calls == 0, "different core binding rejected");
  }
  {
    Fixture f; f.world.active_wars[1].war_id = f.world.active_wars[0].war_id;
    f.published = f.world; Failure(f); Require(f.context_calls == 0, "duplicate scope is not filtered");
  }
  for (const auto values : {std::pair{minimum, std::int64_t{1}},
      std::pair{maximum, std::int64_t{-1}}}) {
    Fixture f; f.gross = values.first; f.expenses = values.second;
    const auto out = Read(f); const auto cash = Cash(out);
    Require(!out.monthly_net_income_raw && out.net_unavailable_reason == "war_cash_monthly_net_income_overflow" &&
        cash.At("player_monthly_net_income").IsNull() &&
        cash.At("monthly_net_income_unavailable_reason").Text() == "war_cash_monthly_net_income_overflow" &&
        !cash.At("readiness").At("monthly_net_income_ready").Flag(), "checked overflow exact legacy reason, no fake NET");
    Fixed(cash, "player_monthly_gross_income", f.gross);
    Fixed(cash, "player_monthly_total_expenses", f.expenses); UnknownScope(out, cash);
  }
  for (const auto values : {std::pair{minimum, std::int64_t{0}},
      std::pair{maximum, std::int64_t{0}}, std::pair{std::int64_t{0}, std::int64_t{0}}}) {
    Fixture f; f.gross = values.first; f.expenses = values.second;
    const auto out = Read(f); const auto cash = Cash(out);
    Fixed(cash, "player_monthly_net_income", f.gross);
    Require(cash.At("monthly_net_income_unavailable_reason").IsNull(), "int64 edge/zero NET observed exactly");
  }
  for (const auto id : {std::int32_t{0}, std::int32_t{1},
      (std::numeric_limits<std::int32_t>::min)(), kActor}) {
    Fixture f; f.ActorId(id); const auto out = Read(f);
    Require(Cash(out).At("played_character_id").Number() == std::to_string(id), "canonical signed full generation preserved");
  }
  {
    Fixture f; f.world.active_wars.clear(); f.world.player_armies.clear(); f.published = f.world;
    const auto out = Read(f); const auto cash = Cash(out);
    Require(cash.At("active_war_ids").elements.empty() && cash.At("player_army_ids").elements.empty(),
        "real empty basis retained as empty without fabricating scope");
  }
  {
    Fixture f; auto out = Read(f); out.monthly_net_income_raw = 42;
    const auto cash = Cash(out);
    Require(cash.At("current_treasury").IsNull() && cash.At("player_monthly_net_income").IsNull() &&
        !cash.At("readiness").At("same_frame_ready").Flag(), "inconsistent DTO serializer fails closed");
  }
  {
    PersonalCashObservationV1 out{}; out.unavailable_reason = "quote\" slash\\ control\n";
    const auto cash = Cash(out);
    Require(cash.At("unavailable_reason").Text() == out.unavailable_reason,
        "pure serializer escapes reasons into valid JSON");
  }
  for (const unsigned deny_at : {1U, 4U, 8U}) {
    Fixture f; CashAdmissionTrace trace{0, deny_at};
    f.bindings.monthly.native_call_admission = &AdmitCashMonthlyTestOwner;
    f.bindings.monthly.native_call_admission_context = &trace;
    PersonalCashObservationV1 observed{};
    Require(!ReadPersonalCashV1(f.bindings, f.request, observed) && !observed.completed &&
        !observed.same_frame_ready && !observed.personal_gold_raw && !observed.monthly_gross_income_raw &&
        !observed.monthly_total_expenses_raw && !observed.monthly_net_income_raw &&
        observed.unavailable_reason == "personal_cash_actor_owner_changed" &&
        observed.current_full_call_attempts == 1 && f.full_calls == 1 && trace.calls == deny_at,
        "failed native owner admission cannot revive a wallet partial using later valid-looking Full");
    Require(f.context_calls == (deny_at == 1 ? 0U : deny_at == 4 ? 1U : 2U) &&
        f.gross_calls == (deny_at == 1 ? 0U : 1U) && f.expense_calls == (deny_at == 8 ? 1U : 0U),
        "whole Cash failure retains exact already attempted monthly calls");
    Attempts(f, observed); const auto cash = Cash(observed);
    Require(cash.At("status").Text() == "unavailable" && cash.At("current_treasury").IsNull(),
        "owner loss is distinct from an ordinary stable-wallet monthly unknown");
  }
  std::cout << "ck3_1210_personal_cash_v1 NoGame fixture PASS\n";
  return 0;
}
