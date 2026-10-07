#include "xar_bridge/ck3_12004_prisoner_release_action.hpp"
#include "xar_bridge/ck3_12004_commands.hpp"

#include <array>

namespace xar::ck3_12004 {
namespace {

constexpr std::size_t kContextBytes = 0x338;
constexpr std::size_t kCommandBytes = 0x368;
constexpr std::size_t kCopiedContextOffset = 0x20;
constexpr std::uint32_t kInteractionChannel = 0x0E;

template <typename T>
bool Read(const PrisonerReleasePreviewAccess12004 &access,
    std::uintptr_t base, std::size_t offset, T &value) noexcept {
  return base != 0 && access.read_memory != nullptr &&
      access.read_memory(access.context, base + offset, &value, sizeof(value));
}

bool Accepted(const PrisonerNegotiatedPreview12004 &terms) noexcept {
  return terms.observation.available && terms.observation.can_send &&
      (terms.observation.auto_accept || (terms.recipient_answer_available &&
          terms.recipient_answer_status_raw <= 1));
}

bool SameTerms(const PrisonerNegotiatedPreview12004 &a,
    const PrisonerNegotiatedPreview12004 &b) noexcept {
  const auto &x = a.observation;
  const auto &y = b.observation;
  // Pump epochs differ between query and submit. Compare the actual selected
  // native terms, while the existing mailbox holds their public/native frame.
  return a.requested_option_mask_bits == b.requested_option_mask_bits &&
      x.definition_key == y.definition_key &&
      x.definition_stable_hash == y.definition_stable_hash &&
      x.definition_ordinal == y.definition_ordinal &&
      x.actor_character_id == y.actor_character_id &&
      x.recipient_character_id == y.recipient_character_id &&
      x.jailer_character_id == y.jailer_character_id &&
      x.prisoner_character_id == y.prisoner_character_id &&
      x.puppet_or_actor_character_id == y.puppet_or_actor_character_id &&
      x.observed_definition_option_count == y.observed_definition_option_count &&
      x.observed_context_option_count == y.observed_context_option_count &&
      x.selected_option_mask_bits == y.selected_option_mask_bits &&
      x.can_send == y.can_send && x.auto_accept == y.auto_accept &&
      x.send_costs_raw == y.send_costs_raw && x.raw_scale == y.raw_scale &&
      a.recipient_answer_available == b.recipient_answer_available &&
      (!a.recipient_answer_available ||
          (a.recipient_acceptance_score_raw == b.recipient_acceptance_score_raw &&
              a.recipient_answer_status_raw == b.recipient_answer_status_raw));
}

bool ContextMatches(const PrisonerReleasePreviewAccess12004 &access,
    const void *value, const void *definition,
    const PrisonerNegotiatedPreview12004 &terms) noexcept {
  const auto address = reinterpret_cast<std::uintptr_t>(value);
  std::uintptr_t observed_definition = 0, options = 0;
  std::uint32_t actor = 0, recipient = 0, effective_actor = 0;
  std::int32_t secondary_actor = 0, secondary_recipient = 0, intermediary = 0;
  std::int32_t count = 0, capacity = 0;
  const auto &o = terms.observation;
  if (!Read(access, address, 0, observed_definition) ||
      observed_definition != reinterpret_cast<std::uintptr_t>(definition) ||
      !Read(access, address, ck3_12002::kFactionGiftContextActorOffsetV1, actor) ||
      !Read(access, address, ck3_12002::kFactionGiftContextRecipientOffsetV1, recipient) ||
      !Read(access, address, ck3_12002::kFactionGiftContextPayerOffsetV1, effective_actor) ||
      !Read(access, address, ck3_12003::kPrisonerReleaseContextSecondaryActorOffset12003,
          secondary_actor) ||
      !Read(access, address, ck3_12003::kPrisonerReleaseContextSecondaryRecipientOffset12003,
          secondary_recipient) ||
      !Read(access, address, ck3_12003::kPrisonerReleaseContextIntermediaryOffset12003,
          intermediary) ||
      actor != o.actor_character_id || recipient != o.recipient_character_id ||
      effective_actor != actor || secondary_actor != -1 || secondary_recipient != -1 ||
      intermediary != -1 ||
      !Read(access, address, ck3_12003::kPrisonerReleaseContextOptionDataOffset12003,
          options) || options == 0 ||
      !Read(access, address, ck3_12003::kPrisonerReleaseContextOptionCapacityOffset12003,
          capacity) ||
      !Read(access, address, ck3_12003::kPrisonerReleaseContextOptionCountOffset12003,
          count) || count != 13 || capacity < count)
    return false;
  std::uint32_t actual_mask = 0;
  for (std::int32_t index = 0; index < count; ++index) {
    std::uint8_t selected = 0;
    if (!Read(access, options, static_cast<std::size_t>(index), selected) || selected > 1)
      return false;
    if (selected != 0) actual_mask |= std::uint32_t{1} << index;
  }
  return actual_mask == terms.requested_option_mask_bits &&
      actual_mask == o.selected_option_mask_bits;
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
  alignas(8) std::array<std::byte, kContextBytes> bytes_{};
  ck3_12002::MarriageDestroyInteractionContext destroy_ = nullptr;
  bool constructed_ = false;
};

std::string Quote(std::string_view value) {
  std::string out = "\"";
  constexpr char hex[] = "0123456789abcdef";
  for (const unsigned char ch : value) {
    if (ch == '"' || ch == '\\') { out += '\\'; out += static_cast<char>(ch); }
    else if (ch < 0x20) { out += "\\u00"; out += hex[ch >> 4]; out += hex[ch & 15]; }
    else out += static_cast<char>(ch);
  }
  return out + '"';
}

} // namespace

PrisonerReleaseActionBindings12004 BindPrisonerReleaseAction12004(
    std::uintptr_t base, std::string_view actual_sha) noexcept {
  PrisonerReleaseActionBindings12004 bindings{};
  bindings.preview = BindPrisonerNegotiatedPreview12004(base, actual_sha);
  bindings.commands = BindCommandImage12004(base, actual_sha);
  if (!bindings.preview.release.enabled || !bindings.commands.enabled) return bindings;
  bindings.construct_send = reinterpret_cast<ck3_12002::MarriageConstructSendInteractionCommand>(
      base + kPrisonerRansomSendConstructorRva12004);
  bindings.primary_vtable = base + kPrisonerRansomSendPrimaryVtableRva12004;
  bindings.secondary_vtable = base + kPrisonerRansomSendSecondaryVtableRva12004;
  bindings.module_base = base;
  bindings.enabled = true;
  return bindings;
}

PrisonerReleaseSubmit12004 SubmitPlayerPrisonerRelease12004(
    const PrisonerReleaseActionBindings12004 &bindings,
    const PrisonerReleasePreviewAccess12004 &access,
    const PrisonerNegotiatedPreview12004 &observed,
    std::uint64_t expected_revision, std::int64_t expected_date) noexcept {
  using Result = PrisonerReleaseSubmit12004;
  const auto &release = bindings.preview.release;
  const auto &native = release.gift.interaction;
  const auto &o = observed.observation;
  try {
    if (!bindings.enabled || bindings.module_base == 0 || !release.enabled ||
        !native.enabled || !bindings.commands.enabled ||
        bindings.commands.command_manager == nullptr ||
        bindings.commands.queue_owned_command == nullptr || bindings.construct_send == nullptr ||
        bindings.primary_vtable != bindings.module_base + kPrisonerRansomSendPrimaryVtableRva12004 ||
        bindings.secondary_vtable != bindings.module_base + kPrisonerRansomSendSecondaryVtableRva12004 ||
        access.capture_frame == nullptr || access.read_memory == nullptr ||
        access.current_thread_id == 0 ||
        access.current_thread_id != access.application_main_thread_id ||
        expected_revision == 0 || o.frame.native_revision != expected_revision ||
        expected_date <= 0 || o.frame.date_raw != expected_date || !Accepted(observed) ||
        observed.requested_option_mask_bits > kPrisonerReleaseAllOptionMask12004 ||
        o.selected_option_mask_bits != observed.requested_option_mask_bits)
      return Result::unavailable;
    bridge::PlayerPrisonerFrameV1 before{};
    if (!access.capture_frame(access.context, before) || !before.paused || !before.map_ready ||
        !before.played_character_alive || !before.played_character_identity_round_trip ||
        before.native_revision != expected_revision || before.date_raw != expected_date ||
        before.played_character_id <= 0 ||
        static_cast<std::uint32_t>(before.played_character_id) != o.jailer_character_id)
      return Result::unavailable;

    PrisonerNegotiatedPreview12004 fresh{};
    fresh.requested_option_mask_bits = observed.requested_option_mask_bits;
    const bool sampled = observed.requested_option_mask_bits == 0 ?
        ReadPrisonerReleasePreview12004(release, access, o.jailer_character_id,
            o.prisoner_character_id, fresh.observation) :
        ReadPrisonerNegotiatedPreview12004(bindings.preview, access, o.jailer_character_id,
            o.prisoner_character_id, observed.requested_option_mask_bits, fresh);
    if (!sampled || !Accepted(fresh) || !SameTerms(observed, fresh))
      return Result::quote_changed;

    void *const database = release.gift.get_database();
    if (database == nullptr) return Result::unavailable;
    const auto key = ck3_12003::kPrisonerReleaseDefinitionKey12003;
    const auto hash = release.gift.stable_hash(database, key.data(),
        static_cast<std::uint32_t>(key.size()));
    void *const definition = release.gift.lookup_definition(database, hash);
    std::int32_t stored_hash = 0, ordinal = -1;
    if (definition == nullptr ||
        !Read(access, reinterpret_cast<std::uintptr_t>(definition),
            ck3_12002::kFactionGiftDefinitionHashOffsetV1, stored_hash) || stored_hash != hash ||
        static_cast<std::uint32_t>(hash) != fresh.observation.definition_stable_hash ||
        !Read(access, reinterpret_cast<std::uintptr_t>(definition),
            ck3_12003::kPrisonerReleaseDefinitionOrdinalOffset12003, ordinal) ||
        ordinal != fresh.observation.definition_ordinal)
      return Result::quote_changed;

    OwnedContext context(native.destroy);
    if (release.gift.construct_two_role(context.data(), definition,
        static_cast<std::int32_t>(o.jailer_character_id),
        static_cast<std::int32_t>(o.prisoner_character_id), nullptr, true) != context.data())
      return Result::command_unavailable;
    context.MarkConstructed();
    release.clear_local_options(context.data());
    for (std::size_t index = 0; index < ck3_12003::kPrisonerReleaseOptionKeys12003.size(); ++index)
      if ((observed.requested_option_mask_bits & (std::uint32_t{1} << index)) != 0)
        bindings.preview.select_local_option(context.data(), static_cast<std::int32_t>(index));
    native.refresh(context.data(), true);
    native.finalize(context.data());
    if (!ContextMatches(access, context.data(), definition, fresh) ||
        !native.validate(context.data(), nullptr))
      return Result::final_legality_changed;
    std::array<std::int64_t, 10> costs{};
    native.evaluate_cost(static_cast<const std::byte *>(definition) +
        ck3_12002::kFactionGiftDefinitionCostOffsetV1, context.scope(), costs.data());
    if (costs != fresh.observation.send_costs_raw) return Result::quote_changed;

    alignas(8) std::array<std::byte, kCommandBytes> command{};
    void *const copy = command.data() + kCopiedContextOffset;
    const auto destroy_copy = [&]() noexcept {
      std::uintptr_t copied_definition = 0;
      if (Read(access, reinterpret_cast<std::uintptr_t>(copy), 0, copied_definition) &&
          copied_definition == reinterpret_cast<std::uintptr_t>(definition))
        native.destroy(copy);
    };
    if (bindings.construct_send(command.data(), context.data()) != command.data()) {
      destroy_copy(); return Result::command_unavailable;
    }
    std::uintptr_t primary = 0, secondary = 0;
    if (!Read(access, reinterpret_cast<std::uintptr_t>(command.data()), 0, primary) ||
        !Read(access, reinterpret_cast<std::uintptr_t>(command.data()), 0x18, secondary) ||
        primary != bindings.primary_vtable || secondary != bindings.secondary_vtable ||
        !ContextMatches(access, copy, definition, fresh)) {
      destroy_copy(); return Result::command_unavailable;
    }
    bridge::PlayerPrisonerFrameV1 checked{};
    if (!access.capture_frame(access.context, checked) || checked != before) {
      destroy_copy(); return Result::quote_changed;
    }
    const bool submitted = ck3_12002::SubmitCommandCopy(bindings.commands,
        command.data(), kInteractionChannel) == ck3_12002::CommandSubmitResult::submitted;
    destroy_copy();
    return submitted ? Result::submitted_verification_pending : Result::command_unavailable;
  } catch (...) {
    return Result::unavailable;
  }
}

std::string SerializePlayerPrisonerReleaseCommandResult12004(
    std::string_view request_id, PrisonerReleaseSubmit12004 result) {
  std::string output = "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":" +
      Quote(request_id);
  if (result == PrisonerReleaseSubmit12004::submitted_verification_pending)
    return output + ",\"ok\":true,\"result\":{\"step\":\"submit-player-prisoner-release-private-v1\","
        "\"accepted\":true,\"status\":\"submitted_verification_pending\"}}";
  return output + ",\"ok\":false,\"error\":\"private release submit unresolved or rejected\"}";
}

} // namespace xar::ck3_12004
