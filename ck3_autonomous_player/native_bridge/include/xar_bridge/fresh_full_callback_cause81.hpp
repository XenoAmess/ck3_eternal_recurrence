#pragma once
#include "xar_bridge/ck3_1210_full_snapshot_v1.hpp"
#include "xar_bridge/game_adapter.hpp"
#include <array>
#include <cstring>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::diagnostic81 {
// Private diagnostic values. They grant no reader, callback or owner role.
// No address, borrowed game object or mailbox pointer crosses into the wire.
struct RawFullCause {
  bool exact_reader = false;
  bool attempted = false;
  bool returned = false;
  bool available = false;
  bool exception = false;
  ck3_1210::FullSnapshotDiagnosticsV1 full{};
  bool full_value_captured = false;
  std::array<char,96> stage_bytes{};
  std::array<char,256> reason_bytes{};
  std::uint16_t stage_length = 0, reason_length = 0;
  bool stage_captured = false, reason_captured = false;
  std::uint32_t military_rejection = 0;
};
template<std::size_t N>
inline bool CopyText(std::string_view source,std::array<char,N> &out,std::uint16_t &length) noexcept {
  length=0;
  if(source.size()>N)return false;
  if(!source.empty())std::memcpy(out.data(),source.data(),source.size());
  length=static_cast<std::uint16_t>(source.size());return true;
}
inline void CaptureFullValue(RawFullCause &out,const ck3_1210::FullSnapshotDiagnosticsV1 &value) noexcept {
  out.full=value;out.full_value_captured=true;
  out.stage_captured=CopyText(value.stage,out.stage_bytes,out.stage_length);
  out.reason_captured=CopyText(value.reason,out.reason_bytes,out.reason_length);
}
struct CallbackCause {
  bool entered = false;
  std::uint64_t sequence = 0, pump_epoch = 0;
  std::uint32_t thread_id = 0;
  bool owner_before = false, owner_after = false;
  std::int32_t stamp_date_raw = 0;
  bool stamp_paused = false;
  RawFullCause raw{};
  bool observed_valid = false;
  std::int32_t observed_date_raw = 0;
  bool observed_paused = false;
  bool date_matches = false, paused_matches = false;
  bool result_available = false;
};
// Separate C++ seam, no GameAdapter virtual/Full/header/mailbox ABI change.
// `exact_reader=false` means the caller must retain its old generic path.
bool ReadFlorinSnapshotForRequest(const game::GameAdapter &, game::Snapshot &,
                                 RawFullCause &) noexcept;
inline std::string_view MilitaryRejectionName(std::uint32_t code) noexcept {
  switch(code) {
  case 0: return "not_rejected";
  case 1: return "ticket_identity_missing";
  case 2: return "binding_or_callback_context";
  case 3: return "mapped_targets_or_TLS";
  case 4: return "snapshot_owner_changed";
  case 5: return "executor_not_registered";
  case 6: return "executor_or_context_changed";
  case 7: return "not_executing";
  case 8: return "published_or_started_sequence_changed";
  case 9: return "started_pump_epoch_changed";
  case 10: return "current_pump_epoch_changed";
  case 11: return "stop_reset_failure_or_hook_exit";
  default: return "unknown_diagnostic_code";
  }
}
inline void Quote(std::string &out, std::string_view text) {
  constexpr char hex[]="0123456789abcdef";
  out+='"';
  for(const unsigned char value:text) {
    if(value=='"' || value=='\\') {out+='\\';out+=char(value);}
    else if(value<32) {out+="\\u00";out+=hex[value>>4];out+=hex[value&15];}
    else out+=char(value);
  }
  out+='"';
}
inline std::string SerializeCallbackCause(const CallbackCause &value) {
  std::string out="{\"schema\":\"xar.native.fresh-full-callback-cause/v1\"";
  const auto flag=[&](std::string_view key,bool v) {out+=",\"";out+=key;out+="\":";out+=v?"true":"false";};
  const auto number=[&](std::string_view key,auto v) {out+=",\"";out+=key;out+="\":";out+=std::to_string(v);};
  flag("callback_entered",value.entered);
  out+=",\"ticket_sequence\":\""+std::to_string(value.sequence)+"\"";
  out+=",\"pump_epoch\":\""+std::to_string(value.pump_epoch)+"\"";
  number("thread_id",value.thread_id);
  flag("owner_before",value.owner_before);flag("owner_after",value.owner_after);
  number("stamp_date_raw",value.stamp_date_raw);flag("stamp_paused",value.stamp_paused);
  flag("exact_florin_reader",value.raw.exact_reader);
  flag("raw_read_attempted",value.raw.attempted);flag("raw_read_returned",value.raw.returned);
  flag("raw_read_available",value.raw.available);flag("raw_read_exception",value.raw.exception);
  out+=",\"full_stage\":";
  if(value.raw.exact_reader && value.raw.returned && value.raw.stage_captured)
    Quote(out,std::string_view(value.raw.stage_bytes.data(),value.raw.stage_length));else out+="null";
  out+=",\"full_reason\":";
  if(value.raw.exact_reader && value.raw.returned && value.raw.reason_captured)
    Quote(out,std::string_view(value.raw.reason_bytes.data(),value.raw.reason_length));else out+="null";
  flag("full_stage_captured",value.raw.stage_captured);flag("full_reason_captured",value.raw.reason_captured);
  const auto optional=[&](std::string_view key,std::string v) {out+=",\"";out+=key;out+="\":";out+=v;};
  const bool full_known=value.raw.exact_reader && value.raw.returned && value.raw.full_value_captured;
  optional("full_complete",full_known?(value.raw.full.complete?"true":"false"):"null");
  optional("completed_passes",full_known?std::to_string(value.raw.full.completed_passes):"null");
  optional("military_rejection",full_known?std::to_string(value.raw.military_rejection):"null");
  out+=",\"military_rejection_reason\":";
  if(full_known)Quote(out,MilitaryRejectionName(value.raw.military_rejection));else out+="null";
  optional("observed_date_raw",value.observed_valid?std::to_string(value.observed_date_raw):"null");
  optional("observed_paused",value.observed_valid?(value.observed_paused?"true":"false"):"null");
  optional("date_matches",value.observed_valid?(value.date_matches?"true":"false"):"null");
  optional("paused_matches",value.observed_valid?(value.paused_matches?"true":"false"):"null");
  flag("result_available",value.result_available);
  out+='}';return out;
}
} // namespace xar::diagnostic81
