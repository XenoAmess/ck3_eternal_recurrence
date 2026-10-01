#include "xar_bridge/scoped_character_variable_monitor_v1.hpp"
#include "xar_bridge/scoped_observer_lifetime_v1.hpp"
#include <windows.h>
#include <intrin.h>
#include <algorithm>
#include <cstring>
#include <limits>
#include <sstream>

namespace xar::ck3_11906 {
namespace {
std::atomic<ScopedCharacterVariableMonitorV1 *> g_monitor{nullptr};
std::atomic<ScopedVariableOwnerOriginalV1> g_owner{nullptr};
std::atomic<ScopedVariableSetterOriginalV1> g_setter{nullptr};
std::atomic<ScopedVariableEffectOriginalV1> g_effect{nullptr};
std::atomic<ScopedHousePredicateOriginalV1> g_house{nullptr};
std::atomic<ScopedEventImmediateRootOriginalV1> g_event_root{nullptr};
thread_local ScopedVariableEventProducerV1 g_event_producer{};
thread_local std::uint32_t g_event_root_depth=0;
struct SetterContext {
  std::uintptr_t node = 0, context = 0, original_owner = 0;
  std::int32_t character_id = -1;
};
thread_local SetterContext g_setter_context{};
template <typename T> T Read(std::uintptr_t address, std::size_t offset = 0) noexcept {
  T result{};
  std::memcpy(&result, reinterpret_cast<const void *>(address + offset), sizeof(T));
  return result;
}
std::uintptr_t ResolveCharacter(const Bindings &bindings, std::int32_t id) noexcept {
  if (id <= 0 || bindings.character_storage_slot == nullptr) return 0;
  const auto storage = reinterpret_cast<std::uintptr_t>(*bindings.character_storage_slot);
  if (storage == 0) return 0;
  const auto slots = Read<std::uintptr_t>(storage, 0x20);
  const auto capacity = Read<std::int32_t>(storage, 0x2C);
  const auto index = static_cast<std::uint32_t>(id) & 0xFFFFFFU;
  if (slots == 0 || capacity <= 0 || capacity > 4'194'304 || index >= static_cast<std::uint32_t>(capacity)) return 0;
  const auto object = Read<std::uintptr_t>(slots, index * 0x10 + 8);
  return object != 0 && Read<std::int32_t>(object, 0x18) == id ? object : 0;
}
bool KeyEquals(std::uintptr_t string, const char *expected, std::size_t length) noexcept {
  const auto size = Read<std::uint64_t>(string, 0x10);
  const auto capacity = Read<std::uint64_t>(string, 0x18);
  if (size != length || size > capacity || (capacity < 16 && capacity != 15)) return false;
  const auto data = capacity >= 16 ? Read<std::uintptr_t>(string) : string;
  return data != 0 && std::memcmp(reinterpret_cast<void *>(data), expected, length) == 0 &&
      Read<char>(data, length) == 0;
}
bool ReadStableKey(std::uintptr_t string, CombatScopedStableKeyV1 &key) noexcept {
  const auto size = Read<std::uint64_t>(string, 0x10);
  const auto capacity = Read<std::uint64_t>(string, 0x18);
  if (size == 0 || size >= key.bytes.size() || size > capacity ||
      (capacity < 16 && capacity != 15)) return false;
  const auto data = capacity >= 16 ? Read<std::uintptr_t>(string) : string;
  if (data == 0 || Read<char>(data, size) != 0) return false;
  std::memcpy(key.bytes.data(), reinterpret_cast<void *>(data), size);
  for (std::size_t i=0;i<size;++i) if(key.bytes[i]<' '||key.bytes[i]>126) return false;
  key.size=static_cast<std::uint32_t>(size);
  return true;
}
void HouseType(ScopedCharacterVariableMonitorV1 &session, ScopedVariableMonitorRecordV1 &row, void *type) noexcept {
  row.relation_type=reinterpret_cast<std::uintptr_t>(type);
  row.relation_type_id=Read<std::int32_t>(row.relation_type,0x10);
  if(!ReadStableKey(row.relation_type+0x18,row.relation_type_key))
    session.failure_flags.fetch_or(row.failure_flags|=scoped_chain_failure_container);
}
bool EventIdentityStable(const ScopedCharacterVariableMonitorV1 &s,
    const ScopedVariableEventProducerV1 &p) noexcept {
  return p.read && s.event_producer_definitions_read &&
      Read<std::uintptr_t>(s.event_manager_slot)==s.event_manager &&
      Read<std::uintptr_t>(s.event_manager,0x40)==s.event_definitions_data &&
      Read<std::int32_t>(s.event_manager,0x4C)==s.event_definitions_count &&
      p.definition_index<static_cast<std::uint32_t>(s.event_definitions_count) &&
      Read<std::uintptr_t>(s.event_definitions_data,p.definition_index*8ULL)==p.definition &&
      Read<std::uintptr_t>(p.definition)==s.module_base+0x42F5710 &&
      Read<std::uint32_t>(p.definition,8)==p.definition_id &&
      Read<std::uint32_t>(p.definition,0xC)==p.runtime_stats_ordinal &&
      KeyEquals(p.definition+0x10,p.definition_key.bytes.data(),p.definition_key.size) &&
      Read<std::uintptr_t>(p.definition,0x230)==p.immediate_root &&
      Read<std::uintptr_t>(p.immediate_root)==s.module_base+0x44CF030 &&
      Read<std::uint32_t>(p.immediate_root,0x38)==p.root_hash &&
      Read<std::uintptr_t>(p.immediate_root,0x40)==p.children_data &&
      Read<std::int32_t>(p.immediate_root,0x48)==p.children_capacity &&
      Read<std::int32_t>(p.immediate_root,0x4C)==p.children_count &&
      Read<std::uintptr_t>(s.module_base+0x44CF030,0xB0)==s.module_base+0x3380EC0;
}
bool ResolveEventProducers(ScopedCharacterVariableMonitorV1 &s,std::uintptr_t slot) noexcept {
  static constexpr std::array<const char *,7> keys{"death_management.1200","death_management.1201",
      "death_management.1202","death_management.1204","death_management.1205",
      "death_management.1206","death_management.1207"};
  s.event_manager_slot=slot;s.event_manager=Read<std::uintptr_t>(slot);
  if(!s.event_manager)return false;
  s.event_definitions_data=Read<std::uintptr_t>(s.event_manager,0x40);
  s.event_definitions_count=Read<std::int32_t>(s.event_manager,0x4C);
  const auto cap=Read<std::int32_t>(s.event_manager,0x48);
  if(s.event_definitions_count<=0||cap<s.event_definitions_count||s.event_definitions_count>1048576||!s.event_definitions_data)return false;
  for(std::int32_t i=0;i<s.event_definitions_count;++i){
    const auto def=Read<std::uintptr_t>(s.event_definitions_data,i*8ULL);if(!def)return false;
    for(std::size_t j=0;j<keys.size();++j){
      if(!KeyEquals(def+0x10,keys[j],std::strlen(keys[j])))continue;
      auto &p=s.event_producer_definitions[j];if(p.read)return false;
      p.definition=def;p.definition_index=static_cast<std::uint32_t>(i);
      p.definition_id=Read<std::uint32_t>(def,8);p.runtime_stats_ordinal=Read<std::uint32_t>(def,0xC);
      p.immediate_root=Read<std::uintptr_t>(def,0x230);if(!p.immediate_root)return false;
      p.definition_vtable_rva=0x42F5710;p.root_vtable_rva=0x44CF030;p.original_execute_rva=0x3380EC0;
      p.root_hash=Read<std::uint32_t>(p.immediate_root,0x38);
      p.children_data=Read<std::uintptr_t>(p.immediate_root,0x40);
      p.children_capacity=Read<std::int32_t>(p.immediate_root,0x48);
      p.children_count=Read<std::int32_t>(p.immediate_root,0x4C);
      if(p.children_count<0||p.children_capacity<p.children_count||p.children_count>65536||
          (p.children_count!=0&&p.children_data==0))return false;
      if(!ReadStableKey(def+0x10,p.definition_key))return false;p.read=true;
    }
  }
  s.event_producer_definitions_read=true;
  for(std::size_t i=0;i<s.event_producer_definitions.size();++i){
    const auto &p=s.event_producer_definitions[i];if(!EventIdentityStable(s,p)){s.event_producer_definitions_read=false;return false;}
    for(std::size_t j=0;j<i;++j)if(p.definition==s.event_producer_definitions[j].definition ||
        p.immediate_root==s.event_producer_definitions[j].immediate_root){s.event_producer_definitions_read=false;return false;}
    for(std::int32_t j=0;j<s.event_definitions_count;++j){const auto def=Read<std::uintptr_t>(s.event_definitions_data,j*8ULL);
      if(def!=p.definition&&Read<std::uintptr_t>(def,0x230)==p.immediate_root){s.event_producer_definitions_read=false;return false;}
    }
  }
  return Read<std::int32_t>(s.event_manager,0x48)==cap;
}
bool ResolveSignatureKey(ScopedCharacterVariableMonitorV1 &session, std::uintptr_t table) noexcept {
  // 3B971C0 returns this already-initialized table. 3B970D1..EE reads the
  // name vector; insertion 3B96F56..5F binds byte0 epoch + index. No helper call.
  const auto data = Read<std::uintptr_t>(table, 0x30);
  const auto count = Read<std::int32_t>(table, 0x3C);
  const auto epoch = Read<std::uint8_t>(table);
  if (data == 0 || count <= 0 || count > 1'048'576 || epoch > 127) return false;
  std::int32_t match = -1;
  for (std::int32_t i = 0; i < count; ++i) {
    if (!KeyEquals(data + static_cast<std::size_t>(i) * 0x20, "signature_weapon", 16)) continue;
    if (match != -1) return false;
    match = static_cast<std::int32_t>((static_cast<std::uint32_t>(epoch) << 24) |
                                     static_cast<std::uint32_t>(i));
  }
  if (match < 0 || Read<std::uintptr_t>(table, 0x30) != data ||
      Read<std::int32_t>(table, 0x3C) != count || Read<std::uint8_t>(table) != epoch) return false;
  session.signature_key_id = match;
  session.identifier_table = table;
  session.identifier_count = static_cast<std::uint32_t>(count);
  session.identifier_epoch = epoch;
  return true;
}
bool NamedExtent(std::uintptr_t pointer,std::uintptr_t size) noexcept {
  return pointer!=0 && size<=std::numeric_limits<std::uintptr_t>::max()-pointer;
}
bool NamedRows(std::uintptr_t data,std::int32_t count,std::uintptr_t stride) noexcept {
  if(count<0 || count>65536)return false;
  return count==0 || NamedExtent(data,static_cast<std::uintptr_t>(count)*stride);
}
bool ResolveDeadCharacterKey(ScopedCharacterVariableMonitorV1 &session) noexcept {
  const auto table=session.identifier_table;
  if(!NamedExtent(table,0x40))return false;
  const auto data=Read<std::uintptr_t>(table,0x30);
  const auto count=Read<std::int32_t>(table,0x3C);
  const auto epoch=Read<std::uint8_t>(table);
  if(!NamedExtent(table,0x40) || !data || count<=0 || count>1048576 ||
      !NamedExtent(data,static_cast<std::uintptr_t>(count)*0x20) || epoch!=session.identifier_epoch ||
      static_cast<std::uint32_t>(count)!=session.identifier_count)return false;
  std::int32_t found=-1;
  for(std::int32_t i=0;i<count;++i)if(KeyEquals(data+i*0x20ULL,"dead_character",14)){
    if(found!=-1)return false;
    found=static_cast<std::int32_t>((static_cast<std::uint32_t>(epoch)<<24)|static_cast<std::uint32_t>(i));
  }
  if(found<0 || Read<std::uintptr_t>(table,0x30)!=data || Read<std::int32_t>(table,0x3C)!=count ||
      Read<std::uint8_t>(table)!=epoch)return false;
  session.dead_character_key_id=found;return true;
}
bool ReadNamedDeadCharacterOnce(const ScopedCharacterVariableMonitorV1 &s,std::uintptr_t context,
    ScopedNotificationNamedDeadCharacterV1 &out) noexcept {
  out.execution_context=context;out.key_id=s.dead_character_key_id;
  out.failure_stage=ScopedNotificationNamedReadFailureV1::none;
  out.identifier_table=s.identifier_table;out.prearmed_identifier_count=s.identifier_count;
  out.prearmed_identifier_epoch=s.identifier_epoch;
  out.identifier_key_index=static_cast<std::uint32_t>(out.key_id)&0xFFFFFF;
  const auto fail=[&](ScopedNotificationNamedReadFailureV1 stage){out.failure_stage=stage;return false;};
  if(!NamedExtent(context,0x20))return fail(ScopedNotificationNamedReadFailureV1::context_extent);
  if(out.key_id<0 || (static_cast<std::uint32_t>(out.key_id)>>24)!=s.identifier_epoch)
    return fail(ScopedNotificationNamedReadFailureV1::prearmed_key);
  if(!NamedExtent(s.identifier_table,0x40))return fail(ScopedNotificationNamedReadFailureV1::identifier_table_extent);
  const auto names=Read<std::uintptr_t>(s.identifier_table,0x30);
  const auto count=Read<std::int32_t>(s.identifier_table,0x3C);
  const auto epoch=Read<std::uint8_t>(s.identifier_table);
  out.identifier_data=names;out.identifier_count=count;out.identifier_epoch=epoch;out.identifier_header_read=true;
  const auto index=out.identifier_key_index;
  if(!names || count<=0 || count>1048576 || !NamedExtent(names,static_cast<std::uintptr_t>(count)*0x20))
    return fail(ScopedNotificationNamedReadFailureV1::identifier_names_span);
  if(static_cast<std::uint32_t>(count)<s.identifier_count)
    return fail(ScopedNotificationNamedReadFailureV1::identifier_count_shrunk);
  if(epoch!=s.identifier_epoch)return fail(ScopedNotificationNamedReadFailureV1::identifier_epoch);
  if(index>=static_cast<std::uint32_t>(count))return fail(ScopedNotificationNamedReadFailureV1::identifier_key_index);
  out.identifier_key_name_matches=KeyEquals(names+index*0x20ULL,"dead_character",14);
  if(!out.identifier_key_name_matches)return fail(ScopedNotificationNamedReadFailureV1::identifier_key_name);
  out.store=Read<std::uintptr_t>(context,0x18);if(!NamedExtent(out.store,0x10))return fail(ScopedNotificationNamedReadFailureV1::store_extent);
  out.primary_data=Read<std::uintptr_t>(out.store);out.primary_count=Read<std::int32_t>(out.store,0xC);
  if(!NamedRows(out.primary_data,out.primary_count,0x20))return fail(ScopedNotificationNamedReadFailureV1::primary_rows);
  for(std::int32_t i=0;i<out.primary_count;++i){const auto row=out.primary_data+i*0x20ULL;
    if(Read<std::int32_t>(row)!=out.key_id)continue;
    out.present=true;out.source_level=1;out.found_row=row;out.found_index=i;
    out.scope_words={Read<std::uint64_t>(row,8),Read<std::uint64_t>(row,0x10)};out.scope_words_read=true;break;
  }
  // Original3359690 consults the parent only after no primary key match, even when the primary value is kind0.
  if(!out.present){
    if(!NamedExtent(out.store,0x3D8))return fail(ScopedNotificationNamedReadFailureV1::fallback_store_extent);
    out.fallback_pointer_read=true;out.fallback_parent=Read<std::uintptr_t>(out.store,0x3D0);
    if(out.fallback_parent){
      if(!NamedExtent(out.fallback_parent,0x28))return fail(ScopedNotificationNamedReadFailureV1::fallback_parent_extent);
      out.fallback_header_read=true;out.fallback_data=Read<std::uintptr_t>(out.fallback_parent,0x18);
      out.fallback_count=Read<std::int32_t>(out.fallback_parent,0x24);
      if(!NamedRows(out.fallback_data,out.fallback_count,0x18))return fail(ScopedNotificationNamedReadFailureV1::fallback_rows);
      for(std::int32_t i=0;i<out.fallback_count;++i){const auto row=out.fallback_data+i*0x18ULL;
        if(Read<std::int32_t>(row)!=out.key_id)continue;
        out.present=true;out.source_level=2;out.found_row=row;out.found_index=i;
        out.scope_words={Read<std::uint64_t>(row,8),Read<std::uint64_t>(row,0x10)};out.scope_words_read=true;break;
      }
    }
  }
  // Missing original lookup writes kind0 and payload0, not the complete word0 padding.
  if(out.present){out.kind=Read<std::uint16_t>(out.found_row,8);out.subtype=Read<std::uint16_t>(out.found_row,0xA);
    out.payload=Read<std::int64_t>(out.found_row,0x10);out.payload_raw64=Read<std::uint64_t>(out.found_row,0x10);
    // Exact original201AD3C reads the dword payload; preserve the full copied16B independently.
    if(out.kind==4){
      out.character_full_id_low32_read=true;out.character_full_id_raw32=Read<std::uint32_t>(out.found_row,0x10);
      out.character_id=static_cast<std::int32_t>(out.character_full_id_raw32);
    }
    if(out.kind==4 && out.character_id>0){
      out.resolved_character=ResolveCharacter(s.bindings,out.character_id);
      if(out.resolved_character){if(!NamedExtent(out.resolved_character,0x1C))return fail(ScopedNotificationNamedReadFailureV1::resolved_character_extent);
        out.character_identity_read=true;out.observed_character_id=Read<std::int32_t>(out.resolved_character,0x18);
        out.character_full_identity_matches=out.observed_character_id==out.character_id;
        out.matches_monitored_victim=out.character_full_identity_matches && out.character_id==s.character_ids[0] &&
          out.resolved_character==s.character_objects[0];}
    }
  }
  if(Read<std::uintptr_t>(s.identifier_table,0x30)!=names || Read<std::int32_t>(s.identifier_table,0x3C)!=count ||
      Read<std::uint8_t>(s.identifier_table)!=epoch)return fail(ScopedNotificationNamedReadFailureV1::identifier_header_changed);
  if(!KeyEquals(names+index*0x20ULL,"dead_character",14))return fail(ScopedNotificationNamedReadFailureV1::identifier_key_changed);
  return true;
}
bool ReadSignature(const ScopedCharacterVariableMonitorV1 &session, std::uintptr_t container,
                   ScopedVariableValueV1 &value) noexcept {
  const auto rows = Read<std::uintptr_t>(container, 8);
  const auto capacity = Read<std::int32_t>(container, 0x10);
  const auto count = Read<std::int32_t>(container, 0x14);
  if (capacity < 0 || count < 0 || count > capacity || count > 8192 || (count != 0 && rows == 0)) return false;
  for (std::int32_t i = 0; i < count; ++i) {
    const auto row = rows + static_cast<std::size_t>(i) * 0x20;
    if (Read<std::int32_t>(row, 8) != session.signature_key_id) continue;
    if (value.present) return false;
    value.present = true;
    value.expiration_raw = Read<std::int32_t>(row, 0x0C);
    value.words = {Read<std::uint64_t>(row, 0x10), Read<std::uint64_t>(row, 0x18)};
  }
  value.read = true;
  return true;
}
bool DecodeFlag(const ScopedCharacterVariableMonitorV1 &session,ScopedVariableValueV1 &value) noexcept {
  if(!value.present||(value.words[0]&0xFFFF)!=3)return true;
  const auto table=session.identifier_table;const auto data=Read<std::uintptr_t>(table,0x30);
  const auto count=Read<std::int32_t>(table,0x3C);const auto epoch=Read<std::uint8_t>(table);
  const auto index=static_cast<std::uint32_t>(value.words[1])&0xFFFFFF;
  if(epoch!=session.identifier_epoch||count<=0||count>1048576||index>=static_cast<std::uint32_t>(count)||data==0)return false;
  if(!ReadStableKey(data+index*0x20,value.flag_name)||Read<std::uintptr_t>(table,0x30)!=data||
     Read<std::int32_t>(table,0x3C)!=count||Read<std::uint8_t>(table)!=epoch)return false;
  value.flag_identifier_count=static_cast<std::uint32_t>(count);value.flag_identifier_epoch=epoch;
  value.flag_index=index;value.flag_name_read=true;return true;
}
void Fail(ScopedCharacterVariableMonitorV1 &session, ScopedVariableMonitorRecordV1 *row,
          std::uint32_t bit) noexcept {
  session.failure_flags.fetch_or(bit);
  if (row != nullptr) row->failure_flags |= bit;
}
void ReadRecordState(ScopedCharacterVariableMonitorV1 &session,
    ScopedVariableMonitorRecordV1 &row, ScopedVariableMonitorBoundaryV1 boundary,
    std::int32_t character, std::uint32_t invocation) noexcept {
  row.invocation = invocation; row.boundary = boundary;
  row.thread_id = GetCurrentThreadId(); row.character_id = character;
  row.key_id = session.signature_key_id;
  if ((boundary==ScopedVariableMonitorBoundaryV1::variable_write_enter ||
       boundary==ScopedVariableMonitorBoundaryV1::variable_write_return ||
       boundary==ScopedVariableMonitorBoundaryV1::original_owner_return) && character>0)
    (void)ReadCurrentCombatScopedDeathCommitContextV1(row.current_death_commit_context);
  if ((boundary==ScopedVariableMonitorBoundaryV1::variable_write_enter ||
        boundary==ScopedVariableMonitorBoundaryV1::variable_write_return ||
        boundary==ScopedVariableMonitorBoundaryV1::original_owner_return) &&
      character>0 && g_event_producer.read) {
    if (EventIdentityStable(session,g_event_producer)) {row.event_producer=g_event_producer;
      row.event_producer.active_effect_group_depth=g_event_root_depth;
      if(boundary!=ScopedVariableMonitorBoundaryV1::original_owner_return &&
          !ReadScopedNotificationNamedDeadCharacterV1(session,row.event_producer.context,
            row.event_producer.named_dead_character_at_observation))Fail(session,&row,scoped_chain_failure_container);}
    else Fail(session,&row,scoped_chain_failure_identity);
  }
  (void)ReadCurrentCombatScopedEffectContextV1(row.daily_effect_context);
  const auto date = Read<std::uintptr_t>(session.date_slot);
  if (date != session.date_object) Fail(session, &row, scoped_chain_failure_identity);
  else {
    row.date_raw = Read<std::int32_t>(date, 8);
    if (row.date_raw != session.begin_date && row.date_raw != session.begin_date + 24)
      Fail(session, &row, scoped_chain_failure_thread_or_date);
  }
  for (std::size_t i = 0; i < 2; ++i) {
    const auto object = ResolveCharacter(session.bindings, session.character_ids[i]);
    if (object == 0 || object != session.character_objects[i]) Fail(session, &row, scoped_chain_failure_identity);
    if (session.character_ids[i] != character || object == 0) continue;
    row.observed_character_id = Read<std::int32_t>(object, 0x18);
    row.full_identity_matches = row.observed_character_id == character && object == session.character_objects[i];
    row.victim_dead = Read<std::uintptr_t>(object, 0x1C8) != 0;
  }
}
ScopedVariableMonitorRecordV1 *Record(ScopedCharacterVariableMonitorV1 &session,
    ScopedVariableMonitorBoundaryV1 boundary, std::int32_t character = -1,
    std::uint32_t invocation = 0) noexcept {
  if(boundary!=ScopedVariableMonitorBoundaryV1::original_owner_return)
    session.owner_activity_epoch.fetch_add(1);
  const auto index = session.count.fetch_add(1);
  if (index >= session.records.size()) { Fail(session, nullptr, scoped_chain_failure_capacity); return nullptr; }
  auto &row = session.records[index];
  row.sequence = index;
  ReadRecordState(session,row,boundary,character,invocation);
  return &row;
}
bool SameDeadNullOwnerReturn(const ScopedVariableMonitorRecordV1 &a,
                            const ScopedVariableMonitorRecordV1 &b) noexcept {
  const auto eligible=[](const ScopedVariableMonitorRecordV1 &r) noexcept {
    return r.boundary==ScopedVariableMonitorBoundaryV1::original_owner_return &&
        r.failure_flags==0 && r.full_identity_matches && r.victim_dead &&
        r.owner_from_original_getter && r.owner==0 && r.container==0 && !r.value.read;
  };
  return eligible(a)&&eligible(b)&&a.character_id==b.character_id &&
      a.observed_character_id==b.observed_character_id && a.thread_id==b.thread_id &&
      a.date_raw==b.date_raw && a.key_id==b.key_id && a.previous_owner==b.previous_owner &&
      a.value==b.value && a.owner_state_epoch==b.owner_state_epoch &&
      a.owner_activity_epoch==b.owner_activity_epoch && a.caller==b.caller &&
      a.native_root_scope==b.native_root_scope && a.native_scope_words==b.native_scope_words &&
      a.setter_node==b.setter_node && a.execution_context==b.execution_context &&
      a.daily_effect_context==b.daily_effect_context &&
      a.current_death_commit_context==b.current_death_commit_context &&
      a.event_producer==b.event_producer;
}
void PublishOwnerReturnLocked(ScopedCharacterVariableMonitorV1 &session,
    std::size_t character_index, std::uintptr_t scope, std::uintptr_t owner,
    std::uintptr_t caller) noexcept {
  const auto call_index=session.owner_getter_observed.fetch_add(1);
  const auto previous=session.owners[character_index].exchange(owner);
  if(g_setter_context.node!=0){g_setter_context.original_owner=owner;
    g_setter_context.character_id=session.character_ids[character_index];}
  ScopedVariableValueV1 value{};
  const bool read=owner!=0&&ReadSignature(session,owner+8,value)&&DecodeFlag(session,value);
  ScopedVariableMonitorRecordV1 candidate{};
  ReadRecordState(session,candidate,ScopedVariableMonitorBoundaryV1::original_owner_return,
                  session.character_ids[character_index],0);
  candidate.owner=owner;candidate.previous_owner=previous;
  candidate.container=owner!=0?owner+8:0;candidate.owner_from_original_getter=true;
  candidate.value=value;candidate.caller=caller;candidate.native_root_scope=scope;
  candidate.native_scope_words={Read<std::uint64_t>(scope),Read<std::uint64_t>(scope,8)};
  candidate.setter_node=g_setter_context.node;candidate.execution_context=g_setter_context.context;
  const bool changed=!session.owner_state_seen[character_index] || previous!=owner ||
      value!=session.last_owner_values[character_index] ||
      candidate.victim_dead!=session.last_owner_dead[character_index];
  if(changed)++session.owner_state_epochs[character_index];
  session.owner_state_seen[character_index]=true;
  session.last_owner_dead[character_index]=candidate.victim_dead;
  session.last_owner_values[character_index]=value;
  candidate.owner_state_epoch=session.owner_state_epochs[character_index];
  candidate.owner_activity_epoch=session.owner_activity_epoch.load();
  if(!read&&owner!=0)Fail(session,&candidate,scoped_chain_failure_container);
  if(!changed&&read&&candidate.failure_flags==0){
    // Preserve the pre-existing unchanged non-null suppression, now counted honestly.
    session.owner_nonnull_unchanged_unrecorded.fetch_add(1);return;
  }
  for(std::uint32_t i=0;i<session.owner_record_count;++i){
    auto &kept=session.records[session.owner_record_indices[i]];
    if(SameDeadNullOwnerReturn(kept,candidate) &&
       candidate.owner_activity_epoch==session.owner_activity_epoch.load()){
      kept.owner_observation_last_call_index=call_index;
      ++kept.owner_observation_count;session.owner_getter_coalesced.fetch_add(1);return;
    }
  }
  const auto index=session.count.fetch_add(1);
  if(index>=session.records.size()){Fail(session,nullptr,scoped_chain_failure_capacity);return;}
  candidate.sequence=index;candidate.owner_observation_first_call_index=call_index;
  candidate.owner_observation_last_call_index=call_index;candidate.owner_observation_count=1;
  session.records[index]=candidate;
  session.owner_record_indices[session.owner_record_count++]=index;
  session.owner_getter_retained.fetch_add(1);
}
void NodeProvenance(ScopedCharacterVariableMonitorV1 &session, ScopedVariableMonitorRecordV1 &row,
                    std::uintptr_t caller) noexcept {
  row.setter_node = g_setter_context.node;
  row.execution_context = g_setter_context.context;
  row.caller = caller;
  if (row.setter_node != 0) {
    const auto vtable = Read<std::uintptr_t>(row.setter_node);
    if (vtable < session.module_base || vtable - session.module_base >= 0x6000000)
      Fail(session, &row, scoped_chain_failure_identity);
    else row.setter_node_vtable_rva = static_cast<std::uint32_t>(vtable - session.module_base);
    row.setter_node_hash = Read<std::uint32_t>(row.setter_node, 0x38);
  }
  if (row.execution_context != 0) {
    row.native_root_scope = Read<std::uintptr_t>(row.execution_context);
    if (row.native_root_scope != 0) row.native_scope_words = {
        Read<std::uint64_t>(row.native_root_scope), Read<std::uint64_t>(row.native_root_scope, 8)};
  }
  std::array<void *, 40> frames{};
  row.stack_count = CaptureStackBackTrace(0, static_cast<DWORD>(frames.size()), frames.data(), nullptr);
  for (std::uint32_t i = 0; i < row.stack_count; ++i) {
    const auto address = reinterpret_cast<std::uintptr_t>(frames[i]);
    row.stack_rvas[i] = address >= session.module_base && address - session.module_base < 0x6000000
        ? static_cast<std::uint32_t>(address - session.module_base) : 0;
  }
}
constexpr std::array<std::uint8_t,16> kOwner{
    0x48,0x89,0x5C,0x24,0x08,0x57,0x48,0x83,0xEC,0x20,0x0F,0xB7,0x39,0x48,0x8B,0xD9};
constexpr std::array<std::uint8_t,14> kSetter{
    0x48,0x89,0x5C,0x24,0x20,0x56,0x48,0x83,0xEC,0x40,0x4C,0x63,0x51,0x14};
constexpr std::array<std::uint8_t,18> kEffect{
    0x48,0x89,0x5C,0x24,0x08,0x48,0x89,0x74,0x24,0x18,0x57,0x48,0x81,0xEC,0x70,0x02,0,0};
constexpr std::array<std::uint8_t,15> kHouse{
    0x48,0x89,0x5C,0x24,0x08,0x48,0x89,0x6C,0x24,0x10,0x48,0x89,0x74,0x24,0x18};
constexpr std::array<std::uint8_t,15> kEventRoot{
    0x48,0x89,0x5C,0x24,0x08,0x48,0x89,0x74,0x24,0x10,0x57,0x48,0x83,0xEC,0x20};
std::array<std::uintptr_t,5> Callbacks() noexcept {
  return {reinterpret_cast<std::uintptr_t>(&ObservedCharacterVariableOwnerV1),
          reinterpret_cast<std::uintptr_t>(&ObservedCharacterVariableSetterV1),
          reinterpret_cast<std::uintptr_t>(&ObservedCharacterVariableEffectV1),
          reinterpret_cast<std::uintptr_t>(&ObservedScopedHousePredicateV1),
          reinterpret_cast<std::uintptr_t>(&ObservedScopedEventImmediateRootV1)};
}
bool Uninstall(ScopedCharacterVariableMonitorV1 &session) noexcept {
  const auto callbacks = Callbacks(); bool okay = true;
  for (std::size_t i=session.detours.size();i!=0;--i) okay = UninstallCombatScopedExactDetourV1(session.detours[i-1],callbacks[i-1]) && okay;
  // Original trampoline pointers remain callable for late decoded branches.
  session.detours_uninstalled = okay;
  return okay;
}
bool StartUnsafe(ScopedCharacterVariableMonitorV1 &session, const Bindings &bindings,
    std::uintptr_t module, std::array<std::int32_t,2> ids, std::uint64_t token,
    bool exact, bool paused, std::uintptr_t table_override, std::uintptr_t date_override,
    std::uintptr_t event_override) noexcept {
  if (!exact || !paused || module==0 || token==0 || ids[0]<=0 || ids[1]<=0 || ids[0]==ids[1] ||
      g_monitor.load()!=nullptr || session.stage!=ScopedVariableMonitorStageV1::idle) return false;
  session.bindings=bindings; session.module_base=module; session.character_ids=ids; session.token=token;
  for (std::size_t i=0;i<2;++i) {
    session.character_objects[i]=ResolveCharacter(bindings,ids[i]);
    if(session.character_objects[i]==0)return false;
  }
  session.date_slot=date_override!=0?date_override:module+0x570E068;
  session.date_object=Read<std::uintptr_t>(session.date_slot);
  if(session.date_object==0)return false;
  session.begin_date=Read<std::int32_t>(session.date_object,8);
  if(session.begin_date<=0 || session.begin_date>std::numeric_limits<std::int32_t>::max()-24 ||
      !ResolveSignatureKey(session,table_override!=0?table_override:module+0x585F240) ||
      !ResolveDeadCharacterKey(session)) return false;
  if ((table_override==0 || event_override!=0) &&
      !ResolveEventProducers(session,event_override!=0?event_override:module+0x570F790)) return false;
  if (table_override==0) {
    if (!PinScopedObserverModuleUntilProcessExitV1(reinterpret_cast<const void *>(&ObservedCharacterVariableOwnerV1))) return false;
    const auto callbacks=Callbacks();
    const bool okay=
        InstallCombatScopedExactDetourV1(session.detours[0],module+0x3329A40,callbacks[0],kOwner.data(),kOwner.size()) &&
        (g_owner.store(reinterpret_cast<ScopedVariableOwnerOriginalV1>(session.detours[0].trampoline)),true) &&
        InstallCombatScopedExactDetourV1(session.detours[1],module+0x3346BE0,callbacks[1],kSetter.data(),kSetter.size()) &&
        (g_setter.store(reinterpret_cast<ScopedVariableSetterOriginalV1>(session.detours[1].trampoline)),true) &&
        InstallCombatScopedExactDetourV1(session.detours[2],module+0x3393530,callbacks[2],kEffect.data(),kEffect.size()) &&
        (g_effect.store(reinterpret_cast<ScopedVariableEffectOriginalV1>(session.detours[2].trampoline)),true) &&
        InstallCombatScopedExactDetourV1(session.detours[3],module+0x2DF7030,callbacks[3],kHouse.data(),kHouse.size()) &&
        (g_house.store(reinterpret_cast<ScopedHousePredicateOriginalV1>(session.detours[3].trampoline)),true) &&
        InstallCombatScopedExactDetourV1(session.detours[4],module+0x3380EC0,callbacks[4],kEventRoot.data(),kEventRoot.size()) &&
        (g_event_root.store(reinterpret_cast<ScopedEventImmediateRootOriginalV1>(session.detours[4].trampoline)),true);
    if(!okay){Fail(session,nullptr,scoped_chain_failure_detour);(void)Uninstall(session);return false;}
  } else if(g_owner.load()==nullptr||g_setter.load()==nullptr||g_effect.load()==nullptr||g_house.load()==nullptr) return false;
  if(!BindCombatScopedOriginalDeathCommitObserverV1(&ObserveScopedVariableMonitorOriginalDeathCommitV1)){
    Fail(session,nullptr,scoped_chain_failure_detour);(void)Uninstall(session);return false;
  }
  g_setter_context={};g_event_producer={}; session.armed.store(1);g_monitor.store(&session);session.stage=ScopedVariableMonitorStageV1::armed;
  (void)Record(session,ScopedVariableMonitorBoundaryV1::arm);
  return session.failure_flags.load()==0;
}
} // namespace

bool ReadScopedNotificationNamedDeadCharacterV1(const ScopedCharacterVariableMonitorV1 &session,
    std::uintptr_t context,ScopedNotificationNamedDeadCharacterV1 &out) noexcept {
  out={};
  __try {
    if(!ReadNamedDeadCharacterOnce(session,context,out))return false;
    const auto first=out;out={};
    if(!ReadNamedDeadCharacterOnce(session,context,out))return false;
    const auto second=out;
    return ValidateScopedNotificationNamedDeadCharacterPairV1(first,second,out);
  } __except(EXCEPTION_EXECUTE_HANDLER){out.read=false;out.stable_two_reads=false;
    out.failure_stage=ScopedNotificationNamedReadFailureV1::access_fault;return false;}
}
bool ValidateScopedNotificationNamedDeadCharacterPairV1(const ScopedNotificationNamedDeadCharacterV1 &first,
    const ScopedNotificationNamedDeadCharacterV1 &second,ScopedNotificationNamedDeadCharacterV1 &out) noexcept {
  const auto a=first,b=second;out=b;out.read=false;out.stable_two_reads=false;
  if(a.failure_stage!=ScopedNotificationNamedReadFailureV1::none){out=a;out.read=false;out.stable_two_reads=false;return false;}
  if(b.failure_stage!=ScopedNotificationNamedReadFailureV1::none)return false;
  if(!a.identifier_header_read || !b.identifier_header_read){out.failure_stage=ScopedNotificationNamedReadFailureV1::observations_unread;return false;}
  if(a!=b){out.failure_stage=ScopedNotificationNamedReadFailureV1::snapshots_differ;return false;}
  out.read=true;out.stable_two_reads=true;return true;
}

void ObserveScopedVariableMonitorOriginalDeathCommitV1(bool entering, void *manager,
    void *victim, void *reason, void *date, void *killer, void *artifact) noexcept {
  auto *const session=g_monitor.load(std::memory_order_acquire);
  if(session==nullptr)return;
  session->active_callbacks.fetch_add(1);
  __try {
    if(session->armed.load(std::memory_order_acquire)==0)return;
    CombatScopedDeathCommitContextV1 active{};
    const bool active_read=ReadCurrentCombatScopedDeathCommitContextV1(active);
    auto *row=Record(*session,entering?ScopedVariableMonitorBoundaryV1::original_death_commit_enter:
        ScopedVariableMonitorBoundaryV1::original_death_commit_return,
        active_read?active.victim_id:-1,active.invocation);
    if(row==nullptr)return;
    auto &sample=row->original_death_commit_context;
    sample=active;sample.read=false;
    // Every argument token below comes from this original call's six parameters.
    sample.manager=reinterpret_cast<std::uintptr_t>(manager);
    sample.victim=reinterpret_cast<std::uintptr_t>(victim);
    sample.reason=reinterpret_cast<std::uintptr_t>(reason);
    sample.date_argument=reinterpret_cast<std::uintptr_t>(date);
    sample.killer=reinterpret_cast<std::uintptr_t>(killer);
    sample.artifact=reinterpret_cast<std::uintptr_t>(artifact);
    sample.artifact_actual_null=artifact==nullptr;
    sample.artifact_id_read=false;sample.artifact_id=-1;
    sample.reason_key_read=false;sample.reason_key={};
    __try {
      if(victim==nullptr || date==nullptr || manager==nullptr){Fail(*session,row,scoped_chain_failure_container);return;}
      sample.victim_id=Read<std::int32_t>(sample.victim,0x18);
      sample.killer_id=killer!=nullptr?Read<std::int32_t>(sample.killer,0x18):-1;
      sample.requested_death_date_raw=Read<std::int64_t>(sample.date_argument);
      if(reason!=nullptr)sample.reason_key_read=ReadStableKey(sample.reason+0x18,sample.reason_key);
      if(artifact!=nullptr){sample.artifact_id=Read<std::int32_t>(sample.artifact,0x10);sample.artifact_id_read=true;}
      sample.victim_full_identity_matches=false;sample.killer_full_identity_matches=killer==nullptr;
      for(std::size_t i=0;i<session->character_ids.size();++i){
        const auto object=ResolveCharacter(session->bindings,session->character_ids[i]);
        if(object!=0 && object==session->character_objects[i]){
          if(sample.victim_id==session->character_ids[i] && sample.victim==object)sample.victim_full_identity_matches=true;
          if(sample.killer_id==session->character_ids[i] && sample.killer==object)sample.killer_full_identity_matches=true;
        }
      }
      if(!active_read || active.managed_daily_sequence_token==0 || active.invocation==0 || active.combat_id<=0 ||
         active.thread_id!=row->thread_id || active.native_date_raw!=row->date_raw ||
         !sample.victim_full_identity_matches || !sample.killer_full_identity_matches ||
         sample.manager!=active.manager || sample.victim!=active.victim || sample.reason!=active.reason ||
         sample.date_argument!=active.date_argument || sample.killer!=active.killer || sample.artifact!=active.artifact ||
         sample.victim_id!=active.victim_id || sample.killer_id!=active.killer_id ||
         sample.requested_death_date_raw!=active.requested_death_date_raw ||
         sample.artifact_actual_null!=active.artifact_actual_null || sample.artifact_id_read!=active.artifact_id_read ||
         sample.artifact_id!=active.artifact_id || sample.reason_key_read!=active.reason_key_read || sample.reason_key!=active.reason_key){
        Fail(*session,row,scoped_chain_failure_identity);return;
      }
      if(reason!=nullptr && !sample.reason_key_read){Fail(*session,row,scoped_chain_failure_container);return;}
      sample.read=true;
    } __except(EXCEPTION_EXECUTE_HANDLER){Fail(*session,row,scoped_chain_failure_memory);}
  } __finally {session->active_callbacks.fetch_sub(1);}
}

extern "C" void *__fastcall ObservedCharacterVariableOwnerV1Impl(const void *scope,
    std::uintptr_t caller) noexcept {
  const auto original=g_owner.load();if(original==nullptr)return nullptr;
  auto *const session=g_monitor.load();
  if(session!=nullptr)session->active_callbacks.fetch_add(1);
  auto *const result=original(scope);
  ObserveCombatScopedOriginalVariableOwnerV1(scope,result);
  if(session!=nullptr && session->armed.load()!=0) {
    __try {
      const auto object=reinterpret_cast<std::uintptr_t>(scope);
      const auto kind=Read<std::uint16_t>(object);
      const auto payload=Read<std::int64_t>(object,8);
      if(kind==4 && payload>0 && payload<=std::numeric_limits<std::int32_t>::max()) {
        for(std::size_t i=0;i<2;++i)if(session->character_ids[i]==payload) {
          AcquireSRWLockExclusive(&session->owner_observation_lock);
          __try {PublishOwnerReturnLocked(*session,i,object,reinterpret_cast<std::uintptr_t>(result),caller);}
          __finally {ReleaseSRWLockExclusive(&session->owner_observation_lock);}
        }
      }
    } __except(EXCEPTION_EXECUTE_HANDLER){Fail(*session,nullptr,scoped_chain_failure_memory);}
  }
  if(session!=nullptr)session->active_callbacks.fetch_sub(1);
  return result;
}
extern "C" std::uintptr_t __fastcall ObservedCharacterVariableEffectV1Impl(void *node,void *context) noexcept {
  const auto original=g_effect.load();if(original==nullptr)return 0;
  const auto previous=g_setter_context;
  g_setter_context={reinterpret_cast<std::uintptr_t>(node),reinterpret_cast<std::uintptr_t>(context),0,-1};
  auto *const session=g_monitor.load();if(session)session->active_callbacks.fetch_add(1);
  const auto result=original(node,context);
  g_setter_context=previous;
  if(session)session->active_callbacks.fetch_sub(1);
  return result;
}
extern "C" std::uintptr_t __fastcall ObservedCharacterVariableSetterV1Impl(void *container,std::int32_t key,const void *value,std::int32_t duration, std::uintptr_t native_caller) noexcept {
  const auto original=g_setter.load();if(original==nullptr)return 0;
  auto *const session=g_monitor.load();if(session)session->active_callbacks.fetch_add(1);
  std::int32_t character=-1;std::uintptr_t owner=0;std::uint32_t invocation=0;
  const auto caller=native_caller;
  if(session&&session->armed.load()!=0&&key==session->signature_key_id) {
    __try {
      for(std::size_t i=0;i<2;++i) {
        const auto observed=session->owners[i].load();
        if(observed!=0&&observed+8==reinterpret_cast<std::uintptr_t>(container)){character=session->character_ids[i];owner=observed;}
      }
      if(character!=-1) {
        invocation=session->next_invocation.fetch_add(1)+1;
        auto *row=Record(*session,ScopedVariableMonitorBoundaryV1::variable_write_enter,character,invocation);
        if(row){
          row->owner=owner;row->container=reinterpret_cast<std::uintptr_t>(container);row->duration=duration;
          row->owner_from_original_getter=true;
          row->owner_from_same_setter_invocation=g_setter_context.original_owner==owner&&g_setter_context.character_id==character;
          row->requested_value={Read<std::uint64_t>(reinterpret_cast<std::uintptr_t>(value)),Read<std::uint64_t>(reinterpret_cast<std::uintptr_t>(value),8)};
          row->requested_value_decoding.read=true;row->requested_value_decoding.present=true;row->requested_value_decoding.words=row->requested_value;
          if(!DecodeFlag(*session,row->requested_value_decoding))Fail(*session,row,scoped_chain_failure_container);
          NodeProvenance(*session,*row,caller);
          if(!ReadSignature(*session,row->container,row->value)||!DecodeFlag(*session,row->value))Fail(*session,row,scoped_chain_failure_container);
          if(!row->owner_from_same_setter_invocation)Fail(*session,row,scoped_chain_failure_correlation);
        }
      }
    } __except(EXCEPTION_EXECUTE_HANDLER){Fail(*session,nullptr,scoped_chain_failure_memory);}
  }
  const auto result=original(container,key,value,duration);
  if(session&&character!=-1) {
    __try {
      auto *row=Record(*session,ScopedVariableMonitorBoundaryV1::variable_write_return,character,invocation);
      if(row){row->owner=owner;row->container=reinterpret_cast<std::uintptr_t>(container);row->original_return_bits=result;
        row->owner_from_original_getter=true;row->owner_from_same_setter_invocation=g_setter_context.original_owner==owner&&g_setter_context.character_id==character;
        NodeProvenance(*session,*row,caller);
        if(!ReadSignature(*session,row->container,row->value)||!DecodeFlag(*session,row->value))Fail(*session,row,scoped_chain_failure_container);}
    } __except(EXCEPTION_EXECUTE_HANDLER){Fail(*session,nullptr,scoped_chain_failure_memory);}
  }
  if(session)session->active_callbacks.fetch_sub(1);
  return result;
}
extern "C" std::uintptr_t __fastcall ObservedScopedHousePredicateV1Impl(void *type,void *first,void *second, std::uintptr_t native_caller) noexcept {
  const auto original=g_house.load();if(original==nullptr)return 0;
  auto *const session=g_monitor.load();if(session)session->active_callbacks.fetch_add(1);
  std::array<std::int32_t,2> ids{-1,-1};std::uint32_t invocation=0;bool matched=false;
  const auto caller=native_caller;
  if(session&&session->armed.load()!=0) {
    __try {
      ids={Read<std::int32_t>(reinterpret_cast<std::uintptr_t>(first),0x10),Read<std::int32_t>(reinterpret_cast<std::uintptr_t>(second),0x10)};
      const std::array<std::int32_t,2> current{
        Read<std::int32_t>(session->character_objects[0],0x150),Read<std::int32_t>(session->character_objects[1],0x150)};
      matched=current[0]>0&&current[1]>0&&current[0]!=current[1]&&
          ((ids[0]==current[0]&&ids[1]==current[1])||(ids[0]==current[1]&&ids[1]==current[0]));
      if(matched){invocation=session->next_invocation.fetch_add(1)+1;
        auto *row=Record(*session,ScopedVariableMonitorBoundaryV1::house_predicate_enter,-1,invocation);
        if(row){row->house_ids=ids;HouseType(*session,*row,type);row->caller=caller;}}
    } __except(EXCEPTION_EXECUTE_HANDLER){Fail(*session,nullptr,scoped_chain_failure_memory);}
  }
  const auto result=original(type,first,second);
  if(session&&matched) {
    __try {auto *row=Record(*session,ScopedVariableMonitorBoundaryV1::house_predicate_return,-1,invocation);
      if(row){row->house_ids=ids;HouseType(*session,*row,type);row->caller=caller;
        row->original_return_bits=result;row->original_boolean_read=true;row->original_boolean=(result&0xFF)!=0;
        if((result&0xFF)>1)Fail(*session,row,scoped_chain_failure_container);}}
    __except(EXCEPTION_EXECUTE_HANDLER){Fail(*session,nullptr,scoped_chain_failure_memory);}
  }
  if(session)session->active_callbacks.fetch_sub(1);
  return result;
}

extern "C" void __fastcall ObservedScopedEventImmediateRootV1Impl(void *root,void *context) noexcept {
  const auto original=g_event_root.load();if(!original)return;
  auto *const session=g_monitor.load();
  if(session)session->active_callbacks.fetch_add(1);
  const auto previous=g_event_producer;
  ++g_event_root_depth;
  // Unrelated event roots are not journaled. Only a matched two-character
  // signature setter copies this actual execution identity into its row.
  // Nested ordinary CJominiEffect groups inherit their matched notification
  // ancestor. A different matched notification replaces it only for its call.
  if(session&&session->armed.load()!=0&&session->event_producer_definitions_read){
    __try {
      // Another registered event's immediate root is a producer boundary.
      // Ordinary nested effect groups inherit; an unrelated registered event
      // cannot borrow this notification's identity for its own setter.
      if(previous.read && Read<std::uintptr_t>(session->event_manager_slot)==session->event_manager){
        const auto data=Read<std::uintptr_t>(session->event_manager,0x40);
        const auto count=Read<std::int32_t>(session->event_manager,0x4C);
        if(data!=session->event_definitions_data||count!=session->event_definitions_count){
          Fail(*session,nullptr,scoped_chain_failure_identity);g_event_producer={};
        } else {
          for(std::int32_t i=0;i<count;++i){const auto def=Read<std::uintptr_t>(data,i*8ULL);
            if(def && Read<std::uintptr_t>(def,0x230)==reinterpret_cast<std::uintptr_t>(root)){
              g_event_producer={};break;
            }
          }
        }
      }
      for(const auto &p:session->event_producer_definitions)if(p.immediate_root==reinterpret_cast<std::uintptr_t>(root)){
        if(!EventIdentityStable(*session,p)){Fail(*session,nullptr,scoped_chain_failure_identity);break;}
        g_event_producer=p;g_event_producer.invocation=session->next_invocation.fetch_add(1)+1;
        (void)ReadCurrentCombatScopedDeathCommitContextV1(g_event_producer.activation_death_commit_context);
        g_event_producer.matched_root_execution_depth=g_event_root_depth;
        g_event_producer.context=reinterpret_cast<std::uintptr_t>(context);
        if(!context){Fail(*session,nullptr,scoped_chain_failure_correlation);g_event_producer={};break;}
        g_event_producer.root_scope=Read<std::uintptr_t>(g_event_producer.context);
        if(g_event_producer.root_scope)g_event_producer.root_scope_words={
            Read<std::uint64_t>(g_event_producer.root_scope),Read<std::uint64_t>(g_event_producer.root_scope,8)};
        if(!ReadScopedNotificationNamedDeadCharacterV1(*session,g_event_producer.context,
            g_event_producer.named_dead_character_at_activation))Fail(*session,nullptr,scoped_chain_failure_container);
        break;
      }
    }__except(EXCEPTION_EXECUTE_HANDLER){Fail(*session,nullptr,scoped_chain_failure_memory);g_event_producer={};}
  }
  __try {original(root,context);}
  __finally {g_event_producer=previous;--g_event_root_depth;if(session)session->active_callbacks.fetch_sub(1);}
}
extern "C" void __fastcall ObservedScopedEventImmediateRootV1(void *root,void *context) noexcept {
  EnterScopedObserverCallbackV1();
  __try {ObservedScopedEventImmediateRootV1Impl(root,context);}
  __finally {LeaveScopedObserverCallbackV1();}
}

bool StartScopedCharacterVariableMonitorV1Impl(ScopedCharacterVariableMonitorV1 &session,const Bindings &bindings,
    std::uintptr_t module,std::array<std::int32_t,2> ids,std::uint64_t token,bool exact,bool paused,
    std::uintptr_t table,std::uintptr_t date,std::uintptr_t event) noexcept {
  __try{return StartUnsafe(session,bindings,module,ids,token,exact,paused,table,date,event);}
  __except(EXCEPTION_EXECUTE_HANDLER){
    Fail(session,nullptr,scoped_chain_failure_memory);
    session.armed.store(0);
    if(g_monitor.load()==&session)g_monitor.store(nullptr);
    (void)Uninstall(session);
    session.stage=ScopedVariableMonitorStageV1::failed;
    return false;
  }
}
bool FinishScopedCharacterVariableMonitorV1Impl(ScopedCharacterVariableMonitorV1 &session,bool paused) noexcept {
  if(!paused||session.stage!=ScopedVariableMonitorStageV1::armed||g_monitor.load()!=&session||session.active_callbacks.load()!=0)return false;
  __try {
    (void)Record(session,ScopedVariableMonitorBoundaryV1::final_paused);
    for(std::size_t i=0;i<2;++i){
      const auto owner=session.owners[i].load();
      if(owner==0)continue;
      auto *row=Record(session,ScopedVariableMonitorBoundaryV1::final_paused,session.character_ids[i]);
      // A dead character's owner may have migrated after its last getter.
      // Preserve the token; do not turn a cached pointer into a final read.
      if(row){row->owner=owner;row->container=owner+8;row->owner_from_original_getter=true;}
    }
  } __except(EXCEPTION_EXECUTE_HANDLER){Fail(session,nullptr,scoped_chain_failure_memory);}
  session.armed.store(0);g_monitor.store(nullptr);
  if(!Uninstall(session)){Fail(session,nullptr,scoped_chain_failure_detour);session.stage=ScopedVariableMonitorStageV1::failed;return false;}
  session.stage=ScopedVariableMonitorStageV1::drained;
  return true;
}
bool ScopedVariableMonitorHasInstalledHooksV1(const ScopedCharacterVariableMonitorV1 &session) noexcept {
  return std::any_of(session.detours.begin(),session.detours.end(),[](const auto &site){return site.installed;});
}
bool BindScopedVariableMonitorOfflineOriginalsV1(ScopedVariableOwnerOriginalV1 owner,
    ScopedVariableSetterOriginalV1 setter,ScopedVariableEffectOriginalV1 effect,ScopedHousePredicateOriginalV1 house,
    ScopedEventImmediateRootOriginalV1 event_root) noexcept {
  if(g_monitor.load()!=nullptr||!owner||!setter||!effect||!house)return false;
  g_owner.store(owner);g_setter.store(setter);g_effect.store(effect);g_house.store(house);g_event_root.store(event_root);return true;
}
namespace {
bool QueryUnsafe(ScopedVariableMonitorQueryV1 &query,const MainThreadExecutionStampV1 &stamp) noexcept {
  if(!query.mailbox||!query.session||!query.game_adapter||!query.exact_build||query.token==0||
     query.ticket.sequence==0||!stamp.paused||stamp.thread_id!=GetCurrentThreadId()||stamp.pump_epoch==0||
      stamp.tls_initialized_flag_address==0||stamp.tls_initialized!=1||stamp.tls_context==0||stamp.tls_main_thread_marker!=1||
      stamp.jomini_state==0||stamp.game_state==0||stamp.date_raw!=query.expected_snapshot.date_raw||
      query.mailbox->owner_thread_id.load()!=stamp.thread_id||
      query.mailbox->paused_owner_verified_pump_epochs.load()<kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs||
      query.mailbox->executor!=&ExecuteScopedVariableMonitorQueryV1||
      query.mailbox->executor_context!=&query||
     query.mailbox->state.load()!=MainThreadQueryMailboxStateV1::executing||
     query.mailbox->published_sequence.load()!=query.ticket.sequence||
     query.mailbox->stop_requested.load()||query.mailbox->failure_flags.load()!=0) return false;
  game::Snapshot snapshot{};
  if(!game::ReadSnapshot(*query.game_adapter,snapshot)||!snapshot.paused||snapshot!=query.expected_snapshot)return false;
  if(query.begin){
    if(!StartScopedCharacterVariableMonitorV1(*query.session,query.bindings,query.module_base,
        query.character_ids,query.token,true,true))return false;
  }else{
    if(query.session->token!=query.token||!FinishScopedCharacterVariableMonitorV1(*query.session,true))return false;
  }
  game::Snapshot after{};
  if(!game::ReadSnapshot(*query.game_adapter,after)||after!=snapshot)return false;
  return true;
}
}
bool ExecuteScopedVariableMonitorQueryV1(void *context,const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *query=static_cast<ScopedVariableMonitorQueryV1 *>(context);if(!query)return false;
  __try{query->completed=QueryUnsafe(*query,stamp);return query->completed;}
  __except(EXCEPTION_EXECUTE_HANDLER){if(query->session)Fail(*query->session,nullptr,scoped_chain_failure_memory);return false;}
}

std::string SerializeScopedCharacterVariableMonitorV1(const ScopedCharacterVariableMonitorV1 &session) {
  std::ostringstream out;out<<std::boolalpha;
  auto key=[&](const CombatScopedStableKeyV1 &v){out<<'\"';for(std::uint32_t i=0;i<v.size;++i){const auto c=v.bytes[i];if(c=='\\'||c=='\"')out<<'\\';out<<c;}out<<'\"';};
  auto value=[&](const ScopedVariableValueV1 &v){
    out<<"{\"read\":"<<v.read<<",\"present\":"<<v.present<<",\"expiration_raw\":"<<v.expiration_raw
       <<",\"scope_word0\":"<<v.words[0]<<",\"scope_word1\":"<<v.words[1]
       <<",\"flag_name_read\":"<<v.flag_name_read<<",\"flag_index\":"<<v.flag_index
       <<",\"flag_identifier_epoch\":"<<static_cast<unsigned>(v.flag_identifier_epoch)
       <<",\"flag_identifier_count\":"<<v.flag_identifier_count<<",\"flag_name\":";key(v.flag_name);out<<'}';
  };
  auto commit=[&](const CombatScopedDeathCommitContextV1 &c,bool direct=false){
    out<<"{\"read\":"<<c.read<<",\"context_kind\":\""
       <<(direct?"original_264BCB0_direct_enter_return_arguments":"currently_executing_original_264BCB0_same_thread")<<"\""
       <<",\"managed_daily_sequence_token\":"<<c.managed_daily_sequence_token
       <<",\"invocation\":"<<c.invocation<<",\"parent_invocation\":"<<c.parent_invocation
       <<",\"thread_id\":"<<c.thread_id<<",\"native_date_raw\":"<<c.native_date_raw
       <<",\"combat_id\":"<<c.combat_id<<",\"victim_id\":"<<c.victim_id<<",\"killer_id\":"<<c.killer_id
       <<",\"victim_full_identity_matches\":"<<c.victim_full_identity_matches
       <<",\"killer_full_identity_matches\":"<<c.killer_full_identity_matches
       <<",\"manager_token\":"<<c.manager<<",\"victim_token\":"<<c.victim<<",\"killer_token\":"<<c.killer
       <<",\"reason_token\":"<<c.reason<<",\"date_argument_token\":"<<c.date_argument
       <<",\"requested_death_date_raw\":"<<c.requested_death_date_raw
       <<",\"reason_key_read\":"<<c.reason_key_read<<",\"reason_key\":";key(c.reason_key);
    out<<",\"artifact_token\":"<<c.artifact<<",\"artifact_actual_null\":"<<c.artifact_actual_null
       <<",\"artifact_id_read\":"<<c.artifact_id_read<<",\"artifact_id\":"<<c.artifact_id<<'}';
  };
  auto named=[&](const ScopedNotificationNamedDeadCharacterV1 &n){
    const auto failure=[](ScopedNotificationNamedReadFailureV1 f){switch(f){
      case ScopedNotificationNamedReadFailureV1::none:return "none";
      case ScopedNotificationNamedReadFailureV1::context_extent:return "context_extent";
      case ScopedNotificationNamedReadFailureV1::identifier_table_extent:return "identifier_table_extent";
      case ScopedNotificationNamedReadFailureV1::prearmed_key:return "prearmed_key";
      case ScopedNotificationNamedReadFailureV1::identifier_names_span:return "identifier_names_span";
      case ScopedNotificationNamedReadFailureV1::identifier_count_shrunk:return "identifier_count_shrunk";
      case ScopedNotificationNamedReadFailureV1::identifier_epoch:return "identifier_epoch";
      case ScopedNotificationNamedReadFailureV1::identifier_key_index:return "identifier_key_index";
      case ScopedNotificationNamedReadFailureV1::identifier_key_name:return "identifier_key_name";
      case ScopedNotificationNamedReadFailureV1::store_extent:return "store_extent";
      case ScopedNotificationNamedReadFailureV1::primary_rows:return "primary_rows";
      case ScopedNotificationNamedReadFailureV1::fallback_store_extent:return "fallback_store_extent";
      case ScopedNotificationNamedReadFailureV1::fallback_parent_extent:return "fallback_parent_extent";
      case ScopedNotificationNamedReadFailureV1::fallback_rows:return "fallback_rows";
      case ScopedNotificationNamedReadFailureV1::resolved_character_extent:return "resolved_character_extent";
      case ScopedNotificationNamedReadFailureV1::identifier_header_changed:return "identifier_header_changed";
      case ScopedNotificationNamedReadFailureV1::identifier_key_changed:return "identifier_key_changed";
      case ScopedNotificationNamedReadFailureV1::snapshots_differ:return "snapshots_differ";
      case ScopedNotificationNamedReadFailureV1::observations_unread:return "observations_unread";
      case ScopedNotificationNamedReadFailureV1::access_fault:return "access_fault";
      case ScopedNotificationNamedReadFailureV1::not_observed:return "not_observed";
    }return "unknown_failure_stage";};
    out<<"{\"read\":"<<n.read<<",\"stable_two_reads\":"<<n.stable_two_reads<<",\"present\":"<<n.present
       <<",\"identifier_header_read\":"<<n.identifier_header_read<<",\"identifier_table_token\":"<<n.identifier_table
       <<",\"identifier_data_token\":"<<n.identifier_data<<",\"identifier_count\":"<<n.identifier_count
       <<",\"identifier_epoch\":"<<static_cast<unsigned>(n.identifier_epoch)
       <<",\"prearmed_identifier_count\":"<<n.prearmed_identifier_count
       <<",\"prearmed_identifier_epoch\":"<<static_cast<unsigned>(n.prearmed_identifier_epoch)
       <<",\"identifier_key_index\":"<<n.identifier_key_index
       <<",\"identifier_key_name_matches\":"<<n.identifier_key_name_matches
       <<",\"failure_stage\":\""<<failure(n.failure_stage)<<'"'
       <<",\"execution_context_token\":"<<n.execution_context<<",\"saved_target_store_token\":"<<n.store
       <<",\"key_id\":"<<n.key_id<<",\"primary_data_token\":"<<n.primary_data<<",\"primary_count\":"<<n.primary_count
       <<",\"fallback_pointer_read\":"<<n.fallback_pointer_read<<",\"fallback_parent_token\":"<<n.fallback_parent
       <<",\"fallback_header_read\":"<<n.fallback_header_read<<",\"fallback_data_token\":"<<n.fallback_data
       <<",\"fallback_count\":"<<n.fallback_count<<",\"source_level\":"<<n.source_level
       <<",\"found_row_token\":"<<n.found_row<<",\"found_index\":"<<n.found_index
       <<",\"scope_words_read\":"<<n.scope_words_read<<",\"scope_words\":["<<n.scope_words[0]<<','<<n.scope_words[1]
       <<"],\"kind\":"<<n.kind<<",\"subtype\":"<<n.subtype<<",\"payload\":"<<n.payload
       <<",\"payload_raw64\":"<<n.payload_raw64<<",\"character_full_id_low32_read\":"<<n.character_full_id_low32_read
       <<",\"character_full_id_raw32\":"<<n.character_full_id_raw32
       <<",\"character_id\":"<<n.character_id<<",\"resolved_character_token\":"<<n.resolved_character
       <<",\"character_identity_read\":"<<n.character_identity_read<<",\"observed_character_id\":"<<n.observed_character_id
       <<",\"character_full_identity_matches\":"<<n.character_full_identity_matches
       <<",\"matches_monitored_victim\":"<<n.matches_monitored_victim
       <<",\"missing_padding_is_unknown\":"<<(!n.present)<<'}';
  };
  auto producer=[&](const ScopedVariableEventProducerV1 &p){
    out<<"{\"identity_read\":"<<p.read<<",\"invocation\":"<<p.invocation
       <<",\"actual_original_execution_observed\":"<<(p.read&&p.invocation!=0)
       <<",\"identity_kind\":\"nearest_matched_notification_immediate_ancestor\""
       <<",\"matched_root_execution_depth\":"<<p.matched_root_execution_depth
       <<",\"active_effect_group_depth\":"<<p.active_effect_group_depth
       <<",\"definition_token\":"<<p.definition<<",\"definition_index\":"<<p.definition_index
       <<",\"definition_id\":"<<p.definition_id<<",\"runtime_stats_ordinal\":"<<p.runtime_stats_ordinal
       <<",\"definition_key\":";key(p.definition_key);
    out<<",\"compiled_immediate_root_token\":"<<p.immediate_root
       <<",\"definition_vtable_rva\":"<<p.definition_vtable_rva<<",\"root_vtable_rva\":"<<p.root_vtable_rva
       <<",\"root_hash\":"<<p.root_hash<<",\"original_execute_rva\":"<<p.original_execute_rva
       <<",\"children_data_token\":"<<p.children_data<<",\"children_capacity\":"<<p.children_capacity
       <<",\"children_count\":"<<p.children_count
       <<",\"execution_context_token\":"<<p.context<<",\"root_scope_token\":"<<p.root_scope
        <<",\"root_scope_words\":["<<p.root_scope_words[0]<<','<<p.root_scope_words[1]<<"]"
         <<",\"activation_death_commit_context\":";commit(p.activation_death_commit_context);
     out<<",\"named_dead_character_at_activation\":";named(p.named_dead_character_at_activation);
     out<<",\"named_dead_character_at_observation\":";named(p.named_dead_character_at_observation);out<<'}';
  };
  out<<"{\"schema_version\":1,\"scope\":\"two_full_character_ids_signature_weapon_and_current_house_pair\","
        "\"direct_original_death_commit_schema_version\":1,\"notification_named_dead_character_schema_version\":1,"
       "\"monitor_sequence_token\":"<<session.token<<",\"character_ids\":["<<session.character_ids[0]<<','<<session.character_ids[1]
      <<"],\"begin_date_raw\":"<<session.begin_date<<",\"signature_weapon_key_id\":"<<session.signature_key_id
      <<",\"dead_character_key_id\":"<<session.dead_character_key_id
     <<",\"native_identifier_table_token\":"<<session.identifier_table<<",\"native_identifier_epoch\":"<<static_cast<unsigned>(session.identifier_epoch)
     <<",\"native_identifier_count\":"<<session.identifier_count<<",\"failure_flags\":"<<session.failure_flags.load()
     <<",\"detours_uninstalled\":"<<session.detours_uninstalled<<",\"truncated\":"<<(session.count.load()>session.records.size())
     <<",\"whole_game_mutable_bundle_complete\":false,\"battle_event_causality_inferred_from_endpoint\":false,"
         "\"final_owner_state_reread_from_cached_pointer\":false"
      <<",\"owner_return_compression\":{\"schema_version\":1,\"scope\":\"exact_dead_null_original_returns_only\""
      <<",\"observed\":"<<session.owner_getter_observed.load()
      <<",\"retained\":"<<session.owner_getter_retained.load()
      <<",\"coalesced\":"<<session.owner_getter_coalesced.load()
      <<",\"unchanged_nonnull_unrecorded\":"<<session.owner_nonnull_unchanged_unrecorded.load()
      <<",\"capacity\":128,\"writer_calls_coalesced\":0,\"aggregate_bounds_are_not_per_call_chronology\":true}"
     <<",\"event_producer_definitions_read\":"<<session.event_producer_definitions_read
     <<",\"event_manager_token\":"<<session.event_manager
     <<",\"event_definition_count\":"<<session.event_definitions_count
     <<",\"prearmed_event_definitions\":[";
  for(std::size_t i=0;i<session.event_producer_definitions.size();++i){if(i)out<<',';producer(session.event_producer_definitions[i]);}
  out<<"],\"notification_receiver_inferred_as_victim\":false,\"records\":[";
  const std::array<const char *,9> boundaries{"arm","original_owner_return","variable_write_enter","variable_write_return","house_predicate_enter","house_predicate_return","final_paused","original_death_commit_enter","original_death_commit_return"};
  const auto count=std::min<std::uint32_t>(session.count.load(),static_cast<std::uint32_t>(session.records.size()));
  for(std::uint32_t i=0;i<count;++i){if(i)out<<',';const auto &r=session.records[i];
    if(static_cast<std::size_t>(r.boundary)>=boundaries.size()||r.stack_count>r.stack_rvas.size())return {};
    out<<"{\"sequence\":"<<r.sequence<<",\"invocation\":"<<r.invocation<<",\"boundary\":\""<<boundaries[static_cast<std::size_t>(r.boundary)]
       <<"\",\"failure_flags\":"<<r.failure_flags<<",\"thread_id\":"<<r.thread_id<<",\"date_raw\":"<<r.date_raw
       <<",\"character_id\":"<<r.character_id<<",\"observed_character_id\":"<<r.observed_character_id
       <<",\"full_identity_matches\":"<<r.full_identity_matches<<",\"dead\":"<<r.victim_dead
       <<",\"owner_token\":"<<r.owner<<",\"previous_owner_token\":"<<r.previous_owner<<",\"container_token\":"<<r.container
       <<",\"owner_from_original_getter\":"<<r.owner_from_original_getter<<",\"owner_from_same_setter_invocation\":"<<r.owner_from_same_setter_invocation
        <<",\"key_id\":"<<r.key_id<<",\"duration\":"<<r.duration
        <<",\"owner_observation_first_call_index\":"<<r.owner_observation_first_call_index
        <<",\"owner_observation_last_call_index\":"<<r.owner_observation_last_call_index
        <<",\"owner_observation_count\":"<<r.owner_observation_count
        <<",\"owner_state_epoch\":"<<r.owner_state_epoch
        <<",\"owner_activity_epoch\":"<<r.owner_activity_epoch<<",\"value\":";
    value(r.value);out<<",\"requested_value_decoding\":";value(r.requested_value_decoding);
    out<<",\"requested_scope_words\":["<<r.requested_value[0]<<','<<r.requested_value[1]<<']'
       <<",\"setter_node_token\":"<<r.setter_node<<",\"setter_node_vtable_rva\":"<<r.setter_node_vtable_rva<<",\"setter_node_hash\":"<<r.setter_node_hash
       <<",\"execution_context_token\":"<<r.execution_context<<",\"native_root_scope_token\":"<<r.native_root_scope
       <<",\"native_scope_words\":["<<r.native_scope_words[0]<<','<<r.native_scope_words[1]<<"],\"caller_token\":"<<r.caller<<",\"native_stack_rvas\":[";
    for(std::uint32_t j=0;j<r.stack_count;++j){if(j)out<<',';out<<r.stack_rvas[j];}
    out<<"],\"house_ids\":["<<r.house_ids[0]<<','<<r.house_ids[1]<<"],\"relation_type_token\":"<<r.relation_type
       <<",\"relation_type_id\":"<<r.relation_type_id<<",\"relation_type_key\":\"";
    for(std::uint32_t j=0;j<r.relation_type_key.size;++j){const char c=r.relation_type_key.bytes[j];if(c=='\\'||c=='\"')out<<'\\';out<<c;}
    out<<'\"'<<",\"event_producer\":";producer(r.event_producer);
    out<<",\"current_death_commit_context\":";commit(r.current_death_commit_context);
    out<<",\"original_death_commit_context\":";commit(r.original_death_commit_context,true);
    out
       <<",\"original_boolean_read\":"<<r.original_boolean_read<<",\"original_boolean\":"<<r.original_boolean
       <<",\"original_return_bits\":"<<r.original_return_bits
       <<",\"daily_effect_context\":{\"read\":"<<r.daily_effect_context.read
       <<",\"managed_daily_sequence_token\":"<<r.daily_effect_context.managed_daily_sequence_token
       <<",\"invocation\":"<<r.daily_effect_context.invocation<<",\"node_token\":"<<r.daily_effect_context.node
       <<",\"node_vtable_rva\":"<<r.daily_effect_context.node_vtable_rva<<",\"node_hash\":"<<r.daily_effect_context.node_hash
       <<",\"execution_context_token\":"<<r.daily_effect_context.execution_context
       <<",\"depth\":"<<r.daily_effect_context.depth<<",\"combat_id\":"<<r.daily_effect_context.combat_id
       <<",\"side_index\":"<<r.daily_effect_context.side_index<<",\"event_load_index\":"<<r.daily_effect_context.event_load_index<<"}}";
  }
  out<<"]}";return out.str();
}

extern "C" void * __fastcall ObservedCharacterVariableOwnerV1(const void *a) noexcept {
  EnterScopedObserverCallbackV1();
  const auto caller=reinterpret_cast<std::uintptr_t>(_ReturnAddress());
  __try { return ObservedCharacterVariableOwnerV1Impl(a,caller); }
  __finally { LeaveScopedObserverCallbackV1(); }
}

extern "C" std::uintptr_t __fastcall ObservedCharacterVariableEffectV1(void *a,void *b) noexcept {
  EnterScopedObserverCallbackV1();
  __try { return ObservedCharacterVariableEffectV1Impl(a,b); }
  __finally { LeaveScopedObserverCallbackV1(); }
}

extern "C" std::uintptr_t __fastcall ObservedCharacterVariableSetterV1(void *a,std::int32_t b,const void *c,std::int32_t d) noexcept {
  EnterScopedObserverCallbackV1();
  __try { return ObservedCharacterVariableSetterV1Impl(a,b,c,d, reinterpret_cast<std::uintptr_t>(_ReturnAddress())); }
  __finally { LeaveScopedObserverCallbackV1(); }
}

extern "C" std::uintptr_t __fastcall ObservedScopedHousePredicateV1(void *a,void *b,void *c) noexcept {
  EnterScopedObserverCallbackV1();
  __try { return ObservedScopedHousePredicateV1Impl(a,b,c, reinterpret_cast<std::uintptr_t>(_ReturnAddress())); }
  __finally { LeaveScopedObserverCallbackV1(); }
}

bool StartScopedCharacterVariableMonitorV1(ScopedCharacterVariableMonitorV1 &a,const Bindings &b,std::uintptr_t c,std::array<std::int32_t,2> d,std::uint64_t e,bool f,bool g,std::uintptr_t h,std::uintptr_t i,std::uintptr_t j) noexcept {
  if (!TryEnterScopedObserverMutationV1()) return false;
  __try { return StartScopedCharacterVariableMonitorV1Impl(a,b,c,d,e,f,g,h,i,j); }
  __finally { LeaveScopedObserverMutationV1(); }
}

bool FinishScopedCharacterVariableMonitorV1(ScopedCharacterVariableMonitorV1 &a,bool b) noexcept {
  if (!TryEnterScopedObserverMutationV1()) return false;
  __try { return FinishScopedCharacterVariableMonitorV1Impl(a,b); }
  __finally { LeaveScopedObserverMutationV1(); }
}

} // namespace xar::ck3_11906
