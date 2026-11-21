#define main PreviousAdmission125Main
#include "admission125_factory_test.cpp"
#undef main
// This TU uses the real production controller/binder, not a shadow binder.
#include "ck3_1210_date_sentinel_v1.cpp"
#include "xar_bridge/ck3_1210_full_clock_request_v1.hpp"
#include "xar_bridge/ck3_1210_date_sentinel_request_v1.hpp"
#include "xar_bridge/ck3_121003_full111_rvas.hpp"
namespace {
std::string ArmPayload131(std::string_view version,std::string_view sha){
 std::string step="research-arm-tactical-daily-sentinel-v1-53179344-to-53179368-speed-5-mode-terminal-a-0";
 return "{\"type\":\"execute_step\",\"protocol_version\":1,\"request_id\":\"own131\",\"step\":\""+step+"\",\"expected_revision\":7,\"date_sentinel_arm\":{\"schema\":\"ck3_1210_date_sentinel_arm_v1\",\"game_version\":\""+std::string(version)+"\",\"executable_sha256\":\""+std::string(sha)+"\",\"adapter_id\":\"ck3-1.21.0.3-26785313-full111-msvc-x64\",\"backend\":\"ck3-1.21.0.3-native-headless-main-thread\",\"snapshot_id\":\"native:7\",\"native_revision\":7,\"deadline_unix_ms\":2000000}}";
}
template<class A>void Pin131(Image &image,std::uintptr_t oldRva,const A &bytes){
 const auto r=xar::ck3_1210::full111_rvas::Lookup(oldRva);Need(r!=0,"real current RVA mapping");image.commit(r,bytes.size());std::memcpy(reinterpret_cast<void*>(image.base+r),bytes.data(),bytes.size());
}
}
int main(){try{
 using namespace xar::ck3_1210;
 Image image(true);auto adapter=xar::game::CreateCk3_1210AdapterForImage125(b::kExecutableSha256,image.base);
 Need(adapter&&adapter->enabled(),"actual current Factory admitted");
 const auto step="research-arm-tactical-daily-sentinel-v1-53179344-to-53179368-speed-5-mode-terminal-a-0";
 Need(adapter->supports_step(step),"actual supportStep ARM");
 Need(adapter->supports_step("research-query-tactical-daily-sentinel-v1"),"actual status cap");
 Need(adapter->supports_step("research-cancel-tactical-daily-sentinel-v1-generation-1"),"actual cancel cap");
 Need(!adapter->supports_step("research-arm-tactical-daily-sentinel-v1-53179344-to-53179368-speed-5-mode-decision-a-0"),"no decision-mode expansion");
 DateSentinelArmRequestV1 request{};
 Need(ParseDateSentinelArmRequestV1(ArmPayload131("1.21.0.3",b::kExecutableSha256),request,ImageBuildV1::full11126785313),"actual current tuple/step parser");
 Need(request.starting_date_raw==53179344&&request.target_date_raw==53179368&&request.native_revision==7,"actual parsed target/revision");
 Need(!ParseDateSentinelArmRequestV1(ArmPayload131("1.21.0",b::kExecutableSha256),request,ImageBuildV1::full11126785313),"oldforeign version rejected");
 Need(!ParseDateSentinelArmRequestV1(ArmPayload131("1.21.0.3",std::string(64,'0')),request,ImageBuildV1::full11126785313),"wrong hash rejected");
 auto wrong=xar::game::CreateCk3_1210AdapterForImage125("NOT_A_BUILD",image.base);Need(!wrong->enabled()&&!wrong->supports_step(step),"unsupported factory cannot acquire cap");
 Pin131(image,kPauseRva,full111_pins::kPauseEntry);Pin131(image,kWorkerRva,kConsumerEntry);
 Pin131(image,0x3E1D180,kRunnerEntry);Pin131(image,0x3E1D194,kScopeBegin);Pin131(image,0x3E1D286,kScopeEnd);
 const auto bindings=BindDateSentinelImageV1(image.base,b::kExecutableSha256);Need(bindings.exact_build_admitted&&bindings.core.enabled,"real current date binder");
 xar::ck3_11906::MainThreadQueryMailboxV1 mailbox{};
 const auto worker=full111_rvas::Lookup(kWorkerRva);auto *byte=reinterpret_cast<unsigned char*>(image.base+worker);*byte^=1;
 DateSentinelStateV1 bad{};Need(!InitializeDateSentinelV1(bad,bindings,mailbox),"actual production current pin guard rejects");*byte^=1;
 DateSentinelStateV1 actual{};Need(InitializeDateSentinelV1(actual,bindings,mailbox),"actual current binder/pins initializes dateonly kernel with cold globals");
 std::cout<<HelloFrame(*adapter,1)<<'\n'<<"CURRENT_SENTINEL131_ROUTE_PASS no CK3 body execution\n";return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
