#include "xar_bridge/ck3_12004_holy_site_modifier_aggregate.hpp"
#include <sstream>
#include <string_view>

namespace xar::ck3_12004::religion::holy_site_relic {
namespace {
std::string Quote(std::string_view value){
 static constexpr char hex[]="0123456789abcdef";std::string out="\"";
 for(unsigned char c:value){if(c=='"'||c=='\\'){out+='\\';out+=static_cast<char>(c);}
  else if(c<32){out+="\\u00";out+=hex[c>>4];out+=hex[c&15];}else out+=static_cast<char>(c);}
 return out+'"';
}
void Reason(std::ostream &o,const std::string &value){if(value.empty())o<<"null";else o<<Quote(value);}
template<class T>void Number(std::ostream &o,std::optional<T> value){if(value)o<<*value;else o<<"null";}
}
std::string SerializeHolySiteModifierAggregate12004(const ModifierAggregateObservation &v){
 std::ostringstream o;o<<std::boolalpha;
 o<<"{\"schema\":\"ck3_12004_holy_site_modifier_aggregate_v1\",\"available\":"<<v.available
  <<",\"complete\":"<<v.complete<<",\"source_arrays_stable\":"<<v.source_arrays_stable
  <<",\"capture_epoch\":"<<v.capture_epoch<<",\"date_raw\":"<<v.date_raw<<",\"played_character_id\":"<<v.played_character_id
  <<",\"holy_site_id\":"<<v.holy_site_id<<",\"county_holder_character_id\":";Number(o,v.county_holder_character_id);
 o<<",\"read_only\":true,\"native_functions_called\":false,\"evaluation_atomic\":false,\"names_bound\":false,"
  "\"site_attribution_observed\":false,\"scaled_effects_observed\":false,\"definition_blocks\":[";
 bool first=true;for(const auto &block:v.definition_blocks){if(!first)o<<',';first=false;
  o<<"{\"kind\":"<<Quote(block.kind)<<",\"available\":"<<block.available<<",\"count_raw\":";Number(o,block.count_raw);
  o<<",\"entries\":[";bool entry_first=true;for(const auto &entry:block.entries){if(!entry_first)o<<',';entry_first=false;
   o<<"{\"key_raw_u16\":"<<entry.key_raw_u16<<",\"definition_raw_q64\":"<<entry.definition_raw_q64<<",\"property_name\":null}";}
  o<<"],\"unavailable_reason\":";Reason(o,block.unavailable_reason);o<<'}';
 }
 o<<"],\"recipients\":[";first=true;for(const auto &r:v.recipients){if(!first)o<<',';first=false;
  o<<"{\"character_id\":"<<r.character_id<<",\"source_player\":"<<r.source_player<<",\"source_county_holder\":"<<r.source_county_holder
   <<",\"rite_id\":";Number(o,r.rite_id);o<<",\"faith_id\":";Number(o,r.faith_id);
  o<<",\"available\":"<<r.available<<",\"owned_aggregate_observed\":"<<r.owned_aggregate_observed<<",\"values\":[";
  bool value_first=true;for(const auto &value:r.values){if(!value_first)o<<',';value_first=false;
   o<<"{\"key_raw_u16\":"<<value.key_raw_u16<<",\"available\":"<<value.available<<",\"aggregate_raw_q64\":";Number(o,value.aggregate_raw_q64);
   o<<",\"unavailable_reason\":";Reason(o,value.unavailable_reason);o<<'}';}
  o<<"],\"unavailable_reason\":";Reason(o,r.unavailable_reason);o<<'}';
 }
 o<<"],\"limits\":{\"definition_entries_per_block\":"<<ModifierAggregateObservation::max_definition_entries_per_block
  <<",\"unique_keys\":"<<ModifierAggregateObservation::max_unique_keys<<",\"recipients\":"<<ModifierAggregateObservation::max_recipients
  <<"},\"unavailable_reason\":";Reason(o,v.unavailable_reason);o<<'}';return o.str();
}
}
