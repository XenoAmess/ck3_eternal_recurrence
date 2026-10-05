#include "xar_bridge/normal_exit_map_v1.hpp"
#include "xar_bridge/normal_exit_map_source_v1.hpp"
#include "xar_bridge/ingame_ui_navigation_v1.hpp"
#include <windows.h>

#include <array>
#include <limits>

namespace xar::ck3_12003 {
namespace {
using namespace ck3_11906;
#include "normal_exit_map_pins_v1.inc"
struct Target { std::string_view root, leaf; };
constexpr std::array<Target,3> kTargets{{
  {"timeline_widget","pause_menu_button"},
  {"ingame_pausemenu","exit_button"},
  {"ingame_resign_confirmation","descktop_button"},
}};
struct Census {
  void *context=nullptr, *owner=nullptr;
  std::array<void *,3> roots{},targets{},vtables{};
  std::array<NormalExitMapTargetV1,3> observations{};
};
bool Pins(const ZhongguoScoreboardNativeEnvironmentV1 &env,
    const ZhongguoScoreboardActionDispatchEnvironmentV1 &dispatch) noexcept {
  if(!env.exact_build_admitted || !dispatch.exact_build_admitted ||
      env.offline_fixture_function_overrides || dispatch.offline_fixture_function_overrides ||
      env.module_base==0 || env.module_base!=dispatch.module_base ||
      env.gui_abi_revision!=GuiAbiRevisionV1::crozier12003 ||
      dispatch.gui_abi_revision!=GuiAbiRevisionV1::crozier12003) return false;
  for(const auto &pin:kPins) {
    if(env.module_base>(std::numeric_limits<std::uintptr_t>::max)()-pin.rva) return false;
    std::array<unsigned char,32> actual{}; SIZE_T received=0;
    if(!ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<void *>(env.module_base+pin.rva),actual.data(),actual.size(),&received) ||
        received!=actual.size() || actual!=pin.bytes) return false;
  }
  return true;
}
bool Process(const NormalExitMapRequestV1 &request) noexcept {
  FILETIME creation{},exit{},kernel{},user{};
  if(request.expected_game_pid==0 || request.expected_game_pid!=GetCurrentProcessId() ||
      request.expected_process_creation_filetime_100ns==0 ||
      !GetProcessTimes(GetCurrentProcess(),&creation,&exit,&kernel,&user)) return false;
  return ((std::uint64_t{creation.dwHighDateTime}<<32)|creation.dwLowDateTime)==request.expected_process_creation_filetime_100ns;
}
bool Owner(const NormalExitMapContextV1 &ctx,const MainThreadQueryMailboxV1 &mailbox,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  return ctx.ticket.sequence!=0 && ctx.owner_executor_context &&
      IsIngameUiPausedOwnerStampV1(mailbox,stamp,GetCurrentThreadId()) &&
      mailbox.state.load(std::memory_order_acquire)==MainThreadQueryMailboxStateV1::executing &&
      !mailbox.stop_requested.load(std::memory_order_acquire) && mailbox.failure_flags.load(std::memory_order_acquire)==0 &&
      mailbox.published_sequence.load(std::memory_order_acquire)==ctx.ticket.sequence &&
      mailbox.permitted_frontend_executor && mailbox.executor==mailbox.permitted_frontend_executor &&
      mailbox.executor_context==ctx.owner_executor_context;
}
bool Frame(const NormalExitMapContextV1 &ctx,const MainThreadExecutionStampV1 &stamp,
    game::Snapshot &snapshot) noexcept {
  return ctx.game && game::ReadSnapshot(*ctx.game,snapshot) && snapshot==ctx.expected_snapshot &&
      snapshot.paused && snapshot.map_ready && snapshot.has_played_character && snapshot.played_character_alive &&
      snapshot.played_character_id>0 && static_cast<std::uint32_t>(snapshot.played_character_id)==ctx.request.expected_player_character_id &&
      snapshot.date_raw==stamp.date_raw;
}
bool Inspect(std::size_t index,const ZhongguoScoreboardNativeEnvironmentV1 &env,
    ZhongguoScoreboardActionDispatchEnvironmentV1 &dispatch,Census &census) {
  auto &out=census.observations[index]; const auto &fixed=kTargets[index];
  ZhongguoScoreboardAccessV1 access{};
  auto &root=census.roots[index]; auto &target=census.targets[index]; auto &vtable=census.vtables[index];
  if(!ResolveNamedGuiWidgetV1(env,access,fixed.root,fixed.leaf,root,target)) return false;
  out.root_exists=root!=nullptr; out.target_exists=target!=nullptr;
  if(!root) { out.read_complete=target==nullptr; return out.read_complete; }
  std::string root_name; void *root_vtable=nullptr; bool root_enabled=false;
  if(!ReadGuiWidgetRuntimeV1(access,root,root_name,root_vtable,out.root_visible,root_enabled) || root_name!=fixed.root) return false;
  NamedGuiTreeInspectionV1 tree{};
  if(!InspectNamedGuiSubtreeV1(access,env.module_base,root,fixed.root,tree) || !tree.root_available || tree.truncated ||
      tree.widget_count==0 || tree.widget_count!=tree.widgets.size()) return false;
  std::size_t count=0; const NamedGuiWidgetInspectionV1 *row=nullptr;
  for(const auto &candidate:tree.widgets) if(candidate.runtime_name==fixed.leaf) { ++count; row=&candidate; }
  out.unique_target=count==1;
  if(!target) { out.read_complete=count==0; return out.read_complete; }
  std::string target_name;
  if(count!=1 || !row || !ReadGuiWidgetRuntimeV1(access,target,target_name,vtable,out.target_visible,out.target_enabled) ||
      target_name!=fixed.leaf || out.target_visible!=row->effective_visible || out.target_enabled!=row->enabled) return false;
  const auto raw=reinterpret_cast<std::uintptr_t>(vtable);
  if(raw<env.module_base || raw-env.module_base>=GuiExactImageSizeV1(env.gui_abi_revision) ||
      raw-env.module_base!=row->vtable_rva) return false;
  out.target_vtable_rva=raw-env.module_base;
  out.dispatch_admitted=out.root_visible && out.unique_target && out.target_visible && out.target_enabled &&
      InspectFixedGuiWidgetDispatchAdmissionV1(dispatch,target,vtable);
  out.read_complete=true; return true;
}
bool ReadCensus(const ZhongguoScoreboardNativeEnvironmentV1 &env,
    ZhongguoScoreboardActionDispatchEnvironmentV1 &dispatch,Census &census) {
  census={}; ZhongguoScoreboardAccessV1 access{};
  if(!ResolveZhongguoScoreboardNativeGuiContextAndOwnerV1(env,access,census.context,census.owner)) return false;
  for(std::size_t i=0;i<kTargets.size();++i) if(!Inspect(i,env,dispatch,census)) return false;
  void *context=nullptr,*owner=nullptr;
  return ResolveZhongguoScoreboardNativeGuiContextAndOwnerV1(env,access,context,owner) && context==census.context && owner==census.owner;
}
bool Same(const Census &first,const Census &second) noexcept {
  return first.context==second.context && first.owner==second.owner && first.roots==second.roots &&
      first.targets==second.targets && first.vtables==second.vtables && first.observations==second.observations;
}
bool Current(NormalExitMapContextV1 &ctx,const MainThreadQueryMailboxV1 &mailbox,
    const MainThreadExecutionStampV1 &stamp,const ZhongguoScoreboardNativeEnvironmentV1 &env,
    ZhongguoScoreboardActionDispatchEnvironmentV1 &dispatch,Census &census) {
  game::Snapshot snapshot{}; bool stock=false; std::string reason;
  return Owner(ctx,mailbox,stamp) && Process(ctx.request) && Frame(ctx,stamp,snapshot) && Pins(env,dispatch) &&
      VerifyNormalExitMapSourcesV1(ctx.request.source_inventory_sha256,stock,reason) && stock && ReadCensus(env,dispatch,census);
}
bool Signature(NormalExitMapContextV1 &ctx,const MainThreadExecutionStampV1 &stamp,const Census &census) {
  auto &session=*ctx.session;
  if(session.query_epoch==(std::numeric_limits<std::uint64_t>::max)()) return false;
  std::string text="normal-exit-map-v1|"+ctx.request.source_inventory_sha256+"|"+ctx.request.request_nonce;
  const auto add=[&](auto value) { text+='|'; text+=std::to_string(value); };
  add(++session.query_epoch); add(ctx.native_revision); add(ctx.connection_generation);
  add(ctx.request.expected_game_pid); add(ctx.request.expected_process_creation_filetime_100ns);
  add(ctx.request.expected_player_character_id); add(stamp.thread_id); add(stamp.pump_epoch);
  add(ctx.expected_snapshot.date_raw); add(reinterpret_cast<std::uintptr_t>(census.context)); add(reinterpret_cast<std::uintptr_t>(census.owner));
  for(std::size_t i=0;i<kTargets.size();++i) {
    add(reinterpret_cast<std::uintptr_t>(census.roots[i])); add(reinterpret_cast<std::uintptr_t>(census.targets[i]));
    add(reinterpret_cast<std::uintptr_t>(census.vtables[i])); add(census.observations[i].dispatch_admitted);
    add(session.claimed[i].load(std::memory_order_acquire));
  }
  if(!NormalExitMapSha256V1(text,session.signature)) return false;
  session.queried_snapshot=ctx.expected_snapshot; session.queried_revision=ctx.native_revision;
  session.queried_generation=ctx.connection_generation; session.queried_inventory_sha256=ctx.request.source_inventory_sha256;
  session.queried_gui_context=census.context; session.queried_gui_owner=census.owner;
  session.queried_roots=census.roots; session.queried_targets=census.targets; session.queried_vtables=census.vtables;
  session.queried_observations=census.observations;
  ctx.observation.exit_context_signature=session.signature; return true;
}
bool BoundQuery(const NormalExitMapContextV1 &ctx,const Census &census) noexcept {
  const auto &s=*ctx.session;
  return !s.signature.empty() && ctx.request.expected_exit_context_signature==s.signature &&
      s.queried_revision==ctx.native_revision && s.queried_generation==ctx.connection_generation &&
      s.queried_inventory_sha256==ctx.request.source_inventory_sha256 && s.queried_snapshot==ctx.expected_snapshot &&
      s.queried_gui_context==census.context && s.queried_gui_owner==census.owner &&
      s.queried_roots==census.roots && s.queried_targets==census.targets && s.queried_vtables==census.vtables &&
      s.queried_observations==census.observations;
}
bool DispatchStage(std::size_t index,NormalExitMapContextV1 &ctx,const MainThreadQueryMailboxV1 &mailbox,
    const MainThreadExecutionStampV1 &stamp,const ZhongguoScoreboardNativeEnvironmentV1 &env,
    ZhongguoScoreboardActionDispatchEnvironmentV1 &dispatch,const Census &before,Census &after) {
  auto &out=ctx.observation; auto &d=out.dispatches[index]; Census fresh{};
  if(!Current(ctx,mailbox,stamp,env,dispatch,fresh) || !Same(fresh,before) || !fresh.observations[index].dispatch_admitted) {
    out.reason="predispatch_owner_frame_source_or_fixed_target_changed"; return false;
  }
  bool unclaimed=false;
  if(!ctx.session->claimed[index].compare_exchange_strong(unclaimed,true,std::memory_order_acq_rel,std::memory_order_acquire)) {
    out.reason="fixed_stage_already_consumed_no_retry"; return false;
  }
  d.claim_latched=true; out.status=NormalExitMapStatusV1::dispatch_unknown_claimed;
  out.reason="claimed_native_dispatch_requires_fresh_readback";
  d.dispatch_invoked=DispatchFixedGuiWidgetNativeV1(&dispatch,game::ZhongguoScoreboardActionV1::open,
      fresh.targets[index],fresh.vtables[index],d.native_handled);
  if(!d.dispatch_invoked) return false;
  d.post_read_complete=Current(ctx,mailbox,stamp,env,dispatch,after);
  if(d.post_read_complete) {
    out.targets=after.observations; out.confirmation_visible=after.observations[2].root_visible;
    d.postcondition_observed=index==0?after.observations[1].dispatch_admitted:
        index==1?after.observations[2].dispatch_admitted:false;
  }
  // Native boolean is diagnostic. This exit provider conservatively retains
  // unknown for false, even if a callback may have run. Claims never clear.
  if(!d.native_handled || !d.post_read_complete || after.context!=before.context || after.owner!=before.owner) return false;
  if(index==2) { out.status=NormalExitMapStatusV1::dispatch_pending; out.reason="desktop_dispatch_pending_independent_process_observation"; return true; }
  if(!d.postcondition_observed) { out.reason="opening_callback_postcondition_not_yet_observed_no_retry"; return false; }
  return true;
}
} // namespace

bool ExecuteNormalExitMapV1(NormalExitMapContextV1 &ctx,MainThreadQueryMailboxV1 &mailbox,
    const MainThreadExecutionStampV1 &stamp,const ZhongguoScoreboardNativeEnvironmentV1 &env,
    ZhongguoScoreboardActionDispatchEnvironmentV1 &dispatch) noexcept {
  auto &out=ctx.observation; out={}; out.action=ctx.request.action;
  out.native_revision=ctx.native_revision; out.connection_generation=ctx.connection_generation;
  out.game_pid=ctx.request.expected_game_pid; out.played_character_id=ctx.request.expected_player_character_id;
  out.process_creation_filetime_100ns=ctx.request.expected_process_creation_filetime_100ns; out.pump_epoch=stamp.pump_epoch;
  try {
    const auto reject=[&](const char *why) { out.reason=why; return true; };
    if(!kNormalExitMapV1CompiledEnabled) return reject("normal_exit_map_private_default_off");
    if(!ctx.game || !ctx.game->enabled() || ctx.game->descriptor().game_version!="1.20.0.3" ||
        ctx.game->descriptor().executable_sha256!="94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6" ||
        ctx.native_revision==0 || ctx.connection_generation==0 || ctx.request.expected_revision!=ctx.native_revision ||
        ctx.request.expected_connection_generation!=ctx.connection_generation || !ctx.session ||
        NormalExitMapActionNameV1(ctx.request.action).empty()) return reject("exact_paused_map_request_binding_unavailable");
    out.exact_build_verified=true;
    if(!Owner(ctx,mailbox,stamp)) return reject("paused_owner_ticket_tls_unverified"); out.owner_verified=true;
    if(!Process(ctx.request)) return reject("retained_process_identity_changed"); out.process_identity_verified=true;
    auto &session=*ctx.session;
    if(session.process_pid==0) {
      session.process_pid=ctx.request.expected_game_pid;
      session.process_creation_filetime_100ns=ctx.request.expected_process_creation_filetime_100ns;
    }
    if(session.process_pid!=ctx.request.expected_game_pid ||
        session.process_creation_filetime_100ns!=ctx.request.expected_process_creation_filetime_100ns)
      return reject("persistent_claim_process_binding_changed");
    if(!Pins(env,dispatch)) return reject("exact_gui_code_pins_changed"); out.source_abi_pins_verified=true;
    if(!VerifyNormalExitMapSourcesV1(ctx.request.source_inventory_sha256,out.stock_files_verified,out.reason)) return true;
    out.loaded_source_binding_verified=true;
    game::Snapshot before{};
    if(!Frame(ctx,stamp,before)) return reject("fresh_alive_paused_map_frame_changed"); out.frame_verified=true;
    Census initial{},verified{};
    if(!ReadCensus(env,dispatch,initial) || !Current(ctx,mailbox,stamp,env,dispatch,verified) || !Same(initial,verified))
      return reject("fresh_fixed_targets_census_changed");
    out.targets=initial.observations; out.confirmation_visible=initial.observations[2].root_visible;
    if(ctx.request.action==NormalExitMapActionV1::query_context) {
      session.signature.clear();
      if(!Signature(ctx,stamp,initial)) return reject("backend_context_signature_unavailable");
      out.status=NormalExitMapStatusV1::context_observed; out.reason="fresh_backend_context_observed"; return true;
    }
    if(!BoundQuery(ctx,initial)) return reject("fresh_backend_query_signature_mismatch");
    out.context_signature_verified=true;
    out.exit_context_signature=session.signature;
    // A mutation consumes this query authorization before any native action.
    // A later read-only query can issue a fresh signature but never resets CAS.
    session.signature.clear();
    if(ctx.request.action==NormalExitMapActionV1::confirm_desktop) {
      if(!initial.observations[2].dispatch_admitted) return reject("fresh_official_desktop_confirmation_not_admitted");
      Census after{}; DispatchStage(2,ctx,mailbox,stamp,env,dispatch,initial,after); return true;
    }
    if(initial.observations[2].dispatch_admitted) {
      out.status=NormalExitMapStatusV1::confirmation_observed; out.reason="official_confirmation_already_visible_observed"; return true;
    }
    Census menu=initial;
    if(!initial.observations[1].dispatch_admitted) {
      if(!initial.observations[0].dispatch_admitted) return reject("fixed_visible_map_menu_button_not_admitted");
      if(!DispatchStage(0,ctx,mailbox,stamp,env,dispatch,initial,menu)) return true;
    }
    Census confirmation{};
    if(!DispatchStage(1,ctx,mailbox,stamp,env,dispatch,menu,confirmation)) return true;
    out.status=NormalExitMapStatusV1::confirmation_observed;
    out.confirmation_visible=true; out.reason="official_resign_confirmation_freshly_observed";
    // The enclosing mailbox keeps its existing ReadExecutionStamp and
    // SameExecutionBoundary rule unchanged, including synchronous teardown drift.
    return true;
  } catch(...) {
    bool claimed=false; for(const auto &d:out.dispatches) claimed=claimed||d.claim_latched;
    out.status=claimed?NormalExitMapStatusV1::dispatch_unknown_claimed:NormalExitMapStatusV1::unavailable;
    out.orderly_exit_verified=false; out.autosave_verified=false;
    try { out.reason="normal_exit_map_provider_exception"; } catch(...) {}
    return true;
  }
}
} // namespace xar::ck3_12003
