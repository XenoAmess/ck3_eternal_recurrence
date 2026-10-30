#include <windows.h>

BOOL WINAPI SwayFixtureVirtualProtect(LPVOID, SIZE_T, DWORD, PDWORD);
BOOL WINAPI SwayFixtureFlushInstructionCache(HANDLE, LPCVOID, SIZE_T);

// Compile the repository's actual observer; redirect only the two OS failure
// boundaries used by this regression. No production implementation is copied.
#define VirtualProtect SwayFixtureVirtualProtect
#define FlushInstructionCache SwayFixtureFlushInstructionCache
#include "../src/sway_common_termination_callsite_observer_12004.cpp"
#undef FlushInstructionCache
#undef VirtualProtect
