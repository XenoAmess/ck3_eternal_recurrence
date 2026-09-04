#include <fstream>
#include <iostream>
#include <iterator>
#include <string>
#include <string_view>
#include <vector>

namespace {

bool AppearsInOrder(std::string_view source,
                    const std::vector<std::string_view> &needles) {
  std::size_t position = 0;
  for (const auto needle : needles) {
    position = source.find(needle, position);
    if (position == std::string_view::npos) {
      std::cerr << "missing or reordered war-termination frame token: "
                << needle << '\n';
      return false;
    }
    position += needle.size();
  }
  return true;
}

bool ReadSource(const char *path, std::string &output) {
  std::ifstream input(path, std::ios::binary);
  if (!input) {
    std::cerr << "could not open bridge source: " << path << '\n';
    return false;
  }
  output.assign(std::istreambuf_iterator<char>(input),
                std::istreambuf_iterator<char>());
  return true;
}

std::size_t Count(std::string_view source, std::string_view needle) {
  std::size_t count = 0;
  std::size_t position = 0;
  while ((position = source.find(needle, position)) !=
         std::string_view::npos) {
    ++count;
    position += needle.size();
  }
  return count;
}

} // namespace

int main(int argc, char **argv) {
  if (argc != 2) {
    std::cerr << "usage: war_termination_same_frame_source_contract_test "
                 "<bridge.cpp>\n";
    return 1;
  }
  std::string source;
  if (!ReadSource(argv[1], source)) {
    return 1;
  }
  const std::string_view view(source);
  const auto session = view.find("void RunConnectedSession(");
  const auto begin = view.find(
      "\"query-war-termination-options-\"", session);
  const auto terms_end = view.find(
      "\"query-war-termination-terms-v1-\"",
      begin == std::string_view::npos ? 0 : begin + 1);
  const auto actual_expiry_end = view.find(
      "kRaiktorActualTruceExpiryV1StepPrefix",
      begin == std::string_view::npos ? 0 : begin + 1);
  const auto end = actual_expiry_end != std::string_view::npos &&
                           actual_expiry_end < terms_end
                       ? actual_expiry_end
                       : terms_end;
  if (session == std::string_view::npos ||
      begin == std::string_view::npos || end == std::string_view::npos ||
      begin >= end) {
    std::cerr << "could not isolate production war-termination query branch\n";
    return 1;
  }
  const auto branch = view.substr(begin, end - begin);
  if (!AppearsInOrder(
          branch,
          {
              "ParseCampaignRootContextExpectedRevisionV1(",
              "expected_revision != state_revision",
              "ReadSnapshot(game, admission_snapshot)",
              "admission_snapshot != previous_snapshot.value()",
              "PublishSnapshot(",
              "war-termination admission snapshot changed; ",
              "ReadWarTerminationOptions(",
              "ReadSnapshot(game, completion_snapshot)",
              "completion_snapshot != admission_snapshot",
              "PublishSnapshot(",
              "war-termination completion snapshot ",
              "const auto next_query_sequence =",
              "WarTerminationOptionsResultFrame(",
              "war_termination_query_sequence = next_query_sequence",
          })) {
    return 1;
  }
  if (Count(branch, "PublishSnapshot(") != 2 ||
      branch.find("++war_termination_query_sequence") !=
          std::string_view::npos) {
    std::cerr << "war-termination retry/sequence contract is not exact\n";
    return 1;
  }
  return 0;
}
