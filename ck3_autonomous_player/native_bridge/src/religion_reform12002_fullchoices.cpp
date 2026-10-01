#include "xar_bridge/religion_reform12002_fullchoices.hpp"
#include "xar_bridge/religion_reform12002_group_model.hpp"
#include <cstring>

namespace xar::ck3_12002::religion_reform {
namespace {
template<class T> T Load(const void *p,std::size_t offset) {
  T value{};std::memcpy(&value,static_cast<const std::byte *>(p)+offset,sizeof(value));return value;
}
const std::byte *At(const void *p,std::size_t offset) { return static_cast<const std::byte *>(p)+offset; }
struct ArrayView { const std::byte *data{};std::int32_t count{}; };
bool Array(const void *p,ArrayView &value) {
  value={Load<const std::byte *>(p,0),Load<std::int32_t>(p,0xC)};
  return value.count>=0&&value.count<=8192&&value.count<=Load<std::int32_t>(p,8)&&(!value.count||value.data);
}
bool Same(const void *p,const ArrayView &value) {
  return Load<const std::byte *>(p,0)==value.data&&Load<std::int32_t>(p,0xC)==value.count;
}
bool Fail(DraftFullDoctrineChoices &value,const char *reason) { value.failure=reason;return false; }
bool ReadOnce(const DraftChoiceBindings &b,std::uint64_t epoch,DraftFullDoctrineChoices &out) {
  DraftWindowView window{};
  if(!ReadCurrentRiteCreationWindow12002(b.window,epoch,window)) return Fail(out,DraftWindowFailureKey(window.failure));
  out.capture_epoch=epoch;out.date_raw=window.date_raw;out.played_character_id=window.played_character_id;out.source_rite_id=window.source_rite_id;
  if(!window.window) {out.available=true;out.failure="none";return true;}
  auto *actor=ResolveCoreCharacter(b.window.core,static_cast<std::int32_t>(window.played_character_id));
  if(!actor)return Fail(out,"played_character_unavailable");
  const auto *scope=At(window.window,kDraftTopScopeOffset);
  const auto *slots_array=At(window.window,kDraftSelectedSlotsOffset);
  ArrayView slots{};
  if(!Array(slots_array,slots))return Fail(out,"selected_slots_unavailable");
  std::vector<const void *> selected;
  for(std::int32_t i=0;i<slots.count;++i)
    selected.push_back(Load<const void *>(slots.data,static_cast<std::size_t>(i)*kActualDraftSlotStride+kChoiceDefinitionOffset));
  for(std::int32_t i=0;i<slots.count;++i) {
    const auto *selected_definition=selected[static_cast<std::size_t>(i)];
    religion::doctrine12002::DoctrineRow selected_key{};
    if(!religion::doctrine12002::CopyDoctrineDefinition12002(selected_definition,selected_key))
      return Fail(out,"selected_doctrine_definition_unavailable");
    DraftDoctrineChoiceSlot slot{};slot.slot_index=static_cast<std::uint32_t>(i);
    slot.group_key=std::move(selected_key.group_key);slot.selected_doctrine_key=std::move(selected_key.doctrine_key);
    const auto *group=Load<const void *>(selected_definition,religion::doctrine12002::kDoctrineGroupPointerOffset);
    const auto *source_array=At(group,kGroupDefinitionSourcesOffset);ArrayView sources{};
    if(!Array(source_array,sources))return Fail(out,"group_source_collection_unavailable");
    for(std::int32_t j=0;j<sources.count;++j) {
      const auto *definition=Load<const void *>(sources.data,static_cast<std::size_t>(j)*sizeof(void *));
      religion::doctrine12002::DoctrineRow keys{};
      if(!religion::doctrine12002::CopyDoctrineDefinition12002(definition,keys))
        return Fail(out,"group_source_definition_unavailable");
      DraftDoctrineSourceChoice row{};row.source_index=static_cast<std::uint32_t>(j);row.doctrine_key=std::move(keys.doctrine_key);
      row.currently_selected=definition==selected_definition;
      if(!row.currently_selected) {
        for(const auto *other:selected)if(other==definition){row.duplicate_excluded=true;break;}
      }
      if(!row.duplicate_excluded) {
        row.passed_shown=b.evaluate_trigger(At(definition,0x1B8),scope);
        row.native_can_pick=*row.passed_shown&&b.evaluate_trigger(At(definition,0xE8),scope);
        if(*row.native_can_pick) {
          row.native_knows_doctrine=b.knows_doctrine(actor,definition);
          if(!*row.native_knows_doctrine) {
            const auto *database=b.perk_database_global?*b.perk_database_global:nullptr;
            const auto *prophet=database?Load<const void *>(database,kProphetPerkCacheOffset):nullptr;
            if(!prophet)return Fail(out,"prophet_definition_unavailable");
            row.native_has_prophet=b.has_perk(actor,prophet);
          }
          row.final_selectable=*row.native_knows_doctrine||row.native_has_prophet.value_or(false);
        }
      }
      slot.sources.push_back(std::move(row));
    }
    if(!Same(source_array,sources))return Fail(out,"state_changed");
    out.slots.push_back(std::move(slot));
  }
  if(!Same(slots_array,slots))return Fail(out,"state_changed");
  for(std::int32_t i=0;i<slots.count;++i)
    if(Load<const void *>(slots.data,static_cast<std::size_t>(i)*kActualDraftSlotStride+kChoiceDefinitionOffset)!=selected[static_cast<std::size_t>(i)])
      return Fail(out,"state_changed");
  DraftWindowView after{};
  if(!ReadCurrentRiteCreationWindow12002(b.window,epoch,after)||after.window!=window.window||after.date_raw!=window.date_raw||
     after.played_character_id!=window.played_character_id||after.source_rite_id!=window.source_rite_id||
     ResolveCoreCharacter(b.window.core,static_cast<std::int32_t>(window.played_character_id))!=actor)
    return Fail(out,"state_changed");
  out.available=true;out.draft_observed=true;out.doctrine_gates_complete=true;out.failure="none";return true;
}
std::string Quote(std::string_view value) {
  std::string text="\"";constexpr char hex[]="0123456789abcdef";
  for(const unsigned char c:value) {
    if(c=='\\'||c=='"'){text+='\\';text+=static_cast<char>(c);}
    else if(c<32){text+="\\u00";text+=hex[c>>4];text+=hex[c&15];}
    else text+=static_cast<char>(c);
  }return text+'"';
}
const char *Bool(bool value){return value?"true":"false";}
std::string Optional(const std::optional<bool> &value){return value?Bool(*value):"null";}
} // namespace
bool ReadCurrentDraftFullDoctrineChoices12002(const DraftChoiceBindings &b,std::uint64_t epoch,DraftFullDoctrineChoices &out) noexcept {
  out={};out.capture_epoch=epoch;
  if(!b.window.enabled||!b.evaluate_trigger||!b.knows_doctrine||!b.has_perk)return false;
  DraftFullDoctrineChoices candidate{};candidate.capture_epoch=epoch;bool ok=false;
#if defined(_WIN32)&&defined(_MSC_VER)
  auto guarded=[](const DraftChoiceBindings &binding,std::uint64_t e,DraftFullDoctrineChoices &value)->bool {
    __try{return ReadOnce(binding,e,value);}__except(1){value.failure="full_doctrine_choices_layout_unavailable";return false;}
  };ok=guarded(b,epoch,candidate);
#else
  ok=ReadOnce(b,epoch,candidate);
#endif
  if(ok)out=std::move(candidate);
  else {out.failure=std::move(candidate.failure);out.date_raw=candidate.date_raw;out.played_character_id=candidate.played_character_id;}
  return ok;
}
std::string SerializeCurrentDraftFullDoctrineChoices12002(const DraftFullDoctrineChoices &value) {
  std::string slots="[";
  for(const auto &slot:value.slots) {
    if(slots.size()>1)slots+=',';std::string sources="[";
    for(const auto &row:slot.sources) {
      if(sources.size()>1)sources+=',';
      sources+="{\"source_index\":"+std::to_string(row.source_index)+",\"doctrine_key\":"+Quote(row.doctrine_key)+
        ",\"currently_selected\":"+Bool(row.currently_selected)+",\"duplicate_excluded\":"+Bool(row.duplicate_excluded)+
        ",\"passed_shown\":"+Optional(row.passed_shown)+",\"native_can_pick\":"+Optional(row.native_can_pick)+
        ",\"native_knows_doctrine\":"+Optional(row.native_knows_doctrine)+",\"native_has_prophet\":"+Optional(row.native_has_prophet)+
        ",\"final_selectable\":"+Bool(row.final_selectable)+'}';
    }
    slots+="{\"slot_index\":"+std::to_string(slot.slot_index)+",\"group_key\":"+Quote(slot.group_key)+
      ",\"selected_doctrine_key\":"+Quote(slot.selected_doctrine_key)+",\"sources\":"+sources+"]}";
  }
  return "{\"schema\":\"ck3_12002_current_draft_full_doctrine_choices_v1\",\"game_version\":\"1.20.0.2\",\"executable_sha256\":"+
    Quote(kExecutableSha256)+",\"scope\":\"actual_current_draft_selected_slot_group_sources\",\"available\":"+Bool(value.available)+
    ",\"unavailable_reason\":"+(value.available?"null":Quote(value.failure))+",\"capture_epoch\":"+std::to_string(value.capture_epoch)+
    ",\"date_raw\":"+std::to_string(value.date_raw)+",\"played_character_id\":"+std::to_string(value.played_character_id)+
    ",\"source_rite_id\":"+(value.source_rite_id?std::to_string(*value.source_rite_id):"null")+
    ",\"draft_observed\":"+Bool(value.draft_observed)+",\"doctrine_gates_complete\":"+Bool(value.doctrine_gates_complete)+",\"slots\":"+slots+"]}";
}
} // namespace xar::ck3_12002::religion_reform
