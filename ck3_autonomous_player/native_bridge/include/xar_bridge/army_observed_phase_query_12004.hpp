#pragma once
#include "xar_bridge/army_assault_preparation_placement_observations_12004_serializer.hpp"
#include "xar_bridge/army_regular_core_passive_12004.hpp"
#include "xar_bridge/army_ordered_refill_persistent_v1_serializer.hpp"
#include "xar_bridge/ck3_12004_actual_assault_consumer_journal.hpp"
#include "xar_bridge/army_actual_assault_consumer_observations_v1_serializer.hpp"
#include "xar_bridge/army_assault_group_release_observer_12004.hpp"
#include "xar_bridge/army_assault_group_release_observations_12004.hpp"
#include "xar_bridge/army_gathering_due_natural_stage_12004_serializer.hpp"
#include "xar_bridge/army_actual_monthfirst_cleanup_12004_serializer.hpp"
#include "xar_bridge/actual_army_pre_date_prefix_observations12004_serializer.hpp"
#include <algorithm>
#include <set>

namespace xar::game::observed_assault_json_12004 {
inline bool RosterContains(const ck3_12004::ArmyNaturalPhaseRoster12004 &roster,std::uint32_t full_id) {
  return std::find(roster.ordered_full_ids.begin(),roster.ordered_full_ids.end(),full_id) != roster.ordered_full_ids.end();
}
template<class N, class S> void CoreOccurrence(std::string &out, const ck3_12004::ArmyRegularCoreOccurrence12004 &v, N number, S string) {
  out += '{'; Writer<N,S> w{out,number,string};
  w.Integer("stored_index",v.stored_index);
  w.Integer("raw_full_id",v.raw_full_id);
  w.Integer("resolved_full_id",v.resolved_full_id);
  w.Integer("physical_token",v.physical_token);
  w.Boolean("used_fallback",v.used_fallback);
  w.Text("unavailable_reason",v.unavailable_reason);
  out += '}';
}
template<class N, class S> void CoreFrame(std::string &out, const ck3_12004::ArmyRegularCoreFrame12004 &v, N number, S string) {
  out += '{'; Writer<N,S> w{out,number,string};
  w.Integer("native_persistent_occurrence_count",v.native_persistent_occurrence_count);
  w.Integer("native_army_refresh_occurrence_count",v.native_army_refresh_occurrence_count);
  w.Boolean("capture_complete",v.capture_complete);
  w.Key("persistent_occurrences"); Array(out,v.persistent_occurrences,[&](const auto &x){CoreOccurrence(out,x,number,string);});
  w.Key("army_refresh_occurrences"); Array(out,v.army_refresh_occurrences,[&](const auto &x){CoreOccurrence(out,x,number,string);});
  w.Key("persistent_objects"); Array(out,v.persistent_objects,[&](const auto &x){out += '{'; Writer<N,S>d{out,number,string};d.Integer("physical_token",x.physical_token);d.Integer("resolved_full_id",x.resolved_full_id);d.Text("unavailable_reason",x.unavailable_reason);d.Key("physical_values"); ArmyOrderedRefillPersistentV1 p;p.persistent_regiment_id=x.resolved_full_id.value_or(-1);p.prepared_fraction_raw=x.prepared_fraction_raw;p.unavailable_reason=x.unavailable_reason;p.chunks=x.chunks;AppendArmyOrderedRefillPersistentV1(out,p,number,string);out += '}';});
  w.Key("army_objects"); Array(out,v.army_objects,[&](const auto &x){out += '{'; Writer<N,S>d{out,number,string};d.Integer("physical_token",x.physical_token);d.Integer("resolved_full_id",x.resolved_full_id);d.Integer("native_arrg_occurrence_count",x.native_arrg_occurrence_count);d.Text("unavailable_reason",x.unavailable_reason);d.Key("arrg_occurrences");Array(out,x.arrg_occurrences,[&](const auto &a){out += '{';Writer<N,S>r{out,number,string};r.Key("occurrence");CoreOccurrence(out,a.occurrence,number,string);r.Integer("resolved_magic_14_raw",a.resolved_magic_14_raw);r.Boolean("native_refresh_admitted",a.native_refresh_admitted);r.Boolean("native_loss_writer_skipped",a.native_loss_writer_skipped);r.Integer("native_record_count",a.native_record_count);r.Boolean("records_complete",a.records_complete);r.Text("unavailable_reason",a.unavailable_reason);r.Key("records");Array(out,a.records,[&](const auto &q){out += '{';Writer<N,S>z{out,number,string};z.Integer("record_index",q.record_index);z.Integer("persistent_regiment_id",q.persistent_regiment_id);z.Integer("chunk_index",q.chunk_index);z.Integer("persistent_physical_token",q.persistent_physical_token);z.Integer("state_raw",q.state_raw);z.Boolean("native_record_admitted",q.native_record_admitted);z.Text("unavailable_reason",q.unavailable_reason);out += '}';});out += '}';});out += '}';});
  w.Key("missing_inputs"); Array(out,v.missing_inputs,[&](const auto &x){string(out,x);});
  out += '}';
}
template<class N, class S> void CoreEvent(std::string &out, const ck3_12004::ArmyRegularCoreObservation12004 &v, N number, S string) {
  out += '{'; Writer<N,S> w{out,number,string};
  w.Integer("journal_sequence",v.journal_sequence);
  w.Integer("manager_identity",v.manager_identity);
  w.Integer("caller_return_rva",v.caller_return_rva);
  w.Integer("raw_return_bits",v.raw_return_bits);
  w.Integer("entry_date_raw",v.entry_date_raw);
  w.Integer("returned_date_raw",v.returned_date_raw);
  w.Boolean("observed",v.observed);
  w.Boolean("original_called",v.original_called);
  w.Boolean("original_returned",v.original_returned);
  w.Boolean("entry_provenance_complete",v.entry_provenance_complete);
  w.Boolean("return_provenance_complete",v.return_provenance_complete);
  w.Key("parent_scope"); Scope(out,v.parent_scope);
  w.Key("entry_event"); Token(out,v.entry_event); w.Key("returned_event"); Token(out,v.returned_event);
  w.Key("entry"); CoreFrame(out,v.entry,number,string); w.Key("returned"); CoreFrame(out,v.returned,number,string);
  w.Key("provenance_failures"); Array(out,v.provenance_failures,[&](const auto &x){string(out,x);});
  out += '}';
}
} // namespace xar::game::observed_assault_json_12004
namespace xar::game {
// This query copies already retained observations. It never invokes a collector,
// native callback or setter and never supplies a later query value to a frame.
template<class N,class S> void AppendArmyObservedPhaseQuery12004(std::string &out,
    bool available,bool full_id_observable,std::int32_t signed_full_id,N number,S string) {
  using namespace observed_assault_json_12004;
  const auto full_id = static_cast<std::uint32_t>(signed_full_id);
  const bool joined = available && full_id_observable;
  const auto field = [&](const char *key){out += ',';string(out,key);out += ':';};
  const auto preparation = joined ? ck3_12004::ReadActualArmyDailyAssaultPreparationObservations12004(full_id) : std::nullopt;
  field("actual_army_daily_assault_preparation_observations_v1");
  if(preparation) AppendActualArmyDailyAssaultPreparationObservations12004(out,*preparation,number,string); else out += "null";
  field("actual_army_assault_placement_observations_v1");
  if(joined) {
    if(const auto placement=ck3_12004::ReadActualArmyAssaultPlacementObservations12004(full_id))
      AppendActualArmyAssaultPlacementObservations12004(out,*placement,preparation,number,string);
    else out += "null";
  } else out += "null";
  const auto phase_records = joined ? ck3_12004::ReadArmyNaturalPhaseJournal12004() : std::vector<ck3_12004::ArmyNaturalPhaseRecord12004>{};
  std::vector<ck3_12004::ArmyNaturalPhaseRecord12004> matching_phases;
  std::set<std::uintptr_t> primary_managers;
  for(const auto &record:phase_records) {
    if(RosterContains(record.scope.original_army_roster,full_id)) {
      matching_phases.push_back(record);primary_managers.insert(record.scope.primary_manager_identity);
    }
  }
  field("army_natural_phase_observations_v1");
  if(joined) {
    out += '{';Writer<N,S>w{out,number,string};w.Integer("schema_version",1);
    w.Text("source",std::string("owned_native_natural_army_phase_records"));
    w.Text("membership_basis",std::string("captured_parent_roster_full_CArmy_ID_occurrences"));
    w.Integer("subject_full_carmy_id_u32",full_id);w.Key("records");
    std::ostringstream stream;ck3_12004::AppendArmyNaturalPhaseJournal12004(stream,matching_phases);out += stream.str();out += '}';
  } else out += "null";
  field("actual_army_regular_core_observations_v1");
  if(joined) {
    auto core=ck3_12004::ReadArmyRegularCoreJournal12004();
    core.events.erase(std::remove_if(core.events.begin(),core.events.end(),[&](const auto &event){
      return std::none_of(event.entry.army_refresh_occurrences.begin(),event.entry.army_refresh_occurrences.end(),
        [&](const auto &occurrence){return occurrence.resolved_full_id && static_cast<std::uint32_t>(*occurrence.resolved_full_id)==full_id;});
    }),core.events.end());
    out += '{';Writer<N,S>w{out,number,string};w.Integer("schema_version",1);
    w.Text("source",std::string("native_natural_army_regular_core_entry_return"));
    w.Text("membership_basis",std::string("captured_core_entry_resolved_Army_roster_full_ID"));
    w.Boolean("observer_initialized",core.observer_initialized);w.Boolean("observer_installed",core.observer_installed);
    w.Integer("latest_journal_sequence",core.latest_journal_sequence);w.Integer("overwritten_events",core.overwritten_events);w.Integer("publication_failures",core.publication_failures);
    w.Key("events");Array(out,core.events,[&](const auto &event){CoreEvent(out,event,number,string);});out += '}';
  } else out += "null";
  field("army_actual_assault_consumer_observations_v1");
  if(joined) {if(const auto consumer=ck3_12004::ReadActualAssaultConsumerObservations12004(full_id)) AppendArmyActualAssaultConsumerObservations12004(out,*consumer);else out += "null";} else out += "null";
  field("actual_army_assault_group_release_observations_v1");
  if(joined) {if(const auto release=ck3_12004::ReadArmyAssaultGroupReleaseObservations12004(full_id)) AppendArmyAssaultGroupReleaseObservations12004(out,*release);else out += "null";} else out += "null";
  field("native_gathering_due_natural_stage_12004");
  if(joined) out += ck3_12004::SerializeArmyGatheringDueNaturalStage12004(ck3_12004::ReadArmyGatheringDueNaturalForArmy12004(full_id)); else out += "null";
  field("actual_army_cleanup_observations_v1");
  if(joined) {
    auto cleanup=ck3_12004::ReadArmyActualMonthfirstCleanupJournal12004();
    cleanup.events.erase(std::remove_if(cleanup.events.begin(),cleanup.events.end(),[&](const auto &event){return !RosterContains(event.phase.original_army_roster,full_id);}),cleanup.events.end());
    out += "{\"membership_basis\":\"parent_entry_roster_membership\",\"journal\":";
    ck3_12004::AppendArmyActualMonthfirstCleanupObservations12004(out,cleanup);out += '}';
  } else out += "null";
  field("actual_army_pre_date_prefix_observations_v1");
  if(joined) {
    out += "{\"membership_basis\":\"complete_literal_prefix_return_roster_full_ID\",\"journals\":[";
    bool first=true;
    for(auto primary:primary_managers) {
      if(auto prefix=ck3_12004::ReadActualArmyPreDatePrefixObservations12004(primary)) {
        prefix->events.erase(std::remove_if(prefix->events.begin(),prefix->events.end(),[&](const auto &event){
          const auto &roster=event.captured_original_roster;
          return !event.original_roster_capture_complete || !roster.complete || roster.capture_rva!=ck3_12004::kActualArmyPreDatePrefixReturnRva12004 || !RosterContains(roster,full_id);
        }),prefix->events.end());
        if(prefix->events.empty()) continue;
        if(!first) out += ',';first=false;out += ck3_12004::SerializeActualArmyPreDatePrefixObservations12004(*prefix);
      }
    }
    out += "]}";
  } else out += "null";
}
} // namespace xar::game
