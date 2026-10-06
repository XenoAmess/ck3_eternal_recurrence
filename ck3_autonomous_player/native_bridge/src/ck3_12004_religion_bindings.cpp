#include "xar_bridge/ck3_12004_religion_bindings.hpp"
#include "xar_bridge/ck3_12004_religion_profile.hpp"

#include <cstring>

namespace xar::ck3_12004::religion {
namespace {
namespace legacy = ck3_12002::religion;
namespace doctrine = legacy::doctrine12002;
namespace reform = ck3_12002::religion_reform;
namespace target = ck3_12003::religion::target_tenet;
namespace knowledge = ck3_12003::religion::tenet_knowledge;

bool Admitted(std::uintptr_t base, std::string_view sha) noexcept {
  return base != 0 && sha == ck3_12004::kExecutableSha256;
}

const void *ReligionDefinitionKey(void *religion) noexcept {
  const void *definition = nullptr;
  std::memcpy(&definition, static_cast<const std::byte *>(religion) +
      profile::kReligionDefinitionPointerOffset, sizeof(definition));
  return definition ? static_cast<const std::byte *>(definition) +
      profile::kReligionDefinitionKeyOffset : nullptr;
}

enum class FrameFailure { none, bindings, played, paused };
FrameFailure SelectPlayedFrame(const CoreBindings &core,
    CoreSnapshotPrefix &frame) noexcept {
  if (!core.enabled) return FrameFailure::bindings;
#if defined(_WIN32) && defined(_MSC_VER)
  __try {
#endif
    // This selector explicitly uses the actual .4 core. The shared software
    // readers below reuse only proved layouts and these supplied callbacks.
    if (!ck3_12004::ReadCoreSnapshot(core, frame) || !frame.map_ready ||
        !frame.has_played_character || !frame.played_character_alive ||
        !ck3_12004::ResolveCoreCharacter(core, frame.played_character_id))
      return FrameFailure::played;
    return frame.clock.paused ? FrameFailure::none : FrameFailure::paused;
#if defined(_WIN32) && defined(_MSC_VER)
  } __except (1) { return FrameFailure::played; }
#endif
}
const char *FrameReason(FrameFailure failure) noexcept {
  switch (failure) {
  case FrameFailure::none: return "none";
  case FrameFailure::bindings: return "bindings_unavailable";
  case FrameFailure::played: return "played_character_unavailable";
  case FrameFailure::paused: return "frame_not_paused";
  }
  return "played_character_unavailable";
}
template <typename T> void Stamp(T &out, std::uint64_t epoch,
    const CoreSnapshotPrefix &frame) noexcept {
  out.capture_epoch = epoch;
  out.date_raw = frame.clock.date_raw;
  out.played_character_id =
      static_cast<decltype(out.played_character_id)>(frame.played_character_id);
}
} // namespace

ContextBindings BindReligionContextImage12004(std::uintptr_t base,
    std::string_view sha) noexcept {
  ContextBindings b{};
  if (!Admitted(base, sha)) return b;
  b.enabled = true;
  b.core = ck3_12004::BindCoreImage(base, sha);
  b.character_rite = reinterpret_cast<legacy::ObjectGetter>(base + profile::kCharacterRiteRva);
  b.character_faith = reinterpret_cast<legacy::ObjectGetter>(base + profile::kCharacterFaithRva);
  b.rite_faith = reinterpret_cast<legacy::ObjectGetter>(base + profile::kRiteFaithRva);
  b.faith_religion = reinterpret_cast<legacy::ObjectGetter>(base + profile::kFaithReligionRva);
  b.faith_main_rite = reinterpret_cast<legacy::ObjectGetter>(base + profile::kFaithMainRiteRva);
  b.faith_fervor = reinterpret_cast<legacy::FixedPointGetter>(base + profile::kFaithFervorRva);
  b.character_spiritual_fulfillment = reinterpret_cast<legacy::FixedPointGetter>(base + profile::kCharacterSpiritualFulfillmentRva);
  b.faith_tag = reinterpret_cast<legacy::TagGetter>(base + profile::kFaithTagRva);
  b.religion_tag = &ReligionDefinitionKey;
  return b;
}

RiteModelBindings BindRiteModelImage12004(std::uintptr_t base,
    std::string_view sha) noexcept {
  RiteModelBindings b{};
  if (!Admitted(base, sha)) return b;
  b.enabled = true;
  b.core = ck3_12004::BindCoreImage(base, sha);
  b.character_rite = reinterpret_cast<legacy::ObjectGetter>(base + profile::kCharacterRiteRva);
  b.rite_faith = reinterpret_cast<legacy::ObjectGetter>(base + profile::kRiteFaithRva);
  b.faith_main_rite = reinterpret_cast<legacy::ObjectGetter>(base + profile::kFaithMainRiteRva);
  b.rite_is_main = reinterpret_cast<reform::rite::IsMainGetter>(base + profile::kRiteIsMainRva);
  b.divergence_to_main = reinterpret_cast<reform::rite::DivergenceGetter>(base + profile::kRiteDivergenceToMainRva);
  b.faith_heresy_threshold = reinterpret_cast<legacy::FixedPointGetter>(base + profile::kFaithHeresyThresholdRva);
  return b;
}

MainRiteBindings BindFaithMainRiteUnreformedImage12004(std::uintptr_t base,
    std::string_view sha) noexcept {
  MainRiteBindings b{};
  if (!Admitted(base, sha)) return b;
  b.enabled = true;
  b.main_rite = reinterpret_cast<reform::MainRiteGetter>(base + profile::kFaithMainRiteRva);
  b.is_unreformed = reinterpret_cast<reform::IsUnreformedGetter>(base + profile::kFaithIsUnreformedRva);
  return b;
}

DraftWindowBindings BindCurrentRiteCreationWindow12004(std::uintptr_t base,
    std::string_view sha) noexcept {
  DraftWindowBindings b{};
  if (!Admitted(base, sha)) return b;
  b.enabled = true;
  b.core = ck3_12004::BindCoreImage(base, sha);
  b.idler_vtable = base + profile::kDraftIdlerVtableRva;
  b.handler_vtable = base + profile::kDraftHandlerVtableRva;
  b.window_vtable = base + profile::kDraftWindowPrimaryVtableRva;
  b.window_secondary_vtable = base + profile::kDraftWindowSecondaryVtableRva;
  b.is_visible = reinterpret_cast<reform::DraftWindowVisible>(base + profile::kDraftWindowVisibilityRva);
  return b;
}

ReformQueryBindings BindReformQueryImage12004(std::uintptr_t base,
    std::string_view sha) noexcept {
  ReformQueryBindings b{};
  if (!Admitted(base, sha)) return b;
  b.enabled = true;
  b.core = ck3_12004::BindCoreImage(base, sha);
  b.context = BindReligionContextImage12004(base, sha);
  b.rite_model = BindRiteModelImage12004(base, sha);
  b.main_rite = BindFaithMainRiteUnreformedImage12004(base, sha);
  b.window = BindCurrentRiteCreationWindow12004(base, sha);
  return b;
}

CurrentDoctrineBindings BindCurrentDoctrineImage12004(std::uintptr_t base,
    std::string_view sha) noexcept {
  CurrentDoctrineBindings b{};
  if (!Admitted(base, sha)) return b;
  b.context = BindReligionContextImage12004(base, sha);
  b.parameters.enabled = true;
  b.parameters.contains_boolean_parameter = reinterpret_cast<doctrine::BooleanParameterMembership>(base + profile::kBooleanParameterMembershipRva);
  b.parameters.parameter_key = reinterpret_cast<doctrine::ParameterTokenKey>(base + profile::kParameterTokenKeyRva);
  return b;
}

DoctrineKnowledgeBindings BindDoctrineKnowledgeImage12004(std::uintptr_t base,
    std::string_view sha) noexcept {
  DoctrineKnowledgeBindings b{};
  if (!Admitted(base, sha)) return b;
  b.context = BindReligionContextImage12004(base, sha);
  b.knows_doctrine = reinterpret_cast<doctrine::NativeKnowsDoctrine>(base + profile::kCharacterKnowsDoctrineRva);
  b.definition_database_global = reinterpret_cast<void *const *>(base + profile::kDoctrineDatabaseSlotRva);
  return b;
}

PlayerTenetBindings BindPlayerTenetImage12004(std::uintptr_t base,
    std::string_view sha) noexcept {
  PlayerTenetBindings b{};
  if (!Admitted(base, sha)) return b;
  b.context = BindReligionContextImage12004(base, sha);
  b.rows.enabled = true;
  b.rows.tenet_state = reinterpret_cast<doctrine::NativeTenetState>(base + profile::kNativeTenetStateRva);
  b.comparison.context = b.context;
  b.comparison.rite_storage_global = reinterpret_cast<void *const *>(base + profile::kRiteStorageSlotRva);
  b.comparison.tenet_database_global = reinterpret_cast<void *const *>(base + profile::kTenetDatabaseSlotRva);
  b.comparison.tenet_state = b.rows.tenet_state;
  b.knowledge.context = b.context;
  b.knowledge.tenet_database_global = b.comparison.tenet_database_global;
  b.knowledge.perk_database_global = reinterpret_cast<void *const *>(base + profile::kPerkDatabaseSlotRva);
  b.knowledge.actor_extra_collection = reinterpret_cast<reform::TenetSourcesCollection>(base + profile::kCharacterExtraTenetsRva);
  b.knowledge.actor_perks_collection = reinterpret_cast<reform::TenetSourcesCollection>(base + profile::kCharacterActualPerksRva);
  b.knowledge.contains = reinterpret_cast<reform::TenetSourcesContains>(base + profile::kActualDefinitionPointerContainsRva);
  return b;
}

bool ReadPlayedReligionContext12004(const ContextBindings &b,
    std::uint64_t epoch, legacy::Context &out) noexcept {
  out = {};
  CoreSnapshotPrefix frame{};
  const auto failure = b.enabled ? SelectPlayedFrame(b.core, frame) : FrameFailure::bindings;
  Stamp(out, epoch, frame);
  if (failure != FrameFailure::none) {
    out.failure = failure == FrameFailure::paused ? legacy::Failure::frame_not_paused
        : (failure == FrameFailure::bindings ? legacy::Failure::bindings_unavailable
                                            : legacy::Failure::played_character_unavailable);
    return false;
  }
  const bool read = legacy::ReadPlayedReligionContext12002(b, epoch, out);
  if (!read) Stamp(out, epoch, frame);
  return read;
}

bool ReadPlayedReformQuery12004(const ReformQueryBindings &b,
    std::uint64_t epoch, reform::query::Observation &out) noexcept {
  out = {};
  CoreSnapshotPrefix frame{};
  const auto failure = b.enabled ? SelectPlayedFrame(b.core, frame) : FrameFailure::bindings;
  Stamp(out, epoch, frame);
  if (failure != FrameFailure::none) { out.failure = FrameReason(failure); return false; }
  const bool read = reform::query::ReadPlayedReformQuery12002(b, epoch, out);
  if (!read) Stamp(out, epoch, frame);
  return read;
}

bool ReadPlayedCurrentDoctrines12004(const CurrentDoctrineBindings &b,
    std::uint64_t epoch, doctrine::CurrentDoctrineContext &out) noexcept {
  out = {};
  CoreSnapshotPrefix frame{};
  const auto failure = b.context.enabled ? SelectPlayedFrame(b.context.core, frame) : FrameFailure::bindings;
  Stamp(out, epoch, frame);
  if (failure != FrameFailure::none) { out.unavailable_reason = FrameReason(failure); return false; }
  const bool read = doctrine::ReadPlayedCurrentDoctrines12002(b, epoch, out);
  if (!read) Stamp(out, epoch, frame);
  return read;
}

bool ReadPlayedDoctrineKnowledge12004(const DoctrineKnowledgeBindings &b,
    std::uint64_t epoch, doctrine::PlayedDoctrineKnowledge &out) noexcept {
  out = {};
  CoreSnapshotPrefix frame{};
  const auto failure = b.context.enabled ? SelectPlayedFrame(b.context.core, frame) : FrameFailure::bindings;
  Stamp(out, epoch, frame);
  if (failure != FrameFailure::none) { out.unavailable_reason = FrameReason(failure); return false; }
  const bool read = doctrine::ReadPlayedDoctrineKnowledge12002(b, epoch, out);
  if (!read) Stamp(out, epoch, frame);
  return read;
}

bool ReadPlayedDoctrineKnowledgeByKey12004(const DoctrineKnowledgeBindings &b,
    std::string_view key, std::uint64_t epoch,
    doctrine::PlayedDoctrineKnowledgeLookup &out) noexcept {
  out = {};
  out.requested_doctrine_key = key;
  CoreSnapshotPrefix frame{};
  const auto failure = b.context.enabled ? SelectPlayedFrame(b.context.core, frame) : FrameFailure::bindings;
  Stamp(out, epoch, frame);
  if (failure != FrameFailure::none) { out.unavailable_reason = FrameReason(failure); return false; }
  const bool read = doctrine::ReadPlayedDoctrineKnowledgeByKey12002(b, key, epoch, out);
  if (!read) Stamp(out, epoch, frame);
  return read;
}

bool ReadPlayedTenetRows12004(const ContextBindings &b,
    const doctrine::TenetRowsBindings &rows, std::uint64_t epoch,
    doctrine::TenetRowsContext &out) noexcept {
  out = {};
  CoreSnapshotPrefix frame{};
  const auto failure = b.enabled ? SelectPlayedFrame(b.core, frame) : FrameFailure::bindings;
  Stamp(out, epoch, frame);
  if (failure != FrameFailure::none) { out.failure = FrameReason(failure); return false; }
  const bool read = doctrine::ReadPlayedTenetRows12002(b, rows, epoch, out);
  if (!read) Stamp(out, epoch, frame);
  return read;
}

bool ReadPlayedTargetRiteTenetComparison12004(const target::Bindings &b,
    std::uint32_t target_id, std::string_view key, std::uint64_t epoch,
    target::Comparison &out) noexcept {
  out = {};
  out.requested_target_rite_id = target_id;
  out.tenet_key = key;
  CoreSnapshotPrefix frame{};
  const auto failure = b.context.enabled ? SelectPlayedFrame(b.context.core, frame) : FrameFailure::bindings;
  Stamp(out, epoch, frame);
  if (failure != FrameFailure::none) {
    out.failure = failure == FrameFailure::paused ? target::Failure::frame_not_paused
        : (failure == FrameFailure::bindings ? target::Failure::bindings_unavailable
                                            : target::Failure::played_character_unavailable);
    return false;
  }
  const bool read = target::ReadPlayedTargetRiteTenetComparison12003(b, target_id, key, epoch, out);
  if (!read) Stamp(out, epoch, frame);
  return read;
}

bool ReadPlayedTenetKnowledgeCatalogue12004(const knowledge::Bindings &b,
    std::uint64_t epoch, knowledge::Catalogue &out) noexcept {
  out = {};
  CoreSnapshotPrefix frame{};
  const auto failure = b.context.enabled ? SelectPlayedFrame(b.context.core, frame) : FrameFailure::bindings;
  Stamp(out, epoch, frame);
  if (failure != FrameFailure::none) {
    out.failure = failure == FrameFailure::paused ? knowledge::Failure::frame_not_paused
        : (failure == FrameFailure::bindings ? knowledge::Failure::bindings_unavailable
                                            : knowledge::Failure::played_character_unavailable);
    return false;
  }
  const bool read = knowledge::ReadPlayedTenetKnowledgeCatalogue12003(b, epoch, out);
  if (!read) Stamp(out, epoch, frame);
  return read;
}

} // namespace xar::ck3_12004::religion
