#include "xar_bridge/war_payment_passive_12004.hpp"
#include <algorithm>
#include <bit>
#include <limits>

namespace xar::ck3_12004 {
namespace {
using Event = ArmyNaturalPhaseEvent12004;
thread_local WarPaymentRecord12004 *g_transition = nullptr, *g_gateway = nullptr;
thread_local std::size_t g_depth = 0;
bool Valid(const Event &e) noexcept { return e.clock_identity && e.sequence && e.thread_id.has_value(); }
bool Before(const Event &a, const Event &b) noexcept {
  return Valid(a) && Valid(b) && a.clock_identity == b.clock_identity &&
      a.thread_id == b.thread_id && a.sequence < b.sequence;
}
bool SameSession(const WarPaymentSession12004 &a, const WarPaymentSession12004 &b) noexcept {
  const bool source_epoch = a.loaded_game_epoch && *a.loaded_game_epoch &&
      a.loaded_game_epoch == b.loaded_game_epoch;
  const bool controlled = a.same_owned_process_no_load_window && b.same_owned_process_no_load_window &&
      a.controlled_window_id && a.controlled_window_id == b.controlled_window_id &&
      a.process_create_time_100ns && a.process_create_time_100ns == b.process_create_time_100ns &&
      a.game_state_identity_witness && a.game_state_identity_witness == b.game_state_identity_witness;
  return a.pid && a.process_create_time_100ns && a.connection_generation && a.player_character_full_id &&
      a.process_create_time_100ns == b.process_create_time_100ns &&
      a.pid == b.pid && a.connection_generation == b.connection_generation &&
      a.loaded_game_epoch == b.loaded_game_epoch &&
      a.player_character_full_id == b.player_character_full_id && (source_epoch || controlled);
}
template<class T> std::optional<T> Read(const WarPaymentBindings12004 &b,
    WarPaymentFrame12004 &f, std::uintptr_t address, std::size_t offset) noexcept {
  T out{};
  if (!address || offset > (std::numeric_limits<std::uintptr_t>::max)() - address ||
      !b.read || !b.read(b.read_context, address + offset, &out, sizeof out)) {
    ++f.failed_reads; return std::nullopt;
  }
  return out;
}
// Pure raw reads for one exact source caller; never invoke a game getter.
template<class T> std::optional<T> GenericRead(const WarPaymentBindings12004 &b,
    WarPaymentGenericValues12004 &v,std::uintptr_t address,std::size_t offset) noexcept {
  T out{};
  if(!address||offset>(std::numeric_limits<std::uintptr_t>::max)()-address||
     !b.read||!b.read(b.read_context,address+offset,&out,sizeof out)) {
    ++v.failed_reads;return std::nullopt;
  }
  return out;
}
WarPaymentGenericValues12004 GenericValues(const WarPaymentBindings12004 &b,
    std::uintptr_t character) noexcept {
  WarPaymentGenericValues12004 v{};
  v.context_identity_before=GenericRead<std::uintptr_t>(b,v,character,0x1C0);
  if(v.context_identity_before&&*v.context_identity_before) {
    const auto context=*v.context_identity_before;
    v.value_2c0=GenericRead<std::int64_t>(b,v,context,0x2C0);
    v.value_2c8=GenericRead<std::int64_t>(b,v,context,0x2C8);
    v.value_28=GenericRead<std::int64_t>(b,v,context,0x28);
    v.value_30=GenericRead<std::int64_t>(b,v,context,0x30);
  }
  v.context_identity_after=GenericRead<std::uintptr_t>(b,v,character,0x1C0);
  v.context_stable=v.context_identity_before&&*v.context_identity_before&&
    v.context_identity_after&&v.context_identity_before==v.context_identity_after;
  v.capture_complete=!v.failed_reads&&v.context_stable&&v.value_2c0&&
    v.value_2c8&&v.value_28&&v.value_30;
  return v;
}
WarPaymentGenericParentTrace12004 GenericParent(const WarPaymentBindings12004 &b) noexcept {
  WarPaymentGenericParentTrace12004 p{};
  p.module_base=b.generic_module_base;p.module_image_size=b.generic_module_image_size;
  if(!b.capture_stack_frames)return p;
  p.reported_frame_count=b.capture_stack_frames(b.capture_stack_context,
    p.frames_absolute.data(),p.frames_absolute.size());
  p.capture_succeeded=p.reported_frame_count>0&&p.reported_frame_count<=p.frames_absolute.size();
  p.truncated=p.capture_succeeded&&p.reported_frame_count==p.frames_absolute.size();
  if(!p.capture_succeeded)return p;
  if(!p.module_base||kWarPaymentGenericReturn12004>(std::numeric_limits<std::uintptr_t>::max)()-p.module_base)return p;
  const auto known=p.module_base+kWarPaymentGenericReturn12004;
  std::size_t match=0;
  for(std::size_t i=0;i<p.reported_frame_count;++i)if(p.frames_absolute[i]==known) {
    ++p.caller_match_count;match=i;
  }
  if(p.caller_match_count!=1||match+1>=p.reported_frame_count)return p;
  p.parent_return_absolute=p.frames_absolute[match+1];
  if(p.module_image_size>kWarPaymentGenericReturn12004&&
     *p.parent_return_absolute>=p.module_base&&
     *p.parent_return_absolute-p.module_base<p.module_image_size) {
    p.parent_in_same_image=true;
    p.parent_return_rva=*p.parent_return_absolute-p.module_base;
  }
  return p;
}
bool SameGenericValues(const WarPaymentGenericValues12004 &a,
    const WarPaymentGenericValues12004 &b) noexcept {
  return a.capture_complete&&b.capture_complete&&
    a.context_identity_before==b.context_identity_before&&
    a.value_2c0==b.value_2c0&&a.value_2c8==b.value_2c8&&
    a.value_28==b.value_28&&a.value_30==b.value_30;
}

WarPaymentFrame12004 Capture(const WarPaymentBindings12004 &b, const WarPaymentRecord12004 &r) noexcept {
  WarPaymentFrame12004 f{};
  if (r.kind == WarPaymentKind12004::transition) {
    f.army_id = Read<std::uint32_t>(b,f,r.receiver,0x10);
    f.army_magic = Read<std::uint32_t>(b,f,r.receiver,0x14);
    f.requested_unit_id = Read<std::uint32_t>(b,f,r.receiver,0x124);
    f.army_1d4 = Read<std::uint8_t>(b,f,r.receiver,0x1D4);
    f.province_magic = Read<std::uint32_t>(b,f,r.second_pointer,0x85C);
    f.province_id = Read<std::uint32_t>(b,f,r.second_pointer,0x10);
  } else {
    f.character = r.kind == WarPaymentKind12004::gateway ? r.receiver : r.second_pointer;
    f.character_id = Read<std::uint32_t>(b,f,f.character,0x18);
    f.character_magic = Read<std::uint32_t>(b,f,f.character,0x1C);
    f.character_extension = Read<std::uintptr_t>(b,f,f.character,0x1B0);
    if (f.character_extension && *f.character_extension)
      f.personal_gold_bits = Read<std::uint64_t>(b,f,*f.character_extension,0x100);
    if (r.kind != WarPaymentKind12004::gateway) {
      f.wrapper = r.receiver;
      f.wrapper_balance_bits = Read<std::uint64_t>(b,f,f.wrapper,8);
      if (r.kind == WarPaymentKind12004::land_sub && f.wrapper >= 0x310) {
        f.land_id = Read<std::uint32_t>(b,f,f.wrapper-0x310,0x10);
        f.land_magic = Read<std::uint32_t>(b,f,f.wrapper-0x310,0x14);
      }
    }
  }
  f.capture_complete = f.failed_reads == 0;
  return f;
}
void Parent(WarPaymentRecord12004 &r) noexcept {
  if (g_transition) {
    r.parent_transition_entry = g_transition->entry_event;
    r.parent_transition_army = g_transition->receiver;
    r.parent_transition_caller = g_transition->caller_return_rva;
  }
  if (g_gateway) {
    r.parent_gateway_entry = g_gateway->entry_event;
    r.parent_gateway_character = g_gateway->receiver;
    r.parent_gateway_caller = g_gateway->caller_return_rva;
    r.parent_gateway_resource = g_gateway->resource_kind_raw;
    r.parent_gateway_component = g_gateway->component_raw;
    r.parent_gateway_amount = g_gateway->amount_raw;
  }
}
WarPaymentNaturalParent12004 Natural(const WarPaymentBindings12004 &b) noexcept {
  if (!b.natural_metadata) return {};
  const auto p=b.natural_metadata(b.natural_context);
  return {p.observed,p.phase,p.actual_entry_rva,p.primary_manager_identity,
    p.game_state_identity,p.session_identity,p.entry_event,p.date_raw,p.absolute_day_raw};
}
bool Ready(const WarPaymentBindings12004 &b) noexcept {
  return b.exact_build_and_prefixes_verified && b.read && b.next_event && b.session && b.journal;
}
void Publish(const WarPaymentBindings12004 &b, WarPaymentRecord12004 &r,
             const army_observer_research_detail_12004::Permit &permit) noexcept {
  try {
    const std::lock_guard lock(b.journal->mutex);
    if (!permit.CanPublishLocked()) return;
    if (b.journal->latest == (std::numeric_limits<std::uint64_t>::max)()) {
      ++b.journal->publication_failures; return;
    }
    r.journal_sequence = ++b.journal->latest;
    b.journal->records[(r.journal_sequence-1)%WarPaymentJournal12004::capacity] = r;
  } catch (...) {}
}
struct Scope {
  WarPaymentRecord12004 *old_transition = g_transition, *old_gateway = g_gateway;
  bool entered = false;
  explicit Scope(WarPaymentRecord12004 &r) noexcept {
    if (g_depth >= 8) { r.tls_depth_exceeded = true; g_transition=nullptr;g_gateway=nullptr;return; }
    ++g_depth; entered = true;
    if (r.kind == WarPaymentKind12004::transition) g_transition = &r;
    if (r.kind == WarPaymentKind12004::gateway) g_gateway = &r;
  }
  ~Scope() {g_transition=old_transition;g_gateway=old_gateway;if(entered)--g_depth;}
};
template<class Call> std::uintptr_t Invoke(const WarPaymentBindings12004 &b,
    WarPaymentRecord12004 &r, Call call) noexcept {
  if (!Ready(b)) return call();
  if (b.retain_actor && !b.retain_actor(b.retain_actor_context,r.kind,r.receiver,r.second_pointer))
    return call();
  army_observer_research_detail_12004::Permit permit(b.journal->mutex,b.journal->policy);
  if (!permit.admitted()) return call();
  Parent(r);
  r.entry_event = b.next_event(b.event_context);
  r.session_entry = b.session(b.session_context);
  r.natural_parent_metadata = Natural(b);
  r.before = Capture(b,r);
  if(b.generic_context_capture_enabled&&r.kind==WarPaymentKind12004::personal_add&&
      r.caller_return_rva==kWarPaymentGenericReturn12004) {
    auto &g=r.generic_wallet_context.emplace();
    g.before=GenericValues(b,r.before.character);g.parent_trace=GenericParent(b);
    if(g.before.capture_complete) {
      const auto bits=static_cast<std::uint64_t>(*g.before.value_2c0)-
        static_cast<std::uint64_t>(*g.before.value_2c8)-
        (static_cast<std::uint64_t>(*g.before.value_28)+static_cast<std::uint64_t>(*g.before.value_30));
      g.before_computed_add_raw=std::bit_cast<std::int64_t>(bits);
      g.before_formula_matches_amount=*g.before_computed_add_raw==r.amount_raw;
    }
  }
  {
    Scope scope(r);
    r.original_called = true;
    r.raw_return_bits = call(); // exactly one original; no getter or replay
    r.original_returned = true;
  }
  r.after = Capture(b,r);
  if(r.generic_wallet_context) {
    auto &g=*r.generic_wallet_context;
    g.after=GenericValues(b,r.after.character);
    g.context_values_stable=SameGenericValues(g.before,g.after);
  }
  r.session_return = b.session(b.session_context);
  r.natural_return_metadata = Natural(b);
  r.returned_event = b.next_event(b.event_context);
  r.clock_thread_order_matches = Before(r.entry_event,r.returned_event);
  r.session_matches = SameSession(r.session_entry,r.session_return);
  const auto &p=r.natural_parent_metadata;const auto &q=r.natural_return_metadata;
  r.natural_parent_matches=p.observed && q.observed && p.phase==ArmyNaturalPhaseKind12004::post_date &&
    q.phase==p.phase && p.actual_entry_rva==0x2A9A570 && q.actual_entry_rva==p.actual_entry_rva &&
    p.entry_event.clock_identity==q.entry_event.clock_identity && p.entry_event.sequence==q.entry_event.sequence &&
    p.entry_event.thread_id==q.entry_event.thread_id && Before(p.entry_event,r.entry_event) &&
    p.primary_manager && p.primary_manager==q.primary_manager && p.game_state && p.game_state==q.game_state &&
    ((p.session_identity && p.session_identity==q.session_identity) ||
     (r.session_matches && r.session_entry.same_owned_process_no_load_window &&
      p.game_state==r.session_entry.game_state_identity_witness &&
      q.game_state==r.session_return.game_state_identity_witness)) &&
    p.date_raw && p.date_raw==q.date_raw && p.absolute_day_raw && p.absolute_day_raw==q.absolute_day_raw;
  r.same_character_after = r.before.character && r.before.character == r.after.character &&
      r.before.character_id && r.before.character_id == r.after.character_id &&
      r.before.character_magic == 0x43686172U && r.after.character_magic == 0x43686172U &&
      *r.before.character_id != 0xFFFFFFFFU &&
      r.before.character_extension && r.before.character_extension == r.after.character_extension;
  r.same_wrapper_after = r.before.wrapper && r.before.wrapper == r.after.wrapper &&
      r.before.wrapper_balance_bits && r.after.wrapper_balance_bits && r.same_character_after &&
      (r.kind != WarPaymentKind12004::land_sub ||
       (r.before.land_id && r.before.land_id == r.after.land_id &&
        r.before.land_magic == 0x4C616E64U && r.after.land_magic == 0x4C616E64U &&
        *r.before.land_id != 0xFFFFFFFFU));
  r.personal_wrapper_matches_character = r.before.character_extension &&
      *r.before.character_extension <= (std::numeric_limits<std::uintptr_t>::max)()-0xF8 &&
      r.before.wrapper == *r.before.character_extension+0xF8;
  const bool personal = r.kind == WarPaymentKind12004::personal_sub &&
      r.parent_gateway_resource == 0 && r.caller_return_rva == 0x28B99B2 && r.personal_wrapper_matches_character;
  const bool land = r.kind == WarPaymentKind12004::land_sub &&
      r.parent_gateway_resource == 3 && r.caller_return_rva == 0x28B9A6D;
  r.source_boarding_call_chain_matches = (personal || land) &&
      r.parent_transition_caller == 0x2A9A8C5 && r.parent_gateway_caller == 0x24E8F40 &&
      r.parent_gateway_character == r.before.character && r.parent_gateway_amount == r.amount_raw &&
      r.parent_gateway_component == 3 &&
      Before(r.parent_transition_entry,r.parent_gateway_entry) && Before(r.parent_gateway_entry,r.entry_event);
  // This is source-call matching only. Parent returns, natural phase, account
  // identity, session, failure and retention fences must be joined at query.
  Publish(b,r,permit);
  return r.raw_return_bits;
}
void Clear(WarPaymentJournal12004 &j) noexcept {for(auto &r:j.records)r={};j.latest=j.publication_failures=0;}
ArmyObserverResearchSamplingState12004 Sampling(WarPaymentJournal12004 &j) noexcept {
  return j.policy.StateLocked(true,(std::min<std::uint64_t>)(j.latest,j.capacity),0);
}
} // namespace
ArmyObserverResearchSamplingState12004 WarPaymentJournal12004::SetEnabled(bool enabled) noexcept {
  try {const std::lock_guard lock(mutex);policy.SetLocked(enabled,[&]{Clear(*this);});return Sampling(*this);}
  catch (...) {return {};}
}
WarPaymentJournalSnapshot12004 WarPaymentJournal12004::Copy() noexcept {
  try {
    const std::lock_guard lock(mutex);
    WarPaymentJournalSnapshot12004 out{};out.sampling=Sampling(*this);
    if (!policy.ReadableLocked()) return out;
    out.latest_sequence=latest;out.publication_failures=publication_failures;
    out.oldest_sequence=latest ? (latest>capacity?latest-capacity+1:1) : 0;
    out.overwritten=latest>capacity?latest-capacity:0;
    for(auto i=out.oldest_sequence;i && i<=latest;++i) {
      const auto &r=records[(i-1)%capacity];
      if(r.journal_sequence!=i)return out;
      out.records.push_back(r);
      if(i==(std::numeric_limits<std::uint64_t>::max)())break;
    }
    out.read_complete=true;return out;
  } catch (...) {return {};}
}
std::uintptr_t InvokeWarPaymentTransition12004(const WarPaymentBindings12004 &b,
    WarPaymentTransitionOriginal12004 original,void *army,void *province,std::uintptr_t pc) noexcept {
  if(!original)return 0;
  WarPaymentRecord12004 r{};r.kind=WarPaymentKind12004::transition;
  r.receiver=reinterpret_cast<std::uintptr_t>(army);r.second_pointer=reinterpret_cast<std::uintptr_t>(province);r.caller_return_rva=pc;
  return Invoke(b,r,[&]{return original(army,province);});
}
std::uintptr_t InvokeWarPaymentGateway12004(const WarPaymentBindings12004 &b,
    WarPaymentGatewayOriginal12004 original,void *character,std::int32_t resource,
    std::int64_t amount,std::int32_t component,std::uintptr_t pc) noexcept {
  if(!original)return 0;
  WarPaymentRecord12004 r{};r.kind=WarPaymentKind12004::gateway;
  r.receiver=reinterpret_cast<std::uintptr_t>(character);r.caller_return_rva=pc;
  r.resource_kind_raw=resource;r.amount_raw=amount;r.component_raw=component;
  return Invoke(b,r,[&]{return original(character,resource,amount,component);});
}
std::uintptr_t InvokeWarPaymentWriter12004(const WarPaymentBindings12004 &b,
    WarPaymentWriterOriginal12004 original,WarPaymentKind12004 kind,void *wrapper,
    std::int64_t amount,void *character,std::uintptr_t pc) noexcept {
  if(!original)return 0;
  WarPaymentRecord12004 r{};r.kind=kind;r.receiver=reinterpret_cast<std::uintptr_t>(wrapper);
  r.second_pointer=reinterpret_cast<std::uintptr_t>(character);r.amount_raw=amount;r.caller_return_rva=pc;
  return Invoke(b,r,[&]{return original(wrapper,amount,character);});
}
} // namespace xar::ck3_12004
