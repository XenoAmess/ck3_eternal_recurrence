// Exact closed semantics used below; all static evidence, not runtime P.
inline constexpr rmtm_observation_pins::Pin kOfferVisibilityPins267V1[]={
 {0x2516E20, "48895c2408574883ec20488b59604885db7470ba01000000488bcbe820c7b7014863f883ffff741ae8b312cd014c69c708030000488b004180bc0000030000007541f683d000000008742b33d2488bcbe8ebc6b7014863d883fbff7426e87e12cd014869d308030000488b0080bc020003000000740db001488b5c24304883c4205fc3488b5c243032c04883c4205fc3"},
 {0x4093560, "48895c2408574883ec204863fa488bd9e8fbe8ffff4c8bc04885c07510b8ffffffff488b5c24304883c4205fc3b802000000f00fc105de8c8c02a80174316690f08305d08c8c02fe8b05ca8c8c02a801740cf3908b05be8c8c02a80175f4b802000000f00fc105ad8c8c02a80175d14863836403000083f8ff741a486bc8704903481074108b4cb928b8ffffffff3bc80f44c8eb05b9fffffffff08305768c8c02fe488b5c24308bc14883c4205fc3"},
 {0x4091E70, "40534881ec8000000033dbe800cb0c0048630883f9ff0f84e400000085c978193b48147d14488b4008488b1cc8488bc34881c4800000005bc3488d05e01c0401488944244048c74424485a00000048895c2430488d44245048894424384c8d442430488d542440488d4c2460e8ef5e80fc908b05d4208202903da08601007d3bb902000000e8564445004885c0742c488d4c246048894c242841b90100000041b87a000000488d15d41b0401488bc8e8ac5f80fcf0ff0591208202488b5424784883fa0f762e48ffc2488b4c2460488bc14881fa0010000072154883c227488b49f8482bc14883e8084883f81f771ce84ce87700488bc34881c4800000005bc333c04881c4800000005bc348895c24204533c94533c033d233c9e889df7800cc"},
 {0x415E980, "4883ec2865488b042558000000b91c000000488b008b0401390566dd9a027f35488d0569dd9a024883c428c3488d0d7d378600e8d01d6b00488d0d45dd9a02e864196b00488b7c2420488d0540dd9a024883c428c3488d0d28dd9a02e8b3196b00833d1cdd9a02ff75b648895c2430488d05c254f70048890533dd9a0233db488d059203c10148897c2420488d3d1edd9a024889052fdd9a02488bcfc705eadc9a02ffffffff33d248891de9dc9a0241b80800000048891de4dc9a0248893de5dc9a02e8a86e73fc488b05e1dc9a0248891dc2dc9a0248891dc3dc9a02488b5c24304c8b4820488d05837473fc4c3bc8751d488d05bfdc9a02c7059ddc9a02020000004889058edc9a02e91dffffff4c8d058adc9a02488bcf488d1578dc9a0241ffd1e904ffffff"},
 {0x41E8100, "4883ec2865488b042558000000b91c000000488b008b04013905124f92027f0c488d05114f92024883c428c3488d0dfd4e9202e85c826200833df14e9202ff75df33d2488d05366cb801488905f74e9202488d0de8b67d00488d0501cfb601488915d24e9202488905f34e9202488915cc4e9202488915d54e9202488915d64e9202e801866200488d0da24e9202e895816200488d059e4e92024883c428c3"},
 {0x4810394, "40534883ec20488bd9488d0d9c4b0902ff1506831c00833b007525c703ffffffffeb454533c9488d157f4b09024183c8ff488d0d6c4b0902ff153e7e1c00ebd6833bff74de65488b0425580000008b0d3051090241b81c000000488b14c88b05b03f510141890410488d0d3d4b09024883c4205b48ff2591821c00"},
 {0x4041B30, "48895c241048896c2418488974242057415641574883ec400fb6da488bf90fb689d0000000f6c110750984d275054532ffeb0341b7010fb6c1c0e8032401413ac70f846b01000080e1f7410fb6c7c0e0030ac8888fd0000000488b8fd800000033f6c644243401897424284584ff7424c74424300a000000488d0511ce070148894424204c8d442420488bd7e84f0e030090eb22c744243009000000488d05ddcd070148894424204c8d442420488bd7e82b0e030090488b8fc80000004885c9740c80f301488b010fb6d3ff50488977408b473489474485c07e388bc60f1f0048897c24604898488d0cc0488b4728488b4cc8404885c90f84ce000000488b01488d542460ff5010ff47408b47403b47447ccd48c74740000000004c63b7fc0000004d85f67e61660f1f840000000000488b87f0000000488b2cf00fb69dd0000000c0eb0380e301410fb6d7488bcde8acfeffff0fb685d0000000c0e80324013ac3741c488bcd84c0740433d2eb05ba01000000e8b71805008bc8e87012050048ffc6493bf67ca8f687d0000000087521f687d100000002741841b9060000004533c0488bd7488b8fd8000000e8de1e0300488b5c2468488b6c2470488b7424784883c440415f415e5fc3e860c37c00cc"},
};
// Exact physical equivalent of current859 CInGameView bool2516E20, restricted
// to the two existing typed Offer views. No factory, mutex, TLS initializer or
// native function is called. Only the already-current owner and at most two
// actual channel records are read; no guessed total capacity or enumeration.
[[maybe_unused]]bool OfferLogicalVisible267V1(std::uintptr_t image,std::uintptr_t view,
 std::vector<std::byte>&proof,bool&visible){
 visible=false;std::uintptr_t vt=0,method=0,root=0;
 if(!At(view,0,vt)||(vt!=image+0x4BDB6B8&&vt!=image+0x4BAC188)||
  !At(vt,0x38,method)||method!=image+0x2516E20||!At(view,0x60,root)||!root||
  !Add(proof,view,8)||!Add(proof,vt+0x38,8)||!Add(proof,view+0x60,8))return false;
 std::uint8_t flags=0;std::int32_t guard=0,current=-1,count=0;
 // guard0 starts initialization and guard-1 waits. Do not initialize it merely
 // to observe a window. An already-initialized valid current=-1 means no owner.
 if(!At(root,0xD0,flags)||!At(image,0x6B0C704,guard)||guard==0||guard==-1||
  !At(image,0x6B0C710,current)||!Add(proof,root+0xD0,1)||
  !Add(proof,image+0x6B0C704,4)||!Add(proof,image+0x6B0C710,4))return false;
 std::uintptr_t owner=0,ownerArray=0,rows=0;
 std::int32_t rowIndex=-1;
 if(current!=-1){
  if(current<0||!At(image,0x6B0C724,count)||count<0||current>=count||
   !At(image,0x6B0C718,ownerArray)||!ownerArray||
   !At(ownerArray,static_cast<std::size_t>(current)*8,owner)||
   !Add(proof,image+0x6B0C718,16)||
   !Add(proof,ownerArray+static_cast<std::size_t>(current)*8,8))return false;
  // A valid actual null owner produces invalid channel IDs in4093560. It is
  // not an invented requirement that every view have an active animation.
  if(owner&&(!At(root,0x364,rowIndex)||rowIndex<-1||!At(owner,0x10,rows)||
   !Add(proof,root+0x364,4)||!Add(proof,owner+0x10,8)))return false;
 }
 const auto channel=[&](unsigned which,std::int32_t&index){
  index=-1;if(!owner||rowIndex==-1)return true;
  const auto offset=static_cast<std::size_t>(rowIndex)*0x70;
  if(offset>(std::numeric_limits<std::uintptr_t>::max)()-rows)return false;
  const auto row=rows+offset;if(!row)return true;
  return At(row,0x28+which*4,index)&&index>=-1&&Add(proof,row+0x28+which*4,4);
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
   !At(records+offset,0x300,value)||!Add(proof,image+0x6B0D030,4)||
   !Add(proof,image+0x6B0D038,8)||!Add(proof,records+offset+0x300,1))return false;
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
