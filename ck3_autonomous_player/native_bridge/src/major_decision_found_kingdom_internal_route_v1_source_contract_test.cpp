#include <algorithm>
#include <cctype>
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

std::string Compact(std::string_view value) {
  std::string output;
  output.reserve(value.size());
  for (const unsigned char character : value) {
    if (!std::isspace(character)) output.push_back(character);
  }
  return output;
}

std::size_t Count(std::string_view value, std::string_view token) {
  std::size_t result = 0;
  for (std::size_t offset = 0;
       (offset = value.find(token, offset)) != std::string_view::npos;
       offset += token.size()) {
    ++result;
  }
  return result;
}

bool Require(std::string_view value, std::string_view token) {
  if (value.find(token) != std::string_view::npos) return true;
  std::cerr << "missing source-contract token: " << token << '\n';
  return false;
}

} // namespace

int main(int argc, char **argv) {
  if (argc != 8) {
    std::cerr << "expected seven source-contract paths\n";
    return 1;
  }
  const auto mailbox_header = ReadAll(argv[1]);
  const auto mailbox_source = ReadAll(argv[2]);
  const auto bridge = Compact(ReadAll(argv[3]));
  const auto shared_test = ReadAll(argv[4]);
  const auto route_source = ReadAll(argv[5]);
  const auto route_test = ReadAll(argv[6]);
  const auto cmake = ReadAll(argv[7]);
  if (mailbox_header.empty() || mailbox_source.empty() || bridge.empty() ||
      shared_test.empty() || route_source.empty() || route_test.empty() ||
      cmake.empty()) {
    std::cerr << "source-contract input is unreadable\n";
    return 1;
  }

  if (Count(mailbox_header, "permitted_executor_sextrigintary") != 2 ||
      Count(mailbox_source, "permitted_executor_sextrigintary") != 5) {
    std::cerr << "executor 36 install/copy/allowlist surface drifted\n";
    return 1;
  }
  if (!Require(
          bridge,
          "environment.permitted_executor_quattuortrigintary="
          "&xar::ck3_11906::ExecuteFactionGiftMitigationAsyncMailboxV1;") ||
      !Require(
          bridge,
          "environment.permitted_executor_quintrigintary="
          "&xar::ck3::shared::"
          "ExecuteDomainConstructionApplicationMainRuntimeV1;") ||
      !Require(
          bridge,
          "environment.permitted_executor_sextrigintary="
          "&xar::bridge::ExecuteMajorDecisionFoundKingdomSharedMailboxV1;")) {
    return 1;
  }
  if (shared_test.find("mailbox.permitted_executor_sextrigintary") ==
          std::string::npos ||
      route_test.find("mailbox.permitted_executor_sextrigintary") ==
          std::string::npos ||
      route_source.find("WaitForMainThreadQueryV1") != std::string::npos) {
    std::cerr << "decision executor fixture or async driver contract drifted\n";
    return 1;
  }
  if (!Require(cmake,
               "XAR_CK3_ENABLE_G2_MAJOR_DECISION_FOUND_KINGDOM_INTERNAL_ROUTE_V1") ||
      !Require(cmake,
               "major_decision_found_kingdom_internal_route_v1_source_contract_test")) {
    return 1;
  }

  std::cout << "found-kingdom executor 36 source contract passed\n";
  return 0;
}
