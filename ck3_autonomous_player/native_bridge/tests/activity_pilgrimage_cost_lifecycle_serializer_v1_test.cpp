#include "xar_bridge/activity_pilgrimage_cost_lifecycle_v1.hpp"
#include "xar_bridge/activity_typed_cost_serializer_v1.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include <cstdlib>
#include <cstring>
#include <iostream>

namespace {
using namespace xar::bridge;
int install_calls=0;
bool fail_install=false;
ActivityPilgrimageCostLifecycleV1 *stop_during_install=nullptr;
void Need(bool value) { if(!value) std::abort(); }
bool Memory(void *,std::uintptr_t,void *,std::size_t) noexcept { return false; }
bool Frame(void *,ActivityCostSlot12FrameV1 &) noexcept { return false; }
bool Install(ActivityCostSlot12ObserverV1 &observer,
             const ActivityCostSlot12EnvironmentV1 &environment) noexcept {
  ++install_calls;
  if(fail_install) return false;
  observer.environment=environment;observer.installed=true;
  if(stop_during_install) StopActivityPilgrimageCostQueriesV1(*stop_during_install);
  return true;
}
ActivityCostSlot12EnvironmentV1 Cold() {
  ActivityCostSlot12EnvironmentV1 out{};
  out.enabled=true;out.primary_thread_suspended=true;
  out.executable_sha256=xar::ck3_12004::kExecutableSha256;
  out.module_base=0x180000000ULL;out.read_memory=&Memory;out.read_frame=&Frame;
  return out;
}
ActivityTypedFullCostResultV1 Quote() {
  ActivityTypedFullCostResultV1 result{};
  result.status=ActivityTypedFullCostStatusV1::observed;
  auto &q=result.quote;const auto &contract=kOrdinaryPilgrimagePiousContractV1;
  q.observed=true;q.kind=contract.kind;
  q.frame={7,43800000,42,true,true,true,true};
  q.planner=0xABCDEF120001ULL;q.owner=0xABCDEF120002ULL;
  q.activity_type=0xABCDEF120003ULL;q.planning_stage=5;
  q.normal_refresh_sequence=3;q.configuration_fingerprint=1234567;
  q.configured_cost_raw={300000,0,0,18500000,0,0,0,0,0,0};
  q.diagnostic_aggregate_raw={0,0,0,10000000,0,0,0,0,0,0};
  q.known_name_resource_indices={3,2,0,4};
  for(auto index:q.known_name_resource_indices) q.named_cost_verified[index]=true;
  q.final_can_start_observed=true;q.final_can_start=false;
  auto &s=q.selection;s.observed=true;s.kind=contract.kind;s.frame=q.frame;
  s.planner=q.planner;s.activity_type=q.activity_type;s.planning_stage=5;
  s.native_selected_option=0xABCDEF120004ULL;s.native_option_id=17;
  s.option_key_size=static_cast<std::uint16_t>(contract.special_option_key.size());
  std::memcpy(s.option_key.data(),contract.special_option_key.data(),s.option_key_size);
  return result;
}
} // namespace

int main() {
  using Status=ActivityPilgrimageCostLifecycleStatusV1;
  { ActivityPilgrimageCostLifecycleV1 s;
    Need(InstallActivityPilgrimageCostColdV1(s,Cold(),false,false,&Install)==Status::disabled);
    Need(install_calls==0 && !GetActivityPilgrimageCostObserverForQueriesV1(s)); }
  { ActivityPilgrimageCostLifecycleV1 s;
    Need(InstallActivityPilgrimageCostColdV1(s,Cold(),true,true,&Install)==Status::conflicting_legacy_gate);
    Need(install_calls==0 && !GetActivityPilgrimageCostObserverForQueriesV1(s)); }
  { ActivityPilgrimageCostLifecycleV1 s;auto e=Cold();e.primary_thread_suspended=false;
    Need(InstallActivityPilgrimageCostColdV1(s,e,true,false,&Install)==Status::invalid_cold_environment); }
  { ActivityPilgrimageCostLifecycleV1 s;auto e=Cold();e.executable_sha256="not-exact4";
    Need(InstallActivityPilgrimageCostColdV1(s,e,true,false,&Install)==Status::invalid_cold_environment); }
  { ActivityPilgrimageCostLifecycleV1 s;auto e=Cold();e.typed_contract=&kOrdinaryPilgrimagePiousContractV1;
    Need(InstallActivityPilgrimageCostColdV1(s,e,true,false,&Install)==Status::invalid_cold_environment); }
  { ActivityPilgrimageCostLifecycleV1 s;
    Need(InstallActivityPilgrimageCostColdV1(s,Cold(),true,false,&Install)==Status::installed);
    Need(GetActivityPilgrimageCostObserverForQueriesV1(s)==&s.observer);
    Need(s.observer.environment.typed_contract==&kOrdinaryPilgrimagePiousContractV1);
    const int calls=install_calls;
    Need(InstallActivityPilgrimageCostColdV1(s,Cold(),true,false,&Install)==Status::already_attempted);
    Need(install_calls==calls);
    StopActivityPilgrimageCostQueriesV1(s);
    Need(!GetActivityPilgrimageCostObserverForQueriesV1(s) && s.observer.installed);
    Need(s.observer.environment.typed_contract==&kOrdinaryPilgrimagePiousContractV1);
    Need(InstallActivityPilgrimageCostColdV1(s,Cold(),true,false,&Install)==Status::already_attempted); }
  { ActivityPilgrimageCostLifecycleV1 s;fail_install=true;
    Need(InstallActivityPilgrimageCostColdV1(s,Cold(),true,false,&Install)==Status::install_failed);
    Need(!GetActivityPilgrimageCostObserverForQueriesV1(s));fail_install=false; }
  { ActivityPilgrimageCostLifecycleV1 s;StopActivityPilgrimageCostQueriesV1(s);
    const int calls=install_calls;
    Need(InstallActivityPilgrimageCostColdV1(s,Cold(),true,false,&Install)==Status::already_attempted);
    Need(install_calls==calls); }
  { ActivityPilgrimageCostLifecycleV1 s;stop_during_install=&s;
    Need(InstallActivityPilgrimageCostColdV1(s,Cold(),true,false,&Install)==Status::stopped);
    Need(!GetActivityPilgrimageCostObserverForQueriesV1(s) && s.observer.installed);
    stop_during_install=nullptr; }
  { auto r=Quote();const auto wire=SerializeActivityTypedPlannerFullCostV1(r);
    Need(!wire.empty());
    Need(wire.find("\"schema\":\"activity-pilgrimage-configured-full10-cost-v1\"")!=std::string::npos);
    Need(wire.find("\"known_name_resource_indices\":[3,2,0,4]")!=std::string::npos);
    Need(wire.find("\"configured_cost_raw\":[300000,0,0,18500000,0,0,0,0,0,0]")!=std::string::npos);
    Need(wire.find("\"diagnostic_aggregate_raw\":[0,0,0,10000000,0,0,0,0,0,0]")!=std::string::npos);
    Need(wire.find("\"final_can_start\":false")!=std::string::npos);
    for(auto address:{r.quote.planner,r.quote.owner,r.quote.activity_type,
                      r.quote.selection.native_selected_option})
      Need(wire.find(std::to_string(address))==std::string::npos);
    Need(wire.find("ABCDEF")==std::string::npos);
    // Root may capture this exact producer output after actually running the EXE.
    std::cout<<wire<<'\n'; }
  { auto r=Quote();r.status=ActivityTypedFullCostStatusV1::no_normal_refresh;
    Need(SerializeActivityTypedPlannerFullCostV1(r).empty()); }
  { auto r=Quote();r.quote.observed=false;Need(SerializeActivityTypedPlannerFullCostV1(r).empty()); }
  { auto r=Quote();r.quote.selection.frame.revision++;
    Need(SerializeActivityTypedPlannerFullCostV1(r).empty()); }
  { auto r=Quote();r.quote.known_name_resource_indices[1]=3;
    Need(SerializeActivityTypedPlannerFullCostV1(r).empty()); }
  { auto r=Quote();r.quote.named_cost_verified[9]=true;
    Need(SerializeActivityTypedPlannerFullCostV1(r).empty()); }
  { auto r=Quote();r.quote.failure_display_known=true;
    Need(SerializeActivityTypedPlannerFullCostV1(r).empty()); }
  { auto r=Quote();r.quote.configured_cost_raw[9]=1;
    r.unknown_positive_configured_cost=true;
    Need(SerializeActivityTypedPlannerFullCostV1(r).find(
      "\"unknown_positive_configured_cost\":true")!=std::string::npos); }
  { auto r=Quote();r.quote.configured_cost_raw[9]=-1;
    const auto wire=SerializeActivityTypedPlannerFullCostV1(r);
    Need(wire.find(",0,0,0,0,0,-1]")!=std::string::npos);
    Need(wire.find("\"unknown_positive_configured_cost\":false")!=std::string::npos); }
  { auto r=Quote();r.quote.configured_cost_raw[9]=1;
    Need(SerializeActivityTypedPlannerFullCostV1(r).empty()); }
  { auto r=Quote();r.quote.frame.date_raw=0x100000000LL;
    r.quote.selection.frame=r.quote.frame;
    Need(SerializeActivityTypedPlannerFullCostV1(r).empty()); }
  { auto r=Quote();r.final_failure_display_unknown_reason="invented";
    Need(SerializeActivityTypedPlannerFullCostV1(r).empty()); }
  return 0;
}
