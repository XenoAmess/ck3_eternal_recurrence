#pragma once
#include "xar_bridge/ck3_121003_readonly26785313_v1.hpp"
#include "xar_bridge/ck3_1210_core_control_v1.hpp"

namespace xar::ck3_121003::build26785313 {
inline constexpr std::uintptr_t kApplicationQuitRequestRva267V1=0x3F5B170;
inline constexpr char kApplicationExitBackend267V1[]="ck3-1.21.0.3-native-headless-main-thread";
struct ApplicationExitContext267V1 {
  ReadonlyBindings bindings{};
  ck3_11906::MainThreadQueryMailboxV1 *mailbox=nullptr;
  ck3_11906::MainThreadQueryTicketV1 ticket{};
  ck3_1210::CoreControlRequestV1 request{};
  ck3_1210::ApplicationExitSessionV1 *session=nullptr;
  ck3_1210::CoreControlResultV1 result{};
  std::uint64_t connection_generation=0;
  std::uint64_t monotonic_deadline_ms=0;
};
std::span<const ImagePin> ApplicationExitImagePins267V1() noexcept;
bool VerifyApplicationExitImage267V1(std::uintptr_t image_base) noexcept;
ck3_1210::ApplicationExitBindingsV1 BindApplicationExitImage267V1(
    std::uintptr_t image_base,std::string_view executable_sha256) noexcept;
bool ExecuteApplicationExitOnOwner267V1(void*,const ck3_11906::MainThreadExecutionStampV1&) noexcept;
void ArmApplicationExitDeadline267V1(ApplicationExitContext267V1&) noexcept;
// Fixed secondary-owner role; never exposes arbitrary executors/callbacks.
bool ReadApplicationExitCoreOnOwner267V1(const ReadonlyBindings&,
    ck3_11906::MainThreadQueryMailboxV1*,const ck3_11906::MainThreadQueryTicketV1&,
    const ck3_11906::MainThreadExecutionStampV1&,void *actual_exit_context,ReadonlyObservation&) noexcept;
bool ApplicationExitRouteEnabled267V1(const game::AdapterDescriptor&) noexcept;
bool ParseApplicationExitRequest267V1(std::string_view,ck3_1210::CoreControlRequestV1&) noexcept;
std::string SerializeApplicationExitResult267V1(std::string_view,const ck3_1210::CoreControlResultV1&);
} // namespace xar::ck3_121003::build26785313
