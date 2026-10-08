// New retained-state whole packets. The memory/callbacks are fixture-owned;
// the actual4 binders, readers and command_result formatter are production.
#include "xar_bridge/ck3_12004_prisoner_collection_result.hpp"
#include "xar_bridge/ck3_12004_prisoner_retained_target_state.hpp"

#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <vector>

namespace {
namespace native = xar::ck3_12004;
namespace bridge = xar::bridge;
constexpr std::uintptr_t kModule = 0x140000000ULL;
constexpr std::uint32_t kActor = 29829;
constexpr std::uint32_t kTarget = 0x04000003;
constexpr std::uint32_t kOther = 0x05000004;
constexpr std::uint32_t kHash = 0x55AA0066;
constexpr std::string_view kStep = "query-player-prisoner-collection-private-v1";

void Require(bool condition, std::string_view message) {
  if (!condition) throw std::runtime_error(std::string(message));
}
template <class T> void Put(void *object, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
}
struct Scene {
  std::array<std::byte, 0x30> storage{};
  std::vector<std::byte> slots = std::vector<std::byte>((kActor + 1) * 0x10);
  std::array<std::byte, 0x1D8> actor{}, target{}, other{};
  std::array<std::byte, 0x290> extension{};
  std::array<std::byte, 0x360> actor_land{};
  std::array<std::byte, 4> relation{};
  std::array<std::byte, 0x98> definition{};
  std::array<std::byte, 0x20> group{}, active{};
  std::array<void *, 1> opinion_rows{active.data()};
  std::array<std::uint32_t, 1> prisoner_rows{kTarget};
  void *storage_pointer = storage.data();
  void *database = definition.data();
  bridge::PlayerPrisonerFrameV1 frame{};

  explicit Scene(std::uint64_t revision) {
    Put(storage.data(), 0x20, slots.data());
    Put(storage.data(), 0x2C, static_cast<std::int32_t>(kActor + 1));
    Put(slots.data(), kActor * 0x10 + 8, actor.data());
    Put(slots.data(), 3 * 0x10 + 8, target.data());
    Put(slots.data(), 4 * 0x10 + 8, other.data());
    Put(actor.data(), 0x18, kActor); Put(target.data(), 0x18, kTarget);
    Put(other.data(), 0x18, kOther);
    Put(actor.data(), 0x158, std::int32_t{-1});
    Put(target.data(), 0x158, std::int32_t{-1});
    Put(target.data(), 0x1B0, extension.data());
    Put(definition.data(), 0, kModule + native::kGiftOpinionModifierVtableRva12004);
    Put(definition.data(), 0x88,
        kModule + native::kGiftOpinionModifierSecondaryVtableRva12004);
    Put(definition.data(), 0x14, kHash);
    Put(definition.data(), 0x38, std::uint32_t{0x4744624F});
    const auto key = native::kPrisonerReleaseMaterialOpinionKey12004;
    Put(definition.data(), 0x18, key.data());
    Put(definition.data(), 0x28, static_cast<std::uint64_t>(key.size()));
    Put(definition.data(), 0x30, static_cast<std::uint64_t>(key.size()));
    Put(group.data(), 8, opinion_rows.data());
    // The existing named modifier is independently absent in all new cases.
    Put(group.data(), 0x14, std::int32_t{0});
    Put(active.data(), 8, definition.data());
    frame.public_revision = frame.native_revision = revision;
    frame.proof_epoch = 101; frame.date_raw = 1220411;
    frame.paused = frame.map_ready = frame.played_character_alive =
        frame.played_character_identity_round_trip = true;
    frame.played_character_id = static_cast<std::int32_t>(kActor);
  }

  void Hold(std::uint32_t jailer) {
    Put(relation.data(), 0, jailer);
    Put(extension.data(), 0x288, relation.data());
    if (jailer == kActor) {
      Put(actor.data(), 0x1C0, actor_land.data());
      Put(actor_land.data(), 0xD8, prisoner_rows.data());
      Put(actor_land.data(), 0xE4, std::int32_t{1});
    }
  }
};
Scene *current = nullptr;
bool Capture(void *opaque, bridge::PlayerPrisonerFrameV1 &out) noexcept {
  out = static_cast<Scene *>(opaque)->frame; return true;
}
bool ReadMemory(void *opaque, std::uintptr_t address, void *out,
                std::size_t size) noexcept {
  auto &scene = *static_cast<Scene *>(opaque);
  if (address == kModule + native::kCharacterStorageSlotRva) {
    if (size != sizeof(void *)) return false;
    std::memcpy(out, &scene.storage_pointer, size); return true;
  }
  if (address == kModule + 0x5C67570 ||
      address == kModule + native::kPrisonerTitleFallbackSlotRva12004) {
    if (size != sizeof(void *)) return false;
    void *empty = nullptr; std::memcpy(out, &empty, size); return true;
  }
  if (!address || !out || !size) return false;
  std::memcpy(out, reinterpret_cast<const void *>(address), size); return true;
}
void *PrimaryTitle(void *) { return nullptr; }
std::int32_t Total(void *owner, void *toward) {
  if (owner == current->actor.data() && toward == current->target.data()) return -2;
  Require(owner == current->target.data() && toward == current->actor.data(),
      "existing opposite material direction remains independent");
  return 42;
}
std::int32_t Hash(void *database, const char *key, std::uint32_t length) {
  Require(database == current->database && std::string_view(key, length) ==
      native::kPrisonerReleaseMaterialOpinionKey12004, "existing loaded modifier key");
  return static_cast<std::int32_t>(kHash);
}
void *Lookup(void *database, std::uint32_t hash) {
  Require(database == current->database && hash == kHash, "existing modifier identity");
  return current->definition.data();
}
void *Group(void *extension, std::uint32_t actor) {
  Require(extension == current->extension.data() && actor == kActor,
      "retained material uses the existing target-to-actor group");
  return current->group.data();
}
std::int32_t Sum(void *, void *) {
  throw std::runtime_error("absent modifier must not be summed");
}

void Emit(const std::filesystem::path &directory, std::string_view name,
          std::uint64_t revision, std::string_view expected_state) {
  Scene scene(revision); current = &scene;
  if (expected_state == "held_by_player") scene.Hold(kActor);
  else if (expected_state == "held_by_other") scene.Hold(kOther);
  else if (expected_state == "dead") Put(scene.target.data(), 0x1D0, scene.definition.data());
  else if (expected_state == "unavailable") scene.Hold(0x06000004);
  bridge::PlayerPrisonerCollectionAccessV1 access{};
  access.exact_build_admitted = true;
  access.admitted_executable_sha256 = native::kExecutableSha256;
  access.module_base = kModule;
  access.current_thread_id = access.application_main_thread_id = 8;
  access.context = &scene; access.capture_frame = &Capture; access.read_memory = &ReadMemory;
  access.read_lineage = access.read_child_relation = access.read_title_tier = access.read_dread = true;
  access.get_primary_title = &PrimaryTitle;
  bridge::PlayerPrisonerCollectionSnapshotV1 collection{};
  const auto expected_count = expected_state == "held_by_player" ? 1U : 0U;
  Require(native::ReadPlayerPrisonerCollectionV1(access, collection) && collection.available &&
      collection.collection_complete && collection.returned_count == expected_count,
      "real collection reader observes current player custody, not hand-authored rows");
  if (expected_count != 0) Require(collection.rows[0].full_character_id == kTarget &&
      collection.rows[0].jailer_character_id == kActor, "actual held row is joined by full ID");

  auto bindings = native::BindRetainedTargetStateImage12004(kModule, native::kExecutableSha256);
  Require(bindings.enabled && bindings.core.enabled &&
      reinterpret_cast<std::uintptr_t>(bindings.core.character_storage_slot) ==
          kModule + native::kCharacterStorageSlotRva, "actual4 binder starts at admitted storage");
  bindings.core.character_storage_slot = &scene.storage_pointer;
  native::RetainedTargetState12004 state{};
  const bool available = expected_state != "unavailable";
  Require(native::ReadRetainedTargetState12004(bindings, access, collection.frame, kTarget, state) ==
      available && state.available == available && state.custody_state == expected_state &&
      state.frame == collection.frame && state.target_character_id == kTarget,
      "production retained-state reader emits the actual raw postcondition");
  if (!available) Require(!state.target_alive.has_value() && !state.is_imprisoned.has_value() &&
      !state.jailer_character_id.has_value() && state.unavailable_reason ==
          "retained_target_jailer_identity_unavailable", "stale full captor is not freedom");
  else if (expected_state == "dead") Require(state.target_alive == false &&
      !state.is_imprisoned.has_value() && !state.jailer_character_id.has_value(), "dead is separate");
  else Require(state.target_alive == true && state.is_imprisoned == (expected_count != 0 ||
      expected_state == "held_by_other") && (expected_state == "free" ?
      !state.jailer_character_id.has_value() : state.jailer_character_id ==
          (expected_state == "held_by_player" ? kActor : kOther)), "alive current custody scalars");

  auto material_bindings = native::BindPrisonerReleaseMaterialOpinionImage12004(
      kModule, native::kExecutableSha256);
  material_bindings.opinion.core.character_storage_slot = &scene.storage_pointer;
  material_bindings.opinion.modifier_database_slot = &scene.database;
  material_bindings.opinion.read_opinion = &Total;
  material_bindings.opinion.lookup_modifier = &Lookup;
  material_bindings.opinion.find_group = &Group; material_bindings.opinion.sum_modifier = &Sum;
  material_bindings.hash_key = &Hash;
  Put(scene.active.data(), 0, material_bindings.opinion.active_opinion_vtable);
  native::PrisonerReleaseMaterialOpinion12004 material{};
  Require(native::ReadPrisonerReleaseMaterialOpinion12004(material_bindings, access,
      collection.frame, kTarget, material) && material.available &&
      material.target_opinion_of_actor == 42 && material.modifier_observed &&
      !material.modifier_present && !material.modifier_value.has_value(),
      "unchanged material observer supplies actual independent fixture observations");
  auto keeper_bindings = native::BindKeeperOpinionImage12004(kModule, native::kExecutableSha256);
  keeper_bindings.opinion.core.character_storage_slot = &scene.storage_pointer;
  keeper_bindings.opinion.read_opinion = &Total;
  native::KeeperOpinion12004 keeper{};
  Require(native::ReadKeeperOpinion12004(keeper_bindings, access, collection.frame,
      kTarget, keeper) && keeper.actor_opinion_of_target == -2, "existing keeper stays independent");
  std::array<native::PlayerPrisonerRansomQuoteV1, bridge::kPlayerPrisonerMaximumRowsV1> quotes{};
  std::array<native::PrisonerReleasePreview12004, bridge::kPlayerPrisonerMaximumRowsV1> previews{};
  for (std::uint32_t i = 0; i < collection.returned_count; ++i)
    quotes[i].failure = native::PlayerPrisonerRansomQuoteFailureV1::not_evaluated;
  if (collection.returned_count != 0) {
    // This new fixture supplies no ransom interaction context. Route the
    // selected held row through the production reader's typed unavailable
    // result; do not claim a fresh quote or leave selected ordinal0 unevaluated.
    quotes[0] = native::ReadPlayerPrisonerRansomQuotePrivateV1(
        native::PrisonerRansomBindings12004{}, kModule,
        static_cast<std::int32_t>(kActor), static_cast<std::int32_t>(kTarget));
    Require(!quotes[0].available && quotes[0].failure ==
        native::PlayerPrisonerRansomQuoteFailureV1::binding_unavailable,
        "selected unrelated quote has an actual production failure reason");
  }
  const auto wire = native::SerializePrisonerCollectionCommandResult12004(
      name, kStep, revision - 900, scene.frame.proof_epoch, revision,
      collection, quotes, true, &previews, &material, nullptr, &keeper, &state);
  Require(!wire.empty(), "owning production whole serializer with retained-state sibling");
  std::ofstream out(directory / (std::string(name) + ".json"), std::ios::binary);
  out << wire << '\n'; Require(out.good(), "write fresh retained-state whole packet");
  current = nullptr;
}
} // namespace

int main(int argc, char **argv) {
  try {
    Require(argc == 2, "usage: ck3_12004_prisoner_retained_target_state_whole_first OUTPUT_DIRECTORY");
    const std::filesystem::path directory(argv[1]);
    std::filesystem::create_directories(directory);
    Emit(directory, "retained-free", 901, "free");
    Emit(directory, "retained-held-player", 902, "held_by_player");
    Emit(directory, "retained-held-other", 903, "held_by_other");
    Emit(directory, "retained-dead", 904, "dead");
    Emit(directory, "retained-unavailable", 905, "unavailable");
    std::ofstream receipt(directory / "NATIVE-FIRST.json", std::ios::binary);
    receipt << "{\"schema\":\"ck3.actual4.prisoner-retained-target-state-whole-first.v1\","
        "\"whole_wire_cases\":5,\"fixture_owned_memory\":true,"
        "\"new_build_production_live\":false,\"action_submitted\":false}\n";
    Require(receipt.good(), "write new native FIRST receipt");
    std::cout << "FIRST actual4 retained prisoner state whole cases=5\n"; return 0;
  } catch (const std::exception &error) {
    std::cerr << "FIRST retained prisoner state RED " << error.what() << '\n'; return 1;
  }
}
