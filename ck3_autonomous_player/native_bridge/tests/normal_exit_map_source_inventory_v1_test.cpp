#include "xar_bridge/normal_exit_map_inventory_context_v1.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include <iostream>
#include <string>

int main(int argc,char **argv) {
  if(argc!=8 || std::string_view(argv[1])!="--source-context" ||
      std::string_view(argv[3])!="--executable" || std::string_view(argv[5])!="--sha256") return 1;
  const auto expected=std::string_view(argv[7]);
  if(expected!="accept" && expected!="reject") return 1;
  const xar::game::AdapterDescriptor descriptor{xar::ck3_12004::kAdapterId,
      xar::ck3_12004::kGameVersion,xar::ck3_12004::kExecutableSha256,"",{}};
  bool stock=false; std::string reason;
  const bool accepted=xar::ck3_12003::VerifyNormalExitMapInventoryForContextV1(
      argv[6],descriptor,std::filesystem::u8path(argv[2]),std::filesystem::u8path(argv[4]),stock,reason);
  std::cout<<"{\"accepted\":"<<(accepted?"true":"false")
      <<",\"stock_verified\":"<<(stock?"true":"false")<<",\"reason\":\""<<reason
      <<"\",\"production_filesystem_verifier_invoked\":true,\"game_process_invoked\":false}\n";
  return accepted==(expected=="accept") && stock==accepted?0:2;
}
