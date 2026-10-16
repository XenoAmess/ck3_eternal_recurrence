// Focused synthetic ownership counterexamples; not an OS attach/TID-reuse test.
// Compile and run only via a separately qualified future project build.
#include <array>
#include <cstdint>
#include <map>
#include <set>
#include <vector>
using DWORD=std::uint32_t;using DWORD64=std::uint64_t;using HANDLE=void*;
constexpr bool FALSE=false;constexpr DWORD DUPLICATE_SAME_ACCESS=2;
std::map<DWORD,std::array<DWORD64,6>> g_saved_debug;
std::vector<HANDLE> closed;bool duplicate_ok=true;
HANDLE GetCurrentProcess(){return reinterpret_cast<HANDLE>(1);}
bool DuplicateHandle(HANDLE,HANDLE borrowed,HANDLE,HANDLE*out,DWORD,bool,DWORD){
  if(!duplicate_ok)return false;
  *out=reinterpret_cast<HANDLE>(reinterpret_cast<std::uintptr_t>(borrowed)+0x1000);return true;
}
bool CloseHandle(HANDLE h){closed.push_back(h);return true;}
#include "debug_thread_ownership_12004.hpp"
int main(){
  constexpr DWORD tid=123;HANDLE borrowed=reinterpret_cast<HANDLE>(0x2000);
  std::map<DWORD,HANDLE> threads;std::set<DWORD> armed;
  // The old a06 path: exited TID leaves a saved DR0, then occupied-DR arm rejects
  // before saving a new context. Its contains(tid) branch would falsely arm it.
  g_saved_debug[tid]={0xdead0000,0,0,0,0,0};
  if(!OwnDebugThread(tid,borrowed,threads,armed)||g_saved_debug.contains(tid))return 1;
  const bool rejected_new_arm=false; // Occupied/TF/GetContext early reject: no new save.
  if(rejected_new_arm||g_saved_debug.contains(tid))armed.insert(tid);
  if(armed.contains(tid)||threads.at(tid)==borrowed)return 2;
  RetireDebugThread(tid,threads,armed);
  if(!threads.empty()||!armed.empty()||g_saved_debug.contains(tid)||closed.size()!=1||closed[0]==borrowed)return 3;
  // EXIT retires a real saved context too, including in the cleanup loop.
  if(!OwnDebugThread(tid,borrowed,threads,armed))return 4;
  g_saved_debug[tid]={0xbeef0000,0,0,0,0,0};armed.insert(tid);
  RetireDebugThread(tid,threads,armed);
  if(g_saved_debug.contains(tid)||armed.contains(tid)||!threads.empty())return 5;
  // Failed duplication must leave no ownership or restore obligation.
  duplicate_ok=false;g_saved_debug[tid]={0xdead0000,0,0,0,0,0};
  if(OwnDebugThread(tid,borrowed,threads,armed)||!threads.empty()||g_saved_debug.contains(tid))return 6;
  return 0;
}
