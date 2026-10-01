#include "xar_bridge/combat_scoped_transition_chain_v1.hpp"
#include <windows.h>
#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <memory>
#include <string>

using namespace xar::ck3_11906;

namespace {
template <typename T, std::size_t N> void Store(std::array<std::byte, N> &value, std::size_t offset, T scalar) {
  assert(offset + sizeof(T) <= N);
  std::memcpy(value.data() + offset, &scalar, sizeof(T));
}
template <typename T> void Store(void *value, std::size_t offset, T scalar) {
  std::memcpy(static_cast<std::byte *>(value) + offset, &scalar, sizeof(T));
}
template <typename T> T Load(void *value, std::size_t offset) {
  T scalar{}; std::memcpy(&scalar, static_cast<std::byte *>(value) + offset, sizeof(T)); return scalar;
}
void Key(void *value, const char *key) {
  const auto length = std::strlen(key);
  assert(length < 16);
  std::memcpy(value, key, length + 1);
  Store(value, 0x10, static_cast<std::uint64_t>(length));
  Store(value, 0x18, std::uint64_t{15});
}

struct Fixture {
  std::array<std::byte, 0x720> combat{};
  std::array<std::array<std::byte, 0x1D0>, 2> characters{};
  std::array<std::array<std::byte, 0x160>, 2> extensions{};
  std::array<std::array<std::byte, 0x100>, 2> links{};
  std::array<std::array<std::byte, 0x150>, 2> regiments{};
  std::array<std::array<std::byte, 0x60>, 2> entries{};
  std::array<std::array<std::byte, 0x18>, 2> hard_owners{};
  std::array<std::array<std::int32_t, 2>, 2> traits{{{1,2},{1,2}}};
  std::array<std::byte, 0x80> trait_database{};
  std::array<std::array<std::byte, 0x40>, 2> trait_definitions{};
  std::array<std::uintptr_t, 2> trait_definition_pointers{};
  std::array<std::byte, 0x40> reason{};
  std::array<std::byte, 0xB8> death{};
  std::array<std::byte,0x18> artifact{};
  std::array<std::int32_t,2> kills{};
  std::array<std::int64_t,2> track_values{1000,2500};
  std::array<std::byte, 0x4E20> manager{};
  std::array<std::byte, 0x30> queued_command{};
  std::array<std::byte, 0x40> node{};
  std::array<std::array<std::uint64_t, 2>, 2> candidate_scopes{{{4,101},{4,201}}};
  std::array<std::byte, 0x10> candidates{};
  std::array<std::byte, 0x10> date{};
  std::uintptr_t date_slot = 0;
  std::int64_t death_date = 53'146'872;
  CombatPhaseEventTraceCapturePlanV1 plan{};
  Fixture() {
    plan.module_base = 0x140000000;
    plan.managed_daily_sequence_token = 17;
    plan.combat_id = 0x01000002;
    plan.combat = reinterpret_cast<std::uintptr_t>(combat.data());
    Store(combat, 8, plan.combat_id);
    Store(combat, 0x6B4, std::int32_t{26});
    date_slot = reinterpret_cast<std::uintptr_t>(date.data());
    plan.current_date_slot = reinterpret_cast<std::uintptr_t>(&date_slot);
    plan.expected_current_date_object = date_slot;
    Store(date, 8, std::int32_t{53'146'848});
    plan.loaded_event_row_objects_available = true;
    plan.character_count = plan.regiment_count = 2;
    for (std::size_t i = 0; i < 2; ++i) {
      const auto id = static_cast<std::int32_t>(101 + i * 100);
      const auto rid = static_cast<std::int32_t>(31 + i * 10);
      plan.characters[i] = {id, reinterpret_cast<std::uintptr_t>(characters[i].data())};
      plan.regiments[i] = {rid, reinterpret_cast<std::uintptr_t>(regiments[i].data())};
      Store(characters[i], 0x18, id);
      Store(characters[i], 0xE8, std::int32_t{5});
      Store(characters[i], 0x1A8, reinterpret_cast<std::uintptr_t>(extensions[i].data()));
      Store(extensions[i],0xE0,reinterpret_cast<std::uintptr_t>(kills.data()));
      Store(extensions[i],0xE8,std::int32_t(2));Store(extensions[i],0xEC,std::int32_t(0));
      Store(characters[i],0x138,reinterpret_cast<std::uintptr_t>(track_values.data()));Store(characters[i],0x144,std::int32_t(2));
      Store(characters[i], 0x1B0, reinterpret_cast<std::uintptr_t>(links[i].data()));
      Store(characters[i], 0xF0, reinterpret_cast<std::uintptr_t>(traits[i].data()));
      Store(characters[i], 0xFC, std::int32_t{2});
      Store(links[i], 0xF8, rid);
      Store(regiments[i], 0x10, rid);
      Store(regiments[i], 0x140, static_cast<std::int32_t>(11 + i));
      Store(regiments[i], 0x148, id);
      Store(entries[i], 8, rid);
      Store(entries[i], 0x10, std::int64_t{100'000});
      Store(entries[i], 0x18, std::int64_t{100'000});
      Store(entries[i], 0x40, std::int64_t{200'000});
      Store(entries[i], 0x48, std::int64_t{100'000});
      const auto side = plan.combat + (i == 0 ? 0x20 : 0x368);
      plan.sides[i] = side;
      Store(reinterpret_cast<void *>(side), 0xB8, plan.combat);
      Store(reinterpret_cast<void *>(side), 0x40, reinterpret_cast<std::uintptr_t>(entries[i].data()));
      Store(reinterpret_cast<void *>(side), 0x48, std::int32_t{1});
      Store(reinterpret_cast<void *>(side), 0x4C, std::int32_t{1});
      Store(reinterpret_cast<void *>(side), 0x98, std::int64_t{100'000});
      Store(hard_owners[i], 8, id);
      Store(reinterpret_cast<void *>(side), 0x58, reinterpret_cast<std::uintptr_t>(hard_owners[i].data()));
      Store(reinterpret_cast<void *>(side), 0x60, std::int32_t{1});
      Store(reinterpret_cast<void *>(side), 0x64, std::int32_t{1});
      trait_definition_pointers[i] = reinterpret_cast<std::uintptr_t>(trait_definitions[i].data());
      Store(trait_definitions[i], 0x10, static_cast<std::int32_t>(i + 1));
      Key(trait_definitions[i].data() + 0x18, i == 0 ? "brave" : "wounded_1");
    }
    Store(trait_database, 0x68, reinterpret_cast<std::uintptr_t>(trait_definition_pointers.data()));
    Store(trait_database, 0x74, std::int32_t{2});
    Store(node, 0, plan.module_base + 0x4468B28);
    Store(node, 0x38, std::uint32_t{9});
    Key(reason.data() + 0x18, "death_battle");
    Store(candidates, 0, reinterpret_cast<std::uintptr_t>(candidate_scopes.data()));
    Store(candidates, 8, std::int32_t{2});
    Store(candidates, 12, std::int32_t{2});
    Store(artifact,0x10,std::int32_t(51));
  }
};
Fixture *g_fixture = nullptr;
std::string g_offline_fixture_json;

std::uintptr_t Queue(void *header, const void *command) {
  std::memcpy(g_fixture->queued_command.data(), command, 0x30);
  Store(header, 12, Load<std::int32_t>(header, 12) + 1);
  return 0x12345678;
}
void Request(void *manager, void *victim, void *reason, void *date, void *killer, void *artifact) {
  std::array<std::byte, 0x30> command{};
  Store(command, 8, victim); Store(command, 0x10, reason);
  Store(command, 0x18, Load<std::int64_t>(date, 0));
  Store(command, 0x20, killer); Store(command, 0x28, artifact);
  assert(ScopedDeathEnqueue(static_cast<std::byte *>(manager) + 0x4E08,
                            command.data()) == 0x12345678);
}
void Commit(void *, void *victim, void *reason, void *date, void *killer, void *artifact) {
  auto &fixture = *g_fixture;
  Store(fixture.death, 4, Load<std::int64_t>(date, 0));
  Store(fixture.death, 0x10, reason);
  Store(fixture.death, 0x18, Load<std::int32_t>(killer, 0x18));
  Store(fixture.death, 0x1C, artifact?Load<std::int32_t>(artifact,0x10):std::int32_t{-1});
  fixture.kills[0]=Load<std::int32_t>(victim,0x18);Store(fixture.extensions[1],0xEC,std::int32_t(1));
  Store(victim, 0x1C8, reinterpret_cast<std::uintptr_t>(fixture.death.data()));
  Store(victim, 0x1B0, std::uintptr_t{0});
  Store(reinterpret_cast<void *>(fixture.plan.sides[0]), 0x4C, std::int32_t{0});
  Store(fixture.regiments[0], 0x10, std::int32_t{31 + 0x01000000});
}
std::uintptr_t Casualty(void *side, std::int64_t damage, void *) {
  const auto index = reinterpret_cast<std::uintptr_t>(side) == g_fixture->plan.sides[0] ? 0 : 1;
  Store(g_fixture->entries[index], 0x18, std::int64_t{100'000} - damage);
  Store(g_fixture->entries[index], 0x20, damage / 2);
  Store(g_fixture->hard_owners[index], 0x10, damage / 2);
  return 0xABCDEF;
}

bool JournalCase() {
  auto fixture = std::make_unique<Fixture>(); g_fixture = fixture.get();
  auto chain = std::make_unique<CombatScopedChainV1>();
  assert(BindCombatScopedOriginalsForOfflineFixtureV1(&Request, &Commit, &Queue, &Casualty));
  assert(ArmCombatScopedChainV1(*chain, fixture->plan, 101, 201, 11,
                              reinterpret_cast<std::uintptr_t>(fixture->trait_database.data())));
  assert(!BindCombatScopedOriginalsForOfflineFixtureV1(&Request, &Commit, &Queue, &Casualty));
  Store(fixture->date, 8, std::int32_t{53'146'872});
  Store(fixture->combat, 0x6B4, std::int32_t{27});
  ObserveCombatScopedPhaseV1(CombatPhaseEventTraceBoundaryV1::before_side0_phase_fire, 0);
  const auto root = EnterCombatScopedEffectV1(fixture->node.data(), 0, 11, 0);
  const auto no_rng_mutation = EnterCombatScopedEffectV1(fixture->node.data(), 0, 11, 1);
  Store(fixture->extensions[1], 0x130, std::int64_t{150'000});
  Store(fixture->extensions[1], 0x138, std::int64_t{150'000});
  ReturnCombatScopedEffectV1(no_rng_mutation, fixture->node.data(), 0, 11, 1);
  ObserveCombatScopedSelectorV1(true, 0, 11, fixture->candidates.data());
  ObserveCombatScopedSelectorV1(false, 0, 11, fixture->candidates.data(), 1);
  ScopedDeathRequest(fixture->manager.data(), fixture->characters[0].data(),
                     fixture->reason.data(), &fixture->death_date,
                     fixture->characters[1].data(), fixture->artifact.data());
  ReturnCombatScopedEffectV1(root, fixture->node.data(), 0, 11, 0);
  ObserveCombatScopedPhaseV1(CombatPhaseEventTraceBoundaryV1::after_side0_phase_fire, 0);
  assert(ScopedCasualty(reinterpret_cast<void *>(fixture->plan.sides[0]), 4'000,
                       reinterpret_cast<void *>(fixture->plan.sides[1])) == 0xABCDEF);
  assert(ScopedCasualty(reinterpret_cast<void *>(fixture->plan.sides[1]), 6'000,
                       reinterpret_cast<void *>(fixture->plan.sides[0])) == 0xABCDEF);
  ScopedDeathCommit(fixture->manager.data(), fixture->characters[0].data(),
                    fixture->reason.data(), &fixture->death_date,
                    fixture->characters[1].data(), fixture->artifact.data());
  FinishCombatScopedChainV1(*chain);
  assert(chain->failure_flags.load() == 0);
  assert(chain->count.load() == 20);
  const auto &last = chain->records[chain->count.load() - 1];
  assert(last.boundary == CombatScopedChainBoundaryV1::next_paused);
  assert(last.characters[0].death_marker_present && last.characters[0].death_details_read);
  assert(last.characters[0].death_killer_character_id == 201);
  assert(last.characters[0].death_artifact_id==51&&last.characters[1].kills_read&&last.characters[1].kill_count==1&&last.characters[1].kill_character_ids[0]==101);
  assert(last.characters[0].trait_tracks_read&&last.characters[0].trait_track_raw_count==2&&last.characters[0].trait_track_raw_values[1]==2500);
  assert(last.characters[0].death_date_raw == fixture->death_date);
  assert(last.characters[0].current_regiment_id == -1);
  assert(!last.scoped_regiment_in_side[0]);
  assert(last.characters[1].prestige_currency_raw == 150'000);
  assert(last.characters[1].prestige_experience_raw == 150'000);
  const auto json = SerializeCombatScopedChainV1(*chain);
  g_offline_fixture_json = json;
  assert(json.find("death_battle") != std::string::npos);
  assert(json.find("death_enqueue_return") != std::string::npos);
  assert(json.find("effect_enter") != std::string::npos);
  assert(json.find("\"global_mutable_bundle_complete\":false") != std::string::npos);
  assert(json.find("\"live_scoped_write_set_verified\":false") != std::string::npos);
  assert(json.find("\"character_id\":201,\"character_full_identity_matches\":true") != std::string::npos);
  return true;
}

bool SerializationFailureDiagnostics() {
  auto chain=std::make_unique<CombatScopedChainV1>();chain->count=1;
  chain->failure_flags=32;auto &r=chain->records[0];r.sequence=17;r.invocation=9;
  CombatScopedWireDiagnosticV1 d{};
  const auto unchanged=SerializeCombatScopedChainV1(*chain);
  assert(SerializeCombatScopedChainV1(*chain,&d)==unchanged && std::string(d.failure_gate)=="none");
  const auto expect=[&](const char *field,auto mutate,auto restore){
    mutate();assert(SerializeCombatScopedChainV1(*chain,&d).empty());
    assert(std::string(d.field)==field && chain->failure_flags==32);
    restore();assert(!SerializeCombatScopedChainV1(*chain).empty());
  };
  expect("trait_definition_count",[&]{chain->trait_definition_count=8193;},[&]{chain->trait_definition_count=0;});
  expect("trait_definition.key",[&]{chain->trait_definition_count=1;chain->trait_definitions[0].key.size=128;},[&]{chain->trait_definition_count=0;chain->trait_definitions[0].key.size=0;});
  expect("trait_definition.key",[&]{chain->trait_definition_count=1;chain->trait_definitions[0].key.size=1;chain->trait_definitions[0].key.bytes[0]=' ';},[&]{chain->trait_definition_count=0;chain->trait_definitions[0].key.size=0;});
  expect("selector_candidate_count",[&]{r.selector_candidate_count=257;},[&]{r.selector_candidate_count=0;});
  expect("variable_key",[&]{r.variable_key.size=128;},[&]{r.variable_key.size=0;});
  expect("variable_list_count",[&]{r.variable_list_count=129;},[&]{r.variable_list_count=0;});
  expect("character.trait_count",[&]{r.characters[1].trait_count=129;},[&]{r.characters[1].trait_count=0;});
  expect("character.death_reason_key",[&]{r.characters[0].death_reason_key.size=1;r.characters[0].death_reason_key.bytes[0]='"';},[&]{r.characters[0].death_reason_key.size=0;});
  expect("character.trait_track_raw_count",[&]{r.characters[0].trait_track_raw_count=257;},[&]{r.characters[0].trait_track_raw_count=0;});
  expect("character.kill_count",[&]{r.characters[0].kill_count=513;},[&]{r.characters[0].kill_count=0;});
  expect("battle_event_snapshot_index",[&]{r.battle_event_snapshot_index=8;},[&]{r.battle_event_snapshot_index=-1;});
  expect("battle_event_snapshot.count",[&]{r.battle_event_snapshot_index=0;chain->battle_event_snapshots[0].count=257;},[&]{r.battle_event_snapshot_index=-1;chain->battle_event_snapshots[0].count=0;});
  expect("battle_event.key",[&]{r.battle_event_snapshot_index=0;auto &s=chain->battle_event_snapshots[0];s.count=1;s.rows[0].stable_key_size=1;s.rows[0].stable_key[0]='\\';},[&]{r.battle_event_snapshot_index=-1;chain->battle_event_snapshots[0].count=0;});
  expect("entry_snapshot_index",[&]{r.entry_snapshot_index=16;},[&]{r.entry_snapshot_index=-1;});
  expect("entry_snapshot.entry_count",[&]{r.entry_snapshot_index=0;chain->entry_snapshots[0].entry_count[1]=2049;},[&]{r.entry_snapshot_index=-1;chain->entry_snapshots[0].entry_count[1]=0;});
  expect("entry_snapshot.owner_hard_count",[&]{r.entry_snapshot_index=0;auto &s=chain->entry_snapshots[0];s.owner_hard_count[0]=static_cast<std::uint32_t>(s.owner_hard[0].size()+1);},[&]{r.entry_snapshot_index=-1;chain->entry_snapshots[0].owner_hard_count[0]=0;});
  chain->count=256;chain->entry_snapshots[0].entry_count={200,200};
  for(auto &row:chain->records)row.entry_snapshot_index=0;
  assert(SerializeCombatScopedChainV1(*chain,&d).empty() && std::string(d.failure_gate)=="scoped_wire_cap");
  assert(d.observed>16*1024*1024 && chain->failure_flags==32);
  std::cout<<"serialization diagnostics: original good bytes unchanged,16 key/count/index failures plus original16MiB cap attributed; flags preserved; offline only\n";
  return true;
}

bool GuardCases() {
  auto fixture = std::make_unique<Fixture>(); g_fixture = fixture.get();
  auto chain = std::make_unique<CombatScopedChainV1>();
  const auto database = reinterpret_cast<std::uintptr_t>(fixture->trait_database.data());
  assert(!ArmCombatScopedChainV1(*chain, fixture->plan, 101, 101, 11, database));
  assert(!ArmCombatScopedChainV1(*chain, fixture->plan, 101, 201, 13, database));
  assert(ArmCombatScopedChainV1(*chain, fixture->plan, 101, 201, 11, database));
  assert(EnterCombatScopedEffectV1(fixture->node.data(), 0, 10, 0) == 0);
  const auto before = chain->count.load();
  Store(fixture->characters[0], 0x18, std::int32_t{101 + 0x01000000});
  ObserveCombatScopedPhaseV1(CombatPhaseEventTraceBoundaryV1::before_side0_phase_fire, 0);
  assert(chain->count.load() == before + 1);
  assert((chain->failure_flags.load() & scoped_chain_failure_identity) != 0);
  assert(!chain->records[before].characters[0].identity_matches);
  CancelCombatScopedChainV1(*chain);
  chain = std::make_unique<CombatScopedChainV1>();
  Store(fixture->characters[0], 0x18, std::int32_t{101});
  assert(ArmCombatScopedChainV1(*chain, fixture->plan, 101, 201, 11, database));
  Store(fixture->date, 8, std::int32_t{53'146'896});
  FinishCombatScopedChainV1(*chain);
  assert((chain->failure_flags.load() & scoped_chain_failure_thread_or_date) != 0);
  assert(SerializeCombatScopedChainV1(*chain).find("\"failure_flags\":32") != std::string::npos);
  chain = std::make_unique<CombatScopedChainV1>();
  Store(fixture->date, 8, std::int32_t{53'146'848});
  Store(fixture->characters[0], 0xFC, std::int32_t{129});
  assert(!ArmCombatScopedChainV1(*chain, fixture->plan, 101, 201, 11, database));
  assert((chain->failure_flags.load() & scoped_chain_failure_capacity) != 0);
  CancelCombatScopedChainV1(*chain);
  CombatScopedDetoursV1 detours{};
  assert(!InstallCombatScopedDetoursV1(detours, 0x140000000, false, true));
  assert(!InstallCombatScopedDetoursV1(detours, 0x140000000, true, false));
  assert(UninstallCombatScopedDetoursV1(detours));
  return true;
}

// Every executable byte in this case belongs to this test process. The exact
std::array<std::array<std::uint64_t,2>,8> g_filter_scopes{};
std::array<std::byte,0x60> g_source_predicate{},g_shared_predicate{};
std::uint32_t g_materializer_calls=0,g_filter_calls=0,g_shared_calls=0,g_source_calls=0;
std::array<std::byte,0x48> g_list_row{};
std::array<std::array<std::uint64_t,2>,2> g_list_values{};
std::array<std::int32_t,2> g_list_expirations{};
std::uintptr_t Materialize(void *,void *header,void *) {
  ++g_materializer_calls;auto n=Load<std::int32_t>(header,12);
  g_filter_scopes[n++]={4,101};g_filter_scopes[n++]={4,201};g_filter_scopes[n++]={4,101};Store(header,12,n);return 0xA012;
}
std::uintptr_t Evaluate(void *predicate,void *,std::uint8_t mode) {
  assert(mode==0);if(predicate==g_shared_predicate.data())return ++g_shared_calls==1?0xAB00:0xAB01;
  assert(predicate==g_source_predicate.data());return ++g_source_calls==1?0xCD00:0xCD01;
}
std::uintptr_t Filter(void *self,void *source,void *shared,void *context,void *header) {
  ++g_filter_calls;const auto prefix=Load<std::int32_t>(header,12);
  assert(ScopedSelectorMaterializer(self,header,context)==0xA012);
  if(Load<std::int32_t>(source,0x5C)==0&&Load<std::int32_t>(shared,0x5C)==0)return 0xF123;
  for(auto i=prefix;i<Load<std::int32_t>(header,12);){std::array<std::byte,0x28> eval{};Store(eval,0,reinterpret_cast<std::uintptr_t>(&g_filter_scopes[i]));
    const bool okay=(ScopedSelectorPredicate(shared,eval.data(),0)&0xFF)!=0&&
       (ScopedSelectorPredicate(source,eval.data(),0)&0xFF)!=0;
    if(okay)++i;else{const auto last=Load<std::int32_t>(header,12)-1;g_filter_scopes[i]=g_filter_scopes[last];Store(header,12,last);}
  }
  return 0xF123;
}
std::uintptr_t ListWriter(void *owner,std::int32_t key,const void *value,std::int32_t expiry) {
  Store(owner,0x30,reinterpret_cast<std::uintptr_t>(g_list_row.data()));Store(owner,0x3C,std::int32_t(1));
  Store(g_list_row,8,key);Store(g_list_row,0x10,reinterpret_cast<std::uintptr_t>(g_list_values.data()));Store(g_list_row,0x18,std::int32_t(2));Store(g_list_row,0x1C,std::int32_t(1));
  Store(g_list_row,0x28,reinterpret_cast<std::uintptr_t>(g_list_expirations.data()));Store(g_list_row,0x34,std::int32_t(1));Store(g_list_row,0x40,std::int32_t(10));
  std::memcpy(g_list_values[0].data(),value,16);g_list_expirations[0]=expiry==-1?-1:10+expiry;return 0xC110;
}
std::string g_offline_selector_fixture_json;
bool SelectorAndListCase(){
  auto f=std::make_unique<Fixture>();auto chain=std::make_unique<CombatScopedChainV1>();
  std::array<std::byte,0x40> table{};std::array<std::byte,0x20> name{};
  const char *list_key="slain_side_knights";Store(name,0,reinterpret_cast<std::uintptr_t>(list_key));Store(name,0x10,std::uint64_t(18));Store(name,0x18,std::uint64_t(18));
  Store(table,0,std::uint8_t(1));Store(table,0x30,reinterpret_cast<std::uintptr_t>(name.data()));Store(table,0x3C,std::int32_t(1));
  std::array<std::array<std::byte,0x60>,3> input_rows{f->entries[0],f->entries[1],f->entries[0]};
  Store(reinterpret_cast<void*>(f->plan.sides[0]),0x40,reinterpret_cast<std::uintptr_t>(input_rows.data()));
  Store(reinterpret_cast<void*>(f->plan.sides[0]),0x48,std::int32_t(3));Store(reinterpret_cast<void*>(f->plan.sides[0]),0x4C,std::int32_t(3));
  assert(BindCombatScopedSelectorOriginalsForOfflineFixtureV1(Materialize,Filter,Evaluate,ListWriter));
  assert(ArmCombatScopedChainV1(*chain,f->plan,101,201,11,reinterpret_cast<std::uintptr_t>(f->trait_database.data()),reinterpret_cast<std::uintptr_t>(table.data())));
  std::array<std::uint64_t,2> combat_scope{11,static_cast<std::uint64_t>(f->plan.combat_id)};
  std::array<std::byte,0x28> context{};Store(context,0,reinterpret_cast<std::uintptr_t>(combat_scope.data()));
  std::array<std::byte,0x10> header{};Store(header,0,reinterpret_cast<std::uintptr_t>(g_filter_scopes.data()));Store(header,8,std::int32_t(8));Store(header,12,std::int32_t(1));g_filter_scopes[0]={4,201};
  Store(g_source_predicate,0x5C,std::int32_t(1));Store(g_shared_predicate,0x5C,std::int32_t(1));
  const auto root=EnterCombatScopedEffectV1(f->node.data(),1,11,0,context.data());
  assert(ScopedSelectorFilter(nullptr,g_source_predicate.data(),g_shared_predicate.data(),context.data(),header.data())==0xF123);
  assert(g_materializer_calls==1&&g_filter_calls==1&&g_shared_calls==3&&g_source_calls==2&&Load<std::int32_t>(header.data(),12)==2);
  assert(g_filter_scopes[0][1]==201&&g_filter_scopes[1][1]==201);
  std::array<std::byte,0x120> list_node{};Store(list_node,0,f->plan.module_base+0x44D3760);Store(list_node,0x38,std::uint32_t(22));
  std::array<std::byte,0x50> owner{};std::array<std::uint64_t,2> victim{4,101};
  const auto child=EnterCombatScopedEffectV1(list_node.data(),1,11,1,context.data());
  ObserveCombatScopedOriginalVariableOwnerV1(combat_scope.data(),owner.data());
  assert(ScopedCombatListWriter(owner.data(),0x01000000,victim.data(),1)==0xC110);
  ReturnCombatScopedEffectV1(child,list_node.data(),1,11,1);ReturnCombatScopedEffectV1(root,f->node.data(),1,11,0);
  std::uint32_t predicates=0,list_rows=0;bool swapped=false;
  for(std::uint32_t i=0;i<chain->count.load();++i){const auto &r=chain->records[i];
    if(r.boundary==CombatScopedChainBoundaryV1::predicate_return){++predicates;assert(r.original_predicate_boolean_read&&r.selector_current_index==1&&r.selector_prefix_count==1&&r.selector_source_side_index==0);if(r.selector_candidate_count==2&&r.selector_candidates[1].character_id==201)swapped=true;}
    if(r.boundary==CombatScopedChainBoundaryV1::list_write_return){++list_rows;assert(r.variable_list_read&&r.variable_list_present&&r.variable_list_count==1&&r.variable_list_values[0]==victim&&r.variable_list_expirations[0]==11&&r.selector_source_combat_identity_matches);}
  }
  assert(predicates==5&&swapped&&list_rows==1);
  // Native zero predicate counts produce no calls and preserve the prefix.
  Store(g_source_predicate,0x5C,std::int32_t(0));Store(g_shared_predicate,0x5C,std::int32_t(0));Store(header,12,std::int32_t(1));
  const auto second=EnterCombatScopedEffectV1(f->node.data(),1,11,0,context.data());
  assert(ScopedSelectorFilter(nullptr,g_source_predicate.data(),g_shared_predicate.data(),context.data(),header.data())==0xF123);
  ReturnCombatScopedEffectV1(second,f->node.data(),1,11,0);assert(g_shared_calls==3&&g_source_calls==2&&Load<std::int32_t>(header.data(),12)==4);
  FinishCombatScopedChainV1(*chain);assert(chain->failure_flags.load()==0);
  g_offline_selector_fixture_json=SerializeCombatScopedChainV1(*chain);assert(!g_offline_selector_fixture_json.empty());
  return true;
}

// Every executable byte in this case belongs to this test process. The exact
// prologues are followed by fixture epilogues, never by CK3 executable code.
bool RelocationAndRollbackCase() {
  constexpr std::size_t module_size = 0x6000000;
  auto *module = static_cast<std::uint8_t *>(VirtualAlloc(
      nullptr, module_size, MEM_RESERVE, PAGE_NOACCESS));
  assert(module != nullptr);
  const std::array<std::size_t, 8> pages{0x264B000, 0x2654000, 0x23CE000, 0x570E000,0x19DD000,0x19F4000,0x334C000,0x3346000};
  for (const auto page : pages) {
    assert(VirtualAlloc(module + page, 0x1000, MEM_COMMIT, PAGE_READWRITE) == module + page);
  }
  constexpr std::array<std::uint8_t, 18> request{
      0x48,0x83,0xEC,0x68,0x48,0x8B,0x05,0x5D,0x24,0x0C,0x03,
      0x80,0xB8,0xC1,0,0,0,0};
  constexpr std::array<std::uint8_t, 15> commit{
      0x48,0x89,0x5C,0x24,0x08,0x4C,0x89,0x4C,0x24,0x20,
      0x4C,0x89,0x44,0x24,0x18};
  constexpr std::array<std::uint8_t, 17> enqueue{
      0x48,0x89,0x5C,0x24,0x18,0x55,0x56,0x41,0x56,0x48,0x83,0xEC,0x20,
      0x48,0x63,0x41,0x0C};
  constexpr std::array<std::uint8_t, 20> casualty{
      0x4C,0x89,0x44,0x24,0x18,0x56,0x57,0x41,0x55,0x48,0x83,0xEC,0x60,
      0x48,0x8B,0x81,0x98,0,0,0};
  constexpr std::array<std::uint8_t,15> materializer{0x48,0x89,0x5C,0x24,0x18,0x48,0x89,0x74,0x24,0x20,0x57,0x48,0x83,0xEC,0x30};
  constexpr std::array<std::uint8_t,15> filter{0x48,0x89,0x6C,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x48,0x89,0x7C,0x24,0x20};
  constexpr std::array<std::uint8_t,15> predicate{0x48,0x8B,0xC4,0x48,0x89,0x58,0x08,0x48,0x89,0x70,0x18,0x48,0x89,0x78,0x20};
  constexpr std::array<std::uint8_t,14> list{0x48,0x89,0x5C,0x24,0x08,0x48,0x89,0x74,0x24,0x18,0x89,0x54,0x24,0x10};
  // Preserve the CMP flags, store all six ABI arguments, then restore RSP.
  constexpr std::array<std::uint8_t, 51> request_tail{
      0x48,0x89,0x01,0x0F,0x94,0x81,0xC0,0,0,0,
      0x48,0x89,0x51,0x08,0x4C,0x89,0x41,0x10,0x4C,0x89,0x49,0x18,
      0x48,0x8B,0x84,0x24,0x90,0,0,0,0x48,0x89,0x41,0x20,
      0x48,0x8B,0x84,0x24,0x98,0,0,0,0x48,0x89,0x41,0x28,
      0x48,0x83,0xC4,0x68,0xC3};
  constexpr std::array<std::uint8_t, 6> commit_tail{0x48,0x8B,0x5C,0x24,0x08,0xC3};
  constexpr std::array<std::uint8_t, 24> enqueue_tail{
      0x48,0x83,0xC4,0x20,0x41,0x5E,0x5E,0x5D,0x48,0x8B,0x5C,0x24,0x18,
      0x48,0xB8,0x78,0x56,0x34,0x12,0,0,0,0,0xC3};
  constexpr std::array<std::uint8_t, 19> casualty_tail{
      0x48,0x83,0xC4,0x60,0x41,0x5D,0x5F,0x5E,
      0x48,0xB8,0xEF,0xCD,0xAB,0,0,0,0,0,0xC3};
  const std::array<std::size_t, 4> rvas{0x264BC00, 0x264BCB0, 0x2654960, 0x23CE080};
  const std::array<const std::uint8_t *, 4> anchors{
      request.data(), commit.data(), enqueue.data(), casualty.data()};
  const std::array<std::size_t, 4> lengths{
      request.size(), commit.size(), enqueue.size(), casualty.size()};
  const std::array<const std::uint8_t *, 4> tails{
      request_tail.data(), commit_tail.data(), enqueue_tail.data(), casualty_tail.data()};
  const std::array<std::size_t, 4> tail_lengths{
      request_tail.size(), commit_tail.size(), enqueue_tail.size(), casualty_tail.size()};
  for (std::size_t i = 0; i < rvas.size(); ++i) {
    std::memcpy(module + rvas[i], anchors[i], lengths[i]);
    std::memcpy(module + rvas[i] + lengths[i], tails[i], tail_lengths[i]);
  }
  const std::array<std::size_t,4> extra_rvas{0x19DD670,0x19F4760,0x334C600,0x33463D0};
  const std::array<const std::uint8_t*,4> extra_anchors{materializer.data(),filter.data(),predicate.data(),list.data()};
  const std::array<std::size_t,4> extra_lengths{materializer.size(),filter.size(),predicate.size(),list.size()};
  for(std::size_t i=0;i<4;++i)std::memcpy(module+extra_rvas[i],extra_anchors[i],extra_lengths[i]);
  std::array<std::byte, 0xD0> global_object{};
  Store(module + 0x570E068, 0, reinterpret_cast<std::uintptr_t>(global_object.data()));
  for (std::size_t i = 0; i < 3; ++i) {
    DWORD old = 0;
    assert(VirtualProtect(module + pages[i], 0x1000, PAGE_EXECUTE_READ, &old));
    assert(FlushInstructionCache(GetCurrentProcess(), module + pages[i], 0x1000));
  }
  CombatScopedDetoursV1 detours{};
  assert(InstallCombatScopedDetoursV1(detours, reinterpret_cast<std::uintptr_t>(module), true, true));
  std::array<std::byte, 0xD0> receiver{};
  std::array<std::byte, 0x10> queue_header{};
  std::array<std::byte, 0xA0> side{};
  const auto call_request = reinterpret_cast<CombatScopedDeathOriginalV1>(module + rvas[0]);
  const auto call_commit = reinterpret_cast<CombatScopedDeathOriginalV1>(module + rvas[1]);
  const auto call_queue = reinterpret_cast<CombatScopedQueueOriginalV1>(module + rvas[2]);
  const auto call_casualty = reinterpret_cast<CombatScopedCasualtyOriginalV1>(module + rvas[3]);
  auto *const victim = receiver.data() + 0x40;
  auto *const reason = receiver.data() + 0x48;
  auto *const date = receiver.data() + 0x50;
  auto *const killer = receiver.data() + 0x58;
  auto *const artifact = receiver.data() + 0x60;
  call_request(receiver.data(), victim, reason, date, killer, artifact);
  assert(Load<std::uintptr_t>(receiver.data(), 0) == reinterpret_cast<std::uintptr_t>(global_object.data()));
  assert(Load<std::uint8_t>(receiver.data(), 0xC0) == 1);
  assert(Load<void *>(receiver.data(), 8) == victim);
  assert(Load<void *>(receiver.data(), 0x10) == reason);
  assert(Load<void *>(receiver.data(), 0x18) == date);
  assert(Load<void *>(receiver.data(), 0x20) == killer);
  assert(Load<void *>(receiver.data(), 0x28) == artifact);
  Store(global_object, 0xC1, std::uint8_t{1});
  call_request(receiver.data(), victim, reason, date, killer, artifact);
  assert(Load<std::uint8_t>(receiver.data(), 0xC0) == 0);
  call_commit(receiver.data(), victim, reason, date, killer, artifact);
  assert(call_queue(queue_header.data(), receiver.data()) == 0x12345678);
  assert(call_casualty(side.data(), 2, receiver.data()) == 0xABCDEF);
  assert(UninstallCombatScopedDetoursV1(detours));
  for(std::size_t i=0;i<4;++i)assert(std::memcmp(module+extra_rvas[i],extra_anchors[i],extra_lengths[i])==0);
  for (std::size_t i = 0; i < rvas.size(); ++i) {
    assert(!detours.hooks[i].installed && detours.hooks[i].trampoline != nullptr);
    MEMORY_BASIC_INFORMATION resident{};
    assert(VirtualQuery(detours.hooks[i].trampoline,&resident,sizeof(resident))==sizeof(resident));
    assert(resident.State==MEM_COMMIT&&resident.Protect==PAGE_EXECUTE_READ);
    assert(std::memcmp(module + rvas[i], anchors[i], lengths[i]) == 0);
  }
  // The fourth exact-anchor rejection must roll back the first three patches.
  DWORD old = 0;
  assert(VirtualProtect(module + pages[2], 0x1000, PAGE_EXECUTE_READWRITE, &old));
  module[rvas[3]] ^= 1;
  assert(VirtualProtect(module + pages[2], 0x1000, old, &old));
  CombatScopedDetoursV1 rejected{};
  assert(!InstallCombatScopedDetoursV1(rejected, reinterpret_cast<std::uintptr_t>(module), true, true));
  assert((rejected.failure_flags & scoped_chain_failure_detour) != 0);
  for (std::size_t i = 0; i < rvas.size(); ++i) {
    assert(!rejected.hooks[i].installed);
    assert((rejected.hooks[i].trampoline != nullptr) == (i < 3));
    if (i != 3) assert(std::memcmp(module + rvas[i], anchors[i], lengths[i]) == 0);
  }
  assert(VirtualFree(module, 0, MEM_RELEASE));
  return true;
}
} // namespace

int main(int argc, char **argv) {
  assert(JournalCase());
  assert(SelectorAndListCase());
  assert(GuardCases());
  assert(SerializationFailureDiagnostics());
  assert(RelocationAndRollbackCase());
  if (argc == 2 && std::string(argv[1]) == "--emit-offline-fixture") {
    std::cout << "{\"kind\":\"OFFLINE_FIXTURE_NOT_NATIVE_GAME_TRUTH\",\"scoped_transition_chain\":"
              << g_offline_fixture_json << ",\"selector_list_fixture\":"<<g_offline_selector_fixture_json<<"}\n";
  } else {
    assert(argc == 1);
    std::cout << "scoped journal / no-draw effect / queue RAX / death detach / traits / prestige / full-ID / +24 / RIP relocation / six ABI arguments / CMP flags / four-hook rollback PASS\n";
  }
  return 0;
}
