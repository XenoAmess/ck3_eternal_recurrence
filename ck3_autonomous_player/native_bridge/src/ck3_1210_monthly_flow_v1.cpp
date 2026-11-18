#include "xar_bridge/ck3_1210_monthly_flow_v1.hpp"

#include <cstring>
#include <limits>

#if defined(_MSC_VER)
#include <windows.h>
#endif

// FINANCE-MONTHLY-LIFECYCLE01.json, 53437 bytes, SHA256 a5e1d60d...
// New native HUD E01CD3..E01D27 and NET wrapper 30F1E10 prove the argument
// chain. Context 2DA46E0 borrows Character storage. No GUI row ownership is
// imported. Recursive callee effects and exceptional cleanup remain unknown.
namespace xar::ck3_1210 {
namespace {
constexpr std::size_t kType = 0x1C, kLiving = 0x1B0;
constexpr std::size_t kDependent = 0x1B8, kOwner = 0x1C0;

bool Copy(const void *source, void *target, std::size_t size) noexcept {
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(target, source, size);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}

template <class T>
bool Read(const void *base, std::size_t offset, T &output) noexcept {
  const auto address = reinterpret_cast<std::uintptr_t>(base);
  const auto maximum = (std::numeric_limits<std::uintptr_t>::max)();
  return address != 0 && offset <= maximum - address &&
      sizeof(T) - 1 <= maximum - (address + offset) &&
      Copy(reinterpret_cast<const void *>(address + offset), &output, sizeof(T));
}

bool Core(const CoreBindings &bindings, CoreSnapshotPrefix &output) noexcept {
#if defined(_MSC_VER)
  __try {
#endif
    return ReadCoreSnapshot(bindings, output);
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { output = {}; return false; }
#endif
}

void *Resolve(const CoreBindings &bindings, std::int32_t id) noexcept {
#if defined(_MSC_VER)
  __try {
#endif
    return ResolveCoreCharacter(bindings, id);
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return nullptr; }
#endif
}

// Thin SEH functions have no C++ objects needing unwinding. Let MSVC C++
// exceptions continue to the enclosing C++ catch; do not swallow their unwind.
bool AdmissionCall(MonthlyFlowNativeCallAdmissionV1 function, void *context) noexcept {
#if defined(_MSC_VER)
  __try {
#endif
    return function(context);
#if defined(_MSC_VER)
  } __except (GetExceptionCode() == 0xE06D7363UL ?
      EXCEPTION_CONTINUE_SEARCH : EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}

bool ContextSeh(MonthlyFlowContextV1 function, void *actor, void *&output) {
#if defined(_MSC_VER)
  __try {
#endif
    output = function(actor);
    return true;
#if defined(_MSC_VER)
  } __except (GetExceptionCode() == 0xE06D7363UL ?
      EXCEPTION_CONTINUE_SEARCH : EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}

bool GrossSeh(MonthlyFlowGrossV1 function, void *actor, std::int64_t &gross,
    std::int64_t &secondary, std::int64_t *&returned) {
#if defined(_MSC_VER)
  __try {
#endif
    returned = function(&gross, actor, &secondary, nullptr);
    return true;
#if defined(_MSC_VER)
  } __except (GetExceptionCode() == 0xE06D7363UL ?
      EXCEPTION_CONTINUE_SEARCH : EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}

bool ExpensesSeh(MonthlyFlowExpensesV1 function, void *actor, void *context,
    std::int64_t secondary, std::int64_t &total, std::int64_t *&returned) {
#if defined(_MSC_VER)
  __try {
#endif
    returned = function(&total, actor, context, secondary, false, nullptr);
    return true;
#if defined(_MSC_VER)
  } __except (GetExceptionCode() == 0xE06D7363UL ?
      EXCEPTION_CONTINUE_SEARCH : EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}

bool ContextCall(MonthlyFlowContextV1 function, void *actor, void *&output) noexcept {
  try { return ContextSeh(function, actor, output); } catch (...) { return false; }
}
bool GrossCall(MonthlyFlowGrossV1 function, void *actor, std::int64_t &gross,
    std::int64_t &secondary, std::int64_t *&returned) noexcept {
  try { return GrossSeh(function, actor, gross, secondary, returned); }
  catch (...) { return false; }
}
bool ExpensesCall(MonthlyFlowExpensesV1 function, void *actor, void *context,
    std::int64_t secondary, std::int64_t &total, std::int64_t *&returned) noexcept {
  try { return ExpensesSeh(function, actor, context, secondary, total, returned); }
  catch (...) { return false; }
}

struct Identity {
  std::int32_t id = -1;
  std::uint32_t type = 0;
  void *death = nullptr, *living = nullptr, *dependent = nullptr, *owner = nullptr;
  friend bool operator==(const Identity &, const Identity &) = default;
};

bool Capture(const CoreBindings &core, const void *pointer, Identity &identity) noexcept {
  return Read(pointer, kCharacterFullIdOffset, identity.id) && identity.id != -1 &&
      Read(pointer, kType, identity.type) && identity.type == 0x43686172U &&
      Resolve(core, identity.id) == pointer &&
      Read(pointer, kCharacterDeathDataOffset, identity.death) &&
      Read(pointer, kLiving, identity.living) &&
      Read(pointer, kDependent, identity.dependent) && Read(pointer, kOwner, identity.owner);
}

bool SamePrefix(const CoreSnapshotPrefix &a, const CoreSnapshotPrefix &b) noexcept {
  return a.clock.date_raw == b.clock.date_raw && a.clock.speed == b.clock.speed &&
      a.clock.paused == b.clock.paused && a.local_player_id == b.local_player_id &&
      a.map_ready == b.map_ready && a.has_played_character == b.has_played_character &&
      a.played_character_id == b.played_character_id &&
      a.played_character_alive == b.played_character_alive;
}

bool Fail(MonthlyFlowObservationV1 &output, std::string_view reason) noexcept {
  const auto context_calls = output.context_call_attempts;
  const bool gross_called = output.gross_call_attempted;
  const bool expenses_called = output.expenses_call_attempted;
  output = {};
  output.context_call_attempts = context_calls;
  output.gross_call_attempted = gross_called;
  output.expenses_call_attempted = expenses_called;
  output.unavailable_reason = reason;
  output.net_unavailable_reason = reason;
  return false;
}

bool OwnerAdmissionFailed(MonthlyFlowObservationV1 &output) noexcept {
  Fail(output, "monthly_flow_owner_changed");
  output.native_owner_admission_failed = true;
  return false;
}

std::string_view Guard(const CoreBindings &core, const CoreSnapshotPrefix &expected,
    const void *actor, const Identity &actor_identity, const void *context,
    const Identity &context_identity) noexcept {
  CoreSnapshotPrefix current{};
  if (!Core(core, current)) return "core_read_failed";
  if (!SamePrefix(current, expected)) return "core_frame_changed";
  Identity actor_now{}, context_now{};
  if (!Capture(core, actor, actor_now) || actor_now != actor_identity)
    return "player_identity_changed";
  if (!Capture(core, context, context_now) || context_now != context_identity)
    return "expense_context_identity_changed";
  return {};
}
} // namespace

MonthlyFlowBindingsV1 BindMonthlyFlowImageV1(std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept {
  MonthlyFlowBindingsV1 result{};
  if (image_base == 0 || executable_sha256 != kExecutableSha256 ||
      image_base > (std::numeric_limits<std::uintptr_t>::max)() -
          kJominiStateSlotRva - (sizeof(void *) - 1)) return result;
  result.core = BindCoreImage(image_base, executable_sha256);
  result.exact_build_admitted = result.core.enabled;
  result.context = reinterpret_cast<MonthlyFlowContextV1>(image_base + kMonthlyFlowContextRvaV1);
  result.gross = reinterpret_cast<MonthlyFlowGrossV1>(image_base + kMonthlyFlowGrossRvaV1);
  result.expenses = reinterpret_cast<MonthlyFlowExpensesV1>(image_base + kMonthlyFlowExpensesRvaV1);
  return result;
}

bool CheckedMonthlyNetV1(std::int64_t gross, std::int64_t total_expenses,
    std::int64_t &net) noexcept {
  net = 0;
  constexpr auto minimum = (std::numeric_limits<std::int64_t>::min)();
  constexpr auto maximum = (std::numeric_limits<std::int64_t>::max)();
  if ((total_expenses > 0 && gross < minimum + total_expenses) ||
      (total_expenses < 0 && gross > maximum + total_expenses)) return false;
  net = gross - total_expenses;
  return true;
}

bool ReadMonthlyFlowV1(const MonthlyFlowBindingsV1 &bindings,
    const CoreSnapshotPrefix &expected, MonthlyFlowObservationV1 &output) noexcept {
  output = {};
  if (!bindings.exact_build_admitted || !bindings.core.enabled)
    return Fail(output, "unsupported_build");
  if (!bindings.integration_native_calls_permitted)
    return Fail(output, "native_integration_gate_closed");
  const auto &core = bindings.core;
  if (core.game_state_slot == nullptr || core.jomini_state_slot == nullptr ||
      core.character_storage_slot == nullptr || core.get_local_player == nullptr ||
      bindings.context == nullptr || bindings.gross == nullptr || bindings.expenses == nullptr)
    return Fail(output, "monthly_flow_binding_unavailable");
  const auto admission = bindings.native_call_admission;
  void *const admission_context = bindings.native_call_admission_context;
  const auto admitted = [&]() noexcept {
    if (bindings.native_call_admission != admission ||
        bindings.native_call_admission_context != admission_context) return false;
    const bool accepted = admission == nullptr || AdmissionCall(admission, admission_context);
    return accepted && bindings.native_call_admission == admission &&
        bindings.native_call_admission_context == admission_context;
  };
  if (!expected.clock.paused) return Fail(output, "requires_paused");
  if (!expected.map_ready) return Fail(output, "map_not_ready");
  if (expected.local_player_id < 0 || !expected.has_played_character ||
      expected.played_character_id == -1)
    return Fail(output, "player_identity_unavailable");
  if (!expected.played_character_alive) return Fail(output, "player_not_alive");
  CoreSnapshotPrefix before{};
  if (!Core(core, before)) return Fail(output, "core_read_failed");
  if (!SamePrefix(before, expected)) return Fail(output, "core_frame_changed");
  void *actor = Resolve(core, expected.played_character_id);
  Identity actor_identity{}, context_identity{};
  if (!Capture(core, actor, actor_identity) || actor_identity.id != expected.played_character_id ||
      actor_identity.death != nullptr) return Fail(output, "player_identity_unavailable");
  void *context = nullptr;
  if (!admitted()) return OwnerAdmissionFailed(output);
  ++output.context_call_attempts;
  const bool context_read = ContextCall(bindings.context, actor, context);
  if (!admitted()) return OwnerAdmissionFailed(output);
  if (!context_read) return Fail(output, "native_context_call_failed");
  if (!Capture(core, context, context_identity))
    return Fail(output, "expense_context_identity_unavailable");
  auto reason = Guard(core, expected, actor, actor_identity, context, context_identity);
  if (!reason.empty()) return Fail(output, reason);

  // Exactly three native scalar slots. No constructed context/row/GUI object.
  std::int64_t gross = 0, secondary = 0, total = 0;
  std::int64_t *returned = nullptr;
  if (!admitted()) return OwnerAdmissionFailed(output);
  output.gross_call_attempted = true;
  const bool gross_read = GrossCall(bindings.gross, actor, gross, secondary, returned);
  if (!admitted()) return OwnerAdmissionFailed(output);
  if (!gross_read) return Fail(output, "native_gross_call_failed");
  if (returned != &gross) return Fail(output, "native_gross_output_mismatch");
  reason = Guard(core, expected, actor, actor_identity, context, context_identity);
  if (!reason.empty()) return Fail(output, reason);
  if (!admitted()) return OwnerAdmissionFailed(output);
  output.expenses_call_attempted = true;
  const bool expenses_read = ExpensesCall(bindings.expenses, actor, context, secondary, total, returned);
  if (!admitted()) return OwnerAdmissionFailed(output);
  if (!expenses_read) return Fail(output, "native_expenses_call_failed");
  if (returned != &total) return Fail(output, "native_expenses_output_mismatch");
  reason = Guard(core, expected, actor, actor_identity, context, context_identity);
  if (!reason.empty()) return Fail(output, reason);
  void *confirmed_context = nullptr;
  if (!admitted()) return OwnerAdmissionFailed(output);
  ++output.context_call_attempts;
  const bool confirmed_read = ContextCall(bindings.context, actor, confirmed_context);
  if (!admitted()) return OwnerAdmissionFailed(output);
  if (!confirmed_read) return Fail(output, "native_context_call_failed");
  if (confirmed_context != context) return Fail(output, "expense_context_changed");
  reason = Guard(core, expected, actor, actor_identity, context, context_identity);
  if (!reason.empty()) return Fail(output, reason);

  output.frame = expected;
  output.actor_identity = reinterpret_cast<std::uintptr_t>(actor);
  output.context_identity = reinterpret_cast<std::uintptr_t>(context);
  output.context_full_id = context_identity.id;
  output.available = output.same_frame_ready = true;
  output.monthly_gross_income_raw = gross;
  output.monthly_total_expenses_raw = total;
  output.gross_ready = output.total_expenses_ready = true;
  // Native no longer uses secondary; reuse that same scalar for checked NET.
  if (CheckedMonthlyNetV1(gross, total, secondary)) {
    output.monthly_net_income_raw = secondary;
    output.net_ready = true;
    output.net_unavailable_reason = output.unavailable_reason = {};
  } else {
    output.net_unavailable_reason = "monthly_net_income_overflow";
    output.unavailable_reason = "monthly_flow_partial";
  }
  return true;
}

} // namespace xar::ck3_1210
