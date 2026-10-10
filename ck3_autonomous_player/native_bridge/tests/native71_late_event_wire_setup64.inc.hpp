// Setup-only input for59's new whole query/strict/Service wire fixture.
// No old64 main, assertions, install/qualification replay, Game, or SDK call.
#pragma once
#include "xar_bridge/ck3_12004_actual_army_late_event_journal.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include <array>
#include <cstring>

namespace late_event_new_wire_setup64 {
inline std::array<std::byte,0x168> incoming_scope{};
inline std::array<std::byte,0x320> actual_definition{};
inline std::array<std::byte,0x680> actual_table{};
inline std::array<std::byte,0x40> actual_manager{};
inline std::array<std::byte,72> named_rows{};
inline std::array<std::uint32_t,3> loaded_keys{7,8,9};
inline std::uint32_t original_calls=0;
inline constexpr std::uintptr_t fixture_image_base=0x100000;
template <typename T,std::size_t N> void Put(std::array<std::byte,N> &object,std::size_t offset,T value) {
  std::memcpy(object.data()+offset,&value,sizeof(value));
}
template <std::size_t N> bool Owns(const std::array<std::byte,N> &object,std::uintptr_t address,std::size_t size) {
  const auto start=reinterpret_cast<std::uintptr_t>(object.data());
  return address>=start && size<=N && address-start<=N-size;
}
inline bool Reader(void *,const void *address,void *out,std::size_t size) noexcept {
  const auto raw=reinterpret_cast<std::uintptr_t>(address);
  constexpr std::array<std::uintptr_t,3> source_key_slots{0x5D4C27C,0x5D4BE20,0x5D4BE1C};
  for(std::size_t i=0;i<source_key_slots.size();++i) {
    if(raw==fixture_image_base+source_key_slots[i] && size==sizeof(std::uint32_t)) {
      std::memcpy(out,&loaded_keys[i],size);return true;
    }
  }
  if(!(Owns(incoming_scope,raw,size)||Owns(actual_definition,raw,size)||
       Owns(actual_table,raw,size)||Owns(actual_manager,raw,size)||Owns(named_rows,raw,size)))return false;
  std::memcpy(out,address,size);return true;
}
inline void __fastcall Original(void *,const void *,void *,void *,void *,void *) {
  ++original_calls;
  Put(incoming_scope,0x10,std::uint32_t{41});
}
// The current query's full CArmy ID must be the same signed DWORD supplied here.
// Labels retain their production values, while the surrounding59 result receipt
// must explicitly classify this graph/entry as synthetic offline wire input.
inline bool InitializeAndSeed(std::int32_t native_carmy_id) noexcept {
  incoming_scope={};actual_definition={};actual_table={};actual_manager={};named_rows={};original_calls=0;
  Put(incoming_scope,0,std::uint16_t{27});
  Put(incoming_scope,8,std::uint64_t{static_cast<std::uint32_t>(native_carmy_id)});
  Put(incoming_scope,0x10,std::uint32_t{37});
  Put(incoming_scope,0x18,reinterpret_cast<std::uintptr_t>(named_rows.data()));
  Put(incoming_scope,0x20,std::int32_t{3});Put(incoming_scope,0x24,std::int32_t{3});
  for(std::size_t i=0;i<3;++i) {
    Put(named_rows,i*24,loaded_keys[i]);
    Put(named_rows,i*24+8,std::uint16_t{i==0?std::uint16_t{4}:std::uint16_t{5}});
    Put(named_rows,i*24+16,std::uint64_t{100+i});
  }
  Put(actual_manager,0x38,reinterpret_cast<std::uintptr_t>(actual_table.data()));
  Put(actual_table,0x640,reinterpret_cast<std::uintptr_t>(actual_definition.data()));
  Put(actual_definition,0x2C,std::int32_t{3});
  auto bindings=xar::ck3_12004::BindActualArmyLateEventJournalImage12004(fixture_image_base,xar::ck3_12004::kExecutableSha256);
  bindings.read_memory=&Reader;
  if(!xar::ck3_12004::InitializeActualArmyLateEventJournalFixture12004(bindings,&Original))return false;
  xar::ck3_12004::InvokeActualArmyLateEventJournalFixture12004(
      0x2C448F5,actual_manager.data(),actual_definition.data(),incoming_scope.data(),nullptr,nullptr,nullptr);
  return true;
}
} // namespace late_event_new_wire_setup64
