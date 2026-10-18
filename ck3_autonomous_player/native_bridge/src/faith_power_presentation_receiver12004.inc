// Purpose-specific direct/local receiver observation. No native getter/provider
// is invoked; no temporary engine variable table is claimed to be observed.
struct PresentationBuildingReceiver12004 {
  void *callback=nullptr,*callback_vtable=nullptr,*context=nullptr,*declarations=nullptr,*indices=nullptr;
  void *definition=nullptr,*entries=nullptr,*entry=nullptr,*row=nullptr,*rows=nullptr;
  void *registry=nullptr,*type_rows=nullptr,*converter=nullptr,*getter=nullptr;
  void *row_owner_raw=nullptr,*building=nullptr,*next_building=nullptr;
  std::uint32_t type_id=0,declared_type=0,final_type=0,receiver_type=0,category=0,mode=0;
  std::int32_t declaration_count=0,index_count=0,receiver_index=0,entry_count=0,array_capacity=0,array_count=0;
  std::int32_t type_capacity=0;
  std::int32_t dynamic_count=0,literal_count=0,chain_count=0,final_kind=0;
  std::int8_t entry_mode=0;std::uint8_t receiver_flag=0,entry_flag=0,local_active=0;
  std::string building_key,next_building_key;
  bool operator==(const PresentationBuildingReceiver12004&)const=default;
};
bool PresentationBuildingDefinition12004(void*building,std::string&key) {
  key.clear();if(!building)return true;
  std::uint32_t magic=0;std::uint64_t size=0,capacity=0;void*data=nullptr;
  if(!Value(building,0x38,magic)||magic!=0x4744624FU||!Value(building,0x28,size)||!Value(building,0x30,capacity)||
      !size||size>160||size>capacity||(capacity<16&&capacity!=15))return false;
  data=static_cast<unsigned char*>(building)+0x18;
  if(capacity>=16&&(!Value(building,0x18,data)||!data))return false;
  std::array<char,161>bytes{};if(!Read(data,bytes.data(),static_cast<std::size_t>(size)+1)||bytes[size]!=0)return false;
  key.assign(bytes.data(),static_cast<std::size_t>(size));
  return std::all_of(key.begin(),key.end(),[](unsigned char c){return (c>='a'&&c<='z')||(c>='0'&&c<='9')||c=='_';});
}
bool CapturePresentationBuildingReceiver12004(const ZhongguoScoreboardNativeEnvironmentV1&env,
    const IngameUiGuiOwnerBindingV1&gui,const PresentationPanel12004&panel,void*root,
    std::string_view path,bool potential,PresentationBuildingReceiver12004&v,std::string&why) {
  v={};const auto fail=[&](const char*s){why=s;return false;};
  if(!PresentationReceiverSourcePins12004(env))return fail("presentation_building_receiver_source_pin_mismatch");
  const auto type_slot=potential?0x5D56864U:0x5D20B98U;
  const auto wrapper=potential?0x12B3260U:0x12B2610U;
  if(!Slot(env.module_base+type_slot,v.type_id)||!v.type_id)return fail("presentation_building_receiver_type_unregistered");
  if(v.type_id>0x7FFFFFFFU||!Slot(env.module_base+0x5C6A9C0,v.registry)||!v.registry||
      !Value(v.registry,0x20,v.type_rows)||!v.type_rows||!Value(v.registry,0x2C,v.type_capacity)||
      v.type_capacity<=0||v.type_id>=static_cast<std::uint32_t>(v.type_capacity)||
      v.type_id>(std::numeric_limits<std::size_t>::max)()/0x130)
    return fail("presentation_building_type_registry_record_unverified");
  auto*type_record=static_cast<unsigned char*>(v.type_rows)+static_cast<std::size_t>(v.type_id)*0x130;
  if(!Value(type_record,0xE8,v.converter)||!Value(type_record,0xF0,v.getter)||(v.converter&&v.getter))
    return fail("presentation_building_model_provider_path_not_supported");
  void*widget=nullptr,*data=nullptr,*entry_function=nullptr,*slot2=nullptr;std::int32_t count=0;
  if(!ArmyTooltipResolvePath(env,root,gui.context,path,widget,false)||
      !Value(widget,0x404,count)||count!=1||!Value(widget,0x3F8,data)||!data||
      !Value(data,0x40,v.callback)||!v.callback||!Value(v.callback,0,v.callback_vtable)||
      !Value(v.callback_vtable,0x10,slot2)||reinterpret_cast<std::uintptr_t>(slot2)!=env.module_base+0x3AA30E0||
      !Value(v.callback,8,entry_function)||reinterpret_cast<std::uintptr_t>(entry_function)!=env.module_base+0x3A9F960||
      !Value(v.callback,0x1C,v.dynamic_count)||!Value(v.callback,0x9C,v.literal_count)||v.dynamic_count||v.literal_count||
      !Value(v.callback,0x34,v.chain_count)||v.chain_count||!Value(v.callback,0x44,v.final_kind)||v.final_kind!=3||
      !Value(v.callback,0x48,entry_function)||reinterpret_cast<std::uintptr_t>(entry_function)!=env.module_base+wrapper||
      !Value(v.callback,0x58,v.receiver_type)||v.receiver_type!=v.type_id||!Value(v.callback,0x5C,v.receiver_flag)||v.receiver_flag)
    return fail("presentation_building_callback_is_not_zero_preparation_direct_typed_method");
  if(!Value(v.callback,0xF0,v.context)||!v.context||!Value(v.callback,0xA8,v.declarations)||!v.declarations||
      !Value(v.callback,0xB4,v.declaration_count)||v.declaration_count<1||v.declaration_count>256||
      !Value(v.callback,0xC0,v.indices)||!v.indices||!Value(v.callback,0xCC,v.index_count)||v.index_count<1||v.index_count>256||
      !Value(v.indices,static_cast<std::size_t>(v.index_count-1)*4,v.receiver_index)||v.receiver_index<0||v.receiver_index>=v.declaration_count||
      !Value(v.declarations,static_cast<std::size_t>(v.receiver_index)*8,v.declared_type)||v.declared_type!=v.type_id||
      !Value(v.context,0xE0,v.definition)||!v.definition||!Value(v.definition,0x115,v.local_active)||!v.local_active||
      !Value(v.definition,0x90,v.entries)||!Value(v.definition,0x9C,v.entry_count)||v.entry_count<0||v.entry_count>256||
      (v.entry_count&&!v.entries))return fail("presentation_building_local_receiver_declaration_unverified");
  for(std::int32_t i=0;i<v.entry_count;++i){
    std::uint32_t key=0;auto*e=static_cast<unsigned char*>(v.entries)+static_cast<std::size_t>(i)*0x50;
    if(!Value(e,0x48,key))return fail("presentation_building_local_key_unreadable");
    if(key==v.type_id){v.entry=e;break;}
  }
  if(!v.entry||!Value(v.entry,0x40,v.entry_mode)||v.entry_mode!=1||
      !Value(v.entry,0x4C,v.entry_flag)||!v.entry_flag||!Value(v.entry,0,v.row)||!v.row)
    return fail("presentation_building_receiver_not_local_ready_mode1_provider_unknown");
  const auto header=potential?0xE8U:0x100U;
  if(!Value(panel.window,header,v.rows)||!Value(panel.window,header+8,v.array_capacity)||
      !Value(panel.window,header+12,v.array_count)||v.array_count<0||v.array_count>4096||
      v.array_capacity<v.array_count||v.array_capacity>8192||(v.array_count&&!v.rows))return fail("presentation_building_owned_model_header_unverified");
  bool member=false;
  if(potential){
    for(std::int32_t i=0;i<v.array_count;++i){void*row=nullptr;if(!Value(v.rows,static_cast<std::size_t>(i)*8,row))return fail("presentation_potential_model_entry_unreadable");if(row==v.row){member=true;break;}}
  }else{
    const auto row=reinterpret_cast<std::uintptr_t>(v.row),rows=reinterpret_cast<std::uintptr_t>(v.rows);
    member=v.array_count&&row>=rows&&(row-rows)%0x28==0&&(row-rows)/0x28<static_cast<std::uint32_t>(v.array_count);
    // Original GetGUIHoldingBuilding separately returns the exact inline row.
    member=member||v.row==static_cast<unsigned char*>(panel.window)+0x118;
  }
  if(!member||!Value(v.row,0,v.row_owner_raw)||!Value(v.row,8,v.building))return fail("presentation_building_row_not_owned_by_current_view");
  if(potential){
    if(v.row_owner_raw!=panel.window||!v.building||!Value(v.row,0x10,v.mode)||!Value(v.building,0x6FFE8,v.category))return fail("presentation_potential_row_view_or_definition_unverified");
  }else if(!Value(v.row,0x10,v.next_building)||!Value(v.row,0x18,v.mode)||!Value(v.row,0x1C,v.category))return fail("presentation_building_slot_fields_unreadable");
  if(!PresentationBuildingDefinition12004(v.building,v.building_key)||!PresentationBuildingDefinition12004(v.next_building,v.next_building_key))return fail("presentation_building_definition_identity_unverified");
  why.clear();return true;
}
bool ReadPresentationBuildingReceiver12004(const ZhongguoScoreboardNativeEnvironmentV1&env,
    const IngameUiGuiOwnerBindingV1&gui,const PresentationPanel12004&panel,void*root,
    std::string_view path,bool potential,PresentationBuildingReceiver12004&out,std::string&why) {
  PresentationBuildingReceiver12004 first{},last{};
  if(!CapturePresentationBuildingReceiver12004(env,gui,panel,root,path,potential,first,why)||
      !CapturePresentationBuildingReceiver12004(env,gui,panel,root,path,potential,last,why))return false;
  if(first!=last){why="presentation_building_receiver_model_or_definition_changed";return false;}
  out=std::move(first);return true;
}
