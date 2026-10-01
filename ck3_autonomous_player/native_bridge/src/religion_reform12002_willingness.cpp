#include "xar_bridge/religion_reform12002_willingness.hpp"

#include <cstring>

namespace xar::ck3_12002::religion_reform {
namespace {
template <typename T> T Load(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset,
              sizeof(value));
  return value;
}
}

MainRiteBindings BindFaithMainRiteUnreformedImage12002(
    std::uintptr_t base, std::string_view sha) noexcept {
  MainRiteBindings b{};
  if (!base || sha != kExecutableSha256) return b;
  b.enabled = true;
  b.main_rite = reinterpret_cast<MainRiteGetter>(base + kFaithMainRiteGetterRva);
  b.is_unreformed = reinterpret_cast<IsUnreformedGetter>(
      base + kFaithIsUnreformedGetterRva);
  return b;
}

MainRiteUnreformed ReadFaithMainRiteUnreformed12002(
    const MainRiteBindings &b, void *faith,
    std::uint32_t expected_faith_id) noexcept {
  MainRiteUnreformed out{};
  if (!b.enabled || !b.main_rite || !b.is_unreformed) return out;
  out.status = MainRiteStatus::faith_unavailable;
  if (!faith || expected_faith_id == kAbsentFullReference ||
      Load<std::uint32_t>(faith, kObjectFullReferenceOffset) != expected_faith_id)
    return out;
  out.faith_id = expected_faith_id;
  const auto main_id = Load<std::uint32_t>(faith, kFaithMainRiteIdOffset);
  out.status = MainRiteStatus::main_rite_unavailable;
  if (main_id == kAbsentFullReference) return out;
  auto *main_rite = b.main_rite(faith);
  if (!main_rite ||
      Load<std::uint32_t>(main_rite, kObjectFullReferenceOffset) != main_id)
    return out;
  const bool value = b.is_unreformed(faith);
  out.status = MainRiteStatus::state_changed;
  if (Load<std::uint32_t>(faith, kObjectFullReferenceOffset) != expected_faith_id ||
      Load<std::uint32_t>(faith, kFaithMainRiteIdOffset) != main_id ||
      Load<std::uint32_t>(main_rite, kObjectFullReferenceOffset) != main_id ||
      b.main_rite(faith) != main_rite ||
      (Load<std::uint8_t>(main_rite, kRiteUnreformedOffset) != 0) != value)
    return out;
  out.main_rite_id = main_id;
  out.is_unreformed = value;
  out.status = MainRiteStatus::observed;
  return out;
}
} // namespace xar::ck3_12002::religion_reform
