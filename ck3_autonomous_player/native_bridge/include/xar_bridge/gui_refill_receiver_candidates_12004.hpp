#pragma once
#include <array>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#ifndef XAR_ENABLE_GUI_REFILL_PARENT_PREFIX_12004
#define XAR_ENABLE_GUI_REFILL_PARENT_PREFIX_12004 0
#endif
#ifndef XAR_ENABLE_GUI_REFILL_FRONTIER_CONTINUATION_12004
#define XAR_ENABLE_GUI_REFILL_FRONTIER_CONTINUATION_12004 0
#endif
#if XAR_ENABLE_GUI_REFILL_FRONTIER_CONTINUATION_12004 && !XAR_ENABLE_GUI_REFILL_PARENT_PREFIX_12004
#error frontier continuation requires the independently stable depth8 prefix
#endif

namespace xar::game {
struct GuiRefillReceiverEntry12004V1 {
  std::uint32_t ancestor_depth=0,entry_type_48=0;
  std::int8_t entry_mode_40=0;
  std::uint8_t entry_flag_4c=0;
  bool direct_value_present=false,provider_present=false;
  std::optional<std::uint64_t> provider_vtable_rva,provider_slot2_rva;
  std::optional<std::int32_t> direct_owner_full_id;
  bool direct_owner_identity_verified=false;
  bool operator==(const GuiRefillReceiverEntry12004V1 &) const=default;
};
struct GuiRefillReceiverFailure12004V1 {
  std::string stage,kind;
  std::uint32_t capture_pass=0,read_ordinal=0;
  std::optional<std::uint32_t> ancestor_depth;
  std::optional<std::int32_t> raw_declaration_count,raw_index_count,raw_definition_entry_count;
  std::optional<bool> context_present,definition_present;
  std::optional<std::uint8_t> local_definition_active_raw;
  bool operator==(const GuiRefillReceiverFailure12004V1 &) const=default;
};
struct GuiRefillLocalDefinitionEntry12004V1 {
  std::string status="unavailable",unavailable_reason="local_prefix_not_admitted";
  std::optional<std::int32_t> receiver_variable_index,raw_definition_entry_count;
  std::optional<std::uint32_t> declared_type_id;
  std::optional<bool> definition_present,local_entry_present;
  std::optional<std::uint8_t> local_definition_active_raw;
  bool stable_double_read=false;
  std::vector<GuiRefillReceiverEntry12004V1> entries;
  std::optional<GuiRefillReceiverFailure12004V1> failure_diagnostic;
  bool operator==(const GuiRefillLocalDefinitionEntry12004V1 &) const=default;
};
struct GuiRefillDefinitionPrefixRow12004V1 {
  std::uint32_t ancestor_depth=0;
  bool definition_present=false;
  std::optional<std::int32_t> raw_definition_entry_count;
  std::vector<GuiRefillReceiverEntry12004V1> entries;
  std::string parent_edge;
  bool parent_present=false;
  bool operator==(const GuiRefillDefinitionPrefixRow12004V1 &) const=default;
};
struct GuiRefillDefinitionPrefix12004V1 {
  std::string status="unavailable",unavailable_reason="definition_prefix_double_read_incomplete";
  std::optional<std::int32_t> receiver_variable_index;
  std::optional<std::uint32_t> declared_type_id;
  bool stable_double_read=false;
  std::vector<GuiRefillDefinitionPrefixRow12004V1> rows;
  bool operator==(const GuiRefillDefinitionPrefix12004V1 &) const=default;
};
struct GuiRefillContinuationRow12004V1 {
  std::uint32_t ancestor_depth=0;
  bool definition_present=false;
  std::optional<std::int32_t> raw_definition_entry_count;
  std::optional<std::int32_t> first_match_entry_index;
  std::vector<GuiRefillReceiverEntry12004V1> entries;
  std::string parent_edge;
  std::optional<bool> parent_present;
  bool operator==(const GuiRefillContinuationRow12004V1 &) const=default;
};
struct GuiRefillDefinitionContinuation12004V1 {
  std::string status="unavailable",unavailable_reason="frontier_continuation_not_admitted",stop_reason;
  std::optional<std::int32_t> receiver_variable_index;
  std::optional<std::uint32_t> declared_type_id,stop_depth;
  std::optional<bool> next_context_present;
  bool stable_double_read=false;
  std::vector<GuiRefillContinuationRow12004V1> rows;
  std::optional<GuiRefillReceiverFailure12004V1> failure_diagnostic;
  bool operator==(const GuiRefillDefinitionContinuation12004V1 &) const=default;
};
struct GuiRefillReceiverCandidates12004V1 {
  std::string status="unavailable",unavailable_reason="candidate_read_not_admitted";
  std::optional<std::int32_t> receiver_variable_index;
  std::optional<std::uint32_t> declared_type_id;
  bool stable_double_read=false;
  std::vector<GuiRefillReceiverEntry12004V1> entries;
  std::optional<GuiRefillReceiverFailure12004V1> failure_diagnostic;
  std::optional<GuiRefillLocalDefinitionEntry12004V1> local_definition_entry_only;
  std::optional<GuiRefillDefinitionPrefix12004V1> definition_chain_prefix_depth8;
  std::optional<GuiRefillDefinitionContinuation12004V1> definition_frontier_continuation_depth8_12;
  bool operator==(const GuiRefillReceiverCandidates12004V1 &) const=default;
};
struct GuiRefillReceiverFrame12004V1 {
  std::uint64_t native_revision=0,connection_generation=0,pump_epoch=0,ticket_sequence=0;
  std::uint32_t game_pid=0,thread_id=0;
  std::int32_t played_character_full_id=-1,date_raw=0;
};
}

namespace xar::ck3_12004 {
using GuiRefillRead12004=bool(*)(void*,std::uintptr_t,void*,std::size_t) noexcept;
// Pure memory only. No callback/provider invocation and no native variable-table
// claim: 3AC38C0 creates that table in its own temporary stack invocation.
inline game::GuiRefillReceiverCandidates12004V1 ReadGuiRefillReceiverCandidates12004(
    GuiRefillRead12004 read,void *opaque,std::uintptr_t module_base,
    std::uintptr_t callback) {
  using Result=game::GuiRefillReceiverCandidates12004V1;
  constexpr std::uintptr_t image_size=0x61C5000;
  Result rejected;
  if(!read||!module_base||module_base>UINTPTR_MAX-image_size||!callback)return rejected;
  const auto started=std::chrono::steady_clock::now();
  std::size_t reads=0,bytes=0;
  const char *failure="candidate_memory_unreadable";
  game::GuiRefillReceiverFailure12004V1 diagnostic;
  const auto guard=[&](bool ok,const char *kind) {
    if(!ok){failure="candidate_layout_guard_rejected";diagnostic.kind=kind;}
    return ok;
  };
  const auto load=[&]<class T>(const char *stage,std::uintptr_t object,std::size_t offset,T &value) {
    diagnostic.stage=stage;diagnostic.kind="condition_failed";
    diagnostic.read_ordinal=static_cast<std::uint32_t>(reads+1);
    if(!object||object>UINTPTR_MAX-offset||object+offset>UINTPTR_MAX-sizeof(T)){
      diagnostic.kind="invalid_address_range";return false;
    }
    if(++reads>4096||(bytes+=sizeof(T))>65536||
        std::chrono::steady_clock::now()-started>std::chrono::milliseconds(20)){
      failure="candidate_read_budget_exhausted";diagnostic.kind="read_budget_exhausted";return false;
    }
    if(!read(opaque,object+offset,&value,sizeof(T))){diagnostic.kind="memory_read_failed";return false;}
    return true;
  };
  const auto rva=[&](std::uintptr_t p,std::size_t n)->std::optional<std::uint64_t>{
    if(p<=module_base||n>image_size||p-module_base>image_size-n)return {};
    return p-module_base;
  };
  struct Capture {
    Result result;std::vector<std::uintptr_t> private_identity;
    game::GuiRefillLocalDefinitionEntry12004V1 local;
    std::vector<std::uintptr_t> local_identity;
    bool local_complete=false,prefix_boundary=false;
    std::vector<game::GuiRefillDefinitionPrefixRow12004V1> prefix_rows;
    std::optional<game::GuiRefillReceiverFailure12004V1> local_failure;
    std::uintptr_t frontier_context=0;
    std::array<std::uintptr_t,8> prefix_contexts{};
    game::GuiRefillDefinitionContinuation12004V1 continuation;
    std::vector<std::uintptr_t> continuation_identity;
    bool continuation_complete=false;
  };
  const auto once=[&](Capture &out,bool local_only=false,bool prefix_only=false) {
    auto &v=out.result;auto &identity=out.private_identity;
    std::uintptr_t context=0,declarations=0,indices=0;
    std::int32_t count=0,index_count=0,index=0;std::uint32_t key=0;
    // The callback+10 expression block supplies declaration keys and the last
    // receiver-variable index. These are declarations, not an evaluated table.
    diagnostic.ancestor_depth.reset();diagnostic.raw_declaration_count.reset();
    diagnostic.raw_index_count.reset();diagnostic.raw_definition_entry_count.reset();
    diagnostic.context_present.reset();diagnostic.definition_present.reset();
    diagnostic.local_definition_active_raw.reset();
    if(!load("callback_context_f0",callback,0xF0,context))return false;
    diagnostic.context_present=context!=0;
    if(!guard(context!=0,"required_context_null"))return false;
    if(!load("callback_declaration_pointer_a8",callback,0xA8,declarations)||
        !load("callback_declaration_count_b4",callback,0xB4,count))return false;
    diagnostic.raw_declaration_count=count;
    if(!guard(count>=1&&count<=256,"declaration_count_out_of_bound")||
        !guard(declarations!=0,"required_declaration_pointer_null"))return false;
    if(!load("callback_indices_pointer_c0",callback,0xC0,indices)||
        !load("callback_index_count_cc",callback,0xCC,index_count))return false;
    diagnostic.raw_index_count=index_count;
    if(!guard(index_count>=1&&index_count<=256,"index_count_out_of_bound")||
        !guard(indices!=0,"required_indices_pointer_null"))return false;
    if(!load("receiver_last_index",indices,static_cast<std::size_t>(index_count-1)*4,index)||
        !guard(index>=0&&index<count,"receiver_index_out_of_bound")||
        !load("receiver_declaration_key",declarations,static_cast<std::size_t>(index)*8,key))return false;
    v.receiver_variable_index=index;v.declared_type_id=key;
    if(key!=635){failure="receiver_declaration_not_type635";diagnostic.kind="declaration_type_mismatch";return false;}
    identity={callback,context,declarations,indices,static_cast<std::uintptr_t>(count),static_cast<std::uintptr_t>(index_count)};
    std::array<std::uintptr_t,8> visited{};
    for(std::uint32_t depth=0;context;++depth){
      diagnostic.ancestor_depth=depth;diagnostic.stage="parent_walk";
      // These fields describe this context, not the last completed one. A
      // depth/cycle guard can return before its definition has been read.
      diagnostic.context_present=context!=0;
      diagnostic.raw_definition_entry_count.reset();
      diagnostic.definition_present.reset();
      if(depth==visited.size()){
        out.prefix_boundary=true;
        out.frontier_context=context;out.prefix_contexts=visited;
        // A prefix replay stops before reading depth8. It never turns the
        // failed full traversal into an available full candidate.
        if(prefix_only)return true;
        failure="candidate_parent_depth_exhausted";diagnostic.kind="parent_depth_exhausted";return false;
      }
      for(std::size_t n=0;n<depth;++n)if(visited[n]==context){failure="candidate_parent_cycle";diagnostic.kind="parent_cycle";return false;}
      visited[depth]=context;
      std::uintptr_t definition=0,table=0,parent=0,matched=0;std::int32_t entries=0;std::uint8_t active=0;bool stop_here=false;
      if(!load("context_definition_e0",context,0xE0,definition))return false;
      diagnostic.definition_present=definition!=0;
      if(depth==0){
        if(!guard(definition!=0,"local_definition_null")||
            !load("local_definition_active_115",definition,0x115,active))return false;
        diagnostic.local_definition_active_raw=active;
        if(!guard(active!=0,"local_definition_inactive"))return false;
      }
      // Actual3AC4107/410A skips a null ancestor definition and follows that
      // context's +E8. Only the initial builder checks definition+115.
      if(definition){
        if(!load("definition_entry_pointer_90",definition,0x90,table)||
            !load("definition_entry_count_9c",definition,0x9C,entries))return false;
        diagnostic.raw_definition_entry_count=entries;
        if(!guard(entries>=0&&entries<=256,"definition_entry_count_out_of_bound")||
            !guard(entries==0||table!=0,"required_entry_pointer_null"))return false;
      }
      identity.insert(identity.end(),{context,definition,table,static_cast<std::uintptr_t>(entries),active});
      // First match follows native lookup order; a duplicate key is not
      // silently treated as a second native receiver candidate.
      for(std::int32_t n=0;n<entries;++n){
        std::uint32_t actual=0;const auto offset=static_cast<std::size_t>(n)*0x50;
        if(!load("definition_entry_key_48",table,offset+0x48,actual))return false;
        identity.push_back(actual);
        // Actual3AC3FE3/3AC4167 leaves lookup on the first matching key. A
        // later entry is unrelated and must not cause extra reads/failures.
        if(actual==key){if(table>UINTPTR_MAX-offset)return false;matched=table+offset;break;}
      }
      if(matched){
        game::GuiRefillReceiverEntry12004V1 e;e.ancestor_depth=depth;
        std::uintptr_t direct=0,provider=0,vt=0,target=0;
        if(!load("matched_entry_type_48",matched,0x48,e.entry_type_48)||!guard(e.entry_type_48==key,"matched_entry_type_changed")||!load("matched_entry_mode_40",matched,0x40,e.entry_mode_40)||
            !load("matched_entry_flag_4c",matched,0x4C,e.entry_flag_4c)||!load("matched_direct_value_0",matched,0,direct)||!load("matched_provider_38",matched,0x38,provider))return false;
        e.direct_value_present=direct!=0;e.provider_present=provider!=0;
        identity.insert(identity.end(),{matched,direct,provider,static_cast<std::uintptr_t>(static_cast<std::uint8_t>(e.entry_mode_40)),e.entry_flag_4c});
        const bool branch_eligible=depth==0||e.entry_flag_4c!=0;
        if(branch_eligible&&e.entry_mode_40>=2&&provider){
          if(!load("provider_vtable",provider,0,vt))return false;
          e.provider_vtable_rva=rva(vt,24);
          if(e.provider_vtable_rva){if(!load("provider_slot2",vt,0x10,target))return false;e.provider_slot2_rva=rva(target,1);}
          identity.insert(identity.end(),{vt,target});
        }
        if(branch_eligible&&e.entry_mode_40==1&&direct){
          std::int32_t owner=-1;std::uintptr_t storage=0,slots=0,character=0;std::int32_t capacity=0,id=-1;std::uint32_t magic=0;
          if(!load("direct_owner_218",direct,0x218,owner))return false;
          e.direct_owner_full_id=owner;
          const auto slot=static_cast<std::uint32_t>(owner)&0xFFFFFFU;
          if(owner!=-1&&load("character_registry_slot",module_base,0x5C67568,storage)&&storage&&
              load("character_registry_slots",storage,0x20,slots)&&load("character_registry_capacity",storage,0x2C,capacity)&&slots&&capacity>0&&slot<static_cast<std::uint32_t>(capacity)&&
              load("character_registry_object",slots,static_cast<std::size_t>(slot)*0x10+8,character)&&character&&
              load("character_full_id_18",character,0x18,id)&&load("character_magic_1c",character,0x1C,magic)&&id==owner&&magic==0x43686172)
            e.direct_owner_identity_verified=true;
          identity.insert(identity.end(),{static_cast<std::uintptr_t>(static_cast<std::uint32_t>(owner)),storage,slots,character,static_cast<std::uintptr_t>(static_cast<std::uint32_t>(capacity)),static_cast<std::uintptr_t>(static_cast<std::uint32_t>(id)),magic});
        }
        v.entries.push_back(e);
        // The selected receiver never becomes pending when its local flag4C
        // is nonzero. A parent flag4C entry in mode0/1 returns AL1 by source,
        // removing this receiver from pending. Do not read unrelated parents.
        if((depth==0&&e.entry_flag_4c!=0)||
            (depth>0&&e.entry_flag_4c!=0&&e.entry_mode_40>=0&&e.entry_mode_40<=1))stop_here=true;
      }
      if(depth==0){
        // This snapshot ends before any parent-pointer read. Keep the complete
        // private prefix even if the legacy parent walk later fails.
        out.local.status="available";out.local.unavailable_reason.clear();
        out.local.receiver_variable_index=v.receiver_variable_index;
        out.local.declared_type_id=v.declared_type_id;
        out.local.raw_definition_entry_count=entries;
        out.local.definition_present=definition!=0;
        out.local.local_definition_active_raw=active;
        out.local.local_entry_present=matched!=0;
        out.local.entries=v.entries;out.local_identity=identity;
        out.local_complete=reads<=4096&&bytes<=65536&&
            std::chrono::steady_clock::now()-started<=std::chrono::milliseconds(20);
        if(!out.local_complete){
          auto d=diagnostic;d.stage="local_prefix_budget_check";d.kind="read_budget_exhausted";
          out.local_failure=d;
          if(local_only){failure="candidate_read_budget_exhausted";diagnostic=d;return false;}
        }
        if(local_only)return true;
      }
      if(stop_here)break;
      // Publish bounded entry candidates, without predicting whether a dynamic
      // provider returns success or which pending parent entry native selects.
      if(definition&&!load("definition_parent_108",definition,0x108,parent))return false;
#if XAR_ENABLE_GUI_REFILL_PARENT_PREFIX_12004
      const bool definition_edge=parent!=0;
#endif
      if(!parent&&!load("context_parent_e8",context,0xE8,parent))return false;
      identity.push_back(parent);
#if XAR_ENABLE_GUI_REFILL_PARENT_PREFIX_12004
      game::GuiRefillDefinitionPrefixRow12004V1 row;
      row.ancestor_depth=depth;row.definition_present=definition!=0;
      if(definition)row.raw_definition_entry_count=entries;
      if(matched)row.entries.push_back(v.entries.back());
      row.parent_edge=definition_edge?"definition_108":"context_e8";
      row.parent_present=parent!=0;out.prefix_rows.push_back(std::move(row));
#endif
      context=parent;
    }
    v.status="available";v.unavailable_reason.clear();return true;
  };
  // The local result has independent stability and never changes the legacy
  // unavailable/index/entries/failure fields. Both paths use the same load budget.
  const auto attach_local=[&](Result &destination,const Capture &a,const Capture &b,
      const std::optional<game::GuiRefillReceiverFailure12004V1> &failure_detail) {
    game::GuiRefillLocalDefinitionEntry12004V1 leaf;
    if(reads>4096||bytes>65536||
        std::chrono::steady_clock::now()-started>std::chrono::milliseconds(20)){
      leaf.unavailable_reason="local_prefix_shared_budget_exhausted";
      auto d=diagnostic;d.stage="local_prefix_budget_check";d.kind="read_budget_exhausted";
      leaf.failure_diagnostic=d;
    }else if(!a.local_complete||!b.local_complete){
      leaf.unavailable_reason="local_prefix_double_read_incomplete";
      leaf.failure_diagnostic=a.local_failure?a.local_failure:
          b.local_failure?b.local_failure:failure_detail;
    }else if(a.local_identity!=b.local_identity||a.local!=b.local){
      leaf.unavailable_reason="local_prefix_identity_or_entry_changed";
    }else{leaf=a.local;leaf.stable_double_read=true;}
    destination.local_definition_entry_only=std::move(leaf);
  };
#if XAR_ENABLE_GUI_REFILL_PARENT_PREFIX_12004
  const auto attach_prefix=[&](Result &destination,const Capture &a,const Capture &b) {
    game::GuiRefillDefinitionPrefix12004V1 leaf;
    if(reads>4096||bytes>65536||
        std::chrono::steady_clock::now()-started>std::chrono::milliseconds(20))
      leaf.unavailable_reason="definition_prefix_shared_budget_exhausted";
    else if(!a.prefix_boundary||!b.prefix_boundary||a.prefix_rows.size()!=8||b.prefix_rows.size()!=8)
      leaf.unavailable_reason="definition_prefix_double_read_incomplete";
    else if(a.private_identity!=b.private_identity||a.prefix_rows!=b.prefix_rows||
        a.result.receiver_variable_index!=b.result.receiver_variable_index||
        a.result.declared_type_id!=b.result.declared_type_id)
      leaf.unavailable_reason="definition_prefix_identity_or_rows_changed";
    else{
      leaf.status="available";leaf.unavailable_reason.clear();leaf.stable_double_read=true;
      leaf.receiver_variable_index=a.result.receiver_variable_index;
      leaf.declared_type_id=a.result.declared_type_id;leaf.rows=a.prefix_rows;
    }
    destination.definition_chain_prefix_depth8=std::move(leaf);
  };
#endif
  // Resume only the actual depth8 frontier saved by each complete prefix
  // capture. This is a bounded source walk, never the native resolver/provider.
#if XAR_ENABLE_GUI_REFILL_FRONTIER_CONTINUATION_12004
  const auto continue_frontier=[&](Capture &out) {
    auto &v=out.continuation;auto &identity=out.continuation_identity;
    auto context=out.frontier_context;
    std::array<std::uintptr_t,12> visited{};
    for(std::size_t n=0;n<out.prefix_contexts.size();++n)visited[n]=out.prefix_contexts[n];
    v.receiver_variable_index=out.result.receiver_variable_index;
    v.declared_type_id=out.result.declared_type_id;
    const auto finish=[&](const char *reason,std::uint32_t depth,std::optional<bool> next) {
      v.stop_reason=reason;v.stop_depth=depth;v.next_context_present=next;
      out.continuation_complete=true;return true;
    };
    for(std::uint32_t depth=8;depth<12;++depth){
      diagnostic.ancestor_depth=depth;diagnostic.stage="continuation_parent_walk";
      diagnostic.context_present=context!=0;diagnostic.definition_present.reset();
      diagnostic.raw_definition_entry_count.reset();
      identity.push_back(context);
      if(!context)return finish("null_end",depth,false);
      for(std::size_t n=0;n<depth;++n)if(visited[n]==context)return finish("cycle",depth,true);
      visited[depth]=context;
      game::GuiRefillContinuationRow12004V1 row;row.ancestor_depth=depth;
      std::uintptr_t definition=0,table=0,matched=0,parent=0;std::int32_t count=0;
      if(!load("continuation_context_definition_e0",context,0xE0,definition))return false;
      row.definition_present=definition!=0;diagnostic.definition_present=definition!=0;
      if(definition){
        if(!load("continuation_entry_pointer_90",definition,0x90,table)||
            !load("continuation_entry_count_9c",definition,0x9C,count))return false;
        diagnostic.raw_definition_entry_count=count;row.raw_definition_entry_count=count;
        if(!guard(count>=0&&count<=256,"continuation_entry_count_out_of_bound")||
            !guard(count==0||table!=0,"continuation_entry_pointer_null"))return false;
      }
      identity.insert(identity.end(),{context,definition,table,static_cast<std::uintptr_t>(count)});
      for(std::int32_t n=0;n<count;++n){
        std::uint32_t key=0;const auto offset=static_cast<std::size_t>(n)*0x50;
        if(!load("continuation_entry_key_48",table,offset+0x48,key))return false;
        identity.push_back(key);
        if(key==635U){if(table>UINTPTR_MAX-offset)return false;matched=table+offset;row.first_match_entry_index=n;break;}
      }
      bool static_stop=false;
      if(matched){
        game::GuiRefillReceiverEntry12004V1 e;e.ancestor_depth=depth;
        std::uintptr_t direct=0,provider=0,vt=0,target=0;
        if(!load("continuation_matched_type_48",matched,0x48,e.entry_type_48)||
            !guard(e.entry_type_48==635U,"continuation_matched_type_changed")||
            !load("continuation_entry_mode_40",matched,0x40,e.entry_mode_40)||
            !load("continuation_entry_flag_4c",matched,0x4C,e.entry_flag_4c)||
            !load("continuation_direct_value_0",matched,0,direct)||
            !load("continuation_provider_38",matched,0x38,provider))return false;
        e.direct_value_present=direct!=0;e.provider_present=provider!=0;
        identity.insert(identity.end(),{matched,direct,provider,static_cast<std::uintptr_t>(static_cast<std::uint8_t>(e.entry_mode_40)),e.entry_flag_4c});
        // Parent flag0 is filtered before resolver/provider dispatch.
        if(e.entry_flag_4c!=0&&e.entry_mode_40>=2&&provider){
          if(!load("continuation_provider_vtable",provider,0,vt))return false;
          e.provider_vtable_rva=rva(vt,24);
          if(e.provider_vtable_rva){if(!load("continuation_provider_slot2",vt,0x10,target))return false;e.provider_slot2_rva=rva(target,1);}
          identity.insert(identity.end(),{vt,target});
        }
        if(e.entry_flag_4c!=0&&e.entry_mode_40==1&&direct){
          std::int32_t owner=-1;std::uintptr_t storage=0,slots=0,character=0;std::int32_t capacity=0,id=-1;std::uint32_t magic=0;
          if(!load("continuation_direct_owner_218",direct,0x218,owner))return false;
          e.direct_owner_full_id=owner;const auto slot=static_cast<std::uint32_t>(owner)&0xFFFFFFU;
          if(owner!=-1&&load("continuation_character_registry",module_base,0x5C67568,storage)&&storage&&
              load("continuation_character_slots",storage,0x20,slots)&&load("continuation_character_capacity",storage,0x2C,capacity)&&slots&&capacity>0&&slot<static_cast<std::uint32_t>(capacity)&&
              load("continuation_character_object",slots,static_cast<std::size_t>(slot)*0x10+8,character)&&character&&
              load("continuation_character_full_id",character,0x18,id)&&load("continuation_character_magic",character,0x1C,magic)&&id==owner&&magic==0x43686172)
            e.direct_owner_identity_verified=true;
          identity.insert(identity.end(),{static_cast<std::uintptr_t>(static_cast<std::uint32_t>(owner)),storage,slots,character,static_cast<std::uintptr_t>(static_cast<std::uint32_t>(capacity)),static_cast<std::uintptr_t>(static_cast<std::uint32_t>(id)),magic});
        }
        static_stop=e.entry_flag_4c!=0&&e.entry_mode_40>=0&&e.entry_mode_40<=1;
        row.entries.push_back(e);
      }
      if(static_stop){
        row.parent_edge="not_read_native_static_stop";out.continuation.rows.push_back(std::move(row));
        return finish("static_direct_terminal",depth,std::nullopt);
      }
      if(definition&&!load("continuation_definition_parent_108",definition,0x108,parent))return false;
      const bool definition_edge=parent!=0;
      if(!parent&&!load("continuation_context_parent_e8",context,0xE8,parent))return false;
      row.parent_edge=definition_edge?"definition_108":"context_e8";row.parent_present=parent!=0;
      identity.push_back(parent);out.continuation.rows.push_back(std::move(row));
      context=parent;
      if(!context)return finish("null_end",depth+1U,false);
    }
    return finish("depth_limit",12U,true);
  };
  const auto attach_continuation=[&](Result &destination,const Capture &a,const Capture &b) {
    game::GuiRefillDefinitionContinuation12004V1 leaf;
    if(reads>4096||bytes>65536||std::chrono::steady_clock::now()-started>std::chrono::milliseconds(20))
      leaf.unavailable_reason="frontier_continuation_shared_budget_exhausted";
    else if(!destination.definition_chain_prefix_depth8||destination.definition_chain_prefix_depth8->status!="available")
      leaf.unavailable_reason="frontier_continuation_prefix_not_stable";
    else if(!a.continuation_complete||!b.continuation_complete){
      leaf.unavailable_reason="frontier_continuation_capture_incomplete";
      leaf.failure_diagnostic=a.continuation.failure_diagnostic?a.continuation.failure_diagnostic:b.continuation.failure_diagnostic;
    }else if(a.continuation_identity!=b.continuation_identity||a.continuation!=b.continuation)
      leaf.unavailable_reason="frontier_continuation_identity_or_rows_changed";
    else{leaf=a.continuation;leaf.status="available";leaf.unavailable_reason.clear();leaf.stable_double_read=true;}
    destination.definition_frontier_continuation_depth8_12=std::move(leaf);
  };
#endif
  Capture a,b;
  diagnostic.capture_pass=1;
  if(!once(a)){
    // Preserve this first full-capture failure before the local-only second
    // read changes the diagnostic cursor, stage or failure reason.
    rejected.unavailable_reason=failure;rejected.failure_diagnostic=diagnostic;
    if(!a.local_complete||std::string_view(failure)=="candidate_read_budget_exhausted"||reads>4096||bytes>65536){
      attach_local(rejected,a,b,rejected.failure_diagnostic);return rejected;
    }
    diagnostic.capture_pass=2;
#if XAR_ENABLE_GUI_REFILL_PARENT_PREFIX_12004
    const bool capture_prefix=a.prefix_boundary&&a.prefix_rows.size()==8;
#if XAR_ENABLE_GUI_REFILL_FRONTIER_CONTINUATION_12004
    if(capture_prefix){diagnostic.capture_pass=1;if(!continue_frontier(a))a.continuation.failure_diagnostic=diagnostic;}
    diagnostic.capture_pass=2;
#endif
    const bool local_ok=once(b,!capture_prefix,capture_prefix);
#if XAR_ENABLE_GUI_REFILL_FRONTIER_CONTINUATION_12004
    if(capture_prefix&&local_ok){if(!continue_frontier(b))b.continuation.failure_diagnostic=diagnostic;}
#endif
#else
    const bool local_ok=once(b,true);
#endif
    std::optional<game::GuiRefillReceiverFailure12004V1> local_failure;
    if(!local_ok)local_failure=diagnostic;
    attach_local(rejected,a,b,local_failure);
#if XAR_ENABLE_GUI_REFILL_PARENT_PREFIX_12004
    if(capture_prefix)attach_prefix(rejected,a,b);
#if XAR_ENABLE_GUI_REFILL_FRONTIER_CONTINUATION_12004
    if(capture_prefix)attach_continuation(rejected,a,b);
#endif
#endif
    return rejected;
  }
  diagnostic.capture_pass=2;
  if(!once(b)){
    rejected.unavailable_reason=failure;rejected.failure_diagnostic=diagnostic;
    attach_local(rejected,a,b,rejected.failure_diagnostic);return rejected;
  }
  if(a.private_identity!=b.private_identity||a.result!=b.result){
    rejected.unavailable_reason="candidate_identity_or_type_changed";
    attach_local(rejected,a,b,std::nullopt);return rejected;
  }
  a.result.stable_double_read=true;
  attach_local(a.result,a,b,std::nullopt);return a.result;
}
}
