#include "xar_bridge/verified_owner_wake_v1.hpp"
#include <cstdio>
using namespace xar::ck3_11906;
struct Fake { MainThreadQueryMailboxV1 *mailbox; int calls=0; bool fail=false; bool drift=false; };
VerifiedOwnerPostResultV1 FakePost(void *opaque,std::uint32_t owner) noexcept {
  auto &f=*static_cast<Fake *>(opaque); ++f.calls;
  if(owner!=42) return {false,999};
  if(f.drift) f.mailbox->owner_thread_id.store(43);
  return {!f.fail,f.fail?123u:0u};
}
void Ready(MainThreadQueryMailboxV1 &m) {
  m.state.store(MainThreadQueryMailboxStateV1::idle); m.iat_hook_installed.store(true);
  m.owner_thread_id.store(42);m.owner_verified_pump_epochs.store(kMainThreadQueryMinimumOwnerVerifiedPumpEpochs);
  m.observed_stamp_read_success.store(true);m.observed_current_thread_id.store(42);m.observed_rng_owner_thread_id.store(42);
  m.observed_tls_initialized.store(1);m.observed_tls_main_thread_marker.store(1);m.observed_tls_context.store(1);
}
int main(){
  int cases=0;
  for(int which=0;which<13;++which){
    MainThreadQueryMailboxV1 m{};Ready(m);Fake f{&m};
    switch(which){
    case 1:m.iat_hook_installed.store(false);break;case 2:m.state.store(MainThreadQueryMailboxStateV1::detached);break;
    case 3:m.stop_requested.store(true);break;case 4:m.failure_flags.store(1);break;case 5:m.proof_reset_requested.store(true);break;
    case 6:m.owner_thread_id.store(0);break;case 7:m.owner_verified_pump_epochs.store(0);break;
    case 8:m.observed_stamp_read_success.store(false);break;case 9:m.observed_current_thread_id.store(43);break;
    case 10:m.observed_rng_owner_thread_id.store(43);break;case 11:m.observed_tls_initialized.store(0);break;
    case 12:m.observed_tls_main_thread_marker.store(0);break;}
    auto r=WakeVerifiedApplicationMainOwnerV1(m,&FakePost,&f);
    if((which==0 || which==10) ? !(r.attempted&&r.posted&&r.owner_stable&&f.calls==1) : (r.attempted||r.posted||f.calls!=0))return 10+which;
    if(m.next_sequence.load()!=0||m.published_sequence.load()!=0||m.executed_requests.load()!=0)return 50;
    ++cases;
  }
  {MainThreadQueryMailboxV1 m{};Ready(m);m.observed_tls_context.store(0);Fake f{&m};auto r=WakeVerifiedApplicationMainOwnerV1(m,&FakePost,&f);if(r.attempted||f.calls)return 60;++cases;}
  {MainThreadQueryMailboxV1 m{};Ready(m);Fake f{&m,0,true};auto r=WakeVerifiedApplicationMainOwnerV1(m,&FakePost,&f);if(!r.attempted||r.posted||r.last_error!=123||f.calls!=1)return 61;VerifiedOwnerWakeCountersV1 c;c.Record(r);auto d=c.Read();if(d.attempts!=1||d.posted!=0||d.last_error!=123)return 62;++cases;}
  {MainThreadQueryMailboxV1 m{};Ready(m);Fake f{&m,0,false,true};auto r=WakeVerifiedApplicationMainOwnerV1(m,&FakePost,&f);if(!r.attempted||!r.posted||r.owner_stable||r.owner_after!=43||f.calls!=1)return 63;VerifiedOwnerWakeCountersV1 c;c.Record(r);if(c.Read().owner_drift!=1)return 64;++cases;}
  {MainThreadQueryMailboxV1 m{};Ready(m);auto r=WakeVerifiedApplicationMainOwnerV1(m,nullptr);if(r.attempted)return 65;VerifiedOwnerWakeCountersV1 c;c.Record(r);if(c.Read().guard_rejections!=1)return 66;++cases;}
  std::printf("PASS %d fake-poster guard/diagnostic cases; no OS posts or game I/O\n",cases);return 0;
}
