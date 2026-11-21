// Included inside full111's private namespace, under the default-OFF option.
// Source: 116/117 typed registry/ID extent, 119 CUnit RTTI, 122 actual
// same-object virtual+8 wrapper -> virtual+10 -> owner+174 consumer.
struct OwnedUnitPass123 {
 Roots &roots;
 const FullSnapshotBindingsV1 &bindings;
 const CoreSnapshotPrefix &expected;
 std::uintptr_t module;
 std::string_view reason="current123_owned_unit_read_failed";
 std::int32_t scanned=0;
 static constexpr std::size_t kWordLimit=8'388'608;
 static constexpr std::size_t kRowLimit=65'536;

 template<class T> bool Read(const void *from,std::size_t offset,T &value) {
  static_assert(std::is_trivially_copyable_v<T> && sizeof(T)<=8);
  const auto a=reinterpret_cast<std::uintptr_t>(from);
  const auto top=(std::numeric_limits<std::uintptr_t>::max)();
  if(!a||offset>top-a||sizeof(T)-1>top-a-offset) {
   reason="current123_owned_address_invalid";return false;
  }
  const auto *source=reinterpret_cast<const void*>(a+offset);
  const auto &access=bindings.army_fixture_access;
  const bool copied=access.copy?access.copy(access.context,source,&value,sizeof(value)):
      Copy(source,&value,sizeof(value));
  if(!copied)return false;
  if(roots.owned_words.size()==kWordLimit) {
   reason="current123_owned_read_scope_exceeded";return false;
  }
  std::uint64_t word=0;std::memcpy(&word,&value,sizeof(value));
  roots.owned_words.push_back(word);return true;
 }

 bool Owner(std::int32_t id,void *&owner) {
  owner=nullptr;
  if(id==-1){reason="current123_unit_owner_unresolved";return false;}
  void *slots=nullptr;std::int32_t capacity=0,actual=-1;std::uint32_t type=0;
  const auto index=static_cast<std::uint32_t>(id)&0xFFFFFFU;
  if(!Read(roots.storage,0x20,slots)||!Read(roots.storage,0x2C,capacity))return false;
  if(capacity<=0||capacity>16'777'216||index>=static_cast<std::uint32_t>(capacity)||!slots) {
   reason="current123_unit_owner_unresolved";return false;
  }
  if(!Read(slots,static_cast<std::size_t>(index)*16+8,owner)||!owner) {
   reason="current123_unit_owner_unresolved";return false;
  }
  if(!Read(owner,0x18,actual)||!Read(owner,0x1C,type))return false;
  if(actual!=id||type!=0x43686172U) {
   reason="current123_unit_owner_unresolved";return false;
  }
  return true;
 }

 bool Capture(std::vector<xar::game::ArmySnapshot> &rows) {
  rows.clear();roots.owned_words.clear();
  const auto &core=bindings.core;const auto &military=bindings.military;
  const auto &mc=military.core;
  if(core.image_build!=ImageBuildV1::full11126785313||!military.exact_build_admitted||
     mc.game_state_slot!=core.game_state_slot||mc.jomini_state_slot!=core.jomini_state_slot||
     mc.character_storage_slot!=core.character_storage_slot||mc.get_local_player!=core.get_local_player||
     mc.image_build!=core.image_build||
     military.unit_registry_slot!=reinterpret_cast<void**>(module+kUnitRegistry)||
     military.unit_manager_vtable!=module+kUnitManagerVt||
     military.unit_registry_vtable!=module+kUnitRegistryVt) {
   reason="current123_owned_source_mismatch";return false;
  }
  void *registry=nullptr,*owned=nullptr,*slots=nullptr,*blocks=nullptr;
  std::uintptr_t manager_type=0,registry_type=0;
  std::int32_t capacity=0,block_count=0;
  if(!Read(military.unit_registry_slot,0,registry)||
     !Read(roots.data,kUnitManager,manager_type)||
     !Read(roots.data,kUnitManager+0x20,owned))return false;
  if(!registry||registry!=owned||manager_type!=module+kUnitManagerVt) {
   reason="current123_unit_registry_owner_mismatch";return false;
  }
  if(!Read(registry,0,registry_type)||registry_type!=module+kUnitRegistryVt) {
   reason="current123_unit_registry_type_mismatch";return false;
  }
  if(!Read(registry,8,blocks)||!Read(registry,0x14,block_count)||
     !Read(registry,0x20,slots)||!Read(registry,0x2C,capacity))return false;
  if(capacity<0||capacity>kMilitaryEmptyStorageLimitV1||(capacity&&!slots)||
     block_count<0||block_count>kMilitaryEmptyStorageLimitV1/1024||
     (block_count&&!blocks)) {
   reason="current123_unit_extent_invalid";return false;
  }
  // Mirror actual2FFEE70: block extent first. Canonical slot capacity is an
  // identity check, not a substitute universe of all native unit records.
  scanned=block_count*1024;
  for(std::int32_t bi=0;bi<block_count;++bi) {
   void *block=nullptr;
   if(!Read(blocks,static_cast<std::size_t>(bi)*sizeof(void*),block))return false;
   if(!block){reason="current123_unit_extent_invalid";return false;}
   for(std::size_t oi=0;oi<1024;++oi) {
   const auto top=(std::numeric_limits<std::uintptr_t>::max)();
   const auto start=reinterpret_cast<std::uintptr_t>(block);
   if(oi*0x1D8>top-start){reason="current123_owned_address_invalid";return false;}
   void *unit=reinterpret_cast<void*>(start+oi*0x1D8);
   std::uintptr_t unit_type=0;std::int32_t id=-1,owner_id=-1;
   if(!Read(unit,0x10,id))return false;
   if(id==-1)continue; // Actual native empty-record branch, before vptr use.
   void *canonical=nullptr;std::int32_t canonical_id=-1;
   const auto index=static_cast<std::uint32_t>(id)&0xFFFFFFU;
   if(index>=static_cast<std::uint32_t>(capacity)||!slots) {
    reason="current123_unit_identity_invalid";return false;
   }
   if(!Read(slots,static_cast<std::size_t>(index)*16+8,canonical))return false;
   if(canonical!=unit){reason="current123_unit_identity_invalid";return false;}
   if(!Read(canonical,0x10,canonical_id)||!Read(unit,0,unit_type))return false;
   // Type membership comes from the current CUnit vtable and canonical
   // database slot, not an unproved magic value at object+14.
   if(unit_type!=module+0x4E42B98||canonical_id!=id) {
    reason="current123_unit_identity_invalid";return false;
   }
   if(!Read(unit,0x174,owner_id))return false;
   void *owner=nullptr;if(!Owner(owner_id,owner))return false;
   if(owner_id!=expected.played_character_id)continue;
   if(owner!=roots.actor){reason="current123_owned_actor_source_mismatch";return false;}
   if(rows.size()==kRowLimit){reason="current123_owned_rows_scope_exceeded";return false;}
   xar::game::ArmySnapshot row{};
   row.army_id=id;row.owner_character_id=owner_id;
   // Historical contract: this flag is derived after exact actor ownership,
   // not a newly claimed independent native commandability predicate.
   row.controllable=true;rows.push_back(std::move(row));
   }
  }
  return true;
 }
};
