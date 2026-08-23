#include <windows.h>

#include <string_view>

int wmain(int argc, wchar_t** argv) {
  if (argc == 3 && std::wstring_view(argv[1]) == L"--wait-event") {
    HANDLE event = OpenEventW(SYNCHRONIZE, FALSE, argv[2]);
    if (event == nullptr) {
      return 2;
    }
    const DWORD wait_result = WaitForSingleObject(event, 30'000);
    CloseHandle(event);
    return wait_result == WAIT_OBJECT_0 ? 0 : 3;
  }
  // The offline host creates this process with CREATE_SUSPENDED. Reaching main
  // proves the host resumed the original primary thread after the injected DLL
  // completed its pipe exchange.
  return 0;
}
