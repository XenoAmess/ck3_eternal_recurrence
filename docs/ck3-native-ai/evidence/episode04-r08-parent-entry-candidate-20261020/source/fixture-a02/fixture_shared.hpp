#pragma once
#include "../candidate-a04/parent_entry_opportunity_12004.hpp"
struct alignas(16) ParentFixtureSeen {
  std::uint64_t rax,rcx,rdx,r8,r9,r10,r11,rbx,rbp,rsi,rdi,r12,r13,r14,r15,rsp;
  unsigned char xmm[16][16];
  std::uint64_t fifth,sixth;
};
extern "C" {
extern ParentFixtureSeen ParentFixtureBodySeen;
extern unsigned char ParentFixtureInputXmm[16][16];
extern unsigned char ParentFixtureReturnXmm[16];
extern unsigned char ParentFixtureFxBefore[512],ParentFixtureFxAfter[512];
extern std::uint64_t ParentFixtureCallEntryRsp,ParentFixtureCallRbp;
extern std::uint64_t ParentFixtureReturnedRax,ParentFixtureReturnedRsp;
extern unsigned char ParentFixtureReturnedXmm[16];
extern volatile LONG64 ParentFixtureBodyCalls;
extern void (*ParentFixtureCallTarget)();
void ParentFixtureInvoke(std::uint64_t target);
void ParentFixtureBody();
void ParentFixtureAfterCall();
bool ParentFixtureSeed(std::uint64_t target);
void ParentFixtureReadFailure(bool fail);
bool ParentFixtureAdmissionGuardTest();
}
