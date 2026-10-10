#include "xar_bridge/clergy_mode0_source_packet_12004.hpp"
#include "xar_bridge/clergy_mode0_task_raw_al_31b4a10_12004.hpp"
#include "xar_bridge/clergy_task_block_31b4810_12004.hpp"
#include "xar_bridge/clergy_position_raw_al_31bde90_12004.hpp"
#include "xar_bridge/clergy_position_check_31bd1a0_12004.hpp"
#include "xar_bridge/clergy_shared_condition_successor_31bdda0_12004.hpp"
#include "xar_bridge/generic_trigger_receiver_372df10_12004.hpp"

#include <sstream>
#include <type_traits>

namespace xar::ck3_12004::religion::clergy {
namespace {
struct ChildContext {
  const ClergyMode0SourceAccess12004 *access = nullptr;
  GenericTriggerOwnerScopeChildContext12004 generic;
  GenericTriggerReceiver372DF10Result12004 generic_result;
  bool generic_invoked = false;
};
bool Initial(void *opaque, std::uintptr_t task, std::uint8_t &raw) noexcept {
  auto &c = *static_cast<ChildContext *>(opaque);
  try {
    const auto operands = ReadClergyTaskBlock31B4810Operands12004(
        c.access->read_context, c.access->read_memory, task);
    if (!operands.source_ready || !operands.task_44_raw_u32) return false;
    const auto shared = ReadClergyShared31BDDA0WithGenericChild12004(
        c.access->read_context, c.access->read_memory, *operands.task_44_raw_u32,
        operands.child_rdx_identity, operands.child_r8_identity, c.generic);
    c.generic_invoked = c.generic_invoked || shared.condition_child_required;
    ClergyTaskBlock31BDDA0Child12004 child{};
    child.actual_callee_rva = kClergySharedConditionRva12004;
    child.rcx_raw_u32 = *operands.task_44_raw_u32;
    child.rdx_identity = operands.child_rdx_identity;
    child.r8_identity = operands.child_r8_identity;
    child.raw_al = shared.raw_al; child.source_ready = shared.source_ready;
    const auto result = ResolveClergyTaskBlock31B4810NullTooltip12004(
        c.access->read_context, c.access->read_memory, operands, child);
    if (!result.source_ready || !result.raw_al) return false;
    raw = *result.raw_al; return true;
  } catch (...) { return false; }
}
bool Position(void *opaque, std::uint32_t owner, std::uintptr_t byte_input,
              std::uintptr_t predicate_input, std::uint8_t &raw) noexcept {
  auto &c = *static_cast<ChildContext *>(opaque);
  const auto input = ReadClergyPositionRawAlInputs12004(
      c.access->read_memory, c.access->read_context,
      {owner, byte_input, predicate_input, 0});
  const bool needs_child = input.position_byte_raw && *input.position_byte_raw == 1 &&
      input.predicate_4c_raw_u32 && *input.predicate_4c_raw_u32 != 0;
  c.generic_invoked = c.generic_invoked || needs_child;
  const ClergyPositionRawAlChildReader12004 child{
      &c.generic, &TryReadGenericTriggerOwnerScope372DF1012004};
  const auto result = ProjectClergyPositionRawAl12004(
      c.access->read_memory, c.access->read_context, input, child);
  if (!result.raw_al) return false;
  raw = *result.raw_al; return true;
}
const char *Branch(ClergyMode0TaskRawAlBranch12004 value) noexcept {
  switch (value) {
  case ClergyMode0TaskRawAlBranch12004::initial_nonzero_returns_zero: return "initial_nonzero_returns_zero";
  case ClergyMode0TaskRawAlBranch12004::position_zero_returns_zero: return "position_zero_returns_zero";
  case ClergyMode0TaskRawAlBranch12004::final_raw_al: return "final_raw_al";
  default: return "unavailable";
  }
}
const char *SourceFailure(ClergyMode0TaskRawAlFailure12004 value) noexcept {
  switch (value) {
  case ClergyMode0TaskRawAlFailure12004::none: return "";
  case ClergyMode0TaskRawAlFailure12004::initial_source_unavailable: return "initial_source_unavailable";
  case ClergyMode0TaskRawAlFailure12004::read_access_unavailable: return "read_access_unavailable";
  case ClergyMode0TaskRawAlFailure12004::task_type_unavailable: return "task_type_unavailable";
  case ClergyMode0TaskRawAlFailure12004::owner_raw32_unavailable: return "owner_raw32_unavailable";
  case ClergyMode0TaskRawAlFailure12004::position_unavailable: return "position_unavailable";
  case ClergyMode0TaskRawAlFailure12004::incumbent_raw32_unavailable: return "incumbent_raw32_unavailable";
  case ClergyMode0TaskRawAlFailure12004::compared_raw32_unavailable: return "compared_raw32_unavailable";
  case ClergyMode0TaskRawAlFailure12004::operand_address_unavailable: return "operand_address_unavailable";
  case ClergyMode0TaskRawAlFailure12004::position_source_unavailable: return "position_source_unavailable";
  case ClergyMode0TaskRawAlFailure12004::final_source_unavailable: return "final_source_unavailable";
  }
  return "unavailable";
}
std::string Quote(std::string_view text) {
  static constexpr char hex[] = "0123456789abcdef";
  std::string out = "\"";
  for (const char character : text) {
    const auto byte = static_cast<unsigned char>(character);
    if (byte == '"' || byte == '\\') { out += '\\'; out += static_cast<char>(byte); }
    else if (byte < 0x20) { out += "\\u00"; out += hex[byte >> 4]; out += hex[byte & 15]; }
    else out += static_cast<char>(byte);
  }
  return out+'"';
}
template<class T> void Optional(std::ostringstream &out, const std::optional<T> &v) {
  if (!v) { out << "null"; return; }
  if constexpr (std::is_same_v<T,std::string>) out << Quote(*v);
  else if constexpr (std::is_same_v<T,std::uint8_t>) out << static_cast<unsigned>(*v);
  else out << *v;
}
} // namespace

ClergyMode0SourcePacket12004 ReadClergyMode0SourcePacket12004(
    const ClergyMode0SourceAccess12004 &access, const ClergyMode0SourceSeat12004 &seat,
    const ClergyMode0SourceCapture12004 &capture, std::uint64_t epoch,
    std::int32_t date, std::int32_t owner, std::int32_t candidate) noexcept {
  ClergyMode0SourcePacket12004 out{};
  try {
    out.capture_epoch = epoch; out.date_raw = date;
    out.owner_character_id = owner; out.candidate_character_id = candidate;
    if (seat.task_id != -1) out.active_task_id = seat.task_id;
    if (seat.incumbent_id != -1) out.incumbent_character_id = seat.incumbent_id;
    auto &frame = out.source_read_frame;
    frame.native_revision = capture.native_revision;
    frame.query_sequence = capture.query_sequence;
    frame.proof_epoch = capture.proof_epoch; frame.date_raw = date;
    bool borrowed_scope_matches = false;
    if (capture.borrowed_frame) {
      const auto &borrowed = *capture.borrowed_frame;
      if (borrowed.frame_identity) frame.frame_identity = borrowed.frame_identity;
      if (!borrowed.snapshot_identity.empty()) frame.snapshot_identity = borrowed.snapshot_identity;
      borrowed_scope_matches = borrowed.module_base == access.module_base &&
          borrowed.native_revision == capture.native_revision &&
          borrowed.query_sequence == capture.query_sequence &&
          borrowed.proof_epoch == capture.proof_epoch && borrowed.proof_epoch == epoch &&
          borrowed.date_raw && *borrowed.date_raw == date &&
          borrowed.caller_domain == "player_clergy_appointment_v1";
      frame.caller_snapshot_confirmed = borrowed_scope_matches && borrowed.caller_snapshot_confirmed;
      frame.ready = borrowed_scope_matches && SourceReadFrameReady12004(borrowed);
    }
    if (!seat.actual_task) { out.unavailable_input = "seat_absent"; return out; }
    if (seat.incumbent_id == -1) {
      out.capture_scope = "seat_vacant"; out.unavailable_input = "seat_vacant"; return out;
    }
    out.capture_scope = "occupied_seat_mode0_software_projection";
    if (access.executable_sha256 != ck3_12004::kExecutableSha256 || !access.read_memory) {
      out.unavailable_input = "source_access_unavailable"; return out;
    }
    ChildContext context{}; context.access = &access;
    context.generic.current_query_frame = borrowed_scope_matches ? capture.borrowed_frame : nullptr;
    context.generic.copied_result = &context.generic_result;
    ClergyPosition31BD1A0ReadContext12004 final_context{
        access.read_context, access.read_memory, access.module_base, access.executable_sha256};
    const ClergyMode0TaskRawAlReaders12004 readers{
        &context, &Initial, &context, &Position,
        &final_context, &ReadClergyPosition31BD1A0Callback12004};
    const auto result = ReadClergyMode0TaskRawAl12004(access.read_context,
        access.read_memory, seat.actual_task, access.module_base, readers);
    out.source_projected = true; out.raw_al = result.raw_al;
    out.initial_raw_al = result.initial_raw_al;
    out.position_raw_al = result.position_raw_al; out.final_raw_al = result.final_raw_al;
    out.owner_id_raw32 = result.owner_id_raw32;
    out.incumbent_id_raw32 = result.incumbent_id_raw32;
    out.compared_id_raw32 = result.compared_id_raw32;
    out.branch = Branch(result.branch); out.unavailable_input = SourceFailure(result.failure);
    out.source_ready = result.raw_al.has_value();
    if ((result.position && *result.position != seat.actual_position) ||
        (result.owner_id_raw32 && *result.owner_id_raw32 != static_cast<std::uint32_t>(owner)) ||
        (result.incumbent_id_raw32 && *result.incumbent_id_raw32 != static_cast<std::uint32_t>(seat.incumbent_id))) {
      out.raw_al.reset(); out.source_ready = false; out.branch = "unavailable";
      out.unavailable_input = "source_seat_operand_changed";
    }
    const auto &generic = context.generic_result;
    out.generic_trigger.software_adapter_invoked = context.generic_invoked;
    out.generic_trigger.copied_frame_ready = generic.copied_frame_ready;
    out.generic_trigger.copied_inputs_ready = generic.copied_inputs_ready;
    out.generic_trigger.source_value_ready = generic.source_value_ready;
    out.generic_trigger.scope_root_word = generic.scope_root_word;
    out.generic_trigger.scope_full_id_payload = generic.scope_full_id_payload;
    out.generic_trigger.evaluation_flag_raw_u8 = generic.evaluation_flag_raw_u8;
    out.generic_trigger.raw_al = generic.raw_al;
    out.generic_trigger.unavailable_input = generic.unavailable_reason;
    return out;
  } catch (...) {
    out.source_ready = false; out.raw_al.reset(); out.unavailable_input = "source_projection_exception";
    return out;
  }
}

std::string SerializeClergyMode0SourcePacket12004(const ClergyMode0SourcePacket12004 &v) {
  std::ostringstream o; o << std::boolalpha;
  o << "{\"schema\":\"xar.ck3.clergy-mode0-source-inputs-12004/v1\",\"schema_version\":1,"
    << "\"source_executable_sha256\":" << Quote(ck3_12004::kExecutableSha256)
    << ",\"capture_scope\":" << Quote(v.capture_scope)
    << ",\"capture_epoch\":" << v.capture_epoch << ",\"date_raw\":" << v.date_raw
    << ",\"owner_character_id\":" << v.owner_character_id
    << ",\"candidate_character_id\":" << v.candidate_character_id
    << ",\"active_task_id\":"; Optional(o,v.active_task_id);
  o << ",\"incumbent_character_id\":"; Optional(o,v.incumbent_character_id);
  o << ",\"position_key\":\"councillor_court_chaplain\",\"input_scope_confirmed\":" << v.input_scope_confirmed
    << ",\"source_read_frame\":{\"frame_identity\":"; Optional(o,v.source_read_frame.frame_identity);
  o << ",\"snapshot_identity\":"; Optional(o,v.source_read_frame.snapshot_identity);
  o << ",\"native_revision\":" << v.source_read_frame.native_revision
    << ",\"query_sequence\":" << v.source_read_frame.query_sequence
    << ",\"proof_epoch\":" << v.source_read_frame.proof_epoch
    << ",\"date_raw\":" << v.source_read_frame.date_raw
    << ",\"caller_domain\":\"player_clergy_appointment_v1\",\"caller_snapshot_confirmed\":"
    << v.source_read_frame.caller_snapshot_confirmed << ",\"ready\":" << v.source_read_frame.ready
    << "},\"sourceproof\":{\"producer_rva\":" << kClergyMode0TaskPredicateRva12004
    << ",\"source_projected\":" << v.source_projected << ",\"source_ready\":" << v.source_ready
    << ",\"native_callee_invocation_observed\":false,\"natural_return_witness\":false,\"native_calls_added\":false},"
    << "\"inputs\":{\"owner_id_raw32\":"; Optional(o,v.owner_id_raw32);
  o << ",\"incumbent_id_raw32\":"; Optional(o,v.incumbent_id_raw32);
  o << ",\"compared_id_raw32\":"; Optional(o,v.compared_id_raw32);
  o << ",\"initial_raw_al\":"; Optional(o,v.initial_raw_al);
  o << ",\"position_raw_al\":"; Optional(o,v.position_raw_al);
  o << ",\"final_raw_al\":"; Optional(o,v.final_raw_al);
  o << ",\"raw_al\":"; Optional(o,v.raw_al);
  o << ",\"branch\":" << Quote(v.branch) << ",\"unavailable_input\":" << Quote(v.unavailable_input)
    << "},\"generic_trigger\":{\"software_adapter_invoked\":" << v.generic_trigger.software_adapter_invoked
    << ",\"copied_frame_ready\":" << v.generic_trigger.copied_frame_ready
    << ",\"copied_inputs_ready\":" << v.generic_trigger.copied_inputs_ready
    << ",\"source_value_ready\":" << v.generic_trigger.source_value_ready
    << ",\"scope_root_word\":"; Optional(o,v.generic_trigger.scope_root_word);
  o << ",\"scope_full_id_payload\":"; Optional(o,v.generic_trigger.scope_full_id_payload);
  o << ",\"evaluation_flag_raw_u8\":"; Optional(o,v.generic_trigger.evaluation_flag_raw_u8);
  o << ",\"raw_al\":"; Optional(o,v.generic_trigger.raw_al);
  o << ",\"unavailable_input\":" << Quote(v.generic_trigger.unavailable_input) << "}}";
  return o.str();
}
} // namespace xar::ck3_12004::religion::clergy
