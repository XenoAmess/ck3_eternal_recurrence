#pragma once

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12002_adapter.hpp"
#include <string>

namespace xar::game {
using Ck3_12004AdapterBindings = Ck3_12002AdapterBindings;
Ck3_12004AdapterBindings BindCk3_12004AdapterImage(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;
std::unique_ptr<GameAdapter> CreateCk3_12004AdapterFromBindings(
    Ck3_12004AdapterBindings bindings) noexcept;
bool ReadCk3_12004Snapshot(const Ck3_12004AdapterBindings &bindings,
                         Snapshot &output) noexcept;
const AdapterDescriptor &Ck3_12004AdapterDescriptor() noexcept;
std::unique_ptr<GameAdapter> CreateCk3_12004Adapter(
    std::string_view executable_sha256) noexcept;
bool IsCk3_12004Descriptor(const AdapterDescriptor &descriptor) noexcept;
const ck3_12002::DeclarationsBindings *BorrowOrdinaryHolyWarDeclarations12004(
    const GameAdapter &adapter) noexcept;
std::string Render12004BuildIdentity(
    std::string serialized, const AdapterDescriptor &descriptor);
} // namespace xar::game
