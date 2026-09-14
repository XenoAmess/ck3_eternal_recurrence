#include <fstream>
#include <iostream>
#include <iterator>
#include <string>
#include <string_view>
#include <vector>

namespace {

bool ReadSource(const char *path, std::string &output) {
  std::ifstream input(path, std::ios::binary);
  if (!input) {
    std::cerr << "could not open source: " << path << '\n';
    return false;
  }
  output.assign(std::istreambuf_iterator<char>(input),
                std::istreambuf_iterator<char>());
  return true;
}

bool ContainsAll(std::string_view source,
                 const std::vector<std::string_view> &tokens) {
  for (const auto token : tokens) {
    if (source.find(token) == std::string_view::npos) {
      std::cerr << "missing military preparation contract token: " << token
                << '\n';
      return false;
    }
  }
  return true;
}

} // namespace

int main(int argc, char **argv) {
  if (argc != 4) {
    std::cerr << "usage: military_preparation_summary_v1_source_contract_test "
                 "<abi.hpp> <core.cpp> <serializer.cpp>\n";
    return 1;
  }
  std::string abi;
  std::string core;
  std::string serializer;
  if (!ReadSource(argv[1], abi) || !ReadSource(argv[2], core) ||
      !ReadSource(argv[3], serializer)) {
    return 1;
  }

  if (!ContainsAll(
          abi,
          {"kMilitaryPreparationSummaryEnabledByDefaultV1 = false",
           "0x999AF0", "0x9999B0", "0x3B8B000", "0x81F190",
           "0x337B210", "0x3354330", "0x3354280", "0x3369820",
           "kMilitaryPreparationRootScopeSizeV1 = 0x168",
           "kMilitaryPreparationCharacterRootKindV1 = 4",
           "0xF08", "0xF10", "0xF14",
           "0x34, 0x35, 0x36, 0x43, 0x44",
           "xar_mcp_military_current_strength_final",
           "xar_mcp_military_max_strength_final",
           "xar_mcp_military_number_of_knights_final",
           "xar_mcp_military_max_number_of_knights_final",
           "xar_mcp_military_maa_gold_expense_relative_final",
           "ai_men_at_arms_expense_gold_min",
           "ai_men_at_arms_expense_gold_ideal",
           "ai_men_at_arms_expense_gold_max",
           "ai_men_at_arms_chance_expense_below_min",
           "ai_men_at_arms_chance_expense_below_ideal",
           "88C220FD822BE90E6E8DF71E1FC26214D62E5218493F5FCF1B64C2CD80A2DC04"})) {
    return 1;
  }

  const std::string_view core_view(core);
  const auto reader = core_view.find("bool ReadMilitaryPreparationSummaryV1(");
  if (reader == std::string_view::npos) {
    std::cerr << "private observer reader is missing\n";
    return 1;
  }
  const auto body = core_view.substr(reader);
  const auto disabled = body.find("!environment.observer_enabled");
  const auto exact = body.find("!environment.exact_build_admitted");
  const auto callbacks = body.find("!CallbacksComplete(environment)");
  const auto thread = body.find("environment.current_thread_id == 0");
  const auto first_state_read = body.find("environment.read_frame(");
  if (disabled == std::string_view::npos || exact == std::string_view::npos ||
      callbacks == std::string_view::npos || thread == std::string_view::npos ||
      first_state_read == std::string_view::npos || !(disabled < exact &&
      exact < callbacks && callbacks < thread && thread < first_state_read)) {
    std::cerr << "default-off/exact-build/callback/thread admission must precede state read\n";
    return 1;
  }
  if (!ContainsAll(
          body,
          {"before.snapshot_revision != expected_revision",
           "before.played_character_id <= 0",
           "environment.begin_session(",
           "EvaluatePass(environment, session, first, failure)",
           "EvaluatePass(environment, session, second, failure)",
           "first != second", "after != before",
           "environment.end_session(",
           "output.values = Decode(first)",
           "output.observation_ready = true"})) {
    return 1;
  }
  for (const auto forbidden : {std::string_view{"static void *"},
                               std::string_view{"thread_local"},
                               std::string_view{"cached_definition"}}) {
    if (core_view.find(forbidden) != std::string_view::npos) {
      std::cerr << "cross-frame native pointer retention token found: "
                << forbidden << '\n';
      return 1;
    }
  }
  if (!ContainsAll(serializer,
                   {"xar.ck3.private.military_preparation_summary_v1",
                    "raw_pointer_fields_persisted\\\":false"})) {
    return 1;
  }
  return 0;
}
