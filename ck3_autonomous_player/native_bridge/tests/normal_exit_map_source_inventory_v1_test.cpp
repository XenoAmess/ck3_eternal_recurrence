#include "xar_bridge/normal_exit_map_inventory_context_v1.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include <iostream>
#include <string>

int wmain(int argc,wchar_t **argv) {
  if(argc!=8 || std::wstring_view(argv[1])!=L"--source-context" ||
      std::wstring_view(argv[3])!=L"--executable" || std::wstring_view(argv[5])!=L"--sha256") return 1;
  const auto expected=std::wstring_view(argv[7]);
  if(expected!=L"accept" && expected!=L"reject") return 1;
  std::string inventory_sha;
  for(const auto c:std::wstring_view(argv[6])) {
    if(!((c>=L'0'&&c<=L'9') || (c>=L'a'&&c<=L'f'))) return 1;
    inventory_sha+=static_cast<char>(c);
  }
  const xar::game::AdapterDescriptor descriptor{xar::ck3_12004::kAdapterId,
      xar::ck3_12004::kGameVersion,xar::ck3_12004::kExecutableSha256,"",{}};
  bool stock=false; std::string reason;
  const bool accepted=xar::ck3_12003::VerifyNormalExitMapInventoryForContextV1(
      inventory_sha,descriptor,std::filesystem::path(argv[2]),std::filesystem::path(argv[4]),stock,reason);
  std::cout<<"{\"accepted\":"<<(accepted?"true":"false")
      <<",\"stock_verified\":"<<(stock?"true":"false")<<",\"reason\":\""<<reason
      <<"\",\"production_filesystem_verifier_invoked\":true,\"game_process_invoked\":false}\n";
  return accepted==(expected==L"accept") && stock==accepted?0:2;
}
