#include "xar_bridge/ck3_12004_holy_site_relic_recognition_matrix.hpp"
#include <sstream>
#include <string_view>

namespace xar::ck3_12004::religion::holy_site_relic {
namespace {
std::string Quoted(std::string_view value) {
  constexpr char hex[]="0123456789abcdef";
  std::string out="\"";
  for(unsigned char c:value){
    switch(c){case '"':out+="\\\"";break;case '\\':out+="\\\\";break;
      case '\n':out+="\\n";break;case '\r':out+="\\r";break;case '\t':out+="\\t";break;
      default:if(c<32){out+="\\u00";out+=hex[c>>4];out+=hex[c&15];}else out+=static_cast<char>(c);}
  }
  out+='"';return out;
}
void Reason(std::ostream &o,const std::string &reason){if(reason.empty())o<<"null";else o<<Quoted(reason);}
void Id(std::ostream &o,std::optional<std::uint32_t> id){if(id)o<<*id;else o<<"null";}
template<class T>void Ids(std::ostream &o,const std::vector<T> &values){
  o<<'[';bool first=true;for(const auto &id:values){if(!first)o<<',';first=false;Id(o,id);}o<<']';
}
}
std::string SerializeHolySiteRelicRecognitionMatrix12004(const RecognitionMatrix &v){
  std::ostringstream o;o<<std::boolalpha;
  o<<"{\"schema\":\"ck3_12004_holy_site_relic_recognition_matrix_v1\",\"available\":"<<v.available
    <<",\"complete\":"<<v.complete<<",\"source_arrays_stable\":"<<v.source_arrays_stable
    <<",\"evaluation_atomic\":false,\"benefits_observed\":false,\"world_cache_written\":false,\"read_only\":true"
    <<",\"holy_site_id\":"<<v.holy_site_id<<",\"capture_epoch\":"<<v.capture_epoch
    <<",\"date_raw\":"<<v.date_raw<<",\"played_character_id\":"<<v.played_character_id
    <<",\"faith_deduplication\":\"first_seen_full_id_associated_player_county_holder\""
    <<",\"artifact_deduplication\":\"first_seen_full_id_slots_window_candidates_action_request\""
    <<",\"faith_sources\":{\"associated_available\":"<<v.associated_available<<",\"associated_faith_ids\":";
  if(v.associated_available)Ids(o,v.associated_faith_ids);else o<<"null";
  o<<",\"player_faith_id\":";Id(o,v.player_faith_id);o<<",\"county_holder_faith_id\":";Id(o,v.county_holder_faith_id);
  o<<"},\"artifact_sources\":{\"slots_available\":"<<v.slots_available<<",\"slot_artifact_ids\":";
  if(v.slots_available)Ids(o,v.slot_artifact_ids);else o<<"null";
  o<<",\"window_candidates_available\":"<<v.window_candidates_available<<",\"window_candidate_artifact_ids\":";
  if(v.window_candidates_available)Ids(o,v.window_candidate_artifact_ids);else o<<"null";
  o<<",\"requested_action_artifact_id\":";Id(o,v.requested_action_artifact_id);o<<"},\"faiths\":[";
  bool first=true;for(const auto &f:v.faiths){if(!first)o<<',';first=false;
    o<<"{\"faith_id\":"<<f.faith_id<<",\"source_associated\":"<<f.source_associated
      <<",\"source_player\":"<<f.source_player<<",\"source_county_holder\":"<<f.source_county_holder
      <<",\"object_resolved\":"<<f.object_resolved<<",\"unavailable_reason\":";Reason(o,f.unavailable_reason);o<<'}';}
  o<<"],\"artifacts\":[";first=true;for(const auto &a:v.artifacts){if(!first)o<<',';first=false;
    o<<"{\"artifact_id\":"<<a.artifact_id<<",\"slot_indices\":";Ids(o,a.slot_indices);
    o<<",\"candidate_indices\":";Ids(o,a.candidate_indices);
    o<<",\"source_action_request\":"<<a.source_action_request<<",\"object_resolved\":"<<a.object_resolved
      <<",\"unavailable_reason\":";Reason(o,a.unavailable_reason);o<<'}';}
  o<<"],\"cells\":[";first=true;for(const auto &c:v.cells){if(!first)o<<',';first=false;
    o<<"{\"artifact_id\":"<<c.artifact_id<<",\"faith_id\":"<<c.faith_id<<",\"available\":"<<c.available<<",\"value\":";
    if(c.value.has_value())o<<*c.value;else o<<"null";
    o<<",\"unavailable_reason\":";Reason(o,c.unavailable_reason);o<<'}';}
  o<<"],\"native_getter_calls\":"<<v.native_getter_calls<<",\"max_native_getter_calls\":"<<RecognitionMatrix::max_native_getter_calls
    <<",\"limits\":{\"faiths\":"<<RecognitionMatrix::max_faiths<<",\"slots\":"<<RecognitionMatrix::max_slots
    <<",\"candidates\":"<<RecognitionMatrix::max_candidates<<",\"artifacts\":"<<RecognitionMatrix::max_artifacts
    <<"},\"unavailable_reason\":";Reason(o,v.unavailable_reason);o<<'}';return o.str();
}
}
