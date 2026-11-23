#include "rite_creation_blockers_owner_nogame_fixture.hpp"
using namespace blockers_owner_test;
int main(){try{state.Reset();RiteBlockersSession267V1 s;auto m=Box();auto q=Query(s,m.get());Run(q);NoSource(q);Wire(q,false);Need(state.frames==0&&state.rawcalls==0&&state.binds==0,"default OFF reached native dependency");std::cout<<"PASS default OFF query\n";return 0;}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
