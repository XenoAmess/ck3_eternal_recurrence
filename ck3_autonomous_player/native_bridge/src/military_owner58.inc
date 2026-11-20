// Included inside FlorinAdapter after SnapshotOwnerToken. This is a private
// production token, not a public bool/fixture/wire proof.
  struct MilitaryOwnerScope58 {
    const FlorinAdapter *adapter=nullptr;
    const ck3_1210::FullSnapshotBindingsV1 *bindings=nullptr;
    SnapshotOwnerToken owner{};
    std::uint64_t sequence=0;
    ck3_11906::MainThreadQueryExecutorV1 executor=nullptr;
    void *context=nullptr;
    xar::diagnostic81::RawFullCause *cause81=nullptr;
    xar::snapshot_observer92::View observer92{};
  };
  bool MilitaryTargets58(const ck3_1210::ArmyBaseBindingsV1 &b) const noexcept {
    __try {
      using namespace ck3_1210;
      const auto base=reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
      if(!base || !IsHotfix(core_.image_build))return false;
      const auto exact=BindArmyBaseImageV1(base,hotfix26757580::kExecutableSha256);
      const auto &a=b.player_armies;const auto &e=exact.player_armies;
      const auto &c=a.core;const auto &ec=e.core;
      if(!exact.exact_build_admitted || !b.exact_build_admitted || !a.exact_build_admitted ||
        !core_.enabled || !c.enabled || c.image_build!=core_.image_build || !ec.enabled ||
        c.game_state_slot!=ec.game_state_slot || c.jomini_state_slot!=ec.jomini_state_slot ||
        c.character_storage_slot!=ec.character_storage_slot || c.get_local_player!=ec.get_local_player ||
        core_.game_state_slot!=ec.game_state_slot || core_.jomini_state_slot!=ec.jomini_state_slot ||
        core_.character_storage_slot!=ec.character_storage_slot || core_.get_local_player!=ec.get_local_player ||
        a.unit_registry_slot!=e.unit_registry_slot || a.unit_registry_vtable!=e.unit_registry_vtable ||
        a.unit_manager_vtable!=e.unit_manager_vtable || a.get_unit_state!=e.get_unit_state ||
        b.native_army_registry_slot!=exact.native_army_registry_slot || b.no_army_fallback_slot!=exact.no_army_fallback_slot ||
        b.native_army_registry_vtable!=exact.native_army_registry_vtable || b.native_army_manager_vtable!=exact.native_army_manager_vtable ||
        b.native_army_vtable!=exact.native_army_vtable)return false;
      const auto *m=owner_mailbox_.load(std::memory_order_acquire);
      if(!m || m->offline_fixture || m->module_base!=base || m->tls_initialized_flag!=base+hotfix26757580::kTlsFlag ||
        reinterpret_cast<std::uintptr_t>(m->tls_context_getter)!=base+hotfix26757580::kTlsGetter ||
        *reinterpret_cast<const std::uint8_t*>(m->tls_initialized_flag)!=1)return false;
      // Do not enter the lazy TLS getter until its embedded CRT guard is warm.
      const auto slots=reinterpret_cast<void**>(__readgsqword(0x58));
      if(!slots || !slots[0])return false;
      const auto block=reinterpret_cast<std::uintptr_t>(slots[0]);
      if((*reinterpret_cast<const std::uint32_t*>(block+0x3620)&1U)==0 ||
        *reinterpret_cast<const std::uint8_t*>(block+0x3628+0x20)!=1)return false;
      return std::memcmp(reinterpret_cast<const void*>(a.get_unit_state),
        military_hotfix26757580::kStateEntry32.data(),military_hotfix26757580::kStateEntry32.size())==0;
    } __except(EXCEPTION_EXECUTE_HANDLER){return false;}
  }
  static bool AdmitMilitaryState58(void *context) noexcept {
    if(!context)return false;const auto &scope=*static_cast<const MilitaryOwnerScope58*>(context);
    const auto reject=[&](std::uint32_t why) noexcept {
      if(scope.cause81 && !scope.cause81->military_rejection)scope.cause81->military_rejection=why;
      return false;
    };
    if(!scope.adapter || !scope.bindings || !scope.owner.mailbox)return reject(1);
    const bool observer92=scope.observer92.generation!=0;
    if(!observer92 && (!scope.sequence || !scope.executor || !scope.context))return reject(1);
    const auto &b=*scope.bindings;const auto &p=b.army_base.player_armies;
    if(!b.enable_army_base || !p.integration_native_calls_permitted ||
      p.native_call_admission!=&AdmitMilitaryState58 || p.native_call_admission_context!=context)return reject(2);
    if(!scope.adapter->MilitaryTargets58(b.army_base))return reject(3);
    SnapshotOwnerToken current{};
    if(!scope.adapter->ReadCurrentSnapshotOwner(current) || current!=scope.owner)return reject(4);
    const auto &m=*scope.owner.mailbox;
    if(observer92) {
      const auto &v=scope.observer92;
      if(!xar::snapshot_observer92::ReadScope::Validate(v,*scope.adapter,m) ||
        v.stamp.pump_epoch!=scope.owner.pump_epoch || v.stamp.thread_id!=scope.owner.thread_id ||
        v.stamp.tls_context!=scope.owner.tls || v.stamp.game_state!=scope.owner.state ||
        v.stamp.jomini_state!=scope.owner.jomini || v.stamp.date_raw!=scope.owner.date_raw ||
        v.stamp.paused!=scope.owner.paused)return reject(4);
      return true;
    }
    const auto executor=m.executor.load();
    const bool registered=executor==m.permitted_executor || executor==m.permitted_executor_secondary ||
      executor==m.permitted_executor_tertiary || executor==m.permitted_executor_quaternary;
    if(!registered)return reject(5);
    if(executor!=scope.executor || m.executor_context!=scope.context)return reject(6);
    if(m.state.load()!=ck3_11906::MainThreadQueryMailboxStateV1::executing)return reject(7);
    if(m.published_sequence.load()!=scope.sequence || m.executor_started_sequence.load()!=scope.sequence)return reject(8);
    if(m.executor_started_pump_epoch.load()!=scope.owner.pump_epoch)return reject(9);
    if(m.pump_epochs.load()!=scope.owner.pump_epoch)return reject(10);
    if(m.stop_requested.load() || m.proof_reset_requested.load() || m.failure_flags.load()!=0 || m.active_hook_calls.load()==0)return reject(11);
    return true;
  }
