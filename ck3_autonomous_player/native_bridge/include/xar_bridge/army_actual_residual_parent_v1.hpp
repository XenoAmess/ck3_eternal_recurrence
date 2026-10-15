#pragma once
#include "xar_bridge/army_actual_residual_siege_budget_v1.hpp"
#include <charconv>
#include <cstdint>
#include <optional>
#include <string>

namespace xar::game {
enum class ArmyResidualRequestSource12004 : std::uint8_t {
  unknown, county_entry, periodic_callback,
};
struct ArmyActualResidualParentV1 {
  std::uint64_t invocation_token=0;
  std::uint32_t native_thread_id=0,nesting_depth=0;
  std::optional<std::uint64_t> parent_invocation_token,allocator_caller_return_rva;
  std::optional<std::uint32_t> enclosing_parent_kind;
  std::int32_t requested_budget=0;
  std::uint8_t flags_raw=0;
  ArmyResidualRequestSource12004 request_source=ArmyResidualRequestSource12004::unknown;
  std::optional<std::int32_t> army_id,native_carmy_id,matching_roster_occurrence;
  bool receiver_identity_matches=false,array_header_matches=false;
  bool writer_full_id_in_actual_array=false,source_complete=false;
  std::uint32_t capture_failure_flags=0;
  std::optional<ArmyActualResidualSiegeBudgetV1> siege_budget_at_allocator_v1;
};
inline void AppendArmyActualResidualParentV1(std::string &out,
    const ArmyActualResidualParentV1 &v) {
  const auto number=[&](auto value){char b[32]{};const auto r=std::to_chars(b,b+sizeof b,value);out.append(b,r.ptr);};
  const auto optional=[&](auto value){if(value)number(*value);else out+="null";};
  const auto boolean=[&](bool value){out+=value?"true":"false";};
  out+="{\"parent_kind\":4,\"invocation_token\":";number(v.invocation_token);
  out+=",\"native_thread_id\":";number(v.native_thread_id);
  out+=",\"nesting_depth\":";number(v.nesting_depth);
  out+=",\"parent_invocation_token\":";optional(v.parent_invocation_token);
  out+=",\"allocator_caller_return_rva\":";optional(v.allocator_caller_return_rva);
  out+=",\"enclosing_parent_kind\":";optional(v.enclosing_parent_kind);
  out+=",\"allocator_entry_rva\":44652512,\"observed_continuation_rva\":44652520";
  out+=",\"requested_budget\":";number(v.requested_budget);
  out+=",\"flags_raw\":";number(static_cast<unsigned>(v.flags_raw));
  out+=",\"request_source\":\"";
  switch(v.request_source){
    case ArmyResidualRequestSource12004::county_entry:out+="county_entry";break;
    case ArmyResidualRequestSource12004::periodic_callback:out+="periodic_callback";break;
    default:out+="unknown";break;
  }
  out+="\",\"army_id\":";optional(v.army_id);
  out+=",\"native_carmy_id\":";optional(v.native_carmy_id);
  out+=",\"matching_roster_occurrence\":";optional(v.matching_roster_occurrence);
  out+=",\"receiver_identity_matches\":";boolean(v.receiver_identity_matches);
  out+=",\"array_header_matches\":";boolean(v.array_header_matches);
  out+=",\"writer_full_id_in_actual_array\":";boolean(v.writer_full_id_in_actual_array);
  out+=",\"source_complete\":";boolean(v.source_complete);
  out+=",\"capture_failure_flags\":";number(v.capture_failure_flags);
  if(v.siege_budget_at_allocator_v1){
    out+=",\"siege_budget_at_allocator_v1\":";
    AppendArmyActualResidualSiegeBudgetV1(out,*v.siege_budget_at_allocator_v1);
  }
  out+='}';
}
}
