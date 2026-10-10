#pragma once
#include "xar_bridge/army_actual_assault_consumer_observations_v1.hpp"
#include <charconv>
#include <string>
#include <type_traits>
namespace xar::ck3_12004::assault_consumer_json_detail {
struct Object {
  std::string &out; bool first=true;
  explicit Object(std::string &s):out(s){out+='{' ;}
  ~Object(){out+='}';}
  void Key(const char *key){if(!first)out+=',';first=false;out+='"';out+=key;out+="\":";}
  template<class T> void Number(const char *key,T value){Key(key);char buf[32];auto r=std::to_chars(buf,buf+sizeof(buf),value);out.append(buf,r.ptr);}
  void Bool(const char *key,bool value){Key(key);out+=value?"true":"false";}
  template<class T> void Optional(const char *key,const std::optional<T> &value){
    if(!value){Key(key);out+="null";}else if constexpr(std::is_same_v<T,bool>)Bool(key,*value);
    else Number(key,*value);
  }
  void Text(const char *key,const char *value){Key(key);out+='"';out+=value;out+='"';}
};
inline void Token(std::string &s,const ArmyNaturalPhaseEvent12004 &v){Object o(s);o.Number("clock_identity",v.clock_identity);o.Number("sequence",v.sequence);o.Optional("thread_id",v.thread_id);}
inline void Resolved(std::string &s,const AssaultConsumerResolved12004 &v){Object o(s);o.Optional("requested_full_id_u32",v.requested_full_id);o.Optional("object_identity",v.object_identity);o.Optional("selected_full_id_u32",v.selected_full_id);o.Optional("used_fallback",v.used_fallback);}
template<class T,class F> void Array(std::string &s,const std::vector<T> &v,F emit){s+='[';bool first=true;for(const auto &x:v){if(!first)s+=',';first=false;emit(s,x);}s+=']';}
inline void Vector(std::string &s,const AssaultConsumerVector12004 &v){Object o(s);o.Optional("data_identity",v.data_identity);o.Optional("capacity_raw_i32",v.capacity);o.Optional("count_raw_i32",v.count);o.Optional("allocator_identity",v.allocator_identity);o.Bool("references_complete",v.references_complete);o.Key("ordered_full_ids_u32");Array(s,v.ordered_full_ids,[](auto &out,const auto &raw){if(!raw)out+="null";else{char buf[32];auto r=std::to_chars(buf,buf+32,*raw);out.append(buf,r.ptr);}});}
inline void Army(std::string &s,const AssaultConsumerArmy12004 &v){Object o(s);o.Number("native_index",v.native_index);o.Key("resolution");Resolved(s,v.resolution);o.Key("regiment_roster");Vector(s,v.regiment_roster);o.Optional("native_whole_current_soldiers",v.native_whole_current_soldiers);}
inline void Group(std::string &s,const AssaultConsumerGroup12004 &v){Object o(s);o.Number("native_index",v.native_index);o.Number("physical_slot_i64",v.physical_slot);o.Optional("control_raw_u8",v.control);o.Optional("hash_raw_u32",v.hash);o.Optional("siege_full_id_u32",v.siege_full_id);o.Key("siege_resolution");Resolved(s,v.siege_resolution);o.Optional("province_identity",v.province_identity);o.Optional("province_magic_raw_u32",v.province_magic);o.Optional("province_full_id_u32",v.province_full_id);o.Optional("breach_level_raw_i32",v.breach_level);o.Optional("native_current_expected_loss",v.native_current_expected_loss);o.Bool("natural_budget_observed",v.natural_budget_observed);o.Key("budget_entry_event");Token(s,v.budget_entry_event);o.Key("budget_returned_event");Token(s,v.budget_returned_event);o.Bool("besieging_dependencies_complete",v.besieging_dependencies_complete);o.Key("armies");Vector(s,v.armies);o.Key("arrgs");Vector(s,v.arrgs);o.Key("army_occurrences");Array(s,v.army_occurrences,Army);}
inline void Table(std::string &s,const AssaultConsumerTable12004 &v){Object o(s);o.Optional("entries_identity",v.entries_identity);o.Optional("occupied_count_raw_i32",v.occupied_count);o.Optional("mask_raw_i32",v.mask);o.Optional("end_slot_raw_i32",v.end_slot);o.Optional("tail_distance_raw_u8",v.tail_distance);o.Optional("end_marker_control_raw_u8",v.end_marker_control);o.Optional("load_factor_f32_bits_u32",v.load_factor_bits);o.Bool("controls_complete",v.controls_complete);o.Bool("raw_references_complete",v.raw_references_complete);o.Key("physical_controls");Array(s,v.physical_controls,[](auto &out,const auto &raw){if(!raw)out+="null";else{char buf[32];auto r=std::to_chars(buf,buf+32,*raw);out.append(buf,r.ptr);}});o.Key("groups");Array(s,v.groups,Group);}
inline void Physical(std::string &s,const AssaultConsumerPhysical12004 &v){Object o(s);o.Number("object_identity",v.object_identity);o.Optional("maximum_soldiers",v.maximum);o.Optional("current_soldiers",v.current);o.Optional("persistent_regiment_id",v.persistent_full_id);o.Optional("own_chunk_ordinal",v.own_ordinal);o.Optional("army_regiment_id",v.army_regiment_full_id);o.Optional("state_raw_i32",v.state);}
inline void Data(std::string &s,const AssaultConsumerData12004 &v){Object o(s);o.Number("native_index",v.native_index);o.Optional("persistent_full_id_u32",v.persistent_full_id);o.Optional("data_chunk_ordinal",v.data_ordinal);o.Key("persistent_resolution");Resolved(s,v.persistent_resolution);o.Optional("persistent_identity_valid",v.persistent_identity_valid);o.Bool("ready",v.ready);o.Key("physical");if(v.physical)Physical(s,*v.physical);else s+="null";}
inline void Regiment(std::string &s,const AssaultConsumerRegiment12004 &v){Object o(s);o.Key("resolution");Resolved(s,v.resolution);o.Optional("magic_raw_u32",v.magic);o.Optional("identity_valid",v.identity_valid);o.Optional("native_loss_writer_skipped",v.native_loss_writer_skipped);o.Optional("current_soldiers",v.current);o.Optional("maximum_soldiers",v.maximum);o.Optional("definition_type_raw_i32",v.definition_type);o.Optional("data_identity",v.data_identity);o.Optional("data_capacity_raw_i32",v.data_capacity);o.Optional("data_count_raw_i32",v.data_count);o.Bool("data_complete",v.data_complete);o.Optional("same_instance_after",v.same_instance_after);o.Optional("same_data_header_after",v.same_data_header_after);o.Key("data_records");Array(s,v.data_records,Data);}
inline void Parent(std::string &s,const ArmyAssaultConsumerParent12004 &v){Object o(s);o.Bool("active",v.active);o.Bool("exact_post_date_parent",v.exact_post_date_parent);o.Number("actual_entry_rva",v.actual_entry_rva);o.Optional("caller_return_rva",v.caller_return_rva);o.Number("manager_identity",v.manager_identity);o.Key("entry_event");Token(s,v.entry_event);o.Key("phase_entry_event");Token(s,v.phase_entry_event);o.Optional("date_raw",v.date_raw);o.Optional("absolute_day_raw",v.absolute_day_raw);}
inline void Event(std::string &s,const ArmyActualAssaultConsumerObservationV1 &v){Object o(s);o.Number("journal_sequence",v.journal_sequence);o.Text("capture_stage","natural_2A97EB0_entry_and_return");o.Key("parent");Parent(s,v.parent);o.Key("returned_event");Token(s,v.returned_event);o.Bool("original_called",v.original_called);o.Bool("original_returned",v.original_returned);o.Bool("current_session_guard",v.current_session_guard);o.Bool("actual",v.current_session_guard&&v.parent.exact_post_date_parent&&v.original_returned);o.Number("raw_return_bits",v.raw_return_bits);o.Number("capture_failure_flags",v.capture_failure_flags);o.Key("entry_table");Table(s,v.entry_table);o.Key("returned_table");Table(s,v.returned_table);o.Key("entry_pending_queue");Vector(s,v.entry_pending_queue);o.Key("returned_pending_queue");Vector(s,v.returned_pending_queue);o.Key("entry_regiments");Array(s,v.entry_regiments,Regiment);o.Key("returned_regiments");Array(s,v.returned_regiments,Regiment);o.Bool("entry_dependencies_complete",v.entry_dependencies_complete);o.Bool("returned_dependencies_complete",v.returned_dependencies_complete);o.Bool("conditional_stage_binding_ready",v.conditional_stage_binding_ready);o.Bool("full_daily",false);o.Bool("full_monthly",false);}
} // namespace xar::ck3_12004::assault_consumer_json_detail
namespace xar::game {
inline void AppendArmyActualAssaultConsumerObservations12004(std::string &s,
    const ck3_12004::ArmyActualAssaultConsumerObservationsV1 &v){
  using namespace ck3_12004::assault_consumer_json_detail;Object o(s);
  o.Number("schema_version",1);o.Text("source","native_actual_assault_consumer_entry_return");
  o.Text("membership_basis","captured_entry_group_army_full_ids");o.Bool("observer_installed",v.observer_installed);
  o.Bool("current_session_guard",v.current_session_guard);o.Number("latest_journal_sequence",v.latest_journal_sequence);
  o.Number("overwritten_events",v.overwritten_events);o.Key("events");Array(s,v.events,Event);
}
} // namespace xar::game
