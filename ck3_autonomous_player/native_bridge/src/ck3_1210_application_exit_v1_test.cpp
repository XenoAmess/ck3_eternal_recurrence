#include "xar_bridge/ck3_1210_application_exit_v1.hpp"
#include <windows.h>
#include <array>
#include <cstdio>
#include <cstdlib>
#include <cstring>
using namespace xar::ck3_1210;
namespace {
unsigned calls=0;
void Quit(void *app) { ++calls; static_cast<unsigned char *>(app)[0x89]=1; }
void NoEffect(void *) { ++calls; }
void Fault(void *) { ++calls; RaiseException(0xE0123456,0,0,nullptr); }
struct Admission { bool accepted=true; void **slot=nullptr; void *replacement=nullptr; };
bool Admitted(void *opaque) noexcept {
  auto &a=*static_cast<Admission *>(opaque);
  if(a.slot!=nullptr) *a.slot=a.replacement;
  return a.accepted;
}
void Check(bool value,int line) { if(!value) { std::fprintf(stderr,"exit fixture line %d",line); std::exit(1); } }
}
#define CHECK(x) Check((x),__LINE__)
int main() {
  std::array<unsigned char,0x100> app{},other{};void *slot=app.data();Admission admit{};
  const std::uintptr_t table=0x12340; std::memcpy(app.data(),&table,sizeof(table));
  ApplicationExitBindingsV1 b{true,&slot,&Quit,table,table+8};
  CHECK(!BindApplicationExitImageV1(1,"old image").enabled);
  CHECK(!BindApplicationExitImageV1(0,kExecutableSha256).enabled);
  { ApplicationExitSessionV1 s;admit.accepted=false;
    CHECK(RequestApplicationExitV1(b,s,&Admitted,&admit)==ApplicationExitStatusV1::admission_rejected);
    CHECK(!s.claimed.load() && calls==0);admit.accepted=true; }
  { ApplicationExitSessionV1 s;admit.slot=&slot;admit.replacement=other.data();
    CHECK(RequestApplicationExitV1(b,s,&Admitted,&admit)==ApplicationExitStatusV1::admission_rejected);
    CHECK(!s.claimed.load() && calls==0);admit.slot=nullptr;slot=app.data(); }
  { ApplicationExitSessionV1 s;
    CHECK(RequestApplicationExitV1(b,s,&Admitted,&admit)==ApplicationExitStatusV1::requested);
    CHECK(s.claimed.load() && calls==1 && app[0x89]==1);
    app[0x89]=0; // Even a changed native flag cannot release a consumed request.
    CHECK(RequestApplicationExitV1(b,s,&Admitted,&admit)==ApplicationExitStatusV1::claim_consumed);
    CHECK(calls==1); }
  { ApplicationExitSessionV1 s;b.request_quit=&NoEffect;
    CHECK(RequestApplicationExitV1(b,s,&Admitted,&admit)==ApplicationExitStatusV1::indeterminate);
    CHECK(s.claimed.load() && calls==2);
    CHECK(RequestApplicationExitV1(b,s,&Admitted,&admit)==ApplicationExitStatusV1::claim_consumed);
    CHECK(calls==2); }
  { ApplicationExitSessionV1 s;b.request_quit=&Fault;
    CHECK(RequestApplicationExitV1(b,s,&Admitted,&admit)==ApplicationExitStatusV1::indeterminate);
    CHECK(s.claimed.load() && calls==3);
    CHECK(RequestApplicationExitV1(b,s,&Admitted,&admit)==ApplicationExitStatusV1::claim_consumed);
    CHECK(calls==3); }
  { ApplicationExitSessionV1 s;b.request_quit=&Quit;app[0x89]=1;
    CHECK(RequestApplicationExitV1(b,s,&Admitted,&admit)==ApplicationExitStatusV1::already_requested);
    CHECK(calls==3 && s.claimed.load()); }
  { ApplicationExitSessionV1 s;app[0x89]=2;
    CHECK(RequestApplicationExitV1(b,s,&Admitted,&admit)==ApplicationExitStatusV1::unavailable);
    CHECK(calls==3 && !s.claimed.load()); }
  std::puts("PASS native application quit helper: exact guard rejection, admission/identity, once-only and fault/unknown ownership; NoGame");
}
