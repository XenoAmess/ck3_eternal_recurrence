#include "xar_bridge/zhongguo_workforce_owner_snapshot_v1.hpp"

#include <iomanip>
#include <limits>
#include <sstream>

namespace xar::ck3_11906 {
namespace {

using Raw = ZhongguoRawVariableV1;
using OwnerRows = std::array<Raw, kZhongguoWorkforceOwnerOwnerVariableAllowlist.size()>;
using SubjectRows = std::array<Raw, kZhongguoWorkforceOwnerSubjectVariableAllowlist.size()>;

template <typename T>
void Unavailable(game::ZhongguoTypedValueV1<T> &field, std::string_view reason) {
  field = {};
  field.unavailable_reason.assign(reason);
}

void Number(const Raw &raw, game::ZhongguoTypedIntegerV1 &field) {
  if (!raw.present) return Unavailable(field, "variable_absent");
  if (raw.kind != 1 || raw.payload % 100'000 != 0)
    return Unavailable(field, "value_type_mismatch");
  field.available = true;
  field.value = raw.payload / 100'000;
  field.unavailable_reason.clear();
}

void Character(const Raw &raw, game::ZhongguoTypedIntegerV1 &field) {
  if (!raw.present) return Unavailable(field, "variable_absent");
  if (raw.kind != 4 || raw.payload <= 0 ||
      raw.payload > std::numeric_limits<std::int32_t>::max())
    return Unavailable(field, "character_identity_invalid");
  field.available = true;
  field.value = raw.payload;
  field.unavailable_reason.clear();
}

void Boolean(const Raw &raw, game::ZhongguoTypedBooleanV1 &field) {
  game::ZhongguoTypedIntegerV1 number;
  Number(raw, number);
  if (!number.available) return Unavailable(field, number.unavailable_reason);
  if (*number.value != 0 && *number.value != 1)
    return Unavailable(field, "boolean_value_invalid");
  field.available = true;
  field.value = *number.value == 1;
  field.unavailable_reason.clear();
}

template <typename T>
bool Equal(const game::ZhongguoTypedValueV1<T> &field, T value) {
  return field.available && field.value && *field.value == value;
}

bool Positive(const game::ZhongguoTypedIntegerV1 &field) {
  return field.available && field.value && *field.value > 0;
}

void Decode(const OwnerRows &owner, const SubjectRows &subject,
            game::ZhongguoWorkforceOwnerSnapshotV1 &out) {
  { Character(owner[0], out.central.subject_character_id); } // zg361_p2c_subject
  { Number(owner[1], out.central.cycle_serial); } // zg361_p2c_cycle
  { Number(owner[2], out.central.case_serial); } // zg361_p2c_case_serial
  { Number(owner[3], out.central.stage11_status); } // zg361_p2c_stage_11_status
  { Number(owner[4], out.source.status); } // zg361_p2c_m360_source_status
  { Character(owner[5], out.source.owner_character_id); } // zg361_p2c_m360_source_owner
  { Character(owner[6], out.source.subject_character_id); } // zg361_p2c_m360_source_subject
  { Number(owner[7], out.source.p2c_cycle_serial); } // zg361_p2c_m360_source_p2c_cycle
  { Number(owner[8], out.source.p2c_case_serial); } // zg361_p2c_m360_source_p2c_case
  { Number(owner[9], out.source.al_cycle_serial); } // zg361_p2c_m360_source_al_cycle
  { Number(owner[10], out.source.al_case_serial); } // zg361_p2c_m360_source_al_case
  { Character(subject[0], out.al_case.owner_character_id); } // zg361_case_al_owner
  { Character(subject[1], out.al_case.subject_character_id); } // zg361_case_al_subject
  { Number(subject[2], out.al_case.cycle_serial); } // zg361_case_al_cycle_serial
  { Number(subject[3], out.al_case.case_serial); } // zg361_case_al_case_serial
  { Number(subject[4], out.al_case.state); } // zg361_case_al_state
  { Boolean(subject[5], out.al_case.active); } // zg361_case_al_active
  { Number(subject[6], out.al_case.revision); } // zg361_case_al_revision
  { Character(subject[7], out.m360_receipt.owner_character_id); } // zg361_we_m360_receipt_owner
  { Character(subject[8], out.m360_receipt.subject_character_id); } // zg361_we_m360_receipt_subject
  { Number(subject[9], out.m360_receipt.cycle_serial); } // zg361_we_m360_receipt_cycle
  { Number(subject[10], out.m360_receipt.case_serial); } // zg361_we_m360_receipt_case
  { Number(subject[11], out.m360_receipt.state); } // zg361_we_m360_receipt_state
  { Number(subject[12], out.m360_receipt.choice); } // zg361_we_m360_receipt_choice
  { Boolean(subject[13], out.portfolio.closed); } // zg361_we_portfolio_closed
  { Number(subject[14], out.portfolio.status); } // zg361_we_portfolio_status
  { Number(subject[15], out.portfolio.cycle_serial); } // zg361_we_portfolio_cycle
  { Boolean(subject[16], out.portfolio.final_conservation_ok); } // zg361_we_final_conservation_ok
  { Boolean(subject[17], out.portfolio.terminal_history_accruing); } // zg361_we_portfolio_terminal_history_accruing
  { Number(subject[18], out.portfolio.history_cycle_count); } // zg361_we_portfolio_history_cycle_count
  { Boolean(subject[19], out.portfolio.terminal_success); } // zg361_we_portfolio_terminal_success
  { Boolean(subject[20], out.portfolio.terminal_na); } // zg361_we_portfolio_terminal_na
  { Number(subject[21], out.portfolio.terminal_reason); } // zg361_we_portfolio_terminal_reason
  { Number(subject[22], out.portfolio.terminal_owned_operations); } // zg361_we_portfolio_terminal_owned_operations
  { Number(subject[23], out.portfolio.terminal_skipped_manager_only); } // zg361_we_portfolio_terminal_skipped_manager_only
  { Number(subject[24], out.portfolio.terminal_skipped_charter); } // zg361_we_portfolio_terminal_skipped_charter
}

std::string Escape(std::string_view text) {
  std::ostringstream out;
  for (unsigned char ch : text) {
    if (ch == '\\') out << "\\\\";
    else if (ch == '"') out << "\\\"";
    else if (ch < 0x20)
      out << "\\u" << std::hex << std::setw(4) << std::setfill('0')
          << static_cast<int>(ch) << std::dec;
    else out << static_cast<char>(ch);
  }
  return out.str();
}

template <typename T>
std::string TypedJson(const game::ZhongguoTypedValueV1<T> &field) {
  std::ostringstream out;
  out << std::boolalpha << "{\"status\":\""
      << (field.available ? "available" : "unavailable") << "\",\"value\":";
  if (field.available && field.value) out << *field.value;
  else out << "null";
  out << ",\"unavailable_reason\":";
  if (field.unavailable_reason.empty()) out << "null";
  else out << '"' << Escape(field.unavailable_reason) << '"';
  out << '}';
  return out.str();
}

std::string CentralJson(const game::ZhongguoWorkforceOwnerCentralV1 &value) {
  return "{\"subject_character_id\":" + TypedJson(value.subject_character_id) +
         ",\"cycle_serial\":" + TypedJson(value.cycle_serial) +
         ",\"case_serial\":" + TypedJson(value.case_serial) +
         ",\"stage11_status\":" + TypedJson(value.stage11_status) + "}";
}

std::string SourceJson(const game::ZhongguoWorkforceOwnerSourceV1 &value) {
  return "{\"status\":" + TypedJson(value.status) +
         ",\"owner_character_id\":" + TypedJson(value.owner_character_id) +
         ",\"subject_character_id\":" + TypedJson(value.subject_character_id) +
         ",\"p2c_cycle_serial\":" + TypedJson(value.p2c_cycle_serial) +
         ",\"p2c_case_serial\":" + TypedJson(value.p2c_case_serial) +
         ",\"al_cycle_serial\":" + TypedJson(value.al_cycle_serial) +
         ",\"al_case_serial\":" + TypedJson(value.al_case_serial) + "}";
}

std::string AlCaseJson(const game::ZhongguoWorkforceOwnerAlCaseV1 &value) {
  return "{\"owner_character_id\":" + TypedJson(value.owner_character_id) +
         ",\"subject_character_id\":" + TypedJson(value.subject_character_id) +
         ",\"cycle_serial\":" + TypedJson(value.cycle_serial) +
         ",\"case_serial\":" + TypedJson(value.case_serial) +
         ",\"state\":" + TypedJson(value.state) +
         ",\"active\":" + TypedJson(value.active) +
         ",\"revision\":" + TypedJson(value.revision) + "}";
}

std::string M360ReceiptJson(const game::ZhongguoWorkforceOwnerM360ReceiptV1 &value) {
  return "{\"owner_character_id\":" + TypedJson(value.owner_character_id) +
         ",\"subject_character_id\":" + TypedJson(value.subject_character_id) +
         ",\"cycle_serial\":" + TypedJson(value.cycle_serial) +
         ",\"case_serial\":" + TypedJson(value.case_serial) +
         ",\"state\":" + TypedJson(value.state) +
         ",\"choice\":" + TypedJson(value.choice) + "}";
}

std::string PortfolioJson(const game::ZhongguoWorkforceOwnerPortfolioV1 &value) {
  return "{\"closed\":" + TypedJson(value.closed) +
         ",\"status\":" + TypedJson(value.status) +
         ",\"cycle_serial\":" + TypedJson(value.cycle_serial) +
         ",\"final_conservation_ok\":" + TypedJson(value.final_conservation_ok) +
         ",\"terminal_history_accruing\":" + TypedJson(value.terminal_history_accruing) +
         ",\"history_cycle_count\":" + TypedJson(value.history_cycle_count) +
         ",\"terminal_success\":" + TypedJson(value.terminal_success) +
         ",\"terminal_na\":" + TypedJson(value.terminal_na) +
         ",\"terminal_reason\":" + TypedJson(value.terminal_reason) +
         ",\"terminal_owned_operations\":" + TypedJson(value.terminal_owned_operations) +
         ",\"terminal_skipped_manager_only\":" + TypedJson(value.terminal_skipped_manager_only) +
         ",\"terminal_skipped_charter\":" + TypedJson(value.terminal_skipped_charter) + "}";
}

} // namespace

ZhongguoWorkforceOwnerNativeEnvironmentV1 BindZhongguoWorkforceOwnerNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept {
  return BindZhongguoCaseNativeEnvironmentV1(module_base, exact_build_admitted);
}

game::ReadZhongguoWorkforceOwnerResultV1 ReadZhongguoWorkforceOwnerSnapshotV1(
    const ZhongguoWorkforceOwnerNativeEnvironmentV1 &environment,
    const ZhongguoWorkforceOwnerAccessV1 &access,
    const ZhongguoWorkforceOwnerRequestV1 &request,
    game::ZhongguoWorkforceOwnerSnapshotV1 &output) noexcept {
  output = {};
  output.request_nonce = request.request_nonce;
  output.snapshot_revision = request.expected_snapshot_revision;
  Decode({}, {}, output);
  const auto fail = [&](std::string_view reason) {
    output.status = game::ZhongguoWorkforceOwnerStatusV1::unavailable;
    output.readiness = {};
    output.terminal = false;
    output.terminal_kind = "none";
    output.unavailable_reason.assign(reason);
    return game::ReadZhongguoWorkforceOwnerResultV1::unavailable;
  };
  try {
    if (request.request_nonce.empty() || request.expected_snapshot_revision == 0)
      return fail("invalid_request");
    if (!IsZhongguoVariableAbiExactV1(environment))
      return fail("exact_build_not_admitted");
    if (access.capture_frame == nullptr || access.is_main_thread == nullptr ||
        !access.is_main_thread(access.context))
      return fail("application_main_thread_required");
    game::ZhongguoCaseFrameV1 before{};
    if (!access.capture_frame(access.context, before))
      return fail("frame_capture_failed");
    output.date_raw = before.date_raw;
    output.paused = before.paused;
    output.player_character_id = before.played_character_id;
    if (before.snapshot_revision != request.expected_snapshot_revision)
      return fail("revision_mismatch");
    if (!before.paused || !before.map_ready || !before.has_played_character ||
        !before.played_character_alive || before.played_character_id <= 0)
      return fail("paused_player_unavailable");
    OwnerRows owner{}, owner_again{};
    SubjectRows subject{}, subject_again{};
    const auto read_owner = [&](OwnerRows &rows) {
      return ReadZhongguoFixedVariableSetV1(
                 environment, access, before.played_character_id,
                 kZhongguoWorkforceOwnerOwnerVariableAllowlist, rows) ==
             ReadZhongguoFixedVariableSetResultV1::available;
    };
    if (!read_owner(owner)) return fail("owner_projection_read_failed");
    game::ZhongguoTypedIntegerV1 subject_id;
    // Central's subject exists before M360 and on the legitimate N/A branch.
    Character(owner[0], subject_id);
    if (!Positive(subject_id)) return fail("central_subject_unavailable");
    output.subject_character_id = static_cast<std::int32_t>(*subject_id.value);
    const auto read_subject = [&](SubjectRows &rows) {
      return ReadZhongguoFixedVariableSetV1(
                 environment, access, output.subject_character_id,
                 kZhongguoWorkforceOwnerSubjectVariableAllowlist, rows) ==
             ReadZhongguoFixedVariableSetResultV1::available;
    };
    if (!read_subject(subject)) return fail("subject_projection_read_failed");
    if (!read_owner(owner_again) || !read_subject(subject_again))
      return fail("second_projection_read_failed");
    game::ZhongguoCaseFrameV1 after{};
    if (!access.capture_frame(access.context, after))
      return fail("frame_capture_failed");
    if (before != after || owner != owner_again || subject != subject_again)
      return fail("state_changed");
    Decode(owner, subject, output);
    auto &ready = output.readiness;
    const auto &c = output.central;
    const auto &s = output.source;
    const auto &al = output.al_case;
    const auto &p = output.portfolio;
    ready.player_owner_binding_ready =
        Equal(al.owner_character_id, std::int64_t{before.played_character_id});
    ready.portfolio_subject_binding_ready =
        Equal(al.subject_character_id, *subject_id.value);
    const bool source_bound = !owner[5].present || (
        Equal(s.owner_character_id, std::int64_t{before.played_character_id}) &&
        Equal(s.subject_character_id, *subject_id.value) &&
        Positive(s.p2c_cycle_serial) && s.p2c_cycle_serial.value == c.cycle_serial.value &&
        Positive(s.p2c_case_serial) && s.p2c_case_serial.value == c.case_serial.value &&
        Positive(s.al_cycle_serial) && s.al_cycle_serial.value == al.cycle_serial.value &&
        Positive(s.al_case_serial) && s.al_case_serial.value == al.case_serial.value);
    ready.case_identity_ready = Positive(c.cycle_serial) && Positive(c.case_serial) &&
        Positive(al.cycle_serial) && Positive(al.case_serial) && Positive(al.revision) &&
        Positive(al.state) && *al.state.value <= 8 && al.active.available &&
        al.cycle_serial.value == c.cycle_serial.value &&
        Positive(p.cycle_serial) && p.cycle_serial.value == c.cycle_serial.value && source_bound;
    ready.same_frame_ready = true;
    ready.ready = ready.player_owner_binding_ready && ready.portfolio_subject_binding_ready &&
                  ready.case_identity_ready && ready.same_frame_ready;
    const bool common = ready.ready && Equal(p.closed, true) && Equal(p.final_conservation_ok, true);
    // These are the three product-owned stage-11 closure predicates. Central's
    // stage11_status is exposed separately because it advances on the next pump.
    const bool success = common && Equal(p.status, std::int64_t{6});
    const bool history = common && Equal(p.status, std::int64_t{8}) &&
        Equal(p.terminal_history_accruing, true) && Positive(p.history_cycle_count) &&
        *p.history_cycle_count.value <= 3 &&
        Equal(p.terminal_owned_operations, std::int64_t{39}) &&
        Equal(p.terminal_skipped_charter, std::int64_t{1}) &&
        Equal(p.terminal_success, false) && Equal(al.active, false) &&
        Equal(al.state, std::int64_t{8});
    const bool na = common && Equal(p.status, std::int64_t{7}) &&
        Equal(p.terminal_na, true) &&
        (Equal(p.terminal_reason, std::int64_t{360361}) || Equal(p.terminal_reason, std::int64_t{360362})) &&
        Equal(p.terminal_owned_operations, std::int64_t{38}) &&
        Equal(p.terminal_skipped_manager_only, std::int64_t{2}) &&
        Equal(p.terminal_success, false) && Equal(al.active, false);
    output.terminal = success || history || na;
    output.terminal_kind = success ? "success" : history ? "history_accruing" : na ? "not_applicable" : "none";
    output.status = game::ZhongguoWorkforceOwnerStatusV1::available;
    output.unavailable_reason = ready.ready ? "" : "workforce_owner_identity_not_bound";
    return game::ReadZhongguoWorkforceOwnerResultV1::available;
  } catch (...) {
    return fail("projection_exception");
  }
}

std::string SerializeZhongguoWorkforceOwnerSnapshotV1(
    const game::ZhongguoWorkforceOwnerSnapshotV1 &s) {
  std::ostringstream out;
  out << std::boolalpha << "{\"schema_version\":1,\"status\":\""
      << (s.status == game::ZhongguoWorkforceOwnerStatusV1::available ? "available" : "unavailable")
      << "\",\"capability\":\"" << kZhongguoWorkforceOwnerSnapshotV1Capability
      << "\",\"source_backend_id\":\"" << kZhongguoWorkforceOwnerSnapshotV1BackendId
      << "\",\"request_nonce\":\"" << Escape(s.request_nonce)
      << "\",\"snapshot_revision\":" << s.snapshot_revision
      << ",\"date_raw\":" << s.date_raw << ",\"paused\":" << s.paused
      << ",\"player_character_id\":" << s.player_character_id
      << ",\"subject_character_id\":" << s.subject_character_id
      << ",\"workforce\":{\"central\":" << CentralJson(s.central)
      << ",\"source\":" << SourceJson(s.source)
      << ",\"al_case\":" << AlCaseJson(s.al_case)
      << ",\"m360_receipt\":" << M360ReceiptJson(s.m360_receipt)
      << ",\"portfolio\":" << PortfolioJson(s.portfolio) << "}"
      << ",\"readiness\":{\"player_owner_binding_ready\":" << s.readiness.player_owner_binding_ready
      << ",\"portfolio_subject_binding_ready\":" << s.readiness.portfolio_subject_binding_ready
      << ",\"case_identity_ready\":" << s.readiness.case_identity_ready
      << ",\"same_frame_ready\":" << s.readiness.same_frame_ready
      << ",\"ready\":" << s.readiness.ready << "}"
      << ",\"terminal\":" << s.terminal
      << ",\"terminal_kind\":\"" << s.terminal_kind << "\",\"unavailable_reason\":";
  if (s.unavailable_reason.empty()) out << "null";
  else out << '"' << Escape(s.unavailable_reason) << '"';
  out << '}';
  return out.str();
}

} // namespace xar::ck3_11906
