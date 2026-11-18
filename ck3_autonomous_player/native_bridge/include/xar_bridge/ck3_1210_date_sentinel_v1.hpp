#pragma once
#include "xar_bridge/ck3_1210.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/tactical_daily_sentinel_v1.hpp"
#include <atomic>
namespace xar::ck3_1210 {
using DateSentinelNowV1=std::uint64_t (*)(void *) noexcept;
// Native manager is an embedded object, not a pointer slot. This record is
// copied only after complete reads; fields describe one native worker epoch.
struct DateSentinelWorkerNativeV1 {
  std::uintptr_t manager=0,function=0,context=0,holder=0,native_handle=0;
  std::uint32_t thread_id=0;
  std::uint8_t started=0,stop=1;
  friend bool operator==(const DateSentinelWorkerNativeV1 &,
      const DateSentinelWorkerNativeV1 &)=default;
};
struct DateSentinelWorkerEpochV1 {
  DateSentinelWorkerNativeV1 native{};
  std::uintptr_t owned_handle=0; // Our duplicate only; NEVER the native handle.
  std::uint64_t creation_time=0;
};
using DateSentinelGameBodyV1=bool (*)(void *) noexcept;
// Must synchronously enter the versioned native RAII scope, invoke body once,
// and release on every path. Default production binding is deliberately empty
// until that exact RAII implementation is supplied; identity alone grants no write.
using DateSentinelGameAccessV1=bool (*)(void *,DateSentinelGameBodyV1,void *) noexcept;
// Explicit NoGame model only. Production rejects every nonempty seam, and an
// offline model has module_base=0; model handles are never passed to Win32.
struct DateSentinelWorkerFixtureV1 {
  void *context=nullptr;
  bool (*snapshot)(void *,DateSentinelWorkerNativeV1 &) noexcept=nullptr;
  bool (*duplicate)(void *,std::uintptr_t,std::uintptr_t &) noexcept=nullptr;
  bool (*probe)(void *,std::uintptr_t,std::uint32_t &,std::uint64_t &,bool &,bool &) noexcept=nullptr;
  bool (*scope)(void *,std::uint32_t &,std::uint8_t &,std::uint32_t &,std::uint8_t &) noexcept=nullptr;
  bool (*close)(void *,std::uintptr_t) noexcept=nullptr;
  DateSentinelGameAccessV1 with_game_access=nullptr;
};
struct DateSentinelBindingsV1 {
  bool exact_build_admitted=false;
  bool offline_fixture=false; // Explicit NoGame only; never runtime qualification.
  std::uintptr_t module_base=0;
  CoreBindings core{};
  ck3_11906::TacticalSetPausedV1 set_paused=nullptr;
  void *clock_context=nullptr;
  DateSentinelNowV1 utc_now=nullptr;
  DateSentinelNowV1 monotonic_now=nullptr;
  std::uintptr_t command_manager=0,worker_function=0;
  DateSentinelWorkerFixtureV1 worker_fixture{};
  void *game_access_context=nullptr;
  DateSentinelGameAccessV1 worker_game_access=nullptr;
};
enum DateSentinelFailureV1 : std::uint32_t {
  date_sentinel_failure_none=0,
  date_sentinel_failure_owner=1U<<0,
  date_sentinel_failure_tls=1U<<1,
  date_sentinel_failure_world=1U<<2,
  date_sentinel_failure_actor=1U<<3,
  date_sentinel_failure_speed=1U<<4,
  date_sentinel_failure_expired=1U<<5,
  date_sentinel_failure_observation=1U<<6,
  date_sentinel_failure_sequence=1U<<7,
  date_sentinel_failure_runtime=1U<<8,
  date_sentinel_failure_unexpected_pause=1U<<9,
  date_sentinel_failure_shutdown=1U<<10,
};
struct DateSentinelObservationV1 {
  CoreSnapshotPrefix core{};
  void *game=nullptr,*jomini=nullptr,*storage=nullptr,*data=nullptr;
  void *players=nullptr,*player=nullptr,*actor=nullptr;
};
// Initialize once while cold. UI owner captures immutable worker/arm payload;
// only that UI owner or the separately proven native worker may close the arm.
// A foreign post may only publish atomic diagnostics/failure.
// Keep this fixed state alive through hook uninstall and complete rundown.
struct DateSentinelStateV1 {
  std::atomic<bool> initialized{false},armed{false};
  std::atomic<bool> shutdown_requested{false},shutdown_safe{true};
  std::atomic<std::uint32_t> pending_failure{0},owner_thread_id{0};
  DateSentinelBindingsV1 bindings{};
  ck3_11906::MainThreadQueryMailboxV1 *mailbox=nullptr;
  DateSentinelObservationV1 initial{};
  std::atomic<std::uint64_t> generation{0};
  std::uint64_t original_deadline_unix_ms=0,monotonic_deadline_ms=0;
  std::uintptr_t owner_tls_context=0;
  std::uint64_t armed_unix_ms=0,armed_monotonic_ms=0;
  bool fixture_only=false;
  // Atomic diagnostics only; not an observation, role or coherent snapshot.
  std::atomic<std::uint32_t> last_post_thread_id{0},last_post_stage{0};
  std::atomic<std::int32_t> last_post_date_raw{0};
  mutable SRWLOCK worker_lifetime_lock=SRWLOCK_INIT;
  std::atomic<std::uint32_t> post_callbacks{0};
  std::atomic<std::uint32_t> captured_worker_thread_id{0};
  DateSentinelWorkerEpochV1 worker{};
};
struct DateSentinelDiagnosticsV1 {
  bool initialized=false,armed=false,fixture_only=false;
  bool capability_granted=false;
  bool shutdown_requested=false,shutdown_safe=true;
  std::uint32_t failure_flags=0;
  std::uint32_t captured_worker_thread_id=0,post_callbacks=0;
  std::uint64_t generation=0,original_deadline_unix_ms=0,monotonic_deadline_ms=0;
};
// Address calculation only. Initialize checks actual mapped consumer/pause/
// command-scope code pins; it never reads manager/holder state while cold.
DateSentinelBindingsV1 BindDateSentinelImageV1(std::uintptr_t,
    std::string_view executable_sha256) noexcept;
bool InitializeDateSentinelV1(DateSentinelStateV1 &,const DateSentinelBindingsV1 &,
    ck3_11906::MainThreadQueryMailboxV1 &) noexcept;
ck3_11906::TacticalDailySentinelArmStatusV1 ArmDateSentinelV1(DateSentinelStateV1 &,
    const ck3_11906::TacticalDailySentinelArmRequestV1 &,
    std::uint64_t original_deadline_unix_ms) noexcept;
bool DateSentinelAllowsResumeV1(DateSentinelStateV1 &,
    const CoreSnapshotPrefix &expected) noexcept;
// Only the verified final-stage hook calls this, after actual original returns.
// Validates the separately captured native command worker, not the UI owner.
// Safe/unarmed calls perform zero world/TLS/clock reads; unsafe failure cleanup
// remains eligible on a proven command worker. Never call from a raw pump.
void PostDateSentinelV1(void *) noexcept;
// Owner pump handles only expiry/failure and safe failed+pause publication.
// It never calls ProcessTacticalDailySentinelAfterTickV1 or fabricates a day.
// True means a failed/disarmed publication was committed. This does NOT imply
// safe teardown: only DateSentinelShutdownSafeV1 authorizes owner removal.
// Unsafe failed generations remain eligible for later owner-pump pause retries.
bool PollDateSentinelOwnerV1(DateSentinelStateV1 &,
    const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
ck3_11906::TacticalDailySentinelCancelStatusV1 CancelDateSentinelV1(
    DateSentinelStateV1 &,std::uint64_t generation) noexcept;
ck3_11906::TacticalDailySentinelStatusV1 ReadDateSentinelStatusV1(
    const DateSentinelStateV1 &) noexcept;
// Any thread: two atomic publications only, no TLS/world/clock/native calls.
// Sticky for this state lifetime. An unarmed state remains initially safe.
void RequestDateSentinelShutdownV1(DateSentinelStateV1 &) noexcept;
// Atomic-only acknowledgement. False retains owner/hook/context resources until
// a later proven owner confirms actual paused + same-generation disarmed.
bool DateSentinelShutdownSafeV1(const DateSentinelStateV1 &) noexcept;
// Close only our duplicate, under the lifetime gate, after safe acknowledgement
// and zero callbacks. Never closes/joins/frees the engine's native holder.
// False retains resources; final process teardown may honestly retain them.
bool ReleaseDateSentinelWorkerV1(DateSentinelStateV1 &) noexcept;
// Owner-only diagnostics; no capability or live qualification is granted.
DateSentinelDiagnosticsV1 ReadDateSentinelDiagnosticsV1(
    const DateSentinelStateV1 &) noexcept;
} // namespace xar::ck3_1210
