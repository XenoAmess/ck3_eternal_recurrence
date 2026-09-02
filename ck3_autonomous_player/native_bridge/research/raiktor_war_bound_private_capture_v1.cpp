// Private exact-build debugger capture for bookmark.1071.a war-bound armies.
//
// This executable is opt-in, is not linked into xar_ck3_bridge.dll, and never
// calls CK3 mutation helpers. It observes the post-finalize/pre-cleanup window
// of spawn_army::Execute in a debugger-owned isolated process. The production
// public ABI and readiness remain unchanged.

#include <windows.h>
#include <bcrypt.h>

#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

#pragma comment(lib, "bcrypt.lib")

namespace {

constexpr std::uint64_t kObservationStopRva = 0x2E7F951;
constexpr std::uint64_t kObservationWindowEndRva = 0x2E7F9A6;
constexpr std::uint64_t kSpawnArmyRuntimeVtableRva = 0x443C6E8;
constexpr std::uint64_t kCurrentRegimentStorageSlotRva = 0x57BF4C8;
constexpr std::uint64_t kExpectedExeSize = 95206008;
constexpr wchar_t kExpectedExeSha256[] =
    L"2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
constexpr std::uint8_t kObservationStopByte = 0x41;
constexpr std::size_t kExpectedSourceExecutions = 6;
constexpr std::size_t kMaximumPersistentRegimentsPerExecution = 16;
constexpr std::size_t kMaximumCurrentRegimentsPerArmy = 32;
constexpr std::size_t kCompositionRowCount = 7;

constexpr std::size_t kComponentStorageSlotsOffset = 0x20;
constexpr std::size_t kComponentStorageCapacityOffset = 0x2C;
constexpr std::size_t kComponentStorageSlotSize = 0x10;
constexpr std::size_t kComponentStorageSlotObjectOffset = 0x08;
constexpr std::size_t kObjectIdOffset = 0x10;
constexpr std::size_t kInternalArmyRegimentIdsOffset = 0x38;
constexpr std::size_t kInternalArmyRegimentCapacityOffset = 0x40;
constexpr std::size_t kInternalArmyRegimentCountOffset = 0x44;
constexpr std::size_t kCurrentRegimentSoldiersOffset = 0x38;
constexpr std::size_t kCurrentRegimentArmyIdOffset = 0x140;
constexpr std::size_t kPersistentRegimentCompositionRowsOffset = 0x18;
constexpr std::size_t kPersistentRegimentCompositionRowStride = 0x24;
constexpr std::size_t kPersistentRegimentRowOwnerIdOffset = 0x08;
constexpr std::size_t kPersistentRegimentRowOrdinalOffset = 0x0C;
constexpr std::size_t kPersistentRegimentRowCurrentRegimentIdOffset = 0x10;
constexpr std::size_t kPersistentRegimentBoundWarIdOffset = 0x13C;
constexpr std::size_t kPersistentRegimentWarKeepOffset = 0x142;

constexpr char kArmProof[] =
    "event_definition_key=bookmark.1071\n"
    "option_key=bookmark.1071.a\n"
    "option_index=0\n";
constexpr char kExpectedArmyName[] = "norman_highwaymen";

struct Options {
  bool self_test = false;
  DWORD attach_pid = 0;
  std::filesystem::path exe;
  std::filesystem::path userdir;
  std::filesystem::path output;
  std::filesystem::path arm_file;
  std::filesystem::path ready_file;
  DWORD timeout_ms = 180000;
};

struct CurrentRegimentCapture {
  std::int32_t generation_id = -1;
  std::int32_t current_soldiers = -1;
};

struct PersistentRegimentCapture {
  std::int32_t generation_id = -1;
  std::int32_t war_id = -1;
  std::vector<std::int32_t> current_regiment_ids;
};

struct SourceExecutionCapture {
  std::size_t sequence = 0;
  DWORD thread_id = 0;
  std::uint64_t loaded_node = 0;
  std::uint64_t created_army = 0;
  std::int32_t army_generation_id = -1;
  std::int32_t war_id = -1;
  std::int64_t initial_soldiers = -1;
  std::string evaluated_name;
  std::vector<CurrentRegimentCapture> current_regiments;
  std::vector<PersistentRegimentCapture> persistent_regiments;
};

struct CaptureResult {
  std::string result = "RED";
  std::string reason = "not-started";
  DWORD pid = 0;
  std::uint64_t image_base = 0;
  std::int32_t exact_raiktor_war_id = -1;
  std::string exe_sha256;
  std::string arm_proof_sha256;
  bool breakpoint_installed = false;
  bool original_breakpoint_byte_restored = false;
  bool process_terminated = false;
  bool attach_mode = false;
  bool debugger_detached = false;
  std::vector<SourceExecutionCapture> executions;
};

std::string Narrow(const std::wstring &value) {
  if (value.empty()) return {};
  const int size = WideCharToMultiByte(CP_UTF8, 0, value.data(),
                                       static_cast<int>(value.size()), nullptr,
                                       0, nullptr, nullptr);
  if (size <= 0) throw std::runtime_error("WideCharToMultiByte failed");
  std::string output(static_cast<std::size_t>(size), '\0');
  if (WideCharToMultiByte(CP_UTF8, 0, value.data(),
                          static_cast<int>(value.size()), output.data(), size,
                          nullptr, nullptr) != size) {
    throw std::runtime_error("WideCharToMultiByte failed");
  }
  return output;
}

std::string JsonEscape(const std::string &value) {
  std::ostringstream out;
  for (const unsigned char ch : value) {
    switch (ch) {
      case '\\': out << "\\\\"; break;
      case '"': out << "\\\""; break;
      case '\n': out << "\\n"; break;
      case '\r': out << "\\r"; break;
      case '\t': out << "\\t"; break;
      default:
        if (ch < 0x20) {
          out << "\\u" << std::hex << std::setw(4) << std::setfill('0')
              << static_cast<int>(ch) << std::dec;
        } else {
          out << ch;
        }
    }
  }
  return out.str();
}

std::string Hex(std::uint64_t value) {
  std::ostringstream out;
  out << "0x" << std::uppercase << std::hex << value;
  return out.str();
}

std::wstring Quote(const std::wstring &value) {
  std::wstring output = L"\"";
  std::size_t slashes = 0;
  for (const wchar_t ch : value) {
    if (ch == L'\\') {
      ++slashes;
      continue;
    }
    if (ch == L'\"') {
      output.append(slashes * 2 + 1, L'\\');
      output.push_back(L'\"');
      slashes = 0;
      continue;
    }
    output.append(slashes, L'\\');
    slashes = 0;
    output.push_back(ch);
  }
  output.append(slashes * 2, L'\\');
  output.push_back(L'\"');
  return output;
}

std::string Sha256(const std::filesystem::path &path) {
  BCRYPT_ALG_HANDLE algorithm = nullptr;
  BCRYPT_HASH_HANDLE hash = nullptr;
  DWORD object_size = 0;
  DWORD hash_size = 0;
  DWORD returned = 0;
  std::vector<std::uint8_t> object;
  std::vector<std::uint8_t> digest;
  auto check = [](NTSTATUS status, const char *message) {
    if (status < 0) throw std::runtime_error(message);
  };
  try {
    check(BCryptOpenAlgorithmProvider(&algorithm, BCRYPT_SHA256_ALGORITHM,
                                      nullptr, 0),
          "BCryptOpenAlgorithmProvider failed");
    check(BCryptGetProperty(algorithm, BCRYPT_OBJECT_LENGTH,
                            reinterpret_cast<PUCHAR>(&object_size),
                            sizeof(object_size), &returned, 0),
          "BCryptGetProperty object failed");
    check(BCryptGetProperty(algorithm, BCRYPT_HASH_LENGTH,
                            reinterpret_cast<PUCHAR>(&hash_size),
                            sizeof(hash_size), &returned, 0),
          "BCryptGetProperty hash failed");
    object.resize(object_size);
    digest.resize(hash_size);
    check(BCryptCreateHash(algorithm, &hash, object.data(), object_size,
                           nullptr, 0, 0),
          "BCryptCreateHash failed");
    std::ifstream input(path, std::ios::binary);
    if (!input) throw std::runtime_error("could not open hash input");
    std::vector<char> buffer(1024 * 1024);
    while (input) {
      input.read(buffer.data(), static_cast<std::streamsize>(buffer.size()));
      const auto count = input.gcount();
      if (count > 0) {
        check(BCryptHashData(hash, reinterpret_cast<PUCHAR>(buffer.data()),
                             static_cast<ULONG>(count), 0),
              "BCryptHashData failed");
      }
    }
    check(BCryptFinishHash(hash, digest.data(), hash_size, 0),
          "BCryptFinishHash failed");
  } catch (...) {
    if (hash) BCryptDestroyHash(hash);
    if (algorithm) BCryptCloseAlgorithmProvider(algorithm, 0);
    throw;
  }
  BCryptDestroyHash(hash);
  BCryptCloseAlgorithmProvider(algorithm, 0);
  std::ostringstream output;
  output << std::uppercase << std::hex << std::setfill('0');
  for (const auto byte : digest) output << std::setw(2) << int(byte);
  return output.str();
}

template <typename T>
bool ReadRemote(HANDLE process, std::uint64_t address, T *value) {
  SIZE_T read = 0;
  return ReadProcessMemory(process, reinterpret_cast<const void *>(address),
                           value, sizeof(T), &read) && read == sizeof(T);
}

bool WriteRemoteByte(HANDLE process, std::uint64_t address,
                     std::uint8_t value) {
  SIZE_T written = 0;
  return WriteProcessMemory(process, reinterpret_cast<void *>(address),
                            &value, sizeof(value), &written) &&
         written == sizeof(value) &&
         FlushInstructionCache(process, reinterpret_cast<void *>(address), 1);
}

HANDLE CreateKillOnCloseJob() {
  HANDLE job = CreateJobObjectW(nullptr, nullptr);
  if (!job) throw std::runtime_error("CreateJobObjectW failed");
  JOBOBJECT_EXTENDED_LIMIT_INFORMATION info{};
  info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
  if (!SetInformationJobObject(job, JobObjectExtendedLimitInformation, &info,
                               sizeof(info))) {
    CloseHandle(job);
    throw std::runtime_error("SetInformationJobObject failed");
  }
  return job;
}

std::string ReadMsvcString(HANDLE process, std::uint64_t object) {
  std::array<char, 16> inline_data{};
  std::uint64_t heap_data = 0;
  std::uint64_t size = 0;
  std::uint64_t capacity = 0;
  if (!ReadRemote(process, object, &inline_data) ||
      !ReadRemote(process, object, &heap_data) ||
      !ReadRemote(process, object + 0x10, &size) ||
      !ReadRemote(process, object + 0x18, &capacity) || size > 127) {
    return {};
  }
  std::string output(static_cast<std::size_t>(size), '\0');
  if (size == 0) return output;
  if (capacity < 16) {
    std::copy_n(inline_data.begin(), static_cast<std::size_t>(size),
                output.begin());
    return output;
  }
  SIZE_T read = 0;
  if (!ReadProcessMemory(process, reinterpret_cast<const void *>(heap_data),
                         output.data(), output.size(), &read) ||
      read != output.size()) {
    return {};
  }
  return output;
}

bool ReadExactArmProof(const std::filesystem::path &path,
                       std::string *sha256) {
  std::ifstream input(path, std::ios::binary);
  if (!input) return false;
  const std::string bytes((std::istreambuf_iterator<char>(input)),
                          std::istreambuf_iterator<char>());
  if (bytes != kArmProof) return false;
  *sha256 = Sha256(path);
  return true;
}

bool ResolveRemoteComponent(HANDLE process, std::uint64_t storage_slot,
                            std::int32_t generation_id,
                            std::uint64_t *component) {
  if (generation_id < 0) return false;
  std::uint64_t storage = 0;
  std::uint64_t slots = 0;
  std::int32_t capacity = 0;
  if (!ReadRemote(process, storage_slot, &storage) || storage == 0 ||
      !ReadRemote(process, storage + kComponentStorageSlotsOffset, &slots) ||
      !ReadRemote(process, storage + kComponentStorageCapacityOffset,
                  &capacity) ||
      slots == 0 || capacity < 0 || capacity > 0x01000000) {
    return false;
  }
  const auto index = static_cast<std::uint32_t>(generation_id) & 0x00FFFFFFU;
  if (index >= static_cast<std::uint32_t>(capacity)) return false;
  const auto object_slot = slots +
      static_cast<std::uint64_t>(index) * kComponentStorageSlotSize +
      kComponentStorageSlotObjectOffset;
  std::int32_t observed_id = -1;
  if (!ReadRemote(process, object_slot, component) || *component == 0 ||
      !ReadRemote(process, *component + kObjectIdOffset, &observed_id) ||
      observed_id != generation_id) {
    return false;
  }
  return true;
}

bool CaptureSourceExecution(HANDLE process, std::uint64_t image_base,
                            DWORD thread_id, const CONTEXT &context,
                            SourceExecutionCapture *output,
                            std::string *reason) {
  output->thread_id = thread_id;
  output->loaded_node = context.R14;
  output->created_army = context.Rsi;
  std::uint64_t vptr = 0;
  if (output->loaded_node == 0 || output->created_army == 0 ||
      !ReadRemote(process, output->loaded_node, &vptr) ||
      vptr != image_base + kSpawnArmyRuntimeVtableRva) {
    *reason = "armed-hit-loaded-node-identity-mismatch";
    return false;
  }
  output->evaluated_name = ReadMsvcString(process, context.Rbp + 0x70);
  if (output->evaluated_name != kExpectedArmyName) {
    *reason = "armed-hit-evaluated-name-mismatch";
    return false;
  }
  if (!ReadRemote(process, output->created_army + kObjectIdOffset,
                  &output->army_generation_id) ||
      output->army_generation_id < 0) {
    *reason = "created-army-generation-unavailable";
    return false;
  }

  std::uint64_t roster = 0;
  std::int32_t roster_capacity = 0;
  std::int32_t roster_count = 0;
  if (!ReadRemote(process,
                  output->created_army + kInternalArmyRegimentIdsOffset,
                  &roster) ||
      !ReadRemote(process,
                  output->created_army + kInternalArmyRegimentCapacityOffset,
                  &roster_capacity) ||
      !ReadRemote(process,
                  output->created_army + kInternalArmyRegimentCountOffset,
                  &roster_count) ||
      roster == 0 || roster_count < 1 || roster_capacity < roster_count ||
      roster_count > static_cast<std::int32_t>(kMaximumCurrentRegimentsPerArmy)) {
    *reason = "created-army-roster-invalid";
    return false;
  }
  std::set<std::int32_t> roster_ids;
  std::int64_t initial_soldiers = 0;
  for (std::int32_t index = 0; index < roster_count; ++index) {
    std::int32_t regiment_id = -1;
    if (!ReadRemote(process,
                    roster + static_cast<std::uint64_t>(index) *
                                 sizeof(regiment_id),
                    &regiment_id) || !roster_ids.insert(regiment_id).second) {
      *reason = "created-army-roster-generation-invalid";
      return false;
    }
    std::uint64_t regiment = 0;
    std::int32_t backlink = -1;
    std::int32_t soldiers = -1;
    if (!ResolveRemoteComponent(
            process, image_base + kCurrentRegimentStorageSlotRva,
            regiment_id, &regiment) ||
        !ReadRemote(process, regiment + kCurrentRegimentArmyIdOffset,
                    &backlink) ||
        !ReadRemote(process, regiment + kCurrentRegimentSoldiersOffset,
                    &soldiers) ||
        backlink != output->army_generation_id || soldiers < 0 ||
        initial_soldiers >
            std::numeric_limits<std::int64_t>::max() - soldiers) {
      *reason = "created-army-current-regiment-invalid";
      return false;
    }
    output->current_regiments.push_back({regiment_id, soldiers});
    initial_soldiers += soldiers;
  }
  output->initial_soldiers = initial_soldiers;

  std::uint64_t persistent_vector = 0;
  std::int32_t persistent_count = 0;
  if (!ReadRemote(process, context.Rsp + 0x60, &persistent_vector) ||
      !ReadRemote(process, context.Rsp + 0x6C, &persistent_count) ||
      persistent_vector == 0 || persistent_count < 1 ||
      persistent_count >
          static_cast<std::int32_t>(kMaximumPersistentRegimentsPerExecution)) {
    *reason = "persistent-regiment-vector-invalid";
    return false;
  }
  std::set<std::int32_t> persistent_ids;
  std::set<std::int32_t> persistent_current_ids;
  for (std::int32_t index = 0; index < persistent_count; ++index) {
    std::uint64_t persistent = 0;
    PersistentRegimentCapture captured{};
    std::uint8_t keep = 0xFF;
    if (!ReadRemote(process,
                    persistent_vector + static_cast<std::uint64_t>(index) *
                                            sizeof(persistent),
                    &persistent) || persistent == 0 ||
        !ReadRemote(process, persistent + kObjectIdOffset,
                    &captured.generation_id) ||
        !ReadRemote(process, persistent + kPersistentRegimentBoundWarIdOffset,
                    &captured.war_id) ||
        !ReadRemote(process, persistent + kPersistentRegimentWarKeepOffset,
                    &keep) || captured.generation_id < 0 ||
        captured.war_id < 0 || keep != 0 ||
        !persistent_ids.insert(captured.generation_id).second) {
      *reason = "persistent-regiment-identity-invalid";
      return false;
    }
    if (output->war_id == -1) output->war_id = captured.war_id;
    if (captured.war_id != output->war_id) {
      *reason = "persistent-regiment-war-id-mismatch";
      return false;
    }
    for (std::size_t row_index = 0; row_index < kCompositionRowCount;
         ++row_index) {
      const auto row = persistent + kPersistentRegimentCompositionRowsOffset +
                       row_index * kPersistentRegimentCompositionRowStride;
      std::int32_t owner_id = -1;
      std::int32_t ordinal = -1;
      std::int32_t current_id = -1;
      if (!ReadRemote(process, row + kPersistentRegimentRowOwnerIdOffset,
                      &owner_id) ||
          !ReadRemote(process, row + kPersistentRegimentRowOrdinalOffset,
                      &ordinal) ||
          !ReadRemote(process,
                      row + kPersistentRegimentRowCurrentRegimentIdOffset,
                      &current_id) || owner_id != captured.generation_id ||
          ordinal != static_cast<std::int32_t>(row_index)) {
        *reason = "persistent-regiment-composition-identity-invalid";
        return false;
      }
      if (current_id != -1) {
        captured.current_regiment_ids.push_back(current_id);
        persistent_current_ids.insert(current_id);
      }
    }
    output->persistent_regiments.push_back(std::move(captured));
  }
  if (persistent_current_ids != roster_ids) {
    *reason = "persistent-to-current-roster-mismatch";
    return false;
  }
  return true;
}

std::filesystem::path QueryProcessImagePath(HANDLE process) {
  std::vector<wchar_t> buffer(32768, L'\0');
  DWORD size = static_cast<DWORD>(buffer.size());
  if (!QueryFullProcessImageNameW(process, 0, buffer.data(), &size) ||
      size == 0) {
    throw std::runtime_error("QueryFullProcessImageNameW failed");
  }
  return std::filesystem::path(std::wstring(buffer.data(), size));
}

void WriteReadyFile(const Options &options, const CaptureResult &capture) {
  if (options.ready_file.empty()) return;
  if (!options.ready_file.parent_path().empty()) {
    std::filesystem::create_directories(options.ready_file.parent_path());
  }
  std::ofstream output(options.ready_file, std::ios::binary | std::ios::trunc);
  if (!output) throw std::runtime_error("could not open attach ready file");
  output << "{\n"
         << "  \"schema\": \"raiktor-war-bound-private-attach-ready-v1\",\n"
         << "  \"attach_mode\": true,\n"
         << "  \"pid\": " << capture.pid << ",\n"
         << "  \"exe_sha256\": \"" << capture.exe_sha256 << "\",\n"
         << "  \"image_base\": \"" << Hex(capture.image_base) << "\",\n"
         << "  \"observation_stop_rva\": \"" << Hex(kObservationStopRva)
         << "\",\n"
         << "  \"breakpoint_installed\": true\n"
         << "}\n";
}

void WriteManifest(const Options &options, const CaptureResult &capture) {
  std::ofstream output(options.output, std::ios::binary | std::ios::trunc);
  if (!output) throw std::runtime_error("could not open output manifest");
  output << "{\n"
         << "  \"schema\": \"raiktor-war-bound-private-capture-v1\",\n"
         << "  \"status\": \"private_test_only\",\n"
         << "  \"result\": \"" << JsonEscape(capture.result) << "\",\n"
         << "  \"reason\": \"" << JsonEscape(capture.reason) << "\",\n"
         << "  \"read_only\": true,\n"
         << "  \"public_bridge_abi_changed\": false,\n"
         << "  \"production_detour_installed\": false,\n"
         << "  \"readiness_promotion\": false,\n"
         << "  \"pid\": " << capture.pid << ",\n"
         << "  \"image_base\": \"" << Hex(capture.image_base) << "\",\n"
         << "  \"observation_stop_rva\": \"" << Hex(kObservationStopRva)
         << "\",\n"
         << "  \"observation_window_end_rva_exclusive\": \""
         << Hex(kObservationWindowEndRva) << "\",\n"
         << "  \"exe_sha256\": \"" << capture.exe_sha256 << "\",\n"
         << "  \"arm_proof_sha256\": \"" << capture.arm_proof_sha256
         << "\",\n"
         << "  \"event_definition_key\": \"bookmark.1071\",\n"
         << "  \"option_key\": \"bookmark.1071.a\",\n"
         << "  \"option_index\": 0,\n"
         << "  \"exact_raiktor_war_id\": "
         << capture.exact_raiktor_war_id << ",\n"
         << "  \"source_execution_count\": " << capture.executions.size()
         << ",\n"
         << "  \"breakpoint_installed\": "
         << (capture.breakpoint_installed ? "true" : "false") << ",\n"
         << "  \"original_breakpoint_byte_restored\": "
         << (capture.original_breakpoint_byte_restored ? "true" : "false")
         << ",\n"
         << "  \"process_terminated\": "
         << (capture.process_terminated ? "true" : "false") << ",\n"
         << "  \"attach_mode\": "
         << (capture.attach_mode ? "true" : "false") << ",\n"
         << "  \"debugger_detached\": "
         << (capture.debugger_detached ? "true" : "false") << ",\n"
         << "  \"executions\": [\n";
  for (std::size_t i = 0; i < capture.executions.size(); ++i) {
    const auto &row = capture.executions[i];
    output << "    {\"sequence\": " << row.sequence
           << ", \"thread_id\": " << row.thread_id
           << ", \"loaded_node\": \"" << Hex(row.loaded_node)
           << "\", \"created_army\": \"" << Hex(row.created_army)
           << "\", \"army_generation_id\": " << row.army_generation_id
           << ", \"war_id\": " << row.war_id
           << ", \"initial_soldiers\": " << row.initial_soldiers
           << ", \"evaluated_name\": \""
           << JsonEscape(row.evaluated_name) << "\", \"current_regiments\": [";
    for (std::size_t j = 0; j < row.current_regiments.size(); ++j) {
      if (j) output << ", ";
      output << "{\"generation_id\": "
             << row.current_regiments[j].generation_id
             << ", \"current_soldiers\": "
             << row.current_regiments[j].current_soldiers << "}";
    }
    output << "], \"persistent_regiments\": [";
    for (std::size_t j = 0; j < row.persistent_regiments.size(); ++j) {
      if (j) output << ", ";
      const auto &persistent = row.persistent_regiments[j];
      output << "{\"generation_id\": " << persistent.generation_id
             << ", \"war_id\": " << persistent.war_id
             << ", \"current_regiment_ids\": [";
      for (std::size_t k = 0; k < persistent.current_regiment_ids.size(); ++k) {
        if (k) output << ", ";
        output << persistent.current_regiment_ids[k];
      }
      output << "]}";
    }
    output << "]}" << (i + 1 == capture.executions.size() ? "\n" : ",\n");
  }
  output << "  ]\n}\n";
}

Options ParseOptions(int argc, wchar_t **argv) {
  Options options{};
  for (int i = 1; i < argc; ++i) {
    const std::wstring name = argv[i];
    auto value = [&]() -> std::wstring {
      if (++i >= argc) throw std::runtime_error("missing option value");
      return argv[i];
    };
    if (name == L"--self-test") options.self_test = true;
    else if (name == L"--attach-pid") {
      const auto parsed = std::stoul(value());
      if (parsed == 0 || parsed > MAXDWORD) {
        throw std::runtime_error("attach PID out of range");
      }
      options.attach_pid = static_cast<DWORD>(parsed);
    }
    else if (name == L"--exe") options.exe = value();
    else if (name == L"--userdir") options.userdir = value();
    else if (name == L"--output") options.output = value();
    else if (name == L"--arm-file") options.arm_file = value();
    else if (name == L"--ready-file") options.ready_file = value();
    else if (name == L"--timeout-ms") {
      const auto parsed = std::stoul(value());
      if (parsed < 1000 || parsed > 1200000) {
        throw std::runtime_error("timeout out of range");
      }
      options.timeout_ms = static_cast<DWORD>(parsed);
    } else {
      throw std::runtime_error("unknown option: " + Narrow(name));
    }
  }
  if (!options.self_test &&
      (options.exe.empty() || options.output.empty() ||
       options.arm_file.empty() || options.ready_file.empty() ||
       (options.attach_pid == 0 && options.userdir.empty()))) {
    throw std::runtime_error(
        "required: --exe --output --arm-file --ready-file and either "
        "--attach-pid or --userdir");
  }
  return options;
}

bool ValidateSixExecutions(const std::vector<SourceExecutionCapture> &rows,
                           std::string *reason) {
  if (rows.size() != kExpectedSourceExecutions) {
    *reason = "source-execution-count-not-six";
    return false;
  }
  std::set<std::uint64_t> nodes;
  std::set<std::int32_t> armies;
  const auto war_id = rows.front().war_id;
  if (war_id < 0) {
    *reason = "exact-raiktor-war-id-invalid";
    return false;
  }
  for (const auto &row : rows) {
    if (row.war_id != war_id || row.army_generation_id < 0 ||
        row.initial_soldiers < 0 || row.evaluated_name != kExpectedArmyName ||
        !nodes.insert(row.loaded_node).second ||
        !armies.insert(row.army_generation_id).second) {
      *reason = "six-execution-identity-mismatch";
      return false;
    }
  }
  return true;
}

int SelfTest() {
  std::vector<SourceExecutionCapture> rows;
  for (std::size_t index = 0; index < kExpectedSourceExecutions; ++index) {
    SourceExecutionCapture row{};
    row.sequence = index + 1;
    row.loaded_node = 0x1000 + index * 0x100;
    row.army_generation_id = 0x01000020 + static_cast<std::int32_t>(index);
    row.war_id = 0x02000042;
    row.initial_soldiers = 500;
    row.evaluated_name = kExpectedArmyName;
    rows.push_back(row);
  }
  std::string reason;
  if (!ValidateSixExecutions(rows, &reason)) return 1;
  rows[5].war_id = 0x03000042;
  if (ValidateSixExecutions(rows, &reason) ||
      reason != "six-execution-identity-mismatch") return 2;
  rows[5].war_id = rows[0].war_id;
  rows[5].loaded_node = rows[0].loaded_node;
  if (ValidateSixExecutions(rows, &reason)) return 3;
  std::cout << "PASS: private=1 action_arm=1 loaded_nodes=6 exact_war_id=1 "
               "public_abi=0 readiness=0\n";
  return 0;
}

int Run(const Options &options) {
  CaptureResult capture{};
  capture.attach_mode = options.attach_pid != 0;
  const auto absolute_exe = std::filesystem::absolute(options.exe);
  if (std::filesystem::file_size(absolute_exe) != kExpectedExeSize) {
    throw std::runtime_error("CK3 executable size mismatch");
  }
  capture.exe_sha256 = Sha256(absolute_exe);
  if (capture.exe_sha256 != Narrow(kExpectedExeSha256)) {
    throw std::runtime_error("CK3 executable hash mismatch");
  }

  if (!capture.attach_mode) {
    std::filesystem::create_directories(options.userdir);
  }
  if (!options.output.parent_path().empty()) {
    std::filesystem::create_directories(options.output.parent_path());
  }
  HANDLE job = nullptr;
  PROCESS_INFORMATION process_info{};
  if (capture.attach_mode) {
    process_info.dwProcessId = options.attach_pid;
    process_info.hProcess = OpenProcess(
        PROCESS_QUERY_INFORMATION | PROCESS_VM_READ | PROCESS_VM_WRITE |
            PROCESS_VM_OPERATION | SYNCHRONIZE,
        FALSE, options.attach_pid);
    if (!process_info.hProcess) {
      throw std::runtime_error("OpenProcess for attach failed");
    }
    const auto observed_exe = QueryProcessImagePath(process_info.hProcess);
    if (!std::filesystem::equivalent(observed_exe, absolute_exe)) {
      CloseHandle(process_info.hProcess);
      throw std::runtime_error("attached PID executable path mismatch");
    }
    if (!DebugActiveProcess(options.attach_pid)) {
      CloseHandle(process_info.hProcess);
      throw std::runtime_error("DebugActiveProcess failed");
    }
    if (!DebugSetProcessKillOnExit(FALSE)) {
      DebugActiveProcessStop(options.attach_pid);
      CloseHandle(process_info.hProcess);
      throw std::runtime_error("DebugSetProcessKillOnExit failed");
    }
  } else {
    job = CreateKillOnCloseJob();
    std::wstring command =
        Quote(absolute_exe.wstring()) + L" -debug_mode -userdir=" +
        Quote(std::filesystem::absolute(options.userdir).wstring());
    std::vector<wchar_t> mutable_command(command.begin(), command.end());
    mutable_command.push_back(L'\0');
    STARTUPINFOW startup{};
    startup.cb = sizeof(startup);
    if (!CreateProcessW(absolute_exe.c_str(), mutable_command.data(), nullptr,
                        nullptr, FALSE,
                        DEBUG_ONLY_THIS_PROCESS | CREATE_NEW_PROCESS_GROUP,
                        nullptr, absolute_exe.parent_path().c_str(), &startup,
                        &process_info)) {
      CloseHandle(job);
      throw std::runtime_error("CreateProcessW failed");
    }
    if (!AssignProcessToJobObject(job, process_info.hProcess)) {
      TerminateProcess(process_info.hProcess, 1);
      CloseHandle(process_info.hThread);
      CloseHandle(process_info.hProcess);
      CloseHandle(job);
      throw std::runtime_error("AssignProcessToJobObject failed");
    }
    CloseHandle(process_info.hThread);
  }
  capture.pid = process_info.dwProcessId;

  const auto start = std::chrono::steady_clock::now();
  std::uint64_t breakpoint = 0;
  DWORD stepping_thread = 0;
  bool breakpoint_live = false;
  bool done = false;
  bool process_exited = false;
  bool initial_breakpoint_seen = false;
  std::set<std::uint64_t> loaded_nodes;
  while (!done && !process_exited) {
    const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::steady_clock::now() - start);
    if (elapsed.count() >= options.timeout_ms) {
      capture.reason = "timeout-before-six-source-executions";
      break;
    }
    DEBUG_EVENT event{};
    if (!WaitForDebugEvent(&event, 100)) continue;
    DWORD disposition = DBG_CONTINUE;
    if (event.dwDebugEventCode == CREATE_PROCESS_DEBUG_EVENT) {
      capture.image_base = reinterpret_cast<std::uint64_t>(
          event.u.CreateProcessInfo.lpBaseOfImage);
      breakpoint = capture.image_base + kObservationStopRva;
      std::uint8_t original = 0;
      if (!ReadRemote(process_info.hProcess, breakpoint, &original) ||
          original != kObservationStopByte ||
          !WriteRemoteByte(process_info.hProcess, breakpoint, 0xCC)) {
        capture.reason = "observation-breakpoint-install-failed";
        done = true;
      } else {
        capture.breakpoint_installed = true;
        breakpoint_live = true;
        try {
          WriteReadyFile(options, capture);
        } catch (const std::exception &) {
          capture.reason = "attach-ready-file-write-failed";
          done = true;
        }
      }
      if (event.u.CreateProcessInfo.hFile) {
        CloseHandle(event.u.CreateProcessInfo.hFile);
      }
    } else if (event.dwDebugEventCode == LOAD_DLL_DEBUG_EVENT) {
      if (event.u.LoadDll.hFile) CloseHandle(event.u.LoadDll.hFile);
    } else if (event.dwDebugEventCode == CREATE_THREAD_DEBUG_EVENT) {
      if (event.u.CreateThread.hThread) CloseHandle(event.u.CreateThread.hThread);
    } else if (event.dwDebugEventCode == EXIT_PROCESS_DEBUG_EVENT) {
      process_exited = true;
      capture.reason = "process-exited-before-six-source-executions";
    } else if (event.dwDebugEventCode == EXCEPTION_DEBUG_EVENT) {
      const auto code = event.u.Exception.ExceptionRecord.ExceptionCode;
      const auto address = reinterpret_cast<std::uint64_t>(
          event.u.Exception.ExceptionRecord.ExceptionAddress);
      if (code == EXCEPTION_BREAKPOINT && address == breakpoint) {
        HANDLE thread = OpenThread(THREAD_GET_CONTEXT | THREAD_SET_CONTEXT,
                                   FALSE, event.dwThreadId);
        CONTEXT context{};
        context.ContextFlags = CONTEXT_CONTROL | CONTEXT_INTEGER;
        if (!thread || !GetThreadContext(thread, &context) ||
            !WriteRemoteByte(process_info.hProcess, breakpoint,
                             kObservationStopByte)) {
          if (thread) CloseHandle(thread);
          capture.reason = "observation-breakpoint-restore-failed";
          done = true;
        } else {
          breakpoint_live = false;
          capture.original_breakpoint_byte_restored = true;
          context.Rip = breakpoint;
          context.EFlags |= 0x100U;
          if (!SetThreadContext(thread, &context)) {
            capture.reason = "observation-single-step-arm-failed";
            done = true;
          } else {
            stepping_thread = event.dwThreadId;
            std::string proof_sha;
            if (ReadExactArmProof(options.arm_file, &proof_sha)) {
              capture.arm_proof_sha256 = proof_sha;
              SourceExecutionCapture row{};
              row.sequence = capture.executions.size() + 1;
              std::string reason;
              if (!CaptureSourceExecution(process_info.hProcess,
                                          capture.image_base, event.dwThreadId,
                                          context, &row, &reason) ||
                  !loaded_nodes.insert(row.loaded_node).second) {
                capture.reason = reason.empty()
                                     ? "duplicate-loaded-source-node"
                                     : reason;
                done = true;
              } else if (capture.exact_raiktor_war_id != -1 &&
                         row.war_id != capture.exact_raiktor_war_id) {
                capture.reason = "exact-raiktor-war-id-mismatch";
                done = true;
              } else {
                if (capture.exact_raiktor_war_id == -1) {
                  capture.exact_raiktor_war_id = row.war_id;
                }
                capture.executions.push_back(std::move(row));
              }
            }
          }
          CloseHandle(thread);
        }
      } else if (code == EXCEPTION_SINGLE_STEP &&
                 event.dwThreadId == stepping_thread) {
        stepping_thread = 0;
        if (!done && capture.executions.size() < kExpectedSourceExecutions) {
          if (!WriteRemoteByte(process_info.hProcess, breakpoint, 0xCC)) {
            capture.reason = "observation-breakpoint-reinstall-failed";
            done = true;
          } else {
            breakpoint_live = true;
          }
        } else if (capture.executions.size() == kExpectedSourceExecutions) {
          std::string reason;
          if (ValidateSixExecutions(capture.executions, &reason)) {
            capture.result = "GREEN";
            capture.reason = "six-action-bound-source-executions-captured";
          } else {
            capture.reason = reason;
          }
          done = true;
        }
      } else if (code == EXCEPTION_BREAKPOINT && !initial_breakpoint_seen) {
        initial_breakpoint_seen = true;
      } else if (code == EXCEPTION_BREAKPOINT) {
        disposition = DBG_EXCEPTION_NOT_HANDLED;
      } else {
        disposition = DBG_EXCEPTION_NOT_HANDLED;
      }
    }
    ContinueDebugEvent(event.dwProcessId, event.dwThreadId, disposition);
  }

  if (breakpoint_live) {
    capture.original_breakpoint_byte_restored = WriteRemoteByte(
        process_info.hProcess, breakpoint, kObservationStopByte);
  }
  if (!process_exited && capture.attach_mode) {
    capture.debugger_detached =
        DebugActiveProcessStop(process_info.dwProcessId) != FALSE;
    if (!capture.debugger_detached) {
      capture.result = "RED";
      capture.reason = "debugger-detach-failed";
    }
  } else if (!process_exited) {
    capture.process_terminated = TerminateProcess(
        process_info.hProcess, capture.result == "GREEN" ? 0 : 1) != FALSE;
    WaitForSingleObject(process_info.hProcess, 10000);
  } else {
    capture.process_terminated = true;
  }
  CloseHandle(process_info.hProcess);
  if (job) CloseHandle(job);
  WriteManifest(options, capture);
  return capture.result == "GREEN" ? 0 : 1;
}

}  // namespace

int wmain(int argc, wchar_t **argv) {
  try {
    const auto options = ParseOptions(argc, argv);
    if (options.self_test) return SelfTest();
    return Run(options);
  } catch (const std::exception &error) {
    std::cerr << "ERROR: " << error.what() << "\n";
    return 2;
  }
}
