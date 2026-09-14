#include "xar_bridge/steward_develop_county_action_v1.hpp"

#include <fstream>
#include <iostream>
#include <iterator>
#include <string>
#include <string_view>

namespace {

std::string ReadAll(const char *path) {
  std::ifstream input(path, std::ios::binary);
  return {std::istreambuf_iterator<char>(input),
          std::istreambuf_iterator<char>()};
}

bool Contains(std::string_view value, std::string_view token) {
  return value.find(token) != std::string_view::npos;
}

bool ContainsAll(std::string_view value,
                 std::initializer_list<std::string_view> tokens) {
  for (const auto token : tokens) {
    if (!Contains(value, token)) {
      std::cerr << "missing source-contract token: " << token << '\n';
      return false;
    }
  }
  return true;
}

} // namespace

int main(int argc, char **argv) {
  if (argc != 7) {
    std::cerr << "expected six source-contract paths\n";
    return 1;
  }
  const auto header = ReadAll(argv[1]);
  const auto action = ReadAll(argv[2]);
  const auto game_adapter = ReadAll(argv[3]);
  const auto adapter = ReadAll(argv[4]);
  const auto bridge = ReadAll(argv[5]);
  const auto abi = ReadAll(argv[6]);
  if (header.empty() || action.empty() || game_adapter.empty() ||
      adapter.empty() || bridge.empty() || abi.empty()) {
    std::cerr << "source-contract input is unreadable\n";
    return 1;
  }

  using namespace xar::ck3_11906;
  if (kStewardDevelopCountyActionV1Capability !=
          "game.command.change-steward-develop-county-task-v1" ||
      kStewardDevelopCountyActionV1Step !=
          "change-steward-develop-county-task-v1" ||
      kStewardDevelopCountyActionV1TaskKey != "task_develop_county" ||
      kStewardDevelopCountyActionV1ExecutableSha256 !=
          "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86") {
    std::cerr << "frozen action constants drifted\n";
    return 1;
  }
  if (!ContainsAll(header,
                   {"CaptureStewardDevelopCountyTaskObservationV1",
                    "ValidateStewardDevelopCountyCommandV1",
                    "SubmitStewardDevelopCountyCommandV1",
                    "submitted_verification_pending",
                    "postcondition_failed"}) ||
      !ContainsAll(action,
                   {"native_command_abi_not_certified",
                    "state_changed_before_submit",
                    "native_validation_failed",
                    "no_new_paused_observation",
                    "wrong_task_or_target_observed",
                    "progress_binding_unavailable"}) ||
      !ContainsAll(abi,
                   {"\"command_abi_certified\": false",
                    "\"production_capability_advertised\": false",
                    "steward-develop-county-command-observer-v1"})) {
    return 1;
  }

  // Static discovery is not authorization.  Until the command observer closes
  // the object and apply lifecycle, no production registry may advertise or
  // route this capability.
  constexpr std::string_view capability =
      "game.command.change-steward-develop-county-task-v1";
  constexpr std::string_view step =
      "change-steward-develop-county-task-v1";
  if (Contains(game_adapter, capability) || Contains(adapter, capability) ||
      Contains(bridge, capability) || Contains(game_adapter, step) ||
      Contains(adapter, step) || Contains(bridge, step)) {
    std::cerr << "uncertified action is advertised by production native code\n";
    return 1;
  }
  std::cout << "steward-develop-county-action-v1 source contract passed\n";
  return 0;
}
