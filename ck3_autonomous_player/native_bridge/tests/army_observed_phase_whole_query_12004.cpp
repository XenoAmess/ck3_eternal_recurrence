#include "xar_bridge/army_strength_v1_serializer.hpp"
#include "xar_bridge/army_natural_phase_scope_12004.hpp"
#include <fstream>
#include <iostream>
#include <stdexcept>

bool InitializeArmyPreparationNaturalQuerySetup12004(std::uint32_t) noexcept;
void EnableArmyPlacementNaturalQueryFocus12004() noexcept;
xar::ck3_12004::ArmyNaturalPhaseBindings12004 ArmyPreparationNaturalSetupBindings12004() noexcept;
void *ArmyPreparationNaturalSetupSecondary12004() noexcept;
xar::ck3_12004::ArmyNaturalPhaseOriginal12004 ArmyPreparationNaturalSetupOriginal12004() noexcept;

int main(int argc, char **argv) {
  try {
    using namespace xar::ck3_12004;
    if (argc != 2) throw std::runtime_error("whole observed Army wire needs one new output path");
    constexpr std::uint32_t full_id = 0x81000021U;
    if (!InitializeArmyPreparationNaturalQuerySetup12004(full_id))
      throw std::runtime_error("owned installed preparation input setup failed");
    EnableArmyPlacementNaturalQueryFocus12004();
    const auto phase = InvokeArmyNaturalPhaseScope12004(ArmyPreparationNaturalSetupBindings12004(),
        ArmyPreparationNaturalSetupOriginal12004(), ArmyPreparationNaturalSetupSecondary12004(),
        ArmyNaturalPhaseKind12004::pre_date, 0);
    if (!phase.original_called || !phase.original_returned)
      throw std::runtime_error("fresh natural parent did not return");
    const auto before = ReadActualArmyDailyAssaultPreparationObservations12004(full_id);
    const auto placement_before = ReadActualArmyAssaultPlacementObservations12004(full_id);
    if (!before || before->events.size() != 1 || !before->observer_installed || !before->current_session_guard)
      throw std::runtime_error("fresh installed owned preparation was not retained exactly once");
    if (!placement_before || placement_before->events.size() != 1 || !placement_before->observer_installed || !placement_before->current_session_guard)
      throw std::runtime_error("fresh installed owned placement was not retained exactly once");

    xar::game::ArmyStrengthSnapshot strength{};
    strength.available = true; strength.army_id = 11;
    strength.native_carmy_id_observable = true;
    strength.native_carmy_id = static_cast<std::int32_t>(full_id);
    strength.scope_role = xar::game::ArmyStrengthScopeRole::player;
    strength.current_soldiers = 160; strength.maximum_soldiers = 200;
    const auto number = [](auto value) { return std::to_string(value); };
    const auto string = [](std::string &out, std::string_view text) {
      army_actual_monthfirst_cleanup_json_detail::String(out, text);
    };
    const auto array = [](std::string &out, const auto &values) {
      out += '['; bool first = true;
      for (const auto value : values) { if (!first) out += ','; first = false; out += std::to_string(value); }
      out += ']';
    };
    std::string row;
    xar::game::AppendArmyStrengthV1WithManagerInputsMode(row, strength, number, array, string,
        xar::game::ArmyStrengthManagerInputsModeV1::inline_values);
    const auto after = ReadActualArmyDailyAssaultPreparationObservations12004(full_id);
    const auto placement_after = ReadActualArmyAssaultPlacementObservations12004(full_id);
    if (!after || after->latest_sequence != before->latest_sequence || after->events.size() != 1 ||
        !placement_after || placement_after->latest_sequence != placement_before->latest_sequence || placement_after->events.size() != 1)
      throw std::runtime_error("whole query invoked a native phase again");
    if (row.find("\"mapping_ready\":true") == std::string::npos)
      throw std::runtime_error("production owned placement join did not call the conditional append adapter successfully");
    std::ofstream output(argv[1], std::ios::binary);
    output << "{\"status\":\"available\",\"query_sequence\":5904,\"source\":{\"game_version\":\"1.20.0.4\","
        "\"executable_sha256\":\"98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518\"},"
        "\"native_readiness\":{\"current_strength\":true,\"full_monthly\":false},\"army_strengths\":[" << row << "]}\n";
    if (!output) throw std::runtime_error("whole query packet write failed");
    std::cout << "fresh parent/preparation/placement to whole Army query; synthetic offline; native body is owned stub; live CK3 acceptance false\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
