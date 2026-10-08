#include "xar_bridge/ck3_12003_title_holder.hpp"
#include "xar_bridge/ck3_12003.hpp"
#include "xar_bridge/ck3_12002_campaign.hpp"

#include <cstring>
#include <utility>

namespace xar::ck3_12003 {
namespace {

template <class T> T Load(const void *object, std::size_t offset) noexcept {
  T value{};
  if (object != nullptr)
    std::memcpy(&value, static_cast<const std::byte *>(object) + offset,
                sizeof value);
  return value;
}

void *ResolveCharacter(const TitleHolderBindingsV1 &b,
                       std::int32_t id) noexcept {
  if (id == -1 || b.character_storage_slot == nullptr ||
      *b.character_storage_slot == nullptr) return nullptr;
  void *storage = *b.character_storage_slot;
  void *objects = Load<void *>(storage, 0x20);
  const auto capacity = Load<std::int32_t>(storage, 0x2C);
  const auto index = static_cast<std::uint32_t>(id) & 0xFFFFFFU;
  if (objects == nullptr || capacity <= 0 || capacity > 1'000'000 ||
      index >= static_cast<std::uint32_t>(capacity)) return nullptr;
  void *character = Load<void *>(objects, static_cast<std::size_t>(index) * 0x10 + 8);
  void *fallback = b.character_fallback_slot != nullptr
      ? *b.character_fallback_slot : nullptr;
  return character != nullptr && character != fallback &&
      Load<std::int32_t>(character, 0x18) == id &&
      Load<std::uint32_t>(character, 0x1C) == 0x43686172U ? character : nullptr;
}

std::string_view TierKey(std::int32_t raw) noexcept {
  // Existing campaign/title-map tier semantics, including Crozier hegemony.
  switch (raw) {
  case 1: return "barony";
  case 2: return "county";
  case 3: return "duchy";
  case 4: return "kingdom";
  case 5: return "empire";
  case 6: return "hegemony";
  default: return {};
  }
}

bool ReadHolderLieges(const TitleHolderBindingsV1 &b, void *holder,
                      void *actor, game::TitleHolderV1 &value) noexcept {
  void *fallback = *b.character_fallback_slot;
  void *immediate = b.immediate_liege(holder);
  void *top = b.top_liege(holder);
  if (top == nullptr || top == fallback ||
      ResolveCharacter(b, Load<std::int32_t>(top, 0x18)) != top) return false;
  value.holder_top_liege_character_id = Load<std::int32_t>(top, 0x18);
  if (immediate != nullptr && immediate != fallback && immediate != holder) {
    const auto immediate_id = Load<std::int32_t>(immediate, 0x18);
    if (ResolveCharacter(b, immediate_id) != immediate) return false;
    value.holder_immediate_liege_character_id = immediate_id;
  }

  // Reuse the native campaign subrealm traversal semantics. Equal top lieges
  // do not place a sibling vassal inside a vassal player's own subrealm.
  void *current = holder;
  for (std::int32_t depth = 0; depth < 1'024; ++depth) {
    if (ResolveCharacter(b, Load<std::int32_t>(current, 0x18)) != current)
      return false;
    if (current == actor) value.holder_in_player_realm = true;
    void *liege = depth == 0 ? immediate : b.immediate_liege(current);
    if (liege == nullptr || liege == fallback || liege == current)
      return current == top;
    const auto liege_id = Load<std::int32_t>(liege, 0x18);
    if (ResolveCharacter(b, liege_id) != liege) return false;
    current = liege;
  }
  return false;
}

} // namespace

TitleHolderBindingsV1 BindTitleHolderImageV1(
    std::uintptr_t image_base, std::string_view sha) noexcept {
  TitleHolderBindingsV1 b{};
  if (image_base == 0 || sha != kExecutableSha256) return b;
  b.enabled = true;
  b.provinces = ck3_12002::BindProvinceImage(
      image_base, ck3_12002::kExecutableSha256);
  b.character_storage_slot = reinterpret_cast<void **>(
      image_base + ck3_12002::kCampaignRootCharacterStorageSlotRva);
  b.character_fallback_slot = reinterpret_cast<void **>(
      image_base + ck3_12002::kCampaignRootCharacterFallbackSlotRva);
  b.immediate_liege = reinterpret_cast<decltype(b.immediate_liege)>(
      image_base + ck3_12002::kCampaignRootImmediateLiegeRva);
  b.top_liege = reinterpret_cast<decltype(b.top_liege)>(
      image_base + ck3_12002::kCampaignRootTopLiegeRva);
  return b;
}

game::ReadTitleHolderV1Result ReadTitleHolderV1(
    const TitleHolderBindingsV1 &b, const game::Snapshot &scope,
    std::int32_t title_id, game::TitleHolderV1 &out) noexcept {
  using Result = game::ReadTitleHolderV1Result;
  out = {};
  out.date_raw = scope.date_raw;
  out.actor_character_id = scope.played_character_id;
  out.title_id = title_id;
  auto fail = [&out](std::string_view reason) {
    out.unavailable_reason = reason;
    return Result::unavailable;
  };
  if (!b.enabled || !b.provinces.enabled ||
      b.provinces.landed_title_storage_slot == nullptr ||
      b.character_storage_slot == nullptr || b.character_fallback_slot == nullptr ||
      b.immediate_liege == nullptr || b.top_liege == nullptr)
    return fail("title_holder_bindings_unavailable");
  void *actor = ResolveCharacter(b, scope.played_character_id);
  if (!scope.paused || !scope.map_ready || !scope.has_played_character ||
      !scope.played_character_alive || actor == nullptr)
    return fail("paused_player_scope_unavailable");
  if (title_id < 0) return fail("title_id_unavailable");
  void *title = ck3_12002::ResolveObjectiveTitle(b.provinces, title_id);
  if (title == nullptr) return fail("title_generation_unavailable");
  void *definition = Load<void *>(title, 0x48);
  if (definition == nullptr) return fail("title_template_unavailable");
  const auto tier = Load<std::int32_t>(definition, 0x64);
  const auto key = TierKey(tier);
  if (key.empty()) return fail("title_tier_unavailable");

  game::TitleHolderV1 value{};
  value.date_raw = out.date_raw;
  value.actor_character_id = out.actor_character_id;
  value.title_id = title_id;
  value.title_tier_raw = tier;
  value.title_tier_key = key;
  std::string stable_key;
  if (b.read_title_key == nullptr) {
    value.title_key_unavailable_reason = "title_key_reader_unavailable";
  } else if (!b.read_title_key(title, stable_key) || stable_key.empty()) {
    value.title_key_unavailable_reason = "title_key_read_or_format_unavailable";
  } else if (stable_key[0] != std::string_view(" bcdkeh")[static_cast<std::size_t>(tier)]) {
    value.title_key_unavailable_reason = "title_key_tier_prefix_unavailable";
  } else {
    value.title_key = std::move(stable_key);
    value.title_key_available = true;
    value.title_key_unavailable_reason = {};
  }
  const auto holder_id = Load<std::int32_t>(title, 0x128);
  void *holder = nullptr;
  if (holder_id != -1) {
    holder = ResolveCharacter(b, holder_id);
    if (holder == nullptr) return fail("holder_generation_unavailable");
    value.holder_character_id = holder_id;
    value.holder_is_player = holder == actor;
    if (!ReadHolderLieges(b, holder, actor, value))
      return fail("holder_liege_relationship_unavailable");
  }
  if (value.title_key_available) {
    std::string current_key;
    if (!b.read_title_key(title, current_key) || current_key != value.title_key) {
      value.title_key.clear();
      value.title_key_available = false;
      value.title_key_unavailable_reason = "title_key_source_changed";
    }
  }
  if (ck3_12002::ResolveObjectiveTitle(b.provinces, title_id) != title ||
      Load<void *>(title, 0x48) != definition ||
      Load<std::int32_t>(definition, 0x64) != tier ||
      Load<std::int32_t>(title, 0x128) != holder_id ||
      (holder != nullptr && ResolveCharacter(b, holder_id) != holder) ||
      ResolveCharacter(b, scope.played_character_id) != actor)
    return fail("title_holder_identity_changed");
  value.available = true;
  value.unavailable_reason = {};
  out = std::move(value);
  return Result::available;
}

} // namespace xar::ck3_12003
