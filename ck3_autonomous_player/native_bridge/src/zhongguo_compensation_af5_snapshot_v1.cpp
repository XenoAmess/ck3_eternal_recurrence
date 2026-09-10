#include "xar_bridge/zhongguo_compensation_af5_snapshot_v1.hpp"

#include <iomanip>
#include <limits>
#include <sstream>

namespace xar::ck3_11906 {
namespace {

using Raw = ZhongguoRawVariableV1;
using OwnerRows = std::array<Raw, kZhongguoCompensationAf5OwnerVariableAllowlist.size()>;
using SubjectRows = std::array<Raw, kZhongguoCompensationAf5SubjectVariableAllowlist.size()>;

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

bool IdentityReady(const game::ZhongguoCompensationAf5IdentityV1 &identity) {
  return Positive(identity.owner_character_id) &&
         Positive(identity.subject_character_id) &&
         Positive(identity.cycle_serial) && Positive(identity.case_serial);
}

bool SameIdentity(const game::ZhongguoCompensationAf5IdentityV1 &left,
                  const game::ZhongguoCompensationAf5IdentityV1 &right) {
  return IdentityReady(left) && IdentityReady(right) &&
         left.owner_character_id.value == right.owner_character_id.value &&
         left.subject_character_id.value == right.subject_character_id.value &&
         left.cycle_serial.value == right.cycle_serial.value &&
         left.case_serial.value == right.case_serial.value;
}

void Identity(const Raw *rows, game::ZhongguoCompensationAf5IdentityV1 &out) {
  Character(rows[0], out.owner_character_id);
  Character(rows[1], out.subject_character_id);
  Number(rows[2], out.cycle_serial);
  Number(rows[3], out.case_serial);
}

void Receipt(const Raw *rows, game::ZhongguoCompensationAf5ReceiptV1 &out) {
  Identity(rows, out.identity);
  Number(rows[4], out.state);
  Boolean(rows[5], out.active);
  Boolean(rows[6], out.consumed);
  Number(rows[7], out.route);
}

void Decode(const OwnerRows &owner, const SubjectRows &subject,
            game::ZhongguoCompensationAf5SnapshotV1 &out) {
  Number(owner[0], out.portfolio.domain);
  Number(owner[1], out.portfolio.stage);
  Number(owner[2], out.portfolio.completed_cycle);
  Boolean(owner[3], out.portfolio.visible_pending);
  Identity(owner.data() + 4, out.portfolio.result_identity);
  Identity(subject.data(), out.af_case.identity);
  Number(subject[4], out.af_case.revision);
  Number(subject[5], out.af_case.state);
  Boolean(subject[6], out.af_case.active);
  Number(subject[7], out.af_case.last_operation);
  Number(subject[8], out.af_case.last_route);
  Boolean(subject[9], out.af_case.repurchase_resolved);
  Boolean(subject[10], out.af_case.unit_conserved);
  Receipt(subject.data() + 11, out.m299);
  Receipt(subject.data() + 19, out.m300);
  Number(subject[27], out.af_case.result_case_serial);
}

bool ReceiptCommitted(const game::ZhongguoCompensationAf5ReceiptV1 &receipt,
                      const game::ZhongguoCompensationAf5IdentityV1 &identity) {
  return SameIdentity(receipt.identity, identity) &&
         Equal(receipt.state, std::int64_t{5}) &&
         Equal(receipt.active, true) && Equal(receipt.consumed, true) &&
         Equal(receipt.route, std::int64_t{3});
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

std::string IdentityJson(const game::ZhongguoCompensationAf5IdentityV1 &identity) {
  return "{\"owner_character_id\":" + TypedJson(identity.owner_character_id) +
         ",\"subject_character_id\":" + TypedJson(identity.subject_character_id) +
         ",\"cycle_serial\":" + TypedJson(identity.cycle_serial) +
         ",\"case_serial\":" + TypedJson(identity.case_serial) + "}";
}

std::string ReceiptJson(const game::ZhongguoCompensationAf5ReceiptV1 &receipt) {
  return "{\"identity\":" + IdentityJson(receipt.identity) +
         ",\"state\":" + TypedJson(receipt.state) +
         ",\"active\":" + TypedJson(receipt.active) +
         ",\"consumed\":" + TypedJson(receipt.consumed) +
         ",\"route\":" + TypedJson(receipt.route) + "}";
}

} // namespace

ZhongguoCompensationAf5NativeEnvironmentV1
BindZhongguoCompensationAf5NativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept {
  return BindZhongguoCaseNativeEnvironmentV1(module_base, exact_build_admitted);
}

game::ReadZhongguoCompensationAf5ResultV1 ReadZhongguoCompensationAf5SnapshotV1(
    const ZhongguoCompensationAf5NativeEnvironmentV1 &environment,
    const ZhongguoCompensationAf5AccessV1 &access,
    const ZhongguoCompensationAf5RequestV1 &request,
    game::ZhongguoCompensationAf5SnapshotV1 &output) noexcept {
  output = {};
  output.request_nonce = request.request_nonce;
  output.snapshot_revision = request.expected_snapshot_revision;
  Decode({}, {}, output);
  const auto fail = [&](std::string_view reason) {
    output.status = game::ZhongguoCompensationAf5StatusV1::unavailable;
    output.readiness = {};
    output.terminal = false;
    output.unavailable_reason.assign(reason);
    return game::ReadZhongguoCompensationAf5ResultV1::unavailable;
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
                 kZhongguoCompensationAf5OwnerVariableAllowlist, rows) ==
             ReadZhongguoFixedVariableSetResultV1::available;
    };
    if (!read_owner(owner)) return fail("owner_projection_read_failed");
    game::ZhongguoTypedIntegerV1 subject_id;
    // The result subject persists after next-day portfolio cursor cleanup.
    Character(owner[5], subject_id);
    if (!Positive(subject_id)) return fail("portfolio_result_subject_unavailable");
    output.subject_character_id = static_cast<std::int32_t>(*subject_id.value);
    const auto read_subject = [&](SubjectRows &rows) {
      return ReadZhongguoFixedVariableSetV1(
                 environment, access, output.subject_character_id,
                 kZhongguoCompensationAf5SubjectVariableAllowlist, rows) ==
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
    const auto &identity = output.af_case.identity;
    ready.player_owner_binding_ready =
        Equal(identity.owner_character_id,
              std::int64_t{before.played_character_id}) &&
        Equal(output.portfolio.result_identity.owner_character_id,
              std::int64_t{before.played_character_id});
    game::ZhongguoTypedIntegerV1 cursor_subject;
    Character(owner[8], cursor_subject);
    ready.portfolio_subject_binding_ready =
        Equal(identity.subject_character_id, *subject_id.value) &&
        (!owner[8].present || Equal(cursor_subject, *subject_id.value));
    ready.same_case_identity_ready =
        IdentityReady(identity) && IdentityReady(output.portfolio.result_identity) &&
        identity.cycle_serial.value == output.portfolio.result_identity.cycle_serial.value &&
        output.af_case.result_case_serial.available &&
        output.af_case.result_case_serial.value == output.portfolio.result_identity.case_serial.value &&
        Positive(output.af_case.revision);
    ready.same_frame_ready = true;
    ready.ready = ready.player_owner_binding_ready &&
                  ready.portfolio_subject_binding_ready &&
                  ready.same_case_identity_ready && ready.same_frame_ready;
    const bool portfolio_closed =
        Equal(output.portfolio.domain, std::int64_t{4}) ||
        (!owner[0].present && Positive(identity.cycle_serial) &&
         Equal(output.portfolio.completed_cycle, *identity.cycle_serial.value));
    output.terminal = ready.ready && portfolio_closed &&
        Equal(output.portfolio.visible_pending, false) &&
        Equal(output.af_case.state, std::int64_t{6}) &&
        Equal(output.af_case.active, false) &&
        Equal(output.af_case.last_operation, std::int64_t{300}) &&
        Equal(output.af_case.last_route, std::int64_t{3}) &&
        Equal(output.af_case.repurchase_resolved, true) &&
        Equal(output.af_case.unit_conserved, true) &&
        ReceiptCommitted(output.m299, identity) &&
        ReceiptCommitted(output.m300, identity);
    output.status = game::ZhongguoCompensationAf5StatusV1::available;
    output.unavailable_reason = ready.ready ? "" : "af5_identity_not_bound";
    return game::ReadZhongguoCompensationAf5ResultV1::available;
  } catch (...) {
    return fail("projection_exception");
  }
}

std::string SerializeZhongguoCompensationAf5SnapshotV1(
    const game::ZhongguoCompensationAf5SnapshotV1 &s) {
  auto case_identity = IdentityJson(s.af_case.identity);
  case_identity.pop_back();
  case_identity += ",\"revision\":" + TypedJson(s.af_case.revision) + "}";
  std::ostringstream out;
  out << std::boolalpha << "{\"schema_version\":1,\"status\":\""
      << (s.status == game::ZhongguoCompensationAf5StatusV1::available
              ? "available" : "unavailable")
      << "\",\"capability\":\"" << kZhongguoCompensationAf5SnapshotV1Capability
      << "\",\"source_backend_id\":\"" << kZhongguoCompensationAf5SnapshotV1BackendId
      << "\",\"request_nonce\":\"" << Escape(s.request_nonce)
      << "\",\"snapshot_revision\":" << s.snapshot_revision
      << ",\"date_raw\":" << s.date_raw << ",\"paused\":" << s.paused
      << ",\"player_character_id\":" << s.player_character_id
      << ",\"subject_character_id\":" << s.subject_character_id
      << ",\"af5\":{\"portfolio\":{\"domain\":" << TypedJson(s.portfolio.domain)
      << ",\"stage\":" << TypedJson(s.portfolio.stage)
      << ",\"completed_cycle\":" << TypedJson(s.portfolio.completed_cycle)
      << ",\"visible_pending\":" << TypedJson(s.portfolio.visible_pending)
      << ",\"result_identity\":" << IdentityJson(s.portfolio.result_identity)
      << "},\"case\":{\"identity\":" << case_identity
      << ",\"state\":" << TypedJson(s.af_case.state)
      << ",\"result_case_serial\":" << TypedJson(s.af_case.result_case_serial)
      << ",\"active\":" << TypedJson(s.af_case.active)
      << ",\"last_operation\":" << TypedJson(s.af_case.last_operation)
      << ",\"last_route\":" << TypedJson(s.af_case.last_route)
      << ",\"repurchase_resolved\":" << TypedJson(s.af_case.repurchase_resolved)
      << ",\"unit_conserved\":" << TypedJson(s.af_case.unit_conserved)
      << "},\"m299\":" << ReceiptJson(s.m299)
      << ",\"m300\":" << ReceiptJson(s.m300) << "}"
      << ",\"readiness\":{\"player_owner_binding_ready\":"
      << s.readiness.player_owner_binding_ready
      << ",\"portfolio_subject_binding_ready\":"
      << s.readiness.portfolio_subject_binding_ready
      << ",\"same_case_identity_ready\":" << s.readiness.same_case_identity_ready
      << ",\"same_frame_ready\":" << s.readiness.same_frame_ready
      << ",\"ready\":" << s.readiness.ready << "}"
      << ",\"terminal\":" << s.terminal << ",\"unavailable_reason\":";
  if (s.unavailable_reason.empty()) out << "null";
  else out << '"' << Escape(s.unavailable_reason) << '"';
  out << '}';
  return out.str();
}

} // namespace xar::ck3_11906
