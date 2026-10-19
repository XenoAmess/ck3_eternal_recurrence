// Provider-private finite selectors. Included in navigation's private namespace.
#ifndef XAR_ENABLE_RELIGION_UI12004_PRESENTATION
#define XAR_ENABLE_RELIGION_UI12004_PRESENTATION 0
#endif
constexpr bool PresentationUiEnabled12004() noexcept {
  return XAR_ENABLE_RELIGION_UI12004_PRESENTATION!=0;
}
bool PresentationRequested12004(const IngameUiRequestV1 &r) noexcept {
  return r.presentation_requested||static_cast<std::uint32_t>(r.window_kind)>=9;
}
bool ValidatePresentationRequest12004(const IngameUiRequestV1&r) noexcept {
  const auto k=static_cast<std::uint32_t>(r.window_kind),o=static_cast<std::uint32_t>(r.operation);
  if(!PresentationRequested12004(r)||(k!=7&&k!=9&&k!=10&&k!=11)||r.subject_id==0xFFFFFFFFU||
      (k==9&&r.subject_id>0x7FFFFFFFU)||r.presentation_index>=128||
      !r.army_tooltip_kind.empty()||!r.army_tooltip_receipt.empty()||r.holy_site_decision_explicit||
      r.relic_action_explicit||r.relic_action!=ck3_12004::religion::relic_actions::Request{}||
      !r.holy_site_creation_type_key.empty()||r.holy_site_creation_selected.has_value()||
      !r.holy_site_creation_expected_preview_identity_sha256.empty()||
      r.appointment.requested_title_id||r.appointment.candidate_offset||r.appointment.candidate_limit!=32||
      r.appointment.breakdown_character_id||r.appointment.diagnostic_character_id)return false;
  const auto&t=r.presentation_target;const auto&tab=r.presentation_tab;
  const bool target=t.empty()||(k==7&&(t=="faith_core_tenet"||t=="faith_doctrine"))||
      (k==9&&(t=="holding_building"||t=="holding_building_preview"||t=="holding_construct_conditions"))||
      (k==10&&t=="personal_tenet")||(k==11&&t=="rite_core_tenet_choice");
  const bool tab_ok=tab.empty()||(k==7&&(tab=="beliefs"||tab=="holy_sites"))||
      (k==10&&(tab=="tenets"||tab=="doctrines"));
  if(!target||!tab_ok)return false;
  if(o==0) {
    if(!r.presentation_receipt.empty())return !t.empty()&&ArmyTooltipNonceValid(r.presentation_receipt);
    return true;
  }
  if(o==200)return k==9&&r.subject_id>0&&t.empty()&&tab.empty()&&!r.presentation_index&&r.presentation_receipt.empty();
  if(o==201)return k==10&&r.subject_id>0&&t.empty()&&tab.empty()&&!r.presentation_index&&r.presentation_receipt.empty();
  if(o==202)return (k==7||k==10)&&!tab.empty()&&t.empty()&&!r.presentation_index&&r.presentation_receipt.empty();
  if(o==203)return k==11&&t.empty()&&tab.empty()&&r.presentation_receipt.empty();
  if(o==204)return !t.empty()&&r.presentation_receipt.empty();
  if(o==205)return !t.empty()&&ArmyTooltipNonceValid(r.presentation_receipt);
  if(o==206)return k==9&&t=="holding_building_preview"&&tab.empty()&&r.presentation_receipt.empty();
  if(o==207)return k==9&&t=="holding_building"&&tab.empty()&&r.presentation_receipt.empty();
  if(o==208)return k==10&&r.subject_id>0&&!r.presentation_requested; // No selector fields, including explicit empty/zero markers.
  return false;
}
// This route's explicit empty tab is a presence marker. The shared
// JsonStringField deliberately rejects empty strings and remains unchanged.
// Accept only this finite top-level compact/unescaped selector, once.
bool ParsePresentationTabSelector12004(std::string_view json,std::string&out) noexcept {
  constexpr std::string_view field="\"presentation_tab\":";
  if(json.empty()||json.front()!='{'||json.back()!='}')return false;
  const auto at=json.find(field);
  if(at==std::string_view::npos||json.find(field,at+field.size())!=std::string_view::npos||
      at==0||(json[at-1]!='{'&&json[at-1]!=','))return false;
  bool quoted=false,escaped=false;std::size_t objects=0,arrays=0;
  for(std::size_t i=0;i<at;++i){const char c=json[i];
    if(quoted){if(escaped)escaped=false;else if(c=='\\')escaped=true;else if(c=='"')quoted=false;}
    else if(c=='"')quoted=true;
    else if(c=='{')++objects;
    else if(c=='}'){if(!objects)return false;--objects;}
    else if(c=='[')++arrays;
    else if(c==']'){if(!arrays)return false;--arrays;}
  }
  if(quoted||objects!=1||arrays!=0)return false;
  const auto value=at+field.size();
  for(const auto tab:std::array<std::string_view,5>{{"","beliefs","holy_sites","tenets","doctrines"}}){
    const auto end=value+tab.size()+2;
    if(end<json.size()&&json[value]=='"'&&json.substr(value+1,tab.size())==tab&&json[end-1]=='"'&&
        (json[end]==','||json[end]=='}')){out.assign(tab);return true;}
  }
  return false;
}
bool ParsePresentationRequest12004(std::string_view json,IngameUiRequestV1&r) noexcept {
  const auto has=[&](std::string_view name){return json.find(std::string("\"")+std::string(name)+"\"")!=std::string_view::npos;};
  r.presentation_requested=has("presentation_target")||has("presentation_index")||has("presentation_tab")||has("presentation_receipt");
  if(has("presentation_target")&&!bridge::JsonStringField(json,"presentation_target",r.presentation_target,32))return false;
  if(has("presentation_tab")&&!ParsePresentationTabSelector12004(json,r.presentation_tab))return false;
  if(has("presentation_receipt")&&!bridge::JsonStringField(json,"presentation_receipt",r.presentation_receipt,32))return false;
  if(has("presentation_index")){
    std::uint64_t i=0;if(!bridge::JsonUnsignedField(json,"presentation_index",i)||i>=128)return false;r.presentation_index=static_cast<std::uint32_t>(i);
  }
  return true;
}
void SerializePresentationUi12004(std::ostringstream&o,const FaithPowerPresentationObservationV1&v) {
  if(!v.requested)return;
  const auto text=[&](const auto&x){if(x)o<<'"'<<JsonEscape(*x)<<'"';else o<<"null";};
  const auto scalar=[&](const auto&x){if(x)o<<*x;else o<<"null";};
  o<<",\"presentation_ui\":{\"schema\":\"ck3-presentation-ui-v1\",\"requested\":true,\"available\":"<<v.available
    <<",\"status\":\""<<JsonEscape(v.status)<<"\",\"unavailable_reason\":";
  if(v.unavailable_reason.empty())o<<"null";else o<<'"'<<JsonEscape(v.unavailable_reason)<<'"';
  o<<",\"subject_id\":";scalar(v.subject_id);o<<",\"target_index\":";scalar(v.target_index);
  o<<",\"active_tab\":";text(v.active_tab);o<<",\"target_kind\":";text(v.target_kind);o<<",\"receipt_id\":";text(v.receipt_id);
  o<<",\"action_owner_epoch\":";scalar(v.action_owner_epoch);o<<",\"observation_owner_epoch\":";scalar(v.observation_owner_epoch);
  o<<",\"post_window_visible\":";scalar(v.post_window_visible);
  o<<",\"source_bound\":"<<v.source_bound<<",\"tab_observed\":"<<v.tab_observed
    <<",\"picker_observed\":"<<v.picker_observed<<",\"preview_observed\":"<<v.preview_observed
    <<",\"hover_source_matches\":"<<v.hover_source_matches<<",\"tooltip_stack_observed\":"<<v.tooltip_stack_observed
    <<",\"tooltip_root_visible\":"<<v.tooltip_root_visible<<",\"tooltip_active_count\":";scalar(v.tooltip_active_count);
  o<<",\"tooltip_top_locked\":";scalar(v.tooltip_top_locked);
  o<<",\"leave_observed\":"<<v.leave_observed<<",\"cache_complete\":"<<v.cache_complete
    <<",\"rendered_pixels_observed\":false,\"cache_texts\":[";
  for(std::size_t i=0;i<v.cache_texts.size();++i){if(i)o<<',';const auto&x=v.cache_texts[i];
    o<<"{\"runtime_name\":\""<<JsonEscape(x.runtime_name)<<"\",\"text\":\""<<JsonEscape(x.text)<<"\",\"sha256\":\""<<JsonEscape(x.sha256)<<"\"}";}
  o<<"],\"targets\":[";
  for(std::size_t i=0;i<v.targets.size();++i){if(i)o<<',';const auto&x=v.targets[i];
    o<<"{\"index\":"<<x.index<<",\"kind\":\""<<JsonEscape(x.kind)<<"\",\"runtime_name\":\""<<JsonEscape(x.runtime_name)<<"\",\"definition_key\":";text(x.definition_key);
    o<<",\"label\":";text(x.label);o<<",\"effective_visible\":"<<x.effective_visible<<",\"enabled\":"<<x.enabled<<'}';}
  o<<']';
  if(v.holding_tracks){const auto&t=*v.holding_tracks;
    o<<",\"holding_tracks\":{\"available\":"<<t.available<<",\"unavailable_reason\":";
    if(t.unavailable_reason.empty())o<<"null";else o<<'"'<<JsonEscape(t.unavailable_reason)<<'"';
    o<<",\"owner_bound\":"<<t.owner_bound<<",\"window_exists\":";scalar(t.window_exists);
    o<<",\"root_exists\":";scalar(t.root_exists);o<<",\"effective_visible\":";scalar(t.effective_visible);
    o<<",\"selection_category_id\":";scalar(t.selection_category_id);o<<",\"selection_mode\":";scalar(t.selection_mode);
    o<<",\"selection_action_raw\":";scalar(t.selection_action_raw);o<<",\"selected_building_key\":";text(t.selected_building_key);o<<'}';
  }
  o<<'}';
}
