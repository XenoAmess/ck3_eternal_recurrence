#if defined(XAR_CK3_ENABLE_121003_26785313_CCC_DECISION_V1) && XAR_CK3_ENABLE_121003_26785313_CCC_DECISION_V1
#error Independent OFF test must not enable CCC_DECISION
#endif
#include "ccc_decision_owner_nogame_fixture.hpp"
using namespace ccc_decision_nogame;
int main(){try{Fixture f;for(auto action:{CccDecisionAction267V1::query,CccDecisionAction267V1::open_list,CccDecisionAction267V1::open_detail,CccDecisionAction267V1::confirm}){auto q=f.Context("off",action);if(action!=CccDecisionAction267V1::query){q.request.provider_generation=q.request.query_sequence=1;if(action!=CccDecisionAction267V1::open_list)q.request.decision=CccDecision267V1::corruption_policy;}f.Run(q);Check(q.result.status==CccDecisionStatus267V1::unavailable&&!q.result.source&&!q.result.effect_attempted&&!q.result.claim_sequence&&!calls&&!reads&&!frames,"default OFF never observes or calls");}std::cout<<"PASS CCC decision independent default OFF\n";return 0;}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
