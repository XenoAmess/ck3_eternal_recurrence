#pragma once
#include <windows.h>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <stdexcept>
#include <string>

namespace m1_native_liege17 {

template <class T>
T Load(const void* base, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::uint8_t*>(base) + offset, sizeof(value));
  return value;
}

template <class T>
void Store(void* base, std::size_t offset, T value) {
  std::memcpy(static_cast<std::uint8_t*>(base) + offset, &value, sizeof(value));
}

inline void Require(bool value, const char* message) {
  if (!value) throw std::runtime_error(message);
}

class NativeLiegeImage17 final {
 public:
  explicit NativeLiegeImage17(const std::string& raw_path)
      : image_(nullptr), original_code_{} {
    try {
      // Reserve sparse address space with original RVA layout.
      // Size 0x5C68000 covers RVA 0x28BF000 to 0x5C67FFF.
      image_ = static_cast<std::uint8_t*>(VirtualAlloc(
          nullptr, 0x5C68000U, MEM_RESERVE, PAGE_NOACCESS));
      Require(image_ != nullptr, "reserve relative image");

      // Commit only the code page (0x28BF000..0x28C0000) and globals page (0x5C67000..0x5C68000).
      // Code page size: 0x1000. Globals page size: 0x1000.
      Commit(0x28BF000U, 0x1000U);
      Commit(0x5C67000U, 0x1000U);

      // Read exactly 118 bytes from the supplied raw path.
      std::ifstream input(raw_path, std::ios::binary);
      Require(static_cast<bool>(input), "read original held fragment");

      // Read into fixed array + one extra byte to reject too long source files.
      std::array<std::uint8_t, 119> buffer{};
      input.read(reinterpret_cast<char*>(buffer.data()), 119);
      Require(input.gcount() == 118, "original fragment exact size");

      // Place unchanged at image+0x28BFC50.
      std::memcpy(image_ + 0x28BFC50U, buffer.data(), 118);
      std::memcpy(original_code_.data(), buffer.data(), 118);

      // Set initial RIP targets to null (ordinary fixture data).
      Store<void*>(image_, 0x5C67568U, nullptr);
      Store<void*>(image_, 0x5C67570U, nullptr);

      // Protect code page as PAGE_EXECUTE_READ.
      DWORD old_protection = 0;
      Require(VirtualProtect(image_ + 0x28BF000U, 0x1000U,
          PAGE_EXECUTE_READ, &old_protection) != FALSE, "protect original code");

      // Flush instruction cache once after code is copied.
      Require(FlushInstructionCache(GetCurrentProcess(), image_ + 0x28BF000U,
          0x1000U) != FALSE, "flush original code");
    } catch (...) {
      if (image_) {
        VirtualFree(image_, 0, MEM_RELEASE);
        image_ = nullptr;
      }
      throw;
    }
  }

  ~NativeLiegeImage17() {
    if (image_) {
      VirtualFree(image_, 0, MEM_RELEASE);
    }
  }

  NativeLiegeImage17(const NativeLiegeImage17&) = delete;
  NativeLiegeImage17& operator=(const NativeLiegeImage17&) = delete;
  NativeLiegeImage17(NativeLiegeImage17&&) = delete;
  NativeLiegeImage17& operator=(NativeLiegeImage17&&) = delete;

  void SetStorage(void* value) {
    Store<void*>(image_, 0x5C67568U, value);
  }

  void SetFallback(void* value) {
    Store<void*>(image_, 0x5C67570U, value);
  }

  using Getter = void* (__fastcall*)(void*);

  Getter function() const noexcept {
    return reinterpret_cast<Getter>(image_ + 0x28BFC50U);
  }

  void* call(void* receiver) const {
    return reinterpret_cast<Getter>(image_ + 0x28BFC50U)(receiver);
  }

  void RequireOriginalCodeUnchanged() const {
    std::array<std::uint8_t, 118> current{};
    std::memcpy(current.data(), image_ + 0x28BFC50U, 118);
    Require(std::memcmp(current.data(), original_code_.data(), 118) == 0,
            "original code changed");
  }

 private:
  void Commit(std::uint32_t rva, std::size_t size) {
    Require(VirtualAlloc(image_ + rva, size, MEM_COMMIT,
        PAGE_READWRITE) == image_ + rva, "commit selected relative page");
  }

  std::uint8_t* image_ = nullptr;
  std::array<std::uint8_t, 118> original_code_{};
};

}
