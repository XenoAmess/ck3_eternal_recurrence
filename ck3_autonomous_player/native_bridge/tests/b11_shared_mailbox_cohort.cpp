#ifdef NDEBUG
#error B11 cohort assertions must remain enabled
#endif
#include "b11_mailbox_owned_support.hpp"
#include "xar_bridge/ck3_12002_nonwar_mailbox.hpp"
#include "xar_bridge/ck3_12002_nonwar_router.hpp"
#include "xar_bridge/character_skill_effect12004_mailbox.hpp"
#include "xar_bridge/character_skill_effect12004_native.hpp"
#include "xar_bridge/player_inventory_window12004_transport.hpp"
#include "current_player_observers12004.hpp"
#include <cstdio>
#include <string_view>

namespace owned=b11_owned;
namespace mt=xar::ck3_11906;
namespace actor=xar::ck3_12004::character_skill_effects;
namespace core=xar::bridge::character_skill_effect12004;
namespace obs=xar::ck3_12004::current_player_observers;
namespace inventory=xar::ck3_12004::player_inventory_window;
namespace {
void SingleSlotInstallGuard() {
  // Production nonempty test remains active (offline_fixture=false). A rejecting
  // profile prevents any fake module-base dereference after that exact guard.
  mt::MainThreadQueryMailboxV1 empty{};
  mt::MainThreadQueryInstallEnvironmentV1 environment{};
  environment.module_base=1;environment.exact_build_admitted=true;
  environment.executor_submission_enabled=true;environment.build_profile=&owned::profile;
  assert(!mt::InstallMainThreadQueryMailboxV1(empty,environment));
  assert(empty.failure_flags.load()==mt::main_thread_query_failure_request_identity);
  for(std::size_t i=0;i<6;++i) {
    mt::MainThreadQueryMailboxV1 mailbox{};auto one=environment;
    one.*owned::slots[i].environment=owned::slots[i].callback;
    assert(!mt::InstallMainThreadQueryMailboxV1(mailbox,one));
    assert(mailbox.failure_flags.load()==mt::main_thread_query_failure_pump_anchor);
  }
}
void OwnedSingleSlotAndCohort() {
  for(std::size_t i=0;i<6;++i) {
    auto& runtime=owned::NewRuntime();auto& mailbox=owned::retained_mailbox;auto env=runtime.Environment();
    env.*owned::slots[i].environment=owned::slots[i].callback;
    assert(mt::InstallMainThreadQueryMailboxV1(mailbox,env));
    for(std::size_t j=0;j<owned::slots.size();++j)
      assert((mailbox.*owned::slots[j].mailbox)==(i==j?owned::slots[i].callback:nullptr));
    runtime.Warm(mailbox);
    owned::Seen rejected{};mt::MainThreadQueryTicketV1 no_ticket{};
    assert(mt::TrySubmitMainThreadQueryV1(mailbox,&owned::Marker<10>,&rejected,no_ticket)==mt::MainThreadQuerySubmitResultV1::invalid_request);
    assert(no_ticket.sequence==0&&rejected.calls==0);
    owned::RunMarker(runtime,mailbox,owned::slots[i],static_cast<unsigned>(i+1));
    runtime.Finish(mailbox);
  }
  auto& runtime=owned::NewRuntime();auto& mailbox=owned::retained_mailbox;auto env=runtime.Environment();
  for(const auto& s:owned::slots)env.*s.environment=s.callback;
  assert(mt::InstallMainThreadQueryMailboxV1(mailbox,env));runtime.Warm(mailbox);
  for(std::size_t i=0;i<owned::slots.size();++i) {
    assert(mailbox.*owned::slots[i].mailbox==owned::slots[i].callback);
    owned::RunMarker(runtime,mailbox,owned::slots[i],static_cast<unsigned>(i+1));
  }
  // Stale identities must not cancel/reclaim another queued request.
  owned::Seen seen{};mt::MainThreadQueryTicketV1 ticket{};
  assert(mt::TrySubmitMainThreadQueryV1(mailbox,owned::slots[0].callback,&seen,ticket)==mt::MainThreadQuerySubmitResultV1::submitted);
  auto stale=ticket;++stale.sequence;
  assert(mt::WaitForMainThreadQueryV1(mailbox,stale,0)==mt::MainThreadQueryWaitResultV1::ticket_mismatch);
  assert(mt::CancelMainThreadQueryV1(mailbox,stale)==mt::MainThreadQueryCancelResultV1::ticket_mismatch);
  assert(mt::ReclaimMainThreadQueryV1(mailbox,stale)==mt::MainThreadQueryReclaimResultV1::ticket_mismatch);
  assert(seen.calls==0);
  assert(mt::CancelMainThreadQueryV1(mailbox,ticket)==mt::MainThreadQueryCancelResultV1::cancelled);
  assert(mt::ReclaimMainThreadQueryV1(mailbox,ticket)==mt::MainThreadQueryReclaimResultV1::reclaimed);
  runtime.Finish(mailbox);
}
void BadTlsDoesNotDispatch() {
  auto& runtime=owned::NewRuntime();auto& mailbox=owned::retained_mailbox;auto env=runtime.Environment();
  env.permitted_executor_character_skill_effect12004=&owned::Marker<1>;
  assert(mt::InstallMainThreadQueryMailboxV1(mailbox,env));runtime.Warm(mailbox);
  owned::Seen seen{};mt::MainThreadQueryTicketV1 ticket{};
  assert(mt::TrySubmitMainThreadQueryV1(mailbox,&owned::Marker<1>,&seen,ticket)==mt::MainThreadQuerySubmitResultV1::submitted);
  runtime.tls[0x20]=std::byte{0};
  assert(!mt::ObserveMainThreadPumpAndDrainV1(mailbox,owned::kOwnedPumpReturn,runtime.thread));
  assert(mt::WaitForMainThreadQueryV1(mailbox,ticket,20)==mt::MainThreadQueryWaitResultV1::infrastructure_failed);
  assert(seen.calls==0&&(mailbox.failure_flags.load()&mt::main_thread_query_failure_tls_identity));
  assert(mt::ReclaimMainThreadQueryV1(mailbox,ticket)==mt::MainThreadQueryReclaimResultV1::reclaimed);
  runtime.Finish(mailbox);
}
xar::ck3_12002::NonwarMailboxExecutorsV1 RealExecutors() {
  xar::ck3_12002::NonwarMailboxExecutorsV1 e{};
  xar::ck3_12002::PopulateNonwarRouterExecutors12004(e);
  assert(e.artifact_personal_read==&obs::ExecuteArtifactPersonalRead12004);
  assert(e.artifact_personal_action==&obs::ExecuteArtifactPersonalAction12004);
  assert(e.ghw_permissions_read==&obs::ExecuteGhwPermissionsRead12004);
  assert(e.character_skill_effects==&actor::Execute);
  assert(e.inventory_window_read==&inventory::ExecuteRead);
  assert(e.inventory_window_open==&inventory::ExecuteOpen);
  assert(e.pilgrimage_identities&&e.pilgrimage_execution);
  return e;
}
struct SnapshotSource {xar::game::Snapshot snapshot{};unsigned calls=0;};
bool ReadOwnedSnapshot(void* p,xar::game::Snapshot& out) noexcept {
  if(!p)return false;auto& s=*static_cast<SnapshotSource*>(p);++s.calls;out=s.snapshot;return true;
}
void RealFactoryAndTypedOwnerGuard(bool wrong_thread) {
  auto& runtime=owned::NewRuntime();auto& mailbox=owned::retained_mailbox;auto env=runtime.Environment();
  const auto executors=RealExecutors();
  xar::ck3_12002::RegisterNonwarMailboxExecutorsV1(env,executors);
  env.permitted_frontend_executor=&owned::Marker<9>;
  assert(env.permitted_executor_character_skill_effect12004==executors.character_skill_effects);
  assert(env.permitted_executor_player_inventory_window_read12004==executors.inventory_window_read);
  assert(env.permitted_executor_player_inventory_window_open12004==executors.inventory_window_open);
  assert(env.permitted_executor_artifact_personal_read12004==executors.artifact_personal_read);
  assert(env.permitted_executor_artifact_personal_action12004==executors.artifact_personal_action);
  assert(env.permitted_executor_ghw_permissions_read12004==executors.ghw_permissions_read);
  assert(env.permitted_executor_player_pilgrimage_identities12004==executors.pilgrimage_identities);
  assert(env.permitted_executor_player_pilgrimage_execution12004==executors.pilgrimage_execution);
  assert(mt::InstallMainThreadQueryMailboxV1(mailbox,env));runtime.Warm(mailbox);
  // Actual provider addresses, no fabricated private query layouts. Null context
  // rejects before any frame/native reader. Their business callbacks are not run.
  mt::MainThreadExecutionStampV1 invalid{};
  assert(!executors.artifact_personal_read(nullptr,invalid));
  assert(!executors.artifact_personal_action(nullptr,invalid));
  assert(!executors.ghw_permissions_read(nullptr,invalid));
  assert(!executors.inventory_window_read(nullptr,invalid));
  assert(!executors.inventory_window_open(nullptr,invalid));
  assert(!executors.character_skill_effects(nullptr,invalid));
  SnapshotSource source{};
  source.snapshot.date_raw=runtime.date;source.snapshot.paused=true;source.snapshot.map_ready=true;
  source.snapshot.has_played_character=true;source.snapshot.played_character_alive=true;
  source.snapshot.played_character_id=123;
  actor::Query q{};q.mailbox=&mailbox;q.enabled=true;q.module_base=0; // Stop before any native/RPM path.
  q.executable_sha256=core::kExeSha;q.native_context=&source;q.read_snapshot=&ReadOwnedSnapshot;
  q.expected_snapshot=source.snapshot;q.expected_revision=11;q.connection_generation=1;
  q.game_pid=GetCurrentProcessId();q.character_id=123;q.skill=0;
  assert(mt::TrySubmitMainThreadQueryV1(mailbox,&actor::Execute,&q,q.ticket)==mt::MainThreadQuerySubmitResultV1::submitted);
  const auto boundary_thread=wrong_thread?(runtime.thread^0x40000000U):runtime.thread;
  // For wrong_thread only the explicit offline boundary stamp is synthetic.
  // The production typed callback compares it with actual GetCurrentThreadId.
  assert(mt::ObserveMainThreadPumpAndDrainV1(mailbox,owned::kOwnedPumpReturn,boundary_thread));
  const auto wait=mt::WaitForMainThreadQueryV1(mailbox,q.ticket,20);
  if(wrong_thread) {
    assert(wait==mt::MainThreadQueryWaitResultV1::executor_failed);
    assert(q.invocations==0&&!q.completed&&source.calls==0);
  } else {
    assert(wait==mt::MainThreadQueryWaitResultV1::completed);
    assert(q.invocations==1&&q.completed&&!q.frame_changed&&source.calls>=2);
    assert(!q.observation.available);
    assert(q.observation.unavailable_reason=="exact4_native_actor_getter_pins_or_owner_unavailable");
  }
  assert(mt::ReclaimMainThreadQueryV1(mailbox,q.ticket)==mt::MainThreadQueryReclaimResultV1::reclaimed);
  runtime.Finish(mailbox);
}
void RealOnFactoryNegative() {
  core::NativeContext c{};c.enabled=true;c.module_base=0;c.executable_sha256=core::kExeSha;
  const auto e=core::BindNative(c);
  assert(!e.enabled&&!e.context&&!e.read_memory&&!e.read_frame&&!e.read_level&&!e.read_breakdown);
  assert(e.callback_provenance==core::CallbackProvenance::unavailable&&!e.allow_owned_fixture);
  assert(std::string_view(c.failure)=="exact4_native_actor_getter_pins_or_owner_unavailable");
  assert(!core::NativeSourceStillBound(c));
  assert(c.level_calls==0&&c.breakdown_calls==0&&c.string_destroy_calls==0);
}
}
int main() {
  SingleSlotInstallGuard();OwnedSingleSlotAndCohort();BadTlsDoesNotDispatch();
  RealOnFactoryNegative();RealFactoryAndTypedOwnerGuard(false);RealFactoryAndTypedOwnerGuard(true);
  std::puts("b11_shared_mailbox_cohort owned_memory_only six_slots legacy_pilgrimage_frontend typed_actor_factory_guard");
}
