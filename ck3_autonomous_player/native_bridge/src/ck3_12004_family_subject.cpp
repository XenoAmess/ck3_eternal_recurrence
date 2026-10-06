#include "xar_bridge/ck3_12004_family_subject.hpp"

#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
#include "xar_bridge/ck3_12004_family_relationships.hpp"

#include <cstring>

namespace xar::ck3_12004 {
namespace {
template <typename T> T Load(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset,
              sizeof(value));
  return value;
}

// Actual inline is_child_of operands: 2B6EED4 parent full ID+18,
// 2B6EEDC child Family+1A8, 2B6EEE8/2B6EEED parent slots+4/+0.
// This software mirror is not a native trigger-wrapper callback.
bool NativeChildOf(void *child, void *parent) noexcept {
  if (child == nullptr || parent == nullptr) return false;
  const auto *family = Load<const std::byte *>(
      child, family_relationships_abi::kCharacterFamilyOffset);
  if (family == nullptr) return false;
  const auto id = Load<std::int32_t>(parent, kCharacterFullIdOffset);
  return Load<std::int32_t>(family, 0x0) == id ||
      Load<std::int32_t>(family, 0x4) == id;
}
} // namespace

ck3_12002::FamilySubjectBindings BindFamilySubjectImage(
    std::uintptr_t base, std::string_view sha) noexcept {
  ck3_12002::FamilySubjectBindings bindings{};
  bindings.family = xar::ck3_12004::BindFamilyImage(base, sha);
  if (!bindings.family.enabled) return bindings;
  bindings.enabled = true;
  bindings.is_character_child_of = &NativeChildOf;
  const auto &values = bindings.family.values;
  bindings.house_storage_slot = values.house_store;
  bindings.house_fallback_slot = values.house_fallback;
  bindings.dynasty_storage_slot = values.dynasty_store;
  bindings.dynasty_fallback_slot = values.dynasty_fallback;
  return bindings;
}

} // namespace xar::ck3_12004
#endif
