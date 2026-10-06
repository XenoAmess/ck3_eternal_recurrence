#include "xar_bridge/ck3_12004_prisoner_ransom_action.hpp"

// Integration dependency: the central actual4 command provider, source-closed
// in d2ced9237c25e758f9380637eaf76e4f02891452.
#include "xar_bridge/ck3_12004_commands.hpp"

#include <array>
#include <cstring>
#include <limits>

#if defined(_WIN32)
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#endif

namespace xar::ck3_12004 {
namespace {

constexpr std::string_view kRansom = "ransom_interaction";
constexpr std::size_t kContextSize = 0x338;
constexpr std::size_t kSendCommandSize = 0x368;
constexpr std::size_t kCopiedContextOffset = 0x20;
constexpr std::size_t kSecondaryVtableOffset = 0x18;
constexpr std::uint32_t kInteractionChannelFlags = 0x0E;

template <typename T>
bool Read(const void *base, std::size_t offset, T &out) noexcept {
  if (base == nullptr || reinterpret_cast<std::uintptr_t>(base) >
                             (std::numeric_limits<std::uintptr_t>::max)() - offset)
    return false;
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(&out, static_cast<const std::byte *>(base) + offset, sizeof(out));
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#endif
}

bool ReadFrame(const PrisonerRansomBindings12004 &bindings,
               game::Snapshot &out) noexcept {
  CoreSnapshotPrefix core{};
  if (!xar::ck3_12004::ReadCoreSnapshot(bindings.interaction.context.core, core))
    return false;
  out = {};
  out.date_raw = core.clock.date_raw;
  out.paused = core.clock.paused;
  out.speed = core.clock.speed;
  out.map_ready = core.map_ready;
  out.has_played_character = core.has_played_character;
  out.played_character_id = core.played_character_id;
  out.played_character_alive = core.played_character_alive;
  return true;
}

} // namespace

PrisonerRansomActionBindings12004 BindPrisonerRansomActionImage12004(
    std::uintptr_t module, std::string_view actual_sha) noexcept {
  PrisonerRansomActionBindings12004 bindings{};
  if (module == 0 || actual_sha != kExecutableSha256) return bindings;
  bindings.quote = BindPrisonerRansomImage12004(module, actual_sha);
  bindings.commands = BindCommandImage12004(module, actual_sha);
  if (!bindings.quote.enabled || !bindings.commands.enabled) return bindings;
  bindings.construct_send_character_interaction_command =
      reinterpret_cast<ck3_12002::MarriageConstructSendInteractionCommand>(
          module + kPrisonerRansomSendConstructorRva12004);
  bindings.send_character_interaction_primary_vtable =
      module + kPrisonerRansomSendPrimaryVtableRva12004;
  bindings.send_character_interaction_secondary_vtable =
      module + kPrisonerRansomSendSecondaryVtableRva12004;
  bindings.module_base = module;
  bindings.enabled = true;
  return bindings;
}

PlayerPrisonerRansomSubmitV1 SubmitPlayerPrisonerRansomPrivateV1(
    const PrisonerRansomActionBindings12004 &bindings, std::uintptr_t module,
    const PlayerPrisonerRansomQuoteV1 &observed,
    std::uint64_t expected_native_revision,
    std::int64_t expected_date_raw) noexcept {
  using Result = PlayerPrisonerRansomSubmitV1;
  const auto &quote = bindings.quote;
  const auto &interaction = quote.interaction;
  if (!bindings.enabled || module == 0 || module != bindings.module_base ||
      !quote.enabled || quote.module_base != module || !observed.available ||
      observed.failure != PlayerPrisonerRansomQuoteFailureV1::none ||
      observed.jailer_character_id <= 0 || observed.payer_character_id <= 0 ||
      observed.prisoner_character_id <= 0 || observed.quoted_gold_raw <= 0 ||
      (observed.selected_option != "gold" &&
       observed.selected_option != "current_gold") ||
      !observed.would_accept_now || observed.recipient_answer_status_raw > 1 ||
      expected_native_revision == 0 || expected_date_raw <= 0 ||
      !bindings.commands.enabled ||
      bindings.commands.command_manager == nullptr ||
      bindings.commands.queue_owned_command == nullptr ||
      bindings.construct_send_character_interaction_command == nullptr ||
      bindings.send_character_interaction_primary_vtable !=
          module + kPrisonerRansomSendPrimaryVtableRva12004 ||
      bindings.send_character_interaction_secondary_vtable !=
          module + kPrisonerRansomSendSecondaryVtableRva12004)
    return Result::unavailable;

  game::Snapshot before{};
  if (!ReadFrame(quote, before) || !before.paused || !before.map_ready ||
      !before.has_played_character || !before.played_character_alive ||
      before.played_character_id != observed.jailer_character_id ||
      before.date_raw != expected_date_raw)
    return Result::unavailable;

  // The mailbox correlates expected_native_revision with its stored quote.
  // At application-main, native roles, final CanSend and amount are reread.
  const auto fresh = xar::ck3_12004::ReadPlayerPrisonerRansomQuotePrivateV1(
      quote, module, observed.jailer_character_id, observed.prisoner_character_id);
  if (!fresh.available || fresh.failure != observed.failure ||
      fresh.jailer_character_id != observed.jailer_character_id ||
      fresh.payer_character_id != observed.payer_character_id ||
      fresh.prisoner_character_id != observed.prisoner_character_id ||
      fresh.selected_option != observed.selected_option ||
      fresh.quoted_gold_raw != observed.quoted_gold_raw ||
      fresh.amount_is_acceptance_time_quote !=
          observed.amount_is_acceptance_time_quote ||
      !fresh.would_accept_now || fresh.recipient_answer_status_raw > 1)
    return Result::quote_changed;

  void *const database = interaction.get_database();
  if (database == nullptr) return Result::unavailable;
  const auto hash = interaction.stable_hash(
      database, kRansom.data(), static_cast<std::uint32_t>(kRansom.size()));
  void *const definition = interaction.lookup_definition(database, hash);
  if (!ValidatePrisonerRansomDefinition12004(quote, definition, hash))
    return Result::unavailable;

  const auto option = observed.selected_option == "gold" ? 2 : 3;
  alignas(8) std::array<std::byte, kContextSize> context_storage{};
  void *const context = context_storage.data();
  if (interaction.context.construct_all_roles(
          context, definition, observed.jailer_character_id,
          observed.payer_character_id, -1, observed.prisoner_character_id,
          -1, nullptr) != context)
    return Result::command_unavailable;
  interaction.clear_local_options(context);
  interaction.select_local_option(context, option);
  const auto context_ok = [&](const void *value) noexcept {
    return ValidatePrisonerRansomSelectedContext12004(value, definition,
                                                    observed);
  };
  if (!context_ok(context) ||
      !interaction.context.validate(context, nullptr)) {
    interaction.context.destroy(context);
    return Result::final_legality_changed;
  }

  game::Snapshot checked{};
  if (!ReadFrame(quote, checked) || checked != before ||
      interaction.get_database() != database ||
      interaction.lookup_definition(database, hash) != definition) {
    interaction.context.destroy(context);
    return Result::quote_changed;
  }

  alignas(8) std::array<std::byte, kSendCommandSize> command_storage{};
  void *const command = command_storage.data();
  void *const copied_context = command_storage.data() + kCopiedContextOffset;
  const auto destroy_copy_if_owned = [&]() noexcept {
    void *copied_definition = nullptr;
    if (Read(copied_context, 0, copied_definition) &&
        copied_definition == definition)
      interaction.context.destroy(copied_context);
  };
  if (bindings.construct_send_character_interaction_command(command, context) !=
      command) {
    destroy_copy_if_owned();
    interaction.context.destroy(context);
    return Result::command_unavailable;
  }
  std::uintptr_t primary = 0;
  std::uintptr_t secondary = 0;
  if (!Read(command, 0, primary) ||
      !Read(command, kSecondaryVtableOffset, secondary) ||
      primary != bindings.send_character_interaction_primary_vtable ||
      secondary != bindings.send_character_interaction_secondary_vtable ||
      !context_ok(copied_context)) {
    destroy_copy_if_owned();
    interaction.context.destroy(context);
    return Result::command_unavailable;
  }

  // SubmitCommandCopy clones through primary+0x40, transfers the game-owned
  // clone to native QueueOwnedCommand, and deletes only residual owned clones.
  const bool submitted = ck3_12002::SubmitCommandCopy(
      bindings.commands, command, kInteractionChannelFlags) ==
      ck3_12002::CommandSubmitResult::submitted;
  destroy_copy_if_owned();
  interaction.context.destroy(context);
  return submitted ? Result::submitted_verification_pending
                   : Result::command_unavailable;
}

} // namespace xar::ck3_12004
