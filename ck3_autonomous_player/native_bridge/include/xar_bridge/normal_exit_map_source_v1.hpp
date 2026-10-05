#pragma once
#include "xar_bridge/normal_exit_map_v1.hpp"

#include <string>
#include <string_view>

namespace xar::ck3_12003 {
bool NormalExitMapSha256V1(std::string_view bytes, std::string &digest) noexcept;
// Reads only the fixed manifest below the actual launch -userdir. No protocol
// path, arbitrary function/address, or caller-supplied verified flag is accepted.
bool VerifyNormalExitMapSourcesV1(std::string_view inventory_sha256,
    bool &stock_verified, std::string &reason) noexcept;
} // namespace xar::ck3_12003
