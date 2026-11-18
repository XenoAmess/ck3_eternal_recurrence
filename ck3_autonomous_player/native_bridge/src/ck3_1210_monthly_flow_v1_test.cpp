#include "xar_bridge/ck3_1210_monthly_flow_v1.hpp"

#include <array>
#include <bit>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <limits>
#include <vector>

#if defined(_MSC_VER)
#include <windows.h>
#endif

namespace {
using namespace xar::ck3_1210;
constexpr auto kActorId = std::bit_cast<std::int32_t>(std::uint32_t{0x81000001});
constexpr auto kContextId = std::bit_cast<std::int32_t>(std::uint32_t{0x82000002});
constexpr std::int32_t kAlternateId = 0x03000003;
unsigned context_destructions = 0, cpp_unwinds = 0;
void Require(bool value, const char *message) {
  if (!value) { std::cerr << "FAIL " << message << '\n'; std::exit(1); }
}
template <class Buffer, class T>
void Store(Buffer &buffer, std::size_t offset, T value) {
  Require(offset <= buffer.size() && sizeof(value) <= buffer.size() - offset,
      "fixture write bounds");
  std::memcpy(buffer.data() + offset, &value, sizeof(value));
}
struct FixtureException {};
struct UnwindWitness { ~UnwindWitness() { ++cpp_unwinds; } };
void Throw() { [[maybe_unused]] UnwindWitness witness{}; throw FixtureException{}; }
void Fault() {
#if defined(_MSC_VER)
  RaiseException(EXCEPTION_ACCESS_VIOLATION, 0, 0, nullptr);
#else
  throw FixtureException{};
#endif
}
struct BorrowedContext {
  std::array<std::byte, 0x1D8> bytes{};
  ~BorrowedContext() { ++context_destructions; }
};
enum class Mode {
  normal, null_context, fallback_context, different_context_second,
  throw_context, throw_gross, throw_expenses, throw_context_second,
  fault_context, fault_gross, fault_expenses, fault_context_second,
  wrong_gross_output, wrong_expenses_output, date_context, date_gross,
  date_expenses, paused_gross, map_expenses, actor_generation_gross,
  actor_pointer_gross, actor_type_gross, actor_death_gross, actor_living_gross,
  actor_owner_gross, context_generation_gross, context_pointer_gross,
  context_type_expenses, context_living_expenses, context_owner_expenses
};
struct Fixture;
Fixture *active = nullptr;
void *LocalPlayer(void *);
void *Context(void *);
std::int64_t *Gross(std::int64_t *, void *, std::int64_t *, void *);
std::int64_t *Expenses(std::int64_t *, void *, void *, std::int64_t, bool, void *);

struct Fixture {
  std::array<std::byte, 0xA8> state{};
  std::array<std::byte, 0x21> jomini{};
  std::array<std::byte, 0x200> players{};
  std::array<std::byte, 0x78> player{};
  std::vector<std::byte> data =
      std::vector<std::byte>(kPlayerCharacterManagerOffset + 0x70);
  std::array<std::byte, 0xE0> entry{};
  std::array<void *, 1> entries{entry.data()};
  std::array<std::byte, 0x1D8> actor{}, actor_replacement{}, context_replacement{},
      alternate{}, fallback{};
  BorrowedContext borrowed;
  std::array<std::byte, 0x30> storage{};
  std::array<std::byte, 0x40> slots{};
  void *state_pointer = state.data(), *jomini_pointer = jomini.data(),
      *storage_pointer = storage.data();
  void *context_result = borrowed.bytes.data();
  MonthlyFlowBindingsV1 bindings{};
  std::int32_t actor_id = kActorId, context_id = kContextId;
  std::int64_t gross_value = 500000, secondary_value = -900001, expense_value = 720000;
  std::int64_t other_output = 0;
  std::int64_t *gross_output = nullptr, *secondary_output = nullptr;
  unsigned context_calls = 0, gross_calls = 0, expense_calls = 0, core_calls = 0;
  Mode mode = Mode::normal;
  bool map = true;

  Fixture() {
    active = this;
    Store(state, 8, std::int32_t{123456}); Store(state, 0x70, std::int32_t{4});
    Store(state, 0xA0, data.data()); Store(jomini, 0x18, players.data());
    jomini[0x20] = std::byte{1}; Store(players, 0x1F0, std::int32_t{7});
    Store(player, 0x70, std::int32_t{7});
    Store(data, kPlayerCharacterManagerOffset + 0x58, entries.data());
    Store(data, kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Store(entry, 0xD8, std::int32_t{7}); Store(entry, 0xB0, actor_id);
    Init(actor, actor_id); Init(actor_replacement, actor_id);
    Init(borrowed.bytes, context_id); Init(context_replacement, context_id);
    Init(alternate, kAlternateId); Init(fallback, -1);
    Store(storage, 0x20, slots.data()); Store(storage, 0x2C, std::int32_t{4});
    Place(actor_id, actor.data()); Place(context_id, borrowed.bytes.data());
    Place(kAlternateId, alternate.data());
    bindings = BindMonthlyFlowImageV1(0x140000000, kExecutableSha256);
    Require(bindings.exact_build_admitted && !bindings.integration_native_calls_permitted,
        "exact binding keeps integration gate closed");
    bindings.core = {true, &state_pointer, &jomini_pointer, &storage_pointer, &LocalPlayer};
    bindings.context = &Context; bindings.gross = &Gross; bindings.expenses = &Expenses;
    // Explicit fixture-only admission after replacing EVERY native callback.
    bindings.integration_native_calls_permitted = true;
  }
  template <class Buffer>
  void Init(Buffer &buffer, std::int32_t id) {
    Store(buffer, 0x18, id); Store(buffer, 0x1C, std::uint32_t{0x43686172});
  }
  void Place(std::int32_t id, void *object) {
    const auto index = static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
    Store(slots, index * 0x10 + 8, object);
  }
  void ResetCalls() {
    context_calls = gross_calls = expense_calls = core_calls = 0;
    gross_output = secondary_output = nullptr;
  }
  CoreSnapshotPrefix Expected() {
    CoreSnapshotPrefix prefix{};
    Require(ReadCoreSnapshot(bindings.core, prefix) && prefix.map_ready &&
        prefix.has_played_character && prefix.played_character_id == actor_id &&
        prefix.played_character_alive, "real Core fixture capture");
    ResetCalls();
    return prefix;
  }
};

void *LocalPlayer(void *) {
  auto &f = *active; ++f.core_calls;
  return f.map ? f.player.data() : nullptr;
}
void *Context(void *actor) {
  auto &f = *active; ++f.context_calls;
  Require(actor == f.actor.data(), "context gets real played actor");
  if (f.mode == Mode::throw_context ||
      (f.mode == Mode::throw_context_second && f.context_calls == 2)) Throw();
  if (f.mode == Mode::fault_context ||
      (f.mode == Mode::fault_context_second && f.context_calls == 2)) Fault();
  if (f.mode == Mode::null_context) return nullptr;
  if (f.mode == Mode::fallback_context) return f.fallback.data();
  if (f.mode == Mode::date_context) Store(f.state, 8, std::int32_t{123457});
  if (f.mode == Mode::different_context_second && f.context_calls == 2)
    return f.alternate.data();
  return f.context_result;
}
std::int64_t *Gross(std::int64_t *output, void *actor,
    std::int64_t *secondary, void *breakdown) {
  auto &f = *active; ++f.gross_calls;
  Require(actor == f.actor.data() && output != nullptr && secondary != nullptr &&
      output != secondary && breakdown == nullptr, "gross exact nullable-breakdown ABI");
  f.gross_output = output; f.secondary_output = secondary;
  *output = f.gross_value; *secondary = f.secondary_value;
  if (f.mode == Mode::throw_gross) Throw();
  if (f.mode == Mode::fault_gross) Fault();
  if (f.mode == Mode::date_gross) Store(f.state, 8, std::int32_t{123457});
  if (f.mode == Mode::paused_gross) f.jomini[0x20] = std::byte{};
  if (f.mode == Mode::actor_generation_gross)
    Store(f.actor, 0x18, std::bit_cast<std::int32_t>(std::uint32_t{0x82000001}));
  if (f.mode == Mode::actor_pointer_gross) f.Place(f.actor_id, f.actor_replacement.data());
  if (f.mode == Mode::actor_type_gross) Store(f.actor, 0x1C, std::uint32_t{0x4C616E64});
  if (f.mode == Mode::actor_death_gross) Store(f.actor, 0x1D0, f.actor.data());
  if (f.mode == Mode::actor_living_gross) Store(f.actor, 0x1B0, f.actor.data());
  if (f.mode == Mode::actor_owner_gross) Store(f.actor, 0x1C0, f.actor.data());
  if (f.mode == Mode::context_generation_gross)
    Store(f.borrowed.bytes, 0x18, std::bit_cast<std::int32_t>(std::uint32_t{0x83000002}));
  if (f.mode == Mode::context_pointer_gross)
    f.Place(f.context_id, f.context_replacement.data());
  return f.mode == Mode::wrong_gross_output ? &f.other_output : output;
}
std::int64_t *Expenses(std::int64_t *output, void *actor, void *context,
    std::int64_t secondary, bool exclude_military, void *breakdown) {
  auto &f = *active; ++f.expense_calls;
  Require(actor == f.actor.data() && context == f.context_result && output != nullptr &&
      output != f.gross_output && output != f.secondary_output &&
      secondary == f.secondary_value && !exclude_military && breakdown == nullptr,
      "expense uses borrowed context, exact secondary and third independent scalar slot");
  *output = f.expense_value;
  if (f.mode == Mode::throw_expenses) Throw();
  if (f.mode == Mode::fault_expenses) Fault();
  if (f.mode == Mode::date_expenses) Store(f.state, 8, std::int32_t{123457});
  if (f.mode == Mode::map_expenses) f.map = false;
  if (f.mode == Mode::context_type_expenses)
    Store(f.borrowed.bytes, 0x1C, std::uint32_t{0x4C616E64});
  if (f.mode == Mode::context_living_expenses)
    Store(f.borrowed.bytes, 0x1B0, f.borrowed.bytes.data());
  if (f.mode == Mode::context_owner_expenses)
    Store(f.borrowed.bytes, 0x1C0, f.borrowed.bytes.data());
  return f.mode == Mode::wrong_expenses_output ? &f.other_output : output;
}

void Scope(const MonthlyFlowObservationV1 &out) {
  Require(out.schema == kMonthlyFlowSchemaV1 && out.game_version == kGameVersion &&
      out.steam_build_id == kSteamBuildId && out.executable_sha256 == kExecutableSha256 &&
      out.executable_file_size == kExecutableFileSize && out.scale == 100000,
      "exact internal tuple and scale");
  Require(out.partial && !out.full_snapshot_available && !out.root_ready &&
      !out.formal_action_ready && !out.treasury_observed && !out.military_categories_observed &&
      !out.tax_categories_observed && !out.prosperity_observed &&
      !out.zero_native_side_effects_verified && !out.native_unwind_cleanup_verified,
      "internal scalar evidence cannot mint RootReady or unknown lifecycle closure");
}
void Attempts(const Fixture &f, const MonthlyFlowObservationV1 &out) {
  Require(out.context_call_attempts == f.context_calls &&
      out.gross_call_attempted == (f.gross_calls != 0) &&
      out.expenses_call_attempted == (f.expense_calls != 0), "actual attempted calls preserved");
}
void Failure(Fixture &f, const CoreSnapshotPrefix &expected, std::string_view reason) {
  MonthlyFlowObservationV1 out{};
  out.available = out.same_frame_ready = out.full_snapshot_available = out.root_ready = true;
  out.context_call_attempts = 99; out.gross_call_attempted = out.expenses_call_attempted = true;
  out.monthly_gross_income_raw = 11; out.monthly_total_expenses_raw = 22;
  out.monthly_net_income_raw = 33;
  Require(!ReadMonthlyFlowV1(f.bindings, expected, out) && !out.available &&
      !out.same_frame_ready && !out.gross_ready && !out.total_expenses_ready && !out.net_ready &&
      !out.monthly_gross_income_raw && !out.monthly_total_expenses_raw &&
      !out.monthly_net_income_raw && !out.context_full_id && out.actor_identity == 0 &&
      out.context_identity == 0 && out.unavailable_reason == reason,
      "failure clears every monetary value and stale readiness");
  Scope(out); Attempts(f, out);
}
MonthlyFlowObservationV1 Success(Fixture &f) {
  const auto expected = f.Expected(); const auto destroyed = context_destructions;
  MonthlyFlowObservationV1 out{};
  Require(ReadMonthlyFlowV1(f.bindings, expected, out) && out.available && out.same_frame_ready &&
      out.gross_ready && out.total_expenses_ready && out.context_full_id.has_value(),
      "observed aggregate with stable native inputs");
  Require(out.monthly_gross_income_raw == f.gross_value &&
      out.monthly_total_expenses_raw == f.expense_value && out.context_call_attempts == 2 &&
      f.gross_calls == 1 && f.expense_calls == 1 && context_destructions == destroyed,
      "borrowed context is not destroyed; scalars read once");
  Require(out.frame.played_character_id == f.actor_id && out.frame.clock.date_raw == 123456 &&
      out.frame.clock.speed == 5 && out.frame.clock.paused && out.frame.map_ready &&
      out.frame.local_player_id == 7 && out.frame.has_played_character &&
      out.frame.played_character_alive, "complete expected Core prefix retained");
  Scope(out); Attempts(f, out); return out;
}
struct NativeOwnerAdmissionTrace {
  unsigned calls = 0, deny_at = 0;
  bool fault_at_denial = false;
};
bool AdmitMonthlyTestOwner(void *opaque) noexcept {
  auto &trace = *static_cast<NativeOwnerAdmissionTrace *>(opaque);
  if (++trace.calls != trace.deny_at) return true;
#if defined(_MSC_VER)
  if (trace.fault_at_denial) RaiseException(EXCEPTION_ACCESS_VIOLATION, 0, 0, nullptr);
#endif
  return false;
}
} // namespace

int main() {
  using namespace xar::ck3_1210;
  constexpr auto minimum = (std::numeric_limits<std::int64_t>::min)();
  constexpr auto maximum = (std::numeric_limits<std::int64_t>::max)();
  const auto exact = BindMonthlyFlowImageV1(0x140000000, kExecutableSha256);
  Require(exact.exact_build_admitted && !exact.integration_native_calls_permitted &&
      reinterpret_cast<std::uintptr_t>(exact.context) == 0x140000000 + kMonthlyFlowContextRvaV1 &&
      reinterpret_cast<std::uintptr_t>(exact.gross) == 0x140000000 + kMonthlyFlowGrossRvaV1 &&
      reinterpret_cast<std::uintptr_t>(exact.expenses) == 0x140000000 + kMonthlyFlowExpensesRvaV1,
      "exact addresses only, default gate closed");
  {
    Fixture f; const auto expected = f.Expected(); f.bindings = exact;
    // These are intentionally nonloaded EXE addresses. The closed gate must
    // return before reading Core or invoking any native address.
    Failure(f, expected, "native_integration_gate_closed");
    Require(f.core_calls == 0 && f.context_calls == 0 && f.gross_calls == 0 && f.expense_calls == 0,
        "closed gate performs no calls");
  }
  const auto before_owner_destruction = context_destructions;
  {
    Fixture f; auto out = Success(f);
    Require(kActorId < 0 && kContextId < 0 && out.context_full_id == kContextId &&
        out.context_identity == reinterpret_cast<std::uintptr_t>(f.borrowed.bytes.data()) &&
        out.net_ready && out.monthly_net_income_raw == -220000, "negative full generations and NET");
    f.context_result = f.actor.data(); out = Success(f);
    Require(out.context_full_id == f.actor_id, "native context may borrow the actor itself");
    f.context_result = f.borrowed.bytes.data(); f.context_id = 0;
    Store(f.borrowed.bytes, 0x18, std::int32_t{0}); f.Place(0, f.borrowed.bytes.data());
    out = Success(f); Require(out.context_full_id == 0, "zero full context ID is not fallback");
    Store(f.borrowed.bytes, 0x1D0, f.borrowed.bytes.data());
    out = Success(f); Require(out.net_ready, "do not invent a context-alive source condition");
  }
  Require(context_destructions == before_owner_destruction + 1,
      "only fixture owner destroys borrowed context on its own scope exit");
  {
    Fixture f; f.actor_id = 0; Store(f.actor, 0x18, std::int32_t{0});
    Store(f.entry, 0xB0, std::int32_t{0}); f.Place(0, f.actor.data());
    Require(Success(f).net_ready, "canonical actor full ID zero");
  }
  struct ArithmeticCase { std::int64_t gross, total, net; bool valid; };
  const std::array cases{
      ArithmeticCase{0, 0, 0, true}, ArithmeticCase{-100, -20, -80, true},
      ArithmeticCase{minimum, 0, minimum, true}, ArithmeticCase{maximum, 0, maximum, true},
      ArithmeticCase{minimum, minimum, 0, true}, ArithmeticCase{maximum, maximum, 0, true},
      ArithmeticCase{-1, minimum, maximum, true}, ArithmeticCase{0, minimum, 0, false},
      ArithmeticCase{minimum, 1, 0, false}, ArithmeticCase{maximum, -1, 0, false}};
  for (const auto &item : cases) {
    std::int64_t net = 999;
    Require(CheckedMonthlyNetV1(item.gross, item.total, net) == item.valid &&
        net == item.net, "checked signed arithmetic endpoints");
    Fixture f; f.gross_value = item.gross; f.expense_value = item.total;
    const auto out = Success(f);
    Require(item.valid ? (out.net_ready && out.monthly_net_income_raw == item.net &&
        out.net_unavailable_reason.empty()) : (!out.net_ready && !out.monthly_net_income_raw &&
        out.net_unavailable_reason == "monthly_net_income_overflow" &&
        out.unavailable_reason == "monthly_flow_partial"), "overflow preserves only gross/total");
  }
  for (const auto mode : {Mode::null_context, Mode::fallback_context}) {
    Fixture f; const auto expected = f.Expected(); f.mode = mode;
    Failure(f, expected, "expense_context_identity_unavailable");
    Require(f.context_calls == 1 && f.gross_calls == 0 && f.expense_calls == 0,
        "unqualified context stops before financial getters");
  }
  {
    Fixture f; const auto expected = f.Expected();
    Store(f.context_replacement, 0x18,
        std::bit_cast<std::int32_t>(std::uint32_t{0x83000002}));
    f.Place(kContextId, f.context_replacement.data());
    Failure(f, expected, "expense_context_identity_unavailable");
  }
  {
    Fixture f; const auto expected = f.Expected();
    Store(f.borrowed.bytes, 0x1C, std::uint32_t{0x4C616E64});
    Failure(f, expected, "expense_context_identity_unavailable");
  }
  struct FailureCase { Mode mode; std::string_view reason; };
  const std::array failures{
      FailureCase{Mode::throw_context, "native_context_call_failed"},
      FailureCase{Mode::throw_gross, "native_gross_call_failed"},
      FailureCase{Mode::throw_expenses, "native_expenses_call_failed"},
      FailureCase{Mode::throw_context_second, "native_context_call_failed"},
      FailureCase{Mode::wrong_gross_output, "native_gross_output_mismatch"},
      FailureCase{Mode::wrong_expenses_output, "native_expenses_output_mismatch"},
      FailureCase{Mode::different_context_second, "expense_context_changed"},
      FailureCase{Mode::date_context, "core_frame_changed"},
      FailureCase{Mode::date_gross, "core_frame_changed"},
      FailureCase{Mode::date_expenses, "core_frame_changed"},
      FailureCase{Mode::paused_gross, "core_frame_changed"},
      FailureCase{Mode::map_expenses, "core_frame_changed"},
      FailureCase{Mode::actor_generation_gross, "core_frame_changed"},
      FailureCase{Mode::actor_pointer_gross, "player_identity_changed"},
      FailureCase{Mode::actor_type_gross, "player_identity_changed"},
      FailureCase{Mode::actor_death_gross, "core_frame_changed"},
      FailureCase{Mode::actor_living_gross, "player_identity_changed"},
      FailureCase{Mode::actor_owner_gross, "player_identity_changed"},
      FailureCase{Mode::context_generation_gross, "expense_context_identity_changed"},
      FailureCase{Mode::context_pointer_gross, "expense_context_identity_changed"},
      FailureCase{Mode::context_type_expenses, "expense_context_identity_changed"},
      FailureCase{Mode::context_living_expenses, "expense_context_identity_changed"},
      FailureCase{Mode::context_owner_expenses, "expense_context_identity_changed"}};
  for (const auto &item : failures) {
    Fixture f; const auto expected = f.Expected(); f.mode = item.mode;
    const auto unwound = cpp_unwinds;
    Failure(f, expected, item.reason);
    if (item.mode == Mode::throw_context || item.mode == Mode::throw_gross ||
        item.mode == Mode::throw_expenses || item.mode == Mode::throw_context_second)
      Require(cpp_unwinds == unwound + 1, "C++ exception unwinds through thin SEH layer");
    if (item.mode == Mode::date_context)
      Require(f.gross_calls == 0 && f.expense_calls == 0, "entry frame guard before gross");
    if (item.mode == Mode::date_gross || item.mode == Mode::context_pointer_gross ||
        item.mode == Mode::actor_pointer_gross || item.mode == Mode::wrong_gross_output)
      Require(f.expense_calls == 0, "entry identity/output guard before expense");
  }
  {
    Fixture f; const auto expected = f.Expected(); auto wrong = expected;
    wrong.clock.paused = false; Failure(f, wrong, "requires_paused");
    wrong = expected; wrong.map_ready = false; Failure(f, wrong, "map_not_ready");
    wrong = expected; wrong.has_played_character = false;
    Failure(f, wrong, "player_identity_unavailable");
    wrong = expected; wrong.played_character_id = -1;
    Failure(f, wrong, "player_identity_unavailable");
    wrong = expected; wrong.played_character_alive = false;
    Failure(f, wrong, "player_not_alive");
    wrong = expected; ++wrong.clock.date_raw; Failure(f, wrong, "core_frame_changed");
    wrong = expected; --wrong.clock.speed; Failure(f, wrong, "core_frame_changed");
    wrong = expected; ++wrong.local_player_id; Failure(f, wrong, "core_frame_changed");
    Require(f.context_calls == 0 && f.gross_calls == 0 && f.expense_calls == 0,
        "expected input rejection calls no finance entry");
    f.bindings.exact_build_admitted = false; Failure(f, expected, "unsupported_build");
    f.bindings.exact_build_admitted = true; f.bindings.gross = nullptr;
    Failure(f, expected, "monthly_flow_binding_unavailable");
  }
#if defined(_MSC_VER)
  for (const auto mode : {Mode::fault_context, Mode::fault_gross,
           Mode::fault_expenses, Mode::fault_context_second}) {
    Fixture f; const auto expected = f.Expected(); f.mode = mode;
    Failure(f, expected, mode == Mode::fault_gross ? "native_gross_call_failed" :
        mode == Mode::fault_expenses ? "native_expenses_call_failed" : "native_context_call_failed");
  }
  {
    Fixture f; const auto expected = f.Expected();
    f.context_result = reinterpret_cast<void *>(std::uintptr_t{1});
    Failure(f, expected, "expense_context_identity_unavailable");
  }
#endif
  Require(!BindMonthlyFlowImageV1(0, kExecutableSha256).exact_build_admitted,
      "null image rejected");
  Require(!BindMonthlyFlowImageV1(0x140000000,
      "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518")
      .exact_build_admitted, "old .4 identity rejected");
  Require(!BindMonthlyFlowImageV1((std::numeric_limits<std::uintptr_t>::max)(),
      kExecutableSha256).exact_build_admitted, "base overflow rejected");
  for (unsigned deny_at = 1; deny_at != 9; ++deny_at) {
    Fixture f; NativeOwnerAdmissionTrace trace{0, deny_at, false};
    f.bindings.native_call_admission = &AdmitMonthlyTestOwner;
    f.bindings.native_call_admission_context = &trace;
    MonthlyFlowObservationV1 observed{};
    Require(!ReadMonthlyFlowV1(f.bindings, f.Expected(), observed) &&
        observed.native_owner_admission_failed && !observed.available &&
        !observed.monthly_gross_income_raw && !observed.monthly_total_expenses_raw &&
        !observed.monthly_net_income_raw && trace.calls == deny_at &&
        observed.unavailable_reason == "monthly_flow_owner_changed",
        "every native monetary call brackets current owner and latches failed admission");
    const unsigned contexts = (deny_at >= 2 ? 1U : 0U) + (deny_at >= 8 ? 1U : 0U);
    Require(f.context_calls == contexts && f.gross_calls == (deny_at >= 4 ? 1U : 0U) &&
        f.expense_calls == (deny_at >= 6 ? 1U : 0U), "no later native getter after lost owner");
    Attempts(f, observed); Scope(observed);
  }
  {
    Fixture f; NativeOwnerAdmissionTrace trace{};
    f.bindings.native_call_admission = &AdmitMonthlyTestOwner;
    f.bindings.native_call_admission_context = &trace;
    const auto observed = Success(f);
    Require(trace.calls == 8 && !observed.native_owner_admission_failed,
        "current owner survives all four native calls without changing scalar semantics");
  }
#if defined(_MSC_VER)
  {
    Fixture f; NativeOwnerAdmissionTrace trace{0, 4, true};
    f.bindings.native_call_admission = &AdmitMonthlyTestOwner;
    f.bindings.native_call_admission_context = &trace;
    MonthlyFlowObservationV1 observed{};
    Require(!ReadMonthlyFlowV1(f.bindings, f.Expected(), observed) &&
        observed.native_owner_admission_failed && f.context_calls == 1 &&
        f.gross_calls == 1 && f.expense_calls == 0,
        "SEH during owner recheck retains completed native attempts and blocks expense");
    Attempts(f, observed);
  }
#endif
  std::cout << "PASS fake monthly ABI/borrowed lifetime/default gate/full generation/"
      "overflow/frame/throw/fault guards; no native Game entry executed\n";
  return 0;
}
