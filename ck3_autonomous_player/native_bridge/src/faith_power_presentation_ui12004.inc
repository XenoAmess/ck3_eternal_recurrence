// Exact 1.20.0.4 finite presentation adapter, inside navigation's private namespace.
// Never accepts caller widget paths, names, native pointers, view enums or RVAs.
struct PresentationPanel12004 {
  void *window=nullptr,*root=nullptr;std::uint32_t subject=0;
  bool present=false,subject_available=false,visible=false,enabled=false;
  NamedGuiTreeInspectionV1 tree{};
  void *tracks_window=nullptr,*tracks_root=nullptr;
  bool tracks_visible=false,tracks_enabled=false;
  NamedGuiTreeInspectionV1 tracks_tree{};
  FaithPowerHoldingTracksObservation12004 tracks_observation{};
  void*tracks_selected_building=nullptr;
};
#include "faith_power_presentation_receiver12004.inc"
bool PresentationDetailSourcePins12004(const ZhongguoScoreboardNativeEnvironmentV1&env);
bool ReadPresentationTracks12004(const ZhongguoScoreboardNativeEnvironmentV1&env,
    const IngameUiGuiOwnerBindingV1&gui,void*handler,PresentationPanel12004&p,std::string&why) {
  if(!PresentationDetailSourcePins12004(env)){why="presentation_show_details_loaded_source_pin_mismatch";return false;}
  struct State {
    void*window=nullptr,*root=nullptr,*back=nullptr,*owner=nullptr,*handler=nullptr;
    std::uintptr_t primary=0,secondary=0;
    bool visible=false,enabled=false;
    bool operator==(const State&)const=default;
  };
  const auto capture=[&](State&s)->bool{
    if(!Value(p.window,0xC8,s.window))return false;
    if(!s.window)return true;
    if(!Value(s.window,0,s.primary)||s.primary!=env.module_base+0x45435C0||
        !Value(s.window,0x10,s.secondary)||s.secondary!=env.module_base+0x4543690||
        !TypedObject(env.module_base,s.window,0x5769298,UiExactImageSizeV1(env.gui_abi_revision))||
        !Value(s.window,0x98,s.owner)||s.owner!=gui.owner||!Value(s.window,0xA0,s.handler)||s.handler!=handler||
        !Value(s.window,0xC8,s.back)||s.back!=p.window||!Value(s.window,0x60,s.root))return false;
    ZhongguoScoreboardAccessV1 access{};void*root=nullptr,*widget=nullptr;
    if(!ResolveNamedGuiWidgetV1(env,access,"holding_tracks_view","holding_tracks_view",root,widget))return false;
    if(!s.root)return !root;
    std::string name;void*vt=nullptr;void*ctx=nullptr;
    return root==s.root&&widget==root&&Value(root,0xD8,ctx)&&ctx==gui.context&&
        ReadGuiWidgetRuntimeV1(access,root,name,vt,s.visible,s.enabled)&&name=="holding_tracks_view";
  };
  State first{},last{};if(!capture(first)){why="presentation_owned_building_tracks_binding_unverified";return false;}
  if(first.root){
    ZhongguoScoreboardAccessV1 access{};
    if(!InspectNamedGuiSubtreeV1(access,env.module_base,first.root,"holding_tracks_view",p.tracks_tree,true)||p.tracks_tree.truncated||
        !p.tracks_tree.root_available||p.tracks_tree.widget_count!=p.tracks_tree.widgets.size()){
      why="presentation_building_tracks_callback_census_unverified";return false;
    }
  }
  if(!capture(last)||first!=last){why="presentation_building_tracks_changed_during_read";return false;}
  auto&t=p.tracks_observation;t.available=true;t.owner_bound=first.window!=nullptr;
  t.window_exists=first.window!=nullptr;t.root_exists=first.root!=nullptr;t.effective_visible=first.visible;
  if(first.window){std::int32_t category=0,mode=0,action=0,category2=0,mode2=0,action2=0;
    if(!Value(p.window,0xEF4,category)||!Value(p.window,0xEF0,mode)||!Value(p.window,0xEF8,action)||
        !Value(p.window,0xEF4,category2)||!Value(p.window,0xEF0,mode2)||!Value(p.window,0xEF8,action2)||
        category!=category2||mode!=mode2||action!=action2){why="presentation_tracks_selection_changed";return false;}
    t.selection_category_id=category;t.selection_mode=mode;t.selection_action_raw=action;
    void*selected=nullptr,*selected2=nullptr;std::string key,key2;
    if(!Value(p.window,0x630,selected)||!Value(p.window,0x630,selected2)||selected!=selected2){why="presentation_tracks_selected_definition_changed";return false;}
    const bool known=selected&&PresentationBuildingDefinition12004(selected,key);
    const bool known2=selected2&&PresentationBuildingDefinition12004(selected2,key2);
    if(known!=known2||(known&&key!=key2)){why="presentation_tracks_selected_definition_identity_changed";return false;}
    if(!Value(p.window,0x630,selected2)||selected2!=selected||!Value(p.window,0xEF4,category2)||!Value(p.window,0xEF0,mode2)||!Value(p.window,0xEF8,action2)||category2!=category||mode2!=mode||action2!=action){why="presentation_tracks_selection_changed_after_identity";return false;}
    p.tracks_selected_building=selected;if(known&&!key.empty())t.selected_building_key=key;
    // Original GUITrackItem.GetSelectedBuilding reads track+468, with
    // track=view+1C8. +628 is only next/candidate; +630 is native selection.
  }
  p.tracks_window=first.window;p.tracks_root=first.root;p.tracks_visible=first.visible;p.tracks_enabled=first.enabled;return true;
}
bool PresentationStockFile12004(const ZhongguoScoreboardNativeEnvironmentV1&env,
    std::string_view relative,std::string_view expected) {
  std::array<wchar_t,32768>path{};const auto n=GetModuleFileNameW(reinterpret_cast<HMODULE>(env.module_base),path.data(),static_cast<DWORD>(path.size()));
  if(!n||n>=path.size())return false;
  const auto file=std::filesystem::path(path.data()).parent_path().parent_path()/L"game"/std::filesystem::path(relative);
  std::ifstream input(file,std::ios::binary|std::ios::ate);if(!input)return false;
  const auto size=input.tellg();if(size<=0||size>2*1024*1024)return false;
  std::string bytes(static_cast<std::size_t>(size),'\0');input.seekg(0);input.read(bytes.data(),static_cast<std::streamsize>(size));
  std::string sha;return input&&ArmyTooltipDigest(bytes,sha)&&sha==expected;
}
bool PresentationStock12004(const ZhongguoScoreboardNativeEnvironmentV1&env,IngameUiWindowKindV1 kind) {
  if(kind==IngameUiWindowKindV1::faith)return PresentationStockFile12004(env,"gui/window_faith.gui","67924e58ccba26d95853ac48af35d91a774f5ce6d2e7f32a0a033de3b9d51521");
  if(kind==IngameUiWindowKindV1::holding)return PresentationStockFile12004(env,"gui/window_county_view.gui","4e932366e397b06347d4296c05f3c4c5850e995b010eecda7d5a3b5a7c48675c");
  if(kind==IngameUiWindowKindV1::personal_beliefs)return PresentationStockFile12004(env,"gui/window_personal_beliefs.gui","2c9b85a11381119d0d91ec68731d5c376aed10fe48387b73701184a3d39513e2")&&
      PresentationStockFile12004(env,"gui/shared/lists.gui","71c6dd9036ed54d53d95e6229782924325f262d208f4e971775237bd4852e5ac");
  if(kind==IngameUiWindowKindV1::rite_creation)return PresentationStockFile12004(env,"gui/window_rite_creation.gui","9476299fdbf0975e41923eac9b192d3fe0b2cd74a4da0d928d0da7974b7ea9f8");
  return false;
}
std::string PresentationParentPath12004(std::string_view path,unsigned levels=1) {
  std::string out(path);while(levels--){const auto slash=out.rfind('/');if(slash==std::string::npos)out.clear();else out.resize(slash);}return out;
}
bool PresentationDescendantPath12004(std::string_view child,std::string_view parent) noexcept {
  return child==parent||parent.empty()||(child.size()>parent.size()&&child.starts_with(parent)&&child[parent.size()]=='/');
}
const NamedGuiWidgetInspectionV1*PresentationRow12004(const NamedGuiTreeInspectionV1&tree,std::string_view path) {
  for(const auto&x:tree.widgets)if(x.child_path==path)return &x;return nullptr;
}
bool PresentationUnderName12004(const NamedGuiTreeInspectionV1&tree,std::string_view path,std::string_view name) {
  for(const auto&x:tree.widgets)if(x.runtime_name==name&&PresentationDescendantPath12004(path,x.child_path))return true;return false;
}
bool ReadPresentationPanel12004(const ZhongguoScoreboardNativeEnvironmentV1&env,
    const IngameUiRequestV1&r,const game::Snapshot&snapshot,std::uint64_t epoch,
    const IngameUiGuiOwnerBindingV1&gui,void*handler,PresentationPanel12004&out,std::string&why) {
  out={};const auto kind=r.window_kind;const auto root_name=IngameUiWindowNameV1(kind);
  if(!PresentationStock12004(env,kind)){why="presentation_stock_gui_source_mismatch";return false;}
  const auto read_owned=[&](PresentationPanel12004&v)->bool {
    if(kind==IngameUiWindowKindV1::faith){
      ck3_12004::religion_ui::Selection s{};
      if(!ck3_12004::religion_ui::ReadSelection12004(ck3_12004::religion_ui::BindImage12004(env.module_base,env.executable_sha256),handler,ck3_12004::religion_ui::Window::faith,s)){why=s.unavailable_reason;return false;}
      v.window=const_cast<void*>(s.window);v.root=const_cast<void*>(s.root);v.present=s.window!=nullptr;
      v.subject=s.subject_id;v.subject_available=s.subject_available;return true;
    }
    if(kind==IngameUiWindowKindV1::holding||kind==IngameUiWindowKindV1::personal_beliefs){
      PresentationWindow12004 s{};if(!ReadPresentationOwnedWindow12004(env,handler,kind,s,why))return false;
      v.window=s.window;v.root=s.root;v.present=s.present;v.subject=s.subject;v.subject_available=s.subject_available;return true;
    }
    namespace reform=ck3_12002::religion_reform;reform::DraftWindowView s{};
    if(!reform::ReadCurrentRiteCreationWindow12002(ck3_12004::religion::BindCurrentRiteCreationWindow12004(env.module_base,env.executable_sha256),epoch,s)||!s.available||
        s.played_character_id!=static_cast<std::uint32_t>(snapshot.played_character_id)||s.date_raw!=snapshot.date_raw){why="presentation_current_rite_draft_unverified";return false;}
    v.window=const_cast<void*>(s.window);v.present=s.present;v.subject_available=s.source_rite_id.has_value();
    if(s.source_rite_id)v.subject=*s.source_rite_id;
    if(v.present&&!Value(s.window,0x60,v.root)){why="presentation_rite_root_unreadable";return false;}return true;
  };
  if(!read_owned(out))return false;
  ZhongguoScoreboardAccessV1 access{};void*root=nullptr,*widget=nullptr;
  if(!ResolveNamedGuiWidgetV1(env,access,root_name,root_name,root,widget)){why="presentation_fixed_root_lookup_failed";return false;}
  if(!out.present){if(root){why="presentation_gui_root_without_owned_window";return false;}why.clear();return true;}
  void*ctx=nullptr,*vt=nullptr;std::string name;
  if(!out.window||!out.root||root!=out.root||widget!=root||!Value(root,0xD8,ctx)||ctx!=gui.context||
      !ReadGuiWidgetRuntimeV1(access,root,name,vt,out.visible,out.enabled)||name!=root_name||
      !InspectNamedGuiSubtreeV1(access,env.module_base,root,root_name,out.tree)||out.tree.truncated||
      !out.tree.root_available||out.tree.widget_count!=out.tree.widgets.size()||out.tree.widget_count>2048){why="presentation_owned_root_census_unverified";return false;}
  PresentationPanel12004 again{};void*lastroot=nullptr,*lastwidget=nullptr,*lastvt=nullptr;std::string lastname;bool visible=false,enabled=false;
  IngameUiGuiOwnerBindingV1 lastgui{};void*lasthandler=nullptr;
  if(!read_owned(again)||again.window!=out.window||again.root!=out.root||again.present!=out.present||again.subject_available!=out.subject_available||
      (again.subject_available&&again.subject!=out.subject)||!ReadIngameUiGuiOwnerBindingV1(env,lastgui)||lastgui!=gui||!ResolveHandler(env,lasthandler)||lasthandler!=handler||
      !ResolveNamedGuiWidgetV1(env,access,root_name,root_name,lastroot,lastwidget)||lastroot!=root||lastwidget!=root||
      !ReadGuiWidgetRuntimeV1(access,root,lastname,lastvt,visible,enabled)||lastname!=name||lastvt!=vt||visible!=out.visible||enabled!=out.enabled){why="presentation_window_subject_or_owner_changed";return false;}
  if(kind==IngameUiWindowKindV1::holding&&!ReadPresentationTracks12004(env,gui,handler,out,why))return false;
  why.clear();return true;
}
void PresentationCopyPanel12004(const PresentationPanel12004&p,IngameUiResultV1&out) {
  out.window_exists=p.present;out.effective_visible=p.visible;out.enabled=p.enabled;out.subject_id_available=p.subject_available;
  if(p.subject_available)out.current_subject_id=p.subject;out.tree=p.tree;
  auto&v=out.presentation_ui;v.post_window_visible=p.visible;
  if(p.subject_available)v.subject_id=p.subject;
  v.source_bound=p.present&&p.visible&&p.subject_available;
  if(p.tracks_observation.available)v.holding_tracks=p.tracks_observation;
}
std::optional<std::string>PresentationActiveTab12004(const IngameUiRequestV1&r,const PresentationPanel12004&p) {
  std::optional<std::string>active;bool ambiguous=false;
  const auto add=[&](std::string value){if(active&&*active!=value)ambiguous=true;else active=std::move(value);};
  if(r.window_kind==IngameUiWindowKindV1::faith){
    for(const auto&x:p.tree.widgets)if(x.effective_visible){if(x.runtime_name=="tab_beliefs")add("beliefs");if(x.runtime_name=="tab_holy_sites")add("holy_sites");}
  }else if(r.window_kind==IngameUiWindowKindV1::personal_beliefs){
    for(const auto&x:p.tree.widgets){
      const auto levels=x.runtime_name=="sort_order"?2U:x.runtime_name=="rite_button"?3U:0U;if(!levels)continue;
      const auto path=PresentationParentPath12004(x.child_path,levels);const auto*page=PresentationRow12004(p.tree,path);
      const auto*parent=PresentationRow12004(p.tree,PresentationParentPath12004(path));
      if(page&&page->effective_visible&&parent&&parent->runtime_name=="personal_beliefs_right_side_tutorial_uses_this")add(levels==2?"tenets":"doctrines");
    }
  }
  return ambiguous?std::nullopt:active;
}
struct PresentationSourceRow12004 {std::string kind,path;const NamedGuiWidgetInspectionV1*row=nullptr;void*root=nullptr;};
bool PresentationCensus12004(const IngameUiRequestV1&r,const PresentationPanel12004&p,
    std::vector<PresentationSourceRow12004>&sources,FaithPowerPresentationObservationV1&out) {
  sources.clear();out.targets.clear();
  const auto add=[&](std::string kind,std::string path){
    const auto*row=PresentationRow12004(p.tree,path);if(!row||!row->effective_visible)return;
    if(std::any_of(sources.begin(),sources.end(),[&](const auto&x){return x.kind==kind&&x.path==path;}))return;
    sources.push_back({std::move(kind),std::move(path),row,p.root});
  };
  for(const auto&x:p.tree.widgets){
    if(!x.effective_visible)continue;
    if(r.window_kind==IngameUiWindowKindV1::faith&&x.runtime_name=="doctrine_group_bg"&&
        (PresentationUnderName12004(p.tree,x.child_path,"doctrines_grid_core_tenets")||PresentationUnderName12004(p.tree,x.child_path,"doctrines_compact_grid_core_tenets")))
      add("faith_core_tenet",PresentationParentPath12004(x.child_path));
    if(r.window_kind==IngameUiWindowKindV1::faith&&x.runtime_name=="doctrine_name"&&PresentationUnderName12004(p.tree,x.child_path,"doctrines_compact_grid_core_tenets"))
      add("faith_core_tenet",PresentationParentPath12004(x.child_path,2));
    if(r.window_kind==IngameUiWindowKindV1::faith&&PresentationUnderName12004(p.tree,x.child_path,"tab_beliefs")){
      if(x.runtime_name=="doctrine_group_icon")add("faith_doctrine",PresentationParentPath12004(x.child_path,3));
      if(x.runtime_name=="doctrine_icon_main"||x.runtime_name=="doctrine_icon_other"||x.runtime_name=="doctrine_icon_special")
        add("faith_doctrine",PresentationParentPath12004(x.child_path,2));
    }
    if(r.window_kind==IngameUiWindowKindV1::holding&&x.runtime_name=="building_button"&&PresentationUnderName12004(p.tree,x.child_path,"buildings_grid"))add("holding_building",x.child_path);
    if(r.window_kind==IngameUiWindowKindV1::rite_creation&&x.runtime_name=="tenet_name"&&PresentationUnderName12004(p.tree,x.child_path,"tenet_selection"))
      add("rite_core_tenet_choice",PresentationParentPath12004(x.child_path,3));
    if(r.window_kind==IngameUiWindowKindV1::rite_creation&&x.runtime_name=="tenet_name"&&PresentationUnderName12004(p.tree,x.child_path,"left_side")&&PresentationUnderName12004(p.tree,x.child_path,"tenets_grid"))
      add("rite_core_tenet_slot",PresentationParentPath12004(x.child_path,3));
    // Additional finite provider-owned carriers are added only from closed stock
    // source predicates below. A mechanism list is never treated as GUI order.
  }
  if(r.window_kind==IngameUiWindowKindV1::holding&&p.tracks_visible&&p.tracks_enabled&&
      p.tracks_tree.callback_thunk_3aa30e0_pin_verified&&p.tracks_tree.expression_layout_3a9f960_pin_verified){
    for(const auto&x:p.tracks_tree.widgets){
      const auto&b=x.standard_click_binding_12004;
      if(!x.effective_visible||!b.button_base_slot13||!b.primary_group||b.callbacks.size()!=1||
          !PresentationUnderName12004(p.tracks_tree,x.child_path,"tracks_grid")||
          !PresentationUnderName12004(p.tracks_tree,x.child_path,"header"))continue;
      const auto&callback=b.callbacks.front();
      if(!callback.indirect_target_3aa30e0||!callback.expression_descriptor_3a9f960||
          callback.expression_3a9f960.final_target_38_rva!=0x12B3260)continue;
      sources.push_back({"holding_building_preview",x.child_path,&x,p.tracks_root});
    }
  }
  if(sources.size()>128)return false;
  for(const auto&s:sources){std::uint32_t index=0;for(const auto&prior:out.targets)if(prior.kind==s.kind)++index;
    out.targets.push_back({index,s.kind,s.row->runtime_name,std::nullopt,std::nullopt,s.row->effective_visible,s.row->enabled});}
  return true;
}
bool ResolvePresentationTarget12004(const ZhongguoScoreboardNativeEnvironmentV1&env,const IngameUiRequestV1&r,
    const game::Snapshot&snapshot,std::uint64_t epoch,const IngameUiGuiOwnerBindingV1&gui,void*handler,
    PresentationTargetBinding12004&out,FaithPowerPresentationObservationV1&value) {
  PresentationPanel12004 panel{};std::string why;
  if(!epoch||!ReadPresentationPanel12004(env,r,snapshot,epoch,gui,handler,panel,why)||!panel.present||!panel.visible||!panel.enabled||
      !panel.subject_available||panel.subject!=r.subject_id)return false;
  if(r.window_kind==IngameUiWindowKindV1::personal_beliefs&&panel.subject!=static_cast<std::uint32_t>(snapshot.played_character_id))return false;
  std::vector<PresentationSourceRow12004>rows;if(!PresentationCensus12004(r,panel,rows,value))return false;
  std::uint32_t index=0;const PresentationSourceRow12004*match=nullptr;
  for(const auto&row:rows)if(row.kind==r.presentation_target){if(index++==r.presentation_index)match=&row;}
  if(!match)return false;
  void*source=nullptr;if(!ArmyTooltipResolvePath(env,match->root,gui.context,match->path,source,false)||!ArmyTooltipVisibleAncestors(env,source,gui.context))return false;
  out={gui,match->root,source,panel.subject,r.presentation_index,r.presentation_target,match->path};
  value.subject_id=panel.subject;value.source_bound=true;value.post_window_visible=panel.visible;
  value.active_tab=PresentationActiveTab12004(r,panel);value.tab_observed=value.active_tab.has_value();
  value.target_kind=r.presentation_target;value.target_index=r.presentation_index;
  if(r.operation==IngameUiOperationV1::query&&panel.tracks_observation.available)value.holding_tracks=panel.tracks_observation;
  if(r.presentation_target=="holding_building_preview"||r.presentation_target=="holding_building"){
    PresentationBuildingReceiver12004 receiver{};
    if(!ReadPresentationBuildingReceiver12004(env,gui,panel,match->root,match->path,r.presentation_target=="holding_building_preview",receiver,why)){value.unavailable_reason=why;return false;}
    if(r.presentation_target=="holding_building_preview")for(auto&target:value.targets)if(target.kind==r.presentation_target&&target.index==r.presentation_index)target.definition_key=receiver.building_key;
  }
  return true;
}

bool PresentationOriginalClick12004(const ZhongguoScoreboardNativeEnvironmentV1&env,
    const IngameUiGuiOwnerBindingV1&gui,void*root,std::string_view path,IngameUiResultV1&out) {
  if(!PresentationStockFile12004(env,"gui/shared/buttons.gui","88403785a1acdacc628730aaa101a04b2ae6293e74aa706a93e0e1695f3b1a0c"))return false;
  void*target=nullptr,*vt=nullptr;std::string name;bool visible=false,enabled=false;ZhongguoScoreboardAccessV1 access{};
  if(!ArmyTooltipResolvePath(env,root,gui.context,path,target)||!ArmyTooltipVisibleAncestors(env,target,gui.context)||
      !ReadGuiWidgetRuntimeV1(access,target,name,vt,visible,enabled)||!visible||!enabled||
      !ReadModalNavigationAdmission(gui.context,out.modal_admission))return false;
  auto dispatch=BindZhongguoScoreboardActionDispatchEnvironmentV1(env.module_base,env.exact_build_admitted,env.gui_abi_revision);
  if(!InspectFixedGuiWidgetDispatchAdmissionV1(dispatch,target,vt))return false;
  // The existing shared routine dispatches a fixed widget through the original
  // ShortcutManager. Its enum only excludes reopen; no scoreboard action runs.
  bool handled=false;
  const bool ok=DispatchFixedGuiWidgetNativeWithAttemptV1(&dispatch,game::ZhongguoScoreboardActionV1::open,target,vt,handled,out.native_dispatch_attempted);
  out.dispatch_invoked=ok;out.verification_pending=ok;return ok;
}
std::optional<std::string>PresentationTabClickPath12004(const IngameUiRequestV1&r,const PresentationPanel12004&p) {
  std::vector<std::string>buttons;
  for(const auto&x:p.tree.widgets)if(x.runtime_name=="tab_name"&&x.effective_visible){
    const auto button=PresentationParentPath12004(x.child_path,2),tabs=PresentationParentPath12004(button);
    const auto*parent=PresentationRow12004(p.tree,tabs);
    if(!parent||parent->runtime_name!="tabs")continue;
    if(r.window_kind==IngameUiWindowKindV1::personal_beliefs&&!PresentationUnderName12004(p.tree,tabs,"personal_beliefs_right_side_tutorial_uses_this"))continue;
    if(std::find(buttons.begin(),buttons.end(),button)==buttons.end())buttons.push_back(button);
  }
  // Stock source order is checked independently of mechanism arrays. A hidden
  // tab or changed source structure is unavailable, never an index shift.
  const auto need=r.window_kind==IngameUiWindowKindV1::faith?3U:2U;
  if(buttons.size()!=need)return std::nullopt;
  const auto index=r.presentation_tab=="holy_sites"?2U:r.presentation_tab=="doctrines"?1U:0U;
  return buttons[index];
}
std::optional<std::string>PresentationCoreClickPath12004(const PresentationPanel12004&p,std::uint32_t index) {
  std::vector<std::string>rows;
  for(const auto&x:p.tree.widgets)if(x.runtime_name=="tenet_name"&&x.effective_visible&&
      PresentationUnderName12004(p.tree,x.child_path,"left_side")&&PresentationUnderName12004(p.tree,x.child_path,"tenets_grid")){
    const auto path=PresentationParentPath12004(x.child_path,3);
    if(std::find(rows.begin(),rows.end(),path)==rows.end())rows.push_back(path);
  }
  if(index>=rows.size())return std::nullopt;return rows[index];
}
bool ExecutePresentationUi12004(const ZhongguoScoreboardNativeEnvironmentV1&env,const IngameUiRequestV1&r,
    const game::Snapshot&snapshot,const MainThreadExecutionStampV1&stamp,
    const IngameUiGuiOwnerBindingV1&gui,void*handler,IngameUiResultV1&out) {
  auto&v=out.presentation_ui;v.requested=true;
  const auto fail=[&](std::string_view why){v.available=false;v.source_bound=false;v.status="unavailable";v.unavailable_reason=why;
    out.available=false;out.status=v.status;out.unavailable_reason=why;return true;};
  try{
    const auto operation=static_cast<std::uint32_t>(r.operation);
    if(operation==204||operation==205||(operation==0&&!r.presentation_receipt.empty())){
      PresentationPanel12004 tooltip_panel{};std::string why;
      if(!ReadPresentationPanel12004(env,r,snapshot,stamp.pump_epoch,gui,handler,tooltip_panel,why))return fail(why);
      PresentationCopyPanel12004(tooltip_panel,out);
      if(PresentationTooltipExecute12004(env,r,snapshot,stamp,gui,handler,out))return true;
      return fail("presentation_tooltip_operation_not_handled");
    }
    if(operation==200||operation==201){
      if(operation==201&&r.subject_id!=static_cast<std::uint32_t>(snapshot.played_character_id))return fail("presentation_personal_beliefs_requires_actual_player");
      std::string why;
      if(!PresentationStock12004(env,r.window_kind)||!ReadModalNavigationAdmission(gui.context,out.modal_admission))return fail("presentation_open_source_or_modal_admission_unavailable");
      const bool ok=OpenPresentationOwnedWindow12004(env,handler,r.window_kind,r.subject_id,out.native_dispatch_attempted,why);
      if(!ok)return fail(why.empty()?"presentation_original_open_failed_do_not_retry_if_attempted":why);
      out.dispatch_invoked=true;out.verification_pending=true;
      PresentationPanel12004 immediate{};
      if(!ReadPresentationPanel12004(env,r,snapshot,stamp.pump_epoch,gui,handler,immediate,why))return fail("presentation_open_returned_immediate_window_unknown_do_not_retry");
      PresentationCopyPanel12004(immediate,out);
      v.source_bound=false;v.holding_tracks.reset(); // Immediate open read grants no independent postcondition.
      out.available=true;out.status="acknowledged_verification_pending";out.unavailable_reason.clear();
      v.available=true;v.status=out.status;v.unavailable_reason.clear();v.action_owner_epoch=stamp.pump_epoch;
      // Opening can materialize on a later GUI update. Only an independent query
      // may bind the selected object/window; no requested ID is copied as actual.
      return true;
    }
    PresentationPanel12004 panel{};std::string why;
    if(!ReadPresentationPanel12004(env,r,snapshot,stamp.pump_epoch,gui,handler,panel,why))return fail(why);
    PresentationCopyPanel12004(panel,out);v.active_tab=PresentationActiveTab12004(r,panel);v.tab_observed=v.active_tab.has_value();
    if(r.window_kind==IngameUiWindowKindV1::personal_beliefs&&panel.subject_available&&panel.subject!=static_cast<std::uint32_t>(snapshot.played_character_id))return fail("presentation_personal_selected_character_differs_from_player");
    v.picker_observed=std::any_of(panel.tree.widgets.begin(),panel.tree.widgets.end(),[](const auto&x){return x.runtime_name=="tenet_selection"&&x.effective_visible;});
    v.preview_observed=panel.tracks_visible&&panel.tracks_observation.owner_bound&&panel.tracks_observation.selection_action_raw==std::optional<std::int32_t>(1)&&panel.tracks_observation.selected_building_key.has_value();
    std::vector<PresentationSourceRow12004>sources;if(!PresentationCensus12004(r,panel,sources,v))return fail("presentation_target_census_limit_exceeded");
    if(operation==0){
      if((r.subject_id!=0||!r.presentation_target.empty())&&(!panel.subject_available||panel.subject!=r.subject_id))return fail("presentation_query_requested_subject_differs_from_actual");
      if(!r.presentation_tab.empty()&&(!v.active_tab||*v.active_tab!=r.presentation_tab))return fail("presentation_query_requested_tab_not_observed");
      if(!r.presentation_target.empty()){
        PresentationTargetBinding12004 binding{};
        if(!ResolvePresentationTarget12004(env,r,snapshot,stamp.pump_epoch,gui,handler,binding,v))return fail("presentation_query_actual_target_unverified");
      }
      v.observation_owner_epoch=stamp.pump_epoch;v.available=true;v.status="observed";v.unavailable_reason.clear();out.available=true;out.status=v.status;out.unavailable_reason.clear();return true;
    }
    if(!panel.present||!panel.visible||!panel.enabled||!panel.subject_available||panel.subject!=r.subject_id||
        (r.window_kind==IngameUiWindowKindV1::personal_beliefs&&panel.subject!=static_cast<std::uint32_t>(snapshot.played_character_id)))return fail("presentation_action_current_subject_not_bound");
    std::optional<std::string>path;
    if(operation==202)path=PresentationTabClickPath12004(r,panel);
    if(operation==203)path=PresentationCoreClickPath12004(panel,r.presentation_index);
    void*click_root=panel.root;
    PresentationBuildingReceiver12004 receiver{};
    const bool building_action=operation==206||operation==207;
    if(building_action){
      const auto kind=operation==206?"holding_building_preview":"holding_building";std::uint32_t index=0;
      for(const auto&row:sources)if(row.kind==kind&&index++==r.presentation_index){path=row.path;click_root=row.root;}
      if(!path||!ReadPresentationBuildingReceiver12004(env,gui,panel,click_root,*path,operation==206,receiver,why))return fail(why.empty()?"presentation_building_owned_source_unavailable":why);
      if(operation==207&&panel.tracks_observation.selection_category_id==std::optional<std::int32_t>(static_cast<std::int32_t>(receiver.category))&&
          (receiver.category!=0||panel.tracks_observation.selection_mode==std::optional<std::int32_t>(static_cast<std::int32_t>(receiver.mode))))
        return fail("presentation_building_track_current_category_original_toggle_would_close");
    }
    if(!path)return fail("presentation_original_finite_button_not_unique");
    PresentationPanel12004 last{};
    if(!ReadPresentationPanel12004(env,r,snapshot,stamp.pump_epoch,gui,handler,last,why)||last.window!=panel.window||last.root!=panel.root||
        last.subject_available!=panel.subject_available||last.subject!=panel.subject)return fail("presentation_subject_changed_before_original_callback");
    std::optional<std::string>lastpath;
    void*last_click_root=last.root;
    if(operation==202)lastpath=PresentationTabClickPath12004(r,last);
    if(operation==203)lastpath=PresentationCoreClickPath12004(last,r.presentation_index);
    if(building_action){
      std::vector<PresentationSourceRow12004>again;FaithPowerPresentationObservationV1 ignored{};PresentationBuildingReceiver12004 receiver2{};
      if(!PresentationCensus12004(r,last,again,ignored))return fail("presentation_building_fresh_census_unavailable");
      std::uint32_t index=0;for(const auto&row:again)if(row.kind==r.presentation_target&&index++==r.presentation_index){lastpath=row.path;last_click_root=row.root;}
      if(!lastpath||!ReadPresentationBuildingReceiver12004(env,gui,last,last_click_root,*lastpath,operation==206,receiver2,why)||receiver2!=receiver)return fail("presentation_building_receiver_changed_before_original_callback");
    }
    if(lastpath!=path||last_click_root!=click_root||!PresentationOriginalClick12004(env,gui,click_root,*path,out))return fail("presentation_original_callback_admission_or_dispatch_failed_do_not_retry_if_attempted");
    v.action_owner_epoch=stamp.pump_epoch;v.observation_owner_epoch.reset();v.active_tab.reset();v.tab_observed=false;v.picker_observed=false;v.preview_observed=false;
    if(operation==203){v.target_index=r.presentation_index;v.target_kind="rite_core_tenet_slot";}
    if(building_action){v.target_index=r.presentation_index;v.target_kind=r.presentation_target;
      if(operation==206)for(auto&target:v.targets)if(target.kind==r.presentation_target&&target.index==r.presentation_index)target.definition_key=receiver.building_key;}
    v.holding_tracks.reset();
    v.available=true;v.status="acknowledged_verification_pending";v.unavailable_reason.clear();out.available=true;out.status=v.status;out.unavailable_reason.clear();return true;
  }catch(...){out.verification_pending=out.dispatch_invoked;return fail("presentation_exception_do_not_retry_if_attempted");}
}
