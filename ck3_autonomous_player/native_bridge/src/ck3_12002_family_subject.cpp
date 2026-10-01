#include "xar_bridge/ck3_12002_family_subject.hpp"

#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
#include "xar_bridge/ck3_12002_family_subject_abi.hpp"
#include "xar_bridge/ck3_12002_family_query_abi.hpp"

#include <algorithm>
#include <cstring>
#include <utility>

namespace xar::ck3_12002 {
namespace {
using Failure = ck3_11906::PlayerChildMarriageSubjectFailureV1;

template <typename T> T Load(const void *base, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(base) + offset, sizeof(T));
  return value;
}
bool SameFrame(const CoreSnapshotPrefix &a, const CoreSnapshotPrefix &b) noexcept {
  return a.clock.date_raw == b.clock.date_raw && a.clock.paused == b.clock.paused &&
      a.clock.speed == b.clock.speed && a.local_player_id == b.local_player_id &&
      a.map_ready == b.map_ready && a.has_played_character == b.has_played_character &&
      a.played_character_id == b.played_character_id &&
      a.played_character_alive == b.played_character_alive;
}
bool Frame(const FamilySubjectBindings &b, CoreSnapshotPrefix &out) noexcept {
  return b.enabled && b.family.enabled && ReadCoreSnapshot(b.family.context.core, out) &&
      out.clock.paused && out.map_ready && out.has_played_character && out.played_character_alive;
}
bool NativeChildOf(void *child, void *parent) noexcept {
  if (child == nullptr || parent == nullptr) return false;
  const auto *family = Load<const std::byte *>(child, family_query_abi::kFamilyDataOffset);
  if (family == nullptr) return false;
  const auto id = Load<std::int32_t>(parent, 0x18);
  return Load<std::int32_t>(family, kFamilySubjectFirstParentIdOffset) == id ||
      Load<std::int32_t>(family, kFamilySubjectSecondParentIdOffset) == id;
}
void *ResolveComponent(void **storage_slot, void **fallback_slot, std::int32_t id) noexcept {
  if (id < 0 || storage_slot == nullptr || *storage_slot == nullptr || fallback_slot == nullptr)
    return nullptr;
  void *storage = *storage_slot;
  const auto capacity = Load<std::int32_t>(storage, 0x2C);
  const auto index = static_cast<std::uint32_t>(id) & 0xFFFFFF;
  void *slots = Load<void *>(storage, 0x20);
  if (slots == nullptr || capacity <= 0 || capacity > 1'000'000 ||
      index >= static_cast<std::uint32_t>(capacity)) return nullptr;
  void *object = Load<void *>(slots, index * 0x10U + 8);
  return object != nullptr && object != *fallback_slot &&
      Load<std::int32_t>(object, 0x10) == id ? object : nullptr;
}
bool Lineage(const FamilySubjectBindings &b, const void *character,
             ck3_11906::MarriageCharacterLineageV1 &out) noexcept {
  out = {};
  const auto house_id = Load<std::int32_t>(character, kFamilySubjectCharacterHouseIdOffset);
  if (house_id == -1) return true;
  void *house = ResolveComponent(b.house_storage_slot, b.house_fallback_slot, house_id);
  if (house == nullptr) return false;
  const auto dynasty_id = Load<std::int32_t>(house, kFamilySubjectHouseDynastyIdOffset);
  if (dynasty_id != -1 &&
      ResolveComponent(b.dynasty_storage_slot, b.dynasty_fallback_slot, dynasty_id) == nullptr)
    return false;
  out.house_id = house_id;
  out.dynasty_id = dynasty_id;
  return true;
}
bool SameSubject(const PlayerChildMarriageSubjectRead12002 &a,
                 const PlayerChildMarriageSubjectRead12002 &b) noexcept {
  return a.played_character_id == b.played_character_id &&
      a.subject_character_id == b.subject_character_id &&
      a.adult_measure_raw == b.adult_measure_raw && a.lineage == b.lineage &&
      a.employer_character_id == b.employer_character_id &&
      a.subject_is_player_child == b.subject_is_player_child &&
      a.adult_readback_available == b.adult_readback_available &&
      a.adult_selector_raw == b.adult_selector_raw &&
      a.adult_threshold_raw == b.adult_threshold_raw && a.is_adult == b.is_adult;
}
Failure SampleSubject(const FamilySubjectBindings &b, std::int32_t played_id,
                      std::int32_t subject_id, PlayerChildMarriageSubjectRead12002 &out) noexcept {
  const auto &core = b.family.context.core;
  void *played = ResolveCoreCharacter(core, played_id);
  void *subject = ResolveCoreCharacter(core, subject_id);
  if (played == nullptr || subject == nullptr || subject_id <= 0 || subject_id == played_id ||
      Load<void *>(subject, kCharacterDeathDataOffset) != nullptr)
    return Failure::subject_unavailable;
  if (b.is_character_child_of == nullptr) return Failure::relationship_unavailable;
  if (!b.is_character_child_of(subject, played)) return Failure::not_player_child;
  out.subject_is_player_child = true;
  const auto selector = Load<std::uint8_t>(subject, family_query_abi::kAdultSelectorOffset);
  if (selector > 1 || b.family.adult_threshold_zero == nullptr ||
      b.family.adult_threshold_one == nullptr) return Failure::relationship_unavailable;
  out.adult_measure_raw = Load<std::int16_t>(subject, family_query_abi::kAdultMeasureOffset);
  out.adult_selector_raw = selector;
  out.adult_threshold_raw = selector == 0 ? *b.family.adult_threshold_zero : *b.family.adult_threshold_one;
  out.is_adult = family_query_abi::IsAdult(out.adult_measure_raw, out.adult_threshold_raw);
  out.adult_readback_available = true;
  if (!Lineage(b, subject, out.lineage)) return Failure::lineage_unavailable;
  const auto *court_relation = Load<const std::byte *>(subject, kFamilySubjectCharacterCourtRelationOffset);
  out.employer_character_id = court_relation == nullptr ? -1 :
      Load<std::int32_t>(court_relation, kFamilySubjectCourtEmployerIdOffset);
  if (out.employer_character_id != -1 &&
      ResolveCoreCharacter(core, out.employer_character_id) == nullptr) return Failure::employer_unavailable;
  return Failure::none;
}
std::string_view Reason(Failure f) noexcept {
  switch (f) {
  case Failure::none: return {};
  case Failure::frame_changed: return "player_child_frame_changed";
  case Failure::subject_unavailable: return "player_child_subject_unavailable";
  case Failure::not_player_child: return "not_actual_child_of_played_character";
  case Failure::relationship_unavailable: return "player_child_relation_or_adult_input_unavailable";
  case Failure::lineage_unavailable: return "player_child_lineage_unavailable";
  case Failure::employer_unavailable: return "player_child_employer_unavailable";
  }
  return "player_child_subject_unavailable";
}
ck3_11906::PlayerFamilyArrayProbeSlotV1 ArraySlot(
    const CoreBindings &core, const std::byte *family, std::uint32_t offset) {
  ck3_11906::PlayerFamilyArrayProbeSlotV1 out{};
  out.offset = offset;
  out.header_readable = true;
  const auto *data = Load<const std::int32_t *>(family, offset);
  out.data_pointer_present = data != nullptr;
  out.capacity = Load<std::int32_t>(family, offset + 8);
  out.count = Load<std::int32_t>(family, offset + 12);
  out.native_int_array_shape = out.capacity >= 0 && out.count >= 0 &&
      out.count <= out.capacity && out.count <= 1'000'000 && (out.count == 0 || data != nullptr);
  if (!out.native_int_array_shape) return out;
  out.sample_readable = true;
  const auto count = (std::min)(out.count, std::int32_t{16});
  for (std::int32_t index = 0; index < count; ++index) {
    out.sample_ids.push_back(data[index]);
    out.sample_generation_valid.push_back(ResolveCoreCharacter(core, data[index]) != nullptr);
  }
  return out;
}
} // namespace

FamilySubjectBindings BindFamilySubjectImage(std::uintptr_t base, std::string_view sha) noexcept {
  FamilySubjectBindings out{};
  out.family = BindFamilyImage(base, sha);
  if (!out.family.enabled) return out;
  out.enabled = true;
  out.is_character_child_of = &NativeChildOf;
  out.house_storage_slot = reinterpret_cast<void **>(base + kFamilySubjectHouseStorageSlotRva);
  out.house_fallback_slot = reinterpret_cast<void **>(base + kFamilySubjectHouseFallbackSlotRva);
  out.dynasty_storage_slot = reinterpret_cast<void **>(base + kFamilySubjectDynastyStorageSlotRva);
  out.dynasty_fallback_slot = reinterpret_cast<void **>(base + kFamilySubjectDynastyFallbackSlotRva);
  return out;
}

PlayerChildMarriageSubjectRead12002 ReadPlayerChildMarriageSubjectV1(
    const FamilySubjectBindings &b, std::int32_t subject) noexcept {
  PlayerChildMarriageSubjectRead12002 out{};
  out.subject_character_id = subject;
  CoreSnapshotPrefix before{}, after{};
  if (!Frame(b, before)) {
    out.failure = Failure::frame_changed; out.unavailable_reason = Reason(out.failure); return out;
  }
  out.played_character_id = before.played_character_id;
  auto first = out;
  out.failure = SampleSubject(b, before.played_character_id, subject, first);
  if (out.failure == Failure::none) {
    const auto relation = ReadCurrentFirstHeirRelationshipV1(b.family, subject);
    if (relation.failure != ck3_11906::CurrentFirstHeirRelationshipFailureV1::none) {
      out.failure = relation.failure == ck3_11906::CurrentFirstHeirRelationshipFailureV1::frame_changed ?
          Failure::frame_changed : Failure::relationship_unavailable;
    } else {
      out.failure = SampleSubject(b, before.played_character_id, subject, out);
      if (out.failure == Failure::none &&
          (!Frame(b, after) || !SameFrame(before, after) || !SameSubject(first, out)))
        out.failure = Failure::frame_changed;
      if (out.failure == Failure::none) out.relationship = relation.relationship;
    }
  }
  if (out.failure != Failure::none) {
    const auto failure = out.failure;
    out = {}; out.played_character_id = before.played_character_id;
    out.subject_character_id = subject; out.failure = failure;
  }
  out.unavailable_reason = Reason(out.failure);
  return out;
}

ck3_11906::PlayerFamilyArrayProbeV1 ReadPlayerFamilyArrayProbeV1(
    const FamilySubjectBindings &b, std::int32_t played_id) noexcept {
  ck3_11906::PlayerFamilyArrayProbeV1 out{};
  out.played_character_id = played_id;
  CoreSnapshotPrefix before{}, after{};
  if (!Frame(b, before) || before.played_character_id != played_id) return out;
  const auto &core = b.family.context.core;
  void *played = ResolveCoreCharacter(core, played_id);
  if (played == nullptr) return out;
  const auto *family = Load<const std::byte *>(played, family_query_abi::kFamilyDataOffset);
  if (family != nullptr) {
    const auto relation = ReadCurrentFirstHeirRelationshipV1(b.family, played_id);
    out.spouse_readable = relation.failure == ck3_11906::CurrentFirstHeirRelationshipFailureV1::none;
    if (out.spouse_readable) out.primary_spouse_character_id = relation.relationship.primary_spouse_character_id;
    for (const auto offset : {kFamilySubjectSpouseArrayOffset, kFamilySubjectChildrenArrayOffset})
      out.slots.push_back(ArraySlot(core, family, static_cast<std::uint32_t>(offset)));
  } else {
    out.spouse_readable = true;
  }
  if (!Frame(b, after) || !SameFrame(before, after)) return {};
  out.available = true;
  return out;
}

} // namespace xar::ck3_12002
#endif
