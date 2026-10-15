#pragma once
#include "xar_bridge/war_payment_runtime_12004.hpp"
#include <mutex>

namespace xar::ck3_12004 {
struct WarPaymentCurrentFrame12004 {
  std::uint64_t connection_generation=0,snapshot_revision=0,native_date_raw=0;
  std::uint32_t player_character_full_id=0;
  bool paused=false,map_ready=false,alive=false;
};
struct WarPaymentWindow12004 {
  std::mutex mutex;
  std::uintptr_t module_base=0;
  ArmyNaturalPhaseRead12004 read=nullptr;
  void *read_context=nullptr;
  WarPaymentJournal12004 *journal=nullptr;
  WarPaymentSession12004 session;
  std::string machine_id;
  std::string reason="not_enabled";
  bool admitted=false;
};
struct WarPaymentWindowControl12004 {
  bool accepted=false;
  std::string requested,reason;
};
void ConfigureWarPaymentWindow12004(WarPaymentWindow12004 &,std::uintptr_t,
  ArmyNaturalPhaseRead12004,void *,WarPaymentJournal12004 &) noexcept;
WarPaymentWindowControl12004 ControlWarPaymentWindow12004(WarPaymentWindow12004 &,
  std::string_view mode,std::string_view no_load_contract,std::string_view machine_id,
  const WarPaymentCurrentFrame12004 &) noexcept;
void ObserveWarPaymentWindowFrame12004(WarPaymentWindow12004 &,
  const WarPaymentCurrentFrame12004 &) noexcept;
void InvalidateWarPaymentWindow12004(WarPaymentWindow12004 &,std::string_view reason) noexcept;
// A full worker snapshot may be unavailable while its owner cache is being
// refreshed. This callback reads only a new exact-build identity/clock prefix;
// it must never return a previous full snapshot or publish a partial one.
using WarPaymentIdentityFrameReader12004 = bool (*)(void *,WarPaymentCurrentFrame12004 &) noexcept;
bool RefreshWarPaymentIdentityAfterSnapshotUnavailable12004(WarPaymentWindow12004 &,
  WarPaymentIdentityFrameReader12004,void *) noexcept;

WarPaymentSession12004 ReadWarPaymentWindowSession12004(void *) noexcept;
bool RetainWarPaymentWindowActor12004(void *,WarPaymentKind12004,
  std::uintptr_t receiver,std::uintptr_t second_pointer) noexcept;
WarPaymentEnvelope12004 ReadWarPaymentWindowEnvelope12004(WarPaymentWindow12004 &,
  const WarPaymentDetourState12004 &);
std::string SerializeWarPaymentWindowControl12004(const WarPaymentWindowControl12004 &);
} // namespace xar::ck3_12004
