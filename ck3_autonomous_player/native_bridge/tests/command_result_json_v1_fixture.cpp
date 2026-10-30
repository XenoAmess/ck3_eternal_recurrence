#include "xar_bridge/nonwar_private_snapshot_guard_diagnostics_v1.hpp"
#include <array>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>

// Generated include containing the actual current production bodies of
// AppendJsonString and CommandResultFrame from src/bridge.cpp.
#include "command_result_body.inc"

static void Write(const std::filesystem::path &path, std::string_view value) {
  std::ofstream output(path, std::ios::binary);
  if (!output.write(value.data(), static_cast<std::streamsize>(value.size())))
    throw std::runtime_error("fixture output failed");
}

static void WritePacket(const std::filesystem::path &path, std::string_view value) {
  const auto length = static_cast<std::uint32_t>(value.size());
  std::string packet(4, '\0');
  for (unsigned shift = 0; shift != 32; shift += 8)
    packet[shift / 8] = static_cast<char>((length >> shift) & 0xffU);
  packet.append(value);
  Write(path, packet);
}

static std::string ReadBinary(const std::filesystem::path &path) {
  std::ifstream input(path, std::ios::binary);
  if (!input) throw std::runtime_error("fixture input failed");
  std::string content;
  input.seekg(0, std::ios::end);
  const auto size = input.tellg();
  input.seekg(0, std::ios::beg);
  content.resize(static_cast<std::size_t>(size));
  if (size > 0 && !input.read(content.data(), static_cast<std::streamsize>(size)))
    throw std::runtime_error("fixture input read failed");
  return content;
}

int main(int argc, char **argv) {
  if (argc != 3) return 2;
  const std::filesystem::path output(argv[1]);
  const std::filesystem::path golden(argv[2]);
  std::filesystem::create_directories(output);

  // Scene 1: Nonwar date_raw difference
  xar::game::Snapshot prior{};
  prior.date_raw = 1008; prior.paused = true;
  const std::optional<xar::game::Snapshot> previous{prior};
  xar::game::Snapshot current{};
  unsigned reads = 0;
  const auto error = xar::bridge::NonwarPrivateSnapshotGuardFailureV1(
      false, true, 3, 3, previous, current,
      [&](xar::game::Snapshot &observed) {
        ++reads; observed = prior; observed.date_raw += 24; return true;
      }, true);
  if (reads != 1 || error.find("changed_snapshot_fields=[\"date_raw\"]") == std::string::npos)
    return 3;
  Write(output / "nonwar.expected", error);
  WritePacket(output / "nonwar.bin", CommandResultFrame("fixture-nonwar", "private-query-fixture-v1", false, error));

  // Scene 2: Status grammar
  std::string status = "path=C:\\save\\slot\nnext\t";
  status.push_back('\x01'); status.push_back('\0'); status += "\"quoted\"";
  Write(output / "controls.expected", status);
  WritePacket(output / "controls.bin", CommandResultFrame("fixture-controls", "private-query-fixture-v1", true, status));

  // Compare produced payloads with canonical Java golden resources
  for (const auto &name : {"nonwar", "controls"}) {
    const std::string bin_name = std::string(name) + ".bin";
    const std::string json_name = std::string(name) + ".json";
    const auto produced = ReadBinary(output / bin_name);
    const auto expected = ReadBinary(golden / json_name);
    // Strip the 4-byte LE length prefix from produced packet for comparison
    if (produced.size() < 4) return 4;
    const std::string_view produced_json(produced.data() + 4, produced.size() - 4);
    if (produced_json != std::string_view(expected.data(), expected.size())) {
      std::cerr << "golden mismatch for " << name << '\n';
      return 5;
    }
  }

  std::cout << "produced 2 software packets; actual Nonwar guard callback count=" << reads << '\n';
  return 0;
}
