// Fresh keeper whole packets use real actual4 binders/readers and the owning
// production command_result serializer. Callback memory belongs to this test.
#include "xar_bridge/ck3_12004_prisoner_collection_result.hpp"
#include "xar_bridge/ck3_12004_prisoner_keeper_opinion.hpp"

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
constexpr std::uint32_t kTarget = 0x03000002;
constexpr std::uint32_t kHash = 0x55AA0066;
constexpr std::string_view kStep = "query-player-prisoner-collection-private-v1";
constexpr std::string_view kOldSha =
    "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";

void Require(bool condition, std::string_view message) {
  if (!condition) throw std::runtime_error(std::string(message));
}
template <class T> void Put(void *object, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
}
struct Scene {
  std::array<std::byte, 0x30> storage{};
  std::vector<std::byte> slots = std::vector<std::byte>((kActor + 1) * 0x10);
  std::array<std::byte, 0x1D0> actor{}, target{};
  std::array<std::byte, 0x98> definition{};
  std::array<std::byte, 0x20> extension{}, group{}, active{};
  std::array<void *, 1> rows{active.data()};
  void *storage_pointer = storage.data();
  void *database = definition.data();
  bridge::PlayerPrisonerFrameV1 frame{};
  std::int32_t keeper_opinion = 0, reverse_opinion = 0, named_value = 0;
  unsigned frame_reads = 0, keeper_reads = 0, reverse_reads = 0, sum_reads = 0;

  explicit Scene(std::uint64_t revision) {
    Put(storage.data(), 0x20, slots.data());
    Put(storage.data(), 0x2C, static_cast<std::int32_t>(kActor + 1));
    Put(slots.data(), kActor * 0x10 + 8, actor.data());
    Put(slots.data(), 2 * 0x10 + 8, target.data());
    Put(actor.data(), 0x18, kActor); Put(target.data(), 0x18, kTarget);
    // The real reader returns complete empty custody. Both observers resolve
    // the independently retained generation-bearing ID, rather than ordinal0.
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
    Put(group.data(), 8, rows.data()); Put(group.data(), 0x14, std::int32_t{1});
    Put(active.data(), 8, definition.data());
    frame.public_revision = frame.native_revision = revision;
    frame.proof_epoch = 91; frame.date_raw = 1220410;
    frame.paused = frame.map_ready = frame.played_character_alive =
        frame.played_character_identity_round_trip = true;
    frame.played_character_id = static_cast<std::int32_t>(kActor);
  }
};
Scene *current = nullptr;
bool Capture(void *opaque, bridge::PlayerPrisonerFrameV1 &out) noexcept {
  auto &scene = *static_cast<Scene *>(opaque);
  out = scene.frame; ++scene.frame_reads; return true;
}
bool ReadMemory(void *opaque, std::uintptr_t address, void *out,
                std::size_t size) noexcept {
  auto &scene = *static_cast<Scene *>(opaque);
  if (address == kModule + native::kCharacterStorageSlotRva) {
    if (size != sizeof(void *)) return false;
    std::memcpy(out, &scene.storage_pointer, size); return true;
  }
  if (address == kModule + 0x5C67570) {
    if (size != sizeof(void *)) return false;
    void *empty = nullptr; std::memcpy(out, &empty, size); return true;
  }
  if (!address || !out || !size) return false;
  std::memcpy(out, reinterpret_cast<const void *>(address), size); return true;
}
std::int32_t Total(void *owner, void *toward) {
  if (owner == current->actor.data() && toward == current->target.data()) {
    ++current->keeper_reads; return current->keeper_opinion;
  }
  Require(owner == current->target.data() && toward == current->actor.data(),
      "only the independently observed opposite pair is used by material v1");
  ++current->reverse_reads; return current->reverse_opinion;
}
std::int32_t Hash(void *database, const char *key, std::uint32_t length) {
  Require(database == current->database &&
      std::string_view(key, length) == native::kPrisonerReleaseMaterialOpinionKey12004,
      "material v1 keeps the one fixed loaded modifier");
  return static_cast<std::int32_t>(kHash);
}
void *Lookup(void *database, std::uint32_t hash) {
  Require(database == current->database && hash == kHash, "loaded modifier identity");
  return current->definition.data();
}
void *Group(void *extension, std::uint32_t actor) {
  Require(extension == current->extension.data() && actor == kActor,
      "material modifier group belongs to the opposite pair");
  return current->group.data();
}
std::int32_t Sum(void *group, void *definition) {
  Require(group == current->group.data() && definition == current->definition.data(),
      "material v1 sums only released_from_prison");
  ++current->sum_reads; return current->named_value;
}

native::KeeperOpinionBindings12004 KeeperBindings(Scene &scene) {
  auto b = native::BindKeeperOpinionImage12004(kModule, native::kExecutableSha256);
  Require(b.opinion.enabled && b.opinion.core.enabled &&
      reinterpret_cast<std::uintptr_t>(b.opinion.read_opinion) ==
          kModule + native::kGiftReadCharacterOpinionRva12004 &&
      reinterpret_cast<std::uintptr_t>(b.opinion.core.character_storage_slot) ==
          kModule + native::kCharacterStorageSlotRva,
      "begin with the production admitted actual4 binder and mapped addresses");
  b.opinion.core.character_storage_slot = &scene.storage_pointer;
  b.opinion.read_opinion = &Total;
  return b;
}
native::PrisonerReleaseMaterialOpinionBindings12004 MaterialBindings(Scene &scene) {
  auto b = native::BindPrisonerReleaseMaterialOpinionImage12004(
      kModule, native::kExecutableSha256);
  Require(b.opinion.enabled && b.opinion.core.enabled, "material uses its actual4 binder");
  b.opinion.core.character_storage_slot = &scene.storage_pointer;
  b.opinion.modifier_database_slot = &scene.database;
  b.opinion.read_opinion = &Total; b.opinion.lookup_modifier = &Lookup;
  b.opinion.find_group = &Group; b.opinion.sum_modifier = &Sum; b.hash_key = &Hash;
  Put(scene.active.data(), 0, b.opinion.active_opinion_vtable);
  return b;
}

void Emit(const std::filesystem::path &directory, std::string_view name,
          std::uint64_t revision, std::int32_t keeper, std::int32_t reverse,
          bool named_present, std::int32_t named) {
  Scene scene(revision); current = &scene;
  scene.keeper_opinion = keeper; scene.reverse_opinion = reverse; scene.named_value = named;
  if (!named_present) Put(scene.group.data(), 0x14, std::int32_t{0});
  bridge::PlayerPrisonerCollectionAccessV1 access{};
  access.exact_build_admitted = true;
  access.admitted_executable_sha256 = native::kExecutableSha256;
  access.module_base = kModule; access.current_thread_id = access.application_main_thread_id = 8;
  access.context = &scene; access.capture_frame = &Capture; access.read_memory = &ReadMemory;
  bridge::PlayerPrisonerCollectionSnapshotV1 collection{};
  Require(native::ReadPlayerPrisonerCollectionV1(access, collection) && collection.available &&
      collection.collection_complete && collection.returned_count == 0,
      "real actual4 collection reader returns complete empty owned custody");
  native::KeeperOpinion12004 opinion{};
  Require(native::ReadKeeperOpinion12004(KeeperBindings(scene), access,
      collection.frame, kTarget, opinion) && opinion.available &&
      opinion.actor_opinion_of_target == keeper && opinion.unavailable_reason.empty() &&
      opinion.target_character_id == kTarget && opinion.frame == collection.frame &&
      scene.keeper_reads == 2 && scene.reverse_reads == 0 && scene.sum_reads == 0,
      "keeper reads actor toward retained full target twice, including signed/zero values");
  native::PrisonerReleaseMaterialOpinion12004 material{};
  Require(native::ReadPrisonerReleaseMaterialOpinion12004(MaterialBindings(scene), access,
      collection.frame, kTarget, material) && material.available &&
      material.target_opinion_of_actor == reverse && material.modifier_observed &&
      material.modifier_present == named_present && material.modifier_value ==
      (named_present ? std::optional<std::int32_t>{named} : std::nullopt) &&
      scene.reverse_reads == 2 && scene.keeper_reads == 2 &&
      scene.sum_reads == (named_present ? 2U : 0U) && scene.frame_reads == 6,
      "unchanged material v1 observes opposite total and independent named presence/value");
  std::array<native::PlayerPrisonerRansomQuoteV1, bridge::kPlayerPrisonerMaximumRowsV1> quotes{};
  std::array<native::PrisonerReleasePreview12004, bridge::kPlayerPrisonerMaximumRowsV1> previews{};
  const auto wire = native::SerializePrisonerCollectionCommandResult12004(
      name, kStep, revision - 800, scene.frame.proof_epoch, revision,
      collection, quotes, true, &previews, &material, nullptr, &opinion);
  Require(!wire.empty(), "same owning production whole command_result serializer");
  std::ofstream out(directory / (std::string(name) + ".json"), std::ios::binary);
  out << wire << '\n'; Require(out.good(), "write fresh whole keeper packet");
  current = nullptr;
}
} // namespace

int main(int argc, char **argv) {
  try {
    Require(argc == 2,
        "usage: ck3_12004_prisoner_keeper_opinion_whole_first OUTPUT_DIRECTORY");
    Require(!native::BindKeeperOpinionImage12004(kModule, kOldSha).opinion.enabled,
        "actual4 keeper binder rejects historical actual3 SHA without substitution");
    const std::filesystem::path directory(argv[1]);
    std::filesystem::create_directories(directory);
    Emit(directory, "keeper-positive", 801, 25, -10, false, 0);
    Emit(directory, "keeper-zero", 802, 0, 45, true, 0);
    Emit(directory, "keeper-negative", 803, -35, 80, true, 20);
    Emit(directory, "keeper-reverse-distinct", 804, 60, -60, true, 20);
    Emit(directory, "keeper-material-independent", 805, 25, -10, true, 20);
    std::ofstream receipt(directory / "NATIVE-FIRST.json", std::ios::binary);
    receipt << "{\"schema\":\"ck3.actual4.prisoner-keeper-opinion-whole-first.v1\","
        "\"whole_wire_cases\":5,\"fixture_owned_memory\":true,"
        "\"new_build_production_live\":false,\"action_submitted\":false}\n";
    Require(receipt.good(), "write fresh native FIRST receipt");
    std::cout << "FIRST actual4 prisoner keeper whole cases=5\n"; return 0;
  } catch (const std::exception &error) {
    std::cerr << "FIRST prisoner keeper RED " << error.what() << '\n'; return 1;
  }
}
