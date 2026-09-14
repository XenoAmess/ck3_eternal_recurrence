#include "xar_bridge/marriage_alliance_projection_adapter_v1.hpp"

#include <array>
#include <limits>

namespace xar::bridge {
namespace {

void SetFailure(MarriageAllianceProjectionStateV1 &state,
                MarriageAllianceProjectionFailureV1 failure) noexcept {
  state.last_failure.store(static_cast<std::uint32_t>(failure),
                           std::memory_order_release);
}

bool ReadMemory(const MarriageAllianceProjectionEnvironmentV1 &env,
                std::uintptr_t address, void *output, std::size_t size) {
  return env.read_memory != nullptr && address != 0 && output != nullptr &&
      size != 0 && env.read_memory(env.memory_context, address, output, size);
}

template <typename Value>
bool ReadAt(const MarriageAllianceProjectionEnvironmentV1 &env,
            std::uintptr_t base, std::size_t offset, Value &output) {
  return base != 0 &&
      offset <= (std::numeric_limits<std::uintptr_t>::max)() - base &&
      ReadMemory(env, base + offset, &output, sizeof(output));
}

MarriageAllianceProjectionFailureV1 Validate(
    const MarriageAllianceProjectionEnvironmentV1 &env) {
  if (!env.exact_build_admitted ||
      env.admitted_executable_sha256 !=
          kMarriageProposalNativeBinderExecutableSha256V1 ||
      (!env.offline_fixture && env.module_base == 0))
    return MarriageAllianceProjectionFailureV1::exact_build_not_admitted;
  if (env.read_memory == nullptr)
    return MarriageAllianceProjectionFailureV1::memory_reader_unavailable;
  if (env.character_storage_slot == 0 ||
      env.current_player_id_address == 0)
    return MarriageAllianceProjectionFailureV1::binding_mismatch;
  if (env.offline_fixture) return MarriageAllianceProjectionFailureV1::none;
  if (env.character_storage_slot !=
          env.module_base + kMarriageCharacterStorageSlotRvaV1 ||
      env.current_player_id_address !=
          env.module_base + kMarriageInfoCurrentPlayerIdRvaV1)
    return MarriageAllianceProjectionFailureV1::binding_mismatch;
  struct Prefix {
    std::uintptr_t rva;
    std::array<std::uint8_t, 16> bytes;
  };
  constexpr std::array<Prefix, 5> prefixes{{
      {kMarriageInfoAllianceItemsCallbackRvaV1,
       {0x48, 0x83, 0xEC, 0x58, 0x4C, 0x8B, 0xC2, 0x48,
        0x85, 0xC9, 0x74, 0x40, 0x48, 0x8D, 0x41, 0x50}},
      {kMarriageInfoAllianceProducerRvaV1,
       {0x48, 0x89, 0x5C, 0x24, 0x18, 0x48, 0x89, 0x54,
        0x24, 0x10, 0x55, 0x56, 0x57, 0x41, 0x54, 0x41}},
      {kMarriageInfoAllianceClearRvaV1,
       {0x48, 0x89, 0x5C, 0x24, 0x10, 0x56, 0x48, 0x83,
        0xEC, 0x20, 0x8B, 0x59, 0x0C, 0x48, 0x8B, 0xF1}},
      {kMarriageInfoAllianceAppendRvaV1,
       {0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x6C,
        0x24, 0x10, 0x48, 0x89, 0x74, 0x24, 0x18, 0x48}},
      {kMarriageInfoAllianceRowResolverRvaV1,
       {0x4C, 0x8B, 0x0D, 0x89, 0x74, 0x49, 0x04, 0x8B,
        0x01, 0x4C, 0x8B, 0x05, 0x88, 0x74, 0x49, 0x04}},
  }};
  for (const auto &prefix : prefixes) {
    std::array<std::uint8_t, 16> actual{};
    if (!ReadMemory(env, env.module_base + prefix.rva, actual.data(),
                    actual.size()) ||
        actual != prefix.bytes)
      return MarriageAllianceProjectionFailureV1::signature_mismatch;
  }
  return MarriageAllianceProjectionFailureV1::none;
}

struct ProjectionSampleV1 {
  std::uintptr_t data = 0;
  std::int32_t capacity = 0;
  std::int32_t count = 0;
  std::uintptr_t allocator = 0;
  std::uint32_t current_player_id = 0;
};

MarriageAllianceProjectionFailureV1 ReadHeader(
    const MarriageAllianceProjectionEnvironmentV1 &env,
    std::uintptr_t marriage_info, ProjectionSampleV1 &output) {
  output = {};
  if (!ReadAt(env, marriage_info, kMarriageInfoAllianceDataOffsetV1,
              output.data) ||
      !ReadAt(env, marriage_info, kMarriageInfoAllianceCapacityOffsetV1,
              output.capacity) ||
      !ReadAt(env, marriage_info, kMarriageInfoAllianceCountOffsetV1,
              output.count) ||
      !ReadAt(env, marriage_info, kMarriageInfoAllianceAllocatorOffsetV1,
              output.allocator) ||
      !ReadMemory(env, env.current_player_id_address,
                  &output.current_player_id,
                  sizeof(output.current_player_id)) ||
      output.capacity < 0 || output.count < 0 ||
      output.count > output.capacity ||
      output.count > kMarriageInfoMaximumAllianceRowsV1 ||
      (output.count != 0 && output.data == 0))
    return MarriageAllianceProjectionFailureV1::projection_header_invalid;
  return MarriageAllianceProjectionFailureV1::none;
}

bool ResolveFullCharacterId(
    const MarriageAllianceProjectionEnvironmentV1 &env,
    std::uint32_t character_id) {
  std::uintptr_t storage = 0;
  std::uintptr_t slots = 0;
  std::int32_t capacity = 0;
  if (!ReadMemory(env, env.character_storage_slot, &storage,
                  sizeof(storage)) ||
      storage == 0 ||
      !ReadAt(env, storage, kMarriageCharacterStorageSlotsOffsetV1, slots) ||
      !ReadAt(env, storage, kMarriageCharacterStorageCapacityOffsetV1,
              capacity) ||
      slots == 0 || capacity <= 0)
    return false;
  const auto index = character_id & 0x00FFFFFFU;
  if (index >= static_cast<std::uint32_t>(capacity)) return false;
  const auto offset = static_cast<std::uintptr_t>(index) *
          kMarriageCharacterStorageSlotStrideV1 +
      kMarriageCharacterStorageSlotObjectOffsetV1;
  if (offset > (std::numeric_limits<std::uintptr_t>::max)() - slots)
    return false;
  std::uintptr_t character = 0;
  std::uint32_t resolved_id = 0;
  return ReadMemory(env, slots + offset, &character, sizeof(character)) &&
      character != 0 &&
      ReadAt(env, character, kMarriageCharacterIdOffsetV1, resolved_id) &&
      resolved_id == character_id;
}

MarriageAllianceProjectionFailureV1 ReadProjection(
    const MarriageAllianceProjectionEnvironmentV1 &env,
    std::uintptr_t marriage_info, std::uint32_t first_character_id,
    std::uint32_t second_character_id, bool &projected) {
  projected = false;
  ProjectionSampleV1 before{};
  auto failure = ReadHeader(env, marriage_info, before);
  if (failure != MarriageAllianceProjectionFailureV1::none) return failure;
  if (!ResolveFullCharacterId(env, before.current_player_id))
    return MarriageAllianceProjectionFailureV1::
        current_player_identity_unavailable;
  std::uint32_t other_id = 0;
  if (first_character_id == before.current_player_id) {
    other_id = second_character_id;
  } else if (second_character_id == before.current_player_id) {
    other_id = first_character_id;
  } else {
    return MarriageAllianceProjectionFailureV1::pair_not_current_player;
  }
  if (!ResolveFullCharacterId(env, other_id))
    return MarriageAllianceProjectionFailureV1::row_identity_unavailable;
  auto scan = [&](bool &found, std::uint64_t &identity_hash) {
    found = false;
    identity_hash = 1469598103934665603ULL;
    for (std::int32_t index = 0; index < before.count; ++index) {
      const auto unsigned_index = static_cast<std::uintptr_t>(index);
      if (unsigned_index >
          ((std::numeric_limits<std::uintptr_t>::max)() - before.data) /
              kMarriageInfoAllianceRowStrideV1)
        return MarriageAllianceProjectionFailureV1::projection_header_invalid;
      std::uint32_t row_id = 0;
      if (!ReadMemory(env,
                      before.data + unsigned_index *
                              kMarriageInfoAllianceRowStrideV1,
                      &row_id, sizeof(row_id)) ||
          !ResolveFullCharacterId(env, row_id))
        return MarriageAllianceProjectionFailureV1::row_identity_unavailable;
      identity_hash ^= row_id;
      identity_hash *= 1099511628211ULL;
      if (row_id == other_id) found = true;
    }
    return MarriageAllianceProjectionFailureV1::none;
  };
  std::uint64_t first_hash = 0;
  failure = scan(projected, first_hash);
  if (failure != MarriageAllianceProjectionFailureV1::none) return failure;
  ProjectionSampleV1 after{};
  failure = ReadHeader(env, marriage_info, after);
  if (failure != MarriageAllianceProjectionFailureV1::none ||
      before.data != after.data || before.capacity != after.capacity ||
      before.count != after.count || before.allocator != after.allocator ||
      before.current_player_id != after.current_player_id)
    return MarriageAllianceProjectionFailureV1::projection_sample_drift;
  bool projected_second = false;
  std::uint64_t second_hash = 0;
  failure = scan(projected_second, second_hash);
  if (failure != MarriageAllianceProjectionFailureV1::none)
    return failure;
  if (projected_second != projected || second_hash != first_hash)
    return MarriageAllianceProjectionFailureV1::projection_sample_drift;
  return MarriageAllianceProjectionFailureV1::none;
}

} // namespace

MarriageAllianceProjectionEnvironmentV1
BindMarriageAllianceProjectionEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted,
    std::string_view admitted_executable_sha256) noexcept {
  MarriageAllianceProjectionEnvironmentV1 output{};
  output.module_base = module_base;
  output.exact_build_admitted = exact_build_admitted;
  output.admitted_executable_sha256 = admitted_executable_sha256;
  if (module_base != 0 &&
      kMarriageCharacterStorageSlotRvaV1 <=
          (std::numeric_limits<std::uintptr_t>::max)() - module_base &&
      kMarriageInfoCurrentPlayerIdRvaV1 <=
          (std::numeric_limits<std::uintptr_t>::max)() - module_base) {
    output.character_storage_slot =
        module_base + kMarriageCharacterStorageSlotRvaV1;
    output.current_player_id_address =
        module_base + kMarriageInfoCurrentPlayerIdRvaV1;
  }
  return output;
}

bool ReadMarriageAllianceProjectionPairExactV1(
    MarriageAllianceProjectionStateV1 &state,
    std::uintptr_t marriage_info, std::uint32_t first_character_id,
    std::uint32_t second_character_id, bool &projected) noexcept {
  projected = false;
  auto failure = Validate(state.environment);
  if (failure == MarriageAllianceProjectionFailureV1::none &&
      (marriage_info == 0 || first_character_id == 0 ||
       second_character_id == 0 || first_character_id == second_character_id))
    failure = MarriageAllianceProjectionFailureV1::invalid_input;
  if (failure == MarriageAllianceProjectionFailureV1::none)
    failure = ReadProjection(state.environment, marriage_info,
                             first_character_id, second_character_id,
                             projected);
  SetFailure(state, failure);
  return failure == MarriageAllianceProjectionFailureV1::none;
}

MarriageAllianceProjectionFailureV1 ReadMarriageAllianceProjectionFailureV1(
    const MarriageAllianceProjectionStateV1 &state) noexcept {
  return static_cast<MarriageAllianceProjectionFailureV1>(
      state.last_failure.load(std::memory_order_acquire));
}

} // namespace xar::bridge
