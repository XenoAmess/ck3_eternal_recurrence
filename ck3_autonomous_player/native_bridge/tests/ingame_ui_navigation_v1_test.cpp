// Offline test only. No CK3 process, desktop, or native game function executes.
#if defined(NDEBUG)
#undef NDEBUG
#endif
#include "../src/ingame_ui_navigation_v1.cpp"
#include <cassert>
#include <iostream>

namespace xar::ck3_11906 {
// Link-only GUI stubs; the negative admission cases never reach these.
bool ResolveNamedGuiWidgetV1(const ZhongguoScoreboardNativeEnvironmentV1 &,const ZhongguoScoreboardAccessV1 &,std::string_view,std::string_view,void *&,void *&) noexcept {return false;}
bool ReadGuiWidgetRuntimeV1(const ZhongguoScoreboardAccessV1 &,void *,std::string &,void *&,bool &,bool &) noexcept {return false;}
bool InspectNamedGuiSubtreeV1(const ZhongguoScoreboardAccessV1 &,std::uintptr_t,void *,std::string_view,NamedGuiTreeInspectionV1 &) noexcept {return false;}
bool ResolveZhongguoScoreboardNativeGuiContextAndOwnerV1(const ZhongguoScoreboardNativeEnvironmentV1 &,const ZhongguoScoreboardAccessV1 &,void *&,void *&) noexcept {return false;}
}
int main() {
  using namespace xar::ck3_11906;
  IngameUiRequestV1 r{};
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
  IngameUiResultV1 result{};ZhongguoScoreboardNativeEnvironmentV1 env{};
  xar::game::Snapshot snapshot{};MainThreadExecutionStampV1 stamp{};
  assert(ExecuteIngameUiNavigationV1(env,r,snapshot,stamp,result) && !result.available);
  env.exact_build_admitted=true;env.module_base=1;env.offline_fixture_function_overrides=true;
  snapshot.paused=true;snapshot.map_ready=true;snapshot.has_played_character=true;
  stamp.paused=true;stamp.thread_id=GetCurrentThreadId();stamp.pump_epoch=1;
  assert(ExecuteIngameUiNavigationV1(env,r,snapshot,stamp,result) && !result.available);
  std::cout<<"offline parser/full-generation/RTTI/admission negative cases PASS; no game calls\n";
}
