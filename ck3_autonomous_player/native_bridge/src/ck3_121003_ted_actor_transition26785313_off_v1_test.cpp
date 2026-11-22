// Actual owner/wire code; dependencies below are explicitly NoGame DATA models.
// These tests qualify private custody/once/epoch decisions, never native ABI/Game.
#include "ck3_121003_ted_actor_transition26785313_wire_v1.cpp"
#include "ck3_121003_ted_actor_transition26785313_owner_v1.cpp"
#include "ck3_121003_ted_actor_transition26785313_raw_v1.cpp"
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
 auto&s=proof.status;s.generation=proof.generation;s.state=xar::ck3_11906::TacticalDailySentinelStateV1::triggered;s.mode=xar::ck3_11906::TacticalDailySentinelModeV1::terminal_or_sentinel;s.starting_date_raw=proof.before.core.clock.date_raw;s.target_date_raw=s.last_observed_date_raw=s.trigger_date_raw=world.core.clock.date_raw;s.speed=world.core.clock.speed;s.completed_daily_ticks=1;s.pause_observed=s.pause_wrapper_called=true;s.trigger_flags=xar::ck3_11906::tactical_daily_trigger_date_deadline;runtime.armed=false;runtime.shutdown_safe=true;has_proof=true;
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
int main(){using namespace xar::ck3_121003::build26785313;ReadonlyBindings b;TedRoleFrame267V1 f;TedRoleRaw267V1 raw;std::string reason;
 if(VerifyTedRoleImage267V1(0)||ReadTedRoleRaw267V1(b,f,false,1,1,raw,reason)||raw.entered||!raw.cleanup_known)throw std::runtime_error("defaultOFF entered actual role read");
 TedTransitionContext267V1 q;q.request.action=TedTransitionAction267V1::confirm_epoch;q.request.provider_generation=7;q.request.query_sequence=9;q.request.deadline_unix_ms=1899999999999ULL;const std::string id="off-confirm",op="off-original";std::copy(id.begin(),id.end(),q.request.request_id.begin());q.request.request_id_size=static_cast<std::uint8_t>(id.size());std::copy(op.begin(),op.end(),q.request.operation_id.begin());q.request.operation_id_size=static_cast<std::uint8_t>(op.size());xar::ck3_11906::MainThreadExecutionStampV1 stamp;
 if(!ExecuteTedTransitionInner267V1(q,stamp)||q.result.status!=TedTransitionStatus267V1::unavailable||q.result.action!=q.request.action||q.result.provider_generation!=7||q.result.query_sequence!=9||q.result.operation_id!=op||q.result.deadline_unix_ms!=q.request.deadline_unix_ms||q.result.effect_attempted||q.result.native_returned||q.result.accepted)throw std::runtime_error("defaultOFF lost parsed original lease/subjects or attempted effect");
 std::cout<<"PASS actual TED owner/Raw defaultOFF, parsed original claim/deadline preserved\n";return 0;}
