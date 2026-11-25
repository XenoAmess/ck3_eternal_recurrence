// Included in the Raw TU private namespace; no capability or caller selector.
struct ScoreboardRaw {
 ck3_1210::GuiControlCaptureV1 capture;
 Zg361Scoreboard267V1 source;
 std::uintptr_t open=0,close=0;
 friend bool operator==(const ScoreboardRaw&,const ScoreboardRaw&)=default;
};
[[maybe_unused]]bool ScoreboardRead(const ReadonlyBindings&b,const Zg361Ae2Frame267V1&f,ScoreboardRaw&out,std::string&why){
 if(!f.scoreboard)return false;const auto&w=*f.scoreboard;
 const auto image=BindGuiControlImage267V2(b.module_base,kExecutableSha256);
 ScoreboardRaw a,z;
 if(!CaptureFixedScoreboardControls267V1(image,w,a.capture,why)||
  !CaptureFixedScoreboardControls267V1(image,w,z.capture,why)||a.capture!=z.capture)return false;
 a.capture.played_character_id=f.core.played_character_id;a.capture.date_raw=f.core.clock.date_raw;
 a.capture.native_revision=w.connection_generation;a.capture.complete=true;
 auto&s=a.source;s.complete=true;
 std::optional<std::size_t>root,modal;
 for(std::size_t i=0;i<w.tree.size();++i){const auto&n=w.tree[i];
  if(n.name==kZg361ScoreboardWindow267V1){if(root)return false;root=i;}
  if(n.name==kZg361ScoreboardModal267V1){if(modal)return false;modal=i;}}
 const auto inside=[&](std::size_t n,std::size_t ancestor){
  for(std::size_t depth=0;depth<=64;++depth){if(n==ancestor)return true;
   const auto p=w.tree[n].parent_index;if(p<0||static_cast<std::size_t>(p)>=n)return false;n=static_cast<std::size_t>(p);}return false;};
 if(modal&&(!root||!inside(*modal,*root)))return false;
 if(root){const auto&r=w.tree[*root];s.window_found=true;s.window_visible=r.visible;s.window_enabled=r.enabled;
  for(std::size_t i=0;i<w.tree.size();++i)if(inside(i,*root))++s.window_nodes;}
 if(modal){const auto&m=w.tree[*modal];s.modal_found=true;s.modal_visible=m.visible;s.modal_enabled=m.enabled;
  s.modal_children=static_cast<std::uint32_t>(m.child_count);}
 unsigned open_count=0,close_count=0;
 for(std::size_t i=0;i<a.capture.widgets.size();++i){const auto&v=a.capture.widgets[i];
  const bool entry=std::find(kZg361ScoreboardEntries267V1.begin(),kZg361ScoreboardEntries267V1.end(),v.row.runtime_name)!=kZg361ScoreboardEntries267V1.end();
  if(entry&&v.row.clickable&&root&&inside(i,*root)){
   ++open_count;a.open=v.widget;s.open_entry=v.row.runtime_name;}
  if(v.row.runtime_name==kZg361ScoreboardClose267V1&&modal&&inside(i,*modal)){
   ++close_count;if(v.row.clickable)a.close=v.widget;}}
 if(open_count>1||close_count>1){why="zg361_scoreboard_fixed_button_ambiguous";return false;}
 s.open_admissible=s.window_found&&s.window_visible&&s.window_enabled&&!s.modal_visible&&open_count==1&&a.open;
 s.close_admissible=s.window_found&&s.window_visible&&s.window_enabled&&s.modal_found&&s.modal_visible&&s.modal_enabled&&close_count==1&&a.close;
 out=std::move(a);return true;
}
[[maybe_unused]]GuiWindowV1 ScoreboardLeaseWindow(GuiWindowV1 w){w.ticket_sequence=0;w.pump_epoch=0;return w;}
