// machine_id: 4-8e1c2f1861; authored 2026-10-19 UTC for isolated B5.
// Production ExecuteIngameDecisionItemActionV1, keyed reader, ModelPass,
// ActionPins, ConfirmReceiver and fixed-widget dispatcher are linked unchanged.
// Fixture seams: GameAdapter snapshot, top-level finder, owned-memory model,
// and a controlled native ABI leaf at the exact manager RVA. This is NOT CK3
// callee/business/HoF qualification. Neither offline override is admitted.
#include "xar_bridge/ingame_decision_item_v1.hpp"
#include "xar_bridge/ingame_ui_navigation_v1.hpp"
#include "xar_bridge/ck3_12004_ingame_decision_v1.hpp"
#include <Windows.h>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
namespace api = xar::ck3_11906;
namespace exact = xar::ck3_12004;
namespace game = xar::game;
// Reuse the exact production pin data; do not replace any production check.
#include "../src/ingame_decision_item_12004_pins_v1.inc"
constexpr auto kAbi = api::GuiAbiRevisionV1::crozier12004;
constexpr std::int32_t kActor = 7;
constexpr std::string_view kDecision = "create_hof_decision";

template<class T> void Put(void *object, std::size_t offset, const T &value) {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
}
template<std::size_t N> struct Buffer {
  alignas(void *) std::array<std::byte, N> bytes{};
  void *data() noexcept { return bytes.data(); }
};

// Reserve the image address range but commit only pages actually used below.
// No image file, mapping file, TEMP file or CK3 process is created.
class OwnedImage {
 public:
  OwnedImage() {
    base_ = static_cast<std::byte *>(VirtualAlloc(nullptr, api::kCrozierExactImageSize,
        MEM_RESERVE, PAGE_NOACCESS));
    if (!base_) throw std::runtime_error("owned image reserve failed");
  }
  ~OwnedImage() { if (base_) VirtualFree(base_, 0, MEM_RELEASE); }
  OwnedImage(const OwnedImage &) = delete;
  OwnedImage &operator=(const OwnedImage &) = delete;
  std::uintptr_t base() const noexcept { return reinterpret_cast<std::uintptr_t>(base_); }
  void *at(std::uintptr_t rva) const noexcept { return base_ + rva; }
  void write(std::uintptr_t rva, const void *data, std::size_t count) {
    if (rva >= api::kCrozierExactImageSize || count > api::kCrozierExactImageSize-rva)
      throw std::runtime_error("owned image bound");
    const auto first = rva & ~std::uintptr_t{4095};
    const auto last = (rva + count + 4095) & ~std::uintptr_t{4095};
    for (auto page=first; page<last; page+=4096) {
      MEMORY_BASIC_INFORMATION info{};
      if (!VirtualQuery(at(page), &info, sizeof(info))) throw std::runtime_error("VirtualQuery");
      if (info.State != MEM_COMMIT && !VirtualAlloc(at(page),4096,MEM_COMMIT,PAGE_READWRITE))
        throw std::runtime_error("owned image page commit failed");
      DWORD old=0;
      if (!VirtualProtect(at(page),4096,PAGE_READWRITE,&old)) throw std::runtime_error("VirtualProtect RW");
    }
    std::memcpy(at(rva),data,count);
  }
  template<class T> void value(std::uintptr_t rva,const T &v) { write(rva,&v,sizeof(v)); }
  template<std::size_t N> void code(std::uintptr_t rva,const std::array<unsigned char,N> &v) {
    write(rva,v.data(),v.size());
  }
  void executable(std::uintptr_t rva) {
    DWORD old=0;
    if (!VirtualProtect(at(rva & ~std::uintptr_t{4095}),4096,PAGE_EXECUTE_READ,&old))
      throw std::runtime_error("VirtualProtect RX");
    if (!FlushInstructionCache(GetCurrentProcess(),at(rva),128)) throw std::runtime_error("FlushInstructionCache");
  }
  void jump(std::uintptr_t rva,void *function) {
    std::array<unsigned char,12> code{0x48,0xb8,0,0,0,0,0,0,0,0,0xff,0xe0};
    const auto address=reinterpret_cast<std::uintptr_t>(function);
    std::memcpy(code.data()+2,&address,sizeof(address));
    write(rva,code.data(),code.size());
  }
 private:
  std::byte *base_=nullptr;
};

class SnapshotAdapter final : public game::GameAdapter {
 public:
  game::Snapshot frame{};
  SnapshotAdapter() {
    frame.date_raw=51394920;frame.speed=3;frame.paused=true;frame.map_ready=true;
    frame.has_played_character=true;frame.played_character_id=kActor;frame.played_character_alive=true;
  }
  const game::AdapterDescriptor &descriptor() const noexcept override {
    static const game::AdapterDescriptor descriptor{exact::kAdapterId,exact::kGameVersion,
        exact::kExecutableSha256,"owned-memory-fixture-not-CK3",{}};
    return descriptor;
  }
  bool enabled() const noexcept override { return true; }
  bool read_snapshot(game::Snapshot &out) const noexcept override { out=frame;return true; }
  game::PauseSubmitResult submit_pause_map(game::Snapshot *) const noexcept override { return game::PauseSubmitResult::unavailable; }
  game::ResumeSubmitResult submit_resume_map(game::Snapshot *) const noexcept override { return game::ResumeSubmitResult::unavailable; }
  bool submit_set_speed(std::int32_t) const noexcept override { return false; }
  game::SaveCheckpointResult submit_save_checkpoint() const noexcept override { return {}; }
  game::PreviewMoveArmyResult preview_move_army(std::int32_t,std::int32_t) const noexcept override { return {}; }
  bool read_declarable_wars(std::vector<game::DeclarableWarSnapshot> &) const noexcept override { return false; }
#define NO_ACTION(Result,Method,Parameters) game::Result Method Parameters const noexcept override { return game::Result::unavailable; }
  NO_ACTION(SelectEventOptionResult,submit_select_event_option,(std::int32_t))
  NO_ACTION(ReplyPendingInteractionResult,submit_reply_to_pending_interaction,(game::PendingInteractionReply))
  NO_ACTION(RaiseTroopsResult,submit_raise_troops_default,())
  NO_ACTION(MoveArmyResult,submit_move_army,(std::int32_t,std::int32_t))
  NO_ACTION(DisbandArmyResult,submit_disband_army,(std::int32_t))
  NO_ACTION(SplitArmyHalfResult,submit_split_army_half,(std::int32_t))
  NO_ACTION(MergeArmiesResult,submit_merge_armies,(std::int32_t,std::int32_t))
  NO_ACTION(StartAssaultResult,submit_start_assault,(std::int32_t))
  NO_ACTION(StopAssaultResult,submit_stop_assault,(std::int32_t))
  NO_ACTION(ReadDeclarableWarsResult,read_declarable_wars_for_target,(std::int32_t,std::vector<game::DeclarableWarSnapshot> &))
  NO_ACTION(DeclareWarResult,submit_declare_war,(const game::DeclarableWarSnapshot &))
  NO_ACTION(ReadArrangeMarriageChoicesResult,read_arrange_marriage_choices,(std::vector<game::ArrangeMarriageChoice> &,game::ArrangeMarriageQueryDiagnostics &))
  NO_ACTION(ArrangeMarriageResult,submit_arrange_marriage,(const game::ArrangeMarriageChoice &))
  NO_ACTION(EnforceDemandsResult,submit_enforce_demands,(std::int32_t))
  NO_ACTION(ReadArmyStrengthsResult,read_army_strengths,(std::vector<game::ArmyStrengthSnapshot> &))
  NO_ACTION(ReadCombatSimulationInputsResult,read_combat_simulation_inputs,(const game::CombatSimulationInputsRequest &,game::CombatSimulationInputsSnapshot &))
  NO_ACTION(ReadCombatSimulationInputsV3Result,read_combat_simulation_inputs_v3,(const game::CombatSimulationInputsRequest &,game::CombatSimulationInputsV3Snapshot &))
  NO_ACTION(ReadWarTerminationOptionsResult,read_war_termination_options,(std::int32_t,game::WarTerminationOptionsSnapshot &))
  NO_ACTION(ReadWarTerminationTermsResult,read_war_termination_terms,(std::int32_t,game::WarTerminationTermsSnapshot &))
  NO_ACTION(ReadWarTerminationExitTermsResult,read_war_termination_exit_terms,(std::int32_t,game::WarTerminationExitTermsSnapshot &))
  NO_ACTION(SurrenderWarResult,submit_surrender_war,(std::int32_t))
  NO_ACTION(OfferWhitePeaceResult,submit_offer_white_peace,(std::int32_t))
#undef NO_ACTION
};

struct Widget {
  Buffer<0x500> memory;
  std::string name;
  std::vector<void *> children;
  void *data() noexcept { return memory.data(); }
};
struct Scene;
Scene *current_scene=nullptr;
void *__fastcall FindRootLeaf(void *,const std::string *);
bool __fastcall ManagerLeaf(void *,std::uint32_t,const void *,void *);
void __fastcall ConfirmLeaf(void *);

struct Scene {
  OwnedImage image;
  SnapshotAdapter adapter;
  Buffer<0x220> application,logical;
  Buffer<0x100> gfx;
  Buffer<0x200> handler;
  Buffer<0x300> list;
  Buffer<0x100> detail;
  Buffer<0x80> definition;
  Buffer<0x80> second;
  Buffer<0x500> context;
  Buffer<0x20> lookup_host,manager;
  Buffer<0x100> owner;
  Buffer<0x40> storage;
  Buffer<0x200> character;
  Buffer<0x80> slots;
  Buffer<0x20> groups,rows;
  Buffer<0x48> callback_rows;
  Buffer<0x20> callback;
  std::array<Widget,15> widgets;
  api::MainThreadQueryMailboxV1 mailbox;
  api::MainThreadExecutionStampV1 stamp{};
  api::ZhongguoScoreboardNativeEnvironmentV1 environment;
  api::ZhongguoScoreboardActionDispatchEnvironmentV1 dispatch;
  std::uint8_t tls_initialized=1;
  std::uint32_t manager_calls=0,callback_calls=0;
  bool leaf_contract=false,fault=false;
  Scene() {
    current_scene=this;
    SeedPins();
    Type(application.data(),exact::kDecisionApplicationType12004V1,0);
    Type(logical.data(),exact::kDecisionLogicalType12004V1,1);
    Type(gfx.data(),exact::kDecisionGfxType12004V1,2);
    Type(handler.data(),exact::kDecisionHandlerType12004V1,3);
    Type(list.data(),exact::kDecisionListType12004V1,4);
    Type(detail.data(),exact::kDecisionDetailType12004V1,5);
    Type(definition.data(),exact::kDecisionDefinitionType12004V1,6);
    // This owning string remains alive until all reads have completed.
    DecisionString(definition.data(),0x18,kDecision);
    Put(application.data(),api::kZhongguoGuiChainFirstOffset,second.data());
    Put(second.data(),api::kZhongguoGuiChainSecondOffset,context.data());
    Put(context.data(),api::kZhongguoGuiContextOffset,lookup_host.data());
    Put(lookup_host.data(),api::kZhongguoGuiOwnerOffset,owner.data());
    Put(context.data(),api::kZhongguoGuiShortcutManagerOffset,manager.data());
    Put(manager.data(),0,context.data());
    Put(logical.data(),0x18,application.data());Put(logical.data(),0x10,gfx.data());
    Put(gfx.data(),0x90,application.data());Put(gfx.data(),0x20,logical.data());Put(gfx.data(),0x88,handler.data());
    Put(handler.data(),0x1B0,list.data());Put(handler.data(),0x1B8,detail.data());
    Put(list.data(),0x98,logical.data());Put(list.data(),0xA0,handler.data());
    Put(list.data(),0x60,widgets[14].data());Put(detail.data(),0x60,widgets[0].data());
    Put(detail.data(),0xA0,handler.data());Put(detail.data(),0xD0,definition.data());Put(detail.data(),0xD8,kActor);
    Vector(list.data(),0x258,groups.data());Put(groups.data(),0,definition.data());Vector(groups.data(),8,rows.data());
    Put(rows.data(),0,definition.data());Put(rows.data(),8,character.data());Put(rows.data(),0x10,kActor);Put(rows.data(),0x18,list.data());
    Put(storage.data(),0x20,slots.data());Put(storage.data(),0x2C,std::uint32_t{8});
    Put(slots.data(),std::size_t{kActor}*0x10+8,character.data());Put(character.data(),0x18,kActor);
    image.value(exact::kDecisionActorReferenceSlotRva12004V1,kActor);
    image.value(exact::kCharacterStorageSlotRva,storage.data());image.value(exact::kJominiStateSlotRva,logical.data());
    BuildTree();
    environment=api::BindZhongguoScoreboardNativeEnvironmentV1(image.base(),true,kAbi,exact::kExecutableSha256);
    environment.find_top_level_widget=&FindRootLeaf; // disclosed outer lookup leaf, not a core reader replacement
    image.value(api::GuiGlobalSlotRvaV1(kAbi),application.data());
    dispatch=api::BindZhongguoScoreboardActionDispatchEnvironmentV1(image.base(),true,kAbi);
    const auto tid=GetCurrentThreadId();mailbox.owner_thread_id=tid;
    mailbox.owner_verified_pump_epochs=api::kMainThreadQueryMinimumOwnerVerifiedPumpEpochs;
    mailbox.paused_owner_verified_pump_epochs=api::kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs;
    stamp.pump_epoch=9;stamp.thread_id=tid;stamp.date_raw=adapter.frame.date_raw;stamp.paused=true;
    stamp.tls_initialized_flag_address=reinterpret_cast<std::uintptr_t>(&tls_initialized);
    stamp.tls_initialized=1;stamp.tls_context=reinterpret_cast<std::uintptr_t>(logical.data());stamp.tls_main_thread_marker=1;
    stamp.jomini_state=reinterpret_cast<std::uintptr_t>(logical.data());stamp.game_state=reinterpret_cast<std::uintptr_t>(character.data());
  }
  ~Scene() { current_scene=nullptr; }
  static void Vector(void *object,std::size_t offset,void *data) {
    Put(object,offset,data);Put(object,offset+8,std::uint32_t{1});Put(object,offset+12,std::uint32_t{1});
  }
  void Type(void *object,exact::IngameDecisionTypeIdentity12004V1 type,std::uint32_t index) {
    const auto col_rva=std::uint32_t{0x6000}+index*0x40;
    const std::array<std::uint32_t,6> col{1,0,0,type.type_descriptor_rva,0,col_rva};
    image.write(col_rva,col.data(),sizeof(col));image.value(type.vtable_rva-8,image.at(col_rva));
    Put(object,0,image.at(type.vtable_rva));
  }
  static void DecisionString(void *object,std::size_t offset,std::string_view text) {
    // kDecision is a static literal with a trailing NUL.
    Put(object,offset,text.data());Put(object,offset+0x10,std::uint64_t{text.size()});
    Put(object,offset+0x18,std::uint64_t{text.size()});
  }
  void Node(std::size_t n,std::string name,std::initializer_list<std::size_t> children={}) {
    auto &w=widgets[n];w.name=std::move(name);Put(w.data(),0,image.at(0x4000));
    Put(w.data(),api::kZhongguoWidgetGuiContextOffset,context.data());
    const auto length=static_cast<std::uint64_t>(w.name.size());
    if(length<16) {
      std::memcpy(static_cast<std::byte *>(w.data())+api::kZhongguoWidgetNameOffset,w.name.c_str(),w.name.size()+1);
      Put(w.data(),api::kZhongguoWidgetNameOffset+24,std::uint64_t{15});
    } else {
      Put(w.data(),api::kZhongguoWidgetNameOffset,w.name.c_str());
      Put(w.data(),api::kZhongguoWidgetNameOffset+24,length);
    }
    Put(w.data(),api::kZhongguoWidgetNameOffset+16,length);
    for(const auto child:children){w.children.push_back(widgets[child].data());Put(widgets[child].data(),api::kZhongguoWidgetParentOffset,w.data());}
    Put(w.data(),api::kZhongguoWidgetChildrenOffset,w.children.data());
    Put(w.data(),api::kZhongguoWidgetChildCountOffset,static_cast<std::int32_t>(w.children.size()));
  }
  void BuildTree() {
    Node(0,"decisiondetail_view",{1});Node(1,"",{2,3,4,5,6,7,8});
    Node(2,"cost");Node(3,"");Node(4,"",{9,10,11});Node(5,"",{12,13});
    Node(6,"");Node(7,"");Node(8,"");Node(9,"");Node(10,"");
    Node(11,"cram_study_start_tutorial_highlight");Node(12,"back");Node(13,"");Node(14,"decisions_view");
    Put(widgets[13].data(),api::kZhongguoWidgetHiddenFlagsOffset,std::uint8_t{8});
    Put(widgets[10].data(),0,image.at(0x4800));
    image.value(0x4800+13*sizeof(void *),image.at(api::GuiButtonBaseSlot13RvaV1(kAbi)));
    image.value(0x4800+10*sizeof(void *),image.at(0x3000));
    image.value(0x5000+2*sizeof(void *),image.at(0x3000));
    Put(callback.data(),0,image.at(0x5000));Put(callback_rows.data(),api::kZhongguoCallbackObjectOffset,callback.data());
    Put(widgets[10].data(),api::kZhongguoPrimaryCallbackGroupOffset,callback_rows.data());
    Put(widgets[10].data(),api::kZhongguoPrimaryCallbackGroupOffset+api::kZhongguoCallbackGroupCountOffset,std::int32_t{1});
    Put(owner.data(),api::kZhongguoGuiOwnerRootWidgetOffset,widgets[14].data());
  }
  void SeedPins() {
    constexpr std::array<unsigned char,32> find{0x48,0x89,0x5c,0x24,0x08,0x48,0x89,0x6c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x57,0x48,0x83,0xec,0x20,0x48,0x8b,0x81,0xd0,0,0,0,0x48,0x8b,0xfa,0x48,0x8b};
    constexpr std::array<unsigned char,8> groups_code{0x48,0x8d,0x81,0x58,0x02,0,0,0xc3};
    constexpr std::array<unsigned char,4> definition_code{0x48,0x8b,0x01,0xc3};
    constexpr std::array<unsigned char,32> activate{0x48,0x89,0x5c,0x24,0x08,0x48,0x89,0x6c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x57,0x48,0x83,0xec,0x60,0x49,0x8b,0xf0,0x8b,0xea,0x48,0x8b,0xf9,0x49,0x8b,0x59,0x48};
    constexpr std::array<unsigned char,32> descendant{0x48,0x89,0x5c,0x24,0x08,0x48,0x89,0x6c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x57,0x48,0x83,0xec,0x20,0x48,0x8b,0xf1,0x48,0x8b,0xea,0x48,0x8b,0x89,0xf0,0,0};
    constexpr std::array<unsigned char,32> button{0x40,0x53,0x48,0x83,0xec,0x20,0x48,0x8b,0xd9,0x0f,0xb6,0x89,0xd0,0,0,0,0x80,0xe1,0x02,0x74,0x26,0x44,0x8b,0x42,0x10,0x41,0x83,0xe8,0x0d,0x74,0x0c,0x41};
    image.code(api::GuiFindTopLevelWidgetRvaV1(kAbi),find);
    image.code(exact::kDecisionGroupsGetterRva12004V1,groups_code);
    image.code(exact::kDecisionDefinitionGetterRva12004V1,definition_code);
    image.code(exact::kDecisionRowOnSelectRva12004V1,kDecisionOnSelectPin12004V1);
    image.code(exact::kDecisionRowOnSelectWrapperRva12004V1,kDecisionOnSelectWrapperPin12004V1);
    image.code(exact::kDecisionSetDecisionRva12004V1,kDecisionSetDecisionPin12004V1);
    image.code(exact::kDecisionDetailDispatchRva12004V1,kDecisionDetailDispatchPin12004V1);
    image.code(api::GuiShortcutManagerActivateRvaV1(kAbi),activate);
    image.code(api::GuiStrictDescendantRvaV1(kAbi),descendant);
    image.code(api::GuiButtonBaseSlot13RvaV1(kAbi),button);
    // Execute the pinned manager prologue, restore exactly its nonvolatile
    // saves/stack, then tail-call the disclosed ABI leaf. No guarded prefix is
    // overwritten; no real CK3 machine-code body or semantic effect is claimed.
    constexpr std::array<unsigned char,20> restore{0x48,0x83,0xc4,0x60,0x5f,
        0x48,0x8b,0x5c,0x24,0x08,0x48,0x8b,0x6c,0x24,0x10,0x48,0x8b,0x74,0x24,0x18};
    const auto manager_rva=api::GuiShortcutManagerActivateRvaV1(kAbi);
    image.code(manager_rva+32,restore);image.jump(manager_rva+52,reinterpret_cast<void *>(&ManagerLeaf));
    image.jump(0x3000,reinterpret_cast<void *>(&ConfirmLeaf));
    image.executable(manager_rva);image.executable(0x3000);
  }
  api::IngameDecisionItemActionContextV1 Request() {
    api::IngameDecisionItemActionContextV1 q{};q.action=api::IngameDecisionItemActionKindV1::confirm_outcome;
    q.expected_outcome="decision_closed";q.observation.game=&adapter;q.observation.expected_snapshot=adapter.frame;
    q.observation.native_revision=42;q.observation.connection_generation=3;q.observation.requested_key=kDecision;
    return q;
  }
};

void *__fastcall FindRootLeaf(void *owner,const std::string *name) {
  if(!current_scene||!name||owner!=current_scene->owner.data())return nullptr;
  if(*name=="decisions_view")return current_scene->widgets[14].data();
  if(*name=="decisiondetail_view")return current_scene->widgets[0].data();
  return nullptr;
}
void __fastcall ConfirmLeaf(void *callback) {
  if(!current_scene||callback!=current_scene->callback.data())RaiseException(0xE0420011,0,0,nullptr);
  ++current_scene->callback_calls;
  if(current_scene->fault)RaiseException(0xE0420012,0,0,nullptr);
  Put(current_scene->widgets[0].data(),api::kZhongguoWidgetHiddenFlagsOffset,std::uint8_t{8});
}
bool __fastcall ManagerLeaf(void *manager,std::uint32_t event,const void *text,void *pimpl) {
  if(!current_scene)return false;
  auto &s=*current_scene;++s.manager_calls;
  void *target=nullptr;std::uint64_t capacity=0,length=1;
  std::memcpy(&target,static_cast<std::byte *>(pimpl)+api::kZhongguoShortcutPimplTargetOffset,sizeof(target));
  std::memcpy(&capacity,static_cast<const std::byte *>(text)+api::kZhongguoShortcutCStringCapacityOffset,sizeof(capacity));
  std::memcpy(&length,static_cast<const std::byte *>(text)+api::kZhongguoShortcutCStringLengthOffset,sizeof(length));
  s.leaf_contract=manager==s.manager.data()&&event==0&&target==s.widgets[10].data()&&capacity==15&&length==0;
  if(!s.leaf_contract)return false;
  void *rows=nullptr,*callback=nullptr,*vtable=nullptr,*slot2=nullptr;
  std::memcpy(&rows,static_cast<std::byte *>(target)+api::kZhongguoPrimaryCallbackGroupOffset,sizeof(rows));
  std::memcpy(&callback,static_cast<std::byte *>(rows)+api::kZhongguoCallbackObjectOffset,sizeof(callback));
  std::memcpy(&vtable,callback,sizeof(vtable));std::memcpy(&slot2,static_cast<std::byte *>(vtable)+16,sizeof(slot2));
  reinterpret_cast<void(__fastcall *)(void *)>(slot2)(callback);
  return false; // Native handled=false still must remain an ACK, never success.
}
bool Check(bool value,const char *what,const api::IngameDecisionItemActionResultV1 *r=nullptr) {
  if(!value){std::cerr<<what;if(r)std::cerr<<": "<<r->unavailable_reason<<" / "<<r->before.unavailable_reason
      <<" / "<<r->before.model_failed_stage;std::cerr<<'\n';}return value;
}
bool Positive() {
  Scene s;auto q=s.Request();
  if(!Check(api::ExecuteIngameDecisionItemActionV1(q,s.mailbox,s.stamp,s.environment,s.dispatch),"production action execute"))return false;
  const auto &r=q.result;
  bool ok=Check(r.before.available&&r.before.source_abi_pins_verified&&r.action_abi_pins_verified&&r.receiver_qualified&&
      r.detail_actor_binding_verified&&r.no_blocking_modal_verified&&r.dispatch_invoked&&r.native_call_completed&&
      !r.native_handled&&r.gui_owner_binding_verified&&r.frame_verified&&!r.postcondition_verified&&
      r.status=="acknowledged_verification_pending"&&r.target_child_path=="0/2/1"&&r.unavailable_reason.empty()&&
      s.manager_calls==1&&s.callback_calls==1&&s.leaf_contract,"real guarded Confirm one dispatch/pending",&r);
  auto after=q.observation;after.result={};
  ok&=Check(api::ExecuteIngameDecisionItemQueryV1(after,s.mailbox,s.stamp,s.environment)&&after.result.available&&
      after.result.detail_tree_complete&&!after.result.detail_root_visible&&s.manager_calls==1&&s.callback_calls==1,
      "independent production reader observes owned closure without redispatch");
  const auto json=api::SerializeIngameDecisionItemActionV1(r);
  ok&=Check(json.find("\"verification_pending\":true")!=std::string::npos&&
      json.find("\"postcondition_verified\":false")!=std::string::npos,"production action serializer keeps pending");
  return ok;
}
template<class Mutate> bool Reject(const char *name,Mutate change) {
  Scene s;auto q=s.Request();change(s,q);
  const bool execute=api::ExecuteIngameDecisionItemActionV1(q,s.mailbox,s.stamp,s.environment,s.dispatch);
  return Check(execute&&!q.result.dispatch_invoked&&!q.result.postcondition_verified&&
      !q.result.unavailable_reason.empty()&&s.manager_calls==0&&s.callback_calls==0,name,&q.result);
}
bool FaultUnknown() {
  Scene s;s.fault=true;auto q=s.Request();
  const bool execute=api::ExecuteIngameDecisionItemActionV1(q,s.mailbox,s.stamp,s.environment,s.dispatch);
  return Check(execute&&q.result.dispatch_invoked&&!q.result.native_call_completed&&!q.result.postcondition_verified&&
      q.result.unavailable_reason=="native_outcome_confirm_result_unknown_no_retry"&&
      s.manager_calls==1&&s.callback_calls==1,"fault consumes one attempt and remains unknown/no retry",&q.result);
}
} // namespace

int main() {
  try {
    bool ok=Positive();
    ok&=Reject("native query offline override rejected",[](Scene&s,auto&){s.environment.offline_fixture_function_overrides=true;});
    ok&=Reject("dispatch offline override rejected",[](Scene&s,auto&){s.dispatch.offline_fixture_function_overrides=true;});
    ok&=Reject("wrong selected actor rejected",[](Scene&s,auto&){Put(s.detail.data(),0xD8,std::int32_t{8});});
    ok&=Reject("disabled real Confirm rejected",[](Scene&s,auto&){Put(s.widgets[10].data(),api::kZhongguoWidgetHiddenFlagsOffset,std::uint8_t{2});});
    ok&=Reject("wrong owner stamp rejected",[](Scene&s,auto&){++s.stamp.thread_id;});
    ok&=Reject("changed actual action pin rejected",[](Scene&s,auto&){s.image.value(exact::kDecisionRowOnSelectRva12004V1,std::uint8_t{0});});
    ok&=FaultUnknown();
    std::cout<<"{\"schema\":\"ingame-decision-confirm-outcome12004-owned-fixture-v1\","
        "\"machine_id\":\"4-8e1c2f1861\",\"status\":\""<<(ok?"GREEN":"RED")<<"\","
        "\"production_action_and_dispatch\":true,\"offline_override\":false,\"scenes\":8,"
        "\"owned_image_virtual_reserve_bytes\":"<<api::kCrozierExactImageSize<<","
        "\"disk_image_written\":false,\"native_abi_leaf_is_fixture\":true,"
        "\"top_level_lookup_and_snapshot_are_fixture_seams\":true,\"ck3_business_or_hof_success_proved\":false}\n";
    return ok?0:1;
  } catch(const std::exception &e){std::cerr<<"fixture setup failed: "<<e.what()<<'\n';return 2;}
}
