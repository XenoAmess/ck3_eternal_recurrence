#include "xar_bridge/character_skill_effect12004_mailbox.hpp"
#include "xar_bridge/character_skill_effect12004_native.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/protocol.hpp"
#include <windows.h>
#include <array>
#include <limits>

namespace xar::ck3_12004::character_skill_effects {
namespace {
struct Context { Query *query=nullptr;DWORD owner=0; };
[[maybe_unused]] bool Snapshot(void *opaque,game::Snapshot &out) noexcept {
  return opaque!=nullptr&&static_cast<const game::GameAdapter *>(opaque)->read_snapshot(out);
}
bool CurrentFrame(void *opaque,core::Frame &out) noexcept {
  const auto &c=*static_cast<Context *>(opaque);const auto &q=*c.query;
  game::Snapshot actual{};
  if(GetCurrentThreadId()!=c.owner||q.game_pid!=GetCurrentProcessId()||
      q.connection_generation==0||q.mailbox==nullptr||
      q.mailbox->stop_requested.load(std::memory_order_acquire)||
      q.read_snapshot==nullptr||!q.read_snapshot(q.native_context,actual)||
      actual!=q.expected_snapshot||!actual.paused||!actual.map_ready||
      !actual.has_played_character||!actual.played_character_alive||actual.played_character_id<=0)return false;
  out={q.expected_revision,actual.date_raw,static_cast<std::uint32_t>(actual.played_character_id),true,true,true};return true;
}

void Quote(std::string &out,std::string_view text){
  constexpr char hex[]="0123456789abcdef";out+='"';
  for(const unsigned char c:text){if(c=='"'||c=='\\'){out+='\\';out+=static_cast<char>(c);}else if(c<32){out+="\\u00";out+=hex[c>>4];out+=hex[c&15];}else out+=static_cast<char>(c);}out+='"';
}
[[maybe_unused]] std::string Envelope(const Query &q,std::string_view request_id,std::string_view domain){
  std::string out="{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":";Quote(out,request_id);
  out+=",\"ok\":true,\"result\":{\"step\":";Quote(out,q.knight_query?kKnightStep:kStep);
  out+=",\"accepted\":true,\"status\":";
  Quote(out,(q.knight_query?q.knight_observation.available:q.observation.available)?"available":"unavailable");
  out+=",\"private_build\":true,\"advertised\":false,\"read_only\":true,\"snapshot_revision\":"+std::to_string(q.expected_revision);
  out+=",\"date_raw\":"+std::to_string(q.expected_snapshot.date_raw)+",\"game_pid\":"+std::to_string(q.game_pid);
  out+=",\"connection_generation\":"+std::to_string(q.connection_generation)+",\"game_version\":\"1.20.0.4\",\"executable_sha256\":";
  Quote(out,core::kExeSha);out+=",\"domain_key\":";Quote(out,q.knight_query?kKnightDomain:kDomain);
  out+=q.knight_query?",\"character_knight_effectiveness_v1\":":",\"character_skill_effects_v1\":";
  out+=domain;out+=",\"backend_id\":\"native-headless\"}}";return out;
}
} // namespace
bool Execute(void *opaque,const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  using namespace ck3_11906;auto *q=static_cast<Query *>(opaque);
  if(q==nullptr||q->mailbox==nullptr||q->ticket.sequence==0||q->expected_revision==0||q->invocations!=0||
      q->game_pid!=GetCurrentProcessId()||q->connection_generation==0||stamp.pump_epoch==0||stamp.thread_id==0||
      !stamp.paused||stamp.tls_initialized_flag_address==0||stamp.tls_initialized!=1||stamp.tls_context==0||
      stamp.tls_main_thread_marker!=1||stamp.jomini_state==0||stamp.game_state==0||GetCurrentThreadId()!=stamp.thread_id)return false;
  auto &m=*q->mailbox;
  if(m.state.load(std::memory_order_acquire)!=MainThreadQueryMailboxStateV1::executing||
      m.stop_requested.load(std::memory_order_acquire)||m.failure_flags.load(std::memory_order_acquire)!=0||
      m.published_sequence.load(std::memory_order_acquire)!=q->ticket.sequence||
      m.owner_thread_id.load(std::memory_order_acquire)!=stamp.thread_id||
      m.paused_owner_verified_pump_epochs.load(std::memory_order_acquire)<kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs||
      m.executor!=&Execute||m.executor_context!=q)return false;
  try{
    ++q->invocations;Context context{q,stamp.thread_id};core::Frame frame{};
    if(!CurrentFrame(&context,frame)||frame.date_raw!=stamp.date_raw){q->frame_changed=true;q->failure="actor_effects_published_frame_changed";}
    else{
      core::NativeContext native{};native.enabled=q->enabled;native.module_base=q->module_base;
      native.executable_sha256=q->executable_sha256;native.owner_thread_id=stamp.thread_id;native.expected=frame;
      native.requested_character_id=q->character_id;native.snapshot_context=&context;native.snapshot_frame=&CurrentFrame;
      if(q->knight_query){
        const auto env=core::BindKnightNative(native);
        (void)core::ReadKnightEffectiveness(env,core::KnightRequest{frame,q->character_id},q->knight_observation);
        if(q->knight_observation.available&&
            (native.breakdown_calls!=2||native.string_destroy_calls!=2)){
          q->knight_observation={};q->knight_observation.frame=frame;
          q->knight_observation.character_id=q->character_id;
          q->knight_observation.unavailable_reason="native_knight_cleanup_count_unverified";
        }
        if(!q->knight_observation.available&&native.failure!=nullptr&&*native.failure!='\0')
          q->knight_observation.unavailable_reason=native.failure;
      }else{
        const auto env=core::BindNative(native);
        (void)core::Read(env,core::Request{frame,q->character_id,q->skill},q->observation);
        if(!q->observation.available&&native.failure!=nullptr&&*native.failure!='\0')q->observation.unavailable_reason=native.failure;
      }
      core::Frame after{};if(!CurrentFrame(&context,after)||after!=frame){q->frame_changed=true;q->failure="actor_effects_post_frame_changed";}
    }
    q->completed=true;return true;
  }catch(...){q->failure="actor_effects_native_exception";q->completed=true;return true;}
}
bool Handle(const game::GameAdapter &adapter,ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot *published,std::uint64_t revision,std::uint64_t generation,
    std::string_view payload,std::string_view request_id,std::string &wire,std::string &failure) noexcept {
  wire.clear();failure.clear();
#if !defined(XAR_CK3_ENABLE_CHARACTER_SKILL_EFFECTS12004_PRIVATE_QUERY_V1)
  (void)adapter;(void)mailbox;(void)published;(void)revision;(void)generation;(void)payload;(void)request_id;
  failure="character_skill_effects_private_query_disabled";return false;
#else
  using namespace ck3_11906;
  try{
    game::Snapshot current{};std::uint32_t target=0xFFFFFFFFU;std::int32_t skill=-1;
    std::string requested_step;
    if(!bridge::JsonStringField(payload,"step",requested_step,128)||!IsStep(requested_step)){
      failure="character_effects_fixed_step_invalid";return false;
    }
    const bool knight=requested_step==kKnightStep;
    if(!adapter.enabled()||!game::IsCk3_12004Descriptor(adapter.descriptor())||revision==0||generation==0||
        published==nullptr||!adapter.read_snapshot(current)||current!=*published||!current.paused||!current.map_ready||
        !current.has_played_character||!current.played_character_alive||current.played_character_id<=0||
        !(knight?ParseKnightRequest(payload,current,revision,generation,target):
                  ParseRequest(payload,current,revision,generation,target,skill))){failure="character_effects_request_or_binding_invalid";return false;}
    Query q{};q.mailbox=&mailbox;q.enabled=true;q.module_base=reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
    q.executable_sha256=adapter.descriptor().executable_sha256;q.native_context=const_cast<game::GameAdapter *>(&adapter);q.read_snapshot=&Snapshot;
    q.expected_snapshot=current;q.expected_revision=revision;q.connection_generation=generation;q.game_pid=GetCurrentProcessId();q.character_id=target;q.skill=skill;q.knight_query=knight;
    if(TrySubmitMainThreadQueryV1(mailbox,&Execute,&q,q.ticket)!=MainThreadQuerySubmitResultV1::submitted){failure="character_skill_effects_owner_executor_unavailable";return false;}
    auto wait=WaitForMainThreadQueryV1(mailbox,q.ticket,8000);
    while(wait==MainThreadQueryWaitResultV1::timeout_executor_already_running)wait=WaitForMainThreadQueryV1(mailbox,q.ticket,2000);
    if(wait!=MainThreadQueryWaitResultV1::completed||!q.completed){(void)ReclaimMainThreadQueryV1(mailbox,q.ticket);failure="character_skill_effects_owner_executor_incomplete";return false;}
    game::Snapshot after{};const bool stable=!q.frame_changed&&adapter.read_snapshot(after)&&after==current;
    const auto domain=stable?(q.knight_query?SerializeKnight(q):Serialize(q)):std::string{};
    const bool reclaimed=ReclaimMainThreadQueryV1(mailbox,q.ticket)==MainThreadQueryReclaimResultV1::reclaimed;
    if(!stable||domain.empty()||!reclaimed){failure=q.failure.empty()?"character_skill_effects_frame_serialize_or_reclaim_failed":q.failure;return false;}
    wire=Envelope(q,request_id,domain);return true;
  }catch(...){failure="character_skill_effects_handler_exception";return false;}
#endif
}
} // namespace xar::ck3_12004::character_skill_effects
