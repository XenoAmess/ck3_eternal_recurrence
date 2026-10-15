struct WindowMemory {
  World *world=nullptr;U base=0x10000;
  std::array<unsigned char,0xB0> state{},alternate{};
  U selected=0;bool fail=false;
  std::array<unsigned char,0x400> npc{},npc_extension{};
  explicit WindowMemory(World &w):world(&w) {
    selected=reinterpret_cast<U>(state.data());Put(state,8,std::uint64_t{123456});Put(state,0x9C,std::uint32_t{5144});
    Put(alternate,8,std::uint64_t{123456});Put(alternate,0x9C,std::uint32_t{5144});
    Put(npc,0x18,std::uint32_t{0x12345678});Put(npc,0x1C,std::uint32_t{0x43686172});
    Put(npc,0x1B0,reinterpret_cast<U>(npc_extension.data()));Put(npc_extension,0x100,std::uint64_t{70000000});
  }
};
bool WindowRead(void *context,U address,void *out,std::size_t n) noexcept {
  auto &m=*static_cast<WindowMemory*>(context);if(m.fail)return false;
  if(address==m.base+0x5C68C50 && n==sizeof m.selected){std::memcpy(out,&m.selected,n);return true;}
  for(const auto [p,size]:std::array<std::pair<const unsigned char*,std::size_t>,4>{{
      {m.state.data(),m.state.size()},{m.alternate.data(),m.alternate.size()},
      {m.npc.data(),m.npc.size()},{m.npc_extension.data(),m.npc_extension.size()}}}) {
    const U begin=reinterpret_cast<U>(p);if(address>=begin && address-begin<=size && n<=size-(address-begin)) {
      std::memcpy(out,reinterpret_cast<const void*>(address),n);return true;
    }
  }
  return Read(m.world,address,out,n);
}
WarPaymentCurrentFrame12004 Current(World &w) {
  WarPaymentCurrentFrame12004 f{};f.connection_generation=w.session.connection_generation;
  f.snapshot_revision=4;f.native_date_raw=123456;f.player_character_full_id=w.session.player_character_full_id.value();
  f.paused=f.map_ready=f.alive=true;return f;
}
void NaturalDependency(bool enabled=true,bool busy=false) {
  fixture_natural_dependency::state={true,enabled,busy,false,77,busy?1ULL:0ULL,0,0};
}
WarPaymentWindowControl12004 Enable(WarPaymentWindow12004 &window,const WarPaymentCurrentFrame12004 &f) {
  return ControlWarPaymentWindow12004(window,"enable","same_owned_process_no_load_v1",g_machine_id,f);
}
void WindowCases() {
  {
    g_case="production_window_enable_lifecycle";World w;WindowMemory memory(w);WarPaymentWindow12004 window{};NaturalDependency();
    ConfigureWarPaymentWindow12004(window,memory.base,&WindowRead,&memory,*w.journal);
    auto f=Current(w);const auto enabled=Enable(window,f);auto session=ReadWarPaymentWindowSession12004(&window);
    Check(enabled.accepted && window.admitted && session.pid==GetCurrentProcessId() && session.process_create_time_100ns==w.session.process_create_time_100ns,"actual_process_and_explicit_window_start");
    Check(!session.loaded_game_epoch && session.same_owned_process_no_load_window && session.controlled_window_id && session.game_state_identity_witness==memory.selected,"window_metadata_not_fabricated_load_epoch");
    const auto id=session.controlled_window_id;const auto again=Enable(window,f);
    Check(again.accepted && ReadWarPaymentWindowSession12004(&window).controlled_window_id==id,"idempotent_enable_preserves_window_and_sampling_epoch");
    Put(memory.state,8,std::uint64_t{123480});Put(memory.state,0x9C,std::uint32_t{5145});f.native_date_raw=123480;f.paused=false;++f.snapshot_revision;
    ObserveWarPaymentWindowFrame12004(window,f);session=ReadWarPaymentWindowSession12004(&window);
    Check(window.admitted && session.native_date_raw==123480 && session.absolute_day_raw==5145U && session.controlled_window_id==id,"legitimate_forward_day_and_unpaused_march_do_not_end_window");
    auto disabled=ControlWarPaymentWindow12004(window,"disable","",g_machine_id,f);
    Check(disabled.accepted && !window.admitted && w.journal->Copy().sampling.clear_completed,"disable_clears_own_journal");
    f.paused=true;const auto reenabled=Enable(window,f);
    Check(reenabled.accepted && ReadWarPaymentWindowSession12004(&window).controlled_window_id!=id,"new_window_has_new_control_identity");
  }
  {
    g_case="production_window_explicit_admission";World w;WindowMemory memory(w);WarPaymentWindow12004 window{};NaturalDependency();
    ConfigureWarPaymentWindow12004(window,memory.base,&WindowRead,&memory,*w.journal);auto f=Current(w);
    Check(!ControlWarPaymentWindow12004(window,"enable","wrong",g_machine_id,f).accepted,"no_implicit_no_load_contract");
    Check(!ControlWarPaymentWindow12004(window,"enable","same_owned_process_no_load_v1","Desktop 3",f).accepted,"noncanonical_machine_id_rejected");
    NaturalDependency(true,true);Check(!Enable(window,f).accepted,"busy_natural_sampler_cannot_start_window");
    NaturalDependency(false);Check(!Enable(window,f).accepted,"disabled_natural_sampler_cannot_start_window");
    NaturalDependency();f.paused=false;Check(!Enable(window,f).accepted,"start_requires_paused_current_frame");
    f.paused=true;f.native_date_raw=123480;Check(!Enable(window,f).accepted,"mismatched_current_date_and_owned_state_rejected");
  }
  for(int mode=0;mode<9;++mode) {
    g_case="production_window_invalidation_matrix";World w;WindowMemory memory(w);WarPaymentWindow12004 window{};NaturalDependency();
    ConfigureWarPaymentWindow12004(window,memory.base,&WindowRead,&memory,*w.journal);auto f=Current(w);
    Check(Enable(window,f).accepted,"invalidation_case_starts_from_admitted_window");
    if(mode==0)++f.connection_generation;
    if(mode==1)++f.player_character_full_id;
    if(mode==2)f.map_ready=false;
    if(mode==3)f.alive=false;
    if(mode==4){f.native_date_raw=123432;Put(memory.state,8,std::uint64_t{123432});}
    if(mode==5)Put(memory.state,0x9C,std::uint32_t{5143});
    if(mode==6)memory.selected=reinterpret_cast<U>(memory.alternate.data());
    if(mode==7)memory.fail=true;
    if(mode==8)NaturalDependency(false);
    ObserveWarPaymentWindowFrame12004(window,f);const auto s=ReadWarPaymentWindowSession12004(&window);
    Check(!window.admitted && !s.same_owned_process_no_load_window && !s.controlled_window_id && !w.journal->Copy().sampling.enabled,"connection_owner_map_liveness_date_day_state_read_or_natural_change_stops_capture");
    Check(!s.loaded_game_epoch,"invalidation_never_creates_loaded_epoch");
  }
  {
    g_case="production_window_busy_disable";World w;WindowMemory memory(w);WarPaymentWindow12004 window{};NaturalDependency();
    ConfigureWarPaymentWindow12004(window,memory.base,&WindowRead,&memory,*w.journal);const auto f=Current(w);Check(Enable(window,f).accepted,"window_enabled_before_busy_disable");
    {
      army_observer_research_detail_12004::Permit permit(w.journal->mutex,w.journal->policy);
      const auto result=ControlWarPaymentWindow12004(window,"disable","",g_machine_id,f);
      Check(permit.admitted() && !result.accepted && result.reason=="clear_pending" && !window.admitted,"inflight_disable_reports_clear_pending_without_faking_clear");
    }
    const auto cleared=ControlWarPaymentWindow12004(window,"disable","",g_machine_id,f);
    Check(cleared.accepted && w.journal->Copy().sampling.clear_completed,"clear_completes_after_actual_capture_returns");
  }
  {
    g_case="production_window_actor_filter_connected";World w;WindowMemory memory(w);WarPaymentWindow12004 window{};NaturalDependency();
    ConfigureWarPaymentWindow12004(window,memory.base,&WindowRead,&memory,*w.journal);const auto f=Current(w);Check(Enable(window,f).accepted,"window_enabled_for_dynamic_actor_filter");
    w.bindings.read=&WindowRead;w.bindings.read_context=&memory;
    w.bindings.session=&ReadWarPaymentWindowSession12004;w.bindings.session_context=&window;
    w.bindings.retain_actor=&RetainWarPaymentWindowActor12004;w.bindings.retain_actor_context=&window;
    const auto before=w.journal->Copy().latest_sequence;
    SubEntry(memory.npc_extension.data()+0xF8,19,memory.npc.data());
    Check(w.writers==1 && w.journal->Copy().latest_sequence==before && Get<std::uint64_t>(memory.npc_extension,0x100)==69999981,"proven_other_character_calls_original_once_without_filling_player_ring");
    SubEntry(w.Wrapper(),23,w.Character());const auto s=w.journal->Copy();
    Check(w.writers==2 && s.records.size()==1 && s.records[0].before.character_id==w.session.player_character_full_id,"current_dynamic_owner_is_observed_through_same_core_seam");
    Put(memory.npc,0x1C,std::uint32_t{0});SubEntry(memory.npc_extension.data()+0xF8,29,memory.npc.data());
    Check(w.writers==3 && w.journal->Copy().records.size()==2,"unknown_identity_retained_instead_of_silently_classified_unrelated");
    Put(memory.npc,0x1C,std::uint32_t{0x43686172});Put(memory.npc,0x18,std::uint32_t{0xFFFFFFFFU});
    SubEntry(memory.npc_extension.data()+0xF8,31,memory.npc.data());
    Check(w.writers==4 && w.journal->Copy().records.size()==3,"invalid_fullID_is_unknown_not_proven_unrelated");
  }
  {
    g_case="production_inactive_query_fresh_binding";World w;WindowMemory memory(w);WarPaymentWindow12004 window{};NaturalDependency();
    ConfigureWarPaymentWindow12004(window,memory.base,&WindowRead,&memory,*w.journal);auto f=Current(w);Check(Enable(window,f).accepted,"window_enabled_before_current_owner_changes");
    ++f.connection_generation;++f.player_character_full_id;++f.snapshot_revision;ObserveWarPaymentWindowFrame12004(window,f);
    const auto query=ControlWarPaymentWindow12004(window,"query","",g_machine_id,f);
    WarPaymentDetourState12004 state{};const auto envelope=ReadWarPaymentWindowEnvelope12004(window,state);
    Check(query.accepted && !envelope.controlled_window_admitted && envelope.current_session.controlled_window_id==0 && !envelope.current_session.loaded_game_epoch,"explicit_inactive_query_never_implicitly_readmits_window");
    Check(!envelope.current_session.same_owned_process_no_load_window,"inactive_diagnostic_context_is_not_a_qualified_current_window");
  }
}
