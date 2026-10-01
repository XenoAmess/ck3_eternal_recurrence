#include "xar_bridge/religion_doctrine12002_selection.hpp"
#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>

namespace selection = xar::ck3_12002::religion::doctrine12002;
namespace reform = xar::ck3_12002::religion_reform;
namespace core = xar::ck3_12002;
namespace {
template<std::size_t Size> using Bytes = std::array<std::byte, Size>;
template<class Buffer, class Value> void Put(Buffer &buffer, std::size_t at, Value value) {
  std::memcpy(buffer.data()+at, &value, sizeof(value));
}
template<class Buffer> void Key(Buffer &buffer, const char *key) {
  const auto count = std::strlen(key); std::memcpy(buffer.data()+0x18, key, count);
  Put(buffer, 0x28, static_cast<std::uint64_t>(count)); Put(buffer, 0x30, std::uint64_t{15});
}
struct Fixture {
  Bytes<0xA8> state{}; Bytes<0x28> jomini{}; Bytes<0x1F8> players{}; Bytes<0x78> player{};
  std::vector<std::byte> data = std::vector<std::byte>(0x22350);
  Bytes<0xE0> entry{}; std::array<void *,1> entries{entry.data()};
  Bytes<0x30> storage{}; Bytes<0x80> slots{}; Bytes<0x1D8> character{};
  Bytes<0x90> idler{}; Bytes<0x280> handler{}; Bytes<0xC00> window{};
  std::array<Bytes<0xB20>,4> definitions{}; Bytes<0x40> group{};
  Bytes<0x50*4> items{}; Bytes<0xF00> perks{};
  void *state_pointer=state.data(), *jomini_pointer=jomini.data(),
       *storage_pointer=storage.data(), *perk_pointer=perks.data();
  static constexpr std::int32_t actor=0x03000004;
  bool visible=true, prophet=false, arguments_correct=true, drift=false;
  int knows_calls=0, perk_calls=0, trigger_calls=0;
  Fixture() {
    Put(state,8,std::int32_t{53175816}); Put(state,0x70,std::int32_t{2}); Put(state,0xA0,data.data());
    Put(jomini,0x18,players.data()); jomini[0x20]=std::byte{1};
    Put(players,0x1F0,std::int32_t{7}); Put(player,0x70,std::int32_t{7});
    Put(data,core::kPlayerCharacterManagerOffset+0x58,entries.data());
    Put(data,core::kPlayerCharacterManagerOffset+0x64,std::int32_t{1});
    Put(entry,0xD8,std::int32_t{7}); Put(entry,0xB0,actor);
    Put(storage,0x20,slots.data()); Put(storage,0x2C,std::int32_t{8});
    Put(slots,4*0x10+8,character.data()); Put(character,0x18,actor);
    Put(jomini,0x10,idler.data()); Put(idler,0,std::uintptr_t{11}); Put(idler,0x88,handler.data());
    Put(handler,0,std::uintptr_t{22}); Put(handler,0x278,window.data());
    Put(window,0,std::uintptr_t{33}); Put(window,0x10,std::uintptr_t{44}); Put(window,0xA0,handler.data());
    Put(window,0xC8,std::uint32_t{0x83000003}); Put(window,0xCC,static_cast<std::uint32_t>(actor));
    Key(group,"group_a");
    const std::array<const char *,4> keys={"known_\"信","unknown_a","hidden_a","blocked_a"};
    for (std::size_t index=0;index<definitions.size();++index) {
      Key(definitions[index],keys[index]); Put(definitions[index],0xB08,group.data());
      Put(items,index*0x50+0x28,definitions[index].data());
    }
    Put(window,0x8A8,items.data()); Put(window,0x8B0,std::int32_t{4}); Put(window,0x8B4,std::int32_t{4});
    // No tenet groups: this fixture exercises the actual doctrine pipeline.
    Put(perks,0xEF0,player.data());
  }
};
Fixture *fixture{};
void *Player(void *) { return fixture->player.data(); }
bool Visible(const void *) { return fixture->visible; }
bool Trigger(const void *trigger, const void *scope) {
  ++fixture->trigger_calls; fixture->arguments_correct &= scope==fixture->window.data()+0xD0;
  for (std::size_t index=0;index<fixture->definitions.size();++index) {
    const auto *definition=fixture->definitions[index].data();
    if (trigger==definition+0x1B8) {
      if (fixture->drift) Put(fixture->state,8,std::int32_t{53175817});
      return index!=2;
    }
    if (trigger==definition+0xE8) return index!=3;
  }
  fixture->arguments_correct=false; return false;
}
bool Knows(void *actor,const void *definition) {
  ++fixture->knows_calls; fixture->arguments_correct &= actor==fixture->character.data() &&
      (definition==fixture->definitions[0].data() || definition==fixture->definitions[1].data());
  return definition==fixture->definitions[0].data();
}
bool HasPerk(void *actor,const void *perk) {
  ++fixture->perk_calls; fixture->arguments_correct &= actor==fixture->character.data() && perk==fixture->player.data();
  return fixture->prophet;
}
bool Tenet(const void *,void *,const void *) { fixture->arguments_correct=false; return false; }
reform::DraftChoiceBindings Bind(Fixture &value) {
  fixture=&value; reform::DraftChoiceBindings bindings{}; bindings.window.enabled=true;
  bindings.window.core={true,&value.state_pointer,&value.jomini_pointer,&value.storage_pointer,&Player};
  bindings.window.idler_vtable=11; bindings.window.handler_vtable=22;
  bindings.window.window_vtable=33; bindings.window.window_secondary_vtable=44; bindings.window.is_visible=&Visible;
  bindings.knows_doctrine=&Knows; bindings.evaluate_trigger=&Trigger; bindings.has_perk=&HasPerk;
  bindings.tenet_can_pick=&Tenet; bindings.perk_database_global=&value.perk_pointer; return bindings;
}
int checks{};
bool Check(bool value,const char *label) { ++checks; if (!value) std::cerr<<"FAIL "<<label<<'\n'; return value; }
void Wire(const std::filesystem::path &directory,const char *name,const selection::CurrentDoctrineSelection &value) {
  std::ofstream(directory/name)<<selection::SerializeCurrentDraftDoctrineSelection12002(value)<<'\n';
}
} // namespace

int main(int argc,char **argv) {
  const auto output=argc>1?std::filesystem::path(argv[1]):std::filesystem::current_path();
  Fixture value; auto bindings=Bind(value); selection::CurrentDoctrineSelection observed{};
  if (!Check(selection::ReadCurrentDraftDoctrineSelection12002(bindings,1,observed) &&
      observed.available && observed.popup_observed && observed.selection_ready && observed.rows.size()==4 &&
      observed.selectable_doctrine_keys==std::vector<std::string>{"known_\"信"},
      "actual producer full rows and complete current selectable keys")) return 1;
  if (!Check(observed.rows[0].native_should_display && observed.rows[0].choice.native_can_pick &&
      observed.rows[0].choice.native_knows_doctrine==true && !observed.rows[0].choice.native_has_prophet &&
      observed.rows[0].selectable && observed.rows[0].selection_blocker=="none",
      "known actual definition enabled without perk evaluation")) return 2;
  if (!Check(observed.rows[1].native_should_display && observed.rows[1].choice.native_can_pick &&
      observed.rows[1].choice.native_knows_doctrine==false && observed.rows[1].choice.native_has_prophet==false &&
      !observed.rows[1].selectable && observed.rows[1].selection_blocker=="doctrine_not_known_and_no_prophet",
      "unknown no-Prophet visible row disabled")) return 3;
  if (!Check(!observed.rows[2].native_should_display && !observed.rows[2].choice.native_can_pick &&
      !observed.rows[2].selectable && observed.rows[2].selection_blocker=="hidden_by_native_should_display" &&
      !observed.rows[2].choice.native_knows_doctrine,
      "native hidden row excluded with short-circuited knowledge")) return 4;
  if (!Check(observed.rows[3].native_should_display && !observed.rows[3].choice.native_can_pick &&
      !observed.rows[3].selectable && observed.rows[3].selection_blocker=="blocked_by_native_can_pick" &&
      value.arguments_correct && value.knows_calls==2 && value.perk_calls==1 && value.trigger_calls==11,
      "native pick trigger independently blocks with actual scope and definitions")) return 5;
  Wire(output,"current-selection.json",observed);
  value.prophet=true;
  if (!Check(selection::ReadCurrentDraftDoctrineSelection12002(bindings,2,observed) &&
      observed.rows[1].choice.native_has_prophet==true && observed.rows[1].selectable &&
      observed.selectable_doctrine_keys.size()==2,"native Prophet opens the actual unknown candidate")) return 6;
  Wire(output,"prophet-selection.json",observed);
  reform::DraftChoices raw{};
  if (!Check(reform::ReadCurrentDraftChoices12002(bindings,3,raw),"same actual producer input for composition")) return 7;
  const auto known_before=value.knows_calls;
  if (!Check(selection::ObserveCurrentDraftDoctrineSelection12002(bindings,raw,3,observed) &&
      value.knows_calls==known_before && observed.rows[1].selectable,
      "observer consumes raw popup without repeating knowledge/candidate producer")) return 8;
  value.drift=true;
  if (!Check(!selection::ObserveCurrentDraftDoctrineSelection12002(bindings,raw,3,observed) &&
      observed.failure=="state_changed" && !observed.selection_ready && observed.rows.empty() &&
      observed.selectable_doctrine_keys.empty(),"changed frame clears partial selection")) return 9;
  Wire(output,"changed-selection.json",observed);
  value.drift=false; Put(value.state,8,std::int32_t{53175816});
  Put(value.items,0x28,value.definitions[1].data());
  if (!Check(!selection::ObserveCurrentDraftDoctrineSelection12002(bindings,raw,3,observed) &&
      observed.failure=="state_changed","popup index must still name actual stable definition")) return 10;
  Put(value.items,0x28,value.definitions[0].data());
  if (!Check(!selection::ObserveCurrentDraftDoctrineSelection12002(bindings,raw,4,observed) &&
      observed.failure=="popup_epoch_changed","composition shares capture epoch")) return 11;
  value.visible=false;
  if (!Check(!selection::ReadCurrentDraftDoctrineSelection12002(bindings,5,observed) &&
      observed.failure=="current_draft_not_visible" && !observed.available && !observed.popup_observed,
      "closed window returns typed unavailable rather than universal empty catalog")) return 12;
  Wire(output,"closed-selection.json",observed);
  value.visible=true; Put(value.window,0x8B4,std::int32_t{0});
  if (!Check(selection::ReadCurrentDraftDoctrineSelection12002(bindings,6,observed) && observed.selection_ready &&
      observed.rows.empty() && observed.selectable_doctrine_keys.empty(),
      "materialized current empty popup is observed empty")) return 13;
  Wire(output,"empty-selection.json",observed);
  Put(value.window,0x8B4,std::int32_t{4}); value.perk_pointer=nullptr;
  if (!Check(!selection::ReadCurrentDraftDoctrineSelection12002(bindings,7,observed) &&
      observed.failure=="prophet_definition_unavailable" && !observed.selection_ready,
      "required Prophet cache absence propagates actual missing input")) return 14;
  Wire(output,"missing-prophet-selection.json",observed);
  const auto exact=reform::BindCurrentDraftChoices12002(0x140000000,core::kExecutableSha256);
  if (!Check(exact.window.enabled && reinterpret_cast<std::uintptr_t>(exact.evaluate_trigger)==0x14372DF30ULL &&
      !reform::BindCurrentDraftChoices12002(0x140000000,"old-build").window.enabled,
      "reuses exact-build source binding")) return 15;
  std::cout<<"GREEN checks="<<checks<<" actual DoctrineItem selection reader and serializer; no CK3\n"; return 0;
}
