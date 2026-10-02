#include "xar_bridge/religion_rite_governance12002_clergy.hpp"

#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>

namespace c = xar::ck3_12002;
namespace r = c::religion::clergy;
namespace {
template <std::size_t N> using Bytes = std::array<std::byte,N>;
template <typename Buffer,typename T>
void Put(Buffer &b,std::size_t at,T value) {
  std::memcpy(b.data()+at,&value,sizeof(value));
}
struct Fixture {
  Bytes<0xA8> state{};
  Bytes<0x28> jomini{};
  Bytes<0x1F8> players{};
  Bytes<0x78> player{};
  std::vector<std::byte> data = std::vector<std::byte>(0x22350);
  Bytes<0xE0> entry{};
  std::array<void *,1> entries{entry.data()};
  Bytes<0x30> characters{}, tasks{};
  Bytes<0xA0> character_slots{}, task_slots{};
  Bytes<0x1D8> owner{}, candidate{}, foreign_owner{};
  Bytes<0x240> landed{};
  Bytes<0x50> task{}, type{};
  Bytes<0x60> position{};
  std::array<std::int32_t,2> task_ids{task_id,task_id};
  void *state_ptr=state.data(), *jomini_ptr=jomini.data();
  void *characters_ptr=characters.data(), *tasks_ptr=tasks.data();
  static constexpr std::int32_t owner_id=0x03000004;
  static constexpr std::int32_t candidate_id=0x06000005;
  static constexpr std::int32_t foreign_owner_id=0x01000007;
  static constexpr std::int32_t task_id=0x02000006;
  int native_calls=0;
  bool position_value=true,character_value=true,reassign_value=true;
  bool foreign_context=false,drift=false,bad_arguments=false,deny_read=false;
  Fixture() {
    Put(state,8,std::int32_t{53175816}); Put(state,0x70,std::int32_t{2}); Put(state,0xA0,data.data());
    Put(jomini,0x18,players.data()); jomini[0x20]=std::byte{1};
    Put(players,0x1F0,std::int32_t{7}); Put(player,0x70,std::int32_t{7});
    Put(data,c::kPlayerCharacterManagerOffset+0x58,entries.data());
    Put(data,c::kPlayerCharacterManagerOffset+0x64,std::int32_t{1});
    Put(entry,0xD8,std::int32_t{7}); Put(entry,0xB0,owner_id);
    Put(characters,0x20,character_slots.data()); Put(characters,0x2C,std::int32_t{10});
    Put(character_slots,4*0x10+8,owner.data()); Put(owner,0x18,owner_id);
    Put(character_slots,5*0x10+8,candidate.data()); Put(candidate,0x18,candidate_id);
    Put(character_slots,7*0x10+8,foreign_owner.data()); Put(foreign_owner,0x18,foreign_owner_id);
    Put(owner,r::kCharacterRiteOffset,std::uint32_t{0});
    Put(candidate,r::kCharacterRiteOffset,std::uint32_t{0});
    Put(owner,r::kLandedOffset,landed.data());
    Put(landed,r::kTaskIdsOffset,task_ids.data()); Put(landed,r::kTaskCountOffset,std::int32_t{1});
    Put(tasks,0x20,task_slots.data()); Put(tasks,0x2C,std::int32_t{10});
    Put(task_slots,6*0x10+8,task.data()); Put(task,r::kTaskIdentityOffset,task_id);
    Put(task,r::kTaskTypeOffset,type.data()); Put(task,r::kTaskOwnerOffset,owner_id);
    Put(task,r::kTaskIncumbentOffset,std::int32_t{-1});
    Put(type,r::kTypePositionOffset,position.data());
    Put(position,r::kPositionKeyOffset,r::kPositionKey.data());
    Put(position,r::kPositionKeyOffset+0x10,std::uint64_t{r::kPositionKey.size()});
    Put(position,r::kPositionKeyOffset+0x18,std::uint64_t{31});
  }
};
Fixture *f=nullptr;
void *Player(void *) { return f->player.data(); }
void *CourtOwner(void *candidate) {
  if (candidate!=f->candidate.data()) f->bad_arguments=true;
  return f->foreign_context ? f->foreign_owner.data() : f->owner.data();
}
bool ValidPosition(void *position,std::int32_t owner) {
  ++f->native_calls;
  if (position!=f->position.data() || owner!=Fixture::owner_id) f->bad_arguments=true;
  return f->position_value;
}
bool ValidCharacter(void *position,std::int32_t candidate) {
  ++f->native_calls;
  if (position!=f->position.data() || candidate!=Fixture::candidate_id) f->bad_arguments=true;
  return f->character_value;
}
bool CanReassign(void *task,void *tooltip) {
  ++f->native_calls;
  if (task!=f->task.data() || tooltip!=nullptr) f->bad_arguments=true;
  if (f->drift) Put(f->state,8,std::int32_t{53175817});
  return f->reassign_value;
}
bool CanFire(void *, void *, void *, std::uint32_t, void *) { return true; }
bool Read(void *,const void *address,void *out,std::size_t size) noexcept {
  if (f->deny_read && address==f->owner.data()+r::kCharacterRiteOffset) return false;
  std::memcpy(out,address,size); return true;
}
r::Bindings Bind(Fixture &fixture) {
  f=&fixture;
  r::Bindings b{}; b.enabled=true; b.offline_fixture=true;
  b.executable_sha256=c::kExecutableSha256;
  b.core={true,&f->state_ptr,&f->jomini_ptr,&f->characters_ptr,&Player};
  b.task_storage_slot=&f->tasks_ptr;
  b.valid_position=&ValidPosition; b.valid_character=&ValidCharacter;
  b.can_reassign=&CanReassign; b.can_fire=&CanFire; b.court_owner=&CourtOwner;
  b.read_memory=&Read; return b;
}
int checks=0;
bool Check(bool value,const char *label) {
  ++checks; if(!value) std::cerr<<"FAIL "<<label<<'\n'; return value;
}
void Wire(const std::filesystem::path &dir,const char *name,const r::Observation &out) {
  if(!dir.empty()) std::ofstream(dir/name)<<r::SerializeClergyAppointment12002(out)<<'\n';
}
}

int main(int argc,char **argv) {
  const auto dir=argc>1 ? std::filesystem::path{argv[1]} : std::filesystem::path{};
  Fixture q; auto b=Bind(q); r::Observation out{};
  if(!Check(r::ReadClergyAppointment12002(b,70,Fixture::candidate_id,out),"actual player->task->final predicates") ||
     !Check(out.available && out.position_present && out.capture_epoch==70,"query source ready") ||
     !Check(out.active_task_id==Fixture::task_id && !out.incumbent_character_id,"full task generation and vacant seat") ||
     !Check(out.owner_rite_id==0U && out.candidate_rite_id==0U,"zero Rite is present") ||
     !Check(out.native_valid_position==true && out.native_valid_character==true && out.native_can_reassign==true,"all independent final true") ||
     !Check(q.native_calls==3 && !q.bad_arguments,"actual native ABI arguments") ||
     !Check(r::SerializeClergyAppointment12002(out).find("\"action_eligibility_complete\":false")!=std::string::npos,"not an action capability")) return 1;
  Wire(dir,"vacant-valid.json",out);
  Put(q.task,r::kTaskIncumbentOffset,Fixture::candidate_id); q.reassign_value=false;
  if(!Check(r::ReadClergyAppointment12002(b,71,Fixture::candidate_id,out),"fixed incumbent query") ||
     !Check(out.incumbent_character_id==Fixture::candidate_id && out.candidate_is_incumbent,"actual incumbent identity") ||
     !Check(out.native_valid_character==true && out.native_can_reassign==false,"native rejection preserved")) return 2;
  Wire(dir,"incumbent-reassign-denied.json",out);
  q.reassign_value=true; q.character_value=false;
  Put(q.candidate,r::kCharacterRiteOffset,std::uint32_t{0x83000003});
  if(!Check(r::ReadClergyAppointment12002(b,72,Fixture::candidate_id,out) && out.native_valid_character==false,"candidate final false is available") ||
     !Check(out.candidate_rite_id==0x83000003U && out.owner_rite_id==0U,"distinct Rite full references")) return 3;
  Wire(dir,"candidate-native-denied.json",out);
  q.foreign_context=true; q.character_value=true;
  if(!Check(r::ReadClergyAppointment12002(b,73,Fixture::candidate_id,out) && out.candidate_matches_owner_context==false &&
            out.candidate_court_owner_id==Fixture::foreign_owner_id && out.native_valid_character==true,
            "foreign context is separate from native candidate predicate")) return 4;
  Wire(dir,"foreign-context.json",out); q.foreign_context=false;
  const int before=q.native_calls;
  Put(q.landed,r::kTaskCountOffset,std::int32_t{0});
  if(!Check(r::ReadClergyAppointment12002(b,74,Fixture::candidate_id,out) && !out.position_present &&
            !out.native_valid_position && !out.native_valid_character && !out.native_can_reassign && q.native_calls==before,
            "observed absent seat does not invent boolean false or call native")) return 5;
  Wire(dir,"position-absent.json",out);
  Put(q.landed,r::kTaskCountOffset,std::int32_t{1});
  Put(q.candidate,0x18,Fixture::candidate_id+0x01000000);
  if(!Check(!r::ReadClergyAppointment12002(b,75,Fixture::candidate_id,out) && out.failure==r::Failure::candidate_unavailable,
            "same index different candidate generation rejected")) return 6;
  Wire(dir,"candidate-unavailable.json",out); Put(q.candidate,0x18,Fixture::candidate_id);
  Put(q.task,r::kTaskIdentityOffset,Fixture::task_id+0x01000000);
  if(!Check(!r::ReadClergyAppointment12002(b,76,Fixture::candidate_id,out) && out.failure==r::Failure::task_unavailable,
            "full task generation roundtrip")) return 7;
  Put(q.task,r::kTaskIdentityOffset,Fixture::task_id);
  Put(q.task,r::kTaskOwnerOffset,Fixture::foreign_owner_id);
  if(!Check(!r::ReadClergyAppointment12002(b,77,Fixture::candidate_id,out) && out.failure==r::Failure::task_unavailable,
            "task belongs actual player")) return 8;
  Put(q.task,r::kTaskOwnerOffset,Fixture::owner_id);
  Put(q.landed,r::kTaskCountOffset,std::int32_t{2});
  if(!Check(!r::ReadClergyAppointment12002(b,78,Fixture::candidate_id,out) && out.failure==r::Failure::task_unavailable,
            "duplicate actual chaplain seat is unavailable")) return 9;
  Put(q.landed,r::kTaskCountOffset,std::int32_t{1}); q.jomini[0x20]=std::byte{0};
  if(!Check(!r::ReadClergyAppointment12002(b,79,Fixture::candidate_id,out) && out.failure==r::Failure::not_paused,
            "existing paused owner requirement")) return 10;
  q.jomini[0x20]=std::byte{1}; q.deny_read=true;
  if(!Check(!r::ReadClergyAppointment12002(b,80,Fixture::candidate_id,out) && out.failure==r::Failure::candidate_context_unavailable,
            "failed Rite read is not zero")) return 11;
  q.deny_read=false; q.drift=true;
  if(!Check(!r::ReadClergyAppointment12002(b,81,Fixture::candidate_id,out) && out.failure==r::Failure::state_changed &&
            !out.native_valid_character && !out.native_can_reassign,"independent frame drift discards gates")) return 12;
  Wire(dir,"state-changed.json",out);
  const auto exact=r::BindClergyAppointmentImage12002(0x140000000,c::kExecutableSha256);
  if(!Check(exact.enabled && exact.core.enabled &&
            reinterpret_cast<std::uintptr_t>(exact.can_reassign)==0x1431B4980 &&
            reinterpret_cast<std::uintptr_t>(exact.valid_character)==0x1431BCF90 &&
            reinterpret_cast<std::uintptr_t>(exact.task_storage_slot)==0x145D1DEA0,
            "production binder final function addresses") ||
     !Check(!r::BindClergyAppointmentImage12002(0x140000000,"old").enabled &&
            !r::BindClergyAppointmentImage12002(0,c::kExecutableSha256).enabled,"exact build binding")) return 13;
  std::cout<<"PASS checks="<<checks<<" actual_reader=true actual_serializer=true live=false\n";
  return 0;
}
