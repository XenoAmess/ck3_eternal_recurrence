#include "xar_bridge/ck3_121003_des_init_guard26785313_owner_v1.hpp"
#include <stdexcept>
#include <iostream>
using namespace xar::ck3_121003::build26785313;
int main(){ReadonlyBindings b;DesInitGuardFrame267V1 f;DesInitGuardRaw267V1 r;std::string why;
 if(VerifyDesInitGuardImage267V1(1)||ReadDesInitGuardRaw267V1(b,f,1,1,r,why)||why!="des_init_guard_default_off"||r.entered||!r.cleanup_known)throw std::runtime_error("OFF native gate read or entered");
 DesInitGuardContext267V1 q;DesInitGuardSession267V1 session;q.session=&session;xar::ck3_11906::MainThreadExecutionStampV1 stamp;
 if(!ExecuteDesInitGuardInner267V1(q,stamp)||q.result.status!=DesInitGuardStatus267V1::unavailable||q.result.source_available||q.result.source||q.native_observation_entered||q.result.provider_generation||q.result.query_sequence)throw std::runtime_error("OFF owner minted source");
 std::cout<<"DES defaultOFF: no native read, Source, provider or query generation\n";return 0;}
