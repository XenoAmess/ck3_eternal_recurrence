#include "xar_bridge/war_entry_assessments_v1.hpp"

#include <windows.h>
#include <bcrypt.h>

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iterator>
#include <limits>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace {

std::string ReadFile(const char *path) {
  std::ifstream stream(path, std::ios::binary);
  return {std::istreambuf_iterator<char>(stream),
          std::istreambuf_iterator<char>()};
}

bool Contains(std::string_view haystack, std::string_view needle) {
  return haystack.find(needle) != std::string_view::npos;
}

template <std::size_t Size>
bool ContainsAll(std::string_view haystack,
                 const std::array<std::string_view, Size> &needles) {
  return std::all_of(needles.begin(), needles.end(),
                     [haystack](std::string_view needle) {
                       return Contains(haystack, needle);
                     });
}

template <typename Value>
bool ReadInteger(std::string_view image, std::size_t offset,
                 Value &output) {
  if (offset > image.size() || sizeof(output) > image.size() - offset) {
    return false;
  }
  std::memcpy(&output, image.data() + offset, sizeof(output));
  return true;
}

std::optional<std::size_t> RvaToOffset(std::string_view image,
                                       std::uint32_t rva) {
  std::uint32_t pe_offset = 0;
  if (image.size() < 0x40 || image.substr(0, 2) != "MZ" ||
      !ReadInteger(image, 0x3C, pe_offset) ||
      pe_offset > image.size() - 24 ||
      image.substr(pe_offset, 4) != std::string_view{"PE\0\0", 4}) {
    return std::nullopt;
  }
  std::uint16_t section_count = 0;
  std::uint16_t optional_header_size = 0;
  if (!ReadInteger(image, pe_offset + 6, section_count) ||
      !ReadInteger(image, pe_offset + 20, optional_header_size) ||
      section_count == 0 || section_count > 128) {
    return std::nullopt;
  }
  const auto section_table =
      static_cast<std::size_t>(pe_offset) + 24 + optional_header_size;
  if (section_table > image.size() ||
      static_cast<std::size_t>(section_count) >
          (image.size() - section_table) / 40) {
    return std::nullopt;
  }
  for (std::uint16_t index = 0; index < section_count; ++index) {
    const auto row = section_table + static_cast<std::size_t>(index) * 40;
    std::uint32_t virtual_size = 0;
    std::uint32_t virtual_address = 0;
    std::uint32_t raw_size = 0;
    std::uint32_t raw_offset = 0;
    if (!ReadInteger(image, row + 8, virtual_size) ||
        !ReadInteger(image, row + 12, virtual_address) ||
        !ReadInteger(image, row + 16, raw_size) ||
        !ReadInteger(image, row + 20, raw_offset)) {
      return std::nullopt;
    }
    const auto mapped_size = std::max(virtual_size, raw_size);
    if (rva < virtual_address || rva - virtual_address >= mapped_size) {
      continue;
    }
    const auto delta = static_cast<std::size_t>(rva - virtual_address);
    if (delta >= raw_size || raw_offset > image.size() ||
        delta > image.size() - raw_offset) {
      return std::nullopt;
    }
    return static_cast<std::size_t>(raw_offset) + delta;
  }
  return std::nullopt;
}

bool BytesAt(std::string_view image, std::uint32_t rva,
             std::initializer_list<std::uint8_t> expected) {
  const auto offset = RvaToOffset(image, rva);
  if (!offset || *offset > image.size() ||
      expected.size() > image.size() - *offset) {
    return false;
  }
  return std::equal(expected.begin(), expected.end(),
                    reinterpret_cast<const std::uint8_t *>(image.data()) +
                        *offset);
}

bool Sha256Upper(std::string_view input, std::string &output) {
  output.clear();
  if (input.size() > std::numeric_limits<ULONG>::max()) {
    return false;
  }
  BCRYPT_ALG_HANDLE algorithm = nullptr;
  BCRYPT_HASH_HANDLE hash = nullptr;
  std::vector<std::uint8_t> object;
  std::array<std::uint8_t, 32> digest{};
  bool succeeded = false;
  do {
    if (BCryptOpenAlgorithmProvider(&algorithm, BCRYPT_SHA256_ALGORITHM,
                                    nullptr, 0) < 0) {
      break;
    }
    DWORD object_size = 0;
    DWORD copied = 0;
    if (BCryptGetProperty(algorithm, BCRYPT_OBJECT_LENGTH,
                          reinterpret_cast<PUCHAR>(&object_size),
                          sizeof(object_size), &copied, 0) < 0 ||
        object_size == 0 || copied != sizeof(object_size)) {
      break;
    }
    object.resize(object_size);
    if (BCryptCreateHash(algorithm, &hash, object.data(), object_size, nullptr,
                         0, 0) < 0 ||
        BCryptHashData(
            hash,
            reinterpret_cast<PUCHAR>(const_cast<char *>(input.data())),
            static_cast<ULONG>(input.size()), 0) < 0 ||
        BCryptFinishHash(hash, digest.data(),
                         static_cast<ULONG>(digest.size()), 0) < 0) {
      break;
    }
    succeeded = true;
  } while (false);
  if (hash != nullptr) {
    BCryptDestroyHash(hash);
  }
  if (algorithm != nullptr) {
    BCryptCloseAlgorithmProvider(algorithm, 0);
  }
  if (!succeeded) {
    return false;
  }
  constexpr char digits[] = "0123456789ABCDEF";
  output.resize(digest.size() * 2);
  for (std::size_t index = 0; index < digest.size(); ++index) {
    output[index * 2] = digits[digest[index] >> 4U];
    output[index * 2 + 1] = digits[digest[index] & 0x0FU];
  }
  return true;
}

} // namespace

int main(int argc, char **argv) {
  if (argc != 8) {
    return 1;
  }
  const auto header = ReadFile(argv[1]);
  const auto reader = ReadFile(argv[2]);
  const auto serializer = ReadFile(argv[3]);
  const auto abi = ReadFile(argv[4]);
  const auto fixture = ReadFile(argv[5]);
  const auto documentation = ReadFile(argv[6]);
  const auto executable = ReadFile(argv[7]);
  if (header.empty() || reader.empty() || serializer.empty() || abi.empty() ||
      fixture.empty() || documentation.empty() || executable.empty()) {
    return 2;
  }

  if (!xar::ck3_11906::kWarEntryAssessmentsV1CapabilityAdvertised ||
      xar::ck3_11906::kWarEntryAssessmentsV1MaximumTargets != 1 ||
      xar::ck3_11906::kWarEntryAssessmentsV1FixedPointScale != 100'000 ||
      xar::ck3_11906::kWarEntryActorStateBuilderRva != 0x18784D0 ||
      xar::ck3_11906::kWarEntryAssessmentRva != 0x1878A00 ||
      xar::ck3_11906::kWarEntryNetworkCollectorRva != 0x1879850 ||
      xar::ck3_11906::kWarEntryEffectiveTargetResolverRva != 0x2909D30) {
    return 3;
  }

  constexpr auto required_header = std::to_array<std::string_view>({
      "game.command.query-war-entry-assessments-v1-N",
      "query-war-entry-assessments-v1-",
      "kWarEntryAssessmentsV1CapabilityAdvertised = true",
      "kWarEntryAssessmentsV1GameVersion",
      "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86",
      "kWarEntryAssessmentRva = 0x1878A00",
      "kWarEntryNetworkCollectorRva = 0x1879850",
      "0x2909D30",
      "kWarEntryGameStateSlotRva = 0x570E068",
      "kWarEntryCharacterStorageSlotRva = 0x570C130",
      "kWarEntryCharacterFallbackSlotRva = 0x570C138",
      "kWarEntryActorStateBuilderRva = 0x18784D0",
      "kWarEntryActorStateDependencySlotRva",
      "0x570C638",
      "NativeWarEntryActorStateV1",
      "sizeof(NativeWarEntryActorStateV1) == 0x10",
      "power_base_raw) == 0x00",
      "native_state_08_raw) ==",
      "native_state_0c_raw) ==",
      "native_flags_raw) == 0x0E",
      "native_state_0f_raw) ==",
      "NativeWarEntryActorStateBuilderFunctionV1",
      "actor_state_dependency_slot",
      "actor_state_builder",
      "NativeWarEntryAssessmentOutputV1",
      "sizeof(NativeWarEntryAssessmentOutputV1) == 0x28",
      "target_power_total_raw) == 0x08",
      "actual_power_ratio_raw) == 0x10",
      "native_flags_raw) ==",
      "NativeWarEntryNetworkConfigurationV1",
      "void **root_character",
      "std::int32_t *filter_a",
      "std::int32_t *filter_b",
      "std::int32_t *filter_c",
      "std::int64_t *accumulator",
      "root_character) == 0x00",
      "filter_a) ==",
      "filter_b) ==",
      "filter_c) ==",
      "accumulator) ==",
      "actor_power_base_raw",
      "actor_network_contribution_raw",
      "target_pre_adjustment_total_raw",
      "target_adjustment_delta_raw",
      "native_flags_raw",
      "offline_fixture_function_overrides",
      "IsWarEntryAssessmentMainThreadV1",
      "is_main_thread = nullptr",
      "war_entry_assessment_unavailable:<stage>",
      "SerializeWarEntryAssessmentsV1",
  });
  if (!ContainsAll(header, required_header)) {
    return 4;
  }

  constexpr auto required_reader = std::to_array<std::string_view>({
      "kCharacterIdentityOffset = 0x18",
      "ActorStatesEqualExact",
      "std::memcmp(&left, &right, sizeof(left))",
      "kStorageSlotsOffset = 0x20",
      "kStorageCapacityOffset = 0x2C",
      "kStorageSlotStride = 0x10",
      "kStorageObjectOffset = 0x08",
      "InvokeActorStateBuilder",
      "output = {}",
      "function(actor_character, &output)",
      "environment.actor_state_dependency_slot",
      "kCharacterPowerContainerOffset = 0x1B8",
      "kCharacterPowerRawOffset = 0x308",
      "builder_dependency_unchanged",
      "builder_dependency == nullptr",
      "actor_state.power_base_raw < 0",
      "ActorStatesEqualExact(actor_state, actor_state_after_builder)",
      "environment.module_base + kWarEntryActorStateBuilderRva",
      "environment.module_base + kWarEntryActorStateDependencySlotRva",
      "environment.module_base + kWarEntryAssessmentRva",
      "environment.module_base + kWarEntryNetworkCollectorRva",
      "environment.module_base + kWarEntryEffectiveTargetResolverRva",
      "function(actor_character, target_character, 0, false)",
      "function(root_character, &configuration)",
      "&output, nullptr, 1",
      "target.effective_character, 0, 0, 0",
      "environment.network_collector, actor, 1",
      "CheckedAdd(actor_state.power_base_raw, actor_network, actor_total)",
      "CheckedAdd(target.target_power_base_raw, target_network",
      "CheckedSubtract(native.target_power_total_raw",
      "ReconstructNativeRatio(native.target_power_total_raw, actor_total",
      "row.actual_power_ratio_raw = native.actual_power_ratio_raw",
      "native_ratio_cross_check",
      "AcquireAssessmentRows",
      "resolved, false",
      "resolved, true",
      "repeated_rows != rows",
      "same_frame_native_sample",
      "repeat_target_network_collector",
      "repeat_native_ratio_cross_check",
      "same_frame_actor_state_builder_dependency",
      "same_frame_actor_state_builder",
      "actor_state_builder_mutated",
      "actor_state_builder_dependency_drift",
      "actor_network_intra_sample",
      "network_contribution_domain",
      "same_frame_stamp_after_repeat",
      "same_frame_stamp",
      "actor_same_frame_revalidation",
      "effective_target_same_frame",
      "target_not_declarable",
      "output.assessments = std::move(rows)",
      "output.readiness = {true, true, true, true, true, true, true, true}",
      "output.unavailable_stage.clear()",
      "offline_fixture_function_overrides",
      "access.is_main_thread == nullptr",
      "!access.is_main_thread(access.context)",
      "main_thread_required",
      "EXCEPTION_EXECUTE_HANDLER",
  });
  if (!ContainsAll(reader, required_reader) ||
      Contains(reader, "kGameDataAiManagerOffset") ||
      Contains(reader, "kAiManagerContextsDataOffset") ||
      Contains(reader, "ReadActorWarEntryContext") ||
      Contains(reader, "actor_context_fallback_slot") ||
      Contains(reader, "kCharacterAiExtensionOffset") ||
      Contains(reader, "pending.actor != actor_character") ||
      Contains(reader, "soldier_fallback") ||
      Contains(reader, "partial_assessment")) {
    return 5;
  }

  constexpr std::array<std::string_view, 24> required_serializer{
      "\\\"schema_version\\\":1,\\\"status\\\":\\\"available\\\"",
      "\\\"snapshot_revision\\\"",
      "\\\"requested_target_character_ids\\\"",
      "\\\"target_adjustment_delta_raw\\\"",
      "\\\"actual_power_ratio_raw\\\"",
      "\\\"target_ai_context_actor_entry_raw\\\"",
      "\\\"actor_ai_context_target_entry_raw\\\"",
      "\\\"native_flags_raw\\\"",
      "\\\"actor_identity_ready\\\":true",
      "\\\"targets_declarable_ready\\\":true",
      "\\\"effective_targets_ready\\\":true",
      "\\\"ai_context_ready\\\":true",
      "\\\"native_output_ready\\\":true",
      "\\\"network_decomposition_ready\\\":true",
      "\\\"same_frame_ready\\\":true",
      "\\\"ready\\\":true",
      "\\\"game_version\\\":\\\"1.19.0.6\\\"",
      "\\\"executable_sha256\\\"",
      "\\\"assessment_rva\\\":\\\"0x1878A00\\\"",
      "\\\"network_collector_rva\\\":\\\"0x1879850\\\"",
      "row.actor_network_contribution_raw < 0",
      "row.target_network_contribution_raw < 0",
      "CCharacter+0x1B8->+0x308",
      "return {}",
  };
  if (!ContainsAll(serializer, required_serializer) ||
      Contains(serializer, "\\\"status\\\":\\\"unavailable\\\"")) {
    return 6;
  }

  constexpr auto required_abi = std::to_array<std::string_view>({
      "\"game_version\": \"1.19.0.6\"",
      "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86",
      "\"advertised\": true",
      "\"live_boundary_observation\": true",
      "\"live_executor_observation\": false",
      "\"typed_executor_invoked_live\": true",
      "\"last_live_failure_stage\": \"actor_ai_context\"",
      "0x18784D0",
      "0x18784D0..0x18789F8",
      "caller-owned State16",
      "zero all 0x10 bytes",
      "module+0x570C638",
      "no RNG, script VM or world-object store",
      "0x1878A00",
      "0x1879850",
      "0x2909D30",
      "module+0x570C130",
      "module+0x570C138",
      "module+0x570E068",
      "0x18BE0E9 lea RDX,[RSI+8]",
      "stack5 optional int64 distance override",
      "stack6 int32 include-network mode",
      "target_power_total_raw Q100000",
      "actual_power_ratio_raw Q100000",
      "{target,0,0,0,0}",
      "{actor,1,1,1,0}",
      "0x1B35DF0",
      "0x28BCEB0",
      "0x187A770..0x187A789",
      "State16+0x00",
      "int64 *(CCharacter+0x1B8+0x308)",
      "0x101B125",
      "module+0x57C1CA0",
      "0x101B141",
      "0x18BDFFA",
      "[RDX+0x0E]",
      "0x255A080",
      "0x1885290",
      "0x28BCEB0",
      "AI-only",
      "main_thread_gate",
      "worker_dispatch",
      "same_query_double_sample",
      "no_pointer_cache_across_frame",
      "no partial rows, null fields, soldier fallback or ratio fallback",
  });
  if (!ContainsAll(abi, required_abi)) {
    return 7;
  }

  constexpr std::array<std::string_view, 17> required_fixture{
      "\"snapshot_revision\":74",
      "\"date_raw\":53175816",
      "\"actor_character_id\":29829",
      "\"requested_target_character_ids\":[67890]",
      "\"effective_target_character_id\":67891",
      "\"actor_power_base_raw\":1200000",
      "\"actor_network_contribution_raw\":300000",
      "\"actor_power_total_raw\":1500000",
      "\"target_pre_adjustment_total_raw\":2500000",
      "\"target_adjustment_delta_raw\":-100000",
      "\"target_power_total_raw\":2400000",
      "\"actual_power_ratio_raw\":160000",
      "\"native_flags_raw\":99",
      "\"network_decomposition_ready\":true",
      "\"same_frame_ready\":true",
      "\"assessment_rva\":\"0x1878A00\"",
      "\"network_collector_rva\":\"0x1879850\"",
  };
  if (!ContainsAll(fixture, required_fixture) || Contains(fixture, "null")) {
    return 8;
  }

  constexpr auto required_documentation = std::to_array<std::string_view>({
      "query-war-entry-assessments-v1",
      "```mermaid",
      "0x18784D0",
      "State16",
      "zeroed",
      "module+0x570C638",
      "0x1878A00",
      "0x1879850",
      "0x2909D30",
      "AI context",
      "AIContext",
      "provenance/fixture",
      "0x1885290",
      "actor_ai_context",
      "target_pre_adjustment_total_raw",
      "target_adjustment_delta_raw",
      "actual_power_ratio_raw",
      "native_flags_raw",
      "no partial",
      "main_thread_required",
      "capability",
  });
  if (!ContainsAll(documentation, required_documentation)) {
    return 9;
  }

  std::string digest;
  if (!Sha256Upper(executable, digest) ||
      digest != xar::ck3_11906::kWarEntryAssessmentsV1ExecutableSha256) {
    return 10;
  }
  // Exact instruction anchors close the State16 builder ABI and writes, its
  // cold singleton dependency, register/stack assessment ABI, both 5-pointer
  // configurations, historical context provenance, and the human exclusion
  // which invalidated the retired manager scan.
  if (!BytesAt(executable, 0x18784D0,
               {0x40, 0x55, 0x57, 0x48, 0x83, 0xEC, 0x38}) ||
      !BytesAt(executable, 0x18784DC,
               {0x48, 0x8B, 0xFA, 0x48, 0x89, 0x74, 0x24, 0x58,
                0x48, 0x8B, 0xF1}) ||
      !BytesAt(executable, 0x187850B,
               {0x0F, 0xB7, 0x48, 0x44, 0x66, 0x89, 0x4F, 0x0C}) ||
      !BytesAt(executable, 0x1878535, {0x44, 0x89, 0x77, 0x08}) ||
      !BytesAt(executable, 0x1878565, {0x0F, 0xB6, 0x4F, 0x0E}) ||
      !BytesAt(executable, 0x187861E,
               {0x48, 0x8B, 0x86, 0xB8, 0x01, 0x00, 0x00}) ||
      !BytesAt(executable, 0x187862A,
               {0x48, 0x8B, 0x80, 0x08, 0x03, 0x00, 0x00}) ||
      !BytesAt(executable, 0x1878639, {0x48, 0x89, 0x07}) ||
      !BytesAt(executable, 0x18789BA, {0x48, 0x01, 0x17}) ||
      !BytesAt(executable, 0x18789EE, {0x48, 0x89, 0x2F}) ||
      !BytesAt(executable, 0x0999AF4,
               {0x48, 0x8B, 0x05, 0x3D, 0x2B, 0xD7, 0x04}) ||
      !BytesAt(executable, 0x18849CE,
               {0x49, 0x8D, 0x56, 0x08, 0x49, 0x8B, 0x4E, 0x18}) ||
      !BytesAt(executable, 0x18849D6,
               {0xE8, 0xF5, 0x3A, 0xFF, 0xFF}) ||
      !BytesAt(executable, 0x1885E33,
               {0x49, 0x8D, 0x57, 0x08, 0x49, 0x8B, 0x4F, 0x18}) ||
      !BytesAt(executable, 0x20505C9,
               {0x48, 0x8D, 0x50, 0x08, 0xE8, 0xFE, 0x7E, 0x82, 0xFF}) ||
      !BytesAt(executable, 0x2791DFC,
               {0x48, 0x8D, 0x53, 0x08, 0xE8, 0xCB, 0x66, 0x0E, 0xFF}) ||
      !BytesAt(executable, 0x1878A00,
               {0x48, 0x89, 0x54, 0x24, 0x10, 0x55, 0x53, 0x56, 0x57}) ||
      !BytesAt(executable, 0x1878B9C, {0xE8, 0xAF, 0x0C, 0x00, 0x00}) ||
      !BytesAt(executable, 0x1878BF5, {0xE8, 0x56, 0x0C, 0x00, 0x00}) ||
      !BytesAt(executable, 0x1878F99,
               {0x4D, 0x8B, 0x17, 0x4C, 0x03, 0xD3}) ||
      !BytesAt(executable, 0x1879070, {0x48, 0x89, 0x4F, 0x10}) ||
      !BytesAt(executable, 0x187908E,
               {0x41, 0xF6, 0x40, 0x0E, 0x01}) ||
      !BytesAt(executable, 0x18790B4,
               {0x41, 0xF6, 0x40, 0x0E, 0x01}) ||
      !BytesAt(executable, 0x18790DC,
               {0x41, 0x0A, 0x50, 0x0E}) ||
      !BytesAt(executable, 0x187910D,
               {0x49, 0x8B, 0x85, 0xA8, 0x01, 0x00, 0x00}) ||
      !BytesAt(executable, 0x1879119,
               {0x48, 0x8B, 0x80, 0x78, 0x02, 0x00, 0x00}) ||
      !BytesAt(executable, 0x1879122,
               {0x48, 0x8B, 0x05, 0x77, 0x8B, 0xF4, 0x03}) ||
      !BytesAt(executable, 0x1879129,
               {0x48, 0x8B, 0x40, 0x20}) ||
      !BytesAt(executable, 0x1879248,
               {0xF6, 0x40, 0x0E, 0x01}) ||
      !BytesAt(executable, 0x1879850,
               {0x48, 0x8B, 0xC4, 0x48, 0x89, 0x58, 0x10}) ||
      !BytesAt(executable, 0x187A129,
               {0x49, 0x8B, 0x4C, 0x24, 0x20, 0x48, 0x01, 0x01}) ||
      !BytesAt(executable, 0x18BE0E9, {0x48, 0x8D, 0x56, 0x08}) ||
      !BytesAt(executable, 0x18BE0FA,
               {0x4C, 0x8D, 0x8D, 0xA0, 0x03, 0x00, 0x00}) ||
      !BytesAt(executable, 0x18BE101,
               {0x4D, 0x8B, 0xC5, 0x49, 0x8B, 0xCF}) ||
      !BytesAt(executable, 0x18BE107, {0xE8, 0xF4, 0xA8, 0xFB, 0xFF}) ||
      !BytesAt(executable, 0x101B125,
               {0x48, 0x8B, 0x98, 0xA8, 0x01, 0x00, 0x00}) ||
      !BytesAt(executable, 0x101B131,
               {0x48, 0x8B, 0x9B, 0x78, 0x02, 0x00, 0x00}) ||
      !BytesAt(executable, 0x101B13A,
               {0x48, 0x8B, 0x1D, 0x5F, 0x6B, 0x7A, 0x04}) ||
      !BytesAt(executable, 0x101B141,
               {0x48, 0x83, 0x7B, 0x20, 0x00}) ||
      !BytesAt(executable, 0x101B14C,
               {0x4C, 0x8B, 0x63, 0x18}) ||
      !BytesAt(executable, 0x101B169, {0x48, 0x8B, 0xCB}) ||
      !BytesAt(executable, 0x101B16C,
               {0xE8, 0x2F, 0x2C, 0x8A, 0x00}) ||
      !BytesAt(executable, 0x18BDDAA,
               {0x48, 0x89, 0x4C, 0x24, 0x08}) ||
      !BytesAt(executable, 0x18BDDE0,
               {0x4C, 0x8B, 0x79, 0x18}) ||
      !BytesAt(executable, 0x18BDFFA,
               {0x48, 0x8B, 0xB5, 0x90, 0x4A, 0x01, 0x00}) ||
      !BytesAt(executable, 0x1885290,
               {0x8B, 0x4A, 0x18, 0xE8, 0x18, 0x7C, 0x03, 0x01}) ||
      !BytesAt(executable, 0x1885298,
               {0x84, 0xC0, 0x0F, 0x85, 0x84, 0x00, 0x00, 0x00}) ||
      !BytesAt(executable, 0x18852F5,
               {0xE8, 0x26, 0x7A, 0x09, 0x00}) ||
      !BytesAt(executable, 0x1885309,
               {0x48, 0x89, 0x98, 0x78, 0x02, 0x00, 0x00}) ||
      !BytesAt(executable, 0x255A10F,
               {0x48, 0x8B, 0x05, 0x22, 0x20, 0x1B, 0x03}) ||
      !BytesAt(executable, 0x255A116,
               {0x48, 0x89, 0x41, 0x18}) ||
      !BytesAt(executable, 0x255A124,
               {0x48, 0x89, 0x59, 0x20}) ||
      !BytesAt(executable, 0x2909D30,
               {0x48, 0x89, 0x5C, 0x24, 0x10, 0x48, 0x89, 0x74})) {
    return 11;
  }
  return 0;
}
