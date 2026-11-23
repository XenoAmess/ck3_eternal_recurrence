// Complete closed current859 bodies; exact source/order proof, not runtime P.
inline constexpr rmtm_observation_pins::Pin kOfferOriginPins267V1[]={
 {0x3E65760, "48895c2410574883ec40488b791833db381d4fcaa402488d4c2420410f94c0488d97f8010000e8a52cbafc486387e40100008bd3448b97f001000085c07e2e4c8b87d80100004c8bc88bc30f1f440000498b0cc044395170740cffc248ffc0493bc17ceceb074863c2498b1cc0807c242800740a488b4c2420e8a2959a00488bc3488b5c24584883c4405fc3"},
 {0x1441CF0, "4883ec38488b91a00000004533c0f20f1044242044884424288b442428f20f1182406c01008982486c01004c8982386c01004881c2506c01004c89421048837a180f7603488b12448802488b05b76c6205488981b8010000488b01c781d4000000ffffffff44898144010000c681d8000000024883c43848ff6020"},
};
// Included in the existing private observation namespace. This does not mutate
// the cached origin or construct a widget. Only two already captured real root
// widgets are eligible, and neither is the interaction menu itself.
[[maybe_unused]]bool SelectOfferOrigin267V1(const RmtmObservationFrame267V1&f,
 std::vector<std::byte>&proof,std::uintptr_t menuRoot,std::uintptr_t&out){
 out=0;std::uintptr_t cached=0;
 if(!At(f.scene.handler,0x16C38,cached)||!Add(proof,f.scene.handler+0x16C38,8))return false;
 constexpr std::array<std::string_view,2>names{"hud_layer","windows_layer"};
 std::array<std::uintptr_t,2>eligible{};
 for(std::size_t index=0;index<names.size();++index){
  const GuiWindowNodeV1*found=nullptr;
  for(const auto&node:f.witness)if(node.name==names[index]&&node.parent==f.scene.global){
   if(found)return false;found=&node;
  }
  if(!found||!found->widget||found->widget==menuRoot)return false;
  std::uintptr_t vt=0,context=0,parent=0;std::uint8_t flags=0;
  if(!At(found->widget,0,vt)||vt!=found->vtable||
   !At(found->widget,0xD0,flags)||(flags&1)||
   !At(found->widget,0xD8,context)||context!=f.scene.context||
   !At(found->widget,0xE8,parent)||parent!=f.scene.global||
   !Add(proof,found->widget,8)||!Add(proof,found->widget+0xD0,0x30)||
   !Add(proof,found->widget+0x128,8))return false;
  // The frame already has effective ancestor visibility/enabled state. The
  // physical root flags are independently current; neither check is inferred
  // from a serialized row or caller-provided pointer.
  if(found->visible&&found->enabled&&(flags&0x1E)==0&&found->widget!=cached)
   eligible[index]=found->widget;
 }
 out=eligible[0]?eligible[0]:eligible[1];
 // No eligible anchor is clean DATA: open_admissible will remain false. A null
 // origin is never passed to the native callback as a fallback.
 return true;
}

// These are precisely the two flag bytes and one manager DWORD tested by
// BC3A70. They are not relabelled AI/dead/Shift/Ctrl or treated as permissions.
[[maybe_unused]]bool ReadOfferOpenerScalarGuards267V1(const RmtmObservationFrame267V1&f,
 std::uintptr_t target,std::vector<std::byte>&proof,bool&can){
 std::uint32_t mode=0;std::uint8_t flag1A4=0,flag1A5=0;can=false;
 if(!At(f.scene.handler,0x60,mode)||!At(target,0x1A4,flag1A4)||!At(target,0x1A5,flag1A5)||
  !Add(proof,f.scene.handler+0x60,4)||!Add(proof,target+0x1A4,2))return false;
 can=mode!=1&&flag1A4==0&&flag1A5==0;return true;
}

// Physical equivalent of the already closed readonly 3E65760 first-match
// lookup. Do not call its lock helpers or assign an unproved functional name
// to this collection. A valid lookup returning no object ALLOWS the opener.
[[maybe_unused]]bool ReadOfferOpenerCollectionGate267V1(const RmtmObservationFrame267V1&f,
 std::vector<std::byte>&proof,bool&can){
 can=false;std::uintptr_t collection=0,rows=0;std::int32_t count=0;std::uint32_t current=0;
 const auto jomini=reinterpret_cast<std::uintptr_t>(f.role.world.jomini);
 if(!jomini||!At(jomini,0x18,collection)||!collection||
  collection!=reinterpret_cast<std::uintptr_t>(f.role.world.players)||
  !At(collection,0x1D8,rows)||!At(collection,0x1E4,count)||count<0||count>4096||
  !At(collection,0x1F0,current)||(!rows&&count)||!Add(proof,jomini+0x18,8)||
  !Add(proof,collection+0x1D8,16)||!Add(proof,collection+0x1F0,4)||
  (count&&!Add(proof,rows,static_cast<std::size_t>(count)*8)))return false;
 for(std::int32_t index=0;index<count;++index){
  std::uintptr_t entry=0;std::uint32_t id=0;
  if(!At(rows,static_cast<std::size_t>(index)*8,entry)||!At(entry,0x70,id)||
   !Add(proof,entry+0x70,4))return false;
  if(id!=current)continue;
  std::uint8_t flags=0;
  if(!At(entry,0x48,flags)||!Add(proof,entry+0x48,1))return false;
  can=(flags&0x20)==0;return true;
 }
 can=true;return true;
}
