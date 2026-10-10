#include "xar_bridge/campaign_root_state_changed_diagnostics_12004.hpp"
#include <iostream>
#include <stdexcept>

namespace {
using namespace xar::ck3_12004;
using Frame = xar::game::CampaignRootFrameV1;
using Diagnostic = std::optional<CampaignRootStateChangedDiagnostic12004>;

void Require(bool condition, const char *reason) {
  if (!condition) throw std::runtime_error(reason);
}
bool Contains(const std::string &text, const char *value) {
  return text.find(value) != std::string::npos;
}
Frame SyntheticFrame() {
  // Reachable typed inputs, never a claim about the missing R92 native copies.
  return Frame{2U, 123, true, true, true, true, 17};
}
struct Capture {
  Frame supplied = SyntheticFrame();
  bool completed = true;
  int calls = 0;
  bool operator()(Frame &output) {
    ++calls; output = supplied; return completed;
  }
};

void CaptureBeforeFailure() {
  Capture capture{}; capture.completed = false;
  capture.supplied.snapshot_revision = 99U;
  Frame before{}; Diagnostic detail{};
  Require(!CaptureCampaignRootBefore12004(capture, 2U, before, &detail), "before failure preserved");
  Require(capture.calls == 1 && detail && detail->failed_conjunct == "capture_before_failed", "before single call and cause");
  Require(before.snapshot_revision == 99U && detail->before.snapshot_revision == 99U && !detail->before_capture_completed && !detail->after_capture_attempted, "partial copy retained without completed credit");
  const auto wire = SerializeCampaignRootStateChangedDiagnostic12004(*detail);
  Require(Contains(wire, "\"before\":null") && Contains(wire, "\"after\":null") && Contains(wire, "\"frame_diff_mask\":null") && Contains(wire, "\"observation_diff_mask\":null"), "failed capture wire unknowns");
}

void ExpectedRevisionFailure() {
  Capture capture{}; capture.supplied.snapshot_revision = 3U;
  Frame before{}; Diagnostic detail{};
  Require(CaptureCampaignRootBefore12004(capture, 2U, before, &detail), "before captured once");
  Require(!MatchCampaignRootExpectedRevision12004(2U, before, &detail), "revision mismatch preserved");
  Require(capture.calls == 1 && detail && detail->failed_conjunct == "expected_revision_mismatch" && detail->expected_revision == 2U && detail->before.snapshot_revision == 3U && !detail->after_capture_attempted, "actual input revisions forwarded, no second capture");
  const auto wire = SerializeCampaignRootStateChangedDiagnostic12004(*detail);
  Require(Contains(wire, "\"expected_revision\":2") && Contains(wire, "\"snapshot_revision\":3") && Contains(wire, "\"after\":null"), "revision diagnostic serializer");
}

void CaptureAfterFailure() {
  Capture capture{}; capture.completed = false;
  Frame after{}; Diagnostic detail{}; int comparisons = 0; int differences = 0;
  Require(!CaptureStableCampaignRootAfter12004(capture,
      [&] { ++comparisons; return true; }, [&] { ++differences; return 1U; },
      2U, SyntheticFrame(), after, &detail), "after failure preserved");
  Require(capture.calls == 1 && comparisons == 0 && differences == 0 && detail && detail->failed_conjunct == "capture_after_failed", "after capture short circuit");
  const auto wire = SerializeCampaignRootStateChangedDiagnostic12004(*detail);
  Require(Contains(wire, "\"before\":{") && Contains(wire, "\"after\":null") && Contains(wire, "\"observation_compared\":false"), "after failure exposes only completed before");
}

void FrameDifferenceFailure() {
  Capture capture{}; capture.supplied.date_raw = 124;
  Frame after{}; Diagnostic detail{}; int comparisons = 0; int differences = 0;
  Require(!CaptureStableCampaignRootAfter12004(capture,
      [&] { ++comparisons; return true; }, [&] { ++differences; return 1U; },
      2U, SyntheticFrame(), after, &detail), "frame difference preserved");
  Require(capture.calls == 1 && comparisons == 0 && differences == 0 && detail && detail->failed_conjunct == "after_frame_changed" && detail->frame_diff_mask == (1U << 1U), "owned frame difference and original short circuit");
  const auto wire = SerializeCampaignRootStateChangedDiagnostic12004(*detail);
  Require(Contains(wire, "\"date_raw\":123") && Contains(wire, "\"date_raw\":124") && Contains(wire, "\"frame_diff_fields\":[\"date_raw\"]") && Contains(wire, "\"observation_diff_fields\":null"), "frame diff copied values and bounded labels");
}

void ObservationDifferenceFailure() {
  Capture capture{}; Frame after{}; Diagnostic detail{};
  int comparisons = 0; int differences = 0;
  Require(!CaptureStableCampaignRootAfter12004(capture,
      [&] { ++comparisons; return true; }, [&] { ++differences; return 1U << 3U; },
      2U, SyntheticFrame(), after, &detail), "observation difference preserved");
  Require(capture.calls == 1 && comparisons == 1 && differences == 1 && detail && detail->failed_conjunct == "observation_changed" && detail->observation_compared && detail->observation_diff_mask == (1U << 3U), "owned observation diff callback only on actual failure");
  const auto wire = SerializeCampaignRootStateChangedDiagnostic12004(*detail);
  Require(Contains(wire, "\"frame_diff_fields\":[]") && Contains(wire, "\"observation_diff_fields\":[\"metrics\"]"), "observation group label has no memory dump");
  std::cout << wire << '\n';
}

void StableFrameAndAbsentDiagnostic() {
  Capture capture{}; Frame before{}, after{}; Diagnostic detail{};
  int comparisons = 0; int differences = 0;
  Require(CaptureCampaignRootBefore12004(capture, 2U, before, &detail) && MatchCampaignRootExpectedRevision12004(2U, before, &detail), "normal first two guards preserved");
  Require(CaptureStableCampaignRootAfter12004(capture,
      [&] { ++comparisons; return false; }, [&] { ++differences; return 1U; },
      2U, before, after, &detail), "original stable acceptance preserved");
  Require(capture.calls == 2 && comparisons == 1 && differences == 0 && !detail, "two original captures, no failure record on success");
  Require(!CaptureStableCampaignRootAfter12004(capture,
      [&] { ++comparisons; return true; }, [&] { ++differences; return 1U; },
      2U, before, after, nullptr), "null optional diagnostic does not relax failure");
  Require(capture.calls == 3 && comparisons == 2 && differences == 0, "absent diagnostic avoids extra owned comparisons");
}
}

int main() {
  try {
    CaptureBeforeFailure(); ExpectedRevisionFailure(); CaptureAfterFailure();
    FrameDifferenceFailure(); ObservationDifferenceFailure(); StableFrameAndAbsentDiagnostic();
    std::cout << "PASS: 6 new production diagnostic guard/serializer cases; original order and captures; no R92 cause or Game credit\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n'; return 1;
  }
}
