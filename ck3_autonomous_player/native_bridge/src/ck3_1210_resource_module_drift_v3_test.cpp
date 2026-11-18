// Owner-only source-boundary test. This executes no CK3 image/game code.
#include "xar_bridge/ck3_1210_actor_resource_leaf_v2.hpp"
#include "xar_bridge/ck3_1210_non_cash_owner_sources_v3.hpp"
#include <cstdlib>
#include <iostream>
#if defined(_MSC_VER)
#include <windows.h>
#endif
using namespace xar::ck3_1210;
void Check(bool ok,const char *message){if(!ok){std::cerr<<message<<'\n';std::exit(1);}}
int main(){
  ActorResourceLeafSourceInputV2 i{};i.game_version=kGameVersion;i.adapter_id=kAdapterId;
  i.executable_sha256=kExecutableSha256;i.application_main_owner_admitted=true;
#if defined(_MSC_VER)
  const auto module=reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
  i.image_base=module+0x1000; // Foreign, numerically consistent with crafted Bind input.
#else
  i.image_base=0x140001000;
#endif
  i.gold_bindings=BindPersonalGoldImageV1(i.image_base,i.executable_sha256);
  i.expected.clock={123456,4,true};i.expected.local_player_id=7;
  i.expected.map_ready=i.expected.has_played_character=i.expected.played_character_alive=true;
  i.expected.played_character_id=0;
  ActorResourceLeafObservationV2 base{};
  Check(!ReadActorResourceLeafV2(i,base) && !base.prestige_raw && !base.piety_raw &&
      base.unavailable_reason=="image_module_before_changed","foreign module must reject before Core/native getter access");
  NonCashOwnerSourceObservationV3 sources{};
  Check(!ReadNonCashOwnerSourcesV3(i,sources) && !sources.owner_source_interval_verified &&
      !sources.renown.raw && !sources.treasury.raw,"foreign module never becomes extra source DATA");
  i.application_main_owner_admitted=false;i.image_base=0x140000000;
  i.gold_bindings=BindPersonalGoldImageV1(i.image_base,i.executable_sha256);
  Check(!ReadNonCashOwnerSourcesV3(i,sources) && !sources.owner_source_interval_verified &&
      !sources.renown.raw && !sources.treasury.raw,"address binding without real main owner keeps both unknown");
  std::cout<<"PASS module/caller source boundary without Game\n";
}
