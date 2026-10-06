#include "xar_bridge/army_strength_result_write_diagnostic_v1.hpp"

#include <array>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <string>
#include <string_view>

namespace {

void Check(bool condition, std::string_view message) {
  if (!condition) {
    std::cerr << message << '\n';
    std::exit(EXIT_FAILURE);
  }
}

struct PipePair {
  HANDLE reader = nullptr;
  HANDLE writer = nullptr;

  PipePair() {
    Check(CreatePipe(&reader, &writer, nullptr, 4096U) != FALSE,
          "anonymous fixture pipe created");
  }
  ~PipePair() {
    if (reader != nullptr) CloseHandle(reader);
    if (writer != nullptr) CloseHandle(writer);
  }
  PipePair(const PipePair &) = delete;
  PipePair &operator=(const PipePair &) = delete;
};

std::string ReadWire(HANDLE reader, std::string_view expected) {
  std::array<unsigned char, 4> header{};
  DWORD read = 0;
  Check(ReadFile(reader, header.data(), static_cast<DWORD>(header.size()),
                 &read, nullptr) != FALSE && read == header.size(),
        "actual protocol length header read");
  const auto length = static_cast<std::uint32_t>(header[0]) |
      (static_cast<std::uint32_t>(header[1]) << 8U) |
      (static_cast<std::uint32_t>(header[2]) << 16U) |
      (static_cast<std::uint32_t>(header[3]) << 24U);
  Check(length == expected.size(), "transmitted length equals actual payload");
  std::string actual(length, '\0');
  Check(ReadFile(reader, actual.data(), length, &read, nullptr) != FALSE &&
                 read == length,
        "actual complete protocol payload read");
  Check(actual == expected, "complete result bytes unchanged");
  return actual;
}

} // namespace

int main(int argc, char* argv[]) {
  using namespace xar::bridge;
  const bool broken_reader_only = argc == 3 &&
      std::string_view(argv[1]) == "--scene" &&
      std::string_view(argv[2]) == "broken_reader";
  Check(argc == 1 || broken_reader_only,
        "usage: army_strength_result_write_diagnostic_v1_test [--scene broken_reader]");
  const std::string ordinary =
      R"({"type":"command_result","protocol_version":1,"request_id":"army-write-result","ok":true,"result":{"step":"query-army-strengths-v1","accepted":true,"status":"available","query_sequence":1,"army_strengths":[{"status":"available","army_id":218104048,"native_carmy_id":218105048,"scope_role":"player","war_ids":[],"regiment_count":3,"current_soldiers":1200,"maximum_soldiers":1500,"ai_base_power_raw":180000000,"ai_base_power_scale":100000,"unavailable_reason":null}]}})";
  if (!broken_reader_only) {
    PipePair pipe;
    ArmyStrengthResultWriteDiagnosticV1 diagnostic;
    Check(SerializeArmyStrengthResultWriteDiagnosticV1(diagnostic) == "null",
          "no previous Army write is reported before capture");
    Check(WriteArmyStrengthResultFrameV1(pipe.writer, ordinary, 1U, diagnostic),
          "ordinary Army result uses actual production writer");
    ReadWire(pipe.reader, ordinary);
    Check(diagnostic.recorded && diagnostic.query_sequence == 1U &&
              diagnostic.frame.payload_bytes == ordinary.size() &&
              diagnostic.frame.limit_bytes == kMaximumFrameBytes &&
              diagnostic.frame.stage == FrameWriteStage::complete &&
              diagnostic.frame.success && !diagnostic.frame.windows_error,
          "ordinary final-byte accounting and absent WinError");
    std::cout << SerializeArmyStrengthResultWriteDiagnosticV1(diagnostic) << '\n';
  }
  if (!broken_reader_only) {
    PipePair pipe;
    ArmyStrengthResultWriteDiagnosticV1 diagnostic;
    const std::string prefix =
        R"({"type":"command_result","protocol_version":1,"request_id":"army-write-size","ok":true,"result":{"step":"query-army-strengths-v1","fixture_padding":")";
    const std::string suffix = R"("}})";
    const auto oversize_bytes = static_cast<std::size_t>(kMaximumFrameBytes) + 1U;
    const std::string oversized = prefix +
        std::string(oversize_bytes - prefix.size() - suffix.size(), 'x') + suffix;
    Check(!WriteArmyStrengthResultFrameV1(pipe.writer, oversized, 2U, diagnostic),
          "existing over-limit admission returns false");
    Check(diagnostic.frame.payload_bytes == oversize_bytes &&
              diagnostic.frame.limit_bytes == kMaximumFrameBytes &&
              diagnostic.frame.stage == FrameWriteStage::size_limit &&
              !diagnostic.frame.success && !diagnostic.frame.windows_error,
          "over-limit actual bytes and absent stale WinError");
    const auto original = SerializeArmyStrengthResultWriteDiagnosticV1(diagnostic);
    const auto error = ArmyStrengthResultSizeLimitErrorV1(diagnostic.frame);
    Check(error.find("payload_bytes=" + std::to_string(oversize_bytes)) !=
              std::string::npos &&
              error.find("limit_bytes=" + std::to_string(kMaximumFrameBytes)) !=
              std::string::npos,
          "ordinary error contains actual bytes and existing bound");
    const auto fallback =
        std::string(R"({"type":"command_result","protocol_version":1,"request_id":"army-write-size","ok":false,"error":")") +
        error + R"("})";
    Check(WriteFrame(pipe.writer, fallback), "same-request small diagnostic writes");
    ReadWire(pipe.reader, fallback);
    Check(SerializeArmyStrengthResultWriteDiagnosticV1(diagnostic) == original,
          "fallback preserves the original rejected Army diagnostic");
    std::cout << original << '\n';
  }
  {
    PipePair pipe;
    Check(CloseHandle(pipe.reader) != FALSE, "fixture reader closes normally");
    pipe.reader = nullptr;
    const std::array<unsigned char, 4> header{};
    DWORD written = 0;
    const BOOL direct_result = WriteFile(
        pipe.writer, header.data(), static_cast<DWORD>(header.size()),
        &written, nullptr);
    const DWORD direct_error = GetLastError();
    ArmyStrengthResultWriteDiagnosticV1 diagnostic;
    const bool result = WriteArmyStrengthResultFrameV1(
        pipe.writer, ordinary, 3U, diagnostic);
    std::cout << "broken_reader direct_write_result=" << direct_result
              << " direct_windows_error=" << direct_error
              << " captured="
              << SerializeArmyStrengthResultWriteDiagnosticV1(diagnostic)
              << std::endl;
    Check(direct_result == FALSE, "closed reader direct WriteFile probe fails");
    Check(!result,
          "broken reader causes an actual WriteFile failure");
    Check(diagnostic.frame.payload_bytes == ordinary.size() &&
              diagnostic.frame.limit_bytes == kMaximumFrameBytes &&
              diagnostic.frame.stage == FrameWriteStage::header &&
              !diagnostic.frame.success &&
              diagnostic.frame.windows_error ==
                  static_cast<std::uint32_t>(direct_error),
          "actual immediate WinError and header phase retained");
    const auto original = diagnostic.frame.windows_error;
    SetLastError(ERROR_SUCCESS);
    const auto wire = SerializeArmyStrengthResultWriteDiagnosticV1(diagnostic);
    Check(diagnostic.frame.windows_error == original &&
              wire.find("\"windows_error\":" +
                        std::to_string(static_cast<std::uint32_t>(direct_error))) !=
                  std::string::npos,
          "later Windows calls do not overwrite the captured actual error");
    std::cout << wire << '\n';
  }
  std::cout << (broken_reader_only
      ? "army result write diagnostic: broken_reader scene passed\n"
      : "army result write diagnostic: three offline scenes passed\n");
  return EXIT_SUCCESS;
}
