#include "xar_bridge/ck3_12003_war_cash_current_serializer.hpp"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
namespace cash = xar::ck3_12003::war_cash_current;
enum class Fault { none, context_null, income_return, expense_return,
                   context_actor_changed, income_actor_changed,
                   expense_actor_changed, current_actor_changed };
struct State {
  std::array<std::byte, 0x200> actor{};
  std::array<std::byte, 0x200> living{};
  std::array<std::byte, 8> context{};
  std::int64_t gross = 500000;
  std::int64_t expenses = 720000;
  std::int64_t secondary = 123456;
  std::array<std::int64_t, 10> current{300000, 11, 12, 13, 14, 15, 60000, 17, 18, 19};
  std::array<std::int64_t, 10> all{900000, 21, 22, 23, 24, 25, 160000, 27, 28, 29};
  std::vector<std::string> calls;
  Fault fault = Fault::none;
  bool arguments_ok = true;
} state;

void Require(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}
template <typename T> void Put(std::size_t offset, const T &value) {
  std::memcpy(state.actor.data() + offset, &value, sizeof(value));
}
void Reset() {
  state = {};
  Put(0x18, std::int32_t{33388});
  Put(0x1C, std::uint32_t{0x43686172});
  Put(0x1B0, static_cast<void *>(state.living.data()));
  const std::int64_t gold = -123456;
  std::memcpy(state.living.data() + 0x100, &gold, sizeof(gold));
}
void *Context(void *actor) {
  state.calls.push_back("context");
  state.arguments_ok &= actor == state.actor.data();
  if (state.fault == Fault::context_actor_changed) Put(0x18, std::int32_t{33389});
  return state.fault == Fault::context_null ? nullptr : state.context.data();
}
std::int64_t *Income(std::int64_t *out, void *actor,
                     std::int64_t *secondary, void *breakdown) {
  state.calls.push_back("income");
  state.arguments_ok &= out != nullptr && actor == state.actor.data() &&
                        secondary != nullptr && breakdown == nullptr;
  if (secondary == nullptr) return nullptr;
  *secondary = state.secondary;
  *out = state.gross;
  if (state.fault == Fault::income_actor_changed) Put(0x18, std::int32_t{33389});
  return state.fault == Fault::income_return ? nullptr : out;
}
std::int64_t *Expenses(std::int64_t *out, void *actor, void *context,
                       std::int64_t secondary, bool exclude_military,
                       void *breakdown) {
  state.calls.push_back("expenses");
  state.arguments_ok &= out != nullptr && actor == state.actor.data() &&
                        context == state.context.data() && context != actor &&
                        secondary == state.secondary && !exclude_military &&
                        breakdown == nullptr;
  *out = state.expenses;
  if (state.fault == Fault::expense_actor_changed) Put(0x18, std::int32_t{33389});
  return state.fault == Fault::expense_return ? nullptr : out;
}
std::int64_t *Current(std::int64_t *out, void *actor, void *breakdown) {
  state.calls.push_back("current");
  state.arguments_ok &= actor == state.actor.data() && breakdown == nullptr;
  std::copy(state.current.begin(), state.current.end(), out);
  if (state.fault == Fault::current_actor_changed) Put(0x18, std::int32_t{33389});
  return out;
}
std::int64_t *All(std::int64_t *out, void *actor) {
  state.calls.push_back("all");
  state.arguments_ok &= actor == state.actor.data();
  std::copy(state.all.begin(), state.all.end(), out);
  return out;
}
cash::Bindings Bindings() {
  cash::Bindings b{};
  b.enabled = true;
  b.monthly_income = &Income;
  b.expense_context_character = &Context;
  b.monthly_total_expenses = &Expenses;
  b.current_maintenance = &Current;
  b.all_raised_maintenance = &All;
  return b;
}
cash::ActorResources Read(const cash::Bindings &b = Bindings()) {
  cash::ActorResources out{};
  (void)cash::ReadActor(b, state.actor.data(), 33388, out);
  Require(state.arguments_ok, "native argument/caller buffer contract changed");
  return out;
}
void Emit(const std::filesystem::path &dir, const char *name,
          const cash::ActorResources &out) {
  xar::game::Snapshot frame{};
  frame.played_character_id = 33388;
  frame.date_raw = 53147160;
  frame.paused = true;
  frame.map_ready = true;
  frame.has_played_character = true;
  frame.played_character_alive = true;
  xar::game::ArmySnapshot army{};
  army.army_id = 0;
  frame.player_armies.push_back(army);
  xar::game::ActiveWarSnapshot war{};
  war.war_id = 1;
  frame.active_wars.push_back(war);
  const auto wire = cash::SerializeCurrentResourcesV1(out, frame, 2, true);
  Require(wire.find("native-income-minus-total-expenses-v2") != std::string::npos,
          "new semantics marker missing from actual serializer");
  const auto path = dir / (std::string(name) + ".json");
  Require(!std::filesystem::exists(path), "preserve old attempt: output already exists");
  std::ofstream stream(path, std::ios::binary);
  Require(static_cast<bool>(stream), "cannot create actual wire output");
  stream << wire << '\n';
  Require(static_cast<bool>(stream), "cannot write actual wire output");
}
void Normal(const std::filesystem::path &dir) {
  Reset();
  const auto out = Read();
  Require(out.monthly_gross_income_raw == 500000 &&
          out.monthly_total_expenses_raw == 720000 && out.monthly_net_income_raw == -220000,
          "NET must use complete expenses, not gross or military-only subtotal");
  Require(out.current_treasury_raw == -123456 && out.current.resources_raw == state.current &&
          out.all_raised.resources_raw == state.all, "other signed/vector observations changed");
  Require(state.calls == std::vector<std::string>{"context", "income", "expenses", "current", "all"},
          "same actor native producer sequence changed");
  Emit(dir, "negative-net", out);
  Reset(); state.gross = state.expenses = 0;
  const auto zero = Read();
  Require(zero.monthly_gross_income_raw == 0 && zero.monthly_total_expenses_raw == 0 &&
          zero.monthly_net_income_raw == 0, "legitimate zero must remain available");
  Emit(dir, "zero-net", zero);
  Reset(); state.gross = -500000; state.expenses = -200000;
  Require(Read().monthly_net_income_raw == -300000, "signed subtraction changed");
}
void Failures(const std::filesystem::path &dir) {
  Reset(); state.fault = Fault::context_null;
  auto out = Read();
  Require(!out.monthly_gross_income_raw && !out.monthly_total_expenses_raw &&
          !out.monthly_net_income_raw, "missing context fabricated NET");
  Require(std::find(state.calls.begin(), state.calls.end(), "income") == state.calls.end(),
          "income invoked with missing expense context");
  Emit(dir, "context-unavailable", out);
  Reset(); state.fault = Fault::income_return; out = Read();
  Require(!out.monthly_gross_income_raw && !out.monthly_total_expenses_raw &&
          !out.monthly_net_income_raw, "invalid income return pointer trusted");
  Emit(dir, "income-unavailable", out);
  Reset(); state.fault = Fault::expense_return; out = Read();
  Require(out.monthly_gross_income_raw == 500000 && !out.monthly_total_expenses_raw &&
          !out.monthly_net_income_raw, "failed complete expenses replaced by a military-only NET");
  Emit(dir, "expenses-unavailable", out);
  Reset(); auto missing = Bindings(); missing.monthly_total_expenses = nullptr; out = Read(missing);
  Require(!out.monthly_net_income_raw && state.calls == std::vector<std::string>{"current", "all"},
          "missing bound function still yielded NET");
  for (const auto fault : {Fault::context_actor_changed, Fault::income_actor_changed,
                          Fault::expense_actor_changed, Fault::current_actor_changed}) {
    Reset(); state.fault = fault; out = Read();
    Require(!out.current_treasury_raw && !out.monthly_gross_income_raw &&
            !out.monthly_total_expenses_raw && !out.monthly_net_income_raw &&
            !out.current.available && !out.all_raised.available,
            "identity drift published any actor-bound observation");
  }
  Reset(); Put(0x1C, std::uint32_t{0}); out = Read();
  Require(state.calls.empty() && !out.monthly_net_income_raw, "wrong native type invoked getters");
  Reset(); Put(0x1D0, static_cast<void *>(state.context.data())); out = Read();
  Require(state.calls.empty() && !out.monthly_net_income_raw, "dead actor invoked getters");
}
void Overflow(const std::filesystem::path &dir) {
  Reset(); state.gross = std::numeric_limits<std::int64_t>::min(); state.expenses = 1;
  auto out = Read();
  Require(!out.monthly_net_income_raw && out.monthly_gross_income_raw && out.monthly_total_expenses_raw &&
          out.income_unavailable_reason == "war_cash_monthly_net_income_overflow", "negative overflow not unknown");
  Emit(dir, "overflow-net", out);
  Reset(); state.gross = std::numeric_limits<std::int64_t>::max(); state.expenses = -1;
  Require(!Read().monthly_net_income_raw, "positive overflow not unknown");
  Reset(); state.gross = std::numeric_limits<std::int64_t>::min(); state.expenses = 0;
  Require(Read().monthly_net_income_raw == state.gross, "valid signed minimum lost");
  Reset(); state.gross = std::numeric_limits<std::int64_t>::max(); state.expenses = 0;
  Require(Read().monthly_net_income_raw == state.gross, "valid signed maximum lost");
}
void ExactBinding() {
  constexpr std::uintptr_t base = 0x140000000ULL;
  const auto good = cash::BindImage(base, "1.20.0.3", xar::ck3_12003::kExecutableSha256);
  Require(good.enabled && reinterpret_cast<std::uintptr_t>(good.monthly_income) == base + 0x2BCA960 &&
          reinterpret_cast<std::uintptr_t>(good.expense_context_character) == base + 0x28BFDA0 &&
          reinterpret_cast<std::uintptr_t>(good.monthly_total_expenses) == base + 0x2BCB180,
          "exact3 source binding changed");
  Require(!cash::BindImage(base, "1.20.0.2", xar::ck3_12003::kExecutableSha256).enabled &&
          !cash::BindImage(base, "1.20.0.3", "wrong sha").enabled &&
          !cash::BindImage(0, "1.20.0.3", xar::ck3_12003::kExecutableSha256).enabled,
          "unverified image admitted");
}
} // namespace

int main(int argc, char **argv) {
  try {
    Require(argc == 2, "supply a fresh external wire output directory");
    const std::filesystem::path dir = argv[1];
    std::filesystem::create_directories(dir);
    ExactBinding(); Normal(dir); Failures(dir); Overflow(dir);
    std::cout << "PASS exact3 production reader/serializer: complete expenses, signed/zero, ABI args, caller pointers, unavailable, actor drift, overflow; no CK3 calls\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
