// Included in the existing exact readonly implementation's private namespace.
// No function in this reader calls Game/GUI code or dereferences a widget.
bool ReadGuiRootIndexV1([[maybe_unused]]ReadonlyContext &q,
    [[maybe_unused]]const ck3_11906::MainThreadExecutionStampV1 &stamp,
    [[maybe_unused]]const ck3_1210::CoreSnapshotPrefix &core,
    [[maybe_unused]]GuiRootIndexV1 &out) noexcept {
#if !defined(XAR_CK3_ENABLE_121003_26785313_GUI_ROOT_INDEX_V1)
  return false;
#else
  try {
    const auto unexpired=[&]() {
      const auto wall=std::chrono::duration_cast<std::chrono::milliseconds>(
          std::chrono::system_clock::now().time_since_epoch()).count();
      return q.gui_root_request && wall>=0 &&
          static_cast<std::uint64_t>(wall)<q.gui_root_request->deadline_unix_ms;
    };
    if(!q.gui_root_request || !q.gui_root_request->connection_generation || !unexpired() ||
        !Same(q.gui_root_request->expected_core,core) || !Owner(q,stamp) ||
        !VerifyGuiRootIndexImageV1(q.bindings.module_base))return false;
    const auto base=q.bindings.module_base;
    GuiRootIndexV1 value{};
    value.connection_generation=q.gui_root_request->connection_generation;
    value.ticket_sequence=q.ticket.sequence;value.pump_epoch=stamp.pump_epoch;
    value.owner_thread_id=stamp.thread_id;
    std::uintptr_t vtable=0;
    if(!At(reinterpret_cast<std::uintptr_t>(q.bindings.core.jomini_state_slot),0,value.logical_owner) ||
        !At(value.logical_owner,0x18,value.application) || !At(value.application,0,vtable) ||
        vtable!=base+kGuiRootApplicationVtableRvaV1 ||
        !At(value.application,0x1B8,value.first) || !At(value.first,0x58,value.context) ||
        !value.context)return false;
    value.manager=base+kGuiRootManagerRvaV1;
    if(!At(value.manager,0,vtable) || vtable!=base+kGuiRootManagerVtableRvaV1 ||
        !At(value.manager,0x30,value.data) || !At(value.manager,0x38,value.capacity) ||
        !At(value.manager,0x3C,value.count) || value.count<0 || value.capacity<value.count ||
        static_cast<std::size_t>(value.count)>kGuiRootIndexMaximumEntriesV1 ||
        (value.count && !value.data))return false;
    std::unordered_set<std::uintptr_t> objects,widgets;
    value.entries.reserve(static_cast<std::size_t>(value.count));
    for(std::int32_t i=0;i<value.count;++i) {
      GuiRootIndexEntryV1 entry{};
      if(!At(value.data,static_cast<std::size_t>(i)*sizeof(std::uintptr_t),entry.object) ||
          !entry.object || !objects.insert(entry.object).second || !At(entry.object,0,vtable) ||
          vtable!=base+kGuiRootEntryVtableRvaV1 || !At(entry.object,0x60,entry.widget) ||
          !At(entry.object,0x68,entry.context) || entry.context!=value.context ||
          (entry.widget && !widgets.insert(entry.widget).second))return false;
      value.entries.push_back(entry);
    }
    // All identity-bearing fields are re-read before the second Core/owner
    // sample. A root index is not a complete widget tree or an action token.
    std::uintptr_t logical_owner=0,application=0,first=0,context=0,data=0;
    std::int32_t count=0,capacity=0;
    if(!At(reinterpret_cast<std::uintptr_t>(q.bindings.core.jomini_state_slot),0,logical_owner) ||
        logical_owner!=value.logical_owner || !At(logical_owner,0x18,application) ||
        application!=value.application || !At(application,0,vtable) ||
        vtable!=base+kGuiRootApplicationVtableRvaV1 || !At(application,0x1B8,first) ||
        first!=value.first || !At(first,0x58,context) || context!=value.context ||
        !At(value.manager,0,vtable) || vtable!=base+kGuiRootManagerVtableRvaV1 ||
        !At(value.manager,0x30,data) || data!=value.data ||
        !At(value.manager,0x38,capacity) || capacity!=value.capacity ||
        !At(value.manager,0x3C,count) || count!=value.count)return false;
    for(std::size_t i=0;i<value.entries.size();++i) {
      const auto &entry=value.entries[i];GuiRootIndexEntryV1 again{};
      if(!At(data,i*sizeof(std::uintptr_t),again.object) || again.object!=entry.object ||
          !At(again.object,0,vtable) || vtable!=base+kGuiRootEntryVtableRvaV1 ||
          !At(again.object,0x60,again.widget) || !At(again.object,0x68,again.context) ||
          again!=entry)return false;
    }
    if(!unexpired() || !Owner(q,stamp))return false;
    out=std::move(value);return true;
  } catch(...) {return false;}
#endif
}
