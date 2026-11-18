#include "xar_bridge/ck3_1210_decision_candidates_v1.hpp"
#include <array>
#include <bit>
#include <cstring>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>
#include <utility>

namespace {
using namespace xar::ck3_1210;
void Require(bool value, const char *message) { if (!value) throw std::runtime_error(message); }
struct Region { std::uint64_t address; std::vector<std::byte> bytes; };
struct Memory {
  std::vector<Region> regions;
  std::uint64_t deny = 0, mutate = 0;
  std::size_t copy_calls = 0, mutate_hits = 0;
  std::byte replacement{0};
  void Add(std::uint64_t address, std::size_t size) { regions.push_back({address, std::vector<std::byte>(size)}); }
  template <class T> void Put(std::uint64_t address, const T &value) {
    for (auto &region : regions) {
      if (address >= region.address && address - region.address <= region.bytes.size() &&
          sizeof(T) <= region.bytes.size() - static_cast<std::size_t>(address - region.address)) {
        std::memcpy(region.bytes.data() + (address - region.address), &value, sizeof value); return;
      }
    }
    throw std::runtime_error("fixture Put outside region");
  }
  bool Copy(std::uint64_t address, void *destination, std::size_t size) noexcept {
    ++copy_calls;
    if (address == deny) return false;
    for (auto &region : regions) {
      if (address >= region.address && address - region.address <= region.bytes.size() &&
          size <= region.bytes.size() - static_cast<std::size_t>(address - region.address)) {
        const auto offset = static_cast<std::size_t>(address - region.address);
        if (address == mutate && ++mutate_hits == 2) region.bytes[offset] = replacement;
        std::memcpy(destination, region.bytes.data() + offset, size); return true;
      }
    }
    return false;
  }
};
struct Fixture {
  static constexpr std::uint64_t base = 0x140000000ULL, list = 9007199254740993ULL;
  static constexpr std::uint64_t database = list + 0x1000, groups = list + 0x3000, rows = list + 0x4000;
  static constexpr std::uint64_t definition_a = list + 0x5000, definition_b = list + 0x6000, pool = list + 0x7000;
  static constexpr std::uint64_t storage = list + 0x8000, slots = list + 0x9000, actor = list + 0xA000;
  static constexpr std::uint64_t remapped = list + 0xB000, frame = list + 0xC000;
  static constexpr std::int32_t actor_id = std::bit_cast<std::int32_t>(0x81000001U);
  static constexpr std::int32_t remapped_id = std::bit_cast<std::int32_t>(0x82000002U);
  Memory memory;
  DecisionCandidateBindingsV1 bindings{};
  DecisionCandidateReadContextV1 context{};
  DecisionCandidateCaptureV1 current_metadata{};
  std::size_t capture_calls = 0;
  bool change_date = false, change_owner = false, change_actor = false, current_failure = false;

  Fixture() {
    for (auto pair : std::array<std::pair<std::uint64_t, std::size_t>, 12>{{
        {list,0x300},{database,0x80},{groups,0x20},{rows,0x40},{definition_a,0x40},{definition_b,0x40},
        {pool,0x18},{storage,0x40},{slots,0x30},{actor,0x1D8},{remapped,0x1D8},{frame,0x28}}}) memory.Add(pair.first,pair.second);
    memory.Add(base + 0x6A66790,8); memory.Add(base + 0x5D50448,4); memory.Add(base + kCharacterStorageSlotRva,8);
    Type(0x4BFAB30,0x52EEC58,0x62225F0); Type(0x4FCD288,0x5776DC0,0x5F4A6E8); Type(0x5000638,0x57E2B60,0x5EBEB80);
    memory.Put(list,base+0x4BFAB30); memory.Put(database,base+0x4FCD288);
    memory.Put(definition_a,base+0x5000638); memory.Put(definition_b,base+0x5000638);
    memory.Put(definition_a+0x38,std::uint32_t{0x4744624F}); memory.Put(definition_b+0x38,std::uint32_t{0x4744624F});
    memory.Put(base+0x6A66790,database); memory.Put(base+0x5D50448,actor_id); memory.Put(base+kCharacterStorageSlotRva,storage);
    memory.Put(storage+0x20,slots); memory.Put(storage+0x2C,std::int32_t{3});
    memory.Put(slots+0x18,actor); memory.Put(slots+0x28,remapped);
    memory.Put(actor+0x18,actor_id); memory.Put(actor+0x1C,std::uint32_t{0x43686172});
    memory.Put(remapped+0x18,remapped_id); memory.Put(remapped+0x1C,std::uint32_t{0x43686172});
    // Raw cache membership is retained even for a now-dead remapped actor;
    // the collector only resolves the full generation, never a legal gate.
    memory.Put(remapped+0x1D0,std::uint64_t{1});
    Vector(list+0x260,groups,1); memory.Put(groups,std::uint64_t{0x123456}); Vector(groups+8,rows,2);
    Row(rows,definition_a,actor_id,255,UINT64_MAX); Row(rows+0x20,definition_b,remapped_id,0,0);
    Vector(database+0x50,pool,3); memory.Put(pool,definition_b); memory.Put(pool+8,definition_a); memory.Put(pool+16,definition_b);
    auto &capture=context.expected;
    capture.frame={"software-decision-data","software-session",4294967295U,UINT64_MAX,UINT64_MAX,31,-1234,actor_id};
    capture.producer_source={"software-data:constructed-memory","aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",1};
    capture.source=DecisionCandidateSourceV1::gui_cache; capture.owner_held=true; capture.paused_application_main_owner_held=true;
    capture.owner_thread_id=7; capture.capture_epoch=UINT64_MAX; capture.owner_address=list;
    current_metadata=capture; context.source_pins_admitted=true; context.read_current_capture=Current; context.current_capture_context=this;
    memory.Put(frame,std::int32_t{-1234}); memory.Put(frame+4,actor_id); memory.Put(frame+8,list);
    memory.Put(frame+16,UINT64_MAX); memory.Put(frame+24,std::uint32_t{7}); memory.Put(frame+28,std::uint8_t{1});
    bindings=BindDecisionCandidateImageV1(base,kExecutableSha256);
  }
  void Type(std::uint64_t vt,std::uint64_t col,std::uint32_t td) {
    memory.Add(base+vt-8,8); memory.Add(base+col,24); memory.Put(base+vt-8,base+col);
    memory.Put(base+col,std::array<std::uint32_t,6>{1,0,0,td,0,static_cast<std::uint32_t>(col)});
  }
  void Vector(std::uint64_t address,std::uint64_t data,std::int32_t count) {
    memory.Put(address,data); memory.Put(address+8,count); memory.Put(address+12,count); memory.Put(address+16,std::uint64_t{0x123});
  }
  void Row(std::uint64_t address,std::uint64_t definition,std::int32_t id,std::uint8_t enabled,std::uint64_t parameter) {
    memory.Put(address,definition); memory.Put(address+8,parameter); memory.Put(address+0x10,id);
    memory.Put(address+0x14,enabled); memory.Put(address+0x18,list);
  }
  void DatabaseMode() {
    context.expected.source=DecisionCandidateSourceV1::database_pool; context.expected.owner_address=database;
    current_metadata=context.expected; memory.Put(frame+8,database);
  }
  static bool Copy(void *context,std::uint64_t address,void *destination,std::size_t size) noexcept {
    return static_cast<Fixture *>(context)->memory.Copy(address,destination,size);
  }
  static bool Current(void *context,DecisionCandidateCaptureV1 &capture) noexcept {
    auto &f=*static_cast<Fixture *>(context);
    try {
      ++f.capture_calls;
      if (f.current_failure) return false;
      if (f.capture_calls==2 && f.change_date) f.memory.Put(frame,std::int32_t{-1233});
      if (f.capture_calls==2 && f.change_owner) f.memory.Put(frame+8,list+1);
      if (f.capture_calls==2 && f.change_actor) f.memory.Put(frame+4,remapped_id);
      capture=f.current_metadata; std::uint8_t held=0;
      if (!f.memory.Copy(frame,&capture.frame.date_raw,4) || !f.memory.Copy(frame+4,&capture.frame.snapshot_actor_character_id,4) ||
          !f.memory.Copy(frame+8,&capture.owner_address,8) || !f.memory.Copy(frame+16,&capture.capture_epoch,8) ||
          !f.memory.Copy(frame+24,&capture.owner_thread_id,4) || !f.memory.Copy(frame+28,&held,1)) return false;
      capture.paused_application_main_owner_held=held==1; return true;
    } catch (...) { return false; }
  }
  bool Read(DecisionCandidatesObservationV1 &out) { return ReadDecisionCandidatesV1(bindings,context,{this,Copy},out); }
};
std::string Wire(const DecisionCandidatesObservationV1 &observation) {
  std::string output; Require(SerializeDecisionCandidatesV1(observation,output),"serializer refused valid metadata"); return output;
}
void Failed(Fixture &fixture,DecisionCandidateReasonV1 reason) {
  DecisionCandidatesObservationV1 out; out.completed=true; out.candidates.resize(1);
  Require(!fixture.Read(out),"invalid memory/capture was accepted"); Require(!out.completed && out.candidates.empty(),"failed scan leaked rows");
  Require(out.unavailable_reason==reason,"failure reason changed"); const auto wire=Wire(out);
  Require(wire.find("\"status\":\"unavailable\"")!=std::string::npos && wire.find("\"candidates\":null")!=std::string::npos,"failed scan became empty available rows");
}
void ActualGuiReaderAndFormatter() {
  Fixture f; DecisionCandidatesObservationV1 out;
  Require(f.Read(out),"GUI fixture read failed"); Require(out.completed && out.candidates.size()==2 && f.capture_calls==3,"GUI read/capture count");
  Require(out.candidates[0].cached_enabled_byte==255 && out.candidates[1].cached_enabled_byte==0,"cached byte was converted to availability");
  Require(out.candidates[1].row_actor_character_id==Fixture::remapped_id && out.candidates[1].row_actor_character_id!=out.capture.frame.snapshot_actor_character_id,"remapped actor was replaced");
  Require(out.candidates[0].parameter_address==UINT64_MAX && !out.candidates[0].definition.key,"raw parameter/null key semantics changed");
  const auto wire=Wire(out);
  for (const char *fragment : {"\"read_only\":true","\"action_qualified\":false","\"complete_snapshot\":false","\"parameter_address\":\"18446744073709551615\"","\"creation_filetime\":\"18446744073709551615\"","\"owner_address\":\"9007199254740993\"","\"command_availability\":{\"status\":\"unobserved\",\"reason\":\"parameter_scope_unverified\"}","\"key\":null"})
    Require(wire.find(fragment)!=std::string::npos,"exact serializer field missing");
  Require(wire.find("can_execute")==std::string::npos && wire.find("\"available\"")==std::string::npos,"formatter minted availability");
}
void ActualDatabasePoolReader() {
  Fixture f; f.DatabaseMode(); DecisionCandidatesObservationV1 out;
  f.memory.Put(Fixture::base+0x5D50448,std::int32_t{7});
  Require(f.Read(out) && out.candidates.size()==3 && !out.gui_global_actor_character_id,"DB must not consume GUI actor/cache");
  Require(out.candidates[0].definition.address==Fixture::definition_b && out.candidates[1].definition.address==Fixture::definition_a && out.candidates[2].definition.address==Fixture::definition_b,"DB order/duplicate definition records changed");
  const auto wire=Wire(out);
  Require(wire.find("database_definitions_0x50_count_0x5c")!=std::string::npos && wire.find("\"database_index\":2")!=std::string::npos && wire.find("\"gui_global_actor_character_id\":null")!=std::string::npos,"DB formatter source mismatch");
  Require(wire.find("\"reason\":\"not_queried\"")!=std::string::npos && wire.find("cached_enabled_byte")==std::string::npos,"DB gained GUI/availability fields");
}
void EmptyIsAnObservedEmptyScan() {
  for (bool db : {false,true}) {
    Fixture f; if (db) f.DatabaseMode();
    f.Vector((db ? Fixture::database+0x50 : Fixture::list+0x260),0,0);
    DecisionCandidatesObservationV1 out; Require(f.Read(out) && out.candidates.empty(),"real empty scan rejected");
    Require(Wire(out).find("\"candidates\":[]")!=std::string::npos,"empty scan collapsed to null");
  }
}
void AdmissionAndCaptureDrift() {
  { Fixture f; f.context.source_pins_admitted=false; Failed(f,DecisionCandidateReasonV1::source_pins_unavailable); Require(f.memory.copy_calls==0,"unadmitted source was read"); }
  { Fixture f; f.bindings=BindDecisionCandidateImageV1(Fixture::base,"wrong"); Failed(f,DecisionCandidateReasonV1::source_pins_unavailable); }
  { Fixture f; f.context.expected.owner_held=false; Failed(f,DecisionCandidateReasonV1::owner_not_held); }
  { Fixture f; f.context.expected.paused_application_main_owner_held=false; Failed(f,DecisionCandidateReasonV1::owner_not_held); }
  { Fixture f; f.context.read_current_capture=nullptr; Failed(f,DecisionCandidateReasonV1::native_read_unavailable); }
  { Fixture f; f.change_date=true; Failed(f,DecisionCandidateReasonV1::frame_not_current); }
  { Fixture f; f.change_owner=true; Failed(f,DecisionCandidateReasonV1::frame_not_current); }
  { Fixture f; f.change_actor=true; Failed(f,DecisionCandidateReasonV1::frame_not_current); }
  { Fixture f; f.current_failure=true; Failed(f,DecisionCandidateReasonV1::frame_not_current); }
  { Fixture f; f.memory.mutate=Fixture::rows+0x14; f.memory.replacement=std::byte{1}; Failed(f,DecisionCandidateReasonV1::frame_not_current); }
}
void BadSourceMemoryNeverBecomesPartialSuccess() {
  { Fixture f; f.memory.Put(Fixture::base+0x5D50448,Fixture::remapped_id); Failed(f,DecisionCandidateReasonV1::gui_actor_differs_from_snapshot); }
  { Fixture f; f.memory.Put(Fixture::rows+0x18,Fixture::list+1); Failed(f,DecisionCandidateReasonV1::native_read_unavailable); }
  { Fixture f; f.memory.Put(Fixture::remapped+0x18,std::bit_cast<std::int32_t>(0x83000002U)); Failed(f,DecisionCandidateReasonV1::native_read_unavailable); }
  { Fixture f; f.memory.Put(Fixture::list+0x26C,std::int32_t{65}); Failed(f,DecisionCandidateReasonV1::native_read_unavailable); }
  { Fixture f; f.memory.Put(Fixture::groups+0x14,std::int32_t{2049}); Failed(f,DecisionCandidateReasonV1::native_read_unavailable); }
  { Fixture f; f.memory.deny=Fixture::rows+0x20; Failed(f,DecisionCandidateReasonV1::native_read_unavailable); }
  { Fixture f; f.memory.Put(Fixture::definition_a+0x38,std::uint32_t{0}); Failed(f,DecisionCandidateReasonV1::native_read_unavailable); }
  { Fixture f; f.memory.Put(Fixture::base+0x52EEC58+12,std::uint32_t{0x62225F1}); Failed(f,DecisionCandidateReasonV1::native_read_unavailable); }
  { Fixture f; f.memory.Put(Fixture::list+0x260,UINT64_MAX-1); Failed(f,DecisionCandidateReasonV1::native_read_unavailable); }
  { Fixture f; f.DatabaseMode(); f.memory.Put(Fixture::base+0x6A66790,Fixture::database+1); Failed(f,DecisionCandidateReasonV1::native_read_unavailable); }
  { Fixture f; f.DatabaseMode(); f.Vector(Fixture::database+0x50,Fixture::pool,4097); Failed(f,DecisionCandidateReasonV1::native_read_unavailable); }
  { Fixture f; f.DatabaseMode(); f.memory.Put(Fixture::database+0x58,std::int32_t{-1}); Failed(f,DecisionCandidateReasonV1::native_read_unavailable); }
  { Fixture f; std::int32_t legacy_count=0; Require(f.memory.Copy(Fixture::list+0x264,&legacy_count,4),"legacy diagnostic read");
    Require(legacy_count>64,"constructed legacy header must be invalid"); DecisionCandidatesObservationV1 out;
    Require(f.Read(out) && out.candidates.size()==2,"reader borrowed legacy +258 header"); }
}
void SerializerIndependentlyRejectsInconsistentDtos() {
  Fixture f; DecisionCandidatesObservationV1 out; Require(f.Read(out),"fixture read");
  out.candidates[0].gui_owner_address++; Require(Wire(out).find("\"candidates\":null")!=std::string::npos,"forged DTO owner admitted");
  Require(f.Read(out),"fixture re-read"); out.candidates.push_back(out.candidates[0]);
  Require(Wire(out).find("\"candidates\":null")!=std::string::npos,"duplicate position admitted");
  Require(f.Read(out),"fixture re-read"); out.capture.frame.machine_id="invalid.machine";
  std::string wire="stale"; Require(!SerializeDecisionCandidatesV1(out,wire) && wire.empty(),"invalid outer metadata produced packet");
  Require(f.Read(out),"fixture re-read"); out.capture.producer_source.bytes=9007199254740992ULL;
  Require(!SerializeDecisionCandidatesV1(out,wire) && wire.empty(),"unsafe numeric source bytes admitted");
  Require(f.Read(out),"fixture re-read"); out.capture.producer_source.path="fixture:\n\"escaped";
  Require(Wire(out).find(std::string("fixture:") + static_cast<char>(92) + "u000a" + static_cast<char>(92) + static_cast<char>(34) + "escaped")!=std::string::npos,"metadata JSON escaping changed");
  Require(f.Read(out),"fixture re-read"); out.candidates.clear();
  for (std::uint32_t g=0;g<2;++g) for (std::uint32_t r=0;r<2048;++r) {
    DecisionCandidateRowV1 row; row.group_index=g; row.row_index=r; row.definition.address=Fixture::definition_a;
    row.gui_owner_address=Fixture::list; row.row_actor_character_id=Fixture::remapped_id;
    row.command_unobserved_reason=DecisionCandidateReasonV1::parameter_scope_unverified; out.candidates.push_back(row);
  }
  wire=Wire(out); Require(wire.size()<=262144 && wire.find("\"candidates\":null")!=std::string::npos,"oversize data silently truncated");
}
} // namespace
int main(int argc,char **argv) {
  try {
    // Owner can pipe this REAL collector->formatter packet directly into the
    // frozen Java codec. No hand-built packet or engine state is substituted.
    if (argc==2 && std::string(argv[1])=="--emit-gui") {
      Fixture f; DecisionCandidatesObservationV1 out; Require(f.Read(out),"GUI emit read"); std::cout<<Wire(out)<<'\n'; return 0;
    }
    if (argc==2 && std::string(argv[1])=="--emit-db") {
      Fixture f; f.DatabaseMode(); DecisionCandidatesObservationV1 out; Require(f.Read(out),"DB emit read"); std::cout<<Wire(out)<<'\n'; return 0;
    }
    ActualGuiReaderAndFormatter(); ActualDatabasePoolReader(); EmptyIsAnObservedEmptyScan();
    AdmissionAndCaptureDrift(); BadSourceMemoryNeverBecomesPartialSuccess(); SerializerIndependentlyRejectsInconsistentDtos();
    std::cout<<"decision candidates pure-memory reader/serializer fixtures passed\n"; return 0;
  } catch (const std::exception &error) { std::cerr<<error.what()<<'\n'; return 1; }
}
