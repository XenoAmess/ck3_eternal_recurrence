#include "xar_bridge/combat_scoped_transition_chain_v1.hpp"
#include "xar_bridge/scoped_observer_lifetime_v1.hpp"

#include <windows.h>
#include <intrin.h>

#include <algorithm>
#include <cstring>
#include <limits>

namespace xar::ck3_11906 {
namespace {

std::atomic<CombatScopedChainV1 *> g_chain{nullptr};
thread_local std::uint32_t g_effect_invocation = 0;
thread_local std::uint32_t g_death_request_invocation = 0;
thread_local CombatScopedDeathCommitContextV1 g_death_commit_context{};
using DeathOriginal = void (*)(void *, void *, void *, void *, void *, void *);
using QueueOriginal = std::uintptr_t (*)(void *, const void *);
using CasualtyOriginal = std::uintptr_t (*)(void *, std::int64_t, void *);
std::atomic<DeathOriginal> g_death_request{nullptr};
std::atomic<DeathOriginal> g_death_commit{nullptr};
std::atomic<QueueOriginal> g_death_enqueue{nullptr};
std::atomic<CasualtyOriginal> g_casualty{nullptr};
std::atomic<CombatScopedMaterializerOriginalV1> g_materializer{nullptr};
std::atomic<CombatScopedFilterOriginalV1> g_filter{nullptr};
std::atomic<CombatScopedPredicateOriginalV1> g_predicate{nullptr};
std::atomic<CombatScopedListWriterOriginalV1> g_list_writer{nullptr};
bool g_selector_offline_fixture=false;
struct SelectorFilterContext {
  std::uintptr_t vector=0,context=0,source=0,shared=0;
  std::int32_t prefix=-1;
  std::uint32_t invocation=0;
};
thread_local SelectorFilterContext g_filter_context{};
struct ListOwnerContext {
  std::uint32_t effect_invocation=0;
  std::uintptr_t owner=0,scope=0;
  std::array<std::uint64_t,2> words{};
};
thread_local ListOwnerContext g_list_owner{};

template <typename T>
T Read(std::uintptr_t base, std::size_t offset = 0) noexcept {
  T value{};
  std::memcpy(&value, reinterpret_cast<const void *>(base + offset), sizeof(T));
  return value;
}

bool ReadStableKey(std::uintptr_t object, CombatScopedStableKeyV1 &out) noexcept {
  const auto size = Read<std::uint64_t>(object, 0x10);
  const auto capacity = Read<std::uint64_t>(object, 0x18);
  if (size == 0 || size >= out.bytes.size() || capacity < size ||
      (capacity < 16 && capacity != 15)) return false;
  const auto data = capacity >= 16 ? Read<std::uintptr_t>(object) : object;
  if (data == 0) return false;
  for (std::uint64_t i = 0; i < size; ++i) {
    const auto character = Read<char>(data, static_cast<std::size_t>(i));
    if (character <= 0x20 || character == '"' || character == '\\') return false;
    out.bytes[static_cast<std::size_t>(i)] = character;
  }
  if (Read<char>(data, static_cast<std::size_t>(size)) != '\0') return false;
  out.size = static_cast<std::uint32_t>(size);
  return true;
}

bool ReadTraitDefinitions(CombatScopedChainV1 &chain, std::uintptr_t database) noexcept {
  if (database == 0) return false;
  const auto data = Read<std::uintptr_t>(database, 0x68);
  const auto count = Read<std::int32_t>(database, 0x74);
  if (data == 0 || count <= 0 || count >
      static_cast<std::int32_t>(chain.trait_definitions.size())) return false;
  for (std::int32_t i = 0; i < count; ++i) {
    const auto definition = Read<std::uintptr_t>(data, static_cast<std::size_t>(i) * 8);
    auto &out = chain.trait_definitions[static_cast<std::size_t>(i)];
    if (definition == 0) return false;
    out.trait_id = Read<std::int32_t>(definition, 0x10);
    if (out.trait_id < 0 || !ReadStableKey(definition + 0x18, out.key)) return false;
    out.track_count = Read<std::int32_t>(definition, 0x294);
    if (out.track_count < 0 || out.track_count >
        static_cast<std::int32_t>(kCombatScopedChainMaxTraitTracksV1)) return false;
  }
  std::sort(chain.trait_definitions.begin(), chain.trait_definitions.begin() + count,
            [](const auto &left, const auto &right) { return left.trait_id < right.trait_id; });
  for (std::int32_t i = 1; i < count; ++i) {
    if (chain.trait_definitions[i - 1].trait_id == chain.trait_definitions[i].trait_id) return false;
  }
  chain.trait_definition_count = static_cast<std::uint32_t>(count);
  return true;
}

const CombatPhaseEventTraceObjectRefV1 *FindRegiment(
    const CombatPhaseEventTraceCapturePlanV1 &plan, std::int32_t id) noexcept {
  const auto end = plan.regiments.begin() + plan.regiment_count;
  const auto found = std::lower_bound(
      plan.regiments.begin(), end, id,
      [](const auto &row, std::int32_t full_id) { return row.full_id < full_id; });
  return found != end && found->full_id == id ? &*found : nullptr;
}

void Failure(CombatScopedChainV1 &chain, CombatScopedChainRecordV1 &row,
             std::uint32_t flag) noexcept {
  row.failure_flags |= flag;
  chain.failure_flags.fetch_or(flag, std::memory_order_acq_rel);
}

bool ReadEffectIdentity(const CombatScopedChainV1 &chain,std::uintptr_t node,
                        CombatScopedEffectIdentityV1 &identity) noexcept {
  identity.node=node;
  if(node==0 || chain.plan==nullptr)return false;
  const auto base=chain.plan->module_base;
  const auto vtable=Read<std::uintptr_t>(node);
  if(vtable<base || vtable-base>=0x6000000)return false;
  const auto execute=Read<std::uintptr_t>(vtable,0xB0);
  if(execute<base || execute-base>=0x6000000)return false;
  identity.vtable_rva=static_cast<std::uint32_t>(vtable-base);
  identity.hash=Read<std::uint32_t>(node,0x38);
  identity.original_execute_rva=static_cast<std::uint32_t>(execute-base);
  identity.read=true;
  return true;
}

void ReadEffectBranchLayout(CombatScopedChainV1 &chain,CombatScopedChainRecordV1 &row) noexcept {
  // Exact original 3380EC0 child loop and 33884B0 CIf full CFG. A scripted
  // wrapper or random-list type is not inferred to share this layout.
  const bool conditional=row.node_vtable_rva==0x44D1E18;
  if(!conditional && row.node_vtable_rva!=0x44CF030 && row.node_vtable_rva!=0x4478388)return;
  CombatScopedEffectIdentityV1 identity{};
  if(!ReadEffectIdentity(chain,row.node_identity,identity) ||
     identity.original_execute_rva!=(conditional?0x33884B0U:0x3380EC0U)) {
    Failure(chain,row,scoped_chain_failure_binding);return;
  }
  row.node_original_execute_rva=identity.original_execute_rva;
  row.effect_children_data=Read<std::uintptr_t>(row.node_identity,0x40);
  row.effect_child_count_raw=Read<std::int32_t>(row.node_identity,0x4C);
  if(row.effect_child_count_raw<0 || (row.effect_child_count_raw!=0&&row.effect_children_data==0)) {
    Failure(chain,row,scoped_chain_failure_container);return;
  }
  if(row.effect_child_count_raw>static_cast<std::int32_t>(row.effect_children.size())) {
    Failure(chain,row,scoped_chain_failure_capacity);return;
  }
  for(std::int32_t i=0;i<row.effect_child_count_raw;++i){
    const auto child=Read<std::uintptr_t>(row.effect_children_data,static_cast<std::size_t>(i)*8);
    if(!ReadEffectIdentity(chain,child,row.effect_children[static_cast<std::size_t>(i)])) {
      Failure(chain,row,scoped_chain_failure_binding);return;
    }
    ++row.effect_child_identity_count;
  }
  row.effect_children_read=true;
  if(conditional){
    row.effect_if_optional_node=Read<std::uintptr_t>(row.node_identity,0x258);
    if(row.effect_if_optional_node!=0 &&
       !ReadEffectIdentity(chain,row.effect_if_optional_node,row.effect_if_optional_identity)) {
      Failure(chain,row,scoped_chain_failure_binding);return;
    }
    row.effect_if_optional_read=true;
  }
}

bool ReadCharacter(CombatScopedChainV1 &chain, std::size_t index,
                   CombatScopedChainRecordV1 &record) noexcept {
  auto &out = record.characters[index];
  out.character_id = chain.character_ids[index];
  const auto object = chain.character_objects[index];
  out.observed_character_id = Read<std::int32_t>(object, 0x18);
  out.identity_matches = out.observed_character_id == out.character_id;
  if (!out.identity_matches) {
    Failure(chain, record, scoped_chain_failure_identity);
    return false;
  }
  out.martial = Read<std::int32_t>(object, 0xD8);
  out.learning = Read<std::int32_t>(object, 0xE4);
  out.prowess = Read<std::int32_t>(object, 0xE8);
  const auto extension = Read<std::uintptr_t>(object, 0x1A8);
  out.prestige_currency_raw = extension != 0 ? Read<std::int64_t>(extension, 0x130) : 0;
  out.prestige_experience_raw = extension != 0 ? Read<std::int64_t>(extension, 0x138) : 0;
  out.prestige_read = true;
  out.regiment_link = Read<std::uintptr_t>(object, 0x1B0);
  if (out.regiment_link != 0) {
    out.current_regiment_id = Read<std::int32_t>(out.regiment_link, 0xF8);
  }
  if (out.current_regiment_id == -1) {
    out.current_regiment_identity_matches = true;
    out.current_regiment_back_reference_matches = true;
  } else {
    const auto *regiment = FindRegiment(*chain.plan, out.current_regiment_id);
    out.current_regiment_identity_matches = regiment != nullptr &&
        Read<std::int32_t>(regiment->object, 0x10) == out.current_regiment_id;
    if (!out.current_regiment_identity_matches) {
      Failure(chain, record, scoped_chain_failure_identity);
      return false;
    }
    out.current_regiment_back_reference_matches =
        Read<std::int32_t>(regiment->object, 0x148) == out.character_id;
  }
  const auto death = Read<std::uintptr_t>(object, 0x1C8);
  out.death_marker_present = death != 0;
  if (death != 0) {
    // Exact 1.19.0.6 CDeathData writes at 264BF85 / 2609370,7B,85.
    out.death_date_raw = Read<std::int64_t>(death, 0x04);
    out.death_reason = Read<std::uintptr_t>(death, 0x10);
    out.death_killer_character_id = Read<std::int32_t>(death, 0x18);
    out.death_artifact_id = Read<std::int32_t>(death, 0x1C);
    out.death_details_read = out.death_reason != 0 &&
        ReadStableKey(out.death_reason + 0x18, out.death_reason_key);
    if (out.death_reason != 0 && !out.death_details_read) {
      Failure(chain, record, scoped_chain_failure_container);
      return false;
    }
  }
  // Exact traits materializer 198B560 reads character+F0, +FC; stride4.
  // Capacity is deliberately not inferred from an adjacent unanchored field.
  const auto traits = Read<std::uintptr_t>(object, 0xF0);
  const auto trait_count = Read<std::int32_t>(object, 0xFC);
  if (trait_count < 0 || trait_count > static_cast<std::int32_t>(out.trait_ids.size()) ||
      (trait_count != 0 && traits == 0)) {
    Failure(chain, record, trait_count > static_cast<std::int32_t>(out.trait_ids.size())
                               ? scoped_chain_failure_capacity
                               : scoped_chain_failure_container);
    return false;
  }
  for (std::int32_t i = 0; i < trait_count; ++i) {
    const auto id = Read<std::int32_t>(traits, static_cast<std::size_t>(i) * 4);
    const auto end = chain.trait_definitions.begin() + chain.trait_definition_count;
    const auto definition = std::lower_bound(chain.trait_definitions.begin(), end, id,
        [](const auto &row, std::int32_t trait_id) { return row.trait_id < trait_id; });
    if (definition == end || definition->trait_id != id) {
      Failure(chain, record, scoped_chain_failure_identity);
      return false;
    }
    out.trait_ids[static_cast<std::size_t>(i)] = id;
  }
  out.trait_count = static_cast<std::uint32_t>(trait_count);
  out.traits_read = true;
  // 260F640 reads the complete character track raw vector, distinct from the
  // prestige extension's +138 experience scalar. No track key is guessed.
  const auto tracks=Read<std::uintptr_t>(object,0x138);
  const auto track_count=Read<std::int32_t>(object,0x144);
  if(track_count<0||track_count>static_cast<std::int32_t>(out.trait_track_raw_values.size())||
     (track_count!=0&&tracks==0)) {Failure(chain,record,scoped_chain_failure_container);return false;}
  out.trait_track_raw_count=static_cast<std::uint32_t>(track_count);
  for(std::int32_t i=0;i<track_count;++i)out.trait_track_raw_values[i]=Read<std::int64_t>(tracks,i*8);
  out.trait_tracks_read=true;
  // 2609210 inserts the full victim ID into the original killer's sorted list:
  // live extension+E0, or death_data+40 when that killer is already dead.
  const auto kills=death!=0?death+0x40:extension!=0?extension+0xE0:0;
  if(kills!=0){const auto data=Read<std::uintptr_t>(kills);const auto cap=Read<std::int32_t>(kills,8);
    const auto n=Read<std::int32_t>(kills,12);
    if(n<0||cap<n||n>static_cast<std::int32_t>(out.kill_character_ids.size())||(n!=0&&data==0)) {
      Failure(chain,record,scoped_chain_failure_container);return false;}
    out.kill_count=static_cast<std::uint32_t>(n);
    for(std::int32_t i=0;i<n;++i)out.kill_character_ids[i]=Read<std::int32_t>(data,i*4);
    out.kills_read=true;
  }
  return true;
}

bool ReadCombatEntries(CombatScopedChainV1 &chain,
                       CombatScopedChainRecordV1 &record) noexcept {
  const auto index = chain.entry_snapshot_count.fetch_add(1);
  if (index >= chain.entry_snapshots.size()) {
    Failure(chain, record, scoped_chain_failure_capacity);
    return false;
  }
  record.entry_snapshot_index = static_cast<std::int32_t>(index);
  auto &snapshot = chain.entry_snapshots[index];
  for (std::size_t side_index = 0; side_index < 2; ++side_index) {
    const auto side = chain.plan->sides[side_index];
    if (Read<std::uintptr_t>(side, 0xB8) != chain.plan->combat) {
      Failure(chain, record, scoped_chain_failure_identity);
      return false;
    }
    record.side_cache_raw[side_index] = Read<std::int64_t>(side, 0x98);
    record.side_first_bucket_cache_raw[side_index] = Read<std::int64_t>(side, 0xA0);
    for (std::uint32_t bucket = 0; bucket < 2; ++bucket) {
      const auto header = side + (bucket == 0 ? 0x28 : 0x40);
      const auto entries = Read<std::uintptr_t>(header);
      const auto capacity = Read<std::int32_t>(header, 8);
      const auto count = Read<std::int32_t>(header, 12);
      if (capacity < 0 || count < 0 || count > capacity ||
          static_cast<std::uint32_t>(count) >
              kCombatScopedChainMaxEntriesV1 - snapshot.entry_count[side_index] ||
          (count != 0 && entries == 0)) {
        Failure(chain, record, scoped_chain_failure_container);
        return false;
      }
      for (std::int32_t i = 0; i < count; ++i) {
        const auto native = entries + static_cast<std::size_t>(i) * 0x60;
        auto &out = snapshot.entries[side_index][snapshot.entry_count[side_index]];
        out.regiment_id = Read<std::int32_t>(native, 8);
        const auto *regiment = FindRegiment(*chain.plan, out.regiment_id);
        if (regiment == nullptr ||
            Read<std::int32_t>(regiment->object, 0x10) != out.regiment_id) {
          Failure(chain, record, scoped_chain_failure_identity);
          return false;
        }
        out.army_id = Read<std::int32_t>(regiment->object, 0x140);
        out.character_id = Read<std::int32_t>(regiment->object, 0x148);
        out.bucket = bucket;
        out.starting_raw = Read<std::int64_t>(native, 0x10);
        out.current_raw = Read<std::int64_t>(native, 0x18);
        out.soft_raw = Read<std::int64_t>(native, 0x20);
        out.effective_damage_raw = Read<std::int64_t>(native, 0x40);
        out.effective_toughness_raw = Read<std::int64_t>(native, 0x48);
        for (std::size_t who = 0; who < 2; ++who) {
          if (out.regiment_id == chain.prearmed_regiment_ids[who]) {
            record.scoped_regiment_in_side[who] = true;
          }
        }
        ++snapshot.entry_count[side_index];
      }
    }
    const auto header = side + 0x58;
    const auto owners = Read<std::uintptr_t>(header);
    const auto capacity = Read<std::int32_t>(header, 8);
    const auto count = Read<std::int32_t>(header, 12);
    if (capacity < 0 || count < 0 || count > capacity ||
        static_cast<std::size_t>(count) > snapshot.owner_hard[side_index].size() ||
        (count != 0 && owners == 0)) {
      Failure(chain, record, scoped_chain_failure_container);
      return false;
    }
    for (std::int32_t i = 0; i < count; ++i) {
      const auto native = owners + static_cast<std::size_t>(i) * 0x18;
      snapshot.owner_hard[side_index][i] =
          {Read<std::int32_t>(native, 8), Read<std::int64_t>(native, 0x10)};
    }
    snapshot.owner_hard_count[side_index] = static_cast<std::uint32_t>(count);
  }
  record.combat_entries_read = true;
  return true;
}

bool ReadBattleEventLedger(CombatScopedChainV1 &chain,CombatScopedChainRecordV1 &r) noexcept {
  const auto &p=*chain.plan;
  if(!p.battle_result||Read<std::int32_t>(p.combat,0x708)!=p.battle_result_id||Read<std::int32_t>(p.battle_result,8)!=p.battle_result_id){Failure(chain,r,scoped_chain_failure_identity);return false;}
  const auto index=chain.battle_event_snapshot_count.fetch_add(1);
  if(index>=chain.battle_event_snapshots.size()){Failure(chain,r,scoped_chain_failure_capacity);return false;}
  auto &snapshot=chain.battle_event_snapshots[index];r.battle_event_snapshot_index=static_cast<std::int32_t>(index);
  const auto data=Read<std::uintptr_t>(p.battle_result,0x188);const auto cap=Read<std::int32_t>(p.battle_result,0x190);const auto n=Read<std::int32_t>(p.battle_result,0x194);
  if(n<0||cap<n||n>static_cast<std::int32_t>(snapshot.rows.size())||(n!=0&&!data)){Failure(chain,r,scoped_chain_failure_container);return false;}
  snapshot.count=static_cast<std::uint32_t>(n);
  for(std::int32_t i=0;i<n;++i){const auto item=data+i*0x38;auto &row=snapshot.rows[i];
    if(Read<std::uintptr_t>(item)!=p.expected_battle_event_vtable){Failure(chain,r,scoped_chain_failure_identity);return false;}
    row.left_character_id=Read<std::int32_t>(item,8);row.right_character_id=Read<std::int32_t>(item,12);row.type_raw=Read<std::int32_t>(item,0x30);
    row.side_index=Read<std::uint8_t>(item,0x34)!=0?0:1;row.target_right=Read<std::uint8_t>(item,0x35)!=0;
    CombatScopedStableKeyV1 key{};
    if(!ReadStableKey(item+0x10,key)||key.size>=row.stable_key.size()){Failure(chain,r,scoped_chain_failure_container);return false;}
    row.stable_key_size=static_cast<std::uint16_t>(key.size);std::memcpy(row.stable_key.data(),key.bytes.data(),key.size);
  }
  r.battle_events_read=true;return true;
}
CombatScopedChainRecordV1 *Capture(
    CombatScopedChainBoundaryV1 boundary, std::uint32_t invocation = 0,
    std::uint32_t parent = 0, std::int32_t side = -1, std::int32_t event = -1,
    void *node = nullptr, std::uint32_t depth = 0, bool entries = false) noexcept {
  auto *const chain = g_chain.load(std::memory_order_acquire);
  if (chain == nullptr || chain->armed.load(std::memory_order_acquire) == 0) return nullptr;
  chain->active_readers.fetch_add(1, std::memory_order_acq_rel);
  const auto index = chain->count.fetch_add(1, std::memory_order_acq_rel);
  if (index >= chain->records.size()) {
    chain->failure_flags.fetch_or(scoped_chain_failure_capacity, std::memory_order_acq_rel);
    chain->active_readers.fetch_sub(1, std::memory_order_acq_rel);
    return nullptr;
  }
  auto &record = chain->records[index];
  record.sequence = index;
  record.invocation = invocation;
  record.parent_invocation = parent;
  record.boundary = boundary;
  record.thread_id = GetCurrentThreadId();
  record.side_index = side;
  record.native_event_load_index = event;
  record.depth = depth;
  record.node_identity = reinterpret_cast<std::uintptr_t>(node);
#if defined(_MSC_VER)
  __try {
#endif
    const auto date = Read<std::uintptr_t>(chain->plan->current_date_slot);
    if (date != chain->plan->expected_current_date_object ||
        Read<std::int32_t>(chain->plan->combat, 8) != chain->plan->combat_id) {
      Failure(*chain, record, scoped_chain_failure_identity);
    } else {
      record.native_date_raw = Read<std::int32_t>(date, 8);
      record.combat_id = chain->plan->combat_id;
      record.phase_day = Read<std::int32_t>(chain->plan->combat, 0x6B4);
      if (record.native_date_raw != chain->before_date_raw &&
          record.native_date_raw != chain->before_date_raw + 24) {
        Failure(*chain, record, scoped_chain_failure_thread_or_date);
      }
      if (node != nullptr) {
        const auto vtable = Read<std::uintptr_t>(record.node_identity);
        if (vtable >= chain->plan->module_base &&
            vtable - chain->plan->module_base < 0x6000000) {
          record.node_vtable_rva = static_cast<std::uint32_t>(vtable - chain->plan->module_base);
        }
        record.node_hash = Read<std::uint32_t>(record.node_identity, 0x38);
        if(boundary==CombatScopedChainBoundaryV1::effect_enter ||
           boundary==CombatScopedChainBoundaryV1::effect_return)
          ReadEffectBranchLayout(*chain,record);
      }
      (void)ReadCharacter(*chain, 0, record);
      (void)ReadCharacter(*chain, 1, record);
      if(record.node_vtable_rva==0x444F498&&(boundary==CombatScopedChainBoundaryV1::effect_enter||boundary==CombatScopedChainBoundaryV1::effect_return))
        (void)ReadBattleEventLedger(*chain,record);
      if (entries) (void)ReadCombatEntries(*chain, record);
    }
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    Failure(*chain, record, scoped_chain_failure_memory);
  }
#endif
  chain->active_readers.fetch_sub(1, std::memory_order_acq_rel);
  return &record;
}

bool ScopedVictim(void *victim) noexcept {
  auto *const chain = g_chain.load(std::memory_order_acquire);
  return chain != nullptr && chain->armed.load(std::memory_order_acquire) != 0 &&
      (reinterpret_cast<std::uintptr_t>(victim) == chain->character_objects[0] ||
       reinterpret_cast<std::uintptr_t>(victim) == chain->character_objects[1]);
}

void DeathArguments(CombatScopedChainRecordV1 *row, void *victim, void *reason,
                    void *date, void *killer, void *queue = nullptr,void *artifact = nullptr) noexcept {
  if (row == nullptr) return;
  auto *const chain = g_chain.load(std::memory_order_acquire);
  if (chain == nullptr) return;
#if defined(_MSC_VER)
  __try {
#endif
    row->death_victim_id = Read<std::int32_t>(reinterpret_cast<std::uintptr_t>(victim), 0x18);
    row->death_killer_id = killer != nullptr
        ? Read<std::int32_t>(reinterpret_cast<std::uintptr_t>(killer), 0x18) : -1;
    row->requested_death_artifact=reinterpret_cast<std::uintptr_t>(artifact);
    if(artifact!=nullptr){row->requested_death_artifact_id=Read<std::int32_t>(row->requested_death_artifact,0x10);row->requested_artifact_id_read=true;}
    row->requested_death_reason = reinterpret_cast<std::uintptr_t>(reason);
    row->requested_death_date_raw = Read<std::int64_t>(reinterpret_cast<std::uintptr_t>(date));
    if (queue != nullptr) {
      row->death_queue = reinterpret_cast<std::uintptr_t>(queue);
      row->death_queue_count = Read<std::int32_t>(row->death_queue, 0xC);
    }
    if (row->death_victim_id != chain->character_ids[0] &&
        row->death_victim_id != chain->character_ids[1]) {
      Failure(*chain, *row, scoped_chain_failure_identity);
    }
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    Failure(*chain, *row, scoped_chain_failure_memory);
  }
#endif
}

void DeathCommitContext(CombatScopedChainV1 &chain, CombatScopedChainRecordV1 *row,
    void *manager, void *victim, void *reason, void *date, void *killer, void *artifact) noexcept {
  if (row==nullptr || row->failure_flags!=0 || chain.plan==nullptr) return;
  __try {
    CombatScopedDeathCommitContextV1 context{};
    context.managed_daily_sequence_token=chain.plan->managed_daily_sequence_token;
    context.invocation=row->invocation;context.parent_invocation=row->parent_invocation;
    context.thread_id=row->thread_id;context.native_date_raw=row->native_date_raw;
    context.combat_id=row->combat_id;context.victim_id=row->death_victim_id;
    context.killer_id=row->death_killer_id;
    context.manager=reinterpret_cast<std::uintptr_t>(manager);
    context.victim=reinterpret_cast<std::uintptr_t>(victim);
    context.killer=reinterpret_cast<std::uintptr_t>(killer);
    context.reason=reinterpret_cast<std::uintptr_t>(reason);
    context.date_argument=reinterpret_cast<std::uintptr_t>(date);
    context.artifact=reinterpret_cast<std::uintptr_t>(artifact);
    context.requested_death_date_raw=row->requested_death_date_raw;
    context.artifact_actual_null=artifact==nullptr;
    context.artifact_id_read=row->requested_artifact_id_read;
    context.artifact_id=row->requested_death_artifact_id;
    for(std::uint32_t i=0;i<chain.plan->character_count;++i){const auto &p=chain.plan->characters[i];
      if(p.object==context.victim && p.full_id==context.victim_id &&
         Read<std::int32_t>(p.object,0x18)==p.full_id) context.victim_full_identity_matches=true;
      if(p.object==context.killer && p.full_id==context.killer_id &&
         Read<std::int32_t>(p.object,0x18)==p.full_id) context.killer_full_identity_matches=true;
    }
    // An actual null killer is separately represented; it is not a failed read.
    if(killer==nullptr)context.killer_full_identity_matches=context.killer_id==-1;
    if(!context.victim_full_identity_matches || !context.killer_full_identity_matches){
      Failure(chain,*row,scoped_chain_failure_identity);return;
    }
    if(reason!=nullptr)context.reason_key_read=ReadStableKey(context.reason+0x18,context.reason_key);
    if(reason!=nullptr && !context.reason_key_read){Failure(chain,*row,scoped_chain_failure_container);return;}
    context.read=true;g_death_commit_context=context;
  } __except(EXCEPTION_EXECUTE_HANDLER){Failure(chain,*row,scoped_chain_failure_memory);}
}

} // namespace

extern "C" void __fastcall ScopedDeathRequestImpl(
    void *manager, void *victim, void *reason, void *date, void *killer, void *artifact) noexcept {
  const auto original = g_death_request.load(std::memory_order_acquire);
  if (original == nullptr) return;
  const bool scoped = ScopedVictim(victim);
  auto *const chain = g_chain.load(std::memory_order_acquire);
  const auto invocation = scoped ? chain->next_invocation.fetch_add(1) + 1 : 0;
  const auto previous = g_death_request_invocation;
  if (scoped) {
    auto *row = Capture(CombatScopedChainBoundaryV1::death_request_enter,
                        invocation, g_effect_invocation);
    DeathArguments(row, victim, reason, date, killer,
                   static_cast<std::byte *>(manager) + 0x4E08,artifact);
    g_death_request_invocation = invocation;
  }
  original(manager, victim, reason, date, killer, artifact);
  if (scoped) {
    auto *row = Capture(CombatScopedChainBoundaryV1::death_request_return,
                        invocation, g_effect_invocation);
    DeathArguments(row, victim, reason, date, killer,
                   static_cast<std::byte *>(manager) + 0x4E08,artifact);
  }
  g_death_request_invocation = previous;
}

extern "C" void __fastcall ScopedDeathCommitImpl(
    void *manager, void *victim, void *reason, void *date, void *killer, void *artifact) noexcept {
  const auto original = g_death_commit.load(std::memory_order_acquire);
  if (original == nullptr) return;
  const bool scoped = ScopedVictim(victim);
  auto *const chain = g_chain.load(std::memory_order_acquire);
  const auto invocation = scoped ? chain->next_invocation.fetch_add(1) + 1 : 0;
  const auto previous=g_death_commit_context;
  // Every nested death is a causal boundary. Unrelated deaths must not borrow
  // the outer scoped victim's tuple while forwarding their original call.
  g_death_commit_context={};
  if (scoped) {
    auto *row = Capture(CombatScopedChainBoundaryV1::death_commit_enter,
                        invocation, g_death_request_invocation);
    DeathArguments(row, victim, reason, date, killer,nullptr,artifact);
    DeathCommitContext(*chain,row,manager,victim,reason,date,killer,artifact);
  }
  __try {
    original(manager, victim, reason, date, killer, artifact);
    if (scoped) {
      auto *row = Capture(CombatScopedChainBoundaryV1::death_commit_return,
                           invocation, g_death_request_invocation, -1, -1, nullptr, 0, true);
      DeathArguments(row, victim, reason, date, killer,nullptr,artifact);
    }
  } __finally {g_death_commit_context=previous;}
}

extern "C" std::uintptr_t __fastcall ScopedDeathEnqueueImpl(void *queue, const void *command) noexcept {
  const auto original = g_death_enqueue.load(std::memory_order_acquire);
  if (original == nullptr) return 0;
  void *victim = nullptr;
  void *reason = nullptr;
  void *killer = nullptr;
  void *artifact = nullptr;
  bool scoped = false;
#if defined(_MSC_VER)
  __try {
#endif
    if (command != nullptr) {
      const auto native = reinterpret_cast<std::uintptr_t>(command);
      victim = Read<void *>(native, 8);
      reason = Read<void *>(native, 0x10);
      killer = Read<void *>(native, 0x20);
      artifact = Read<void *>(native,0x28);
      scoped = ScopedVictim(victim);
    }
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { scoped = false; }
#endif
  auto *const chain = g_chain.load(std::memory_order_acquire);
  const auto invocation = scoped ? chain->next_invocation.fetch_add(1) + 1 : 0;
  const auto date = command != nullptr
      ? const_cast<std::byte *>(static_cast<const std::byte *>(command)) + 0x18 : nullptr;
  if (scoped) {
    auto *row = Capture(CombatScopedChainBoundaryV1::death_enqueue_enter,
                        invocation, g_death_request_invocation);
    DeathArguments(row, victim, reason, date, killer, queue,artifact);
  }
  const auto result = original(queue, command);
  if (scoped) {
    auto *row = Capture(CombatScopedChainBoundaryV1::death_enqueue_return,
                        invocation, g_death_request_invocation);
    DeathArguments(row, victim, reason, date, killer, queue,artifact);
  }
  return result;
}

extern "C" std::uintptr_t __fastcall ScopedCasualtyImpl(
    void *side, std::int64_t damage, void *opposite, std::uintptr_t native_caller) noexcept {
  const auto original = g_casualty.load(std::memory_order_acquire);
  if (original == nullptr) return 0;
  auto *const chain = g_chain.load(std::memory_order_acquire);
  const auto side_address = reinterpret_cast<std::uintptr_t>(side);
  const std::int32_t side_index = chain != nullptr && chain->armed.load() != 0
      ? (side_address == chain->plan->sides[0] ? 0
         : side_address == chain->plan->sides[1] ? 1 : -1) : -1;
  const bool scoped = side_index >= 0 && reinterpret_cast<std::uintptr_t>(opposite) ==
      chain->plan->sides[1 - side_index];
  const auto invocation = scoped ? chain->next_invocation.fetch_add(1) + 1 : 0;
  if (scoped) {
    auto *row = Capture(CombatScopedChainBoundaryV1::casualty_enter,
                        invocation, 0, side_index, -1, nullptr, 0, true);
    if (row != nullptr) {
      row->casualty_damage_raw = damage;
      row->caller_return_address = native_caller;
    }
  }
  const auto result = original(side, damage, opposite);
  if (scoped) {
    auto *row = Capture(CombatScopedChainBoundaryV1::casualty_return,
                        invocation, 0, side_index, -1, nullptr, 0, true);
    if (row != nullptr) row->casualty_damage_raw = damage;
  }
  return result;
}

namespace {

void Jump(std::uint8_t *bytes, std::uintptr_t target) noexcept {
  bytes[0] = 0xFF; bytes[1] = 0x25;
  std::memset(bytes + 2, 0, 4);
  std::memcpy(bytes + 6, &target, 8);
}

// Complete instruction boundaries: request18 (one RIP-relative load),
// commit15, enqueue17 and casualty20. No copied relative branch/call.
constexpr std::array<std::uint8_t, 18> kRequest{
    0x48,0x83,0xEC,0x68,0x48,0x8B,0x05,0x5D,0x24,0x0C,0x03,
    0x80,0xB8,0xC1,0,0,0,0};
constexpr std::array<std::uint8_t, 15> kCommit{
    0x48,0x89,0x5C,0x24,0x08,0x4C,0x89,0x4C,0x24,0x20,
    0x4C,0x89,0x44,0x24,0x18};
constexpr std::array<std::uint8_t, 17> kEnqueue{
    0x48,0x89,0x5C,0x24,0x18,0x55,0x56,0x41,0x56,0x48,0x83,0xEC,0x20,
    0x48,0x63,0x41,0x0C};
constexpr std::array<std::uint8_t, 20> kCasualty{
    0x4C,0x89,0x44,0x24,0x18,0x56,0x57,0x41,0x55,0x48,0x83,0xEC,0x60,
    0x48,0x8B,0x81,0x98,0,0,0};

bool InstallOne(CombatScopedDetourV1 &state, std::uintptr_t target,
                std::uintptr_t hook, const std::uint8_t *anchor,
                std::size_t length, bool request) noexcept {
  if (state.installed || std::memcmp(reinterpret_cast<void *>(target), anchor, length) != 0) return false;
  auto *const trampoline = static_cast<std::uint8_t *>(VirtualAlloc(
      nullptr, 64, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE));
  if (trampoline == nullptr) return false;
  std::size_t cursor = length;
  if (request) {
    // Replace MOV RAX,[RIP+disp32] with MOVABS RAX,slot; MOV RAX,[RAX].
    // RAX was overwritten by the original load, so no live register is lost.
    std::memcpy(trampoline, anchor, 4);
    trampoline[4] = 0x48; trampoline[5] = 0xB8;
    std::int32_t displacement = 0;
    std::memcpy(&displacement, anchor + 7, 4);
    const auto slot = target + 11 + displacement;
    std::memcpy(trampoline + 6, &slot, 8);
    trampoline[14] = 0x48; trampoline[15] = 0x8B; trampoline[16] = 0x00;
    std::memcpy(trampoline + 17, anchor + 11, 7);
    cursor = 24;
  } else {
    std::memcpy(trampoline, anchor, length);
  }
  Jump(trampoline + cursor, target + length);
  DWORD previous = 0;
  if (!VirtualProtect(trampoline, 64, PAGE_EXECUTE_READ, &previous) ||
      !FlushInstructionCache(GetCurrentProcess(), trampoline, cursor + 14)) {
    VirtualFree(trampoline, 0, MEM_RELEASE); return false;
  }
  DWORD target_protection = 0;
  if (!VirtualProtect(reinterpret_cast<void *>(target), length, PAGE_EXECUTE_READWRITE,
                      &target_protection)) {
    VirtualFree(trampoline, 0, MEM_RELEASE); return false;
  }
  std::memcpy(state.original.data(), anchor, length);
  std::array<std::uint8_t, 20> patch{};
  patch.fill(0x90);
  Jump(patch.data(), hook);
  std::memcpy(reinterpret_cast<void *>(target), patch.data(), length);
  DWORD unused = 0;
  const bool restored = VirtualProtect(reinterpret_cast<void *>(target), length,
                                      target_protection, &unused) != 0;
  const bool flushed = FlushInstructionCache(GetCurrentProcess(),
                                             reinterpret_cast<void *>(target), length) != 0;
  state.target = target;
  state.trampoline = trampoline;
  state.patch_size = static_cast<std::uint32_t>(length);
  state.installed = true;
  return restored && flushed;
}

} // namespace

bool ArmCombatScopedChainUnsafeV1(CombatScopedChainV1 &chain,
                           const CombatPhaseEventTraceCapturePlanV1 &plan,
                           std::int32_t character_id, std::int32_t related_id,
                            std::int32_t event, std::uintptr_t offline_trait_database_override,
                            std::uintptr_t offline_identifier_table_override) noexcept {
  if (chain.armed.load() != 0 || character_id <= 0 || related_id <= 0 ||
      character_id == related_id || event < 0 || event >= 13 ||
      plan.character_count > plan.characters.size() ||
      !plan.loaded_event_row_objects_available || plan.current_date_slot == 0) return false;
  chain.plan = &plan;
  chain.identifier_table=offline_identifier_table_override!=0?offline_identifier_table_override:
      offline_trait_database_override!=0?0:plan.module_base+0x585F240;
  chain.character_ids = {character_id, related_id};
  chain.event_load_index = event;
  const auto trait_database = offline_trait_database_override != 0
      ? offline_trait_database_override : Read<std::uintptr_t>(plan.module_base + 0x570C0F8);
  if (!ReadTraitDefinitions(chain, trait_database)) return false;
  for (std::size_t who = 0; who < 2; ++who) {
    for (std::uint32_t i = 0; i < plan.character_count; ++i) {
      if (plan.characters[i].full_id == chain.character_ids[who]) {
        chain.character_objects[who] = plan.characters[i].object;
        break;
      }
    }
    if (chain.character_objects[who] == 0 ||
        Read<std::int32_t>(chain.character_objects[who], 0x18) != chain.character_ids[who]) return false;
    const auto link = Read<std::uintptr_t>(chain.character_objects[who], 0x1B0);
    chain.prearmed_regiment_ids[who] = link != 0 ? Read<std::int32_t>(link, 0xF8) : -1;
  }
  chain.before_date_raw = Read<std::int32_t>(plan.expected_current_date_object, 8);
  if (chain.before_date_raw > std::numeric_limits<std::int32_t>::max() - 24) return false;
  chain.count.store(0);
  chain.next_invocation.store(0);
  chain.entry_snapshot_count.store(0);
  chain.battle_event_snapshot_count.store(0);
  chain.failure_flags.store(0);
  chain.active_readers.store(0);
  CombatScopedChainV1 *expected = nullptr;
  if (!g_chain.compare_exchange_strong(expected, &chain)) return false;
  chain.armed.store(1, std::memory_order_release);
  (void)Capture(CombatScopedChainBoundaryV1::arm_paused, 0, 0, -1, -1, nullptr, 0, true);
  return chain.failure_flags.load() == 0;
}

bool ArmCombatScopedChainV1Impl(CombatScopedChainV1 &chain,
                           const CombatPhaseEventTraceCapturePlanV1 &plan,
                           std::int32_t character_id, std::int32_t related_id,
                            std::int32_t event, std::uintptr_t offline_trait_database_override,
                            std::uintptr_t offline_identifier_table_override) noexcept {
#if defined(_MSC_VER)
  __try {
#endif
    return ArmCombatScopedChainUnsafeV1(chain, plan, character_id, related_id,
                                       event, offline_trait_database_override,offline_identifier_table_override);
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    chain.failure_flags.fetch_or(scoped_chain_failure_memory);
    CancelCombatScopedChainV1(chain);
    return false;
  }
#endif
}

void CancelCombatScopedChainV1Impl(CombatScopedChainV1 &chain) noexcept {
  chain.armed.store(0, std::memory_order_release);
  auto *expected = &chain;
  (void)g_chain.compare_exchange_strong(expected, nullptr);
}

void FinishCombatScopedChainV1Impl(CombatScopedChainV1 &chain) noexcept {
  if (g_chain.load() == &chain) {
    (void)Capture(CombatScopedChainBoundaryV1::next_paused, 0, 0, -1, -1, nullptr, 0, true);
  }
  CancelCombatScopedChainV1(chain);
}

std::uint32_t EnterCombatScopedEffectV1Impl(void *node, std::int32_t side,
                                      std::int32_t event, std::uint32_t depth,void *context) noexcept {
  auto *const chain = g_chain.load();
  if (chain == nullptr || chain->armed.load() == 0 || event != chain->event_load_index) return 0;
  const auto invocation = chain->next_invocation.fetch_add(1) + 1;
  auto *row=Capture(CombatScopedChainBoundaryV1::effect_enter, invocation,
                g_effect_invocation, side, event, node, depth);
  if(row&&context) {
    __try {row->execution_context=reinterpret_cast<std::uintptr_t>(context);
      row->native_root_scope=Read<std::uintptr_t>(row->execution_context);
      if(row->native_root_scope)row->native_scope_words={Read<std::uint64_t>(row->native_root_scope),Read<std::uint64_t>(row->native_root_scope,8)};
    } __except(EXCEPTION_EXECUTE_HANDLER){Failure(*chain,*row,scoped_chain_failure_memory);}
  }
  g_effect_invocation = invocation;
  return invocation;
}

void ReturnCombatScopedEffectV1Impl(std::uint32_t invocation, void *node,
                              std::int32_t side, std::int32_t event,
                              std::uint32_t depth) noexcept {
  if (invocation == 0) return;
  auto *row = Capture(CombatScopedChainBoundaryV1::effect_return,
                     invocation, 0, side, event, node, depth);
  auto *const chain = g_chain.load();
  if (chain != nullptr) {
    const auto count = std::min<std::uint32_t>(chain->count.load(),
        static_cast<std::uint32_t>(chain->records.size()));
    for (std::uint32_t i = 0; i < count; ++i) {
      const auto &entry = chain->records[i];
      if (entry.boundary == CombatScopedChainBoundaryV1::effect_enter &&
          entry.invocation == invocation) {
        g_effect_invocation = entry.parent_invocation;
        if (row != nullptr) row->parent_invocation = entry.parent_invocation;
        break;
      }
    }
  }
}

void ObserveCombatScopedPhaseV1Impl(CombatPhaseEventTraceBoundaryV1 boundary,
                              std::int32_t side) noexcept {
  if (boundary == CombatPhaseEventTraceBoundaryV1::before_side0_phase_fire ||
      boundary == CombatPhaseEventTraceBoundaryV1::before_side1_phase_fire) {
    (void)Capture(CombatScopedChainBoundaryV1::phase_before, 0, 0, side, -1, nullptr, 0, true);
  } else if (boundary == CombatPhaseEventTraceBoundaryV1::after_side0_phase_fire ||
             boundary == CombatPhaseEventTraceBoundaryV1::after_side1_phase_fire) {
    (void)Capture(CombatScopedChainBoundaryV1::phase_after, 0, 0, side, -1, nullptr, 0, true);
  }
}

void ObserveCombatScopedSelectorV1Impl(bool before, std::int32_t side,
                                 std::int32_t event, void *candidates,
                                 std::int32_t selected_index) noexcept {
  auto *const chain = g_chain.load();
  if (chain == nullptr || event != chain->event_load_index) return;
  auto *row = Capture(before ? CombatScopedChainBoundaryV1::selector_enter
                       : CombatScopedChainBoundaryV1::selector_return,
                g_effect_invocation, g_effect_invocation, side, event);
  if (row == nullptr) return;
  row->selected_candidate_index = selected_index;
#if defined(_MSC_VER)
  __try {
#endif
    const auto native = reinterpret_cast<std::uintptr_t>(candidates);
    const auto data = Read<std::uintptr_t>(native);
    const auto capacity = Read<std::int32_t>(native, 8);
    const auto count = Read<std::int32_t>(native, 12);
    if (data == 0 || count <= 0 || count > capacity ||
        static_cast<std::size_t>(count) > row->selector_candidates.size() ||
        (!before && (selected_index < 0 || selected_index >= count))) {
      Failure(*chain, *row, scoped_chain_failure_container);
      return;
    }
    for (std::int32_t i = 0; i < count; ++i) {
      auto &candidate = row->selector_candidates[static_cast<std::size_t>(i)];
      candidate.scope_word0 = Read<std::uint64_t>(data, static_cast<std::size_t>(i) * 16);
      candidate.scope_word1 = Read<std::uint64_t>(data, static_cast<std::size_t>(i) * 16 + 8);
      // Exact character scoped object: kind4 plus full-generation stored ID.
      // Never coerce a different scope kind or an opaque pointer into an ID.
      if (candidate.scope_word0 == 4 && candidate.scope_word1 <=
          static_cast<std::uint64_t>(std::numeric_limits<std::int32_t>::max())) {
        candidate.character_id = static_cast<std::int32_t>(candidate.scope_word1);
        for (std::uint32_t j = 0; j < chain->plan->character_count; ++j) {
          const auto &source = chain->plan->characters[j];
          if (source.full_id == candidate.character_id) {
            candidate.character_full_identity_matches =
                Read<std::int32_t>(source.object, 0x18) == source.full_id;
            break;
          }
        }
      }
      if (!candidate.character_full_identity_matches) {
        Failure(*chain, *row, scoped_chain_failure_identity);
      }
      ++row->selector_candidate_count;
    }
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    Failure(*chain, *row, scoped_chain_failure_memory);
  }
#endif
}

namespace {
const CombatScopedChainRecordV1 *CurrentEffect() noexcept {
  auto *chain=g_chain.load();if(!chain||chain->armed.load()==0||g_effect_invocation==0)return nullptr;
  auto n=std::min<std::uint32_t>(chain->count.load(),static_cast<std::uint32_t>(chain->records.size()));
  while(n!=0){const auto &r=chain->records[--n];if(r.boundary==CombatScopedChainBoundaryV1::effect_enter&&r.invocation==g_effect_invocation)return &r;}
  return nullptr;
}
CombatScopedChainRecordV1 *SelectorCapture(CombatScopedChainBoundaryV1 boundary,std::uint32_t invocation) noexcept {
  const auto *effect=CurrentEffect();if(!effect)return nullptr;
  auto *r=Capture(boundary,invocation,effect->invocation,effect->side_index,effect->native_event_load_index,
                  reinterpret_cast<void*>(effect->node_identity),effect->depth,boundary==CombatScopedChainBoundaryV1::materializer_enter);
  if(r){r->execution_context=effect->execution_context;r->native_root_scope=effect->native_root_scope;r->native_scope_words=effect->native_scope_words;}
  return r;
}
void CombatSource(CombatScopedChainV1 &chain,CombatScopedChainRecordV1 &r,std::uintptr_t scope) noexcept {
  if(scope==0){Failure(chain,r,scoped_chain_failure_binding);return;}
  r.native_root_scope=scope;r.native_scope_words={Read<std::uint64_t>(scope),Read<std::uint64_t>(scope,8)};
  const auto kind=Read<std::uint16_t>(scope);const auto aux=Read<std::uint16_t>(scope,2);
  const auto combat=Read<std::int32_t>(scope,8);
  if(kind!=0x0B||aux>1||combat!=chain.plan->combat_id||Read<std::int32_t>(chain.plan->combat,8)!=combat){Failure(chain,r,scoped_chain_failure_identity);return;}
  const auto side=chain.plan->combat+(aux==0?0x20:0x368);
  r.selector_source_side_index=aux;r.selector_source_combat_identity_matches=
      side==chain.plan->sides[aux]&&Read<std::uintptr_t>(side,0xB8)==chain.plan->combat;
  if(!r.selector_source_combat_identity_matches)Failure(chain,r,scoped_chain_failure_identity);
}
void SelectorVector(CombatScopedChainV1 &chain,CombatScopedChainRecordV1 &r,std::uintptr_t vector) noexcept {
  r.selector_vector=vector;
  if(!vector){Failure(chain,r,scoped_chain_failure_container);return;}
  const auto data=Read<std::uintptr_t>(vector);const auto cap=Read<std::int32_t>(vector,8);const auto n=Read<std::int32_t>(vector,12);
  r.selector_data=data;
  if(n<0||cap<n||r.selector_prefix_count<0||r.selector_prefix_count>n||n>static_cast<std::int32_t>(r.selector_candidates.size())||(n!=0&&data==0)){Failure(chain,r,scoped_chain_failure_container);return;}
  r.selector_candidate_count=static_cast<std::uint32_t>(n);
  for(std::int32_t i=0;i<n;++i){auto &c=r.selector_candidates[i];c.scope_word0=Read<std::uint64_t>(data,i*16);c.scope_word1=Read<std::uint64_t>(data,i*16+8);
    // Kind0 is a legitimate rejected filter item. Preserve its raw words.
    if((c.scope_word0&0xFFFF)==0)continue;
    if((c.scope_word0&0xFFFF)==4){const auto raw=Read<std::int64_t>(data,i*16+8);
      if(raw>0&&raw<=INT32_MAX){c.character_id=static_cast<std::int32_t>(raw);
        for(std::uint32_t j=0;j<chain.plan->character_count;++j)if(chain.plan->characters[j].full_id==c.character_id)
          c.character_full_identity_matches=Read<std::int32_t>(chain.plan->characters[j].object,0x18)==c.character_id;
      }
    }
    if(i>=r.selector_prefix_count&&!c.character_full_identity_matches)Failure(chain,r,scoped_chain_failure_identity);
  }
}
void FilterFields(CombatScopedChainV1 &chain,CombatScopedChainRecordV1 &r) noexcept {
  r.selector_prefix_count=g_filter_context.prefix;r.selector_list_context=g_filter_context.context;
  r.source_predicate=g_filter_context.source;r.shared_predicate=g_filter_context.shared;
  if(r.source_predicate==0||r.shared_predicate==0){Failure(chain,r,scoped_chain_failure_binding);return;}
  r.source_predicate_count=Read<std::int32_t>(r.source_predicate,0x5C);
  r.shared_predicate_count=Read<std::int32_t>(r.shared_predicate,0x5C);
  if(r.source_predicate_count<0||r.shared_predicate_count<0)Failure(chain,r,scoped_chain_failure_container);
  CombatSource(chain,r,Read<std::uintptr_t>(r.selector_list_context));
  SelectorVector(chain,r,g_filter_context.vector);
}
bool VariableName(CombatScopedChainV1 &chain,std::int32_t id,CombatScopedStableKeyV1 &out) noexcept {
  const auto table=chain.identifier_table;if(!table||id<0)return false;
  const auto epoch=Read<std::uint8_t>(table);const auto data=Read<std::uintptr_t>(table,0x30);const auto count=Read<std::int32_t>(table,0x3C);
  const auto index=static_cast<std::uint32_t>(id)&0xFFFFFF;
  return epoch==(static_cast<std::uint32_t>(id)>>24)&&data!=0&&count>0&&count<=1048576&&index<static_cast<std::uint32_t>(count)&&
      ReadStableKey(data+index*0x20,out)&&Read<std::uintptr_t>(table,0x30)==data&&Read<std::int32_t>(table,0x3C)==count&&Read<std::uint8_t>(table)==epoch;
}
void ListState(CombatScopedChainV1 &chain,CombatScopedChainRecordV1 &r) noexcept {
  const auto data=Read<std::uintptr_t>(r.variable_owner,0x30);const auto n=Read<std::int32_t>(r.variable_owner,0x3C);
  if(n<0||n>8192||(n!=0&&data==0)){Failure(chain,r,scoped_chain_failure_container);return;}
  for(std::int32_t i=0;i<n;++i){const auto item=data+i*0x48;if(Read<std::int32_t>(item,8)!=r.variable_key_id)continue;
    if(r.variable_list_present){Failure(chain,r,scoped_chain_failure_container);return;}
    r.variable_list_present=true;
    const auto values=Read<std::uintptr_t>(item,0x10);const auto count=Read<std::int32_t>(item,0x1C);const auto cap=Read<std::int32_t>(item,0x18);
    const auto expiry=Read<std::uintptr_t>(item,0x28);const auto expiry_count=Read<std::int32_t>(item,0x34);
    if(count<0||count>cap||count!=expiry_count||count>static_cast<std::int32_t>(r.variable_list_values.size())||(count!=0&&(values==0||expiry==0))){Failure(chain,r,scoped_chain_failure_container);return;}
    r.list_elapsed_offset=Read<std::int32_t>(item,0x40);r.variable_list_count=static_cast<std::uint32_t>(count);
    for(std::int32_t j=0;j<count;++j){r.variable_list_values[j]={Read<std::uint64_t>(values,j*16),Read<std::uint64_t>(values,j*16+8)};r.variable_list_expirations[j]=Read<std::int32_t>(expiry,j*4);}
  }
  r.variable_list_read=true;
}
}
extern "C" std::uintptr_t __fastcall ScopedSelectorFilterImpl(void *self,void *source,void *shared,void *context,void *vector) noexcept {
  const auto original=g_filter.load();if(!original)return 0;
  const auto previous=g_filter_context;auto *chain=g_chain.load();bool scoped=CurrentEffect()!=nullptr;
  if(scoped){
    __try {
      g_filter_context={reinterpret_cast<std::uintptr_t>(vector),reinterpret_cast<std::uintptr_t>(context),reinterpret_cast<std::uintptr_t>(source),reinterpret_cast<std::uintptr_t>(shared),Read<std::int32_t>(reinterpret_cast<std::uintptr_t>(vector),12),chain->next_invocation.fetch_add(1)+1};
      auto *r=SelectorCapture(CombatScopedChainBoundaryV1::filter_enter,g_filter_context.invocation);if(r)FilterFields(*chain,*r);
    }__except(EXCEPTION_EXECUTE_HANDLER){chain->failure_flags.fetch_or(scoped_chain_failure_memory);scoped=false;g_filter_context={};}
  }
  const auto result=original(self,source,shared,context,vector);
  if(scoped){__try{auto *r=SelectorCapture(CombatScopedChainBoundaryV1::filter_return,g_filter_context.invocation);if(r){FilterFields(*chain,*r);r->original_return_bits=result;}}
    __except(EXCEPTION_EXECUTE_HANDLER){chain->failure_flags.fetch_or(scoped_chain_failure_memory);}}
  g_filter_context=previous;return result;
}
extern "C" std::uintptr_t __fastcall ScopedSelectorMaterializerImpl(void *self,void *vector,void *context) noexcept {
  const auto original=g_materializer.load();if(!original)return 0;
  auto *chain=g_chain.load();const bool scoped=chain&&CurrentEffect()&&g_filter_context.invocation!=0&&g_filter_context.vector==reinterpret_cast<std::uintptr_t>(vector)&&g_filter_context.context==reinterpret_cast<std::uintptr_t>(context);
  if(scoped){__try{auto *r=SelectorCapture(CombatScopedChainBoundaryV1::materializer_enter,g_filter_context.invocation);if(r)FilterFields(*chain,*r);}
    __except(EXCEPTION_EXECUTE_HANDLER){chain->failure_flags.fetch_or(scoped_chain_failure_memory);}}
  const auto result=original(self,vector,context);
  if(scoped){__try{auto *r=SelectorCapture(CombatScopedChainBoundaryV1::materializer_return,g_filter_context.invocation);if(r){FilterFields(*chain,*r);r->original_return_bits=result;}}
    __except(EXCEPTION_EXECUTE_HANDLER){chain->failure_flags.fetch_or(scoped_chain_failure_memory);}}
  return result;
}
extern "C" std::uintptr_t __fastcall ScopedSelectorPredicateImpl(void *predicate,void *context,std::uint8_t mode, std::uintptr_t native_caller) noexcept {
  const auto original=g_predicate.load();if(!original)return 0;
  auto *chain=g_chain.load();const auto caller=native_caller;std::uint32_t role=0,invocation=0;
  const auto pred=reinterpret_cast<std::uintptr_t>(predicate);
  if(chain&&CurrentEffect()&&g_filter_context.invocation!=0){
    if((caller==chain->plan->module_base+0x19F480B||g_selector_offline_fixture)&&pred==g_filter_context.shared)role=1;
    if((caller==chain->plan->module_base+0x19F481F||g_selector_offline_fixture)&&pred==g_filter_context.source)role=2;
  }
  auto publish=[&](CombatScopedChainBoundaryV1 boundary,std::uint64_t result,bool returned) noexcept {
    if(role==0)return;
    auto *r=SelectorCapture(boundary,invocation);if(!r)return;
    FilterFields(*chain,*r);r->predicate=pred;r->predicate_role=role;r->caller_return_address=caller;
    const auto candidate=Read<std::uintptr_t>(reinterpret_cast<std::uintptr_t>(context));
    if(candidate<r->selector_data||candidate-r->selector_data>=r->selector_candidate_count*16ULL||((candidate-r->selector_data)%16)!=0||mode!=0){Failure(*chain,*r,scoped_chain_failure_binding);return;}
    r->selector_current_index=static_cast<std::int32_t>((candidate-r->selector_data)/16);
    if(r->selector_current_index<r->selector_prefix_count)Failure(*chain,*r,scoped_chain_failure_correlation);
    r->original_predicate_boolean_read=returned;r->original_return_bits=result;r->original_predicate_boolean=(result&0xFF)!=0;
    if(returned&&(result&0xFF)>1)Failure(*chain,*r,scoped_chain_failure_container);
  };
  if(role!=0){invocation=chain->next_invocation.fetch_add(1)+1;__try{publish(CombatScopedChainBoundaryV1::predicate_enter,0,false);}__except(EXCEPTION_EXECUTE_HANDLER){chain->failure_flags.fetch_or(scoped_chain_failure_memory);}}
  const auto result=original(predicate,context,mode);
  if(role!=0){__try{publish(CombatScopedChainBoundaryV1::predicate_return,result,true);}__except(EXCEPTION_EXECUTE_HANDLER){chain->failure_flags.fetch_or(scoped_chain_failure_memory);}}
  return result;
}
extern "C" std::uintptr_t __fastcall ScopedCombatListWriterImpl(void *owner,std::int32_t key,const void *value,std::int32_t expiry, std::uintptr_t native_caller) noexcept {
  const auto original=g_list_writer.load();if(!original)return 0;
  auto *chain=g_chain.load();const auto *effect=CurrentEffect();bool scoped=effect&&effect->node_vtable_rva==0x44D3760;std::uint32_t invocation=0;
  const auto caller=native_caller;
  auto publish=[&](CombatScopedChainBoundaryV1 boundary,std::uint64_t returned) noexcept {
    auto *r=SelectorCapture(boundary,invocation);if(!r)return;
    r->variable_owner=reinterpret_cast<std::uintptr_t>(owner);r->variable_key_id=key;r->requested_expiry=expiry;
    r->variable_owner_from_original_getter=g_list_owner.effect_invocation==effect->invocation&&g_list_owner.owner!=0&&g_list_owner.owner==r->variable_owner;
    r->variable_owner_scope=g_list_owner.scope;r->variable_owner_scope_words=g_list_owner.words;
    r->requested_scope_words={Read<std::uint64_t>(reinterpret_cast<std::uintptr_t>(value)),Read<std::uint64_t>(reinterpret_cast<std::uintptr_t>(value),8)};
    r->caller_return_address=caller;r->original_return_bits=returned;
    CombatSource(*chain,*r,r->native_root_scope);
    if(!r->variable_owner_from_original_getter)Failure(*chain,*r,scoped_chain_failure_correlation);
    if((r->requested_scope_words[0]&0xFFFF)==4&&r->requested_scope_words[1]>0&&r->requested_scope_words[1]<=INT32_MAX){
      const auto id=static_cast<std::int32_t>(r->requested_scope_words[1]);
      for(std::uint32_t i=0;i<chain->plan->character_count;++i)if(chain->plan->characters[i].full_id==id)
        r->requested_character_full_identity_matches=Read<std::int32_t>(chain->plan->characters[i].object,0x18)==id;
    }
    if(!r->requested_character_full_identity_matches)Failure(*chain,*r,scoped_chain_failure_identity);
    if(!VariableName(*chain,key,r->variable_key))Failure(*chain,*r,scoped_chain_failure_binding);
    else ListState(*chain,*r);
  };
  if(scoped){invocation=chain->next_invocation.fetch_add(1)+1;__try{publish(CombatScopedChainBoundaryV1::list_write_enter,0);}__except(EXCEPTION_EXECUTE_HANDLER){chain->failure_flags.fetch_or(scoped_chain_failure_memory);}}
  const auto result=original(owner,key,value,expiry);
  if(scoped){__try{publish(CombatScopedChainBoundaryV1::list_write_return,result);}__except(EXCEPTION_EXECUTE_HANDLER){chain->failure_flags.fetch_or(scoped_chain_failure_memory);}}
  return result;
}
bool BindCombatScopedSelectorOriginalsForOfflineFixtureV1(CombatScopedMaterializerOriginalV1 materializer,
    CombatScopedFilterOriginalV1 filter,CombatScopedPredicateOriginalV1 predicate,CombatScopedListWriterOriginalV1 list) noexcept {
  if(g_chain.load()!=nullptr||!materializer||!filter||!predicate||!list)return false;
  g_materializer.store(materializer);g_filter.store(filter);g_predicate.store(predicate);g_list_writer.store(list);g_selector_offline_fixture=true;return true;
}
bool ReadCurrentCombatScopedEffectContextV1Impl(CombatScopedEffectContextV1 &out) noexcept {
  const auto *r=CurrentEffect();auto *chain=g_chain.load();if(!r||!chain||!chain->plan)return false;
  out.read=true;out.managed_daily_sequence_token=chain->plan->managed_daily_sequence_token;
  out.invocation=r->invocation;out.depth=r->depth;out.node_hash=r->node_hash;out.node_vtable_rva=r->node_vtable_rva;
  out.combat_id=r->combat_id;out.side_index=r->side_index;out.event_load_index=r->native_event_load_index;
  out.node=r->node_identity;out.execution_context=r->execution_context;return true;
}
bool ReadCurrentCombatScopedDeathCommitContextV1Impl(CombatScopedDeathCommitContextV1 &out) noexcept {
  out={};const auto *chain=g_chain.load(std::memory_order_acquire);
  if(!chain || chain->armed.load(std::memory_order_acquire)==0 || !chain->plan ||
     !g_death_commit_context.read ||
     g_death_commit_context.managed_daily_sequence_token!=chain->plan->managed_daily_sequence_token ||
     g_death_commit_context.thread_id!=GetCurrentThreadId())return false;
  out=g_death_commit_context;return true;
}
void ObserveCombatScopedOriginalVariableOwnerV1Impl(const void *scope,void *owner) noexcept {
  auto *chain=g_chain.load();const auto *effect=CurrentEffect();
  if(!chain||!effect||effect->node_vtable_rva!=0x44D3760||scope==nullptr)return;
  __try {
    const auto s=reinterpret_cast<std::uintptr_t>(scope);const auto root=effect->native_root_scope;
    if(root!=0&&Read<std::uint16_t>(s)==0x0B&&Read<std::int32_t>(s,8)==chain->plan->combat_id&&
       Read<std::uint16_t>(s,2)<=1&&Read<std::uint16_t>(s,2)==Read<std::uint16_t>(root,2)&&Read<std::uint16_t>(root)==0x0B&&Read<std::int32_t>(root,8)==chain->plan->combat_id)
      g_list_owner={effect->invocation,reinterpret_cast<std::uintptr_t>(owner),s,{Read<std::uint64_t>(s),Read<std::uint64_t>(s,8)}};
  }__except(EXCEPTION_EXECUTE_HANDLER){chain->failure_flags.fetch_or(scoped_chain_failure_memory);}
}

bool InstallCombatScopedDetoursV1(CombatScopedDetoursV1 &state,
                                std::uintptr_t module_base,
                                bool exact_build_admitted,
                                bool paused_quiescence_proven) noexcept {
  ScopedObserverMutationV1 mutation; if (!mutation) return false;
  if (!exact_build_admitted || !paused_quiescence_proven || module_base == 0 ||
      g_chain.load() != nullptr) return false;
  g_selector_offline_fixture=false;
  constexpr std::array<std::uint8_t,15> materializer{0x48,0x89,0x5C,0x24,0x18,0x48,0x89,0x74,0x24,0x20,0x57,0x48,0x83,0xEC,0x30};
  constexpr std::array<std::uint8_t,15> filter{0x48,0x89,0x6C,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x48,0x89,0x7C,0x24,0x20};
  constexpr std::array<std::uint8_t,15> predicate{0x48,0x8B,0xC4,0x48,0x89,0x58,0x08,0x48,0x89,0x70,0x18,0x48,0x89,0x78,0x20};
  constexpr std::array<std::uint8_t,14> list{0x48,0x89,0x5C,0x24,0x08,0x48,0x89,0x74,0x24,0x18,0x89,0x54,0x24,0x10};
  const bool success =
      InstallOne(state.hooks[0], module_base + 0x264BC00,
                 reinterpret_cast<std::uintptr_t>(&ScopedDeathRequest), kRequest.data(), kRequest.size(), true) &&
      (g_death_request.store(reinterpret_cast<DeathOriginal>(state.hooks[0].trampoline)), true) &&
      InstallOne(state.hooks[1], module_base + 0x264BCB0,
                 reinterpret_cast<std::uintptr_t>(&ScopedDeathCommit), kCommit.data(), kCommit.size(), false) &&
      (g_death_commit.store(reinterpret_cast<DeathOriginal>(state.hooks[1].trampoline)), true) &&
      InstallOne(state.hooks[2], module_base + 0x2654960,
                 reinterpret_cast<std::uintptr_t>(&ScopedDeathEnqueue), kEnqueue.data(), kEnqueue.size(), false) &&
      (g_death_enqueue.store(reinterpret_cast<QueueOriginal>(state.hooks[2].trampoline)), true) &&
      InstallOne(state.hooks[3], module_base + 0x23CE080,
                 reinterpret_cast<std::uintptr_t>(&ScopedCasualty), kCasualty.data(), kCasualty.size(), false) &&
       (g_casualty.store(reinterpret_cast<CasualtyOriginal>(state.hooks[3].trampoline)), true) &&
       InstallOne(state.hooks[4],module_base+0x19DD670,reinterpret_cast<std::uintptr_t>(&ScopedSelectorMaterializer),materializer.data(),materializer.size(),false) &&
       (g_materializer.store(reinterpret_cast<CombatScopedMaterializerOriginalV1>(state.hooks[4].trampoline)),true) &&
       InstallOne(state.hooks[5],module_base+0x19F4760,reinterpret_cast<std::uintptr_t>(&ScopedSelectorFilter),filter.data(),filter.size(),false) &&
       (g_filter.store(reinterpret_cast<CombatScopedFilterOriginalV1>(state.hooks[5].trampoline)),true) &&
       InstallOne(state.hooks[6],module_base+0x334C600,reinterpret_cast<std::uintptr_t>(&ScopedSelectorPredicate),predicate.data(),predicate.size(),false) &&
       (g_predicate.store(reinterpret_cast<CombatScopedPredicateOriginalV1>(state.hooks[6].trampoline)),true) &&
       InstallOne(state.hooks[7],module_base+0x33463D0,reinterpret_cast<std::uintptr_t>(&ScopedCombatListWriter),list.data(),list.size(),false) &&
       (g_list_writer.store(reinterpret_cast<CombatScopedListWriterOriginalV1>(state.hooks[7].trampoline)),true);
  if (!success) {
    state.failure_flags |= scoped_chain_failure_detour;
    (void)UninstallCombatScopedDetoursV1(state);
  }
  return success;
}

bool InstallCombatScopedExactDetourV1(CombatScopedDetourV1 &state,
                                    std::uintptr_t target, std::uintptr_t hook,
                                    const std::uint8_t *anchor, std::size_t length) noexcept {
  ScopedObserverMutationV1 mutation; if (!mutation) return false;
  if (target == 0 || hook == 0 || anchor == nullptr || length < 14 ||
      length > state.original.size()) return false;
  return InstallOne(state, target, hook, anchor, length, false);
}

bool UninstallCombatScopedExactDetourV1(CombatScopedDetourV1 &state,
                                      std::uintptr_t callback) noexcept {
  ScopedObserverMutationV1 mutation; if (!mutation) return false;
  if (!state.installed) return true;
  if (state.patch_size < 14 || state.patch_size > state.original.size() ||
      callback == 0) return false;
  std::array<std::uint8_t, 20> expected{};
  expected.fill(0x90);
  Jump(expected.data(), callback);
  if (std::memcmp(reinterpret_cast<void *>(state.target), expected.data(), state.patch_size) != 0) return false;
  DWORD protection = 0;
  if (!VirtualProtect(reinterpret_cast<void *>(state.target), state.patch_size,
                      PAGE_EXECUTE_READWRITE, &protection)) return false;
  std::memcpy(reinterpret_cast<void *>(state.target), state.original.data(), state.patch_size);
  DWORD ignored = 0;
  if (!VirtualProtect(reinterpret_cast<void *>(state.target), state.patch_size, protection, &ignored) ||
      !FlushInstructionCache(GetCurrentProcess(), reinterpret_cast<void *>(state.target), state.patch_size)) return false;
  state.installed = false;
  // Retain original trampoline until the owned process exits.
  return true;
}

bool UninstallCombatScopedDetoursV1(CombatScopedDetoursV1 &state) noexcept {
  ScopedObserverMutationV1 mutation; if (!mutation) return false;
  if (g_chain.load() != nullptr) return false;
  bool success = true;
  for (std::size_t i = state.hooks.size(); i != 0; --i) {
    auto &hook = state.hooks[i - 1];
    if (!hook.installed) continue;
    std::array<std::uint8_t, 20> expected{};
    expected.fill(0x90);
    const std::array<std::uintptr_t, 8> callbacks{
        reinterpret_cast<std::uintptr_t>(&ScopedDeathRequest),
        reinterpret_cast<std::uintptr_t>(&ScopedDeathCommit),
        reinterpret_cast<std::uintptr_t>(&ScopedDeathEnqueue),
        reinterpret_cast<std::uintptr_t>(&ScopedCasualty),
        reinterpret_cast<std::uintptr_t>(&ScopedSelectorMaterializer),
        reinterpret_cast<std::uintptr_t>(&ScopedSelectorFilter),
        reinterpret_cast<std::uintptr_t>(&ScopedSelectorPredicate),
        reinterpret_cast<std::uintptr_t>(&ScopedCombatListWriter)};
    Jump(expected.data(), callbacks[i - 1]);
    if (std::memcmp(reinterpret_cast<void *>(hook.target), expected.data(), hook.patch_size) != 0) {
      success = false; continue;
    }
    DWORD previous = 0;
    if (!VirtualProtect(reinterpret_cast<void *>(hook.target), hook.patch_size,
                        PAGE_EXECUTE_READWRITE, &previous)) { success = false; continue; }
    std::memcpy(reinterpret_cast<void *>(hook.target), hook.original.data(), hook.patch_size);
    DWORD unused = 0;
    if (!VirtualProtect(reinterpret_cast<void *>(hook.target), hook.patch_size, previous, &unused) ||
        !FlushInstructionCache(GetCurrentProcess(), reinterpret_cast<void *>(hook.target), hook.patch_size)) {
      success = false; continue;
    }
    hook.installed = false;
    // Retain original trampoline until the owned process exits.
  }
  if (success) g_selector_offline_fixture=false;
  return success;
}

bool BindCombatScopedOriginalsForOfflineFixtureV1(
    CombatScopedDeathOriginalV1 request, CombatScopedDeathOriginalV1 commit,
    CombatScopedQueueOriginalV1 enqueue, CombatScopedCasualtyOriginalV1 casualty) noexcept {
  if (g_chain.load() != nullptr || request == nullptr || commit == nullptr ||
      enqueue == nullptr || casualty == nullptr) return false;
  g_death_request.store(request); g_death_commit.store(commit);
  g_death_enqueue.store(enqueue); g_casualty.store(casualty);
  return true;
}


extern "C" void __fastcall ScopedDeathRequest(void *a,void *b,void *c,void *d,void *e,void *f) noexcept {
  EnterScopedObserverCallbackV1();
  __try { ScopedDeathRequestImpl(a,b,c,d,e,f); }
  __finally { LeaveScopedObserverCallbackV1(); }
}

extern "C" void __fastcall ScopedDeathCommit(void *a,void *b,void *c,void *d,void *e,void *f) noexcept {
  EnterScopedObserverCallbackV1();
  __try { ScopedDeathCommitImpl(a,b,c,d,e,f); }
  __finally { LeaveScopedObserverCallbackV1(); }
}

extern "C" std::uintptr_t __fastcall ScopedDeathEnqueue(void *a,const void *b) noexcept {
  EnterScopedObserverCallbackV1();
  __try { return ScopedDeathEnqueueImpl(a,b); }
  __finally { LeaveScopedObserverCallbackV1(); }
}

extern "C" std::uintptr_t __fastcall ScopedCasualty(void *a,std::int64_t b,void *c) noexcept {
  EnterScopedObserverCallbackV1();
  __try { return ScopedCasualtyImpl(a,b,c, reinterpret_cast<std::uintptr_t>(_ReturnAddress())); }
  __finally { LeaveScopedObserverCallbackV1(); }
}

extern "C" std::uintptr_t __fastcall ScopedSelectorMaterializer(void *a,void *b,void *c) noexcept {
  EnterScopedObserverCallbackV1();
  __try { return ScopedSelectorMaterializerImpl(a,b,c); }
  __finally { LeaveScopedObserverCallbackV1(); }
}

extern "C" std::uintptr_t __fastcall ScopedSelectorFilter(void *a,void *b,void *c,void *d,void *e) noexcept {
  EnterScopedObserverCallbackV1();
  __try { return ScopedSelectorFilterImpl(a,b,c,d,e); }
  __finally { LeaveScopedObserverCallbackV1(); }
}

extern "C" std::uintptr_t __fastcall ScopedSelectorPredicate(void *a,void *b,std::uint8_t c) noexcept {
  EnterScopedObserverCallbackV1();
  __try { return ScopedSelectorPredicateImpl(a,b,c, reinterpret_cast<std::uintptr_t>(_ReturnAddress())); }
  __finally { LeaveScopedObserverCallbackV1(); }
}

extern "C" std::uintptr_t __fastcall ScopedCombatListWriter(void *a,std::int32_t b,const void *c,std::int32_t d) noexcept {
  EnterScopedObserverCallbackV1();
  __try { return ScopedCombatListWriterImpl(a,b,c,d, reinterpret_cast<std::uintptr_t>(_ReturnAddress())); }
  __finally { LeaveScopedObserverCallbackV1(); }
}

bool ArmCombatScopedChainV1(CombatScopedChainV1 &a,const CombatPhaseEventTraceCapturePlanV1 &b,std::int32_t c,std::int32_t d,std::int32_t e,std::uintptr_t f,std::uintptr_t g) noexcept {
  if (!TryEnterScopedObserverMutationV1()) return false;
  __try { return ArmCombatScopedChainV1Impl(a,b,c,d,e,f,g); }
  __finally { LeaveScopedObserverMutationV1(); }
}

void CancelCombatScopedChainV1(CombatScopedChainV1 &a) noexcept {
  if (!TryEnterScopedObserverMutationV1()) return ;
  __try { CancelCombatScopedChainV1Impl(a); }
  __finally { LeaveScopedObserverMutationV1(); }
}

void FinishCombatScopedChainV1(CombatScopedChainV1 &a) noexcept {
  if (!TryEnterScopedObserverMutationV1()) return ;
  __try { FinishCombatScopedChainV1Impl(a); }
  __finally { LeaveScopedObserverMutationV1(); }
}

std::uint32_t EnterCombatScopedEffectV1(void *a,std::int32_t b,std::int32_t c,std::uint32_t d,void *e) noexcept {
 EnterScopedObserverCallbackV1();
 const auto result=EnterCombatScopedEffectV1Impl(a,b,c,d,e);
 if(result==0)LeaveScopedObserverCallbackV1();
 return result;
}
void ReturnCombatScopedEffectV1(std::uint32_t a,void *b,std::int32_t c,std::int32_t d,std::uint32_t e) noexcept {
 if(a==0)return;
 __try {ReturnCombatScopedEffectV1Impl(a,b,c,d,e);}
 __finally {LeaveScopedObserverCallbackV1();}
}

void ObserveCombatScopedPhaseV1(CombatPhaseEventTraceBoundaryV1 a,std::int32_t b) noexcept {
  EnterScopedObserverCallbackV1();
  __try { ObserveCombatScopedPhaseV1Impl(a,b); }
  __finally { LeaveScopedObserverCallbackV1(); }
}

void ObserveCombatScopedSelectorV1(bool a,std::int32_t b,std::int32_t c,void *d,std::int32_t e) noexcept {
  EnterScopedObserverCallbackV1();
  __try { ObserveCombatScopedSelectorV1Impl(a,b,c,d,e); }
  __finally { LeaveScopedObserverCallbackV1(); }
}

void ObserveCombatScopedOriginalVariableOwnerV1(const void *a,void *b) noexcept {
  EnterScopedObserverCallbackV1();
  __try { ObserveCombatScopedOriginalVariableOwnerV1Impl(a,b); }
  __finally { LeaveScopedObserverCallbackV1(); }
}

bool ReadCurrentCombatScopedEffectContextV1(CombatScopedEffectContextV1 &a) noexcept {
  EnterScopedObserverCallbackV1();
  __try { return ReadCurrentCombatScopedEffectContextV1Impl(a); }
  __finally { LeaveScopedObserverCallbackV1(); }
}
bool ReadCurrentCombatScopedDeathCommitContextV1(CombatScopedDeathCommitContextV1 &a) noexcept {
  EnterScopedObserverCallbackV1();
  __try { return ReadCurrentCombatScopedDeathCommitContextV1Impl(a); }
  __finally { LeaveScopedObserverCallbackV1(); }
}

} // namespace xar::ck3_11906
