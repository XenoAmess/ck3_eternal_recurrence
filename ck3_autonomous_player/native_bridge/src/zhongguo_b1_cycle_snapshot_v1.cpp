#include "xar_bridge/zhongguo_b1_cycle_snapshot_v1.hpp"

#include <array>
#include <cstdint>
#include <limits>
#include <string_view>

namespace xar::ck3_11906 {
namespace {

constexpr std::int64_t kFixedScale = 100'000;
using Rows = std::array<ZhongguoRawVariableV1,
                        kZhongguoB1CycleSnapshotV1VariableAllowlist.size()>;

template <typename Value>
void Unavailable(game::ZhongguoTypedValueV1<Value> &field,
                 std::string_view reason) {
  field.available = false;
  field.value.reset();
  field.unavailable_reason.assign(reason);
}

template <typename Value>
void Available(game::ZhongguoTypedValueV1<Value> &field, Value value) {
  field.available = true;
  field.value = value;
  field.unavailable_reason.clear();
}

void Integer(const ZhongguoRawVariableV1 &raw,
             game::ZhongguoTypedIntegerV1 &field) {
  if (!raw.present) return Unavailable(field, "variable_absent");
  if (raw.kind != 1 || raw.payload % kFixedScale != 0)
    return Unavailable(field, "value_type_mismatch");
  Available(field, raw.payload / kFixedScale);
}

void Boolean(const ZhongguoRawVariableV1 &raw,
             game::ZhongguoTypedBooleanV1 &field) {
  game::ZhongguoTypedIntegerV1 integer;
  Integer(raw, integer);
  if (!integer.available)
    return Unavailable(field, integer.unavailable_reason);
  if (*integer.value != 0 && *integer.value != 1)
    return Unavailable(field, "value_out_of_range");
  Available(field, *integer.value == 1);
}

template <typename Value>
bool IsAvailable(const game::ZhongguoTypedValueV1<Value> &field) noexcept {
  return field.available && field.value.has_value();
}

bool Nonnegative(const game::ZhongguoTypedIntegerV1 &field) noexcept {
  return IsAvailable(field) && *field.value >= 0;
}

bool ValidNonce(std::string_view nonce) noexcept {
  if (nonce.empty() || nonce.size() > 64) return false;
  for (std::size_t index = 0; index < nonce.size(); ++index) {
    const char c = nonce[index];
    const bool alnum = (c >= 'A' && c <= 'Z') ||
                       (c >= 'a' && c <= 'z') ||
                       (c >= '0' && c <= '9');
    if ((!alnum && c != '.' && c != '_' && c != ':' && c != '-') ||
        (index == 0 && !alnum))
      return false;
  }
  return true;
}

void AllUnavailable(game::ZhongguoB1CycleSnapshotV1 &out,
                    std::string_view reason) {
#define XAR_UNAVAILABLE(field) Unavailable((field), reason)
  XAR_UNAVAILABLE(out.cycle.cycle_serial);
  XAR_UNAVAILABLE(out.cycle.case_serial);
  XAR_UNAVAILABLE(out.cycle.state);
  XAR_UNAVAILABLE(out.cycle.open_year);
  XAR_UNAVAILABLE(out.cycle.runtime_schema);
  XAR_UNAVAILABLE(out.cycle.active);
  XAR_UNAVAILABLE(out.roster.subject_count);
  XAR_UNAVAILABLE(out.roster.before_prune_count);
  XAR_UNAVAILABLE(out.roster.pruned_count);
  XAR_UNAVAILABLE(out.roster.amendment_count);
  XAR_UNAVAILABLE(out.roster.audit_version);
  XAR_UNAVAILABLE(out.roster.reopen_required);
  XAR_UNAVAILABLE(out.processing.count);
  XAR_UNAVAILABLE(out.processing.agenda_count);
  XAR_UNAVAILABLE(out.processing.local_candidate_count);
  XAR_UNAVAILABLE(out.processing.pre_calibration_valid_count);
  XAR_UNAVAILABLE(out.quota.rebuild_generation);
  XAR_UNAVAILABLE(out.quota.built_case_serial);
  XAR_UNAVAILABLE(out.quota.book_version);
  XAR_UNAVAILABLE(out.quota.target_top);
  XAR_UNAVAILABLE(out.quota.target_middle);
  XAR_UNAVAILABLE(out.quota.target_bottom);
  XAR_UNAVAILABLE(out.quota.recount_top);
  XAR_UNAVAILABLE(out.quota.recount_middle);
  XAR_UNAVAILABLE(out.quota.recount_bottom);
  XAR_UNAVAILABLE(out.quota.pre_calibration_expected_count);
  XAR_UNAVAILABLE(out.quota.pre_calibration_mismatch);
  XAR_UNAVAILABLE(out.quota.pool_membership);
  XAR_UNAVAILABLE(out.closure.calibration_finalized);
  XAR_UNAVAILABLE(out.closure.state);
  XAR_UNAVAILABLE(out.closure.rewards_issued);
  XAR_UNAVAILABLE(out.closure.publication_blocked);
  XAR_UNAVAILABLE(out.pending.open_count);
  XAR_UNAVAILABLE(out.pending.slot_used);
  XAR_UNAVAILABLE(out.pending.reward_expected_count);
  XAR_UNAVAILABLE(out.pending.rewards_paid_count);
  XAR_UNAVAILABLE(out.pending.rewards_committed);
  XAR_UNAVAILABLE(out.pending.watchdog_cancelled_count);
  XAR_UNAVAILABLE(out.pending.watchdog_orphan_count);
#undef XAR_UNAVAILABLE
}

void Envelope(const ZhongguoB1CycleSnapshotRequestV1 &request,
              const game::ZhongguoCaseFrameV1 *frame,
              game::ZhongguoB1CycleSnapshotV1 &out) {
  out = {};
  out.case_kind = kZhongguoB1CycleSnapshotV1CaseKind;
  out.request_nonce = request.request_nonce;
  out.snapshot_revision = request.expected_snapshot_revision;
  if (frame != nullptr) {
    out.date_raw = frame->date_raw;
    out.paused = frame->paused;
    out.player_character_id = frame->played_character_id;
    out.manager_character_id = frame->played_character_id;
  }
  AllUnavailable(out, "cycle_unavailable");
}

void TopUnavailable(game::ZhongguoB1CycleSnapshotV1 &out,
                    std::string_view reason) {
  out.status = game::ZhongguoB1CycleSnapshotStatusV1::unavailable;
  AllUnavailable(out, "cycle_unavailable");
  out.readiness = {};
  out.unavailable_reason.assign(reason);
}

void Decode(const Rows &rows, game::ZhongguoB1CycleSnapshotV1 &out) {
  std::size_t i = 0;
#define XAR_INT(field) Integer(rows[i++], (field))
#define XAR_BOOL(field) Boolean(rows[i++], (field))
  XAR_INT(out.cycle.cycle_serial);
  XAR_INT(out.cycle.case_serial);
  XAR_INT(out.cycle.state);
  XAR_INT(out.cycle.open_year);
  XAR_INT(out.cycle.runtime_schema);
  XAR_INT(out.roster.subject_count);
  XAR_INT(out.roster.before_prune_count);
  XAR_INT(out.roster.pruned_count);
  XAR_INT(out.roster.amendment_count);
  XAR_INT(out.roster.audit_version);
  XAR_BOOL(out.roster.reopen_required);
  XAR_INT(out.processing.count);
  XAR_INT(out.processing.agenda_count);
  XAR_INT(out.processing.local_candidate_count);
  XAR_INT(out.processing.pre_calibration_valid_count);
  XAR_INT(out.quota.rebuild_generation);
  XAR_INT(out.quota.built_case_serial);
  XAR_INT(out.quota.book_version);
  XAR_INT(out.quota.target_top);
  XAR_INT(out.quota.target_middle);
  XAR_INT(out.quota.target_bottom);
  XAR_INT(out.quota.recount_top);
  XAR_INT(out.quota.recount_middle);
  XAR_INT(out.quota.recount_bottom);
  XAR_INT(out.quota.pre_calibration_expected_count);
  XAR_BOOL(out.quota.pre_calibration_mismatch);
  XAR_BOOL(out.quota.pool_membership);
  XAR_BOOL(out.closure.calibration_finalized);
  XAR_INT(out.closure.state);
  XAR_BOOL(out.closure.rewards_issued);
  XAR_BOOL(out.closure.publication_blocked);
  XAR_INT(out.pending.open_count);
  XAR_INT(out.pending.slot_used);
  XAR_INT(out.pending.reward_expected_count);
  XAR_INT(out.pending.rewards_paid_count);
  XAR_BOOL(out.pending.rewards_committed);
  XAR_INT(out.pending.watchdog_cancelled_count);
  XAR_INT(out.pending.watchdog_orphan_count);
#undef XAR_INT
#undef XAR_BOOL
  if (IsAvailable(out.cycle.state) && *out.cycle.state.value >= 1 &&
      *out.cycle.state.value <= 8) {
    Available(out.cycle.active, *out.cycle.state.value < 8);
  } else {
    Unavailable(out.cycle.active, "value_out_of_range");
  }
}

} // namespace

ZhongguoB1CycleNativeEnvironmentV1 BindZhongguoB1CycleNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept {
  return BindZhongguoCaseNativeEnvironmentV1(module_base,
                                              exact_build_admitted);
}

game::ReadZhongguoB1CycleSnapshotResultV1 ReadZhongguoB1CycleSnapshotV1(
    const ZhongguoB1CycleNativeEnvironmentV1 &environment,
    const ZhongguoB1CycleAccessV1 &access,
    const ZhongguoB1CycleSnapshotRequestV1 &request,
    game::ZhongguoB1CycleSnapshotV1 &out) noexcept {
  try {
    Envelope(request, nullptr, out);
    if (request.expected_snapshot_revision == 0 ||
        !ValidNonce(request.request_nonce) ||
        !IsZhongguoVariableAbiExactV1(environment)) {
      TopUnavailable(out, "unsupported_build");
      return game::ReadZhongguoB1CycleSnapshotResultV1::unavailable;
    }
    if (access.capture_frame == nullptr || access.is_main_thread == nullptr ||
        !access.is_main_thread(access.context)) {
      TopUnavailable(out, "requires_application_main");
      return game::ReadZhongguoB1CycleSnapshotResultV1::unavailable;
    }
    game::ZhongguoCaseFrameV1 before{};
    if (!access.capture_frame(access.context, before)) {
      TopUnavailable(out, "state_changed");
      return game::ReadZhongguoB1CycleSnapshotResultV1::unavailable;
    }
    Envelope(request, &before, out);
    if (before.snapshot_revision != request.expected_snapshot_revision) {
      TopUnavailable(out, "state_changed");
      return game::ReadZhongguoB1CycleSnapshotResultV1::unavailable;
    }
    if (!before.paused) {
      TopUnavailable(out, "requires_paused");
      return game::ReadZhongguoB1CycleSnapshotResultV1::unavailable;
    }
    if (!before.map_ready || !before.has_played_character ||
        !before.played_character_alive || before.played_character_id <= 0) {
      TopUnavailable(out, "map_not_ready");
      return game::ReadZhongguoB1CycleSnapshotResultV1::unavailable;
    }
    out.readiness.manager_binding_ready = true;
    Rows first{};
    Rows second{};
    if (ReadZhongguoFixedVariableSetV1(
            environment, access, before.played_character_id,
            kZhongguoB1CycleSnapshotV1VariableAllowlist, first) !=
        ReadZhongguoFixedVariableSetResultV1::available) {
      TopUnavailable(out, "variable_identifier_unavailable");
      return game::ReadZhongguoB1CycleSnapshotResultV1::unavailable;
    }
    if (ReadZhongguoFixedVariableSetV1(
            environment, access, before.played_character_id,
            kZhongguoB1CycleSnapshotV1VariableAllowlist, second) !=
        ReadZhongguoFixedVariableSetResultV1::available) {
      TopUnavailable(out, "variable_context_unavailable");
      return game::ReadZhongguoB1CycleSnapshotResultV1::unavailable;
    }
    game::ZhongguoCaseFrameV1 after{};
    if (!access.capture_frame(access.context, after) || before != after ||
        first != second) {
      TopUnavailable(out, "state_changed");
      return game::ReadZhongguoB1CycleSnapshotResultV1::unavailable;
    }
    out.readiness.same_frame_ready = true;
    if (!first[0].present && !first[1].present && !first[2].present) {
      TopUnavailable(out, "cycle_not_found");
      out.readiness.manager_binding_ready = true;
      out.readiness.same_frame_ready = true;
      return game::ReadZhongguoB1CycleSnapshotResultV1::unavailable;
    }
    Decode(first, out);
    out.readiness.cycle_identity_ready =
        IsAvailable(out.cycle.cycle_serial) &&
        IsAvailable(out.cycle.case_serial) && IsAvailable(out.cycle.state) &&
        *out.cycle.cycle_serial.value > 0 && *out.cycle.case_serial.value > 0 &&
        *out.cycle.state.value >= 1 && *out.cycle.state.value <= 8;
    if (!out.readiness.cycle_identity_ready) {
      TopUnavailable(out, "cycle_inconsistent");
      out.readiness.manager_binding_ready = true;
      out.readiness.same_frame_ready = true;
      return game::ReadZhongguoB1CycleSnapshotResultV1::unavailable;
    }
    out.readiness.roster_ready =
        Nonnegative(out.roster.subject_count) &&
        Nonnegative(out.roster.before_prune_count) &&
        Nonnegative(out.roster.pruned_count) &&
        Nonnegative(out.roster.amendment_count) &&
        Nonnegative(out.roster.audit_version) &&
        IsAvailable(out.roster.reopen_required);
    out.readiness.processing_ready =
        Nonnegative(out.processing.count) &&
        Nonnegative(out.processing.agenda_count) &&
        Nonnegative(out.processing.local_candidate_count) &&
        Nonnegative(out.processing.pre_calibration_valid_count);
    out.readiness.quota_ready =
        Nonnegative(out.quota.rebuild_generation) &&
        Nonnegative(out.quota.built_case_serial) &&
        Nonnegative(out.quota.book_version) &&
        Nonnegative(out.quota.target_top) &&
        Nonnegative(out.quota.target_middle) &&
        Nonnegative(out.quota.target_bottom) &&
        Nonnegative(out.quota.recount_top) &&
        Nonnegative(out.quota.recount_middle) &&
        Nonnegative(out.quota.recount_bottom) &&
        Nonnegative(out.quota.pre_calibration_expected_count) &&
        IsAvailable(out.quota.pre_calibration_mismatch) &&
        IsAvailable(out.quota.pool_membership);
    out.readiness.closure_ready =
        IsAvailable(out.closure.calibration_finalized) &&
        Nonnegative(out.closure.state) &&
        IsAvailable(out.closure.rewards_issued) &&
        IsAvailable(out.closure.publication_blocked);
    out.readiness.pending_ready =
        Nonnegative(out.pending.open_count) &&
        Nonnegative(out.pending.slot_used) &&
        Nonnegative(out.pending.reward_expected_count) &&
        Nonnegative(out.pending.rewards_paid_count) &&
        IsAvailable(out.pending.rewards_committed) &&
        Nonnegative(out.pending.watchdog_cancelled_count) &&
        Nonnegative(out.pending.watchdog_orphan_count);
    out.readiness.ready = out.readiness.manager_binding_ready &&
                            out.readiness.cycle_identity_ready &&
                            out.readiness.same_frame_ready;
    out.status = game::ZhongguoB1CycleSnapshotStatusV1::available;
    out.unavailable_reason.clear();
    return game::ReadZhongguoB1CycleSnapshotResultV1::available;
  } catch (...) {
    TopUnavailable(out, "internal_error");
    return game::ReadZhongguoB1CycleSnapshotResultV1::unavailable;
  }
}

} // namespace xar::ck3_11906
