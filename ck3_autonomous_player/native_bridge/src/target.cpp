#include <windows.h>

int wmain() {
  // The offline host creates this process with CREATE_SUSPENDED. Reaching main
  // proves the host resumed the original primary thread after the injected DLL
  // completed its pipe exchange.
  return 0;
}
