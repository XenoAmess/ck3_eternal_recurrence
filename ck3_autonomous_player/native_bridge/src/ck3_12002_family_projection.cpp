#include "xar_bridge/ck3_12002_family_projection.hpp"

#include "xar_bridge/ck3_12002.hpp"
#include "xar_bridge/ck3_12002_family_query_abi.hpp"

#include <cstring>
#include <limits>

namespace xar::ck3_12002 {
namespace {
using Failure = bridge::MarriageCandidateAllianceProjectionFailureV1;

struct NativePairVector {
  void *data = nullptr;
  std::int32_t capacity = 0;
  std::int32_t count = 0;
  void *owner = nullptr;
  alignas(8) std::array<std::byte, 8 + 3 * 0x20> inline_owner{};
};
static_assert(offsetof(NativePairVector, owner) == 0x10);
static_assert(offsetof(NativePairVector, inline_owner) == 0x18);
struct NativePairRow {
  std::uintptr_t first = 0;
  std::uintptr_t second = 0;
  std::uintptr_t secondary_actor = 0;
  std::uintptr_t secondary_recipient = 0;
};
static_assert(sizeof(NativePairRow) == 0x20);

bool LocalRead(void *, std::uintptr_t address, void *out,
               std::size_t size) noexcept {
  if (address == 0 || out == nullptr) return false;
  std::memcpy(out, reinterpret_cast<const void *>(address), size);
  return true;
}
template <typename T>
bool Read(const FamilyProjectionBindings &b, std::uintptr_t base,
          std::size_t offset, T &out) noexcept {
  return b.read_memory != nullptr && base != 0 &&
      offset <= (std::numeric_limits<std::uintptr_t>::max)() - base &&
      b.read_memory(b.memory_context, base + offset, &out, sizeof(out));
}
constexpr std::array<std::size_t, 4> kRoleOffsets{
    family_query_abi::kContextActorIdOffset,
    family_query_abi::kContextRecipientIdOffset,
    family_query_abi::kContextSecondaryActorIdOffset,
    family_query_abi::kContextSecondaryRecipientIdOffset};

Failure Validate(const FamilyProjectionBindings &b) noexcept {
  if (!b.exact_build_admitted ||
      b.admitted_executable_sha256 != kExecutableSha256 ||
      (!b.offline_fixture && b.module_base == 0))
    return Failure::exact_build_not_admitted;
  if (b.read_memory == nullptr || b.project_pairs == nullptr ||
      b.read_boolean_option == nullptr || b.is_allied == nullptr ||
      b.matrilineal_option_id_slot == 0 || b.native_owner_vtable == 0)
    return Failure::binding_unavailable;
  if (b.offline_fixture) return Failure::none;
  if (reinterpret_cast<std::uintptr_t>(b.project_pairs) !=
          b.module_base + kFamilyProjectionPairWrapperRva ||
      reinterpret_cast<std::uintptr_t>(b.read_boolean_option) !=
          b.module_base + kFamilyProjectionReadOptionRva ||
      reinterpret_cast<std::uintptr_t>(b.is_allied) !=
          b.module_base + kFamilyProjectionIsAlliedRva ||
      b.matrilineal_option_id_slot !=
          b.module_base + kFamilyProjectionMatrilinealSlotRva ||
      b.native_owner_vtable != b.module_base + kFamilyProjectionOwnerVtableRva)
    return Failure::binding_unavailable;
  struct Signature {
    std::uintptr_t rva;
    std::array<std::uint8_t, 16> bytes;
  };
  constexpr std::array<Signature, 4> signatures{{
      {kFamilyProjectionPairWrapperRva,
       {0x40, 0x55, 0x48, 0x83, 0xEC, 0x30, 0x4C, 0x8B,
        0x05, 0xEB, 0x1F, 0x76, 0x03, 0x48, 0x8B, 0xEA}},
      {kFamilyProjectionReadOptionRva,
       {0x4C, 0x8B, 0x09, 0x33, 0xC0, 0x4C, 0x8B, 0xD9,
        0x45, 0x8B, 0x91, 0x64, 0x22, 0x00, 0x00, 0x45}},
      {kFamilyProjectionIsAlliedRva,
       {0x48, 0x89, 0x5C, 0x24, 0x10, 0x48, 0x89, 0x74,
        0x24, 0x18, 0x57, 0x48, 0x83, 0xEC, 0x20, 0x48}},
      {kFamilyProjectionPairGeneratorRva,
       {0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x6C,
        0x24, 0x10, 0x48, 0x89, 0x74, 0x24, 0x18, 0x57}},
  }};
  for (const auto &signature : signatures) {
    std::array<std::uint8_t, 16> actual{};
    if (!b.read_memory(b.memory_context, b.module_base + signature.rva,
                       actual.data(), actual.size()) || actual != signature.bytes)
      return Failure::signature_mismatch;
  }
  // This owner initializes precisely three 0x20-byte inline rows at owner+8.
  constexpr std::array<std::uintptr_t, 8> vtable{
      0xE56110, 0x855AB0, 0x8522C0, 0x855AA0,
      0x855AC0, 0x855AC0, 0x855AB0, 0x855AB0};
  std::array<std::uintptr_t, 8> actual{};
  if (!b.read_memory(b.memory_context, b.native_owner_vtable, actual.data(),
                     sizeof(actual))) return Failure::signature_mismatch;
  for (std::size_t i = 0; i < actual.size(); ++i)
    if (actual[i] != b.module_base + vtable[i]) return Failure::signature_mismatch;
  return Failure::none;
}

bool RolesMatch(const FamilyProjectionBindings &b, std::uintptr_t context,
                const std::array<std::uint32_t, 4> &expected) noexcept {
  for (std::size_t i = 0; i < expected.size(); ++i) {
    std::uint32_t actual = 0;
    if (!Read(b, context, kRoleOffsets[i], actual) || actual != expected[i])
      return false;
  }
  return true;
}
bool ExpectedRole(std::uint32_t id,
                  const std::array<std::uint32_t, 4> &roles) noexcept {
  for (const auto role : roles) if (id == role) return true;
  return false;
}
} // namespace

FamilyProjectionBindings BindFamilyProjectionImage(
    std::uintptr_t module_base,
    std::string_view executable_sha256) noexcept {
  FamilyProjectionBindings b{};
  if (module_base == 0 || executable_sha256 != kExecutableSha256 ||
      kFamilyProjectionMatrilinealSlotRva >
          (std::numeric_limits<std::uintptr_t>::max)() - module_base) return b;
  b.module_base = module_base;
  b.exact_build_admitted = true;
  b.admitted_executable_sha256 = executable_sha256;
  b.read_memory = &LocalRead;
  b.project_pairs = reinterpret_cast<bridge::ProjectMarriageCandidateAlliancePairsV1>(
      module_base + kFamilyProjectionPairWrapperRva);
  b.read_boolean_option = reinterpret_cast<bridge::ReadMarriageCandidateBooleanOptionV1>(
      module_base + kFamilyProjectionReadOptionRva);
  b.set_boolean_option = reinterpret_cast<bridge::SetMarriageCandidateBooleanOptionV1>(
      module_base + kFamilyProjectionSetOptionRva);
  b.is_allied = reinterpret_cast<bridge::ReadMarriageCandidateIsAlliedV1>(
      module_base + kFamilyProjectionIsAlliedRva);
  b.matrilineal_option_id_slot = module_base + kFamilyProjectionMatrilinealSlotRva;
  b.native_owner_vtable = module_base + kFamilyProjectionOwnerVtableRva;
  return b;
}

bool SelectFamilyMatrilinealOptionV1(
    const FamilyProjectionBindings &b, void *context) noexcept {
  if (Validate(b) != Failure::none || context == nullptr ||
      b.set_boolean_option == nullptr) return false;
  if (!b.offline_fixture) {
    if (reinterpret_cast<std::uintptr_t>(b.set_boolean_option) !=
        b.module_base + kFamilyProjectionSetOptionRva) return false;
    constexpr std::array<std::uint8_t, 16> wanted{
        0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x74,
        0x24, 0x10, 0x57, 0x48, 0x83, 0xEC, 0x20, 0x4C};
    std::array<std::uint8_t, 16> actual{};
    if (!b.read_memory(b.memory_context, b.module_base + kFamilyProjectionSetOptionRva,
                       actual.data(), actual.size()) || actual != wanted) return false;
  }
  std::uint32_t option_id = 0;
  if (!Read(b, b.matrilineal_option_id_slot, 0, option_id) || option_id == 0)
    return false;
  if (b.read_boolean_option(context, option_id)) return true;
  b.set_boolean_option(context, option_id, true);
  return b.read_boolean_option(context, option_id);
}

Failure ReadFamilyAllianceProjectionV1(
    const FamilyProjectionBindings &b, const void *finalized_context,
    std::uint32_t actor, std::uint32_t recipient, std::uint32_t subject,
    std::uint32_t candidate,
    bridge::MarriageCandidateAllianceProjectionV1 &output) noexcept {
  output = {};
  const auto validation = Validate(b);
  if (validation != Failure::none) return validation;
  if (finalized_context == nullptr || actor == 0 || recipient == 0 ||
      subject == 0 || candidate == 0 || subject == candidate)
    return Failure::invalid_input;
  const auto context = reinterpret_cast<std::uintptr_t>(finalized_context);
  const std::array<std::uint32_t, 4> roles{actor, recipient, subject, candidate};
  if (!RolesMatch(b, context, roles)) return Failure::context_roles_mismatch;
  std::uint32_t option_id = 0;
  if (!Read(b, b.matrilineal_option_id_slot, 0, option_id) || option_id == 0)
    return Failure::option_id_unavailable;

  NativePairVector vector{};
  std::memcpy(vector.inline_owner.data(), &b.native_owner_vtable,
              sizeof(b.native_owner_vtable));
  vector.data = vector.inline_owner.data() + 8;
  vector.capacity = 3;
  vector.owner = vector.inline_owner.data();
  b.project_pairs(finalized_context, &vector);
  // The frozen generator has exactly three conditional append call sites.
  if (vector.count < 0 || vector.count > 3 || vector.capacity != 3 ||
      vector.owner != vector.inline_owner.data() ||
      vector.data != vector.inline_owner.data() + 8)
    return Failure::native_vector_invalid;
  bridge::MarriageCandidateAllianceProjectionV1 sample{};
  sample.matrilineal_option_selected = b.read_boolean_option(finalized_context, option_id);
  sample.pair_count = static_cast<std::uint32_t>(vector.count);
  for (std::uint32_t i = 0; i < sample.pair_count; ++i) {
    NativePairRow row{};
    std::memcpy(&row, vector.inline_owner.data() + 8 + i * sizeof(row), sizeof(row));
    std::array<std::uint32_t, 4> ids{};
    if (!Read(b, row.first, 0x18, ids[0]) ||
        !Read(b, row.second, 0x18, ids[1]) ||
        !Read(b, row.secondary_actor, 0x18, ids[2]) ||
        !Read(b, row.secondary_recipient, 0x18, ids[3]) ||
        ids[0] == ids[1] || !ExpectedRole(ids[0], roles) ||
        !ExpectedRole(ids[1], roles) || ids[2] != subject || ids[3] != candidate)
      return Failure::row_identity_mismatch;
    std::uintptr_t first_realm = 0, second_realm = 0;
    if (!Read(b, row.first, kFamilyProjectionRealmDataOffset, first_realm) ||
        !Read(b, row.second, kFamilyProjectionRealmDataOffset, second_realm))
      return Failure::row_identity_mismatch;
    auto &pair = sample.pairs[i];
    pair.first_character_id = ids[0];
    pair.second_character_id = ids[1];
    pair.already_allied = b.is_allied(reinterpret_cast<const void *>(row.first),
                                     reinterpret_cast<const void *>(row.second));
    pair.both_have_realm_data = first_realm != 0 && second_realm != 0;
    // Existing wire criterion: the native player-facing branch at
    // 0x250441F..0x2504442. Its false branches still enter the relation effect;
    // this field does not assert final alliance creation legality or success.
    pair.would_attempt_if_accepted = !pair.already_allied && pair.both_have_realm_data;
  }
  if (!RolesMatch(b, context, roles)) return Failure::context_roles_mismatch;
  output = sample;
  return Failure::none;
}
} // namespace xar::ck3_12002
