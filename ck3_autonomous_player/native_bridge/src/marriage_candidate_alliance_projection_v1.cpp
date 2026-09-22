#include "xar_bridge/marriage_candidate_alliance_projection_v1.hpp"

#include <array>
#include <cstring>
#include <limits>
#include <type_traits>

namespace xar::bridge {
namespace {

struct NativePairVectorV1 {
  void *data = nullptr;
  std::int32_t capacity = 0;
  std::int32_t count = 0;
  void *owner = nullptr;
  // 0x2283470 initializes this owner through vtable 0x413C270. Its
  // +0x20 initializer supplies three inline 0x20-byte rows at owner+8.
  alignas(8) std::array<std::byte, 8 + 3 * 0x20> inline_owner{};
};
static_assert(offsetof(NativePairVectorV1, owner) == 0x10);
static_assert(offsetof(NativePairVectorV1, inline_owner) == 0x18);

struct NativePairRowV1 {
  std::uintptr_t first = 0;
  std::uintptr_t second = 0;
  std::uintptr_t secondary_actor = 0;
  std::uintptr_t secondary_recipient = 0;
};
static_assert(sizeof(NativePairRowV1) == 0x20);

bool ReadMemory(const MarriageCandidateAllianceProjectionEnvironmentV1 &env,
                std::uintptr_t address, void *output, std::size_t size) {
  return env.read_memory != nullptr && address != 0 && output != nullptr &&
         env.read_memory(env.memory_context, address, output, size);
}

template <typename Value>
bool ReadAt(const MarriageCandidateAllianceProjectionEnvironmentV1 &env,
            std::uintptr_t base, std::size_t offset, Value &output) {
  return base != 0 &&
         offset <= (std::numeric_limits<std::uintptr_t>::max)() - base &&
         ReadMemory(env, base + offset, &output, sizeof(output));
}

template <typename Value>
bool AddRva(std::uintptr_t base, std::uintptr_t rva, Value &output) {
  if (base == 0 || rva > (std::numeric_limits<std::uintptr_t>::max)() - base)
    return false;
  if constexpr (std::is_pointer_v<Value>) {
    output = reinterpret_cast<Value>(base + rva);
  } else {
    output = static_cast<Value>(base + rva);
  }
  return true;
}

MarriageCandidateAllianceProjectionFailureV1 Validate(
    const MarriageCandidateAllianceProjectionEnvironmentV1 &env) {
  using Failure = MarriageCandidateAllianceProjectionFailureV1;
  if (!env.exact_build_admitted ||
      env.admitted_executable_sha256 !=
          kMarriageMatchmakingSourceAdapterExecutableSha256V1 ||
      (!env.offline_fixture && env.module_base == 0))
    return Failure::exact_build_not_admitted;
  if (env.read_memory == nullptr || env.project_pairs == nullptr ||
      env.read_boolean_option == nullptr || env.is_allied == nullptr ||
      env.matrilineal_option_id_slot == 0 || env.native_owner_vtable == 0)
    return Failure::binding_unavailable;
  if (env.offline_fixture) return Failure::none;
  ProjectMarriageCandidateAlliancePairsV1 expected_project = nullptr;
  ReadMarriageCandidateBooleanOptionV1 expected_option = nullptr;
  ReadMarriageCandidateIsAlliedV1 expected_allied = nullptr;
  std::uintptr_t expected_option_slot = 0;
  std::uintptr_t expected_vtable = 0;
  if (!AddRva(env.module_base, kMarriageCandidateAlliancePairsRvaV1,
              expected_project) ||
      !AddRva(env.module_base, kMarriageCandidateReadOptionRvaV1,
              expected_option) ||
      !AddRva(env.module_base, kMarriageCandidateIsAlliedRvaV1,
              expected_allied) ||
      !AddRva(env.module_base, kMarriageCandidateMatrilinealOptionSlotRvaV1,
              expected_option_slot) ||
      !AddRva(env.module_base, kMarriageCandidateAllianceOwnerVtableRvaV1,
              expected_vtable) ||
      env.project_pairs != expected_project ||
      env.read_boolean_option != expected_option ||
      env.is_allied != expected_allied ||
      env.matrilineal_option_id_slot != expected_option_slot ||
      env.native_owner_vtable != expected_vtable)
    return Failure::binding_unavailable;
  struct Signature {
    std::uintptr_t rva;
    std::array<std::uint8_t, 16> prefix;
  };
  constexpr std::array<Signature, 4> signatures{{
      {kMarriageCandidateAlliancePairsRvaV1,
       {0x40, 0x55, 0x48, 0x83, 0xEC, 0x30, 0x4C, 0x8B,
        0x05, 0x73, 0x7A, 0x48, 0x03, 0x48, 0x8B, 0xEA}},
      {kMarriageCandidateReadOptionRvaV1,
       {0x4C, 0x8B, 0x09, 0x33, 0xC0, 0x4C, 0x8B, 0xD9,
        0x45, 0x8B, 0x91, 0x54, 0x25, 0x00, 0x00, 0x45}},
      {kMarriageCandidateIsAlliedRvaV1,
       {0x48, 0x89, 0x5C, 0x24, 0x10, 0x48, 0x89, 0x74,
        0x24, 0x18, 0x57, 0x48, 0x83, 0xEC, 0x20, 0x48}},
      {0x29615E0,
       {0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x6C,
        0x24, 0x10, 0x48, 0x89, 0x74, 0x24, 0x18, 0x57}},
  }};
  for (const auto &signature : signatures) {
    std::array<std::uint8_t, 16> actual{};
    if (!ReadMemory(env, env.module_base + signature.rva, actual.data(),
                    actual.size()) ||
        actual != signature.prefix)
      return Failure::signature_mismatch;
  }
  constexpr std::array<std::uintptr_t, 8> vtable_rvas{
      0xDB48D0, 0x7E9230, 0x7E6490, 0x7E9220,
      0x7E9240, 0x7E9240, 0x7E9230, 0x7E9230};
  std::array<std::uintptr_t, 8> actual_vtable{};
  if (!ReadMemory(env, env.native_owner_vtable, actual_vtable.data(),
                  sizeof(actual_vtable)))
    return Failure::signature_mismatch;
  for (std::size_t index = 0; index < actual_vtable.size(); ++index) {
    if (actual_vtable[index] != env.module_base + vtable_rvas[index])
      return Failure::signature_mismatch;
  }
  return Failure::none;
}

bool IsExpectedRole(std::uint32_t id, std::uint32_t actor,
                    std::uint32_t recipient, std::uint32_t heir,
                    std::uint32_t candidate) {
  return id == actor || id == recipient || id == heir || id == candidate;
}

} // namespace

MarriageCandidateAllianceProjectionEnvironmentV1
BindMarriageCandidateAllianceProjectionEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted,
    std::string_view admitted_executable_sha256) noexcept {
  MarriageCandidateAllianceProjectionEnvironmentV1 output{};
  output.module_base = module_base;
  output.exact_build_admitted = exact_build_admitted;
  output.admitted_executable_sha256 = admitted_executable_sha256;
  const bool bound =
      AddRva(module_base, kMarriageCandidateAlliancePairsRvaV1,
             output.project_pairs) &&
      AddRva(module_base, kMarriageCandidateReadOptionRvaV1,
             output.read_boolean_option) &&
      AddRva(module_base, kMarriageCandidateIsAlliedRvaV1,
             output.is_allied) &&
      AddRva(module_base, kMarriageCandidateMatrilinealOptionSlotRvaV1,
             output.matrilineal_option_id_slot) &&
      AddRva(module_base, kMarriageCandidateAllianceOwnerVtableRvaV1,
             output.native_owner_vtable);
  if (!bound) return {};
  return output;
}

MarriageCandidateAllianceProjectionFailureV1
ReadMarriageCandidateAllianceProjectionV1(
    const MarriageCandidateAllianceProjectionEnvironmentV1 &env,
    const void *finalized_context, std::uint32_t actor_character_id,
    std::uint32_t recipient_character_id, std::uint32_t heir_character_id,
    std::uint32_t candidate_character_id,
    MarriageCandidateAllianceProjectionV1 &output) noexcept {
  using Failure = MarriageCandidateAllianceProjectionFailureV1;
  output = {};
  const auto validation = Validate(env);
  if (validation != Failure::none) return validation;
  if (finalized_context == nullptr || actor_character_id == 0 ||
      recipient_character_id == 0 || heir_character_id == 0 ||
      candidate_character_id == 0 ||
      heir_character_id == candidate_character_id)
    return Failure::invalid_input;

  const auto context = reinterpret_cast<std::uintptr_t>(finalized_context);
  std::array<std::uint32_t, 4> actual_roles{};
  constexpr std::array<std::size_t, 4> role_offsets{
      kMarriageContextActorIdOffsetV1, kMarriageContextRecipientIdOffsetV1,
      kMarriageContextSecondaryActorIdOffsetV1,
      kMarriageContextSecondaryRecipientIdOffsetV1};
  for (std::size_t index = 0; index < role_offsets.size(); ++index) {
    if (!ReadAt(env, context, role_offsets[index], actual_roles[index]))
      return Failure::context_roles_mismatch;
  }
  const std::array<std::uint32_t, 4> expected_roles{
      actor_character_id, recipient_character_id, heir_character_id,
      candidate_character_id};
  if (actual_roles != expected_roles) return Failure::context_roles_mismatch;

  std::uint32_t lineality_option_id = 0;
  if (!ReadMemory(env, env.matrilineal_option_id_slot, &lineality_option_id,
                  sizeof(lineality_option_id)) ||
      lineality_option_id == 0)
    return Failure::option_id_unavailable;
  const bool selected = env.read_boolean_option(finalized_context,
                                                 lineality_option_id);

  NativePairVectorV1 vector{};
  std::memcpy(vector.inline_owner.data(), &env.native_owner_vtable,
              sizeof(env.native_owner_vtable));
  vector.data = vector.inline_owner.data() + 8;
  vector.capacity = 3;
  vector.owner = vector.inline_owner.data();
  // 0x29615E0 contains exactly three conditional row-append callsites. The
  // native inline owner therefore suffices and no heap lifecycle is entered.
  env.project_pairs(finalized_context, &vector);
  if (vector.count < 0 || vector.count > 3 || vector.capacity != 3 ||
      vector.owner != vector.inline_owner.data() ||
      vector.data != vector.inline_owner.data() + 8)
    return Failure::native_vector_invalid;

  MarriageCandidateAllianceProjectionV1 sample{};
  sample.matrilineal_option_selected = selected;
  sample.pair_count = static_cast<std::uint32_t>(vector.count);
  for (std::uint32_t index = 0; index < sample.pair_count; ++index) {
    NativePairRowV1 row{};
    std::memcpy(&row, vector.inline_owner.data() + 8 + index * sizeof(row),
                sizeof(row));
    std::uint32_t first_id = 0;
    std::uint32_t second_id = 0;
    std::uint32_t secondary_actor_id = 0;
    std::uint32_t secondary_recipient_id = 0;
    if (!ReadAt(env, row.first, kMarriageCharacterIdOffsetV1, first_id) ||
        !ReadAt(env, row.second, kMarriageCharacterIdOffsetV1, second_id) ||
        !ReadAt(env, row.secondary_actor, kMarriageCharacterIdOffsetV1,
                secondary_actor_id) ||
        !ReadAt(env, row.secondary_recipient,
                kMarriageCharacterIdOffsetV1, secondary_recipient_id) ||
        first_id == second_id ||
        !IsExpectedRole(first_id, actor_character_id, recipient_character_id,
                        heir_character_id, candidate_character_id) ||
        !IsExpectedRole(second_id, actor_character_id, recipient_character_id,
                        heir_character_id, candidate_character_id) ||
        secondary_actor_id != heir_character_id ||
        secondary_recipient_id != candidate_character_id)
      return Failure::row_identity_mismatch;
    std::uintptr_t first_realm = 0;
    std::uintptr_t second_realm = 0;
    if (!ReadAt(env, row.first, kMarriageCandidateRealmDataOffsetV1,
                first_realm) ||
        !ReadAt(env, row.second, kMarriageCandidateRealmDataOffsetV1,
                second_realm))
      return Failure::row_identity_mismatch;
    const bool allied = env.is_allied(reinterpret_cast<const void *>(row.first),
                                      reinterpret_cast<const void *>(row.second));
    auto &projected = sample.pairs[index];
    projected.first_character_id = first_id;
    projected.second_character_id = second_id;
    projected.already_allied = allied;
    projected.both_have_realm_data = first_realm != 0 && second_realm != 0;
    projected.would_attempt_if_accepted =
        !allied && projected.both_have_realm_data;
  }
  for (std::size_t index = 0; index < role_offsets.size(); ++index) {
    std::uint32_t after = 0;
    if (!ReadAt(env, context, role_offsets[index], after) ||
        after != expected_roles[index])
      return Failure::context_roles_mismatch;
  }
  output = sample;
  return Failure::none;
}

} // namespace xar::bridge
