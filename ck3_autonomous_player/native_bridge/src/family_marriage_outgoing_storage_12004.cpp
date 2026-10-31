#include "xar_bridge/family_marriage_outgoing_storage_12004.hpp"
#include "xar_bridge/ck3_12002_family_outbound.hpp"

#include <algorithm>
#include <cstdint>
#include <cstring>
#include <limits>
#include <utility>
#include <vector>

namespace xar::bridge {

namespace {

constexpr std::uint32_t kInvalidId = (std::numeric_limits<std::uint32_t>::max)();
constexpr std::size_t kSlotStride = 0x10;
constexpr std::size_t kPendingIdentityOffset = 0x10;
constexpr std::size_t kPendingDefinitionOffset = 0x18;
constexpr std::size_t kPendingActorOffset = 0x2F0;
constexpr std::size_t kPendingRecipientOffset = 0x2F4;
constexpr std::size_t kPendingSubjectOffset = 0x2F8;
constexpr std::size_t kPendingCandidateOffset = 0x2FC;
constexpr std::size_t kPendingIntermediaryOffset = 0x300;
constexpr std::size_t kPendingRouteOffset = 0x5C0;
constexpr std::size_t kPendingAgeOffset = 0x5B8;
constexpr std::size_t kPendingCutoffOffset = 0x5BC;
constexpr std::size_t kPendingBankPointerOffset = 0x318;
constexpr std::size_t kPendingBankCapacityOffset = 0x320;
constexpr std::size_t kPendingBankCountOffset = 0x324;

constexpr std::size_t kDefinitionHashOffset = 0x14;
constexpr std::size_t kDefinitionAuthoredRowsOffset = 0x2258;
constexpr std::size_t kDefinitionDeclaredCountOffset = 0x2264;
constexpr std::size_t kAuthoredRowStride = 0x730;
constexpr std::size_t kAuthoredRowFlagOffset = 0x368;

struct MemoryReader {
  const FamilyOutgoingStorageAccess12004 &access;
  bool failed = false;
  bool changed = false;

  template <typename T>
  T At(std::uintptr_t base, std::size_t offset = 0) {
    if (failed) return T{};
    T value{};
    constexpr auto maximum = (std::numeric_limits<std::uintptr_t>::max)();
    if (base == 0 || offset > maximum - base ||
        sizeof(T) - 1 > maximum - (base + offset)) {
      failed = true;
      return value;
    }
    const auto address = base + offset;
    if (!access.read_memory(access.context, address, &value, sizeof(T))) {
      failed = true;
      return T{};
    }
    return value;
  }

  bool Drift() noexcept {
    changed = true;
    return false;
  }
};

struct StorageShape {
  std::uintptr_t storage_ptr = 0;
  std::uintptr_t slots_ptr = 0;
  std::int32_t capacity = 0;
  std::int32_t scanned_slots = 0;
  friend bool operator==(const StorageShape &, const StorageShape &) = default;
};

struct DefinitionShape {
  std::uintptr_t definition_ptr = 0;
  std::uint32_t definition_hash = 0;
  std::uintptr_t authored_rows_ptr = 0;
  std::int32_t declared_count = 0;
  friend bool operator==(const DefinitionShape &, const DefinitionShape &) = default;
};

struct OccupiedShape {
  std::uintptr_t object_ptr = 0;
  std::uintptr_t vtable = 0;
  std::uint32_t pending_full_id = 0;
  std::uintptr_t definition_ptr = 0;
  std::uint32_t actor = 0;
  friend bool operator==(const OccupiedShape &, const OccupiedShape &) = default;
};

struct CandidateShape {
  std::uintptr_t object_ptr = 0;
  std::uint32_t pending_full_id = 0;
  std::uintptr_t definition_ptr = 0;
  std::array<std::uint32_t, 5> roles{};
  std::int32_t route_kind = 0;
  std::int32_t age_days = 0;
  std::int32_t ai_reply_cutoff_days = 0;
  std::uintptr_t bank_ptr = 0;
  std::int32_t bank_capacity = 0;
  std::int32_t bank_count = 0;
  friend bool operator==(const CandidateShape &, const CandidateShape &) = default;
};

bool ValidateStorageShape(const StorageShape &shape) {
  if (shape.capacity < 0 || shape.capacity > 1'000'000) return false;
  if (shape.scanned_slots < 0 || shape.scanned_slots > 1'000'000) return false;
  if (shape.scanned_slots != shape.capacity) return false;
  if (shape.capacity != 0 && shape.slots_ptr == 0) return false;
  return true;
}

bool ValidateDefinitionShape(const DefinitionShape &shape) {
  if (shape.definition_ptr == 0) return false;
  if (shape.declared_count < 0 || shape.declared_count > 4096) return false;
  if (shape.declared_count != 0 && shape.authored_rows_ptr == 0) return false;
  return true;
}

bool ValidateCandidateShape(const CandidateShape &shape) {
  if (shape.object_ptr == 0) return false;
  if (shape.definition_ptr == 0) return false;
  if (shape.bank_count < 0 || shape.bank_count > 4096) return false;
  if (shape.bank_capacity < 0) return false;
  if (shape.bank_count > shape.bank_capacity) return false;
  if (shape.bank_ptr == 0 && shape.bank_count > 0) return false;
  if (shape.roles[0] == 0 || shape.roles[0] == kInvalidId) return false;
  for (std::size_t i = 1; i < shape.roles.size(); ++i)
    if (shape.roles[i] == 0) return false;
  return true;
}

bool ReadStorageShape(MemoryReader &reader, const ck3_12002::FamilyOutboundBindings &bindings,
                      StorageShape &shape) {
  if (bindings.pending_storage_slot == nullptr) return false;
  shape.storage_ptr = reader.At<std::uintptr_t>(
      reinterpret_cast<std::uintptr_t>(bindings.pending_storage_slot));
  if (reader.failed || shape.storage_ptr == 0) return false;

  shape.capacity = reader.At<std::int32_t>(shape.storage_ptr, 0x2C);
  if (reader.failed) return false;

  shape.slots_ptr = reader.At<std::uintptr_t>(shape.storage_ptr, 0x20);
  if (reader.failed) return false;

  shape.scanned_slots = shape.capacity;
  return ValidateStorageShape(shape);
}

bool ReadDefinitionShape(MemoryReader &reader, std::uintptr_t actual_definition,
                         DefinitionShape &shape) {
  shape.definition_ptr = actual_definition;
  shape.definition_hash = reader.At<std::uint32_t>(actual_definition, kDefinitionHashOffset);
  if (reader.failed) return false;

  shape.authored_rows_ptr = reader.At<std::uintptr_t>(actual_definition, kDefinitionAuthoredRowsOffset);
  if (reader.failed) return false;

  shape.declared_count = reader.At<std::int32_t>(actual_definition, kDefinitionDeclaredCountOffset);
  if (reader.failed) return false;

  return ValidateDefinitionShape(shape);
}

bool ReadOccupiedShape(MemoryReader &reader, const ck3_12002::FamilyOutboundBindings &bindings,
                       std::uintptr_t object_ptr, OccupiedShape &shape) {
  shape.object_ptr = object_ptr;
  shape.vtable = reader.At<std::uintptr_t>(object_ptr);
  if (reader.failed) return false;
  if (shape.vtable != bindings.pending_vtable) return false;
  shape.pending_full_id = reader.At<std::uint32_t>(object_ptr, kPendingIdentityOffset);
  shape.definition_ptr = reader.At<std::uintptr_t>(object_ptr, kPendingDefinitionOffset);
  shape.actor = reader.At<std::uint32_t>(object_ptr, kPendingActorOffset);
  return !reader.failed;
}

bool ReadCandidateShape(MemoryReader &reader,
                        std::uintptr_t object_ptr, CandidateShape &shape) {
  shape.object_ptr = object_ptr;

  shape.pending_full_id = reader.At<std::uint32_t>(object_ptr, kPendingIdentityOffset);
  if (reader.failed) return false;

  shape.definition_ptr = reader.At<std::uintptr_t>(object_ptr, kPendingDefinitionOffset);
  if (reader.failed) return false;

  shape.roles[0] = reader.At<std::uint32_t>(object_ptr, kPendingActorOffset);
  shape.roles[1] = reader.At<std::uint32_t>(object_ptr, kPendingRecipientOffset);
  shape.roles[2] = reader.At<std::uint32_t>(object_ptr, kPendingSubjectOffset);
  shape.roles[3] = reader.At<std::uint32_t>(object_ptr, kPendingCandidateOffset);
  shape.roles[4] = reader.At<std::uint32_t>(object_ptr, kPendingIntermediaryOffset);
  if (reader.failed) return false;

  shape.route_kind = reader.At<std::int32_t>(object_ptr, kPendingRouteOffset);
  shape.age_days = reader.At<std::int32_t>(object_ptr, kPendingAgeOffset);
  shape.ai_reply_cutoff_days = reader.At<std::int32_t>(object_ptr, kPendingCutoffOffset);
  if (reader.failed) return false;

  shape.bank_ptr = reader.At<std::uintptr_t>(object_ptr, kPendingBankPointerOffset);
  shape.bank_capacity = reader.At<std::int32_t>(object_ptr, kPendingBankCapacityOffset);
  shape.bank_count = reader.At<std::int32_t>(object_ptr, kPendingBankCountOffset);
  if (reader.failed) return false;

  return ValidateCandidateShape(shape);
}

bool ReadOptions(MemoryReader &reader, const DefinitionShape &def_shape,
                 const CandidateShape &cand_shape,
                 std::vector<FamilyOutgoingOptionCopy12004> &options) {
  options.clear();
  if (cand_shape.bank_count != def_shape.declared_count) return false;
  if (def_shape.declared_count == 0) return true;
  if (def_shape.authored_rows_ptr == 0) return false;
  if (cand_shape.bank_ptr == 0) return false;

  options.reserve(static_cast<std::size_t>(def_shape.declared_count));
  for (std::int32_t i = 0; i < def_shape.declared_count; ++i) {
    const auto offset = static_cast<std::size_t>(i) * kAuthoredRowStride + kAuthoredRowFlagOffset;
    std::uint32_t flag = reader.At<std::uint32_t>(def_shape.authored_rows_ptr, offset);
    if (reader.failed) return false;

    std::uint8_t bank_byte = reader.At<std::uint8_t>(cand_shape.bank_ptr, static_cast<std::size_t>(i));
    if (reader.failed) return false;
    if (bank_byte > 1) return false;

    options.push_back({flag, bank_byte});
  }
  return true;
}

bool PerformPass(MemoryReader &reader, const ck3_12002::FamilyOutboundBindings &bindings,
                 std::uintptr_t actual_definition, std::uint32_t actual_sender,
                 StorageShape &shape, DefinitionShape &def_shape,
                 std::vector<std::uint32_t> &occupied_ids,
                 std::vector<FamilyOutgoingCandidateCopy12004> &candidates,
                 std::vector<CandidateShape> &candidate_shapes,
                 std::vector<std::uintptr_t> &slot_objects,
                 std::vector<OccupiedShape> &occupied_shapes) {
  if (!ReadStorageShape(reader, bindings, shape)) return false;
  if (!ReadDefinitionShape(reader, actual_definition, def_shape)) return false;

  occupied_ids.clear();
  candidates.clear();
  candidate_shapes.clear();
  slot_objects.clear();
  occupied_shapes.clear();
  slot_objects.reserve(static_cast<std::size_t>(shape.capacity));

  for (std::int32_t slot = 0; slot < shape.capacity; ++slot) {
    const auto offset = static_cast<std::size_t>(slot) * kSlotStride + 8;
    std::uintptr_t object_ptr = reader.At<std::uintptr_t>(shape.slots_ptr, offset);
    if (reader.failed) return false;
    slot_objects.push_back(object_ptr);

    if (object_ptr == 0) continue;

    OccupiedShape occupied;
    if (!ReadOccupiedShape(reader, bindings, object_ptr, occupied) ||
        occupied.pending_full_id == kInvalidId) return false;
    std::uint32_t low24 = occupied.pending_full_id & 0x00FFFFFFU;
    if (low24 != static_cast<std::uint32_t>(slot)) return false;

    occupied_ids.push_back(occupied.pending_full_id);
    occupied_shapes.push_back(occupied);

    if (occupied.definition_ptr == actual_definition && occupied.actor == actual_sender) {
      if (candidates.size() >= 256) return false;
      CandidateShape c_shape;
      if (!ReadCandidateShape(reader, object_ptr, c_shape)) return false;
      if (c_shape.pending_full_id != occupied.pending_full_id ||
          c_shape.definition_ptr != occupied.definition_ptr ||
          c_shape.roles[0] != occupied.actor) return reader.Drift();
      std::vector<FamilyOutgoingOptionCopy12004> options;
      if (!ReadOptions(reader, def_shape, c_shape, options)) return false;

      FamilyOutgoingCandidateCopy12004 copy;
      copy.pending_full_id = c_shape.pending_full_id;
      copy.definition_hash = def_shape.definition_hash;
      copy.roles = c_shape.roles;
      copy.route_kind = c_shape.route_kind;
      copy.age_days = c_shape.age_days;
      copy.ai_reply_cutoff_days = c_shape.ai_reply_cutoff_days;
      copy.options = std::move(options);

      candidates.push_back(std::move(copy));
      candidate_shapes.push_back(c_shape);
    }
  }

  StorageShape after;
  DefinitionShape def_after;
  if (!ReadStorageShape(reader, bindings, after) ||
      !ReadDefinitionShape(reader, actual_definition, def_after)) return false;
  if (shape != after || def_shape != def_after) return reader.Drift();
  std::size_t occupied_index = 0, selected_index = 0;
  for (std::size_t slot = 0; slot < slot_objects.size(); ++slot) {
    const auto observed = reader.At<std::uintptr_t>(shape.slots_ptr, slot * kSlotStride + 8);
    if (reader.failed) return false;
    if (observed != slot_objects[slot]) return reader.Drift();
    if (observed == 0) continue;
    OccupiedShape current;
    if (!ReadOccupiedShape(reader, bindings, observed, current))
      return reader.failed ? false : reader.Drift();
    if (current != occupied_shapes[occupied_index++]) return reader.Drift();
    if (current.definition_ptr != actual_definition || current.actor != actual_sender)
      continue;
    CandidateShape candidate_after;
    if (!ReadCandidateShape(reader, observed, candidate_after))
      return reader.failed ? false : reader.Drift();
    if (candidate_after != candidate_shapes[selected_index]) return reader.Drift();
    std::vector<FamilyOutgoingOptionCopy12004> options_after;
    if (!ReadOptions(reader, def_shape, candidate_after, options_after))
      return reader.failed ? false : reader.Drift();
    if (options_after != candidates[selected_index++].options) return reader.Drift();
  }
  if (!ReadStorageShape(reader, bindings, after) ||
      !ReadDefinitionShape(reader, actual_definition, def_after)) return false;
  if (shape != after || def_shape != def_after) return reader.Drift();
  return true;
}

bool ComparePasses(const StorageShape &s1, const StorageShape &s2,
                   const DefinitionShape &d1, const DefinitionShape &d2,
                   const std::vector<std::uint32_t> &ids1,
                   const std::vector<std::uint32_t> &ids2,
                   const std::vector<FamilyOutgoingCandidateCopy12004> &c1,
                   const std::vector<FamilyOutgoingCandidateCopy12004> &c2,
                   const std::vector<CandidateShape> &shapes1,
                   const std::vector<CandidateShape> &shapes2,
                   const std::vector<std::uintptr_t> &slots1,
                   const std::vector<std::uintptr_t> &slots2,
                   const std::vector<OccupiedShape> &occupied1,
                   const std::vector<OccupiedShape> &occupied2) {
  return s1 == s2 && d1 == d2 && ids1 == ids2 && c1 == c2 &&
      shapes1 == shapes2 && slots1 == slots2 && occupied1 == occupied2;
}

} // namespace

FamilyOutgoingStorageCopyStatus12004 ReadFamilyOutgoingStorageCopy12004(
    const ck3_12002::FamilyOutboundBindings &bindings,
    const FamilyOutgoingStorageAccess12004 &access,
    std::uintptr_t actual_definition, std::uint32_t actual_sender,
    FamilyOutgoingStorageCopy12004 &output) noexcept {

  output = {};

  if (!bindings.enabled || access.read_memory == nullptr ||
      bindings.pending_storage_slot == nullptr || bindings.pending_vtable == 0) {
    return FamilyOutgoingStorageCopyStatus12004::invalid_request;
  }

  if (actual_definition == 0 || actual_sender == 0 || actual_sender == kInvalidId) {
    return FamilyOutgoingStorageCopyStatus12004::invalid_request;
  }

  try {
    MemoryReader reader1{access};
    MemoryReader reader2{access};

    StorageShape shape1, shape2;
    DefinitionShape def1, def2;
    std::vector<std::uint32_t> ids1, ids2;
    std::vector<FamilyOutgoingCandidateCopy12004> cands1, cands2;
    std::vector<CandidateShape> shapes1, shapes2;
    std::vector<std::uintptr_t> slots1, slots2;
    std::vector<OccupiedShape> occupied1, occupied2;

    if (!PerformPass(reader1, bindings, actual_definition, actual_sender, shape1, def1,
                     ids1, cands1, shapes1, slots1, occupied1)) {
      return reader1.changed ? FamilyOutgoingStorageCopyStatus12004::changed :
          FamilyOutgoingStorageCopyStatus12004::unavailable;
    }

    if (!PerformPass(reader2, bindings, actual_definition, actual_sender, shape2, def2,
                     ids2, cands2, shapes2, slots2, occupied2)) {
      return reader2.changed ? FamilyOutgoingStorageCopyStatus12004::changed :
          FamilyOutgoingStorageCopyStatus12004::unavailable;
    }

    if (!ComparePasses(shape1, shape2, def1, def2, ids1, ids2, cands1, cands2,
                       shapes1, shapes2, slots1, slots2, occupied1, occupied2)) {
      return FamilyOutgoingStorageCopyStatus12004::changed;
    }

    output.definition_hash = def1.definition_hash;
    output.sender_id = actual_sender;
    output.scanned_slots = shape1.scanned_slots;
    output.occupied_ids = std::move(ids1);
    output.candidates = std::move(cands1);

    return FamilyOutgoingStorageCopyStatus12004::complete;
  } catch (...) {
    output = {};
    return FamilyOutgoingStorageCopyStatus12004::unavailable;
  }
}

} // namespace xar::bridge
