#include "xar_bridge/lifestyle_owned_perk_collection_2919340_12004.hpp"

#include <limits>

namespace xar::ck3_12004::lifestyle {
namespace {
static_assert(sizeof(std::uintptr_t) == 8, "Actual12004 return identities require x64");
bool Add(std::uintptr_t base, std::uintptr_t offset, std::uintptr_t &address) noexcept {
  if (!base || offset > std::numeric_limits<std::uintptr_t>::max() - base) return false;
  address = base + offset;
  return true;
}
template <typename T>
bool Read(const LifestylePerkReadonlyAccess12004 &access, std::uintptr_t base,
          std::uintptr_t offset, T &value) {
  std::uintptr_t address = 0;
  return access.read_memory && Add(base, offset, address) &&
      access.read_memory(access.read_context, address, &value, sizeof(value));
}
} // namespace

LifestyleOwnedPerkCollectionGetter12004 ReadLifestyleOwnedPerkCollection291934012004(
    const LifestylePerkReadonlyAccess12004 &access, std::uintptr_t character) noexcept {
  LifestyleOwnedPerkCollectionGetter12004 out{};
  out.character_identity = character;
  const auto fail = [&](const char *reason) { out.unavailable_reason = reason; };
  if (!access.module_base || !access.read_memory) {
    fail("owned_perk_getter_read_binding_unavailable");
    return out;
  }
  try {
    std::uintptr_t extension = 0;
    if (!Read(access, character, 0x1B0, extension)) {
      fail("owned_perk_character_extension_unavailable");
      return out;
    }
    out.extension_identity_raw = extension;
    if (extension) {
      // Native ADD returns address-width bits; this does not dereference them.
      out.returned_collection_identity = extension + std::uintptr_t{0x220};
      out.branch = LifestyleOwnedPerkGetterBranch12004::character_extension;
      return out;
    }
    out.current_thread_tls_array_identity_raw = access.current_thread_tls_array_identity;
    if (!access.current_thread_tls_array_identity) {
      fail("owned_perk_same_thread_tls_array_unavailable");
      return out;
    }
    std::uintptr_t tls_zero = 0;
    if (!Read(access, *access.current_thread_tls_array_identity, 0, tls_zero)) {
      fail("owned_perk_tls_slot_zero_unavailable");
      return out;
    }
    out.tls_slot_zero_identity_raw = tls_zero;
    std::int32_t epoch = 0;
    if (!Read(access, tls_zero, 0x10, epoch)) {
      fail("owned_perk_tls_epoch_unavailable");
      return out;
    }
    out.tls_epoch_raw_i32 = epoch;
    std::int32_t guard = 0;
    if (!Read(access, access.module_base, kLifestyleOwnedPerkStaticGuardRva12004, guard)) {
      fail("owned_perk_static_guard_unavailable");
      return out;
    }
    out.static_guard_raw_i32 = guard;
    if (guard > epoch) {
      out.branch = LifestyleOwnedPerkGetterBranch12004::static_epoch_slow_path;
      fail("owned_perk_static_epoch_slow_path_unmodeled");
      return out;
    }
    out.returned_collection_identity = access.module_base + kLifestyleOwnedPerkStaticCollectionRva12004;
    out.branch = LifestyleOwnedPerkGetterBranch12004::static_fast_return;
    return out;
  } catch (...) {
    fail("owned_perk_getter_copy_exception");
    return out;
  }
}
} // namespace xar::ck3_12004::lifestyle
