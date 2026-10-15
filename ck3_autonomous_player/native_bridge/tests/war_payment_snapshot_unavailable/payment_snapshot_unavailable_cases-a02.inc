// Candidate narrow regression: included after B's immutable production-window
// fixture helpers. Exercises the new production guard with real Window/Journal/
// original-once callbacks and the existing fixture-owned memory reader.
// The full cache is deliberately unavailable at the bridge call boundary; this
// does not claim to instantiate/qualify the real WorkerAdapter cache machinery.
struct IdentityCoreFixture12004 {
  WarPaymentCurrentFrame12004 current{};
  bool readable=true;
  unsigned calls=0;
};
bool FixtureIdentityCore12004(void *context,WarPaymentCurrentFrame12004 &out) noexcept {
  auto &f=*static_cast<IdentityCoreFixture12004 *>(context);++f.calls;out={};
  if(!f.readable)return false;
  out=f.current;return true;
}
void ConnectWindowForUnavailable12004(World &w,WindowMemory &memory,WarPaymentWindow12004 &window) {
  w.bindings.read=&WindowRead;w.bindings.read_context=&memory;
  w.bindings.session=&ReadWarPaymentWindowSession12004;w.bindings.session_context=&window;
  w.bindings.retain_actor=&RetainWarPaymentWindowActor12004;w.bindings.retain_actor_context=&window;
}
void SnapshotUnavailableCases12004() {
  {
    g_case="snapshot_unavailable_fresh_identity_preserves_retained_evidence";
    World w;WindowMemory memory(w);WarPaymentWindow12004 window{};NaturalDependency();
    ConfigureWarPaymentWindow12004(window,memory.base,&WindowRead,&memory,*w.journal);
    auto f=Current(w);Check(Enable(window,f).accepted,"explicit_start_before_unavailability");
    ConnectWindowForUnavailable12004(w,memory,window);
    SubEntry(w.Wrapper(),23,w.Character());
    const auto before=w.journal->Copy();const auto session=ReadWarPaymentWindowSession12004(&window);
    Check(before.records.size()==1 && w.writers==1,"seed_is_actual_production_seam_record_and_original_once");
    IdentityCoreFixture12004 core{f};core.current.paused=false;
    core.current.native_date_raw=123480;
    Put(memory.state,8,std::uint64_t{123480});Put(memory.state,0x9C,std::uint32_t{5145});
    Check(RefreshWarPaymentIdentityAfterSnapshotUnavailable12004(window,&FixtureIdentityCore12004,&core),"unavailable_full_cache_uses_fresh_core_and_remains_admitted");
    const auto after=w.journal->Copy();const auto current=ReadWarPaymentWindowSession12004(&window);
    Check(core.calls==1 && window.admitted && after.sampling.enabled,"fresh_identity_was_actually_read_and_sampling_stays_on");
    Check(after.sampling.epoch==before.sampling.epoch && current.controlled_window_id==session.controlled_window_id,"sampling_epoch_and_explicit_window_identity_unchanged");
    Check(after.records.size()==before.records.size() && after.latest_sequence==before.latest_sequence &&
      after.oldest_sequence==before.oldest_sequence && after.overwritten==before.overwritten,"existing_records_and_sequence_history_not_cleared");
    Check(after.records.size()==1 && before.records.size()==1 && after.records[0].amount_raw==before.records[0].amount_raw && after.records[0].before.wrapper_balance_bits==before.records[0].before.wrapper_balance_bits &&
      after.records[0].after.wrapper_balance_bits==before.records[0].after.wrapper_balance_bits,"raw_retained_payment_record_values_preserved");
    Check(current.native_date_raw==123480 && current.absolute_day_raw==5145U && current.snapshot_revision==f.snapshot_revision,"forward_unpaused_identity_check_updates_clock_without_new_public_revision");
    Check(w.writers==1,"identity_fallback_never_executes_or_retries_payment_original");
    Check(RefreshWarPaymentIdentityAfterSnapshotUnavailable12004(window,&FixtureIdentityCore12004,&core) &&
      w.journal->Copy().sampling.epoch==before.sampling.epoch && core.calls==2,"repeated_full_cache_gaps_do_not_reenable_or_advance_epoch");
  }
  for(int mode=0;mode<12;++mode) {
    constexpr const char *names[]={"owner_changed","map_not_ready","actor_dead","connection_changed","identity_core_unreadable","game_state_changed","native_date_rollback","absolute_day_rollback","state_read_failed","natural_disabled","player_zero","player_invalid"};
    g_case=names[mode];
    World w;WindowMemory memory(w);WarPaymentWindow12004 window{};NaturalDependency();
    ConfigureWarPaymentWindow12004(window,memory.base,&WindowRead,&memory,*w.journal);
    auto f=Current(w);Check(Enable(window,f).accepted,"negative_case_has_real_admitted_window");
    ConnectWindowForUnavailable12004(w,memory,window);SubEntry(w.Wrapper(),23,w.Character());
    const auto before=w.journal->Copy();IdentityCoreFixture12004 core{f};
    if(mode==0)++core.current.player_character_full_id;
    if(mode==1)core.current.map_ready=false;
    if(mode==2)core.current.alive=false;
    if(mode==3)++core.current.connection_generation;
    if(mode==4)core.readable=false;
    if(mode==5)memory.selected=reinterpret_cast<U>(memory.alternate.data());
    if(mode==6){core.current.native_date_raw=123432;Put(memory.state,8,std::uint64_t{123432});}
    if(mode==7)Put(memory.state,0x9C,std::uint32_t{5143});
    if(mode==8)memory.fail=true;
    if(mode==9)NaturalDependency(false);
    if(mode==10)core.current.player_character_full_id=0;
    if(mode==11)core.current.player_character_full_id=0xFFFFFFFFU;
    Check(!RefreshWarPaymentIdentityAfterSnapshotUnavailable12004(window,&FixtureIdentityCore12004,&core),"actual_guard_refuses_changed_or_unreadable_identity");
    const auto after=w.journal->Copy();const auto current=ReadWarPaymentWindowSession12004(&window);
    Check(!window.admitted && !after.sampling.enabled && after.sampling.clear_completed &&
      !current.same_owned_process_no_load_window && !current.controlled_window_id,"original_failclosed_window_and_clear_contract_preserved");
    Check(after.records.empty() && after.sampling.epoch>before.sampling.epoch && w.writers==1,"true_failure_clears_actual_seed_record_without_replaying_writer");
    if(mode==4)Check(window.reason=="identity_core_read_failed" && core.calls==1,"true_core_failure_has_specific_reason");
  }
  for(int mode=0;mode<2;++mode) {
    g_case="snapshot_unavailable_never_implicitly_admits";
    World w;WindowMemory memory(w);WarPaymentWindow12004 window{};NaturalDependency();
    ConfigureWarPaymentWindow12004(window,memory.base,&WindowRead,&memory,*w.journal);
    auto f=Current(w);
    if(mode==1){Check(Enable(window,f).accepted,"explicit_start_for_disabled_case");
      Check(ControlWarPaymentWindow12004(window,"disable","",g_machine_id,f).accepted,"explicitly_disabled_before_gap");}
    const auto before=w.journal->Copy();IdentityCoreFixture12004 core{f};
    Check(!RefreshWarPaymentIdentityAfterSnapshotUnavailable12004(window,&FixtureIdentityCore12004,&core),"inactive_window_not_admitted_by_valid_fallback_frame");
    const auto after=w.journal->Copy();
    Check(core.calls==0 && !window.admitted && !after.sampling.enabled && after.sampling.epoch==before.sampling.epoch,"inactive_fallback_has_no_read_enable_or_epoch_side_effect");
  }
}
