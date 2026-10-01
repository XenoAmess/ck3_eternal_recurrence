#pragma once

#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_12002 {

inline constexpr std::uintptr_t kPrewarSubjectContractStorageSlotRva12002 =
    0x5D1EB88;
inline constexpr std::uintptr_t kPrewarSubjectContractFallbackSlotRva12002 =
    0x5D1EB40;
inline constexpr std::uintptr_t kPrewarSubjectContractDatabaseSlotRva12002 =
    0x5D1DED0;
inline constexpr std::size_t kPrewarCharacterLandOffset12002 = 0x1C0;
inline constexpr std::size_t kPrewarObligationDatabaseOffset12002 = 0xF00;
inline constexpr std::size_t kPrewarObligationDefaultLevelOffset12002 = 0x9F28;

struct PrewarParticipantsBindings12002 {
  bool enabled = false;
  void **character_storage_slot = nullptr;
  void **subject_contract_storage_slot = nullptr;
  void **subject_contract_fallback_slot = nullptr;
  void **subject_contract_database_slot = nullptr;
};

struct PrewarParticipantsAccess12002 {
  void *context = nullptr;
  bool (*read_memory)(void *context, const void *source, void *output,
                      std::size_t size) noexcept = nullptr;
};

struct ForcedPrewarParticipant12002 {
  std::int32_t character_id = -1;
  bool attacker_side = false;
  std::int32_t source_primary_character_id = -1;
  std::int32_t subject_contract_id = -1;
  std::uint32_t source_contract_native_order = 0;
  std::uint8_t active_level_index_raw = 0;
  std::uint8_t default_level_index_raw = 0;

  friend bool operator==(const ForcedPrewarParticipant12002 &,
                         const ForcedPrewarParticipant12002 &) = default;
};

struct ForcedPrewarParticipantsSnapshot12002 {
  bool available = false;
  bool complete_initial_participants_ready = false;
  std::int32_t primary_attacker_character_id = -1;
  std::int32_t primary_defender_character_id = -1;
  std::uint32_t attacker_source_contract_count = 0;
  std::uint32_t defender_source_contract_count = 0;
  std::vector<ForcedPrewarParticipant12002> forced_participants;
  // The native attacker round redirects these rows to a world-writing helper.
  // They must not appear in the passive forced-participant projection.
  std::vector<ForcedPrewarParticipant12002> excluded_primary_defender_collisions;

  friend bool operator==(const ForcedPrewarParticipantsSnapshot12002 &,
                         const ForcedPrewarParticipantsSnapshot12002 &) = default;
};

PrewarParticipantsBindings12002 BindPrewarParticipantsImage12002(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

// Called by the owning paused query context with already selected primaries.
// Resolves full IDs, reads two matching complete samples and mirrors the
// contract term predicate. It never constructs CWar or calls a native mutator.
bool ReadForcedPrewarParticipants12002(
    const PrewarParticipantsBindings12002 &bindings,
    const PrewarParticipantsAccess12002 &access,
    std::int32_t primary_attacker_character_id,
    std::int32_t primary_defender_character_id,
    ForcedPrewarParticipantsSnapshot12002 &output,
    std::string_view &failure);

std::string SerializeForcedPrewarParticipants12002(
    const ForcedPrewarParticipantsSnapshot12002 &snapshot);

} // namespace xar::ck3_12002
