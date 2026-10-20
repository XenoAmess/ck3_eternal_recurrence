#include "xar_bridge/character_knight_effectiveness12004.hpp"
#include "xar_bridge/character_skill_effect12004_native.hpp"
#include <windows.h>
#include <cassert>
#ifdef NDEBUG
#error Assertions are required.
#endif
namespace c=xar::bridge::character_skill_effect12004;
int main(){
  c::NativeContext unavailable{};
  assert(!c::BindKnightNative(unavailable).actor.enabled);
  assert(unavailable.level_calls==0&&unavailable.breakdown_calls==0&&unavailable.string_destroy_calls==0);
  c::NativeContext wrong_thread{};wrong_thread.enabled=true;wrong_thread.module_base=1;
  wrong_thread.executable_sha256=c::kExeSha;wrong_thread.owner_thread_id=GetCurrentThreadId()+1;
  assert(!c::BindKnightNative(wrong_thread).actor.enabled);
  assert(wrong_thread.breakdown_calls==0&&wrong_thread.string_destroy_calls==0);
  // Actual native cleanup is not stubbed with owned callbacks. Its exact one
  // destructor attempt per entered native formatter is source-audited and is
  // counted by the actual owner executor; it still needs loaded execution.
}
