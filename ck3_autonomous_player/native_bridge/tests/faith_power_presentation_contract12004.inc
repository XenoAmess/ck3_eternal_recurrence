// Included by the existing navigation fixture; no engine/desktop/native calls.
void FaithPowerPresentationContractFixture12004() {
  using namespace xar::ck3_11906;
  IngameUiRequestV1 r{};
  assert(ParseIngameUiRequestV1(R"({"window_kind":"faith","subject_id":0,"presentation_tab":""})",true,r));
  assert(r.presentation_requested&&r.subject_id==0);
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
 assert(VirtualFree(image,0,MEM_RELEASE));
 std::cout<<"production building direct-row reader/model/type/fallback/preparation/layout/pin fixture PASS; no engine/provider calls\n";
}
