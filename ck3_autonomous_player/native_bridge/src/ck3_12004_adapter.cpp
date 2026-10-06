#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/ck3_12002_query_mailbox.hpp"

#include <windows.h>
#include <array>
#include <utility>

namespace xar::game {
namespace {
void ReplaceIdentityToken(std::string &serialized, std::string_view from,
                          std::string_view to) {
  std::size_t at = 0;
  while ((at = serialized.find(from, at)) != std::string::npos) {
    serialized.replace(at, from.size(), to);
    at += to.size();
  }
}
} // namespace

const AdapterDescriptor &Ck3_12004AdapterDescriptor() noexcept {
  // Only the independently migrated core-frame observation is published here.
  static constexpr std::array<std::string_view, 1> capabilities{
      "game.query.core-frame.v1"};
  static const AdapterDescriptor descriptor{
      ck3_12004::kAdapterId, ck3_12004::kGameVersion,
      ck3_12004::kExecutableSha256, ck3_12002::kCheckpointSaveName,
      capabilities};
  return descriptor;
}

Ck3_12004AdapterBindings BindCk3_12004AdapterImage(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  Ck3_12004AdapterBindings bindings{};
  bindings.core = ck3_12004::BindCoreImage(image_base, executable_sha256);
  bindings.read_core_snapshot = ck3_12004::ReadCoreSnapshot;
  // Advanced families keep their own migration packets; this never calls the
  // old whole-image binder or substitutes its hash for the new executable.
  return bindings;
}

std::unique_ptr<GameAdapter> CreateCk3_12004AdapterFromBindings(
    Ck3_12004AdapterBindings bindings) noexcept {
  bindings.read_core_snapshot = ck3_12004::ReadCoreSnapshot;
  return CreateCrozierAdapterFromBindings(
      std::move(bindings), Ck3_12004AdapterDescriptor());
}

std::unique_ptr<GameAdapter> CreateCk3_12004Adapter(
    std::string_view executable_sha256) noexcept {
  return CreateCk3_12004AdapterFromBindings(BindCk3_12004AdapterImage(
      reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)),
      executable_sha256));
}

std::string Render12004BuildIdentity(
    std::string serialized, const AdapterDescriptor &descriptor) {
  if (!IsCk3_12004Descriptor(descriptor)) return serialized;
  serialized = ck3_12002::RenderQueryBuildIdentity(std::move(serialized));
  for (const auto old_version : {"1.20.0.2", "1.20.0.3"}) {
    for (const auto key : {"game_version", "exact_ck3_build", "exact_build",
                           "version", "build_version", "build"}) {
      ReplaceIdentityToken(serialized,
          std::string("\"") + key + "\":\"" + old_version + "\"",
          std::string("\"") + key + "\":\"1.20.0.4\"");
    }
    for (const auto key : {"backend_id", "campaign_backend_id", "feature_backend_id"}) {
      ReplaceIdentityToken(serialized,
          std::string("\"") + key + "\":\"ck3-" + old_version + "-",
          std::string("\"") + key + "\":\"ck3-1.20.0.4-");
    }
    ReplaceIdentityToken(serialized,
        std::string("\"adapter_id\":\"ck3-") + old_version + "-msvc-x64\"",
        "\"adapter_id\":\"ck3-1.20.0.4-msvc-x64\"");
    ReplaceIdentityToken(serialized,
        std::string("\"played-character-event-icon-indicators-") + old_version + "-v1\"",
        "\"played-character-event-icon-indicators-1.20.0.4-v1\"");
  }
  ReplaceIdentityToken(serialized, "\"schema\":\"ck3_12002_", "\"schema\":\"ck3_12004_");
  ReplaceIdentityToken(serialized, "\"schema\":\"ck3_12003_", "\"schema\":\"ck3_12004_");
  for (const auto old_hash : {std::string_view(ck3_12002::kExecutableSha256),
                            std::string_view(ck3_12003::kExecutableSha256)}) {
    ReplaceIdentityToken(serialized, std::string("\"") + std::string(old_hash) + "\"",
        std::string("\"") + ck3_12004::kExecutableSha256 + "\"");
  }
  for (const auto old_hash : {
      "ae1ba6ff060ba603842f6f4a2ded0af4b7d3666b3dd271f75fb01b0da8e81b2d",
      "94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6"}) {
    ReplaceIdentityToken(serialized, std::string("\"") + old_hash + "\"",
        "\"98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518\"");
  }
  return serialized;
}
} // namespace xar::game
