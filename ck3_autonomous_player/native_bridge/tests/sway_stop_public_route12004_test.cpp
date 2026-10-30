#include "xar_bridge/ck3_12004_sway_stop.hpp"
#include "fixtures/sway_stop_public_route12004_world.hpp"

namespace xar::ck3_12004 {
SwayStopBindings12004 RealBindSwayStopImage12004(std::uintptr_t,std::string_view,const SwayStopCommandProfile12004 &) noexcept;
}
namespace {
World *current_world=nullptr;
bool pure_factory=false,accept_native_queue=true;
std::array<void *,9> command_vtable{};
int command_manager=0,stop_binding_calls=0,native_clones=0,native_queues=0,native_deletes=0;
std::uint32_t last_scheme=0xFFFFFFFFU,last_channel=0;
void *DeleteCommand(void *command,std::uint32_t){++native_deletes;delete static_cast<actual4::SelectedEndSchemeCommand12004 *>(command);return nullptr;}
void **CloneCommand(const void *source,void **storage){++native_clones;*storage=new actual4::SelectedEndSchemeCommand12004(*static_cast<const actual4::SelectedEndSchemeCommand12004 *>(source));return storage;}
bool QueueCommand(void *manager,void **owned,std::uint32_t channel){
 Check(manager==&command_manager&&owned&&*owned,"actual SubmitCommandCopy transfers clone ownership");
 auto *command=static_cast<actual4::SelectedEndSchemeCommand12004 *>(*owned);++native_queues;last_scheme=command->scheme_id;last_channel=channel;
 Check(command->secondary_vtable==reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr))+actual4::kSwayStopCommandProfile12004.secondary_vtable_rva,"production command preserves actual4 secondary interface operand");
 if(accept_native_queue){DeleteCommand(command,1);*owned=nullptr;}return accept_native_queue;
}
void InitializeVtable(){command_vtable[0]=reinterpret_cast<void *>(&DeleteCommand);command_vtable[8]=reinterpret_cast<void *>(&CloneCommand);}
void ResetCounters(){native_clones=native_queues=native_deletes=0;last_scheme=0xFFFFFFFFU;last_channel=0;accept_native_queue=true;}
void PureFactories(){
 pure_factory=true;const std::uintptr_t base=0x140000000;
 auto b=actual4::RealBindSwayStopImage12004(base,actual4::kExecutableSha256,actual4::kSwayStopCommandProfile12004);
 Check(b.enabled&&b.commands.enabled&&b.terminal.enabled&&b.primary_vtable==base+0x476ED40&&b.secondary_vtable==base+0x476EB80,"real current .4 Stop factory and its actual Command/Terminal factories enabled with exact profile");
 Check(!actual4::RealBindSwayStopImage12004(base,native::kExecutableSha256,actual4::kSwayStopCommandProfile12004).enabled,"Stop real factory rejects historical image identity");
 auto bad=actual4::kSwayStopCommandProfile12004;bad.primary_vtable_rva=0;Check(!actual4::RealBindSwayStopImage12004(base,actual4::kExecutableSha256,bad).enabled,"Stop real factory rejects absent actual command table");
 Check(!actual4::RealBindSwayStopImage12004(0,actual4::kExecutableSha256,actual4::kSwayStopCommandProfile12004).enabled,"Stop real factory rejects null image");pure_factory=false;
}
struct Result{bool success=false,drained=false;std::string wire,failure;std::uint64_t tickets=0,executed=0;};
Result Call(FrameAdapter &adapter,bool stop,std::string_view payload,bool expected_queue){
 api::MainThreadQueryMailboxV1 mailbox{};Pump pump(mailbox);Result result{};std::atomic<bool> done=false;adapter.reads=0;
 std::thread worker([&]{result.success=stop?actual4::HandleSelectedSwayStop12004(adapter,mailbox,adapter.frame,7,actual4::kSwayStopStep12004,payload,"stop-public-route",result.wire,result.failure):actual4::HandleSwayTerminal12004(adapter,mailbox,adapter.frame,7,native::kSwayCompletionStepV1,payload,"stop-public-query",result.wire,result.failure);done.store(true,std::memory_order_release);});
 const auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(12);
 while(!done.load(std::memory_order_acquire)&&std::chrono::steady_clock::now()<deadline){if(mailbox.state==api::MainThreadQueryMailboxStateV1::queued)result.drained|=api::ObserveMainThreadPumpAndDrainV1(mailbox,mailbox.pump_exact_return_rva,GetCurrentThreadId());std::this_thread::sleep_for(std::chrono::milliseconds(1));}
 worker.join();result.tickets=mailbox.next_sequence;result.executed=mailbox.executed_requests;
 Check(result.drained==expected_queue,"public Stop/terminal real queue drain classification");Check(mailbox.state==api::MainThreadQueryMailboxStateV1::idle,"public Stop/terminal reclaims real mailbox");Check(result.tickets==(expected_queue?1U:0U)&&result.executed==(expected_queue?1U:0U)&&mailbox.failure_flags==0,"real named callback/ticket counts");
 if(expected_queue)Check(mailbox.executor_started_requests==1&&mailbox.completed_sequence==mailbox.published_sequence,"genuine pump completion identity");return result;
}
bool Has(std::string_view text,std::string_view part){return text.find(part)!=std::string_view::npos;}
std::string Request(std::int32_t actor,std::int32_t target,int revision=7,std::uint32_t scheme=0,std::uint32_t generation=0){return "{\"expected_revision\":"+std::to_string(revision)+",\"action_id\":\"stop-sway-canonical\",\"actor_character_id\":"+std::to_string(actor)+",\"target_character_id\":"+std::to_string(target)+",\"scheme_instance_id\":"+std::to_string(scheme)+",\"scheme_instance_generation\":"+std::to_string(generation)+"}";}
std::string Query(std::int32_t actor,std::int32_t target){return "{\"expected_revision\":7,\"actor_character_id\":"+std::to_string(actor)+",\"target_character_id\":"+std::to_string(target)+",\"scheme_instance_id\":0}";}
void Save(const std::filesystem::path &root,const std::string &name,std::string_view bytes){std::ofstream out(root/name,std::ios::binary);out<<bytes;out.close();Check(out.good(),"save actual original public serializer bytes");}
void Frame(FrameAdapter &a,std::int32_t actor){a.frame.date_raw=53220000;a.frame.speed=1;a.frame.paused=a.frame.map_ready=a.frame.has_played_character=a.frame.played_character_alive=true;a.frame.played_character_id=actor;}
void Case(std::int32_t actor,std::int32_t target,const std::filesystem::path &out,bool baseline){
 World world(actor,target);current_world=&world;FrameAdapter adapter;Frame(adapter,actor);ResetCounters();
 const std::string prefix=actor==-2?"minus2-zero":"zero-minus2";const auto request=Request(actor,target);Save(out,prefix+".stop.request.json",request);
 if(baseline){auto r=Call(adapter,true,request,false);Save(out,prefix+".baseline-observation.json","{\"schema\":\"isolated-public-stop-observation-not-command-result\",\"success\":"+std::string(r.success?"true":"false")+",\"failure\":\""+r.failure+"\",\"serialized_empty\":"+(r.wire.empty()?"true":"false")+",\"tickets\":"+std::to_string(r.tickets)+",\"native_queue_calls\":"+std::to_string(native_queues)+"}");Check(r.success,"canonical full32 Stop should reach real command queue (baseline RED)");Check(!r.success&&r.wire.empty()&&r.failure=="selected_sway_stop_frame_or_request_invalid"&&native_queues==0,"baseline retained precise parser rejection with no invented response or command execution");current_world=nullptr;return;}
 for(const auto field:{std::string_view("actor_character_id"),std::string_view("target_character_id")})for(const auto token:{std::string_view("-1"),std::string_view("true"),std::string_view("0.0"),std::string_view("\"0\""),std::string_view("00"),std::string_view("-0"),std::string_view("2147483648"),std::string_view("4294967294"),std::string_view("-2147483649")}){
   auto invalid=request;const std::string key='"'+std::string(field)+"\":";const auto start=invalid.find(key)+key.size();const auto end=invalid.find(',',start);invalid.replace(start,end-start,token);auto rejected=Call(adapter,true,invalid,false);Check(!rejected.success&&rejected.wire.empty()&&native_queues==0,"public Stop rejects sentinel, wrong JSON type, noncanonical integer and outside signed-full32 before ticket");
 }
 auto self=Call(adapter,true,Request(actor,actor),false);Check(!self.success&&native_queues==0,"public Stop rejects equal actor and target");
 auto before=Call(adapter,false,Query(actor,target),true);Save(out,prefix+".current.response.json",before.wire);Check(before.success&&Has(before.wire,"\"native_status_raw\":0")&&Has(before.wire,"\"native_terminal_state_observed\":false"),"independent public terminal reader observes current full SchemeID0");
 auto stop=Call(adapter,true,request,true);Save(out,prefix+".stop.response.json",stop.wire);Check(stop.success&&stop.failure.empty()&&Has(stop.wire,"\"status\":\"submitted_verification_pending\"")&&Has(stop.wire,"\"scheme_instance_id\":0")&&Has(stop.wire,"\"scheme_instance_generation\":0")&&Has(stop.wire,"\"postcondition_verified\":false")&&Has(stop.wire,"\"terminal_observed\":false")&&Has(stop.wire,"\"terminal_cause_observed\":false"),"real Stop public pending ACK preserves full SchemeID0 without inventing terminal receipt");
 Check(native_queues==1&&native_clones==1&&native_deletes==1&&last_scheme==0&&last_channel==14,"real SubmitCommandCopy clone/move/ownership release uses native Cancel kind14 and full SchemeID0");
 Check(Has(stop.wire,"\"actor_character_id\":"+std::to_string(actor))&&Has(stop.wire,"\"target_character_id\":"+std::to_string(target)),"actual original Stop serializer preserves signed canonical roles");
 auto pending=Call(adapter,false,Query(actor,target),true);Save(out,prefix+".pending.response.json",pending.wire);Check(pending.success&&Has(pending.wire,"\"native_status_raw\":0")&&Has(pending.wire,"\"native_terminal_state_observed\":false")&&native_queues==1,"independent post-ACK query remains active; queue callback did not fake a gameplay effect");
 auto stale=Call(adapter,true,Request(actor,target,6),false);Check(!stale.success&&native_queues==1,"stale revision refused before Stop queue");
 auto mismatch=Call(adapter,true,Request(actor,target,7,0,1),false);Check(!mismatch.success&&native_queues==1,"mismatched full SchemeID generation rejected before ticket");
 auto reused=Call(adapter,true,Request(actor,target,7,0x01000000U,1),true);Check(reused.success&&Has(reused.wire,"\"accepted\":false")&&native_queues==1,"same storage slot wrong scheme generation cannot queue another instance");Save(out,prefix+".wrong-generation.response.json",reused.wire);
 // Explicit independently controlled native-memory fixture state, never an
 // emulated CEndSchemeCommand execute or a cancellation cause observation.
 Put(world.scheme.data(),0x28,std::int32_t{1});Put(world.scheme.data(),0x2C,std::uint32_t{0xFFFFFFFFU});
 auto terminal=Call(adapter,false,Query(actor,target),true);Save(out,prefix+".terminal.response.json",terminal.wire);Check(terminal.success&&Has(terminal.wire,"\"native_terminal_state_observed\":true")&&Has(terminal.wire,"\"owner_cleared\":true")&&Has(terminal.wire,"\"terminal_cause_observed\":false")&&Has(terminal.wire,"\"terminal_cause\":\"unknown\"")&&native_queues==1,"true independent retained-row query proves terminated_unattributed only, no Cancel cause credit");
 auto ended=Call(adapter,true,request,true);Save(out,prefix+".ended-stop.response.json",ended.wire);Check(ended.success&&Has(ended.wire,"\"accepted\":false")&&native_queues==1,"a retained terminal row cannot queue another Stop");current_world=nullptr;
}
}
namespace xar::ck3_12004 {
ck3_12002::SwayCompletionBindings12002 BindSwayTerminalImage12004(std::uintptr_t base,std::string_view sha) noexcept{
 if(pure_factory)return RealBindSwayTerminalImage12004(base,sha);++bind_calls;if(!current_world||sha!=kExecutableSha256)NotExercised();return current_world->binding;
}
SwayStopBindings12004 BindSwayStopImage12004(std::uintptr_t base,std::string_view sha,const SwayStopCommandProfile12004 &profile) noexcept{
 ++stop_binding_calls;auto b=RealBindSwayStopImage12004(base,sha,profile);if(!current_world||!b.enabled)NotExercised();b.terminal=current_world->binding;b.primary_vtable=reinterpret_cast<std::uintptr_t>(command_vtable.data());b.commands.command_manager=&command_manager;b.commands.queue_owned_command=&QueueCommand;return b;
}
}
namespace xar::ck3_12002 {const game::GameAdapter &NativeAdapter12002(const game::GameAdapter &a)noexcept{return a;}}
namespace xar::game {bool ReadCk3_12002TimelineCoreSnapshot(const GameAdapter &,Snapshot &)noexcept{NotExercised();}}
int main(int argc,char **argv){try{if(argc!=3)throw std::runtime_error("mode and unique wire output");const bool baseline=std::string_view(argv[1])=="baseline";if(!baseline&&std::string_view(argv[1])!="candidate")throw std::runtime_error("unknown mode");std::filesystem::path out(argv[2]);std::filesystem::create_directories(out);InitializeVtable();PureFactories();Case(-2,0,out,baseline);Case(0,-2,out,baseline);Check(abort_calls==0,"unused native paths remain zero");std::cout<<"STOP_PUBLIC_CHECKS "<<checks<<" FAILED "<<failures<<" mode="<<argv[1]<<" pureactual4factory; truepublichandler/slot58/queue/pump/copyownership; ACK pending, independent retained row unattributed; no Game/actualnativeexecute\n";return failures==0?0:1;}catch(const std::exception &e){std::cerr<<"ERROR "<<e.what()<<'\n';return 2;}}
