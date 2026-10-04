// Offline test only. No CK3 process, desktop, or native game function executes.
#if defined(NDEBUG)
#undef NDEBUG
#endif
#include "../src/ingame_ui_navigation_v1.cpp"
#include <cassert>
#include <iostream>

namespace xar::ck3_11906 {
// Explicit offline GUI projection stubs. No CK3 function executes.
static void *fixture_army_root=nullptr,*fixture_cast_object=nullptr;
static bool fixture_army_root_available=false;
static std::uint32_t fixture_select_calls=0,fixture_select_id=0xFFFFFFFF;
static void *fixture_select_handler=nullptr;static bool fixture_select_replace=false;
static void *__cdecl FixtureArmyCast(void *,long,const void *,const void *,int) {return fixture_cast_object;}
static void __fastcall FixtureSelectUnit(void *handler,std::uint32_t id,bool replace) {
  ++fixture_select_calls;fixture_select_handler=handler;fixture_select_id=id;fixture_select_replace=replace;
}
bool ResolveNamedGuiWidgetV1(const ZhongguoScoreboardNativeEnvironmentV1 &,const ZhongguoScoreboardAccessV1 &,std::string_view root_name,std::string_view widget_name,void *&root,void *&widget) noexcept {
  if(!fixture_army_root_available || root_name!="army_window" || widget_name!="army_window")return false;
  root=widget=fixture_army_root;return true;
}
bool ReadGuiWidgetRuntimeV1(const ZhongguoScoreboardAccessV1 &,void *root,std::string &name,void *&vtable,bool &visible,bool &enabled) noexcept {
  if(!fixture_army_root_available || root!=fixture_army_root)return false;
  name="army_window";std::uint8_t flags=0;
  if(!Value(root,0,vtable) || !Value(root,0xD0,flags))return false;
  visible=(flags&8)==0;enabled=(flags&2)==0;return true;
}
bool InspectNamedGuiSubtreeV1(const ZhongguoScoreboardAccessV1 &,std::uintptr_t base,void *root,std::string_view name,NamedGuiTreeInspectionV1 &out) noexcept {
  if(!fixture_army_root_available || root!=fixture_army_root)return false;
  out={};out.scope_root_name=std::string(name);out.root_available=true;out.widget_count=1;out.widgets.resize(1);
  auto &row=out.widgets[0];row.runtime_name=std::string(name);row.effective_visible=(static_cast<unsigned char *>(root)[0xD0]&8)==0;
  row.enabled=(static_cast<unsigned char *>(root)[0xD0]&2)==0;void *vtable=nullptr;Value(root,0,vtable);
  row.vtable_rva=reinterpret_cast<std::uintptr_t>(vtable)-base;return true;
}
// Pure offline GUI-chain resolver responses. No native GUI function executes.
static bool fixture_gui_available=false;
static std::uint32_t fixture_gui_reads=0;
static IngameUiGuiOwnerBindingV1 fixture_gui_first{},fixture_gui_second{};
bool ResolveZhongguoScoreboardNativeGuiContextAndOwnerV1(const ZhongguoScoreboardNativeEnvironmentV1 &,const ZhongguoScoreboardAccessV1 &,void *&context,void *&owner) noexcept {
  const auto &row=fixture_gui_reads++==0?fixture_gui_first:fixture_gui_second;
  context=row.context;owner=row.owner;return fixture_gui_available;
}
}
int main() {
  using namespace xar::ck3_11906;
  IngameUiRequestV1 r{};
  for(auto revision:{GuiAbiRevisionV1::legacy11906,GuiAbiRevisionV1::crozier12003}) {
    assert(IsIngameUiRequestSupportedV1(revision,{IngameUiOperationV1::select_army,IngameUiWindowKindV1::army,0}));
    assert(IsIngameUiRequestSupportedV1(revision,{IngameUiOperationV1::query,IngameUiWindowKindV1::army,0}));
  }
  for(auto kind:{IngameUiWindowKindV1::character,IngameUiWindowKindV1::combat,IngameUiWindowKindV1::knights})
    assert(!IsIngameUiRequestSupportedV1(GuiAbiRevisionV1::crozier12003,{IngameUiOperationV1::query,kind,0}));
  assert(!IsIngameUiRequestSupportedV1(static_cast<GuiAbiRevisionV1>(2),{IngameUiOperationV1::query,IngameUiWindowKindV1::army,0}));
  assert(ParseIngameUiRequestV1(R"({"window_kind":"character","operation":"open_character","subject_id":33437})",false,r));
  assert(r.subject_id==33437);
  assert(!ParseIngameUiRequestV1(R"({"window_kind":"character","operation":"open_combat","subject_id":33437})",false,r));
  assert(!ParseIngameUiRequestV1(R"({"window_kind":"combat","operation":"open_combat","subject_id":4294967295})",false,r));
  assert(!ParseIngameUiRequestV1(R"({"window_kind":"combat","operation":"open_combat","subject_id":4294967296})",false,r));
  assert(!ParseIngameUiRequestV1(R"({"window_kind":"knights","operation":"open_knights","subject_id":33437})",false,r));
  assert(ParseIngameUiRequestV1(R"({"window_kind":"knights","operation":"open_knights","subject_id":0})",false,r));
  assert(!ParseIngameUiRequestV1(R"({"window_kind":"unknown","subject_id":0})",true,r));
  assert(ParseIngameUiRequestV1(R"({"window_kind":"combat","subject_id":0})",true,r));
  assert(!ParseIngameUiRequestV1(R"({"window_kind":"combat","subject_id":16777218})",true,r));
  assert(!ParseIngameUiRequestV1(R"({"window_kind":"combat","subject_id":true})",true,r));
  assert(ParseIngameUiRequestV1(R"({"window_kind":"combat","operation":"hover_right_knights","subject_id":16777218})",false,r));
  assert(!ParseIngameUiRequestV1(R"({"window_kind":"character","operation":"hover_right_knights","subject_id":33437})",false,r));
  assert(!ParseIngameUiRequestV1(R"({"window_kind":"combat","operation":"hover_side1_knights","subject_id":16777218})",false,r));
  assert(ParseIngameUiRequestV1(R"({"window_kind":"combat","operation":"fit_combat_window","subject_id":16777218})",false,r));
  assert(!ParseIngameUiRequestV1(R"({"window_kind":"army","operation":"fit_combat_window","subject_id":18})",false,r));
  // A complete content union is fitted with the smallest translation using
  // current native viewport units. Scaling, origin, and oversize are policy
  // inputs rather than a hard-coded screenshot resolution or multiplier.
  UiFloat2V1 delta{};
  assert(ComputeCombatUiFitTranslationV1({0,0,2560,1440},{820,1120,921,364},delta));
  assert(delta.x==0 && delta.y==-44);
  assert(ComputeCombatUiFitTranslationV1({0,0,2560,1440},{820,1076,921,364},delta));
  assert(delta.x==0 && delta.y==0);
  assert(ComputeCombatUiFitTranslationV1({100,50,1000,600},{80,40,900,580},delta));
  assert(delta.x==20 && delta.y==10);
  assert(ComputeCombatUiFitTranslationV1({0,0,5120,2880},{1640,2240,1842,728},delta));
  assert(delta.x==0 && delta.y==-88);
  assert(!ComputeCombatUiFitTranslationV1({0,0,2560,1440},{0,0,2600,400},delta));
  assert(!ComputeCombatUiFitTranslationV1({0,0,2560,1440},{0,0,800,1500},delta));
  assert(!ComputeCombatUiFitTranslationV1({0,0,0,1440},{0,0,800,400},delta));
  assert(!ComputeCombatUiFitTranslationV1({0,0,2560,1440},{0,0,-1,400},delta));
  assert(!ComputeCombatUiFitTranslationV1({0,0,2560,1440},{(std::numeric_limits<float>::quiet_NaN)(),0,800,400},delta));
  assert(JsonEscape("a\"b\\c\n")=="a\\\"b\\\\c\\u000A");
  // Actual production modal helper uses ReadProcessMemory over offline buffers.
  // Registered hidden receivers are not active blocking modals; a visible
  // earlier entry must still refuse even when the absolute last entry is hidden.
  std::array<unsigned char,0x300> modal_context{};
  std::array<unsigned char,0xD1> hidden_receiver{},visible_receiver{};
  hidden_receiver[0xD0]=0xB8;visible_receiver[0xD0]=0;
  std::array<void *,256> modal_entries{};
  const auto set_modal=[&](std::int32_t n,void *data){
    std::memcpy(modal_context.data()+kZhongguoGuiModalReceiversOffset,&data,sizeof(data));
    std::memcpy(modal_context.data()+kZhongguoGuiModalReceiverCountOffset,&n,sizeof(n));
  };
  IngameUiModalAdmissionV1 modal{};
  set_modal(0,nullptr);
  assert(ReadModalNavigationAdmission(modal_context.data(),modal) && modal.header_read && modal.receivers_verified && modal.receivers.empty());
  set_modal(1,modal_entries.data());modal_entries[0]=hidden_receiver.data();
  assert(ReadModalNavigationAdmission(modal_context.data(),modal) && modal.receiver_count==1 && modal.receivers_verified && modal.effective_visible_count==0 && modal.receivers[0].flags_d0==0xB8);
  modal_entries[0]=visible_receiver.data();
  assert(!ReadModalNavigationAdmission(modal_context.data(),modal) && modal.receivers_verified && modal.effective_visible_count==1 && modal.unavailable_reason=="effective_visible_modal_receiver_blocks_navigation");
  visible_receiver[0xD0]=0x10; // local hidden alone is not effective-hidden
  assert(!ReadModalNavigationAdmission(modal_context.data(),modal) && modal.effective_visible_count==1);
  visible_receiver[0xD0]=0;
  set_modal(2,modal_entries.data());modal_entries[0]=visible_receiver.data();modal_entries[1]=hidden_receiver.data();
  assert(!ReadModalNavigationAdmission(modal_context.data(),modal) && modal.effective_visible_count==1 && modal.receivers.size()==2);
  modal_entries[0]=hidden_receiver.data();modal_entries[1]=visible_receiver.data();
  assert(!ReadModalNavigationAdmission(modal_context.data(),modal) && modal.effective_visible_count==1);
  for(auto &entry:modal_entries)entry=hidden_receiver.data();set_modal(256,modal_entries.data());
  assert(ReadModalNavigationAdmission(modal_context.data(),modal) && modal.receivers.size()==256);
  set_modal(-1,modal_entries.data());
  assert(!ReadModalNavigationAdmission(modal_context.data(),modal) && modal.receiver_count==-1 && modal.unavailable_reason=="modal_receiver_count_out_of_bounds");
  set_modal(257,modal_entries.data());assert(!ReadModalNavigationAdmission(modal_context.data(),modal) && modal.receivers.empty());
  set_modal(1,nullptr);assert(!ReadModalNavigationAdmission(modal_context.data(),modal) && modal.unavailable_reason=="modal_receiver_vector_missing");
  set_modal(1,modal_entries.data());modal_entries[0]=nullptr;
  assert(!ReadModalNavigationAdmission(modal_context.data(),modal) && modal.unavailable_reason=="modal_receiver_entry_unreadable_or_null");
  set_modal(1,reinterpret_cast<void *>(1));
  assert(!ReadModalNavigationAdmission(modal_context.data(),modal) && modal.unavailable_reason=="modal_receiver_entry_unreadable_or_null");
  set_modal(1,modal_entries.data());modal_entries[0]=reinterpret_cast<void *>(1);
  assert(!ReadModalNavigationAdmission(modal_context.data(),modal) && modal.unavailable_reason=="modal_receiver_flags_unreadable");
  assert(!ReadModalNavigationAdmission(nullptr,modal) && !modal.header_read && modal.unavailable_reason=="modal_receiver_header_unreadable");
  assert(!ReadModalNavigationAdmission(reinterpret_cast<void *>(1),modal) && !modal.header_read);
  IngameUiResultV1 modal_result{};modal_result.modal_admission=modal;
  auto modal_json=SerializeIngameUiResultV1(r,modal_result,3);
  assert(modal_json.find("\"receiver_count\":null")!=std::string::npos);
  set_modal(1,modal_entries.data());modal_entries[0]=hidden_receiver.data();
  assert(ReadModalNavigationAdmission(modal_context.data(),modal_result.modal_admission));
  modal_json=SerializeIngameUiResultV1(r,modal_result,3);
  assert(modal_json.find("\"receiver_count\":1")!=std::string::npos && modal_json.find("\"flags_d0\":184")!=std::string::npos);
  std::cout<<"offline original modal helper: 15 bounded/hidden/visible/mixed/null/unreadable cases and 2 actual serializer checks PASS; no game calls\n";
  // Real ReadProcessMemory over offline buffers exercises storage indexing and
  // full generation identity; a low-24-bit match alone must fail.
  auto *image=static_cast<unsigned char *>(VirtualAlloc(nullptr,kImageSize,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE));
  assert(image);const auto base=reinterpret_cast<std::uintptr_t>(image);
  std::array<unsigned char,64> storage{},object{};std::array<void *,8> slots{};
  void *storage_ptr=storage.data();void *slots_ptr=slots.data();void *object_ptr=object.data();std::uint32_t count=4,full=0x01000002;
  std::memcpy(image+kCharacterStorage,&storage_ptr,8);std::memcpy(storage.data()+0x20,&slots_ptr,8);
  std::memcpy(storage.data()+0x2C,&count,4);slots[5]=object_ptr;std::memcpy(object.data()+0x18,&full,4);
  void *resolved=nullptr;
  assert(Object(base,kCharacterStorage,full,0x18,resolved) && resolved==object_ptr);
  assert(!Object(base,kCharacterStorage,2,0x18,resolved));
  assert(!Object(base,kCharacterStorage,0x01000004,0x18,resolved));
  assert(!Object(base,kCharacterStorage,0xFFFFFFFF,0x18,resolved));
  // Exact COL type and its self-relative image binding, rather than window
  // runtime names, admit a cached window's native object identity.
  void *vt=image+0x1000;void *col=image+0x2000;std::uint32_t signature=1,type=static_cast<std::uint32_t>(kTypeDescriptors[0]),self=0x2000;
  std::memcpy(image+0x1000-8,&col,8);std::memcpy(image+0x2000,&signature,4);
  std::memcpy(image+0x2000+12,&type,4);std::memcpy(image+0x2000+20,&self,4);std::memcpy(object.data(),&vt,8);
  assert(TypedObject(base,object_ptr,kTypeDescriptors[0]));
  assert(!TypedObject(base,object_ptr,kTypeDescriptors[2]));
  self=0x2004;std::memcpy(image+0x2000+20,&self,4);assert(!TypedObject(base,object_ptr,kTypeDescriptors[0]));
  assert(!TypedObject(base,reinterpret_cast<void *>(1),kTypeDescriptors[0]));
  assert(VirtualFree(image,0,MEM_RELEASE));
  // Actual current producer helpers read only offline memory. No game API runs.
  auto *current_image=static_cast<unsigned char *>(VirtualAlloc(nullptr,UiExactImageSizeV1(GuiAbiRevisionV1::crozier12003),MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE));
  assert(current_image);ZhongguoScoreboardNativeEnvironmentV1 current_env{};
  current_env.module_base=reinterpret_cast<std::uintptr_t>(current_image);current_env.gui_abi_revision=GuiAbiRevisionV1::crozier12003;
  std::array<unsigned char,0x200> unit_buffer{},army_buffer{},window_buffer{};
  std::array<unsigned char,0x40> unit_storage{},army_storage{};
  std::array<void *,8> unit_slots{},army_slots{};
  void *up=unit_storage.data(),*ap=army_storage.data(),*us=unit_slots.data(),*as=army_slots.data();
  std::uint32_t four=4,public_zero=0,native_full=0x01000002;std::int32_t owner=29829;
  std::memcpy(current_image+kUiUnitStorage12003V1,&up,8);std::memcpy(current_image+kUiArmyStorage12003V1,&ap,8);
  std::memcpy(unit_storage.data()+0x20,&us,8);std::memcpy(unit_storage.data()+0x2C,&four,4);
  std::memcpy(army_storage.data()+0x20,&as,8);std::memcpy(army_storage.data()+0x2C,&four,4);
  unit_slots[1]=unit_buffer.data();army_slots[5]=army_buffer.data();
  std::memcpy(unit_buffer.data()+0x10,&public_zero,4);std::memcpy(unit_buffer.data()+0x174,&owner,4);
  std::memcpy(unit_buffer.data()+0x178,&native_full,4);std::memcpy(army_buffer.data()+0x10,&native_full,4);
  std::memcpy(army_buffer.data()+0x124,&public_zero,4);std::memcpy(window_buffer.data()+0xC8,&native_full,4);
  std::uint32_t read_public=99,read_native=99;void *current_unit=nullptr;
  assert(ReadArmyUiSubject(current_env,window_buffer.data(),read_public,read_native) && read_public==0 && read_native==native_full);
  assert(ResolvePlayerArmyUiSubject(current_env,0,owner,current_unit) && current_unit==unit_buffer.data());
  assert(!ResolvePlayerArmyUiSubject(current_env,0,owner+1,current_unit));
  assert(!ResolvePlayerArmyUiSubject(current_env,0x01000000,owner,current_unit));
  auto mismatch=native_full+1;std::memcpy(unit_buffer.data()+0x178,&mismatch,4);
  assert(!ReadArmyUiSubject(current_env,window_buffer.data(),read_public,read_native));
  assert(!ResolvePlayerArmyUiSubject(current_env,0,owner,current_unit));
  std::memcpy(unit_buffer.data()+0x178,&native_full,4);
  auto wrong_public=0x01000000;std::memcpy(army_buffer.data()+0x124,&wrong_public,4);
  assert(!ReadArmyUiSubject(current_env,window_buffer.data(),read_public,read_native));
  assert(!ResolvePlayerArmyUiSubject(current_env,0,owner,current_unit));
  std::memcpy(army_buffer.data()+0x124,&public_zero,4);
  auto invalid=0xFFFFFFFFU;std::memcpy(window_buffer.data()+0xC8,&invalid,4);
  std::memcpy(window_buffer.data()+0xF8,&native_full,4); // legacy field cannot salvage current read
  assert(!ReadArmyUiSubject(current_env,window_buffer.data(),read_public,read_native));
  // Run the actual current producer against an explicit offline synthetic image.
  // The only callable bytes jump to test-local cast/selection stubs; no CK3,
  // DLL, process discovery, SDK, desktop, or original game function executes.
  const auto install_jump=[&](std::uintptr_t rva,std::uintptr_t target) {
    std::array<unsigned char,14> jump{0xFF,0x25,0,0,0,0};std::memcpy(jump.data()+6,&target,8);
    std::memcpy(current_image+rva,jump.data(),jump.size());DWORD old_protection=0;
    assert(VirtualProtect(current_image+rva,jump.size(),PAGE_EXECUTE_READ,&old_protection));
    assert(FlushInstructionCache(GetCurrentProcess(),current_image+rva,jump.size()));
  };
  install_jump(xar::ck3_12003::kSuccessionRuntimeDynamicCastRva12003,reinterpret_cast<std::uintptr_t>(&FixtureArmyCast));
  install_jump(kUiSelectUnitRva12003V1,reinterpret_cast<std::uintptr_t>(&FixtureSelectUnit));
  std::array<unsigned char,0x100> root_object{},idler_object{},cast_object{};
  std::array<unsigned char,0x700> handler_buffer{};std::array<unsigned char,0x200> gui_root{};
  void *root_pointer=root_object.data(),*idler_pointer=idler_object.data(),*handler_pointer=handler_buffer.data();
  void *handler_vtable=current_image+xar::ck3_12003::kSuccessionHandlerPrimaryVtableRva12003;
  std::memcpy(current_image+xar::ck3_12003::kSuccessionIdlerRootSlotRva12003,&root_pointer,8);
  std::memcpy(root_object.data()+0x10,&idler_pointer,8);std::memcpy(cast_object.data()+0x88,&handler_pointer,8);
  std::memcpy(handler_buffer.data(),&handler_vtable,8);fixture_cast_object=cast_object.data();
  std::memcpy(window_buffer.data()+0xC8,&native_full,4); // restore full native subject
  set_modal(0,nullptr);fixture_gui_available=true;fixture_gui_reads=0;
  fixture_gui_first={modal_context.data(),reinterpret_cast<void *>(201)};fixture_gui_second=fixture_gui_first;
  MainThreadExecutionStampV1 current_stamp{};current_stamp.paused=true;current_stamp.date_raw=53146848;
  current_stamp.thread_id=GetCurrentThreadId();current_stamp.pump_epoch=17;
  xar::game::Snapshot current_snapshot{};current_snapshot.paused=true;current_snapshot.map_ready=true;
  current_snapshot.has_played_character=true;current_snapshot.played_character_id=owner;current_snapshot.date_raw=current_stamp.date_raw;
  current_env.exact_build_admitted=true;IngameUiResultV1 action_result{};
  const IngameUiRequestV1 select_zero{IngameUiOperationV1::select_army,IngameUiWindowKindV1::army,0};
  assert(ExecuteIngameUiNavigationV1(current_env,select_zero,current_snapshot,current_stamp,fixture_gui_first,action_result));
  assert(fixture_select_calls==1 && fixture_select_id==0 && fixture_select_handler==handler_pointer && fixture_select_replace);
  assert(action_result.available && action_result.dispatch_invoked && action_result.verification_pending);
  assert(action_result.status=="acknowledged_verification_pending" && !action_result.window_exists && !action_result.subject_id_available);
  assert(action_result.tree.scope_root_name=="army_window" && !action_result.tree.root_available && !action_result.owner_character_id_available);
  IngameUiResultV1 independent_result{};
  assert(ExecuteIngameUiNavigationV1(current_env,{IngameUiOperationV1::query,IngameUiWindowKindV1::army,0},current_snapshot,current_stamp,fixture_gui_first,independent_result));
  assert(!independent_result.available && !independent_result.dispatch_invoked && fixture_select_calls==1);
  // Independently populated synthetic panel permits a fresh query. Hidden or
  // stale GUI binding never becomes pixels or an action completion assertion.
  fixture_army_root_available=true;fixture_army_root=gui_root.data();void *gui_pointer=gui_root.data();
  void *army_window_pointer=window_buffer.data(),*army_window_vtable=current_image+0x1000,*army_window_col=current_image+0x2000;
  std::uint32_t army_window_signature=1,army_window_type=static_cast<std::uint32_t>(kUiArmyWindowTypeDescriptor12003V1),army_window_self=0x2000;
  std::memcpy(handler_buffer.data()+0xC8,&army_window_pointer,8);std::memcpy(window_buffer.data(),&army_window_vtable,8);
  std::memcpy(current_image+0x1000-8,&army_window_col,8);std::memcpy(current_image+0x2000,&army_window_signature,4);
  std::memcpy(current_image+0x2000+12,&army_window_type,4);std::memcpy(current_image+0x2000+20,&army_window_self,4);
  std::memcpy(window_buffer.data()+0x60,&gui_pointer,8);std::memcpy(window_buffer.data()+0xA0,&handler_pointer,8);
  std::memcpy(gui_root.data(),&army_window_vtable,8);
  assert(ExecuteIngameUiNavigationV1(current_env,{IngameUiOperationV1::query,IngameUiWindowKindV1::army,0},current_snapshot,current_stamp,fixture_gui_first,independent_result));
  assert(independent_result.available && independent_result.status=="observed" && !independent_result.dispatch_invoked && !independent_result.verification_pending);
  assert(independent_result.effective_visible && independent_result.subject_id_available && independent_result.current_subject_id==0 && independent_result.native_army_id==native_full);
  assert(independent_result.owner_character_id_available && independent_result.owner_character_id==static_cast<std::uint32_t>(owner));
  std::int32_t foreign_owner=owner+1;std::memcpy(unit_buffer.data()+0x174,&foreign_owner,4);
  assert(ExecuteIngameUiNavigationV1(current_env,{IngameUiOperationV1::query,IngameUiWindowKindV1::army,0},current_snapshot,current_stamp,fixture_gui_first,independent_result));
  assert(independent_result.available && independent_result.owner_character_id_available && independent_result.owner_character_id==static_cast<std::uint32_t>(foreign_owner));
  std::int32_t absent_owner=-1;std::memcpy(unit_buffer.data()+0x174,&absent_owner,4);
  assert(ExecuteIngameUiNavigationV1(current_env,{IngameUiOperationV1::query,IngameUiWindowKindV1::army,0},current_snapshot,current_stamp,fixture_gui_first,independent_result));
  assert(independent_result.available && independent_result.subject_id_available && !independent_result.owner_character_id_available);
  std::memcpy(unit_buffer.data()+0x174,&owner,4);
  gui_root[0xD0]=8;
  assert(ExecuteIngameUiNavigationV1(current_env,{IngameUiOperationV1::query,IngameUiWindowKindV1::army,0},current_snapshot,current_stamp,fixture_gui_first,independent_result));
  assert(independent_result.available && !independent_result.effective_visible && independent_result.subject_id_available);
  void *wrong_root=reinterpret_cast<void *>(999);std::memcpy(window_buffer.data()+0x60,&wrong_root,8);
  assert(ExecuteIngameUiNavigationV1(current_env,{IngameUiOperationV1::query,IngameUiWindowKindV1::army,0},current_snapshot,current_stamp,fixture_gui_first,independent_result));
  assert(!independent_result.available && independent_result.unavailable_reason=="native_army_window_gui_root_binding_failed");
  assert(ExecuteIngameUiNavigationV1(current_env,select_zero,current_snapshot,current_stamp,fixture_gui_first,action_result));
  assert(fixture_select_calls==2 && action_result.available && action_result.verification_pending && !action_result.window_exists);
  assert(!action_result.subject_id_available && !action_result.owner_character_id_available && !action_result.tree.root_available && action_result.tree.widget_count==0);
  fixture_army_root_available=false;fixture_select_calls=0;
  assert(VirtualFree(current_image,0,MEM_RELEASE));
  std::cout<<"current actual producer single-select/closed-window ACK/fresh independent query/public0/hidden/root-binding lifecycle PASS; test-local callable stubs only\n";
  IngameUiResultV1 current_result{};current_result.gui_abi_revision=GuiAbiRevisionV1::crozier12003;
  const auto current_json=SerializeIngameUiResultV1({IngameUiOperationV1::select_army,IngameUiWindowKindV1::army,0},current_result,3);
  assert(current_json.find("ck3-1.20.0.3-native-ingame-ui-v1")!=std::string::npos);
  assert(current_json.find("94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6")!=std::string::npos);
  assert(current_json.find("1.19.0.6")==std::string::npos);
  assert(current_json.find("\"owner_character_id_available\":false")!=std::string::npos && current_json.find("\"owner_character_id\":null")!=std::string::npos);
  current_result.owner_character_id_available=true;current_result.owner_character_id=29829;
  const auto owner_json=SerializeIngameUiResultV1({IngameUiOperationV1::query,IngameUiWindowKindV1::army,0},current_result,3);
  assert(owner_json.find("\"owner_character_id_available\":true")!=std::string::npos && owner_json.find("\"owner_character_id\":29829")!=std::string::npos);
  std::cout<<"current Army-only admission/public0/fullgeneration/owner/reciprocal/sentinel/legacy-offset/serializer helper cases PASS; no game calls\n";
  IngameUiResultV1 result{};ZhongguoScoreboardNativeEnvironmentV1 env{};
  xar::game::Snapshot snapshot{};MainThreadExecutionStampV1 stamp{};
  IngameUiGuiOwnerBindingV1 gui_binding{};
  assert(ExecuteIngameUiNavigationV1(env,r,snapshot,stamp,gui_binding,result) && !result.available);
  env.exact_build_admitted=true;env.module_base=1;env.offline_fixture_function_overrides=true;
  snapshot.paused=true;snapshot.map_ready=true;snapshot.has_played_character=true;
  stamp.paused=true;stamp.thread_id=GetCurrentThreadId();stamp.pump_epoch=1;
  assert(ExecuteIngameUiNavigationV1(env,r,snapshot,stamp,gui_binding,result) && !result.available);
  // Production's exact paused UI gateway, not a mirrored RNG predicate.
  MainThreadQueryMailboxV1 mailbox{};
  stamp.thread_id=GetCurrentThreadId();stamp.pump_epoch=17;stamp.paused=true;
  stamp.tls_initialized_flag_address=1;stamp.tls_initialized=1;
  stamp.tls_context=2;stamp.tls_main_thread_marker=1;stamp.jomini_state=3;stamp.game_state=4;
  mailbox.owner_thread_id.store(stamp.thread_id);
  mailbox.owner_verified_pump_epochs.store(2);mailbox.paused_owner_verified_pump_epochs.store(2);
  stamp.rng_wrapper=0;stamp.rng_state=0;stamp.rng_owner_thread_id=0;
  assert(IsIngameUiPausedOwnerStampV1(mailbox,stamp,GetCurrentThreadId()));
  stamp.rng_owner_thread_id=GetCurrentThreadId()+1;
  assert(IsIngameUiPausedOwnerStampV1(mailbox,stamp,GetCurrentThreadId()));
  assert(!IsIngameUiPausedOwnerStampV1(mailbox,stamp,GetCurrentThreadId()+1));
  auto bad=stamp;bad.thread_id=0;assert(!IsIngameUiPausedOwnerStampV1(mailbox,bad,GetCurrentThreadId()));
  bad=stamp;bad.tls_initialized=0;assert(!IsIngameUiPausedOwnerStampV1(mailbox,bad,GetCurrentThreadId()));
  bad=stamp;bad.tls_main_thread_marker=0;assert(!IsIngameUiPausedOwnerStampV1(mailbox,bad,GetCurrentThreadId()));
  bad=stamp;bad.tls_context=0;assert(!IsIngameUiPausedOwnerStampV1(mailbox,bad,GetCurrentThreadId()));
  bad=stamp;bad.tls_initialized_flag_address=0;assert(!IsIngameUiPausedOwnerStampV1(mailbox,bad,GetCurrentThreadId()));
  bad=stamp;bad.paused=false;assert(!IsIngameUiPausedOwnerStampV1(mailbox,bad,GetCurrentThreadId()));
  bad=stamp;bad.jomini_state=0;assert(!IsIngameUiPausedOwnerStampV1(mailbox,bad,GetCurrentThreadId()));
  bad=stamp;bad.game_state=0;assert(!IsIngameUiPausedOwnerStampV1(mailbox,bad,GetCurrentThreadId()));
  bad=stamp;bad.pump_epoch=0;assert(!IsIngameUiPausedOwnerStampV1(mailbox,bad,GetCurrentThreadId()));
  mailbox.owner_thread_id.store(GetCurrentThreadId()+1);
  assert(!IsIngameUiPausedOwnerStampV1(mailbox,stamp,GetCurrentThreadId()));
  mailbox.owner_thread_id.store(GetCurrentThreadId());mailbox.owner_verified_pump_epochs.store(1);
  assert(!IsIngameUiPausedOwnerStampV1(mailbox,stamp,GetCurrentThreadId()));
  mailbox.owner_verified_pump_epochs.store(2);mailbox.paused_owner_verified_pump_epochs.store(1);
  assert(!IsIngameUiPausedOwnerStampV1(mailbox,stamp,GetCurrentThreadId()));
  // Current original GUI object chain must match in both fresh reads. A stale
  // object/address, failed read, or transient replacement cannot become a gate.
  env.offline_fixture_function_overrides=false;
  fixture_gui_available=true;fixture_gui_reads=0;
  fixture_gui_first={reinterpret_cast<void *>(101),reinterpret_cast<void *>(201)};
  fixture_gui_second=fixture_gui_first;
  assert(ReadIngameUiGuiOwnerBindingV1(env,gui_binding) && gui_binding==fixture_gui_first && fixture_gui_reads==2);
  const auto pinned_gui=gui_binding;
  fixture_gui_reads=0;fixture_gui_second.owner=reinterpret_cast<void *>(202);
  assert(!ReadIngameUiGuiOwnerBindingV1(env,gui_binding) && !gui_binding.context && !gui_binding.owner);
  fixture_gui_reads=0;fixture_gui_second=fixture_gui_first;fixture_gui_second.context=reinterpret_cast<void *>(102);
  assert(!ReadIngameUiGuiOwnerBindingV1(env,gui_binding));
  fixture_gui_reads=0;fixture_gui_available=false;
  assert(!ReadIngameUiGuiOwnerBindingV1(env,gui_binding));
  fixture_gui_available=true;fixture_gui_reads=0;fixture_gui_first={nullptr,reinterpret_cast<void *>(201)};fixture_gui_second=fixture_gui_first;
  assert(!ReadIngameUiGuiOwnerBindingV1(env,gui_binding));
  fixture_gui_reads=0;fixture_gui_first={reinterpret_cast<void *>(102),reinterpret_cast<void *>(202)};fixture_gui_second=fixture_gui_first;
  assert(ReadIngameUiGuiOwnerBindingV1(env,gui_binding) && gui_binding!=pinned_gui); // post-call replacement is rejected by the frontend exact equality
  r={IngameUiOperationV1::open_character,IngameUiWindowKindV1::character,33437};
  assert(ValidateIngameUiRequestV1(r));
  fixture_gui_reads=0;snapshot.date_raw=53146848;snapshot.played_character_id=29829;stamp.date_raw=snapshot.date_raw;
  assert(ExecuteIngameUiNavigationV1(env,r,snapshot,stamp,pinned_gui,result) && !result.available);
  assert(result.unavailable_reason=="current_gui_owner_binding_changed_before_navigation");
  assert(result.date_raw==53146848 && result.thread_id==GetCurrentThreadId());
  const auto serialized=SerializeIngameUiResultV1(r,result,3);
  assert(serialized.find("\"rng_owner_is_ui_admission_gate\":false")!=std::string::npos);
  std::cout<<"offline parser/full-generation/RTTI/application-owner/RNG0/GUI-double-read/admission negative cases PASS; no game calls\n";
}
