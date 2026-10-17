#include "xar_bridge/ck3_12004_holy_site_relic_actions.hpp"
#include <iomanip>
#include <sstream>

namespace xar::ck3_12004::religion::relic_actions {
namespace {
std::string Quote(std::string_view s) {
 std::ostringstream out;out<<'"';for(const unsigned char c:s){
  if(c=='"'||c=='\\')out<<'\\'<<c;
  else if(c<32)out<<"\\u"<<std::hex<<std::setw(4)<<std::setfill('0')<<static_cast<unsigned int>(c)<<std::dec;
  else out<<c;
 }out<<'"';return out.str();
}
void Id(std::ostringstream&o,std::optional<std::uint32_t>v){if(v)o<<*v;else o<<"null";}
void SelectionJson(std::ostringstream&o,const Selection&s){
 o<<"{\"available\":"<<s.available<<",\"artifact_id\":";Id(o,s.artifact_id);
 o<<",\"slot_index\":";Id(o,s.slot_index);o<<",\"slot_artifact_ids\":";
 if(!s.available)o<<"null";else{ o<<'[';for(std::size_t i=0;i<s.slot_artifact_ids.size();++i){if(i)o<<',';Id(o,s.slot_artifact_ids[i]);}o<<']';}
 o<<",\"unavailable_reason\":"<<Quote(s.unavailable_reason)<<'}';
}
}
std::string SerializeHolySiteRelicAction12004(const Result&r) {
 std::ostringstream o;o<<std::boolalpha;
 o<<"{\"available\":"<<r.available<<",\"status\":"<<Quote(r.status)
 <<",\"loaded_source_pins_verified\":"<<r.loaded_source_pins_verified
 <<",\"native_dispatch_attempted\":"<<r.native_dispatch_attempted<<",\"dispatch_invoked\":"<<r.dispatch_invoked
 <<",\"verification_pending\":"<<r.verification_pending<<",\"already_in_requested_state\":"<<r.already_in_requested_state
 <<",\"selection_postcondition_observed\":"<<r.selection_postcondition_observed
 <<",\"original_button_enabled_observed\":"<<r.original_button_enabled_observed<<",\"original_button_enabled\":";
 if(r.original_button_enabled)o<<*r.original_button_enabled;else o<<"null";
 o<<",\"actual_button_presentation_observed\":"<<r.actual_button_presentation_observed<<",\"button_child_path\":"<<Quote(r.button_child_path)
 <<",\"frozen_preview_verified\":"<<r.frozen_preview_verified<<",\"gameplay_command_may_have_been_queued\":"<<r.gameplay_command_may_have_been_queued
 <<",\"business_outcome_observed\":false,\"action_ready\":false,\"before\":";
 SelectionJson(o,r.before);o<<",\"after\":";SelectionJson(o,r.after);
 o<<",\"unavailable_reason\":"<<Quote(r.unavailable_reason)<<'}';return o.str();
}
}
