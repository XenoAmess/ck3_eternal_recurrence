#pragma once

#include "xar_bridge/marriage_matchmaking_source_adapter_v1.hpp"

#include <array>
#include <cstdint>
#include <string_view>

namespace xar::bridge {

// Private, read-only exact-build primitive. It consumes an already finalized
// arrange-marriage context on the paused application-main thread; it does not
// construct a context, submit an interaction, or advertise a capability.
inline constexpr std::string_view kMarriageCandidateAllianceProjectionKeyV1 =
    "marriage_candidate_alliance_projection_v1";
inline constexpr std::uintptr_t kMarriageCandidateAlliancePairsRvaV1 =
    0x22846B0;
inline constexpr std::uintptr_t kMarriageCandidateAllianceOwnerVtableRvaV1 =
    0x413C270;
inline constexpr std::uintptr_t kMarriageCandidateMatrilinealOptionSlotRvaV1 =
    0x57EB680;
inline constexpr std::uintptr_t kMarriageCandidateReadOptionRvaV1 =
    0x2C40770;
inline constexpr std::uintptr_t kMarriageCandidateIsAlliedRvaV1 =
    0x2661E00;
inline constexpr std::size_t kMarriageCandidateRealmDataOffsetV1 = 0x1B8;
inline constexpr std::uint32_t kMarriageCandidateMaximumAlliancePairsV1 = 3;

using ProjectMarriageCandidateAlliancePairsV1 =
    void (*)(const void *finalized_context, void *native_vector);
using ReadMarriageCandidateBooleanOptionV1 =
    bool (*)(const void *finalized_context, std::uint32_t option_id);
using ReadMarriageCandidateIsAlliedV1 =
    bool (*)(const void *first_character, const void *second_character);

enum class MarriageCandidateAllianceProjectionFailureV1 : std::uint32_t {
  none = 0,
  exact_build_not_admitted,
  binding_unavailable,
  signature_mismatch,
  invalid_input,
  context_roles_mismatch,
  option_id_unavailable,
  native_vector_invalid,
  row_identity_mismatch,
};

struct MarriageCandidateAlliancePairV1 {
  std::uint32_t first_character_id = 0;
  std::uint32_t second_character_id = 0;
  bool already_allied = false;
  bool both_have_realm_data = false;
  // Mirrors only the pre-create guards at 0x2283589..0x22835B8.
  // Recipient response and later world effects remain separate unknowns.
  bool would_attempt_if_accepted = false;

  friend bool operator==(const MarriageCandidateAlliancePairV1 &,
                         const MarriageCandidateAlliancePairV1 &) = default;
};

struct MarriageCandidateAllianceProjectionV1 {
  bool matrilineal_option_selected = false;
  std::uint32_t pair_count = 0;
  std::array<MarriageCandidateAlliancePairV1,
             kMarriageCandidateMaximumAlliancePairsV1>
      pairs{};
};

struct MarriageCandidateAllianceProjectionEnvironmentV1 {
  std::uintptr_t module_base = 0;
  bool exact_build_admitted = false;
  std::string_view admitted_executable_sha256{};
  bool offline_fixture = false;
  void *memory_context = nullptr;
  MarriageSourceAdapterMemoryReadV1 read_memory = nullptr;
  ProjectMarriageCandidateAlliancePairsV1 project_pairs = nullptr;
  ReadMarriageCandidateBooleanOptionV1 read_boolean_option = nullptr;
  ReadMarriageCandidateIsAlliedV1 is_allied = nullptr;
  std::uintptr_t matrilineal_option_id_slot = 0;
  std::uintptr_t native_owner_vtable = 0;
};

MarriageCandidateAllianceProjectionEnvironmentV1
BindMarriageCandidateAllianceProjectionEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted,
    std::string_view admitted_executable_sha256) noexcept;

// The caller must have observed native final legality for this exact
// actor/heir/candidate and must bind the result to its paused revision.
MarriageCandidateAllianceProjectionFailureV1
ReadMarriageCandidateAllianceProjectionV1(
    const MarriageCandidateAllianceProjectionEnvironmentV1 &environment,
    const void *finalized_context, std::uint32_t actor_character_id,
    std::uint32_t recipient_character_id, std::uint32_t heir_character_id,
    std::uint32_t candidate_character_id,
    MarriageCandidateAllianceProjectionV1 &output) noexcept;

} // namespace xar::bridge
