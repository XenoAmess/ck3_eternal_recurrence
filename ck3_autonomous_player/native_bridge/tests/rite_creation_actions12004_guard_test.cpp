#include "../src/rite_creation_actions12004_guards.hpp"
#include "xar_bridge/rite_creation_actions12004_wire.hpp"
#include <array>
#include <cstring>
#include <cstdio>
#include <limits>
#include <stdexcept>
using namespace xar::ck3_12004::religion::rite_creation_actions;
namespace {
void Require(bool v,const char*why){if(!v)throw std::runtime_error(why);}
Result Base(Operation op=Operation::open_create_draft){
 Result v{};v.operation=op;v.frame={1,7,9,123,456};v.available=true;
 v.unavailable_reason.clear();v.status="observed";return v;
}
void Encodes(const Result&v){
 const auto wire=SerializeCommandResult12004(v,"guard-fixture");
 Require(!wire.empty(),"original formatter preserves negative guard metadata");
}
struct WindowBytes {
 // Ends after the proven16-byte doctrine prefix. No unconsumed allocator
 // bytes are supplied to the production reader by this owned fixture.
 alignas(void*) std::array<unsigned char,0x7A0>bytes{};
 std::size_t readable=bytes.size();
 static bool Read(void*context,const void*from,void*to,std::size_t count){
  const auto&self=*static_cast<WindowBytes*>(context);
  const auto first=reinterpret_cast<std::uintptr_t>(self.bytes.data());
  const auto address=reinterpret_cast<std::uintptr_t>(from);
  if(address<first||address-first>self.readable||count>self.readable-(address-first))return false;
  std::memcpy(to,from,count);return true;
 }
 void Header(std::size_t offset,const void*data,std::int32_t capacity,std::int32_t count){
  std::memcpy(bytes.data()+offset,&data,sizeof(data));
  std::memcpy(bytes.data()+offset+8,&capacity,sizeof(capacity));
  std::memcpy(bytes.data()+offset+0xC,&count,sizeof(count));
 }
};
int SelectedRowHeaderCases(){
 WindowBytes window{};Bindings bindings{};bindings.read_memory=WindowBytes::Read;bindings.read_context=&window;
 detail::SelectedRowHeaders rows{};const char*why=nullptr;int cases=0;
 const auto reset=[&]{window.readable=window.bytes.size();
  window.Header(0x778,window.bytes.data(),256,3);window.Header(0x790,window.bytes.data(),512,31);};
 const auto read=[&]{return detail::ReadSelectedRowHeaders(bindings,window.bytes.data(),rows,why);};
 const auto rejects=[&](const char*expected){Require(!read()&&why&&std::string_view(why)==expected,
  "production selected-row reader rejects the precise array predicate");++cases;};
 reset();Require(read()&&!why&&rows.tenets.count==3&&rows.tenets.capacity==256&&
  rows.doctrines.count==31&&rows.doctrines.capacity==512,"bounded row counts accept legitimate larger allocation reserve");++cases;
 reset();window.Header(0x790,window.bytes.data(),512,64);
 Require(read()&&rows.doctrines.count==64,"existing SDK doctrine row bound is retained");++cases;
 reset();window.Header(0x778,window.bytes.data(),256,100);
 Require(read()&&rows.tenets.count==100,"physical editor container permits 100 slots");++cases;
 reset();window.Header(0x778,window.bytes.data(),128,101);rejects("rite_creation_selected_tenet_count_above_bound");
 reset();window.Header(0x790,window.bytes.data(),128,65);rejects("rite_creation_selected_doctrine_count_above_bound");
 reset();window.Header(0x790,window.bytes.data(),30,31);rejects("rite_creation_selected_doctrine_capacity_below_count");
 reset();window.Header(0x778,window.bytes.data(),256,-1);rejects("rite_creation_selected_tenet_count_negative");
 reset();window.Header(0x790,nullptr,512,31);rejects("rite_creation_selected_doctrine_rows_missing");
 reset();window.Header(0x778,nullptr,256,0);window.Header(0x790,nullptr,512,0);
 Require(read()&&rows.tenets.count==0&&rows.doctrines.count==0,"empty rows are values independent of allocation reserve");++cases;
 reset();window.readable=0x778+15;rejects("rite_creation_selected_tenet_header_unreadable");
 reset();window.readable=0x790+15;rejects("rite_creation_selected_doctrine_header_unreadable");
 reset();window.Header(0x790,nullptr,-1,0);rejects("rite_creation_selected_doctrine_capacity_below_count");
 reset();window.Header(0x778,window.bytes.data(),std::numeric_limits<std::int32_t>::max(),3);
 Require(read()&&rows.tenets.count==3,"only bounded count is consumed even when reserve is large");++cases;
 reset();window.Header(0x790,window.bytes.data()+1,512,31);rejects("rite_creation_selected_doctrine_rows_misaligned");
 reset();window.Header(0x778,reinterpret_cast<const void*>(std::numeric_limits<std::uintptr_t>::max()-7),256,3);
 rejects("rite_creation_selected_tenet_row_span_overflow");
 reset();Require(!detail::ReadSelectedRowHeaders(bindings,window.bytes.data()+1,rows,why)&&
  std::string_view(why)=="rite_creation_selected_tenet_header_misaligned","misaligned window header is rejected");++cases;
 reset();Require(!detail::ReadSelectedRowHeaders(bindings,
  reinterpret_cast<const void*>(std::numeric_limits<std::uintptr_t>::max()-0x777),rows,why)&&
  std::string_view(why)=="rite_creation_selected_tenet_header_unreadable","header address overflow is rejected before read callback");++cases;
  reset();Require(read(),"capture stores the initial selected-row headers");
  const auto expected=rows;
  const auto unchanged=[&]{return detail::SelectedRowHeadersUnchanged(bindings,window.bytes.data(),expected,why);};
  Require(unchanged()&&!why,"final capture reread accepts the same bounded rows with larger reserve");++cases;
  window.bytes[0x788]=1;
  Require(unchanged()&&!why,"both capture reads ignore unconsumed trailing header bytes");++cases;
  const auto changed=[&]{Require(!unchanged()&&why&&std::string_view(why)=="rite_creation_owned_draft_collections_changed",
   "final capture reread detects changed selected-row identity");++cases;};
  reset();window.Header(0x778,window.bytes.data(),256,2);changed();
  reset();window.Header(0x790,window.bytes.data(),513,31);changed();
  reset();window.Header(0x790,window.bytes.data()+8,512,31);changed();
  reset();window.Header(0x790,window.bytes.data(),30,31);
  Require(!unchanged()&&why&&std::string_view(why)=="rite_creation_selected_doctrine_capacity_below_count",
   "final capture reread preserves precise malformed-header rejection");++cases;
 return cases;
}
struct OwnedModel {
 alignas(void*) std::array<unsigned char,0x5000>bytes{};
 static bool Read(void*context,const void*from,void*to,std::size_t count){
  const auto&self=*static_cast<OwnedModel*>(context);
  const auto first=reinterpret_cast<std::uintptr_t>(self.bytes.data());
  const auto address=reinterpret_cast<std::uintptr_t>(from);
  if(address<first||address-first>self.bytes.size()||count>self.bytes.size()-(address-first))return false;
  std::memcpy(to,from,count);return true;
 }
 const void*At(std::size_t offset)const{return bytes.data()+offset;}
 template<class T>void Put(std::size_t offset,const T&value){std::memcpy(bytes.data()+offset,&value,sizeof(value));}
 void Header(std::size_t offset,const void*data,std::int32_t capacity,std::int32_t count){
  Put(offset,data);Put(offset+8,capacity);Put(offset+0xC,count);
 }
 Bindings Binding(){Bindings result{};result.read_memory=Read;result.read_context=this;return result;}
};
int SparseSlotCases(){
 OwnedModel model{};const auto binding=model.Binding();
 const auto sentinel=model.At(0x4800);const auto first=model.At(0x4810);
 const auto middle=model.At(0x4820);const auto last=model.At(0x4830);
 const auto reset=[&]{
  for(std::uint32_t slot=0;slot<100;++slot){
   model.Put(0x1000+slot*0x70+0x20,slot);model.Put(0x1000+slot*0x70+0x28,sentinel);}
  model.Put(0x1028,first);model.Put(0x1000+50*0x70+0x28,middle);model.Put(0x1000+99*0x70+0x28,last);
 };
 const auto definition=[&](const void*item,std::string&key){
  if(item==first)key="tenet_first";else if(item==middle)key="tenet_middle";
  else if(item==last)key="tenet_last";else return false;return true;
 };
 detail::SelectedRowArrayHeader header{model.At(0x1000),1000,100};
 std::vector<TenetSelection>valid;std::vector<const void*>raw;std::vector<std::string>keys;const char*why=nullptr;
 const auto read=[&]{return detail::ReadSelectedTenetSlots(binding,header,sentinel,definition,valid,raw,keys,why);};
 int cases=0;reset();Require(read()&&!why&&valid.size()==3&&raw.size()==100&&keys.size()==100,
  "production sparse reader retains all 100 raw writer slots");++cases;
 Require(valid[0].slot_index==0&&valid[1].slot_index==50&&valid[2].slot_index==99&&
  raw[0]==first&&raw[50]==middle&&raw[99]==last&&raw[1]==sentinel&&keys[1].empty(),
  "native-default holes retain their physical identity and valid DTO indices");++cases;
 Require(detail::SelectedTenetAt(valid,50)==&valid[1]&&!detail::SelectedTenetAt(valid,1),
  "mutation postcondition resolves physical slot rather than flattened vector index");++cases;
 const auto rejects=[&](const char*reason){Require(!read()&&why&&std::string_view(why)==reason,
  "production sparse reader preserves precise rejection");++cases;};
 const void*missing=nullptr;model.Put(0x1000+0x70+0x28,missing);
 rejects("rite_creation_selected_tenet_definition_unavailable");
 reset();model.Put(0x1000+0x70+0x28,model.At(0x4840));rejects("rite_creation_selected_tenet_definition_unavailable");
 reset();model.Put(0x1000+0x70+0x28,first);rejects("rite_creation_selected_tenet_duplicate");
 reset();model.Put(0x1000+50*0x70+0x20,std::uint32_t{49});rejects("rite_creation_selected_tenet_physical_slot_mismatch");
 reset();header.count=101;rejects("rite_creation_selected_tenet_header_unverified");
 header.count=100;header.capacity=99;rejects("rite_creation_selected_tenet_header_unverified");
 header.capacity=100;header.data=model.At(0x1001);rejects("rite_creation_selected_tenet_header_unverified");
 header.data=model.At(0x1000);header.count=0;header.capacity=1000;
 Require(read()&&valid.empty()&&raw.empty()&&keys.empty(),"observed zero slots is not an unavailable collection");++cases;
 Require(!detail::ReadSelectedTenetSlots(binding,header,nullptr,definition,valid,raw,keys,why)&&
  std::string_view(why)=="rite_creation_native_default_tenet_unavailable","unknown sentinel never means a blank slot");++cases;
 return cases;
}
int CatalogueCases(){
 OwnedModel model{};const auto binding=model.Binding();const auto core=model.At(0x238);
 const auto brave=model.At(0x4800),patient=model.At(0x4810),greedy=model.At(0x4820);
 const auto row=[&](std::size_t offset,std::int32_t classification,const void*trait,std::uint32_t source,
                    std::int64_t weight,const void*draft){
  model.Put(offset,classification);model.Put(offset+8,trait);model.Put(offset+0x10,source);
  model.Put(offset+0x18,weight);model.Put(offset+0x20,draft);
 };
 const auto reset=[&]{
  model.Header(0x840,model.At(0x4000),256,2);model.Header(0x858,model.At(0x4080),256,1);
  row(0x4000,1,brave,absent,std::numeric_limits<std::int64_t>::max(),core);
  row(0x4028,1,patient,155,9007199254740993LL,nullptr);
  row(0x4080,2,greedy,absent,std::numeric_limits<std::int64_t>::min(),core);
 };
 const auto trait=[&](const void*value,std::uint32_t&id,std::string&key){
  if(value==brave){id=7;key="brave";}else if(value==patient){id=2;key="patient";}
  else if(value==greedy){id=9;key="greedy";}else return false;return true;
 };
 VirtueSinCatalogue value{};const auto read=[&]{return detail::ReadVirtueSinCatalogueRows(binding,
  model.At(0),0x840,0x858,VirtueSinScope::draft,155,core,trait,value);};
 int cases=0;reset();Require(read()&&value.observed&&value.rite_id==155&&value.virtues.size()==2&&value.sins.size()==1,
  "actual production catalogue reader consumes original cached row ABI");++cases;
 Require(value.virtues[0].trait_id==7&&value.virtues[1].trait_id==2&&
  value.virtues[1].weight_raw==9007199254740993LL&&value.sins[0].weight_raw==std::numeric_limits<std::int64_t>::min()&&
  value.description_rite_ids[0]==absent&&value.description_draft_cores[0]==core&&value.description_rite_ids[1]==155,
  "native order, signed64 values and distinct source branches are preserved");++cases;
 const auto rejects=[&](const char*reason){Require(!read()&&!value.observed&&value.virtues.empty()&&value.sins.empty()&&
  value.unavailable_reason==reason,"unavailable catalogue is not a partial or empty observation");++cases;};
 model.Put(0x4080,std::int32_t{1});rejects("rite_virtue_sin_native_classification_or_trait_unavailable");
 reset();model.Put(0x4000,std::int32_t{0});rejects("rite_virtue_sin_native_classification_or_trait_unavailable");
 reset();model.Put(0x4088,brave);rejects("rite_virtue_sin_native_trait_duplicate");
 reset();model.Put(0x4038,std::uint32_t{154});rejects("rite_virtue_sin_persistent_reference_unbound");
 reset();model.Put(0x4020,model.At(0x240));rejects("rite_virtue_sin_draft_core_reference_unbound");
 reset();model.Put(0x4088,model.At(0x4830));rejects("rite_virtue_sin_native_classification_or_trait_unavailable");
 reset();model.Header(0x840,model.At(0x4000),1,2);rejects("rite_virtue_sin_native_collection_unavailable");
 reset();model.Header(0x840,model.At(0x4000),8193,8193);rejects("rite_virtue_sin_native_collection_unavailable");
 reset();model.Header(0x840,model.At(0x4000),8192,8192);rejects("rite_virtue_sin_combined_count_above_bound");
 reset();bool changed=false;const auto mutate=[&](const void*p,std::uint32_t&id,std::string&key){
  if(!changed){changed=true;model.Header(0x840,model.At(0x4000),257,2);}return trait(p,id,key);};
 Require(!detail::ReadVirtueSinCatalogueRows(binding,model.At(0),0x840,0x858,VirtueSinScope::draft,155,core,mutate,value)&&
  value.unavailable_reason=="rite_virtue_sin_native_collection_changed","cached header drift prevents an observed list");++cases;
 reset();Require(!detail::ReadVirtueSinCatalogueRows(binding,model.At(0),0x840,0x858,VirtueSinScope::current_rite,
  155,nullptr,trait,value)&&value.unavailable_reason=="rite_virtue_sin_draft_core_reference_unbound",
  "current Rite cannot inherit a draft-core description reference");++cases;
 reset();row(0x4000,1,brave,155,5,nullptr);row(0x4080,2,greedy,155,-5,nullptr);
 Require(detail::ReadVirtueSinCatalogueRows(binding,model.At(0),0x840,0x858,VirtueSinScope::current_rite,
  155,nullptr,trait,value)&&value.scope==VirtueSinScope::current_rite,"current catalogue rows bind their own Rite");++cases;
 model.Header(0x840,nullptr,500,0);model.Header(0x858,nullptr,500,0);
 Require(read()&&value.observed&&value.virtues.empty()&&value.sins.empty(),"observed empty native lists retain empty arrays");++cases;
 return cases;
}
void NativeTextCases(){
 const std::string markup="default\x15" "faith";
 Require(detail::Utf8Text(markup,240,true,true)&&!detail::Utf8Text(markup,240,true),
  "only native description output accepts proven U+0015 markup");
 Require(!detail::Utf8Text("x\x14",240,true,true)&&!detail::Utf8Text(std::string("x\0y",3),240,true,true)&&
  !detail::Utf8Text("\xC0\xAF",240,true,true),"markup exception retains other control and UTF-8 guards");
 Require(detail::Utf8Text("\xE4\xBF\xA1\xE4\xBB\xB0",2,false)&&
  !detail::Utf8Text("\xE4\xBF\xA1\xE4\xBB\xB0",1,false),"text limits count UTF-8 scalars");
}
}
int main(){
 try{
  Request q{};q.operation=Operation::open_create_draft;q.expected_source_rite_id=13;
  int opens=0,reads=0;auto open=[&](){++opens;return true;};
  auto existing=[&](Result&v){++reads;v=Base();v.draft.actual_outcome_kind=Outcome::create_faith;return true;};
  auto v=Base();
  Require(!detail::GuardOpenDraft(q,v,[](bool&){return false;},existing,open)&&!opens&&!reads&&!v.available,
          "unknown independent presence never calls original Open or full reader");Encodes(v);
  v=Base();
  Require(!detail::GuardOpenDraft(q,v,[](bool&shown){shown=true;return true;},
          [&](Result&partial){++reads;partial=Base();return false;},open)&&!opens&&!v.available,
          "visible draft plus full-read failure cannot fall through to Open");Encodes(v);
  v=Base();
  Require(!detail::GuardOpenDraft(q,v,[](bool&shown){shown=true;return true;},
          [&](Result&partial){++reads;partial=Base();partial.available=false;partial.unavailable_reason="preview unavailable";return true;},open)&&!opens&&!v.available,
          "visible draft with bool-success but unavailable complete read stays unavailable");Encodes(v);
  q.expected_outcome_kind=Outcome::create_rite;v=Base();
  Require(!detail::GuardOpenDraft(q,v,[](bool&shown){shown=true;return true;},existing,open)&&!opens,
          "existing actual Faith versus expected Rite never reinitializes");
  q.expected_outcome_kind.reset();q.operation=Operation::open_edit_current_rite_draft;v=Base(q.operation);
  Require(!detail::GuardOpenDraft(q,v,[](bool&shown){shown=true;return true;},existing,open)&&!opens,
          "existing create draft cannot be reopened as Edit");
  q.operation=Operation::open_create_draft;v=Base();
  Require(detail::GuardOpenDraft(q,v,[](bool&shown){shown=true;return true;},existing,open)&&!opens&&
          v.already_in_requested_state&&v.draft_open_postcondition_observed,
          "verified matching existing draft is idempotent");
  const auto reads_before=reads;v=Base();
  Require(detail::GuardOpenDraft(q,v,[](bool&shown){shown=false;return true;},existing,open)&&
          opens==1&&reads==reads_before,"only verified absence calls original Open exactly once");
  v=Base(Operation::preview);detail::MarkCaptureException(v);
  Require(!v.available&&v.status=="unavailable"&&!v.native_dispatch_attempted,
          "capture exception after available result remains unavailable");Encodes(v);
  q.operation=Operation::confirm_once;q.action_id="guard-fixture";v=Base(q.operation);v.action_id=q.action_id;
  detail::MarkActionException(q,v);
  Require(!v.available&&!v.verification_pending&&!v.original_writer_may_have_been_queued,
          "predispatch exception preserves known no-dispatch");Encodes(v);
  v=Base(q.operation);v.action_id=q.action_id;v.native_dispatch_attempted=true;v.dispatch_invoked=true;v.native_once_claimed=true;
  detail::MarkActionException(q,v);
  Require(!v.available&&v.native_dispatch_attempted&&v.dispatch_invoked&&v.native_once_claimed&&
          v.verification_pending&&v.original_writer_may_have_been_queued&&v.status=="dispatch_result_unknown",
          "post-confirm exception retains attempted once claim and possible writer");Encodes(v);
  q.operation=Operation::set_name_field;v=Base(q.operation);v.native_dispatch_attempted=true;
  detail::MarkActionException(q,v);
  Require(!v.available&&v.verification_pending&&!v.original_writer_may_have_been_queued&&!v.dispatch_invoked,
          "draft exception retains attempted state without claiming gameplay queue");Encodes(v);
  q.operation=Operation::open_create_draft;v=Base();const auto before_throw=opens;
  try {detail::GuardOpenDraft(q,v,[](bool&shown){shown=true;return true;},
       [](Result&)->bool{throw std::runtime_error("injected full-reader exception");},open);}
  catch(...){detail::MarkActionException(q,v);}
  Require(opens==before_throw&&!v.available&&!v.native_dispatch_attempted,
          "injected existing reader exception remains no-Open and serializable");Encodes(v);
  const auto selected_cases=SelectedRowHeaderCases();
  const auto sparse_cases=SparseSlotCases(),catalogue_cases=CatalogueCases();NativeTextCases();
  std::printf("12 production open/exception guard cases, %d selected-row headers, %d sparse slots, %d catalogue cases and native text checks passed; owned synthetic memory/callbacks; no live/native game calls\n",selected_cases,sparse_cases,catalogue_cases);return 0;
 }catch(const std::exception&e){std::fprintf(stderr,"FAIL %s\n",e.what());return 1;}
}
