#include "xar_bridge/player_inventory_window12004_transport.hpp"
#include "xar_bridge/player_inventory_open_ledger12004.hpp"
#include "xar_bridge/player_inventory_close_ledger12004.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ingame_ui_navigation_v1.hpp"
#include "xar_bridge/normal_exit_map_source_v1.hpp"
#include "xar_bridge/protocol.hpp"
#include <windows.h>
#include <memory>
#include <mutex>

namespace xar::ck3_12004::player_inventory_window {
namespace {
using namespace ck3_11906;
namespace item=artifact_personal_use;
enum class Operation {query,open,post,close_query,close,close_post};
bool Action(Operation op) noexcept {return op==Operation::open||op==Operation::close;}
bool Post(Operation op) noexcept {return op==Operation::post||op==Operation::close_post;}
bool CloseDomain(Operation op) noexcept {return op==Operation::close_query||op==Operation::close||op==Operation::close_post;}
struct Query;
struct ProcessState {
  std::mutex worker_mutex;
  std::unique_ptr<Query> active;
  PlayerInventoryOpenLedger12004 ledger;
  PlayerInventoryCloseLedger12004 close_ledger;
};
struct Query {
  MainThreadQueryMailboxV1* mailbox=nullptr;
  MainThreadQueryTicketV1 ticket{};
  const game::GameAdapter* game=nullptr;
  game::Snapshot expected{};
  ProcessState* state=nullptr;
  std::uint64_t revision=0,generation=0,original_sequence=0;
  std::uint32_t pid=0,invocations=0;
  std::uintptr_t base=0;
  Operation operation=Operation::query;
  bool sources_verified=false,completed=false;
  Observation result{};
  std::string source_inventory_sha;
};
struct Context {Query* query=nullptr;MainThreadExecutionStampV1 stamp{};};
ProcessState& State(){static ProcessState value;return value;}
PlayerInventoryOpenPost12004 Metadata(const Query& q,std::uint64_t epoch=0) {
  PlayerInventoryOpenPost12004 out{};out.revision=q.revision;out.capture_epoch=epoch;
  out.generation=q.generation;out.date_raw=q.expected.date_raw;out.pid=q.pid;
  out.actor_id=static_cast<std::uint32_t>(q.expected.played_character_id);return out;
}
bool ReadByte(std::uintptr_t address,std::uint8_t& out) noexcept {
  SIZE_T got=0;
  return address&&ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<const void*>(address),&out,sizeof(out),&got)&&got==sizeof(out);
}
bool Current(Context& c,game::Snapshot& now) noexcept {
  const auto& q=*c.query;std::uint8_t initialized=0;
  return q.mailbox&&q.game&&q.pid==GetCurrentProcessId()&&q.revision&&q.generation&&
      q.base==reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr))&&
      q.game->enabled()&&game::IsCk3_12004Descriptor(q.game->descriptor())&&
      !q.mailbox->stop_requested.load(std::memory_order_acquire)&&
      q.mailbox->state.load(std::memory_order_acquire)==MainThreadQueryMailboxStateV1::executing&&
      q.mailbox->published_sequence.load(std::memory_order_acquire)==q.ticket.sequence&&
      q.mailbox->executor_started_sequence.load(std::memory_order_acquire)==q.ticket.sequence&&
      IsIngameUiPausedOwnerStampV1(*q.mailbox,c.stamp,GetCurrentThreadId())&&
      ReadByte(c.stamp.tls_initialized_flag_address,initialized)&&initialized==1&&
      q.game->read_snapshot(now)&&now==q.expected&&now.paused&&now.map_ready&&
      now.has_played_character&&now.played_character_alive&&now.played_character_id>0&&
      now.date_raw==c.stamp.date_raw;
}
bool Admission(void* opaque,item::Frame& frame,bool& event,bool& interaction) noexcept {
  auto& c=*static_cast<Context*>(opaque);game::Snapshot now{};
  if(!Current(c,now))return false;
  const auto& q=*c.query;
  frame={q.revision,c.stamp.pump_epoch,q.generation,now.date_raw,q.pid,
    static_cast<std::uint32_t>(now.played_character_id),c.stamp.jomini_state,true,true,true,true,true};
  event=now.has_active_event;interaction=now.has_pending_character_interaction;return true;
}
bool Claim(void* opaque,std::uint64_t sequence,const PlayerInventoryOpenPost12004& before) noexcept {
  auto& c=*static_cast<Context*>(opaque);auto& q=*c.query;
  item::Frame current{};bool event=false,interaction=false;
  if(!Action(q.operation)||sequence!=q.ticket.sequence||!q.state||!q.sources_verified||
      !Admission(opaque,current,event,interaction)||event||interaction||!before.available||!before.current_admission||
      before.revision!=current.revision||before.capture_epoch!=current.capture_epoch||
      before.generation!=current.connection_generation||before.pid!=current.bridge_pid||
      before.actor_id!=current.actor_id||before.date_raw!=current.date_raw||before.owner!=current.owner)return false;
  const auto actor=static_cast<std::uint32_t>(q.expected.played_character_id);
  if(q.operation==Operation::close) {
    PlayerInventoryOpenLedger12004::Receipt other{};
    if(q.state->ledger.Find(0,q.pid,actor,other)&&other.pending)return false;
    return q.state->close_ledger.Claim(sequence,before);
  }
  PlayerInventoryCloseLedger12004::Receipt other{};
  if(q.state->close_ledger.Find(0,q.pid,actor,other)&&other.pending)return false;
  return q.state->ledger.Claim(sequence,before);
}
void Invalidate(Query& q,const char* reason) {
  const auto epoch=q.result.current.capture_epoch;
  q.result.current=Metadata(q,epoch);q.result.available=false;
  q.result.code_pins_verified=false;q.result.gui_sources_verified=false;
  q.result.desired_window_observed=false;q.result.unavailable_reason=reason;
  if(q.result.has_after)q.result.after=q.result.current;
  if(q.result.once_consumed)q.result.needs_recovery=true;
  if(q.operation==Operation::query||q.operation==Operation::close_query)q.result.status="inventory_window_unavailable";
  if(Post(q.operation))q.result.status="inventory_intent_pending_or_unknown";
}
template<class Receipt> void LoadReceipt(Query& q,const Receipt& receipt) {
  auto& r=q.result;r.intent_found=receipt.found;r.intent_sequence=receipt.sequence;
  r.once_consumed=receipt.found;r.invoked=receipt.invoked;r.call_returned=receipt.call_returned;
  r.needs_recovery=receipt.pending;r.before=receipt.before;r.has_before=receipt.found;
}
bool Execute(void* opaque,const MainThreadExecutionStampV1& stamp,bool action) noexcept {
  auto* query=static_cast<Query*>(opaque);
  if(!query||!query->mailbox||!query->ticket.sequence||query->invocations||!query->state||
      Action(query->operation)!=action||query->mailbox->executor_context!=query||
      query->mailbox->failure_flags.load(std::memory_order_acquire)||
      query->mailbox->executor.load(std::memory_order_acquire)!=(action?&ExecuteOpen:&ExecuteRead))return false;
  auto& q=*query;auto& out=q.result;const bool close=CloseDomain(q.operation);
  const auto actor=static_cast<std::uint32_t>(q.expected.played_character_id);
  try {
    ++q.invocations;Context c{&q,stamp};out.current=Metadata(q,stamp.pump_epoch);
    game::Snapshot current{};
    if(!Current(c,current)){Invalidate(q,"inventory_current_owner_frame_unavailable");q.completed=true;return true;}
    const auto env=BindZhongguoScoreboardNativeEnvironmentV1(q.base,true,GuiAbiRevisionV1::crozier12004,kExecutableSha256);
    PlayerInventoryWindowNativeInputs12004 input{&c,&Admission,&Claim,q.ticket.sequence,q.operation==Operation::open,q.sources_verified};
    input.close_enabled=close;
    std::string reason;bool code=false;PlayerInventoryOpenPost12004 observed{};
    const bool read=ReadPlayerInventoryWindowNative12004(env,input,observed,code,reason);
    out.code_pins_verified=code;out.gui_sources_verified=q.sources_verified;
    if(observed.actor_id!=0xffffffffU)out.current=observed;
    out.available=read&&observed.available;out.unavailable_reason=out.available?"":reason;
    if(action) {
      const auto result=close?ClosePlayerInventoryWindowNative12004(env,input):OpenPlayerInventoryWindowNative12004(env,input);
      if(result.before.actor_id!=0xffffffffU){out.current=result.before;out.before=result.before;out.has_before=true;}
      out.code_pins_verified=result.code_pins_verified;
      out.available=out.current.available&&out.current.current_admission&&out.code_pins_verified&&out.gui_sources_verified;
      out.unavailable_reason=out.available?"":close?"inventory_close_current_observation_unavailable":"inventory_open_current_observation_unavailable";
      out.once_consumed=result.once_consumed;out.intent_found=result.once_consumed;
      out.intent_sequence=result.once_consumed?q.ticket.sequence:0;
      out.invoked=result.invoked;out.call_returned=result.call_returned;out.needs_recovery=result.needs_recovery;out.status=result.status;
      if(result.once_consumed) {
        if(close)q.state->close_ledger.Record(q.ticket.sequence,q.pid,actor,result.invoked,result.call_returned,result.status);
        else q.state->ledger.Record(q.ticket.sequence,q.pid,actor,result.invoked,result.call_returned,result.status);
      }
    } else {
      const auto original=Post(q.operation)?q.original_sequence:0;
      if(close) {PlayerInventoryCloseLedger12004::Receipt receipt{};
        if(q.state->close_ledger.Find(original,q.pid,actor,receipt))LoadReceipt(q,receipt);
      } else {PlayerInventoryOpenLedger12004::Receipt receipt{};
        if(q.state->ledger.Find(original,q.pid,actor,receipt))LoadReceipt(q,receipt);
      }
      if(Post(q.operation)){out.has_after=true;out.after=out.current;}
      else out.status=out.available?"inventory_window_observed":"inventory_window_unavailable";
    }
    item::Frame final_frame{};bool event=false,interaction=false;
    if(!Admission(&c,final_frame,event,interaction)||final_frame.revision!=q.revision||
        final_frame.capture_epoch!=stamp.pump_epoch||final_frame.connection_generation!=q.generation||
        final_frame.owner!=stamp.jomini_state)Invalidate(q,"inventory_owner_frame_changed_after_operation");
    else if(Post(q.operation)&&out.intent_found) {
      const bool proof=out.available&&(close?PlayerInventoryCloseDesiredObserved12004(out.before,out.after):
          PlayerInventoryOpenDesiredObserved12004(out.before,out.after));
      bool found=false,pending=true;
      if(close) {PlayerInventoryCloseLedger12004::Receipt r{};found=q.state->close_ledger.Find(q.original_sequence,q.pid,actor,r);pending=r.pending;}
      else {PlayerInventoryOpenLedger12004::Receipt r{};found=q.state->ledger.Find(q.original_sequence,q.pid,actor,r);pending=r.pending;}
      if(!found)Invalidate(q,"inventory_retained_intent_changed");
      else {
        // Provisional only: worker snapshot/source closure must precede actual
        // ledger resolution. Query never resolves either kind of pending intent.
        out.desired_window_observed=proof;out.needs_recovery=proof?false:pending;
        out.status=proof?(close?"inventory_window_closed_observed":"inventory_window_desired_observed"):
            pending?"inventory_intent_pending_or_unknown":"inventory_intent_previously_resolved_current_window_not_observed";
      }
    }
    if(!out.available){const auto reason=out.unavailable_reason;Invalidate(q,reason.empty()?"inventory_window_unavailable":reason.c_str());}
    q.completed=true;return true;
  }catch(...){Invalidate(q,"inventory_native_exception_no_replay");q.completed=true;return true;}
}
bool Has(std::string_view json,std::string_view key){return json.find('"'+std::string(key)+'"')!=std::string_view::npos;}
bool Parse(std::string_view payload,Query& q) {
  const auto equal=[&](std::string_view key,std::uint64_t expected){std::uint64_t value=0;return bridge::JsonUnsignedField(payload,key,value)&&value==expected;};
  if(!equal("expected_revision",q.revision)||!equal("expected_snapshot_revision",q.revision)||
      !equal("expected_date_raw",static_cast<std::uint64_t>(q.expected.date_raw))||
      !equal("expected_actor_character_id",static_cast<std::uint64_t>(q.expected.played_character_id))||
      !equal("expected_game_pid",q.pid)||!equal("expected_connection_generation",q.generation)||
      !bridge::JsonStringField(payload,"source_inventory_sha256",q.source_inventory_sha,64)||q.source_inventory_sha.size()!=64)return false;
  for(char c:q.source_inventory_sha)if(!((c>='0'&&c<='9')||(c>='a'&&c<='f')))return false;
  for(auto key:{"artifact_id","subject_id","request_sequence","policy_positive","desired_equipped","slot","pointer","path","rva"})if(Has(payload,key))return false;
  if(Post(q.operation))return bridge::JsonUnsignedField(payload,"expected_intent_sequence",q.original_sequence)&&q.original_sequence;
  return !Has(payload,"expected_intent_sequence");
}
bool Reclaim(ProcessState& state) {
  if(!state.active)return true;
  if(ReclaimMainThreadQueryV1(*state.active->mailbox,state.active->ticket)!=MainThreadQueryReclaimResultV1::reclaimed)return false;
  state.active.reset();return true;
}
std::string Text(std::string_view in){std::string out="\"";constexpr char h[]="0123456789abcdef";
  for(unsigned char c:in){if(c=='"'||c=='\\'){out+='\\';out+=static_cast<char>(c);}else if(c<32){out+="\\u00";out+=h[c>>4];out+=h[c&15];}else out+=static_cast<char>(c);}return out+'"';}
std::string Envelope(const Query& q,std::string_view request_id,std::string_view step) {
  const bool close=CloseDomain(q.operation);const auto body=close?SerializeClose(q.result):Serialize(q.result);if(body.empty())return {};
  return "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":"+Text(request_id)+",\"ok\":true,\"result\":{\"step\":"+Text(step)+
    ",\"accepted\":true,\"private_build\":true,\"advertised\":false,\"read_only\":"+(Action(q.operation)?"false":"true")+
    ",\"game_version\":\"1.20.0.4\",\"executable_sha256\":"+Text(kExecutableSha256)+
    ",\"backend_id\":"+Text(close?"ck3-1.20.0.4-native-player-inventory-window-close-v1-private":"ck3-1.20.0.4-native-player-inventory-window-v1-private")+
    ",\"domain_key\":"+Text(close?"player_inventory_window_close_v1":"player_inventory_window_v1")+",\"snapshot_revision\":"+std::to_string(q.revision)+
    ",\"date_raw\":"+std::to_string(q.expected.date_raw)+",\"game_pid\":"+std::to_string(q.pid)+",\"connection_generation\":"+std::to_string(q.generation)+
    ",\"status\":"+Text(q.result.available?"observed":"unavailable")+','+Text(close?"player_inventory_window_close":"player_inventory_window")+':'+body+"}}";
}
}
bool IsStep(std::string_view step) noexcept {
#if defined(XAR_CK3_ENABLE_PLAYER_INVENTORY_WINDOW_OPEN_PRIVATE_V1)
  return step==kQuery||step==kOpen||step==kPost||step==kCloseQuery||step==kClose||step==kClosePost;
#else
  (void)step;return false;
#endif
}
bool ExecuteRead(void* q,const ck3_11906::MainThreadExecutionStampV1& stamp) noexcept{return Execute(q,stamp,false);}
bool ExecuteOpen(void* q,const ck3_11906::MainThreadExecutionStampV1& stamp) noexcept{return Execute(q,stamp,true);}
bool Handle(const game::GameAdapter& game,ck3_11906::MainThreadQueryMailboxV1& mailbox,
    const game::Snapshot* published,std::uint64_t revision,std::uint64_t generation,
    std::string_view step,std::string_view payload,std::string_view request_id,std::string& response,std::string& failure) noexcept {
  response.clear();failure.clear();if(!IsStep(step))return false;
  try {
    game::Snapshot current{};
    if(!game.enabled()||!game::IsCk3_12004Descriptor(game.descriptor())||!revision||!generation||!published||
        !game.read_snapshot(current)||current!=*published||!current.paused||!current.map_ready||
        !current.has_played_character||!current.played_character_alive||current.played_character_id<=0||current.date_raw<0){failure="inventory_current_snapshot_unavailable";return false;}
    auto& state=State();std::lock_guard lock(state.worker_mutex);
    if(!Reclaim(state)){failure="inventory_original_ticket_still_owned_no_replay";return false;}
    auto value=std::make_unique<Query>();auto& q=*value;q.game=&game;q.mailbox=&mailbox;q.state=&state;q.expected=current;
    q.revision=revision;q.generation=generation;q.pid=GetCurrentProcessId();q.base=reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
    q.operation=step==kOpen?Operation::open:step==kPost?Operation::post:step==kClose?Operation::close:
        step==kClosePost?Operation::close_post:step==kCloseQuery?Operation::close_query:Operation::query;
    q.result.operation=q.operation==Operation::open?"open":q.operation==Operation::post?"post":
        q.operation==Operation::close?"close":q.operation==Operation::close_post?"close_post":
        q.operation==Operation::close_query?"close_query":"query";
    q.result.read_only=!Action(q.operation);q.result.current=Metadata(q);
    if(!Parse(payload,q)){failure="inventory_request_binding_invalid";return false;}
    if(!ck3_12003::VerifyPlayerInventoryWindowSources12004(q.source_inventory_sha,game.descriptor(),q.sources_verified,failure)||!q.sources_verified)return false;
    state.active=std::move(value);
    const auto executor=Action(q.operation)?&ExecuteOpen:&ExecuteRead;
    if(TrySubmitMainThreadQueryV1(mailbox,executor,&q,q.ticket)!=MainThreadQuerySubmitResultV1::submitted){state.active.reset();failure="inventory_mailbox_permission_unavailable";return false;}
    if(WaitForMainThreadQueryV1(mailbox,q.ticket,8'000)!=MainThreadQueryWaitResultV1::completed){Reclaim(state);failure="inventory_ticket_pending_or_unknown_no_replay";return false;}
    if(!q.completed){Reclaim(state);failure="inventory_owner_guard_rejected";return false;}
    if(Post(q.operation)&&!q.result.intent_found){Reclaim(state);failure="inventory_intent_not_found_do_not_replay";return false;}
    game::Snapshot after{};bool sources_after=false;std::string source_reason;
    const bool closed=game.read_snapshot(after)&&after==current&&
        ck3_12003::VerifyPlayerInventoryWindowSources12004(q.source_inventory_sha,game.descriptor(),sources_after,source_reason)&&sources_after;
    if(!closed)
      Invalidate(q,"inventory_worker_current_frame_or_sources_changed");
    else if(Post(q.operation)&&q.result.desired_window_observed) {
      const bool resolved=CloseDomain(q.operation)?state.close_ledger.Reconcile(q.original_sequence,q.result.after):
          state.ledger.Reconcile(q.original_sequence,q.result.after);
      if(!resolved)Invalidate(q,"inventory_original_intent_resolution_unavailable");
    }
    response=Envelope(q,request_id,step);
    if(!Reclaim(state)){response.clear();failure="inventory_reclaim_unknown_no_replay";return false;}
    if(response.empty())failure="inventory_serializer_rejected";
    return !response.empty();
  }catch(...){failure="inventory_transport_exception_no_replay";return false;}
}
}
