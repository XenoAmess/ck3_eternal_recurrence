#pragma once

#include "xar_bridge/ck3_12002.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

#include <span>

namespace xar::ck3_12002 {

inline constexpr std::string_view kThreadRuntimeAdapterId =
    "ck3-1.20.0.2-msvc-x64";
inline constexpr std::uintptr_t kSdlWindowsVideoDevicePumpInstallRva = 0x40F39BB;
inline constexpr std::uintptr_t kSdlPumpEventsRva = 0x40C8810;
inline constexpr std::uintptr_t kSdlWindowsPumpFunctionRva = 0x40D93F0;
inline constexpr std::uintptr_t kSdlWindowsPumpFirstPeekCallRva = 0x40D942C;
inline constexpr std::uintptr_t kSdlWindowsPumpFirstPeekReturnRva = 0x40D9432;
inline constexpr std::uintptr_t kPeekMessageWIatSlotRva = 0x43DAE38;
inline constexpr std::uintptr_t kGlobalRngWrapperSlotRva = 0x54DEFC0;
inline constexpr std::uintptr_t kGetCurrentThreadIdThunkRva = 0x40F5210;
inline constexpr std::uintptr_t kGetCurrentThreadIdIatSlotRva = 0x43DA598;
inline constexpr std::uintptr_t kMainThreadTlsInitializedFlagRva = 0x5CBE6BF;
inline constexpr std::uintptr_t kMainThreadTlsContextGetterRva = 0x3F784C0;
inline constexpr std::uintptr_t kMainThreadTlsStartupStoreRva = 0x8545F8;
inline constexpr std::uintptr_t kHandlePdxEventsRva = 0x3E14690;
inline constexpr std::uintptr_t kHandlePdxEventsTlsGateRva = 0x3E146AD;

// This checks a caller-owned mapped image, never discovers or attaches to CK3.
bool VerifyThreadRuntimeImage(std::uintptr_t image_base) noexcept;

const ck3_11906::MainThreadQueryBuildProfileV1 &ThreadRuntimeBuildProfile()
    noexcept;

// Pure address/profile binding. Installation remains an explicit operation
// owned by the bridge worker. Callback ordering matches the existing thirteen
// fixed mailbox executor slots, followed by the semantic adapter executor;
// an empty list installs observation only.
ck3_11906::MainThreadQueryInstallEnvironmentV1 BindThreadRuntimeImage(
    std::uintptr_t image_base, std::string_view executable_sha256,
    std::span<const ck3_11906::MainThreadQueryExecutorV1> executors = {}) noexcept;

} // namespace xar::ck3_12002
