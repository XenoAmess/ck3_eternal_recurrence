#include "xar_bridge/prewar_levy_inventory12004.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12004_army_support.hpp"

#include <array>
#include <cstddef>
#include <cstring>
#include <utility>

#if defined(_WIN32) && defined(_MSC_VER)
#include <windows.h>
#endif

namespace xar::ck3_12004 {
namespace {

// Actual .4 disk reads: seven finite bodies / 3410 bytes, no whole-EXE read.
// All cached .3 decoded instruction boundaries and non-relative bytes match;
// actual relative calls/RIP operands were resolved independently. Frozen .4
// SHA is kExecutableSha256; local body pins (start, bytes, SHA-256):
// 2C175B0 203 480f10986cce3a21d14e6329eabc8f3823a9998bd13dd2580016ca0d59029e64
// 2C16E50 1141 a1b85d4e685975ea6d59cf55900594df12b251aede481c623a812e00493f0408
// 2C16BC0 641 16238b0511639515db8dcb1ab31252326b23e2352b169ee0506f136e36d64cff
// 2646D00 481 4bc53fa44bd706f31c84f1e225a0747ba22ac0da837996939984e9a44fd3e299
// 2C172D0 479 6287657f60d36ca5f53d0b6f7936affa6c8980475446f73557066d1b9b53d9da
// 2646EF0 153 298a346b9a567bb792ac161cbb1bab5899f0096ec3ad348fc2af48203e8f137d
// 2C10B60 312 9697d6dce1801feff5c918b26230cef0ba77a5ef9cbd35c7e618fba1dabd4037
// Existing actual .4 ctor/non-deleting destructor proof remains owned by
// research/ck3_1_20_0_4_army_support.json, reserve_lifetime. Old source manifests
// remain under army-regiment-composition-v71/owned-unraised-source and the
// army-reinforcement-raise reserve-lane/all-roster/EVIDENCE.v2.md contract.

constexpr std::uintptr_t kPersistentStorageRva = 0x5D1EB68;
constexpr std::uintptr_t kCompositionConstructorRva = 0xC6D5B0;
constexpr std::uintptr_t kCompositionDestructorRva = 0xB03250;
constexpr std::size_t kCompositionSize = 0xB8;
constexpr std::size_t kDescriptorVectorOffset = 0x50;
constexpr std::size_t kDescriptorStride = 0x18;
constexpr std::int32_t kMaximumDescriptors = 65'536;
constexpr std::int32_t kMaximumDatabaseCapacity = 1'000'000;

// /EHsc catch(...) does not contain a native access violation. These leaves
// own no C++ objects: a failed native call returns to the outer RAII scope,
// which can still release its successfully constructed temporary exactly once.
#if defined(_WIN32) && defined(_MSC_VER)
#define XAR_PREWAR_LEVY_TRY __try
#define XAR_PREWAR_LEVY_CATCH __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
#define XAR_PREWAR_LEVY_TRY try
#define XAR_PREWAR_LEVY_CATCH catch (...) { return false; }
#endif

bool CopyBytes(const void *object, std::size_t offset, void *output,
               std::size_t bytes) noexcept {
  if (object == nullptr || output == nullptr) return false;
  XAR_PREWAR_LEVY_TRY {
    std::memcpy(output, static_cast<const std::byte *>(object) + offset, bytes);
    return true;
  } XAR_PREWAR_LEVY_CATCH
}

bool ConstructComposition(const ck3_12003::PlayerArmyReserveBindingsV1 &bindings,
                          void *storage, void *&returned) noexcept {
  returned = nullptr;
  XAR_PREWAR_LEVY_TRY {
    returned = bindings.construct_empty(storage);
    return true;
  } XAR_PREWAR_LEVY_CATCH
}

bool CollectDescriptors(const PrewarLevyInventoryBindings12004 &bindings,
                        void *owner, void *vector) noexcept {
  XAR_PREWAR_LEVY_TRY {
    bindings.collect(owner, vector, 0xFU);
    return true;
  } XAR_PREWAR_LEVY_CATCH
}

bool CountDescriptors(const PrewarLevyInventoryBindings12004 &bindings,
                      void *vector, std::int32_t mode,
                      std::int32_t &output) noexcept {
  XAR_PREWAR_LEVY_TRY {
    output = bindings.count(vector, mode);
    return true;
  } XAR_PREWAR_LEVY_CATCH
}

bool DestroyComposition(const ck3_12003::PlayerArmyReserveBindingsV1 &bindings,
                        void *storage) noexcept {
  XAR_PREWAR_LEVY_TRY {
    bindings.destroy_contents(storage);
    return true;
  } XAR_PREWAR_LEVY_CATCH
}

bool ReadFrame(const ck3_12002::MilitaryWorldAccess &world,
               game::Snapshot &output) noexcept {
  XAR_PREWAR_LEVY_TRY {
    return world.read_snapshot(world.context, output);
  } XAR_PREWAR_LEVY_CATCH
}

bool ResolveCharacter(const ck3_12002::MilitaryWorldAccess &world,
                      std::int32_t id, void *&output) noexcept {
  output = nullptr;
  XAR_PREWAR_LEVY_TRY {
    output = world.resolve_character(world.context, id);
    return true;
  } XAR_PREWAR_LEVY_CATCH
}

bool ResolveProvince(const ck3_12002::MilitaryWorldAccess &world,
                     std::int32_t id, void *&output) noexcept {
  output = nullptr;
  XAR_PREWAR_LEVY_TRY {
    output = world.resolve_province(world.context, id);
    return true;
  } XAR_PREWAR_LEVY_CATCH
}

#undef XAR_PREWAR_LEVY_TRY
#undef XAR_PREWAR_LEVY_CATCH

template <class T> bool Read(const void *object, std::size_t offset,
                            T &output) noexcept {
  return CopyBytes(object, offset, &output, sizeof(output));
}

// Only caller-owned bytes already copied by CopyBytes may reach this helper.
template <class T> T FromCopied(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset,
              sizeof(value));
  return value;
}

struct PersistentStorage {
  const void *entries = nullptr;
  std::int32_t capacity = 0;
};

bool ReadStorage(void **slot, PersistentStorage &out) noexcept {
  void *storage = nullptr;
  if (!Read(slot, 0, storage) || storage == nullptr ||
      !Read(storage, 0x20, out.entries) ||
      !Read(storage, 0x2C, out.capacity)) return false;
  return out.capacity >= 0 && out.capacity <= kMaximumDatabaseCapacity &&
      (out.capacity == 0 || out.entries != nullptr);
}

void *ResolveRegiment(const PersistentStorage &storage, std::int32_t id,
                     std::optional<std::int32_t> &observed_id) noexcept {
  if (id == -1) return nullptr;
  const auto index = static_cast<std::uint32_t>(id) & 0xFFFFFFU;
  if (index >= static_cast<std::uint32_t>(storage.capacity)) return nullptr;
  void *object = nullptr;
  std::int32_t actual = -1;
  std::uint32_t magic = 0;
  if (!Read(storage.entries, static_cast<std::size_t>(index) * 0x10 + 8, object) ||
      object == nullptr || !Read(object, 0x10, actual)) return nullptr;
  observed_id = actual;
  return actual == id && Read(object, 0x14, magic) && magic == 0x52656769U
      ? object : nullptr;
}

struct CompositionLifetime {
  const ck3_12003::PlayerArmyReserveBindingsV1 &bindings;
  void *storage = nullptr;
  bool active = false;
  bool Close() noexcept {
    if (!active) return false;
    // Never retry native cleanup against partly destroyed storage.
    active = false;
    return DestroyComposition(bindings, storage);
  }
  ~CompositionLifetime() { if (active) (void)Close(); }
};

bool BindingMatches(const PrewarLevyInventoryBindings12004 &bindings) noexcept {
  const auto base = bindings.module_base;
  return bindings.enabled && base != 0 && bindings.lifetime.enabled &&
      reinterpret_cast<std::uintptr_t>(bindings.persistent_regiment_storage_slot) ==
          base + kPersistentStorageRva &&
      reinterpret_cast<std::uintptr_t>(bindings.collect) ==
          base + kPrewarLevyCollectorRva12004 &&
      reinterpret_cast<std::uintptr_t>(bindings.count) ==
          base + kPrewarLevyCountRva12004 &&
      reinterpret_cast<std::uintptr_t>(bindings.lifetime.construct_empty) ==
          base + kCompositionConstructorRva &&
      reinterpret_cast<std::uintptr_t>(bindings.lifetime.destroy_contents) ==
          base + kCompositionDestructorRva;
}

bool FrameMatches(const game::Snapshot &frame,
                  const PrewarLevyInventoryRequest12004 &request) noexcept {
  return request.snapshot_revision != 0 && frame.paused && frame.map_ready &&
      frame.has_played_character && frame.played_character_alive &&
      frame.played_character_id == request.actor_character_id &&
      frame.date_raw == request.date_raw;
}

void ReadDescriptor(const PrewarLevyInventoryBindings12004 &bindings,
                    const ck3_12002::MilitaryWorldAccess &world,
                    const PersistentStorage &storage, bool storage_ready,
                    const void *source, PrewarLevyDescriptor12004 &row) {
  std::array<std::byte, kDescriptorStride> descriptor_bytes{};
  if (!CopyBytes(source, 0, descriptor_bytes.data(), descriptor_bytes.size())) {
    row.failure = "levy_descriptor_unreadable";
    return;
  }
  const void *descriptor = descriptor_bytes.data();
  const auto vtable = FromCopied<std::uintptr_t>(descriptor, 0);
  if (vtable >= bindings.module_base)
    row.descriptor_vtable_rva = vtable - bindings.module_base;
  row.descriptor_identity_ready =
      vtable == bindings.module_base + kPrewarLevyDescriptorVtableRva12004;
  row.persistent_regiment_id = FromCopied<std::int32_t>(descriptor, 0x08);
  row.chunk_ordinal = FromCopied<std::int32_t>(descriptor, 0x0C);
  row.contribution_cap_raw = FromCopied<std::int32_t>(descriptor, 0x10);
  row.flag14_raw = FromCopied<std::uint8_t>(descriptor, 0x14);
  row.flag15_raw = FromCopied<std::uint8_t>(descriptor, 0x15);
  if (!row.descriptor_identity_ready || *row.chunk_ordinal < 0 ||
      *row.chunk_ordinal >= 7 || *row.contribution_cap_raw < 0) {
    row.failure = "levy_descriptor_fields_invalid";
    return;
  }
  void *regiment = storage_ready
      ? ResolveRegiment(storage, *row.persistent_regiment_id,
                        row.observed_persistent_full_id) : nullptr;
  if (regiment == nullptr) {
    row.failure = "levy_persistent_full_generation_unavailable";
    return;
  }
  std::int32_t owner_id = -1;
  if (!Read(regiment, 0x12C, owner_id)) {
    row.failure = "levy_persistent_owner_unreadable";
    return;
  }
  row.persistent_owner_character_id = owner_id;
  const auto offset = 0x18 + static_cast<std::size_t>(*row.chunk_ordinal) * 0x24;
  std::array<std::byte, 0x1C> chunk_bytes{};
  if (!CopyBytes(regiment, offset, chunk_bytes.data(), chunk_bytes.size())) {
    row.failure = "levy_chunk_unreadable";
    return;
  }
  const void *chunk = chunk_bytes.data();
  row.maximum_soldiers_raw = FromCopied<std::int32_t>(chunk, 0);
  row.current_soldiers_raw = FromCopied<std::int32_t>(chunk, 4);
  row.chunk_persistent_backlink = FromCopied<std::int32_t>(chunk, 8);
  row.native_chunk_ordinal = FromCopied<std::int32_t>(chunk, 0x0C);
  row.army_regiment_id = FromCopied<std::int32_t>(chunk, 0x10);
  row.pending_raw = FromCopied<std::uint8_t>(chunk, 0x14);
  row.state_raw = FromCopied<std::int32_t>(chunk, 0x18);
  row.physical_fields_ready = *row.maximum_soldiers_raw >= 0 &&
      *row.current_soldiers_raw >= 0 &&
      *row.chunk_persistent_backlink == *row.persistent_regiment_id &&
      *row.native_chunk_ordinal == *row.chunk_ordinal;
  if (!row.physical_fields_ready) {
    row.failure = "levy_chunk_physical_fields_invalid";
    return;
  }
  // The stock count follows this chunk's persistent backlink to its Province;
  // qualify that exact native input before invoking its unbounded ordinal ABI.
  void *province = nullptr;
  std::uint32_t province_magic = 0;
  std::int32_t province_id = -1;
  if (!Read(regiment, 0x120, province) || province == nullptr ||
      !Read(province, 0x85C, province_magic) || province_magic != 0x50726F76U ||
      !Read(province, 0x10, province_id)) {
    row.failure = "levy_count_province_unavailable";
    return;
  }
  row.source_province_id = province_id;
  void *resolved = nullptr;
  row.native_count_inputs_ready = world.resolve_province != nullptr &&
      ResolveProvince(world, province_id, resolved) && resolved == province;
  if (!row.native_count_inputs_ready)
    row.failure = "levy_count_province_full_generation_unavailable";
}

void WithdrawReadiness(PrewarLevyInventorySnapshot12004 &output) {
  output.owner_identity_ready = false;
  output.collection_complete = false;
  output.native_counts_ready = false;
  for (auto &row : output.descriptors) {
    row.descriptor_identity_ready = false;
    row.physical_fields_ready = false;
    row.native_count_inputs_ready = false;
  }
}

} // namespace

PrewarLevyInventoryBindings12004 BindPrewarLevyInventoryImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256,
    const ck3_12002::ArmyBindings &armies) noexcept {
  PrewarLevyInventoryBindings12004 bindings{};
  if (image_base == 0 || executable_sha256 != kExecutableSha256 ||
      !armies.enabled ||
      reinterpret_cast<std::uintptr_t>(armies.persistent_regiment_storage_slot) !=
          image_base + kPersistentStorageRva) return bindings;
  bindings.module_base = image_base;
  bindings.persistent_regiment_storage_slot = armies.persistent_regiment_storage_slot;
  bindings.lifetime = BindPlayerArmyReserveImage12004V1(image_base, executable_sha256);
  bindings.collect = reinterpret_cast<decltype(bindings.collect)>(
      image_base + kPrewarLevyCollectorRva12004);
  bindings.count = reinterpret_cast<decltype(bindings.count)>(
      image_base + kPrewarLevyCountRva12004);
  bindings.enabled = bindings.lifetime.enabled;
  return bindings;
}

PrewarLevyInventoryStatus12004 ReadPrewarLevyInventory12004(
    const PrewarLevyInventoryBindings12004 &bindings,
    const ck3_12002::MilitaryWorldAccess &world,
    const PrewarLevyInventoryRequest12004 &request,
    PrewarLevyInventorySnapshot12004 &output) noexcept {
  output = {};
  output.snapshot_revision = request.snapshot_revision;
  output.date_raw = request.date_raw;
  output.actor_character_id = request.actor_character_id;
  output.owner_character_id = request.owner_character_id;
  try {
    if (!BindingMatches(bindings)) {
      output.failure = "exact_12004_levy_bindings_required";
      return output.status;
    }
    output.exact_build_ready = true;
    if (request.owner_character_id == -1 || request.actor_character_id <= 0 ||
        world.read_snapshot == nullptr || world.resolve_character == nullptr) {
      output.failure = "levy_subject_request_unavailable";
      return output.status;
    }
    game::Snapshot before{};
    if (!ReadFrame(world, before) || !FrameMatches(before, request)) {
      output.failure = "paused_actor_frame_unavailable";
      return output.status;
    }
    void *owner = nullptr;
    std::int32_t owner_id = -1;
    std::uint32_t owner_magic = 0;
    output.owner_identity_ready =
        ResolveCharacter(world, request.owner_character_id, owner) && owner != nullptr &&
        Read(owner, 0x18, owner_id) && owner_id == request.owner_character_id &&
        Read(owner, 0x1C, owner_magic) && owner_magic == 0x43686172U;
    if (!output.owner_identity_ready) {
      output.failure = "levy_subject_full_generation_unavailable";
      return output.status;
    }
    alignas(16) std::array<std::byte, kCompositionSize> temporary{};
    CompositionLifetime lifetime{bindings.lifetime, temporary.data(), false};
    void *constructed = nullptr;
    if (!ConstructComposition(bindings.lifetime, temporary.data(), constructed) ||
        constructed != temporary.data()) {
      output.failure = "levy_temporary_constructor_unavailable";
      return output.status;
    }
    lifetime.active = true;
    void *vector = temporary.data() + kDescriptorVectorOffset;
    std::uintptr_t allocator_before = 0;
    const bool collected = Read(vector, 0x10, allocator_before) &&
        allocator_before != 0 && CollectDescriptors(bindings, owner, vector);
    std::array<std::byte, 0x18> vector_bytes{};
    const bool header_read = collected &&
        CopyBytes(vector, 0, vector_bytes.data(), vector_bytes.size());
    const void *data = header_read
        ? FromCopied<const void *>(vector_bytes.data(), 0) : nullptr;
    const auto capacity = header_read
        ? FromCopied<std::int32_t>(vector_bytes.data(), 8) : -1;
    const auto count = header_read
        ? FromCopied<std::int32_t>(vector_bytes.data(), 0x0C) : -1;
    if (header_read) output.source_count = count;
    bool complete = header_read && capacity >= 0 && count >= 0 && count <= capacity &&
        capacity <= kMaximumDescriptors && (count == 0 || data != nullptr) &&
        allocator_before != 0 &&
        FromCopied<std::uintptr_t>(vector_bytes.data(), 0x10) == allocator_before;
    if (!complete) {
      output.failure = "levy_descriptor_vector_unavailable";
    } else {
      output.collection_complete = true;
      PersistentStorage storage{};
      const bool storage_ready = ReadStorage(bindings.persistent_regiment_storage_slot, storage);
      output.descriptors.reserve(static_cast<std::size_t>(count));
      for (std::int32_t index = 0; index < count; ++index) {
        PrewarLevyDescriptor12004 row{};
        row.source_ordinal = index;
        ReadDescriptor(bindings, world, storage, storage_ready,
            static_cast<const std::byte *>(data) +
                static_cast<std::size_t>(index) * kDescriptorStride, row);
        complete = complete && row.native_count_inputs_ready;
        output.descriptors.push_back(std::move(row));
      }
      // Never pass unchecked/stale descriptors or an out-of-bounds ordinal to
      // the stock getter. Preserve the copied rows when a count is unavailable.
      if (complete) {
        std::int32_t mode0 = 0;
        std::int32_t mode1 = 0;
        const bool mode0_read = CountDescriptors(bindings, vector, 0, mode0);
        if (mode0_read) output.native_mode0_count = mode0;
        const bool mode1_read = CountDescriptors(bindings, vector, 1, mode1);
        if (mode1_read) output.native_mode1_count = mode1;
        output.native_counts_ready = mode0_read && mode1_read && mode0 >= 0 && mode1 >= 0;
        complete = output.native_counts_ready;
      }
      if (!complete) output.failure = "levy_descriptor_inputs_partial";
    }
    output.cleanup_ready = lifetime.Close();
    game::Snapshot after{};
    void *owner_after = nullptr;
    output.source_frame_ready = ReadFrame(world, after) &&
        FrameMatches(after, request) && after == before &&
        ResolveCharacter(world, request.owner_character_id, owner_after) && owner_after == owner;
    if (!output.cleanup_ready || !output.source_frame_ready) {
      WithdrawReadiness(output);
      output.failure = !output.cleanup_ready ? "levy_temporary_cleanup_unavailable"
                                            : "source_snapshot_changed";
      return output.status;
    }
    output.status = complete ? PrewarLevyInventoryStatus12004::available
                             : PrewarLevyInventoryStatus12004::partial;
    return output.status;
  } catch (...) {
    WithdrawReadiness(output);
    output.source_frame_ready = false;
    output.status = PrewarLevyInventoryStatus12004::unavailable;
    output.failure = "levy_inventory_sample_exception";
    return output.status;
  }
}

} // namespace xar::ck3_12004
