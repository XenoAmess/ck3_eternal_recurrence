#pragma once
#include "xar_bridge/rite_creation_actions12004.hpp"
#include <utility>

namespace xar::ck3_12004::religion::rite_creation_actions::detail {
// Presence is independent of complete command-preview/model availability.
// Only a verified absent/hidden draft may enter the original Open callback.
template<class ReadPresence,class ReadExisting,class OpenAbsent>
bool GuardOpenDraft(const Request&r,Result&out,ReadPresence&&presence,
                    ReadExisting&&read_existing,OpenAbsent&&open_absent) {
 auto fail=[&](const char*why){out.available=false;out.status="unavailable";out.unavailable_reason=why;return false;};
 bool visible=false;
 if(!presence(visible))return fail("rite_creation_current_draft_presence_unverified_do_not_reinitialize");
 if(!visible)return open_absent();
 Result existing{};
 if(!read_existing(existing)||!existing.available)return fail("rite_creation_existing_visible_draft_unreadable_do_not_reinitialize");
 const bool edit_requested=r.operation==Operation::open_edit_current_rite_draft;
 if(!existing.draft.actual_outcome_kind||
    ((*existing.draft.actual_outcome_kind==Outcome::edit_rite)!=edit_requested)||
    (r.expected_outcome_kind&&r.expected_outcome_kind!=existing.draft.actual_outcome_kind))
  return fail("rite_creation_existing_native_draft_mode_differs_do_not_reinitialize");
 out=std::move(existing);out.available=true;out.unavailable_reason.clear();out.already_in_requested_state=true;
 out.draft_open_postcondition_observed=true;out.status="already_in_requested_state";return true;
}
inline void MarkCaptureException(Result&out) {
 out.available=false;out.status="unavailable";out.unavailable_reason="rite_creation_capture_exception";
}
inline void MarkActionException(const Request&r,Result&out) {
 out.available=false;out.verification_pending=out.native_dispatch_attempted;
 out.status=out.native_dispatch_attempted?"dispatch_result_unknown":"unavailable";
 out.original_writer_may_have_been_queued=r.operation==Operation::confirm_once&&out.native_dispatch_attempted;
 out.unavailable_reason="rite_creation_action_exception_do_not_retry_if_attempted";
}
} // namespace xar::ck3_12004::religion::rite_creation_actions::detail
