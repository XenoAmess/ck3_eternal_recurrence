// AUTHORED_NOTRUN: one CK3 1.20.0.4 whole-producer compound.
// Fixture-owned memory/callbacks replace only native pointer operands after
// pure exact-build binding. No old fixture main, packet or result is replayed.
#include "xar_bridge/ck3_12004_sway.hpp"
#include "xar_bridge/ck3_12002_sway_mailbox.hpp"
#include "xar_bridge/ck3_12002_sway_outcome_mailbox.hpp"

#include <algorithm>
#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
namespace game = xar::game;
namespace actual4 = xar::ck3_12004;
using namespace xar::ck3_12002;
using namespace xar::ck3_11906;
using namespace xar::bridge;

constexpr std::uintptr_t kModuleBase = 0x140000000;
constexpr std::uint64_t kSnapshotRevision = 7;
constexpr std::int32_t kDateRaw = 53220000;
constexpr std::int32_t kActorId = 0x03000001;
constexpr std::int32_t kTargetId = 0x03000002;
constexpr std::uint32_t kSwayHash = 0x12004001;
constexpr std::uint32_t kBlockerHash = 0x12004002;

template <class T> void Put(void *object, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(T));
}
template <class T> T Load(const void *object, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(T));
  return value;
}
void Check(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}

void *gLocalPlayer = nullptr;
void *gDefinition = nullptr;
void *gActor = nullptr;
void *gRecipient = nullptr;
void *gModifierDatabase = nullptr;
void *gExtension = nullptr;
void *gOpinionGroup = nullptr;
void *gSwayDefinition = nullptr;
void *gBlockerDefinition = nullptr;
std::int32_t gOpinion = -15;
int gContexts = 0, gDestroys = 0, gSends = 0;
int gClones = 0, gQueues = 0, gDeletes = 0, gOpinionCalls = 0;
std::array<std::uintptr_t, 9> gCommandVtable{};
std::uintptr_t gSendSecondaryVtable = 0;

void *LocalPlayer(void *) { return gLocalPlayer; }
void *Construct(void *out, void *definition, std::int32_t actor,
                std::int32_t target, void *extra, bool redirect) {
  Check(definition == gDefinition && actor == kActorId && target == kTargetId &&
        extra == nullptr && !redirect, "native two-role Sway constructor ABI");
  ++gContexts;
  Put(out, 0, definition);
  Put(out, 0x2D8, actor);
  Put(out, 0x2DC, target);
  Put(out, 0x2E0, std::int32_t{-1});
  Put(out, 0x2E4, std::int32_t{-1});
  Put(out, 0x2E8, std::int32_t{-1});
  Put(out, 0x2EC, actor);
  return out;
}
void Refresh(void *, bool full) { Check(full, "native full context refresh"); }
void Finalize(void *) {}
bool Shown(void *) { return true; }
bool Valid(void *, bool first, bool second, void *diagnostics) {
  Check(first && second && diagnostics == nullptr, "native complete validity ABI");
  return true;
}
bool CanSend(void *context, void *diagnostics) {
  Check(diagnostics == nullptr &&
        Load<std::int32_t>(context, 0x2D8) == kActorId &&
        Load<std::int32_t>(context, 0x2DC) == kTargetId,
        "native complete CanSend actor/target");
  return true;
}
void Cost(const void *block, const void *scope, std::int64_t *out) {
  Check(block == static_cast<const std::byte *>(gDefinition) + 0x40 &&
        Load<void *>(static_cast<const std::byte *>(scope) - 8, 0) == gDefinition,
        "native finalized ten-resource evaluator ABI");
  for (int index = 0; index != 10; ++index)
    out[index] = index == 0 ? -20'000 : index * 10'000;
}
void Destroy(void *context) {
  ++gDestroys;
  Put(context, 0, static_cast<void *>(nullptr));
}
void *Send(void *out, const void *context) {
  ++gSends;
  Put(out, 0, reinterpret_cast<std::uintptr_t>(gCommandVtable.data()));
  Put(out, 0x18, gSendSecondaryVtable);
  std::memcpy(static_cast<std::byte *>(out) + 0x20, context, 0x338);
  return out;
}
void **Clone(const void *source, void **out) {
  ++gClones;
  auto *owned = new std::array<std::byte, 0x368>;
  std::memcpy(owned->data(), source, owned->size());
  *out = owned;
  return out;
}
void *Delete(void *owned, std::uint32_t flags) {
  Check(flags == 1, "native scalar deleting destructor flags");
  ++gDeletes;
  delete static_cast<std::array<std::byte, 0x368> *>(owned);
  return nullptr;
}
bool Queue(void *manager, void **owned, std::uint32_t flags) {
  Check(manager == &gQueues && owned != nullptr && *owned != nullptr &&
        flags == 0x0E, "native owning Sway command channel");
  ++gQueues;
  Check(Load<std::int32_t>(*owned, 0x20 + 0x2D8) == kActorId &&
        Load<std::int32_t>(*owned, 0x20 + 0x2DC) == kTargetId,
        "native owning clone preserves actor/target");
  // Leave the cloned pointer owned, exercising SubmitCommandCopy's genuine
  // residual scalar-deleting destructor path.
  return true;
}
std::int32_t Opinion(void *recipient, void *actor) {
  Check(recipient == gRecipient && actor == gActor, "opinion receiver direction");
  ++gOpinionCalls;
  return gOpinion;
}
std::int32_t HashStableKey(void *database, const char *key, std::uint32_t size) {
  Check(database == gModifierDatabase, "fixture-owned modifier database");
  const std::string_view value{key, size};
  if (value == "scheme_sway_opinion") return static_cast<std::int32_t>(kSwayHash);
  if (value == "sway_blocker_opinion") return static_cast<std::int32_t>(kBlockerHash);
  throw std::runtime_error("unexpected dedicated modifier key");
}
void *LookupModifier(void *database, std::uint32_t hash) {
  Check(database == gModifierDatabase, "native modifier lookup database");
  return hash == kSwayHash ? gSwayDefinition :
         hash == kBlockerHash ? gBlockerDefinition : nullptr;
}
void *FindGroup(void *extension, std::uint32_t actor) {
  Check(extension == gExtension && actor == static_cast<std::uint32_t>(kActorId),
        "native active opinion group actor");
  return gOpinionGroup;
}
std::int32_t SumModifier(void *group, void *definition) {
  Check(group == gOpinionGroup && definition == gSwayDefinition,
        "native sum only the present dedicated modifier");
  return 0;
}

void VerifyCoreAddresses(const CoreBindings &core) {
  Check(core.enabled &&
        reinterpret_cast<std::uintptr_t>(core.game_state_slot) ==
            kModuleBase + actual4::kGameStateSlotRva &&
        reinterpret_cast<std::uintptr_t>(core.jomini_state_slot) ==
            kModuleBase + actual4::kJominiStateSlotRva &&
        reinterpret_cast<std::uintptr_t>(core.character_storage_slot) ==
            kModuleBase + actual4::kCharacterStorageSlotRva &&
        reinterpret_cast<std::uintptr_t>(core.get_local_player) ==
            kModuleBase + actual4::kGetLocalPlayerRva,
        "pure actual4 core image addresses");
}
void VerifyBindings(const SwayStateBindings12002 &state,
                    const SwayCommandBindingsV1 &command,
                    const SwayOutcomeBindings &opinion) {
  VerifyCoreAddresses(state.core);
  VerifyCoreAddresses(command.context.core);
  VerifyCoreAddresses(opinion.event_window.events.core);
  VerifyCoreAddresses(opinion.opinion_modifiers.core);
  Check(state.enabled && state.module_base == kModuleBase &&
        state.executable_sha256 == actual4::kExecutableSha256 &&
        command.enabled && command.context.enabled &&
        command.context.commands.enabled && opinion.opinion_modifiers.enabled &&
        opinion.build_version == actual4::kGameVersion,
        "actual4 binder identity retained before synthetic operands");
  Check(state.opinion != nullptr && state.opinion == opinion.target_opinion &&
        command.construct_two_roles != nullptr && command.shown != nullptr &&
        command.valid != nullptr && command.context.validate != nullptr &&
        command.context.commands.queue_owned_command != nullptr &&
        opinion.event_window.hash_stable_key != nullptr &&
        opinion.opinion_modifiers.lookup_modifier != nullptr &&
        opinion.opinion_modifiers.find_group != nullptr &&
        opinion.opinion_modifiers.sum_modifier != nullptr,
        "actual4 independent source binders supply typed native callees");
  Check(state.manager_offset == 0xA5C0 &&
        state.manager_vtable_rva == 0x4779548 &&
        state.storage_vtable_rva == 0x4779838 &&
        state.instance_vtable_rva == 0x47794F8 &&
        state.type_vtable_rva == 0x48B9F30 &&
        reinterpret_cast<std::uintptr_t>(state.opinion) == kModuleBase + 0x28BC470,
        "pure actual4 Sway state source profile");
  const auto &context = command.context;
  Check(reinterpret_cast<std::uintptr_t>(context.commands.command_manager) ==
            kModuleBase + 0x5CC1240 &&
        reinterpret_cast<std::uintptr_t>(context.commands.queue_owned_command) ==
            kModuleBase + 0x37F06D0,
        "pure actual4 owning command foundation addresses");
  Check(reinterpret_cast<std::uintptr_t>(context.interaction_database_slot) ==
            kModuleBase + 0x5C67538 &&
        reinterpret_cast<std::uintptr_t>(context.refresh) == kModuleBase + 0x3078A40 &&
        reinterpret_cast<std::uintptr_t>(context.finalize) == kModuleBase + 0x3078C70 &&
        reinterpret_cast<std::uintptr_t>(context.validate) == kModuleBase + 0x307C020 &&
        reinterpret_cast<std::uintptr_t>(context.destroy) == kModuleBase + 0x3077380 &&
        reinterpret_cast<std::uintptr_t>(context.evaluate_cost) == kModuleBase + 0x310CEC0 &&
        reinterpret_cast<std::uintptr_t>(context.construct_send_command) ==
            kModuleBase + 0x2968150 &&
        context.send_primary_vtable == kModuleBase + 0x448BCF0 &&
        context.send_secondary_vtable == kModuleBase + 0x448BCC0 &&
        reinterpret_cast<std::uintptr_t>(command.construct_two_roles) ==
            kModuleBase + 0x3076C70 &&
        reinterpret_cast<std::uintptr_t>(command.shown) == kModuleBase + 0x3079690 &&
        reinterpret_cast<std::uintptr_t>(command.valid) == kModuleBase + 0x307AB50 &&
        command.definition_primary_vtable == kModuleBase + 0x48C2228 &&
        command.definition_secondary_vtable == kModuleBase + 0x48C2238,
        "pure actual4 Sway command source addresses");
  const auto &modifiers = opinion.opinion_modifiers;
  Check(reinterpret_cast<std::uintptr_t>(opinion.event_window.hash_stable_key) ==
            kModuleBase + 0x3F7E220 &&
        reinterpret_cast<std::uintptr_t>(opinion.target_opinion) ==
            kModuleBase + 0x28BC470 &&
        modifiers.module_base == kModuleBase &&
        reinterpret_cast<std::uintptr_t>(modifiers.modifier_database_slot) ==
            kModuleBase + 0x5D207E0 &&
        reinterpret_cast<std::uintptr_t>(modifiers.read_opinion) ==
            kModuleBase + 0x28BC470 &&
        reinterpret_cast<std::uintptr_t>(modifiers.lookup_modifier) ==
            kModuleBase + 0x25A2EE0 &&
        reinterpret_cast<std::uintptr_t>(modifiers.find_group) ==
            kModuleBase + 0x2949A80 &&
        reinterpret_cast<std::uintptr_t>(modifiers.sum_modifier) ==
            kModuleBase + 0x2596290 &&
        modifiers.modifier_primary_vtable == kModuleBase + 0x48C5380 &&
        modifiers.modifier_secondary_vtable == kModuleBase + 0x48C5348 &&
        modifiers.active_opinion_vtable == kModuleBase + 0x473DE18 &&
        modifiers.temporary_opinion_vtable == kModuleBase + 0x473DDE0 &&
        opinion.scheme_storage_slot == nullptr,
        "pure actual4 adopted independent opinion source addresses");
}

struct World {
  SwayStateBindings12002 source =
      actual4::BindSwayStateImage12004(kModuleBase, actual4::kExecutableSha256);
  SwayCommandBindingsV1 commands =
      actual4::BindSwayCommandImage12004(kModuleBase, actual4::kExecutableSha256);
  SwayOutcomeBindings outcome =
      actual4::BindSwayOutcomeOpinionImage12004(kModuleBase, actual4::kExecutableSha256);
  std::array<std::byte, 0xA8> state{};
  std::array<std::byte, 0x28> jomini{};
  std::array<std::byte, 0x1F8> players{};
  std::array<std::byte, 0x78> local{};
  std::uint8_t tls_initialized = 1;
  std::array<std::byte, 0x21> tls_context{};
  std::vector<std::byte> game;
  std::array<std::byte, 0xE0> entry{};
  std::array<void *, 1> entries{entry.data()};
  std::array<std::byte, 0x30> character_storage{};
  std::array<std::byte, 16 * 0x10> character_slots{};
  std::array<std::array<std::byte, 0x1D8>, 2> characters{};
  std::array<std::byte, 0x78> interaction_database{};
  std::array<std::byte, 0x2760> interaction_definition{};
  std::array<void *, 1> interaction_rows{interaction_definition.data()};
  std::array<std::byte, 0x58> scheme_storage{};
  std::array<std::byte, 16 * 0x10> scheme_slots{};
  std::vector<std::byte> scheme_block = std::vector<std::byte>(0x400 * 0x358);
  std::array<void *, 1> scheme_blocks{scheme_block.data()};
  std::array<std::byte, 0xA60> scheme_type{};
  std::array<std::byte, 0x20> modifier_database{};
  std::array<std::byte, 0x20> opinion_extension{};
  std::array<std::byte, 0x20> opinion_group{};
  std::array<std::byte, 0x10> active_sway_opinion{};
  std::array<void *, 1> opinion_rows{active_sway_opinion.data()};
  std::array<std::array<std::byte, 0x90>, 2> modifier_definitions{};
  std::array<std::array<char, 64>, 2> modifier_keys{};
  void *state_pointer = state.data();
  void *jomini_pointer = jomini.data();
  void *character_storage_pointer = character_storage.data();
  void *interaction_database_pointer = interaction_database.data();
  void *modifier_database_pointer = modifier_database.data();

  World() {
    VerifyBindings(source, commands, outcome);
    game.resize((std::max)(std::size_t{0x23000}, source.manager_offset + 0x30));
    gLocalPlayer = local.data();
    gDefinition = interaction_definition.data();
    gActor = characters[0].data();
    gRecipient = characters[1].data();
    gModifierDatabase = modifier_database.data();
    gExtension = opinion_extension.data();
    gOpinionGroup = opinion_group.data();
    gSwayDefinition = modifier_definitions[0].data();
    gBlockerDefinition = modifier_definitions[1].data();
    Put(tls_context.data(), 0x20, std::uint8_t{1});

    Put(state.data(), actual4::kGameStateDateOffset, kDateRaw);
    Put(state.data(), actual4::kGameStateDataOffset, game.data());
    Put(state.data(), actual4::kGameStateSpeedOffset, std::int32_t{0});
    Put(jomini.data(), actual4::kJominiPlayersOffset, players.data());
    Put(jomini.data(), actual4::kJominiPausedOffset, std::uint8_t{1});
    Put(players.data(), actual4::kPlayersLocalPlayerIdOffset, std::int32_t{0});
    Put(local.data(), actual4::kPlayerIdOffset, std::int32_t{0});
    Put(game.data(), actual4::kPlayerCharacterManagerOffset +
        actual4::kPlayerManagerEntriesOffset, entries.data());
    Put(game.data(), actual4::kPlayerCharacterManagerOffset +
        actual4::kPlayerManagerCountOffset, std::int32_t{1});
    Put(entry.data(), actual4::kPlayerEntryLocalPlayerIdOffset, std::int32_t{0});
    Put(entry.data(), actual4::kPlayerEntryCharacterIdOffset, kActorId);
    Put(character_storage.data(), actual4::kCharacterStorageSlotsOffset,
        character_slots.data());
    Put(character_storage.data(), actual4::kCharacterStorageCapacityOffset,
        std::int32_t{16});
    for (int index = 0; index != 2; ++index) {
      Put(characters[index].data(), actual4::kCharacterFullIdOffset, kActorId + index);
      Put(character_slots.data(), (index + 1) *
          actual4::kCharacterStorageSlotStride + actual4::kCharacterStorageObjectOffset,
          characters[index].data());
    }

    auto core = source.core;
    core.game_state_slot = &state_pointer;
    core.jomini_state_slot = &jomini_pointer;
    core.character_storage_slot = &character_storage_pointer;
    core.get_local_player = &LocalPlayer;
    source.core = core;
    source.opinion = &Opinion;
    auto &context = commands.context;
    context.core = core;
    context.commands.command_manager = &gQueues;
    context.commands.queue_owned_command = &Queue;
    context.interaction_database_slot = &interaction_database_pointer;
    context.refresh = &Refresh;
    context.finalize = &Finalize;
    context.validate = &CanSend;
    context.destroy = &Destroy;
    context.evaluate_cost = &Cost;
    context.construct_send_command = &Send;
    gCommandVtable[0] = reinterpret_cast<std::uintptr_t>(&Delete);
    gCommandVtable[8] = reinterpret_cast<std::uintptr_t>(&Clone);
    context.send_primary_vtable = reinterpret_cast<std::uintptr_t>(gCommandVtable.data());
    gSendSecondaryVtable = context.send_secondary_vtable;
    commands.construct_two_roles = &Construct;
    commands.shown = &Shown;
    commands.valid = &Valid;

    Put(interaction_database.data(), kSwayDatabaseRowsOffset, interaction_rows.data());
    Put(interaction_database.data(), kSwayDatabaseCountOffset, std::int32_t{1});
    Put(interaction_definition.data(), 0, commands.definition_primary_vtable);
    Put(interaction_definition.data(), kSwayDefinitionSecondaryOffset,
        commands.definition_secondary_vtable);
    Put(interaction_definition.data(), 0x10, std::int32_t{5});
    Put(interaction_definition.data(), 0x14, std::uint32_t{0x5783F850});
    static constexpr char interaction_key[] = "sway_interaction";
    Put(interaction_definition.data(), 0x18, static_cast<const char *>(interaction_key));
    Put(interaction_definition.data(), 0x28, std::uint64_t{16});
    Put(interaction_definition.data(), 0x30, std::uint64_t{31});
    Put(interaction_definition.data(), 0x38, std::uint32_t{0x4744624F});

    Put(game.data(), source.manager_offset, source.module_base + source.manager_vtable_rva);
    Put(game.data(), source.manager_offset + 0x20, scheme_storage.data());
    Put(scheme_storage.data(), 0, source.module_base + source.storage_vtable_rva);
    Put(scheme_storage.data(), 8, scheme_blocks.data());
    Put(scheme_storage.data(), 0x20, scheme_slots.data());
    Put(scheme_storage.data(), 0x2C, std::int32_t{16});
    Put(scheme_type.data(), 0, source.module_base + source.type_vtable_rva);
    std::memcpy(scheme_type.data() + 0x18, "sway", 5);
    Put(scheme_type.data(), 0x28, std::uint64_t{4});
    Put(scheme_type.data(), 0x30, std::uint64_t{15});
    Put(scheme_type.data(), 0x38, std::uint32_t{0x4744624F});
    Put(scheme_type.data(), 0xA4E, std::uint8_t{1});

    outcome.event_window.events.core = core;
    outcome.event_window.hash_stable_key = &HashStableKey;
    outcome.target_opinion = &Opinion;
    auto &modifiers = outcome.opinion_modifiers;
    modifiers.core = core;
    modifiers.modifier_database_slot = &modifier_database_pointer;
    modifiers.read_opinion = &Opinion;
    modifiers.lookup_modifier = &LookupModifier;
    modifiers.find_group = &FindGroup;
    modifiers.sum_modifier = &SumModifier;
    const std::array<const char *, 2> keys{"scheme_sway_opinion", "sway_blocker_opinion"};
    for (std::size_t index = 0; index != keys.size(); ++index) {
      auto *definition = modifier_definitions[index].data();
      const auto length = std::strlen(keys[index]);
      std::memcpy(modifier_keys[index].data(), keys[index], length + 1);
      Put(definition, 0, modifiers.modifier_primary_vtable);
      Put(definition, 0x88, modifiers.modifier_secondary_vtable);
      Put(definition, 0x14, index == 0 ? kSwayHash : kBlockerHash);
      Put(definition, 0x18, static_cast<const char *>(modifier_keys[index].data()));
      Put(definition, 0x28, static_cast<std::uint64_t>(length));
      Put(definition, 0x30, std::uint64_t{63});
      Put(definition, 0x38, std::uint32_t{0x4744624F});
    }
    Put(characters[1].data(), 0x1B0, opinion_extension.data());
    Put(opinion_group.data(), 8, opinion_rows.data());
    Put(opinion_group.data(), 0x14, std::int32_t{1});
    Put(active_sway_opinion.data(), 0, modifiers.active_opinion_vtable);
    Put(active_sway_opinion.data(), 8, gSwayDefinition);
  }

  void CreateSwayInstance() {
    auto *scheme = scheme_block.data() + 0x358;
    Put(scheme_slots.data(), 0x10 + 8, scheme);
    Put(scheme, 0, source.module_base + source.instance_vtable_rva);
    Put(scheme, 0x10, std::uint32_t{1});
    Put(scheme, 0x20, scheme_type.data());
    Put(scheme, 0x2C, kActorId);
    Put(scheme, 0x30, std::uint32_t{0});
    Put(scheme, 0x34, kTargetId);
    Put(scheme, 0x78, std::int32_t{355});
    Put(scheme, 0x350, std::int32_t{365});
    Put(scheme_storage.data(), 0x3C, std::int32_t{1});
  }
};

class FrameAdapter final : public game::GameAdapter {
public:
  game::Snapshot frame{};
  DWORD owner = GetCurrentThreadId();
  const game::AdapterDescriptor &descriptor() const noexcept override {
    static const game::AdapterDescriptor value{
        actual4::kAdapterId, actual4::kGameVersion, actual4::kExecutableSha256,
        "offline-sway-12004-whole-producer", {}};
    return value;
  }
  bool enabled() const noexcept override { return true; }
  bool read_snapshot(game::Snapshot &out) const noexcept override {
    if (GetCurrentThreadId() != owner) return false;
    out = frame;
    return true;
  }
  bool submit_set_speed(std::int32_t) const noexcept override { return false; }
  game::SaveCheckpointResult submit_save_checkpoint() const noexcept override { return {}; }
  game::PreviewMoveArmyResult preview_move_army(std::int32_t, std::int32_t) const noexcept override { return {}; }
  bool read_declarable_wars(std::vector<game::DeclarableWarSnapshot> &) const noexcept override { return false; }
#define ABSENT(Result, Name, Params) game::Result Name Params const noexcept override { return game::Result::unavailable; }
  ABSENT(PauseSubmitResult, submit_pause_map, (game::Snapshot *))
  ABSENT(ResumeSubmitResult, submit_resume_map, (game::Snapshot *))
  ABSENT(SelectEventOptionResult, submit_select_event_option, (std::int32_t))
  ABSENT(ReplyPendingInteractionResult, submit_reply_to_pending_interaction, (game::PendingInteractionReply))
  ABSENT(RaiseTroopsResult, submit_raise_troops_default, ())
  ABSENT(MoveArmyResult, submit_move_army, (std::int32_t, std::int32_t))
  ABSENT(DisbandArmyResult, submit_disband_army, (std::int32_t))
  ABSENT(SplitArmyHalfResult, submit_split_army_half, (std::int32_t))
  ABSENT(MergeArmiesResult, submit_merge_armies, (std::int32_t, std::int32_t))
  ABSENT(StartAssaultResult, submit_start_assault, (std::int32_t))
  ABSENT(StopAssaultResult, submit_stop_assault, (std::int32_t))
  ABSENT(ReadDeclarableWarsResult, read_declarable_wars_for_target, (std::int32_t, std::vector<game::DeclarableWarSnapshot> &))
  ABSENT(DeclareWarResult, submit_declare_war, (const game::DeclarableWarSnapshot &))
  ABSENT(ReadArrangeMarriageChoicesResult, read_arrange_marriage_choices, (std::vector<game::ArrangeMarriageChoice> &, game::ArrangeMarriageQueryDiagnostics &))
  ABSENT(ArrangeMarriageResult, submit_arrange_marriage, (const game::ArrangeMarriageChoice &))
  ABSENT(EnforceDemandsResult, submit_enforce_demands, (std::int32_t))
  ABSENT(SurrenderWarResult, submit_surrender_war, (std::int32_t))
  ABSENT(OfferWhitePeaceResult, submit_offer_white_peace, (std::int32_t))
  ABSENT(ReadArmyStrengthsResult, read_army_strengths, (std::vector<game::ArmyStrengthSnapshot> &))
  ABSENT(ReadCombatSimulationInputsResult, read_combat_simulation_inputs, (const game::CombatSimulationInputsRequest &, game::CombatSimulationInputsSnapshot &))
  ABSENT(ReadCombatSimulationInputsV3Result, read_combat_simulation_inputs_v3, (const game::CombatSimulationInputsRequest &, game::CombatSimulationInputsV3Snapshot &))
  ABSENT(ReadWarTerminationOptionsResult, read_war_termination_options, (std::int32_t, game::WarTerminationOptionsSnapshot &))
  ABSENT(ReadWarTerminationTermsResult, read_war_termination_terms, (std::int32_t, game::WarTerminationTermsSnapshot &))
  ABSENT(ReadWarTerminationExitTermsResult, read_war_termination_exit_terms, (std::int32_t, game::WarTerminationExitTermsSnapshot &))
#undef ABSENT
};

template <class Query>
bool ExecuteOwning(Query &query, FrameAdapter &adapter,
                   MainThreadQueryMailboxV1 &mailbox, World &world,
                   std::uint64_t epoch, MainThreadQueryExecutorV1 executor) {
  query.envelope.game = &adapter;
  query.envelope.mailbox = &mailbox;
  query.envelope.expected_snapshot = adapter.frame;
  query.envelope.expected_snapshot_revision = kSnapshotRevision;
  query.envelope.typed_context = &query;
  mailbox.state = MainThreadQueryMailboxStateV1::idle;
  mailbox.executor_submission_enabled = true;
  mailbox.owner_thread_id = GetCurrentThreadId();
  mailbox.paused_owner_verified_pump_epochs =
      kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs;
  if (TrySubmitMainThreadQueryV1(mailbox, executor, &query.envelope,
                               query.envelope.ticket) !=
      MainThreadQuerySubmitResultV1::submitted) return false;
  // The fixture synchronously supplies the owning pump's execution boundary.
  mailbox.state = MainThreadQueryMailboxStateV1::executing;
  MainThreadExecutionStampV1 stamp{};
  stamp.pump_epoch = epoch;
  stamp.thread_id = GetCurrentThreadId();
  stamp.tls_initialized_flag_address =
      reinterpret_cast<std::uintptr_t>(&world.tls_initialized);
  stamp.tls_initialized = world.tls_initialized;
  stamp.tls_context = reinterpret_cast<std::uintptr_t>(world.tls_context.data());
  stamp.tls_main_thread_marker = Load<std::uint8_t>(world.tls_context.data(), 0x20);
  stamp.jomini_state = reinterpret_cast<std::uintptr_t>(world.jomini.data());
  stamp.game_state = reinterpret_cast<std::uintptr_t>(world.state.data());
  stamp.date_raw = kDateRaw;
  stamp.paused = true;
  return executor(&query.envelope, stamp) && query.completed &&
         query.failure.empty() && query.envelope.entered &&
         query.envelope.frame_stable &&
         query.envelope.expected_snapshot_revision == kSnapshotRevision;
}

void Save(const std::filesystem::path &output, const char *name,
          const std::string &packet) {
  Check(!packet.empty(), "genuine whole native serializer emitted packet");
  std::ofstream file(output / name, std::ios::binary);
  file << packet << '\n';
  Check(file.good(), "write whole native packet");
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "one output-directory argument");
    const std::filesystem::path output{argv[1]};
    std::filesystem::create_directories(output);
    World world;
    FrameAdapter adapter;
    adapter.frame.date_raw = kDateRaw;
    adapter.frame.paused = true;
    adapter.frame.speed = 1;
    adapter.frame.player_id = 0;
    adapter.frame.map_ready = true;
    adapter.frame.has_played_character = true;
    adapter.frame.played_character_id = kActorId;
    adapter.frame.played_character_alive = true;
    const auto suffix = std::to_string(kTargetId);

    MainThreadQueryMailboxV1 query_mailbox{};
    query_mailbox.permitted_executor_quinquinquagintary = &ExecuteActiveSwayMailbox12002;
    ActiveSwayMailboxContext12002 query{};
    query.source = world.source;
    query.commands = world.commands;
    query.target = kTargetId;
    Check(ExecuteOwning(query, adapter, query_mailbox, world, 40,
                        &ExecuteActiveSwayMailbox12002) &&
          query.active.row_count == 0 && !query.matching &&
          query.terms.complete_can_send && query.opinion == -15 && gQueues == 0,
          "whole owning empty legal target query");
    const auto target_packet = SerializeActiveSwayEnvelope12002(
        query, "query-active-scheme-sway-target-v1-private-" + suffix,
        "fixture-12004-target");

    MainThreadQueryMailboxV1 submit_mailbox{};
    submit_mailbox.permitted_executor_octoquinquagintary = &ExecuteActiveSwayMailbox12002;
    ActiveSwayMailboxContext12002 submit{};
    submit.source = world.source;
    submit.commands = world.commands;
    submit.target = kTargetId;
    submit.formal = true;
    submit.action_id = "sway-12004-whole-producer";
    submit.expected_capture_epoch = query.active.capture_epoch;
    submit.expected_container_generation = query.active.container_generation;
    submit.expected_opinion = query.opinion;
    Check(ExecuteOwning(submit, adapter, submit_mailbox, world, 41,
                        &ExecuteActiveSwayMailbox12002) &&
          submit.ack.verification_pending && submit.ack.submit_call_count == 1 &&
          submit.ack.pre_capture_epoch > query.active.capture_epoch &&
          submit.ack.pre_container_generation == query.active.container_generation &&
          gQueues == 1 && gClones == 1 && gSends == 1 && gDeletes == 1 &&
          gContexts == gDestroys,
          "whole owning exactly-once pending ACK");
    const auto submit_packet = SerializeActiveSwayEnvelope12002(
        submit, "submit-active-scheme-sway-v1-private-" + suffix,
        "fixture-12004-submit");

    // Only the next synthetic engine boundary creates the matching instance.
    // The pending command ACK itself leaves the original storage empty.
    Check(Load<std::int32_t>(world.scheme_storage.data(), 0x3C) == 0 &&
          submit.ack.verification_pending, "ACK alone is not an instance receipt");
    world.CreateSwayInstance();
    MainThreadQueryMailboxV1 receipt_mailbox{};
    receipt_mailbox.permitted_executor_octoquinquagintary = &ExecuteActiveSwayMailbox12002;
    ActiveSwayMailboxContext12002 receipt{};
    receipt.source = world.source;
    receipt.commands = world.commands;
    receipt.target = kTargetId;
    receipt.formal = true;
    receipt.receipt_mode = true;
    receipt.action_id = submit.action_id;
    receipt.prior_ack = submit.ack;
    Check(ExecuteOwning(receipt, adapter, receipt_mailbox, world, 42,
                        &ExecuteActiveSwayMailbox12002) &&
          receipt.receipt.postcondition_verified &&
          receipt.receipt.scheme_instance_id == 1 &&
          receipt.receipt.scheme_instance_generation == 0 &&
          receipt.receipt.post_capture_epoch > submit.ack.pre_capture_epoch &&
          gQueues == 1,
          "whole owning fresh complete-ID instance receipt");
    const auto receipt_packet = SerializeActiveSwayEnvelope12002(
        receipt, "receipt-active-scheme-sway-v1-private-" + suffix,
        "fixture-12004-receipt");

    gOpinion = 37;
    gOpinionCalls = 0;
    MainThreadQueryMailboxV1 opinion_mailbox{};
    opinion_mailbox.permitted_executor_sway_outcome_opinion12002 = &ExecuteSwayOutcomeMailboxV1;
    SwayOutcomeMailboxContextV1 opinion{};
    opinion.opinion_only = true;
    opinion.bindings = world.outcome;
    opinion.request.expected_revision = kSnapshotRevision;
    opinion.request.actor_character_id = kActorId;
    opinion.request.target_character_id = kTargetId;
    Check(ExecuteOwning(opinion, adapter, opinion_mailbox, world, 43,
                        &ExecuteSwayOutcomeMailboxV1) &&
          opinion.opinion_result.available &&
          opinion.opinion_result.build_version == actual4::kGameVersion &&
          opinion.opinion_result.target_opinion_of_actor == 37 && gOpinionCalls == 2 &&
          opinion.opinion_result.scheme_sway_opinion.observed &&
          opinion.opinion_result.scheme_sway_opinion.present &&
          opinion.opinion_result.scheme_sway_opinion.value == 0 &&
          opinion.opinion_result.sway_blocker_opinion.observed &&
          !opinion.opinion_result.sway_blocker_opinion.present &&
          !opinion.opinion_result.sway_blocker_opinion.value && gQueues == 1,
          "whole owning independent material opinion present-zero/absent-null");
    const auto opinion_packet = SerializeSwayOutcomeOpinionResponseV1(
        opinion.opinion_result, opinion.envelope.expected_snapshot_revision,
        opinion.envelope.execution_stamp.date_raw, "fixture-12004-opinion");

    Save(output, "target_query.json", target_packet);
    Save(output, "submit_ack.json", submit_packet);
    Save(output, "instance_receipt.json", receipt_packet);
    Save(output, "outcome_opinion.json", opinion_packet);
    const std::string manifest =
        "{\"schema\":\"xar.ck3.sway-12004-whole-producer-manifest-v1\","
        "\"qualification\":\"offline synthetic world; not live\","
        "\"compound_cases\":1,\"whole_native_packets\":4,"
        "\"game_version\":\"" + std::string(actual4::kGameVersion) +
        "\",\"exe_sha256\":\"" + std::string(actual4::kExecutableSha256) +
        "\",\"steam_build_id\":\"" + std::string(actual4::kSteamBuildId) +
        "\",\"module_base\":" + std::to_string(world.source.module_base) +
        ",\"snapshot_revision\":" + std::to_string(kSnapshotRevision) +
        ",\"date_raw\":" + std::to_string(kDateRaw) +
        ",\"actor_character_id\":" + std::to_string(kActorId) +
        ",\"target_character_id\":" + std::to_string(kTargetId) +
        ",\"pump_epochs\":{\"target_query\":40,\"submit_ack\":41,"
        "\"instance_receipt\":42,\"outcome_opinion\":43},"
        "\"producer_paths\":{\"target_query\":\"ExecuteActiveSwayMailbox12002+SerializeActiveSwayEnvelope12002\","
        "\"submit_ack\":\"ExecuteActiveSwayMailbox12002+SerializeActiveSwayEnvelope12002\","
        "\"instance_receipt\":\"ExecuteActiveSwayMailbox12002+SerializeActiveSwayEnvelope12002\","
        "\"outcome_opinion\":\"ExecuteSwayOutcomeMailboxV1+SerializeSwayOutcomeOpinionResponseV1\"},"
        "\"packets\":{\"target_query\":\"target_query.json\","
        "\"submit_ack\":\"submit_ack.json\",\"instance_receipt\":\"instance_receipt.json\","
        "\"outcome_opinion\":\"outcome_opinion.json\"}}";
    Save(output, "manifest.json", manifest);
    std::cout << "PASS one actual4 whole-producer compound: four native packets and manifest\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL " << error.what() << '\n';
    return 1;
  }
}
