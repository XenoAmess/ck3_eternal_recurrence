#pragma once

#include "xar_bridge/ck3_12002.hpp"
#include "xar_bridge/active_scheme_state_v1_private_observer.hpp"

namespace xar::ck3_12002 {

inline constexpr std::size_t kSwayManagerOffset12002 = 0xA5C0;
inline constexpr std::uintptr_t kSwayManagerVtableRva12002 = 0x4779538;
inline constexpr std::uintptr_t kSwayStorageVtableRva12002 = 0x4779828;
inline constexpr std::uintptr_t kSwayInstanceVtableRva12002 = 0x47794E8;
inline constexpr std::uintptr_t kSwayTypeVtableRva12002 = 0x48B9F20;
inline constexpr std::uintptr_t kSwayOpinionRva12002 = 0x28BC490;
using SwayReadOpinion12002 = std::int32_t (*)(void *owner, void *toward);

struct SwayStateBindings12002 {
  bool enabled = false;
  std::uintptr_t module_base = 0;
  CoreBindings core{};
  SwayReadOpinion12002 opinion = nullptr;
  // Caller-owned image profile. Legacy binders retain their reviewed defaults.
  std::size_t manager_offset = kSwayManagerOffset12002;
  std::uintptr_t manager_vtable_rva = kSwayManagerVtableRva12002;
  std::uintptr_t storage_vtable_rva = kSwayStorageVtableRva12002;
  std::uintptr_t instance_vtable_rva = kSwayInstanceVtableRva12002;
  std::uintptr_t type_vtable_rva = kSwayTypeVtableRva12002;
  std::string_view executable_sha256 = kExecutableSha256;
};

SwayStateBindings12002 BindSwayStateImage12002(std::uintptr_t module_base,
    std::string_view executable_sha256) noexcept;

// The caller confines this reader to one paused owning-thread pump. All owner
// instances are counted and identified; only Sway's fields are interpreted.
// Other types remain opaque rows, so an occupied personal slot is not hidden.
bool ReadActiveSwayState12002(const SwayStateBindings12002 &bindings,
    std::uint64_t capture_epoch,
    bridge::ActiveSchemeStateV1PrivateObservation &output) noexcept;
bool ReadSwayTargetOpinion12002(const SwayStateBindings12002 &bindings,
    std::int64_t actor, std::uint32_t target, std::int32_t &output) noexcept;

} // namespace xar::ck3_12002
