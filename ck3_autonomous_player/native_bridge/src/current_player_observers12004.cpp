#include "current_player_observers12004.hpp"
#include "artifact_personal_use_ledger12004.hpp"
#include "ghw_permission_observer/ghw_variable_bindings_12004.hpp"
#include "ghw_permission_observer/ghw_loaded_source_pins_12004.inc"
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12004_religion_bindings.hpp"
#include "xar_bridge/ingame_ui_navigation_v1.hpp"
#include "xar_bridge/protocol.hpp"
#include <windows.h>
#include <array>
#include <memory>
#include <limits>
#include <mutex>

namespace xar::ck3_12004::current_player_observers {
namespace {
namespace item=artifact_personal_use;
namespace vars=religion::ghw_variables_candidate;
namespace links=religion::ghw_links_candidate;
using namespace ck3_11906;
enum class Kind { artifact_read,artifact_action,artifact_post,ghw_read };
struct Query;
struct ProcessState {
  std::mutex worker_lock;
  std::unique_ptr<Query> active;
  ArtifactIntentLedger12004 intents;
};
struct Query {
  MainThreadQueryMailboxV1* mailbox=nullptr;
  MainThreadQueryTicketV1 ticket{};
  const game::GameAdapter* game=nullptr;
  game::Snapshot expected{};
  std::uint64_t revision=0,generation=0,post_intent_sequence=0;
  std::uintptr_t base=0;
  std::uint32_t pid=0,artifact=item::absent;
  Kind kind=Kind::artifact_read;
  bool policy_positive=false,completed=false,frame_changed=false;
  std::uint32_t invocations=0;
  ProcessState* state=nullptr;
  item::Request request{};
  item::Observation artifact_observation{};
  ArtifactActionObservation action{};
  GhwObservation ghw{};
  std::string failure;
};
ProcessState& State(){static ProcessState state;return state;}
struct Context {
  Query* query=nullptr;
  MainThreadExecutionStampV1 stamp{};
  religion::ContextBindings religion_bindings{};
};
bool Memory(void*,std::uintptr_t address,void* output,std::size_t bytes) noexcept {
  SIZE_T got=0;
  return address&&output&&bytes&&ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<const void*>(address),output,bytes,&got)&&got==bytes;
}
bool Current(Context& c,game::Snapshot& current) noexcept {
  const auto& q=*c.query;std::uint8_t tls=0;
  return q.mailbox&&q.game&&q.pid==GetCurrentProcessId()&&q.generation&&q.revision&&
      q.game->enabled()&&game::IsCk3_12004Descriptor(q.game->descriptor())&&
      q.base==reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr))&&
      !q.mailbox->stop_requested.load(std::memory_order_acquire)&&
      q.mailbox->state.load(std::memory_order_acquire)==MainThreadQueryMailboxStateV1::executing&&
      IsIngameUiPausedOwnerStampV1(*q.mailbox,c.stamp,GetCurrentThreadId())&&
      Memory(nullptr,c.stamp.tls_initialized_flag_address,&tls,sizeof(tls))&&tls==1&&
      q.game->read_snapshot(current)&&current==q.expected&&current.paused&&current.map_ready&&
      current.has_played_character&&current.played_character_alive&&current.played_character_id>0&&
      current.date_raw==c.stamp.date_raw;
}
bool ArtifactFrame(void* opaque,item::Frame& output) noexcept {
  auto& c=*static_cast<Context*>(opaque);auto& q=*c.query;game::Snapshot current{};
  if(!Current(c,current))return false;
  if(q.kind==Kind::artifact_action) {
    if(current.has_active_event||current.has_pending_character_interaction||!q.policy_positive)return false;
    const auto env=BindZhongguoScoreboardNativeEnvironmentV1(q.base,true,GuiAbiRevisionV1::crozier12004,kExecutableSha256);
    IngameUiGuiOwnerBindingV1 binding{};IngameUiModalAdmissionV1 modal{};
    if(!ReadIngameUiGuiOwnerBindingV1(env,binding)||
       !ReadIngameUiModalActionAdmissionV1(env,binding,modal))return false;
  }
  // Frame.owner is the native window outer owner (current Jomini), as in
  // ReadPresentationOuterOwner12004. The GUI lookup owner above belongs to
  // a separate singleton chain; no cross-type pointer equality is inferred.
  output={q.revision,c.stamp.pump_epoch,q.generation,current.date_raw,q.pid,
          static_cast<std::uint32_t>(current.played_character_id),c.stamp.jomini_state,
          true,true,true,true,true};
  return true;
}
bool Claim(void* opaque,const item::Frame& frame,const item::Request& request,
           const item::Observation& before,const item::Witness& witness) noexcept {
  auto& c=*static_cast<Context*>(opaque);auto& q=*c.query;item::Frame actual{};
  if(!q.state||q.kind!=Kind::artifact_action||!q.policy_positive||!ArtifactFrame(opaque,actual)||actual!=frame||
      !before.available||before.frame!=frame||before.artifact_id!=request.artifact_id||
      !witness.actor||!witness.artifact||witness.character_owner!=frame.actor_id||
      witness.site_owner!=item::absent||request.request_sequence!=q.ticket.sequence)return false;
  return q.state->intents.Claim(frame,request,before,witness);
}
void Reconcile(Query& q,const item::Observation& after) {
  if(!q.state)return;
  item::Request request{};item::Result result{};bool desired=false;
  const bool found=q.state->intents.ObserveAfter(after,
      q.kind==Kind::artifact_post?q.post_intent_sequence:0,request,result,desired);
  if(q.kind==Kind::artifact_post&&found) {
    q.action.intent_found=true;q.action.request=request;q.action.result=result;
    q.action.desired_inventory_state_observed=desired;
    q.action.post_status=desired?"desired_inventory_state_observed":result.needs_recovery?
        "intent_pending_or_unknown":"intent_previously_resolved_current_state_not_observed";
  }
}
bool ReligionFrameGuarded(Context& c,ck3_12002::religion::Context& observed,void*& faith,void*& religion_object) noexcept {
#if defined(_WIN32)&&defined(_MSC_VER)
  __try {
#endif
    auto& b=c.religion_bindings;
    if(!religion::ReadPlayedReligionContext12004(b,c.stamp.pump_epoch,observed)||!observed.available||
       !observed.faith_id||!observed.religion_id||*observed.faith_id==0xffffffffU||*observed.religion_id==0xffffffffU||
       !b.character_faith||!b.faith_religion)return false;
    void* actor=ck3_12004::ResolveCoreCharacter(b.core,observed.played_character_id);
    faith=actor?b.character_faith(actor):nullptr;
    religion_object=faith?b.faith_religion(faith):nullptr;
    return faith&&religion_object;
#if defined(_WIN32)&&defined(_MSC_VER)
  } __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#endif
}
bool GhwFrame(void* opaque,vars::BoundFrame& out) noexcept {
  auto& c=*static_cast<Context*>(opaque);game::Snapshot current{};
  ck3_12002::religion::Context observed{};void* faith=nullptr;void* religion_object=nullptr;
  if(!Current(c,current)||!ReligionFrameGuarded(c,observed,faith,religion_object)||
      observed.played_character_id!=current.played_character_id||observed.date_raw!=current.date_raw)return false;
  out={c.stamp.pump_epoch,current.date_raw,current.played_character_id,*observed.faith_id,*observed.religion_id,
       reinterpret_cast<std::uintptr_t>(faith),reinterpret_cast<std::uintptr_t>(religion_object),true,true,true};
  return true;
}
bool LoadedGhwPins(Context& c) noexcept {
  namespace pins=religion::ghw_candidate_loaded_pins;
  for(const auto& pin:pins::kPins) {
    std::array<std::uint8_t,512> actual{};
    if(!pin.count||pin.count>actual.size()||pin.rva>(std::numeric_limits<std::uintptr_t>::max)()-c.query->base||
        !Memory(nullptr,c.query->base+pin.rva,actual.data(),pin.count))return false;
    for(std::size_t i=0;i<pin.count;++i)if(actual[i]!=pin.bytes[i])return false;
  }
  for(auto rva:pins::kObservedSlotRvas) {
    std::uintptr_t pointer=0;
    if(rva>(std::numeric_limits<std::uintptr_t>::max)()-c.query->base||!Memory(nullptr,c.query->base+rva,&pointer,sizeof(pointer)))return false;
    // Readable null does not prove variable absence; each actual leaf decides.
  }
  return true;
}
bool GhwVariablesGuarded(const vars::Access& access,vars::Observation& out,bool& fault) noexcept {
  fault=false;
#if defined(_WIN32)&&defined(_MSC_VER)
  __try {
#endif
    return vars::ReadCurrentPlayerGhwVariables12004(access,out);
#if defined(_WIN32)&&defined(_MSC_VER)
  } __except(EXCEPTION_EXECUTE_HANDLER){fault=true;return false;}
#endif
}
void Invalidate(Query& q,const char* reason) {
  const auto frame=q.artifact_observation.frame;
  q.artifact_observation={};q.artifact_observation.frame=frame;q.artifact_observation.artifact_id=q.artifact;
  q.artifact_observation.unavailable_reason=reason;
  const auto epoch=q.ghw.capture_epoch;
  q.ghw={};q.ghw.capture_epoch=epoch;q.ghw.date_raw=q.expected.date_raw;
  q.ghw.played_character_id=q.expected.played_character_id;q.ghw.unavailable_reason=reason;
  q.action.available=false;q.action.unavailable_reason=reason;
  q.action.desired_inventory_state_observed=false;
  if(q.kind==Kind::artifact_post) {
    q.action.after=q.artifact_observation;
    q.action.post_status="intent_pending_or_unknown";
  }
  if(q.action.result.once_intent_consumed)q.action.result.needs_recovery=true;
}
bool Execute(void* opaque,const MainThreadExecutionStampV1& stamp,Kind kind) noexcept {
  auto* query=static_cast<Query*>(opaque);
  if(!query||query->kind!=kind||!query->mailbox||!query->ticket.sequence||query->invocations||
      query->mailbox->published_sequence.load(std::memory_order_acquire)!=query->ticket.sequence||
      query->mailbox->executor_context!=query||query->mailbox->failure_flags.load(std::memory_order_acquire))return false;
  auto& q=*query;
  const auto expected_executor=kind==Kind::ghw_read?&ExecuteGhwPermissionsRead12004:
      kind==Kind::artifact_action?&ExecuteArtifactPersonalAction12004:&ExecuteArtifactPersonalRead12004;
  if(q.mailbox->executor!=expected_executor)return false;
  try {
    ++q.invocations;Context c{&q,stamp,{}};game::Snapshot current{};
    q.artifact_observation.frame={q.revision,stamp.pump_epoch,q.generation,q.expected.date_raw,q.pid,
      static_cast<std::uint32_t>(q.expected.played_character_id),stamp.jomini_state,false,false,true,true,true};
    q.artifact_observation.artifact_id=q.artifact;
    q.action.played_character_id=static_cast<std::uint32_t>(q.expected.played_character_id);
    q.action.request=q.request;q.action.read_only=kind==Kind::artifact_post;
    if(!Current(c,current)){Invalidate(q,"published_owner_frame_changed");q.completed=true;return true;}
    if(kind==Kind::ghw_read) {
      c.religion_bindings=religion::BindReligionContextImage12004(q.base,kExecutableSha256);
      vars::BoundFrame first{},second{};
      q.ghw.capture_epoch=stamp.pump_epoch;q.ghw.date_raw=current.date_raw;q.ghw.played_character_id=current.played_character_id;
      if(!GhwFrame(&c,first)||!LoadedGhwPins(c)){Invalidate(q,"ghw_current_identity_or_loaded_operand_pins_unavailable");}
      else {
        vars::BindingState bindings{};
        const auto access=vars::BindGhwVariableAccess12004(bindings,q.base,kExecutableSha256,&c,&Memory,&GhwFrame);
        bool fault=false;(void)GhwVariablesGuarded(access,q.ghw.variables,fault);
        if(!fault)(void)links::ReadGhwObjectLinks12004({&Memory,&c,q.base,first.faith_object,kExecutableSha256},q.ghw.object_links);
        const auto& v=q.ghw.variables;
        const bool same_leaf_frame=v.frame_verified&&v.stable_two_pass&&v.capture_epoch==first.capture_epoch&&v.date_raw==first.date_raw&&
            v.played_character_id==first.played_character_id&&v.faith_id==first.faith_id&&v.religion_id==first.religion_id;
        if(fault||!same_leaf_frame||!GhwFrame(&c,second)||first!=second||!LoadedGhwPins(c))Invalidate(q,"ghw_outer_binding_changed_or_native_fault");
        else {q.ghw.available=true;q.ghw.frame_verified=true;q.ghw.loaded_source_pins_verified=true;
          q.ghw.faith_id=first.faith_id;q.ghw.religion_id=first.religion_id;q.ghw.unavailable_reason.clear();}
      }
    } else {
      auto env=item::BindArtifactPersonalUseCallbacks12004(religion::relic_permissions::BindHolySiteRelicPermissionsImage12004(q.base,kExecutableSha256),kExecutableSha256);
      env.enabled=true;env.context=&c;env.frame=&ArtifactFrame;env.claim_once=&Claim;
      item::Frame frame{};
      if(!ArtifactFrame(&c,frame))Invalidate(q,"artifact_current_owner_or_modal_admission_unavailable");
      else {
        (void)item::ReadArtifactPersonalUse12004(env,frame,q.artifact,q.artifact_observation);
        if(kind==Kind::artifact_action) {
          q.request.request_sequence=q.ticket.sequence;q.action.request=q.request;
          env.actions_enabled=q.policy_positive;
          q.action.result=item::SubmitArtifactPersonalUse12004(env,frame,q.request);
          if(q.action.result.before.artifact_id==item::absent)q.action.result.before=q.artifact_observation;
          q.action.available=true;q.action.unavailable_reason.clear();q.action.intent_found=q.action.result.once_intent_consumed;
          if(q.action.result.once_intent_consumed) {
            q.state->intents.RecordResult(frame,q.request,q.action.result);
          }
        } else {
          if(kind==Kind::artifact_post){q.action.after_attempted=true;q.action.after=q.artifact_observation;q.action.available=true;q.action.unavailable_reason.clear();}
        }
        item::Frame later{};
        if(!ArtifactFrame(&c,later)||later!=frame)Invalidate(q,"artifact_owner_frame_changed_after_read_or_dispatch");
        else if(kind!=Kind::artifact_action)Reconcile(q,q.artifact_observation);
      }
    }
    q.completed=true;return true;
  } catch(...) {Invalidate(q,"current_player_observer_exception_no_retry");q.completed=true;return true;}
}
bool UInt(std::string_view json,std::string_view key,std::uint64_t& value){return bridge::JsonUnsignedField(json,key,value);}
bool Has(std::string_view json,std::string_view key){return json.find('"'+std::string(key)+'"')!=std::string_view::npos;}
bool Parse(std::string_view payload,Query& q) {
  std::uint64_t revision=0,snapshot_revision=0,date=0,actor=0,pid=0,generation=0,artifact=0;
  if(!UInt(payload,"expected_revision",revision)||revision!=q.revision||
     !UInt(payload,"expected_snapshot_revision",snapshot_revision)||snapshot_revision!=q.revision||
     !UInt(payload,"expected_date_raw",date)||date!=static_cast<std::uint64_t>(q.expected.date_raw)||
     !UInt(payload,"expected_actor_character_id",actor)||actor!=static_cast<std::uint64_t>(q.expected.played_character_id)||
     !UInt(payload,"expected_game_pid",pid)||pid!=q.pid||
     !UInt(payload,"expected_connection_generation",generation)||generation!=q.generation)return false;
  if(q.kind==Kind::ghw_read)return !Has(payload,"artifact_id")&&!Has(payload,"policy_positive");
  if(!UInt(payload,"artifact_id",artifact)||artifact>=item::absent)return false;
  q.artifact=static_cast<std::uint32_t>(artifact);q.request.artifact_id=q.artifact;
  if(q.kind==Kind::artifact_action) {
    std::uint64_t slot=0,replacement=0;bool empty=false;
    if(!bridge::JsonBooleanField(payload,"policy_positive",q.policy_positive)||!q.policy_positive||
       !bridge::JsonBooleanField(payload,"desired_equipped",q.request.desired_equipped)||
       !UInt(payload,"expected_slot_index",slot)||slot>=64||
       !bridge::JsonBooleanField(payload,"expected_replacing_empty",empty))return false;
    if(empty){if(Has(payload,"expected_replacing_artifact_id"))return false;}
    else if(!UInt(payload,"expected_replacing_artifact_id",replacement)||replacement>=item::absent||!q.request.desired_equipped)return false;
    q.request.expected_slot_index=static_cast<std::uint32_t>(slot);
    q.request.expected_replacing_artifact_id=empty?item::absent:static_cast<std::uint32_t>(replacement);
  } else {
    for(auto key:{"desired_equipped","expected_slot_index","expected_replacing_empty","expected_replacing_artifact_id","policy_positive","request_sequence"})if(Has(payload,key))return false;
    if(q.kind==Kind::artifact_post&&(!UInt(payload,"expected_intent_sequence",q.post_intent_sequence)||!q.post_intent_sequence))return false;
  }
  return !Has(payload,"request_sequence");
}
bool Reclaim(ProcessState& s) {
  if(!s.active)return true;
  if(ReclaimMainThreadQueryV1(*s.active->mailbox,s.active->ticket)!=MainThreadQueryReclaimResultV1::reclaimed)return false;
  s.active.reset();return true;
}
std::string JsonText(std::string_view input) {
  std::string out="\"";constexpr char hex[]="0123456789abcdef";
  for(unsigned char c:input){if(c=='"'||c=='\\'){out+='\\';out+=static_cast<char>(c);}else if(c<32){out+="\\u00";out+=hex[c>>4];out+=hex[c&15];}else out+=static_cast<char>(c);}
  return out+'"';
}
std::string Command(const Query& q,std::string_view request_id,std::string_view step) {
  const bool ghw=q.kind==Kind::ghw_read;
  const bool action=q.kind==Kind::artifact_action||q.kind==Kind::artifact_post;
  const bool read=q.kind!=Kind::artifact_action;
  const std::string body=ghw?SerializeGhwPermissions12004(q.ghw):action?SerializeArtifactPersonalAction12004(q.action):SerializeArtifactPersonalUse12004(q.artifact_observation);
  if(body.empty())return {};
  const bool available=ghw?q.ghw.available:action?q.action.available:q.artifact_observation.available;
  const auto domain=ghw?"player_ghw_permissions":action?"player_artifact_personal_use_action_v1":"player_artifact_personal_use_v1";
  const auto key=ghw?"player_ghw_permissions":action?"player_artifact_personal_use_action":"player_artifact_personal_use";
  const auto backend=ghw?"ck3-1.20.0.4-native-player-ghw-permissions-v1-private":action?
      "ck3-1.20.0.4-native-player-artifact-personal-use-action-v1-private":"ck3-1.20.0.4-native-player-artifact-personal-use-v1";
  std::string out="{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":"+JsonText(request_id)+",\"ok\":true,\"result\":{\"step\":"+JsonText(step);
  out+=",\"accepted\":true,\"private_build\":true,\"read_only\":";out+=read?"true":"false";
  out+=",\"advertised\":false,\"game_version\":\"1.20.0.4\",\"executable_sha256\":"+JsonText(kExecutableSha256);
  out+=",\"backend_id\":"+JsonText(backend)+",\"domain_key\":"+JsonText(domain)+",\"snapshot_revision\":"+std::to_string(q.revision);
  out+=",\"date_raw\":"+std::to_string(q.expected.date_raw)+",\"status\":"+JsonText(available?"observed":"unavailable")+','+JsonText(key)+':'+body+"}}";
  return out;
}
} // namespace
bool IsCurrentPlayerObserverStep12004(std::string_view step) noexcept {
#if defined(XAR_CK3_ENABLE_G2_PLAYER_ARTIFACT_PERSONAL_USE_READONLY_V1)
  if(step==artifact_step)return true;
#endif
#if defined(XAR_CK3_ENABLE_ARTIFACT_PERSONAL_USE_PRIVATE_V1)
  if(step==artifact_submit_step||step==artifact_post_step)return true;
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_GHW_PERMISSIONS_READONLY_V1)
  if(step==ghw_step)return true;
#endif
  (void)step;return false;
}
bool ExecuteArtifactPersonalRead12004(void* q,const MainThreadExecutionStampV1& s) noexcept {
  auto* query=static_cast<Query*>(q);return query&&Execute(q,s,query->kind==Kind::artifact_post?Kind::artifact_post:Kind::artifact_read);
}
bool ExecuteArtifactPersonalAction12004(void* q,const MainThreadExecutionStampV1& s) noexcept {return Execute(q,s,Kind::artifact_action);}
bool ExecuteGhwPermissionsRead12004(void* q,const MainThreadExecutionStampV1& s) noexcept {return Execute(q,s,Kind::ghw_read);}
bool HandleCurrentPlayerObserver12004(const game::GameAdapter& game,MainThreadQueryMailboxV1& mailbox,
    const game::Snapshot* published,std::uint64_t revision,std::uint64_t generation,
    std::string_view step,std::string_view payload,std::string_view request_id,std::string& serialized,std::string& failure) noexcept {
  serialized.clear();failure.clear();
  if(!IsCurrentPlayerObserverStep12004(step))return false;
  try {
    game::Snapshot current{};
    if(!game.enabled()||!game::IsCk3_12004Descriptor(game.descriptor())||!revision||!generation||!published||
        !game.read_snapshot(current)||current!=*published||!current.paused||!current.map_ready||
        !current.has_played_character||!current.played_character_alive||current.played_character_id<=0){failure="current_player_observer_frame_unavailable";return false;}
    auto& state=State();std::lock_guard lock(state.worker_lock);
    if(!Reclaim(state)){failure="previous_observer_ticket_still_owned_no_retry";return false;}
    auto query=std::make_unique<Query>();auto& q=*query;q.mailbox=&mailbox;q.game=&game;q.expected=current;
    q.revision=revision;q.generation=generation;q.pid=GetCurrentProcessId();q.state=&state;
    q.base=reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
    q.kind=step==ghw_step?Kind::ghw_read:step==artifact_submit_step?Kind::artifact_action:step==artifact_post_step?Kind::artifact_post:Kind::artifact_read;
    if(!Parse(payload,q)){failure="current_player_observer_request_binding_invalid";return false;}
    state.active=std::move(query);
    const auto executor=q.kind==Kind::ghw_read?&ExecuteGhwPermissionsRead12004:q.kind==Kind::artifact_action?&ExecuteArtifactPersonalAction12004:&ExecuteArtifactPersonalRead12004;
    if(TrySubmitMainThreadQueryV1(mailbox,executor,&q,q.ticket)!=MainThreadQuerySubmitResultV1::submitted){state.active.reset();failure="observer_mailbox_permission_or_owner_unavailable";return false;}
    const auto waited=WaitForMainThreadQueryV1(mailbox,q.ticket,8'000);
    if(waited!=MainThreadQueryWaitResultV1::completed){Reclaim(state);failure="observer_pending_or_unknown_no_retry";return false;}
    if(!q.completed){Reclaim(state);failure="observer_owner_guard_rejected";return false;}
    if(q.kind==Kind::artifact_post&&!q.action.intent_found){Reclaim(state);failure="artifact_intent_not_found_do_not_replay";return false;}
    game::Snapshot after{};
    if(!game.read_snapshot(after)||after!=current)Invalidate(q,"observer_worker_completion_frame_changed");
    serialized=Command(q,request_id,step);
    if(!Reclaim(state)){serialized.clear();failure="observer_reclaim_unknown_no_retry";return false;}
    if(serialized.empty())failure="observer_typed_serializer_rejected";
    return !serialized.empty();
  } catch(...) {failure="current_player_observer_transport_exception_no_retry";return false;}
}
} // namespace xar::ck3_12004::current_player_observers
