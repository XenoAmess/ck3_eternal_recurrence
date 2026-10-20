#include "xar_bridge/native_time_command_observer_12004.hpp"
#include <algorithm>
#include <cstring>
#include <limits>
namespace xar::ck3_12004::time_observer31 {
namespace {
struct Entry { Ticket ticket{}; bool alive{}; };
struct State {
 std::atomic_flag lock=ATOMIC_FLAG_INIT;
 std::atomic<std::uint32_t> gaps{};
 std::atomic<std::uint64_t> lost{},connections{},invocations{},identity_epoch{1};
 std::uint64_t generations{},sequence{};
 std::array<Entry,kRegistry> entries{};
 std::array<Event,kEvents> events{};
};
State state{};
static_assert(sizeof(State)<=65536);
thread_local Key request_key{};
thread_local const void* bridge_source{};
struct Guard {
 bool owned{!state.lock.test_and_set(std::memory_order_acquire)};
 Guard() noexcept { if(!owned) {state.lost.fetch_add(1,std::memory_order_relaxed);
   state.gaps.fetch_or(busy,std::memory_order_relaxed);
   state.identity_epoch.fetch_add(1,std::memory_order_acq_rel);} }
 ~Guard() noexcept {if(owned)state.lock.clear(std::memory_order_release);}
};
Entry* Find(const void* p) noexcept {
 for(auto& e:state.entries) if(e.alive&&
     e.ticket.identity_epoch==state.identity_epoch.load(std::memory_order_acquire)&&e.ticket.token.address==
     reinterpret_cast<std::uintptr_t>(p))return &e;
 return nullptr;
}
void Append(Event e) noexcept {
 if(e.identity_epoch&&e.identity_epoch!=state.identity_epoch.load(std::memory_order_acquire)) {
  e.key.valid=0;e.qualified=0;
 }
 e.sequence=++state.sequence;
 if(e.sequence>kEvents)state.gaps.fetch_or(event_overwrite,std::memory_order_relaxed);
 state.events[(e.sequence-1)%kEvents]=e;
}
Event Make(Kind kind,const Ticket& t,std::uintptr_t caller,std::uintptr_t aux,
           bool qualified,bool accepted) noexcept {
 Event e{};e.kind=kind;e.token=t.token;e.parent=t.parent;e.key=t.key;e.role=t.role;
 e.invocation=t.invocation;e.identity_epoch=t.identity_epoch;
 if(t.identity_epoch && t.identity_epoch!=state.identity_epoch.load(std::memory_order_acquire)) {
  e.key.valid=0;e.qualified=0;
 }
 e.qpc=Clock();e.thread=Thread();e.caller=caller;e.aux=aux;
 e.qualified=(qualified&&(!t.identity_epoch||t.identity_epoch==state.identity_epoch.load(std::memory_order_acquire)))?1:0;
 e.accepted=accepted?1:0;return e;
}
bool Simple(std::string_view id) noexcept {
 if(id.empty()||id.size()>=kIdBytes)return false;
 for(unsigned char c:id)if(!((c>='A'&&c<='Z')||(c>='a'&&c<='z')||
   (c>='0'&&c<='9')||c=='_'||c=='-'||c=='.'||c==':'))return false;
 return true;
}
void Number(std::string& s,std::string_view name,std::uint64_t value,bool comma=true) {
 s+='"';s+=name;s+="\":";s+=std::to_string(value);if(comma)s+=',';
}
void TokenJson(std::string& s,std::string_view name,Token t) {
 s+='"';s+=name;s+="\":{";Number(s,"pointer",t.address);
 Number(s,"incarnation",t.incarnation,false);s+="},";
}
}
void GapFlag(std::uint32_t bit) noexcept {state.gaps.fetch_or(bit,std::memory_order_relaxed);}
void InvalidateIdentity(std::uint32_t bit) noexcept {
 GapFlag(bit);state.identity_epoch.fetch_add(1,std::memory_order_acq_rel);
}
std::uint64_t BeginConnection() noexcept {
 return state.connections.fetch_add(1,std::memory_order_relaxed)+1;
}
RequestScope::RequestScope(std::uint64_t connection,std::string_view id,bool paused) noexcept
 :previous(request_key) {
 request_key={};
 if(!Attached())return;
 if(!Simple(id)) {GapFlag(id_too_long);return;}
 request_key.connection=connection;request_key.valid=1;
 request_key.desired_paused=paused?1:0;
 std::memcpy(request_key.id.data(),id.data(),id.size());
 Guard lock;if(!lock.owned)return;
 Ticket t{};t.key=request_key;Append(Make(Kind::request,t,0,0,true,false));
}
RequestScope::~RequestScope() noexcept {request_key=previous;}
BridgeCloneScope::BridgeCloneScope(const void* source) noexcept:previous(bridge_source) {
 bridge_source=IsPauseObject(source)?source:nullptr;
}
BridgeCloneScope::~BridgeCloneScope() noexcept {bridge_source=previous;}
CloneSeed CloneEnter(const void* source,std::uintptr_t caller) noexcept {
 CloneSeed result{};
 if(!Attached())return result;
 Guard lock;if(!lock.owned)return result;
 if(auto* found=Find(source)) {
   result.parent=found->ticket;result.key=found->ticket.key;
   result.role=(caller==0x3808E9B||caller==0x3808EF8)?
     Role::recorder_copy:Role::native_copy;
 } else if(source==bridge_source && request_key.valid) {
   result.key=request_key;result.role=Role::bridge_root;
 }
 return result;
}
void CloneReturn(const CloneSeed& seed,const void* clone,std::uintptr_t caller) noexcept {
 if(!Attached()||clone==nullptr)return;
 if(!IsPauseObject(clone)){GapFlag(unreadable);
   state.identity_epoch.fetch_add(1,std::memory_order_acq_rel);return;}
 Guard lock;if(!lock.owned)return;
 for(auto& e:state.entries)if(e.alive&&e.ticket.identity_epoch!=
     state.identity_epoch.load(std::memory_order_acquire))e.alive=false;
 Entry* target=Find(clone);
 if(target!=nullptr){GapFlag(pointer_reuse);target->alive=false;
   state.identity_epoch.fetch_add(1,std::memory_order_acq_rel);}
 if(target==nullptr)for(auto& e:state.entries)if(!e.alive){target=&e;break;}
 if(target==nullptr){GapFlag(full);return;}
 if(state.generations==std::numeric_limits<std::uint64_t>::max()) {GapFlag(full);return;}
 target->ticket={};target->alive=true;
 auto& t=target->ticket;
 t.token={reinterpret_cast<std::uintptr_t>(clone),++state.generations};
 t.parent=seed.parent.token;t.key=seed.key;t.role=seed.role;t.valid=1;
 t.identity_epoch=state.identity_epoch.load(std::memory_order_acquire);
 if(seed.parent.valid && seed.parent.identity_epoch!=t.identity_epoch)t.key.valid=0;
 Event e=Make(Kind::clone,t,caller,0,true,false);
 e.payload_valid=ReadPayload(clone,e.player,e.command_paused,e.native_sequence)?1:0;
 t.payload_valid=e.payload_valid;t.player=e.player;t.command_paused=e.command_paused;
 t.native_sequence=e.native_sequence;
 if(!e.payload_valid)GapFlag(unreadable);
 Append(e);
}
Ticket Lookup(const void* p) noexcept {
 if(!Attached())return {};
 Guard lock;if(!lock.owned)return {};
 if(auto* found=Find(p))return found->ticket;
 return {};
}
Ticket Enter(Kind kind,const void* object,std::uintptr_t caller,std::uintptr_t aux,
             bool qualified) noexcept {
 if(!Attached())return {};
 Ticket t{};
 // Invoke IDs need not be contiguous. They bind a return to this exact entry.
 t.invocation=state.invocations.fetch_add(1,std::memory_order_relaxed)+1;
 const Scalar scalar=ReadScalar();
 std::int32_t player{};std::uint8_t paused{};std::uint32_t native_sequence{};
 const bool payload=ReadPayload(object,player,paused,native_sequence);
 Guard lock;if(!lock.owned)return t;
 if(auto* found=Find(object)) {
   const auto invocation=t.invocation;
   if(kind==Kind::insert_enter) {
     // Entry is not an insertion receipt. Invalidate any prior qualification first.
     found->ticket.inserted=0;found->ticket.invocation=invocation;
     qualified=qualified&&payload&&found->ticket.payload_valid&&
       player==found->ticket.player&&paused==found->ticket.command_paused;
   }
   t=found->ticket;t.invocation=invocation;
   if(kind==Kind::insert_enter) {
     t.native_sequence=native_sequence;t.payload_valid=payload?1:0;
   }
   if(kind==Kind::execute_enter&&(!payload||!t.payload_valid||!t.inserted||
       player!=t.player||paused!=t.command_paused||native_sequence!=t.native_sequence)){
     qualified=false;t.key.valid=0;InvalidateIdentity(identity_drift);
   }

 }else GapFlag(no_token);
 t.qualified=qualified?1:0;
 Event e=Make(kind,t,caller,aux,qualified,false);e.scalar=scalar;
 e.player=player;e.command_paused=paused;e.native_sequence=native_sequence;e.payload_valid=payload?1:0;
 if(!payload)GapFlag(unreadable);
 Append(e);return t;
}
bool CommitInsertion(const Ticket& ticket) noexcept {
 if(!ticket.valid||!ticket.qualified||!ticket.payload_valid)return false;
 const auto* object=reinterpret_cast<const void*>(ticket.token.address);
 std::int32_t player{};std::uint8_t paused{};std::uint32_t sequence{};
 if(!ReadPayload(object,player,paused,sequence)) {GapFlag(unreadable);return false;}
 Guard lock;if(!lock.owned)return false;
 auto* found=Find(object);
 if(!found||!(found->ticket.token==ticket.token)||
    found->ticket.identity_epoch!=ticket.identity_epoch||
    found->ticket.invocation!=ticket.invocation||
    player!=ticket.player||paused!=ticket.command_paused||
    sequence!=ticket.native_sequence) {
   GapFlag(identity_drift);return false;
 }
 found->ticket.native_sequence=ticket.native_sequence;
 found->ticket.inserted=1;
 return true;
}
void Return(Kind kind,const Ticket& t,std::uintptr_t aux,bool qualified,bool accepted) noexcept {
 if(!Attached()||t.invocation==0)return;
 const Scalar scalar=ReadScalar();
 Guard lock;if(!lock.owned)return;
 Event e=Make(kind,t,0,aux,qualified&&t.qualified,accepted);e.scalar=scalar;
 e.player=t.player;e.command_paused=t.command_paused;e.native_sequence=t.native_sequence;
 e.payload_valid=t.payload_valid;Append(e);
}
void Retire(const Ticket& ticket) noexcept {
 Guard lock;if(!lock.owned)return;
 for(auto& e:state.entries)if(e.alive&&e.ticket.token==ticket.token) {e.alive=false;return;}
}
bool ReadDump(Dump& out) noexcept {
 out={};Guard lock;if(!lock.owned)return false;
 out.newest=state.sequence;
 out.oldest=out.newest>kEvents?out.newest-kEvents+1:1;
 out.count=static_cast<std::uint32_t>(std::min<std::uint64_t>(out.newest,kDumpEvents));
 const auto start=out.newest-out.count+1;
 for(std::uint32_t i=0;i<out.count;++i)out.events[i]=state.events[(start+i-1)%kEvents];
 for(const auto& e:state.entries)if(e.alive)++out.live_registry;
 out.gaps=state.gaps.load(std::memory_order_relaxed);
 out.lost=state.lost.load(std::memory_order_relaxed);return true;
}
std::string DiagnosticFrame(std::string_view id) {
 // Diagnostic transport only: no Game query, mailbox work, or native command.
 Dump d{};const bool readable=ReadDump(d);
 std::string s="{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"";
 s+=id; // Caller already passed bridge IsSimpleRequestId; keep full wire ID.
 s+="\",\"ok\":true,\"result\":{";
 s+="\"step\":\"observe-time-command-journal-v1\",\"accepted\":true,";
 s+="\"status\":\"passive_observation_only\",\"drain_fence\":false,";
 s+="\"observer_schema\":\"xar.ck3.time-command-observer31/v1\",";
 s+="\"lifetime_coverage\":\"observed_clone_and_primary_delete_slots_only\",";
 s+="\"scalar_samples_are_snapshots\":false,\"query_is_tail\":true,";
 const auto identity=Identity();
 Number(s,"qpc_frequency",identity.qpc_frequency);Number(s,"snapshot_qpc",Clock());
 Number(s,"process_id",identity.process_id);
 s+="\"process_birth\":\"";s+=std::to_string(identity.process_birth);s+="\",";
 Number(s,"image_base",identity.image_base);
 Number(s,"attached",Attached()?1:0);Number(s,"readable",readable?1:0);
 Number(s,"newest",d.newest);Number(s,"oldest_retained",d.oldest);
 Number(s,"returned_count",d.count);Number(s,"first_returned",d.newest-d.count+1);
 Number(s,"coverage_gaps",d.gaps);Number(s,"lost",d.lost);
 Number(s,"live_registry",d.live_registry);s+="\"events\":[";
 for(std::uint32_t i=0;i<d.count;++i) {
  const auto& e=d.events[i];if(i)s+=',';s+='{';
  Number(s,"seq",e.sequence);Number(s,"qpc",e.qpc);Number(s,"thread",e.thread);
  Number(s,"kind",static_cast<unsigned>(e.kind));Number(s,"role",static_cast<unsigned>(e.role));
  Number(s,"invocation",e.invocation);Number(s,"identity_epoch",e.identity_epoch);Number(s,"connection",e.key.connection);
  Number(s,"attributed",e.key.valid);s+="\"request_id\":\"";s+=e.key.id.data();s+="\",";
  Number(s,"desired_paused",e.key.desired_paused);TokenJson(s,"token",e.token);
  TokenJson(s,"parent",e.parent);Number(s,"caller_rva",e.caller);Number(s,"aux",e.aux);
  Number(s,"qualified",e.qualified);Number(s,"queue_accepted",e.accepted);
  Number(s,"payload_valid",e.payload_valid);Number(s,"player_bits",static_cast<std::uint32_t>(e.player));
  Number(s,"command_paused",e.command_paused);Number(s,"native_sequence",e.native_sequence);Number(s,"scalar_valid",e.scalar.valid);
  Number(s,"game",e.scalar.game);Number(s,"jomini",e.scalar.jomini);
  Number(s,"date_bits",static_cast<std::uint32_t>(e.scalar.date));
  Number(s,"paused",e.scalar.paused,false);s+='}';
 }
 s+="]}}";return s;
}
void** ForwardClone(CloneNative original,const void* source,void** storage,std::uintptr_t caller) {
 if(!Attached())return original(source,storage);
 const auto seed=CloneEnter(source,caller);
 auto** result=original(source,storage);
 void* clone{};
 if(result&&ReadPointer(result,clone))CloneReturn(seed,clone,caller);
 else if(Attached())InvalidateIdentity(unreadable);
 return result;
}
void* ForwardDelete(DeleteNative original,void* object,std::uint32_t flags,std::uintptr_t caller) {
 if(!Attached())return original(object,flags);
 const auto ticket=Enter(Kind::delete_enter,object,caller,flags,true);
 if(ticket.valid)Retire(ticket);
 auto* result=original(object,flags);
 Return(Kind::delete_return,ticket,flags,true,false);
 return result;
}
void ForwardExecute(ExecuteNative original,void* secondary,std::uintptr_t caller) {
 if(!Attached()){original(secondary);return;}
 const auto address=reinterpret_cast<std::uintptr_t>(secondary);
 const void* object=address>=0x18?reinterpret_cast<const void*>(address-0x18):nullptr;
 const auto ticket=Enter(Kind::execute_enter,object,caller,0,true);
 original(secondary); // Exactly once, native exceptions retain their normal propagation.
 Return(Kind::execute_return,ticket,0,true,false);
}
void** ForwardAppend(AppendNative original,void* container,void** source,std::uintptr_t caller) {
 if(!Attached()||(caller!=0x37F0794&&caller!=0x37F07AD))
   return original(container,source);
 void* object{};const bool read=ReadPointer(source,object);
 const bool relevant=read&&IsPauseObject(object);
 const bool qualified=ExpectedContainer(container)&&(caller==0x37F0794||caller==0x37F07AD);
 Ticket ticket{};
 if(relevant)ticket=Enter(Kind::insert_enter,object,caller,
   reinterpret_cast<std::uintptr_t>(container),qualified);
 auto** slot=original(container,source);
 void* inserted{};
 const bool matched=relevant&&slot&&ReadPointer(slot,inserted)&&inserted==object;
 if(relevant) {
  if(!matched)GapFlag(unreadable);
  const bool committed=qualified&&matched&&CommitInsertion(ticket);
  Return(Kind::insert_return,ticket,reinterpret_cast<std::uintptr_t>(slot),
     committed,false);
 }
 return slot;
}

}
