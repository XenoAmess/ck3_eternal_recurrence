#include <fstream>
#include <iostream>
#include <iterator>
#include <string>
#include <string_view>
#include <vector>

namespace {

bool ReadFile(const char *path, std::string &output) {
  std::ifstream input(path, std::ios::binary);
  if (!input) return false;
  output.assign(std::istreambuf_iterator<char>(input),
                std::istreambuf_iterator<char>());
  return true;
}

bool ContainsAll(std::string_view text,
                 const std::vector<std::string_view> &tokens) {
  for (const auto token : tokens) {
    if (text.find(token) == std::string_view::npos) {
      std::cerr << "missing MIL4 binding contract token: " << token << '\n';
      return false;
    }
  }
  return true;
}

} // namespace

int main(int argc, char **argv) {
  if (argc != 6) {
    std::cerr << "usage: military_preparation_summary_v1_binding_source_contract_test "
                 "<binding.hpp> <binding.cpp> <wrapper.txt> <abi.json> "
                 "<contract.json>\n";
    return 1;
  }
  std::string header;
  std::string source;
  std::string wrappers;
  std::string abi;
  std::string contract;
  if (!ReadFile(argv[1], header) || !ReadFile(argv[2], source) ||
      !ReadFile(argv[3], wrappers) || !ReadFile(argv[4], abi) ||
      !ReadFile(argv[5], contract)) {
    return 1;
  }
  if (!ContainsAll(header,
                   {"bool binding_enabled = false",
                    "kMilitaryPreparationRootScopeSizeV1",
                    "construct_support", "destroy_support",
                    "upstream_read_frame", "root_scope_storage", "session_active",
                    "scope_constructed"}) ||
      !ContainsAll(source,
                   {"kCharacterStorageSlotRva = 0x570C130",
                    "kCharacterFallbackSlotRva = 0x570C138",
                    "kDestroyScopeTailRva = 0x81E900",
                    "kDestroyRows48Rva = 0x81E980",
                    "kDestroySupport2A8RowsRva = 0x969BA0",
                    "kMilitaryPreparationFixedEvaluatorRvaV1",
                    "fixed_definition != definition",
                    "state.session_active = false",
                    "AlignedInternalContext(state)",
                    "AnyOverride(binding.operations)"}) ||
      !ContainsAll(wrappers,
                   {"xar_mcp_military_current_strength_final",
                    "value = current_military_strength",
                    "xar_mcp_military_max_strength_final",
                    "value = max_military_strength",
                    "xar_mcp_military_number_of_knights_final",
                    "value = number_of_knights",
                    "xar_mcp_military_max_number_of_knights_final",
                    "value = max_number_of_knights",
                    "xar_mcp_military_maa_gold_expense_relative_final",
                    "value = character_men_at_arms_expense_gold_relative"}) ||
      !ContainsAll(abi,
                   {"static_confirmed_no_ck3_launch",
                    "0F1A84CDD95DD6DB78E7A49D4FC754164BB8340F4374073DC71F7531D63C0DB8",
                    "7156A7E95CB379797E67D986F4CDBE2936EE932F6DCA093CDAD0669DE1994D10",
                    "A44085ACBBFFFBF575179D89A316FA967E849F39393FBDBB91DCB2E509C96035"}) ||
      !ContainsAll(contract,
                   {"static_ready_no_ck3_launch",
                    "partial_values_published_on_failure\": false",
                    "public_capability_registered\": false"})) {
    return 1;
  }
  if (wrappers.size() < 3 ||
      static_cast<unsigned char>(wrappers[0]) != 0xEF ||
      static_cast<unsigned char>(wrappers[1]) != 0xBB ||
      static_cast<unsigned char>(wrappers[2]) != 0xBF ||
      wrappers.find("random") != std::string::npos ||
      wrappers.find("effect =") != std::string::npos ||
      wrappers.find("save_scope") != std::string::npos) {
    std::cerr << "wrapper file is not BOM UTF-8 or is not read-only\n";
    return 1;
  }
  return 0;
}
