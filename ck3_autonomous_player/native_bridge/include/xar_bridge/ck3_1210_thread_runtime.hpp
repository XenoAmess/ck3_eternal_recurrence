#pragma once
#include "xar_bridge/ck3_1210.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

namespace xar::ck3_1210 {
inline constexpr std::uintptr_t kSdlWindowsPumpFunctionRva = 0x47045A0;
inline constexpr std::uintptr_t kSdlWindowsPumpDeviceInstallRva = 0x4706CD8;
inline constexpr std::uintptr_t kSdlWindowsPumpFirstPeekCallRva = 0x47045DA;
inline constexpr std::uintptr_t kSdlWindowsPumpFirstPeekReturnRva = 0x47045E0;
inline constexpr std::uintptr_t kPeekMessageWIatSlotRva = 0x49D8DE8;
inline constexpr std::uintptr_t kGetCurrentThreadIdThunkRva = 0x480E7CC;
inline constexpr std::uintptr_t kGetCurrentThreadIdIatSlotRva = 0x49D85B8;
inline constexpr std::uintptr_t kGlobalRngWrapperSlotRva = 0x5D559B8;
inline constexpr std::uintptr_t kMainThreadTlsInitializedFlagRva = 0x695910C;
inline constexpr std::uintptr_t kMainThreadTlsContextGetterRva = 0x44FEA30;
inline constexpr std::uintptr_t kMainThreadTlsStartupStoreRva = 0x893B58;
inline constexpr std::uintptr_t kHandlePdxEventsRva = 0x438CF70;
inline constexpr std::uintptr_t kHandlePdxEventsTlsGateRva = 0x438CF8D;

bool VerifyThreadRuntimeImage(std::uintptr_t image_base) noexcept;
const ck3_11906::MainThreadQueryBuildProfileV1 &ThreadRuntimeBuildProfile() noexcept;
ck3_11906::MainThreadQueryInstallEnvironmentV1 BindThreadRuntimeImage(
    std::uintptr_t image_base, std::string_view executable_sha256,
    std::span<const ck3_11906::MainThreadQueryExecutorV1> executors = {}) noexcept;
} // namespace xar::ck3_1210
