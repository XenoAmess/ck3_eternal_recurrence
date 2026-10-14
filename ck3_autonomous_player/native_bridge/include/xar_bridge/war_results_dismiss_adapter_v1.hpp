#pragma once

#include <cstdint>
#include <windows.h>

namespace xar::ck3_11906 {

// Only the fixed WarResultsWindow.Dismiss button uses this adapter. The caller
// has already admitted its current owner, exact build, widget and callback.
enum class WarResultsDismissStageV1 : std::uint8_t {
  not_attempted, preflight_rejected, callback_entered, callback_returned,
  callback_exception,
};

struct WarResultsDismissTraceV1 {
  WarResultsDismissStageV1 stage = WarResultsDismissStageV1::not_attempted;
  std::uint32_t exception_code = 0;
};

// CK3 1.20.0.4's GUI callback dispatcher invokes slot 2 with the address of
// its widget pointer. Calling only that bound callback avoids touching a
// widget again after Dismiss may destroy it. No replay is attempted on SEH.
inline bool InvokeWarResultsDismissCallbackV1(
    void *callback_object, void *callback_slot2, void *button,
    WarResultsDismissTraceV1 &trace) noexcept {
  trace.stage = WarResultsDismissStageV1::preflight_rejected;
  trace.exception_code = 0;
  if (!callback_object || !callback_slot2 || !button) return false;
  using Callback = void(__fastcall *)(void *, void **);
  auto function = reinterpret_cast<Callback>(callback_slot2);
  void *widget = button;
#if defined(_MSC_VER)
  __try {
    trace.stage = WarResultsDismissStageV1::callback_entered;
    function(callback_object, &widget);
    trace.stage = WarResultsDismissStageV1::callback_returned;
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    trace.exception_code = static_cast<std::uint32_t>(GetExceptionCode());
    trace.stage = WarResultsDismissStageV1::callback_exception;
    return false;
  }
#else
  trace.stage = WarResultsDismissStageV1::callback_entered;
  function(callback_object, &widget);
  trace.stage = WarResultsDismissStageV1::callback_returned;
  return true;
#endif
}

inline constexpr const char *WarResultsDismissStageNameV1(
    WarResultsDismissStageV1 stage) noexcept {
  switch (stage) {
    case WarResultsDismissStageV1::not_attempted: return "not_attempted";
    case WarResultsDismissStageV1::preflight_rejected: return "preflight_rejected";
    case WarResultsDismissStageV1::callback_entered: return "callback_entered";
    case WarResultsDismissStageV1::callback_returned: return "callback_returned";
    case WarResultsDismissStageV1::callback_exception: return "callback_exception";
  }
  return "invalid";
}

} // namespace xar::ck3_11906
