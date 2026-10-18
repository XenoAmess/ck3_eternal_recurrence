// Included inside ingame_ui_navigation_v1.cpp's private namespace, after
// Value/Slot/TypedObject/ResolveHandler and opening_source_pins12004.inc.
// Exact4 source candidate only; no build or live qualification is implied.
struct PresentationWindow12004 {
  void *window=nullptr,*root=nullptr;
  std::uint32_t subject=0;
  bool present=false,subject_available=false;
  bool operator==(const PresentationWindow12004 &) const = default;
};

bool PresentationProvince12004(std::uintptr_t base,std::uint32_t id,
                             void *&province) noexcept {
  province=nullptr;
  if(id==0 || id>0x7FFFFFFFU)return false;
  void *world=nullptr,*manager=nullptr,*rows=nullptr;
  std::int32_t count=0;std::uint32_t actual=0,magic=0;
  // CE0B80's int32 branch: map index, not a low24 TPdxRef storage lookup.
  return Slot(base+0x5C68C50,world) && world && Value(world,0xA0,manager) && manager &&
      Value(manager,0x140,rows) && rows && Value(manager,0x14C,count) && count>0 &&
      id<static_cast<std::uint32_t>(count) &&
      Value(rows,static_cast<std::size_t>(id)*sizeof(void *),province) && province &&
      Value(province,0x10,actual) && actual==id &&
      Value(province,0x85C,magic) && magic==0x50726F76U;
}

bool PresentationCharacter12004(std::uintptr_t base,std::uint32_t id,
                              void *&character) noexcept {
  std::uint32_t magic=0;
  return id!=0xFFFFFFFFU && Object(base,0x5C67568,id,0x18,character) &&
      Value(character,0x1C,magic) && magic==0x43686172U;
}

bool ReadPresentationOwnedWindow12004(
    const ZhongguoScoreboardNativeEnvironmentV1 &env,void *handler,
    IngameUiWindowKindV1 kind,PresentationWindow12004 &view,std::string &reason) {
  view={};reason.clear();
  const auto n=static_cast<std::uint32_t>(kind);
  const bool holding=n==9;
  if(!holding && n!=10){reason="presentation_window_kind_invalid";return false;}
  if(!env.exact_build_admitted || env.offline_fixture_function_overrides ||
     env.gui_abi_revision!=GuiAbiRevisionV1::crozier12004 || !env.module_base ||
     !Actual4UiBoundV1(env) || !PresentationOpeningSourcePins12004(env.module_base)) {
    reason="presentation_exact4_source_binding_unavailable";return false;
  }
  void *current_handler=nullptr;
  if(!ResolveHandler(env,current_handler) || current_handler!=handler) {
    reason="presentation_handler_binding_unavailable";return false;
  }
  ZhongguoScoreboardAccessV1 access{};
  void *context=nullptr,*owner=nullptr,*handler_owner=nullptr;
  if(!ResolveZhongguoScoreboardNativeGuiContextAndOwnerV1(env,access,context,owner) ||
     !context || !owner || !Value(handler,0x40,handler_owner) || handler_owner!=owner) {
    reason="presentation_current_gui_owner_unavailable";return false;
  }
  const std::size_t slot=holding?0xD0:0x5E0;
  void *window=nullptr;
  if(!Value(handler,slot,window)) {
    reason="presentation_window_slot_unreadable";return false;
  }
  // Readable null is explicit absence, not an invented subject ID zero.
  if(!window)return true;
  const auto base=env.module_base;
  const auto primary=holding?0x45434F0U:0x4592C08U;
  const auto secondary=holding?0x45434C8U:0x4592CD8U;
  const auto descriptor=holding?0x5769390U:0x57EB878U;
  const auto set_data=holding?0x12ACA30U:0x17E0F60U;
  const auto matches=holding?0x12ACA70U:0x17E1030U;
  std::uintptr_t vt=0,secondary_vt=0,set_slot=0,match_slot=0;
  void *back_owner=nullptr,*back_handler=nullptr,*native_root=nullptr;
  if(!Value(window,0,vt) || vt!=base+primary ||
     !Value(window,0x10,secondary_vt) || secondary_vt!=base+secondary ||
     !TypedObject(base,window,descriptor,UiExactImageSizeV1(env.gui_abi_revision)) ||
     !Value(reinterpret_cast<void *>(vt),0x90,set_slot) || set_slot!=base+set_data ||
     !Value(reinterpret_cast<void *>(vt),0x98,match_slot) || match_slot!=base+matches ||
     !Value(window,0x98,back_owner) || back_owner!=owner ||
     !Value(window,0xA0,back_handler) || back_handler!=handler ||
     !Value(window,0x60,native_root) || !native_root) {
    reason="presentation_window_type_owner_root_or_callbacks_unavailable";return false;
  }
  const std::string_view name=holding?"holding_view":"window_personal_beliefs";
  void *root=nullptr,*widget=nullptr,*root_vt=nullptr;
  std::string runtime_name;bool visible=false,enabled=false;
  if(!ResolveNamedGuiWidgetV1(env,access,name,name,root,widget) || root!=native_root ||
     widget!=root || !ReadGuiWidgetRuntimeV1(access,root,runtime_name,root_vt,visible,enabled) ||
     runtime_name!=name) {
    reason="presentation_fixed_owned_root_unavailable";return false;
  }
  PresentationWindow12004 candidate{};
  candidate.window=window;candidate.root=root;candidate.present=true;
  if(holding) {
    void *selected=nullptr,*resolved=nullptr;
    if(!Value(window,0xD8,selected)) {
      reason="presentation_selected_province_pointer_unreadable";return false;
    }
    if(selected) {
      std::uint32_t id=0;
      if(!Value(selected,0x10,id) || !PresentationProvince12004(base,id,resolved) || resolved!=selected) {
        reason="presentation_selected_province_namespace_unavailable";return false;
      }
      candidate.subject=id;candidate.subject_available=true;
    }
  } else {
    std::uint32_t id=0xFFFFFFFFU;void *character=nullptr;
    if(!Value(window,0xE8,id)) {
      reason="presentation_selected_character_id_unreadable";return false;
    }
    if(id!=0xFFFFFFFFU) {
      if(!PresentationCharacter12004(base,id,character)) {
        reason="presentation_selected_character_full_reference_unavailable";return false;
      }
      candidate.subject=id;candidate.subject_available=true;
    }
  }
  view=candidate;return true;
}

// Isolate SEH from std::string and other C++ objects with unwinding semantics.
bool PresentationAnyFactory12004(std::uintptr_t base,std::uintptr_t factory,
                                void *&type) noexcept {
  type=nullptr;
#if defined(_MSC_VER)
  __try {type=reinterpret_cast<AnyType>(base+factory)();return type!=nullptr;}
  __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
  (void)base;(void)factory;return false;
#endif
}
bool PresentationInvokeOpen12004(std::uintptr_t base,void *handler,std::uint32_t index,
                                const IdAnyV1 &argument,bool &attempted) noexcept {
#if defined(_MSC_VER)
  __try {
    attempted=true;
    reinterpret_cast<OpenViewData>(base+0xAF39E0)(handler,index,&argument);
    return true;
  } __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
  (void)base;(void)handler;(void)index;(void)argument;(void)attempted;return false;
#endif
}

bool OpenPresentationOwnedWindow12004(
    const ZhongguoScoreboardNativeEnvironmentV1 &env,void *handler,
    IngameUiWindowKindV1 kind,std::uint32_t id,bool &attempted,std::string &reason) {
  attempted=false;reason.clear();
  PresentationWindow12004 before{};
  if(!ReadPresentationOwnedWindow12004(env,handler,kind,before,reason))return false;
  if(!before.present){reason="presentation_native_window_absent";return false;}
  const bool holding=static_cast<std::uint32_t>(kind)==9;
  const auto base=env.module_base;
  void *subject=nullptr;
  if(holding) {
    if(!PresentationProvince12004(base,id,subject)) {
      reason="presentation_requested_province_namespace_unavailable";return false;
    }
  } else {
    std::uint32_t actor=0xFFFFFFFFU;
    if(!Slot(base+0x54DBC00,actor) || actor==0 || actor==0xFFFFFFFFU || actor!=id ||
       !PresentationCharacter12004(base,id,subject)) {
      reason="presentation_personal_window_requires_current_player_full_reference";return false;
    }
  }
  void *type=nullptr;
  const auto factory=holding?0x9F0B20U:0xA05DE0U;
  const auto singleton=holding?0x542FE08U:0x542FE60U;
  const auto any_vt=holding?0x44A0490U:0x44A1938U;
  const auto any_td=holding?0x566BA30U:0x566D0B0U;
  const auto copy=holding?0x878290U:0x8771F0U;
  std::uintptr_t type_vt=0,copy_slot=0,dtor_slot=0,data_slot=0;
  if(!PresentationAnyFactory12004(base,factory,type) ||
     reinterpret_cast<std::uintptr_t>(type)!=base+singleton ||
     !Value(type,0,type_vt) || type_vt!=base+any_vt ||
     !TypedObject(base,type,any_td,UiExactImageSizeV1(env.gui_abi_revision)) ||
     !Value(reinterpret_cast<void *>(type_vt),0x10,copy_slot) || copy_slot!=base+copy ||
     !Value(reinterpret_cast<void *>(type_vt),0x18,dtor_slot) || dtor_slot!=base+0x8522C0 ||
     !Value(reinterpret_cast<void *>(type_vt),0x28,data_slot) || data_slot!=base+0x876E00) {
    reason="presentation_native_any_metadata_unavailable";return false;
  }
  IdAnyV1 argument{};argument.type=type;
  if(holding)std::memcpy(argument.data.data(),&subject,sizeof(subject));
  else std::memcpy(argument.data.data(),&id,sizeof(id));
  // The metadata getter may initialize TLS/static state; reacquire bindings.
  PresentationWindow12004 later{};void *later_subject=nullptr;
  if(!ReadPresentationOwnedWindow12004(env,handler,kind,later,reason) || later!=before ||
     !(holding?PresentationProvince12004(base,id,later_subject):
                PresentationCharacter12004(base,id,later_subject)) || later_subject!=subject) {
    reason="presentation_binding_changed_before_open";return false;
  }
  if(!holding) {
    std::uint32_t actor=0xFFFFFFFFU;
    if(!Slot(base+0x54DBC00,actor) || actor!=id) {
      reason="presentation_current_player_changed_before_open";return false;
    }
  }
  // Deliberately use original OpenGameViewData, not the stock Toggle entry:
  // a repeated already-visible request must not close the requested panel.
  if(!PresentationInvokeOpen12004(base,handler,holding?7U:0xA9U,argument,attempted)) {
    reason=attempted?"presentation_open_attempted_result_unknown_do_not_retry":
                     "presentation_original_open_not_invoked";
    return false;
  }
  // Native history copies an 8-byte nonowning Province pointer or 4-byte uint32
  // value. Both precise metadata destructors are trivial; no caller-stack
  // payload reference is retained. Parent must independently read post-state.
  return true;
}
