#pragma once
#include "xar_bridge/ck3_12002_console_fixture.hpp"
#include "xar_bridge/ck3_121003_readonly26785313_v1.hpp"
#include <string_view>
namespace xar::ck3_121003::build26785313 {
// Private fixed acceptance inbox only. Reuses the original runner/structs;
// no current public console capability, owner, file authorization or once claim.
ck3_12002::ConsoleFixtureBindings BindAubPrivateInboxFixture267V1(std::uintptr_t,std::string_view) noexcept;
bool VerifyAubPrivateInboxImage267V1(std::uintptr_t) noexcept;
bool ReadBoundAubPrivateInboxConsole267V1(const ReadonlyBindings&,
 const ck3_12002::ConsoleFixtureBindings&,std::uintptr_t& console) noexcept;
} // namespace xar::ck3_121003::build26785313
