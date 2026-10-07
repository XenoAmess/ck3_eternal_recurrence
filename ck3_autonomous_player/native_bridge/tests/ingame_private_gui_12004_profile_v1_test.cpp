#include "xar_bridge/ingame_private_gui_profile_v1.hpp"
#include <iostream>
#include <stdexcept>

namespace {
void Check(bool condition,const char *message) {
  if(!condition)throw std::runtime_error(message);
}
}

int main() {
  try {
    using namespace xar::ck3_11906;
    using namespace xar::ck3_12004;
    constexpr auto current=GuiAbiRevisionV1::crozier12004,old=GuiAbiRevisionV1::crozier12003;
    constexpr auto previous="94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";
    Check(IngamePrivateGuiIdentityAdmittedV1(kGameVersion,kExecutableSha256,current),"actual .4 identity/profile rejected");
    Check(IngamePrivateGuiIdentityAdmittedV1("1.20.0.3",previous,old),"historical .3 identity/profile changed");
    Check(!IngamePrivateGuiIdentityAdmittedV1(kGameVersion,kExecutableSha256,old),"actual .4 selected historical .3 coordinates");
    Check(!IngamePrivateGuiIdentityAdmittedV1("1.20.0.3",previous,current),"historical .3 selected actual .4 coordinates");
    Check(!IngamePrivateGuiIdentityAdmittedV1(kGameVersion,previous,current),"cross-build SHA admitted");
    Check(!IngamePrivateGuiIdentityAdmittedV1("1.20.0.3",kExecutableSha256,current),"cross-build version admitted");
    Check(!IngamePrivateGuiIdentityAdmittedV1(kGameVersion,"",current),"empty SHA admitted");
    Check(!IngamePrivateGuiIdentityAdmittedV1(kGameVersion,kExecutableSha256,GuiAbiRevisionV1::legacy11906),"legacy GUI profile admitted");
    std::cout<<"private GUI exact identity/profile gates only; no native provider or live qualification\n";
    return 0;
  }catch(const std::exception &error){std::cerr<<error.what()<<'\n';return 1;}
}
