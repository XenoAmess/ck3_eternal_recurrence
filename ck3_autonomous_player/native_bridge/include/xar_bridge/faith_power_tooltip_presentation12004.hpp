#pragma once
#include <cstdint>
#include <string_view>
namespace xar::ck3_11906 {
struct MainThreadQueryMailboxV1;
bool InstallFaithPowerTooltipPresentation12004(std::uintptr_t,std::string_view,bool) noexcept;
bool BindFaithPowerTooltipPresentationOwner12004(MainThreadQueryMailboxV1*,std::uint64_t) noexcept;
void PublishFaithPowerTooltipPresentationConnection12004(std::uint64_t) noexcept;
void CancelFaithPowerTooltipPresentation12004() noexcept;
}
