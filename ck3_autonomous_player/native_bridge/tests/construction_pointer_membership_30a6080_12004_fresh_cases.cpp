#include "xar_bridge/construction_pointer_membership_30a6080_12004.hpp"
#include <array>
#include <cstring>
#include <stdexcept>
#include <vector>

namespace {
using namespace xar::ck3_12004::construction_owner_mode3;
struct Range {std::uintptr_t begin;std::size_t bytes;};
struct Scene {
  alignas(8) std::array<std::byte,0x430> receiver{};
  std::array<std::uintptr_t,8> values{};
  std::vector<std::uintptr_t> read_addresses;
  std::uintptr_t blocked=0;
  unsigned payload_reads=0;
  ContextPredicateInputsV1 inputs;
  RawReceiverAccessV1 access;
  Scene(){
    inputs.frame_key=0x12004;inputs.selector_object_pointer=reinterpret_cast<std::uintptr_t>(receiver.data());
    inputs.raw_receiver_pointer=0x060000;inputs.slots_pointer=0x030000;
    access.context=this;access.read_memory=&Copy;access.exact_12004_bound=true;
  }
  static bool Copy(void *context,const void *p,void *out,std::size_t n){
    auto &s=*static_cast<Scene *>(context);auto a=reinterpret_cast<std::uintptr_t>(p);
    s.read_addresses.push_back(a);if(a==s.blocked)return false;
    for(auto r:{Range{reinterpret_cast<std::uintptr_t>(s.receiver.data()),s.receiver.size()},
        Range{reinterpret_cast<std::uintptr_t>(s.values.data()),sizeof(s.values)}}){
      if(a>=r.begin&&n<=r.bytes&&a-r.begin<=r.bytes-n){
        if(r.begin==reinterpret_cast<std::uintptr_t>(s.values.data()))++s.payload_reads;
        std::memcpy(out,p,n);return true;
      }
    }
    return false;
  }
  template<class T>void Set(std::size_t off,T value){std::memcpy(receiver.data()+off,&value,sizeof(value));}
  auto Read(){return ReadConstructionPointerMembership30A6080V1(access,inputs,inputs.selector_object_pointer,inputs.first_pointer);}
  void Header(std::int32_t count,bool null=false){Set(0x420,null?std::uintptr_t{0}:reinterpret_cast<std::uintptr_t>(values.data()));Set(0x42C,count);}
};
void Check(bool result,const char *reason){if(!result)throw std::runtime_error(reason);}
}

// Fresh37c fragment. Central21/03->10 owns its unique first compile/run.
void RunConstructionPointerMembership30A6080FreshCases12004(){
  using namespace xar::ck3_12004::construction_owner_mode3;
  {Scene s;s.Header(0,true);s.inputs.first_pointer=0xFA00000000000000ULL;auto r=s.Read();
    Check(r.value==false&&r.probe_count==0&&s.payload_reads==0&&r.collection_pointer==std::uintptr_t{0},"zero count demanded an unused payload");
    bool output=true;Check(ReadConstructionPointerMembership30A6080ChildV1(nullptr,s.access,s.inputs,s.inputs.selector_object_pointer,s.inputs.first_pointer,output)&&!output,"nativefalse collapsed into unavailable");}
  {Scene s;s.values={1,4,4,9,0,0,0,0};s.Header(4);s.inputs.first_pointer=4;auto r=s.Read();
    Check(r.value==true&&r.selected_index_raw_i32==1&&r.probe_count==4,"positive pointer search branch/index changed");
    auto base=reinterpret_cast<std::uintptr_t>(s.values.data());
    Check(r.probes[0].address==base+16&&r.probes[1].address==base+8&&r.probes[2].address==base&&r.probes[3].address==base+8,"native qword probe order changed");
    s.inputs.first_pointer=3;Check(s.Read().value==false,"missing pointer acquired true AL");}
  {Scene s;s.values={0,0x8000000000000000ULL,0xFFFFFFFFFFFFFFF0ULL,0,0,0,0,0};s.Header(3);
    s.inputs.first_pointer=0x8000000000000000ULL;auto r=s.Read();Check(r.value==true&&r.selected_index_raw_i32==1,"qword comparison became signed");
    s.inputs.first_pointer=0;Check(s.Read().value==true,"zero copied pointer gained an invented ID gate");}
  {Scene s;s.values={4,1,6,0,0,0,0,0};s.Header(3);s.inputs.first_pointer=4;auto r=s.Read();
    Check(r.value==false&&r.probes[0].copied_value==std::uintptr_t{1}&&r.probes[1].copied_value==std::uintptr_t{6},"reader sorted/scanned an unsorted raw collection");}
  {Scene s;s.values[0]=9;s.Header(-1);s.inputs.first_pointer=10;auto r=s.Read();
    Check(r.value==true&&r.probe_count==1&&r.selected_index_raw_i32==0&&r.count_raw_i32==-1,"negative native count path was rejected or clamped");
    s.inputs.first_pointer=8;Check(s.Read().value==false,"negative count final unsigned compare changed");}
  {Scene s;s.Header(1);s.values[0]=1;s.inputs.first_pointer=1;s.blocked=reinterpret_cast<std::uintptr_t>(s.values.data());auto r=s.Read();
    Check(!r.value&&r.failure==PointerMembershipFailure12004::probe_copy,"failed reached qword was filled from expected AL");
    bool output=true;Check(!ReadConstructionPointerMembership30A6080ChildV1(nullptr,s.access,s.inputs,s.inputs.selector_object_pointer,s.inputs.first_pointer,output)&&output,"unavailable callback overwrote output");}
  {Scene s;s.Header(1);s.blocked=s.inputs.selector_object_pointer+0x42C;auto r=s.Read();
    Check(!r.value&&r.collection_pointer&&r.failure==PointerMembershipFailure12004::collection_header&&s.payload_reads==0,"header load order/missing count changed");}
  {Scene s;s.Header(1);auto r=ReadConstructionPointerMembership30A6080V1(s.access,s.inputs,s.inputs.selector_object_pointer,s.inputs.first_pointer+1);
    Check(!r.value&&r.failure==PointerMembershipFailure12004::copied_operands&&s.read_addresses.empty(),"cross-frame copied argument mismatch was read");
    s.access.exact_12004_bound=false;Check(s.Read().failure==PointerMembershipFailure12004::exact_build,"exact build gate lost");
    s.access.exact_12004_bound=true;s.access.read_memory=nullptr;Check(s.Read().failure==PointerMembershipFailure12004::read_callback,"missing raw reader fabricated AL");}
}
