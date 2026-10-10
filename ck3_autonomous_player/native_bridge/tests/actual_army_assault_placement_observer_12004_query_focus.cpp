#include "xar_bridge/actual_army_assault_placement_observer_12004.hpp"
#include <array>
#include <cstring>

// Fresh synthetic offline whole-query graph only. These peer exports belong to
// 35's separate setup TU; no old focus Run/main/assert entry is reused.
std::uintptr_t ArmyPreparationNaturalQueryImageBase12004() noexcept;
bool ReadArmyPreparationNaturalQueryFocus12004(void *,const void *,void *,std::size_t) noexcept;
namespace {
using namespace xar::ck3_12004;
constexpr std::uint32_t kKey=0x72000003U;
constexpr std::uint32_t Hash(std::uint32_t value) {
  std::uint32_t result=0x811C9DC5U;
  for(unsigned shift=0;shift<32;shift+=8)result=(result^static_cast<std::uint8_t>(value>>shift))*0x01000193U;
  return result;
}
constexpr std::uint32_t kHash=Hash(kKey);
struct QueryPlacementFixture {
  std::uintptr_t base=0,manager=0,state=0,army=0;
  std::array<std::byte,0x28> table{};
  std::array<std::byte,2*0x40> empty{};
  std::array<std::byte,14*0x40> grown{};
  std::array<std::byte,16> output{};
  std::uint32_t key=kKey;
  bool enabled=false,installed=false,invoked=false,arguments_exact=false;
  std::size_t original_calls=0;
};
QueryPlacementFixture q;
template<class T,std::size_t N> void Put(std::array<std::byte,N> &bytes,std::size_t offset,T value) {
  std::memcpy(bytes.data()+offset,&value,sizeof value);
}
template<std::size_t N> bool Region(std::uintptr_t address,void *out,std::size_t size,const std::array<std::byte,N> &bytes,std::uintptr_t identity=0) noexcept {
  const auto start=identity ? identity : reinterpret_cast<std::uintptr_t>(bytes.data());
  if(address<start || address-start>N || size>N-(address-start))return false;
  std::memcpy(out,bytes.data()+(address-start),size);return true;
}
bool ReadOwned(void *context,const void *address,void *out,std::size_t size) noexcept {
  const auto raw=reinterpret_cast<std::uintptr_t>(address);
  std::uintptr_t value=0;bool slot=false;
  if(q.state && raw==q.base+0x5C68C50){value=q.state;slot=true;}
  if(q.state && q.manager>=0x2A540 && raw==q.state+0xA0){value=q.manager-0x2A540;slot=true;}
  if(slot && size==sizeof value){std::memcpy(out,&value,size);return true;}
  if(q.manager && Region(raw,out,size,q.table,q.manager+0x170))return true;
  if(q.base && Region(raw,out,size,q.empty,q.base+kActualArmyAssaultEmptyStorageRva12004))return true;
  if(Region(raw,out,size,q.grown) || Region(raw,out,size,q.output))return true;
  if(raw==reinterpret_cast<std::uintptr_t>(&q.key) && size==sizeof q.key){std::memcpy(out,&q.key,size);return true;}
  return ReadArmyPreparationNaturalQueryFocus12004(context,address,out,size);
}
std::uint64_t __fastcall Original(const void *table,void *output,std::uint32_t hash,const std::uint32_t *key) {
  ++q.original_calls;
  q.arguments_exact=reinterpret_cast<std::uintptr_t>(table)==q.manager+0x170 && output==q.output.data() && hash==kHash && key==&q.key;
  // Fixed owned initial-growth postimage. No placement/allocator/game body is
  // replayed. This is independently visible to the actual typed observer.
  Put(q.table,8,reinterpret_cast<std::uintptr_t>(q.grown.data()));Put(q.table,0x10,std::int32_t{1});
  Put(q.table,0x14,std::int32_t{7});Put(q.table,0x18,std::uint8_t{5});
  Put(q.output,0,reinterpret_cast<std::uintptr_t>(q.grown.data()+(kHash&7U)*0x40));Put(q.output,8,std::uint8_t{1});
  return reinterpret_cast<std::uintptr_t>(output);
}
bool InstallOwned() noexcept {
  const auto base=ArmyPreparationNaturalQueryImageBase12004();if(!base || base>UINTPTR_MAX-kActualArmyAssaultPlacementRva12004)return false;
  q.base=base;
  auto *target=reinterpret_cast<std::uint8_t *>(base+kActualArmyAssaultPlacementRva12004);
  auto *caller=reinterpret_cast<std::uint8_t *>(base+kActualArmyAssaultPlacementDirectReturnRva12004-9);
  DWORD target_old=0,caller_old=0;
  if(!VirtualProtect(target,64,PAGE_EXECUTE_READWRITE,&target_old))return false;
  if(!VirtualProtect(caller,14,PAGE_EXECUTE_READWRITE,&caller_old)) {
    DWORD ignored=0;(void)VirtualProtect(target,64,target_old,&ignored);return false;
  }
  constexpr std::array<std::uint8_t,19> prefix{0x48,0x89,0x5C,0x24,0x10,0x55,0x56,0x57,0x41,0x56,0x41,0x57,0x48,0x81,0xEC,0x80,0,0,0};
  std::memcpy(target,prefix.data(),prefix.size());
  constexpr std::array<std::uint8_t,16> tail{0x48,0x81,0xC4,0x80,0,0,0,0x41,0x5F,0x41,0x5E,0x5F,0x5E,0x5D,0x48,0xB8};
  std::memcpy(target+19,tail.data(),tail.size());
  const auto body=reinterpret_cast<std::uintptr_t>(&Original);std::memcpy(target+35,&body,8);target[43]=0xFF;target[44]=0xE0;
  constexpr std::array<std::uint8_t,5> call_head{0x48,0x83,0xEC,0x28,0xE8};std::memcpy(caller,call_head.data(),call_head.size());
  constexpr std::int32_t relative=static_cast<std::int32_t>(kActualArmyAssaultPlacementRva12004-kActualArmyAssaultPlacementDirectReturnRva12004);
  std::memcpy(caller+5,&relative,4);
  constexpr std::array<std::uint8_t,5> ret{0x48,0x83,0xC4,0x28,0xC3};std::memcpy(caller+9,ret.data(),ret.size());
  const bool flushed=FlushInstructionCache(GetCurrentProcess(),target,64)!=FALSE && FlushInstructionCache(GetCurrentProcess(),caller,14)!=FALSE;
  DWORD ignored=0;const bool target_restored=VirtualProtect(target,64,target_old,&ignored)!=FALSE;
  const bool caller_restored=VirtualProtect(caller,14,caller_old,&ignored)!=FALSE;
  if(!flushed || !target_restored || !caller_restored)return false;
  ActualArmyAssaultPlacementInstallEnvironment12004 environment{};environment.primary_thread_suspended_proven=true;
  environment.bindings=BindActualArmyAssaultPlacementImage12004(base,kDailyAssaultPreparationExecutableSha256);environment.bindings.read_memory=&ReadOwned;
  static ActualArmyAssaultPlacementDetourState12004 state;
  return InstallActualArmyAssaultPlacementObserver12004(state,environment,kDailyAssaultPreparationExecutableSha256);
}
} // namespace

void EnableArmyPlacementNaturalQueryFocus12004() noexcept {
  q.enabled=true;q.installed=InstallOwned();
}
bool InvokeArmyPlacementNaturalQueryFocus12004(const void *manager,const void *army) noexcept {
  if(!q.enabled || !q.installed || q.invoked)return false;
  const auto active=CopyActiveActualArmyDailyAssaultPreparation12004();
  if(!active.observed || !active.parent_bound || !active.original_occurrence_bound || active.incoming_primary_manager!=reinterpret_cast<std::uintptr_t>(manager) || active.incoming_selected_army!=reinterpret_cast<std::uintptr_t>(army))return false;
  q.invoked=true;q.manager=reinterpret_cast<std::uintptr_t>(manager);q.army=reinterpret_cast<std::uintptr_t>(army);q.state=active.parent.game_state_identity;
  q.table.fill(std::byte{0});q.empty.fill(std::byte{0});q.grown.fill(std::byte{0});q.output.fill(std::byte{0});
  Put(q.table,8,q.base+kActualArmyAssaultEmptyStorageRva12004);Put(q.table,0x1C,std::uint32_t{0x3F800000U});Put(q.empty,0x40+4,std::uint8_t{0xFF});
  const auto slot=static_cast<std::size_t>(kHash&7U),offset=slot*0x40;
  Put(q.grown,offset,kHash);Put(q.grown,offset+4,std::uint8_t{1});Put(q.grown,offset+8,kKey);
  Put(q.grown,offset+0x20,q.base+0x54E0570);Put(q.grown,offset+0x38,q.base+0x54DEB68);Put(q.grown,13*0x40+4,std::uint8_t{0xFF});
  const auto returned=reinterpret_cast<ActualArmyAssaultPlacementOriginal12004>(q.base+kActualArmyAssaultPlacementDirectReturnRva12004-9)(reinterpret_cast<const void *>(q.manager+0x170),q.output.data(),kHash,&q.key);
  return q.arguments_exact && q.original_calls==1 && returned==reinterpret_cast<std::uintptr_t>(q.output.data());
}
bool ReadArmyPlacementNaturalQueryFocus12004(void *context,const void *address,void *out,std::size_t size) noexcept {
  return ReadOwned(context,address,out,size);
}
