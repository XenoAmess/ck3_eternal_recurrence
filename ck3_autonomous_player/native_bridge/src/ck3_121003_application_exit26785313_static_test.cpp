#define main ExistingCurrentCoreStaticMain
#include "ck3_121003_readonly26785313_static_test.cpp"
#undef main
#include "ck3_121003_application_exit26785313_v1.cpp"
#include "ck3_121003_application_exit26785313_wire_v1.cpp"
#include "ck3_1210_application_exit_v1.cpp"
#include "ck3_1210_core_control_request_v1.cpp"
#include "ck3_1210_core_frame_v1.cpp"
#include "ck3_121003_personal_gold26785313_v2.cpp"

namespace {
std::string CurrentExitRequest267() {
  return std::string(R"({"type":"execute_step","protocol_version":1,"request_id":"exit-267-1","step":"normal-exit-application-v1","expected_revision":0,"core_control_deadline_unix_ms":4102444800000,"arguments":{},"core_application_exit":{"schema":"ck3_1210_application_exit_v1","game_version":")")+
      f::kGameVersion+R"(","executable_sha256":")"+f::kExecutableSha256+R"(","adapter_id":")"+f::kAdapterId+
      R"(","backend":")"+f::kApplicationExitBackend267V1+
      R"(","date_raw":53176992,"speed":3,"paused":true,"local_player_id":1,"map_ready":true,"has_played_character":true,"played_character_id":-16777215,"played_character_alive":true}})";
}
std::string ExitReplace(std::string value,std::string_view a,std::string_view b) {
  const auto pos=value.find(a);Require(pos!=std::string::npos,"exit fixture replacement");value.replace(pos,a.size(),b);return value;
}
void ExitWriteFixture(const std::filesystem::path &p,const std::string &s) {
  std::ofstream out(p,std::ios::binary);Require(bool(out),"exit golden file");out<<s<<'\n';Require(bool(out),"exit golden written");
}
}
int main(int argc,char **argv) {
  try {
    Require(argc==2||(argc==4&&std::string_view(argv[2])=="--emit-exit-fixtures"),"image mode [--emit-exit-fixtures ownedDir]");
    Require(ExistingCurrentCoreStaticMain(2,argv)==0,"original Core/raw/root boundary suite still passes");
    const bool synthetic=std::string_view(argv[1])=="--synthetic-image";
    const auto image=synthetic?std::make_unique<PeWindows>():std::make_unique<PeWindows>(argv[1]);
    const auto base=reinterpret_cast<std::uintptr_t>(image->image);
    Require(f::VerifyApplicationExitImage267V1(base),"whole current quit body+exact RTTI guards");
    Require(!c::BindApplicationExitImageV1(base,f::kExecutableSha256).enabled,"old exit hash mapper stays closed");
    Require(!f::BindApplicationExitImage267V1(base,"old").enabled,"mixed exit SHA denied");
    Fixture fixture;Put(fixture.players,0,base+f::kGuiRootApplicationVtableRvaV1);
    auto*slot=static_cast<unsigned char*>(image->image)+f::kJominiStateSlotRva;
    void *jomini=fixture.jomini.data();std::memcpy(slot,&jomini,sizeof(jomini));
    const auto binding=f::BindApplicationExitImage267V1(base,f::kExecutableSha256);
    Require(binding.enabled&&reinterpret_cast<std::uintptr_t>(binding.application_slot)==reinterpret_cast<std::uintptr_t>(fixture.jomini.data())+0x18&&
        reinterpret_cast<std::uintptr_t>(binding.request_quit)==base+f::kApplicationQuitRequestRva267V1&&
        binding.expected_application_vtable==base+f::kGuiRootApplicationVtableRvaV1&&binding.alternative_application_vtable==0,
        "independent current dynamic app slot and function binding; no native function invoked");
    Put(fixture.players,0,base+0x4AFA620);Require(!f::BindApplicationExitImage267V1(base,f::kExecutableSha256).enabled,"old application vtable refused");Put(fixture.players,0,base+f::kGuiRootApplicationVtableRvaV1);
    auto *pin=static_cast<unsigned char*>(image->image)+f::ApplicationExitImagePins267V1()[0].rva;*pin^=1;
    Require(!f::VerifyApplicationExitImage267V1(base)&&!f::BindApplicationExitImage267V1(base,f::kExecutableSha256).enabled,"quit body tamper denies binding");*pin^=1;
    const auto request=CurrentExitRequest267();c::CoreControlRequestV1 parsed;
    Require(f::ParseApplicationExitRequest267V1(request,parsed)&&parsed.operation==c::CoreControlOperationV1::application_exit&&
        parsed.expected.played_character_id==-16777215,"exact current exit claim preserves signed ID");
    Require(!c::ParseCoreControlRequestV1(request,parsed,c::ImageBuildV1::unknown),"current tuple not added to old control parser");
    for(const auto &pair:std::array<std::pair<std::string_view,std::string_view>,10>{{
      {"\"paused\":true","\"paused\":false"},{"\"map_ready\":true","\"map_ready\":false"},
      {"\"played_character_id\":-16777215","\"played_character_id\":-1"},
      {"\"played_character_id\":-16777215","\"played_character_id\":2147483648"},
      {"\"played_character_id\":-16777215","\"played_character_id\":-16777215.0"},
      {"\"expected_revision\":0","\"expected_revision\":1"},
      {"\"game_version\":\"1.21.0.3\"","\"game_version\":\"1.21.0\""},
      {"\"speed\":3","\"speed\":3,\"speed\":3"},
      {"\"arguments\":{}","\"arguments\":{\"address\":1}"},
      {"\"backend\":\"ck3-1.21.0.3-native-headless-main-thread\"","\"backend\":\"ck3-1.21.0-native-headless-main-thread\""}
    }})Require(!f::ParseApplicationExitRequest267V1(ExitReplace(request,pair.first,pair.second),parsed),"wrong/duplicate/extra exit claim refused");
    Require(f::ParseApplicationExitRequest267V1(request,parsed),"request restored");
    m::MainThreadQueryMailboxV1 mailbox;mailbox.offline_fixture=true;c::ApplicationExitSessionV1 session;
    f::ApplicationExitContext267V1 query;query.bindings=f::NoGameBindings(base,fixture.Core());query.mailbox=&mailbox;
    query.ticket.sequence=1;query.request=parsed;query.session=&session;query.connection_generation=7;
    f::ArmApplicationExitDeadline267V1(query);Require(query.monotonic_deadline_ms>GetTickCount64()&&query.monotonic_deadline_ms-GetTickCount64()<=8000,"original wall deadline also bounded by monotonic8s");
    Require(f::ExecuteApplicationExitOnOwner267V1(&query,{})&&!query.result.effect_attempted&&!session.claimed.load()&&fixture.calls==0,
        "NoGame fixture cannot dispatch current quit or claim a real owner");
    const auto unavailable=f::SerializeApplicationExitResult267V1("exit-267-1",query.result);
    mailbox.offline_fixture=false;
    Require(f::ExecuteApplicationExitOnOwner267V1(&query,{})&&!query.result.effect_attempted&&!session.claimed.load()&&fixture.calls==0,
        "fixture binding cannot become real secondary owner");
    query.request.deadline_unix_ms=1;f::ArmApplicationExitDeadline267V1(query);Require(query.monotonic_deadline_ms==0,"expired absolute deadline not refreshed");
    Require(f::ExecuteApplicationExitOnOwner267V1(&query,{})&&query.result.status==c::CoreControlStatusV1::expired&&!session.claimed.load(),"expired read refuses before claim");
    const auto &descriptor=f::PersonalGoldAdapterDescriptorV2();
    Require(descriptor.capabilities.size()==3&&f::ApplicationExitRouteEnabled267V1(descriptor),"only Core/Gold/normalexit current caps with optins");
    for(const auto cap:descriptor.capabilities)Require(cap!=c::kCoreControlCapabilityV1&&cap!="game.state.snapshot"&&cap!="game.command.save-checkpoint","no Full/clock/save/GUI permission from quit");
    c::CoreControlResultV1 requested;requested.status=c::CoreControlStatusV1::exit_requested;requested.effect_attempted=true;
    c::CoreControlResultV1 unknown;unknown.status=c::CoreControlStatusV1::indeterminate;unknown.effect_attempted=true;
    const auto positive=f::SerializeApplicationExitResult267V1("exit-267-1",requested);
    const auto indeterminate=f::SerializeApplicationExitResult267V1("exit-267-1",unknown);
    Require(positive.find("\"normal_exit_confirmed\":false")!=std::string::npos&&positive.find("\"physical_save_confirmed\":false")!=std::string::npos&&
        indeterminate.find("\"dispatch_status\":\"indeterminate\"")!=std::string::npos,"ACK never claims physical save or natural exit");
    if(argc==4) {
      const std::filesystem::path out=argv[3];std::filesystem::create_directories(out);
      ExitWriteFixture(out/"request-current267.json",request);ExitWriteFixture(out/"unavailable-NoGame.json",unavailable);
      ExitWriteFixture(out/"requested-SYNTHETIC-DATA.json",positive);ExitWriteFixture(out/"indeterminate-SYNTHETIC-DATA.json",indeterminate);
      ExitWriteFixture(out/"qualifier.json",R"({"scope":"C++ current-exit producer and NoGame binding/denial only","native_request_quit_call":"NOT_RUN","actual_natural_exit_noSave_MainOwner":"NOT_RUN","positive_and_unknown_ACK":"SYNTHETIC DATA; no replay authority"})");
    }
    std::cout<<"PASS current quit exact static binding/secondary owner refusal/parser/ACK; NO GAME CALL/SAVE/NATURAL EXIT qualification\n";return 0;
  }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}
}
