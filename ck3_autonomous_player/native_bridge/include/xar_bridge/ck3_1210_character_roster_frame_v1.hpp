#pragma once
#include "xar_bridge/ck3_1210_character_manager_candidate_data_v1.hpp"
#include "xar_bridge/ck3_1210_personal_gold_frame_v1.hpp"
namespace xar::ck3_1210 {
inline constexpr char kCharacterRosterStepV1[] = "query-character-manager-roster-v1";
inline constexpr char kCharacterRosterCapabilityV1[] = "game.query.character-manager-roster.v1";
inline constexpr char kCharacterRosterSchemaV1[] = "ck3_1210_character_roster_readonly_v1";
struct CharacterRosterSourceProofV1 {
  bool custody_available = false;
  bool offline_fixture = false;
  std::uint64_t native_revision = 0, connection_generation = 0, mailbox_sequence = 0, pump_epoch = 0;
  std::uint32_t owner_thread_id = 0;
  std::int32_t date_raw = 0, played_character_id = -1;
};
struct CharacterRosterMailboxContextV1 {
  CharacterManagerBindingsV1 bindings{};
  CoreSnapshotPrefix expected{};
  std::uint64_t expected_native_revision = 0, expected_connection_generation = 0;
  // Internal WorkerState borrows. Kept alive until actual ticket reclamation;
  // never set from wire pointers and never retained after this query.
  const std::uint64_t *current_native_revision = nullptr;
  const std::uint64_t *current_connection_generation = nullptr;
  CharacterManagerObservationV1 observation{};
  CharacterRosterSourceProofV1 source{};
  bool application_main_observed = false;
  CharacterManagerReadAccessV1 fixture_access{};
};
void ClearCharacterRosterV1(CharacterRosterMailboxContextV1 &, std::string_view reason) noexcept;
bool ExecuteCharacterRosterOnActorOwnerV1(PersonalGoldMailboxContextV1 &,
    const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
// Owned envelope around unchanged candidate DATA. Source proof is optional;
// no model-source, Family join, living-universe or action authority is created.
std::string SerializeCharacterRosterResultV1(const CharacterRosterMailboxContextV1 &);
std::string SerializeCharacterRosterCommandResultV1(std::string_view request_id,
    const CharacterRosterMailboxContextV1 &);
} // namespace xar::ck3_1210
