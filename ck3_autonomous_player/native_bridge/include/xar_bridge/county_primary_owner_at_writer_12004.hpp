#pragma once
#include "xar_bridge/army_county_primary_owner_at_writer_v1.hpp"
#include "xar_bridge/army_natural_phase_scope_12004.hpp"
#include <cstddef>
#include <cstdint>
#include <optional>
namespace xar::ck3_12004 {
struct CountyPrimaryWriterRegisters12004 {
  const void *writer_receiver=nullptr,*source_carmy_r13=nullptr;
  std::uint64_t caller_return_rva=0,writer_invocation_token=0;
  std::uint32_t native_thread_id=0;
};
struct CountyPrimaryPhaseCapture12004 {
  ArmyNaturalPhaseScope12004 scope;
  ArmyNaturalPhaseEvent12004 writer_event;
};
using CountyPrimaryPhaseReader12004=CountyPrimaryPhaseCapture12004(*)() noexcept;
using CountyPrimaryOwnerRead12004=bool(*)(void*,const void*,void*,std::size_t) noexcept;
std::optional<game::ArmyCountyPrimaryOwnerAtWriterV1> CaptureCountyPrimaryOwnerAtWriter12004(
    CountyPrimaryOwnerRead12004,void*,const CountyPrimaryWriterRegisters12004 &,
    const CountyPrimaryPhaseCapture12004 &,std::int32_t writer_full_id,
    std::optional<std::int32_t> writer_date,std::uintptr_t current_game_state) noexcept;
} // namespace xar::ck3_12004
