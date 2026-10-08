#include "xar_bridge/ck3_12004_prisoner_collection_result.hpp"
#include "xar_bridge/ck3_12004_prisoner_submission_lifecycle.hpp"

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
constexpr std::uint32_t kActor = 29829, kPrevious = 56063, kNext = 54235;
void Require(bool value, const char *message) {
  if (!value) throw std::runtime_error(message);
}
template<class T> void Put(void *object, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
}
struct Scene {
  std::array<std::byte, 0x30> storage{};
  std::vector<std::byte> slots = std::vector<std::byte>((kPrevious + 1) * 0x10);
  std::array<std::byte, 0x1D8> actor{}, previous{}, next{};
  std::array<std::byte, 0x290> previous_extension{}, next_extension{};
  std::array<std::byte, 4> previous_relation{}, next_relation{};
  std::array<std::byte, 0x360> land{};
  std::array<std::uint32_t, 1> rows{kPrevious};
  void *storage_pointer = storage.data();
  bridge::PlayerPrisonerFrameV1 frame{};
  Scene() {
    Put(storage.data(), 0x20, slots.data());
    Put(storage.data(), 0x2C, static_cast<std::int32_t>(kPrevious + 1));
    Put(slots.data(), kActor * 0x10 + 8, actor.data());
    Put(slots.data(), kPrevious * 0x10 + 8, previous.data());
    Put(slots.data(), kNext * 0x10 + 8, next.data());
    Put(actor.data(), 0x18, kActor); Put(previous.data(), 0x18, kPrevious);
    Put(next.data(), 0x18, kNext);
    Put(actor.data(), 0x158, std::int32_t{-1});
    Put(previous.data(), 0x158, std::int32_t{-1});
    Put(next.data(), 0x158, std::int32_t{-1});
    Put(actor.data(), 0x1C0, land.data());
    Put(land.data(), 0xD8, rows.data()); Put(land.data(), 0xE4, std::int32_t{1});
    Put(previous.data(), 0x1B0, previous_extension.data());
    Put(next.data(), 0x1B0, next_extension.data());
    Put(previous_extension.data(), 0x288, previous_relation.data());
    Put(next_extension.data(), 0x288, next_relation.data());
    Put(previous_relation.data(), 0, kActor); Put(next_relation.data(), 0, kActor);
    frame.public_revision = frame.native_revision = 4;
    frame.proof_epoch = 202; frame.date_raw = 53288544;
    frame.paused = frame.map_ready = frame.played_character_alive =
        frame.played_character_identity_round_trip = true;
    frame.played_character_id = static_cast<std::int32_t>(kActor);
  }
};
bool Capture(void *context, bridge::PlayerPrisonerFrameV1 &out) noexcept {
  out = static_cast<Scene *>(context)->frame; return true;
}
bool Read(void *context, std::uintptr_t address, void *out, std::size_t size) noexcept {
  auto &scene = *static_cast<Scene *>(context);
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
void *Title(void *) { return nullptr; }
} // namespace

int main(int argc, char **argv) {
  try {
    Require(argc == 2, "usage: ck3_12004_prisoner_release_worker_lifecycle_first OUTPUT_DIR");
    Scene scene;
    bridge::PlayerPrisonerCollectionAccessV1 access{};
    access.exact_build_admitted = true;
    access.admitted_executable_sha256 = native::kExecutableSha256;
    access.module_base = kModule;
    access.current_thread_id = access.application_main_thread_id = 8;
    access.context = &scene; access.capture_frame = &Capture; access.read_memory = &Read;
    access.read_lineage = access.read_child_relation = access.read_title_tier = access.read_dread = true;
    access.get_primary_title = &Title;
    native::PrisonerPrivateWorkerState12004 state{};
    state.may_have_submitted = true;
    state.current_release.emplace();
    state.current_release->observation.jailer_character_id = kActor;
    state.current_release->observation.prisoner_character_id = kPrevious;
    state.release_revision = 4; state.release_query_sequence = 6;
    // Only previously copied pair/cache state is seeded, no legal/send/ACK value.
    bridge::PlayerPrisonerCollectionSnapshotV1 held{};
    Require(native::ReadPlayerPrisonerCollectionV1(access, held) && held.collection_complete &&
        held.rows[0].full_character_id == kPrevious, "actual reader observes previous held full ID");
    Require(!native::ObservePrisonerSubmissionAfterCollection12004(state, held) &&
        state.may_have_submitted && state.current_release &&
        state.current_release->observation.prisoner_character_id == kPrevious,
        "still-held query preserves existing latch and its original pair");
    scene.rows[0] = kNext;
    Put(scene.previous_extension.data(), 0x288, static_cast<void *>(nullptr));
    bridge::PlayerPrisonerCollectionSnapshotV1 next{};
    Require(native::ReadPlayerPrisonerCollectionV1(access, next) && next.collection_complete &&
        next.returned_count == 1 && next.rows[0].full_character_id == kNext,
        "actual new collection observes a different current full prisoner ID");
    Require(native::ObservePrisonerSubmissionAfterCollection12004(state, next) &&
        !state.may_have_submitted && !state.current_release && !state.current_quote &&
        state.release_revision == 0 && state.release_query_sequence == 0,
        "production helper closes old latch and invalidates its old terms after absence");
    std::array<native::PlayerPrisonerRansomQuoteV1, bridge::kPlayerPrisonerMaximumRowsV1> quotes{};
    quotes[0] = native::ReadPlayerPrisonerRansomQuotePrivateV1(
        native::PrisonerRansomBindings12004{}, kModule,
        static_cast<std::int32_t>(kActor), static_cast<std::int32_t>(kNext));
    std::array<native::PrisonerReleasePreview12004, bridge::kPlayerPrisonerMaximumRowsV1> previews{};
    const auto wire = native::SerializePrisonerCollectionCommandResult12004(
        "lifecycle-next", "query-player-prisoner-collection-private-v1", 10,
        scene.frame.proof_epoch, scene.frame.native_revision,
        next, quotes, true, &previews, nullptr);
    Require(!wire.empty(), "production owning whole serializer supplies the fresh unavailable-offer packet");
    const std::filesystem::path directory(argv[1]);
    std::filesystem::create_directories(directory);
    std::ofstream out(directory / "lifecycle-next.json", std::ios::binary);
    out << wire << '\n'; Require(out.good(), "write new whole source packet");
    std::ofstream receipt(directory / "CACHE-FIRST.json", std::ios::binary);
    receipt << "{\"schema\":\"xar.prisoner-worker-lifecycle-first-12004-v1\","
        "\"previous_target\":56063,\"next_target\":54235,"
        "\"held_preserved\":true,\"absence_closed\":true,"
        "\"old_terms_invalidated\":true,\"fixture_owned_memory\":true,"
        "\"native_actions\":0,\"live_credit\":false}\n";
    Require(receipt.good(), "write new cache FIRST metadata");
    std::cout << "FIRST prisoner worker lifecycle held/absent and new whole packet\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FIRST prisoner worker lifecycle RED " << error.what() << '\n'; return 1;
  }
}
