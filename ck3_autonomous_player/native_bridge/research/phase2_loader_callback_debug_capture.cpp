// Private exact-build debugger probe for the phase-two loader callback.
//
// This executable is deliberately not linked into xar_ck3_bridge.dll and does
// not change the public bridge ABI.  It launches one isolated CK3 process as a
// Windows debugger, places a one-shot breakpoint on the already-frozen
// callback call instruction, captures the paused register/vtable identity,
// restores the original byte, and terminates the isolated process.

#define NOMINMAX
#include <windows.h>
#include <bcrypt.h>

#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

#pragma comment(lib, "bcrypt.lib")

namespace {

constexpr std::uint64_t kCallbackCallRva = 0x3B9AB90;
constexpr std::uint64_t kCallbackContinuationRva = 0x3B9AB93;
constexpr std::uint64_t kNodeLoadedStopRva = 0x3B9AB53;
constexpr std::uint64_t kLoopExitRva = 0x3B9ACC4;
constexpr std::uint64_t kCallbackSlotTargetRva = 0x3B9BA70;
constexpr std::uint64_t kObservedRuntimeVtableRva = 0x408A450;
constexpr std::uint64_t kObservedRuntimeSlotTargetRva = 0x947BD0;
constexpr std::array<std::uint64_t, 2> kCandidateVtableRvas = {
    0x4558700,
    0x4558770,
};
constexpr std::array<std::uint8_t, 3> kCallbackBytes = {0xFF, 0x50, 0x10};
constexpr std::uint8_t kNodeLoadedStopByte = 0x48;
constexpr std::uint8_t kLoopExitByte = 0x4C;
constexpr std::uint64_t kExpectedExeSize = 95206008;
constexpr wchar_t kExpectedExeSha256[] =
    L"2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";

struct Options {
  std::filesystem::path exe;
  std::filesystem::path userdir;
  std::filesystem::path output;
  DWORD timeout_ms = 45000;
  bool sequence = false;
  bool next_node = false;
};

struct SequenceEntry {
  std::size_t sequence = 0;
  DWORD entry_thread_id = 0;
  DWORD return_thread_id = 0;
  std::uint64_t node = 0;
  std::string node_name;
  std::uint64_t receiver = 0;
  std::uint64_t wrapper_vptr = 0;
  std::uint64_t wrapper_slot_2_target = 0;
  std::uint64_t concrete_callback = 0;
  std::uint64_t global_pointer_rva = 0;
  std::uint64_t global_object = 0;
  std::uint64_t global_vptr = 0;
  std::uint64_t global_slot_2_target = 0;
  bool trampoline_decoded = false;
  bool returned = false;
  bool same_thread = false;
  bool receiver_survived = false;
  bool wrapper_vptr_survived = false;
  bool concrete_callback_survived = false;
  double entry_elapsed_seconds = 0.0;
  double return_elapsed_seconds = 0.0;
};

struct NextNodeTransition {
  std::size_t callback_sequence = 0;
  DWORD callback_return_thread_id = 0;
  DWORD transition_thread_id = 0;
  std::string outcome;
  std::uint64_t node = 0;
  std::string node_name;
  std::uint64_t receiver = 0;
  bool receiver_is_null = false;
  bool same_thread = false;
  double elapsed_seconds = 0.0;
};

struct Capture {
  bool breakpoint_installed = false;
  bool callback_observed = false;
  bool return_breakpoint_installed = false;
  bool callback_return_observed = false;
  bool original_byte_restored = false;
  bool continuation_byte_restored = false;
  bool process_terminated = false;
  DWORD pid = 0;
  DWORD thread_id = 0;
  DWORD return_thread_id = 0;
  std::uint64_t image_base = 0;
  std::uint64_t callback_address = 0;
  std::uint64_t node = 0;
  std::uint64_t receiver = 0;
  std::uint64_t receiver_from_node = 0;
  std::uint64_t vptr = 0;
  std::uint64_t slot_target = 0;
  std::uint64_t callback_function = 0;
  std::uint64_t post_receiver_from_node = 0;
  std::uint64_t post_vptr = 0;
  std::uint64_t post_callback_function = 0;
  std::uint64_t vptr_rva = 0;
  std::uint64_t slot_target_rva = 0;
  bool receiver_matches_node = false;
  bool vptr_matches_candidate = false;
  bool slot_target_matches = false;
  bool vptr_matches_runtime_owner = false;
  bool slot_target_matches_runtime_owner = false;
  bool return_thread_matches = false;
  bool receiver_survived_return = false;
  bool vptr_survived_return = false;
  bool callback_function_survived_return = false;
  std::string result = "RED";
  std::string reason = "not-started";
  std::string exe_sha256;
  double elapsed_seconds = 0.0;
  std::vector<SequenceEntry> sequence_entries;
  std::uint64_t timeout_thread_rip = 0;
  std::uint64_t timeout_thread_rva = 0;
  std::uint64_t timeout_node = 0;
  std::string timeout_node_name;
  std::uint64_t timeout_receiver = 0;
  DWORD timeout_thread_id = 0;
  bool timeout_thread_suspended = false;
  std::vector<NextNodeTransition> next_node_transitions;
  std::size_t awaiting_transition_sequence = 0;
  DWORD awaiting_transition_thread_id = 0;
  bool node_breakpoint_installed = false;
  bool node_breakpoint_byte_restored = false;
  bool loop_exit_breakpoint_installed = false;
  bool loop_exit_breakpoint_byte_restored = false;
};

std::string Narrow(const std::wstring& value) {
  if (value.empty()) return {};
  const int size = WideCharToMultiByte(CP_UTF8, 0, value.data(),
                                       static_cast<int>(value.size()), nullptr,
                                       0, nullptr, nullptr);
  if (size <= 0) throw std::runtime_error("WideCharToMultiByte failed");
  std::string result(static_cast<std::size_t>(size), '\0');
  if (WideCharToMultiByte(CP_UTF8, 0, value.data(),
                          static_cast<int>(value.size()), result.data(), size,
                          nullptr, nullptr) != size) {
    throw std::runtime_error("WideCharToMultiByte failed");
  }
  return result;
}

std::string JsonEscape(const std::string& value) {
  std::ostringstream out;
  for (const unsigned char ch : value) {
    switch (ch) {
      case '\\': out << "\\\\"; break;
      case '"': out << "\\\""; break;
      case '\b': out << "\\b"; break;
      case '\f': out << "\\f"; break;
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

std::wstring Quote(const std::wstring& value) {
  std::wstring quoted = L"\"";
  std::size_t slashes = 0;
  for (const wchar_t ch : value) {
    if (ch == L'\\') {
      ++slashes;
      continue;
    }
    if (ch == L'"') {
      quoted.append(slashes * 2 + 1, L'\\');
      quoted.push_back(L'"');
      slashes = 0;
      continue;
    }
    quoted.append(slashes, L'\\');
    slashes = 0;
    quoted.push_back(ch);
  }
  quoted.append(slashes * 2, L'\\');
  quoted.push_back(L'"');
  return quoted;
}

std::string Sha256(const std::filesystem::path& path) {
  BCRYPT_ALG_HANDLE algorithm = nullptr;
  BCRYPT_HASH_HANDLE hash = nullptr;
  DWORD object_size = 0;
  DWORD hash_size = 0;
  DWORD result_size = 0;
  std::vector<std::uint8_t> object;
  std::vector<std::uint8_t> digest;
  auto check = [](NTSTATUS status, const char* operation) {
    if (status < 0) throw std::runtime_error(operation);
  };
  try {
    check(BCryptOpenAlgorithmProvider(&algorithm, BCRYPT_SHA256_ALGORITHM,
                                      nullptr, 0),
          "BCryptOpenAlgorithmProvider failed");
    check(BCryptGetProperty(algorithm, BCRYPT_OBJECT_LENGTH,
                            reinterpret_cast<PUCHAR>(&object_size),
                            sizeof(object_size), &result_size, 0),
          "BCryptGetProperty(object length) failed");
    check(BCryptGetProperty(algorithm, BCRYPT_HASH_LENGTH,
                            reinterpret_cast<PUCHAR>(&hash_size),
                            sizeof(hash_size), &result_size, 0),
          "BCryptGetProperty(hash length) failed");
    object.resize(object_size);
    digest.resize(hash_size);
    check(BCryptCreateHash(algorithm, &hash, object.data(), object_size,
                           nullptr, 0, 0),
          "BCryptCreateHash failed");
    std::ifstream input(path, std::ios::binary);
    if (!input) throw std::runtime_error("could not open executable for hash");
    // Keep the 1 MiB streaming buffer off the default 1 MiB Windows stack.
    std::vector<char> buffer(1024 * 1024);
    while (input) {
      input.read(buffer.data(), static_cast<std::streamsize>(buffer.size()));
      const auto count = input.gcount();
      if (count > 0) {
        check(BCryptHashData(
                  hash, reinterpret_cast<PUCHAR>(buffer.data()),
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
  std::ostringstream out;
  out << std::uppercase << std::hex << std::setfill('0');
  for (const auto value : digest) out << std::setw(2) << int(value);
  return out.str();
}

template <typename T>
bool ReadRemote(HANDLE process, std::uint64_t address, T* value) {
  SIZE_T read = 0;
  return ReadProcessMemory(process, reinterpret_cast<const void*>(address),
                           value, sizeof(T), &read) && read == sizeof(T);
}

std::string ReadRemoteCString(HANDLE process, std::uint64_t address,
                              std::size_t limit = 192) {
  if (address == 0 || limit == 0) return {};
  std::vector<char> buffer(limit, '\0');
  SIZE_T read = 0;
  if (!ReadProcessMemory(process, reinterpret_cast<const void*>(address),
                         buffer.data(), buffer.size(), &read) || read == 0) {
    return {};
  }
  const auto end = std::find(buffer.begin(), buffer.begin() + read, '\0');
  return std::string(buffer.begin(), end);
}

std::string ReadNodeName(HANDLE process, std::uint64_t node) {
  std::uint64_t name_pointer = 0;
  if (!ReadRemote(process, node + 0x08, &name_pointer)) return {};
  return ReadRemoteCString(process, name_pointer);
}

void DecodeConcreteTrampoline(HANDLE process, std::uint64_t image_base,
                              SequenceEntry* entry) {
  if (entry->concrete_callback < image_base) return;
  const std::uint64_t callback_rva = entry->concrete_callback - image_base;
  std::array<std::uint8_t, 14> code{};
  SIZE_T read = 0;
  if (!ReadProcessMemory(process,
                         reinterpret_cast<const void*>(entry->concrete_callback),
                         code.data(), code.size(), &read) ||
      read != code.size()) {
    return;
  }
  if (code[0] != 0x48 || code[1] != 0x8B || code[2] != 0x0D ||
      code[7] != 0x48 || code[8] != 0x8B || code[9] != 0x01 ||
      code[10] != 0x48 || code[11] != 0xFF || code[12] != 0x60 ||
      code[13] != 0x10) {
    return;
  }
  std::int32_t displacement = 0;
  std::memcpy(&displacement, code.data() + 3, sizeof(displacement));
  entry->global_pointer_rva = callback_rva + 7 + displacement;
  const std::uint64_t global_pointer_address =
      image_base + entry->global_pointer_rva;
  if (!ReadRemote(process, global_pointer_address, &entry->global_object) ||
      entry->global_object == 0 ||
      !ReadRemote(process, entry->global_object, &entry->global_vptr) ||
      entry->global_vptr == 0 ||
      !ReadRemote(process, entry->global_vptr + 0x10,
                  &entry->global_slot_2_target)) {
    return;
  }
  entry->trampoline_decoded = true;
}

bool WriteBreakpointByte(HANDLE process, std::uint64_t address,
                         std::uint8_t value) {
  DWORD old_protection = 0;
  if (!VirtualProtectEx(process, reinterpret_cast<void*>(address), 1,
                        PAGE_EXECUTE_READWRITE, &old_protection)) {
    return false;
  }
  SIZE_T written = 0;
  const bool wrote =
      WriteProcessMemory(process, reinterpret_cast<void*>(address), &value, 1,
                         &written) &&
      written == 1 &&
      FlushInstructionCache(process, reinterpret_cast<void*>(address), 1);
  DWORD ignored = 0;
  const bool restored =
      VirtualProtectEx(process, reinterpret_cast<void*>(address), 1,
                       old_protection, &ignored) != FALSE;
  return wrote && restored;
}

bool ResetThreadInstructionPointer(DWORD thread_id, std::uint64_t address) {
  HANDLE thread = OpenThread(THREAD_GET_CONTEXT | THREAD_SET_CONTEXT |
                                 THREAD_QUERY_INFORMATION,
                             FALSE, thread_id);
  if (!thread) return false;
  CONTEXT context{};
  context.ContextFlags = CONTEXT_CONTROL;
  const bool context_ok = GetThreadContext(thread, &context) != FALSE;
  context.Rip = address;
  const bool context_set =
      context_ok && SetThreadContext(thread, &context) != FALSE;
  CloseHandle(thread);
  return context_set;
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

Options ParseOptions(int argc, wchar_t** argv) {
  Options options;
  for (int index = 1; index < argc; ++index) {
    const std::wstring name = argv[index];
    auto next = [&]() -> std::wstring {
      if (++index >= argc) throw std::runtime_error("missing option value");
      return argv[index];
    };
    if (name == L"--exe") options.exe = next();
    else if (name == L"--userdir") options.userdir = next();
    else if (name == L"--output") options.output = next();
    else if (name == L"--timeout-ms") options.timeout_ms = std::stoul(next());
    else if (name == L"--sequence") options.sequence = true;
    else if (name == L"--next-node") {
      options.next_node = true;
      options.sequence = true;
    }
    else throw std::runtime_error("unknown option: " + Narrow(name));
  }
  if (options.exe.empty() || options.userdir.empty() || options.output.empty()) {
    throw std::runtime_error("--exe, --userdir, and --output are required");
  }
  if (options.timeout_ms < 1000 || options.timeout_ms > 60000) {
    throw std::runtime_error("--timeout-ms must be within [1000,60000]");
  }
  return options;
}

void WriteReport(const Options& options, const Capture& capture) {
  std::ofstream output(options.output, std::ios::binary | std::ios::trunc);
  if (!output) throw std::runtime_error("could not create output artifact");
  std::size_t last_successful_sequence = 0;
  std::size_t first_unreturned_sequence = 0;
  for (const auto& row : capture.sequence_entries) {
    if (row.returned) {
      last_successful_sequence = row.sequence;
    } else if (first_unreturned_sequence == 0) {
      first_unreturned_sequence = row.sequence;
    }
  }
  const NextNodeTransition* last_successful_transition = nullptr;
  for (const auto& row : capture.next_node_transitions) {
    if (row.callback_sequence == last_successful_sequence) {
      last_successful_transition = &row;
    }
  }
  output << "{\n"
         << "  \"schema\": \"xar.phase2.loader_callback_private_debug_capture.v3\",\n"
         << "  \"result\": \"" << capture.result << "\",\n"
         << "  \"reason\": \"" << JsonEscape(capture.reason) << "\",\n"
         << "  \"exact_build\": {\n"
         << "    \"product_version\": \"1.19.0.6\",\n"
         << "    \"exe_sha256\": \"" << capture.exe_sha256 << "\",\n"
         << "    \"expected_exe_sha256\": \""
         << Narrow(kExpectedExeSha256) << "\",\n"
         << "    \"file_size\": " << kExpectedExeSize << "\n"
         << "  },\n"
         << "  \"launch\": {\n"
         << "    \"exe\": \""
         << JsonEscape(Narrow(options.exe.wstring())) << "\",\n"
         << "    \"isolated_userdir\": \""
         << JsonEscape(Narrow(options.userdir.wstring())) << "\",\n"
         << "    \"pid\": " << capture.pid << ",\n"
         << "    \"debug_only_this_process\": true,\n"
         << "    \"timeout_ms\": " << options.timeout_ms << "\n"
         << "  },\n"
         << "  \"paused_observation\": {\n"
         << "    \"callback_observed\": "
         << (capture.callback_observed ? "true" : "false") << ",\n"
         << "    \"breakpoint_installed\": "
         << (capture.breakpoint_installed ? "true" : "false") << ",\n"
         << "    \"thread_id\": " << capture.thread_id << ",\n"
         << "    \"image_base\": \"" << Hex(capture.image_base) << "\",\n"
         << "    \"callback_call_rva\": \"" << Hex(kCallbackCallRva)
         << "\",\n"
         << "    \"callback_address\": \""
         << Hex(capture.callback_address) << "\",\n"
         << "    \"callback_continuation_rva\": \""
         << Hex(kCallbackContinuationRva) << "\",\n"
         << "    \"node\": \"" << Hex(capture.node) << "\",\n"
         << "    \"receiver_rcx\": \"" << Hex(capture.receiver)
         << "\",\n"
         << "    \"receiver_from_node_plus_0x88\": \""
         << Hex(capture.receiver_from_node) << "\",\n"
         << "    \"receiver_matches_node\": "
         << (capture.receiver_matches_node ? "true" : "false") << ",\n"
         << "    \"vptr\": \"" << Hex(capture.vptr) << "\",\n"
         << "    \"vptr_rva\": \"" << Hex(capture.vptr_rva) << "\",\n"
         << "    \"vptr_matches_static_candidate\": "
         << (capture.vptr_matches_candidate ? "true" : "false") << ",\n"
         << "    \"slot_2_target\": \"" << Hex(capture.slot_target)
         << "\",\n"
         << "    \"slot_2_target_rva\": \""
         << Hex(capture.slot_target_rva) << "\",\n"
         << "    \"slot_2_target_matches_static_contract\": "
         << (capture.slot_target_matches ? "true" : "false") << ",\n"
         << "    \"vptr_matches_runtime_owner_contract\": "
         << (capture.vptr_matches_runtime_owner ? "true" : "false") << ",\n"
         << "    \"slot_2_matches_runtime_owner_contract\": "
         << (capture.slot_target_matches_runtime_owner ? "true" : "false")
         << ",\n"
         << "    \"callback_function_at_receiver_plus_0x08\": \""
         << Hex(capture.callback_function) << "\",\n"
         << "    \"return_breakpoint_installed\": "
         << (capture.return_breakpoint_installed ? "true" : "false") << ",\n"
         << "    \"callback_return_observed\": "
         << (capture.callback_return_observed ? "true" : "false") << ",\n"
         << "    \"return_thread_id\": " << capture.return_thread_id << ",\n"
         << "    \"return_thread_matches_entry\": "
         << (capture.return_thread_matches ? "true" : "false") << ",\n"
         << "    \"post_return_receiver_from_node_plus_0x88\": \""
         << Hex(capture.post_receiver_from_node) << "\",\n"
         << "    \"post_return_vptr\": \"" << Hex(capture.post_vptr)
         << "\",\n"
         << "    \"post_return_callback_function\": \""
         << Hex(capture.post_callback_function) << "\",\n"
         << "    \"receiver_survived_return\": "
         << (capture.receiver_survived_return ? "true" : "false") << ",\n"
         << "    \"vptr_survived_return\": "
         << (capture.vptr_survived_return ? "true" : "false") << ",\n"
         << "    \"callback_function_survived_return\": "
         << (capture.callback_function_survived_return ? "true" : "false")
         << "\n"
         << "  },\n";
  output << "  \"sequence_observation\": {\n"
         << "    \"enabled\": " << (options.sequence ? "true" : "false")
         << ",\n"
         << "    \"entry_count\": " << capture.sequence_entries.size()
         << ",\n"
         << "    \"last_successful_sequence\": "
         << last_successful_sequence << ",\n"
         << "    \"first_unreturned_sequence\": "
         << first_unreturned_sequence << ",\n"
         << "    \"entries\": [\n";
  for (std::size_t index = 0; index < capture.sequence_entries.size(); ++index) {
    const auto& row = capture.sequence_entries[index];
    auto module_rva = [&](std::uint64_t address) {
      return address >= capture.image_base ? address - capture.image_base : 0;
    };
    output << "      {\n"
           << "        \"sequence\": " << row.sequence << ",\n"
           << "        \"node\": \"" << Hex(row.node) << "\",\n"
           << "        \"node_name\": \"" << JsonEscape(row.node_name)
           << "\",\n"
           << "        \"entry_thread_id\": " << row.entry_thread_id << ",\n"
           << "        \"return_thread_id\": " << row.return_thread_id << ",\n"
           << "        \"receiver\": \"" << Hex(row.receiver) << "\",\n"
           << "        \"wrapper_vptr_rva\": \""
           << Hex(module_rva(row.wrapper_vptr)) << "\",\n"
           << "        \"wrapper_slot_2_target_rva\": \""
           << Hex(module_rva(row.wrapper_slot_2_target)) << "\",\n"
           << "        \"concrete_callback_rva\": \""
           << Hex(module_rva(row.concrete_callback)) << "\",\n"
           << "        \"trampoline_decoded\": "
           << (row.trampoline_decoded ? "true" : "false") << ",\n"
           << "        \"global_pointer_rva\": \""
           << Hex(row.global_pointer_rva) << "\",\n"
           << "        \"global_object\": \"" << Hex(row.global_object)
           << "\",\n"
           << "        \"global_vptr_rva\": \""
           << Hex(module_rva(row.global_vptr)) << "\",\n"
           << "        \"global_slot_2_target_rva\": \""
           << Hex(module_rva(row.global_slot_2_target)) << "\",\n"
           << "        \"returned\": " << (row.returned ? "true" : "false")
           << ",\n"
           << "        \"same_thread\": "
           << (row.same_thread ? "true" : "false") << ",\n"
           << "        \"receiver_survived\": "
           << (row.receiver_survived ? "true" : "false") << ",\n"
           << "        \"wrapper_vptr_survived\": "
           << (row.wrapper_vptr_survived ? "true" : "false") << ",\n"
           << "        \"concrete_callback_survived\": "
           << (row.concrete_callback_survived ? "true" : "false") << ",\n"
           << "        \"entry_elapsed_seconds\": " << std::fixed
           << std::setprecision(3) << row.entry_elapsed_seconds << ",\n"
           << "        \"return_elapsed_seconds\": " << row.return_elapsed_seconds
           << "\n"
           << "      }" << (index + 1 == capture.sequence_entries.size() ? "" : ",")
           << "\n";
  }
  output << "    ],\n"
         << "    \"timeout_thread_id\": " << capture.timeout_thread_id << ",\n"
         << "    \"timeout_thread_rip\": \"" << Hex(capture.timeout_thread_rip)
         << "\",\n"
         << "    \"timeout_thread_rva\": \"" << Hex(capture.timeout_thread_rva)
         << "\",\n"
         << "    \"timeout_node\": \"" << Hex(capture.timeout_node) << "\",\n"
         << "    \"timeout_node_name\": \""
         << JsonEscape(capture.timeout_node_name) << "\",\n"
         << "    \"timeout_receiver\": \"" << Hex(capture.timeout_receiver)
         << "\",\n"
         << "    \"timeout_thread_suspended\": "
         << (capture.timeout_thread_suspended ? "true" : "false") << "\n"
         << "  },\n";
  output << "  \"next_node_observation\": {\n"
         << "    \"enabled\": " << (options.next_node ? "true" : "false")
         << ",\n"
         << "    \"node_loaded_stop_rva\": \"" << Hex(kNodeLoadedStopRva)
         << "\",\n"
         << "    \"loop_exit_discriminator_rva\": \"" << Hex(kLoopExitRva)
         << "\",\n"
         << "    \"last_successful_callback_sequence\": "
         << last_successful_sequence << ",\n"
         << "    \"matching_transition_observed\": "
         << (last_successful_transition ? "true" : "false") << ",\n"
         << "    \"transitions\": [\n";
  for (std::size_t index = 0; index < capture.next_node_transitions.size();
       ++index) {
    const auto& row = capture.next_node_transitions[index];
    output << "      {\n"
           << "        \"callback_sequence\": " << row.callback_sequence
           << ",\n"
           << "        \"callback_return_thread_id\": "
           << row.callback_return_thread_id << ",\n"
           << "        \"transition_thread_id\": "
           << row.transition_thread_id << ",\n"
           << "        \"same_thread\": "
           << (row.same_thread ? "true" : "false") << ",\n"
           << "        \"outcome\": \"" << JsonEscape(row.outcome)
           << "\",\n"
           << "        \"node\": \"" << Hex(row.node) << "\",\n"
           << "        \"node_name\": \"" << JsonEscape(row.node_name)
           << "\",\n"
           << "        \"receiver\": \"" << Hex(row.receiver) << "\",\n"
           << "        \"receiver_is_null\": "
           << (row.receiver_is_null ? "true" : "false") << ",\n"
           << "        \"elapsed_seconds\": " << std::fixed
           << std::setprecision(3) << row.elapsed_seconds << "\n"
           << "      }"
           << (index + 1 == capture.next_node_transitions.size() ? "" : ",")
           << "\n";
  }
  output << "    ],\n"
         << "    \"node_breakpoint_byte_restored\": "
         << (capture.node_breakpoint_byte_restored ? "true" : "false")
         << ",\n"
         << "    \"loop_exit_breakpoint_byte_restored\": "
         << (capture.loop_exit_breakpoint_byte_restored ? "true" : "false")
         << "\n"
         << "  },\n"
         << "  \"cleanup\": {\n"
         << "    \"original_breakpoint_byte_restored\": "
         << (capture.original_byte_restored ? "true" : "false") << ",\n"
         << "    \"continuation_breakpoint_byte_restored\": "
         << (capture.continuation_byte_restored ? "true" : "false") << ",\n"
         << "    \"process_terminated\": "
         << (capture.process_terminated ? "true" : "false") << ",\n"
         << "    \"real_user_profile_targeted\": false\n"
         << "  },\n"
         << "  \"scope\": {\n"
         << "    \"private_test_only\": true,\n"
         << "    \"public_bridge_abi_changed\": false,\n"
         << "    \"production_detour_installed\": false,\n"
         << "    \"callback_return_observed\": "
         << (capture.callback_return_observed ? "true" : "false") << ",\n"
         << "    \"readiness_promotion\": false\n"
         << "  },\n"
         << "  \"elapsed_seconds\": " << std::fixed << std::setprecision(3)
         << capture.elapsed_seconds << "\n"
         << "}\n";
}

Capture Run(const Options& options) {
  Capture capture;
  const auto started = std::chrono::steady_clock::now();
  PROCESS_INFORMATION process_info{};
  HANDLE job = nullptr;
  bool current_event_active = false;
  DEBUG_EVENT current_event{};
  auto finish_elapsed = [&]() {
    capture.elapsed_seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - started).count();
  };
  auto restore_transition_breakpoints = [&]() {
    bool ok = true;
    if (process_info.hProcess && capture.image_base != 0 &&
        capture.node_breakpoint_installed) {
      const auto address = capture.image_base + kNodeLoadedStopRva;
      const bool wrote = WriteBreakpointByte(
          process_info.hProcess, address, kNodeLoadedStopByte);
      std::uint8_t restored = 0;
      capture.node_breakpoint_byte_restored =
          wrote && ReadRemote(process_info.hProcess, address, &restored) &&
          restored == kNodeLoadedStopByte;
      capture.node_breakpoint_installed = false;
      ok &= capture.node_breakpoint_byte_restored;
    }
    if (process_info.hProcess && capture.image_base != 0 &&
        capture.loop_exit_breakpoint_installed) {
      const auto address = capture.image_base + kLoopExitRva;
      const bool wrote =
          WriteBreakpointByte(process_info.hProcess, address, kLoopExitByte);
      std::uint8_t restored = 0;
      capture.loop_exit_breakpoint_byte_restored =
          wrote && ReadRemote(process_info.hProcess, address, &restored) &&
          restored == kLoopExitByte;
      capture.loop_exit_breakpoint_installed = false;
      ok &= capture.loop_exit_breakpoint_byte_restored;
    }
    return ok;
  };

  try {
    if (!std::filesystem::is_regular_file(options.exe)) {
      throw std::runtime_error("exact executable does not exist");
    }
    if (std::filesystem::file_size(options.exe) != kExpectedExeSize) {
      throw std::runtime_error("exact executable size mismatch");
    }
    capture.exe_sha256 = Sha256(options.exe);
    if (_wcsicmp(std::wstring(capture.exe_sha256.begin(),
                             capture.exe_sha256.end()).c_str(),
                 kExpectedExeSha256) != 0) {
      throw std::runtime_error("exact executable SHA-256 mismatch");
    }
    std::filesystem::create_directories(options.userdir);
    std::filesystem::create_directories(options.output.parent_path());

    job = CreateKillOnCloseJob();
    const std::wstring command =
        Quote(options.exe.wstring()) + L" -gdpr-compliant -userdir=" +
        Quote(options.userdir.wstring());
    std::vector<wchar_t> mutable_command(command.begin(), command.end());
    mutable_command.push_back(L'\0');
    STARTUPINFOW startup{};
    startup.cb = sizeof(startup);
    if (!CreateProcessW(options.exe.c_str(), mutable_command.data(), nullptr,
                        nullptr, FALSE,
                        DEBUG_ONLY_THIS_PROCESS | CREATE_NEW_PROCESS_GROUP,
                        nullptr, options.exe.parent_path().c_str(), &startup,
                        &process_info)) {
      throw std::runtime_error("CreateProcessW debug launch failed");
    }
    capture.pid = process_info.dwProcessId;
    if (!AssignProcessToJobObject(job, process_info.hProcess)) {
      throw std::runtime_error("AssignProcessToJobObject failed");
    }

    const auto deadline = started + std::chrono::milliseconds(options.timeout_ms);
    bool initial_breakpoint_seen = false;
    while (std::chrono::steady_clock::now() < deadline &&
           (options.sequence || !capture.callback_return_observed)) {
      const auto remaining = std::chrono::duration_cast<std::chrono::milliseconds>(
          deadline - std::chrono::steady_clock::now());
      const DWORD wait_ms = static_cast<DWORD>(
          std::max<std::int64_t>(1, std::min<std::int64_t>(500, remaining.count())));
      DEBUG_EVENT event{};
      if (!WaitForDebugEvent(&event, wait_ms)) {
        if (GetLastError() == ERROR_SEM_TIMEOUT) continue;
        throw std::runtime_error("WaitForDebugEvent failed");
      }
      current_event = event;
      current_event_active = true;
      DWORD continue_status = DBG_CONTINUE;

      if (event.dwDebugEventCode == CREATE_PROCESS_DEBUG_EVENT) {
        capture.image_base = reinterpret_cast<std::uint64_t>(
            event.u.CreateProcessInfo.lpBaseOfImage);
        capture.callback_address = capture.image_base + kCallbackCallRva;
        std::array<std::uint8_t, 3> actual{};
        SIZE_T read = 0;
        if (!ReadProcessMemory(process_info.hProcess,
                               reinterpret_cast<const void*>(
                                    capture.callback_address),
                               actual.data(), actual.size(), &read) ||
            read != actual.size() || actual != kCallbackBytes) {
          throw std::runtime_error("callback instruction bytes mismatch");
        }
        if (options.next_node) {
          std::uint8_t node_byte = 0;
          std::uint8_t exit_byte = 0;
          if (!ReadRemote(process_info.hProcess,
                          capture.image_base + kNodeLoadedStopRva,
                          &node_byte) ||
              node_byte != kNodeLoadedStopByte ||
              !ReadRemote(process_info.hProcess,
                          capture.image_base + kLoopExitRva, &exit_byte) ||
              exit_byte != kLoopExitByte) {
            throw std::runtime_error(
                "next-node observation instruction bytes mismatch");
          }
        }
        if (!WriteBreakpointByte(process_info.hProcess,
                                 capture.callback_address, 0xCC)) {
          throw std::runtime_error("could not install callback breakpoint");
        }
        capture.breakpoint_installed = true;
        if (event.u.CreateProcessInfo.hFile) {
          CloseHandle(event.u.CreateProcessInfo.hFile);
        }
      } else if (event.dwDebugEventCode == LOAD_DLL_DEBUG_EVENT) {
        if (event.u.LoadDll.hFile) CloseHandle(event.u.LoadDll.hFile);
      } else if (event.dwDebugEventCode == CREATE_THREAD_DEBUG_EVENT) {
        if (event.u.CreateThread.hThread) CloseHandle(event.u.CreateThread.hThread);
      } else if (event.dwDebugEventCode == EXCEPTION_DEBUG_EVENT) {
        const auto& exception = event.u.Exception.ExceptionRecord;
        const auto address = reinterpret_cast<std::uint64_t>(
            exception.ExceptionAddress);
        if (exception.ExceptionCode == EXCEPTION_BREAKPOINT &&
            options.next_node &&
            capture.awaiting_transition_sequence != 0 &&
            ((address == capture.image_base + kNodeLoadedStopRva &&
              capture.node_breakpoint_installed) ||
             (address == capture.image_base + kLoopExitRva &&
              capture.loop_exit_breakpoint_installed))) {
          HANDLE thread = OpenThread(THREAD_GET_CONTEXT | THREAD_SET_CONTEXT |
                                         THREAD_QUERY_INFORMATION,
                                     FALSE, event.dwThreadId);
          if (!thread) {
            throw std::runtime_error(
                "OpenThread failed at next-node transition");
          }
          CONTEXT context{};
          context.ContextFlags = CONTEXT_CONTROL | CONTEXT_INTEGER;
          const bool context_ok = GetThreadContext(thread, &context) != FALSE;
          CloseHandle(thread);
          if (!context_ok) {
            throw std::runtime_error(
                "GetThreadContext failed at next-node transition");
          }

          NextNodeTransition row;
          row.callback_sequence = capture.awaiting_transition_sequence;
          row.callback_return_thread_id =
              capture.awaiting_transition_thread_id;
          row.transition_thread_id = event.dwThreadId;
          row.same_thread = row.callback_return_thread_id == row.transition_thread_id;
          row.elapsed_seconds = std::chrono::duration<double>(
              std::chrono::steady_clock::now() - started).count();
          if (address == capture.image_base + kNodeLoadedStopRva) {
            row.outcome = "next-node-loaded";
            row.node = context.Rsi;
            row.node_name = ReadNodeName(process_info.hProcess, row.node);
            if (!ReadRemote(process_info.hProcess, row.node + 0x88,
                            &row.receiver)) {
              throw std::runtime_error(
                  "could not read next node+0x88 receiver");
            }
            row.receiver_is_null = row.receiver == 0;
          } else {
            row.outcome = "vector-exhausted";
            row.receiver_is_null = true;
          }
          if (!restore_transition_breakpoints()) {
            throw std::runtime_error(
                "could not restore next-node transition breakpoints");
          }
          if (!ResetThreadInstructionPointer(event.dwThreadId, address)) {
            throw std::runtime_error(
                "could not reset instruction pointer at next-node transition");
          }
          capture.next_node_transitions.push_back(row);
          capture.awaiting_transition_sequence = 0;
          capture.awaiting_transition_thread_id = 0;
        } else if (exception.ExceptionCode == EXCEPTION_BREAKPOINT &&
            address == capture.callback_address) {
          HANDLE thread = OpenThread(THREAD_GET_CONTEXT | THREAD_SET_CONTEXT |
                                         THREAD_QUERY_INFORMATION,
                                     FALSE, event.dwThreadId);
          if (!thread) throw std::runtime_error("OpenThread failed at callback");
          CONTEXT context{};
          context.ContextFlags = CONTEXT_CONTROL | CONTEXT_INTEGER;
          const bool context_ok = GetThreadContext(thread, &context) != FALSE;
          CloseHandle(thread);
          if (!context_ok) {
            throw std::runtime_error("GetThreadContext failed at callback");
          }
          capture.thread_id = event.dwThreadId;
          capture.node = context.Rsi;
          capture.receiver = context.Rcx;
          capture.vptr = context.Rax;
          if (!ReadRemote(process_info.hProcess, capture.node + 0x88,
                          &capture.receiver_from_node)) {
            throw std::runtime_error("could not read node+0x88 receiver");
          }
          if (!ReadRemote(process_info.hProcess, capture.vptr + 0x10,
                          &capture.slot_target)) {
            throw std::runtime_error("could not read callback vtable slot 2");
          }
          if (!ReadRemote(process_info.hProcess, capture.receiver + 0x08,
                          &capture.callback_function)) {
            throw std::runtime_error("could not read callback function pointer");
          }
          capture.receiver_matches_node =
              capture.receiver != 0 &&
              capture.receiver == capture.receiver_from_node;
          capture.vptr_rva = capture.vptr - capture.image_base;
          capture.slot_target_rva = capture.slot_target - capture.image_base;
          for (const auto candidate : kCandidateVtableRvas) {
            capture.vptr_matches_candidate |= capture.vptr_rva == candidate;
          }
          capture.slot_target_matches =
              capture.slot_target_rva == kCallbackSlotTargetRva;
          capture.vptr_matches_runtime_owner =
              capture.vptr_rva == kObservedRuntimeVtableRva;
          capture.slot_target_matches_runtime_owner =
              capture.slot_target_rva == kObservedRuntimeSlotTargetRva;
          if (options.sequence) {
            SequenceEntry row;
            row.sequence = capture.sequence_entries.size() + 1;
            row.entry_thread_id = event.dwThreadId;
            row.node = capture.node;
            row.node_name = ReadNodeName(process_info.hProcess, capture.node);
            row.receiver = capture.receiver;
            row.wrapper_vptr = capture.vptr;
            row.wrapper_slot_2_target = capture.slot_target;
            row.concrete_callback = capture.callback_function;
            row.entry_elapsed_seconds = std::chrono::duration<double>(
                std::chrono::steady_clock::now() - started).count();
            DecodeConcreteTrampoline(process_info.hProcess, capture.image_base,
                                     &row);
            capture.sequence_entries.push_back(row);
          }
          if (!WriteBreakpointByte(process_info.hProcess,
                                   capture.callback_address,
                                   kCallbackBytes[0])) {
            throw std::runtime_error("could not restore callback byte");
          }
          std::uint8_t restored = 0;
          capture.original_byte_restored =
              ReadRemote(process_info.hProcess, capture.callback_address,
                         &restored) &&
              restored == kCallbackBytes[0];
          capture.callback_observed = true;
          const std::uint64_t continuation_address =
              capture.image_base + kCallbackContinuationRva;
          std::uint8_t continuation_byte = 0;
          if (!ReadRemote(process_info.hProcess, continuation_address,
                          &continuation_byte) || continuation_byte != 0x4C) {
            throw std::runtime_error("callback continuation byte mismatch");
          }
          if (!WriteBreakpointByte(process_info.hProcess, continuation_address,
                                   0xCC)) {
            throw std::runtime_error("could not install return breakpoint");
          }
          capture.return_breakpoint_installed = true;
          capture.continuation_byte_restored = false;
          HANDLE resume_thread = OpenThread(THREAD_GET_CONTEXT | THREAD_SET_CONTEXT |
                                                THREAD_QUERY_INFORMATION,
                                            FALSE, event.dwThreadId);
          if (!resume_thread) {
            throw std::runtime_error("OpenThread failed before callback resume");
          }
          context.Rip = capture.callback_address;
          const bool context_set = SetThreadContext(resume_thread, &context) != FALSE;
          CloseHandle(resume_thread);
          if (!context_set) {
            throw std::runtime_error("SetThreadContext failed before callback resume");
          }
        } else if (exception.ExceptionCode == EXCEPTION_BREAKPOINT &&
                   address == capture.image_base + kCallbackContinuationRva &&
                   capture.callback_observed) {
          capture.return_thread_id = event.dwThreadId;
          capture.return_thread_matches =
              capture.return_thread_id == capture.thread_id;
          const std::uint64_t continuation_address =
              capture.image_base + kCallbackContinuationRva;
          if (!WriteBreakpointByte(process_info.hProcess, continuation_address,
                                   0x4C)) {
            throw std::runtime_error("could not restore continuation byte");
          }
          std::uint8_t restored = 0;
          capture.continuation_byte_restored =
              ReadRemote(process_info.hProcess, continuation_address, &restored) &&
              restored == 0x4C;
          if (!ReadRemote(process_info.hProcess, capture.node + 0x88,
                          &capture.post_receiver_from_node) ||
              !ReadRemote(process_info.hProcess, capture.receiver,
                          &capture.post_vptr) ||
              !ReadRemote(process_info.hProcess, capture.receiver + 0x08,
                          &capture.post_callback_function)) {
            throw std::runtime_error("callback object was unreadable after return");
          }
          capture.receiver_survived_return =
              capture.post_receiver_from_node == capture.receiver;
          capture.vptr_survived_return = capture.post_vptr == capture.vptr;
          capture.callback_function_survived_return =
              capture.post_callback_function == capture.callback_function;
          capture.callback_return_observed = true;
          if (options.sequence && !capture.sequence_entries.empty()) {
            auto& row = capture.sequence_entries.back();
            row.returned = true;
            row.return_thread_id = event.dwThreadId;
            row.same_thread = capture.return_thread_matches;
            row.receiver_survived = capture.receiver_survived_return;
            row.wrapper_vptr_survived = capture.vptr_survived_return;
            row.concrete_callback_survived =
                capture.callback_function_survived_return;
            row.return_elapsed_seconds = std::chrono::duration<double>(
                std::chrono::steady_clock::now() - started).count();
            if (options.next_node) {
              if (capture.node_breakpoint_installed ||
                  capture.loop_exit_breakpoint_installed ||
                  capture.awaiting_transition_sequence != 0) {
                throw std::runtime_error(
                    "previous next-node transition remained pending");
              }
              const auto node_address =
                  capture.image_base + kNodeLoadedStopRva;
              const auto exit_address = capture.image_base + kLoopExitRva;
              std::uint8_t node_byte = 0;
              std::uint8_t exit_byte = 0;
              if (!ReadRemote(process_info.hProcess, node_address,
                              &node_byte) ||
                  node_byte != kNodeLoadedStopByte ||
                  !ReadRemote(process_info.hProcess, exit_address,
                              &exit_byte) ||
                  exit_byte != kLoopExitByte) {
                throw std::runtime_error(
                    "next-node breakpoint source byte mismatch");
              }
              if (!WriteBreakpointByte(process_info.hProcess, node_address,
                                       0xCC)) {
                throw std::runtime_error(
                    "could not install node-loaded breakpoint");
              }
              capture.node_breakpoint_installed = true;
              capture.node_breakpoint_byte_restored = false;
              if (!WriteBreakpointByte(process_info.hProcess, exit_address,
                                       0xCC)) {
                throw std::runtime_error(
                    "could not install loop-exit breakpoint");
              }
              capture.loop_exit_breakpoint_installed = true;
              capture.loop_exit_breakpoint_byte_restored = false;
              capture.awaiting_transition_sequence = row.sequence;
              capture.awaiting_transition_thread_id = event.dwThreadId;
            }
            HANDLE resume_thread = OpenThread(
                THREAD_GET_CONTEXT | THREAD_SET_CONTEXT |
                    THREAD_QUERY_INFORMATION,
                FALSE, event.dwThreadId);
            if (!resume_thread) {
              throw std::runtime_error(
                  "OpenThread failed before continuation resume");
            }
            CONTEXT context{};
            context.ContextFlags = CONTEXT_CONTROL | CONTEXT_INTEGER;
            const bool context_ok =
                GetThreadContext(resume_thread, &context) != FALSE;
            context.Rip = continuation_address;
            const bool context_set =
                context_ok && SetThreadContext(resume_thread, &context) != FALSE;
            CloseHandle(resume_thread);
            if (!context_set) {
              throw std::runtime_error(
                  "SetThreadContext failed before continuation resume");
            }
            if (!WriteBreakpointByte(process_info.hProcess,
                                     capture.callback_address, 0xCC)) {
              throw std::runtime_error(
                  "could not rearm callback entry breakpoint");
            }
            capture.original_byte_restored = false;
          } else {
            capture.result = capture.vptr_matches_runtime_owner &&
                                   capture.slot_target_matches_runtime_owner &&
                                   capture.return_thread_matches &&
                                   capture.receiver_survived_return &&
                                   capture.vptr_survived_return &&
                                   capture.callback_function_survived_return &&
                                   capture.original_byte_restored &&
                                   capture.continuation_byte_restored
                               ? "GREEN"
                               : "RED";
          capture.reason = capture.result == "GREEN"
                               ? "callback-entry-return-lifetime-observed"
                               : "callback-entry-return-lifetime-mismatch";
          }
        } else if (exception.ExceptionCode == EXCEPTION_BREAKPOINT &&
                   !initial_breakpoint_seen) {
          initial_breakpoint_seen = true;
        } else {
          continue_status = DBG_EXCEPTION_NOT_HANDLED;
        }
      }

      ContinueDebugEvent(event.dwProcessId, event.dwThreadId, continue_status);
      current_event_active = false;
    }

    if (options.sequence) {
      if (capture.thread_id != 0) {
        HANDLE thread = OpenThread(THREAD_SUSPEND_RESUME | THREAD_GET_CONTEXT |
                                       THREAD_QUERY_INFORMATION,
                                   FALSE, capture.thread_id);
        if (thread) {
          if (SuspendThread(thread) != static_cast<DWORD>(-1)) {
            capture.timeout_thread_suspended = true;
            CONTEXT context{};
            context.ContextFlags = CONTEXT_CONTROL | CONTEXT_INTEGER;
            if (GetThreadContext(thread, &context)) {
              capture.timeout_thread_id = capture.thread_id;
              capture.timeout_thread_rip = context.Rip;
              capture.timeout_thread_rva =
                  context.Rip >= capture.image_base
                      ? context.Rip - capture.image_base
                      : 0;
              capture.timeout_node = context.Rsi;
              capture.timeout_node_name =
                  ReadNodeName(process_info.hProcess, capture.timeout_node);
              ReadRemote(process_info.hProcess, capture.timeout_node + 0x88,
                         &capture.timeout_receiver);
            }
          }
          CloseHandle(thread);
        }
      }
      const bool has_pending = !capture.sequence_entries.empty() &&
                               !capture.sequence_entries.back().returned;
      const bool has_unentered_candidate = capture.timeout_thread_suspended &&
                                            !capture.timeout_node_name.empty();
      if (options.next_node) {
        std::size_t last_successful_sequence = 0;
        for (const auto& row : capture.sequence_entries) {
          if (row.returned) last_successful_sequence = row.sequence;
        }
        const NextNodeTransition* matching = nullptr;
        for (const auto& row : capture.next_node_transitions) {
          if (row.callback_sequence == last_successful_sequence) {
            matching = &row;
          }
        }
        capture.result =
            last_successful_sequence != 0 && matching && matching->same_thread
                ? "GREEN"
                : "RED";
        capture.reason =
            capture.result == "GREEN"
                ? (matching->outcome == "vector-exhausted"
                       ? "last-returned-callback-vector-exhausted"
                       : "last-returned-callback-next-node-observed")
                : "last-returned-callback-next-transition-unobserved";
      } else {
        capture.result = !capture.sequence_entries.empty() &&
                                 (has_pending || has_unentered_candidate)
                             ? "GREEN"
                             : "RED";
        capture.reason =
            has_pending
                ? "callback-sequence-first-unreturned-observed"
                : (has_unentered_candidate
                       ? "callback-sequence-first-unentered-candidate-observed"
                       : "callback-sequence-stall-boundary-unobservable");
      }
    } else if (!capture.callback_observed) {
      capture.result = "RED";
      capture.reason = "callback-breakpoint-timeout";
    } else if (!capture.callback_return_observed) {
      capture.result = "RED";
      capture.reason = "callback-return-breakpoint-timeout";
    }
  } catch (const std::exception& error) {
    capture.result = "RED";
    capture.reason = error.what();
  }

  if (process_info.hProcess) {
    if (!restore_transition_breakpoints()) {
      capture.result = "RED";
      capture.reason += "; transition-breakpoint-cleanup-failed";
    }
    if (capture.breakpoint_installed && !capture.original_byte_restored &&
        capture.callback_address != 0) {
      capture.original_byte_restored = WriteBreakpointByte(
          process_info.hProcess, capture.callback_address, kCallbackBytes[0]);
    }
    if (capture.return_breakpoint_installed &&
        !capture.continuation_byte_restored && capture.image_base != 0) {
      capture.continuation_byte_restored = WriteBreakpointByte(
          process_info.hProcess,
          capture.image_base + kCallbackContinuationRva, 0x4C);
    }
    TerminateProcess(process_info.hProcess, 0);
    if (current_event_active) {
      ContinueDebugEvent(current_event.dwProcessId, current_event.dwThreadId,
                         DBG_CONTINUE);
      current_event_active = false;
    }
    // A debuggee cannot finish termination until its EXIT_PROCESS event is
    // drained.  Waiting on the process handle first would deadlock against
    // the debugger protocol and incorrectly report cleanup as unproven.
    const auto cleanup_deadline =
        std::chrono::steady_clock::now() + std::chrono::seconds(5);
    while (std::chrono::steady_clock::now() < cleanup_deadline) {
      DEBUG_EVENT event{};
      if (!WaitForDebugEvent(&event, 100)) {
        if (GetLastError() == ERROR_SEM_TIMEOUT) continue;
        break;
      }
      if (event.dwDebugEventCode == LOAD_DLL_DEBUG_EVENT &&
          event.u.LoadDll.hFile) {
        CloseHandle(event.u.LoadDll.hFile);
      } else if (event.dwDebugEventCode == CREATE_THREAD_DEBUG_EVENT &&
                 event.u.CreateThread.hThread) {
        CloseHandle(event.u.CreateThread.hThread);
      }
      const bool exited =
          event.dwDebugEventCode == EXIT_PROCESS_DEBUG_EVENT &&
          event.dwProcessId == process_info.dwProcessId;
      ContinueDebugEvent(event.dwProcessId, event.dwThreadId, DBG_CONTINUE);
      if (exited) break;
    }
    capture.process_terminated =
        WaitForSingleObject(process_info.hProcess, 0) == WAIT_OBJECT_0;
  }
  if (job) {
    CloseHandle(job);
    job = nullptr;
  }
  // Closing the kill-on-close Job is the final cleanup fallback.  Recheck the
  // process handle after that close so the report reflects this last step.
  if (process_info.hProcess && !capture.process_terminated) {
    capture.process_terminated =
        WaitForSingleObject(process_info.hProcess, 5000) == WAIT_OBJECT_0;
  }
  if (process_info.hThread) CloseHandle(process_info.hThread);
  if (process_info.hProcess) CloseHandle(process_info.hProcess);
  finish_elapsed();
  if (!capture.process_terminated && capture.pid != 0) {
    capture.result = "RED";
    capture.reason += "; cleanup-unproven";
  }
  return capture;
}

}  // namespace

int wmain(int argc, wchar_t** argv) {
  if (argc == 2 && std::wstring(argv[1]) == L"--self-test") {
    const bool ok = kCallbackCallRva == 0x3B9AB90 &&
                     kCallbackContinuationRva == 0x3B9AB93 &&
                     kNodeLoadedStopRva == 0x3B9AB53 &&
                     kLoopExitRva == 0x3B9ACC4 &&
                     kCallbackSlotTargetRva == 0x3B9BA70 &&
                    kObservedRuntimeVtableRva == 0x408A450 &&
                    kObservedRuntimeSlotTargetRva == 0x947BD0 &&
                     kCallbackBytes ==
                         std::array<std::uint8_t, 3>{0xFF, 0x50, 0x10} &&
                     kNodeLoadedStopByte == 0x48 && kLoopExitByte == 0x4C;
    std::cout << (ok ? "phase2-private-debug-capture-self-test=GREEN\n"
                     : "phase2-private-debug-capture-self-test=RED\n");
    return ok ? 0 : 2;
  }
  try {
    const Options options = ParseOptions(argc, argv);
    const Capture capture = Run(options);
    WriteReport(options, capture);
    std::cout << "result=" << capture.result << " reason=" << capture.reason
              << " artifact=" << Narrow(options.output.wstring()) << "\n";
    return capture.result == "GREEN" ? 0 : 2;
  } catch (const std::exception& error) {
    std::cerr << "phase2 private debug capture failed: " << error.what() << "\n";
    return 3;
  }
}
