#include "xar_bridge/conception_pair_provider_passive_12004.hpp"
#include <cstring>
#include <stdexcept>

namespace xar::ck3_12004 {
namespace {
void Check(bool condition) { if (!condition) throw std::runtime_error("provider boundary fixture"); }
struct Fixture {
  std::array<std::byte,0x40> first{},second{};
  std::int64_t output=17, native_output=250000;
  ConceptionSampleParentScope12004 scope{};
  std::uint64_t event_sequence=100;
  std::uint32_t calls=0, read_calls=0, attached=0;
  bool fail_before=false, fail_after=false, fail_ids=false, change_parent=false;
  bool different_return=false, fail_attach=false, wrong_clock=false;
  void *last_output=nullptr,*last_first=nullptr,*last_second=nullptr,*last_fifth=nullptr;
  std::uint32_t last_mode=0;
  std::optional<ConceptionPairProviderObservation12004> child;
  std::array<std::uint8_t,32> target{};
  std::array<std::uint8_t,30> trampoline{};
  std::uint32_t allocations=0,frees=0,protects=0,flushes=0;
  std::uint32_t fail_protect_at=0,fail_flush_at=0;
  Fixture() {
    scope.active=true; scope.parent_scope_id=100; scope.process_clock=100;
    scope.clock_identity=0x713; scope.thread_id=GetCurrentThreadId();
    scope.first_character=reinterpret_cast<std::uintptr_t>(first.data());
    scope.second_character=reinterpret_cast<std::uintptr_t>(second.data());
    scope.first_full_id=0xF0000001U; scope.second_full_id=2;
    scope.sample_receiver=0x714;
    std::memcpy(first.data()+0x18,&scope.first_full_id,4);
    std::memcpy(second.data()+0x18,&scope.second_full_id,4);
    constexpr std::array<std::uint8_t,16> prefix{
      0x48,0x89,0x5C,0x24,0x08,0x55,0x56,0x57,0x41,0x54,0x41,0x55,0x41,0x56,0x41,0x57};
    std::memcpy(target.data(),prefix.data(),prefix.size());
  }
  static bool Read(void *context,const void *address,void *out,std::size_t size) noexcept {
    auto &f=*static_cast<Fixture *>(context); ++f.read_calls;
    if (address==&f.output && ((f.calls==0 && f.fail_before) || (f.calls!=0 && f.fail_after))) return false;
    if (f.fail_ids && (address==f.first.data()+0x18 || address==f.second.data()+0x18)) return false;
    const auto a=reinterpret_cast<std::uintptr_t>(address);
    auto Contains=[&](const void *base,std::size_t bytes) noexcept {
      const auto b=reinterpret_cast<std::uintptr_t>(base);
      return a>=b && a-b<=bytes && size<=bytes-(a-b);
    };
    if (!Contains(f.first.data(),f.first.size()) && !Contains(f.second.data(),f.second.size()) &&
        !Contains(&f.output,sizeof(f.output)) && !Contains(f.target.data(),f.target.size())) return false;
    std::memcpy(out,address,size); return true;
  }
  static bool Parent(void *context,ConceptionSampleParentScope12004 &out) noexcept {
    auto &f=*static_cast<Fixture *>(context); out=f.scope;
    if (f.change_parent && f.calls!=0) ++out.parent_scope_id;
    return out.active;
  }
  static PersonInstalledTransferEvent12004 Event(void *context) noexcept {
    auto &f=*static_cast<Fixture *>(context);
    return {f.wrong_clock ? f.scope.clock_identity+1 : f.scope.clock_identity,
      ++f.event_sequence,f.scope.thread_id};
  }
  static bool Attach(void *context,const ConceptionPairProviderObservation12004 &record) noexcept {
    auto &f=*static_cast<Fixture *>(context); ++f.attached;
    if (f.fail_attach) return false;
    f.child=record; return true;
  }
  static void *__fastcall Native(void *out,void *first,void *second,std::uint32_t mode,void *fifth);
  ConceptionPairProviderBindings12004 Bind() {
    auto b=BindConceptionPairProviderImage12004(0x10000000,kConceptionPairProviderSourcePin12004);
    b.read_context=this; b.read_memory=Read; b.parent_context=this; b.read_parent=Parent;
    b.event_context=this; b.next_event=Event; b.child_return_context=this; b.child_return=Attach;
    return b;
  }
  static void *Alloc(void *context,std::size_t size,DWORD,DWORD) noexcept {
    auto &f=*static_cast<Fixture *>(context); ++f.allocations;
    return size<=f.trampoline.size() ? f.trampoline.data() : nullptr;
  }
  static bool Free(void *context,void *,std::size_t,DWORD) noexcept {
    ++static_cast<Fixture *>(context)->frees; return true;
  }
  static bool Protect(void *context,void *,std::size_t,DWORD,DWORD &previous) noexcept {
    auto &f=*static_cast<Fixture *>(context); previous=PAGE_EXECUTE_READ;
    return ++f.protects!=f.fail_protect_at;
  }
  static bool Flush(void *context,const void *,std::size_t) noexcept {
    auto &f=*static_cast<Fixture *>(context); return ++f.flushes!=f.fail_flush_at;
  }
  ConceptionPairProviderInstallEnvironment12004 Environment() {
    ConceptionPairProviderInstallEnvironment12004 e;
    e.primary_thread_suspended_proven=true; e.bindings=Bind();
    e.bindings.image_base=reinterpret_cast<std::uintptr_t>(target.data())-kConceptionPairProviderRva12004;
    e.callback_target_override=0x1234567812345678ULL;
    e.memory_context=this; e.virtual_alloc_override=Alloc; e.virtual_free_override=Free;
    e.virtual_protect_override=Protect; e.flush_instruction_cache_override=Flush;
    return e;
  }
};
thread_local Fixture *active=nullptr;
void *__fastcall Fixture::Native(void *out,void *first,void *second,std::uint32_t mode,void *fifth) {
  auto &f=*active; ++f.calls;
  f.last_output=out; f.last_first=first; f.last_second=second; f.last_mode=mode; f.last_fifth=fifth;
  if (out==&f.output) f.output=f.native_output;
  return f.different_return ? f.first.data() : out;
}
ConceptionPairProviderObservation12004 Capture(Fixture &f) {
  active=&f; Check(InitializeConceptionPairProviderFixture12004(f.Bind(),Fixture::Native));
  void *returned=InvokeConceptionPairProviderFixture12004(kConceptionPairProviderReturnRva12004,
      &f.output,f.first.data(),f.second.data(),3,nullptr);
  Check(f.calls==1 && f.last_output==&f.output && f.last_first==f.first.data() &&
        f.last_second==f.second.data() && f.last_mode==3 && f.last_fifth==nullptr);
  Check(returned==(f.different_return ? static_cast<void *>(f.first.data()) : static_cast<void *>(&f.output)));
  const auto records=ReadConceptionPairProviderObservations12004(f.scope.clock_identity,f.scope.parent_scope_id);
  Check(records && records->events.size()==1); return records->events.front();
}
} // namespace

bool RunConceptionPairProviderPassiveFixture12004() noexcept {
  try {
    {
      Fixture f; const auto r=Capture(f);
      Check(r.output_before==17 && r.output_after==250000 && r.actual_caller_input_ready &&
            r.original_returned && r.native_return_matches_output && f.attached==1 && f.child &&
            r.first_full_id_after==0xF0000001U && r.process_id==GetCurrentProcessId());
      Check(f.child->journal_sequence==r.journal_sequence);
      const auto serialized=SerializeConceptionPairProviderObservation12004(r);
      Check(serialized.find("\"output_after\":250000")!=std::string::npos &&
            serialized.find("\"source\":\"natural_original_pair_provider_first_qword\"")!=std::string::npos);
    }
    { Fixture f; f.fail_before=true; const auto r=Capture(f);
      Check(!r.output_before && r.output_after==250000 && r.actual_caller_input_ready); }
    { Fixture f; f.fail_after=true; const auto r=Capture(f);
      Check(r.output_before==17 && !r.output_after && !r.actual_caller_input_ready &&
            SerializeConceptionPairProviderObservation12004(r).find("\"output_after\":null")!=std::string::npos); }
    { Fixture f; f.different_return=true; const auto r=Capture(f);
      Check(!r.native_return_matches_output && r.actual_caller_input_ready && r.output_after==250000); }
    { Fixture f; f.native_output=0; const auto r=Capture(f);
      Check(r.output_after==0 && r.actual_caller_input_ready); }
    { Fixture f; f.fail_ids=true; const auto r=Capture(f);
      Check(!r.first_full_id_before && !r.first_full_id_after && r.output_after==250000 &&
            (r.capture_failure_flags&conception_provider_capture_identity_after)!=0); }
    { Fixture f; f.change_parent=true; const auto r=Capture(f);
      Check(r.output_after==250000 && !r.parent_extent_unchanged && !r.actual_caller_input_ready); }
    { Fixture f; f.wrong_clock=true; const auto r=Capture(f);
      Check(r.output_after==250000 && !r.event_clock_and_thread_match && !r.actual_caller_input_ready); }
    { Fixture f; f.fail_attach=true; const auto r=Capture(f);
      Check(r.actual_caller_input_ready && (r.capture_failure_flags&conception_provider_capture_attach)!=0); }
    {
      for (std::uint32_t cell=0; cell<5; ++cell) {
        Fixture f; active=&f;
        if (cell==4) f.scope.active=false;
        Check(InitializeConceptionPairProviderFixture12004(f.Bind(),Fixture::Native));
        const auto rva=cell==0 ? kConceptionPairProviderReturnRva12004+1 : kConceptionPairProviderReturnRva12004;
        void *first_arg=cell==3 ? static_cast<void *>(f.second.data()) : static_cast<void *>(f.first.data());
        void *fifth=cell==2 ? static_cast<void *>(f.first.data()) : nullptr;
        void *returned=InvokeConceptionPairProviderFixture12004(rva,&f.output,first_arg,f.second.data(),cell==1?2U:3U,fifth);
        const auto records=ReadConceptionPairProviderObservations12004();
        Check(returned==&f.output && f.calls==1 && f.read_calls==0 && f.attached==0 &&
              records && records->events.empty() && f.last_first==first_arg && f.last_fifth==fifth);
      }
    }
    {
      Fixture f; ConceptionPairProviderDetourState12004 state;
      auto env=f.Environment(); env.primary_thread_suspended_proven=false;
      Check(!InstallConceptionPairProviderPassive12004(state,env,kConceptionPairProviderSourcePin12004) && f.allocations==0);
      env.primary_thread_suspended_proven=true; f.target[0]=0;
      Check(!InstallConceptionPairProviderPassive12004(state,env,kConceptionPairProviderSourcePin12004) && f.allocations==0);
    }
    {
      Fixture f; const auto expected=f.target; ConceptionPairProviderDetourState12004 state;
      const auto env=f.Environment();
      Check(InstallConceptionPairProviderPassive12004(state,env,kConceptionPairProviderSourcePin12004));
      Check(f.allocations==1 && f.target[0]==0xFF && f.target[1]==0x25 &&
            f.target[14]==0x90 && f.target[15]==0x90 && f.calls==0);
      Check(std::memcmp(f.trampoline.data(),expected.data(),16)==0 && f.trampoline[16]==0xFF);
      std::uintptr_t return_target=0; std::memcpy(&return_target,f.trampoline.data()+22,sizeof(return_target));
      Check(return_target==reinterpret_cast<std::uintptr_t>(f.target.data())+16);
      Check(UninstallConceptionPairProviderPassive12004(state,true) && f.target==expected && f.frees==1);
    }
    {
      Fixture f; const auto expected=f.target; f.fail_flush_at=2;
      ConceptionPairProviderDetourState12004 state; const auto env=f.Environment();
      Check(!InstallConceptionPairProviderPassive12004(state,env,kConceptionPairProviderSourcePin12004));
      Check(f.target==expected && f.frees==1 && state.installed.load()==0 && f.calls==0);
    }
    active=nullptr; return true;
  } catch (...) { active=nullptr; return false; }
}
} // namespace xar::ck3_12004
