#include "xar_bridge/normal_exit_map_v1.hpp"
#include "xar_bridge/normal_exit_map_source_v1.hpp"
#include "xar_bridge/ck3_12003.hpp"
#include <fstream>
#include <iostream>
#include <iterator>
#include <stdexcept>

int main(int argc,char **argv) {
  using namespace xar::ck3_12003;
  if(argc==2 && std::string_view(argv[1])=="--self-test") {
    NormalExitMapObservationV1 observation{};
    observation.orderly_exit_verified=true; observation.autosave_verified=true;
    const auto result=SerializeNormalExitMapObservationV1(observation);
    if(result.find("\"orderly_exit_verified\":false")==std::string::npos ||
        result.find("\"autosave_verified\":false")==std::string::npos) return 2;
    NormalExitMapSessionV1 session{};
    bool first=false;
    if(!session.claimed[0].compare_exchange_strong(first,true)) return 3;
    session.signature.clear(); session.query_epoch=99; session.queried_revision=100;
    first=false;
    if(session.claimed[0].compare_exchange_strong(first,true) || !session.claimed[0].load()) return 4;
    first=false;
    if(!session.claimed[1].compare_exchange_strong(first,true) || session.claimed[2].load()) return 5;
    std::string digest,reason; bool stock=true;
    if(!NormalExitMapSha256V1("abc",digest) || digest!="ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad") return 6;
    const xar::game::AdapterDescriptor descriptor{kAdapterId,kGameVersion,kExecutableSha256,"",{}};
    if(VerifyNormalExitMapSourcesV1("",descriptor,stock,reason) || stock || reason!="source_inventory_reference_missing") return 7;
    if(VerifyNormalExitMapSourcesV1(std::string(64,'a'),descriptor,stock,reason) || stock || reason!="actual_launch_userdir_contract_unsupported") return 8;
    std::cout<<"{\"self_test\":true,\"facts_never_forged\":true,\"claims_survive_query\":true,\"stock_source_missing_rejected\":true}\n";
    return 0;
  }
  if(argc!=3 || std::string_view(argv[1])!="--packet") return 1;
  std::ifstream input(argv[2],std::ios::binary);
  const std::string packet((std::istreambuf_iterator<char>(input)),std::istreambuf_iterator<char>());
  if(!input || packet.size()<4) return 9;
  std::uint32_t length=0;
  for(std::size_t i=0;i<4;++i) length|=static_cast<std::uint32_t>(static_cast<unsigned char>(packet[i]))<<(8*i);
  if(length!=packet.size()-4 || length>2U*1024U*1024U) return 10;
  NormalExitMapRequestV1 request{};
  request.request_id="sentinel-old-state"; request.action=NormalExitMapActionV1::confirm_desktop;
  request.expected_revision=71; request.expected_player_character_id=72; request.expected_game_pid=73;
  request.expected_connection_generation=74; request.expected_process_creation_filetime_100ns=75;
  request.request_nonce="sentinel-nonce"; request.source_inventory_sha256=std::string(64,'b');
  request.expected_exit_context_signature=std::string(64,'c');
  std::string reason;
  const bool accepted=ParseNormalExitMapRequestV1(std::string_view(packet).substr(4),request,reason);
  const bool unchanged=request.request_id=="sentinel-old-state" && request.action==NormalExitMapActionV1::confirm_desktop &&
      request.expected_revision==71 && request.expected_player_character_id==72 && request.expected_game_pid==73 &&
      request.expected_connection_generation==74 && request.expected_process_creation_filetime_100ns==75 &&
      request.request_nonce=="sentinel-nonce" && request.source_inventory_sha256==std::string(64,'b') &&
      request.expected_exit_context_signature==std::string(64,'c');
  if(!accepted && !unchanged) return 11;
  std::cout<<"{\"accepted\":"<<(accepted?"true":"false")<<",\"rejected_output_unchanged\":"<<(!accepted&&unchanged?"true":"false")
      <<",\"reason\":\""<<reason<<"\",\"action\":\""<<NormalExitMapActionNameV1(request.action)
      <<"\",\"expected_revision\":"<<request.expected_revision<<",\"expected_player_character_id\":"<<request.expected_player_character_id
      <<",\"expected_game_pid\":"<<request.expected_game_pid<<",\"expected_connection_generation\":"<<request.expected_connection_generation
      <<",\"expected_process_creation_filetime_100ns\":"<<request.expected_process_creation_filetime_100ns<<"}\n";
  return 0;
}
