// Fresh offline FIRST: actual4 owned-custody collection and release observers,
// action submit, real SubmitCommandCopy ownership, and production whole wires.
// The actor ID identifies the allowed campaign entry; the prisoner is entirely
// synthetic. No natural capture, live release, or on-accept effect is claimed.
#include "xar_bridge/ck3_12004_prisoner_collection_result.hpp"
#include "xar_bridge/ck3_12004_prisoner_release_action.hpp"
#include "xar_bridge/game_adapter.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <string_view>
#include <unordered_map>
#include <vector>

#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>

namespace {
namespace native = xar::ck3_12004;
namespace portable = xar::ck3_12003;
namespace bridge = xar::bridge;
namespace ownership = xar::ck3_12002;

constexpr std::uint32_t kActor = 29829, kPrisoner = 0x03000002;
constexpr std::int32_t kHash = 0x51520413, kOrdinal = 186, kDate = 1220410;
constexpr std::uint64_t kRevision = 811, kProofEpoch = 91;
constexpr std::uint32_t kHookMask = 1U << 3;
constexpr std::size_t kContextSize = 0x338, kCommandSize = 0x368;
constexpr std::array<std::int64_t, 10> kCosts{
    100001, 200002, 300003, 400004, 500005,
    600006, 700007, 800008, 900009, 1000010};
constexpr std::string_view kQueryStep =
    "query-player-prisoner-collection-private-v1";
using Options = std::array<std::uint8_t, 13>;
using Command = std::array<std::byte, kCommandSize>;
using Result = native::PrisonerReleaseSubmit12004;

void Require(bool value, std::string_view message) {
  if (!value) throw std::runtime_error(std::string(message));
}
template <class T> void Put(void *base, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(base) + offset, &value, sizeof(value));
}
template <class T> T Get(const void *base, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(base) + offset, sizeof(value));
  return value;
}
enum class Case { all_off_pending, gain_hook_pending, gain_hook_native_false,
                  gain_hook_copied_mask_changed, gain_hook_native_refused };
struct Scene;
Scene *current = nullptr;
void *Database();
std::int32_t Hash(void *, const char *, std::uint32_t);
void *Lookup(void *, std::int32_t);
std::int32_t *Identifier(void *, std::int32_t *, const void *);
void *Construct(void *, void *, std::int32_t, std::int32_t, void *, bool);
void Clear(void *);
void Select(void *, std::int32_t);
void Refresh(void *, bool);
void Finalize(void *);
bool CanSend(void *, void *);
void Cost(const void *, const void *, std::int64_t *);
bool AutoAccept(void *, const void *);
std::int64_t *Score(void *, std::int64_t *);
std::uint8_t Answer(void *, std::uint8_t, std::uint8_t, void *, void *);
void DestroyContext(void *);
void *ConstructSend(void *, const void *);
void **Clone(const void *, void **);
void *Delete(void *, std::uint32_t);
bool Queue(void *, void **, std::uint32_t);
bool Capture(void *, bridge::PlayerPrisonerFrameV1 &) noexcept;
bool ReadMemory(void *, std::uintptr_t, void *, std::size_t) noexcept;
void *PrimaryTitle(void *);

// The fixture's vtable arena intentionally requires pointer-aligned storage.
// MSVC C4324 reports its expected padding; keep the production /WX unchanged.
#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4324)
#endif
struct Scene {
  Case kind;
  // This small table arena retains actual module+RVA vptr identities. Function
  // callbacks model fixture-owned native objects; SubmitCommandCopy is real.
  alignas(8) std::array<std::byte, 0x100> tables{};
  std::array<std::byte, 0x30> storage{};
  std::vector<std::byte> slots = std::vector<std::byte>((kActor + 1) * 0x10);
  std::array<std::byte, 0x1D0> actor{}, prisoner{};
  std::array<std::byte, 0x358> land{};
  std::array<std::byte, 0x290> extension{};
  std::array<std::byte, 8> relation{};
  std::array<std::uint32_t, 1> prisoners{kPrisoner};
  std::array<std::byte, 0x2800> definition{};
  std::array<std::byte, 13 * 0x730> option_rows{};
  std::uint8_t auto_trigger = 1;
  bridge::PlayerPrisonerFrameV1 frame{
      kRevision, kRevision, kProofEpoch, kDate, true, true,
      static_cast<std::int32_t>(kActor), true, true};
  native::PrisonerReleaseActionBindings12004 bindings{};
  std::unordered_map<void *, std::unique_ptr<Options>> contexts;
  std::vector<std::pair<std::uintptr_t, std::size_t>> readable;
  void *queued = nullptr;
  void *source_command = nullptr;
  unsigned created_contexts = 0, destroyed_contexts = 0, flag_reads = 0;
  unsigned selected_calls = 0, score_reads = 0, answer_reads = 0;
  unsigned send_copies = 0, clone_calls = 0, queue_calls = 0, deleted_commands = 0;
  std::uint32_t queued_mask = 0;

  std::uintptr_t Module() const {
    return reinterpret_cast<std::uintptr_t>(tables.data() + 0x30) -
        native::kPrisonerRansomSendPrimaryVtableRva12004;
  }
  template <class T> void Register(T &region) {
    readable.emplace_back(reinterpret_cast<std::uintptr_t>(region.data()),
        sizeof(typename T::value_type) * region.size());
  }
  Options &Selection(const void *context) {
    const auto found = contexts.find(const_cast<void *>(context));
    Require(found != contexts.end(), "selected bytes have a unique live context owner");
    return *found->second;
  }
  std::uint32_t Mask(const void *context) {
    const auto &selected = Selection(context);
    std::uint32_t mask = 0;
    for (std::size_t i = 0; i < selected.size(); ++i) {
      Require(selected[i] <= 1, "all thirteen copied selection bytes are boolean");
      if (selected[i]) mask |= 1U << i;
    }
    return mask;
  }
  void AddContext(void *context, std::unique_ptr<Options> selected) {
    Require(contexts.emplace(context, std::move(selected)).second,
        "every context owns one independent thirteen-option allocation");
    Put(context, 0x300, contexts.at(context)->data());
    Put(context, 0x308, std::int32_t{13});
    Put(context, 0x30C, std::int32_t{13});
    ++created_contexts;
  }
  void CopyContext(void *destination, const void *source) {
    auto selected = std::make_unique<Options>(Selection(source));
    std::memcpy(destination, source, kContextSize);
    AddContext(destination, std::move(selected));
    Require(Get<void *>(destination, 0x300) != Get<void *>(source, 0x300),
        "native send/clone callbacks perform a deep option copy");
  }
  explicit Scene(Case value) : kind(value) {
    current = this;
    Put(storage.data(), 0x20, slots.data());
    Put(storage.data(), 0x2C, static_cast<std::int32_t>(kActor + 1));
    Put(slots.data(), kActor * 0x10 + 8, actor.data());
    Put(slots.data(), 2 * 0x10 + 8, prisoner.data());
    Put(actor.data(), 0x18, kActor); Put(prisoner.data(), 0x18, kPrisoner);
    Put(actor.data(), 0x158, std::int32_t{-1});
    Put(prisoner.data(), 0x158, std::int32_t{-1});
    Put(actor.data(), 0x1C0, land.data());
    Put(land.data(), 0xD8, prisoners.data()); Put(land.data(), 0xE4, std::int32_t{1});
    Put(prisoner.data(), 0x1B0, extension.data());
    Put(extension.data(), 0x288, relation.data()); Put(relation.data(), 0, kActor);
    Put(definition.data(), 0x10, kOrdinal); Put(definition.data(), 0x14, kHash);
    const auto key = portable::kPrisonerReleaseDefinitionKey12003;
    Put(definition.data(), 0x18, key.data());
    Put(definition.data(), 0x28, static_cast<std::uint64_t>(key.size()));
    Put(definition.data(), 0x30, static_cast<std::uint64_t>(key.size()));
    Put(definition.data(), 0x2258, option_rows.data());
    Put(definition.data(), 0x2264, std::int32_t{13});
    Put(definition.data(), 0x2290, &auto_trigger);
    for (std::size_t i = 0; i < 13; ++i)
      Put(option_rows.data(), i * 0x730 + 0x368, static_cast<std::int32_t>(1000 + i));

    bindings = native::BindPrisonerReleaseAction12004(Module(), native::kExecutableSha256);
    Require(bindings.enabled && bindings.preview.release.enabled && bindings.commands.enabled &&
        reinterpret_cast<std::uintptr_t>(bindings.construct_send) ==
            Module() + native::kPrisonerRansomSendConstructorRva12004 &&
        bindings.primary_vtable == Module() + native::kPrisonerRansomSendPrimaryVtableRva12004 &&
        bindings.secondary_vtable == Module() + native::kPrisonerRansomSendSecondaryVtableRva12004,
        "actual4 production factory supplies admitted context/command/typed-send identities");
    auto &preview = bindings.preview;
    auto &release = preview.release;
    release.gift.get_database = &Database; release.gift.stable_hash = &Hash;
    release.gift.lookup_definition = &Lookup; release.gift.construct_two_role = &Construct;
    release.get_script_identifier_table = &Database;
    release.lookup_script_identifier_id = &Identifier; release.clear_local_options = &Clear;
    auto &context = release.gift.interaction;
    context.refresh = &Refresh; context.finalize = &Finalize; context.validate = &CanSend;
    context.evaluate_cost = &Cost; context.evaluate_trigger = &AutoAccept;
    context.recipient_answer_score = &Score; context.destroy = &DestroyContext;
    preview.select_local_option = &Select; preview.evaluate_answer = &Answer;
    bindings.construct_send = &ConstructSend;
    bindings.commands.command_manager = this; bindings.commands.queue_owned_command = &Queue;
    Put(tables.data(), 0x30, &Delete); Put(tables.data(), 0x70, &Clone);
    Register(storage); Register(slots); Register(actor); Register(prisoner); Register(land);
    Register(extension); Register(relation); Register(prisoners); Register(definition); Register(option_rows);
    readable.emplace_back(reinterpret_cast<std::uintptr_t>(key.data()), key.size());
  }
  native::PrisonerReleasePreviewAccess12004 PreviewAccess() {
    return {8, 8, this, &Capture, &ReadMemory};
  }
  bridge::PlayerPrisonerCollectionAccessV1 CollectionAccess() {
    bridge::PlayerPrisonerCollectionAccessV1 access{};
    access.exact_build_admitted = true; access.admitted_executable_sha256 = native::kExecutableSha256;
    access.module_base = Module(); access.current_thread_id = access.application_main_thread_id = 8;
    access.read_lineage = access.read_child_relation = access.read_title_tier = access.read_dread = true;
    access.context = this; access.capture_frame = &Capture; access.read_memory = &ReadMemory;
    access.get_primary_title = &PrimaryTitle;
    return access;
  }
};
#ifdef _MSC_VER
#pragma warning(pop)
#endif

bool Capture(void *opaque, bridge::PlayerPrisonerFrameV1 &out) noexcept {
  out = static_cast<Scene *>(opaque)->frame; return true;
}
bool ReadMemory(void *opaque, std::uintptr_t address, void *out, std::size_t size) noexcept {
  auto &scene = *static_cast<Scene *>(opaque);
  if (!address || !out || !size) return false;
  if (address == scene.Module() + native::kCharacterStorageSlotRva && size == sizeof(void *)) {
    void *storage = scene.storage.data(); std::memcpy(out, &storage, size); return true;
  }
  if ((address == scene.Module() + 0x5C67570 ||
       address == scene.Module() + native::kPrisonerTitleFallbackSlotRva12004) &&
      size == sizeof(void *)) {
    void *empty = nullptr; std::memcpy(out, &empty, size); return true;
  }
  const auto copy = [&](std::uintptr_t start, std::size_t length) {
    if (address < start || address - start > length || size > length - (address - start))
      return false;
    std::memcpy(out, reinterpret_cast<const void *>(address), size); return true;
  };
  for (const auto &[start, length] : scene.readable)
    if (copy(start, length)) return true;
  if (scene.source_command &&
      copy(reinterpret_cast<std::uintptr_t>(scene.source_command), kCommandSize)) return true;
  for (const auto &[context, selected] : scene.contexts)
    if (copy(reinterpret_cast<std::uintptr_t>(context), kContextSize) ||
        copy(reinterpret_cast<std::uintptr_t>(selected->data()), selected->size())) return true;
  return false;
}
void *PrimaryTitle(void *character) {
  Require(character == current->prisoner.data(), "title query reads the selected synthetic captive");
  return nullptr;
}
void *Database() { return current; }
std::int32_t Hash(void *database, const char *key, std::uint32_t size) {
  Require(database == current &&
      std::string_view(key, size) == portable::kPrisonerReleaseDefinitionKey12003,
      "loaded stock release definition key");
  return kHash;
}
void *Lookup(void *database, std::int32_t hash) {
  Require(database == current && hash == kHash, "release definition identity");
  return current->definition.data();
}
std::int32_t *Identifier(void *table, std::int32_t *out, const void *view) {
  Require(table == current && out && view, "loaded script identifier view");
  const auto size = Get<std::int32_t>(view, 8);
  Require(size >= 0, "loaded option key size");
  const auto key = std::string_view(Get<const char *>(view, 0), static_cast<std::size_t>(size));
  for (std::size_t i = 0; i < portable::kPrisonerReleaseOptionKeys12003.size(); ++i)
    if (key == portable::kPrisonerReleaseOptionKeys12003[i]) {
      *out = static_cast<std::int32_t>(1000 + i); ++current->flag_reads; return out;
    }
  Require(false, "all thirteen loaded release flags have their stock identities"); return nullptr;
}
void *Construct(void *context, void *definition, std::int32_t actor,
    std::int32_t recipient, void *extras, bool redirect) {
  Require(definition == current->definition.data() && actor == static_cast<std::int32_t>(kActor) &&
      recipient == static_cast<std::int32_t>(kPrisoner) && !extras && redirect,
      "actual two-role release constructor inputs");
  Put(context, 0, definition); Put(context, 0x2D8, actor); Put(context, 0x2DC, recipient);
  Put(context, 0x2E0, std::int32_t{-1}); Put(context, 0x2E4, std::int32_t{-1});
  Put(context, 0x2E8, std::int32_t{-1}); Put(context, 0x2EC, actor);
  current->AddContext(context, std::make_unique<Options>()); return context;
}
void Clear(void *context) { current->Selection(context).fill(0); }
void Select(void *context, std::int32_t ordinal) {
  Require(ordinal >= 0 && ordinal < 13, "selection uses the actual thirteen-option index");
  current->Selection(context)[static_cast<std::size_t>(ordinal)] = 1; ++current->selected_calls;
}
void Refresh(void *context, bool recompute) {
  Require(recompute && current->contexts.count(context) == 1, "refresh the owning context");
}
void Finalize(void *context) {
  Require(current->contexts.count(context) == 1, "finalize the owning context");
}
bool CanSend(void *context, void *error) {
  Require(!error && current->contexts.count(context) == 1, "final CanSend owns the selected context");
  return current->kind != Case::gain_hook_native_false;
}
void Cost(const void *cost, const void *scope, std::int64_t *out) {
  auto *context = const_cast<std::byte *>(static_cast<const std::byte *>(scope) - 8);
  Require(cost == current->definition.data() + 0x40 && current->contexts.count(context) == 1,
      "all ten send costs use the current finalized native scope");
  std::memcpy(out, kCosts.data(), sizeof(kCosts));
}
bool AutoAccept(void *trigger, const void *scope) {
  auto *context = const_cast<std::byte *>(static_cast<const std::byte *>(scope) - 8);
  Require(trigger == &current->auto_trigger, "current native autoaccept trigger");
  return current->Mask(context) == 0;
}
std::int64_t *Score(void *context, std::int64_t *out) {
  Require(out && current->Mask(context) == kHookMask, "native answer score retains gain_hook");
  *out = current->kind == Case::gain_hook_native_refused ? -3100001 : 2700003;
  ++current->score_reads; return out;
}
std::uint8_t Answer(void *context, std::uint8_t mode, std::uint8_t flag, void *a, void *b) {
  Require(current->Mask(context) == kHookMask && mode == 1 && flag == 1 && !a && !b,
      "native selected release answer ABI");
  ++current->answer_reads;
  return current->kind == Case::gain_hook_native_refused ? 2 : 1;
}
void DestroyContext(void *context) {
  Require(current->contexts.erase(context) == 1, "each native context allocation is destroyed once");
  if (current->source_command &&
      context == static_cast<std::byte *>(current->source_command) + 0x20)
    current->source_command = nullptr;
  Put(context, 0, static_cast<void *>(nullptr)); Put(context, 0x300, static_cast<void *>(nullptr));
  ++current->destroyed_contexts;
}
void *ConstructSend(void *command, const void *context) {
  Require(!current->source_command, "one borrowed typed send command source at a time");
  current->source_command = command;
  Put(command, 0, current->bindings.primary_vtable);
  Put(command, 0x18, current->bindings.secondary_vtable);
  void *copy = static_cast<std::byte *>(command) + 0x20;
  current->CopyContext(copy, context); ++current->send_copies;
  if (current->kind == Case::gain_hook_copied_mask_changed) current->Selection(copy)[5] = 1;
  return command;
}
void **Clone(const void *source, void **out) {
  Require(out != nullptr, "native clone return storage");
  auto *clone = new Command{};
  std::memcpy(clone->data(), source, clone->size());
  current->CopyContext(clone->data() + 0x20, static_cast<const std::byte *>(source) + 0x20);
  ++current->clone_calls; *out = clone; return out;
}
void *Delete(void *command, std::uint32_t flags) {
  Require(flags == 1, "native scalar deleting destructor ownership flag");
  DestroyContext(static_cast<std::byte *>(command) + 0x20);
  delete static_cast<Command *>(command); ++current->deleted_commands; return nullptr;
}
bool Queue(void *manager, void **owned, std::uint32_t flags) {
  Require(manager == current && flags == 0x0E && owned && *owned && !current->queued,
      "real SubmitCommandCopy transfers one owning clone to the native interaction channel");
  auto *context = static_cast<std::byte *>(*owned) + 0x20;
  Require(Get<void *>(context, 0) == current->definition.data() &&
      Get<std::uint32_t>(context, 0x2D8) == kActor &&
      Get<std::uint32_t>(context, 0x2DC) == kPrisoner &&
      Get<std::uint32_t>(context, 0x2EC) == kActor &&
      Get<std::int32_t>(context, 0x30C) == 13,
      "queued clone keeps loaded definition, current roles and thirteen options");
  current->queued_mask = current->Mask(context);
  current->queued = *owned; *owned = nullptr; ++current->queue_calls; return true;
}

void Write(const std::filesystem::path &path, const std::string &wire) {
  std::ofstream out(path, std::ios::binary); out << wire << '\n';
  Require(out.good(), "write fresh complete native FIRST artifact");
}
std::string HelloWire() {
  // HelloFrame itself is translation-unit-private in bridge.cpp. This offline
  // shape follows it and takes all game identity/capability values from the
  // same production descriptor. It is not an in-game connection handshake.
  const auto &descriptor = xar::game::PreferredAdapterDescriptor();
  Require(descriptor.game_version == native::kGameVersion &&
      descriptor.executable_sha256 == native::kExecutableSha256 &&
      descriptor.adapter_id == native::kAdapterId, "genuine current4 production hello descriptor");
#if defined(XAR_BRIDGE_VERSION)
  constexpr std::string_view version = XAR_BRIDGE_VERSION;
#else
  constexpr std::string_view version = "0.1.0";
#endif
  std::string wire = "{\"type\":\"hello\",\"protocol_version\":1,\"bridge_version\":\"" +
      std::string(version) + "\",\"pid\":" + std::to_string(GetCurrentProcessId()) +
      ",\"session_generation\":0,\"connection_generation\":1,"
      "\"architecture\":\"x86_64-windows-msvc\",\"expected_ck3_version\":\"" +
      std::string(descriptor.game_version) + "\",\"expected_ck3_sha256\":\"" +
      std::string(descriptor.executable_sha256) + "\",\"game_adapter_id\":\"" +
      std::string(descriptor.adapter_id) + "\",\"game_adapter_status\":\"ready\","
      "\"ck3_build_match\":true,\"capabilities\":[\"bridge.identity\","
      "\"bridge.heartbeat\",\"bridge.ping\"";
  for (const auto capability : descriptor.capabilities) wire += ",\"" + std::string(capability) + '"';
  return wire + "]}";
}
std::string SnapshotWire(const Scene &scene) {
  return "{\"type\":\"state_snapshot\",\"protocol_version\":1,\"snapshot_id\":\"native:" +
      std::to_string(scene.frame.native_revision) + "\",\"revision\":" +
      std::to_string(scene.frame.native_revision) +
      ",\"state\":{\"phase\":\"map_hud\",\"date\":\"synthetic:release-action12004\","
      "\"date_raw\":" + std::to_string(scene.frame.date_raw) +
      ",\"speed\":1,\"paused\":true,\"map_ready\":true,\"history\":[],"
      "\"active_event\":null,\"pending_character_interaction\":null,"
      "\"played_character\":{\"character_id\":29829,\"alive\":true},"
      "\"one_life_settlement\":null,\"active_wars\":[],\"player_armies\":[]}}";
}
void Emit(Case kind, std::string_view name, const std::filesystem::path &directory) {
  Scene scene(kind);
  bridge::PlayerPrisonerCollectionSnapshotV1 collection{};
  Require(native::ReadPlayerPrisonerCollectionV1(scene.CollectionAccess(), collection) &&
      collection.available && collection.collection_complete && collection.returned_count == 1 &&
      collection.rows[0].full_character_id == kPrisoner && collection.rows[0].jailer_character_id == kActor,
      "actual4 whole collection resolves synthetic full ID and independently verifies player custody");
  std::array<native::PrisonerReleasePreview12004, bridge::kPlayerPrisonerMaximumRowsV1> releases{};
  const auto access = scene.PreviewAccess();
  Require(native::ReadPrisonerReleasePreview12004(scene.bindings.preview.release, access,
      kActor, kPrisoner, releases[0]), "actual4 all-off observer returns native true or false CanSend");
  std::array<native::PrisonerNegotiatedPreview12004, bridge::kPlayerPrisonerMaximumRowsV1> negotiated{};
  const auto requested = kind == Case::all_off_pending ? 0U : kHookMask;
  native::PrisonerNegotiatedPreview12004 observed{};
  if (!requested) observed.observation = releases[0];
  else {
    Require(native::ReadPrisonerNegotiatedCollectionRow12004(scene.bindings.preview, access,
        collection, 0, requested, negotiated), "actual4 selected-row negotiated observer");
    observed = negotiated[0];
  }
  const bool sendable = kind != Case::gain_hook_native_false;
  Require(observed.observation.available && observed.observation.frame == collection.frame &&
      observed.observation.can_send == sendable &&
      observed.observation.observed_definition_option_count == 13 &&
      observed.observation.observed_context_option_count == 13 &&
      observed.observation.selected_option_mask_bits == requested &&
      observed.observation.send_costs_raw == kCosts && scene.contexts.empty(),
      "observed frame, final gate, selected mask and ten costs come from real native readers");
  if (requested && sendable)
    Require(observed.recipient_answer_available && observed.recipient_answer_status_raw ==
        (kind == Case::gain_hook_native_refused ? 2 : 1), "actual native conditional recipient answer");
  if (!sendable)
    Require(!observed.recipient_answer_available && scene.score_reads == 0 && scene.answer_reads == 0,
        "false native CanSend does not invent an answer");

  std::array<native::PlayerPrisonerRansomQuoteV1, bridge::kPlayerPrisonerMaximumRowsV1> quotes{};
  for (auto &quote : quotes) quote.failure = native::PlayerPrisonerRansomQuoteFailureV1::not_evaluated;
  quotes[0].failure = native::PlayerPrisonerRansomQuoteFailureV1::role_unavailable;
  const auto query = native::SerializePrisonerCollectionCommandResult12004(
      "fixture-release-query-" + std::string(name), kQueryStep, 1, collection.frame.proof_epoch,
      collection.frame.native_revision, collection, quotes, true, &releases, nullptr,
      requested ? &negotiated : nullptr);
  Require(!query.empty() && query.find("\"type\":\"command_result\"") != std::string::npos,
      "production actual4 whole collection command_result formatter");
  const auto submitted = native::SubmitPlayerPrisonerRelease12004(scene.bindings, access,
      observed, collection.frame.native_revision, collection.frame.date_raw);
  const bool pending = kind == Case::all_off_pending || kind == Case::gain_hook_pending;
  const Result expected = pending ? Result::submitted_verification_pending :
      kind == Case::gain_hook_copied_mask_changed ? Result::command_unavailable : Result::unavailable;
  Require(submitted == expected, "production action returns the expected queue-only disposition");
  const auto ack = native::SerializePlayerPrisonerReleaseCommandResult12004(
      "fixture-release-action-" + std::string(name), submitted);
  Require(!ack.empty() && ack.find("material_result") == std::string::npos,
      "production full action ACK makes no material outcome claim");
  if (pending) {
    Require(scene.send_copies == 1 && scene.clone_calls == 1 && scene.queue_calls == 1 &&
        scene.deleted_commands == 0 && scene.contexts.size() == 1 && scene.queued_mask == requested &&
        ack.find("\"status\":\"submitted_verification_pending\"") != std::string::npos,
        "real SubmitCommandCopy transfers the complete requested mask and leaves queue verification pending");
    auto *queued_context = static_cast<std::byte *>(scene.queued) + 0x20;
    Require(scene.Mask(queued_context) == requested,
        "owned queued selection survives destruction of original and send-copy contexts");
    Require(ownership::DestroyOwnedCommand(scene.queued) && !scene.queued,
        "real command ownership helper destroys only the retained fixture-owned clone");
  } else {
    Require(scene.clone_calls == 0 && scene.queue_calls == 0 && !scene.queued,
        "native refusal, native false CanSend and copy mismatch never reach the queue");
    Require(scene.send_copies == (kind == Case::gain_hook_copied_mask_changed ? 1U : 0U),
        "copy mismatch is detected after constructor; other refusal branches precede it");
  }
  Require(scene.contexts.empty() && scene.created_contexts == scene.destroyed_contexts,
      "all observed, fresh, source, copied and cloned native contexts end exactly once");
  const std::string result_name = pending ? "submitted_verification_pending" :
      kind == Case::gain_hook_copied_mask_changed ? "command_unavailable" : "unavailable";
  const std::string prefix(name);
  Write(directory / (prefix + "-query.json"), query);
  Write(directory / (prefix + "-ack.json"), ack);
  Write(directory / (prefix + ".json"),
      "{\"scenario\":\"" + prefix + "\",\"hello\":" + HelloWire() +
      ",\"before_snapshot\":" + SnapshotWire(scene) +
      ",\"before_collection\":" + query + ",\"command_result\":" + ack +
      ",\"native_expectations\":{\"submit_result\":\"" + result_name +
      "\",\"requested_option_mask_bits\":" + std::to_string(requested) +
      ",\"queued_option_mask_bits\":" + std::to_string(scene.queued_mask) +
      ",\"queue_calls\":" + std::to_string(scene.queue_calls) +
      ",\"clone_calls\":" + std::to_string(scene.clone_calls) +
      ",\"send_constructor_calls\":" + std::to_string(scene.send_copies) +
      ",\"native_recipient_answer_status_raw\":" +
          std::to_string(observed.recipient_answer_status_raw) +
      ",\"fixture_owned_memory\":true,\"synthetic_native_callbacks\":true,"
      "\"mailbox_route_fixture_covered\":false,\"live_capture\":false,"
      "\"live_release\":false,\"material_result\":false}}");
  std::cout << "FIRST release action " << name << " queue=" << scene.queue_calls << '\n';
  current = nullptr;
}
} // namespace

int main(int argc, char **argv) {
  try {
    Require(argc == 2, "usage: ck3_12004_prisoner_release_action_whole_first OUTPUT_DIRECTORY");
    const std::filesystem::path directory(argv[1]); std::filesystem::create_directories(directory);
    Write(directory / "hello.json", HelloWire());
    Emit(Case::all_off_pending, "all_off_pending", directory);
    Emit(Case::gain_hook_pending, "gain_hook_pending", directory);
    Emit(Case::gain_hook_native_false, "gain_hook_native_false", directory);
    Emit(Case::gain_hook_copied_mask_changed, "gain_hook_copied_mask_changed", directory);
    Emit(Case::gain_hook_native_refused, "gain_hook_native_refused", directory);
    Write(directory / "NATIVE-FIRST.json",
        "{\"schema\":\"ck3.actual4.prisoner-release-action-whole-first.v1\","
        "\"compound_cases\":5,\"successful_queue_cases\":2,\"no_queue_cases\":3,"
        "\"actual4_query_provider\":true,\"actual4_action_provider\":true,"
        "\"production_submit_command_copy\":true,\"production_whole_query_and_ack\":true,"
        "\"production_descriptor_derived_hello\":true,"
        "\"fixture_owned_memory\":true,\"mailbox_route_fixture_covered\":false,"
        "\"natural_live_captives\":false,\"production_live_release\":false}");
    std::cout << "FIRST actual4 release action compound cases=5 complete\n"; return 0;
  } catch (const std::exception &error) {
    std::cerr << "FIRST actual4 release action RED " << error.what() << '\n'; return 1;
  }
}
