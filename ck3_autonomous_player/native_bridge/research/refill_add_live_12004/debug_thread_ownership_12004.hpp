#pragma once
// Included after the owning translation unit declares g_saved_debug.
// This guard is byte-identical to the already compiled maintenance watch guard.
bool BeginThreadOwnership(DWORD tid,const std::map<DWORD,HANDLE>&threads,const std::set<DWORD>&armed){
  if(threads.contains(tid)||armed.contains(tid))return false;
  g_saved_debug.erase(tid); // Never reuse a saved state from another thread generation.
  return true;
}
bool OwnDebugThread(DWORD tid,HANDLE borrowed,std::map<DWORD,HANDLE>&threads,const std::set<DWORD>&armed){
  if(!BeginThreadOwnership(tid,threads,armed))return false;
  HANDLE owned=nullptr;
  if(!DuplicateHandle(GetCurrentProcess(),borrowed,GetCurrentProcess(),&owned,0,FALSE,DUPLICATE_SAME_ACCESS))return false;
  threads.emplace(tid,owned);return true;
}
void RetireDebugThread(DWORD tid,std::map<DWORD,HANDLE>&threads,std::set<DWORD>&armed){
  const auto it=threads.find(tid);
  if(it!=threads.end()){if(it->second)CloseHandle(it->second);threads.erase(it);}
  armed.erase(tid);g_saved_debug.erase(tid);
}
