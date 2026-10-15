#pragma once
#include "xar_bridge/normal_exit_map_source_v1.hpp"

namespace xar::ck3_12003 {
// Filesystem verifier shared by the production process wrapper and offline
// source fixtures. Production obtains both paths from its actual Win32 process;
// neither path is accepted by the bridge protocol or its normal-exit request.
bool VerifyNormalExitMapInventoryForContextV1(
    std::string_view inventory_sha256, const game::AdapterDescriptor &descriptor,
    const std::filesystem::path &actual_userdir,
    const std::filesystem::path &actual_executable,
    bool &stock_verified, std::string &reason) noexcept;
} // namespace xar::ck3_12003
