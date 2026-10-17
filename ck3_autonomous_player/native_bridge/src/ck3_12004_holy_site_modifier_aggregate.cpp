#include "xar_bridge/ck3_12004_holy_site_modifier_aggregate.hpp"
#include "xar_bridge/ck3_12004_holy_site_relic_context.hpp"
#include "xar_bridge/construction_character_modifier_2c4d1d0_12004.hpp"
#include <algorithm>
#include <array>
#include <limits>
#include <utility>

namespace xar::ck3_12004::religion::holy_site_relic {
namespace {
constexpr std::uint32_t absent=0xFFFFFFFFU;
const void *At(const void *p,std::size_t offset)noexcept{
 const auto a=reinterpret_cast<std::uintptr_t>(p);
 return a&&offset<=std::numeric_limits<std::uintptr_t>::max()-a?reinterpret_cast<const void*>(a+offset):nullptr;
}
template<class T>bool Read(const Bindings &b,const void *p,std::size_t offset,T &out)noexcept{
 const auto *a=At(p,offset);return a&&b.read_memory&&b.read_memory(b.read_context,a,&out,sizeof(out));
}
const void *Resolve(const Bindings &b,void **global,std::uint32_t id,std::size_t offset)noexcept{
 const void *storage=nullptr,*rows=nullptr,*object=nullptr;std::uint32_t count=0,physical=absent;
 if(id==absent||!Read(b,global,0,storage)||!storage||!Read(b,storage,0x20,rows)||!rows||
  !Read(b,storage,0x2C,count)||(id&0xFFFFFFU)>=count||
  !Read(b,rows,static_cast<std::size_t>(id&0xFFFFFFU)*16+8,object)||!object||
  !Read(b,object,offset,physical)||physical!=id)return nullptr;
 return object;
}
struct PcState {
 const void *keys=nullptr,*values=nullptr;std::int32_t count=0;
 std::vector<std::uint16_t> key_rows;std::vector<std::int64_t> value_rows;
 bool operator==(const PcState &)const=default;
};
bool Pc(const Bindings &b,const void *pc,FixedModifierBlock &out,PcState &state){
 std::int32_t count=-1;
 if(!Read(b,pc,0xC,count)){out.unavailable_reason="fixed_pc_count_unavailable";return false;}
 out.count_raw=count;
 state.count=count;
 if(count<0||static_cast<std::uint32_t>(count)>ModifierAggregateObservation::max_definition_entries_per_block){
  out.unavailable_reason="fixed_pc_source_limit_exceeded";return false;
 }
 // Actual2303100 demands these two pointers and the one key count. Do not
 // invent an independent value count/capacity prerequisite for this PC ABI.
 if(!Read(b,pc,0,state.keys)||!Read(b,pc,0x68,state.values)||(count&&(!state.keys||!state.values))){
  out.unavailable_reason="fixed_pc_pointers_unavailable";return false;}
 state.key_rows.resize(static_cast<std::size_t>(count));state.value_rows.resize(static_cast<std::size_t>(count));
 if(count&&(!b.read_memory(b.read_context,state.keys,state.key_rows.data(),state.key_rows.size()*sizeof(std::uint16_t))||
  !b.read_memory(b.read_context,state.values,state.value_rows.data(),state.value_rows.size()*sizeof(std::int64_t)))){
  out.unavailable_reason="fixed_pc_rows_unavailable";return false;
 }
 for(std::size_t i=0;i<state.key_rows.size();++i)out.entries.push_back({state.key_rows[i],state.value_rows[i]});
 out.available=true;out.unavailable_reason.clear();return true;
}
struct CharacterState {
 const void *actor=nullptr,*rite=nullptr,*faith=nullptr;
 std::uint32_t rite_id=absent,faith_id=absent;
 bool operator==(const CharacterState &)const=default;
};
bool Character(const Bindings &b,std::uint32_t id,CharacterState &s)noexcept{
 std::uint32_t magic=0;
 return (s.actor=Resolve(b,b.character_storage,id,0x18))&&Read(b,s.actor,0x1C,magic)&&magic==0x43686172U&&
  Read(b,s.actor,0xB4,s.rite_id)&&(s.rite=Resolve(b,b.rite_storage,s.rite_id,8))&&
  Read(b,s.rite,0x4B8,s.faith_id)&&(s.faith=Resolve(b,b.faith_storage,s.faith_id,8));
}
struct CountyState {
 const void *barony=nullptr,*county=nullptr;std::uint32_t barony_id=absent,county_id=absent,holder_id=absent;
 bool operator==(const CountyState &)const=default;
};
bool County(const Bindings &b,const void *site,CountyState &s)noexcept{
 return Read(b,site,0xB0,s.barony_id)&&(s.barony=Resolve(b,b.title_storage,s.barony_id,0x10))&&
  Read(b,s.barony,0x108,s.county_id)&&(s.county=Resolve(b,b.title_storage,s.county_id,0x10))&&
  Read(b,s.county,0x128,s.holder_id)&&s.holder_id!=absent;
}
void Invalidate(ModifierAggregateObservation &out,const char *why){
 out.available=false;out.complete=false;out.source_arrays_stable=false;out.unavailable_reason=why;
 for(auto &block:out.definition_blocks){block.available=false;block.entries.clear();block.unavailable_reason=why;}
 for(auto &recipient:out.recipients){recipient.available=false;recipient.owned_aggregate_observed=false;
  recipient.values.clear();recipient.unavailable_reason=why;}
}
struct RecipientState {
 CharacterState actor{};std::uintptr_t extension=0,model=0,owner=0;
 bool operator==(const RecipientState &)const=default;
};
void Recipient(const Bindings &b,const std::vector<std::uint16_t> &keys,ModifierRecipient &out,RecipientState &state){
 auto &actor=state.actor;
 if(!Character(b,out.character_id,actor)){out.unavailable_reason="derived_character_rite_faith_unavailable";}
 else {
  out.rite_id=actor.rite_id;out.faith_id=actor.faith_id;
  construction_owner_mode3::RawReceiverAccessV1 access{b.read_context,b.read_memory,b.image_base,true};
  // Resolve the original owned-cache branch even for an empty definition grid.
  // The read helper's initialized default is not actual recipient evidence.
  auto &extension=state.extension;auto &model=state.model;auto &owner=state.owner;
  if(Read(b,actor.actor,0x1B0,extension)&&extension&&Read(b,reinterpret_cast<const void*>(extension),0x258,model)&&model&&
   Read(b,reinterpret_cast<const void*>(model),8,owner)&&owner==reinterpret_cast<std::uintptr_t>(actor.actor)){
   out.owned_aggregate_observed=true;out.available=true;out.unavailable_reason.clear();
   for(auto key:keys){
    AggregateModifierValue value{};value.key_raw_u16=key;
    const auto scalar=construction_owner_mode3::ReadCharacterModifier2C4D1D012004(access,reinterpret_cast<std::uintptr_t>(actor.actor),key,0,100000);
    if(scalar.ready&&scalar.value_raw_q64&&scalar.context.source==ConceptionModifierContextSource12004::OwnedCharacter&&
     scalar.context.model_address==model){value.available=true;value.aggregate_raw_q64=scalar.value_raw_q64;value.unavailable_reason.clear();}
    else {out.available=false;out.unavailable_reason="actual_owned_character_aggregate_key_unavailable";}
    out.values.push_back(std::move(value));
   }
  }else out.unavailable_reason="actual_owned_character_aggregate_unavailable";
 }
 if(!out.available){
  out.values.clear();
  for(auto key:keys){AggregateModifierValue value{};value.key_raw_u16=key;value.unavailable_reason=out.unavailable_reason;out.values.push_back(std::move(value));}
 }
}
}
bool ReadHolySiteModifierAggregate12004(const Bindings &b,const ck3_12002::religion::Context &c,
 std::uint32_t site_id,ModifierAggregateObservation &out)noexcept{
 out={};out.capture_epoch=c.capture_epoch;out.date_raw=c.date_raw;out.played_character_id=c.played_character_id;out.holy_site_id=site_id;
 out.definition_blocks.resize(2);out.definition_blocks[0].kind="faith_fixed";out.definition_blocks[1].kind="local_fixed";
 try{
  if(!b.enabled||!b.image_base||!b.read_memory||!c.available||!c.capture_epoch||c.played_character_id<=0||!c.rite_id||!c.faith_id){
   Invalidate(out,"modifier_aggregate_current_player_context_unavailable");return false;
  }
  const void *site=Resolve(b,b.holy_site_storage,site_id,0x10),*type=nullptr;std::uint32_t magic=0;
  CharacterState current{};
  if(!site||!Read(b,site,0x14,magic)||magic!=0x486F5374U||!Read(b,site,0x20,type)||!type||
   !Character(b,static_cast<std::uint32_t>(c.played_character_id),current)||current.rite_id!=*c.rite_id||current.faith_id!=*c.faith_id){
   Invalidate(out,"modifier_aggregate_site_type_or_player_full_reference_unavailable");return false;
  }
  const std::array<std::size_t,2> offsets{0x58,0x218};std::array<PcState,2> pcs{};
  for(std::size_t i=0;i<2;++i)if(!Pc(b,At(type,offsets[i]),out.definition_blocks[i],pcs[i])){
   Invalidate(out,"modifier_aggregate_fixed_pc_unavailable_or_over_limit");return false;
  }
  std::vector<std::uint16_t> keys;
  for(const auto &block:out.definition_blocks)for(const auto &entry:block.entries)
   if(entry.key_raw_u16!=0xFFFF&&std::find(keys.begin(),keys.end(),entry.key_raw_u16)==keys.end())keys.push_back(entry.key_raw_u16);
  if(keys.size()>ModifierAggregateObservation::max_unique_keys){Invalidate(out,"modifier_aggregate_key_union_limit_exceeded");return false;}
  CountyState county{};const bool county_available=County(b,site,county);
  ModifierRecipient player_row{};player_row.character_id=static_cast<std::uint32_t>(c.played_character_id);player_row.source_player=true;
  if(county_available){out.county_holder_character_id=county.holder_id;player_row.source_county_holder=county.holder_id==player_row.character_id;}
  out.recipients.push_back(std::move(player_row));
  if(county_available&&county.holder_id!=static_cast<std::uint32_t>(c.played_character_id)){
   ModifierRecipient holder{};holder.character_id=county.holder_id;holder.source_county_holder=true;out.recipients.push_back(std::move(holder));
  }
  std::vector<RecipientState> recipient_states(out.recipients.size());
  for(std::size_t i=0;i<out.recipients.size();++i)Recipient(b,keys,out.recipients[i],recipient_states[i]);
  const void *after_type=nullptr;CharacterState after_player{};CountyState after_county{};
  bool stable=Resolve(b,b.holy_site_storage,site_id,0x10)==site&&Read(b,site,0x20,after_type)&&after_type==type&&
   Character(b,static_cast<std::uint32_t>(c.played_character_id),after_player)&&after_player==current;
  const bool after_county_available=County(b,site,after_county);
  stable=stable&&after_county_available==county_available&&(!county_available||after_county==county);
  for(std::size_t i=0;i<2;++i){FixedModifierBlock block{};PcState state{};
   stable=stable&&Pc(b,At(type,offsets[i]),block,state)&&state==pcs[i];}
  for(std::size_t i=0;i<out.recipients.size();++i){const auto &row=out.recipients[i];
   ModifierRecipient after{};RecipientState state{};after.character_id=row.character_id;after.source_player=row.source_player;
   after.source_county_holder=row.source_county_holder;Recipient(b,keys,after,state);
   stable=stable&&after==row&&state==recipient_states[i];}
  if(!stable){Invalidate(out,"modifier_aggregate_sources_changed_during_copy");return false;}
  out.available=true;out.source_arrays_stable=true;
  out.complete=county_available&&std::all_of(out.recipients.begin(),out.recipients.end(),[](const auto &r){return r.available&&r.owned_aggregate_observed;});
  out.unavailable_reason=out.complete?"":"modifier_aggregate_partial_recipient_or_county_sources";return true;
 }catch(...){Invalidate(out,"modifier_aggregate_copy_exception");return false;}
}
}
