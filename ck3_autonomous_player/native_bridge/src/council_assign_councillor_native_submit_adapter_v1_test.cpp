#include "xar_bridge/council_assign_councillor_action_v1.hpp"

#include <iostream>
#include <stdexcept>

namespace {

struct Capture {
  int calls = 0;
  std::int32_t candidate = -1;
  std::int32_t task = -1;
};

void Helper(void *context, std::int32_t candidate,
            std::int32_t task) noexcept {
  auto &capture = *static_cast<Capture *>(context);
  ++capture.calls;
  capture.candidate = candidate;
  capture.task = task;
}

void Require(bool value) {
  if (!value) throw std::runtime_error("native submit adapter fixture failed");
}

xar::ck3_11906::CouncilAssignCouncillorNativeSubmitAdapterV1 Adapter(
    Capture &capture) {
  xar::ck3_11906::CouncilAssignCouncillorNativeSubmitAdapterV1 adapter{};
  adapter.environment.exact_build_admitted = true;
  adapter.environment.admitted_executable_sha256 =
      xar::ck3_11906::kCouncilAssignCouncillorExecutableSha256V1;
  adapter.environment.native_command_abi_certified = true;
  adapter.environment.private_candidate_admitted = true;
  adapter.environment.offline_fixture = true;
  adapter.environment.current_thread_id = 44;
  adapter.environment.application_main_thread_id = 44;
  adapter.override_context = &capture;
  adapter.helper_override = Helper;
  return adapter;
}

xar::game::CouncilAssignCouncillorNativeSubmissionV1 Submission() {
  return {
      xar::game::CouncilAssignCouncillorRouteV1::replace_incumbent,
      0x01007485,
      0x02001BF7,
      0x01005678,
      true,
      0x01001234,
  };
}

} // namespace

int main() {
  try {
    Capture capture;
    auto adapter = Adapter(capture);
    auto submission = Submission();
    Require(xar::ck3_11906::
                InvokeCouncilAssignCouncillorNativeSubmitAdapterV1(
                    &adapter, submission));
    Require(capture.calls == 1 && adapter.invocation_count == 1);
    Require(capture.candidate == submission.candidate_character_id);
    Require(capture.task == submission.active_task_id);

    auto wrong_build = Adapter(capture);
    wrong_build.environment.admitted_executable_sha256 = "wrong";
    Require(!xar::ck3_11906::
                 InvokeCouncilAssignCouncillorNativeSubmitAdapterV1(
                     &wrong_build, submission));
    Require(capture.calls == 1 && wrong_build.invocation_count == 0);

    auto invalid = submission;
    invalid.route = xar::game::CouncilAssignCouncillorRouteV1::assign_vacant;
    Require(!xar::ck3_11906::
                 InvokeCouncilAssignCouncillorNativeSubmitAdapterV1(
                     &adapter, invalid));
    Require(capture.calls == 1);

    auto public_path = Adapter(capture);
    public_path.environment.private_candidate_admitted = false;
    Require(!xar::ck3_11906::
                 InvokeCouncilAssignCouncillorNativeSubmitAdapterV1(
                     &public_path, submission));
    Require(capture.calls == 1);
    std::cout << "council_assign_councillor_native_submit_adapter_v1_test: GREEN\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
