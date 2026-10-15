#pragma once
#include "xar_bridge/ck3_12004_residual_parent_context.hpp"
#include <array>
#include <atomic>
#include <cstdint>
#include <string_view>
#include <windows.h>

namespace xar::ck3_12004 {
inline constexpr std::uintptr_t kActualResidualEntry12004=0x2A957E0;
inline constexpr std::uintptr_t kActualResidualNonzeroContinuation12004=0x2A957E8;
inline constexpr std::array<std::uint8_t,18> kActualResidualContinuationPrefix12004{
  0x48,0x89,0x4C,0x24,0x08,0x53,0x56,0x41,0x55,0x48,0x83,0xEC,0x30,0x48,0x89,0x6C,0x24,0x58};
using ActualResidualNonzeroOriginal12004=std::uintptr_t(__fastcall*)(void*,std::int32_t,std::uint8_t);

// SOURCE-only candidate: same typed seam serves future runtime and local fixture.
// The native TEST/JE already executed before this nonzero-continuation hook.
inline std::uintptr_t InvokeActualResidualNonzeroParent12004(
    const ResidualParentReader12004 &reader,ActualResidualNonzeroOriginal12004 original,
    void *array,std::int32_t budget,std::uint8_t flags,
    std::optional<std::uint64_t> actual_caller_return_rva,std::uint32_t thread,
    const void *natural_return_slot=nullptr) noexcept {
  if(!original)return 0;
  ResidualParentScope12004 scope(reader,array,budget,flags,actual_caller_return_rva,thread,natural_return_slot);
  return original(array,budget,flags); // exactly one native continuation
}
// Install only from the existing exact4 suspended-primary PrepareStartup path.
// The option adds no public query and uses the existing writer ring exclusively.
bool InstallActualResidualParentHook12004(std::uintptr_t image_base,
    std::string_view executable_sha256,bool primary_thread_suspended) noexcept;
extern "C" std::uintptr_t __fastcall XarActualResidualNonzeroHook12004(
    void *array,std::int32_t budget,std::uint8_t flags) noexcept;
}
