#pragma once
#include "xar_bridge/army_county_primary_owner_at_writer_v1.hpp"
#include "xar_bridge/county_primary_owner_at_writer_12004.hpp"
#include <array>
#include <cstddef>

namespace xar::game {
struct ArmyActualLossWriterObservationV1;
struct ArmyCountyDirectPhysicalAssociationV2 {
  std::int32_t data_record_index=-1,persistent_regiment_id=-1,data_chunk_ordinal=-1;
  std::int32_t physical_slot_index=-1;
  std::uintptr_t persistent_registry_identity=0,selected_physical_identity=0,expected_physical_identity=0;
  std::optional<std::int32_t> physical_persistent_regiment_id,physical_own_ordinal,physical_army_regiment_id;
  bool registry_matches=false,physical_identity_matches=false;
};
struct ArmyCountyPrimaryDirectOwnerAtWriterV2 {
  std::uint64_t caller_return_rva=0,writer_invocation_token=0;
  std::uintptr_t writer_receiver_identity=0,source_carmy_identity=0,current_game_state_identity=0,public_unit_identity=0;
  std::uint32_t writer_thread_id=0;
  ArmyCountyWriterEventTokenV1 writer_event;
  std::optional<std::uint64_t> observed_date_raw64;
  bool natural_sampling_enabled=false,actual4_source_qualified=false;
  std::uint64_t natural_sampling_epoch=0;
  std::optional<std::int32_t> army_id,native_carmy_id,writer_full_regiment_id;
  std::uintptr_t native_army_registry_identity=0,public_unit_registry_identity=0,writer_registry_identity=0;
  std::optional<std::int32_t> army_roster_occurrence,army_roster_count;
  bool receiver_identity_matches=false,writer_identity_matches=false;
  bool native_army_registry_matches=false,public_unit_registry_matches=false,public_native_bidirectional_matches=false;
  bool writer_registry_matches=false,actual_array_contains_writer=false;
  bool physical_association_complete=false,physical_capture_complete=false;
  std::uint32_t captured_physical_association_count=0,capture_failure_flags=0;
  std::array<ArmyCountyDirectPhysicalAssociationV2,64> physical_associations{};
  bool active_phase_observed=false;
  std::uint32_t active_phase_kind=0;
  std::uintptr_t active_phase_entry_rva=0;
  bool source_complete=false;
};
const char *CountyPrimaryDirectCaptureSkipReasonV2(std::uint32_t) noexcept;
void AppendArmyCountyPrimaryDirectOwnerAtWriterV2(std::string &,
    const ArmyCountyPrimaryDirectOwnerAtWriterV2 &);
} // namespace xar::game

namespace xar::ck3_12004 {
enum class CountyDirectRegistryKind12004 { army,unit,army_regiment,persistent_regiment };
using CountyDirectRegistryLookup12004=const void *(*)(void *,CountyDirectRegistryKind12004,std::int32_t) noexcept;
struct CountyDirectPhysicalInputs12004 {
  std::array<const void *,64> selected_slots{};
};
enum CountyDirectFailure12004 : std::uint32_t {
  county_direct_registers_missing=1U,
  county_direct_register_argument=2U,
  county_direct_writer_event=4U,
  county_direct_game_state_date=8U,
  county_direct_army_identity=16U,
  county_direct_army_registry=32U,
  county_direct_unit_registry=64U,
  county_direct_bidirectional=128U,
  county_direct_writer_identity=256U,
  county_direct_writer_registry=512U,
  county_direct_roster_read=1024U,
  county_direct_roster_membership=2048U,
  county_direct_physical_association=4096U,
  county_direct_physical_post=8192U,
  county_direct_sampling_changed=16384U,
  county_direct_source_unqualified=32768U
};
// Always called only for exact natural CALL return and actual sampling ON.
// No phase kind is a qualification gate. Lookup must use the existing strict
// registry reader; it must never call a getter, a writer or a query snapshot.
game::ArmyCountyPrimaryDirectOwnerAtWriterV2 CaptureCountyPrimaryDirectOwnerAtWriter12004(
    CountyPrimaryOwnerRead12004,void *,CountyDirectRegistryLookup12004,void *,
    const CountyPrimaryWriterRegisters12004 *,const CountyPrimaryPhaseCapture12004 &,
    const game::ArmyActualLossWriterObservationV1 &,const CountyDirectPhysicalInputs12004 &,
    const void *actual_receiver,std::uint32_t actual_tid,std::uintptr_t current_state,
    bool source_qualified) noexcept;
void FinishCountyPrimaryDirectOwnerAtWriter12004(
    game::ArmyCountyPrimaryDirectOwnerAtWriterV2 &,
    const game::ArmyActualLossWriterObservationV1 &,
    const ArmyObserverResearchSamplingState12004 &) noexcept;
} // namespace xar::ck3_12004
