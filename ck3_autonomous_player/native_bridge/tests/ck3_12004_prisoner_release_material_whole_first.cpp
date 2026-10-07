// Fresh source fixture: real actual4 collection/retained-pair readers and
// production complete command_result formatter; no CK3 state or action.
#include "xar_bridge/ck3_12004_prisoner_collection_result.hpp"

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
  std::int32_t total_opinion = -12, named_value = 0;
  unsigned frame_reads = 0, total_reads = 0, sum_reads = 0;
  bool frame_drift = false;
  Scene(std::uint64_t revision, std::int32_t date) {
    Put(storage.data(), 0x20, slots.data());
    Put(storage.data(), 0x2C, static_cast<std::int32_t>(kActor + 1));
    Put(slots.data(), kActor * 0x10 + 8, actor.data());
    Put(slots.data(), 2 * 0x10 + 8, target.data());
    Put(actor.data(), 0x18, kActor); Put(target.data(), 0x18, kTarget);
    // Both frames have an empty custody collection. The retained full ID is
    // resolved independently; never select a post-release collection ordinal.
    Put(target.data(), 0x1B0, extension.data());
    Put(definition.data(), 0, std::uintptr_t{0x3000});
    Put(definition.data(), 0x88, std::uintptr_t{0x3010});
    Put(definition.data(), 0x14, kHash);
    Put(definition.data(), 0x38, std::uint32_t{0x4744624F});
    const auto key = native::kPrisonerReleaseMaterialOpinionKey12004;
    Put(definition.data(), 0x18, key.data());
    Put(definition.data(), 0x28, static_cast<std::uint64_t>(key.size()));
    Put(definition.data(), 0x30, static_cast<std::uint64_t>(key.size()));
    Put(active.data(), 0, std::uintptr_t{0x4000});
    Put(active.data(), 8, definition.data());
    Put(group.data(), 8, rows.data()); Put(group.data(), 0x14, std::int32_t{1});
    frame.public_revision = frame.native_revision = revision;
    frame.proof_epoch = 91; frame.date_raw = date;
    frame.paused = frame.map_ready = frame.played_character_alive =
        frame.played_character_identity_round_trip = true;
    frame.played_character_id = static_cast<std::int32_t>(kActor);
  }
};
Scene *current = nullptr;
bool Capture(void *opaque, bridge::PlayerPrisonerFrameV1 &out) noexcept {
  auto &scene = *static_cast<Scene *>(opaque);
  out = scene.frame;
  if (++scene.frame_reads == 4 && scene.frame_drift) ++out.native_revision;
  return true;
}
bool ReadMemory(void *opaque, std::uintptr_t address, void *out, std::size_t size) noexcept {
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
std::int32_t Hash(void *database, const char *key, std::uint32_t length) {
  Require(database == current->database &&
      std::string_view(key, length) == native::kPrisonerReleaseMaterialOpinionKey12004,
      "hash only the released_from_prison loaded definition");
  return static_cast<std::int32_t>(kHash);
}
void *Lookup(void *database, std::uint32_t hash) {
  Require(database == current->database && hash == kHash, "definition lookup identity");
  return current->definition.data();
}
std::int32_t Total(void *target, void *actor) {
  Require(target == current->target.data() && actor == current->actor.data(),
      "opinion owner is retained target, toward is the played actor");
  ++current->total_reads; return current->total_opinion;
}
void *Group(void *extension, std::uint32_t actor) {
  Require(extension == current->extension.data() && actor == kActor, "group actor full ID");
  return current->group.data();
}
std::int32_t Sum(void *group, void *definition) {
  Require(group == current->group.data() && definition == current->definition.data(),
      "sum the one loaded named modifier");
  ++current->sum_reads; return current->named_value;
}
native::PrisonerReleaseMaterialOpinionBindings12004 BindScene(Scene &scene) {
  native::PrisonerReleaseMaterialOpinionBindings12004 b{};
  b.hash_key = &Hash;
  auto &opinion = b.opinion;
  opinion.enabled = opinion.core.enabled = true; opinion.module_base = kModule;
  opinion.core.character_storage_slot = &scene.storage_pointer;
  opinion.modifier_database_slot = &scene.database;
  opinion.read_opinion = &Total; opinion.lookup_modifier = &Lookup;
  opinion.find_group = &Group; opinion.sum_modifier = &Sum;
  opinion.modifier_primary_vtable = 0x3000; opinion.modifier_secondary_vtable = 0x3010;
  opinion.active_opinion_vtable = 0x4000; opinion.temporary_opinion_vtable = 0x4010;
  return b;
}
void Emit(const std::filesystem::path &directory, std::string_view name,
    std::uint64_t revision, std::int32_t date, std::int32_t total,
    std::int32_t named, bool present, bool drift) {
  Scene scene(revision, date); current = &scene;
  scene.total_opinion = total; scene.named_value = named; scene.frame_drift = drift;
  if (!present) Put(scene.group.data(), 0x14, std::int32_t{0});
  bridge::PlayerPrisonerCollectionAccessV1 access{};
  access.exact_build_admitted = true;
  access.admitted_executable_sha256 = native::kExecutableSha256;
  access.module_base = kModule; access.current_thread_id = access.application_main_thread_id = 8;
  access.context = &scene; access.capture_frame = &Capture; access.read_memory = &ReadMemory;
  bridge::PlayerPrisonerCollectionSnapshotV1 collection{};
  Require(native::ReadPlayerPrisonerCollectionV1(access, collection) &&
      collection.available && collection.collection_complete && collection.returned_count == 0,
      "real .4 collection reader returns the complete empty owned collection");
  native::PrisonerReleaseMaterialOpinion12004 material{};
  const bool observed = native::ReadPrisonerReleaseMaterialOpinion12004(
      BindScene(scene), access, collection.frame, kTarget, material);
  Require(observed == !drift && scene.total_reads == 2 && scene.frame_reads == 4,
      "two actual pair reads plus stable native frame sampling");
  if (drift) {
    Require(material.unavailable_reason == "release_material_frame_changed" &&
        !material.target_opinion_of_actor && !material.modifier_observed && !material.modifier_value,
        "native frame change has no manufactured material observation");
  } else {
    Require(material.available && material.target_opinion_of_actor == total &&
        material.modifier_observed && material.modifier_present == present &&
        material.modifier_value == (present ? std::optional<std::int32_t>{named} : std::nullopt) &&
        scene.sum_reads == (present ? 2U : 0U),
        "named presence/legitimate zero/absence are distinct");
  }
  std::array<native::PlayerPrisonerRansomQuoteV1, bridge::kPlayerPrisonerMaximumRowsV1> quotes{};
  std::array<native::PrisonerReleasePreview12004, bridge::kPlayerPrisonerMaximumRowsV1> previews{};
  const auto wire = native::SerializePrisonerCollectionCommandResult12004(
      name, kStep, revision - 700, scene.frame.proof_epoch, revision,
      collection, quotes, true, &previews, &material);
  Require(!wire.empty(), "same production whole command_result formatter");
  std::ofstream out(directory / (std::string(name) + ".json"), std::ios::binary);
  out << wire << '\n'; Require(out.good(), "write fresh whole native wire");
  current = nullptr;
}
} // namespace

int main(int argc, char **argv) {
  try {
    Require(argc == 2, "usage: ck3_12004_prisoner_release_material_whole_first OUTPUT_DIRECTORY");
    const auto b = native::BindPrisonerReleaseMaterialOpinionImage12004(kModule, native::kExecutableSha256);
    Require(b.opinion.enabled &&
        reinterpret_cast<std::uintptr_t>(b.hash_key) == kModule + native::kOpinionStableKeyHashRva &&
        reinterpret_cast<std::uintptr_t>(b.opinion.read_opinion) == kModule + native::kGiftReadCharacterOpinionRva12004,
        "fixture callback seam begins with the admitted actual4 binding");
    const std::filesystem::path directory(argv[1]); std::filesystem::create_directories(directory);
    Emit(directory, "named-zero", 701, 1220410, -12, 0, true, false);
    Emit(directory, "named-material", 702, 1220411, -5, 20, true, false);
    Emit(directory, "named-absent", 703, 1220411, -5, 0, false, false);
    Emit(directory, "native-frame-drift", 704, 1220411, -5, 20, true, true);
    std::ofstream receipt(directory / "NATIVE-FIRST.json", std::ios::binary);
    receipt << "{\"schema\":\"ck3.actual4.prisoner-release-material-whole-first.v1\","
        "\"whole_wire_cases\":4,\"fixture_owned_memory\":true,"
        "\"new_build_production_live\":false,\"action_submitted\":false}\n";
    Require(receipt.good(), "write source fixture receipt");
    std::cout << "FIRST prisoner retained full-ID material whole cases=4\n"; return 0;
  } catch (const std::exception &error) {
    std::cerr << "FIRST prisoner material RED " << error.what() << '\n'; return 1;
  }
}
