#include "xar_bridge/prisoner_selected_quote_source_12004.hpp"

namespace xar::ck3_12004 {
namespace {
std::uint64_t MultiplyHigh(std::uint64_t a, std::uint64_t b) noexcept {
  const auto al = a & 0xFFFFFFFFULL, ah = a >> 32;
  const auto bl = b & 0xFFFFFFFFULL, bh = b >> 32;
  const auto low = al * bl;
  const auto mid1 = ah * bl + (low >> 32);
  const auto mid2 = al * bh + (mid1 & 0xFFFFFFFFULL);
  return ah * bh + (mid1 >> 32) + (mid2 >> 32);
}
std::string String(const std::string &s) {
  std::string out = "\"";
  for (const unsigned char c : s) {
    if (c == '"' || c == '\\') out += '\\';
    if (c < 0x20) { constexpr char hex[] = "0123456789abcdef";
      out += "\\u00"; out += hex[c >> 4]; out += hex[c & 15];
    } else out += static_cast<char>(c);
  }
  return out + '"';
}
template <class T> std::string Number(const std::optional<T> &v) {
  return v ? std::to_string(*v) : "null";
}
std::string Boolean(bool b) { return b ? "true" : "false"; }
std::string Boolean(const std::optional<bool> &b) { return b ? Boolean(*b) : "null"; }
std::string Frame(const PrisonerQuoteSourceFrame12004 &f) {
  return "{\"executable_sha256\":" + String(f.executable_sha256) +
      ",\"module_base\":" + std::to_string(f.module_base) +
      ",\"native_revision\":" + std::to_string(f.native_revision) +
      ",\"query_sequence\":" + std::to_string(f.query_sequence) +
      ",\"proof_epoch\":" + std::to_string(f.proof_epoch) + ",\"date_raw\":" + Number(f.date_raw) +
      ",\"jailer_full_id\":" + Number(f.jailer_full_id) + ",\"prisoner_full_id\":" + Number(f.prisoner_full_id) +
      ",\"recipient_full_id\":" + Number(f.recipient_full_id) +
      ",\"definition_identity\":" + std::to_string(f.definition_identity) +
      ",\"interaction_context_identity\":" + std::to_string(f.interaction_context_identity) +
      ",\"original_scope_identity\":" + std::to_string(f.original_scope_identity) +
      ",\"roles_verified_in_owned_context\":" + Boolean(f.roles_verified_in_owned_context) +
      ",\"same_frame_confirmed\":" + Boolean(f.same_frame_confirmed) + "}";
}
}

PrisonerQuoteSourceSample12004 CopyPrisonerQuoteSourceSample12004(
    const PrisonerQuoteReadOnlyAccess12004 &access, PrisonerQuoteSourceFrame12004 frame,
    std::uintptr_t context, bool ordinary) {
  PrisonerQuoteSourceSample12004 out{};
  frame.interaction_context_identity = context;
  frame.original_scope_identity = context <= (std::numeric_limits<std::uintptr_t>::max)() - 8 ? context + 8 : 0;
  const auto definition = ReadPrisonerQuoteSource12004<std::uintptr_t>(access, context);
  const auto actor = ReadPrisonerQuoteSource12004<std::uint32_t>(access, context, 0x2D8);
  const auto recipient = ReadPrisonerQuoteSource12004<std::uint32_t>(access, context, 0x2DC);
  const auto secondary = ReadPrisonerQuoteSource12004<std::uint32_t>(access, context, 0x2E4);
  frame.definition_identity = definition.value_or(0); frame.recipient_full_id = recipient;
  frame.roles_verified_in_owned_context = definition && *definition != 0 && actor == frame.jailer_full_id &&
      actor && *actor != 0 && *actor != UINT32_MAX && recipient && *recipient != 0 && *recipient != UINT32_MAX &&
      frame.prisoner_full_id && *frame.prisoner_full_id != 0 && *frame.prisoner_full_id != UINT32_MAX &&
      (ordinary ? secondary == frame.prisoner_full_id : recipient == frame.prisoner_full_id);
  out.frame = frame;
  out.caller_aliases.primary_scope = frame.original_scope_identity;
  out.caller_aliases.secondary_scope = std::uintptr_t{0};
  out.caller_aliases.tertiary_scope = frame.original_scope_identity;
  out.caller_aliases.primary_scope_root_word = ReadPrisonerQuoteSource12004<std::uint16_t>(access, frame.original_scope_identity);
  if (frame.module_base <= (std::numeric_limits<std::uintptr_t>::max)() - 0x5D1DADC)
    out.caller_aliases.evaluation_flag_raw_u8 = ReadPrisonerQuoteSource12004<std::uint8_t>(access, frame.module_base, 0x5D1DADC);
  // These describe the caller's scope, not the transient recipient-root clone
  // or the callee's physical internal/support stack addresses.
  out.answer_raw = ReadPrisonerAnswerHelperRaw12004(access, frame);
  out.answer_predicate_raw = ReadPrisonerAnswerPredicate3148BB0Raw12004(access, out.answer_raw);
  const auto predicate = ProjectPrisonerAnswerPredicate3148BB012004(out.answer_predicate_raw, {});
  const PrisonerAnswerQueryArguments12004 query_args{std::uint8_t{1}, std::uint8_t{1}, std::uintptr_t{0}, std::uintptr_t{0}};
  const auto initial = ProjectPrisonerAnswerInitialGate12004(out.answer_raw, query_args, predicate.byte_child);
  if (initial.raw_al && *initial.raw_al == 3) {
    out.answer_control_raw = ReadPrisonerAnswerControlPackage12004(access, frame, out.answer_raw.context_2d8_raw_u32);
    if (out.answer_raw.context_2e8_raw_u32 && *out.answer_raw.context_2e8_raw_u32 != UINT32_MAX)
      out.mode0_scalar_raw = ReadPrisonerMode0ScalarInputs12004(access, frame);
  }
  for (std::size_t i = 0; i < out.answer_lookup_raw_u8.size(); ++i)
    out.answer_lookup_raw_u8[i] = ReadPrisonerQuoteSource12004<std::uint8_t>(access, frame.module_base, 0x48B57EC + i);
  return out;
}
void CopyPrisonerQuoteRecipientScoreSource12004(const PrisonerQuoteReadOnlyAccess12004 &access,
    PrisonerQuoteSourceSample12004 &out) {
  PrisonerQuoteRecipientScoreSource12004 score{};
  score.copied_inputs.frame = out.frame;
  if (out.frame.definition_identity != 0 && out.frame.definition_identity <= (std::numeric_limits<std::uintptr_t>::max)() - 0x1918)
    score.copied_inputs = ReadPrisonerRecipientScoreInputs12004(access, out.frame, out.frame.definition_identity + 0x1918);
  out.recipient_score = std::move(score);
}
void CopyPrisonerQuoteCostSource12004(const PrisonerQuoteReadOnlyAccess12004 &access,
    PrisonerQuoteSourceSample12004 &out, std::uintptr_t block, const std::int64_t *original) {
  PrisonerQuoteCostSource12004 cost{}; cost.cost_block_identity = block;
  if (block <= (std::numeric_limits<std::uintptr_t>::max)() - 0x9C2)
    for (std::size_t i = 0; i < cost.lanes.size(); ++i) cost.lanes[i].lane_identity = block + 0x40 + i * 0xF0;
  if (!PrisonerQuoteSourceFrameReady12004(out.frame) ||
      out.frame.definition_identity > (std::numeric_limits<std::uintptr_t>::max)() - 0x40 ||
      block != out.frame.definition_identity + 0x40 || block > (std::numeric_limits<std::uintptr_t>::max)() - 0x9C2) {
    cost.unavailable_reason = "cost_parent_definition_or_frame_unbound"; out.actor_on_send_costs = cost; return;
  }
  cost.original_output_copied = original && access.read_memory &&
      access.read_memory(access.context, original, cost.original_output_q64.data(), sizeof(cost.original_output_q64));
  cost.clamp_nonnegative_raw_u8 = ReadPrisonerQuoteSource12004<std::uint8_t>(access, block, 0x9C1);
  cost.round_raw_u8 = ReadPrisonerQuoteSource12004<std::uint8_t>(access, block, 0x9C0);
  for (std::size_t i = 0; i < cost.lanes.size(); ++i)
    cost.lanes[i] = ReadPrisonerCostLane9D7060Readonly12004(access,
        {out.frame, block + 0x40 + i * 0xF0, out.caller_aliases, block + 0x9A0});
  ProjectPrisonerQuoteCosts12004(cost); out.actor_on_send_costs = std::move(cost);
}
void CopyPrisonerQuoteAutoAcceptSource12004(const PrisonerQuoteReadOnlyAccess12004 &access,
    PrisonerQuoteSourceSample12004 &out) {
  out.auto_accept_trigger_identity = ReadPrisonerQuoteSource12004<std::uintptr_t>(access, out.frame.definition_identity, 0x2290);
  if (!out.auto_accept_trigger_identity) return;
  if (*out.auto_accept_trigger_identity == 0) {
    out.auto_accept_scalar_raw_u8 = ReadPrisonerQuoteSource12004<std::uint8_t>(access, out.frame.definition_identity, 0x2718);
    if (PrisonerQuoteSourceFrameReady12004(out.frame) && out.auto_accept_scalar_raw_u8)
      out.source_auto_accept = *out.auto_accept_scalar_raw_u8 != 0;
    return;
  }
  out.auto_accept_trigger_raw = ReadPrisonerAutoAcceptTriggerCondition12004(access, out.frame,
      out.caller_aliases, out.auto_accept_trigger_identity);
  const auto root = ReadPrisonerTriggerRootScopeGate12004(access, out.frame,
      *out.auto_accept_trigger_identity, out.frame.original_scope_identity);
  out.auto_accept_condition = EvaluatePrisonerAutoAcceptTriggerCondition12004(*out.auto_accept_trigger_raw, root);
  out.source_auto_accept = out.auto_accept_condition->accepted;
}
std::int64_t PrisonerQuoteCostRound310D07012004(std::int64_t value) noexcept {
  const auto bits = std::bit_cast<std::uint64_t>(value);
  const auto biased = bits + (value < 0 ? std::uint64_t{0} - 50000U : std::uint64_t{50000});
  constexpr std::uint64_t magic = 0x29F16B11C6D1E109ULL;
  auto high = MultiplyHigh(magic, biased);
  if (biased >> 63) high -= magic; // signed high half of IMUL
  const auto shifted = (high >> 14) | ((high >> 63) ? (~std::uint64_t{0} << 50) : 0);
  const auto truncated = shifted + (shifted >> 63);
  const auto narrowed = std::bit_cast<std::int32_t>(static_cast<std::uint32_t>(truncated));
  return static_cast<std::int64_t>(narrowed) * std::int64_t{100000};
}
void ProjectPrisonerQuoteCosts12004(PrisonerQuoteCostSource12004 &cost) {
  cost.projected_q64.reset(); cost.numeric_source_ready = false;
  if (!cost.original_output_copied || !cost.clamp_nonnegative_raw_u8 || !cost.round_raw_u8) {
    cost.unavailable_reason = "cost_parent_original_output_or_flags_unavailable"; return;
  }
  auto values = cost.original_output_q64;
  for (std::size_t i = 0; i < values.size(); ++i) {
    if (!cost.lanes[i].raw_temp_q64) { cost.unavailable_reason = "cost_parent_lane_value_unavailable"; return; }
    values[i] = std::bit_cast<std::int64_t>(std::bit_cast<std::uint64_t>(values[i]) +
        std::bit_cast<std::uint64_t>(*cost.lanes[i].raw_temp_q64));
    if (*cost.clamp_nonnegative_raw_u8 != 0 && values[i] < 0) values[i] = 0;
    if (*cost.round_raw_u8 != 0) values[i] = PrisonerQuoteCostRound310D07012004(values[i]);
  }
  cost.projected_q64 = values; cost.numeric_source_ready = true; cost.unavailable_reason.clear();
}
void ProjectPrisonerQuoteAnswerParent12004(PrisonerQuoteSourceSample12004 &out,
    const std::optional<PrisonerAnswerByteChild12004> &expression,
    const PrisonerAnswerModeChildren12004 &mode0_children, const PrisonerAnswerModeChildren12004 &mode1_children) {
  out.source_answer_raw_u8.reset(); out.answer_source_ready = false; out.answer_effects_source_ready = false;
  const PrisonerAnswerQueryArguments12004 args{std::uint8_t{1}, std::uint8_t{1}, std::uintptr_t{0}, std::uintptr_t{0}};
  const auto predicate = ProjectPrisonerAnswerPredicate3148BB012004(out.answer_predicate_raw, expression);
  out.initial_gate = ProjectPrisonerAnswerInitialGate12004(out.answer_raw, args, predicate.byte_child);
  if (!out.initial_gate.raw_al) return;
  if (*out.initial_gate.raw_al != 3) {
    out.source_answer_raw_u8 = std::uint8_t{0}; out.answer_source_ready = true;
    out.answer_effects_source_ready = out.initial_gate.reached_effects_source_ready; return;
  }
  if (out.answer_raw.context_2e8_raw_u32 && *out.answer_raw.context_2e8_raw_u32 != UINT32_MAX)
    out.mode0 = ProjectPrisonerAnswerModeBranch12004(out.answer_raw, args, 0, mode0_children);
  out.mode1 = ProjectPrisonerAnswerModeBranch12004(out.answer_raw, args, 1, mode1_children);
  if (!out.mode1.raw_al || !out.answer_raw.context_2e8_raw_u32) return;
  const auto m0 = *out.answer_raw.context_2e8_raw_u32 == UINT32_MAX ?
      std::optional<std::uint8_t>{std::uint8_t{3}} : out.mode0.raw_al;
  auto answer = *out.mode1.raw_al;
  if (answer != 3) {
    if (!m0) return;
    if (*m0 == 1) {
      if (answer >= out.answer_lookup_raw_u8.size() || !out.answer_lookup_raw_u8[answer]) return;
      answer = *out.answer_lookup_raw_u8[answer];
    } else if (*m0 == 2) answer = 2;
    else if (*m0 != 0 && *m0 != 3) answer = 3;
  }
  out.source_answer_raw_u8 = answer; out.answer_source_ready = true;
  out.answer_effects_source_ready = out.initial_gate.reached_effects_source_ready &&
      out.mode1.reached_effects_source_ready &&
      (*out.answer_raw.context_2e8_raw_u32 == UINT32_MAX || out.mode0.reached_effects_source_ready);
}
void FinishPrisonerQuoteSourceSample12004(PrisonerQuoteSourceSample12004 &out, bool same_frame) {
  out.frame.same_frame_confirmed = same_frame;
  out.answer_raw.frame = out.frame;
  out.answer_raw.frame_ready = PrisonerQuoteSourceFrameReady12004(out.frame) &&
      out.answer_raw.context_definition == std::optional<std::uintptr_t>{out.frame.definition_identity};
  out.answer_predicate_raw.frame = out.frame;
  out.answer_predicate_raw.input_source_ready = out.answer_raw.frame_ready &&
      out.answer_predicate_raw.definition_identity == out.frame.definition_identity &&
      out.answer_predicate_raw.second_argument_identity == out.frame.original_scope_identity;
  if (out.recipient_score) {
    auto &score = *out.recipient_score;
    score.copied_inputs.frame.same_frame_confirmed = same_frame;
    score.projection = ProjectPrisonerRecipientScore12004(score.copied_inputs);
    score.projected_value_matches_native_final.reset();
    if (score.projection.returned_q64 && score.native_final_output_q64)
      score.projected_value_matches_native_final = *score.projection.returned_q64 == *score.native_final_output_q64;
  }
  PrisonerAnswerModeChildren12004 mode0_children{}, mode1_children{};
  if (out.answer_control_raw) {
    auto &control = *out.answer_control_raw;
    control.membership_raw.frame = out.frame; control.debug_raw.frame = out.frame;
    const auto member = ProjectPrisonerControlMembership12004(control.membership_raw);
    const auto debug = ProjectPrisonerControlDebugFlags12004(control.debug_raw, {});
    mode0_children.id_2baa6f0 = member; mode1_children.id_2baa6f0 = member;
    mode0_children.debug_a75d00 = debug; mode1_children.debug_a75d00 = debug;
  }
  for (const auto reporter : {NegotiatedReplyReporter12004::rva307B910, NegotiatedReplyReporter12004::rva307BAF0}) {
    const auto supplied = ProjectNegotiatedReplyReporterNullContents12004({reporter,
        out.frame.executable_sha256, out.frame.query_sequence, std::uintptr_t{0}, std::uintptr_t{0}});
    const PrisonerAnswerReporterEffects12004 witness{out.frame, static_cast<std::uint32_t>(reporter),
        PrisonerQuoteSourceFrameReady12004(out.frame) && supplied.null_path_source_closed && supplied.no_external_effects};
    if (reporter == NegotiatedReplyReporter12004::rva307B910) {
      mode0_children.reporter_307b910 = witness; mode1_children.reporter_307b910 = witness;
    } else { mode0_children.reporter_307baf0 = witness; mode1_children.reporter_307baf0 = witness; }
  }
  if (out.mode0_scalar_raw) {
    out.mode0_scalar_raw->frame = out.frame; out.mode0_scalar_raw->raw_score.frame = out.frame;
    const auto mode0 = ProjectPrisonerMode0Scalar12004(*out.mode0_scalar_raw);
    if (mode0.returned_qword_bits)
      mode0_children.scope = PrisonerAnswerScopeChild12004{out.frame, 0x307C340,
          out.frame.interaction_context_identity, mode0.returned_qword_bits, mode0.reached_effects_source_ready};
  }
  // The 3761780 numerical post and the observed 307C440 getter remain
  // separate. Missing clone/cleanup effects cannot turn the former into a
  // source witness for the latter's final caller output.
  if (out.native_answer_raw_u8)
    ProjectPrisonerQuoteAnswerParent12004(out, {}, mode0_children, mode1_children);
  else { out.source_answer_raw_u8.reset(); out.answer_source_ready = false; out.answer_effects_source_ready = false; }
  if (!same_frame) { out.source_auto_accept.reset(); if (out.actor_on_send_costs) {
    out.actor_on_send_costs->projected_q64.reset(); out.actor_on_send_costs->numeric_source_ready = false;
    out.actor_on_send_costs->unavailable_reason = "cost_parent_query_frame_changed";
  } }
}

std::string SerializePrisonerSelectedQuoteSource12004(const PrisonerSelectedQuoteSource12004 &source) {
  std::string out = "{\"schema\":\"prisoner-selected-quote-source-12004\",\"schema_version\":1,\"source_ordinal\":" +
      std::to_string(source.source_ordinal) + ",\"quote_kind\":" + String(source.quote_kind) +
      ",\"selected_query_completed\":" + Boolean(source.selected_query_completed) +
      ",\"unavailable_reason\":" + (source.unavailable_reason.empty() ? "null" : String(source.unavailable_reason)) +
      ",\"read_only\":true,\"native_callbacks_added\":0,\"samples\":[";
  for (std::size_t i = 0; i < source.samples.size(); ++i) {
    if (i) out += ',';
    const auto &s = source.samples[i];
    out += "{\"sample_index\":" + std::to_string(i) + ",\"frame\":" + Frame(s.frame) +
        ",\"copied_at_existing_query_call\":" + Boolean(s.copied_at_existing_query_call) +
        ",\"source_answer_raw_u8\":" + Number(s.source_answer_raw_u8) +
        ",\"native_answer_raw_u8\":" + Number(s.native_answer_raw_u8) +
        ",\"answer_source_ready\":" + Boolean(s.answer_source_ready) +
        ",\"answer_effects_source_ready\":" + Boolean(s.answer_effects_source_ready) +
        ",\"source_auto_accept\":" + Boolean(s.source_auto_accept) +
        ",\"native_auto_accept\":" + Boolean(s.native_auto_accept) + ",\"recipient_score\":";
    if (!s.recipient_score) out += "null";
    else {
      const auto &score = *s.recipient_score; const auto &in = score.copied_inputs;
      out += "{\"producer_rva\":58070912,\"score_block_identity\":" + std::to_string(in.score_block_identity) +
          ",\"base_q64\":" + Number(in.base_q64) + ",\"modifiers_data_identity\":" + Number(in.modifiers_data_identity) +
          ",\"modifier_count_raw_i32\":" + Number(in.modifier_count_raw_i32) +
          ",\"raw_inputs_complete\":" + Boolean(in.raw_inputs_complete) +
          ",\"numeric_source_ready\":" + Boolean(score.projection.numeric_source_ready) +
          ",\"projected_q64\":" + Number(score.projection.returned_q64) +
          ",\"native_getter_called\":" + Boolean(score.native_getter_called) +
          ",\"native_getter_returned_output_pointer\":" + Boolean(score.native_getter_returned_output_pointer) +
          ",\"native_final_output_q64\":" + Number(score.native_final_output_q64) +
          ",\"projected_value_matches_native_final\":" + Boolean(score.projected_value_matches_native_final) +
          ",\"unavailable_reason\":" + (score.projection.unavailable_reason.empty() ? "null" : String(score.projection.unavailable_reason)) +
          ",\"ordered_modifier_occurrences\":[";
      for (std::size_t j = 0; j < in.ordered_modifier_occurrences.size(); ++j) {
        if (j) out += ','; const auto &row = in.ordered_modifier_occurrences[j];
        out += "{\"native_occurrence_index\":" + std::to_string(row.native_occurrence_index) +
            ",\"stored_receiver_identity\":" + Number(row.stored_receiver_identity) +
            ",\"vtable_identity\":" + Number(row.vtable_identity) +
            ",\"slot30_target_identity\":" + Number(row.slot30_target_identity) +
            ",\"raw_receiver_ready\":" + Boolean(row.raw_receiver_ready) + "}";
      }
      out += "]}";
    }
    out += ",\"actor_on_send_costs\":";
    if (!s.actor_on_send_costs) out += "null";
    else {
      const auto &c = *s.actor_on_send_costs;
      out += "{\"cost_block_identity\":" + std::to_string(c.cost_block_identity) +
          ",\"numeric_source_ready\":" + Boolean(c.numeric_source_ready) +
          ",\"native_getter_called\":" + Boolean(c.native_getter_called) +
          ",\"clamp_nonnegative_raw_u8\":" + Number(c.clamp_nonnegative_raw_u8) +
          ",\"round_raw_u8\":" + Number(c.round_raw_u8) + ",\"projected_q64\":";
      const auto values = [&](const std::optional<std::array<std::int64_t, 10>> &v) {
        std::string a = "null"; if (v) { a = "["; for (std::size_t n = 0; n < v->size(); ++n) {
          if (n) a += ','; a += std::to_string((*v)[n]); } a += ']'; } return a;
      };
      out += values(c.projected_q64) + ",\"native_final_q64\":" + values(c.native_final_q64) +
          ",\"original_output_copied\":" + Boolean(c.original_output_copied) +
          ",\"original_output_q64\":" + values(c.original_output_copied ?
              std::optional<std::array<std::int64_t, 10>>{c.original_output_q64} : std::nullopt) +
          ",\"unavailable_reason\":" + (c.unavailable_reason.empty() ? "null" : String(c.unavailable_reason)) +
          ",\"lanes\":[";
      for (std::size_t n = 0; n < c.lanes.size(); ++n) {
        if (n) out += ','; const auto &lane = c.lanes[n];
        out += "{\"lane_index\":" + std::to_string(n) + ",\"lane_identity\":" + std::to_string(lane.lane_identity) +
            ",\"mode_c0_i32\":" + Number(lane.mode_c0_i32) + ",\"raw_temp_q64\":" + Number(lane.raw_temp_q64) +
            ",\"branch\":" + String(lane.branch) + ",\"unavailable_reason\":" +
            (lane.unavailable_reason.empty() ? "null" : String(lane.unavailable_reason)) + "}";
      }
      out += "]}";
    }
    out += '}';
  }
  return out + "]}";
}
bool AppendPrisonerSelectedQuoteSource12004(std::string &wire, const PrisonerSelectedQuoteSource12004 &source) {
  if (wire.size() < 2 || !wire.ends_with("}}")) return false;
  wire.insert(wire.size() - 2, ",\"prisoner_selected_quote_source_12004\":" + SerializePrisonerSelectedQuoteSource12004(source));
  return true;
}
} // namespace xar::ck3_12004
