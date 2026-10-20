#include "fixture_shared.hpp"
#include <algorithm>
#include <atomic>
#include <cstring>
#include <fstream>
#include <iostream>
#include <string>
#include <thread>
#include <stdexcept>
#include <utility>
#include <set>
#include <vector>
extern "C" {
alignas(16) ParentFixtureSeen ParentFixtureBodySeen{};
alignas(16) unsigned char ParentFixtureInputXmm[16][16]{};
alignas(16) unsigned char ParentFixtureReturnXmm[16]{};
alignas(16) unsigned char ParentFixtureFxBefore[512]{},ParentFixtureFxAfter[512]{};
alignas(16) unsigned char ParentFixtureReturnedXmm[16]{};
std::uint64_t ParentFixtureCallEntryRsp=0,ParentFixtureCallRbp=0;
std::uint64_t ParentFixtureReturnedRax=0,ParentFixtureReturnedRsp=0;
volatile LONG64 ParentFixtureBodyCalls=0;
void (*ParentFixtureCallTarget)()=&XarParentEntryThunk12004;
std::uint64_t ParentFixtureTarget();
}
namespace pe=xar::ck3_12004::parent_entry;
void Require(bool value,const char*message){if(!value)throw std::runtime_error(message);}
void Seed(){Require(ParentFixtureSeed(ParentFixtureTarget()),"private fixture seed failed");
  XarParentEntryContinuation12004=reinterpret_cast<std::uintptr_t>(&ParentFixtureBody);
  for(unsigned i=0;i<16;++i){for(unsigned j=0;j<16;++j)ParentFixtureInputXmm[i][j]=static_cast<unsigned char>(i*13+j);
    ParentFixtureReturnXmm[i]=static_cast<unsigned char>(0xf0+i);}
  InterlockedExchange64(&ParentFixtureBodyCalls,0);
}
void ABI(){
  Seed();Require(pe::ArmOnce(),"arm failed");ParentFixtureInvoke(ParentFixtureTarget());
  pe::Snapshot out;Require(pe::StopAndSnapshot(out)&&out.stopped&&out.frame.has_value(),"snapshot incomplete");
  const auto&f=*out.frame;const auto&b=ParentFixtureBodySeen;
  Require(f.rax==0xaaaa&&f.rcx==0x1111&&f.rdx==ParentFixtureTarget()&&
    f.r8==0xeeeeeeeefffffff9ULL&&f.r9==0x9999&&f.r10==0xa0a0&&f.r11==0xb0b0,"volatile input changed");
  Require(f.rbx==0xbbbb&&f.rbp==ParentFixtureCallRbp&&f.rsi==0x5151&&f.rdi==0xd1d1&&
    f.r12==0x1212&&f.r13==0x1313&&f.r14==0x1414&&f.r15==0x1515,"nonvolatile entry changed");
  Require(f.rsp==ParentFixtureCallEntryRsp&&(f.rflags&0xcd5)==(0xed7&0xcd5),"entry stack or user flags changed");
  Require(f.native_return==reinterpret_cast<std::uintptr_t>(&ParentFixtureAfterCall)&&f.tid==GetCurrentThreadId(),"actual native return slot/TID changed");
  Require(b.rax==f.rsp&&b.rcx==f.rcx&&b.rdx==f.rdx&&b.r8==f.r8&&b.r9==f.r9&&
    b.r10==f.r10&&b.r11==f.r11&&b.rbx==f.rbx&&b.rbp==f.rbp&&b.rsi==f.rsi&&b.rdi==f.rdi&&
    b.r12==f.r12&&b.r13==f.r13&&b.r14==f.r14&&b.r15==f.r15,"native body inputs changed");
  Require(b.rsp==f.rsp-0xa8&&b.fifth==0x5555&&b.sixth==0x6666,"prefix stack/input stack args changed");
  Require(std::memcmp(b.xmm,ParentFixtureInputXmm,sizeof b.xmm)==0,"XMM input changed");
  Require(std::memcmp(ParentFixtureFxBefore,ParentFixtureFxAfter,160)==0,"x87/MXCSR changed");
  Require(ParentFixtureReturnedRax==0xd00dfeed11223344ULL&&
    ParentFixtureReturnedRsp==f.rsp+8&&std::memcmp(ParentFixtureReturnedXmm,ParentFixtureReturnXmm,16)==0,"return ABI changed");
  Require(ParentFixtureBodyCalls==1&&out.matching_pointer_count==1&&out.dropped_matching_count==0,"original not exactly once");
  Require(std::memcmp(reinterpret_cast<const void*>(&XarParentEntryOriginalPrefix12004),pe::kPrefix.data(),16)==0,"emitted first16B differs");
}
void ForeignAndDefaultOff(){
  Seed();ParentFixtureInvoke(ParentFixtureTarget());
  Require(XarParentEntryState12004.frame_state==0&&XarParentEntryState12004.matching_pointer_count==0&&ParentFixtureBodyCalls==1,"defaultOFF collects or skips original");
  Seed();Require(pe::ArmOnce(),"arm foreign test");
  for(unsigned i=0;i<257;++i)ParentFixtureInvoke(ParentFixtureTarget()+8);
  Require(XarParentEntryState12004.frame_state==0,"foreign consumed first frame");
  ParentFixtureInvoke(ParentFixtureTarget());pe::Snapshot out;
  Require(pe::StopAndSnapshot(out)&&out.foreign_count==257&&out.matching_pointer_count==1&&ParentFixtureBodyCalls==258,"foreign budget or original count wrong");
}
void StateRoutes(){
  Require(ParentFixtureAdmissionGuardTest(),"native local player1/Character33388 guard regression");
  Seed();Require(pe::ArmOnce()&&!pe::ArmOnce(),"rearm accepted");
  InterlockedExchange64(&XarParentEntryState12004.active_thunks,1);pe::Snapshot busy;
  Require(!pe::StopAndSnapshot(busy)&&!busy.stopped&&busy.producer_busy==true&&!busy.foreign_count,"injected busy falsely closed");
  Require(XarParentEntryState12004.enabled==0,"OFF not attempted before busy refusal");
  InterlockedExchange64(&XarParentEntryState12004.active_thunks,0);pe::Snapshot done;
  Require(pe::StopAndSnapshot(done)&&done.stopped,"busy completion readback failed");
  Require(!pe::Uninstall(false),"unproven quiescence unpatch accepted");
  Seed();Require(pe::ArmOnce(),"arm overflow");InterlockedExchange64(&XarParentEntryState12004.foreign_count,-1);
  ParentFixtureInvoke(ParentFixtureTarget()+8);pe::Snapshot overflow;
  Require(pe::StopAndSnapshot(overflow)&&overflow.counter_overflow==true&&!overflow.foreign_count&&overflow.raw_foreign_counter_bits==0,"counter wrap became fake zero");
  Seed();Require(pe::ArmOnce(),"arm corrupt");InterlockedExchange64(&XarParentEntryState12004.frame_state,3);pe::Snapshot corrupt;
  Require(!pe::StopAndSnapshot(corrupt)&&!corrupt.stopped&&!corrupt.matching_pointer_count,"corrupt state falsely stopped");
  Seed();Require(pe::ArmOnce(),"arm read fault");ParentFixtureReadFailure(true);pe::Snapshot fault;
  Require(!pe::StopAndSnapshot(fault)&&!fault.stopped&&!fault.foreign_count&&XarParentEntryState12004.enabled==0,"read fault produced false clean");
  ParentFixtureReadFailure(false);
}
void ConcurrentOff(){
  Seed();Require(pe::ArmOnce(),"arm concurrent");
  std::atomic<unsigned> ready{0};std::atomic<bool> go{false};std::vector<std::thread> workers;
  for(unsigned i=0;i<8;++i)workers.emplace_back([&,i]{++ready;while(!go.load())SwitchToThread();
    for(unsigned j=0;j<512;++j)ParentFixtureInvoke(ParentFixtureTarget()+(i?8:0));});
  while(ready.load()!=8)SwitchToThread();go=true;Sleep(1);
  pe::Snapshot first;const bool closed_during_calls=pe::StopAndSnapshot(first);
  if(!closed_during_calls)Require(!first.stopped&&!first.foreign_count,"concurrent unknown not null");
  for(auto&t:workers)t.join();pe::Snapshot final;Require(pe::StopAndSnapshot(final)&&final.stopped,"concurrent closure failed");
  Require(ParentFixtureBodyCalls==4096&&XarParentEntryState12004.active_thunks==0,"concurrent original execution lost");
  // Scheduling may leave zero target entries before OFF. Keep that real outcome;
  // this checks integrity/OFF, not guaranteed occurrence or every interleaving.
}
bool SafeUnwind(DWORD64 base,DWORD64 pc,PRUNTIME_FUNCTION fn,CONTEXT&c) noexcept {
  __try {PVOID handler=nullptr;DWORD64 frame=0;
    RtlVirtualUnwind(UNW_FLAG_NHANDLER,base,pc,fn,&c,&handler,&frame,nullptr);return true;
  }__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
void Describe(){
  const auto image=reinterpret_cast<DWORD64>(GetModuleHandleW(nullptr));
  std::cout<<"{\"image_base\":"<<image;
  for(const auto item:{std::pair<const char*,void*>{"thunk",reinterpret_cast<void*>(&XarParentEntryThunk12004)},
                       {"prefix",reinterpret_cast<void*>(&XarParentEntryOriginalPrefix12004)}}){
    DWORD64 base=0;auto*f=RtlLookupFunctionEntry(reinterpret_cast<DWORD64>(item.second),&base,nullptr);
    Require(f&&base==image,"function entry missing");
    std::cout<<",\""<<item.first<<"\":{\"rva\":"<<f->BeginAddress<<",\"bytes\":"<<f->EndAddress-f->BeginAddress<<"}";
  }std::cout<<"}\n";
}
unsigned UnwindCases(const char*path){
  std::ifstream input(path);Require(input.good(),"case file unavailable");
  std::string header,tkey,pkey;unsigned expected_t=0,expected_p=0,bytes_t=0,bytes_p=0;
  Require(bool(input>>header>>tkey>>expected_t>>bytes_t>>pkey>>expected_p>>bytes_p)&&
    header=="COUNTS"&&tkey=="T"&&pkey=="P"&&expected_t>0&&expected_p>0&&expected_t+expected_p<=1024,"missing decoder counts");
  std::set<std::pair<std::string,unsigned>> visited;unsigned seen_t=0,seen_p=0,last_t=0,last_p=0;bool started_p=false;
  std::string kind;unsigned offset=0,frame_mode=0,count=0;int delta=0;
  while(input>>kind>>std::hex>>offset>>std::dec>>delta>>frame_mode){
    Require(kind=="T"||kind=="P","bad case kind");Require(++count<=1024,"case overflow");
    Require(visited.emplace(kind,offset).second,"duplicate instruction PC");
    if(kind=="T"){
      Require(!started_p&&(seen_t==0?offset==0:offset>last_t),"thunk coverage order");last_t=offset;++seen_t;
    }else{
      started_p=true;Require(seen_p==0?offset==0:offset>last_p,"prefix coverage order");last_p=offset;++seen_p;
    }
    auto*address=kind=="T"?reinterpret_cast<void*>(&XarParentEntryThunk12004):reinterpret_cast<void*>(&XarParentEntryOriginalPrefix12004);
    DWORD64 base=0;auto*f=RtlLookupFunctionEntry(reinterpret_cast<DWORD64>(address),&base,nullptr);
    Require(f&&offset<f->EndAddress-f->BeginAddress,"case outside function");
    Require(f->EndAddress-f->BeginAddress==(kind=="T"?bytes_t:bytes_p),"decoder function range differs");
    alignas(16) unsigned char stack[4096]{};const auto s=reinterpret_cast<DWORD64>(stack+2056);
    CONTEXT c{};c.ContextFlags=CONTEXT_FULL;c.Rip=base+f->BeginAddress+offset;c.Rsp=s+delta;
    c.Rbx=0xbbbb;c.Rbp=frame_mode?s-0x50:0xbaba;c.Rsi=0x5151;c.Rdi=0xd1d1;
    c.R12=0x1212;c.R13=0x1313;c.R14=0x1414;c.R15=0x1515;
    *reinterpret_cast<DWORD64*>(s)=reinterpret_cast<DWORD64>(&Describe);
    if(kind=="T"){
      *reinterpret_cast<DWORD64*>(s-8)=0xbaba;
      *reinterpret_cast<DWORD64*>(s-16)=0xed7;
    }else{
      *reinterpret_cast<DWORD64*>(s-8)=0xbbbb;
      *reinterpret_cast<DWORD64*>(s-16)=0xbaba;
      *reinterpret_cast<DWORD64*>(s-0x20)=0x1414;
    }
    Require(SafeUnwind(base,c.Rip,f,c),"RtlVirtualUnwind raised");
    Require(c.Rip==reinterpret_cast<DWORD64>(&Describe)&&c.Rsp==s+8&&c.Rbp==0xbaba&&
      c.Rbx==0xbbbb&&c.R14==0x1414&&c.Rsi==0x5151&&c.Rdi==0xd1d1&&
      c.R12==0x1212&&c.R13==0x1313&&c.R15==0x1515,"RtlVirtualUnwind caller state mismatch");
  }
  Require(input.eof()&&count>32&&seen_t==expected_t&&seen_p==expected_p,"missing/truncated instruction cases");return count;
}
int main(int argc,char**argv){
  try{
    Require(argc>=3,"usage: EXE MODE MACHINE_ID [CASES]; no CK3 contact");
    const std::string mode=argv[1],machine=argv[2];
    Require(machine=="desktop-3fevhd2-1c74096080","explicit fixture machine binding required");
    if(mode=="--describe"){Describe();return 0;}
    unsigned checks=0;
    if(mode=="--abi"){ABI();ForeignAndDefaultOff();checks=2;}
    else if(mode=="--state-routes"){StateRoutes();ConcurrentOff();checks=2;}
    else if(mode=="--unwind"){Require(argc==4,"case file required");checks=UnwindCases(argv[3]);}
    else Require(false,"unknown explicit mode");
    std::cout<<"{\"schema\":\"xar.parent-entry.synthetic-cold.v1\",\"machine_id\":\""<<machine
      <<"\",\"mode\":\""<<mode<<"\",\"passed_checks\":"<<checks
      <<",\"game_contact\":false,\"fixture_private_owner_seed\":true,\"real_Install_Restore_qualified\":false,\"full_native_qualification\":false}\n";
    return 0;
  }catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 1;}
}
