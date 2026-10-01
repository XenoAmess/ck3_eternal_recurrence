#include "xar_bridge/ck3_12002_prisoner_war_retention.hpp"

#include <algorithm>
#include <cstring>
#include <utility>

namespace xar::ck3_12002 {
namespace {
using Observation = ck3_11906::WarPrisonerReleasePairsObservationV1;
using Result = ck3_11906::ReadWarPrisonerReleasePairsResultV1;

template <typename T> T Load(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset,
              sizeof(value));
  return value;
}

bool Contains(const std::vector<std::int32_t> &ids, std::int32_t id) noexcept {
  return std::find(ids.begin(), ids.end(), id) != ids.end();
}

bool ReadKey(const void *type, std::string &key) {
  if (type == nullptr) return false;
  const auto *text = static_cast<const std::byte *>(type) + 0x18;
  const auto size = Load<std::size_t>(text, 0x10);
  const auto capacity = Load<std::size_t>(text, 0x18);
  if (size == 0 || size > capacity || size > 1'024) return false;
  const char *data = capacity <= 15
                         ? reinterpret_cast<const char *>(text)
                         : Load<const char *>(text, 0);
  if (data == nullptr) return false;
  key.assign(data, size);
  return true;
}

bool ReadParticipants(const PrisonerWarRetentionBindings &bindings,
                      const void *side, std::vector<std::int32_t> &ids) {
  if (!ReadWarParticipantIds(side, ids) || ids.empty()) return false;
  return std::all_of(ids.begin(), ids.end(), [&bindings](std::int32_t id) {
    return id > 0 && ResolveCoreCharacter(bindings.core, id) != nullptr;
  });
}

bool ReadCandidates(const PrisonerWarRetentionBindings &bindings,
                    std::int32_t primary_id,
                    std::vector<std::int32_t> &ids) {
  void *primary = ResolveCoreCharacter(bindings.core, primary_id);
  if (primary == nullptr) return false;
  void *title = bindings.primary_title(primary);
  if (title == nullptr) return false;
  const auto title_id = Load<std::int32_t>(title, 0x10);
  if (title_id <= 0 || ResolveObjectiveTitle(bindings.titles, title_id) != title)
    return false;
  const auto capacity = Load<std::int32_t>(title,
      kWarRetentionSuccessorCapacityOffset);
  const auto count = Load<std::int32_t>(title, kWarRetentionSuccessorCountOffset);
  const void *data = Load<void *>(title, kWarRetentionSuccessorDataOffset);
  if (capacity < 0 || count < 0 || count > capacity || count > 4'096 ||
      (count > 0 && data == nullptr)) return false;
  ids.push_back(primary_id);
  // The stock effect selects positions <= 3; later successors are not
  // candidates and must not acquire a fabricated retention commitment.
  for (std::int32_t index = 0; index < count && index < 3; ++index) {
    const auto id = Load<std::int32_t>(data,
        static_cast<std::size_t>(index) * sizeof(std::int32_t));
    if (id <= 0 || ResolveCoreCharacter(bindings.core, id) == nullptr ||
        Contains(ids, id)) return false;
    ids.push_back(id);
  }
  return bindings.primary_title(primary) == title &&
      ResolveCoreCharacter(bindings.core, primary_id) == primary &&
      ResolveObjectiveTitle(bindings.titles, title_id) == title;
}

bool AppendPairs(const PrisonerWarRetentionBindings &bindings,
                 const std::vector<std::int32_t> &candidates,
                 const std::vector<std::int32_t> &opposite_participants,
                 std::vector<game::WarExitPrisonerReleaseSnapshot> &pairs) {
  for (const auto id : candidates) {
    void *character = ResolveCoreCharacter(bindings.core, id);
    if (character == nullptr) return false;
    void *extension = Load<void *>(character,
        kWarRetentionCharacterExtensionOffset);
    void *relation = extension == nullptr ? nullptr : Load<void *>(extension,
        kWarRetentionCustodyRelationOffset);
    if (relation == nullptr) continue;
    const auto jailer_id = Load<std::int32_t>(relation, kWarRetentionJailerIdOffset);
    void *jailer = ResolveCoreCharacter(bindings.core, jailer_id);
    if (jailer_id <= 0 || jailer == nullptr ||
        bindings.imprisoned_by(character) != jailer) return false;
    if (Contains(opposite_participants, jailer_id))
      pairs.push_back({jailer_id, id,
          "opposite_primary_or_first_three_successors"});
  }
  return true;
}

bool Sample(const PrisonerWarRetentionBindings &bindings, const void *war,
            std::int32_t war_id, std::int32_t date_raw, Observation &output) {
  output = {};
  output.war_id = war_id;
  output.date_raw = date_raw;
  void *cb = Load<void *>(war, kWorldWarCasusBelliOffset);
  if (cb == nullptr) return false;
  output.active_casus_belli_database_index = Load<std::int32_t>(cb, 0x10);
  if (output.active_casus_belli_database_index < 0 ||
      output.active_casus_belli_database_index >= 10'000 ||
      !ReadKey(cb, output.active_casus_belli_key)) return false;
  output.primary_attacker_character_id =
      Load<std::int32_t>(war, kWorldWarPrimaryAttackerOffset);
  output.primary_defender_character_id =
      Load<std::int32_t>(war, kWorldWarPrimaryDefenderOffset);
  if (output.primary_attacker_character_id <= 0 ||
      output.primary_defender_character_id <= 0 ||
      output.primary_attacker_character_id == output.primary_defender_character_id)
    return false;
  const auto *bytes = static_cast<const std::byte *>(war);
  if (!ReadParticipants(bindings, bytes + kWorldWarAttackersOffset,
          output.attacker_participant_ids) ||
      !ReadParticipants(bindings, bytes + kWorldWarDefendersOffset,
          output.defender_participant_ids) ||
      !Contains(output.attacker_participant_ids, output.primary_attacker_character_id) ||
      !Contains(output.defender_participant_ids, output.primary_defender_character_id) ||
      !ReadCandidates(bindings, output.primary_attacker_character_id,
          output.attacker_release_candidate_ids) ||
      !ReadCandidates(bindings, output.primary_defender_character_id,
          output.defender_release_candidate_ids) ||
      !AppendPairs(bindings, output.attacker_release_candidate_ids,
          output.defender_participant_ids, output.release_pairs) ||
      !AppendPairs(bindings, output.defender_release_candidate_ids,
          output.attacker_participant_ids, output.release_pairs)) return false;
  output.full_participant_scan = true;
  output.primary_and_first_three_successors_scanned = true;
  return true;
}
} // namespace

PrisonerWarRetentionBindings BindPrisonerWarRetentionImage(
    std::uintptr_t image_base, std::string_view sha256) noexcept {
  PrisonerWarRetentionBindings bindings{};
  if (image_base == 0 || sha256 != kExecutableSha256) return bindings;
  bindings.enabled = true;
  bindings.core = BindCoreImage(image_base, sha256);
  bindings.world = BindWorldImage(image_base, sha256);
  bindings.titles = BindProvinceImage(image_base, sha256);
  bindings.primary_title = reinterpret_cast<WarRetentionCharacterGetter12002>(
      image_base + kWarRetentionPrimaryTitleRva);
  bindings.imprisoned_by = reinterpret_cast<WarRetentionCharacterGetter12002>(
      image_base + kWarRetentionImprisonedByRva);
  return bindings;
}

Result ReadWarPrisonerReleasePairsV1(
    const PrisonerWarRetentionBindings &bindings, std::int32_t war_id,
    Observation &output) noexcept {
  output = {};
  if (!bindings.enabled || !bindings.core.enabled || !bindings.world.enabled ||
      !bindings.titles.enabled || bindings.primary_title == nullptr ||
      bindings.imprisoned_by == nullptr || war_id <= 0)
    return Result::unavailable;
  try {
    CoreSnapshotPrefix before{};
    if (!ReadCoreSnapshot(bindings.core, before)) return Result::unavailable;
    if (!before.clock.paused) return Result::requires_paused;
    if (!before.has_played_character || !before.played_character_alive)
      return Result::no_played_character;
    void *war = ResolveWar(bindings.world, war_id);
    if (war == nullptr) return Result::war_not_found;
    Observation first{}, second{};
    if (!Sample(bindings, war, war_id, before.clock.date_raw, first))
      return Result::unavailable;
    if (!Contains(first.attacker_participant_ids, before.played_character_id) &&
        !Contains(first.defender_participant_ids, before.played_character_id))
      return Result::player_not_participant;
    if (ResolveWar(bindings.world, war_id) != war ||
        !Sample(bindings, war, war_id, before.clock.date_raw, second) ||
        first != second) return Result::unavailable;
    CoreSnapshotPrefix after{};
    if (!ReadCoreSnapshot(bindings.core, after) || !after.clock.paused ||
        !after.has_played_character || !after.played_character_alive ||
        after.clock.date_raw != before.clock.date_raw ||
        after.played_character_id != before.played_character_id ||
        ResolveWar(bindings.world, war_id) != war) return Result::unavailable;
    second.same_frame_stable = true;
    output = std::move(second);
    return Result::available;
  } catch (...) {
    output = {};
    return Result::unavailable;
  }
}
} // namespace xar::ck3_12002
