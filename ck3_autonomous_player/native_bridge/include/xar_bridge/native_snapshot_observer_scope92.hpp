#pragma once
// Private production scope. It is neither mailbox ABI nor a wire proof.
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/game_adapter.hpp"
#include <cstdint>
#include <limits>
#include <windows.h>

namespace xar::ck3_12002 { class WorkerAdapter; }
namespace xar::snapshot_observer92 {
using Mailbox = ck3_11906::MainThreadQueryMailboxV1;
using Stamp = ck3_11906::MainThreadExecutionStampV1;
using Callback = ck3_11906::MainThreadQueryExecutorV1;

struct View {
  const Mailbox *mailbox = nullptr;
  const game::GameAdapter *native = nullptr;
  const void *worker = nullptr;
  Callback callback = nullptr;
  void *context = nullptr;
  std::uintptr_t module = 0;
  Stamp stamp{};
  std::uint64_t generation = 0;
};

class ReadScope final {
  friend class xar::ck3_12002::WorkerAdapter;
  friend bool xar::ck3_11906::ObserveMainThreadPumpAndDrainV1(
      Mailbox &, std::uintptr_t, std::uint32_t) noexcept;
  using Abort = void (*)(void *) noexcept;
  struct State {
    View view{};
    Abort abort = nullptr;
    void *abort_context = nullptr;
    bool active = false;
    bool poisoned = false;
  };
  static thread_local State state_;
  static thread_local std::uint64_t next_;
  std::uint64_t generation_ = 0;

  static bool SameStamp(const Stamp &a,const Stamp &b) noexcept {
    return a.pump_epoch==b.pump_epoch && a.thread_id==b.thread_id &&
      a.tls_initialized==b.tls_initialized && a.tls_main_thread_marker==b.tls_main_thread_marker &&
      a.tls_context==b.tls_context && a.game_state==b.game_state &&
      a.jomini_state==b.jomini_state && a.date_raw==b.date_raw && a.paused==b.paused;
  }
  static bool Common(const View &v) noexcept {
    if(!v.mailbox || !v.callback || !v.context || !v.module || !v.generation)return false;
    const auto &m=*v.mailbox;const auto &s=v.stamp;
    return !m.offline_fixture && s.pump_epoch && s.thread_id &&
      GetCurrentThreadId()==s.thread_id && s.tls_initialized==1 && s.tls_main_thread_marker==1 &&
      s.tls_context && s.game_state && s.jomini_state && m.module_base==v.module &&
      m.snapshot_observer_callback==v.callback && m.snapshot_observer_context==v.context &&
      !m.stop_requested.load() && !m.proof_reset_requested.load() && m.failure_flags.load()==0 &&
      (m.iat_hook_installed.load() || m.sdl_poll_event_hook_installed.load()) && m.active_hook_calls.load()!=0 &&
      m.drain_guard.test(std::memory_order_acquire) &&
      m.owner_thread_id.load()==s.thread_id && m.observed_current_thread_id.load()==s.thread_id &&
      m.pump_epochs.load()==s.pump_epoch && m.observed_stamp_read_success.load() &&
      m.observed_tls_initialized.load()==1 && m.observed_tls_main_thread_marker.load()==1 &&
      m.observed_tls_context.load()==s.tls_context && m.observed_game_state.load()==s.game_state &&
      m.observed_jomini_state.load()==s.jomini_state && m.observed_date_raw.load()==s.date_raw &&
      m.observed_paused.load()==s.paused &&
      m.state.load()!=ck3_11906::MainThreadQueryMailboxStateV1::executing;
  }
  static bool Begin(Mailbox &m,const Stamp &s) noexcept {
#if defined(XAR_CK3_ENABLE_26757580_OBSERVER_SCOPE92) && XAR_CK3_ENABLE_26757580_OBSERVER_SCOPE92
    if(state_.active) {state_.poisoned=true;return false;}
    if(next_==std::numeric_limits<std::uint64_t>::max())return false;
    View v{};v.mailbox=&m;v.callback=m.snapshot_observer_callback;v.context=m.snapshot_observer_context;
    v.module=m.module_base;v.stamp=s;v.generation=++next_;
    if(!Common(v))return false;
    state_={};state_.view=v;state_.active=true;return true;
#else
    (void)m;(void)s;return false;
#endif
  }
  static void End() noexcept {
    // Also clears an abandoned Worker binding when SEH bypassed its C++ destructor.
    const auto cleanup=state_.abort;auto *context=state_.abort_context;
    state_={};
    if(cleanup)cleanup(context);
  }
  ReadScope(const game::GameAdapter *native,const void *worker,const Mailbox *m,
      const Stamp &s,Abort abort,void *abort_context) noexcept {
#if defined(XAR_CK3_ENABLE_26757580_OBSERVER_SCOPE92) && XAR_CK3_ENABLE_26757580_OBSERVER_SCOPE92
    if(!native)return;
    if(state_.view.native || state_.view.worker) {state_.poisoned=true;return;}
    if(!state_.active || state_.poisoned || state_.view.mailbox!=m ||
        state_.view.context!=worker || !SameStamp(state_.view.stamp,s) || !Common(state_.view))return;
    state_.view.native=native;state_.view.worker=worker;
    state_.abort=abort;state_.abort_context=abort_context;generation_=state_.view.generation;
#else
    (void)native;(void)worker;(void)m;(void)s;(void)abort;(void)abort_context;
#endif
  }
public:
  ReadScope(const ReadScope &)=delete;
  ReadScope &operator=(const ReadScope &)=delete;
  ~ReadScope() noexcept {
    if(generation_ && state_.active && state_.view.generation==generation_) {
      state_.view.native=nullptr;state_.view.worker=nullptr;
      state_.abort=nullptr;state_.abort_context=nullptr;
    }
  }
  bool valid() const noexcept {
    return generation_ && state_.active && !state_.poisoned &&
      state_.view.generation==generation_ && state_.view.native && state_.view.worker && Common(state_.view);
  }
  static View Capture(const game::GameAdapter &native,const Mailbox &m) noexcept {
    const auto &s=state_;
    if(s.active && !s.poisoned && s.view.native==&native && s.view.mailbox==&m &&
        s.view.worker && Common(s.view))return s.view;
    return {};
  }
  static bool Validate(const View &v,const game::GameAdapter &native,const Mailbox &m) noexcept {
    const auto &s=state_;
    return v.generation && s.active && !s.poisoned && s.view.generation==v.generation &&
      v.mailbox==&m && v.native==&native && s.view.native==&native && s.view.mailbox==&m &&
      v.worker==s.view.worker && v.context==s.view.context && v.callback==s.view.callback &&
      v.module==s.view.module && SameStamp(v.stamp,s.view.stamp) && Common(s.view);
  }
  // Read-only inspection of both logical TLS layers; never an admission input.
  static bool Empty() noexcept {
    return !state_.active && !state_.view.native && !state_.view.worker && !state_.abort;
  }
};
inline thread_local ReadScope::State ReadScope::state_{};
inline thread_local std::uint64_t ReadScope::next_=0;
} // namespace xar::snapshot_observer92
