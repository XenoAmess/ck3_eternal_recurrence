#if defined(XAR_CK3_ENABLE_121003_26785313_CCC_EVENT_V1) && XAR_CK3_ENABLE_121003_26785313_CCC_EVENT_V1
#error Independent OFF test must not enable CCC_EVENT
#endif
#include "ccc_event_owner_nogame_fixture.hpp"
using namespace ccc_event_nogame;
int main(){try{Fixture f;for(auto action:{CccEventAction267V1::query,CccEventAction267V1::select_tier_four,CccEventAction267V1::select_temporary_cancel}){auto q=f.Context("off",action);if(action!=CccEventAction267V1::query){q.request.provider_generation=q.request.query_sequence=1;q.request.instance_id=1;}f.Run(q);Check(q.result.status==CccEventStatus267V1::unavailable&&!q.result.source&&!q.result.effect_attempted&&!q.result.claim_sequence&&!calls&&!reads&&!frames,"default OFF never observes or selects");}std::cout<<"PASS CCC event independent default OFF\n";return 0;}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
