#pragma once

#include "xar_bridge/ck3_12002.hpp"

#include <optional>
#include <string>

namespace xar::ck3_12002::religion::clergy {

inline constexpr std::uintptr_t kValidPositionRva = 0x31BCED0;
inline constexpr std::uintptr_t kValidCharacterRva = 0x31BCF90;
inline constexpr std::uintptr_t kCanReassignRva = 0x31B4980;
inline constexpr std::uintptr_t kCanFireRva = 0x2C477E0;
inline constexpr std::uintptr_t kCourtOwnerRva = 0x28BFC70;
inline constexpr std::uintptr_t kTaskStorageRva = 0x5D1DEA0;
inline constexpr std::size_t kLandedOffset = 0x1C0;
inline constexpr std::size_t kTaskIdsOffset = 0x230;
inline constexpr std::size_t kTaskCountOffset = 0x23C;
inline constexpr std::size_t kTaskIdentityOffset = 0x10;
inline constexpr std::size_t kTaskTypeOffset = 0x18;
inline constexpr std::size_t kTaskOwnerOffset = 0x44;
inline constexpr std::size_t kTaskIncumbentOffset = 0x40;
inline constexpr std::size_t kTypePositionOffset = 0x40;
inline constexpr std::size_t kPositionKeyOffset = 0x18;
inline constexpr std::size_t kCharacterRiteOffset = 0xB4;
inline constexpr std::string_view kPositionKey = "councillor_court_chaplain";

using PositionPredicate = bool (*)(void *, std::int32_t);
using TaskPredicate = bool (*)(void *, void *);
using CanFirePredicate = bool (*)(void *, void *, void *, std::uint32_t, void *);
using CourtOwnerGetter = void *(*)(void *);
using ReadMemory = bool (*)(void *, const void *, void *, std::size_t) noexcept;

struct Bindings {
  bool enabled = false;
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;
  std::string_view executable_sha256{};
  CoreBindings core{};
  std::uint32_t application_main_thread_id = 0;
  void **task_storage_slot = nullptr;
  PositionPredicate valid_position = nullptr;
  PositionPredicate valid_character = nullptr;
  TaskPredicate can_reassign = nullptr;
  CanFirePredicate can_fire = nullptr;
  CourtOwnerGetter court_owner = nullptr;
  void *read_context = nullptr;
  ReadMemory read_memory = nullptr;
};

enum class Failure {
  none,
  bindings_unavailable,
  owner_thread_required,
  frame_unavailable,
  not_paused,
  player_unavailable,
  candidate_unavailable,
  task_unavailable,
  candidate_context_unavailable,
  native_predicate_unavailable,
  state_changed,
};

struct Observation {
  bool available = false;
  Failure failure = Failure::bindings_unavailable;
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::int32_t owner_character_id = -1;
  std::int32_t candidate_character_id = -1;
  bool position_present = false;
  std::optional<std::int32_t> active_task_id;
  std::optional<std::int32_t> incumbent_character_id;
  std::optional<std::int32_t> candidate_court_owner_id;
  std::optional<std::uint32_t> owner_rite_id;
  std::optional<std::uint32_t> candidate_rite_id;
  bool candidate_is_incumbent = false;
  std::optional<bool> candidate_matches_owner_context;
  std::optional<bool> native_valid_position;
  std::optional<bool> native_valid_character;
  std::optional<bool> native_can_reassign;
  std::optional<bool> native_can_fire;
};

Bindings BindClergyAppointmentImage12002(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

// Existing application-main owner only. The specified candidate is a real full
// CharacterID, never an empty/default candidate. Queries return independent
// final predicates; they do not advertise a submit action or infer its result.
bool ReadClergyAppointment12002(const Bindings &bindings,
                              std::uint64_t capture_epoch,
                              std::int32_t candidate_character_id,
                              Observation &output) noexcept;
std::string SerializeClergyAppointment12002(const Observation &value);
const char *ClergyAppointmentFailureKey(Failure value) noexcept;

} // namespace xar::ck3_12002::religion::clergy
