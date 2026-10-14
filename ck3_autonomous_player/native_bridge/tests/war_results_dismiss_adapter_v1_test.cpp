#include "xar_bridge/war_results_dismiss_adapter_v1.hpp"
#include <cstdint>

using namespace xar::ck3_11906;

struct Probe {
  int calls = 0;
  void *widget = nullptr;
};

void __fastcall DismissProbe(void *opaque, void **widget) {
  auto *probe = static_cast<Probe *>(opaque);
  ++probe->calls;
  probe->widget = *widget;
  *widget = nullptr; // a Dismiss callback may invalidate its widget
}

void __fastcall ExceptionProbe(void *, void **) {
  RaiseException(0xE0421501, 0, 0, nullptr);
}

extern "C" __declspec(dllexport) int RunAdapterTest() {
  Probe probe{};
  int button = 1;
  WarResultsDismissTraceV1 trace{};
  if (InvokeWarResultsDismissCallbackV1(nullptr,
      reinterpret_cast<void *>(&DismissProbe),&button,trace) ||
      trace.stage != WarResultsDismissStageV1::preflight_rejected || probe.calls) return 1;
  if (!InvokeWarResultsDismissCallbackV1(&probe,
      reinterpret_cast<void *>(&DismissProbe),&button,trace) ||
      trace.stage != WarResultsDismissStageV1::callback_returned ||
      trace.exception_code || probe.calls != 1 || probe.widget != &button) return 2;
  if (InvokeWarResultsDismissCallbackV1(&probe,
      reinterpret_cast<void *>(&ExceptionProbe),&button,trace) ||
      trace.stage != WarResultsDismissStageV1::callback_exception ||
      trace.exception_code != 0xE0421501 || probe.calls != 1) return 3;
  return 0;
}
