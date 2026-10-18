// Included by the existing navigation fixture; no engine/desktop/native calls.
void FaithPowerPresentationContractFixture12004() {
  using namespace xar::ck3_11906;
  IngameUiRequestV1 r{};
  assert(ParseIngameUiRequestV1(R"({"window_kind":"faith","subject_id":0,"presentation_tab":""})",true,r));
  assert(r.presentation_requested&&r.subject_id==0);
  // Preserve the original legal empty marker above; reject non-string, duplicate,
  // nested and escaped selectors rather than changing shared string semantics.
  IngameUiRequestV1 rejected{};
  for(const auto malformed:std::array<std::string_view,6>{{
      R"({"window_kind":"faith","subject_id":0,"presentation_tab":null})",
      R"({"window_kind":"faith","subject_id":0,"presentation_tab":0})",
      R"({"window_kind":"faith","subject_id":0,"presentation_tab":"","presentation_tab":"beliefs"})",
      R"({"window_kind":"faith","subject_id":0,"presentation_tab":"beliefs","presentation_tab":""})",
      R"({"window_kind":"faith","subject_id":0,"nested":{"presentation_tab":""}})",
      R"({"window_kind":"faith","subject_id":0,"presentation_tab":"holy\u005fsites"})"}})
    assert(!ParseIngameUiRequestV1(malformed,true,rejected));

  assert(IsIngameUiRequestSupportedV1(GuiAbiRevisionV1::crozier12004,r)==PresentationUiEnabled12004());
  assert(!IsIngameUiRequestSupportedV1(GuiAbiRevisionV1::crozier12003,r));
  IngameUiResultV1 failed{};failed.unavailable_reason="fixture_owner_not_admitted";
  const auto early=SerializeIngameUiResultV1(r,failed,7);
  assert(early.find("\"presentation_ui\":{")!=std::string::npos);
  assert(early.find("\"unavailable_reason\":\"fixture_owner_not_admitted\"")!=std::string::npos);
  assert(early.find("\"source_bound\":false")!=std::string::npos);
  failed.presentation_ui.source_bound=true;failed.presentation_ui.cache_complete=true;
  failed.presentation_ui.hover_source_matches=true;failed.presentation_ui.cache_texts.push_back({"x","stale","x"});
  const auto invalidated=SerializeIngameUiResultV1(r,failed,7);
  assert(invalidated.find("\"source_bound\":false")!=std::string::npos&&invalidated.find("\"cache_complete\":false")!=std::string::npos);
  assert(invalidated.find("\"cache_texts\":[]")!=std::string::npos);
  assert(ParseIngameUiRequestV1(R"({"window_kind":"faith","subject_id":0})",true,r));
  assert(!r.presentation_requested&&SerializeIngameUiResultV1(r,failed,7).find("presentation_ui")==std::string::npos);
  assert(!ParseIngameUiRequestV1(R"({"window_kind":"holding","subject_id":0,"operation":"open_holding"})",false,r));
  assert(!ParseIngameUiRequestV1(R"({"window_kind":"holding","subject_id":1,"operation":"construct"})",false,r));
  assert(!ParseIngameUiRequestV1(R"({"window_kind":"holding","subject_id":1,"operation":"show_building_details","presentation_target":"holding_building"})",false,r));
  assert(!ParseIngameUiRequestV1(R"({"window_kind":"faith","subject_id":0,"operation":"hover_presentation_tooltip","presentation_target":"rite_core_tenet_slot"})",false,r));
  assert(!ParseIngameUiRequestV1(R"({"window_kind":"faith","subject_id":0,"presentation_tab":"rites"})",true,r));
  assert(!ParseIngameUiRequestV1(R"({"window_kind":"personal_beliefs","subject_id":1,"presentation_target":"faith_core_tenet"})",true,r));
  const std::array<std::pair<std::string_view,std::uint32_t>,7>operations{{
    {R"({"window_kind":"holding","subject_id":1,"operation":"open_holding"})",200},
    {R"({"window_kind":"personal_beliefs","subject_id":1,"operation":"open_personal_beliefs"})",201},
    {R"({"window_kind":"faith","subject_id":0,"operation":"select_presentation_tab","presentation_tab":"holy_sites"})",202},
    {R"({"window_kind":"rite_creation","subject_id":0,"operation":"open_rite_core_picker","presentation_index":2})",203},
    {R"({"window_kind":"faith","subject_id":0,"operation":"hover_presentation_tooltip","presentation_target":"faith_core_tenet"})",204},
    {R"({"window_kind":"faith","subject_id":0,"operation":"leave_presentation_tooltip","presentation_target":"faith_core_tenet","presentation_receipt":"0123456789abcdef0123456789abcdef"})",205},
    {R"({"window_kind":"holding","subject_id":1,"operation":"show_building_details","presentation_target":"holding_building_preview"})",206}}};
  for(const auto&[json,op]:operations){assert(ParseIngameUiRequestV1(json,false,r));assert(static_cast<std::uint32_t>(r.operation)==op);}
  PresentationPanel12004 p{};p.tree.root_available=true;
  const auto row=[&](std::string path,std::string name,bool visible=true,bool enabled=true){
    NamedGuiWidgetInspectionV1 x{};x.child_path=path;x.runtime_name=name;x.effective_visible=visible;x.enabled=enabled;p.tree.widgets.push_back(x);p.tree.widget_count=p.tree.widgets.size();};
  r={};r.window_kind=IngameUiWindowKindV1::faith;r.presentation_requested=true;
  row("0","tab_beliefs");row("0/0","doctrines_grid_core_tenets");row("0/0/0","");row("0/0/0/0","doctrine_group_bg",true,false);
  row("0/0/0/1","doctrine_group_icon"); // Core icon is not a separate doctrine carrier.
  row("1","unrelated_popup");row("1/0","doctrine_group_bg");row("2","tab_holy_sites",false);
  FaithPowerPresentationObservationV1 v{};std::vector<PresentationSourceRow12004>sources;
  assert(PresentationCensus12004(r,p,sources,v)&&v.targets.size()==1&&v.targets[0].kind=="faith_core_tenet");
  assert(PresentationActiveTab12004(r,p)==std::optional<std::string>("beliefs"));
  p.tree.widgets.back().effective_visible=true;assert(!PresentationActiveTab12004(r,p));
  p={};r.window_kind=IngameUiWindowKindV1::rite_creation;
  row("0","left_side");row("0/0","tenets_grid");row("0/0/0","");row("0/0/0/0","");row("0/0/0/0/0","");row("0/0/0/0/0/0","tenet_name");
  row("1","tenet_selection");row("1/0","");row("1/0/0","");row("1/0/0/0","");row("1/0/0/0/0","tenet_name");
  assert(PresentationCensus12004(r,p,sources,v)&&v.targets.size()==2);
  assert(v.targets[0].kind=="rite_core_tenet_slot"&&v.targets[1].kind=="rite_core_tenet_choice");
  assert(v.targets[0].index==0&&v.targets[1].index==0);
  assert(PresentationCoreClickPath12004(p,0)==std::optional<std::string>("0/0/0"));
  assert(!PresentationCoreClickPath12004(p,1));
  p={};r.window_kind=IngameUiWindowKindV1::personal_beliefs;
  row("0","personal_tenets_tutorial_uses_this");row("0/0","");
  assert(PresentationCensus12004(r,p,sources,v)&&v.targets.empty());
  assert(ParseIngameUiRequestV1(R"({"window_kind":"holding","subject_id":1,"operation":"open_building_track","presentation_target":"holding_building","presentation_index":0})",false,r));
  assert(static_cast<std::uint32_t>(r.operation)==207);
  assert(!ParseIngameUiRequestV1(R"({"window_kind":"holding","subject_id":1,"operation":"open_building_track","presentation_target":"holding_building_preview"})",false,r));
  // Anonymous personal carriers remain unknown; never reuse Faith's name.
  std::cout<<"finite presentation parser/zero/legacy/earlyfailure/response-only core census/source-neighborhood policy PASS; no engine or pixels\n";
}

// Included only in the existing navigation fixture. No engine getter executes.
void*position_fixture_tls12004=nullptr;
void*__fastcall PresentationPositionFixtureTls12004() noexcept{return position_fixture_tls12004;}
void FaithPowerPresentationPositionFrameFixture12004(unsigned char*image,std::uintptr_t base){
 using namespace xar::ck3_11906;
 const auto put=[](void*p,std::size_t o,const auto&v){std::memcpy(static_cast<unsigned char*>(p)+o,&v,sizeof(v));};
 std::array<unsigned char,0x30>jomini{},game{},tls{};
 void*jomini_ptr=jomini.data(),*game_ptr=game.data();position_fixture_tls12004=tls.data();
 std::uint8_t initialized=1,yes=1,no=0;std::int32_t date=53144328;std::uint32_t actor=15893;
 put(jomini.data(),kJominiPausedOffset,yes);put(game.data(),kGameStateDateRawOffset,date);
 put(tls.data(),kMainThreadTlsMarkerOffset,yes);put(image,0x54DBC00,actor);
 MainThreadQueryMailboxV1 mailbox{};mailbox.module_base=base;mailbox.owner_thread_id.store(GetCurrentThreadId());
 mailbox.jomini_state_slot=reinterpret_cast<std::uintptr_t>(&jomini_ptr);
 mailbox.game_state_slot=reinterpret_cast<std::uintptr_t>(&game_ptr);
 mailbox.tls_initialized_flag=reinterpret_cast<std::uintptr_t>(&initialized);
 mailbox.tls_context_getter=&PresentationPositionFixtureTls12004;
 auto*saved=presentation_position_mailbox12004;presentation_position_mailbox12004=&mailbox;
 ZhongguoScoreboardNativeEnvironmentV1 env{};env.module_base=base;
 PresentationPositionFrame12004 first{},next{};
 assert(ReadPresentationPositionFrame12004(env,first)&&first.actor==actor&&first.date==date&&first.paused==1);
 put(jomini.data(),kJominiPausedOffset,no);assert(!ReadPresentationPositionFrame12004(env,next));put(jomini.data(),kJominiPausedOffset,yes);
 put(tls.data(),kMainThreadTlsMarkerOffset,no);assert(!ReadPresentationPositionFrame12004(env,next));put(tls.data(),kMainThreadTlsMarkerOffset,yes);
 mailbox.owner_thread_id.store(0);assert(!ReadPresentationPositionFrame12004(env,next));mailbox.owner_thread_id.store(GetCurrentThreadId());
 mailbox.stop_requested.store(true);assert(!ReadPresentationPositionFrame12004(env,next));mailbox.stop_requested.store(false);
 ++date;put(game.data(),kGameStateDateRawOffset,date);assert(ReadPresentationPositionFrame12004(env,next)&&next!=first);
 initialized=0;assert(!ReadPresentationPositionFrame12004(env,next));initialized=1;
 const auto old_connection=presentation_position_connection12004.load();
 const auto old_thread=presentation_position_thread12004.load();
 auto old_lease=std::move(presentation_position_lease12004);
 presentation_position_lease12004={};presentation_position_lease12004.active=true;
 presentation_position_lease12004.nonce="11111111111111111111111111111111";presentation_position_lease12004.updates=1;
 std::string stale_reason;
 assert(!PresentationTooltipPositionReceipt12004("22222222222222222222222222222222",stale_reason)&&
     presentation_position_lease12004.active&&presentation_position_lease12004.nonce=="11111111111111111111111111111111");
 presentation_position_lease12004.generation=7;presentation_position_lease12004.binding.gui.context=jomini.data();
 presentation_position_thread12004.store(GetCurrentThreadId());presentation_position_connection12004.store(0);
 std::uint64_t point=123;
 assert(!PresentationTooltipPositionOverride12004(jomini.data(),point)&&point==123&&!presentation_position_lease12004.active);
 assert(std::string_view(presentation_position_lease12004.failure)=="presentation_tooltip_position_connection_closed_or_changed");
 presentation_position_lease12004=std::move(old_lease);presentation_position_thread12004.store(old_thread);
 presentation_position_connection12004.store(old_connection);
 presentation_position_mailbox12004=saved;position_fixture_tls12004=nullptr;
 std::cout<<"production presentation frame reader paused/TLS/date/actor/owner/stop checks PASS\n";
}

// Offline production-reader fixture; native functions and providers never run.
void FaithPowerBuildingReceiverFixture12004(){
 using namespace xar::ck3_11906;
 auto*image=static_cast<unsigned char*>(VirtualAlloc(nullptr,0x61C5000,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE));assert(image);
 const auto put=[](void*p,std::size_t o,const auto&v){std::memcpy(static_cast<unsigned char*>(p)+o,&v,sizeof(v));};
 const auto digit=[](char c){return c<='9'?c-'0':c-'a'+10;};
 for(const auto&p:kPresentationReceiverPins12004)for(std::size_t i=0;i<std::strlen(p.hex)/2;++i)image[p.rva+i]=static_cast<unsigned char>((digit(p.hex[2*i])<<4)|digit(p.hex[2*i+1]));
 std::array<unsigned char,0x1000>view{},root{},widget{};
 std::array<unsigned char,0x200>gui_context{},data_context{},definition{};
 std::array<unsigned char,0x100>callback{},group{},entry{},registry{};
 std::array<unsigned char,3*0x130>types{};std::array<unsigned char,0x28>slot{};std::array<unsigned char,0x18>potential{};
 std::uint32_t declaration=1;std::int32_t index=0,one=1,three=3;std::uint8_t ready=1;std::int8_t mode1=1;
 void*rootp=root.data(),*widgetp=widget.data(),*guip=gui_context.data(),*datap=data_context.data(),*defp=definition.data();
 void*cbp=callback.data(),*cbvt=image+0x4300000,*groupp=group.data(),*entryp=entry.data(),*registryp=registry.data(),*typesp=types.data();
 void*building=image+0x1800000,*viewp=view.data(),*rowp=potential.data();std::array<void*,1>children{widgetp},rows{rowp};
 void*childp=children.data(),*rowsp=rows.data(),*declp=&declaration,*indexp=&index;
 const auto base=reinterpret_cast<std::uintptr_t>(image);
 // Deliberately distinct Jomini and lookup owners: real factories use the
 // former in window+98; named GUI lookup uses the latter independently.
 std::array<unsigned char,0x20>jomini{};std::array<unsigned char,0x90>gfx{};
 std::array<unsigned char,0x48>handler{};std::array<unsigned char,0xA0>native_window{};
 void*jomini_owner=jomini.data(),*gfxp=gfx.data(),*handlerp=handler.data(),*nativep=native_window.data();
 put(image,ck3_12004::kUiIdlerRootSlotRva12004V1,jomini_owner);put(jomini_owner,0x10,gfxp);put(gfxp,0x88,handlerp);
 put(handlerp,0x40,jomini_owner);put(nativep,0x98,jomini_owner);
 ZhongguoScoreboardNativeEnvironmentV1 owner_env{};owner_env.module_base=base;void*actual_owner=nullptr;
 assert(jomini_owner!=guip&&ReadPresentationOuterOwner12004(owner_env,handlerp,nativep,actual_owner)&&actual_owner==jomini_owner);
 put(nativep,0x98,guip);assert(!ReadPresentationOuterOwner12004(owner_env,handlerp,nativep,actual_owner));put(nativep,0x98,jomini_owner);
 put(handlerp,0x40,guip);assert(!ReadPresentationOuterOwner12004(owner_env,handlerp,nativep,actual_owner));put(handlerp,0x40,jomini_owner);
 put(gfxp,0x88,guip);assert(!ReadPresentationOuterOwner12004(owner_env,handlerp,nativep,actual_owner));put(gfxp,0x88,handlerp);
 assert(ReadPresentationOuterOwner12004(owner_env,handlerp,nullptr,actual_owner)&&actual_owner==jomini_owner);

 put(image,0x5D56864,declaration);std::uint32_t secondtype=2;put(image,0x5D20B98,secondtype);put(image,0x5C6A9C0,registryp);put(registryp,0x20,typesp);put(registryp,0x2C,three);
 void*widgetvt=image+0x4310000;put(rootp,0,widgetvt);put(widgetp,0,widgetvt);put(rootp,0xD8,guip);put(widgetp,0xD8,guip);put(rootp,0xF0,childp);put(rootp,0xFC,one);put(widgetp,0xE8,rootp);
 put(widgetp,0x3F8,groupp);put(widgetp,0x404,one);put(groupp,0x40,cbp);put(cbp,0,cbvt);
 void*fn=image+0x3AA30E0;put(cbvt,0x10,fn);fn=image+0x3A9F960;put(cbp,8,fn);std::int32_t kind3=3;put(cbp,0x44,kind3);fn=image+0x12B3260;put(cbp,0x48,fn);put(cbp,0x58,declaration);
 put(cbp,0xF0,datap);put(cbp,0xA8,declp);put(cbp,0xB4,one);put(cbp,0xC0,indexp);put(cbp,0xCC,one);put(datap,0xE0,defp);put(defp,0x115,ready);put(defp,0x90,entryp);put(defp,0x9C,one);
 put(entryp,0,rowp);put(entryp,0x40,mode1);put(entryp,0x48,declaration);put(entryp,0x4C,ready);
 put(viewp,0xE8,rowsp);put(viewp,0xF0,one);put(viewp,0xF4,one);put(rowp,0,viewp);put(rowp,8,building);
 std::uint32_t magic=0x4744624F;put(building,0x38,magic);std::uint64_t size=9,capacity=15;put(building,0x28,size);put(building,0x30,capacity);std::memcpy(static_cast<unsigned char*>(building)+0x18,"temple_01",10);
 ZhongguoScoreboardNativeEnvironmentV1 e{};e.module_base=base;e.gui_abi_revision=GuiAbiRevisionV1::crozier12004;
 IngameUiGuiOwnerBindingV1 gui{guip,nullptr};PresentationPanel12004 panel{};panel.window=viewp;
 fixture_army_root_available=true;fixture_tooltip_tree=true;fixture_army_root=rootp;fixture_supplies=widgetp;
 PresentationBuildingReceiver12004 observed{};std::string why;
 const auto read=[&](bool ispotential){return ReadPresentationBuildingReceiver12004(e,gui,panel,rootp,"0",ispotential,observed,why);};
 assert(read(true)&&observed.row==rowp&&observed.building_key=="temple_01");
 std::int8_t unsupported=3;put(entryp,0x40,unsupported);assert(!read(true));put(entryp,0x40,mode1);
 put(cbp,0x1C,one);assert(!read(true));std::int32_t zero=0;put(cbp,0x1C,zero);
 void*wrong=rootp;put(rowp,0,wrong);assert(!read(true));put(rowp,0,viewp);
 rows[0]=widgetp;assert(!read(true));rows[0]=rowp;
 void*converter=image+0x100;put(types.data()+0x130,0xE8,converter);assert(read(true));put(types.data()+0x130,0xF0,converter);assert(!read(true));void*nil=nullptr;put(types.data()+0x130,0xE8,nil);put(types.data()+0x130,0xF0,nil);
 // Installed-row ownership is array membership; row[0] is its group, not view.
 rowp=slot.data();void*owned=slot.data(),*groupowner=static_cast<unsigned char*>(viewp)+0x100;
 put(viewp,0x100,owned);put(viewp,0x108,one);put(viewp,0x10C,one);put(rowp,0,groupowner);put(rowp,8,building);put(entryp,0,rowp);
 declaration=2;put(entryp,0x48,declaration);put(cbp,0x58,declaration);fn=image+0x12B2610;put(cbp,0x48,fn);
 assert(read(false)&&observed.row_owner_raw==groupowner&&observed.row_owner_raw!=viewp);
 put(entryp,0,widgetp);assert(!read(false));put(entryp,0,rowp);
 auto&rpin=kPresentationReceiverPins12004[0];const auto original=image[rpin.rva];image[rpin.rva]^=1;assert(!read(false));image[rpin.rva]=original;
 fixture_army_root_available=false;fixture_tooltip_tree=false;fixture_army_root=nullptr;fixture_supplies=nullptr;
 FaithPowerPresentationPositionFrameFixture12004(image,base);
 assert(VirtualFree(image,0,MEM_RELEASE));
 std::cout<<"production building direct-row reader/model/type/fallback/preparation/layout/pin fixture PASS; no engine/provider calls\n";
}

namespace {
using namespace xar::ck3_11906;
// PREPARED ONLY: no compilation or execution has occurred in this lane.
// Place these functions in the existing fixture private namespace AFTER its
// verbatim production relay inc. No second include or definition of real Override.
// The fixture entry requires BOTH bool checks; add <intrin.h> in the host TU.
bool PreparedPtpReject12004(void *, std::uint64_t &packed) noexcept {
  packed = 0x4120000040E00000ULL; return false;
}
bool PreparedPtpAccept12004(void *, std::uint64_t &packed) noexcept {
  packed = 0x4120000040E00000ULL; return true;
}
std::uint64_t PreparedPtpReadU6412004(const PtpStub12004 &bytes, std::size_t at) {
  std::uint64_t value = 0;
  if (at + sizeof(value) > bytes.size()) return 0;
  std::memcpy(&value, bytes.data() + at, sizeof(value)); return value;
}
bool PreparedPtpProductionBuilderChecks12004() {
  constexpr std::uint64_t original = 0x40A0000040200000ULL;
  constexpr std::uint64_t replacement = 0x4120000040E00000ULL;
  auto *gui = reinterpret_cast<void *>(0x12340ULL);
  if (PtpApplyWith12004<&PreparedPtpAccept12004>(gui, original, 0) != original ||
      PtpApplyWith12004<&PreparedPtpAccept12004>(nullptr, original, 2) != original ||
      PtpApplyWith12004<&PreparedPtpReject12004>(gui, original, 2) != original ||
      PtpApplyWith12004<&PreparedPtpAccept12004>(gui, original, 2) != replacement ||
      PtpApplyWith12004<&PreparedPtpAccept12004>(gui, original, 3) != original) return false;
  if (sizeof(kPtpDispatcherHex12004) != 785 || sizeof(kPtpCalleePrefixHex12004) != 103 ||
      PtpShaMatches12004("") || !PtpShaMatches12004(kPtpExeSha12004) ||
      InstallPresentationTooltipPositionHooks12004(1, kPtpExeSha12004, false)) return false;
  std::int32_t relative = 0;
  if (!PtpRelative12004(0x17FFFFFFFULL, 0x100000000ULL, relative) || relative != 0x7FFFFFFF ||
      PtpRelative12004(0x180000000ULL, 0x100000000ULL, relative) ||
      !PtpRelative12004(0x80000000ULL, 0x100000000ULL, relative) ||
      relative != (std::numeric_limits<std::int32_t>::min)() ||
      PtpRelative12004(0x7FFFFFFFULL, 0x100000000ULL, relative)) return false;
  for (std::size_t index = 0; index != 4; ++index) {
    PtpSlot12004 slot{};
    slot.native = 0x140000000ULL + kPtpCallees12004[index];
    slot.continuation = 0x140000000ULL + kPtpCalls12004[index] + 5;
    PtpStub12004 actual{};
    if (PtpBuildStub12004(slot, actual) != 160) return false;
    const std::array<std::uint8_t, 12> saves{
      0x9C,0x50,0x51,0x52,0x41,0x50,0x41,0x51,0x41,0x52,0x41,0x53};
    if (std::memcmp(actual.data(), saves.data(), saves.size())) return false;
    const std::array<std::uint8_t, 16> arguments{
      0x48,0x8B,0x94,0x24,0xA0,0,0,0,0x48,0x8B,0x8C,0x24,0xA8,0,0,0};
    if (std::memcmp(actual.data() + 55, arguments.data(), arguments.size())) return false;
    const std::array<std::uint8_t, 8> replace{0x48,0x89,0x84,0x24,0xA0,0,0,0};
    if (std::memcmp(actual.data() + 83, replace.data(), replace.size())) return false;
    for (std::uint8_t reg = 0; reg != 6; ++reg) {
      const std::array<std::uint8_t, 6> save{
        0xF3,0x0F,0x7F,static_cast<std::uint8_t>(0x44 + 8 * reg),0x24,
        static_cast<std::uint8_t>(0x20 + 0x10 * reg)};
      auto restore = save; restore[2] = 0x6F;
      if (std::memcmp(actual.data() + 19 + reg * 6, save.data(), 6) ||
          std::memcmp(actual.data() + 91 + reg * 6, restore.data(), 6)) return false;
    }
    const std::array<std::uint8_t, 6> native_tail{0xFF,0x25,0,0,0,0};
    if (std::memcmp(actual.data() + 146, native_tail.data(), native_tail.size()) ||
        PreparedPtpReadU6412004(actual, 152) != slot.native) return false;
    for (std::size_t at = 160; at != actual.size(); ++at) if (actual[at] != 0x90) return false;
  }
  return true;
}

// Host-only original-callee sink. No CK3 object, original engine call, main-module
// patch or fake business result. Six slots record count, opaque, GUI, XY, dt bits, actual return address.
std::array<std::uint64_t, 6> &PreparedPtpAbiState12004() {
  static std::array<std::uint64_t, 6> state{}; return state;
}
__declspec(noinline) std::uint64_t __fastcall PreparedPtpNativeSink12004(
    std::uintptr_t opaque, void *gui, std::uint64_t packed, float dt) noexcept {
  auto &state = PreparedPtpAbiState12004();
  ++state[0]; state[1] = opaque; state[2] = reinterpret_cast<std::uintptr_t>(gui); state[3] = packed;
  std::uint32_t dt_bits = 0; std::memcpy(&dt_bits, &dt, sizeof(dt)); state[4] = dt_bits;
  state[5] = reinterpret_cast<std::uintptr_t>(_ReturnAddress());
  return 0xBADC0FFEE1234567ULL;
}
template<bool Accept>
std::uint64_t PreparedPtpAbiApply12004(void *gui, std::uint64_t packed) noexcept {
  if constexpr (Accept) return PtpApplyWith12004<&PreparedPtpAccept12004>(gui, packed, 2);
  else return PtpApplyWith12004<&PreparedPtpReject12004>(gui, packed, 2);
}
template<bool Accept>
bool PreparedPtpExecuteAbiCase12004() {
  auto *memory = VirtualAlloc(nullptr, 4096, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
  if (!memory) return false;
  const auto base = reinterpret_cast<std::uintptr_t>(memory);
  // Entry RSP=8 mod16; sub28 makes original CALL-boundary RSP=0 mod16.
  // Real E8 to same builder; native tail-JMP returns directly to host+9.
  std::array<std::uint8_t, 14> host{
    0x48,0x83,0xEC,0x28,0xE8,0,0,0,0,0x48,0x83,0xC4,0x28,0xC3};
  PtpSlot12004 slot{};
  slot.call = base + 4; slot.continuation = base + 9; slot.stub = base + 16;
  slot.native = reinterpret_cast<std::uintptr_t>(&PreparedPtpNativeSink12004);
  PtpStub12004 bytes{};
  std::int32_t relative = 0;
  bool okay = PtpBuildStub12004<&PreparedPtpAbiApply12004<Accept>>(slot, bytes) == 160 &&
      PtpRelative12004(slot.stub, slot.continuation, relative);
  if (okay) {
    std::memcpy(host.data() + 5, &relative, sizeof(relative));
    okay = PtpCopyTo12004(base, host.data(), host.size()) &&
        PtpCopyTo12004(slot.stub, bytes.data(), bytes.size());
  }
  DWORD previous = 0;
  okay = okay && VirtualProtect(memory, 4096, PAGE_EXECUTE_READ, &previous) &&
      previous == PAGE_READWRITE && FlushInstructionCache(GetCurrentProcess(), memory, 4096);
  if (okay) {
    auto &state = PreparedPtpAbiState12004(); state.fill(0);
    constexpr std::uintptr_t opaque = 0xDEAD0000FEED5678ULL;
    constexpr std::uintptr_t gui = 0x12340ULL;
    constexpr std::uint64_t original = 0x40A0000040200000ULL;
    constexpr std::uint64_t replacement = 0x4120000040E00000ULL;
    constexpr std::uint32_t dt_bits = 0x3EAAAAABU;
    float dt = 0; std::memcpy(&dt, &dt_bits, sizeof(dt));
    using Host = std::uint64_t (__fastcall *)(std::uintptr_t, void *, std::uint64_t, float);
    const auto result = reinterpret_cast<Host>(memory)(opaque, reinterpret_cast<void *>(gui), original, dt);
    okay = result == 0xBADC0FFEE1234567ULL && state[0] == 1 && state[1] == opaque &&
        state[2] == gui && state[3] == (Accept ? replacement : original) && state[4] == dt_bits &&
        state[5] == slot.continuation;
  }
  const bool released = VirtualFree(memory, 0, MEM_RELEASE) != FALSE;
  return okay && released;
}
bool PreparedPtpExecutedStubAbiChecks12004() {
  // Both execute the same production byte-emitter with compile-time host callback.
  // No mutation of production phase/receipt or runtime callback injection exists.
  const bool pass_false = PreparedPtpExecuteAbiCase12004<false>();
  const bool pass_true = PreparedPtpExecuteAbiCase12004<true>();
  return pass_false && pass_true;
}
// Installer/rollback OS failure injection, source-linked compile, real receipt,
// current original factory/source/stack/text postquery remain separate checks.

}
