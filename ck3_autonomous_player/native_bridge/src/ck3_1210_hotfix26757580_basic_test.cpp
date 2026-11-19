#include "xar_bridge/ck3_1210_adapter.hpp"
#include "xar_bridge/ck3_1210_core_frame_v1.hpp"
#include "xar_bridge/ck3_1210_core_control_v1.hpp"
#include "xar_bridge/ck3_1210_full_clock_request_v1.hpp"
#include "xar_bridge/ck3_1210_date_sentinel_request_v1.hpp"
#include "xar_bridge/ck3_1210_daily_final_hook_v1.hpp"
#include "xar_bridge/ck3_1210_date_sentinel_v1.hpp"
#include "xar_bridge/ck3_1210_thread_runtime.hpp"
#include "xar_bridge/ck3_1210_hotfix26757580_v1.hpp"
#include <windows.h>
#include <filesystem>
#include <fstream>
#define main FullBaselineMain36
#include "ck3_1210_full_snapshot_v1_test.cpp"
#undef main
#include "fresh_bridge_snapshot_support.inc"

namespace {
constexpr auto hotfix=ImageBuildV1::hotfix26757580;
const game::AdapterDescriptor descriptor{hotfix26757580::kAdapterId,kGameVersion,
    hotfix26757580::kExecutableSha256,"xar_checkpoint",{}};
void NewFixture(Fixture &f) {
  const auto base=std::uintptr_t{0x140000000};
  auto core=f.bindings.core;core.image_build=hotfix;
  f.bindings.core=core;
  f.bindings.foundation=BindActorFoundationImageV1(base,hotfix26757580::kExecutableSha256);
  f.bindings.event=BindCurrentEventSnapshotImageV1(base,hotfix26757580::kExecutableSha256);
  f.bindings.pending=BindPendingSnapshotImageV1(base,hotfix26757580::kExecutableSha256);
  f.bindings.military=BindMilitaryEmptyImageV1(base,hotfix26757580::kExecutableSha256);
  f.bindings.foundation.core=f.bindings.event.core=f.bindings.pending.core=f.bindings.military.core=core;
  f.bindings.event.get_current_event=&Current;f.bindings.event.selector_character_id_slot=&f.selector_character;
  f.bindings.pending.pending_storage_slot=&f.pending_slot;
  f.bindings.pending.is_pending_for_character=&PendingFor;f.bindings.pending.validate_reply=&Validate;
  f.bindings.military.unit_registry_slot=&f.unit_slot;f.bindings.military.war_registry_slot=&f.war_slot;
  f.Init();
  Put(f.data,0x113C0,f.bindings.pending.owner_manager_vtable);
  Put(f.data,0x11410,f.pending_slot);
}
void Save(const std::filesystem::path &dir,const char *name,const std::string &value) {
  const auto path=dir/name;Require(!std::filesystem::exists(path),"unique output");
  std::ofstream f(path,std::ios::binary);f<<value;Require(bool(f),"original formatter output");
}
struct PeCopy {
  struct Section {std::uint32_t va,bytes,offset;};
  std::ifstream f;std::vector<Section> sections;void *image=nullptr;
  template<class T>T At(std::uint64_t where) {T v{};f.seekg(static_cast<std::streamoff>(where));f.read(reinterpret_cast<char *>(&v),sizeof(v));Require(bool(f),"bounded PE header");return v;}
  explicit PeCopy(const std::filesystem::path &p):f(p,std::ios::binary) {
    Require(bool(f),"PE file open");const auto pe=At<std::uint32_t>(0x3C);
    Require(At<std::uint32_t>(pe)==0x4550 && At<std::uint32_t>(pe+8)==1795002872,"new PE signature/timestamp");
    const auto count=At<std::uint16_t>(pe+6),size=At<std::uint16_t>(pe+20);
    Require(At<std::uint64_t>(pe+24+24)==0x140000000ULL && At<std::uint32_t>(pe+24+56)==0x6FE6000,"new image bounds");
    for(std::uint16_t i=0;i<count;++i){const auto s=pe+24+size+std::uint32_t{i}*40;sections.push_back({At<std::uint32_t>(s+12),At<std::uint32_t>(s+16),At<std::uint32_t>(s+20)});}
    image=VirtualAlloc(nullptr,0x6FE6000,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE);Require(image!=nullptr,"RAM image only");
  }
  ~PeCopy(){if(image)VirtualFree(image,0,MEM_RELEASE);}
  void Span(std::uintptr_t rva,std::size_t n) {
    for(const auto &s:sections)if(rva>=s.va && rva-s.va+n<=s.bytes) {
      f.seekg(static_cast<std::streamoff>(s.offset+rva-s.va));f.read(static_cast<char *>(image)+rva,static_cast<std::streamsize>(n));Require(bool(f),"bounded actual PE span");return;
    }Require(false,"RVA file-backed span");
  }
};
}

int main(int argc,char **argv) {
  Require(argc==3,"EXE path and existing output dir required");
  IngameReadyWitnessV1 basic_witness{}; // BB3 never claims the old lifecycle witness.
  const std::filesystem::path out=argv[2];Require(std::filesystem::is_directory(out),"output directory");
  Require(game::IsCk3_1210BasicDescriptor(descriptor) && !game::IsCk3_1210Descriptor(descriptor),"basic/historical gate split");
  auto wrong=descriptor;wrong.executable_sha256=kExecutableSha256;
  Require(!game::IsCk3_1210BasicDescriptor(wrong),"mixed exact tuple rejected");
  const auto base=std::uintptr_t{0x140000000};
  const auto c=BindCoreImage(base,hotfix26757580::kExecutableSha256);
  Require(c.enabled && c.image_build==hotfix && reinterpret_cast<std::uintptr_t>(c.game_state_slot)==base+0x68B2FD0 &&
      reinterpret_cast<std::uintptr_t>(c.jomini_state_slot)==base+0x68B4A40 &&
      reinterpret_cast<std::uintptr_t>(c.character_storage_slot)==base+0x68A9868 &&
      reinterpret_cast<std::uintptr_t>(c.get_local_player)==base+0x3E66030,"new Core binding");
  const auto old=BindCoreImage(base,kExecutableSha256);
  Require(old.enabled && old.image_build==ImageBuildV1::original26622941 && old.game_state_slot!=c.game_state_slot,"historical profile preserved");
  Require(!BindCoreImage(base,"unknown").enabled,"unknown image denied");
  const auto commands=BindCommandImage(base,hotfix26757580::kExecutableSha256);
  Require(commands.enabled && commands.command_manager==reinterpret_cast<void *>(base+0x69DBAE0) &&
      reinterpret_cast<std::uintptr_t>(commands.queue_owned_command)==base+0x3E184D0 &&
      commands.pause_primary_vtable==base+0x4E8C908 && commands.pause_secondary_vtable==base+0x4E8C8D0 &&
      commands.set_speed_primary_vtable==base+0x4E8C838 && commands.set_speed_secondary_vtable==base+0x4E8CA38,"new queue and RTTI");
  const auto date=BindDateSentinelImageV1(base,hotfix26757580::kExecutableSha256);
  Require(date.exact_build_admitted && date.core.image_build==hotfix && date.command_manager==base+0x69DBAE0 &&
      date.worker_function==base+0x3E1DA10,"new worker metadata");

  Fixture f;NewFixture(f);game::Snapshot snapshot{};FullSnapshotDiagnosticsV1 d{};
  Require(ReadFullSnapshotV1(f.bindings,snapshot,d,basic_witness) && d.complete && d.completed_passes==2 &&
      snapshot.player_armies.empty() && snapshot.active_wars.empty() && !snapshot.has_active_event && d.army_state_calls_attempted==0,"actual hotfix RAM full reader");
  Save(out,"full-ram36.json",StateSnapshotFrame(snapshot,36,{}, {},"hotfix36-ram-full",&descriptor));
  CoreFrameObservationV1 co{};co.core_available=true;co.application_main_observed=true;
  Require(ReadCoreSnapshot(f.bindings.core,co.core),"independent real Core");
  Save(out,"core-ram36.json",SerializeCoreFrameCommandResultV1("hotfix36-core",co,hotfix));
  CoreControlResultV1 result{};result.status=CoreControlStatusV1::already_satisfied;
  Save(out,"clock-formatter36.json",SerializeCoreControlCommandResultV1("hotfix36-clock","pause-map",result,kFullClockControlResultSchemaV1,0,hotfix));
  result.status=CoreControlStatusV1::unavailable;
  Save(out,"exit-negative-formatter36.json",SerializeCoreControlCommandResultV1("hotfix36-exit",kApplicationExitStepV1,result,{},0,hotfix));
  {Fixture x;NewFixture(x);x.EventPresent();Require(!ReadFullSnapshotV1(x.bindings,snapshot,d,basic_witness) && x.selectors==0,"nonempty selector branch denied before native ABI");}
  {Fixture x;NewFixture(x);x.UnitPresent(x.actor_id);Require(!ReadFullSnapshotV1(x.bindings,snapshot,d,basic_witness),"owned nonempty Unit denied");}
  {Fixture x;NewFixture(x);x.WarPresent(true);Require(!ReadFullSnapshotV1(x.bindings,snapshot,d,basic_witness),"active player War denied");}
  {Fixture x;NewFixture(x);Put(x.data,0x11410,static_cast<void *>(nullptr));Require(!ReadFullSnapshotV1(x.bindings,snapshot,d,basic_witness),"new pending manager owner required");}
  {Fixture x;NewFixture(x);x.bindings.foundation.core.image_build=ImageBuildV1::original26622941;Require(!ReadFullSnapshotV1(x.bindings,snapshot,d,basic_witness),"mixed Core domain profile denied");}

  const std::string claim=std::string(R"({"type":"execute_step","protocol_version":1,"request_id":"hotfix36-clock","step":"pause-map","expected_revision":36,"full_snapshot_clock_control":{"schema":"ck3_1210_full_clock_control_v1","game_version":"1.21.0","executable_sha256":")")+hotfix26757580::kExecutableSha256+
      R"(","adapter_id":"ck3-1.21.0-26757580-msvc-x64","backend":"ck3-1.21.0-native-headless-main-thread","snapshot_id":"native:36","native_revision":36,"deadline_unix_ms":9007199254740993}})";
  FullClockRequestV1 parsed{};Require(ParseFullClockRequestV1(claim,parsed,hotfix) && !ParseFullClockRequestV1(claim,parsed),"profile-bound Full clock parser");

  PeCopy pe(argv[1]);
  // Only these file-backed windows are copied, never the executable body.
  const std::pair<std::uintptr_t,std::size_t> spans[]{
    {0x47051B0,32},{0x47051D9,23},{0x47078E8,14},{0x480F3DC,7},{0x44FF630,48},
    {0x893BD8,16},{0x438DB8D,22},{0x3F6D05A,47},{0x3F5B5B6,19},{0x3F5B609,8},
    {0x2EBF910,32},{0x14DECE0,32},{0x2E50270,32},{0x3F5BA40,32},{0x3F5BB05,16},
    {0x2E77B60,32},{0x60B2268+16,24},{0x51C17F0,24},{0x51C1818,24},{0x51BF3F0,16},
    {0x4B3E9D0,0x48},{0x4B3E998,0x30}};
  for(auto [at,n]:spans)pe.Span(at,n);
  const auto mapped=reinterpret_cast<std::uintptr_t>(pe.image);
  // File-backed vtable VAs receive the same base relocation as a mapped PE.
  // Code is only compared, never made executable or called.
  for(auto [at,n]:std::array<std::pair<std::uintptr_t,std::size_t>,2>{{{0x4B3E9D0,0x48},{0x4B3E998,0x30}}}) {
    for(std::size_t i=0;i<n;i+=8) {
      auto *cell=static_cast<std::byte *>(pe.image)+at+i;
      std::uintptr_t value=0;std::memcpy(&value,cell,8);
      if(value>=0x140000000ULL && value<0x146FE6000ULL) {
        value=mapped+value-0x140000000ULL;std::memcpy(cell,&value,8);
      }
    }
  }
  const auto env=BindThreadRuntimeImage(mapped,hotfix26757580::kExecutableSha256);
  Require(env.exact_build_admitted && env.build_profile && env.build_profile->verify_pump_anchors(mapped),"actual new mapped thread pin guards");
  const auto full=BindFullSnapshotImageV1(mapped,hotfix26757580::kExecutableSha256);
  Require(full.exact_build_admitted && !full.enable_army_base,"actual new mapped full pins and empty-only binding");
  Require(BindApplicationExitImageV1(mapped,hotfix26757580::kExecutableSha256).enabled,"actual new mapped exit pins");
  auto daily=BindDailyFinalHookImageV1(mapped,hotfix26757580::kExecutableSha256);DailyFinalHookStateV1 life{};DailyFinalHookEnvironmentV1 de{};
  de.cold_quiescence_proven=true;
  Require(InstallDailyFinalHookV1(life,daily,de,+[](void *) noexcept {},nullptr)==DailyFinalHookResultV1::installed,"new mapped daily RTTI/pipeline metadata");
  Require(UninstallDailyFinalHookV1(life)==DailyFinalHookResultV1::uninstalled,"RAM-only hook restores copied pointer");
  std::cout<<"PASS new exact bb3 basic profile; real RAM Full/Core; tuple parsers; bounded actual PE pin/RTTI checks; no Game code executed\n";
  return 0;
}
