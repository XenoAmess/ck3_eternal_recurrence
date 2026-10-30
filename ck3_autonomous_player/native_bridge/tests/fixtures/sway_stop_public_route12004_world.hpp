#pragma once
// Owned software native memory, frame and queue support; no Game process.
#include "xar_bridge/ck3_12004_sway_terminal.hpp"
#include "xar_bridge/ck3_12004_sway.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12002_sway_completion_termination_mailbox.hpp"
#include "xar_bridge/ck3_12002_semantic_adapter.hpp"
#include "xar_bridge/sway_completion_causal_observer_12004.hpp"
#include "xar_bridge/sway_child_end_causal_path_12004.hpp"
#include <array>
#include <atomic>
#include <bit>
#include <chrono>
#include <cstring>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <thread>
#include <vector>
#include <windows.h>

namespace xar::ck3_12004 {
ck3_12002::SwayCompletionBindings12002 RealBindSwayTerminalImage12004(std::uintptr_t,std::string_view) noexcept;
}
namespace {
namespace native=xar::ck3_12002;
namespace actual4=xar::ck3_12004;
namespace api=xar::ck3_11906;
int checks=0,failures=0,abort_calls=0,bind_calls=0;
[[noreturn]] void NotExercised() noexcept {++abort_calls;std::abort();}
void Check(bool value,const char *what){++checks;if(!value){++failures;std::cerr<<"FAIL "<<what<<'\n';}}
template<class T>void Put(void *p,std::size_t offset,T value){std::memcpy(static_cast<std::byte *>(p)+offset,&value,sizeof(value));}
class FrameAdapter final : public xar::game::GameAdapter {
public:
  xar::game::Snapshot frame{};
  const DWORD owner = GetCurrentThreadId();
  mutable unsigned reads = 0;
  bool drift = false;
  xar::game::AdapterDescriptor identity{"ck3-1.20.0.4-msvc-x64", "1.20.0.4",
      actual4::kExecutableSha256, "epidemic-treatment-fixture", {}};
  const xar::game::AdapterDescriptor &descriptor() const noexcept override { return xar::game::Ck3_12004AdapterDescriptor(); }
  bool enabled() const noexcept override { return true; }
  bool read_snapshot(xar::game::Snapshot &out) const noexcept override {
    if (GetCurrentThreadId() != owner) return false;
    out = frame;
    if (++reads > 1 && drift) ++out.date_raw;
    return true;
  }
  bool submit_set_speed(std::int32_t) const noexcept override { return false; }
  xar::game::SaveCheckpointResult submit_save_checkpoint() const noexcept override { return {}; }
  xar::game::PreviewMoveArmyResult preview_move_army(std::int32_t, std::int32_t) const noexcept override { return {}; }
  bool read_declarable_wars(std::vector<xar::game::DeclarableWarSnapshot> &) const noexcept override { return false; }
#define ABSENT(Result, Name, Params) xar::game::Result Name Params const noexcept override { return xar::game::Result::unavailable; }
  ABSENT(PauseSubmitResult, submit_pause_map, (xar::game::Snapshot *))
  ABSENT(ResumeSubmitResult, submit_resume_map, (xar::game::Snapshot *))
  ABSENT(SelectEventOptionResult, submit_select_event_option, (std::int32_t))
  ABSENT(ReplyPendingInteractionResult, submit_reply_to_pending_interaction, (xar::game::PendingInteractionReply))
  ABSENT(RaiseTroopsResult, submit_raise_troops_default, ())
  ABSENT(MoveArmyResult, submit_move_army, (std::int32_t, std::int32_t))
  ABSENT(DisbandArmyResult, submit_disband_army, (std::int32_t))
  ABSENT(SplitArmyHalfResult, submit_split_army_half, (std::int32_t))
  ABSENT(MergeArmiesResult, submit_merge_armies, (std::int32_t, std::int32_t))
  ABSENT(StartAssaultResult, submit_start_assault, (std::int32_t))
  ABSENT(StopAssaultResult, submit_stop_assault, (std::int32_t))
  ABSENT(ReadDeclarableWarsResult, read_declarable_wars_for_target, (std::int32_t, std::vector<xar::game::DeclarableWarSnapshot> &))
  ABSENT(DeclareWarResult, submit_declare_war, (const xar::game::DeclarableWarSnapshot &))
  ABSENT(ReadArrangeMarriageChoicesResult, read_arrange_marriage_choices, (std::vector<xar::game::ArrangeMarriageChoice> &, xar::game::ArrangeMarriageQueryDiagnostics &))
  ABSENT(ArrangeMarriageResult, submit_arrange_marriage, (const xar::game::ArrangeMarriageChoice &))
  ABSENT(EnforceDemandsResult, submit_enforce_demands, (std::int32_t))
  ABSENT(SurrenderWarResult, submit_surrender_war, (std::int32_t))
  ABSENT(OfferWhitePeaceResult, submit_offer_white_peace, (std::int32_t))
  ABSENT(ReadArmyStrengthsResult, read_army_strengths, (std::vector<xar::game::ArmyStrengthSnapshot> &))
  ABSENT(ReadCombatSimulationInputsResult, read_combat_simulation_inputs, (const xar::game::CombatSimulationInputsRequest &, xar::game::CombatSimulationInputsSnapshot &))
  ABSENT(ReadCombatSimulationInputsV3Result, read_combat_simulation_inputs_v3, (const xar::game::CombatSimulationInputsRequest &, xar::game::CombatSimulationInputsV3Snapshot &))
  ABSENT(ReadWarTerminationOptionsResult, read_war_termination_options, (std::int32_t, xar::game::WarTerminationOptionsSnapshot &))
  ABSENT(ReadWarTerminationTermsResult, read_war_termination_terms, (std::int32_t, xar::game::WarTerminationTermsSnapshot &))
  ABSENT(ReadWarTerminationExitTermsResult, read_war_termination_exit_terms, (std::int32_t, xar::game::WarTerminationExitTermsSnapshot &))
#undef ABSENT
};

void *local_player=nullptr,*tls_context=nullptr;
void *Local(void *){return local_player;}
void *__fastcall Tls()noexcept{return tls_context;}
native::SwayCompletionBindings12002 *current_binding=nullptr;
struct World {
 native::SwayCompletionBindings12002 binding{};
 native::SwayStateBindings12002 source{};
 std::array<std::byte,0xA8> state{};std::array<std::byte,0x28> jomini{};
 std::array<std::byte,0x200> players{};std::array<std::byte,0x80> local{};
 std::vector<std::byte> data=std::vector<std::byte>(0x23000);
 std::array<std::byte,0xE0> entry{};std::array<void *,1> entries{entry.data()};
 std::array<std::byte,0x40> characters{};std::array<std::array<std::byte,0x1D8>,2> persons{};
 void *character_slots=nullptr;
 std::array<std::byte,0x40> storage{},type{},scheme{};std::array<std::byte,0x10> slots{};
 void *state_pointer=state.data(),*jomini_pointer=jomini.data(),*characters_pointer=characters.data();
 World(std::int32_t actor,std::int32_t target){
   binding=actual4::RealBindSwayTerminalImage12004(0x140000000,actual4::kExecutableSha256);
   source=actual4::BindSwayStateImage12004(0x140000000,actual4::kExecutableSha256);
   Check(binding.enabled&&source.enabled&&source.manager_vtable_rva==0x4779548&&source.instance_vtable_rva==0x47794F8&&
       source.type_vtable_rva==0x48B9F30&&binding.success_chance==nullptr&&binding.can_continue==nullptr,
       "actual4 pure terminal/state factories select current proved profile");
   Check(!actual4::RealBindSwayTerminalImage12004(0x140000000,native::kExecutableSha256).enabled,
       "actual4 factory rejects old image identity");
   character_slots=VirtualAlloc(nullptr,0x10000000,MEM_RESERVE,PAGE_NOACCESS);
   if(!character_slots)throw std::runtime_error("reserve full24 character slots");
   SYSTEM_INFO info{};GetSystemInfo(&info);std::array<std::int32_t,2> ids{actor,target};
   for(std::size_t i=0;i<ids.size();++i){auto offset=(static_cast<std::uint32_t>(ids[i])&0xFFFFFFU)*16ULL+8;
     auto page=offset-offset%info.dwPageSize;
     if(!VirtualAlloc(static_cast<std::byte *>(character_slots)+page,info.dwPageSize,MEM_COMMIT,PAGE_READWRITE))throw std::runtime_error("commit own slot");
     Put(persons[i].data(),0x18,ids[i]);Put(character_slots,static_cast<std::size_t>(offset),persons[i].data());}
   binding.core.game_state_slot=&state_pointer;binding.core.jomini_state_slot=&jomini_pointer;
   binding.core.character_storage_slot=&characters_pointer;binding.core.get_local_player=&Local;
   local_player=local.data();Put(state.data(),8,std::int32_t{53220000});Put(state.data(),0xA0,data.data());
   Put(jomini.data(),0x18,players.data());Put(jomini.data(),0x20,std::uint8_t{1});Put(players.data(),0x1F0,std::int32_t{0});Put(local.data(),0x70,std::int32_t{0});
   Put(data.data(),native::kPlayerCharacterManagerOffset+0x58,entries.data());Put(data.data(),native::kPlayerCharacterManagerOffset+0x64,std::int32_t{1});
   Put(entry.data(),0xD8,std::int32_t{0});Put(entry.data(),0xB0,actor);
   Put(characters.data(),0x20,character_slots);Put(characters.data(),0x2C,std::int32_t{0x1000000});
   Put(data.data(),source.manager_offset,source.module_base+source.manager_vtable_rva);Put(data.data(),source.manager_offset+0x20,storage.data());
   Put(storage.data(),0,source.module_base+source.storage_vtable_rva);Put(storage.data(),0x20,slots.data());Put(storage.data(),0x2C,std::int32_t{1});Put(slots.data(),8,scheme.data());
   Put(type.data(),0,source.module_base+source.type_vtable_rva);std::memcpy(type.data()+0x18,"sway",5);Put(type.data(),0x28,std::uint64_t{4});Put(type.data(),0x30,std::uint64_t{15});Put(type.data(),0x38,std::uint32_t{0x4744624F});
   Put(scheme.data(),0,source.module_base+source.instance_vtable_rva);Put(scheme.data(),0x10,std::uint32_t{0});Put(scheme.data(),0x20,type.data());Put(scheme.data(),0x28,std::int32_t{0});
   Put(scheme.data(),0x2C,std::bit_cast<std::uint32_t>(actor));Put(scheme.data(),0x30,std::uint32_t{0});Put(scheme.data(),0x34,std::bit_cast<std::uint32_t>(target));
 }
 ~World(){if(character_slots)VirtualFree(character_slots,0,MEM_RELEASE);}
};
struct Pump {
 std::array<std::byte,0x28> tls{},jomini{};std::array<std::byte,0x18> state{};std::uint8_t initialized=1;
 void *jomini_pointer=jomini.data(),*state_pointer=state.data();std::uintptr_t unused_rng=0;
 explicit Pump(api::MainThreadQueryMailboxV1 &mailbox){
   tls[0x20]=std::byte{1};jomini[0x20]=std::byte{1};Put(state.data(),8,std::int32_t{53220000});tls_context=tls.data();
   mailbox.global_rng_wrapper_slot=reinterpret_cast<std::uintptr_t>(&unused_rng);mailbox.jomini_state_slot=reinterpret_cast<std::uintptr_t>(&jomini_pointer);
   mailbox.game_state_slot=reinterpret_cast<std::uintptr_t>(&state_pointer);mailbox.tls_initialized_flag=reinterpret_cast<std::uintptr_t>(&initialized);mailbox.tls_context_getter=&Tls;
   mailbox.executor_submission_enabled=true;mailbox.offline_fixture=true;mailbox.iat_hook_installed=true;mailbox.state=api::MainThreadQueryMailboxStateV1::idle;
   mailbox.permitted_executor_octoquinquagintary=&actual4::ExecuteSelectedSwayStop12004;
   mailbox.permitted_executor_sway_completion12002=&actual4::ExecuteSwayTerminalMailbox12004;
   for(int i=0;i<2;++i)(void)api::ObserveMainThreadPumpAndDrainV1(mailbox,mailbox.pump_exact_return_rva,GetCurrentThreadId());
 }
 ~Pump(){tls_context=nullptr;}
};
}
