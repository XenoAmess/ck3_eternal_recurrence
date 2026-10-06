#include "xar_bridge/ck3_12003_prisoner_release_preview.hpp"
#include "xar_bridge/ck3_12003_prisoner_negotiated_preview.hpp"

#include <array>
#include <limits>

namespace xar::ck3_12003 {
namespace {

constexpr std::uintptr_t kCharacterFallbackSlotRva = 0x5C67570;
constexpr std::size_t kStorageSlotsOffset = 0x20;
constexpr std::size_t kStorageCapacityOffset = 0x2C;
constexpr std::size_t kStorageSlotStride = 0x10;
constexpr std::size_t kStorageSlotObjectOffset = 0x08;
constexpr std::size_t kCharacterIdentityOffset = 0x18;
constexpr std::size_t kCharacterExtensionOffset = 0x1B0;
constexpr std::size_t kExtensionPrisonRelationOffset = 0x288;
constexpr std::uint32_t kIdentitySlotMask = 0x00FFFFFFU;
constexpr std::int32_t kMaximumCharacterSlots = 1 << 20;

struct NativeStringView {
  const char *data = nullptr;
  std::int32_t size = 0;
  std::uint8_t owned = 0;
  std::array<std::byte, 3> padding{};
};
static_assert(sizeof(NativeStringView) == 0x10);

struct NativeSample {
  std::uintptr_t database = 0;
  std::uintptr_t definition = 0;
  std::uintptr_t option_rows = 0;
  std::uintptr_t jailer = 0;
  std::uintptr_t prisoner = 0;
  std::uintptr_t prisoner_extension = 0;
  std::uintptr_t prison_relation = 0;
  std::int32_t definition_hash = 0;
  std::int32_t definition_ordinal = -1;
  std::array<std::int32_t, 13> option_flags{};
  std::uint32_t actor = 0;
  std::uint32_t recipient = 0;
  std::uint32_t puppet_or_actor = 0;
  std::int32_t definition_option_count = 0;
  std::int32_t context_option_count = 0;
  std::uint32_t selected_option_mask_bits = 0;
  bool can_send = false;
  bool auto_accept = false;
  std::array<std::int64_t, 10> costs{};

  friend bool operator==(const NativeSample &, const NativeSample &) = default;
};

template <typename T>
bool Read(const PrisonerReleasePreviewAccess12003 &access,
    std::uintptr_t base, std::size_t offset, T &value) noexcept {
  return base != 0 &&
      offset <= (std::numeric_limits<std::uintptr_t>::max)() - base &&
      access.read_memory(access.context, base + offset, &value, sizeof(value));
}

bool HasBindings(const PrisonerReleasePreviewBindings12003 &b) noexcept {
  const auto &gift = b.gift;
  const auto &c = gift.interaction;
  return b.enabled && b.module_base != 0 && gift.enabled && c.enabled &&
      gift.get_database != nullptr && gift.stable_hash != nullptr &&
      gift.lookup_definition != nullptr && gift.construct_two_role != nullptr &&
      c.refresh != nullptr && c.finalize != nullptr && c.validate != nullptr &&
      c.destroy != nullptr && c.evaluate_cost != nullptr &&
      c.evaluate_trigger != nullptr && b.clear_local_options != nullptr &&
      b.get_script_identifier_table != nullptr &&
      b.lookup_script_identifier_id != nullptr;
}

bool ResolveCharacter(const PrisonerReleasePreviewAccess12003 &access,
    std::uintptr_t storage, std::uintptr_t fallback, std::uint32_t id,
    std::uintptr_t &character) noexcept {
  std::uintptr_t slots = 0;
  std::int32_t capacity = 0;
  if (id == 0 || !Read(access, storage, kStorageSlotsOffset, slots) || slots == 0 ||
      !Read(access, storage, kStorageCapacityOffset, capacity) || capacity <= 0 ||
      capacity > kMaximumCharacterSlots) return false;
  const auto slot = id & kIdentitySlotMask;
  std::uint32_t observed = 0;
  return slot < static_cast<std::uint32_t>(capacity) &&
      Read(access, slots, static_cast<std::size_t>(slot) * kStorageSlotStride +
          kStorageSlotObjectOffset, character) && character != 0 &&
      character != fallback &&
      Read(access, character, kCharacterIdentityOffset, observed) && observed == id;
}

bool ReadCustody(const PrisonerReleasePreviewBindings12003 &b,
    const PrisonerReleasePreviewAccess12003 &access, std::uint32_t jailer_id,
    std::uint32_t prisoner_id, NativeSample &sample) noexcept {
  std::uintptr_t storage = 0;
  std::uintptr_t fallback = 0;
  std::uint32_t actual_jailer = 0;
  return Read(access, b.module_base, kCharacterStorageSlotRva, storage) &&
      Read(access, b.module_base, kCharacterFallbackSlotRva, fallback) && storage != 0 &&
      ResolveCharacter(access, storage, fallback, jailer_id, sample.jailer) &&
      ResolveCharacter(access, storage, fallback, prisoner_id, sample.prisoner) &&
      Read(access, sample.prisoner, kCharacterExtensionOffset,
          sample.prisoner_extension) && sample.prisoner_extension != 0 &&
      Read(access, sample.prisoner_extension, kExtensionPrisonRelationOffset,
          sample.prison_relation) && sample.prison_relation != 0 &&
      Read(access, sample.prison_relation, 0, actual_jailer) && actual_jailer == jailer_id;
}

bool ReadDefinitionKey(const PrisonerReleasePreviewAccess12003 &access,
    std::uintptr_t definition) {
  const auto text = definition + ck3_12002::kFactionGiftDefinitionKeyOffsetV1;
  std::uint64_t size = 0;
  std::uint64_t capacity = 0;
  if (!Read(access, text, 0x10, size) || !Read(access, text, 0x18, capacity) ||
      size != kPrisonerReleaseDefinitionKey12003.size() || size > capacity)
    return false;
  std::uintptr_t data = text;
  if (capacity >= 16 && (!Read(access, text, 0, data) || data == 0)) return false;
  std::array<char, kPrisonerReleaseDefinitionKey12003.size()> key{};
  return access.read_memory(access.context, data, key.data(), key.size()) &&
      std::string_view(key.data(), key.size()) == kPrisonerReleaseDefinitionKey12003;
}

bool ReadDefinition(const PrisonerReleasePreviewBindings12003 &b,
    const PrisonerReleasePreviewAccess12003 &access, NativeSample &sample,
    std::string &reason) {
  void *const database = b.gift.get_database();
  if (database == nullptr) { reason = "definition_unavailable"; return false; }
  const auto key = kPrisonerReleaseDefinitionKey12003;
  const auto hash = b.gift.stable_hash(database, key.data(),
      static_cast<std::uint32_t>(key.size()));
  void *const definition = b.gift.lookup_definition(database, hash);
  sample.database = reinterpret_cast<std::uintptr_t>(database);
  sample.definition = reinterpret_cast<std::uintptr_t>(definition);
  if (definition == nullptr ||
      !Read(access, sample.definition, ck3_12002::kFactionGiftDefinitionHashOffsetV1,
          sample.definition_hash) || sample.definition_hash != hash ||
      !Read(access, sample.definition, kPrisonerReleaseDefinitionOrdinalOffset12003,
          sample.definition_ordinal) || sample.definition_ordinal < 0 ||
      !ReadDefinitionKey(access, sample.definition)) {
    reason = "definition_identity_unverified"; return false;
  }
  if (!Read(access, sample.definition, kPrisonerReleaseDefinitionOptionCountOffset12003,
          sample.definition_option_count) ||
      sample.definition_option_count !=
          static_cast<std::int32_t>(kPrisonerReleaseOptionKeys12003.size())) {
    reason = "option_definition_count_unexpected"; return false;
  }
  void *const table = b.get_script_identifier_table();
  if (table == nullptr ||
      !Read(access, sample.definition, kPrisonerReleaseDefinitionOptionRowsOffset12003,
          sample.option_rows) || sample.option_rows == 0) {
    reason = "option_flag_identity_unverified"; return false;
  }
  for (std::size_t i = 0; i < kPrisonerReleaseOptionKeys12003.size(); ++i) {
    const auto flag = kPrisonerReleaseOptionKeys12003[i];
    const NativeStringView view{flag.data(), static_cast<std::int32_t>(flag.size())};
    std::int32_t expected = -1;
    if (!Read(access, sample.option_rows,
            i * kPrisonerReleaseDefinitionOptionRowStride12003 +
                kPrisonerReleaseDefinitionOptionFlagOffset12003,
            sample.option_flags[i]) ||
        b.lookup_script_identifier_id(table, &expected, &view) == nullptr ||
        expected < 0 || sample.option_flags[i] != expected) {
      reason = "option_flag_identity_unverified"; return false;
    }
  }
  return true;
}

class OwnedContext {
public:
  explicit OwnedContext(ck3_12002::MarriageDestroyInteractionContext destroy)
      : destroy_(destroy) {}
  ~OwnedContext() { if (constructed_) destroy_(bytes_.data()); }
  void *data() noexcept { return bytes_.data(); }
  const void *scope() const noexcept { return bytes_.data() + 8; }
  void MarkConstructed() noexcept { constructed_ = true; }

private:
  alignas(8) std::array<std::byte, ck3_12002::kFactionGiftContextSizeV1> bytes_{};
  ck3_12002::MarriageDestroyInteractionContext destroy_ = nullptr;
  bool constructed_ = false;
};

bool ReadFinalSelection(const PrisonerReleasePreviewAccess12003 &access,
    std::uintptr_t context, std::uint32_t jailer, std::uint32_t prisoner,
    NativeSample &sample, std::string &reason) {
  std::uintptr_t actual_definition = 0;
  std::uintptr_t data = 0;
  std::int32_t capacity = 0;
  std::int32_t secondary_actor = 0;
  std::int32_t secondary_recipient = 0;
  std::int32_t intermediary = 0;
  if (!Read(access, context, 0, actual_definition) ||
      actual_definition != sample.definition ||
      !Read(access, context, ck3_12002::kFactionGiftContextActorOffsetV1, sample.actor) ||
      !Read(access, context, ck3_12002::kFactionGiftContextRecipientOffsetV1,
          sample.recipient) ||
      !Read(access, context, ck3_12002::kFactionGiftContextPayerOffsetV1,
          sample.puppet_or_actor) ||
      !Read(access, context, kPrisonerReleaseContextSecondaryActorOffset12003,
          secondary_actor) ||
      !Read(access, context, kPrisonerReleaseContextSecondaryRecipientOffset12003,
          secondary_recipient) ||
      !Read(access, context, kPrisonerReleaseContextIntermediaryOffset12003, intermediary) ||
      sample.actor != jailer || sample.recipient != prisoner ||
      sample.puppet_or_actor != jailer || secondary_actor != -1 ||
      secondary_recipient != -1 || intermediary != -1) {
    reason = "option_context_roles_unverified"; return false;
  }
  if (!Read(access, context, kPrisonerReleaseContextOptionDataOffset12003, data) ||
      !Read(access, context, kPrisonerReleaseContextOptionCapacityOffset12003, capacity) ||
      !Read(access, context, kPrisonerReleaseContextOptionCountOffset12003,
          sample.context_option_count) || data == 0 ||
      sample.context_option_count != sample.definition_option_count ||
      capacity < sample.context_option_count) {
    reason = "option_context_count_unexpected"; return false;
  }
  for (std::int32_t i = 0; i < sample.context_option_count; ++i) {
    std::uint8_t selected = 0;
    if (!Read(access, data, static_cast<std::size_t>(i), selected) || selected > 1) {
      reason = "option_selection_unreadable"; return false;
    }
    if (selected != 0) sample.selected_option_mask_bits |= std::uint32_t{1} << i;
  }
  if (sample.selected_option_mask_bits != 0) {
    reason = "option_mask_unexpected"; return false;
  }
  return true;
}

bool ReadSample(const PrisonerReleasePreviewBindings12003 &b,
    const PrisonerReleasePreviewAccess12003 &access, std::uint32_t jailer,
    std::uint32_t prisoner, NativeSample &sample, std::string &reason) {
  if (!ReadCustody(b, access, jailer, prisoner, sample)) {
    reason = "custody_relation_unverified"; return false;
  }
  if (!ReadDefinition(b, access, sample, reason)) return false;
  const auto &c = b.gift.interaction;
  OwnedContext owned(c.destroy);
  void *const context = owned.data();
  if (b.gift.construct_two_role(context, reinterpret_cast<void *>(sample.definition),
          static_cast<std::int32_t>(jailer), static_cast<std::int32_t>(prisoner),
          nullptr, true) != context) {
    reason = "context_construction_unavailable"; return false;
  }
  owned.MarkConstructed();
  b.clear_local_options(context);
  c.refresh(context, true);
  c.finalize(context);
  if (!ReadFinalSelection(access, reinterpret_cast<std::uintptr_t>(context),
          jailer, prisoner, sample, reason)) return false;
  sample.can_send = c.validate(context, nullptr);
  c.evaluate_cost(reinterpret_cast<const std::byte *>(sample.definition) +
      ck3_12002::kFactionGiftDefinitionCostOffsetV1, owned.scope(), sample.costs.data());
  std::uintptr_t trigger = 0;
  if (!Read(access, sample.definition, ck3_12002::kFactionGiftAutoAcceptTriggerOffsetV1,
          trigger)) {
    reason = "auto_accept_unavailable"; return false;
  }
  if (trigger != 0) {
    sample.auto_accept = c.evaluate_trigger(reinterpret_cast<void *>(trigger), owned.scope());
  } else {
    std::uint8_t scalar = 0;
    if (!Read(access, sample.definition, ck3_12002::kFactionGiftAutoAcceptScalarOffsetV1,
            scalar)) {
      reason = "auto_accept_unavailable"; return false;
    }
    sample.auto_accept = scalar != 0;
  }
  if (!sample.auto_accept) { reason = "ordinary_release_auto_accept_false"; return false; }
  return true;
}

} // namespace

PrisonerReleasePreviewBindings12003 BindPrisonerReleasePreview12003(
    std::uintptr_t base, std::string_view actual_sha) noexcept {
  PrisonerReleasePreviewBindings12003 b{};
  if (base == 0 || actual_sha != kExecutableSha256) return b;
  // The actual .3 identity was admitted above. The exact-build reuse manifest
  // preserves these .2 context entries; the .2 binder remains strict.
  b.gift.interaction = ck3_12002::BindContextImage(base, ck3_12002::kExecutableSha256);
  if (!b.gift.interaction.enabled) return b;
  b.module_base = base;
  b.gift.module_base = base;
  b.gift.get_database = reinterpret_cast<ck3_12002::FactionGiftGetDatabaseV1>(
      base + ck3_12002::kFactionGiftDatabaseGetterRvaV1);
  b.gift.stable_hash = reinterpret_cast<ck3_12002::FactionGiftStableHashV1>(
      base + ck3_12002::kFactionGiftStableHashRvaV1);
  b.gift.lookup_definition = reinterpret_cast<ck3_12002::FactionGiftLookupDefinitionV1>(
      base + ck3_12002::kFactionGiftDefinitionLookupRvaV1);
  b.gift.construct_two_role = reinterpret_cast<ck3_12002::FactionGiftConstructTwoRoleContextV1>(
      base + ck3_12002::kFactionGiftConstructTwoRoleContextRvaV1);
  b.get_script_identifier_table = reinterpret_cast<ck3_11906::GetScriptIdentifierTable>(
      base + ck3_12002::kPrisonerGetScriptIdentifierTableRva);
  b.lookup_script_identifier_id = reinterpret_cast<ck3_11906::LookupScriptIdentifierId>(
      base + ck3_12002::kPrisonerLookupScriptIdentifierIdRva);
  b.clear_local_options = reinterpret_cast<void (*)(void *)>(
      base + ck3_12002::kPrisonerClearOptionsRva);
  b.gift.enabled = true;
  b.enabled = true;
  return b;
}

bool ReadPrisonerReleasePreview12003(const PrisonerReleasePreviewBindings12003 &b,
    const PrisonerReleasePreviewAccess12003 &access, std::uint32_t jailer,
    std::uint32_t prisoner, PrisonerReleasePreview12003 &output) noexcept {
  output = {};
  try {
    const auto fail = [&output](std::string_view reason) {
      output.available = false;
      output.unavailable_reason.assign(reason);
      return false;
    };
    if (!HasBindings(b) || access.capture_frame == nullptr || access.read_memory == nullptr)
      return fail("native_bindings_unavailable");
    if (access.current_thread_id == 0 ||
        access.current_thread_id != access.application_main_thread_id)
      return fail("application_main_thread_required");
    if (jailer == 0 || prisoner == 0 || jailer == prisoner) return fail("invalid_roles");
    bridge::PlayerPrisonerFrameV1 before{};
    if (!access.capture_frame(access.context, before)) return fail("frame_unavailable");
    if (!before.paused) return fail("not_paused");
    if (!before.map_ready || !before.played_character_alive ||
        !before.played_character_identity_round_trip || before.public_revision == 0 ||
        before.native_revision == 0 || before.proof_epoch == 0 ||
        static_cast<std::uint32_t>(before.played_character_id) != jailer)
      return fail("player_unavailable");
    NativeSample first{};
    NativeSample second{};
    std::string reason;
    if (!ReadSample(b, access, jailer, prisoner, first, reason) ||
        !ReadSample(b, access, jailer, prisoner, second, reason)) return fail(reason);
    if (first != second) return fail("native_sample_drift");
    bridge::PlayerPrisonerFrameV1 after{};
    if (!access.capture_frame(access.context, after)) return fail("frame_unavailable");
    if (before != after) return fail("frame_drift");
    output.frame = before;
    output.definition_key.assign(kPrisonerReleaseDefinitionKey12003);
    output.definition_stable_hash = static_cast<std::uint32_t>(first.definition_hash);
    output.definition_ordinal = first.definition_ordinal;
    output.actor_character_id = first.actor;
    output.recipient_character_id = first.recipient;
    output.jailer_character_id = jailer;
    output.prisoner_character_id = prisoner;
    output.puppet_or_actor_character_id = first.puppet_or_actor;
    output.can_send = first.can_send;
    output.auto_accept = first.auto_accept;
    output.send_costs_raw = first.costs;
    output.observed_definition_option_count = first.definition_option_count;
    output.observed_context_option_count = first.context_option_count;
    output.selected_option_mask_bits = first.selected_option_mask_bits;
    output.unavailable_reason.clear();
    output.available = true;
    return true;
  } catch (...) {
    output = {};
    output.unavailable_reason = "native_evaluation_unavailable";
    return false;
  }
}

#include "ck3_12003_prisoner_negotiated_preview.inc"

} // namespace xar::ck3_12003

#include "ck3_12003_prisoner_native_kinship.inc"
