#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/ck3_12003_current_daily_assault_loss.hpp"
#include "xar_bridge/army_strength_v1_serializer.hpp"
#include <array>
#include <bit>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <vector>

namespace {
using namespace xar;
void Check(bool value, const char *message) { if (!value) throw std::runtime_error(message); }
struct Memory {
  struct Region { std::unique_ptr<std::byte[]> bytes; std::size_t size; };
  std::vector<Region> regions;
  void *Allocate(std::size_t size) {
    auto bytes=std::make_unique<std::byte[]>(size); auto *address=bytes.get();
    regions.push_back({std::move(bytes),size}); return address;
  }
  template<class T> void Put(void *object,std::size_t offset,T value) {
    std::memcpy(static_cast<std::byte *>(object)+offset,&value,sizeof value);
  }
  static bool Read(void *context,const void *address,void *output,std::size_t size) noexcept {
    const auto begin=reinterpret_cast<std::uintptr_t>(address);
    for (const auto &region:static_cast<Memory *>(context)->regions) {
      const auto base=reinterpret_cast<std::uintptr_t>(region.bytes.get());
      if (begin>=base && begin-base<=region.size && size<=region.size-(begin-base)) {
        std::memcpy(output,address,size); return true;
      }
    }
    return false;
  }
};
template<class T> T Load(const void *object,std::size_t offset) {
  T value{}; std::memcpy(&value,static_cast<const std::byte *>(object)+offset,sizeof value); return value;
}
struct Registry {
  Memory &memory; void *slot,*fallback,*store,*table;
  Registry(Memory &m,std::uint32_t capacity):memory(m),slot(m.Allocate(8)),fallback(m.Allocate(8)),store(m.Allocate(0x30)),table(m.Allocate(capacity*16)) {
    m.Put(slot,0,store); m.Put(store,0x20,table); m.Put(store,0x2C,capacity);
  }
  void Add(std::uint32_t id,void *object,std::size_t full_offset) {
    memory.Put(table,(id&0xFFFFFFU)*16+8,object); memory.Put(object,full_offset,id);
  }
};
constexpr std::uint32_t UA=0x11000001U,UB=0x11000002U,AA=0x22000001U,AB=0x22000002U;
constexpr std::uint32_t RA=0x2B000001U,RB=0x2B000002U,RP=0x2B000003U,RI=0xAB000004U;
constexpr std::uint32_t SA=0xFE000001U,SB=0xFE000002U,SC=0xFE000003U;
constexpr std::uint32_t PA=0xCC000001U,PP=0xCC000002U;
Registry *reg_registry=nullptr; void *army_a=nullptr,*army_b=nullptr,*province_current=nullptr;
std::int32_t Current(void *descriptor,std::uint8_t flags) {
  Check(flags==0,"daily-loss requires actual whole flags0 counts");
  const auto ids=Load<void *>(descriptor,0); const auto count=Load<std::int32_t>(descriptor,0xC);
  std::uint32_t sum=0;
  for (std::int32_t i=0;i<count;++i) {
    const auto raw=Load<std::uint32_t>(ids,static_cast<std::size_t>(i)*4);
    const auto index=raw&0xFFFFFFU;
    if (index>=Load<std::uint32_t>(reg_registry->store,0x2C)) continue;
    const auto object=Load<void *>(reg_registry->table,static_cast<std::size_t>(index)*16+8);
    if (object && Load<std::uint32_t>(object,0x10)==raw && Load<std::uint32_t>(object,0x14)==0x41725267U)
      sum+=std::bit_cast<std::uint32_t>(Load<std::int32_t>(object,0x38));
  }
  return std::bit_cast<std::int32_t>(sum);
}
std::int32_t Maximum(void *receiver) { return receiver==army_a?400:120; }
std::uint8_t Excluded(void *) { return 0; }
std::uint8_t Eligible(void *,void *) { return 1; }
bool Skipped(void *object) { return Load<std::uint32_t>(object,0x10)==RB; }
bool Replenish(void *,void *) { return true; }
bool Chunk(void *) { return true; }
std::int64_t *Fraction(void *,std::int64_t *out) { *out=5000; return out; }
std::int32_t Besieging(void *) { return Current(static_cast<std::byte *>(army_a)+0x38,0)*2+Current(static_cast<std::byte *>(army_b)+0x38,0); }
std::int32_t Expected(void *siege) {
  auto *province=Load<void *>(siege,0x200);
  if (Load<std::uint32_t>(province,0x85C)!=0x50726F76U) return 0;
  const auto breach=Load<std::int32_t>(siege,0x3D8);
  if (breach<1 || breach>2) return 0;
  return Besieging(province)*(breach==1?10:20)/100;
}
struct Fixture {
  Memory memory;
  Registry units{memory,3},armies{memory,3},regiments{memory,5},sieges{memory,4},persistent{memory,3};
  ck3_12002::ArmyBindings b{};
  void *state_slot=memory.Allocate(8),*state=memory.Allocate(0xA8),*data=memory.Allocate(0x2A540+0x190);
  void *manager=static_cast<std::byte *>(data)+0x2A540,*entries=memory.Allocate(5*0x40);
  void *ua=memory.Allocate(0x180),*ub=memory.Allocate(0x180),*aa=memory.Allocate(0x208),*ab=memory.Allocate(0x208);
  void *ra=memory.Allocate(0x150),*rb=memory.Allocate(0x150),*rp=memory.Allocate(0x150),*ri=memory.Allocate(0x150),*rf=memory.Allocate(0x150);
  void *defa=memory.Allocate(0x2A4),*defp=memory.Allocate(0x2A4);
  void *sa=memory.Allocate(0x3DC),*sb=memory.Allocate(0x3DC),*sc=memory.Allocate(0x3DC);
  void *province=memory.Allocate(0x900),*pa=memory.Allocate(0x150),*pp=memory.Allocate(0x150);
  void *percentage_count=memory.Allocate(4),*percentage_slot=memory.Allocate(8),*percentages=memory.Allocate(16);
  Fixture() {
    army_a=aa; army_b=ab; province_current=province; reg_registry=&regiments;
    b.enabled=true; b.current_daily_assault_loss_inputs_enabled=true;
    b.game_state_slot=static_cast<void **>(state_slot); b.unit_storage_slot=static_cast<void **>(units.slot);
    b.internal_army_storage_slot=static_cast<void **>(armies.slot); b.regiment_storage_slot=static_cast<void **>(regiments.slot);
    b.persistent_regiment_storage_slot=static_cast<void **>(persistent.slot);
    b.get_army_current_soldiers=Current; b.get_army_maximum_soldiers=Maximum;
    b.is_army_regiment_loss_writer_skipped=Skipped; b.can_regiment_replenish=Replenish;
    b.can_chunk_replenish=Chunk; b.get_regiment_monthly_replenishment_fraction=Fraction;
    auto &t=b.current_daily_assault_table_bindings;
    t.enabled=true; t.game_state_slot=state_slot; t.army_registry_slot=armies.slot; t.army_fallback_slot=armies.fallback;
    t.arrg_registry_slot=regiments.slot; t.arrg_fallback_slot=regiments.fallback;
    t.siege_registry_slot=sieges.slot; t.siege_fallback_slot=sieges.fallback; t.read_memory=Memory::Read; t.read_context=&memory;
    auto &v=b.current_province_besieging_bindings;
    v.enabled=true; v.unit_fallback_slot=static_cast<void **>(units.fallback); v.army_fallback_slot=static_cast<void **>(armies.fallback);
    v.province_fallback_slot=static_cast<void **>(memory.Allocate(8)); memory.Put(v.province_fallback_slot,0,province);
    v.siege_storage_slot=static_cast<void **>(sieges.slot); v.army_excluded=Excluded; v.army_province_eligible=Eligible;
    v.besieging_strength=Besieging; v.assault_expected_loss=Expected;
    v.casualty_percentage_count=static_cast<const std::int32_t *>(percentage_count);
    v.casualty_percentage_table_slot=static_cast<const std::int64_t **>(percentage_slot);
    memory.Put(percentage_count,0,std::int32_t{2}); memory.Put(percentage_slot,0,percentages);
    memory.Put(percentages,0,std::int64_t{1000000}); memory.Put(percentages,8,std::int64_t{2000000});
    memory.Put(state_slot,0,state); memory.Put(state,0xA0,data);
    memory.Put(manager,0x178,entries); memory.Put(manager,0x180,std::int32_t{2}); memory.Put(manager,0x184,std::int32_t{3});
    memory.Put(manager,0x188,std::uint8_t{0}); memory.Put(manager,0x18C,std::uint32_t{0x3F400000U});
    memory.Put(entries,4*0x40+4,std::uint8_t{0xA5}); // End marker is outside the scanned groups.
    units.Add(UA,ua,0x10); units.Add(UB,ub,0x10); armies.Add(AA,aa,0x10); armies.Add(AB,ab,0x10);
    memory.Put(ua,0x178,AA); memory.Put(ub,0x178,AB); memory.Put(ua,0x20,province); memory.Put(ub,0x20,province);
    memory.Put(aa,0x124,UA); memory.Put(ab,0x124,UB); memory.Put(armies.fallback,0,ab);
    for (auto pair: {std::pair{RA,ra},std::pair{RB,rb},std::pair{RP,rp},std::pair{RI,ri}}) regiments.Add(pair.first,pair.second,0x10);
    for (auto *reg:{ra,rb,rp,rf}) memory.Put(reg,0x14,std::uint32_t{0x41725267U});
    memory.Put(rf,0x10,std::uint32_t{0xFFFFFFFFU}); memory.Put(regiments.fallback,0,rf);
    memory.Put(ra,0x18,defa); memory.Put(rb,0x18,defa); memory.Put(rp,0x18,defp);
    memory.Put(defa,0x2A0,std::int32_t{0}); memory.Put(defp,0x2A0,std::int32_t{1});
    memory.Put(ra,0x38,std::int32_t{200}); memory.Put(ra,0x3C,std::int32_t{300});
    memory.Put(rb,0x38,std::int32_t{80}); memory.Put(rb,0x3C,std::int32_t{120});
    memory.Put(rp,0x38,std::int32_t{50}); memory.Put(rp,0x3C,std::int32_t{100});
    Roster(aa,0x38,{RA,RP}); Roster(ab,0x38,{RB});
    persistent.Add(PA,pa,0x10); persistent.Add(PP,pp,0x10);
    Data(ra,pa,PA,RA,100,150,2); Data(rp,pp,PP,RP,50,100,1);
    // Character skip intentionally has no DATA/persistent requirements.
    memory.Put(rb,0x28,std::int32_t{-1});
    memory.Put(province,0x10,std::int32_t{19}); memory.Put(province,0x85C,std::uint32_t{0x50726F76U});
    Roster(province,0x740,{UA,UA,UB}); memory.Put(province,0x788,SC);
    sieges.Add(SA,sa,8); sieges.Add(SB,sb,8); sieges.Add(SC,sc,8); memory.Put(sieges.fallback,0,sb);
    for (auto *siege:{sa,sb,sc}) memory.Put(siege,0x200,province);
    memory.Put(sa,0x3D8,std::int32_t{2}); memory.Put(sb,0x3D8,std::int32_t{1}); memory.Put(sc,0x3D8,std::int32_t{1});
    Group(0,SA,{AA,AA,AB},{RA,RA,RP,RI}); Group(2,SB,{AB,AB},{RB,RA});
  }
  void Roster(void *object,std::size_t offset,std::initializer_list<std::uint32_t> ids) {
    memory.Put(object,offset+8,static_cast<std::int32_t>(ids.size()));
    memory.Put(object,offset+0xC,static_cast<std::int32_t>(ids.size()));
    if (ids.size()==0) { memory.Put(object,offset,static_cast<void *>(nullptr)); return; }
    auto *values=memory.Allocate(ids.size()*4); std::size_t i=0; for(auto id:ids) memory.Put(values,i++*4,id);
    memory.Put(object,offset,values);
  }
  void Data(void *reg,void *persistent_object,std::uint32_t persistent_id,std::uint32_t reg_id,
            std::int32_t current,std::int32_t maximum,std::int32_t count) {
    memory.Put(persistent_object,0x14,std::uint32_t{0x52656769U});
    memory.Put(persistent_object,0x18,maximum); memory.Put(persistent_object,0x1C,current);
    memory.Put(persistent_object,0x20,persistent_id); memory.Put(persistent_object,0x24,std::int32_t{0});
    memory.Put(persistent_object,0x28,reg_id);
    auto *records=memory.Allocate(static_cast<std::size_t>(count)*0x10);
    for(std::int32_t i=0;i<count;++i) {
      memory.Put(records,static_cast<std::size_t>(i)*0x10+8,persistent_id);
      memory.Put(records,static_cast<std::size_t>(i)*0x10+0xC,std::int32_t{0});
    }
    memory.Put(reg,0x20,records); memory.Put(reg,0x28,count); memory.Put(reg,0x2C,count);
  }
  void Group(std::size_t slot,std::uint32_t siege,std::initializer_list<std::uint32_t> army_ids,std::initializer_list<std::uint32_t> regiment_ids) {
    auto *record=static_cast<std::byte *>(entries)+slot*0x40;
    memory.Put(record,0,std::uint32_t{0x811C9DC5U}); memory.Put(record,4,std::uint8_t{1}); memory.Put(record,8,siege);
    Roster(record,0x10,army_ids); Roster(record,0x28,regiment_ids);
  }
  std::vector<game::ArmyStrengthSnapshot> Observe() {
    const std::array<ck3_12002::ArmyStrengthScope,2> scope{{
      {std::bit_cast<std::int32_t>(UA),game::ArmyStrengthScopeRole::player,{}},
      {std::bit_cast<std::int32_t>(UB),game::ArmyStrengthScopeRole::active_war_ally,{7}}}};
    std::vector<game::ArmyStrengthSnapshot> rows;
    Check(ck3_12002::ReadArmyStrengthsForScope(b,scope,rows)==game::ReadArmyStrengthsResult::available,
          "new daily-loss fixture production Strength query unavailable");
    Check(rows.size()==2 && rows[0].available && rows[0].current_soldiers==250 && rows[1].current_soldiers==80,
          "daily-loss additive family changed base Strength");
    Check(rows[0].current_daily_assault_loss_inputs_v1 && rows[0].current_daily_assault_loss_inputs_v1==rows[1].current_daily_assault_loss_inputs_v1,
          "daily-loss family must share one table-derived capture across Strength rows");
    return rows;
  }
};
void Emit(const std::filesystem::path &dir,const char *name,const std::vector<game::ArmyStrengthSnapshot> &rows) {
  std::string out;
  game::AppendArmyStrengthV1(out,rows[0],[](auto value){return std::to_string(value);},
    [](std::string &wire,const std::vector<std::int32_t> &ids){wire+='['; for(std::size_t i=0;i<ids.size();++i){if(i)wire+=',';wire+=std::to_string(ids[i]);}wire+=']';},
    [](std::string &wire,std::string_view text){wire+='"';wire+=text;wire+='"';});
  std::ofstream file(dir/(std::string("daily-assault-loss-")+name+".json"),std::ios::binary); file<<out<<'\n';
  Check(static_cast<bool>(file),"new daily-loss production wire emission failed");
}
} // namespace
int main(int argc,char **argv) {
  try {
    Check(argc==2,"new daily-loss fixture requires its unique wire directory");
    const std::filesystem::path directory(argv[1]); std::filesystem::create_directories(directory);
    { Fixture f; auto rows=f.Observe(); const auto &leaf=*rows[0].current_daily_assault_loss_inputs_v1;
      Check(leaf.ready && leaf.groups.size()==2 && leaf.target_regiments.size()==4,"whole groups and valid/invalid context union incomplete");
      Check(leaf.groups[0].native_current_expected_loss==116 && leaf.groups[1].native_current_expected_loss==58,
            "actual group Siege budget receiver differs from current Province association");
      Check(leaf.groups[0].besieging_inputs_v1->assault_context.breach_level_raw==2 &&
            leaf.groups[0].besieging_inputs_v1->assault_context.siege_id==std::bit_cast<std::int32_t>(SA),
            "budget context must use the table's actual Siege");
      Check(leaf.target_regiments[1].current_soldiers==50 && leaf.target_regiments[1].maximum_soldiers==100,
            "valid positive type residual current/max must be captured independently of preferred table null");
      Check(leaf.target_regiments[0].replenishment_records_v1->records.size()==2 &&
            leaf.target_regiments[3].native_loss_writer_skipped==true && !leaf.target_regiments[3].replenishment_records_v1,
            "DATA repetitions and independent character skip must survive");
      Emit(directory,"sequential-duplicates",rows); }
    { Fixture f; f.memory.Put(f.ra,0x28,std::int32_t{-1}); auto rows=f.Observe();
      Check(!rows[0].current_daily_assault_loss_inputs_v1->ready && rows[0].available,"used missing DATA must leave only additive family partial");
      Emit(directory,"missing-used-data",rows); }
    { Fixture f; f.memory.Put(f.percentage_slot,0,static_cast<void *>(nullptr)); auto rows=f.Observe();
      Check(!rows[0].current_daily_assault_loss_inputs_v1->ready &&
            rows[0].current_daily_assault_loss_inputs_v1->groups[0].native_current_expected_loss==116,
            "native scalar must remain available when evolving percentage is missing");
      Emit(directory,"missing-loaded-percentage",rows); }
    { Fixture f; f.memory.Put(f.province,0x85C,std::uint32_t{0}); auto rows=f.Observe();
      Check(rows[0].current_daily_assault_loss_inputs_v1->groups[0].native_current_expected_loss==0 &&
            !rows[0].current_daily_assault_loss_inputs_v1->groups[0].besieging_inputs_v1,
            "known invalid Province returns zero without fabricated B inputs");
      Emit(directory,"known-zero-province",rows); }
    { Fixture f; f.memory.Put(f.manager,0x180,std::int32_t{1}); f.memory.Put(f.entries,4,std::uint8_t{0});
      f.Group(2,SB,{AB,AB},{RB}); auto rows=f.Observe(); const auto &leaf=*rows[0].current_daily_assault_loss_inputs_v1;
      Check(leaf.ready && leaf.target_regiments.size()==1 && leaf.target_regiments[0].native_loss_writer_skipped==true &&
            !leaf.target_regiments[0].replenishment_records_v1,"character-only current group needs no unused DATA");
      Emit(directory,"character-skip",rows); }
    { Fixture f; f.memory.Put(f.manager,0x180,std::int32_t{0}); f.memory.Put(f.entries,4,std::uint8_t{0});
      f.memory.Put(f.entries,2*0x40+4,std::uint8_t{0}); auto rows=f.Observe();
      Check(rows[0].current_daily_assault_loss_inputs_v1->ready && rows[0].current_daily_assault_loss_inputs_v1->groups.empty(),
            "actual empty current table has independent ready empty numeric operands");
      Emit(directory,"empty-current-table",rows); }
    std::cout<<"daily assault loss input production fixture GREEN: six new wires\n"; return 0;
  } catch(const std::exception &error) { std::cerr<<error.what()<<'\n'; return 1; }
}
