#pragma once

// Test-only owned-memory source chain. No CK3 process, pipe or desktop access.
#include "xar_bridge/ck3_12002_council_candidates.hpp"

#include <algorithm>
#include <array>
#include <cstring>

namespace xar::ck3_12002::test {

template <std::size_t Size> struct Blob {
  std::array<std::byte, Size> bytes{};
  void *Data() noexcept { return bytes.data(); }
  const void *Data() const noexcept { return bytes.data(); }
  template <typename T> void Put(std::size_t offset, T value) noexcept {
    std::memcpy(bytes.data() + offset, &value, sizeof(value));
  }
};

struct CouncilCandidatesFixture12002 {
  static constexpr std::int32_t kOwner = 0x01000001;
  static constexpr std::int32_t kIncumbent = 0x01000002;
  static constexpr std::int32_t kCandidate = 0x01000010;
  static constexpr std::int32_t kTask = 0x01000001;
  static constexpr std::size_t kCharacters = 24;
  struct Slot { std::uintptr_t reserved = 0; void *object = nullptr; };
  std::array<Blob<0x200>, kCharacters> characters{};
  Blob<0x300> owner_extension{};
  Blob<0x60> position{}, task_type{};
  std::array<Blob<0x80>, 4> tasks{};
  Blob<0x30> character_storage{}, task_storage{};
  std::array<Slot, 128> character_slots{}, task_slots{};
  std::array<std::int32_t, 4> task_ids{kTask, -1, -1, -1};
  std::array<std::uintptr_t, 128> rows{};
  void *character_storage_pointer = nullptr, *character_fallback = nullptr;
  void *task_storage_pointer = nullptr, *task_fallback = nullptr;
  CouncilCandidatesFrameV1 frame{};
  CouncilCandidatesEnvironmentV1 environment{};
  CouncilCandidatesAccessV1 access{};
  CouncilCandidatesRequestV1 request{};
  const void *allocator_address = nullptr;
  std::size_t allocator_size = 0;
  std::int32_t count = 2, capacity = 64;
  std::uint32_t capture_calls = 0, producer_calls = 0, release_calls = 0;
  bool main_thread = true, producer_ok = true, release_ok = true, initialize_ok = true;
  bool drift_revision_after_release = false, drift_date_after_release = false;
  bool drift_incumbent_after_release = false, unreadable_candidate_skill = false;
  bool allocator_shape_valid = true, producer_inputs_valid = true;
  static constexpr char kPosition[] = "councillor_steward";

  CouncilCandidatesFixture12002() noexcept {
    for (std::size_t i = 0; i < characters.size(); ++i) {
      const auto id = static_cast<std::int32_t>(0x01000001 + i);
      characters[i].Put(0x18, id);
      characters[i].Put(0x1C, std::uint32_t{0x43686172});
      characters[i].Put(0xE0, static_cast<std::int32_t>(12 + i));
      character_slots[i + 1].object = characters[i].Data();
    }
    characters[0].Put(0x1C0, owner_extension.Data());
    characters[1].Put(0xE0, std::int32_t{9});
    characters[15].Put(0xE0, std::int32_t{22});
    characters[16].Put(0xE0, std::int32_t{17});
    owner_extension.Put(0x230, task_ids.data());
    owner_extension.Put(0x23C, std::int32_t{1});
    const char *key = kPosition;
    position.Put(0x18, key);
    position.Put(0x28, std::size_t{sizeof(kPosition) - 1});
    position.Put(0x30, std::size_t{31});
    task_type.Put(0x40, position.Data());
    for (std::size_t i = 0; i < tasks.size(); ++i) {
      tasks[i].Put(0x10, static_cast<std::int32_t>(kTask + i));
      tasks[i].Put(0x18, task_type.Data());
      tasks[i].Put(0x40, kIncumbent);
      tasks[i].Put(0x44, kOwner);
      task_slots[i + 1].object = tasks[i].Data();
    }
    character_storage.Put(0x20, character_slots.data());
    character_storage.Put(0x2C, std::int32_t{128});
    task_storage.Put(0x20, task_slots.data());
    task_storage.Put(0x2C, std::int32_t{128});
    character_storage_pointer = character_storage.Data();
    task_storage_pointer = task_storage.Data();
    rows[0] = reinterpret_cast<std::uintptr_t>(characters[16].Data());
    rows[1] = reinterpret_cast<std::uintptr_t>(characters[15].Data());
    constexpr std::string_view snapshot = "native:council12002";
    std::copy(snapshot.begin(), snapshot.end(), frame.snapshot_id.begin());
    frame.public_revision = 8; frame.native_revision = 7; frame.date_raw = 53178264;
    frame.paused = true; frame.map_ready = true; frame.has_played_character = true;
    frame.played_character_alive = true; frame.played_character_id = kOwner;
    frame.played_character = reinterpret_cast<std::uintptr_t>(characters[0].Data());
    environment = BindCouncilCandidates12002(0x140000000, kExecutableSha256);
    environment.offline_fixture_function_overrides = true;
    environment.character_storage_slot = &character_storage_pointer;
    environment.character_fallback_slot = &character_fallback;
    environment.active_task_storage_slot = &task_storage_pointer;
    environment.active_task_fallback_slot = &task_fallback;
    access.context = this;
    access.capture_frame = Capture;
    access.is_main_thread = MainThread;
    access.read_memory = Memory;
    access.initialize_vector = Initialize;
    access.invoke_producer = Produce;
    access.release_allocation = Release;
    request = {std::string_view(frame.snapshot_id.data()), frame.public_revision,
        frame.native_revision, frame.date_raw, kOwner};
  }

  CouncilCandidatesFixture12002(const CouncilCandidatesFixture12002 &) = delete;
  CouncilCandidatesFixture12002 &operator=(const CouncilCandidatesFixture12002 &) = delete;

  static bool MainThread(void *context) noexcept {
    return static_cast<CouncilCandidatesFixture12002 *>(context)->main_thread;
  }
  static bool Capture(void *context, CouncilCandidatesFrameV1 &output) noexcept {
    auto &f = *static_cast<CouncilCandidatesFixture12002 *>(context);
    ++f.capture_calls;
    output = f.frame;
    if (f.release_calls != 0) {
      if (f.drift_revision_after_release) ++output.native_revision;
      if (f.drift_date_after_release) ++output.date_raw;
    }
    return true;
  }
  static bool Span(const void *base, std::size_t size, const void *address,
                   std::size_t length) noexcept {
    const auto b = reinterpret_cast<std::uintptr_t>(base);
    const auto a = reinterpret_cast<std::uintptr_t>(address);
    return base != nullptr && address != nullptr && a >= b &&
           a - b <= size && length <= size - (a - b);
  }
  static bool Memory(void *context, const void *address, void *output,
                     std::size_t size) noexcept {
    auto &f = *static_cast<CouncilCandidatesFixture12002 *>(context);
    if (f.unreadable_candidate_skill && address ==
        static_cast<const std::byte *>(f.characters[15].Data()) + 0xE0) return false;
    const bool valid = Span(f.characters.data(), sizeof(f.characters), address, size) ||
        Span(&f.owner_extension, sizeof(f.owner_extension), address, size) ||
        Span(&f.position, sizeof(f.position), address, size) ||
        Span(&f.task_type, sizeof(f.task_type), address, size) ||
        Span(f.tasks.data(), sizeof(f.tasks), address, size) ||
        Span(&f.character_storage, sizeof(f.character_storage), address, size) ||
        Span(&f.task_storage, sizeof(f.task_storage), address, size) ||
        Span(f.character_slots.data(), sizeof(f.character_slots), address, size) ||
        Span(f.task_slots.data(), sizeof(f.task_slots), address, size) ||
        Span(f.task_ids.data(), sizeof(f.task_ids), address, size) ||
        Span(f.rows.data(), sizeof(f.rows), address, size) ||
        Span(&f.character_storage_pointer, sizeof(void *), address, size) ||
        Span(&f.character_fallback, sizeof(void *), address, size) ||
        Span(&f.task_storage_pointer, sizeof(void *), address, size) ||
        Span(&f.task_fallback, sizeof(void *), address, size) ||
        Span(kPosition, sizeof(kPosition), address, size) ||
        Span(f.allocator_address, f.allocator_size, address, size);
    if (!valid || output == nullptr) return false;
    std::memcpy(output, address, size);
    return true;
  }
  static bool Initialize(void *context, const CouncilCandidatesEnvironmentV1 &env,
      void *allocator, std::size_t size, CouncilCandidatesNativeVectorV1 &vector) noexcept {
    auto &f = *static_cast<CouncilCandidatesFixture12002 *>(context);
    f.allocator_address = allocator; f.allocator_size = size;
    std::uintptr_t vtable = 0, fallback = 0;
    std::memcpy(&vtable, allocator, sizeof(vtable));
    std::memcpy(&fallback, static_cast<std::byte *>(allocator) + 0x208, sizeof(fallback));
    f.allocator_shape_valid = size == 0x210 &&
        reinterpret_cast<std::uintptr_t>(allocator) % 16 == 0 &&
        vtable == env.module_base + kCouncilCandidatesAllocatorVtableRva12002 &&
        fallback == env.module_base + kCouncilCandidatesFallbackAllocatorRva12002;
    vector.data_address = reinterpret_cast<std::uintptr_t>(allocator) + 8;
    vector.capacity = 64; vector.count = 0; vector.allocator = allocator;
    return f.initialize_ok;
  }
  static bool Produce(void *context, const CouncilCandidatesEnvironmentV1 &,
      const void *owner, const void *task, bool gui,
      CouncilCandidatesNativeVectorV1 &vector) noexcept {
    auto &f = *static_cast<CouncilCandidatesFixture12002 *>(context);
    ++f.producer_calls;
    f.producer_inputs_valid = owner == f.characters[0].Data() &&
        task == f.tasks[0].Data() && gui;
    vector.count = f.count; vector.capacity = f.capacity;
    if (f.count > 64) vector.data_address = reinterpret_cast<std::uintptr_t>(f.rows.data());
    else if (f.count > 0)
      std::memcpy(reinterpret_cast<void *>(vector.data_address), f.rows.data(),
          static_cast<std::size_t>(f.count) * sizeof(std::uintptr_t));
    return f.producer_ok;
  }
  static bool Release(void *context, const CouncilCandidatesEnvironmentV1 &,
      CouncilCandidatesNativeVectorV1 &vector) noexcept {
    auto &f = *static_cast<CouncilCandidatesFixture12002 *>(context);
    ++f.release_calls;
    if (f.drift_incumbent_after_release) f.tasks[0].Put(0x40, std::int32_t{-1});
    const bool matched = vector.allocator == f.allocator_address &&
        (vector.data_address == reinterpret_cast<std::uintptr_t>(f.allocator_address) + 8 ||
         vector.data_address == reinterpret_cast<std::uintptr_t>(f.rows.data()));
    vector = {};
    return f.release_ok && matched;
  }
};

} // namespace xar::ck3_12002::test
