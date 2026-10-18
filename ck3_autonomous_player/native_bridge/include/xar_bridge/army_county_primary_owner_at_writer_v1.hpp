#pragma once
#include <charconv>
#include <cstdint>
#include <optional>
#include <string>

namespace xar::game {
struct ArmyCountyWriterEventTokenV1 {
  std::uintptr_t clock_identity=0;
  std::uint64_t sequence=0;
  std::optional<std::uint32_t> thread_id;
};
struct ArmyCountyPrimaryOwnerAtWriterV1 {
  std::uint64_t writer_invocation_token=0;
  std::uintptr_t writer_receiver_identity=0,source_carmy_identity=0;
  std::uintptr_t phase_primary_manager_identity=0,phase_game_state_identity=0;
  std::optional<std::int32_t> army_id,native_carmy_id,writer_full_regiment_id;
  ArmyCountyWriterEventTokenV1 phase_entry_event,writer_event,phase_prefix_roster_event;
  std::optional<std::int32_t> phase_roster_occurrence,army_roster_occurrence;
  bool receiver_identity_matches=false,writer_identity_matches=false;
  bool actual_array_contains_writer=false,source_phase_roster_membership=false;
  std::uint32_t capture_failure_flags=0;
  bool source_complete=false;
};
inline void AppendArmyCountyPrimaryOwnerAtWriterV1(std::string &out,
    const ArmyCountyPrimaryOwnerAtWriterV1 &v) {
  const auto n=[&](auto x){char b[32]{};const auto r=std::to_chars(b,b+sizeof b,x);out.append(b,r.ptr);};
  const auto o=[&](const auto &x){if(x)n(*x);else out+="null";};
  const auto token=[&](const auto &x){out+="{\"clock_identity\":";n(x.clock_identity);out+=",\"sequence\":";n(x.sequence);out+=",\"thread_id\":";o(x.thread_id);out+='}';};
  out+="{\"schema_version\":1,\"source\":\"native_county_primary_R13_pre_date\",\"caller_return_rva\":38675950,\"phase_entry_rva\":44670368,\"phase_prefix_rva\":44670582";
  out+=",\"writer_invocation_token\":";n(v.writer_invocation_token);
  out+=",\"writer_receiver_identity\":";n(v.writer_receiver_identity);
  out+=",\"source_carmy_identity\":";n(v.source_carmy_identity);
  out+=",\"phase_primary_manager_identity\":";n(v.phase_primary_manager_identity);
  out+=",\"phase_game_state_identity\":";n(v.phase_game_state_identity);
  out+=",\"army_id\":";o(v.army_id);out+=",\"native_carmy_id\":";o(v.native_carmy_id);
  out+=",\"writer_full_regiment_id\":";o(v.writer_full_regiment_id);
  out+=",\"phase_entry_event\":";token(v.phase_entry_event);
  out+=",\"writer_event\":";token(v.writer_event);
  out+=",\"phase_prefix_roster_event\":";token(v.phase_prefix_roster_event);
  out+=",\"phase_roster_occurrence\":";o(v.phase_roster_occurrence);
  out+=",\"army_roster_occurrence\":";o(v.army_roster_occurrence);
  out+=",\"receiver_identity_matches\":";out+=v.receiver_identity_matches?"true":"false";
  out+=",\"writer_identity_matches\":";out+=v.writer_identity_matches?"true":"false";
  out+=",\"actual_array_contains_writer\":";out+=v.actual_array_contains_writer?"true":"false";
  out+=",\"source_phase_roster_membership\":";out+=v.source_phase_roster_membership?"true":"false";
  out+=",\"capture_failure_flags\":";n(v.capture_failure_flags);
  out+=",\"source_complete\":";out+=v.source_complete?"true":"false";out+='}';
}
} // namespace xar::game
