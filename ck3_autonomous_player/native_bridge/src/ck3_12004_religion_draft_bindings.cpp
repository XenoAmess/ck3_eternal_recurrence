#include "xar_bridge/ck3_12004_religion_draft_bindings.hpp"
#include "xar_bridge/ck3_12004_religion_profile.hpp"

namespace xar::ck3_12004::religion {
namespace {
namespace reform = ck3_12002::religion_reform;
namespace terms = reform::creation_terms12003;

// SOURCE-READY: adopted-restoration-1262/python-coverage. Complete consumed
// callbacks and concrete field witnesses are mapped independently of .3.
constexpr std::uintptr_t kTenetItemCanPickRva = 0xEE0AD0;
constexpr std::uintptr_t kCharacterHasPerkRva = 0x2919050;
constexpr std::uintptr_t kEvaluateTriggerRva = 0x372DF10;
constexpr std::uintptr_t kTenetSourceFilterRva = 0x14F2010;
constexpr std::uintptr_t kActorFaithRawTenetStatusRva = 0x2442590;
constexpr std::uintptr_t kDefaultTenetDefinitionSlotRva = 0x5D1F6C0;
constexpr std::uintptr_t kFaithStorageSlotRva = 0x5D1E300;
constexpr std::uintptr_t kDraftDivergenceRva = 0x14F1490;
constexpr std::uintptr_t kFaithCreationThresholdRva = 0x5C68C68;
constexpr std::uintptr_t kNativeCreateFaithOrReformRva = 0x2BDCA70;

bool Admitted(std::uintptr_t base, std::string_view sha) noexcept {
  return base != 0 && sha == ck3_12004::kExecutableSha256;
}

const char *SelectFrame(const CoreBindings &core,
    CoreSnapshotPrefix &frame) noexcept {
  if (!core.enabled) return "bindings_unavailable";
#if defined(_WIN32) && defined(_MSC_VER)
  __try {
#endif
    if (!ck3_12004::ReadCoreSnapshot(core, frame) || !frame.map_ready ||
        !frame.has_played_character || !frame.played_character_alive ||
        !ck3_12004::ResolveCoreCharacter(core, frame.played_character_id))
      return "played_character_unavailable";
    return frame.clock.paused ? nullptr : "frame_not_paused";
#if defined(_WIN32) && defined(_MSC_VER)
  } __except (1) { return "played_character_unavailable"; }
#endif
}

template <typename T, typename Reader>
bool ReadOwned(const DraftWindowBindings &window, std::uint64_t epoch,
    T &out, Reader reader) noexcept {
  out = {};
  CoreSnapshotPrefix frame{};
  const auto *reason = window.enabled ? SelectFrame(window.core, frame)
                                      : "bindings_unavailable";
  if (reason) {
    out.failure = reason;
  } else if (reader()) {
    return true;
  }
  out.capture_epoch = epoch;
  out.date_raw = frame.clock.date_raw;
  out.played_character_id = static_cast<decltype(out.played_character_id)>(frame.played_character_id);
  return false;
}
} // namespace

DraftChoiceBindings BindCurrentDraftChoices12004(std::uintptr_t base,
    std::string_view sha) noexcept {
  DraftChoiceBindings b{};
  if (!Admitted(base, sha)) return b;
  b.window = BindCurrentRiteCreationWindow12004(base, sha);
  b.knows_doctrine = BindDoctrineKnowledgeImage12004(base, sha).knows_doctrine;
  b.evaluate_trigger = reinterpret_cast<reform::ChoiceTriggerEval>(base + kEvaluateTriggerRva);
  b.tenet_can_pick = reinterpret_cast<reform::TenetItemCanPick>(base + kTenetItemCanPickRva);
  b.has_perk = reinterpret_cast<reform::ChoiceHasPerk>(base + kCharacterHasPerkRva);
  b.perk_database_global = reinterpret_cast<void *const *>(base + profile::kPerkDatabaseSlotRva);
  return b;
}

TenetSourcesBindings BindCurrentDraftTenetSources12004(std::uintptr_t base,
    std::string_view sha) noexcept {
  TenetSourcesBindings b{};
  if (!Admitted(base, sha)) return b;
  b.window = BindCurrentRiteCreationWindow12004(base, sha);
  b.tenet_database_global = reinterpret_cast<void *const *>(base + profile::kTenetDatabaseSlotRva);
  b.default_tenet_definition_global = reinterpret_cast<void *const *>(base + kDefaultTenetDefinitionSlotRva);
  b.rite_storage_global = reinterpret_cast<void *const *>(base + profile::kRiteStorageSlotRva);
  b.faith_storage_global = reinterpret_cast<void *const *>(base + kFaithStorageSlotRva);
  b.perk_database_global = reinterpret_cast<void *const *>(base + profile::kPerkDatabaseSlotRva);
  b.source_filter = reinterpret_cast<reform::TenetSourcesFilter>(base + kTenetSourceFilterRva);
  b.source_main_rite_status = reinterpret_cast<reform::TenetSourcesStatus>(base + profile::kNativeTenetStateRva);
  b.actor_faith_status = reinterpret_cast<reform::TenetSourcesStatus>(base + kActorFaithRawTenetStatusRva);
  b.actor_extra_collection = reinterpret_cast<reform::TenetSourcesCollection>(base + profile::kCharacterExtraTenetsRva);
  b.actor_perks_collection = reinterpret_cast<reform::TenetSourcesCollection>(base + profile::kCharacterActualPerksRva);
  b.contains = reinterpret_cast<reform::TenetSourcesContains>(base + profile::kActualDefinitionPointerContainsRva);
  b.evaluate_trigger = reinterpret_cast<reform::TenetSourcesTrigger>(base + kEvaluateTriggerRva);
  b.enabled = true;
  return b;
}

DraftCreationTermsBindings BindDraftCreationTermsImage12004(std::uintptr_t base,
    std::string_view sha) noexcept {
  DraftCreationTermsBindings b{};
  if (!Admitted(base, sha)) return b;
  b.rite_storage_global = reinterpret_cast<void *const *>(base + profile::kRiteStorageSlotRva);
  b.faith_storage_global = reinterpret_cast<void *const *>(base + kFaithStorageSlotRva);
  b.draft_divergence = reinterpret_cast<terms::DraftDivergenceGetter>(base + kDraftDivergenceRva);
  b.creation_threshold_raw = reinterpret_cast<const std::int64_t *>(base + kFaithCreationThresholdRva);
  b.native_create_faith_or_reform = reinterpret_cast<terms::NativeCreateFaithOrReform>(base + kNativeCreateFaithOrReformRva);
  b.enabled = true;
  return b;
}

bool ReadCurrentDraftFullDoctrineChoices12004(const DraftChoiceBindings &b,
    std::uint64_t epoch, reform::DraftFullDoctrineChoices &out) noexcept {
  return ReadOwned(b.window, epoch, out, [&] {
    return reform::ReadCurrentDraftFullDoctrineChoices12002(b, epoch, out);
  });
}

bool ReadCurrentDraftGroupModel12004(const DraftChoiceBindings &b,
    std::uint64_t epoch, reform::DraftGroupModel &out) noexcept {
  return ReadOwned(b.window, epoch, out, [&] {
    return reform::ReadCurrentDraftGroupModel12002(b, epoch, out);
  });
}

bool ReadCurrentDraftTenetSources12004(const TenetSourcesBindings &b,
    std::uint64_t epoch, reform::DraftTenetSources &out) noexcept {
  return ReadOwned(b.window, epoch, out, [&] {
    return reform::ReadCurrentDraftTenetSources12002(b, epoch, out);
  });
}

} // namespace xar::ck3_12004::religion
