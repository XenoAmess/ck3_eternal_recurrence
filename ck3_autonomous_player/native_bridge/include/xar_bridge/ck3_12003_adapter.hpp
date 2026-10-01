#pragma once

#include "xar_bridge/ck3_12003.hpp"
#include "xar_bridge/ck3_12002_adapter.hpp"
#include <string>

namespace xar::game {
using Ck3_12003AdapterBindings = Ck3_12002AdapterBindings;
Ck3_12003AdapterBindings BindCk3_12003AdapterImage(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;
std::unique_ptr<GameAdapter> CreateCk3_12003AdapterFromBindings(
    Ck3_12003AdapterBindings bindings) noexcept;
const AdapterDescriptor &Ck3_12003AdapterDescriptor() noexcept;
std::unique_ptr<GameAdapter> CreateCk3_12003Adapter(
    std::string_view executable_sha256) noexcept;

// Internal ABI selection only. Published descriptors and result provenance
// always retain the actual executable identity. All .2 binders stay strict.
bool IsReviewedCrozierAdapter(const GameAdapter &adapter) noexcept;
bool IsCk3_12003Descriptor(const AdapterDescriptor &descriptor) noexcept;
std::string_view ReviewedCrozierAbiSha256(const AdapterDescriptor &descriptor) noexcept;
std::string_view ReviewedCrozierAbiVersion(const AdapterDescriptor &descriptor) noexcept;
std::string RenderCrozierBuildIdentity(
    std::string serialized, const AdapterDescriptor &descriptor);
} // namespace xar::game
