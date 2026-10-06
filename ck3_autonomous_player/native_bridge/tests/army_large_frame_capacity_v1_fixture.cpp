#include "xar_bridge/army_strength_result_write_diagnostic_v1.hpp"

#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>

namespace {

constexpr std::size_t kHistoricalArmyPayloadBytes = 33445694U;
constexpr std::string_view kArmyStep = "query-army-strengths-v1";

void Require(bool condition, std::string_view message) {
  if (!condition) throw std::runtime_error(std::string(message));
}

struct OwnedPipe {
  HANDLE handle = INVALID_HANDLE_VALUE;
  ~OwnedPipe() {
    if (handle != INVALID_HANDLE_VALUE) CloseHandle(handle);
  }
};

xar::bridge::ReadResult WaitForFrame(HANDLE pipe, ULONGLONG deadline) {
  while (GetTickCount64() < deadline) {
    auto result = xar::bridge::TryReadFrame(pipe);
    if (result.status != xar::bridge::ReadStatus::none) return result;
    Sleep(5U);
  }
  throw std::runtime_error("fixture peer request timed out");
}

void WritePong(HANDLE pipe, const std::string& request_id) {
  const auto pong =
      std::string(R"({"type":"pong","protocol_version":1,"request_id":")") +
      request_id + R"("})";
  Require(xar::bridge::WriteFrame(pipe, pong), "fixture pong write failed");
}

struct RenderedResult {
  std::string payload;
  std::size_t prefix_bytes = 0;
  std::size_t source_payload_bytes = 0;
  std::size_t suffix_bytes = 0;
};

RenderedResult RenderResult(const std::string& request_id) {
  // One meaningful nonempty Army row, followed by one unique top-level ASCII
  // source_payload field. This synthetic body matches the historical rendered
  // body length; it does not reproduce the historical gameplay observation.
  const auto prefix =
      std::string(R"({"type":"command_result","protocol_version":1,"request_id":")") +
      request_id +
      R"(","ok":true,"result":{"step":"query-army-strengths-v1","accepted":true,"status":"available","query_sequence":1,"army_strengths":[{"status":"available","army_id":218104048,"native_carmy_id":218105048,"scope_role":"player","war_ids":[],"regiment_count":3,"current_soldiers":1200,"maximum_soldiers":1500,"ai_base_power_raw":180000000,"ai_base_power_scale":100000,"unavailable_reason":null}]},"source_payload":")";
  const std::string suffix = R"("})";
  Require(prefix.size() + suffix.size() < kHistoricalArmyPayloadBytes,
          "fixture envelope exceeds historical length");
  RenderedResult rendered;
  rendered.prefix_bytes = prefix.size();
  rendered.suffix_bytes = suffix.size();
  rendered.source_payload_bytes =
      kHistoricalArmyPayloadBytes - prefix.size() - suffix.size();
  rendered.payload.reserve(kHistoricalArmyPayloadBytes);
  rendered.payload += prefix;
  rendered.payload.append(rendered.source_payload_bytes, 'x');
  rendered.payload += suffix;
  Require(rendered.payload.size() == kHistoricalArmyPayloadBytes,
          "fixture body does not match historical rendered byte count");
  return rendered;
}

void WriteReceipt(const std::filesystem::path& path,
                  const RenderedResult& rendered,
                  const xar::bridge::ArmyStrengthResultWriteDiagnosticV1& diagnostic) {
  const auto receipt =
      std::string(R"({"scene":"historical_army_response_33445694_bytes","synthetic_payload":true,"new_scene_count":1,"native_writer":"WriteArmyStrengthResultFrameV1->WriteFrame","payload_bytes":)") +
      std::to_string(rendered.payload.size()) +
      ",\"prefix_bytes\":" + std::to_string(rendered.prefix_bytes) +
      ",\"source_payload_bytes\":" + std::to_string(rendered.source_payload_bytes) +
      ",\"suffix_bytes\":" + std::to_string(rendered.suffix_bytes) +
      ",\"write_diagnostic\":" +
      xar::bridge::SerializeArmyStrengthResultWriteDiagnosticV1(diagnostic) + "}";
  std::ofstream output(path, std::ios::binary);
  Require(output.is_open(), "fixture writer receipt could not open");
  output << receipt << '\n';
  output.close();
  Require(!output.fail(), "fixture writer receipt could not finish");
  std::cout << receipt << std::endl;
}

}  // namespace

int wmain(int argc, wchar_t* argv[]) {
  try {
    Require(argc == 5 && std::wstring_view(argv[1]) == L"--pipe-name" &&
                std::wstring_view(argv[3]) == L"--receipt",
            "usage: army_large_frame_capacity_v1_fixture --pipe-name NAME --receipt PATH");
    OwnedPipe pipe;
    pipe.handle = CreateFileW(argv[2], GENERIC_READ | GENERIC_WRITE, 0, nullptr,
                              OPEN_EXISTING, 0, nullptr);
    Require(pipe.handle != INVALID_HANDLE_VALUE, "fixture named-pipe connection failed");
    const auto hello =
        std::string(R"({"type":"hello","protocol_version":1,"pid":)") +
        std::to_string(GetCurrentProcessId()) +
        R"(,"bridge_version":"army-large-frame-capacity-fixture-v1","connection_generation":1,"capabilities":["game.step.query-army-strengths-v1"]})";
    Require(xar::bridge::WriteFrame(pipe.handle, hello), "fixture hello write failed");
    const auto deadline = GetTickCount64() + 30000U;
    bool wrote_result = false;
    while (true) {
      const auto request = WaitForFrame(pipe.handle, deadline);
      Require(request.status == xar::bridge::ReadStatus::frame,
              "fixture peer disconnected or sent an invalid frame");
      std::string type;
      std::string request_id;
      Require(xar::bridge::JsonStringField(request.payload, "type", type,
                                           xar::bridge::kMaximumControlStringBytes) &&
                  xar::bridge::JsonStringField(request.payload, "request_id", request_id,
                                               xar::bridge::kMaximumControlStringBytes),
              "fixture peer request lacks type or request_id");
      if (type == "ping") {
        WritePong(pipe.handle, request_id);
        // The consumer sends an ordinary ping after retrieving the full result.
        // Keeping this real peer connected lets the production read loop drain
        // the large frame before normal transport teardown.
        if (wrote_result) return EXIT_SUCCESS;
        continue;
      }
      std::string step;
      Require(!wrote_result && type == "execute_step" &&
                  xar::bridge::JsonStringField(request.payload, "step", step,
                                               xar::bridge::kMaximumControlStringBytes) &&
                  step == kArmyStep,
              "fixture expects one army-strength execute_step request");
      const auto rendered = RenderResult(request_id);
      xar::bridge::ArmyStrengthResultWriteDiagnosticV1 diagnostic;
      const auto success = xar::bridge::WriteArmyStrengthResultFrameV1(
          pipe.handle, rendered.payload, 1U, diagnostic);
      WriteReceipt(std::filesystem::path(argv[4]), rendered, diagnostic);
      Require(success, "historical-size Army frame did not pass the production writer");
      wrote_result = true;
    }
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return EXIT_FAILURE;
  }
}
