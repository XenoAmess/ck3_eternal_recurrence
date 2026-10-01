#include "xar_bridge/religion_reform12002_group_model.hpp"
#include "xar_bridge/religion_doctrine12002_tenet_rows.hpp"
#include <cstring>
namespace xar::ck3_12002::religion_reform {
namespace {
template<class T> T Load(const void *p, std::size_t n) { T v{}; std::memcpy(&v, static_cast<const std::byte *>(p)+n, sizeof(v)); return v; }
const std::byte *At(const void *p, std::size_t n) { return static_cast<const std::byte *>(p)+n; }
struct Array { const std::byte *data{}; std::int32_t count{}; };
bool ReadArray(const void *p, Array &a) {
  a={Load<const std::byte *>(p,0),Load<std::int32_t>(p,0xC)};
  return a.count>=0 && a.count<=8192 && a.count<=Load<std::int32_t>(p,8) && (!a.count || a.data);
}
bool Same(const void *p,const Array &a) { return Load<const std::byte *>(p,0)==a.data && Load<std::int32_t>(p,0xC)==a.count; }
bool Fail(DraftGroupModel &v,const char *reason) { v.failure=reason; return false; }
bool ReadOnce(const DraftChoiceBindings &b,std::uint64_t epoch,DraftGroupModel &v) {
  DraftWindowView w{};
  if(!ReadCurrentRiteCreationWindow12002(b.window,epoch,w)) return Fail(v,DraftWindowFailureKey(w.failure));
  v.capture_epoch=epoch; v.date_raw=w.date_raw; v.played_character_id=w.played_character_id; v.source_rite_id=w.source_rite_id;
  if(!w.window) { v.available=true;v.failure="none";return true; }
  const auto *category=At(w.window,kDraftDoctrineCategoryOffset);
  if(Load<const void *>(category,0)!=w.window) return Fail(v,"category_owner_unavailable");
  v.founder_character_id=Load<std::uint32_t>(w.window,kDraftWindowActorIdOffset);
  if(v.founder_character_id!=w.played_character_id) return Fail(v,"draft_subject_unavailable");
  auto *founder=ResolveCoreCharacter(b.window.core,static_cast<std::int32_t>(v.founder_character_id));
  if(!founder) return Fail(v,"founder_unavailable");
  v.current_category_slot=Load<std::int32_t>(category,kCurrentCategorySlotOffset);
  if(v.current_category_slot < -1) return Fail(v,"category_slot_unavailable");
  const auto *slots_ptr=At(w.window,kDraftSelectedSlotsOffset);
  const auto *doctrine_ptr=At(category,0x20), *tenet_ptr=At(category,0x38);
  const auto *groups_ptr=At(w.window,kDraftTenetGroupArrayOffset);
  Array slots{},doctrines{},tenets{},groups{};
  if(!ReadArray(slots_ptr,slots)||!ReadArray(doctrine_ptr,doctrines)||!ReadArray(tenet_ptr,tenets)||!ReadArray(groups_ptr,groups))
    return Fail(v,"group_model_collection_unavailable");
  for(std::int32_t i=0;i<slots.count;++i) {
    const auto *definition=Load<const void *>(slots.data,static_cast<std::size_t>(i)*kActualDraftSlotStride+kChoiceDefinitionOffset);
    religion::doctrine12002::DoctrineRow key{};
    if(!religion::doctrine12002::CopyDoctrineDefinition12002(definition,key)) return Fail(v,"slot_definition_unavailable");
    DraftSlotSource row{}; row.selected_array_index=static_cast<std::uint32_t>(i);
    row.selected_definition_key=std::move(key.doctrine_key);row.group_key=std::move(key.group_key);
    const auto *group=Load<const void *>(definition,religion::doctrine12002::kDoctrineGroupPointerOffset);
    const auto *source=At(group,kGroupDefinitionSourcesOffset);Array sources{};
    if(!ReadArray(source,sources)) return Fail(v,"group_source_collection_unavailable");
    for(std::int32_t j=0;j<sources.count;++j) {
      religion::doctrine12002::DoctrineRow source_key{};
      if(!religion::doctrine12002::CopyDoctrineDefinition12002(Load<const void *>(sources.data,static_cast<std::size_t>(j)*sizeof(void *)),source_key))
        return Fail(v,"group_source_definition_unavailable");
      row.group_source_definition_keys.push_back(std::move(source_key.doctrine_key));
    }
    if(!Same(source,sources)) return Fail(v,"state_changed");
    v.selected_slots.push_back(std::move(row));
  }
  v.category_materialized=v.current_category_slot>=0;
  if(v.category_materialized) {
    if(v.current_category_slot>=slots.count) return Fail(v,"category_slot_unavailable");
    religion::doctrine12002::DoctrineRow selected{};
    const auto *definition=Load<const void *>(category,0x10);
    if(!religion::doctrine12002::CopyDoctrineDefinition12002(definition,selected)||
       Load<const void *>(category,8)!=Load<const void *>(definition,religion::doctrine12002::kDoctrineGroupPointerOffset))
      return Fail(v,"current_group_identity_unavailable");
    v.current_group_key=std::move(selected.group_key);v.current_selected_definition_key=std::move(selected.doctrine_key);
  }
  v.current_doctrine_cache_count=static_cast<std::uint32_t>(doctrines.count);
  v.current_tenet_source_count=static_cast<std::uint32_t>(tenets.count);
  v.current_tenet_group_count=static_cast<std::uint32_t>(groups.count);
  const auto *scope=At(w.window,kDraftTopScopeOffset);
  for(std::int32_t g=0;g<groups.count;++g) {
    const auto *p=groups.data+static_cast<std::size_t>(g)*kTenetGroupStride+kGroupTenetArrayOffset;Array items{};
    if(!ReadArray(p,items))return Fail(v,"tenet_group_collection_unavailable");
    for(std::int32_t i=0;i<items.count;++i) {
      const auto *item=items.data+static_cast<std::size_t>(i)*kTenetItemStride;
      MaterializedTenetGate row{};row.popup_group_index=static_cast<std::uint32_t>(g);row.popup_item_index=static_cast<std::uint32_t>(i);
      if(!religion::doctrine12002::CopyTenetDefinitionKey12002(Load<const void *>(item,kChoiceDefinitionOffset),row.tenet_key))
        return Fail(v,"tenet_definition_unavailable");
      row.native_pick_source=Load<std::uint8_t>(item,kTenetPickSourceOffset);
      if(row.native_pick_source==0) {
        const auto *database=b.perk_database_global?*b.perk_database_global:nullptr;
        if(!database||!Load<const void *>(database,kProphetPerkCacheOffset))return Fail(v,"prophet_definition_unavailable");
      }
      row.final_can_pick=b.tenet_can_pick(item,founder,scope);v.current_tenet_choices.push_back(std::move(row));
    }
    if(!Same(p,items))return Fail(v,"state_changed");
  }
  DraftWindowView after{};
  if(!Same(slots_ptr,slots)||!Same(doctrine_ptr,doctrines)||!Same(tenet_ptr,tenets)||!Same(groups_ptr,groups)||
     Load<std::int32_t>(category,kCurrentCategorySlotOffset)!=v.current_category_slot||
     !ReadCurrentRiteCreationWindow12002(b.window,epoch,after)||after.window!=w.window||after.date_raw!=w.date_raw||
     after.played_character_id!=w.played_character_id||after.source_rite_id!=w.source_rite_id)
    return Fail(v,"state_changed");
  v.available=true;v.draft_observed=true;v.current_tenet_gate_complete=v.category_materialized;v.failure="none";return true;
}
std::string Q(std::string_view value) {
  std::string s="\"";constexpr char hex[]="0123456789abcdef";
  for(const unsigned char c:value) {
    if(c=='\\'||c=='"'){s+='\\';s+=static_cast<char>(c);}
    else if(c<32){s+="\\u00";s+=hex[c>>4];s+=hex[c&15];}
    else s+=static_cast<char>(c);
  }return s+'"';
}
const char *B(bool v){return v?"true":"false";}
std::string O(const std::optional<std::string> &s){return s?Q(*s):"null";}
} // namespace
bool ReadCurrentDraftGroupModel12002(const DraftChoiceBindings &b,std::uint64_t epoch,DraftGroupModel &out) noexcept {
  out={};out.capture_epoch=epoch;if(!b.window.enabled||!b.tenet_can_pick)return false;
  DraftGroupModel candidate{};candidate.capture_epoch=epoch;bool ok=false;
#if defined(_WIN32)&&defined(_MSC_VER)
  auto guarded=[](const DraftChoiceBindings &binding,std::uint64_t e,DraftGroupModel &v)->bool {
    __try{return ReadOnce(binding,e,v);}__except(1){v.failure="group_model_layout_unavailable";return false;}
  };ok=guarded(b,epoch,candidate);
#else
  ok=ReadOnce(b,epoch,candidate);
#endif
  if(ok)out=std::move(candidate);else{out.failure=std::move(candidate.failure);out.date_raw=candidate.date_raw;out.played_character_id=candidate.played_character_id;}return ok;
}
std::string SerializeCurrentDraftGroupModel12002(const DraftGroupModel &v) {
  std::string slots="[",tenets="[";
  for(const auto &row:v.selected_slots) {
    if(slots.size()>1)slots+=',';std::string sources="[";
    for(const auto &key:row.group_source_definition_keys){if(sources.size()>1)sources+=',';sources+=Q(key);}
    slots+="{\"selected_array_index\":"+std::to_string(row.selected_array_index)+",\"selected_definition_key\":"+Q(row.selected_definition_key)+
      ",\"group_key\":"+Q(row.group_key)+",\"group_source_definition_keys\":"+sources+"]}";
  }
  for(const auto &row:v.current_tenet_choices) {
    if(tenets.size()>1)tenets+=',';
    tenets+="{\"tenet_key\":"+Q(row.tenet_key)+",\"popup_group_index\":"+std::to_string(row.popup_group_index)+
      ",\"popup_item_index\":"+std::to_string(row.popup_item_index)+",\"native_pick_source\":"+std::to_string(row.native_pick_source)+
      ",\"final_can_pick\":"+B(row.final_can_pick)+'}';
  }
  return "{\"schema\":\"ck3_12002_current_draft_group_model_v1\",\"executable_sha256\":"+Q(kExecutableSha256)+
    ",\"available\":"+B(v.available)+",\"unavailable_reason\":"+(v.available?"null":Q(v.failure))+
    ",\"capture_epoch\":"+std::to_string(v.capture_epoch)+",\"date_raw\":"+std::to_string(v.date_raw)+
    ",\"played_character_id\":"+std::to_string(v.played_character_id)+",\"founder_character_id\":"+std::to_string(v.founder_character_id)+
    ",\"source_rite_id\":"+(v.source_rite_id?std::to_string(*v.source_rite_id):"null")+",\"draft_observed\":"+B(v.draft_observed)+
    ",\"category_materialized\":"+B(v.category_materialized)+",\"current_category_slot\":"+std::to_string(v.current_category_slot)+
    ",\"current_group_key\":"+O(v.current_group_key)+",\"current_selected_definition_key\":"+O(v.current_selected_definition_key)+
    ",\"all_group_materialized_choices_complete\":false,\"group_source_scope\":\"actual_selected_slot_group_definition_sources\","
    "\"current_tenet_scope\":\"current_materialized_category_status_groups\",\"current_tenet_gate_complete\":"+B(v.current_tenet_gate_complete)+
    ",\"current_doctrine_cache_count\":"+std::to_string(v.current_doctrine_cache_count)+",\"current_tenet_source_count\":"+
    std::to_string(v.current_tenet_source_count)+",\"current_tenet_group_count\":"+std::to_string(v.current_tenet_group_count)+
    ",\"selected_slots\":"+slots+"],\"current_tenet_choices\":"+tenets+"]}";
}
} // namespace xar::ck3_12002::religion_reform
