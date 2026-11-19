#ifdef NDEBUG
#undef NDEBUG
#endif
#include "xar_bridge/ck3_1210_toast_query_v1.hpp"
#include "xar_bridge/ck3_1210_core_frame_v1.hpp"
#include <cassert>
#include <iostream>
#include <string>
#include <utility>
#include "toast_owned_fixture_v1.hpp"
using namespace xar::ck3_1210;
namespace {
std::string Request() {
  return std::string{"{\"type\":\"execute_step\",\"protocol_version\":1,\"request_id\":\"toast-fixture\",\"step\":\"query-current-interface-toast-v1\",\"expected_revision\":11,\"arguments\":{},\"gui_control_v1\":{\"schema\":\"ck3_1210_gui_control_v1\",\"game_version\":\"1.21.0\",\"executable_sha256\":\""}+
      kExecutableSha256+"\",\"adapter_id\":\"ck3-1.21.0-msvc-x64\",\"backend\":\""+kCoreBackendV1+
      "\",\"snapshot_id\":\"native:11\",\"native_revision\":11,\"deadline_unix_ms\":10000,\"root_name\":\"toast_container_widget\",\"query_generation\":\"0\",\"widget_id\":\"0\"}}";
}
std::string Changed(std::string text,std::string_view old,std::string_view value) {
  const auto at=text.find(old);assert(at!=std::string::npos);text.replace(at,old.size(),value);return text;
}
ToastQueryResultV1 Result() {
  ToastQueryResultV1 r{};r.available=true;r.application_main_observed=true;
  r.full_snapshot_before_verified=true;r.full_snapshot_after_verified=true;r.source_abi_pins_verified=true;
  r.connection_generation=3;r.query_sequence=9007199254740993ULL;r.owner_thread_id=77;
  toast_test::Fixture fixture;fixture.script_typed_pair();
  fixture.graph.completed_frame_epoch=9007199254740994ULL;
  fixture.memory.put(toast_test::Fixture::app+kIngameCompletedFrameEpochOffsetV1,fixture.graph.completed_frame_epoch);
  fixture.text(toast_test::Fixture::item+0x11C8,"software-owned \"title\"");
  fixture.text(toast_test::Fixture::item+0x11E8,"non-ASCII: \xE6\xB6\x88\xE6\x81\xAF\nline");
  assert(fixture.read(r.observation));assert(r.observation.stage==ToastObjectStageV1::visible_pending_frame);
  fixture.advance();assert(fixture.read(r.observation));assert(r.observation.stage==ToastObjectStageV1::visible);
  assert(r.observation.saved_script_scopes[0].identity=="50331650" && r.observation.saved_script_scopes[1].identity=="-2147483646");
  return r;
}
} // namespace
int main(int argc,char **argv) {
  GuiControlRequestV1 request{};assert(ParseGuiControlRequestV1(Request(),request));unsigned checks=1;
  assert(request.step==kToastQueryStepV1 && !request.activate && request.root_name==kToastQueryRootV1);++checks;
  for(const auto &pair: {std::pair<std::string,std::string>{"toast_container_widget","other_root"},
      {"\"query_generation\":\"0\"","\"query_generation\":\"1\""},
      {"\"widget_id\":\"0\"","\"widget_id\":\"1\""},
      {"\"native_revision\":11","\"native_revision\":true"},
      {"\"snapshot_id\":\"native:11\"","\"snapshot_id\":\"native:12\""},
      {"\"deadline_unix_ms\":10000","\"deadline_unix_ms\":0"},
      {"\"arguments\":{}","\"arguments\":{\"recipient\":42}"},
      {"\"game_version\":\"1.21.0\"","\"game_version\":\"1.20.0.4\""}}) {
    GuiControlRequestV1 denied{};assert(!ParseGuiControlRequestV1(Changed(Request(),pair.first,pair.second),denied));++checks;
  }
  assert(ParseGuiControlRequestV1(Request(),request));const auto value=Result();
  const auto wire=SerializeToastQueryResultV1("toast-fixture",request,value);
  assert(wire.find("\"native_revision\":\"11\"")!=std::string::npos &&
      wire.find("\"query_sequence\":\"9007199254740993\"")!=std::string::npos &&
      wire.find("\"completed_application_frame\":\"9007199254740995\"")!=std::string::npos);++checks;
  assert(wire.find("\"delivery_confirmed\":false")!=std::string::npos &&
      wire.find("\"recipient_identity_available\":false")!=std::string::npos &&
      wire.find("\"news_origin_available\":false")!=std::string::npos);++checks;
  if(argc==2 && std::string_view(argv[1])=="--emit-visible") {std::cout<<wire<<'\n';return 0;}
  ToastQueryResultV1 denied{};denied.unavailable_reason="toast_mailbox_not_completed";
  const auto failure=SerializeToastQueryResultV1("toast-fixture",request,denied);
  assert(failure.find("\"accepted\":false")!=std::string::npos && failure.find("\"stage\":\"unavailable\"")!=std::string::npos);++checks;
  std::cout<<"toast public query contract: "<<checks<<" checks; software serializer only; no owner admission or delivery claim\n";
}
