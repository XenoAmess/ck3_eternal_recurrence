#include "xar_bridge/prewar_owner_inventory12004.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12004_army_support.hpp"

#include <array>
#include <cstddef>
#include <cstring>
#include <limits>
#include <set>
#include <type_traits>
#include <utility>

#if defined(_MSC_VER)
#include <Windows.h>
#endif

namespace xar::ck3_12004 {
namespace {

constexpr std::int32_t kMaximumStorageCapacity = 1'000'000;
constexpr std::int32_t kMaximumCollectionEntries = 65'536;
constexpr std::int32_t kMaximumPersistentRows = 16'384;

// SEH stays in trivial leaves: /EHsc catch(...) alone cannot handle a native
// access violation and must not bypass the caller's native-content cleanup.
template <class T>
bool TryRead(const void *object, std::size_t offset, T &output) noexcept {
  static_assert(std::is_trivially_copyable_v<T>);
  if (object == nullptr) return false;
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(&output, static_cast<const std::byte *>(object) + offset, sizeof(T));
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}

template <class T>
std::optional<T> CopyAt(const void *object, std::size_t offset) noexcept {
  T value{};
  return TryRead(object, offset, value) ? std::optional<T>(value) : std::nullopt;
}

bool TryConstruct(void *(*callback)(void *), void *object, void *&returned) noexcept {
  returned = nullptr;
  if (callback == nullptr) return false;
#if defined(_MSC_VER)
  __try {
#endif
    returned = callback(object);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}

bool TryInitialize(void (*callback)(void *, void *), void *object, void *owner) noexcept {
  if (callback == nullptr || object == nullptr || owner == nullptr) return false;
#if defined(_MSC_VER)
  __try {
#endif
    callback(object, owner);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}

bool TryCount(std::int32_t (*callback)(void *), void *object, std::int32_t &value) noexcept {
  if (callback == nullptr || object == nullptr) return false;
#if defined(_MSC_VER)
  __try {
#endif
    value = callback(object);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}

bool TryCleanup(void (*callback)(void *), void *object) noexcept {
  if (callback == nullptr || object == nullptr) return false;
#if defined(_MSC_VER)
  __try {
#endif
    callback(object);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}

bool TryDomicileCurrent(std::int64_t *(*callback)(void *, std::int64_t *),
                        void *domicile, std::int64_t &value,
                        bool &out_echo) noexcept {
  out_echo = false;
  if (callback == nullptr || domicile == nullptr) return false;
#if defined(_MSC_VER)
  __try {
#endif
    out_echo = callback(domicile, &value) == &value;
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}

bool TryTypePredicate(bool (*callback)(void *), void *character,
                      bool &value) noexcept {
  if (callback == nullptr || character == nullptr) return false;
#if defined(_MSC_VER)
  __try {
#endif
    value = callback(character);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}

bool TryResolveCharacter(const ck3_12002::MilitaryWorldAccess &world,
                         std::int32_t id, void *&character) noexcept {
  character = nullptr;
  if (id == -1 || world.resolve_character == nullptr) return false;
#if defined(_MSC_VER)
  __try {
#endif
    character = world.resolve_character(world.context, id);
    return character != nullptr;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}

bool TryReadFrame(const ck3_12002::MilitaryWorldAccess &world,
                  game::Snapshot &frame) noexcept {
  if (world.read_snapshot == nullptr) return false;
#if defined(_MSC_VER)
  __try {
#endif
    return world.read_snapshot(world.context, frame);
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}

struct CompositionLease {
  const ck3_12003::PlayerArmyReserveBindingsV1 &bindings;
  void *object = nullptr;
  bool active = false;
  bool cleanup_attempted = false;
  bool cleanup_succeeded = false;

  bool Close() noexcept {
    if (!active) return cleanup_succeeded;
    // A failed native cleanup must never be called a second time.
    active = false;
    cleanup_attempted = true;
    cleanup_succeeded = TryCleanup(bindings.destroy_contents, object);
    return cleanup_succeeded;
  }
  ~CompositionLease() { if (active) (void)Close(); }
};

bool FrameMatches(const game::Snapshot &frame,
                  const PrewarOwnerInventoryRequest12004 &request) noexcept {
  return request.snapshot_revision != 0 && request.actor_character_id > 0 &&
      frame.paused && frame.map_ready && frame.has_played_character &&
      frame.played_character_alive &&
      frame.played_character_id == request.actor_character_id &&
      frame.date_raw == request.date_raw;
}

struct Registry {
  const void *entries = nullptr;
  std::int32_t capacity = 0;
};

bool ReadRegistry(void **slot, Registry &out) noexcept {
  void *storage = nullptr;
  return TryRead(slot, 0, storage) && storage != nullptr &&
      TryRead(storage, 0x20, out.entries) &&
      TryRead(storage, 0x2C, out.capacity) && out.capacity >= 0 &&
      out.capacity <= kMaximumStorageCapacity &&
      (out.capacity == 0 || out.entries != nullptr);
}

void *ResolveRegistry(const Registry &registry, std::int32_t id,
                      std::optional<std::int32_t> &observed_id,
                      std::optional<std::uint32_t> &observed_magic) noexcept {
  if (id == -1) return nullptr;
  const auto index = static_cast<std::uint32_t>(id) & 0xFFFFFFU;
  if (index >= static_cast<std::uint32_t>(registry.capacity)) return nullptr;
  void *object = nullptr;
  if (!TryRead(registry.entries, static_cast<std::size_t>(index) * 0x10 + 8, object) ||
      object == nullptr) return nullptr;
  observed_id = CopyAt<std::int32_t>(object, 0x10);
  observed_magic = CopyAt<std::uint32_t>(object, 0x14);
  return observed_id == id ? object : nullptr;
}

void CopyIdCollection(void *composition, std::size_t member,
                      PrewarOwnerIdCollection12004 &out) {
  const void *data = nullptr;
  if (TryRead(composition, member, data)) out.data_present = data != nullptr;
  out.capacity = CopyAt<std::int32_t>(composition, member + 8);
  out.count = CopyAt<std::int32_t>(composition, member + 0xC);
  out.header_read_complete = out.data_present.has_value() &&
      out.capacity.has_value() && out.count.has_value();
  if (!out.header_read_complete) {
    out.failure = "collection_header_unread";
    return;
  }
  if (*out.capacity < 0 || *out.capacity > kMaximumStorageCapacity ||
      *out.count < 0 || *out.count > *out.capacity ||
      *out.count > kMaximumCollectionEntries || (*out.count != 0 && data == nullptr)) {
    out.failure = "collection_header_or_budget_invalid";
    return;
  }
  std::set<std::int32_t> seen;
  for (std::int32_t index = 0; index < *out.count; ++index) {
    std::int32_t id = -1;
    if (!TryRead(data, static_cast<std::size_t>(index) * 4, id)) {
      out.failure = "collection_entry_unread";
      return;
    }
    out.full_ids.push_back(id);
    if (seen.insert(id).second) out.unique_full_ids.push_back(id);
    else ++out.duplicate_full_id_occurrences;
  }
  out.entries_copied_complete = true;
}

void CopyPersistent(const Registry &registry, bool registry_ready,
                    std::int32_t id, std::int32_t occurrence,
                    PrewarOwnerPersistentRegiment12004 &row) {
  row.occurrence_index = occurrence;
  row.persistent_regiment_id = id;
  if (!registry_ready) {
    row.failure = "persistent_registry_unavailable";
    return;
  }
  void *regiment = ResolveRegistry(registry, id, row.observed_full_id, row.observed_magic);
  row.full_generation_ready = regiment != nullptr && row.observed_magic == 0x52656769U;
  if (!row.full_generation_ready) {
    row.failure = "persistent_full_generation_or_magic_invalid";
    return;
  }
  row.native_owner_character_id = CopyAt<std::int32_t>(regiment, 0x12C);
  row.native_capacity_raw = CopyAt<std::int32_t>(regiment, 0x128);
  row.atoms_read_complete = row.native_owner_character_id.has_value() &&
      row.native_capacity_raw.has_value();
  for (std::int32_t index = 0; index < 7; ++index) {
    const auto offset = 0x18 + static_cast<std::size_t>(index) * 0x24;
    PrewarOwnerPersistentChunk12004 chunk{};
    chunk.chunk_index = index;
    chunk.maximum_soldiers_raw = CopyAt<std::int32_t>(regiment, offset);
    chunk.current_soldiers_raw = CopyAt<std::int32_t>(regiment, offset + 4);
    chunk.persistent_regiment_id_raw = CopyAt<std::int32_t>(regiment, offset + 8);
    chunk.native_ordinal_raw = CopyAt<std::int32_t>(regiment, offset + 0xC);
    chunk.army_regiment_id_raw = CopyAt<std::int32_t>(regiment, offset + 0x10);
    chunk.pending_raw = CopyAt<std::uint8_t>(regiment, offset + 0x14);
    chunk.state_raw = CopyAt<std::int32_t>(regiment, offset + 0x18);
    chunk.atoms_read_complete = chunk.maximum_soldiers_raw.has_value() &&
        chunk.current_soldiers_raw.has_value() && chunk.persistent_regiment_id_raw.has_value() &&
        chunk.native_ordinal_raw.has_value() && chunk.army_regiment_id_raw.has_value() &&
        chunk.pending_raw.has_value() && chunk.state_raw.has_value();
    if (!chunk.atoms_read_complete) chunk.failure = "persistent_chunk_atoms_unread";
    row.atoms_read_complete = row.atoms_read_complete && chunk.atoms_read_complete;
    row.chunks.push_back(std::move(chunk));
  }
  if (!row.atoms_read_complete) row.failure = "persistent_atoms_unread";
}

void CopyKnight(const ck3_12002::MilitaryWorldAccess &world,
                std::int32_t id, std::int32_t occurrence,
                PrewarOwnerKnight12004 &row) {
  row.occurrence_index = occurrence;
  row.character_id = id;
  void *character = nullptr;
  if (!TryResolveCharacter(world, id, character)) {
    row.failure = "knight_character_unavailable";
    return;
  }
  row.observed_full_id = CopyAt<std::int32_t>(character, 0x18);
  row.observed_magic = CopyAt<std::uint32_t>(character, 0x1C);
  row.full_generation_ready = row.observed_full_id == id && row.observed_magic == 0x43686172U;
  if (!row.full_generation_ready) {
    row.failure = "knight_full_generation_or_magic_invalid";
    return;
  }
  void *component = nullptr;
  if (TryRead(character, 0x1B8, component)) {
    row.assignment_component_present = component != nullptr;
    if (component != nullptr) row.army_regiment_id_raw = CopyAt<std::int32_t>(component, 0xF8);
  }
  row.atoms_read_complete = row.assignment_component_present.has_value() &&
      (!*row.assignment_component_present || row.army_regiment_id_raw.has_value());
  if (!row.atoms_read_complete) row.failure = "knight_assignment_atoms_unread";
}

void CopyArmyRegiment(const Registry &registry, bool registry_ready,
                      std::int32_t id, std::int32_t occurrence,
                      PrewarOwnerArmyRegiment12004 &row) {
  row.occurrence_index = occurrence;
  row.army_regiment_id = id;
  if (!registry_ready) {
    row.failure = "army_regiment_registry_unavailable";
    return;
  }
  void *regiment = ResolveRegistry(registry, id, row.observed_full_id, row.observed_magic);
  row.full_generation_ready = regiment != nullptr && row.observed_magic == 0x41725267U;
  if (!row.full_generation_ready) {
    row.failure = "army_regiment_full_generation_or_magic_invalid";
    return;
  }
  row.current_soldiers_raw = CopyAt<std::int32_t>(regiment, 0x38);
  row.maximum_soldiers_raw = CopyAt<std::int32_t>(regiment, 0x3C);
  row.native_carmy_id_raw = CopyAt<std::int32_t>(regiment, 0x140);
  row.atoms_read_complete = row.current_soldiers_raw.has_value() &&
      row.maximum_soldiers_raw.has_value() && row.native_carmy_id_raw.has_value();
  if (!row.atoms_read_complete) row.failure = "army_regiment_atoms_unread";
}

bool FitsInt32(std::int64_t value) noexcept {
  return value >= std::numeric_limits<std::int32_t>::min() &&
      value <= std::numeric_limits<std::int32_t>::max();
}

bool AddCheckedInt32(std::int64_t &accumulator, std::int64_t delta) noexcept {
  if (!FitsInt32(delta) || !FitsInt32(accumulator)) return false;
  const auto next = accumulator + delta; // Two signed32 operands fit signed64.
  if (!FitsInt32(next)) return false;
  accumulator = next;
  return true;
}

bool DomicileRegimentCurrent(const PrewarOwnerPersistentRegiment12004 &row,
                             std::int64_t &value) noexcept {
  if (!row.full_generation_ready || !row.atoms_read_complete ||
      !row.native_capacity_raw.has_value() || *row.native_capacity_raw < 0 ||
      row.chunks.size() != 7) return false;
  value = *row.native_capacity_raw;
  for (const auto &chunk : row.chunks) {
    if (!chunk.atoms_read_complete || !chunk.maximum_soldiers_raw.has_value() ||
        !chunk.current_soldiers_raw.has_value() || !chunk.state_raw.has_value() ||
        *chunk.maximum_soldiers_raw < 0 || *chunk.current_soldiers_raw < 0)
      return false;
    const std::int64_t maximum = *chunk.maximum_soldiers_raw;
    // Exact 25B8A50 skips max==0 even when that chunk's current is positive.
    if (maximum == 0) continue;
    const std::int64_t effective = *chunk.state_raw == 3 &&
        *chunk.current_soldiers_raw == 0 ? maximum : *chunk.current_soldiers_raw;
    if (!AddCheckedInt32(value, effective - maximum)) return false;
  }
  return value >= 0;
}

void CopyDomicile(const PrewarOwnerInventoryBindings12004 &bindings,
                  const ck3_12002::MilitaryWorldAccess &world,
                  void *requested_owner, const Registry &persistent_registry,
                  bool persistent_registry_ready, PrewarOwnerDomicile12004 &out) {
  out.assigned_regiment_ids.source_member = "native_Domi_owner_military+2A8_Regi_ids";
  void *realm = nullptr;
  if (!TryRead(requested_owner, 0x1C8, realm)) {
    out.failure = "domicile_association_realm_unread";
    return;
  }
  out.realm_present = realm != nullptr;
  if (realm == nullptr) {
    // Empty unique associated-Domi namespace, not a native fallback reading.
    out.association_read_complete = true;
    out.association_empty = true;
    out.current_upper_soldiers = 0;
    out.current_ready = true;
    return;
  }
  out.domicile_id = CopyAt<std::int32_t>(realm, 0xB68);
  if (!out.domicile_id.has_value()) {
    out.failure = "domicile_association_id_unread";
    return;
  }
  out.association_read_complete = true;
  if (*out.domicile_id == -1) {
    out.association_empty = true;
    out.current_upper_soldiers = 0;
    out.current_ready = true;
    return;
  }
  Registry domicile_registry{};
  if (!ReadRegistry(bindings.domicile_storage_slot, domicile_registry)) {
    out.failure = "domicile_registry_unavailable";
    return;
  }
  const auto index = static_cast<std::uint32_t>(*out.domicile_id) & 0xFFFFFFU;
  void *domicile = nullptr;
  if (index >= static_cast<std::uint32_t>(domicile_registry.capacity) ||
      !TryRead(domicile_registry.entries, static_cast<std::size_t>(index) * 0x10 + 8, domicile) ||
      domicile == nullptr) {
    out.failure = "domicile_full_generation_unavailable";
    return;
  }
  out.observed_full_id = CopyAt<std::int32_t>(domicile, 8);
  out.observed_magic = CopyAt<std::uint32_t>(domicile, 0xC);
  out.full_generation_ready = out.observed_full_id == out.domicile_id &&
      out.observed_magic == 0x446F6D69U;
  if (!out.full_generation_ready) {
    out.failure = "domicile_full_generation_or_magic_invalid";
    return;
  }
  out.native_owner_character_id = CopyAt<std::int32_t>(domicile, 0x20);
  void *type = nullptr;
  if (TryRead(domicile, 0x30, type)) {
    out.domicile_type_present = type != nullptr;
    if (type != nullptr) out.type_flag_17e = CopyAt<std::uint8_t>(type, 0x17E);
  }
  void *native_owner = nullptr;
  if (out.native_owner_character_id.has_value() &&
      TryResolveCharacter(world, *out.native_owner_character_id, native_owner)) {
    out.observed_native_owner_full_id = CopyAt<std::int32_t>(native_owner, 0x18);
    out.observed_native_owner_magic = CopyAt<std::uint32_t>(native_owner, 0x1C);
    out.native_owner_identity_ready =
        out.observed_native_owner_full_id == out.native_owner_character_id &&
        out.observed_native_owner_magic == 0x43686172U;
  }
  if (!out.native_owner_identity_ready) {
    out.failure = "domicile_source_owner_full_generation_invalid";
    return;
  }
  bool predicate = false;
  if (TryTypePredicate(bindings.domicile_owner_type_predicate, native_owner, predicate))
    out.native_owner_type_predicate = predicate;
  if (!out.native_owner_type_predicate.has_value()) {
    out.failure = "domicile_source_owner_type_predicate_unavailable";
    return;
  }
  if (!predicate) {
    out.assigned_branch = false;
    out.assigned_atoms_read_complete = true; // Native branch does not read this list.
  } else {
    void *military = nullptr;
    if (TryRead(native_owner, 0x1C0, military))
      out.assigned_owner_military_present = military != nullptr;
    if (!out.assigned_owner_military_present.has_value() || military == nullptr) {
      out.failure = "domicile_assigned_military_unavailable";
      return;
    }
    CopyIdCollection(military, 0x2A8, out.assigned_regiment_ids);
    if (!out.assigned_regiment_ids.entries_copied_complete ||
        !out.assigned_regiment_ids.count.has_value()) {
      out.failure = "domicile_assigned_collection_unavailable";
      return;
    }
    out.assigned_branch = *out.assigned_regiment_ids.count != 0;
    out.assigned_atoms_read_complete = out.assigned_regiment_ids.full_ids.size() <=
        static_cast<std::size_t>(kMaximumPersistentRows);
    std::int64_t total = 0;
    bool arithmetic_ready = out.assigned_atoms_read_complete;
    std::int32_t occurrence = 0;
    for (const auto id : out.assigned_regiment_ids.full_ids) {
      if (occurrence >= kMaximumPersistentRows) break;
      PrewarOwnerPersistentRegiment12004 row{};
      CopyPersistent(persistent_registry, persistent_registry_ready, id, occurrence++, row);
      out.assigned_atoms_read_complete = out.assigned_atoms_read_complete &&
          row.full_generation_ready && row.atoms_read_complete;
      std::int64_t current = 0;
      const bool row_arithmetic_ready = DomicileRegimentCurrent(row, current);
      arithmetic_ready = arithmetic_ready && row_arithmetic_ready;
      if (row_arithmetic_ready && !AddCheckedInt32(total, current)) arithmetic_ready = false;
      out.assigned_regiments.push_back(std::move(row));
    }
    if (arithmetic_ready) out.assigned_current_accumulator = total;
    out.assigned_accumulator_int32_ready = arithmetic_ready && out.assigned_atoms_read_complete;
  }
  std::int64_t native_raw = 0;
  out.native_current_call_succeeded = TryDomicileCurrent(bindings.domicile_current,
      domicile, native_raw, out.native_out_echo_ready);
  if (out.native_current_call_succeeded) out.native_current_raw_q100000 = native_raw;
  const bool scalar_ready = out.native_current_call_succeeded && out.native_out_echo_ready &&
      native_raw >= 0;
  const bool assigned_ready = out.assigned_branch.has_value() &&
      (!*out.assigned_branch ||
       (out.assigned_atoms_read_complete && out.assigned_accumulator_int32_ready &&
        out.assigned_current_accumulator.has_value() &&
        native_raw == *out.assigned_current_accumulator * 100'000));
  out.current_ready = scalar_ready && assigned_ready;
  if (out.current_ready)
    out.current_upper_soldiers = native_raw / 100'000 + (native_raw % 100'000 != 0);
  else out.failure = !scalar_ready ? "domicile_current_getter_unavailable_or_invalid"
                                  : "domicile_assigned_current_arithmetic_unqualified";
}

void WithdrawQualification(PrewarOwnerInventory12004 &out) noexcept {
  out.owner_identity_ready = false;
  out.owner_echo_ready = false;
  out.native_lifetime_ready = false;
  out.native_all_unraised_stock_ready = false;
  out.raw_capture_complete = false;
  out.current_count_atoms_valid = false;
  out.owner_stock_inventory_complete = false;
  out.persistent_atoms_read_complete = false;
  out.knight_atoms_read_complete = false;
  out.raised_atoms_read_complete = false;
  out.overall_current_inventory_complete = false;
  out.current_inventory_lower_bound.reset();
  out.current_inventory_upper_bound.reset();
  out.domicile.current_ready = false;
  out.domicile.current_upper_soldiers.reset();
}

} // namespace

PrewarOwnerInventoryBindings12004 BindPrewarOwnerInventoryImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256,
    const ck3_12002::ArmyBindings &actual4_armies) noexcept {
  PrewarOwnerInventoryBindings12004 out{};
  if (image_base == 0 || executable_sha256 != kExecutableSha256 || !actual4_armies.enabled)
    return out;
  out.composition = BindPlayerArmyReserveImage12004V1(image_base, executable_sha256);
  out.persistent_regiment_storage_slot = actual4_armies.persistent_regiment_storage_slot;
  out.army_regiment_storage_slot = actual4_armies.regiment_storage_slot;
  out.domicile_storage_slot = reinterpret_cast<void **>(image_base + 0x5D1EB80);
  out.domicile_current = reinterpret_cast<decltype(out.domicile_current)>(image_base + 0x25B8A50);
  out.domicile_owner_type_predicate =
      reinterpret_cast<decltype(out.domicile_owner_type_predicate)>(image_base + 0x2B9D2B0);
  out.enabled = out.composition.enabled;
  return out;
}

PrewarOwnerInventoryStatus12004 ReadPrewarOwnerInventory12004(
    const PrewarOwnerInventoryBindings12004 &bindings,
    const ck3_12002::MilitaryWorldAccess &world,
    const PrewarOwnerInventoryRequest12004 &request,
    PrewarOwnerInventory12004 &output) noexcept {
  output = {};
  output.snapshot_revision = request.snapshot_revision;
  output.date_raw = request.date_raw;
  output.actor_character_id = request.actor_character_id;
  output.owner_character_id = request.owner_character_id;
  output.persistent_regiment_ids.source_member = "composition+20/+2C_native_persistent_union";
  output.knight_character_ids.source_member = "composition+38/+44_native_knight_ids";
  output.raised_army_regiment_ids.source_member = "composition+08/+14_native_ArRg_ids";
  alignas(16) std::array<std::byte, 0xB8> storage{};
  CompositionLease lease{bindings.composition, storage.data()};
  try {
    if (!bindings.enabled || !bindings.composition.enabled ||
        bindings.composition.construct_empty == nullptr ||
        bindings.composition.initialize_owner == nullptr ||
        bindings.composition.count_all_unraised == nullptr ||
        bindings.composition.destroy_contents == nullptr) {
      output.failure = "actual4_composition_bindings_unavailable";
      return output.status;
    }
    output.exact_build_ready = true; // Admission belongs to the actual4 factory.
    if (request.owner_character_id == -1 || request.actor_character_id <= 0 ||
        request.snapshot_revision == 0) {
      output.failure = "owner_or_public_actor_request_invalid";
      return output.status;
    }
    game::Snapshot before{};
    if (!TryReadFrame(world, before) || !FrameMatches(before, request)) {
      output.failure = "current_player_frame_unavailable";
      return output.status;
    }
    void *owner = nullptr;
    if (!TryResolveCharacter(world, request.owner_character_id, owner)) {
      output.failure = "owner_character_unavailable";
      return output.status;
    }
    output.observed_owner_full_id = CopyAt<std::int32_t>(owner, 0x18);
    output.observed_owner_magic = CopyAt<std::uint32_t>(owner, 0x1C);
    output.owner_identity_ready = output.observed_owner_full_id == request.owner_character_id &&
        output.observed_owner_magic == 0x43686172U;
    if (!output.owner_identity_ready) {
      output.failure = "owner_full_generation_or_magic_invalid";
      return output.status;
    }
    void *returned = nullptr;
    output.constructor_succeeded = TryConstruct(bindings.composition.construct_empty,
        storage.data(), returned) && returned == storage.data();
    if (!output.constructor_succeeded) {
      output.failure = "native_composition_constructor_failed";
      return output.status;
    }
    lease.active = true;
    output.initializer_succeeded = TryInitialize(bindings.composition.initialize_owner,
        storage.data(), owner);
    if (output.initializer_succeeded) {
      output.composition_owner_echo_90 = CopyAt<std::int32_t>(storage.data(), 0x90);
      output.opaque_scalar_80 = CopyAt<std::int32_t>(storage.data(), 0x80);
      output.owner_echo_ready = output.composition_owner_echo_90 == request.owner_character_id;
      CopyIdCollection(storage.data(), 0x20, output.persistent_regiment_ids);
      CopyIdCollection(storage.data(), 0x38, output.knight_character_ids);
      CopyIdCollection(storage.data(), 8, output.raised_army_regiment_ids);
      Registry persistent_registry{}, army_regiment_registry{};
      const bool persistent_registry_ready = ReadRegistry(bindings.persistent_regiment_storage_slot,
                                                          persistent_registry);
      const bool army_regiment_registry_ready = ReadRegistry(bindings.army_regiment_storage_slot,
                                                            army_regiment_registry);
      output.persistent_atoms_read_complete = output.persistent_regiment_ids.entries_copied_complete &&
          output.persistent_regiment_ids.full_ids.size() <= static_cast<std::size_t>(kMaximumPersistentRows);
      std::int32_t occurrence = 0;
      for (const auto id : output.persistent_regiment_ids.full_ids) {
        if (occurrence >= kMaximumPersistentRows) break;
        PrewarOwnerPersistentRegiment12004 row{};
        CopyPersistent(persistent_registry, persistent_registry_ready, id, occurrence++, row);
        output.persistent_atoms_read_complete = output.persistent_atoms_read_complete &&
            row.full_generation_ready && row.atoms_read_complete;
        output.persistent_regiments.push_back(std::move(row));
      }
      output.knight_atoms_read_complete = output.knight_character_ids.entries_copied_complete;
      occurrence = 0;
      for (const auto id : output.knight_character_ids.full_ids) {
        PrewarOwnerKnight12004 row{};
        CopyKnight(world, id, occurrence++, row);
        output.knight_atoms_read_complete = output.knight_atoms_read_complete &&
            row.full_generation_ready && row.atoms_read_complete;
        output.knights.push_back(std::move(row));
      }
      output.raised_atoms_read_complete = output.raised_army_regiment_ids.entries_copied_complete;
      occurrence = 0;
      for (const auto id : output.raised_army_regiment_ids.full_ids) {
        PrewarOwnerArmyRegiment12004 row{};
        CopyArmyRegiment(army_regiment_registry, army_regiment_registry_ready,
                         id, occurrence++, row);
        output.raised_atoms_read_complete = output.raised_atoms_read_complete &&
            row.full_generation_ready && row.atoms_read_complete;
        output.raised_army_regiments.push_back(std::move(row));
      }
      if (output.owner_echo_ready) {
        std::int32_t stock = 0;
        output.native_all_unraised_stock_call_succeeded = TryCount(
            bindings.composition.count_all_unraised, storage.data(), stock);
        if (output.native_all_unraised_stock_call_succeeded)
          output.native_all_unraised_stock = stock;
      }
      CopyDomicile(bindings, world, owner, persistent_registry,
                    persistent_registry_ready, output.domicile);
    }
    (void)lease.Close();
    output.cleanup_attempted = lease.cleanup_attempted;
    output.cleanup_succeeded = lease.cleanup_succeeded;
    output.native_lifetime_ready = output.constructor_succeeded && output.initializer_succeeded &&
        output.cleanup_attempted && output.cleanup_succeeded;
    game::Snapshot after{};
    output.source_frame_ready = TryReadFrame(world, after) && FrameMatches(after, request) && after == before;
    if (!output.native_lifetime_ready || !output.source_frame_ready || !output.owner_echo_ready) {
      output.failure = !output.cleanup_succeeded ? "native_composition_cleanup_failed"
          : !output.initializer_succeeded ? "native_composition_initializer_failed"
          : !output.source_frame_ready ? "source_frame_changed" : "composition_owner_echo_mismatch";
      WithdrawQualification(output);
      return output.status;
    }
    output.native_all_unraised_stock_ready = output.native_all_unraised_stock_call_succeeded &&
        output.native_all_unraised_stock.has_value() && *output.native_all_unraised_stock >= 0;
    output.raw_capture_complete = output.persistent_atoms_read_complete && output.knight_atoms_read_complete &&
        output.raised_atoms_read_complete && output.opaque_scalar_80.has_value() &&
        output.native_all_unraised_stock_ready;
    output.current_count_atoms_valid = output.raw_capture_complete;
    for (const auto &regiment : output.persistent_regiments) {
      output.current_count_atoms_valid = output.current_count_atoms_valid &&
          regiment.native_capacity_raw.has_value() && *regiment.native_capacity_raw >= 0;
      for (const auto &chunk : regiment.chunks)
        output.current_count_atoms_valid = output.current_count_atoms_valid &&
            chunk.maximum_soldiers_raw.has_value() && *chunk.maximum_soldiers_raw >= 0 &&
            chunk.current_soldiers_raw.has_value() && *chunk.current_soldiers_raw >= 0;
    }
    for (const auto &regiment : output.raised_army_regiments)
      output.current_count_atoms_valid = output.current_count_atoms_valid &&
          regiment.current_soldiers_raw.has_value() && *regiment.current_soldiers_raw >= 0 &&
          regiment.maximum_soldiers_raw.has_value() && *regiment.maximum_soldiers_raw >= 0;
    output.owner_stock_inventory_complete = output.raw_capture_complete &&
        output.current_count_atoms_valid && output.domicile.current_ready;
    output.status = output.owner_stock_inventory_complete ? PrewarOwnerInventoryStatus12004::available
                                                : PrewarOwnerInventoryStatus12004::partial;
    if (!output.owner_stock_inventory_complete) output.failure = "owner_stock_inventory_partial";
    return output.status;
  } catch (...) {
    (void)lease.Close();
    output.cleanup_attempted = lease.cleanup_attempted;
    output.cleanup_succeeded = lease.cleanup_succeeded;
    WithdrawQualification(output);
    output.status = PrewarOwnerInventoryStatus12004::unavailable;
    output.failure = "owner_inventory_cpp_exception";
    return output.status;
  }
}

} // namespace xar::ck3_12004
