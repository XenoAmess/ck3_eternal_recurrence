#pragma once
#include "xar_bridge/ck3_121003_living_inventory26785313_v1.hpp"
#include "xar_bridge/ck3_121003_gui_window26785313_v1.hpp"
#include <memory>
namespace xar::ck3_121003::build26785313 {
// Native-private only. No artifact ID, slot, pointer, key or ordinal is accepted
// from wire. A future independent owner must construct this actual frame.
struct LivingWeaponFrame267V1 {
 LivingInventoryFrame267V1 inventory;
 GuiWindowV1 gui;
 std::uintptr_t gfx=0,manager=0;
 bool owner_observed=false;
};
enum class LivingWeaponAction267V1 { select_weapon,equip_target,unequip_target };
enum class LivingWeaponCallStatus267V1 { refused,returned,indeterminate };
struct LivingWeaponCall267V1 {
 LivingWeaponCallStatus267V1 status=LivingWeaponCallStatus267V1::refused;
 bool entered=false,native_returned=false,native_handled=false,cleanup_known=true;
 // These callbacks queue commands or toggle selection. None proves settlement.
 bool applied=false;
};
class LivingWeaponPrivateSession267V1;
class LivingWeaponLease267V1 {
 public:LivingWeaponLease267V1()=default;
 private:struct State;std::shared_ptr<State>state_;
 friend class LivingWeaponPrivateSession267V1;
 friend bool PrepareLivingWeapon267V1(LivingWeaponPrivateSession267V1&,const ReadonlyBindings&,
  const LivingWeaponFrame267V1&,const LivingInventoryRequest267V1&,std::uint64_t,
  LivingWeaponAction267V1,LivingWeaponLease267V1&,std::string&)noexcept;
 friend LivingWeaponCall267V1 SubmitLivingWeapon267V1(LivingWeaponLease267V1&)noexcept;
};
class LivingWeaponPrivateSession267V1 {
 public:LivingWeaponPrivateSession267V1();~LivingWeaponPrivateSession267V1();
 LivingWeaponPrivateSession267V1(const LivingWeaponPrivateSession267V1&)=delete;
 LivingWeaponPrivateSession267V1&operator=(const LivingWeaponPrivateSession267V1&)=delete;
 private:struct State;std::shared_ptr<State>state_;
 friend struct LivingWeaponLease267V1::State;
 friend bool LivingWeaponSessionUnknown267V1(const LivingWeaponPrivateSession267V1&)noexcept;
 friend bool PrepareLivingWeapon267V1(LivingWeaponPrivateSession267V1&,const ReadonlyBindings&,
  const LivingWeaponFrame267V1&,const LivingInventoryRequest267V1&,std::uint64_t,
  LivingWeaponAction267V1,LivingWeaponLease267V1&,std::string&)noexcept;
 friend LivingWeaponCall267V1 SubmitLivingWeapon267V1(LivingWeaponLease267V1&)noexcept;
};
bool LivingWeaponSessionUnknown267V1(const LivingWeaponPrivateSession267V1&)noexcept;
bool PrepareLivingWeapon267V1(LivingWeaponPrivateSession267V1&,const ReadonlyBindings&,
 const LivingWeaponFrame267V1&,const LivingInventoryRequest267V1&,std::uint64_t,
 LivingWeaponAction267V1,LivingWeaponLease267V1&,std::string&)noexcept;
LivingWeaponCall267V1 SubmitLivingWeapon267V1(LivingWeaponLease267V1&)noexcept;
// Attachment SOURCE only: included in the existing current Readonly TU, under
// the independent Living owner slot. Not callable through RMTM/CCC authority.
bool ReadLivingWeaponFrameOnOwner267V1(const ReadonlyBindings&,
 ck3_11906::MainThreadQueryMailboxV1*,const ck3_11906::MainThreadQueryTicketV1&,
 const ck3_11906::MainThreadExecutionStampV1&,void*,const LivingInventoryQueryRequest267V1&,
 std::uint64_t,LivingWeaponFrame267V1&,std::string&)noexcept;
}
