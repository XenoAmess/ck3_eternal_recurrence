std::vector<std::pair<std::string,std::string>> g_wire;
constexpr const char *kActualSourceSha="98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
std::array<U,5> g_targets{};
U __fastcall RtOriginalGateway(void *c,std::int32_t resource,std::int64_t amount,std::int32_t component) noexcept {
  auto &w=*g_world;++w.gateways;w.received_character=reinterpret_cast<U>(c);
  w.received_resource=resource;w.received_amount=amount;w.received_component=component;
  if(resource==0 || resource==3)
    reinterpret_cast<WarPaymentWriterOriginal12004>(g_targets[resource==0?3:4])(w.Wrapper(resource==3),amount,c);
  return kGatewayReturn;
}
U __fastcall RtOriginalTransition(void *a,void *p) noexcept {
  auto &w=*g_world;++w.transitions;if(a!=w.Army() || p!=w.Province())return 0;
  reinterpret_cast<WarPaymentGatewayOriginal12004>(g_targets[1])(w.Character(),w.selected_resource,w.payment_amount,3);
  return kTransitionReturn;
}
struct RuntimeMemory {
  World *world=nullptr;
  int writes=0,protects=0,flushes=0,allocations=0,frees=0;
  int fail_write=0,fail_protect=0,fail_flush=0;
};
bool Owned(const RuntimeMemory &m,U address,std::size_t n) noexcept {
  for(const auto [begin,size]:m.world->code_ranges)
    if(address>=begin && address-begin<=size && n<=size-(address-begin))return true;
  return false;
}
void *Allocate(void *c,std::size_t n) noexcept {
  auto &m=*static_cast<RuntimeMemory*>(c);void *p=VirtualAlloc(nullptr,n,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE);
  if(p){m.world->code_ranges.push_back({reinterpret_cast<U>(p),n});++m.allocations;}return p;
}
bool Free(void *c,void *p) noexcept {
  auto &m=*static_cast<RuntimeMemory*>(c);const U address=reinterpret_cast<U>(p);
  if(!Owned(m,address,1) || !VirtualFree(p,0,MEM_RELEASE))return false;
  std::erase_if(m.world->code_ranges,[&](const auto &r){return r.first==address;});++m.frees;return true;
}
bool Write(void *c,U address,const void *data,std::size_t n) noexcept {
  auto &m=*static_cast<RuntimeMemory*>(c);if(++m.writes==m.fail_write)return false;
  if(!Owned(m,address,n))return false;std::memcpy(reinterpret_cast<void*>(address),data,n);return true;
}
bool Protect(void *c,void *p,std::size_t n,DWORD protection,DWORD &old) noexcept {
  auto &m=*static_cast<RuntimeMemory*>(c);if(++m.protects==m.fail_protect)return false;
  return Owned(m,reinterpret_cast<U>(p),n) && VirtualProtect(p,n,protection,&old)!=FALSE;
}
bool Flush(void *c,const void *p,std::size_t n) noexcept {
  auto &m=*static_cast<RuntimeMemory*>(c);if(++m.flushes==m.fail_flush)return false;
  return Owned(m,reinterpret_cast<U>(p),n) && FlushInstructionCache(GetCurrentProcess(),p,n)!=FALSE;
}
bool Pin(void *) noexcept {return true;}
void MakeTargets(RuntimeMemory &m) {
  const auto &descriptions=WarPaymentHookDescriptions12004();
  const std::array<U,5> originals{reinterpret_cast<U>(&RtOriginalTransition),reinterpret_cast<U>(&RtOriginalGateway),
    reinterpret_cast<U>(&OriginalAdd),reinterpret_cast<U>(&OriginalWriter),reinterpret_cast<U>(&OriginalWriter)};
  for(std::size_t i=0;i<5;++i) {
    auto *p=static_cast<unsigned char*>(Allocate(&m,4096));if(!p)std::terminate();g_targets[i]=reinterpret_cast<U>(p);
    const auto &d=descriptions[i];std::memcpy(p,d.prefix.data(),d.prefix_bytes);std::size_t n=d.prefix_bytes;
    const auto append=[&](std::initializer_list<unsigned char> bytes){for(const auto v:bytes)p[n++]=v;};
    if(i==0)append({0x48,0x83,0xC4,0x30,0x5B});
    if(i==1)append({0x48,0x8B,0x5C,0x24,0x38,0x48,0x8B,0x74,0x24,0x40,0x48,0x83,0xC4,0x20,0x5F});
    append({0x48,0xB8});std::memcpy(p+n,&originals[i],8);n+=8;append({0xFF,0xE0});
    DWORD old=0;if(!VirtualProtect(p,4096,PAGE_EXECUTE_READ,&old))std::terminate();
    if(!FlushInstructionCache(GetCurrentProcess(),p,n))std::terminate();
  }
}
WarPaymentInstallEnvironment12004 Environment(World &w,RuntimeMemory &m) {
  WarPaymentInstallEnvironment12004 e{};e.primary_thread_suspended_proven=true;
  e.module_base=reinterpret_cast<U>(GetModuleHandleW(nullptr));e.executable_sha256=kActualSourceSha;
  e.bindings=w.bindings;e.fixture_targets=true;e.target_overrides=g_targets;
  e.memory_context=&m;e.write=&Write;e.allocate=&Allocate;e.free=&Free;e.protect=&Protect;e.flush=&Flush;e.pin_module=&Pin;return e;
}
bool PrefixesRestored() {
  const auto &descriptions=WarPaymentHookDescriptions12004();
  for(std::size_t i=0;i<5;++i)
    if(std::memcmp(reinterpret_cast<const void*>(g_targets[i]),descriptions[i].prefix.data(),descriptions[i].prefix_bytes)!=0)return false;
  return true;
}
void DestroyTargets(RuntimeMemory &m) {for(auto p:g_targets)if(!Free(&m,reinterpret_cast<void*>(p)))std::terminate();g_targets={};}
void RuntimeCases() {
  {
    g_case="true_five_thunks_trampolines_ABI";World w;RuntimeMemory memory{};memory.world=&w;MakeTargets(memory);
    auto env=Environment(w,memory);WarPaymentDetourState12004 state{};
    Check(InstallWarPaymentPassive12004(state,env) && state.installed,"transactional_five_hook_install_on_fixture_owned_targets");
    if(state.installed) {
      Check(w.journal->SetEnabled(true).enabled,"sampling_explicitly_enabled_after_default_disabled_install");
      Abi(g_targets[0],{reinterpret_cast<U>(w.Army()),reinterpret_cast<U>(w.Province()),0,0},kTransitionReturn);
      Check(w.transitions==1 && w.gateways==1 && w.writers==1,"real_nested_thunks_all_originals_once");
      auto s=w.journal->Copy();const auto *leaf=Find(s,WarPaymentKind12004::personal_sub);
      Check(s.records.size()==3 && leaf && leaf->parent_transition_army==reinterpret_cast<U>(w.Army()) && leaf->parent_gateway_character==reinterpret_cast<U>(w.Character()),"real_TLS_nesting_and_actual_receiver_identities");
      Check(leaf && !leaf->source_boarding_call_chain_matches,"fixture_caller_RVAs_never_masquerade_as_game_source_PCs");
      Abi(g_targets[1],{reinterpret_cast<U>(w.Character()),3,700000,3},kGatewayReturn);
      Abi(g_targets[1],{reinterpret_cast<U>(w.Character()),0xFFFFFFFFU,0xFFF00000ABCD1234ULL,0xFFFFFFF9U},kGatewayReturn);
      Check(w.received_resource==-1 && w.received_component==-7 && static_cast<std::uint64_t>(w.received_amount)==0xFFF00000ABCD1234ULL,"real_gateway_thunk_preserves_signed_and_raw_arguments");
      Abi(g_targets[2],{reinterpret_cast<U>(w.Wrapper()),17,reinterpret_cast<U>(w.Character()),0},kWriterReturn);
      Abi(g_targets[3],{reinterpret_cast<U>(w.Wrapper()),19,reinterpret_cast<U>(w.Character()),0},kWriterReturn);
      Abi(g_targets[4],{reinterpret_cast<U>(w.Wrapper(true)),23,reinterpret_cast<U>(w.Character()),0},kWriterReturn);
      Check(w.transitions==1 && w.gateways==3 && w.writers==5 && state.active_calls==0,"all_five_runtime_hook_original_once_and_active_fence");
      Check(!UninstallWarPaymentPassive12004(state,false) && state.installed,"uninstall_requires_current_quiescent_proof");
      Check(UninstallWarPaymentPassive12004(state,true) && !state.installed && PrefixesRestored(),"uninstall_restores_exact_prefixes");
      Check(memory.allocations-memory.frees==5,"all_unreachable_trampolines_freed");
      const auto before=w.journal->Copy().latest_sequence;
      reinterpret_cast<WarPaymentWriterOriginal12004>(g_targets[2])(w.Wrapper(),1,w.Character());
      Check(w.journal->Copy().latest_sequence==before,"restored_original_target_has_no_observer");
    }
    DestroyTargets(memory);Check(memory.allocations==memory.frees,"fixture_memory_fully_released");
  }
  for(int mode=0;mode<3;++mode) {
    g_case=mode==0?"install_write_failure_rollback":mode==1?"install_protect_failure_rollback":"install_flush_failure_rollback";
    World w;RuntimeMemory memory{};memory.world=&w;MakeTargets(memory);
    if(mode==0)memory.fail_write=8;if(mode==1)memory.fail_protect=9;if(mode==2)memory.fail_flush=8;
    auto env=Environment(w,memory);WarPaymentDetourState12004 state{};
    const auto installed=InstallWarPaymentPassive12004(state,env);
    Check(!installed,"injected_transaction_failure_reported");
    if(state.installed)Check(UninstallWarPaymentPassive12004(state,true),"retained_reachable_state_can_be_safely_removed");
    Check(PrefixesRestored(),"earlier_published_targets_rolled_back");
    Check(memory.allocations-memory.frees==5,"failed_transaction_releases_only_unreachable_trampolines");
    DestroyTargets(memory);
  }
  {
    g_case="install_binding_and_prefix_gates";World w;RuntimeMemory memory{};memory.world=&w;MakeTargets(memory);
    auto env=Environment(w,memory);env.fixture_targets=false;
    const auto rejected=[&](const WarPaymentInstallEnvironment12004 &e){
      WarPaymentDetourState12004 state{};const bool ok=InstallWarPaymentPassive12004(state,e);
      if(state.installed && !UninstallWarPaymentPassive12004(state,true))std::terminate();return !ok;
    };
    Check(rejected(env),"target_override_requires_explicit_fixture_label");
    env.fixture_targets=true;env.primary_thread_suspended_proven=false;
    Check(rejected(env),"suspended_primary_proof_required");
    env.primary_thread_suspended_proven=true;env.executable_sha256="wrong";
    Check(rejected(env),"wrong_exact_EXE_identity_rejected");
    env.executable_sha256=kActualSourceSha;DWORD old=0;VirtualProtect(reinterpret_cast<void*>(g_targets[3]),4096,PAGE_READWRITE,&old);
    *reinterpret_cast<unsigned char*>(g_targets[3])=0x90;DWORD ignored=0;VirtualProtect(reinterpret_cast<void*>(g_targets[3]),4096,old,&ignored);
    Check(rejected(env),"wrong_literal_prefix_rejected");
    Check(memory.allocations-memory.frees==5,"prefix_failure_has_no_retained_unreachable_allocations");DestroyTargets(memory);
  }
  for(int mode=0;mode<2;++mode) {
    g_case=mode==0?"restore_flush_failure_retry":"restore_protection_failure_retry";
    World w;RuntimeMemory memory{};memory.world=&w;MakeTargets(memory);auto env=Environment(w,memory);WarPaymentDetourState12004 state{};
    Check(InstallWarPaymentPassive12004(state,env),"observer_installed_before_restore_failure");
    if(mode==0)memory.fail_flush=memory.flushes+1;else memory.fail_protect=memory.protects+2;
    Check(!UninstallWarPaymentPassive12004(state,true) && state.installed && PrefixesRestored(),"literal_prefix_restored_but_failed_flush_or_protection_keeps_ownership");
    memory.fail_flush=memory.fail_protect=0;
    const auto retried=UninstallWarPaymentPassive12004(state,true);
    Check(retried && !state.installed,"quiescent_retry_accepts_exact_already_restored_original_bytes");
    if(!retried) {
      // Fixture-only rescue after recording FAIL: re-publish this fixture's own
      // expected JMP so the old implementation can restore/release safely.
      // This is not a production recovery instruction or a test success.
      for(std::size_t i=0;i<5;++i)if(state.hooks[i].patch_may_be_present) {
        const auto &slot=state.hooks[i];std::array<unsigned char,16> patch{};patch.fill(0x90);
        patch[0]=0xFF;patch[1]=0x25;patch[2]=patch[3]=patch[4]=patch[5]=0;
        const auto target=WarPaymentEntryThunkAddress12004(static_cast<WarPaymentHook12004>(i));std::memcpy(patch.data()+6,&target,8);
        DWORD old=0,ignored=0;VirtualProtect(reinterpret_cast<void*>(slot.target),slot.size,PAGE_EXECUTE_READWRITE,&old);
        std::memcpy(reinterpret_cast<void*>(slot.target),patch.data(),slot.size);FlushInstructionCache(GetCurrentProcess(),reinterpret_cast<const void*>(slot.target),slot.size);
        VirtualProtect(reinterpret_cast<void*>(slot.target),slot.size,old,&ignored);
      }
      Check(UninstallWarPaymentPassive12004(state,true),"failed_retry_fixture_rescue_releases_ownership_without_UAF");
    }
    Check(PrefixesRestored() && memory.allocations-memory.frees==5,"final_owned_target_prefixes_restored_and_trampolines_released");DestroyTargets(memory);
  }
  {
    g_case="unknown_third_party_prefix_not_repaired";World w;RuntimeMemory memory{};memory.world=&w;MakeTargets(memory);
    auto env=Environment(w,memory);WarPaymentDetourState12004 state{};Check(InstallWarPaymentPassive12004(state,env),"observer_installed_before_external_byte_change");
    DWORD old=0,ignored=0;VirtualProtect(reinterpret_cast<void*>(g_targets[4]),16,PAGE_EXECUTE_READWRITE,&old);
    *reinterpret_cast<unsigned char*>(g_targets[4])=0xCC;VirtualProtect(reinterpret_cast<void*>(g_targets[4]),16,old,&ignored);
    Check(!UninstallWarPaymentPassive12004(state,true) && state.installed && *reinterpret_cast<unsigned char*>(g_targets[4])==0xCC,"unknown_bytes_rejected_without_overwriting_or_freeing_reachable_state");
    VirtualProtect(reinterpret_cast<void*>(g_targets[4]),16,PAGE_EXECUTE_READWRITE,&old);
    *reinterpret_cast<unsigned char*>(g_targets[4])=0xFF;FlushInstructionCache(GetCurrentProcess(),reinterpret_cast<void*>(g_targets[4]),16);
    VirtualProtect(reinterpret_cast<void*>(g_targets[4]),16,old,&ignored);
    Check(UninstallWarPaymentPassive12004(state,true) && PrefixesRestored(),"fixture_restores_its_own_known_JMP_before_safe_cleanup");DestroyTargets(memory);
  }
}
WarPaymentEnvelope12004 Envelope(World &w) {
  WarPaymentEnvelope12004 e{};e.machine_id=g_machine_id;e.executable_sha256=kActualSourceSha;
  e.current_session=w.session;e.installed=true;return e;
}
std::vector<ArmyNaturalPhaseRecord12004> NaturalRecords(World &w) {
  ArmyNaturalPhaseRecord12004 r{};r.scope=Natural(&w);r.original_called=r.original_returned=true;
  r.returned_event={reinterpret_cast<U>(&w),w.event+1,w.event_thread};r.returned_date_raw=123456;
  r.returned_absolute_day_raw=5144;r.same_clock_thread_order=true;return {r};
}
ArmyNaturalPhaseJournalStatus12004 NaturalStatus() {
  ArmyNaturalPhaseJournalStatus12004 s{};s.read_complete=true;s.retained_records=1;s.appended_records=1;return s;
}
void SaveWire(const char *name,const WarPaymentJournalSnapshot12004 &s,const WarPaymentEnvelope12004 &e,
    const std::vector<ArmyNaturalPhaseRecord12004> &n,const ArmyNaturalPhaseJournalStatus12004 &ns) {
  g_wire.push_back({name,SerializeWarPaymentJournal12004(s,e,n,ns)});
}
void SerializationCases() {
  {
    g_case="qualified_join_and_serialization";World w;Put(w.province,0x10,std::uint32_t{37});TransitionEntry(w.Army(),w.Province());
    const auto s=w.journal->Copy();const auto e=Envelope(w);const auto n=NaturalRecords(w);const auto ns=NaturalStatus();
    const auto q=QualifyWarPaymentDebits12004(s,e,n,ns);
    Check(q.size()==1 && q[0].payer_character_id==w.session.player_character_full_id && q[0].requested_amount_raw==500000 && q[0].account_kind==0,"full_surviving_natural_parent_gateway_writer_debit_join");
    SaveWire("qualified_personal",s,e,n,ns);
    auto lower=e;lower.executable_sha256="98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";
    Check(QualifyWarPaymentDebits12004(s,lower,n,ns).size()==q.size(),"same_actual_hex_SHA_case_has_identical_qualification");
    auto bad=s;std::erase_if(bad.records,[](const auto &r){return r.kind==WarPaymentKind12004::transition;});
    Check(QualifyWarPaymentDebits12004(bad,e,n,ns).empty(),"missing_transition_not_repaired_from_current_snapshot");SaveWire("missing_transition",bad,e,n,ns);
    bad=s;bad.overwritten=1;Check(QualifyWarPaymentDebits12004(bad,e,n,ns).empty(),"retention_loss_rejects_qualification");
    bad=s;bad.records[0].caller_return_rva=0xBAD;
    Check(QualifyWarPaymentDebits12004(bad,e,n,ns).empty(),"raw_writer_PC_rechecked_not_just_derived_flag");
    auto wrong=e;wrong.current_session.player_character_full_id=1;
    Check(QualifyWarPaymentDebits12004(s,wrong,n,ns).empty(),"historical_payer_not_inferred_as_different_current_owner");
    wrong=e;wrong.current_session.loaded_game_epoch=w.session.loaded_game_epoch.value()+1;
    Check(QualifyWarPaymentDebits12004(s,wrong,n,ns).empty(),"current_epoch_mismatch_rejected");
    wrong=e;++wrong.current_session.process_create_time_100ns;
    Check(QualifyWarPaymentDebits12004(s,wrong,n,ns).empty(),"current_process_creation_mismatch_rejected");
    wrong=e;++wrong.current_session.connection_generation;
    Check(QualifyWarPaymentDebits12004(s,wrong,n,ns).empty(),"current_connection_generation_mismatch_rejected");
    wrong=e;++wrong.current_session.pid;
    Check(QualifyWarPaymentDebits12004(s,wrong,n,ns).empty(),"current_PID_mismatch_rejected");
    wrong=e;wrong.executable_sha256="wrong";
    Check(QualifyWarPaymentDebits12004(s,wrong,n,ns).empty(),"wrong_actual_source_EXE_identity_rejected");
    auto no_return=n;no_return[0].original_returned=false;
    Check(QualifyWarPaymentDebits12004(s,e,no_return,ns).empty(),"natural_parent_return_required");
    no_return=n;no_return[0].returned_date_raw.reset();
    Check(QualifyWarPaymentDebits12004(s,e,no_return,ns).empty(),"natural_return_date_read_required");
    no_return=n;no_return[0].returned_absolute_day_raw.reset();
    Check(QualifyWarPaymentDebits12004(s,e,no_return,ns).empty(),"natural_return_absolute_day_read_required");
    no_return=n;no_return[0].returned_date_raw=123480;
    Check(QualifyWarPaymentDebits12004(s,e,no_return,ns).empty(),"natural_return_date_change_rejected");
    no_return=n;no_return[0].returned_absolute_day_raw=5145;
    Check(QualifyWarPaymentDebits12004(s,e,no_return,ns).empty(),"natural_return_absolute_day_change_rejected");
    wrong=e;wrong.install_failure_flags=1;
    Check(QualifyWarPaymentDebits12004(s,wrong,n,ns).empty(),"partial_or_failed_install_not_qualified_as_complete_observer");
    auto malformed=n;malformed[0].returned_event.clock_identity+=1;
    Check(QualifyWarPaymentDebits12004(s,e,malformed,ns).empty(),"natural_return_clock_identity_rechecked");
    auto failed_status=ns;failed_status.failed_appends=1;
    Check(QualifyWarPaymentDebits12004(s,e,n,failed_status).empty(),"missing_natural_history_not_hidden_by_present_parent");
    const auto appended=AppendWarPaymentJournal12004("{\"stock\":123,\"rate\":-5}",s,e,n,ns);
    g_wire.push_back({"existing_response_append",appended});
  }
  {
    g_case="qualified_land_serialization";World w;Put(w.province,0x10,std::uint32_t{38});w.selected_resource=3;
    TransitionEntry(w.Army(),w.Province());const auto s=w.journal->Copy();const auto e=Envelope(w);const auto n=NaturalRecords(w);const auto ns=NaturalStatus();
    const auto q=QualifyWarPaymentDebits12004(s,e,n,ns);Check(q.size()==1 && q[0].account_kind==3 && q[0].land_id==0x1234U,"Land_account_and_character_context_not_conflated");SaveWire("qualified_land",s,e,n,ns);
  }
  {
    g_case="partial_and_unknown_serialization";World w;w.reads_fail=true;TransitionEntry(w.Army(),w.Province());
    const auto s=w.journal->Copy();const auto e=Envelope(w);const auto n=NaturalRecords(w);const auto ns=NaturalStatus();
    Check(QualifyWarPaymentDebits12004(s,e,n,ns).empty(),"failed_reads_remain_unknown");SaveWire("failed_reads",s,e,n,ns);
  }
  for(const std::int64_t amount:std::array<std::int64_t,2>{0,-500000}) {
    g_case=amount==0?"zero_amount_not_actual_debit":"negative_amount_not_actual_debit";
    World w;Put(w.province,0x10,std::uint32_t{39});w.payment_amount=amount;TransitionEntry(w.Army(),w.Province());
    const auto s=w.journal->Copy();const auto e=Envelope(w);const auto n=NaturalRecords(w);const auto ns=NaturalStatus();
    Check(QualifyWarPaymentDebits12004(s,e,n,ns).empty(),"only_actual_nonzero_debit_promoted");SaveWire(amount==0?"zero_amount":"negative_amount",s,e,n,ns);
  }
  {
    g_case="generic_writer_and_signed_arguments_wire";World w;
    AddEntry(w.Wrapper(),17,w.Character());SubEntry(w.Wrapper(),19,w.Character());LandEntry(w.Wrapper(true),23,w.Character());
    GatewayEntry(w.Character(),-1,static_cast<std::int64_t>(0xFFF00000ABCD1234ULL),-7);
    const auto s=w.journal->Copy();const auto e=Envelope(w);const auto n=NaturalRecords(w);const auto ns=NaturalStatus();
    Check(s.records.size()==4 && QualifyWarPaymentDebits12004(s,e,n,ns).empty(),"unknown_writer_callers_retained_without_boarding_or_maintenance_claim");
    SaveWire("generic_writer_signed_args",s,e,n,ns);
  }
  {
    g_case="controlled_window_qualification_wire";World w;Put(w.province,0x10,std::uint32_t{40});
    w.session.loaded_game_epoch.reset();w.session.same_owned_process_no_load_window=true;w.session.controlled_window_id=891;
    TransitionEntry(w.Army(),w.Province());const auto s=w.journal->Copy();auto e=Envelope(w);e.controlled_window_admitted=true;
    const auto n=NaturalRecords(w);const auto ns=NaturalStatus();
    Check(QualifyWarPaymentDebits12004(s,e,n,ns).size()==1,"explicit_owned_process_window_qualifies_without_fabricated_load_epoch");
    SaveWire("controlled_window_personal",s,e,n,ns);e.controlled_window_admitted=false;
    Check(QualifyWarPaymentDebits12004(s,e,n,ns).empty(),"controlled_window_requires_explicit_admission");SaveWire("controlled_window_not_admitted",s,e,n,ns);
  }
}
