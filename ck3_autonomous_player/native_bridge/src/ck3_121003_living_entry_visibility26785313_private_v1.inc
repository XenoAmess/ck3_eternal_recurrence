// Exact physical2516E20 semantics; Inventory/Details actualVT slots separately proven below.
[[maybe_unused]]bool EntryLogicalVisible267V1(std::uintptr_t image,std::uintptr_t view,
 std::vector<std::byte>&proof,bool&visible){
 visible=false;std::uintptr_t vt=0,method=0,root=0;
 if(!At(view,0,vt)||(vt!=image+0x4C213B0&&vt!=image+0x4C22298)||
  !At(vt,0x38,method)||method!=image+0x2516E20||!At(view,0x60,root)||!root||
  !WeaponProof(proof,view,8)||!WeaponProof(proof,vt+0x38,8)||!WeaponProof(proof,view+0x60,8))return false;
 std::uint8_t flags=0;std::int32_t guard=0,current=-1,count=0;
 // guard0 starts initialization and guard-1 waits. Do not initialize it merely
 // to observe a window. An already-initialized valid current=-1 means no owner.
 if(!At(root,0xD0,flags)||!At(image,0x6B0C704,guard)||guard==0||guard==-1||
  !At(image,0x6B0C710,current)||!WeaponProof(proof,root+0xD0,1)||
  !WeaponProof(proof,image+0x6B0C704,4)||!WeaponProof(proof,image+0x6B0C710,4))return false;
 std::uintptr_t owner=0,ownerArray=0,rows=0;
 std::int32_t rowIndex=-1;
 if(current!=-1){
  if(current<0||!At(image,0x6B0C724,count)||count<0||current>=count||
   !At(image,0x6B0C718,ownerArray)||!ownerArray||
   !At(ownerArray,static_cast<std::size_t>(current)*8,owner)||
   !WeaponProof(proof,image+0x6B0C718,16)||
   !WeaponProof(proof,ownerArray+static_cast<std::size_t>(current)*8,8))return false;
  // A valid actual null owner produces invalid channel IDs in4093560. It is
  // not an invented requirement that every view have an active animation.
  if(owner&&(!At(root,0x364,rowIndex)||rowIndex<-1||!At(owner,0x10,rows)||
   !WeaponProof(proof,root+0x364,4)||!WeaponProof(proof,owner+0x10,8)))return false;
 }
 const auto channel=[&](unsigned which,std::int32_t&index){
  index=-1;if(!owner||rowIndex==-1)return true;
  const auto offset=static_cast<std::size_t>(rowIndex)*0x70;
  if(offset>(std::numeric_limits<std::uintptr_t>::max)()-rows)return false;
  const auto row=rows+offset;if(!row)return true;
  return At(row,0x28+which*4,index)&&index>=-1&&WeaponProof(proof,row+0x28+which*4,4);
 };
 const auto active=[&](std::int32_t index,bool&running){
  running=false;if(index==-1)return true;
  std::int32_t recordGuard=0;std::uintptr_t records=0;std::uint8_t value=0;
  // Only require the second initialized factory when the official branch
  // actually needs an animation record. No-animation/null is valid DATA.
  if(index<0||!At(image,0x6B0D030,recordGuard)||recordGuard==0||recordGuard==-1||
   !At(image,0x6B0D038,records)||!records)return false;
  const auto offset=static_cast<std::size_t>(index)*0x308;
  if(offset>(std::numeric_limits<std::uintptr_t>::max)()-records||
   !At(records+offset,0x300,value)||!WeaponProof(proof,image+0x6B0D030,4)||
   !WeaponProof(proof,image+0x6B0D038,8)||!WeaponProof(proof,records+offset+0x300,1))return false;
  running=value!=0;return true;
 };
 std::int32_t hiding=-1;bool running=false;
 if(!channel(1,hiding)||!active(hiding,running))return false;
 if(running){visible=false;return true;}
 if(!(flags&8)){visible=true;return true;}
 std::int32_t showing=-1;
 if(!channel(0,showing)||!active(showing,running))return false;
 visible=running;return true;
}
