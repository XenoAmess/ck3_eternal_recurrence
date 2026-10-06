#pragma once

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/religion_rite_governance12002_clergy.hpp"

namespace xar::ck3_12004::religion::clergy {

inline constexpr std::string_view kPositionKey = "councillor_court_chaplain";

// CLERGY-BASE-FUNCTION-MAP.json: complete actual .3/.4 native body pairs.
inline constexpr std::uintptr_t kValidPositionRva = 0x31BCEB0;
inline constexpr std::uintptr_t kValidCharacterRva = 0x31BCF70;
inline constexpr std::uintptr_t kCanReassignRva = 0x31B4960;
inline constexpr std::uintptr_t kCanFireRva = 0x2C477C0;
// Existing Faction immediate_liege complete118-byte pair; old clergy ABI
// provides the CourtOwner typed meaning. Landed characters return themselves.
inline constexpr std::uintptr_t kCourtOwnerRva = 0x28BFC50;
// Shared actual .4 Council SOURCE-PROOF, including native lookup/table and
// current-owner full task membership. No raw Position key field is consumed.
inline constexpr std::uintptr_t kPositionLookupRva = 0x2684EE0;
inline constexpr std::uintptr_t kTaskStorageRva = 0x5D1DEA0;
inline constexpr std::size_t kLandedOffset = 0x1C0;
inline constexpr std::size_t kTaskIdsOffset = 0x230;
inline constexpr std::size_t kTaskCountOffset = 0x23C;
inline constexpr std::size_t kTaskIdentityOffset = 0x10;
inline constexpr std::size_t kTaskTypeOffset = 0x18;
inline constexpr std::size_t kTaskOwnerOffset = 0x44;
inline constexpr std::size_t kTaskIncumbentOffset = 0x40;
inline constexpr std::size_t kTypePositionOffset = 0x40;
inline constexpr std::size_t kTaskStorageSlotsOffset = 0x20;
inline constexpr std::size_t kTaskStorageCapacityOffset = 0x2C;
inline constexpr std::size_t kTaskStorageSlotStride = 0x10;
inline constexpr std::size_t kTaskStorageObjectOffset = 0x08;
// Faith actor-map/SOURCE-READY.json, CharacterRite actual operand at offset12.
inline constexpr std::size_t kCharacterRiteOffset = 0xB4;

// Reuse software result DTOs and function signatures only. Native image
// bindings and all Core calls belong to the actual 1.20.0.4 implementation.
using Observation = ck3_12002::religion::clergy::Observation;
using Failure = ck3_12002::religion::clergy::Failure;
using CurrentClergySeat = ck3_12002::religion::clergy::CurrentClergySeat;
using PositionPredicate = ck3_12002::religion::clergy::PositionPredicate;
using TaskPredicate = ck3_12002::religion::clergy::TaskPredicate;
using CanFirePredicate = ck3_12002::religion::clergy::CanFirePredicate;
using CourtOwnerGetter = ck3_12002::religion::clergy::CourtOwnerGetter;
using ReadMemory = ck3_12002::religion::clergy::ReadMemory;
using PositionLookup = const void *(*)(const void *, const std::string *);

struct Bindings {
  bool enabled = false;
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;
  std::string_view executable_sha256{};
  ck3_12004::CoreBindings core{};
  std::uint32_t application_main_thread_id = 0;
  void **task_storage_slot = nullptr;
  PositionPredicate valid_position = nullptr;
  PositionPredicate valid_character = nullptr;
  TaskPredicate can_reassign = nullptr;
  CanFirePredicate can_fire = nullptr;
  CourtOwnerGetter court_owner = nullptr;
  PositionLookup position_lookup = nullptr;
  void *read_context = nullptr;
  ReadMemory read_memory = nullptr;
};

// Pure actual-build binding. No legacy hash admission or old native reader
// dispatch is used by these entry points.
Bindings BindClergyAppointmentImage12004(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

// The caller owns the existing application-main paused transaction. Result
// identity, false/null and failure semantics remain the existing clergy DTO.
bool ReadClergyAppointment12004(const Bindings &bindings,
    std::uint64_t capture_epoch, std::int32_t candidate_character_id,
    Observation &output) noexcept;
bool ResolveCurrentClergySeat12004(const Bindings &bindings,
    std::int32_t owner_character_id, CurrentClergySeat &output) noexcept;
std::string SerializeClergyAppointment12004(const Observation &value);

} // namespace xar::ck3_12004::religion::clergy
