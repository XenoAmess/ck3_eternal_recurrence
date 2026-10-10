#include "xar_bridge/ck3_12004_construction_held.hpp"
#include "xar_bridge/construction_owner_modifier_4e_c86670_12004.hpp"
#include "xar_bridge/m4_factor_actor_context_12004.hpp"
#include "xar_bridge/construction_owner_mode3_raw_eax_28be0b0_12004.hpp"
#include "construction_actual_2c42930_return_focus_12004.hpp"
#include <array>
#include <cstring>
#include <fstream>
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>

int RunConstructionOwnerMode3LoadedInputs12004NewCases();
bool RunNewTitleSelectedFullIdCases12004(std::string &);
bool RunNewM4SubobjectPredicateCases12004(std::string &);
bool VerifyRawCharacterModifierContext12004(std::string &);
void RunLoadedD2BE00SingletonNewCase12004();
void RunConstructionPointerMembership30A6080FreshCases12004();
void RunConstructionOwnerMode3ContextScalar12004Cases();
bool RunConstructionCollectionPredicateA11CC0NewCases12004(std::string &);
namespace xar::ck3_12004 {
int RunArmyFactor2B9CBA012004NewCases();
int RunM4FactorActorContext12004NewCases();
int RunActualContext8895D0NewCases12004();
std::string SerializeConstructionMode3CurrentWireForNewCase12004(
    const PlayerHeldConstructionMode3InputResultV1 &,
    const PlayerWorldBuildingSourceResultV1 &, std::uint64_t);
namespace new_cases { bool RunReturnedSelector28C2DF012004NewCases(); }
namespace construction_owner_mode3 {
int RunConstructionMode3RawReceiver12004NewCases();
int RunConstructionMode3Raw28BE0B0Eax12004NewCases();
void RunNewMode3M4Cases12004();
void VerifyConstructionCount28B71E0OwnedCases12004();
void RunScaledCollectionKeyFocus12004();
int RunConstructionContextKey2C23340Scenario12004();
int RunCharacterModifier2C4D1D012004NewCases();
void VerifyConstructionNumericChild24CEF10OwnedCases12004();
void VerifyConstructionNumericHelper2C39B80OwnedCases12004();
void VerifyContextFactor2C399C0ConnectedCasesV1();
void VerifyContextFirstQword24D3260ConnectedCasesV1();
bool ExerciseConstructionContextPredicate2C25010NewCaseV1(std::string &);
void RunPointerKeyPredicate31C1D10FreshCases12004();
}
}

namespace {
using namespace xar::ck3_12004;
using namespace xar::ck3_12004::construction_owner_mode3;
constexpr std::uintptr_t module = 0x100000000ULL;
constexpr std::uintptr_t province = 0x200000000ULL;
constexpr std::uintptr_t context = 0x200010000ULL;
constexpr std::uintptr_t context_object = 0x200020000ULL;
constexpr std::uintptr_t character = 0x200030000ULL;
constexpr std::uintptr_t fallback_character = 0x200040000ULL;
constexpr std::uintptr_t title = 0x200050000ULL;
constexpr std::uintptr_t land = 0x200060000ULL;
constexpr std::uintptr_t selector = 0x200070000ULL;
constexpr std::uintptr_t char_store = 0x200080000ULL;
constexpr std::uintptr_t char_table = 0x200090000ULL;
constexpr std::uintptr_t title_store = 0x2000A0000ULL;
constexpr std::uintptr_t title_table = 0x2000B0000ULL;
constexpr std::uintptr_t keys = 0x2000C0000ULL;
constexpr std::uintptr_t values = 0x2000D0000ULL;
constexpr std::uintptr_t key_root = 0x2000E0000ULL;
constexpr std::uintptr_t key_object = 0x2000F0000ULL;
constexpr std::uintptr_t membership = 0x200100000ULL;
constexpr std::uintptr_t provider = 0x200110000ULL;
constexpr std::uintptr_t modifier_slots = 0x200120000ULL;
constexpr std::uintptr_t definition = 0x200130000ULL;
constexpr std::uintptr_t expression = 0x200140000ULL;
constexpr std::uintptr_t virtual_table = 0x200150000ULL;
constexpr std::uintptr_t game_state = 0x200160000ULL;
constexpr std::uintptr_t jomini_state = 0x200170000ULL;
constexpr std::uintptr_t players = 0x200180000ULL;
constexpr std::uintptr_t game_data = 0x200190000ULL;
constexpr std::uintptr_t player_entries = 0x2001D0000ULL;
constexpr std::uintptr_t player_entry = 0x2001E0000ULL;
constexpr std::uintptr_t province_array = 0x2001F0000ULL;
constexpr std::uintptr_t held_ids = 0x200200000ULL;
constexpr std::uintptr_t title_template = 0x200210000ULL;
constexpr std::uintptr_t world_manager = 0x200220000ULL;
constexpr std::uintptr_t world_definitions = 0x200230000ULL;
constexpr std::uintptr_t world_definition = 0x200240000ULL;
constexpr std::uintptr_t built_slots = 0x200250000ULL;
constexpr std::uintptr_t fallback_title = 0x200260000ULL;
constexpr std::uint64_t frame_key = 13579;

void Require(bool condition, const std::string &reason) {
  if (!condition) throw std::runtime_error(reason);
}

// One new bounded sparse raw snapshot. No game image is allocated or copied.
// Memory is supplied only through the same production read callbacks.
struct Fixture {
  std::map<std::uintptr_t, std::vector<std::byte>> blocks;
  std::uintptr_t denied_address = 0;
  std::size_t denied_size = 0, denied_reads = 0, copy_calls = 0;
  std::uintptr_t first_missing_address = 0;
  std::size_t first_missing_size = 0;
  std::size_t frame_captures = 0;
  bool change_frame_after_first = false;
  xar::game::CampaignRootFrameV1 frame{};
  void Zero(std::uintptr_t address, std::size_t size) {
    blocks.emplace(address, std::vector<std::byte>(size));
  }
  template<class T> void Put(std::uintptr_t address, T value) {
    auto i = blocks.upper_bound(address);
    if (i != blocks.begin()) {
      --i;
      const auto offset = address - i->first;
      if (offset <= i->second.size() && sizeof(T) <= i->second.size() - offset) {
        std::memcpy(i->second.data() + offset, &value, sizeof(value));
        return;
      }
    }
    Zero(address, sizeof(value));
    Put(address, value);
  }
  template<class T> void Global(std::uintptr_t rva, T value) { Put(module+rva, value); }
  static bool Copy(void *opaque, const void *input, void *out, std::size_t size) noexcept {
    auto &f = *static_cast<Fixture *>(opaque);
    ++f.copy_calls;
    const auto address = reinterpret_cast<std::uintptr_t>(input);
    if (f.denied_address && address < f.denied_address + f.denied_size &&
        f.denied_address < address + size) { ++f.denied_reads; return false; }
    auto i = f.blocks.upper_bound(address);
    if (i == f.blocks.begin()) {
      if(!f.first_missing_address) {f.first_missing_address=address;f.first_missing_size=size;}
      return false;
    }
    --i;
    const auto offset = address - i->first;
    if (offset > i->second.size() || size > i->second.size() - offset) {
      if(!f.first_missing_address) {f.first_missing_address=address;f.first_missing_size=size;}
      return false;
    }
    std::memcpy(out, i->second.data()+offset, size);
    return true;
  }
  static bool CopyAddress(void *opaque, std::uintptr_t input, void *out,
                          std::size_t size) noexcept {
    return Copy(opaque, reinterpret_cast<const void *>(input), out, size);
  }
  static bool Main(void *) noexcept { return true; }
  static bool Capture(void *opaque, xar::game::CampaignRootFrameV1 &out) noexcept {
    auto &f=*static_cast<Fixture *>(opaque);
    out=f.frame;
    if (++f.frame_captures > 1 && f.change_frame_after_first) ++out.date_raw;
    return true;
  }
  LoadedInputAccessV1 Loaded() { return {this, Copy, true}; }
  CampaignRootAccessV1 Campaign() {
    CampaignRootAccessV1 access{};
    access.context=this; access.read_memory=Copy;
    access.is_main_thread=Main; access.capture_frame=Capture;
    return access;
  }
  // Independent ordinary-world callbacks for this new software snapshot.
  // They do not invoke stock/native functions or confer live-game readiness.
  static bool WorldLegality(void *, std::int32_t actor, std::int32_t id,
      std::uintptr_t definition_pointer, std::int32_t slot, bool &allowed) noexcept {
    if (actor!=5 || id!=604 || definition_pointer!=world_definition || slot!=0)
      return false;
    allowed=true;
    return true;
  }
  static bool WorldCost(void *, std::int32_t actor, std::int32_t id,
      std::uintptr_t province_pointer, std::int32_t definition_id,
      std::uintptr_t definition_pointer, std::int32_t slot,
      std::array<std::int64_t,10> &cost) noexcept {
    if (actor!=5 || id!=604 || province_pointer!=province || definition_id!=2103 ||
        definition_pointer!=world_definition || slot!=0) return false;
    cost.fill(0);
    return true;
  }
  Fixture() {
    for (auto address : {province,context,context_object,character,
        fallback_character,title,fallback_title,land,selector}) Zero(address,0x1000);
    for (auto address : {char_store,title_store}) Zero(address,0x40);
    for (auto address : {char_table,title_table,keys,values,key_root,key_object,
        membership,provider,modifier_slots,definition,expression,virtual_table,
        game_state,jomini_state,players,player_entries,player_entry,held_ids,
        title_template,world_manager,world_definitions,world_definition,built_slots})
      Zero(address,0x1000);
    Zero(game_data,0x22400);
    Zero(province_array,605*sizeof(std::uintptr_t));
    Global(0x5C68C50,game_state); Global(0x5C6A520,jomini_state);
    Put(game_state+0xA0,game_data); Put(jomini_state+0x18,players);
    Put(players+0x1F0,std::int32_t{77});
    Put(game_data+0x222E8+0x58,player_entries);
    Put(game_data+0x222E8+0x64,std::int32_t{1});
    Put(player_entries,player_entry); Put(player_entry+0xD8,std::int32_t{77});
    Put(player_entry+0xB0,std::int32_t{5});
    Put(game_data+0x140,province_array); Put(game_data+0x14C,std::int32_t{605});
    Put(province_array+604*8,province);
    Global(0x5C67568,char_store); Global(0x5C67570,fallback_character);
    Put(char_store+0x20,char_table); Put(char_store+0x2C,std::uint32_t{32});
    Put(char_table+5*16+8,character);
    Put(character+0x18,std::uint32_t{5}); Put(character+0x1C,std::uint32_t{0x43686172});
    Put(character+0x1C0,land); Put(land+0x1B8,std::uint32_t{5});
    Put(land+0x3F8,selector); Put(fallback_character+0x18,std::uint32_t{0xFFFFFFFF});
    Global(0x5D1DAF8,title_store); Global(0x5D1DAE0,fallback_title);
    Put(title_store+0x20,title_table); Put(title_store+0x2C,std::uint32_t{32});
    Put(title_table+7*16+8,title); Put(title+0x10,std::int32_t{7});
    Put(fallback_title+0x10,std::int32_t{-1});
    Put(title+0x128,std::uint32_t{5}); Put(title+0x130,std::uint8_t{1});
    Put(title+0x48,title_template); Put(title_template+0x64,std::int32_t{1});
    Put(title+0x338,province);
    Put(land+0x1E0,held_ids); Put(land+0x1E8,std::int32_t{1});
    Put(land+0x1EC,std::int32_t{1}); Put(held_ids,std::int32_t{7});
    Put(province+0x10,std::int32_t{604}); Put(province+0x620,title);
    Put(province+0x620+0x10,built_slots);
    Put(province+0x620+0x1C,std::int32_t{1});
    Put(province+0x710,context); Put(province+0x718,std::int64_t{777777});
    Put(context+0x848,context_object); Put(context+0x738,std::uint32_t{7});
    Put(context+0x30+0x68,keys); Put(context+0x30+0x74,std::int32_t{1});
    Put(context+0x30+0xD0,values); Put(keys,std::uint16_t{0x3F});
    Put(values,std::int64_t{500000});
    Put(context+0x20,key_root); Put(key_root+0xB8,key_object);
    Put(key_object+0x78E,std::uint16_t{0xFFFF});
    Global(0x5D242F8,std::uintptr_t{0}); Global(0x5C67670,selector);
    Global(0x5C96180,std::int64_t{0}); Global(0x5C69450,std::int64_t{100000});
    Global(0x5C69440,std::int64_t{100000});
    Global(0x5D1E2A8,selector);
    Put(selector+0x420,membership); Put(selector+0x42C,std::int32_t{1});
    Put(membership,title);
    Global(0x5D67B80,std::int32_t{1}); Zero(module+0x5D67B90,0x200);
    Put(module+0x5D67B90+0x68,keys); Put(module+0x5D67B90+0x70,std::int32_t{1});
    Put(module+0x5D67B90+0x74,std::int32_t{0});
    Put(module+0x5D67B90+0xD0,values); Put(module+0x5D67B90+0xD8,std::int32_t{1});
    Put(module+0x5D67B90+0xDC,std::int32_t{0});
    Global(0x5D1DD50,provider); Put(provider+0xEF0,modifier_slots);
    Put(modifier_slots+0x4E*8,definition);
    Put(expression+8,virtual_table); Put(virtual_table+0x30,std::uintptr_t{0x300000008ULL});
    Global(0x5C67540,world_manager); Global(0x5D1E320,std::uintptr_t{0});
    Put(world_manager+0x50,world_definitions);
    Put(world_manager+0x58,std::int32_t{1});
    Put(world_manager+0x5C,std::int32_t{1});
    Put(world_definitions,world_definition);
    Put(world_definition,module+0x48B6CD8);
    Put(world_definition+0x10,std::int32_t{2103});
    const char world_key[]="farm_01";
    for (std::size_t i=0;i<sizeof(world_key)-1;++i)
      Put(world_definition+0x18+i,world_key[i]);
    Put(world_definition+0x28,std::size_t{sizeof(world_key)-1});
    Put(world_definition+0x30,std::size_t{15});
    frame.snapshot_revision=frame_key; frame.date_raw=53290128;
    frame.paused=true; frame.map_ready=true; frame.has_played_character=true;
    frame.played_character_alive=true; frame.played_character_id=5;
  }
  ConstructionOwnerMode3InputsV1 Inputs() {
    return ReadConstructionOwnerMode3InputsV1(Loaded(),
        {module,true,province,604,frame_key});
  }
  PlayerHeldConstructionMode3InputResultV1 Held() {
    auto access=Campaign();
    return ReadPlayerHeldConstructionMode3InputsV1(module,true,access,{frame_key});
  }
  PlayerWorldBuildingSourceResultV1 World() {
    const PlayerWorldBuildingSourceAccessV1 access{
        Campaign(),WorldLegality,this,WorldCost,this};
    return xar::ck3_12004::ReadPlayerWorldBuildingDefinitionSourcesV1(
        module,true,access,{frame_key,604,1,1});
  }
  void PositiveM4Inputs() {
    Put(fallback_title+0x128,std::uint32_t{5});
    Put(land+0x1EC,std::int32_t{3});
    Put(held_ids+4,std::uint32_t{7}); Put(held_ids+8,std::uint32_t{7});
    Put(land+0x3D8,std::int32_t{1});
    Put(title_template+0x64,std::int32_t{0});
    Put(title+0x130,std::uint8_t{0}); Put(title+0x12C,std::uint32_t{0xFFFFFFFF});
    Put(province+0x85C,std::uint32_t{0x50726F76});
    Put(province+0x628,std::uint8_t{1});
    Put(province+0x620+0x1C,std::uint32_t{0});
    Global(0x5D1E320,selector); // Copied object+38 is known wrong magic.
    Global(0x5C69470,std::int64_t{10000}); Global(0x5C69488,std::int64_t{15000});
  }
};

int RunConnectedProductionCases(int first_case=0) {
  int count=0;
  if(first_case<=0) {
    Fixture f; const auto r=f.Inputs();
    Require(r.inputs_observed && r.all_reached_inputs_observed,
        "03 production full literal branch: "+r.unavailable_input);
    Require(r.returned_receiver_pointer==character && r.context_pointer==context,
        "03 real22->38->06 receiver/frame binding");
    Require(r.conditional_aggregate_raw==std::optional<std::int64_t>{500000} &&
        r.loaded_publisher_718_raw==std::optional<std::int64_t>{777777},
        "03 conditional aggregate must preserve independent loaded publisher");
    Require(!r.per_building_attribution && !r.realized_holder_net &&
        !r.observed_native_producer_call,"03 source projection grants no native benefit"); ++count;
  }
  if(first_case<=1) {
    Fixture f; f.Put(selector+0x4D6,std::uint8_t{5});
    f.Put(definition+0x7B,std::uint8_t{1}); f.Put(definition+0x68,std::int64_t{-25000});
    const auto r=f.Inputs();
    Require(r.all_reached_inputs_observed && r.owner_factor_raw==std::optional<std::int64_t>{0} &&
        r.conditional_aggregate_raw==std::optional<std::int64_t>{0},
        "03 real08/48->12 negative literal ->05 clamp ->parent"); ++count;
  }
  if(first_case<=2) {
    Fixture f; f.Put(selector+0x4D6,std::uint8_t{5});
    f.denied_address=definition+0x68; f.denied_size=8;
    const auto r=f.Inputs();
    Require(r.all_reached_inputs_observed && r.owner_factor_raw==std::optional<std::int64_t>{0} &&
        f.denied_reads==0,"03 literal flag0 must not demand raw68"); ++count;
  }
  if(first_case<=3) {
    Fixture f; f.Put(selector+0x4D6,std::uint8_t{5});
    f.Put(definition+0x70,expression); const auto r=f.Inputs();
    Require(r.inputs_observed && !r.all_reached_inputs_observed &&
        !r.owner_factor_raw && !r.conditional_aggregate_raw &&
        r.loaded_publisher_718_raw.has_value(),
        "03 dynamicmissing remains unavailable with publisher retained"); ++count;
  }
  if(first_case<=4) {
    Fixture f; f.denied_address=values; f.denied_size=8; const auto r=f.Inputs();
    Require(!r.loaded_key_3f_raw && !r.conditional_aggregate_raw &&
        r.loaded_publisher_718_raw.has_value(),"03 present unreadable3F cannot become zero"); ++count;
  }
  if(first_case<=5) {
    Fixture f; const auto r=f.Held();
    std::string state=" frame="+std::to_string(r.current_frame_observed)+
        " failure_enum="+std::to_string(static_cast<int>(r.failure))+
        " revision="+std::to_string(r.snapshot_revision)+
        " date="+std::to_string(r.date_raw)+
        " actor="+std::to_string(r.player_character_id)+
        " holdings="+std::to_string(r.holdings.size())+
        " first_missing_address="+std::to_string(f.first_missing_address)+
        " first_missing_size="+std::to_string(f.first_missing_size);
    if(!r.holdings.empty()) {
      const auto &row=r.holdings[0];
      state+=" title="+std::to_string(row.barony_title_id)+
          " province="+std::to_string(row.province_id)+
          " all_inputs="+std::to_string(row.inputs.all_reached_inputs_observed)+
          " aggregate="+(row.inputs.conditional_aggregate_raw?
              std::to_string(*row.inputs.conditional_aggregate_raw):"null")+
          " unavailable="+row.inputs.unavailable_input;
    }
    Require(r.current_frame_observed && r.snapshot_revision==frame_key &&
        r.date_raw==53290128 && r.player_character_id==5 && r.holdings.size()==1 &&
        r.holdings[0].barony_title_id==7 && r.holdings[0].province_id==604 &&
        r.holdings[0].inputs.conditional_aggregate_raw==std::optional<std::int64_t>{500000},
        "03 existing held/current paused source ->new production packet"+state); ++count;
  }
  if(first_case<=6) {
    Fixture f; f.PositiveM4Inputs(); const auto r=f.Inputs();
    Require(r.all_reached_inputs_observed && r.child_28b9300_signed_eax==2 &&
        r.factor_before_context==std::optional<std::int64_t>{85000} &&
        r.conditional_aggregate_raw==std::optional<std::int64_t>{425000},
        "03 actual13/22d/23d positive reduction +loaded scalar signed cap +parent scale: "+
        r.unavailable_input+" receiver="+std::to_string(r.returned_receiver_pointer)+
        " first_missing_address="+std::to_string(f.first_missing_address)+
        " first_missing_size="+std::to_string(f.first_missing_size)); ++count;
  }
  if(first_case<=7) {
    Fixture f; f.PositiveM4Inputs();
    const auto r=ReadConstructionOwnerMode3InputsV1(f.Loaded(),
        {module,true,province,604,frame_key},
        {nullptr,ReadRaw28BE0B0EaxAdapter12004,true},{});
    Require(r.inputs_observed && !r.all_reached_inputs_observed &&
        !r.factor_before_context && !r.conditional_aggregate_raw &&
        r.loaded_publisher_718_raw==std::optional<std::int64_t>{777777},
        "03 reached unavailable reduction must not project parent factor"); ++count;
  }
  if(first_case<=8) {
    Fixture f; f.denied_address=title+0x12C; f.denied_size=4;
    const auto r=f.Inputs();
    Require(r.all_reached_inputs_observed && f.denied_reads==0,
        "03 native title130 nonzero skips unused12C field"); ++count;
  }
  if(first_case<=9) {
    Fixture f; f.change_frame_after_first=true; const auto r=f.Held();
    Require(!r.current_frame_observed && r.holdings.empty() &&
        r.failure==PlayerHeldConstructionModelFailureV1::frame_changed,
        "03 fullframe change clears optional packet"); ++count;
  }
  return count;
}

int RunModifierFocusedRecipe() {
  Fixture f;
  M4FactorActorContext12004 actor;
  const M4FactorActorContextAccess12004 access{&f,Fixture::CopyAddress};
  const M4FactorActorContextRequest12004 request{module,kMode3InputSourcePin12004,character,frame_key};
  Require(ReadM4FactorActorContext12004(access,request,actor) && actor.complete_source,
          "12 focused source08/48 context must be complete");
  const ConstructionModifier4EAccess12004 input{module,kMode3InputSourcePin12004,Fixture::CopyAddress,&f};
  int count=0;
  actor.complete_source=false;
  f.Put(definition+0x7B,std::uint8_t{1}); f.Put(definition+0x68,std::int64_t{-25000});
  auto r=ReadConstructionOwnerModifier4E12004(input,actor);
  Require(r.factor_input.source_ready && r.factor_input.returned_q64==std::optional<std::int64_t>{-25000},
          "12 literal needs actorprefix but not unused inner"); ++count;
  f.Put(definition+0x7B,std::uint8_t{0}); f.denied_address=definition+0x68;f.denied_size=8;
  r=ReadConstructionOwnerModifier4E12004(input,actor);
  Require(r.factor_input.source_ready && r.factor_input.returned_q64==std::optional<std::int64_t>{0} &&
          f.denied_reads==0,"12 flagzero must not read68"); ++count;
  f.Put(definition+0x7B,std::uint8_t{1});
  r=ReadConstructionOwnerModifier4E12004(input,actor);
  Require(!r.factor_input.source_ready && !r.factor_input.returned_q64,
          "12 reachedunreadable literal remains unavailable"); ++count;
  f.denied_address=0;f.Put(definition+0x70,expression);actor.complete_source=true;
  r=ReadConstructionOwnerModifier4E12004(input,actor);
  Require(!r.factor_input.source_ready && !r.factor_input.returned_q64,
          "12 dynamic no copiedvirtualwitness remains unknown"); ++count;
  ConstructionModifier4EVirtualOutput12004 witness;
  witness.context_input=&actor;witness.context_receiver=character;witness.frame_key=frame_key;
  witness.actor_full_id=5;witness.definition_identity=definition;
  witness.expression_receiver=expression+8;witness.virtual_slot_30=0x300000008ULL;
  witness.context_alias_00=reinterpret_cast<std::uintptr_t>(actor.raw.data());
  witness.context_alias_10=witness.context_alias_00;witness.support118_alias_18=0x300000118ULL;
  witness.name_descriptor_byte_14=1;witness.name_descriptor_dword_18=0xFFFFFFFFU;
  witness.original_output_identity=0x300000200ULL;witness.temporary_output_identity=0x300000300ULL;
  witness.temporary_q64_after_call=0;witness.virtual_call_completed=true;witness.source_ready=true;
  r=ReadConstructionOwnerModifier4E12004(input,actor,&witness);
  Require(r.factor_input.source_ready && r.factor_input.returned_q64==std::optional<std::int64_t>{0},
          "12 qualified conditional suppliedzero remains present"); ++count;
  witness.temporary_q64_after_call=-9;
  r=ReadConstructionOwnerModifier4E12004(input,actor,&witness);
  Require(r.factor_input.source_ready && r.factor_input.returned_q64==std::optional<std::int64_t>{-9},
          "12 signedpostvirtual q64 remains unclamped"); ++count;
  for (int which=0;which<8;++which) {
    auto changed=witness;
    switch(which) {
      case 0:changed.actor_full_id+=0x01000000;break;
      case 1:++changed.frame_key;break;
      case 2:++changed.context_receiver;break;
      case 3:++changed.definition_identity;break;
      case 4:++changed.virtual_slot_30;break;
      case 5:changed.context_input=nullptr;break;
      case 6:++changed.context_alias_10;break;
      default:changed.evaluator_r9=1;break;
    }
    const auto bad=ReadConstructionOwnerModifier4E12004(input,actor,&changed);
    Require(!bad.factor_input.source_ready && !bad.factor_input.returned_q64,
            "12 mismatched dynamic operand must stayunavailable"); ++count;
  }
  return count;
}

std::string Escape(const std::string &s) {
  std::string out;for (char c:s) {if(c=='"'||c=='\\')out+='\\';if(c=='\n')out+="\\n";else out+=c;}return out;
}
} // namespace

int main(int argc,char **argv) {
  using namespace xar::ck3_12004;
  using namespace xar::ck3_12004::construction_owner_mode3;
  std::string current="start", failure;
  int entries=0,own_cases=0,skipped_entries=0;
  std::size_t wire_bytes=0;
  const std::string resume_entry=argc>=3?argv[2]:"03c";
  bool resume_seen=false;
  try {
    Require(argc>=2 && argc<=4,"require wire outputpath, optional exact resume entry and production-case index");
    int production_first_case=0;
    if(argc==4) {
      std::size_t consumed=0;
      production_first_case=std::stoi(argv[3],&consumed);
      Require(consumed==std::string(argv[3]).size() && production_first_case>=0 &&
          production_first_case<=9,"invalid exact production-case index");
    }
    const auto selected=[&](const char *label) {
      if(!resume_seen && resume_entry==label) resume_seen=true;
      if(!resume_seen) {++skipped_entries;return false;}
      current=label;return true;
    };
    const auto counted=[&](const char *label,auto entry) {
      if(!selected(label)) return;
      Require(entry()>0,label);++entries;
    };
    const auto checked=[&](const char *label,auto entry) {
      if(!selected(label)) return;
      entry();++entries;
    };
    counted("03c",RunConstructionOwnerMode3LoadedInputs12004NewCases);
    if(selected("04c")) {Require(new_cases::RunReturnedSelector28C2DF012004NewCases(),current);++entries;}
    counted("05c",RunArmyFactor2B9CBA012004NewCases);
    if(selected("06c")) {Require(RunConstructionMode3RawReceiver12004NewCases()==0,current);++entries;}
    counted("08c",RunM4FactorActorContext12004NewCases);
    if(selected("11c")) {Require(RunConstructionMode3Raw28BE0B0Eax12004NewCases()==0,current);++entries;}
    checked("13e",RunNewMode3M4Cases12004);
    checked("23d",VerifyConstructionCount28B71E0OwnedCases12004);
    if(selected("22d")) {Require(RunNewM4SubobjectPredicateCases12004(failure),current+failure);++entries;}
    counted("48c",RunActualContext8895D0NewCases12004);
    checked("14c",RunScaledCollectionKeyFocus12004);
    checked("15d",RunConstructionOwnerMode3ContextScalar12004Cases);
    counted("17c",RunConstructionContextKey2C23340Scenario12004);
    counted("34c",RunCharacterModifier2C4D1D012004NewCases);
    checked("23c",VerifyConstructionNumericChild24CEF10OwnedCases12004);
    checked("19c",VerifyConstructionNumericHelper2C39B80OwnedCases12004);
    checked("20c",VerifyContextFactor2C399C0ConnectedCasesV1);
    checked("30d",VerifyContextFirstQword24D3260ConnectedCasesV1);
    if(selected("21c")) {Require(ExerciseConstructionContextPredicate2C25010NewCaseV1(failure),current+failure);++entries;}
    if(selected("22c")) {Require(RunNewTitleSelectedFullIdCases12004(failure),current+failure);++entries;}
    if(selected("27c")) {Require(RunConstructionCollectionPredicateA11CC0NewCases12004(failure),current+failure);++entries;}
    checked("28d",RunLoadedD2BE00SingletonNewCase12004);
    checked("29d",RunPointerKeyPredicate31C1D10FreshCases12004);
    checked("37c",RunConstructionPointerMembership30A6080FreshCases12004);
    if(selected("38d")) {
      const auto focus_ok=focus::RunActual2C42930ReturnFocus12004();
      const auto focus_reason=focus::GetActual2C42930ReturnFocusFailure12004();
      Require(focus_ok,std::string("38d ")+(focus_reason?focus_reason:"unknown"));++entries;
    }
    if(selected("46c")) {Require(VerifyRawCharacterModifierContext12004(failure),current+failure);++entries;}
    if(selected("03d production")) {own_cases+=RunConnectedProductionCases(production_first_case);++entries;}
    if(selected("12c connectedrecipe")) {own_cases+=RunModifierFocusedRecipe();++entries;}
    if(selected("57d currentwire")) {
    Fixture source;const auto held=source.Held();
    Require(held.current_frame_observed,"57 actualheldreader frame unavailable");
    const auto world=source.World();
    Require(world.source_available && world.snapshot_revision==held.snapshot_revision &&
        world.date_raw==held.date_raw && world.player_character_id==held.player_character_id &&
        world.native_final_legality_evaluated && world.player_gold_observed,
        "57 ordinaryworld production reader with independent software callbacks failed");
    const auto wire=SerializeConstructionMode3CurrentWireForNewCase12004(held,world,24680);
    Require(!wire.empty(),"57 production serializer returnedempty");
    std::ofstream output(argv[1],std::ios::binary|std::ios::trunc);
    Require(static_cast<bool>(output),"wire output open failed");
    output.write(wire.data(),static_cast<std::streamsize>(wire.size()));output.close();
    Require(static_cast<bool>(output),"wire output write failed");++entries;
    wire_bytes=wire.size();
    }
    Require(resume_seen,"unknown resume entry");
    std::cout<<"{\"status\":\"GREEN\",\"entrypoints_executed\":"<<entries
      <<",\"resume_entry\":\""<<Escape(resume_entry)<<"\",\"prior_entrypoints_skipped\":"<<skipped_entries
      <<",\"own_connected_cases_executed\":"<<own_cases
      <<",\"wire_bytes\":"<<wire_bytes<<",\"game_calls\":0,\"native_getter_calls\":0}"<<'\n';
    return 0;
  } catch(const std::exception &e) {
    std::cerr<<"{\"status\":\"RED\",\"entry\":\""<<Escape(current)
      <<"\",\"failure\":\""<<Escape(e.what())<<"\",\"entrypoints_executed\":"<<entries
      <<",\"resume_entry\":\""<<Escape(resume_entry)<<"\",\"prior_entrypoints_skipped\":"<<skipped_entries<<"}"<<'\n';
    return 1;
  }
}
