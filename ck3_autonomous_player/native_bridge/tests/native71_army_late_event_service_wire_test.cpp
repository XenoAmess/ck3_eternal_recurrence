#include "native71_late_event_wire_setup64.inc.hpp"
#include "xar_bridge/army_strength_v1_serializer.hpp"
#include <fstream>
#include <iostream>
#include <stdexcept>

int main(int argc, char **argv) {
  try {
    if (argc != 2) throw std::runtime_error("new whole query wire needs one output path");
    constexpr std::int32_t army_id = 11;
    constexpr std::int32_t native_carmy_id = -2130706399; // FullID0x81000021, including generation.
    if (!late_event_new_wire_setup64::InitializeAndSeed(native_carmy_id))
      throw std::runtime_error("new owned journal input initialization failed");
    xar::game::ArmyStrengthSnapshot strength{};
    strength.available = true;
    strength.army_id = army_id;
    strength.native_carmy_id_observable = true;
    strength.native_carmy_id = native_carmy_id;
    strength.scope_role = xar::game::ArmyStrengthScopeRole::player;
    strength.current_soldiers = 160;
    strength.maximum_soldiers = 200;
    auto number = [](auto value) { return std::to_string(value); };
    auto string = [](std::string &out, std::string_view text) {
      out += '"';
      for (const auto c : text) {
        if (c == '"' || c == '\\') out += '\\';
        out += c;
      }
      out += '"';
    };
    auto array = [](std::string &out, const auto &values) {
      out += '[';
      bool first = true;
      for (const auto value : values) {
        if (!first) out += ',';
        first = false;
        out += std::to_string(value);
      }
      out += ']';
    };
    std::string row;
    xar::game::AppendArmyStrengthV1WithManagerInputsMode(row, strength, number, array, string,
        xar::game::ArmyStrengthManagerInputsModeV1::inline_values);
    if (late_event_new_wire_setup64::original_calls != 1)
      throw std::runtime_error("query serialization invoked the native dispatcher again");
    if (row.find("\"actual_army_late_event_observations_v1\":") == std::string::npos)
      throw std::runtime_error("actual journal was not appended by the production Army serializer");
    std::ofstream output(argv[1], std::ios::binary);
    output << "{\"status\":\"available\",\"query_sequence\":59,\"source\":{\"game_version\":\"1.20.0.4\","
        "\"executable_sha256\":\"98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518\"},"
        "\"native_readiness\":{\"current_strength\":true,\"full_monthly\":false},\"army_strengths\":["
           << row << "]}\n";
    if (!output) throw std::runtime_error("new whole query wire write failed");
    std::cout << "new Army late event journal to production query serializer GREEN; synthetic offline; original_calls=1\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
