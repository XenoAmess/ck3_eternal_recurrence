// Actual owner/wire code; dependencies below are explicitly NoGame DATA models.
// These tests qualify private custody/once/epoch decisions, never native ABI/Game.
#include "ck3_121003_ted_actor_transition26785313_wire_v1.cpp"
#include "ck3_121003_ted_actor_transition26785313_owner_v1.cpp"
#include <stdexcept>
#include <iostream>
namespace model {
using namespace xar::ck3_121003::build26785313;
constexpr std::int32_t Song=-16777215,Recipient=36423;
std::array<std::byte,16>world_memory[7];xar::ck3_1210::DateSentinelObservationV1 world;
xar::ck3_1210::DateSentinelStateV1 runtime;DateAdvanceSession267V1 old;
bool definition=true,shown=true,cleanup=true,global_unknown=false,old_open=false,ted_active=false;
unsigned reads=0,arms=0,queues=0;bool has_proof=false;
xar::ck3_1210::TedFixedDayProof267V1 proof;
void require(bool value,const char*why){if(!value)throw std::runtime_error(why);}
void Init(){auto&c=world.core;c.clock.date_raw=53144328;c.clock.speed=1;c.clock.paused=true;c.local_player_id=0;c.map_ready=c.has_played_character=c.played_character_alive=true;c.played_character_id=Song;
 world.game=world_memory[0].data();world.jomini=world_memory[1].data();world.storage=world_memory[2].data();world.data=world_memory[3].data();world.players=world_memory[4].data();world.player=world_memory[5].data();world.actor=world_memory[6].data();runtime.initialized=true;runtime.shutdown_safe=true;runtime.bindings.runtime_profile=xar::ck3_1210::DateSentinelRuntimeProfileV1::current26785313;}
void Complete(bool change){world.core.clock.date_raw+=24;world.core.clock.paused=true;if(change){world.core.played_character_id=Recipient;world.actor=world_memory[5].data();}
 proof.captured=true;proof.actor_changed=change;proof.after=world;proof.original_deadline_unix_ms=runtime.original_deadline_unix_ms;proof.monotonic_deadline_ms=runtime.monotonic_deadline_ms;proof.captured_unix_ms=Wall();proof.captured_monotonic_ms=GetTickCount64();
 auto&s=proof.status;s.generation=proof.generation;s.state=xar::ck3_11906::TacticalDailySentinelStateV1::triggered;s.mode=xar::ck3_11906::TacticalDailySentinelModeV1::terminal_or_sentinel;s.starting_date_raw=proof.before.core.clock.date_raw;s.target_date_raw=s.last_observed_date_raw=s.trigger_date_raw=world.core.clock.date_raw;s.speed=world.core.clock.speed;s.completed_daily_ticks=1;s.overshoot_days=0;s.pause_observed=s.pause_wrapper_called=true;s.trigger_flags=xar::ck3_11906::tactical_daily_trigger_date_deadline;runtime.armed=false;runtime.shutdown_safe=true;has_proof=true;
}
}
namespace xar::ck3_121003::build26785313 {
ReadonlyBindings BindReadonlyImage(std::uintptr_t image,std::string_view)noexcept{ReadonlyBindings b;b.exact_image_admitted=true;b.module_base=image;return b;}
bool DateAdvanceRuntimeMatches267V1(DateAdvanceSession267V1&s,const ck3_1210::DateSentinelStateV1&r)noexcept{return &s==&model::old&&&r==&model::runtime;}
bool TedDatePredecessorResolved267V1(const ck3_1210::DateSentinelStateV1&)noexcept{return !model::global_unknown&&!model::old_open;}
bool ClaimTedDateCustody267V1(const ck3_1210::DateSentinelStateV1&,bool continuation)noexcept{if(model::global_unknown||model::old_open||model::ted_active!=continuation)return false;model::ted_active=true;return true;}
void CompleteTedDateCustody267V1(const ck3_1210::DateSentinelStateV1&)noexcept{if(!model::global_unknown)model::ted_active=false;}
void BlockTedDateCustodyUnknown267V1(const ck3_1210::DateSentinelStateV1&)noexcept{model::global_unknown=model::ted_active=true;}
bool ReadTedRoleFrameOnOwner267V1(const ReadonlyBindings&,ck3_11906::MainThreadQueryMailboxV1*,const ck3_11906::MainThreadQueryTicketV1&,const ck3_11906::MainThreadExecutionStampV1&,void*,std::uint64_t,std::uint64_t,TedRoleFrame267V1&out,std::string&)noexcept{out.facts_verified=true;out.world=model::world;return true;}
bool ReadTedRoleRaw267V1(const ReadonlyBindings&,const TedRoleFrame267V1&,bool,std::uint64_t,std::uint64_t,TedRoleRaw267V1&out,std::string&)noexcept{++model::reads;out.definition=model::definition?0x1000:0;out.shown=model::shown;out.entered=true;out.cleanup_known=model::cleanup;return model::cleanup;}
CommandImageBindingsV1 BindCurrentCommandImageV1(std::uintptr_t,const CommandIdentityV1&)noexcept{CommandImageBindingsV1 b;b.current_image_verified=true;return b;}
bool CurrentCommandTargetsMatchV1(const CommandImageBindingsV1&b)noexcept{return b.current_image_verified;}
RuntimeEventTimeGate267V1 ReadRuntimeEventTimeGate267V1(const ReadonlyBindings&,const ck3_1210::CoreSnapshotPrefix&)noexcept{return RuntimeEventTimeGate267V1::clear;}
}
namespace xar::ck3_1210 {
ck3_11906::TacticalDailySentinelArmStatusV1 ArmTedFixedDay267V1(DateSentinelStateV1&r,const ck3_11906::TacticalDailySentinelArmRequestV1&,std::uint64_t deadline,TedFixedDayStage267V1 stage)noexcept{++model::arms;r.generation.fetch_add(1);r.armed=true;r.shutdown_safe=false;r.original_deadline_unix_ms=deadline;r.monotonic_deadline_ms=GetTickCount64()+(deadline-xar::ck3_121003::build26785313::Wall());model::proof={};model::proof.before=model::world;model::proof.generation=r.generation.load();model::proof.stage=stage;model::has_proof=false;return ck3_11906::TacticalDailySentinelArmStatusV1::armed;}
bool DateSentinelAllowsResumeV1(DateSentinelStateV1&r,const CoreSnapshotPrefix&)noexcept{return r.armed.load();}
TimeCommand MakePauseCommand(const CommandBindings&,std::int32_t,bool)noexcept{return {};}
CommandSubmitResult SubmitCommandCopy(const CommandBindings&,const void*,std::uint32_t,BeforeQueueV1 before,void*p)noexcept{if(!before||!before(p))return CommandSubmitResult::rejected;++model::queues;return CommandSubmitResult::submitted;}
bool ReadTedFixedDayProof267V1(const DateSentinelStateV1&r,std::uint64_t generation,TedFixedDayProof267V1&out,ck3_11906::TacticalDailySentinelStatusV1&status)noexcept{if(!model::has_proof){status={};status.generation=generation;status.state=ck3_11906::TacticalDailySentinelStateV1::armed;status.last_observed_date_raw=model::world.core.clock.date_raw;return false;}out=model::proof;status=out.status;return generation==r.generation.load()&&generation==out.generation;}
ck3_11906::TacticalDailySentinelCancelStatusV1 CancelDateSentinelV1(DateSentinelStateV1&,std::uint64_t)noexcept{return ck3_11906::TacticalDailySentinelCancelStatusV1::unavailable;}
void RequestDateSentinelShutdownV1(DateSentinelStateV1&r)noexcept{r.shutdown_requested=true;}
}
int exercise(){using namespace model;using namespace xar::ck3_121003::build26785313;
 Init();TedTransitionSession267V1 session;require(BindTedTransitionSession267V1(session,old,runtime),"fixed actual-binding seam");auto mailbox=std::make_unique<xar::ck3_11906::MainThreadQueryMailboxV1>();mailbox->permitted_executor_sexvigintary=&ExecuteTedTransitionOnOwner267V1;xar::ck3_11906::MainThreadExecutionStampV1 stamp;stamp.thread_id=7;stamp.pump_epoch=11;stamp.paused=true;unsigned ids=0;const auto deadline=Wall()+60000;
 const auto make=[&](A action,std::uint64_t connection=21){TedTransitionContext267V1 q;q.session=&session;q.mailbox=mailbox.get();q.ticket.sequence=17;q.connection_generation=connection;q.request.action=action;q.request.expected=world.core;q.request.deadline_unix_ms=deadline;const auto id="ted-model-"+std::to_string(++ids);std::copy(id.begin(),id.end(),q.request.request_id.begin());q.request.request_id_size=static_cast<std::uint8_t>(id.size());if(action!=A::query_role){const auto op=std::string("ted-date01");std::copy(op.begin(),op.end(),q.request.operation_id.begin());q.request.operation_id_size=static_cast<std::uint8_t>(op.size());}ArmTedTransitionDeadline267V1(q);return q;};
 const auto lease=[&](TedTransitionContext267V1&q,const TedTransitionContext267V1&query){q.request.provider_generation=query.result.provider_generation;q.request.query_sequence=query.result.query_sequence;q.request.actor_epoch=query.result.actor_epoch;};
 definition=false;auto missing=make(A::query_role);ExecuteTedTransitionInner267V1(missing,stamp);require(missing.result.status==S::available&&missing.result.source&&!missing.result.source->definition_found&&!missing.result.source->advance_admissible&&arms==0,"missing definition remains negative DATA");definition=true;shown=false;auto negative=make(A::query_role);ExecuteTedTransitionInner267V1(negative,stamp);require(negative.result.status==S::available&&!negative.result.source->advance_admissible,"false actual role no permission");shown=true;
 auto song=make(A::query_role);ExecuteTedTransitionInner267V1(song,stamp);require(song.result.status==S::available&&song.result.source->advance_admissible,"beforeSong query");
 auto wrong=make(A::advance_day,22);lease(wrong,song);ExecuteTedTransitionInner267V1(wrong,stamp);require(wrong.result.status==S::stale_source&&arms==0,"foreign connection before claim");
 auto advance=make(A::advance_day);lease(advance,song);ExecuteTedTransitionInner267V1(advance,stamp);require(advance.result.status==S::submitted&&advance.result.accepted&&arms==1&&queues==1,"actual private D1 owner submission");
 auto status=advance.request;status.action=A::query_operation;const auto running=QueryTedTransitionOperation267V1(session,status,21);require(running.status==S::running&&!running.source,"pure original operation running DATA");Complete(true);const auto pending=QueryTedTransitionOperation267V1(session,status,21);require(pending.status==S::transition_pending&&pending.progress->transition_pending&&pending.progress->exact_day_confirmed&&!pending.source&&pending.actor_epoch==0,"exact one-day pending, no epoch update");
 auto foreign=make(A::query_role,22);const auto reads_before=reads;ExecuteTedTransitionInner267V1(foreign,stamp);require(foreign.result.status==S::stale_source&&reads==reads_before,"new connection cannot recover pending permission");
 auto after=make(A::query_role);ExecuteTedTransitionInner267V1(after,stamp);require(after.result.status==S::available&&after.result.source->confirm_admissible&&!after.result.source->advance_admissible,"independent recipient proof required");
 auto premature=make(A::advance_day);lease(premature,after);ExecuteTedTransitionInner267V1(premature,stamp);require(premature.result.status==S::unavailable&&arms==1,"pending does not authorize D2");
 auto confirm=make(A::confirm_epoch);lease(confirm,after);ExecuteTedTransitionInner267V1(confirm,stamp);require(confirm.result.status==S::epoch_confirmed&&confirm.result.actor_epoch==1&&confirm.result.source->actor_epoch==0&&confirm.result.source->pending&&!confirm.result.effect_attempted&&!confirm.result.native_returned&&arms==1&&queues==1,"once epoch consumes immutable beforeSource without Game call");
 ExecuteTedTransitionInner267V1(confirm,stamp);require(confirm.result.status==S::claim_consumed&&arms==1,"confirm cannot replay");
 auto recipient=make(A::query_role);ExecuteTedTransitionInner267V1(recipient,stamp);require(recipient.result.actor_epoch==1&&recipient.result.source->advance_admissible,"fresh recipient epoch source");auto second=make(A::advance_day);lease(second,recipient);const std::string op2="ted-date02";second.request.operation_id={};std::copy(op2.begin(),op2.end(),second.request.operation_id.begin());second.request.operation_id_size=static_cast<std::uint8_t>(op2.size());ExecuteTedTransitionInner267V1(second,stamp);require(second.result.status==S::submitted&&arms==2&&queues==2,"D2 separate original request");Complete(false);auto second_status=second.request;second_status.action=A::query_operation;const auto done=QueryTedTransitionOperation267V1(session,second_status,21);require(done.status==S::completed_day&&done.actor_epoch==2&&!done.progress->transition_pending&&!ted_active,"exact D2 completes finite new family");
 auto final=make(A::query_role);ExecuteTedTransitionInner267V1(final,stamp);require(final.result.status==S::available&&final.result.actor_epoch==2&&!final.result.source->advance_admissible,"epoch2 no third action");require(QueryTedTransitionOperation267V1(session,status,21).status==S::transition_pending,"confirmation did not rewrite original D1 outcome");
 BlockTedTransitionUnknown267V1(session);auto later=make(A::query_role);ExecuteTedTransitionInner267V1(later,stamp);require(later.result.status==S::indeterminate&&!later.result.cleanup_known&&global_unknown,"unknown remains process custody");
 std::cout<<"PASS actual TED owner private query/claim/connection/pending/epoch/D2/UNKNOWN logic; explicit NoGame dependency models only\n";return 0;
}

int main(){try{return exercise();}catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<std::endl;return 1;}}
