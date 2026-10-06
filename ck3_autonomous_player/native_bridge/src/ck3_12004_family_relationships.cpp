#include "xar_bridge/ck3_12004_family_relationships.hpp"

#include <cstring>

namespace xar::ck3_12004 {
namespace {
template <typename T> T Load(const void *base, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(base) + offset, sizeof(T));
  return value;
}
} // namespace

bool ReadPlayedCharacterRelationships(
    const CoreBindings &core, std::int32_t character_id,
    game::PlayedCharacterRelationships12002 &output) noexcept {
  output = {};
  void *character = ck3_12004::ResolveCoreCharacter(core, character_id);
  if (character == nullptr) return false;
  using namespace family_relationships_abi;
  void *family = Load<void *>(character, kCharacterFamilyOffset);
  if (family == nullptr) return true;
  const auto betrothed = Load<std::int32_t>(family, kBetrothedIdOffset);
  const auto primary = Load<std::int32_t>(family, kPrimarySpouseIdOffset);
  if (ck3_12004::ResolveCoreCharacter(core, betrothed) != nullptr)
    output.betrothed_character_id = betrothed;
  if (ck3_12004::ResolveCoreCharacter(core, primary) != nullptr)
    output.primary_spouse_character_id = primary;
  const auto *ids = Load<const std::int32_t *>(family, kSpouseIdsOffset);
  const auto capacity = Load<std::int32_t>(family, kSpouseCapacityOffset);
  const auto count = Load<std::int32_t>(family, kSpouseCountOffset);
  if (count < 0 || capacity < count || count > 1'000'000 ||
      (count > 0 && ids == nullptr)) {
    output = {};
    return false;
  }
  for (std::int32_t index = 0; index < count; ++index)
    if (ck3_12004::ResolveCoreCharacter(core, ids[index]) != nullptr)
      output.spouse_character_ids.push_back(ids[index]);
  return true;
}

} // namespace xar::ck3_12004
