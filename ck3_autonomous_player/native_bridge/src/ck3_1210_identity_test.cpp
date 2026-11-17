#include "xar_bridge/ck3_1210.hpp"
#include "xar_bridge/ck3_1210_adapter.hpp"

#include <array>
#include <iostream>
#include <string>

int main() {
  using namespace xar::game;
  const auto &descriptor = Ck3_1210AdapterDescriptor();
  if (descriptor.adapter_id != "ck3-1.21.0-msvc-x64" ||
      descriptor.game_version != "1.21.0" ||
      descriptor.executable_sha256 != xar::ck3_1210::kExecutableSha256 ||
      descriptor.checkpoint_save_name != "xar_checkpoint" ||
      !descriptor.capabilities.empty() ||
      xar::ck3_1210::kExecutableFileSize != 114756216 ||
      std::string_view(xar::ck3_1210::kSteamBuildId) != "26622941") {
    std::cerr << "Florin installation identity drifted" << std::endl;
    return 1;
  }
  std::string one_byte(xar::ck3_1210::kExecutableSha256);
  one_byte.back() = one_byte.back() == '0' ? '1' : '0';
  const std::array<std::string_view, 4> hashes{
      xar::ck3_1210::kExecutableSha256, one_byte, "", "unrecognized"};
  for (const auto hash : hashes) {
    auto adapter = CreateCk3_1210Adapter(hash);
    if (!adapter || adapter->enabled() ||
        &adapter->descriptor() != &descriptor ||
        adapter->supports_snapshot() ||
        adapter->supports("game.command.save-checkpoint")) {
      std::cerr << "Unported build exposed a gameplay capability" << std::endl;
      return 1;
    }
    Snapshot snapshot{};
    std::vector<DeclarableWarSnapshot> wars(1);
    std::vector<ArmyStrengthSnapshot> strengths(1);
    if (adapter->read_snapshot(snapshot) ||
        adapter->submit_pause_map(&snapshot) != PauseSubmitResult::unavailable ||
        adapter->submit_resume_map(&snapshot) != ResumeSubmitResult::unavailable ||
        adapter->submit_set_speed(1) ||
        adapter->submit_select_event_option(1) != SelectEventOptionResult::unavailable ||
        adapter->read_declarable_wars(wars) || !wars.empty() ||
        adapter->read_army_strengths(strengths) != ReadArmyStrengthsResult::unavailable ||
        !strengths.empty()) {
      std::cerr << "Disabled adapter invoked or retained gameplay output" << std::endl;
      return 1;
    }
  }
  std::cout << "PASS Florin exact identity; four hashes remain disabled; zero gameplay capabilities" << std::endl;
  return 0;
}
