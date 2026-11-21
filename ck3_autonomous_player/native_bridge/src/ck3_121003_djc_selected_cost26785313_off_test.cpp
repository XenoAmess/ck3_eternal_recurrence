#include "xar_bridge/ck3_121003_djc_declaration_ui26785313_owner_v1.hpp"
#include <iostream>
#include <stdexcept>
using namespace xar::ck3_121003::build26785313;
int main(){try{
 DjcSelectedCostValues267V1 values;std::string reason;ReadonlyBindings core;DjcUiRawBindings267V1 supplied{1,true};DjcUiRawObservation267V1 prior;
 if(ReadDjcSelectedCostRaw267V1(core,supplied,{},39957,0,{},1,prior,values,reason)||values.available||values.native_getter_calls||!values.cleanup_known||reason!="current_djc_selected_cost_default_off")throw std::runtime_error("default OFF cannot be opened by supplied pointers/boolean");
 DjcUiContext267V1 q;DjcUiSession267V1 session;q.session=&session;q.selected_cost_query=true;q.request.provider_generation=7;q.request.query_sequence=11;
 xar::ck3_11906::MainThreadExecutionStampV1 stamp{};if(!ExecuteDjcUiOnOwner267V1(&q,stamp)||q.result.status!=DjcUiStatus267V1::unavailable||q.result.effect_attempted||q.result.native_returned||q.selected_cost_values.native_getter_calls||q.result.provider_generation!=7||q.result.query_sequence!=11)throw std::runtime_error("actual OFF owner preserves refusal/lease and executes no getters");
 const auto wire=SerializeDjcSelectedCostResult267V1("cost-off",{q.result,q.selected_cost_values});
 if(wire.find("\"ok\":false")==std::string::npos||wire.find("\"costs\":null")==std::string::npos)throw std::runtime_error("OFF result must not fabricate zero prices");
 std::cout<<"SelectedCost actual OFF owner/raw refusal PASS; NoGame\n";return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
