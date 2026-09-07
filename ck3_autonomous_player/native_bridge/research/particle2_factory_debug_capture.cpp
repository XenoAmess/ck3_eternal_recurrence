// Private exact-build debugger probe for the ParticleTexture startup factory.
//
// This executable is deliberately not linked into xar_ck3_bridge.dll. It
// launches one isolated CK3 process suspended, attaches with DebugActiveProcess,
// and uses a per-thread DR0 execute breakpoint state machine. It never patches or writes
// CK3 code/data. The only target-context mutation is the thread debug-register
// state required by the Windows debugger. After capture it clears that state,
// continues the outstanding event, and intentionally terminates the diagnostic
// process. No native-continuation or gameplay-equivalence claim is made.

#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <bcrypt.h>

#include <array>
#include <chrono>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

#pragma comment(lib, "bcrypt.lib")

namespace {

constexpr std::uint64_t kExpectedExeSize = 95206008;
constexpr wchar_t kExpectedExeSha256[] =
    L"2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";

constexpr std::uint64_t kEntryRva = 0x39C70A1;
constexpr std::uint64_t kGraphicsRva = 0x3A86700;
constexpr std::uint64_t kSourceEntryRva = 0x3AAE920;
constexpr std::uint64_t kSourceCacheResultRva = 0x3AAE9A8;
constexpr std::uint64_t kResolverEntryRva = 0x3BE2340;
constexpr std::uint64_t kResolverSizeRva = 0x3BE23AE;
constexpr std::uint64_t kResolverHeapResultRva = 0x3BE23FA;
constexpr std::uint64_t kResolverBufferReadyRva = 0x3BE2403;
constexpr std::uint64_t kResolverNormalizeResultRva = 0x3BE242E;
constexpr std::uint64_t kResolverListHeadRva = 0x3BE2439;
constexpr std::uint64_t kResolverCandidatePrimaryResultRva = 0x3BE245A;
constexpr std::uint64_t kResolverCandidateSecondaryEntryRva = 0x3BE1CE0;
constexpr std::uint64_t kResolverCandidateSecondaryStateRva = 0x3BE1DE8;
constexpr std::uint64_t kResolverCandidateBackendCallbackEntryRva = 0x3BFDC60;
constexpr std::uint64_t kResolverCandidateBackendPathResultRva = 0x3BFDD25;
constexpr std::uint64_t kResolverCandidateBackendReadResultRva = 0x3BFDD38;
constexpr std::uint64_t kResolverCandidateCallbackResultRva = 0x3BE1E57;
constexpr std::uint64_t kResolverCandidateSecondaryResultRva = 0x3BE2480;
constexpr std::uint64_t kResolverCandidateFinalResultRva = 0x3BE24A8;
constexpr std::uint64_t kResolverSearchResultRva = 0x3BE24B6;
constexpr std::uint64_t kSourceResolverResultRva = 0x3AAE9C1;
constexpr std::uint64_t kSourceRva = 0x3A86761;
constexpr std::uint64_t kVariantRva = 0x3A867A8;
constexpr std::uint64_t kBackendEntryRva = 0x3A8E080;
constexpr std::uint64_t kBackendCacheResultRva = 0x3A8E0C9;
constexpr std::uint64_t kBackendCallbackEntryRva = 0x3AD4C30;
constexpr std::uint64_t kBackendInitializerGlobalsRva = 0x3B1C436;
constexpr std::uint64_t kBackendStageLoopRva = 0x3B1C479;
constexpr std::uint64_t kBackendHlslResultRva = 0x3B1C4BE;
constexpr std::uint64_t kBackendShaderCacheResultRva = 0x3B06F77;
constexpr std::uint64_t kBackendShaderVcallEntryRva = 0x3B06F92;
constexpr std::uint64_t kBackendShaderVcallResultRva = 0x3B06F95;
constexpr std::uint64_t kBackendShaderGetterResultRva = 0x3B07007;
constexpr std::uint64_t kBackendShaderResultRva = 0x3B1C501;
constexpr std::uint64_t kBackendInitializerResultRva = 0x3AD4DEC;
constexpr std::uint64_t kBackendCallbackOutputRva = 0x3AD4F05;
constexpr std::uint64_t kBackendVcallResultRva = 0x3A8E0ED;
constexpr std::uint64_t kBackendRva = 0x3A867E4;
constexpr std::uint64_t kReturnRva = 0x39C70A6;

constexpr std::array<std::uint8_t, 5> kEntryAnchor{
    0xE8, 0x7A, 0x18, 0x0C, 0x00};
constexpr std::array<std::uint8_t, 10> kGraphicsAnchor{
    0x4D, 0x85, 0xFF, 0x75, 0x08, 0x4C, 0x89, 0x31, 0xE9, 0xFF};
constexpr std::array<std::uint8_t, 10> kSourceEntryAnchor{
    0x48, 0x89, 0x5C, 0x24, 0x18, 0x48, 0x89, 0x4C, 0x24, 0x08};
constexpr std::array<std::uint8_t, 9> kSourceCacheResultAnchor{
    0x4C, 0x39, 0x2E, 0x0F, 0x85, 0xD0, 0x02, 0x00, 0x00};
constexpr std::array<std::uint8_t, 8> kResolverEntryAnchor{
    0x40, 0x55, 0x56, 0x57, 0x41, 0x54, 0x41, 0x55};
constexpr std::array<std::uint8_t, 9> kResolverSizeAnchor{
    0x48, 0x81, 0xFA, 0x00, 0x02, 0x00, 0x00, 0x73, 0x35};
constexpr std::array<std::uint8_t, 9> kResolverHeapResultAnchor{
    0x48, 0x85, 0xC0, 0x0F, 0x84, 0xD5, 0x00, 0x00, 0x00};
constexpr std::array<std::uint8_t, 7> kResolverBufferReadyAnchor{
    0x48, 0x89, 0x38, 0x4C, 0x8D, 0x68, 0x08};
constexpr std::array<std::uint8_t, 8> kResolverNormalizeResultAnchor{
    0x84, 0xC0, 0x0F, 0x84, 0x80, 0x00, 0x00, 0x00};
constexpr std::array<std::uint8_t, 5> kResolverListHeadAnchor{
    0x48, 0x85, 0xDB, 0x74, 0x78};
constexpr std::array<std::uint8_t, 8> kResolverCandidatePrimaryResultAnchor{
    0x85, 0xC0, 0x75, 0x55, 0x48, 0x8D, 0x45, 0x28};
constexpr std::array<std::uint8_t, 10> kResolverCandidateSecondaryEntryAnchor{
    0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x6C, 0x24, 0x10};
constexpr std::array<std::uint8_t, 13> kResolverCandidateSecondaryStateAnchor{
    0x80, 0xB8, 0xF9, 0x00, 0x00, 0x00, 0x00, 0x0F, 0x85, 0xEB,
    0x00, 0x00, 0x00};
constexpr std::array<std::uint8_t, 10>
    kResolverCandidateBackendCallbackEntryAnchor{
        0x40, 0x55, 0x41, 0x56, 0x41, 0x57, 0x48, 0x83, 0xEC, 0x20};
constexpr std::array<std::uint8_t, 6>
    kResolverCandidateBackendPathResultAnchor{
        0x48, 0x85, 0xC0, 0x74, 0x23, 0x45};
constexpr std::array<std::uint8_t, 5>
    kResolverCandidateBackendReadResultAnchor{
        0x48, 0x83, 0x7B, 0xF8, 0x00};
constexpr std::array<std::uint8_t, 9> kResolverCandidateCallbackResultAnchor{
    0x4D, 0x85, 0xF6, 0x74, 0x22, 0x0F, 0x10, 0x44, 0x24};
constexpr std::array<std::uint8_t, 10>
    kResolverCandidateSecondaryResultAnchor{
        0x85, 0xC0, 0x74, 0x29, 0x8B, 0x85, 0x98, 0x00, 0x00, 0x00};
constexpr std::array<std::uint8_t, 9> kResolverCandidateFinalResultAnchor{
    0x83, 0xF8, 0x01, 0x74, 0x06, 0x48, 0x8B, 0x5B, 0x30};
constexpr std::array<std::uint8_t, 5> kResolverSearchResultAnchor{
    0x45, 0x84, 0xE4, 0x75, 0x08};
constexpr std::array<std::uint8_t, 9> kSourceResolverResultAnchor{
    0x48, 0x85, 0xC0, 0x0F, 0x84, 0xB7, 0x02, 0x00, 0x00};
constexpr std::array<std::uint8_t, 8> kSourceAnchor{
    0xC7, 0x44, 0x24, 0x30, 0x02, 0x00, 0x00, 0x00};
constexpr std::array<std::uint8_t, 8> kVariantAnchor{
    0x4C, 0x8B, 0xE0, 0x48, 0x85, 0xC0, 0x75, 0x10};
constexpr std::array<std::uint8_t, 10> kBackendEntryAnchor{
    0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x74, 0x24, 0x18};
constexpr std::array<std::uint8_t, 8> kBackendCacheResultAnchor{
    0xC7, 0x44, 0x24, 0x30, 0x01, 0x00, 0x00, 0x00};
constexpr std::array<std::uint8_t, 10> kBackendCallbackEntryAnchor{
    0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x6C, 0x24, 0x18};
constexpr std::array<std::uint8_t, 9> kBackendInitializerGlobalsAnchor{
    0x4D, 0x85, 0xF6, 0x0F, 0x84, 0x34, 0x09, 0x00, 0x00};
constexpr std::array<std::uint8_t, 11> kBackendStageLoopAnchor{
    0x49, 0x83, 0x7F, 0x10, 0x00, 0x0F, 0x84, 0xE5, 0x07, 0x00, 0x00};
constexpr std::array<std::uint8_t, 8> kBackendHlslResultAnchor{
    0x84, 0xC0, 0x0F, 0x84, 0x47, 0x08, 0x00, 0x00};
constexpr std::array<std::uint8_t, 10> kBackendShaderCacheResultAnchor{
    0x48, 0x83, 0x3E, 0x00, 0x0F, 0x85, 0x4B, 0x01, 0x00, 0x00};
constexpr std::array<std::uint8_t, 3> kBackendShaderVcallEntryAnchor{
    0xFF, 0x50, 0x08};
constexpr std::array<std::uint8_t, 10> kBackendShaderVcallResultAnchor{
    0x48, 0x8B, 0x08, 0x48, 0xC7, 0x00, 0x00, 0x00, 0x00, 0x00};
constexpr std::array<std::uint8_t, 8> kBackendShaderGetterResultAnchor{
    0x48, 0x8B, 0x06, 0x48, 0x85, 0xC0, 0x0F, 0x84};
constexpr std::array<std::uint8_t, 9> kBackendShaderResultAnchor{
    0x4D, 0x85, 0xF6, 0x0F, 0x84, 0xA4, 0x07, 0x00, 0x00};
constexpr std::array<std::uint8_t, 8> kBackendInitializerResultAnchor{
    0x84, 0xC0, 0x0F, 0x85, 0x06, 0x01, 0x00, 0x00};
constexpr std::array<std::uint8_t, 3> kBackendCallbackOutputAnchor{
    0x49, 0x8B, 0xC6};
constexpr std::array<std::uint8_t, 9> kBackendVcallResultAnchor{
    0x48, 0x8B, 0x08, 0x4C, 0x89, 0x38, 0x48, 0x8B, 0x1F};
constexpr std::array<std::uint8_t, 7> kBackendAnchor{
    0x90, 0x48, 0x83, 0x7D, 0x7F, 0x00, 0x75};
constexpr std::array<std::uint8_t, 7> kReturnAnchor{
    0x48, 0x8B, 0x45, 0x98, 0x49, 0x8B, 0xF7};

constexpr char kExpectedSource[] = "gfx/FX/cw/particle2.shader";
constexpr char kExpectedVariant[] = "ParticleTexture";
constexpr std::size_t kExpectedSourceLength = 26;
constexpr std::size_t kExpectedVariantLength = 15;
// CREATE_SUSPENDED contributes one suspend count and the outstanding attach
// debug event contributes the second. ResumeThread releases the explicit
// count; ContinueDebugEvent releases the debugger-held count.
constexpr DWORD kExpectedAttachEventSuspendCount = 2;

enum class Stage {
  entry,
  graphics,
  source_entry,
  source_cache_result,
  resolver_entry,
  resolver_size,
  resolver_heap_result,
  resolver_buffer_ready,
  resolver_normalize_result,
  resolver_list_head,
  resolver_candidate_primary_result,
  resolver_candidate_secondary_entry,
  resolver_candidate_secondary_state,
  resolver_candidate_backend_callback_entry,
  resolver_candidate_backend_path_result,
  resolver_candidate_backend_read_result,
  resolver_candidate_callback_result,
  resolver_candidate_secondary_result,
  resolver_candidate_final_result,
  resolver_search_result,
  source_resolver_result,
  source,
  variant,
  backend_entry,
  backend_cache_result,
  backend_callback_entry,
  backend_initializer_globals,
  backend_stage_loop,
  backend_hlsl_result,
  backend_shader_cache_result,
  backend_shader_vcall_entry,
  backend_shader_vcall_result,
  backend_shader_getter_result,
  backend_shader_result,
  backend_initializer_result,
  backend_callback_output,
  backend_vcall_result,
  backend,
  returned,
  complete,
};

struct Options {
  std::filesystem::path exe;
  std::filesystem::path userdir;
  std::filesystem::path output;
  DWORD timeout_ms = 45000;
  bool self_test = false;
};

struct Step {
  std::string name;
  DWORD thread_id = 0;
  std::uint64_t rip = 0;
  double elapsed_seconds = 0.0;
};

struct CandidateStep {
  std::uint64_t address = 0;
  std::uint64_t prefix_address = 0;
  std::uint64_t backend_object = 0;
  std::uint64_t rewrite_address = 0;
  std::uint64_t rewrite_offset = 0;
  std::uint64_t dispatch_table = 0;
  std::uint64_t callback_address = 0;
  std::uint64_t next_address = 0;
  std::string prefix_text;
  bool primary_observed = false;
  bool secondary_observed = false;
  bool secondary_state_observed = false;
  bool backend_callback_entry_observed = false;
  bool backend_path_observed = false;
  bool backend_read_observed = false;
  bool secondary_callback_observed = false;
  bool secondary_callback_result_type_observed = false;
  bool final_observed = false;
  std::int64_t primary_result = -1;
  std::int64_t secondary_result = -1;
  std::uint64_t callback_output_address = 0;
  std::uint64_t backend_path_address = 0;
  std::string backend_root_text;
  std::string backend_requested_text;
  std::string backend_path_text;
  std::int64_t backend_read_result = -1;
  std::int64_t secondary_callback_result = -1;
  std::int64_t secondary_callback_result_type = -1;
  std::uint8_t secondary_state_f9 = 0;
  std::uint8_t secondary_state_fa = 0;
  std::int64_t final_result = -1;
};

struct BackendStageStep {
  std::uint32_t index = 0;
  std::uint64_t name_object = 0;
  std::uint64_t name_length = 0;
  std::string name;
  bool active = false;
  bool hlsl_result_observed = false;
  bool hlsl_ok = false;
  bool shader_cache_result_observed = false;
  std::uint64_t shader_cache_output = 0;
  bool shader_vcall_entry_observed = false;
  std::uint64_t shader_manager = 0;
  std::uint64_t shader_dispatch_table = 0;
  std::uint64_t shader_callback_address = 0;
  bool shader_vcall_result_observed = false;
  std::uint64_t shader_vcall_wrapper_address = 0;
  std::uint64_t shader_vcall_output = 0;
  bool shader_getter_result_observed = false;
  std::uint64_t shader_getter_output = 0;
  bool shader_result_observed = false;
  std::uint64_t shader_output = 0;
};

bool CandidateRejected(const CandidateStep &candidate) {
  if (!candidate.primary_observed || candidate.primary_result != 0 ||
      !candidate.secondary_observed) {
    return false;
  }
  if (candidate.secondary_result == 0) return !candidate.final_observed;
  return candidate.final_observed && candidate.final_result != 1;
}

bool CandidateSelected(const CandidateStep &candidate) {
  return (candidate.primary_observed && candidate.primary_result != 0) ||
      (candidate.final_observed && candidate.final_result == 1);
}

struct Capture {
  std::string result = "RED";
  std::string reason = "not-started";
  std::string classification = "unclassified";
  std::string capture_status = "not-started";
  std::string cleanup_status = "not-started";
  std::string process_exit_kind = "unknown";
  std::string exe_sha256;
  std::string probe_sha256;
  std::uint64_t exe_size = 0;
  DWORD pid = 0;
  DWORD target_thread_id = 0;
  std::uint64_t image_base = 0;
  bool ck3_started = false;
  bool debugger_attached = false;
  bool primary_thread_resumed = false;
  bool anchors_verified = false;
  bool target_tuple_observed = false;
  bool graphics_observed = false;
  bool source_detail_entry_observed = false;
  bool source_cache_observed = false;
  bool resolver_entry_observed = false;
  bool resolver_size_observed = false;
  bool resolver_heap_result_observed = false;
  bool resolver_buffer_ready_observed = false;
  bool resolver_normalize_observed = false;
  bool resolver_list_head_observed = false;
  bool resolver_search_observed = false;
  bool source_resolver_observed = false;
  bool source_observed = false;
  bool variant_observed = false;
  bool backend_entry_observed = false;
  bool backend_cache_result_observed = false;
  bool backend_callback_entry_observed = false;
  bool backend_initializer_globals_observed = false;
  bool backend_initializer_result_observed = false;
  bool backend_callback_output_observed = false;
  bool backend_vcall_result_observed = false;
  bool backend_observed = false;
  bool return_observed = false;
  bool debug_registers_cleared = false;
  bool capture_event_continued = false;
  bool debugger_detached = false;
  bool diagnostic_termination_requested = false;
  bool native_continuation_claimed = false;
  bool natural_exit_observed = false;
  bool cleanup_forced = false;
  bool process_terminated = false;
  bool exit_event_observed = false;
  bool artifact_committed = false;
  std::uint64_t caller_rbp = 0;
  std::uint64_t factory_rbp = 0;
  std::uint64_t output_address = 0;
  std::uint64_t manager = 0;
  std::uint64_t slot_address = 0;
  std::uint64_t source_view = 0;
  std::uint64_t source_function_output_address = 0;
  std::uint64_t source_function_view = 0;
  std::uint64_t resolver_input_view = 0;
  std::uint64_t resolver_state = 0;
  std::uint64_t resolver_buffer_base = 0;
  std::uint64_t resolver_normalized_address = 0;
  std::uint64_t variant_view = 0;
  std::uint32_t source_length = 0;
  std::uint32_t variant_length = 0;
  std::uint64_t graphics_global = 0;
  std::uint64_t source_cache_output = 0;
  std::uint64_t resolver_total_buffer_bytes = 0;
  std::uint64_t resolver_heap_output = 0;
  std::uint64_t resolver_list_head = 0;
  std::uint64_t resolver_search_output = 0;
  bool resolver_locked_mode = false;
  bool resolver_used_heap = false;
  bool resolver_normalize_ok = false;
  std::string resolver_normalized_text;
  std::uint64_t source_resolver_output = 0;
  std::uint64_t source_output = 0;
  std::uint64_t variant_output = 0;
  std::uint64_t backend_config_address = 0;
  std::uint64_t backend_device_object = 0;
  std::uint64_t backend_dispatch_table = 0;
  std::uint64_t backend_callback_address = 0;
  std::uint64_t backend_cache_output = 0;
  std::uint64_t backend_callback_output_slot = 0;
  std::uint64_t backend_initializer_object = 0;
  std::uint64_t backend_initializer_request = 0;
  std::uint64_t backend_initializer_resource_global = 0;
  std::uint64_t backend_initializer_graphics_global = 0;
  bool backend_initializer_result = false;
  std::uint64_t backend_callback_output = 0;
  std::uint64_t backend_vcall_wrapper_address = 0;
  std::uint64_t backend_vcall_output = 0;
  std::uint64_t backend_output = 0;
  std::uint64_t final_output = 0;
  std::uint64_t backend_source_confirm = 0;
  std::uint64_t backend_variant_confirm = 0;
  std::string source_text;
  std::string variant_text;
  std::string error;
  double elapsed_seconds = 0.0;
  std::vector<Step> steps;
  std::vector<CandidateStep> candidates;
  std::vector<BackendStageStep> backend_stages;
};

std::string Narrow(const std::wstring &value) {
  if (value.empty()) return {};
  const int size = WideCharToMultiByte(
      CP_UTF8, 0, value.data(), static_cast<int>(value.size()), nullptr, 0,
      nullptr, nullptr);
  if (size <= 0) throw std::runtime_error("WideCharToMultiByte failed");
  std::string result(static_cast<std::size_t>(size), '\0');
  if (WideCharToMultiByte(
          CP_UTF8, 0, value.data(), static_cast<int>(value.size()),
          result.data(), size, nullptr, nullptr) != size) {
    throw std::runtime_error("WideCharToMultiByte failed");
  }
  return result;
}

std::string JsonEscape(const std::string &value) {
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

std::wstring Quote(const std::wstring &value) {
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

std::string Sha256(const std::filesystem::path &path) {
  BCRYPT_ALG_HANDLE algorithm = nullptr;
  BCRYPT_HASH_HANDLE hash = nullptr;
  DWORD object_size = 0;
  DWORD hash_size = 0;
  DWORD written = 0;
  if (BCryptOpenAlgorithmProvider(&algorithm, BCRYPT_SHA256_ALGORITHM, nullptr,
                                  0) != 0 ||
      BCryptGetProperty(algorithm, BCRYPT_OBJECT_LENGTH,
                        reinterpret_cast<PUCHAR>(&object_size),
                        sizeof(object_size), &written, 0) != 0 ||
      BCryptGetProperty(algorithm, BCRYPT_HASH_LENGTH,
                        reinterpret_cast<PUCHAR>(&hash_size),
                        sizeof(hash_size), &written, 0) != 0) {
    if (algorithm) BCryptCloseAlgorithmProvider(algorithm, 0);
    throw std::runtime_error("BCrypt SHA-256 initialization failed");
  }
  std::vector<std::uint8_t> object(object_size);
  std::vector<std::uint8_t> digest(hash_size);
  if (BCryptCreateHash(algorithm, &hash, object.data(), object_size, nullptr, 0,
                       0) != 0) {
    BCryptCloseAlgorithmProvider(algorithm, 0);
    throw std::runtime_error("BCryptCreateHash failed");
  }
  std::ifstream input(path, std::ios::binary);
  if (!input) {
    BCryptDestroyHash(hash);
    BCryptCloseAlgorithmProvider(algorithm, 0);
    throw std::runtime_error("cannot open executable for hashing");
  }
  std::vector<char> buffer(1 << 20);
  while (input) {
    input.read(buffer.data(), static_cast<std::streamsize>(buffer.size()));
    const auto count = input.gcount();
    if (count > 0 &&
        BCryptHashData(hash, reinterpret_cast<PUCHAR>(buffer.data()),
                       static_cast<ULONG>(count), 0) != 0) {
      BCryptDestroyHash(hash);
      BCryptCloseAlgorithmProvider(algorithm, 0);
      throw std::runtime_error("BCryptHashData failed");
    }
  }
  if (BCryptFinishHash(hash, digest.data(), hash_size, 0) != 0) {
    BCryptDestroyHash(hash);
    BCryptCloseAlgorithmProvider(algorithm, 0);
    throw std::runtime_error("BCryptFinishHash failed");
  }
  BCryptDestroyHash(hash);
  BCryptCloseAlgorithmProvider(algorithm, 0);
  std::ostringstream out;
  out << std::uppercase << std::hex << std::setfill('0');
  for (const auto byte : digest) out << std::setw(2) << int(byte);
  return out.str();
}

std::filesystem::path CurrentExecutablePath() {
  std::vector<wchar_t> buffer(32768, L'\0');
  const DWORD length = GetModuleFileNameW(
      nullptr, buffer.data(), static_cast<DWORD>(buffer.size()));
  if (length == 0 || length >= buffer.size()) {
    throw std::runtime_error("GetModuleFileNameW failed");
  }
  return std::filesystem::path(std::wstring(buffer.data(), length));
}

Options ParseOptions(int argc, wchar_t **argv) {
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
    else if (name == L"--timeout-ms") {
      const auto value = std::stoul(next());
      if (value < 1000 || value > 300000) {
        throw std::runtime_error("--timeout-ms must be in [1000,300000]");
      }
      options.timeout_ms = static_cast<DWORD>(value);
    } else if (name == L"--self-test") {
      options.self_test = true;
    } else {
      throw std::runtime_error("unknown option: " + Narrow(name));
    }
  }
  if (!options.self_test &&
      (options.exe.empty() || options.userdir.empty() ||
       options.output.empty())) {
    throw std::runtime_error(
        "--exe, --userdir, and --output are required");
  }
  return options;
}

template <typename T>
bool ReadValue(HANDLE process, std::uint64_t address, T &output) {
  SIZE_T read = 0;
  output = {};
  return address != 0 &&
      ReadProcessMemory(process, reinterpret_cast<LPCVOID>(address), &output,
                        sizeof(output), &read) != FALSE &&
      read == sizeof(output);
}

template <std::size_t Size>
bool BytesEqual(HANDLE process, std::uint64_t address,
                const std::array<std::uint8_t, Size> &expected) {
  std::array<std::uint8_t, Size> actual{};
  SIZE_T read = 0;
  return ReadProcessMemory(process, reinterpret_cast<LPCVOID>(address),
                           actual.data(), actual.size(), &read) != FALSE &&
      read == actual.size() && actual == expected;
}

bool ReadStringView(HANDLE process, std::uint64_t view, std::string &text,
                    std::uint32_t &length) {
  std::uint64_t data = 0;
  std::int32_t signed_length = 0;
  if (!ReadValue(process, view, data) ||
      !ReadValue(process, view + 8, signed_length) ||
      signed_length < 0 || signed_length > 256) {
    return false;
  }
  length = static_cast<std::uint32_t>(signed_length);
  text.assign(length, '\0');
  if (length == 0) return true;
  SIZE_T read = 0;
  return data != 0 &&
      ReadProcessMemory(process, reinterpret_cast<LPCVOID>(data), text.data(),
                        length, &read) != FALSE && read == length;
}

bool ReadCString(HANDLE process, std::uint64_t address, std::string &text,
                 std::size_t limit) {
  text.clear();
  if (address == 0 || limit == 0 || limit > 512) return false;
  for (std::size_t index = 0; index < limit; ++index) {
    char value = '\0';
    if (!ReadValue(process, address + index, value)) return false;
    if (value == '\0') return true;
    text.push_back(value);
  }
  return false;
}

bool ReadMsvcString(HANDLE process, std::uint64_t object, std::string &text,
                    std::uint64_t &length) {
  std::uint64_t capacity = 0;
  std::uint64_t data = object;
  if (!ReadValue(process, object + 0x10, length) ||
      !ReadValue(process, object + 0x18, capacity) || length > 512) {
    return false;
  }
  if (capacity >= 0x10 && !ReadValue(process, object, data)) return false;
  text.assign(static_cast<std::size_t>(length), '\0');
  if (length == 0) return true;
  SIZE_T read = 0;
  return data != 0 &&
      ReadProcessMemory(process, reinterpret_cast<LPCVOID>(data), text.data(),
                        static_cast<SIZE_T>(length), &read) != FALSE &&
      read == length;
}

bool VerifyAnchors(HANDLE process, std::uint64_t base) {
  return BytesEqual(process, base + kEntryRva, kEntryAnchor) &&
      BytesEqual(process, base + kGraphicsRva, kGraphicsAnchor) &&
      BytesEqual(process, base + kSourceEntryRva, kSourceEntryAnchor) &&
      BytesEqual(process, base + kSourceCacheResultRva,
                 kSourceCacheResultAnchor) &&
      BytesEqual(process, base + kResolverEntryRva, kResolverEntryAnchor) &&
      BytesEqual(process, base + kResolverSizeRva, kResolverSizeAnchor) &&
      BytesEqual(process, base + kResolverHeapResultRva,
                 kResolverHeapResultAnchor) &&
      BytesEqual(process, base + kResolverBufferReadyRva,
                 kResolverBufferReadyAnchor) &&
      BytesEqual(process, base + kResolverNormalizeResultRva,
                 kResolverNormalizeResultAnchor) &&
      BytesEqual(process, base + kResolverListHeadRva,
                 kResolverListHeadAnchor) &&
      BytesEqual(process, base + kResolverCandidatePrimaryResultRva,
                 kResolverCandidatePrimaryResultAnchor) &&
      BytesEqual(process, base + kResolverCandidateSecondaryEntryRva,
                 kResolverCandidateSecondaryEntryAnchor) &&
      BytesEqual(process, base + kResolverCandidateSecondaryStateRva,
                 kResolverCandidateSecondaryStateAnchor) &&
      BytesEqual(process, base + kResolverCandidateBackendCallbackEntryRva,
                 kResolverCandidateBackendCallbackEntryAnchor) &&
      BytesEqual(process, base + kResolverCandidateBackendPathResultRva,
                 kResolverCandidateBackendPathResultAnchor) &&
      BytesEqual(process, base + kResolverCandidateBackendReadResultRva,
                 kResolverCandidateBackendReadResultAnchor) &&
      BytesEqual(process, base + kResolverCandidateCallbackResultRva,
                 kResolverCandidateCallbackResultAnchor) &&
      BytesEqual(process, base + kResolverCandidateSecondaryResultRva,
                 kResolverCandidateSecondaryResultAnchor) &&
      BytesEqual(process, base + kResolverCandidateFinalResultRva,
                 kResolverCandidateFinalResultAnchor) &&
      BytesEqual(process, base + kResolverSearchResultRva,
                 kResolverSearchResultAnchor) &&
      BytesEqual(process, base + kSourceResolverResultRva,
                 kSourceResolverResultAnchor) &&
      BytesEqual(process, base + kSourceRva, kSourceAnchor) &&
      BytesEqual(process, base + kVariantRva, kVariantAnchor) &&
      BytesEqual(process, base + kBackendEntryRva, kBackendEntryAnchor) &&
      BytesEqual(process, base + kBackendCacheResultRva,
                 kBackendCacheResultAnchor) &&
      BytesEqual(process, base + kBackendCallbackEntryRva,
                 kBackendCallbackEntryAnchor) &&
      BytesEqual(process, base + kBackendInitializerGlobalsRva,
                 kBackendInitializerGlobalsAnchor) &&
      BytesEqual(process, base + kBackendStageLoopRva,
                 kBackendStageLoopAnchor) &&
      BytesEqual(process, base + kBackendHlslResultRva,
                 kBackendHlslResultAnchor) &&
      BytesEqual(process, base + kBackendShaderCacheResultRva,
                 kBackendShaderCacheResultAnchor) &&
      BytesEqual(process, base + kBackendShaderVcallEntryRva,
                 kBackendShaderVcallEntryAnchor) &&
      BytesEqual(process, base + kBackendShaderVcallResultRva,
                 kBackendShaderVcallResultAnchor) &&
      BytesEqual(process, base + kBackendShaderGetterResultRva,
                 kBackendShaderGetterResultAnchor) &&
      BytesEqual(process, base + kBackendShaderResultRva,
                 kBackendShaderResultAnchor) &&
      BytesEqual(process, base + kBackendInitializerResultRva,
                 kBackendInitializerResultAnchor) &&
      BytesEqual(process, base + kBackendCallbackOutputRva,
                 kBackendCallbackOutputAnchor) &&
      BytesEqual(process, base + kBackendVcallResultRva,
                 kBackendVcallResultAnchor) &&
      BytesEqual(process, base + kBackendRva, kBackendAnchor) &&
      BytesEqual(process, base + kReturnRva, kReturnAnchor);
}

HANDLE OpenDebugThread(DWORD thread_id) {
  return OpenThread(THREAD_GET_CONTEXT | THREAD_SET_CONTEXT |
                        THREAD_QUERY_INFORMATION,
                    FALSE, thread_id);
}

bool SetExecuteBreakpoint(HANDLE thread, std::uint64_t address,
                          bool resume_current_instruction) {
  CONTEXT context{};
  context.ContextFlags =
      CONTEXT_CONTROL | CONTEXT_INTEGER | CONTEXT_DEBUG_REGISTERS;
  if (!GetThreadContext(thread, &context)) return false;
  context.Dr0 = address;
  context.Dr1 = 0;
  context.Dr2 = 0;
  context.Dr3 = 0;
  context.Dr6 = 0;
  context.Dr7 = 1;
  if (resume_current_instruction) context.EFlags |= 0x10000U;
  return SetThreadContext(thread, &context) != FALSE;
}

bool ClearDebugRegisters(HANDLE thread) {
  CONTEXT context{};
  context.ContextFlags = CONTEXT_CONTROL | CONTEXT_DEBUG_REGISTERS;
  if (!GetThreadContext(thread, &context)) return false;
  context.Dr0 = 0;
  context.Dr1 = 0;
  context.Dr2 = 0;
  context.Dr3 = 0;
  context.Dr6 = 0;
  context.Dr7 = 0;
  return SetThreadContext(thread, &context) != FALSE;
}

std::string Classify(const Capture &capture) {
  if (!capture.return_observed || capture.final_output != 0) {
    if (capture.return_observed && capture.graphics_observed &&
        capture.graphics_global != 0 && capture.source_observed &&
        capture.source_output != 0 && capture.variant_observed &&
        capture.variant_output != 0 && capture.backend_observed &&
        capture.backend_output != 0 && capture.final_output != 0) {
      return "all-nonnull";
    }
    return "unclassified";
  }
  if (capture.graphics_observed && capture.graphics_global == 0) {
    return "graphics-global-null";
  }
  if (capture.source_observed && capture.source_output == 0) {
    return "source-lookup-null";
  }
  if (capture.source_observed && capture.source_output != 0 &&
      capture.variant_observed && capture.variant_output == 0) {
    return "variant-lookup-null";
  }
  if (capture.source_observed && capture.source_output != 0 &&
      capture.variant_observed && capture.variant_output != 0 &&
      capture.backend_observed && capture.backend_output == 0) {
    return "backend-creation-null";
  }
  return "unclassified";
}

std::string ClassifySourceDetail(const Capture &capture) {
  if (!capture.source_detail_entry_observed ||
      !capture.source_cache_observed) {
    return "not-observed";
  }
  if (capture.source_cache_output != 0) {
    return capture.source_resolver_observed
        ? "source-detail-inconsistent"
        : "source-cache-hit";
  }
  if (!capture.source_resolver_observed) return "source-detail-incomplete";
  return capture.source_resolver_output == 0
      ? "source-resolver-null"
      : "source-resolver-nonnull";
}

std::string ClassifyResolverDetail(const Capture &capture) {
  if (!capture.resolver_entry_observed || !capture.resolver_size_observed) {
    return "not-observed";
  }
  if (capture.resolver_used_heap &&
      capture.resolver_heap_result_observed &&
      capture.resolver_heap_output == 0) {
    return "resolver-scratch-allocation-null";
  }
  if (!capture.resolver_buffer_ready_observed ||
      !capture.resolver_normalize_observed) {
    return "resolver-detail-incomplete";
  }
  if (!capture.resolver_normalize_ok) {
    return "resolver-path-preprocess-rejected";
  }
  if (!capture.resolver_list_head_observed) {
    return "resolver-detail-incomplete";
  }
  if (capture.resolver_list_head == 0) return "resolver-registry-empty";
  if (!capture.resolver_search_observed) return "resolver-detail-incomplete";
  return capture.resolver_search_output == 0
      ? "resolver-candidates-all-reject"
      : "resolver-candidate-accepted";
}

std::string ClassifyBackendDetail(const Capture &capture) {
  if (!capture.backend_callback_entry_observed ||
      !capture.backend_initializer_globals_observed ||
      !capture.backend_initializer_result_observed) {
    return "not-observed";
  }
  if (capture.backend_initializer_resource_global == 0 ||
      capture.backend_initializer_graphics_global == 0) {
    return capture.backend_initializer_result
        ? "backend-detail-inconsistent"
        : "backend-initializer-global-null";
  }
  for (const auto &stage : capture.backend_stages) {
    if (!stage.active) continue;
    if (stage.hlsl_result_observed && !stage.hlsl_ok) {
      return capture.backend_initializer_result
          ? "backend-detail-inconsistent"
          : "backend-hlsl-generation-null";
    }
    if (stage.shader_result_observed && stage.shader_output == 0) {
      if (capture.backend_initializer_result) {
        return "backend-detail-inconsistent";
      }
      if (stage.shader_cache_result_observed &&
          stage.shader_cache_output == 0 &&
          stage.shader_vcall_result_observed &&
          stage.shader_vcall_output == 0) {
        return "backend-shader-vcall-null";
      }
      return "backend-shader-acquisition-null";
    }
  }
  return capture.backend_initializer_result
      ? "backend-initializer-success"
      : "backend-initializer-false-unclassified";
}

Stage NextAfterGraphics(std::uint64_t output) {
  return output == 0 ? Stage::returned : Stage::source_entry;
}

Stage NextAfterSourceCache(std::uint64_t output) {
  return output == 0 ? Stage::resolver_entry : Stage::source;
}

Stage NextAfterResolverSize(std::uint64_t bytes) {
  return bytes < 0x200 ? Stage::resolver_buffer_ready
                       : Stage::resolver_heap_result;
}

Stage NextAfterResolverHeap(std::uint64_t output) {
  return output == 0 ? Stage::source_resolver_result
                     : Stage::resolver_buffer_ready;
}

Stage NextAfterResolverNormalize(bool ok) {
  return ok ? Stage::resolver_list_head : Stage::source_resolver_result;
}

Stage NextAfterSource(std::uint64_t output) {
  return output == 0 ? Stage::returned : Stage::variant;
}

Stage NextAfterVariant(std::uint64_t output) {
  return output == 0 ? Stage::returned : Stage::backend_entry;
}

std::uint64_t TargetRvaForStage(Stage stage) {
  switch (stage) {
    case Stage::entry: return kEntryRva;
    case Stage::graphics: return kGraphicsRva;
    case Stage::source_entry: return kSourceEntryRva;
    case Stage::source_cache_result: return kSourceCacheResultRva;
    case Stage::resolver_entry: return kResolverEntryRva;
    case Stage::resolver_size: return kResolverSizeRva;
    case Stage::resolver_heap_result: return kResolverHeapResultRva;
    case Stage::resolver_buffer_ready: return kResolverBufferReadyRva;
    case Stage::resolver_normalize_result:
      return kResolverNormalizeResultRva;
    case Stage::resolver_list_head: return kResolverListHeadRva;
    case Stage::resolver_candidate_primary_result:
      return kResolverCandidatePrimaryResultRva;
    case Stage::resolver_candidate_secondary_entry:
      return kResolverCandidateSecondaryEntryRva;
    case Stage::resolver_candidate_secondary_state:
      return kResolverCandidateSecondaryStateRva;
    case Stage::resolver_candidate_backend_callback_entry:
      return kResolverCandidateBackendCallbackEntryRva;
    case Stage::resolver_candidate_backend_path_result:
      return kResolverCandidateBackendPathResultRva;
    case Stage::resolver_candidate_backend_read_result:
      return kResolverCandidateBackendReadResultRva;
    case Stage::resolver_candidate_callback_result:
      return kResolverCandidateCallbackResultRva;
    case Stage::resolver_candidate_secondary_result:
      return kResolverCandidateSecondaryResultRva;
    case Stage::resolver_candidate_final_result:
      return kResolverCandidateFinalResultRva;
    case Stage::resolver_search_result: return kResolverSearchResultRva;
    case Stage::source_resolver_result: return kSourceResolverResultRva;
    case Stage::source: return kSourceRva;
    case Stage::variant: return kVariantRva;
    case Stage::backend_entry: return kBackendEntryRva;
    case Stage::backend_cache_result: return kBackendCacheResultRva;
    case Stage::backend_callback_entry: return kBackendCallbackEntryRva;
    case Stage::backend_initializer_globals:
      return kBackendInitializerGlobalsRva;
    case Stage::backend_stage_loop: return kBackendStageLoopRva;
    case Stage::backend_hlsl_result: return kBackendHlslResultRva;
    case Stage::backend_shader_cache_result:
      return kBackendShaderCacheResultRva;
    case Stage::backend_shader_vcall_entry:
      return kBackendShaderVcallEntryRva;
    case Stage::backend_shader_vcall_result:
      return kBackendShaderVcallResultRva;
    case Stage::backend_shader_getter_result:
      return kBackendShaderGetterResultRva;
    case Stage::backend_shader_result: return kBackendShaderResultRva;
    case Stage::backend_initializer_result:
      return kBackendInitializerResultRva;
    case Stage::backend_callback_output: return kBackendCallbackOutputRva;
    case Stage::backend_vcall_result: return kBackendVcallResultRva;
    case Stage::backend: return kBackendRva;
    case Stage::returned: return kReturnRva;
    case Stage::complete: return 0;
  }
  return 0;
}

const char *StageName(Stage stage) {
  switch (stage) {
    case Stage::entry: return "entry";
    case Stage::graphics: return "graphics";
    case Stage::source_entry: return "source-entry";
    case Stage::source_cache_result: return "source-cache-result";
    case Stage::resolver_entry: return "resolver-entry";
    case Stage::resolver_size: return "resolver-size";
    case Stage::resolver_heap_result: return "resolver-heap-result";
    case Stage::resolver_buffer_ready: return "resolver-buffer-ready";
    case Stage::resolver_normalize_result: return "resolver-normalize-result";
    case Stage::resolver_list_head: return "resolver-list-head";
    case Stage::resolver_candidate_primary_result:
      return "resolver-candidate-primary-result";
    case Stage::resolver_candidate_secondary_entry:
      return "resolver-candidate-secondary-entry";
    case Stage::resolver_candidate_secondary_state:
      return "resolver-candidate-secondary-state";
    case Stage::resolver_candidate_backend_callback_entry:
      return "resolver-candidate-backend-callback-entry";
    case Stage::resolver_candidate_backend_path_result:
      return "resolver-candidate-backend-path-result";
    case Stage::resolver_candidate_backend_read_result:
      return "resolver-candidate-backend-read-result";
    case Stage::resolver_candidate_callback_result:
      return "resolver-candidate-callback-result";
    case Stage::resolver_candidate_secondary_result:
      return "resolver-candidate-secondary-result";
    case Stage::resolver_candidate_final_result:
      return "resolver-candidate-final-result";
    case Stage::resolver_search_result: return "resolver-search-result";
    case Stage::source_resolver_result: return "source-resolver-result";
    case Stage::source: return "source";
    case Stage::variant: return "variant";
    case Stage::backend_entry: return "backend-entry";
    case Stage::backend_cache_result: return "backend-cache-result";
    case Stage::backend_callback_entry: return "backend-callback-entry";
    case Stage::backend_initializer_globals:
      return "backend-initializer-globals";
    case Stage::backend_stage_loop: return "backend-stage-loop";
    case Stage::backend_hlsl_result: return "backend-hlsl-result";
    case Stage::backend_shader_cache_result:
      return "backend-shader-cache-result";
    case Stage::backend_shader_vcall_entry:
      return "backend-shader-vcall-entry";
    case Stage::backend_shader_vcall_result:
      return "backend-shader-vcall-result";
    case Stage::backend_shader_getter_result:
      return "backend-shader-getter-result";
    case Stage::backend_shader_result: return "backend-shader-result";
    case Stage::backend_initializer_result:
      return "backend-initializer-result";
    case Stage::backend_callback_output: return "backend-callback-output";
    case Stage::backend_vcall_result: return "backend-vcall-result";
    case Stage::backend: return "backend";
    case Stage::returned: return "return";
    case Stage::complete: return "complete";
  }
  return "unknown";
}

void AddStep(Capture &capture, const char *name, DWORD thread_id,
             std::uint64_t rip,
             const std::chrono::steady_clock::time_point &started) {
  Step step;
  step.name = name;
  step.thread_id = thread_id;
  step.rip = rip;
  step.elapsed_seconds = std::chrono::duration<double>(
      std::chrono::steady_clock::now() - started).count();
  capture.steps.push_back(std::move(step));
}

std::string CaptureJson(const Capture &capture, const Options &options,
                        Stage final_stage) {
  std::ostringstream out;
  out << std::boolalpha << std::setprecision(9);
  out << "{\n";
  out << "  \"schema\": \"xar-particle2-factory-debug-capture-v3\",\n";
  out << "  \"result\": \"" << JsonEscape(capture.result) << "\",\n";
  out << "  \"reason\": \"" << JsonEscape(capture.reason) << "\",\n";
  out << "  \"classification\": \""
      << JsonEscape(capture.classification) << "\",\n";
  out << "  \"source_detail_classification\": \""
      << JsonEscape(ClassifySourceDetail(capture)) << "\",\n";
  out << "  \"resolver_detail_classification\": \""
      << JsonEscape(ClassifyResolverDetail(capture)) << "\",\n";
  out << "  \"backend_detail_classification\": \""
      << JsonEscape(ClassifyBackendDetail(capture)) << "\",\n";
  out << "  \"final_stage\": \"" << StageName(final_stage) << "\",\n";
  out << "  \"capture_status\": \""
      << JsonEscape(capture.capture_status) << "\",\n";
  out << "  \"cleanup_status\": \""
      << JsonEscape(capture.cleanup_status) << "\",\n";
  out << "  \"process_exit_kind\": \""
      << JsonEscape(capture.process_exit_kind) << "\",\n";
  out << "  \"exe\": \""
      << JsonEscape(Narrow(options.exe.wstring())) << "\",\n";
  out << "  \"userdir\": \""
      << JsonEscape(Narrow(options.userdir.wstring())) << "\",\n";
  out << "  \"exe_sha256\": \"" << capture.exe_sha256 << "\",\n";
  out << "  \"probe_sha256\": \"" << capture.probe_sha256 << "\",\n";
  out << "  \"exe_size\": " << capture.exe_size << ",\n";
  out << "  \"expected_exe_sha256\": \""
      << Narrow(kExpectedExeSha256) << "\",\n";
  out << "  \"expected_exe_size\": " << kExpectedExeSize << ",\n";
  out << "  \"ck3_started\": " << capture.ck3_started << ",\n";
  out << "  \"debugger_attached\": " << capture.debugger_attached << ",\n";
  out << "  \"primary_thread_resumed\": "
      << capture.primary_thread_resumed << ",\n";
  out << "  \"input_sent\": false,\n";
  out << "  \"anchors_verified\": " << capture.anchors_verified << ",\n";
  out << "  \"target_tuple_observed\": "
      << capture.target_tuple_observed << ",\n";
  out << "  \"pid\": " << capture.pid << ",\n";
  out << "  \"target_thread_id\": " << capture.target_thread_id << ",\n";
  out << "  \"image_base\": \"" << Hex(capture.image_base) << "\",\n";
  out << "  \"elapsed_seconds\": " << capture.elapsed_seconds << ",\n";
  out << "  \"tuple\": {\n";
  out << "    \"source\": \"" << JsonEscape(capture.source_text) << "\",\n";
  out << "    \"source_length\": " << capture.source_length << ",\n";
  out << "    \"variant\": \"" << JsonEscape(capture.variant_text) << "\",\n";
  out << "    \"variant_length\": " << capture.variant_length << "\n";
  out << "  },\n";
  out << "  \"addresses\": {\n";
  out << "    \"caller_rbp\": \"" << Hex(capture.caller_rbp) << "\",\n";
  out << "    \"factory_rbp\": \"" << Hex(capture.factory_rbp) << "\",\n";
  out << "    \"output\": \"" << Hex(capture.output_address) << "\",\n";
  out << "    \"manager\": \"" << Hex(capture.manager) << "\",\n";
  out << "    \"slot\": \"" << Hex(capture.slot_address) << "\",\n";
  out << "    \"source_view\": \"" << Hex(capture.source_view) << "\",\n";
  out << "    \"source_function_output\": \""
      << Hex(capture.source_function_output_address) << "\",\n";
  out << "    \"source_function_view\": \""
      << Hex(capture.source_function_view) << "\",\n";
  out << "    \"resolver_input_view\": \""
      << Hex(capture.resolver_input_view) << "\",\n";
  out << "    \"resolver_state\": \""
      << Hex(capture.resolver_state) << "\",\n";
  out << "    \"resolver_buffer_base\": \""
      << Hex(capture.resolver_buffer_base) << "\",\n";
  out << "    \"resolver_normalized_address\": \""
      << Hex(capture.resolver_normalized_address) << "\",\n";
  out << "    \"variant_view\": \"" << Hex(capture.variant_view) << "\"\n";
  out << "  },\n";
  out << "  \"observations\": {\n";
  out << "    \"graphics_observed\": " << capture.graphics_observed << ",\n";
  out << "    \"graphics_global\": \"" << Hex(capture.graphics_global) << "\",\n";
  out << "    \"source_detail_entry_observed\": "
      << capture.source_detail_entry_observed << ",\n";
  out << "    \"source_cache_observed\": "
      << capture.source_cache_observed << ",\n";
  out << "    \"source_cache_output\": \""
      << Hex(capture.source_cache_output) << "\",\n";
  out << "    \"resolver_entry_observed\": "
      << capture.resolver_entry_observed << ",\n";
  out << "    \"resolver_size_observed\": "
      << capture.resolver_size_observed << ",\n";
  out << "    \"resolver_total_buffer_bytes\": "
      << capture.resolver_total_buffer_bytes << ",\n";
  out << "    \"resolver_locked_mode\": "
      << capture.resolver_locked_mode << ",\n";
  out << "    \"resolver_used_heap\": " << capture.resolver_used_heap
      << ",\n";
  out << "    \"resolver_heap_result_observed\": "
      << capture.resolver_heap_result_observed << ",\n";
  out << "    \"resolver_heap_output\": \""
      << Hex(capture.resolver_heap_output) << "\",\n";
  out << "    \"resolver_buffer_ready_observed\": "
      << capture.resolver_buffer_ready_observed << ",\n";
  out << "    \"resolver_normalize_observed\": "
      << capture.resolver_normalize_observed << ",\n";
  out << "    \"resolver_normalize_ok\": "
      << capture.resolver_normalize_ok << ",\n";
  out << "    \"resolver_normalized_text\": \""
      << JsonEscape(capture.resolver_normalized_text) << "\",\n";
  out << "    \"resolver_list_head_observed\": "
      << capture.resolver_list_head_observed << ",\n";
  out << "    \"resolver_list_head\": \""
      << Hex(capture.resolver_list_head) << "\",\n";
  out << "    \"resolver_search_observed\": "
      << capture.resolver_search_observed << ",\n";
  out << "    \"resolver_search_output\": \""
      << Hex(capture.resolver_search_output) << "\",\n";
  out << "    \"source_resolver_observed\": "
      << capture.source_resolver_observed << ",\n";
  out << "    \"source_resolver_output\": \""
      << Hex(capture.source_resolver_output) << "\",\n";
  out << "    \"source_observed\": " << capture.source_observed << ",\n";
  out << "    \"source_output\": \"" << Hex(capture.source_output) << "\",\n";
  out << "    \"variant_observed\": " << capture.variant_observed << ",\n";
  out << "    \"variant_output\": \"" << Hex(capture.variant_output) << "\",\n";
  out << "    \"backend_entry_observed\": "
      << capture.backend_entry_observed << ",\n";
  out << "    \"backend_config_address\": \""
      << Hex(capture.backend_config_address) << "\",\n";
  out << "    \"backend_device_object\": \""
      << Hex(capture.backend_device_object) << "\",\n";
  out << "    \"backend_dispatch_table\": \""
      << Hex(capture.backend_dispatch_table) << "\",\n";
  out << "    \"backend_callback_address\": \""
      << Hex(capture.backend_callback_address) << "\",\n";
  out << "    \"backend_cache_result_observed\": "
      << capture.backend_cache_result_observed << ",\n";
  out << "    \"backend_cache_output\": \""
      << Hex(capture.backend_cache_output) << "\",\n";
  out << "    \"backend_callback_entry_observed\": "
      << capture.backend_callback_entry_observed << ",\n";
  out << "    \"backend_callback_output_slot\": \""
      << Hex(capture.backend_callback_output_slot) << "\",\n";
  out << "    \"backend_initializer_globals_observed\": "
      << capture.backend_initializer_globals_observed << ",\n";
  out << "    \"backend_initializer_object\": \""
      << Hex(capture.backend_initializer_object) << "\",\n";
  out << "    \"backend_initializer_request\": \""
      << Hex(capture.backend_initializer_request) << "\",\n";
  out << "    \"backend_initializer_resource_global\": \""
      << Hex(capture.backend_initializer_resource_global) << "\",\n";
  out << "    \"backend_initializer_graphics_global\": \""
      << Hex(capture.backend_initializer_graphics_global) << "\",\n";
  out << "    \"backend_initializer_result_observed\": "
      << capture.backend_initializer_result_observed << ",\n";
  out << "    \"backend_initializer_result\": "
      << capture.backend_initializer_result << ",\n";
  out << "    \"backend_callback_output_observed\": "
      << capture.backend_callback_output_observed << ",\n";
  out << "    \"backend_callback_output\": \""
      << Hex(capture.backend_callback_output) << "\",\n";
  out << "    \"backend_vcall_result_observed\": "
      << capture.backend_vcall_result_observed << ",\n";
  out << "    \"backend_vcall_wrapper_address\": \""
      << Hex(capture.backend_vcall_wrapper_address) << "\",\n";
  out << "    \"backend_vcall_output\": \""
      << Hex(capture.backend_vcall_output) << "\",\n";
  out << "    \"backend_observed\": " << capture.backend_observed << ",\n";
  out << "    \"backend_output\": \"" << Hex(capture.backend_output) << "\",\n";
  out << "    \"backend_source_confirm\": \""
      << Hex(capture.backend_source_confirm) << "\",\n";
  out << "    \"backend_variant_confirm\": \""
      << Hex(capture.backend_variant_confirm) << "\",\n";
  out << "    \"return_observed\": " << capture.return_observed << ",\n";
  out << "    \"final_output\": \"" << Hex(capture.final_output) << "\"\n";
  out << "  },\n";
  out << "  \"backend_initializer_stages\": [";
  for (std::size_t i = 0; i < capture.backend_stages.size(); ++i) {
    const auto &item = capture.backend_stages[i];
    if (i != 0) out << ',';
    out << "\n    {\"index\":" << item.index
        << ",\"name_object\":\"" << Hex(item.name_object)
        << "\",\"name_length\":" << item.name_length
        << ",\"name\":\"" << JsonEscape(item.name)
        << "\",\"active\":" << item.active
        << ",\"hlsl_result_observed\":" << item.hlsl_result_observed
        << ",\"hlsl_ok\":" << item.hlsl_ok
        << ",\"shader_cache_result_observed\":"
        << item.shader_cache_result_observed
        << ",\"shader_cache_output\":\"" << Hex(item.shader_cache_output)
        << "\",\"shader_vcall_entry_observed\":"
        << item.shader_vcall_entry_observed
        << ",\"shader_manager\":\"" << Hex(item.shader_manager)
        << "\",\"shader_dispatch_table\":\""
        << Hex(item.shader_dispatch_table)
        << "\",\"shader_callback_address\":\""
        << Hex(item.shader_callback_address)
        << "\",\"shader_vcall_result_observed\":"
        << item.shader_vcall_result_observed
        << ",\"shader_vcall_wrapper_address\":\""
        << Hex(item.shader_vcall_wrapper_address)
        << "\",\"shader_vcall_output\":\""
        << Hex(item.shader_vcall_output)
        << "\",\"shader_getter_result_observed\":"
        << item.shader_getter_result_observed
        << ",\"shader_getter_output\":\""
        << Hex(item.shader_getter_output)
        << "\",\"shader_result_observed\":"
        << item.shader_result_observed
        << ",\"shader_output\":\"" << Hex(item.shader_output) << "\"}";
  }
  if (!capture.backend_stages.empty()) out << '\n';
  out << "  ],\n";
  out << "  \"resolver_candidates\": [";
  for (std::size_t i = 0; i < capture.candidates.size(); ++i) {
    const auto &candidate = capture.candidates[i];
    if (i != 0) out << ',';
    out << "\n    {\"address\":\"" << Hex(candidate.address)
        << "\",\"prefix_address\":\"" << Hex(candidate.prefix_address)
        << "\",\"prefix_text\":\"" << JsonEscape(candidate.prefix_text)
        << "\",\"backend_object\":\"" << Hex(candidate.backend_object)
        << "\",\"rewrite_address\":\"" << Hex(candidate.rewrite_address)
        << "\",\"rewrite_offset\":" << candidate.rewrite_offset
        << ",\"dispatch_table\":\"" << Hex(candidate.dispatch_table)
        << "\",\"callback_address\":\"" << Hex(candidate.callback_address)
        << "\",\"next_address\":\"" << Hex(candidate.next_address)
        << "\",\"primary_observed\":" << candidate.primary_observed
        << ",\"primary_result\":" << candidate.primary_result
        << ",\"secondary_observed\":" << candidate.secondary_observed
        << ",\"secondary_result\":" << candidate.secondary_result
        << ",\"secondary_state_observed\":"
        << candidate.secondary_state_observed
        << ",\"secondary_state_f9\":"
        << static_cast<unsigned>(candidate.secondary_state_f9)
        << ",\"secondary_state_fa\":"
        << static_cast<unsigned>(candidate.secondary_state_fa)
        << ",\"backend_callback_entry_observed\":"
        << candidate.backend_callback_entry_observed
        << ",\"callback_output_address\":\""
        << Hex(candidate.callback_output_address)
        << "\",\"backend_root_text\":\""
        << JsonEscape(candidate.backend_root_text)
        << "\",\"backend_requested_text\":\""
        << JsonEscape(candidate.backend_requested_text)
        << "\",\"backend_path_observed\":"
        << candidate.backend_path_observed
        << ",\"backend_path_address\":\""
        << Hex(candidate.backend_path_address)
        << "\",\"backend_path_text\":\""
        << JsonEscape(candidate.backend_path_text)
        << "\",\"backend_read_observed\":"
        << candidate.backend_read_observed
        << ",\"backend_read_result\":"
        << candidate.backend_read_result
        << ",\"secondary_callback_observed\":"
        << candidate.secondary_callback_observed
        << ",\"secondary_callback_result\":"
        << candidate.secondary_callback_result
        << ",\"secondary_callback_result_type_observed\":"
        << candidate.secondary_callback_result_type_observed
        << ",\"secondary_callback_result_type\":"
        << candidate.secondary_callback_result_type
        << ",\"final_observed\":" << candidate.final_observed
        << ",\"final_result\":" << candidate.final_result << '}';
  }
  if (!capture.candidates.empty()) out << '\n' << "  ";
  out << "],\n";
  out << "  \"cleanup\": {\n";
  out << "    \"policy\": \"terminate-after-capture\",\n";
  out << "    \"diagnostic_termination_requested\": "
      << capture.diagnostic_termination_requested << ",\n";
  out << "    \"native_continuation_claimed\": "
      << capture.native_continuation_claimed << ",\n";
  out << "    \"debug_registers_cleared\": "
      << capture.debug_registers_cleared << ",\n";
  out << "    \"capture_event_continued\": "
      << capture.capture_event_continued << ",\n";
  out << "    \"debugger_detached\": "
      << capture.debugger_detached << ",\n";
  out << "    \"natural_exit_observed\": "
      << capture.natural_exit_observed << ",\n";
  out << "    \"cleanup_forced\": " << capture.cleanup_forced << ",\n";
  out << "    \"process_terminated\": " << capture.process_terminated << ",\n";
  out << "    \"exit_event_observed\": " << capture.exit_event_observed << "\n";
  out << "  },\n";
  out << "  \"product_evidence\": {\n";
  out << "    \"bridge_connected\": false,\n";
  out << "    \"map_ready\": false,\n";
  out << "    \"mailbox_ready\": false,\n";
  out << "    \"query_count\": 0,\n";
  out << "    \"gameplay_input_count\": 0,\n";
  out << "    \"readiness_promoted\": false\n";
  out << "  },\n";
  out << "  \"error\": \"" << JsonEscape(capture.error) << "\",\n";
  out << "  \"steps\": [";
  for (std::size_t i = 0; i < capture.steps.size(); ++i) {
    const auto &step = capture.steps[i];
    if (i != 0) out << ',';
    out << "\n    {\"name\":\"" << JsonEscape(step.name)
        << "\",\"thread_id\":" << step.thread_id
        << ",\"rip\":\"" << Hex(step.rip)
        << "\",\"elapsed_seconds\":" << step.elapsed_seconds << '}';
  }
  if (!capture.steps.empty()) out << '\n' << "  ";
  out << "]\n";
  out << "}\n";
  return out.str();
}

void AtomicWrite(const std::filesystem::path &output,
                 const std::string &content) {
  if (std::filesystem::exists(output)) {
    throw std::runtime_error("output already exists");
  }
  const auto temporary = output.wstring() + L".tmp";
  if (std::filesystem::exists(temporary)) {
    throw std::runtime_error("temporary output already exists");
  }
  if (!output.parent_path().empty() &&
      !std::filesystem::is_directory(output.parent_path())) {
    throw std::runtime_error("output parent does not exist");
  }
  HANDLE file = CreateFileW(temporary.c_str(), GENERIC_WRITE, 0, nullptr,
                            CREATE_NEW, FILE_ATTRIBUTE_NORMAL, nullptr);
  if (file == INVALID_HANDLE_VALUE) {
    throw std::runtime_error("cannot create temporary output");
  }
  std::size_t cursor = 0;
  bool write_ok = true;
  while (cursor < content.size()) {
    const auto remaining = content.size() - cursor;
    const DWORD chunk = static_cast<DWORD>(
        remaining > 0x40000000ULL ? 0x40000000ULL : remaining);
    DWORD written = 0;
    if (!WriteFile(file, content.data() + cursor, chunk, &written, nullptr) ||
        written != chunk) {
      write_ok = false;
      break;
    }
    cursor += written;
  }
  const bool flushed = write_ok && FlushFileBuffers(file) != FALSE;
  const bool closed = CloseHandle(file) != FALSE;
  if (!write_ok || !flushed || !closed) {
    DeleteFileW(temporary.c_str());
    throw std::runtime_error("durable temporary output write failed");
  }
  if (!MoveFileExW(temporary.c_str(), output.c_str(),
                   MOVEFILE_WRITE_THROUGH)) {
    DeleteFileW(temporary.c_str());
    throw std::runtime_error("atomic output rename failed");
  }
}

bool SelfTest() {
  if (NextAfterGraphics(0) != Stage::returned ||
      NextAfterGraphics(1) != Stage::source_entry ||
      NextAfterSourceCache(0) != Stage::resolver_entry ||
      NextAfterSourceCache(1) != Stage::source ||
      NextAfterResolverSize(0x1FF) != Stage::resolver_buffer_ready ||
      NextAfterResolverSize(0x200) != Stage::resolver_heap_result ||
      NextAfterResolverHeap(0) != Stage::source_resolver_result ||
      NextAfterResolverHeap(1) != Stage::resolver_buffer_ready ||
      NextAfterResolverNormalize(false) != Stage::source_resolver_result ||
      NextAfterResolverNormalize(true) != Stage::resolver_list_head ||
      NextAfterSource(0) != Stage::returned ||
      NextAfterSource(1) != Stage::variant ||
      NextAfterVariant(0) != Stage::returned ||
      NextAfterVariant(1) != Stage::backend_entry ||
      TargetRvaForStage(Stage::entry) != kEntryRva ||
      TargetRvaForStage(Stage::graphics) != kGraphicsRva ||
      TargetRvaForStage(Stage::source_entry) != kSourceEntryRva ||
      TargetRvaForStage(Stage::source_cache_result) !=
          kSourceCacheResultRva ||
      TargetRvaForStage(Stage::resolver_entry) != kResolverEntryRva ||
      TargetRvaForStage(Stage::resolver_size) != kResolverSizeRva ||
      TargetRvaForStage(Stage::resolver_heap_result) !=
          kResolverHeapResultRva ||
      TargetRvaForStage(Stage::resolver_buffer_ready) !=
          kResolverBufferReadyRva ||
      TargetRvaForStage(Stage::resolver_normalize_result) !=
          kResolverNormalizeResultRva ||
      TargetRvaForStage(Stage::resolver_list_head) !=
          kResolverListHeadRva ||
      TargetRvaForStage(Stage::resolver_candidate_primary_result) !=
          kResolverCandidatePrimaryResultRva ||
      TargetRvaForStage(Stage::resolver_candidate_secondary_entry) !=
          kResolverCandidateSecondaryEntryRva ||
      TargetRvaForStage(Stage::resolver_candidate_secondary_state) !=
          kResolverCandidateSecondaryStateRva ||
      TargetRvaForStage(
          Stage::resolver_candidate_backend_callback_entry) !=
          kResolverCandidateBackendCallbackEntryRva ||
      TargetRvaForStage(Stage::resolver_candidate_backend_path_result) !=
          kResolverCandidateBackendPathResultRva ||
      TargetRvaForStage(Stage::resolver_candidate_backend_read_result) !=
          kResolverCandidateBackendReadResultRva ||
      TargetRvaForStage(Stage::resolver_candidate_callback_result) !=
          kResolverCandidateCallbackResultRva ||
      TargetRvaForStage(Stage::resolver_candidate_secondary_result) !=
          kResolverCandidateSecondaryResultRva ||
      TargetRvaForStage(Stage::resolver_candidate_final_result) !=
          kResolverCandidateFinalResultRva ||
      TargetRvaForStage(Stage::resolver_search_result) !=
          kResolverSearchResultRva ||
      TargetRvaForStage(Stage::source_resolver_result) !=
          kSourceResolverResultRva ||
      TargetRvaForStage(Stage::source) != kSourceRva ||
      TargetRvaForStage(Stage::variant) != kVariantRva ||
      TargetRvaForStage(Stage::backend_entry) != kBackendEntryRva ||
      TargetRvaForStage(Stage::backend_cache_result) !=
          kBackendCacheResultRva ||
      TargetRvaForStage(Stage::backend_callback_entry) !=
          kBackendCallbackEntryRva ||
      TargetRvaForStage(Stage::backend_initializer_globals) !=
          kBackendInitializerGlobalsRva ||
      TargetRvaForStage(Stage::backend_stage_loop) !=
          kBackendStageLoopRva ||
      TargetRvaForStage(Stage::backend_hlsl_result) !=
          kBackendHlslResultRva ||
      TargetRvaForStage(Stage::backend_shader_cache_result) !=
          kBackendShaderCacheResultRva ||
      TargetRvaForStage(Stage::backend_shader_vcall_entry) !=
          kBackendShaderVcallEntryRva ||
      TargetRvaForStage(Stage::backend_shader_vcall_result) !=
          kBackendShaderVcallResultRva ||
      TargetRvaForStage(Stage::backend_shader_getter_result) !=
          kBackendShaderGetterResultRva ||
      TargetRvaForStage(Stage::backend_shader_result) !=
          kBackendShaderResultRva ||
      TargetRvaForStage(Stage::backend_initializer_result) !=
          kBackendInitializerResultRva ||
      TargetRvaForStage(Stage::backend_callback_output) !=
          kBackendCallbackOutputRva ||
      TargetRvaForStage(Stage::backend_vcall_result) !=
          kBackendVcallResultRva ||
      TargetRvaForStage(Stage::backend) != kBackendRva ||
      TargetRvaForStage(Stage::returned) != kReturnRva ||
      TargetRvaForStage(Stage::complete) != 0) {
    return false;
  }
  Capture value;
  value.return_observed = true;
  value.graphics_observed = true;
  value.graphics_global = 1;
  value.source_observed = true;
  value.source_output = 0;
  if (Classify(value) != "source-lookup-null") return false;
  value.source_output = 1;
  value.variant_observed = true;
  value.variant_output = 0;
  if (Classify(value) != "variant-lookup-null") return false;
  value.variant_output = 1;
  value.backend_observed = true;
  value.backend_output = 0;
  if (Classify(value) != "backend-creation-null") return false;
  value.backend_output = 1;
  value.final_output = 1;
  if (Classify(value) != "all-nonnull") return false;
  value.final_output = 0;
  value.graphics_global = 0;
  value.source_observed = false;
  value.variant_observed = false;
  value.backend_observed = false;
  if (Classify(value) != "graphics-global-null") return false;
  Capture backend_detail;
  backend_detail.backend_callback_entry_observed = true;
  backend_detail.backend_initializer_globals_observed = true;
  backend_detail.backend_initializer_result_observed = true;
  if (ClassifyBackendDetail(backend_detail) !=
      "backend-initializer-global-null") return false;
  backend_detail.backend_initializer_resource_global = 1;
  backend_detail.backend_initializer_graphics_global = 1;
  BackendStageStep backend_stage;
  backend_stage.active = true;
  backend_stage.hlsl_result_observed = true;
  backend_stage.hlsl_ok = false;
  backend_detail.backend_stages.push_back(backend_stage);
  if (ClassifyBackendDetail(backend_detail) !=
      "backend-hlsl-generation-null") return false;
  backend_detail.backend_stages.back().hlsl_ok = true;
  backend_detail.backend_stages.back().shader_result_observed = true;
  backend_detail.backend_stages.back().shader_cache_result_observed = true;
  backend_detail.backend_stages.back().shader_vcall_result_observed = true;
  if (ClassifyBackendDetail(backend_detail) !=
      "backend-shader-vcall-null") return false;
  backend_detail.backend_stages.back().shader_output = 1;
  backend_detail.backend_initializer_result = true;
  if (ClassifyBackendDetail(backend_detail) !=
      "backend-initializer-success") return false;
  Capture detail;
  if (ClassifySourceDetail(detail) != "not-observed") return false;
  detail.source_detail_entry_observed = true;
  detail.source_cache_observed = true;
  if (ClassifySourceDetail(detail) != "source-detail-incomplete") return false;
  detail.source_resolver_observed = true;
  if (ClassifySourceDetail(detail) != "source-resolver-null") return false;
  detail.source_resolver_output = 1;
  if (ClassifySourceDetail(detail) != "source-resolver-nonnull") return false;
  detail.source_cache_output = 1;
  detail.source_resolver_observed = false;
  if (ClassifySourceDetail(detail) != "source-cache-hit") return false;
  Capture resolver;
  resolver.resolver_entry_observed = true;
  resolver.resolver_size_observed = true;
  resolver.resolver_buffer_ready_observed = true;
  resolver.resolver_normalize_observed = true;
  if (ClassifyResolverDetail(resolver) !=
      "resolver-path-preprocess-rejected") return false;
  resolver.resolver_normalize_ok = true;
  resolver.resolver_list_head_observed = true;
  if (ClassifyResolverDetail(resolver) != "resolver-registry-empty") {
    return false;
  }
  resolver.resolver_list_head = 1;
  resolver.resolver_search_observed = true;
  if (ClassifyResolverDetail(resolver) !=
      "resolver-candidates-all-reject") return false;
  resolver.resolver_search_output = 1;
  if (ClassifyResolverDetail(resolver) != "resolver-candidate-accepted") {
    return false;
  }
  resolver.resolver_used_heap = true;
  resolver.resolver_heap_result_observed = true;
  resolver.resolver_heap_output = 0;
  if (ClassifyResolverDetail(resolver) !=
      "resolver-scratch-allocation-null") return false;
  CandidateStep candidate;
  candidate.primary_observed = true;
  candidate.primary_result = 0;
  candidate.secondary_observed = true;
  candidate.secondary_result = 0;
  if (!CandidateRejected(candidate) || CandidateSelected(candidate)) {
    return false;
  }
  candidate.secondary_result = 1;
  candidate.final_observed = true;
  candidate.final_result = 1;
  if (CandidateRejected(candidate) || !CandidateSelected(candidate)) {
    return false;
  }
  if (JsonEscape("a\\\"\n") != "a\\\\\\\"\\n") return false;
  return true;
}

int Run(const Options &options) {
  Capture capture;
  Stage stage = Stage::entry;
  const auto started = std::chrono::steady_clock::now();
  PROCESS_INFORMATION process_info{};
  HANDLE job = nullptr;
  bool debug_event_outstanding = false;
  bool initial_loader_breakpoint_seen = false;
  DEBUG_EVENT last_event{};
  std::set<DWORD> live_threads;

  auto finish_elapsed = [&]() {
    capture.elapsed_seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - started).count();
  };
  auto set_error = [&](const std::string &reason) {
    if (capture.error.empty()) capture.error = reason;
  };

  try {
    if (!std::filesystem::is_regular_file(options.exe)) {
      throw std::runtime_error("executable does not exist");
    }
    if (!std::filesystem::is_directory(options.userdir)) {
      throw std::runtime_error("userdir does not exist");
    }
    if (std::filesystem::exists(options.output) ||
        std::filesystem::exists(options.output.wstring() + L".tmp")) {
      throw std::runtime_error("output and output.tmp must be fresh");
    }
    if (options.output.parent_path().empty() ||
        !std::filesystem::is_directory(options.output.parent_path())) {
      throw std::runtime_error("output parent must exist before launch");
    }
    capture.exe_size = std::filesystem::file_size(options.exe);
    capture.exe_sha256 = Sha256(options.exe);
    capture.probe_sha256 = Sha256(CurrentExecutablePath());
    if (capture.exe_size != kExpectedExeSize ||
        capture.exe_sha256 != Narrow(kExpectedExeSha256)) {
      throw std::runtime_error("exact executable gate failed");
    }

    std::wstring command = Quote(options.exe.wstring()) +
        L" -gdpr-compliant -userdir=" + Quote(options.userdir.wstring());
    std::vector<wchar_t> mutable_command(command.begin(), command.end());
    mutable_command.push_back(L'\0');
    STARTUPINFOW startup{};
    startup.cb = sizeof(startup);
    if (!CreateProcessW(options.exe.c_str(), mutable_command.data(), nullptr,
                        nullptr, FALSE,
                        CREATE_SUSPENDED | CREATE_NEW_PROCESS_GROUP,
                        nullptr, options.exe.parent_path().c_str(), &startup,
                        &process_info)) {
      throw std::runtime_error("CreateProcessW failed: " +
                               std::to_string(GetLastError()));
    }
    capture.ck3_started = true;
    capture.pid = process_info.dwProcessId;
    live_threads.insert(process_info.dwThreadId);

    job = CreateJobObjectW(nullptr, nullptr);
    if (!job) throw std::runtime_error("CreateJobObjectW failed");
    JOBOBJECT_EXTENDED_LIMIT_INFORMATION job_info{};
    job_info.BasicLimitInformation.LimitFlags =
        JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
    if (!SetInformationJobObject(job, JobObjectExtendedLimitInformation,
                                 &job_info, sizeof(job_info)) ||
        !AssignProcessToJobObject(job, process_info.hProcess)) {
      throw std::runtime_error("kill-on-close Job setup failed");
    }
    if (!DebugActiveProcess(process_info.dwProcessId)) {
      throw std::runtime_error("DebugActiveProcess failed: " +
                               std::to_string(GetLastError()));
    }
    capture.debugger_attached = true;
    if (!DebugSetProcessKillOnExit(FALSE)) {
      throw std::runtime_error("DebugSetProcessKillOnExit failed: " +
                               std::to_string(GetLastError()));
    }

    bool request_termination = false;
    bool running = true;
    while (running) {
      const auto elapsed_ms = static_cast<DWORD>(
          std::chrono::duration_cast<std::chrono::milliseconds>(
              std::chrono::steady_clock::now() - started).count());
      if (elapsed_ms >= options.timeout_ms) {
        capture.reason = "timeout-before-complete-capture";
        request_termination = true;
      }
      if (request_termination && !debug_event_outstanding) {
        TerminateProcess(process_info.hProcess, 0);
      }

      DEBUG_EVENT event{};
      if (!WaitForDebugEvent(&event, request_termination ? 1000 : 50)) {
        if (GetLastError() == ERROR_SEM_TIMEOUT) {
          if (request_termination &&
              WaitForSingleObject(process_info.hProcess, 0) == WAIT_OBJECT_0) {
            capture.process_terminated = true;
            break;
          }
          continue;
        }
        set_error("WaitForDebugEvent failed: " +
                  std::to_string(GetLastError()));
        request_termination = true;
        continue;
      }
      debug_event_outstanding = true;
      last_event = event;
      DWORD continue_status = DBG_CONTINUE;

      if (event.dwDebugEventCode == CREATE_PROCESS_DEBUG_EVENT) {
        if (event.u.CreateProcessInfo.hFile) {
          CloseHandle(event.u.CreateProcessInfo.hFile);
        }
        capture.image_base = reinterpret_cast<std::uint64_t>(
            event.u.CreateProcessInfo.lpBaseOfImage);
        capture.anchors_verified =
            VerifyAnchors(process_info.hProcess, capture.image_base);
        if (!capture.anchors_verified) {
          capture.reason = "runtime-anchor-gate-failed";
          request_termination = true;
        } else if (!SetExecuteBreakpoint(event.u.CreateProcessInfo.hThread,
                                         capture.image_base + kEntryRva,
                                         false)) {
          capture.reason = "initial-debug-register-install-failed";
          set_error(std::to_string(GetLastError()));
          request_termination = true;
        } else {
          const DWORD previous_suspend_count =
              ResumeThread(process_info.hThread);
          if (previous_suspend_count != kExpectedAttachEventSuspendCount) {
            capture.reason = "primary-thread-resume-failed";
            set_error(previous_suspend_count == static_cast<DWORD>(-1)
                          ? std::to_string(GetLastError())
                          : "unexpected suspend count " +
                                std::to_string(previous_suspend_count));
            request_termination = true;
          } else {
            capture.primary_thread_resumed = true;
          }
        }
        if (event.u.CreateProcessInfo.hProcess &&
            event.u.CreateProcessInfo.hProcess != process_info.hProcess) {
          CloseHandle(event.u.CreateProcessInfo.hProcess);
        }
        if (event.u.CreateProcessInfo.hThread &&
            event.u.CreateProcessInfo.hThread != process_info.hThread) {
          CloseHandle(event.u.CreateProcessInfo.hThread);
        }
      } else if (event.dwDebugEventCode == CREATE_THREAD_DEBUG_EVENT) {
        live_threads.insert(event.dwThreadId);
        if (!request_termination &&
            !SetExecuteBreakpoint(event.u.CreateThread.hThread,
                                  capture.image_base + kEntryRva, false)) {
          capture.reason = "new-thread-debug-register-install-failed";
          set_error(std::to_string(GetLastError()));
          request_termination = true;
        }
        if (event.u.CreateThread.hThread) {
          CloseHandle(event.u.CreateThread.hThread);
        }
      } else if (event.dwDebugEventCode == LOAD_DLL_DEBUG_EVENT) {
        if (event.u.LoadDll.hFile) CloseHandle(event.u.LoadDll.hFile);
      } else if (event.dwDebugEventCode == EXIT_THREAD_DEBUG_EVENT) {
        live_threads.erase(event.dwThreadId);
      } else if (event.dwDebugEventCode == EXIT_PROCESS_DEBUG_EVENT) {
        capture.exit_event_observed = true;
        capture.process_terminated = true;
        running = false;
      } else if (event.dwDebugEventCode == EXCEPTION_DEBUG_EVENT) {
        const auto code = event.u.Exception.ExceptionRecord.ExceptionCode;
        if (code == EXCEPTION_SINGLE_STEP) {
          HANDLE thread = OpenDebugThread(event.dwThreadId);
          CONTEXT context{};
          context.ContextFlags =
              CONTEXT_CONTROL | CONTEXT_INTEGER | CONTEXT_DEBUG_REGISTERS;
          if (!thread || !GetThreadContext(thread, &context)) {
            if (thread) CloseHandle(thread);
            capture.reason = "single-step-context-read-failed";
            set_error(std::to_string(GetLastError()));
            request_termination = true;
          } else if ((context.Dr6 & 1U) == 0) {
            continue_status = DBG_EXCEPTION_NOT_HANDLED;
            CloseHandle(thread);
          } else {
            const std::uint64_t rip = context.Rip;
            const bool is_target_thread =
                capture.target_thread_id != 0 &&
                event.dwThreadId == capture.target_thread_id;
            if (rip == capture.image_base + kEntryRva &&
                capture.target_thread_id == 0) {
              std::string source;
              std::string variant;
              std::uint32_t source_length = 0;
              std::uint32_t variant_length = 0;
              const bool tuple_read =
                  ReadStringView(process_info.hProcess, context.Rdx, source,
                                 source_length) &&
                  ReadStringView(process_info.hProcess, context.R8, variant,
                                 variant_length);
              const bool tuple_match = tuple_read &&
                  source_length == kExpectedSourceLength &&
                  variant_length == kExpectedVariantLength &&
                  source == kExpectedSource && variant == kExpectedVariant &&
                  context.Rbp >= 0x68 && context.Rcx == context.Rbp - 0x68 &&
                  context.R14 != 0;
              if (!tuple_match) {
                if (!SetExecuteBreakpoint(thread,
                                          capture.image_base + kEntryRva,
                                          true)) {
                  capture.reason = "non-target-resume-failed";
                  set_error(std::to_string(GetLastError()));
                  request_termination = true;
                }
              } else {
                capture.target_tuple_observed = true;
                capture.target_thread_id = event.dwThreadId;
                capture.caller_rbp = context.Rbp;
                capture.output_address = context.Rcx;
                capture.manager = context.R14;
                capture.slot_address = context.R14 + 0xA8;
                capture.source_view = context.Rdx;
                capture.variant_view = context.R8;
                capture.source_text = source;
                capture.variant_text = variant;
                capture.source_length = source_length;
                capture.variant_length = variant_length;
                AddStep(capture, "entry", event.dwThreadId, rip, started);
                stage = Stage::graphics;
                if (!SetExecuteBreakpoint(thread,
                                          capture.image_base + kGraphicsRva,
                                          false)) {
                  capture.reason = "graphics-breakpoint-install-failed";
                  set_error(std::to_string(GetLastError()));
                  request_termination = true;
                }
              }
              CloseHandle(thread);
            } else if (rip == capture.image_base + kEntryRva &&
                       !is_target_thread) {
              if (!SetExecuteBreakpoint(thread,
                                        capture.image_base + kEntryRva, true)) {
                capture.reason = "secondary-thread-resume-failed";
                set_error(std::to_string(GetLastError()));
                request_termination = true;
              }
              CloseHandle(thread);
            } else if (is_target_thread && stage == Stage::graphics &&
                       rip == capture.image_base + kGraphicsRva) {
              capture.graphics_observed = true;
              capture.graphics_global = context.R15;
              capture.factory_rbp = context.Rbp;
              AddStep(capture, "graphics", event.dwThreadId, rip, started);
              stage = NextAfterGraphics(capture.graphics_global);
              const auto next = TargetRvaForStage(stage);
              if (!SetExecuteBreakpoint(thread, capture.image_base + next,
                                        false)) {
                capture.reason = "post-graphics-breakpoint-install-failed";
                set_error(std::to_string(GetLastError()));
                request_termination = true;
              }
              CloseHandle(thread);
            } else if (is_target_thread && stage == Stage::source_entry &&
                       rip == capture.image_base + kSourceEntryRva) {
              std::string source;
              std::uint32_t source_length = 0;
              const bool source_read = ReadStringView(
                  process_info.hProcess, context.Rdx, source, source_length);
              const bool identity_ok = source_read &&
                  source_length == kExpectedSourceLength &&
                  source == kExpectedSource &&
                  context.Rcx == capture.factory_rbp + 0x77 &&
                  (context.R8 & 0xFFU) == 0;
              if (!identity_ok) {
                capture.reason = "source-entry-identity-failed";
                set_error("nested source call did not preserve the exact "
                          "outer tuple/output identity");
                request_termination = true;
              } else {
                capture.source_detail_entry_observed = true;
                capture.source_function_output_address = context.Rcx;
                capture.source_function_view = context.Rdx;
                AddStep(capture, "source-entry", event.dwThreadId, rip,
                        started);
                stage = Stage::source_cache_result;
                if (!SetExecuteBreakpoint(
                        thread, capture.image_base + kSourceCacheResultRva,
                        false)) {
                  capture.reason = "source-cache-breakpoint-install-failed";
                  set_error(std::to_string(GetLastError()));
                  request_termination = true;
                }
              }
              CloseHandle(thread);
            } else if (is_target_thread &&
                       stage == Stage::source_cache_result &&
                       rip == capture.image_base + kSourceCacheResultRva) {
              const bool identity_ok =
                  context.Rsi == capture.source_function_output_address &&
                  context.Rbx == capture.source_function_view;
              const bool output_ok = identity_ok && ReadValue(
                  process_info.hProcess, context.Rsi,
                  capture.source_cache_output);
              if (!identity_ok || !output_ok) {
                capture.reason = "source-cache-result-read-failed";
                set_error(identity_ok ? std::to_string(GetLastError())
                                      : "nested source identity drift");
                request_termination = true;
              } else {
                capture.source_cache_observed = true;
                AddStep(capture, "source-cache-result", event.dwThreadId,
                        rip, started);
                stage = NextAfterSourceCache(capture.source_cache_output);
                const auto next = TargetRvaForStage(stage);
                if (!SetExecuteBreakpoint(thread, capture.image_base + next,
                                          false)) {
                  capture.reason =
                      "post-source-cache-breakpoint-install-failed";
                  set_error(std::to_string(GetLastError()));
                  request_termination = true;
                }
              }
              CloseHandle(thread);
            } else if (is_target_thread &&
                       stage == Stage::resolver_entry &&
                       rip == capture.image_base + kResolverEntryRva) {
              std::string source;
              std::uint32_t source_length = 0;
              std::uint64_t return_address = 0;
              const bool identity_ok =
                  ReadStringView(process_info.hProcess, context.Rcx, source,
                                 source_length) &&
                  ReadValue(process_info.hProcess, context.Rsp,
                            return_address) &&
                  source_length == kExpectedSourceLength &&
                  source == kExpectedSource &&
                  return_address ==
                      capture.image_base + kSourceResolverResultRva;
              if (!identity_ok) {
                capture.reason = "resolver-entry-identity-failed";
                set_error("fallback resolver did not preserve the exact "
                          "source/return identity");
                request_termination = true;
              } else {
                capture.resolver_entry_observed = true;
                capture.resolver_input_view = context.Rcx;
                AddStep(capture, "resolver-entry", event.dwThreadId, rip,
                        started);
                stage = Stage::resolver_size;
                if (!SetExecuteBreakpoint(thread,
                                          capture.image_base +
                                              kResolverSizeRva,
                                          false)) {
                  capture.reason = "resolver-size-breakpoint-install-failed";
                  set_error(std::to_string(GetLastError()));
                  request_termination = true;
                }
              }
              CloseHandle(thread);
            } else if (is_target_thread && stage == Stage::resolver_size &&
                       rip == capture.image_base + kResolverSizeRva) {
              const bool identity_ok =
                  context.Rsi == capture.resolver_input_view &&
                  context.Rbx >= 8 &&
                  context.Rdx >= kExpectedSourceLength + 1;
              if (!identity_ok) {
                capture.reason = "resolver-size-identity-failed";
                set_error("fallback resolver size/state identity drift");
                request_termination = true;
              } else {
                capture.resolver_size_observed = true;
                capture.resolver_state = context.Rbx - 8;
                capture.resolver_total_buffer_bytes = context.Rdx;
                capture.resolver_locked_mode = (context.R12 & 0xFFU) != 0;
                capture.resolver_used_heap = context.Rdx >= 0x200;
                AddStep(capture, "resolver-size", event.dwThreadId, rip,
                        started);
                stage = NextAfterResolverSize(context.Rdx);
                const auto next = TargetRvaForStage(stage);
                if (!SetExecuteBreakpoint(thread, capture.image_base + next,
                                          false)) {
                  capture.reason =
                      "post-resolver-size-breakpoint-install-failed";
                  set_error(std::to_string(GetLastError()));
                  request_termination = true;
                }
              }
              CloseHandle(thread);
            } else if (is_target_thread &&
                       stage == Stage::resolver_heap_result &&
                       rip == capture.image_base + kResolverHeapResultRva) {
              capture.resolver_heap_result_observed = true;
              capture.resolver_heap_output = context.Rax;
              AddStep(capture, "resolver-heap-result", event.dwThreadId, rip,
                      started);
              stage = NextAfterResolverHeap(context.Rax);
              const auto next = TargetRvaForStage(stage);
              if (!SetExecuteBreakpoint(thread, capture.image_base + next,
                                        false)) {
                capture.reason =
                    "post-resolver-heap-breakpoint-install-failed";
                set_error(std::to_string(GetLastError()));
                request_termination = true;
              }
              CloseHandle(thread);
            } else if (is_target_thread &&
                       stage == Stage::resolver_buffer_ready &&
                       rip == capture.image_base + kResolverBufferReadyRva) {
              const bool identity_ok =
                  context.Rsi == capture.resolver_input_view &&
                  context.Rax != 0 &&
                  (!capture.resolver_used_heap ||
                   (capture.resolver_heap_result_observed &&
                    context.Rax == capture.resolver_heap_output));
              if (!identity_ok) {
                capture.reason = "resolver-buffer-identity-failed";
                set_error("fallback resolver scratch allocation drift");
                request_termination = true;
              } else {
                capture.resolver_buffer_ready_observed = true;
                capture.resolver_buffer_base = context.Rax;
                AddStep(capture, "resolver-buffer-ready", event.dwThreadId,
                        rip, started);
                stage = Stage::resolver_normalize_result;
                if (!SetExecuteBreakpoint(
                        thread,
                        capture.image_base + kResolverNormalizeResultRva,
                        false)) {
                  capture.reason =
                      "resolver-normalize-breakpoint-install-failed";
                  set_error(std::to_string(GetLastError()));
                  request_termination = true;
                }
              }
              CloseHandle(thread);
            } else if (is_target_thread &&
                       stage == Stage::resolver_normalize_result &&
                       rip ==
                           capture.image_base + kResolverNormalizeResultRva) {
              capture.resolver_normalize_observed = true;
              capture.resolver_normalize_ok = (context.Rax & 0xFFU) != 0;
              capture.resolver_normalized_address = context.Rdi;
              const bool text_ok = !capture.resolver_normalize_ok ||
                  ReadCString(process_info.hProcess, context.Rdi,
                              capture.resolver_normalized_text,
                              kExpectedSourceLength + 1);
              if (!text_ok || context.Rsi != capture.resolver_input_view) {
                capture.reason = "resolver-normalize-result-read-failed";
                set_error(text_ok ? "fallback resolver input identity drift"
                                  : "normalized source read failed");
                request_termination = true;
              } else {
                AddStep(capture, "resolver-normalize-result",
                        event.dwThreadId, rip, started);
                stage = NextAfterResolverNormalize(
                    capture.resolver_normalize_ok);
                const auto next = TargetRvaForStage(stage);
                if (!SetExecuteBreakpoint(thread, capture.image_base + next,
                                          false)) {
                  capture.reason =
                      "post-resolver-normalize-breakpoint-install-failed";
                  set_error(std::to_string(GetLastError()));
                  request_termination = true;
                }
              }
              CloseHandle(thread);
            } else if (is_target_thread &&
                       stage == Stage::resolver_list_head &&
                       rip == capture.image_base + kResolverListHeadRva) {
              if (!capture.resolver_list_head_observed) {
                capture.resolver_list_head_observed = true;
                capture.resolver_list_head = context.Rbx;
              }
              AddStep(capture, "resolver-list-head", event.dwThreadId, rip,
                      started);
              if (context.Rbx == 0) {
                stage = Stage::resolver_search_result;
              } else {
                bool duplicate = false;
                for (const auto &candidate : capture.candidates) {
                  if (candidate.address == context.Rbx) duplicate = true;
                }
                if (duplicate || capture.candidates.size() >= 256) {
                  capture.reason = "resolver-candidate-chain-invalid";
                  set_error(duplicate ? "candidate chain cycle detected"
                                      : "candidate chain exceeded 256 nodes");
                  request_termination = true;
                } else {
                  CandidateStep candidate;
                  candidate.address = context.Rbx;
                  const bool prefix_ok = ReadValue(
                      process_info.hProcess, context.Rbx + 0x10,
                      candidate.prefix_address);
                  const bool backend_ok = ReadValue(
                      process_info.hProcess, context.Rbx,
                      candidate.backend_object);
                  const bool rewrite_ok = ReadValue(
                      process_info.hProcess, context.Rbx + 0x18,
                      candidate.rewrite_address);
                  const bool rewrite_offset_ok = ReadValue(
                      process_info.hProcess, context.Rbx + 0x20,
                      candidate.rewrite_offset);
                  const bool dispatch_ok = ReadValue(
                      process_info.hProcess, context.Rbx + 0x28,
                      candidate.dispatch_table);
                  const bool callback_ok = dispatch_ok &&
                      candidate.dispatch_table != 0 &&
                      ReadValue(process_info.hProcess,
                                candidate.dispatch_table + 0x68,
                                candidate.callback_address);
                  const bool next_ok = ReadValue(
                      process_info.hProcess, context.Rbx + 0x30,
                      candidate.next_address);
                  const bool prefix_text_ok = prefix_ok &&
                      (candidate.prefix_address == 0 ||
                       ReadCString(process_info.hProcess,
                                   candidate.prefix_address,
                                   candidate.prefix_text, 260));
                  if (!prefix_ok || !backend_ok || !rewrite_ok ||
                      !rewrite_offset_ok || !dispatch_ok || !callback_ok ||
                      !next_ok || !prefix_text_ok) {
                    capture.reason = "resolver-candidate-read-failed";
                    set_error(std::to_string(GetLastError()));
                    request_termination = true;
                  } else {
                    capture.candidates.push_back(std::move(candidate));
                    stage = Stage::resolver_candidate_primary_result;
                  }
                }
              }
              if (!request_termination) {
                const auto next = TargetRvaForStage(stage);
                if (!SetExecuteBreakpoint(thread, capture.image_base + next,
                                          false)) {
                  capture.reason =
                      "post-resolver-list-breakpoint-install-failed";
                  set_error(std::to_string(GetLastError()));
                  request_termination = true;
                }
              }
              CloseHandle(thread);
            } else if (is_target_thread &&
                       stage == Stage::resolver_candidate_primary_result &&
                       rip == capture.image_base +
                           kResolverCandidatePrimaryResultRva) {
              if (capture.candidates.empty() ||
                  capture.candidates.back().address != context.Rbx) {
                capture.reason = "resolver-primary-identity-failed";
                set_error("candidate address drift before primary result");
                request_termination = true;
              } else {
                capture.candidates.back().primary_result =
                    static_cast<std::int32_t>(context.Rax);
                capture.candidates.back().primary_observed = true;
                AddStep(capture, "resolver-candidate-primary-result",
                        event.dwThreadId, rip, started);
                stage = static_cast<std::uint32_t>(context.Rax) != 0
                    ? Stage::resolver_search_result
                    : Stage::resolver_candidate_secondary_entry;
                const auto next = TargetRvaForStage(stage);
                if (!SetExecuteBreakpoint(thread, capture.image_base + next,
                                          false)) {
                  capture.reason =
                      "post-resolver-primary-breakpoint-install-failed";
                  set_error(std::to_string(GetLastError()));
                  request_termination = true;
                }
              }
              CloseHandle(thread);
            } else if (is_target_thread &&
                       stage == Stage::resolver_candidate_secondary_entry &&
                       rip == capture.image_base +
                           kResolverCandidateSecondaryEntryRva) {
              std::uint64_t return_address = 0;
              const bool identity_ok = !capture.candidates.empty() &&
                  capture.candidates.back().address == context.Rcx &&
                  ReadValue(process_info.hProcess, context.Rsp,
                            return_address) &&
                  return_address == capture.image_base +
                      kResolverCandidateSecondaryResultRva;
              if (!identity_ok) {
                capture.reason = "resolver-secondary-entry-identity-failed";
                set_error("secondary helper candidate/return identity drift");
                request_termination = true;
              } else {
                AddStep(capture, "resolver-candidate-secondary-entry",
                        event.dwThreadId, rip, started);
                stage = Stage::resolver_candidate_secondary_state;
                if (!SetExecuteBreakpoint(
                        thread,
                        capture.image_base +
                            kResolverCandidateSecondaryStateRva,
                        false)) {
                  capture.reason =
                      "resolver-secondary-state-breakpoint-install-failed";
                  set_error(std::to_string(GetLastError()));
                  request_termination = true;
                }
              }
              CloseHandle(thread);
            } else if (is_target_thread &&
                       stage == Stage::resolver_candidate_secondary_state &&
                       rip == capture.image_base +
                           kResolverCandidateSecondaryStateRva) {
              std::uint8_t state_f9 = 0;
              std::uint8_t state_fa = 0;
              const bool identity_ok = !capture.candidates.empty() &&
                  context.Rax == capture.resolver_state &&
                  ReadValue(process_info.hProcess, context.Rax + 0xF9,
                            state_f9) &&
                  ReadValue(process_info.hProcess, context.Rax + 0xFA,
                            state_fa);
              if (!identity_ok) {
                capture.reason = "resolver-secondary-state-read-failed";
                set_error("secondary helper singleton identity/read failed");
                request_termination = true;
              } else {
                auto &candidate = capture.candidates.back();
                candidate.secondary_state_observed = true;
                candidate.secondary_state_f9 = state_f9;
                candidate.secondary_state_fa = state_fa;
                AddStep(capture, "resolver-candidate-secondary-state",
                        event.dwThreadId, rip, started);
                stage = state_f9 != 0
                    ? Stage::resolver_candidate_secondary_result
                    : Stage::resolver_candidate_backend_callback_entry;
                const auto next = state_f9 != 0
                    ? capture.image_base + TargetRvaForStage(stage)
                    : candidate.callback_address;
                if (state_f9 == 0 &&
                    next != capture.image_base +
                        kResolverCandidateBackendCallbackEntryRva) {
                  capture.reason = "unexpected-backend-callback-address";
                  set_error("exact-build backend callback address drift");
                  request_termination = true;
                } else if (!SetExecuteBreakpoint(thread, next, false)) {
                  capture.reason =
                      "post-secondary-state-breakpoint-install-failed";
                  set_error(std::to_string(GetLastError()));
                  request_termination = true;
                }
              }
              CloseHandle(thread);
            } else if (is_target_thread &&
                       stage ==
                           Stage::resolver_candidate_backend_callback_entry &&
                       rip == capture.image_base +
                           kResolverCandidateBackendCallbackEntryRva) {
              std::string backend_root;
              std::string requested_path;
              const bool identity_ok = !capture.candidates.empty() &&
                  capture.candidates.back().callback_address == rip &&
                  capture.candidates.back().backend_object == context.Rcx &&
                  context.Rdx == capture.resolver_normalized_address &&
                  context.R8 != 0 &&
                  ReadCString(process_info.hProcess, context.Rcx,
                              backend_root, 512) &&
                  ReadCString(process_info.hProcess, context.Rdx,
                              requested_path, 512);
              if (!identity_ok) {
                capture.reason = "backend-callback-entry-read-failed";
                set_error("backend callback argument identity/read failed");
                request_termination = true;
              } else {
                auto &candidate = capture.candidates.back();
                candidate.backend_callback_entry_observed = true;
                candidate.callback_output_address = context.R8;
                candidate.backend_root_text = std::move(backend_root);
                candidate.backend_requested_text = std::move(requested_path);
                AddStep(capture, "resolver-candidate-backend-callback-entry",
                        event.dwThreadId, rip, started);
                stage = Stage::resolver_candidate_backend_path_result;
                if (!SetExecuteBreakpoint(
                        thread,
                        capture.image_base +
                            kResolverCandidateBackendPathResultRva,
                        false)) {
                  capture.reason =
                      "backend-path-result-breakpoint-install-failed";
                  set_error(std::to_string(GetLastError()));
                  request_termination = true;
                }
              }
              CloseHandle(thread);
            } else if (is_target_thread &&
                       stage ==
                           Stage::resolver_candidate_backend_path_result &&
                       rip == capture.image_base +
                           kResolverCandidateBackendPathResultRva) {
              bool path_ok = !capture.candidates.empty() &&
                  capture.candidates.back().backend_callback_entry_observed;
              std::string backend_path;
              if (path_ok && context.Rax != 0) {
                path_ok = ReadCString(process_info.hProcess, context.Rax,
                                      backend_path, 512);
              }
              if (!path_ok) {
                capture.reason = "backend-path-result-read-failed";
                set_error("combined backend path read failed");
                request_termination = true;
              } else {
                auto &candidate = capture.candidates.back();
                candidate.backend_path_observed = true;
                candidate.backend_path_address = context.Rax;
                candidate.backend_path_text = std::move(backend_path);
                AddStep(capture, "resolver-candidate-backend-path-result",
                        event.dwThreadId, rip, started);
                stage = context.Rax == 0
                    ? Stage::resolver_candidate_callback_result
                    : Stage::resolver_candidate_backend_read_result;
                if (!SetExecuteBreakpoint(
                        thread,
                        capture.image_base + TargetRvaForStage(stage),
                        false)) {
                  capture.reason =
                      "post-backend-path-breakpoint-install-failed";
                  set_error(std::to_string(GetLastError()));
                  request_termination = true;
                }
              }
              CloseHandle(thread);
            } else if (is_target_thread &&
                       stage ==
                           Stage::resolver_candidate_backend_read_result &&
                       rip == capture.image_base +
                           kResolverCandidateBackendReadResultRva) {
              const bool identity_ok = !capture.candidates.empty() &&
                  capture.candidates.back().backend_path_address != 0 &&
                  context.Rbx ==
                      capture.candidates.back().backend_path_address &&
                  context.R12 ==
                      capture.candidates.back().callback_output_address;
              if (!identity_ok) {
                capture.reason = "backend-read-result-identity-failed";
                set_error("backend read result identity drift");
                request_termination = true;
              } else {
                auto &candidate = capture.candidates.back();
                candidate.backend_read_observed = true;
                candidate.backend_read_result =
                    static_cast<std::int32_t>(context.Rax);
                AddStep(capture, "resolver-candidate-backend-read-result",
                        event.dwThreadId, rip, started);
                stage = Stage::resolver_candidate_callback_result;
                if (!SetExecuteBreakpoint(
                        thread,
                        capture.image_base +
                            kResolverCandidateCallbackResultRva,
                        false)) {
                  capture.reason =
                      "callback-result-breakpoint-install-failed";
                  set_error(std::to_string(GetLastError()));
                  request_termination = true;
                }
              }
              CloseHandle(thread);
            } else if (is_target_thread &&
                       stage == Stage::resolver_candidate_callback_result &&
                       rip == capture.image_base +
                           kResolverCandidateCallbackResultRva) {
              const auto callback_result =
                  static_cast<std::int32_t>(context.Rax);
              std::int32_t result_type = -1;
              bool result_type_observed = false;
              const bool candidate_ok = !capture.candidates.empty() &&
                  context.R12 == capture.candidates.back().address;
              if (candidate_ok && callback_result != 0) {
                result_type_observed = ReadValue(
                    process_info.hProcess, context.Rsp + 0x40, result_type);
              }
              const bool identity_ok = candidate_ok &&
                  (callback_result == 0 || result_type_observed);
              if (!identity_ok) {
                capture.reason =
                    "resolver-secondary-callback-result-read-failed";
                set_error("secondary callback candidate/result identity drift");
                request_termination = true;
              } else {
                auto &candidate = capture.candidates.back();
                candidate.secondary_callback_observed = true;
                candidate.secondary_callback_result = callback_result;
                candidate.secondary_callback_result_type_observed =
                    result_type_observed;
                candidate.secondary_callback_result_type = result_type;
                AddStep(capture, "resolver-candidate-callback-result",
                        event.dwThreadId, rip, started);
                stage = Stage::resolver_candidate_secondary_result;
                if (!SetExecuteBreakpoint(
                        thread,
                        capture.image_base +
                            kResolverCandidateSecondaryResultRva,
                        false)) {
                  capture.reason =
                      "secondary-result-breakpoint-install-failed";
                  set_error(std::to_string(GetLastError()));
                  request_termination = true;
                }
              }
              CloseHandle(thread);
            } else if (is_target_thread &&
                       stage == Stage::resolver_candidate_secondary_result &&
                       rip == capture.image_base +
                           kResolverCandidateSecondaryResultRva) {
              if (capture.candidates.empty()) {
                capture.reason = "resolver-secondary-identity-failed";
                set_error("secondary result has no candidate");
                request_termination = true;
              } else {
                capture.candidates.back().secondary_result =
                    static_cast<std::int32_t>(context.Rax);
                capture.candidates.back().secondary_observed = true;
                AddStep(capture, "resolver-candidate-secondary-result",
                        event.dwThreadId, rip, started);
                stage = static_cast<std::uint32_t>(context.Rax) == 0
                    ? Stage::resolver_list_head
                    : Stage::resolver_candidate_final_result;
                const auto next = TargetRvaForStage(stage);
                if (!SetExecuteBreakpoint(thread, capture.image_base + next,
                                          false)) {
                  capture.reason =
                      "post-resolver-secondary-breakpoint-install-failed";
                  set_error(std::to_string(GetLastError()));
                  request_termination = true;
                }
              }
              CloseHandle(thread);
            } else if (is_target_thread &&
                       stage == Stage::resolver_candidate_final_result &&
                       rip == capture.image_base +
                           kResolverCandidateFinalResultRva) {
              if (capture.candidates.empty()) {
                capture.reason = "resolver-final-identity-failed";
                set_error("final result has no candidate");
                request_termination = true;
              } else {
                capture.candidates.back().final_result =
                    static_cast<std::int32_t>(context.Rax);
                capture.candidates.back().final_observed = true;
                AddStep(capture, "resolver-candidate-final-result",
                        event.dwThreadId, rip, started);
                stage = static_cast<std::uint32_t>(context.Rax) == 1
                    ? Stage::resolver_search_result
                    : Stage::resolver_list_head;
                const auto next = TargetRvaForStage(stage);
                if (!SetExecuteBreakpoint(thread, capture.image_base + next,
                                          false)) {
                  capture.reason =
                      "post-resolver-final-breakpoint-install-failed";
                  set_error(std::to_string(GetLastError()));
                  request_termination = true;
                }
              }
              CloseHandle(thread);
            } else if (is_target_thread &&
                       stage == Stage::resolver_search_result &&
                       rip == capture.image_base + kResolverSearchResultRva) {
              capture.resolver_search_observed = true;
              capture.resolver_search_output = context.R14;
              const bool candidate_selected = !capture.candidates.empty() &&
                  CandidateSelected(capture.candidates.back());
              bool all_candidates_rejected = !capture.candidates.empty();
              for (const auto &candidate : capture.candidates) {
                all_candidates_rejected = all_candidates_rejected &&
                    CandidateRejected(candidate);
              }
              const bool selection_consistent =
                  (context.R14 == 0 &&
                   ((capture.resolver_list_head == 0 &&
                     capture.candidates.empty()) ||
                    all_candidates_rejected)) ||
                  (context.R14 != 0 && candidate_selected &&
                   capture.candidates.back().address == context.R14);
              if ((capture.resolver_list_head == 0 && context.R14 != 0) ||
                  !selection_consistent) {
                capture.reason = "resolver-search-cross-check-failed";
                set_error("resolver candidate trace disagreed with search "
                          "join output");
                request_termination = true;
              } else {
                AddStep(capture, "resolver-search-result", event.dwThreadId,
                        rip, started);
                stage = Stage::source_resolver_result;
                if (!SetExecuteBreakpoint(
                        thread,
                        capture.image_base + kSourceResolverResultRva,
                        false)) {
                  capture.reason =
                      "source-resolver-breakpoint-install-failed";
                  set_error(std::to_string(GetLastError()));
                  request_termination = true;
                }
              }
              CloseHandle(thread);
            } else if (is_target_thread &&
                       stage == Stage::source_resolver_result &&
                       rip == capture.image_base + kSourceResolverResultRva) {
              const bool identity_ok =
                  context.Rsi == capture.source_function_output_address &&
                  context.Rbx == capture.source_function_view;
              if (!identity_ok) {
                capture.reason = "source-resolver-identity-failed";
                set_error("nested source identity drift");
                request_termination = true;
              } else {
                capture.source_resolver_observed = true;
                capture.source_resolver_output = context.Rax;
                const auto detail = ClassifyResolverDetail(capture);
                const bool detail_consistent =
                    detail != "not-observed" &&
                    detail != "resolver-detail-incomplete" &&
                    ((detail == "resolver-candidate-accepted" &&
                      context.Rax == capture.resolver_search_output) ||
                     (detail != "resolver-candidate-accepted" &&
                      context.Rax == 0));
                if (!detail_consistent) {
                  capture.reason = "resolver-detail-cross-check-failed";
                  set_error("resolver internal branch disagreed with its "
                            "outer raw result");
                  request_termination = true;
                } else {
                  AddStep(capture, "source-resolver-result",
                          event.dwThreadId, rip, started);
                  stage = Stage::source;
                  if (!SetExecuteBreakpoint(thread,
                                            capture.image_base + kSourceRva,
                                            false)) {
                    capture.reason =
                        "post-source-resolver-breakpoint-install-failed";
                    set_error(std::to_string(GetLastError()));
                    request_termination = true;
                  }
                }
              }
              CloseHandle(thread);
            } else if (is_target_thread && stage == Stage::source &&
                       rip == capture.image_base + kSourceRva) {
              capture.source_observed = true;
              if (!ReadValue(process_info.hProcess, context.Rbp + 0x77,
                             capture.source_output)) {
                capture.reason = "source-output-read-failed";
                set_error(std::to_string(GetLastError()));
                request_termination = true;
              } else {
                const auto detail_classification =
                    ClassifySourceDetail(capture);
                const bool detail_consistent =
                    capture.source_detail_entry_observed &&
                    capture.source_cache_observed &&
                    capture.source_function_output_address ==
                        context.Rbp + 0x77 &&
                    context.Rbp == capture.factory_rbp &&
                    ((capture.source_cache_output != 0 &&
                      !capture.source_resolver_observed &&
                      capture.source_output == capture.source_cache_output) ||
                     (capture.source_cache_output == 0 &&
                      capture.source_resolver_observed &&
                      (capture.source_resolver_output != 0 ||
                       capture.source_output == 0))) &&
                    detail_classification != "source-detail-inconsistent" &&
                    detail_classification != "source-detail-incomplete" &&
                    detail_classification != "not-observed";
                if (!detail_consistent) {
                  capture.reason = "source-detail-cross-check-failed";
                  set_error("nested source detail did not agree with the "
                            "outer source result");
                  request_termination = true;
                } else {
                  AddStep(capture, "source", event.dwThreadId, rip, started);
                  stage = NextAfterSource(capture.source_output);
                  const auto next = TargetRvaForStage(stage);
                  if (!SetExecuteBreakpoint(thread,
                                            capture.image_base + next,
                                            false)) {
                    capture.reason = "post-source-breakpoint-install-failed";
                    set_error(std::to_string(GetLastError()));
                    request_termination = true;
                  }
                }
              }
              CloseHandle(thread);
            } else if (is_target_thread && stage == Stage::variant &&
                       rip == capture.image_base + kVariantRva) {
              capture.variant_observed = true;
              capture.variant_output = context.Rax;
              AddStep(capture, "variant", event.dwThreadId, rip, started);
              stage = NextAfterVariant(capture.variant_output);
              const auto next = TargetRvaForStage(stage);
              if (!SetExecuteBreakpoint(thread, capture.image_base + next,
                                        false)) {
                capture.reason = "post-variant-breakpoint-install-failed";
                set_error(std::to_string(GetLastError()));
                request_termination = true;
              }
              CloseHandle(thread);
            } else if (is_target_thread && stage == Stage::backend_entry &&
                       rip == capture.image_base + kBackendEntryRva) {
              std::uint64_t device_object = 0;
              std::uint64_t dispatch_table = 0;
              std::uint64_t callback_address = 0;
              const bool identity_ok = context.Rcx == capture.graphics_global &&
                  context.Rdx == capture.factory_rbp + 0x7F &&
                  context.R8 != 0 &&
                  ReadValue(process_info.hProcess, context.Rcx,
                            device_object) &&
                  device_object != 0 &&
                  ReadValue(process_info.hProcess, device_object,
                            dispatch_table) &&
                  dispatch_table != 0 &&
                  ReadValue(process_info.hProcess, dispatch_table + 0xA0,
                            callback_address) &&
                  callback_address != 0;
              if (!identity_ok) {
                capture.reason = "backend-entry-identity-read-failed";
                set_error("backend manager/output/dispatch identity drift");
                request_termination = true;
              } else {
                capture.backend_entry_observed = true;
                capture.backend_config_address = context.R8;
                capture.backend_device_object = device_object;
                capture.backend_dispatch_table = dispatch_table;
                capture.backend_callback_address = callback_address;
                AddStep(capture, "backend-entry", event.dwThreadId, rip,
                        started);
                stage = Stage::backend_cache_result;
                if (!SetExecuteBreakpoint(
                        thread,
                        capture.image_base + kBackendCacheResultRva,
                        false)) {
                  capture.reason =
                      "backend-cache-result-breakpoint-install-failed";
                  set_error(std::to_string(GetLastError()));
                  request_termination = true;
                }
              }
              CloseHandle(thread);
            } else if (is_target_thread &&
                       stage == Stage::backend_cache_result &&
                       rip == capture.image_base + kBackendCacheResultRva) {
              std::uint64_t cache_output = 0;
              const bool identity_ok = capture.backend_entry_observed &&
                  context.Rbx == capture.graphics_global &&
                  context.Rdi == capture.factory_rbp + 0x7F &&
                  ReadValue(process_info.hProcess, context.Rdi,
                            cache_output);
              if (!identity_ok) {
                capture.reason = "backend-cache-result-read-failed";
                set_error("backend cache output identity/read failed");
                request_termination = true;
              } else {
                capture.backend_cache_result_observed = true;
                capture.backend_cache_output = cache_output;
                AddStep(capture, "backend-cache-result", event.dwThreadId,
                        rip, started);
                stage = cache_output == 0
                    ? Stage::backend_callback_entry
                    : Stage::backend;
                if (!SetExecuteBreakpoint(
                        thread,
                        capture.image_base + TargetRvaForStage(stage),
                        false)) {
                  capture.reason =
                      "post-backend-cache-breakpoint-install-failed";
                  set_error(std::to_string(GetLastError()));
                  request_termination = true;
                }
              }
              CloseHandle(thread);
            } else if (is_target_thread &&
                       stage == Stage::backend_callback_entry &&
                       rip == capture.image_base + kBackendCallbackEntryRva) {
              const bool identity_ok =
                  capture.backend_cache_result_observed &&
                  capture.backend_cache_output == 0 &&
                  context.Rcx == capture.backend_device_object &&
                  context.R8 == capture.backend_config_address &&
                  context.Rdx != 0 &&
                  capture.backend_callback_address == rip;
              if (!identity_ok) {
                capture.reason = "backend-callback-entry-identity-failed";
                set_error("backend callback device/output/request drift");
                request_termination = true;
              } else {
                capture.backend_callback_entry_observed = true;
                capture.backend_callback_output_slot = context.Rdx;
                AddStep(capture, "backend-callback-entry", event.dwThreadId,
                        rip, started);
                stage = Stage::backend_initializer_globals;
                if (!SetExecuteBreakpoint(
                        thread,
                        capture.image_base + kBackendInitializerGlobalsRva,
                        false)) {
                  capture.reason =
                      "backend-initializer-globals-breakpoint-install-failed";
                  set_error(std::to_string(GetLastError()));
                  request_termination = true;
                }
              }
              CloseHandle(thread);
            } else if (is_target_thread &&
                       stage == Stage::backend_initializer_globals &&
                       rip == capture.image_base +
                           kBackendInitializerGlobalsRva) {
              std::uint64_t graphics_global = 0;
              const bool identity_ok = capture.backend_callback_entry_observed &&
                  context.Rsi == capture.backend_config_address &&
                  context.Rbx != 0 &&
                  ReadValue(process_info.hProcess,
                            capture.image_base + 0x570FC60,
                            graphics_global);
              if (!identity_ok) {
                capture.reason = "backend-initializer-globals-read-failed";
                set_error("initializer object/request/global identity failed");
                request_termination = true;
              } else {
                capture.backend_initializer_globals_observed = true;
                capture.backend_initializer_object = context.Rbx;
                capture.backend_initializer_request = context.Rsi;
                capture.backend_initializer_resource_global = context.R14;
                capture.backend_initializer_graphics_global = graphics_global;
                AddStep(capture, "backend-initializer-globals",
                        event.dwThreadId, rip, started);
                stage = (context.R14 == 0 || graphics_global == 0)
                    ? Stage::backend_initializer_result
                    : Stage::backend_stage_loop;
                if (!SetExecuteBreakpoint(
                        thread,
                        capture.image_base + TargetRvaForStage(stage),
                        false)) {
                  capture.reason =
                      "post-backend-initializer-globals-breakpoint-install-failed";
                  set_error(std::to_string(GetLastError()));
                  request_termination = true;
                }
              }
              CloseHandle(thread);
            } else if (is_target_thread &&
                       stage == Stage::backend_stage_loop &&
                       rip == capture.image_base + kBackendStageLoopRva) {
              BackendStageStep item;
              item.index = static_cast<std::uint32_t>(context.R13);
              item.name_object = context.R15;
              const bool identity_ok =
                  capture.backend_initializer_globals_observed &&
                  context.R13 < 9 && context.R15 != 0 &&
                  ReadMsvcString(process_info.hProcess, context.R15,
                                 item.name, item.name_length);
              if (!identity_ok) {
                capture.reason = "backend-stage-loop-read-failed";
                set_error("initializer stage index/name identity failed");
                request_termination = true;
              } else {
                item.active = item.name_length != 0;
                capture.backend_stages.push_back(std::move(item));
                AddStep(capture, "backend-stage-loop", event.dwThreadId, rip,
                        started);
                const auto &current = capture.backend_stages.back();
                stage = current.active
                    ? Stage::backend_hlsl_result
                    : (current.index == 8
                        ? Stage::backend_initializer_result
                        : Stage::backend_stage_loop);
                const bool same_breakpoint =
                    stage == Stage::backend_stage_loop;
                if (!SetExecuteBreakpoint(
                        thread,
                        capture.image_base + TargetRvaForStage(stage),
                        same_breakpoint)) {
                  capture.reason =
                      "post-backend-stage-loop-breakpoint-install-failed";
                  set_error(std::to_string(GetLastError()));
                  request_termination = true;
                }
              }
              CloseHandle(thread);
            } else if (is_target_thread &&
                       stage == Stage::backend_hlsl_result &&
                       rip == capture.image_base + kBackendHlslResultRva) {
              const bool identity_ok = !capture.backend_stages.empty() &&
                  capture.backend_stages.back().active &&
                  capture.backend_stages.back().index ==
                      static_cast<std::uint32_t>(context.R13);
              if (!identity_ok) {
                capture.reason = "backend-hlsl-result-identity-failed";
                set_error("HLSL result stage identity drift");
                request_termination = true;
              } else {
                auto &current = capture.backend_stages.back();
                current.hlsl_result_observed = true;
                current.hlsl_ok = (context.Rax & 0xFFU) != 0;
                AddStep(capture, "backend-hlsl-result", event.dwThreadId,
                        rip, started);
                stage = current.hlsl_ok
                    ? Stage::backend_shader_cache_result
                    : Stage::backend_initializer_result;
                if (!SetExecuteBreakpoint(
                        thread,
                        capture.image_base + TargetRvaForStage(stage),
                        false)) {
                  capture.reason =
                      "post-backend-hlsl-breakpoint-install-failed";
                  set_error(std::to_string(GetLastError()));
                  request_termination = true;
                }
              }
              CloseHandle(thread);
            } else if (is_target_thread &&
                       stage == Stage::backend_shader_cache_result &&
                       rip == capture.image_base +
                           kBackendShaderCacheResultRva) {
              std::uint64_t cache_output = 0;
              const bool identity_ok = !capture.backend_stages.empty() &&
                  capture.backend_stages.back().hlsl_ok &&
                  capture.backend_stages.back().index ==
                      static_cast<std::uint32_t>(context.R14) &&
                  context.Rsi != 0 &&
                  ReadValue(process_info.hProcess, context.Rsi, cache_output);
              if (!identity_ok) {
                capture.reason = "backend-shader-cache-result-read-failed";
                set_error("per-stage shader cache identity/read failed");
                request_termination = true;
              } else {
                auto &current = capture.backend_stages.back();
                current.shader_cache_result_observed = true;
                current.shader_cache_output = cache_output;
                AddStep(capture, "backend-shader-cache-result",
                        event.dwThreadId, rip, started);
                stage = cache_output == 0
                    ? Stage::backend_shader_vcall_entry
                    : Stage::backend_shader_result;
                if (!SetExecuteBreakpoint(
                        thread,
                        capture.image_base + TargetRvaForStage(stage),
                        false)) {
                  capture.reason =
                      "post-backend-shader-cache-breakpoint-install-failed";
                  set_error(std::to_string(GetLastError()));
                  request_termination = true;
                }
              }
              CloseHandle(thread);
            } else if (is_target_thread &&
                       stage == Stage::backend_shader_vcall_entry &&
                       rip == capture.image_base +
                           kBackendShaderVcallEntryRva) {
              std::uint64_t callback_address = 0;
              const bool identity_ok = !capture.backend_stages.empty() &&
                  capture.backend_stages.back().shader_cache_result_observed &&
                  capture.backend_stages.back().shader_cache_output == 0 &&
                  capture.backend_stages.back().index ==
                      static_cast<std::uint32_t>(context.R14) &&
                  context.Rbx != 0 && context.Rax != 0 &&
                  ReadValue(process_info.hProcess, context.Rax + 0x08,
                            callback_address) &&
                  callback_address != 0;
              if (!identity_ok) {
                capture.reason = "backend-shader-vcall-entry-read-failed";
                set_error("shader manager/vtable callback identity failed");
                request_termination = true;
              } else {
                auto &current = capture.backend_stages.back();
                current.shader_vcall_entry_observed = true;
                current.shader_manager = context.Rbx;
                current.shader_dispatch_table = context.Rax;
                current.shader_callback_address = callback_address;
                AddStep(capture, "backend-shader-vcall-entry",
                        event.dwThreadId, rip, started);
                stage = Stage::backend_shader_vcall_result;
                if (!SetExecuteBreakpoint(
                        thread,
                        capture.image_base + kBackendShaderVcallResultRva,
                        false)) {
                  capture.reason =
                      "backend-shader-vcall-result-breakpoint-install-failed";
                  set_error(std::to_string(GetLastError()));
                  request_termination = true;
                }
              }
              CloseHandle(thread);
            } else if (is_target_thread &&
                       stage == Stage::backend_shader_vcall_result &&
                       rip == capture.image_base +
                           kBackendShaderVcallResultRva) {
              std::uint64_t vcall_output = 0;
              const bool identity_ok = !capture.backend_stages.empty() &&
                  capture.backend_stages.back().shader_vcall_entry_observed &&
                  context.Rax != 0 &&
                  ReadValue(process_info.hProcess, context.Rax,
                            vcall_output);
              if (!identity_ok) {
                capture.reason = "backend-shader-vcall-result-read-failed";
                set_error("shader vcall wrapper/output read failed");
                request_termination = true;
              } else {
                auto &current = capture.backend_stages.back();
                current.shader_vcall_result_observed = true;
                current.shader_vcall_wrapper_address = context.Rax;
                current.shader_vcall_output = vcall_output;
                AddStep(capture, "backend-shader-vcall-result",
                        event.dwThreadId, rip, started);
                stage = Stage::backend_shader_getter_result;
                if (!SetExecuteBreakpoint(
                        thread,
                        capture.image_base + kBackendShaderGetterResultRva,
                        false)) {
                  capture.reason =
                      "backend-shader-getter-result-breakpoint-install-failed";
                  set_error(std::to_string(GetLastError()));
                  request_termination = true;
                }
              }
              CloseHandle(thread);
            } else if (is_target_thread &&
                       stage == Stage::backend_shader_getter_result &&
                       rip == capture.image_base +
                           kBackendShaderGetterResultRva) {
              std::uint64_t getter_output = 0;
              const bool identity_ok = !capture.backend_stages.empty() &&
                  capture.backend_stages.back().shader_vcall_result_observed &&
                  context.Rsi != 0 &&
                  ReadValue(process_info.hProcess, context.Rsi,
                            getter_output);
              if (!identity_ok) {
                capture.reason = "backend-shader-getter-result-read-failed";
                set_error("shader getter output read failed");
                request_termination = true;
              } else {
                auto &current = capture.backend_stages.back();
                current.shader_getter_result_observed = true;
                current.shader_getter_output = getter_output;
                AddStep(capture, "backend-shader-getter-result",
                        event.dwThreadId, rip, started);
                stage = Stage::backend_shader_result;
                if (!SetExecuteBreakpoint(
                        thread,
                        capture.image_base + kBackendShaderResultRva,
                        false)) {
                  capture.reason =
                      "backend-shader-result-breakpoint-install-failed";
                  set_error(std::to_string(GetLastError()));
                  request_termination = true;
                }
              }
              CloseHandle(thread);
            } else if (is_target_thread &&
                       stage == Stage::backend_shader_result &&
                       rip == capture.image_base + kBackendShaderResultRva) {
              const bool identity_ok = !capture.backend_stages.empty() &&
                  capture.backend_stages.back().hlsl_ok &&
                  capture.backend_stages.back().index ==
                      static_cast<std::uint32_t>(context.R13);
              const bool origin_ok = identity_ok &&
                  capture.backend_stages.back().shader_cache_result_observed &&
                  ((capture.backend_stages.back().shader_cache_output != 0 &&
                    !capture.backend_stages.back().shader_getter_result_observed &&
                    context.R14 ==
                        capture.backend_stages.back().shader_cache_output) ||
                   (capture.backend_stages.back().shader_cache_output == 0 &&
                    capture.backend_stages.back().shader_getter_result_observed &&
                    context.R14 ==
                        capture.backend_stages.back().shader_getter_output));
              if (!origin_ok) {
                capture.reason = "backend-shader-result-cross-check-failed";
                set_error("shader cache/vcall/getter/main result disagreed");
                request_termination = true;
              } else {
                auto &current = capture.backend_stages.back();
                current.shader_result_observed = true;
                current.shader_output = context.R14;
                AddStep(capture, "backend-shader-result", event.dwThreadId,
                        rip, started);
                stage = (context.R14 == 0 || current.index == 8)
                    ? Stage::backend_initializer_result
                    : Stage::backend_stage_loop;
                if (!SetExecuteBreakpoint(
                        thread,
                        capture.image_base + TargetRvaForStage(stage),
                        false)) {
                  capture.reason =
                      "post-backend-shader-result-breakpoint-install-failed";
                  set_error(std::to_string(GetLastError()));
                  request_termination = true;
                }
              }
              CloseHandle(thread);
            } else if (is_target_thread &&
                       stage == Stage::backend_initializer_result &&
                       rip == capture.image_base +
                           kBackendInitializerResultRva) {
              capture.backend_initializer_result_observed = true;
              capture.backend_initializer_result =
                  (context.Rax & 0xFFU) != 0;
              const auto detail = ClassifyBackendDetail(capture);
              const bool detail_ok = detail != "not-observed" &&
                  detail != "backend-detail-inconsistent" &&
                  detail != "backend-initializer-false-unclassified";
              if (!detail_ok) {
                capture.reason =
                    "backend-initializer-detail-classification-failed";
                set_error("initializer result did not match captured branch");
                request_termination = true;
              } else {
                AddStep(capture, "backend-initializer-result",
                        event.dwThreadId, rip, started);
                stage = Stage::backend_callback_output;
                if (!SetExecuteBreakpoint(
                        thread,
                        capture.image_base + kBackendCallbackOutputRva,
                        false)) {
                  capture.reason =
                      "backend-callback-output-breakpoint-install-failed";
                  set_error(std::to_string(GetLastError()));
                  request_termination = true;
                }
              }
              CloseHandle(thread);
            } else if (is_target_thread &&
                       stage == Stage::backend_callback_output &&
                       rip == capture.image_base + kBackendCallbackOutputRva) {
              std::uint64_t callback_output = 0;
              const bool identity_ok =
                  capture.backend_initializer_result_observed &&
                  context.R14 == capture.backend_callback_output_slot &&
                  ReadValue(process_info.hProcess, context.R14,
                            callback_output) &&
                  callback_output == context.Rbx &&
                  ((capture.backend_initializer_result &&
                    callback_output == capture.backend_initializer_object) ||
                   (!capture.backend_initializer_result &&
                    callback_output == 0));
              if (!identity_ok) {
                capture.reason = "backend-callback-output-cross-check-failed";
                set_error("callback output slot/result disagreed");
                request_termination = true;
              } else {
                capture.backend_callback_output_observed = true;
                capture.backend_callback_output = callback_output;
                AddStep(capture, "backend-callback-output", event.dwThreadId,
                        rip, started);
                stage = Stage::backend_vcall_result;
                if (!SetExecuteBreakpoint(
                        thread,
                        capture.image_base + kBackendVcallResultRva,
                        false)) {
                  capture.reason =
                      "backend-vcall-result-breakpoint-install-failed";
                  set_error(std::to_string(GetLastError()));
                  request_termination = true;
                }
              }
              CloseHandle(thread);
            } else if (is_target_thread &&
                       stage == Stage::backend_vcall_result &&
                       rip == capture.image_base + kBackendVcallResultRva) {
              std::uint64_t vcall_output = 0;
              const bool identity_ok =
                  capture.backend_cache_result_observed &&
                  capture.backend_cache_output == 0 &&
                  capture.backend_callback_entry_observed &&
                  capture.backend_initializer_result_observed &&
                  capture.backend_callback_output_observed &&
                  context.Rdi == capture.factory_rbp + 0x7F &&
                  context.Rax != 0 &&
                  ReadValue(process_info.hProcess, context.Rax,
                            vcall_output) &&
                  vcall_output == capture.backend_callback_output;
              if (!identity_ok) {
                capture.reason = "backend-vcall-result-read-failed";
                set_error("backend vcall wrapper/output identity failed");
                request_termination = true;
              } else {
                capture.backend_vcall_result_observed = true;
                capture.backend_vcall_wrapper_address = context.Rax;
                capture.backend_vcall_output = vcall_output;
                AddStep(capture, "backend-vcall-result", event.dwThreadId,
                        rip, started);
                stage = Stage::backend;
                if (!SetExecuteBreakpoint(
                        thread, capture.image_base + kBackendRva, false)) {
                  capture.reason = "backend-breakpoint-install-failed";
                  set_error(std::to_string(GetLastError()));
                  request_termination = true;
                }
              }
              CloseHandle(thread);
            } else if (is_target_thread && stage == Stage::backend &&
                       rip == capture.image_base + kBackendRva) {
              capture.backend_observed = true;
              const bool output_ok =
                  ReadValue(process_info.hProcess, context.Rbp + 0x7F,
                            capture.backend_output);
              const bool source_ok =
                  ReadValue(process_info.hProcess, context.Rbp + 0x77,
                            capture.backend_source_confirm);
              capture.backend_variant_confirm = context.R12;
              const bool origin_ok =
                  capture.backend_entry_observed &&
                  capture.backend_cache_result_observed &&
                  ((capture.backend_cache_output != 0 &&
                    !capture.backend_vcall_result_observed &&
                    capture.backend_output == capture.backend_cache_output) ||
                   (capture.backend_cache_output == 0 &&
                    capture.backend_vcall_result_observed &&
                    capture.backend_output == capture.backend_vcall_output));
              if (!output_ok || !source_ok ||
                  capture.backend_source_confirm != capture.source_output ||
                  capture.backend_variant_confirm != capture.variant_output ||
                  !origin_ok) {
                capture.reason = "backend-cross-check-failed";
                set_error(std::to_string(GetLastError()));
                request_termination = true;
              } else {
                AddStep(capture, "backend", event.dwThreadId, rip, started);
                stage = Stage::returned;
                if (!SetExecuteBreakpoint(thread,
                                          capture.image_base + kReturnRva,
                                          false)) {
                  capture.reason = "return-breakpoint-install-failed";
                  set_error(std::to_string(GetLastError()));
                  request_termination = true;
                }
              }
              CloseHandle(thread);
            } else if (is_target_thread && stage == Stage::returned &&
                       rip == capture.image_base + kReturnRva) {
              capture.return_observed = true;
              const bool identity_ok = context.Rbp == capture.caller_rbp &&
                  context.R14 == capture.manager;
              const bool output_ok = ReadValue(
                  process_info.hProcess, capture.output_address,
                  capture.final_output);
              AddStep(capture, "return", event.dwThreadId, rip, started);
              capture.classification = Classify(capture);
              if (!identity_ok || !output_ok ||
                  capture.classification == "unclassified") {
                capture.reason = "return-classification-failed";
                if (!identity_ok) set_error("caller identity drift");
                else if (!output_ok) set_error("final output read failed");
              } else {
                capture.result = "GREEN_DIAGNOSTIC";
                capture.reason =
                    "exact-particle2-source-detail-result-captured";
              }
              stage = Stage::complete;
              capture.diagnostic_termination_requested = true;
              request_termination = true;
              CloseHandle(thread);
            } else {
              capture.result = "RED";
              capture.reason = "unexpected-owned-hardware-breakpoint";
              set_error("DR6.B0 was set at an unexpected thread, RIP, or stage");
              request_termination = true;
              CloseHandle(thread);
            }
          }
        } else if (code == EXCEPTION_BREAKPOINT &&
                   !initial_loader_breakpoint_seen) {
          // The first loader breakpoint is not one of this probe's hardware
          // execute breakpoints.
          initial_loader_breakpoint_seen = true;
          continue_status = DBG_CONTINUE;
        } else {
          continue_status = DBG_EXCEPTION_NOT_HANDLED;
        }
      }

      if (request_termination && !capture.debug_registers_cleared) {
        bool all_cleared = true;
        for (const DWORD thread_id : live_threads) {
          HANDLE thread = OpenDebugThread(thread_id);
          if (!thread || !ClearDebugRegisters(thread)) all_cleared = false;
          if (thread) CloseHandle(thread);
        }
        capture.debug_registers_cleared = all_cleared;
        if (!all_cleared) {
          capture.result = "RED";
          capture.reason = "debug-register-clear-failed";
          set_error("one or more live threads retained debugger state");
          request_termination = true;
        }
      }

      const bool continue_ok =
          ContinueDebugEvent(event.dwProcessId, event.dwThreadId,
                             continue_status) != FALSE;
      if (!continue_ok) {
        capture.result = "RED";
        capture.reason = "capture-event-continue-failed";
        set_error("ContinueDebugEvent failed: " +
                  std::to_string(GetLastError()));
        running = false;
      }
      debug_event_outstanding = false;
      if (stage == Stage::complete &&
          capture.diagnostic_termination_requested && continue_ok) {
        capture.capture_event_continued = true;
      }
    }
  } catch (const std::exception &error) {
    set_error(error.what());
    if (capture.reason == "not-started") capture.reason = "preflight-failed";
  }

  if (debug_event_outstanding) {
    ContinueDebugEvent(last_event.dwProcessId, last_event.dwThreadId,
                       DBG_CONTINUE);
  }
  if (process_info.hProcess) {
    if (capture.diagnostic_termination_requested &&
        capture.exit_event_observed &&
        WaitForSingleObject(process_info.hProcess, 5000) == WAIT_OBJECT_0) {
      capture.process_terminated = true;
    } else if (WaitForSingleObject(process_info.hProcess, 0) ==
               WAIT_OBJECT_0) {
      capture.process_terminated = true;
    } else if (capture.debugger_detached &&
               WaitForSingleObject(process_info.hProcess, 5000) ==
                   WAIT_OBJECT_0) {
      capture.natural_exit_observed = true;
      capture.process_terminated = true;
    } else {
      capture.cleanup_forced = true;
      TerminateProcess(process_info.hProcess, 0);
      if (WaitForSingleObject(process_info.hProcess, 5000) == WAIT_OBJECT_0) {
        capture.process_terminated = true;
      }
    }
  }
  if (job) CloseHandle(job);
  if (process_info.hThread) CloseHandle(process_info.hThread);
  if (process_info.hProcess) CloseHandle(process_info.hProcess);
  finish_elapsed();

  if (capture.result == "GREEN_DIAGNOSTIC" &&
      (!capture.debugger_attached || !capture.primary_thread_resumed ||
       !capture.debug_registers_cleared ||
       !capture.capture_event_continued ||
       !capture.diagnostic_termination_requested ||
       capture.native_continuation_claimed || !capture.process_terminated ||
       !capture.exit_event_observed || capture.cleanup_forced)) {
    capture.result = "RED";
    capture.reason = "cleanup-proof-incomplete";
    if (capture.error.empty()) {
      capture.error = "diagnostic observation completed without full "
                      "event-continuation/intentional-exit proof";
    }
  }

  if (capture.return_observed &&
      capture.classification != "unclassified") {
    capture.capture_status = "complete-valid";
  } else if (capture.target_tuple_observed) {
    capture.capture_status = "incomplete";
  }
  if (capture.diagnostic_termination_requested &&
      capture.debug_registers_cleared && capture.capture_event_continued &&
      capture.process_terminated && capture.exit_event_observed &&
      !capture.cleanup_forced) {
    capture.cleanup_status = "diagnostic-termination-clean";
    capture.process_exit_kind = "diagnostic-termination";
  } else if (capture.process_terminated) {
    capture.cleanup_status = "cleanup-reclaimed";
    capture.process_exit_kind = "cleanup-reclamation";
  } else if (capture.ck3_started) {
    capture.cleanup_status = "cleanup-failed";
  }

  try {
    AtomicWrite(options.output, CaptureJson(capture, options, stage));
    capture.artifact_committed = true;
  } catch (const std::exception &error) {
    std::cerr << "artifact write failed: " << error.what() << '\n';
    return 3;
  }
  std::cout << capture.result << ' ' << capture.classification << ' '
            << capture.reason << '\n';
  return capture.result == "GREEN_DIAGNOSTIC" ? 0 : 2;
}

}  // namespace

int wmain(int argc, wchar_t **argv) {
  try {
    const auto options = ParseOptions(argc, argv);
    if (options.self_test) {
      if (!SelfTest()) {
        std::cerr << "self-test: RED\n";
        return 1;
      }
      if (!options.exe.empty()) {
        if (!std::filesystem::is_regular_file(options.exe) ||
            std::filesystem::file_size(options.exe) != kExpectedExeSize ||
            Sha256(options.exe) != Narrow(kExpectedExeSha256)) {
          std::cerr << "self-test exact executable hash: RED\n";
          return 1;
        }
        std::cout << "self-test exact executable hash: GREEN\n";
      }
      std::cout << "self-test: GREEN\n";
      return 0;
    }
    return Run(options);
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 2;
  }
}
