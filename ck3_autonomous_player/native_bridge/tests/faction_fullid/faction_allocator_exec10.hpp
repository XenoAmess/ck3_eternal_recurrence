#pragma once
#include <windows.h>
#include <array>
#include <algorithm>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iterator>
#include <stdexcept>
#include <string>
#include <vector>

// Offline owned memory. Original instructions retain their original relative RVAs.
// No DLL, CK3 process, injection, copied PE or replacement engine callbacks.
namespace m1_allocator_exec10 {
template <class T> T Load(const void* base, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::uint8_t*>(base) + offset, sizeof(value));
  return value;
}
template <class T> void Store(void* base, std::size_t offset, T value) {
  std::memcpy(static_cast<std::uint8_t*>(base) + offset, &value, sizeof(value));
}
inline void Require(bool value, const char* message) {
  if (!value) throw std::runtime_error(message);
}

class FactionAllocatorImage final {
 public:
  explicit FactionAllocatorImage(const std::string& source_root)
      : slots_(1024U * 16U), page_(0x34000U) {
    image_ = static_cast<std::uint8_t*>(VirtualAlloc(nullptr, 0x6200000U,
        MEM_RESERVE, PAGE_NOACCESS));
    Require(image_ != nullptr, "reserve relative image");
    Commit(0x2A6F000U, 0x2000U);
    const std::array<Fragment, 6> fragments{{
        {0x2A70300U, 148U, "/inlined-creation05/creator-entry-2a70300/capture01/code.bin"},
        {0x2A70394U, 403U, "/inlined-creation05/creator-2a70394/capture01/code.bin"},
        {0x2A70527U, 33U, "/inlined-creation05/creator-exit-2a70527/capture01/code.bin"},
        {0x2A6FEB0U, 102U, "/tail-2a6feb0/capture01/code.bin"},
        {0x2A6FF16U, 164U, "/tail-2a6ff16/capture01/code.bin"},
        {0x2A6FFBAU, 15U, "/tail-2a6ffba/capture01/code.bin"}}};
    for (const auto& fragment : fragments) {
      std::ifstream input(source_root + fragment.path, std::ios::binary);
      Require(static_cast<bool>(input), "read original held fragment");
      const std::vector<char> data((std::istreambuf_iterator<char>(input)), {});
      Require(data.size() == fragment.size, "original fragment exact size");
      std::memcpy(image_ + fragment.rva, data.data(), data.size());
      originals_.push_back({fragment.rva, std::vector<std::uint8_t>(data.begin(), data.end())});
    }
    // The one conditional registration branch is disabled by its ordinary input.
    const auto displacement = Load<std::int32_t>(image_, 0x2A70433U);
    registration_flag_rva_ = static_cast<std::uint32_t>(
        static_cast<std::int64_t>(0x2A70438U) + displacement);
    Commit(registration_flag_rva_ & ~0xFFFU, 0x1000U);
    Commit(0x5C82000U, 0x1000U);
    Commit(0x5D1D000U, 0x1000U);
    Store<std::uint8_t>(image_, registration_flag_rva_, 0U);
    Store<std::uint64_t>(image_, 0x5C82F68U, 53186400ULL);
    Store<void*>(image_, 0x5D1DE10U, fallback_.data());
    DWORD old_protection = 0;
    Require(VirtualProtect(image_ + 0x2A6F000U, 0x2000U,
        PAGE_EXECUTE_READ, &old_protection) != FALSE, "protect original code");
    Require(FlushInstructionCache(GetCurrentProcess(), image_ + 0x2A6F000U,
        0x2000U) != FALSE, "flush original code");
    Reset(0xFFFFFFFFU);
  }
  ~FactionAllocatorImage() {
    if (image_) VirtualFree(image_, 0, MEM_RELEASE);
  }
  FactionAllocatorImage(const FactionAllocatorImage&) = delete;
  FactionAllocatorImage& operator=(const FactionAllocatorImage&) = delete;

  void Reset(std::uint32_t old_id) {
    storage_.fill(0);
    std::fill(slots_.begin(), slots_.end(), std::uint8_t{0});
    std::fill(page_.begin(), page_.end(), std::uint8_t{0});
    pages_[0] = page_.data();
    Store<void*>(storage_.data(), 8U, pages_.data());
    Store<std::uint32_t>(storage_.data(), 0x10U, 1U);
    Store<std::uint32_t>(storage_.data(), 0x14U, 1U);
    Store<void*>(storage_.data(), 0x20U, slots_.data());
    Store<std::uint32_t>(storage_.data(), 0x28U, 1024U);
    Store<std::uint32_t>(storage_.data(), 0x2CU, 1024U);
    Store<std::uint32_t>(storage_.data(), 0x38U, 0xFFFFFFFFU);
    Store<std::uint32_t>(storage_.data(), 0x40U, 0U);
    Store<std::uint32_t>(storage_.data(), 0x44U, 1023U);
    for (std::uint32_t i = 0; i < 1024U; ++i) {
      Store<std::uint32_t>(slots_.data(), i * 16U,
          i == 1023U ? 0xFFFFFFU : i + 1U);
      Store<std::uint32_t>(slots_.data(), i * 16U + 4U,
          i == 0U ? 0xFFFFFFU : i - 1U);
      Store<std::uint32_t>(page_.data(), i * 0xD0U + 0x10U, 0xFFFFFFFFU);
    }
    Store<std::uint32_t>(page_.data(), 0x10U, old_id);
  }

  void* Allocate(void* type, std::int32_t target, std::int32_t update_day) {
    using NativeAllocator = void* (__fastcall*)(void*, void* const*,
        const std::int32_t*, const std::int32_t*);
    return reinterpret_cast<NativeAllocator>(image_ + 0x2A70300U)(
        storage_.data(), &type, &target, &update_day);
  }
  void* Storage() noexcept { return storage_.data(); }
  void* FirstObject() noexcept { return page_.data(); }
  void* Fallback() noexcept { return fallback_.data(); }
  std::uintptr_t PrimaryVtable() const noexcept {
    return reinterpret_cast<std::uintptr_t>(image_ + 0x4743530U);
  }
  std::uint32_t RegistrationFlagRva() const noexcept { return registration_flag_rva_; }
  void RequireOriginalCodeUnchanged() const {
    for (const auto& original : originals_)
      Require(std::memcmp(image_ + original.rva, original.bytes.data(),
          original.bytes.size()) == 0, "original code changed");
  }

 private:
  struct Fragment { std::uint32_t rva; std::size_t size; const char* path; };
  struct Original { std::uint32_t rva; std::vector<std::uint8_t> bytes; };
  void Commit(std::uint32_t rva, std::size_t size) {
    Require(VirtualAlloc(image_ + rva, size, MEM_COMMIT,
        PAGE_READWRITE) == image_ + rva, "commit selected relative page");
  }
  std::uint8_t* image_ = nullptr;
  std::uint32_t registration_flag_rva_ = 0;
  std::vector<Original> originals_;
  std::array<std::uint8_t, 0x58U> storage_{};
  std::array<std::uint8_t, 0xD0U> fallback_{};
  std::vector<std::uint8_t> slots_;
  std::vector<std::uint8_t> page_;
  std::array<void*, 1U> pages_{};
};
}
