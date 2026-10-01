#include "xar_bridge/ck3_12003_adapter.hpp"

namespace xar::game {
bool IsCk3_12003Descriptor(const AdapterDescriptor &descriptor) noexcept {
  return descriptor.adapter_id == ck3_12003::kAdapterId &&
         descriptor.game_version == ck3_12003::kGameVersion &&
         descriptor.executable_sha256 == ck3_12003::kExecutableSha256;
}

bool IsReviewedCrozierAdapter(const GameAdapter &adapter) noexcept {
  const auto &descriptor = adapter.descriptor();
  return IsCk3_12003Descriptor(descriptor) ||
      (descriptor.adapter_id == "ck3-1.20.0.2-msvc-x64" &&
       descriptor.game_version == "1.20.0.2" &&
       descriptor.executable_sha256 == ck3_12002::kExecutableSha256);
}

std::string_view ReviewedCrozierAbiSha256(const AdapterDescriptor &descriptor) noexcept {
  return IsCk3_12003Descriptor(descriptor)
      ? std::string_view(ck3_12002::kExecutableSha256) : descriptor.executable_sha256;
}

std::string_view ReviewedCrozierAbiVersion(const AdapterDescriptor &descriptor) noexcept {
  return IsCk3_12003Descriptor(descriptor) ? std::string_view("1.20.0.2")
                                        : descriptor.game_version;
}
} // namespace xar::game
