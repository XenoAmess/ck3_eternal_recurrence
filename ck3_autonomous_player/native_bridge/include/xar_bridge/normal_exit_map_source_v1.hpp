#pragma once
#include "xar_bridge/normal_exit_map_v1.hpp"

#include <filesystem>
#include <span>
#include <string>
#include <string_view>

namespace xar::ck3_12003 {
// Pure parser for the actual process argv; no filesystem, game or Win32 calls.
// Closed flags: unique -userdir=absolute-path, optional unique -debug_mode,
// -gdpr-compliant and -loadsave=bare-save-key (ASCII [A-Za-z0-9_-], 1..128).
// Rejection leaves output unchanged. This is not a protocol/caller input.
struct NormalExitMapLaunchArgumentsV1 {
  std::filesystem::path userdir;
  std::wstring load_save_key;
};
bool ParseNormalExitMapLaunchArgumentsV1(std::span<const std::wstring_view> arguments,
    NormalExitMapLaunchArgumentsV1 &output) noexcept;
bool NormalExitMapSha256V1(std::string_view bytes, std::string &digest) noexcept;
// Pure exact descriptor/inventory digest join; no process or file operations.
bool NormalExitMapSourceExecutableAdmittedV1(
    const game::AdapterDescriptor &descriptor,
    std::string_view inventory_executable_sha256) noexcept;
// Reads only the fixed manifest below the actual launch -userdir. No protocol
// path, arbitrary function/address, or caller-supplied verified flag is accepted.
bool VerifyNormalExitMapSourcesV1(std::string_view inventory_sha256,
    const game::AdapterDescriptor &descriptor,
    bool &stock_verified, std::string &reason) noexcept;
} // namespace xar::ck3_12003
