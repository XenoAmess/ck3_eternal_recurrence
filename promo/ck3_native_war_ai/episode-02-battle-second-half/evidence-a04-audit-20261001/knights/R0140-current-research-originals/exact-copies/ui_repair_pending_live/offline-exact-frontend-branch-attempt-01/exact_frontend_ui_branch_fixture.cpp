#if defined(NDEBUG)
#undef NDEBUG
#endif
#include "xar_bridge/frontend_gui_route_v1.hpp"
#include <windows.h>
#include <cassert>
#include <iostream>
namespace xar::ck3_11906 {
static game::Snapshot fixture_before{},fixture_after{};
static bool snapshot_ok=true,gui_before_ok=true,gui_after_ok=true;
static unsigned snapshot_reads=0,gui_reads=0,invokes=0;
static IngameUiGuiOwnerBindingV1 fixture_gui_before{},fixture_gui_after{};
bool ReadSnapshot(const Bindings &,game::Snapshot &out) noexcept {
  out=snapshot_reads++==0?fixture_before:fixture_after;return snapshot_ok;
}
bool ReadIngameUiGuiOwnerBindingV1(const ZhongguoScoreboardNativeEnvironmentV1 &,IngameUiGuiOwnerBindingV1 &out) noexcept {
  const bool first=gui_reads++==0;out=first?fixture_gui_before:fixture_gui_after;
  return first?gui_before_ok:gui_after_ok;
}
bool ExecuteIngameUiNavigationV1(const ZhongguoScoreboardNativeEnvironmentV1 &,const IngameUiRequestV1 &,
 const game::Snapshot &snap,const MainThreadExecutionStampV1 &stamp,const IngameUiGuiOwnerBindingV1 &,IngameUiResultV1 &out) noexcept {
  ++invokes;out={};out.available=true;out.dispatch_invoked=true;out.verification_pending=true;
  out.status="acknowledged_verification_pending";out.date_raw=snap.date_raw;out.paused=snap.paused;
  out.played_character_id=snap.played_character_id;out.thread_id=stamp.thread_id;out.pump_epoch=stamp.pump_epoch;return true;
}
namespace {
bool IsExecutingFrontendSlot(
    const FrontendGuiRouteMailboxContextV1 &query,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  if (query.mailbox == nullptr || query.ticket.sequence == 0 ||
      stamp.pump_epoch == 0 || stamp.thread_id == 0 ||
      stamp.tls_initialized_flag_address == 0 || stamp.tls_initialized != 1 ||
      stamp.tls_context == 0 || stamp.tls_main_thread_marker != 1 ||
      GetCurrentThreadId() != stamp.thread_id) {
    return false;
  }
  const auto &mailbox = *query.mailbox;
  return mailbox.state.load(std::memory_order_acquire) ==
             MainThreadQueryMailboxStateV1::executing &&
         !mailbox.stop_requested.load(std::memory_order_acquire) &&
         mailbox.failure_flags.load(std::memory_order_acquire) == 0 &&
         mailbox.published_sequence.load(std::memory_order_acquire) ==
             query.ticket.sequence &&
         mailbox.owner_thread_id.load(std::memory_order_acquire) ==
             stamp.thread_id &&
         mailbox.owner_verified_pump_epochs.load(std::memory_order_acquire) >=
             kMainThreadQueryMinimumOwnerVerifiedPumpEpochs &&
         mailbox.executor == &ExecuteFrontendGuiRouteMailboxV1 &&
         mailbox.executor_context ==
             const_cast<FrontendGuiRouteMailboxContextV1 *>(&query);
}

} // anonymous
bool ExecuteFrontendGuiRouteMailboxV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *query = static_cast<FrontendGuiRouteMailboxContextV1 *>(
      opaque_context);
  if (query == nullptr || !IsExecutingFrontendSlot(*query, stamp)) {
    return false;
  }
  query->result = {};
  if (query->operation == FrontendGuiRouteOperationV1::ingame_ui) {
    // Failure metadata is observed at this original application event boundary,
    // never copied from the caller's expected snapshot.
    query->ingame_result = {};
    query->ingame_result.date_raw = stamp.date_raw;
    query->ingame_result.paused = stamp.paused;
    query->ingame_result.pump_epoch = stamp.pump_epoch;
    query->ingame_result.thread_id = stamp.thread_id;
    query->ingame_result.rng_owner_thread_id = stamp.rng_owner_thread_id;
    game::Snapshot before{};
    if (!IsIngameUiPausedOwnerStampV1(*query->mailbox, stamp, GetCurrentThreadId())) {
      query->ingame_result.unavailable_reason = "application_paused_owner_stamp_unverified";
      return true;
    }
    query->ingame_result.application_owner_thread_verified = true;
    if (!ReadSnapshot(query->ingame_bindings, before)) {
      query->ingame_result.unavailable_reason = "owner_fresh_snapshot_read_failed";
      return true;
    }
    query->ingame_result.played_character_id = before.played_character_id;
    if (before != query->ingame_expected_snapshot || !before.paused ||
        !before.map_ready || !before.has_played_character || before.date_raw != stamp.date_raw) {
      query->ingame_result.unavailable_reason = "owner_fresh_snapshot_admission_failed";
      return true;
    }
    IngameUiGuiOwnerBindingV1 gui_before{};
    if (!ReadIngameUiGuiOwnerBindingV1(query->environment, gui_before)) {
      query->ingame_result.unavailable_reason = "current_gui_owner_binding_unverified";
      return true;
    }
    const bool ran = ExecuteIngameUiNavigationV1(query->environment,
        query->ingame_request, before, stamp, gui_before, query->ingame_result);
    query->ingame_result.application_owner_thread_verified = true;
    query->ingame_result.rng_owner_thread_id = stamp.rng_owner_thread_id;
    query->ingame_result.gui_context_address = reinterpret_cast<std::uintptr_t>(gui_before.context);
    query->ingame_result.gui_owner_address = reinterpret_cast<std::uintptr_t>(gui_before.owner);
    IngameUiGuiOwnerBindingV1 gui_after{};
    const bool same_gui = ReadIngameUiGuiOwnerBindingV1(query->environment, gui_after) && gui_after == gui_before;
    query->ingame_result.gui_owner_binding_verified = same_gui;
    game::Snapshot after{};
    if (!ran || !ReadSnapshot(query->ingame_bindings, after) || after != before) {
      query->ingame_result.available = false;
      query->ingame_result.status = "unavailable";
      query->ingame_result.unavailable_reason = "owner_post_navigation_snapshot_changed";
    } else if (!same_gui) {
      query->ingame_result.available = false;
      query->ingame_result.status = "unavailable";
      query->ingame_result.unavailable_reason = "current_gui_owner_binding_changed_after_navigation";
    }
    return true;
  }
  return false;
}

} // namespace xar
int main() {
 using namespace xar::ck3_11906;
 MainThreadQueryMailboxV1 mb{};FrontendGuiRouteMailboxContextV1 q{};MainThreadExecutionStampV1 st{};
 const auto reset=[&] {
  q={};q.mailbox=&mb;q.ticket.sequence=2;q.operation=FrontendGuiRouteOperationV1::ingame_ui;
  mb.state.store(MainThreadQueryMailboxStateV1::executing);mb.stop_requested.store(false);mb.failure_flags.store(0);
  mb.published_sequence.store(2);mb.owner_thread_id.store(GetCurrentThreadId());
  mb.owner_verified_pump_epochs.store(7396);mb.paused_owner_verified_pump_epochs.store(7396);
  mb.executor=&ExecuteFrontendGuiRouteMailboxV1;mb.executor_context=&q;
  st={};st.pump_epoch=23345;st.thread_id=GetCurrentThreadId();st.tls_initialized_flag_address=1;
  st.tls_initialized=1;st.tls_context=2;st.tls_main_thread_marker=1;st.jomini_state=3;st.game_state=4;
  st.date_raw=53146848;st.paused=true;st.rng_owner_thread_id=0;
  fixture_before={};fixture_before.paused=true;fixture_before.map_ready=true;fixture_before.has_played_character=true;
  fixture_before.date_raw=53146848;fixture_before.played_character_id=29829;fixture_after=fixture_before;
  q.ingame_expected_snapshot=fixture_before;snapshot_ok=gui_before_ok=gui_after_ok=true;
  fixture_gui_before={reinterpret_cast<void *>(101),reinterpret_cast<void *>(201)};fixture_gui_after=fixture_gui_before;
  snapshot_reads=gui_reads=invokes=0;
 };
 unsigned cases=0;
 reset();assert(ExecuteFrontendGuiRouteMailboxV1(&q,st) && invokes==1 && q.ingame_result.available);
 assert(q.ingame_result.application_owner_thread_verified && q.ingame_result.gui_owner_binding_verified && q.ingame_result.rng_owner_thread_id==0);++cases;
 reset();st.rng_owner_thread_id=GetCurrentThreadId()+1;assert(ExecuteFrontendGuiRouteMailboxV1(&q,st) && invokes==1);++cases;
 for(unsigned i=0;i<15;++i) {
  reset();switch(i) {
  case 0:q.ticket.sequence=0;break;case 1:mb.published_sequence.store(3);break;
  case 2:mb.executor=nullptr;break;case 3:mb.executor_context=nullptr;break;
  case 4:mb.state.store(MainThreadQueryMailboxStateV1::queued);break;case 5:mb.stop_requested.store(true);break;
  case 6:mb.failure_flags.store(1);break;case 7:st.thread_id=GetCurrentThreadId()+1;break;
  case 8:mb.owner_thread_id.store(GetCurrentThreadId()+1);break;case 9:st.tls_initialized=0;break;
  case 10:st.tls_main_thread_marker=0;break;case 11:st.tls_context=0;break;
  case 12:st.tls_initialized_flag_address=0;break;case 13:st.pump_epoch=0;break;
  case 14:mb.owner_verified_pump_epochs.store(1);break;
  }
  assert(!ExecuteFrontendGuiRouteMailboxV1(&q,st) && invokes==0);++cases;
 }
 for(unsigned i=0;i<4;++i) {
  reset();switch(i) {case 0:st.paused=false;break;case 1:st.jomini_state=0;break;
  case 2:st.game_state=0;break;case 3:mb.paused_owner_verified_pump_epochs.store(1);break;}
  assert(ExecuteFrontendGuiRouteMailboxV1(&q,st) && invokes==0 && !q.ingame_result.available);
  assert(q.ingame_result.unavailable_reason=="application_paused_owner_stamp_unverified");++cases;
 }
 reset();q.ingame_expected_snapshot.date_raw=53146872;
 assert(ExecuteFrontendGuiRouteMailboxV1(&q,st) && invokes==0 && q.ingame_result.date_raw==53146848);
 assert(q.ingame_result.unavailable_reason=="owner_fresh_snapshot_admission_failed");++cases;
 reset();fixture_before.date_raw=53146872;q.ingame_expected_snapshot=fixture_before;
 assert(ExecuteFrontendGuiRouteMailboxV1(&q,st) && invokes==0 && q.ingame_result.date_raw==53146848);++cases;
 reset();snapshot_ok=false;assert(ExecuteFrontendGuiRouteMailboxV1(&q,st) && invokes==0);
 assert(q.ingame_result.played_character_id==-1 && q.ingame_result.unavailable_reason=="owner_fresh_snapshot_read_failed");++cases;
 reset();gui_before_ok=false;assert(ExecuteFrontendGuiRouteMailboxV1(&q,st) && invokes==0);
 assert(q.ingame_result.unavailable_reason=="current_gui_owner_binding_unverified");++cases;
 for(unsigned i=0;i<3;++i) {
  reset();switch(i) {case 0:fixture_gui_after.context=reinterpret_cast<void *>(102);break;
  case 1:fixture_gui_after.owner=reinterpret_cast<void *>(202);break;case 2:gui_after_ok=false;break;}
  assert(ExecuteFrontendGuiRouteMailboxV1(&q,st) && invokes==1 && !q.ingame_result.available && !q.ingame_result.gui_owner_binding_verified);
  assert(q.ingame_result.unavailable_reason=="current_gui_owner_binding_changed_after_navigation");++cases;
 }
 reset();fixture_after.date_raw=53146872;assert(ExecuteFrontendGuiRouteMailboxV1(&q,st) && invokes==1 && !q.ingame_result.available);
 assert(q.ingame_result.unavailable_reason=="owner_post_navigation_snapshot_changed");++cases;
 reset();fixture_after.played_character_id=33437;assert(ExecuteFrontendGuiRouteMailboxV1(&q,st) && invokes==1 && !q.ingame_result.available);++cases;
 std::cout<<cases<<" cases PASS: verbatim production ticket/UI branch with offline snapshot/GUI/navigation stubs, no game calls\n";
}
