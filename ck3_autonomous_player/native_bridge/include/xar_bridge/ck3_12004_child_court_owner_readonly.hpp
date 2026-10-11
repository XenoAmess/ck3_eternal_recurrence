#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <limits>
#include <optional>
#include <ostream>
#include <string_view>

namespace xar::ck3_12004 {

static_assert(sizeof(std::uintptr_t) == sizeof(std::uint64_t));

// Source-equivalent copied operands of the complete held118B getter28BFC50.
// The caller supplies its existing admitted actual4 reader and query revision.
// No native getter, clergy query, role predicate, clock or player read occurs.
struct ChildCourtOwnerReadAccess12004 {
  std::uintptr_t module_base{};
  void *context{};
  bool (*guarded_read)(void *, const void *, void *, std::size_t) noexcept = nullptr;
  bool exact_12004_bound{};
};

struct CurrentChildCourtOwnerRead12004 {
  std::string_view status{"unavailable"};
  std::string_view unavailable_reason{"child_court_owner_inputs_unavailable"};
  std::uint32_t child_character_id{0xFFFFFFFFU};
  std::uint64_t native_revision{};
  std::optional<bool> court_owner_present{};
  std::optional<std::uint32_t> court_owner_id{};
  std::optional<std::uintptr_t> child_address{};
  std::optional<std::uintptr_t> court_owner_address{};
  std::optional<std::uintptr_t> getter_return_address{};
  std::optional<std::uintptr_t> fallback_address{};
  std::optional<std::uint32_t> fallback_full_id_raw{};
  std::optional<std::uint32_t> relation_owner_id_raw{};
  std::string_view source_path{};
  bool fallback_reached{};
  bool getter_projection_complete{};
  // The admitted current child and, for a positive result, the returned owner.
  bool identity_round_trip{};
  bool sample_stable{};
  bool source_qualified{};
};

namespace child_court_owner_readonly_detail {

struct Cell {
  std::uintptr_t address{};
  std::uint64_t bits{};
  std::size_t size{};
};

class Reader {
public:
  explicit Reader(const ChildCourtOwnerReadAccess12004 &access) noexcept
      : access_(access) {}

  template <class T>
  bool At(std::uintptr_t base, std::uintptr_t offset, T &value) noexcept {
    static_assert(sizeof(T) <= sizeof(std::uint64_t));
    constexpr auto maximum = std::numeric_limits<std::uintptr_t>::max();
    if (base == 0 || offset > maximum - base ||
        sizeof(T) - 1U > maximum - (base + offset) || count_ == cells_.size())
      return false;
    const auto address = base + offset;
    if (!access_.guarded_read(access_.context,
          reinterpret_cast<const void *>(address), &value, sizeof(T)))
      return false;
    Cell cell{address, 0, sizeof(T)};
    std::memcpy(&cell.bits, &value, sizeof(T));
    cells_[count_++] = cell;
    return true;
  }

  template <class T>
  bool Rva(std::uintptr_t rva, T &value) noexcept {
    return At(access_.module_base, rva, value);
  }

  bool Stable() const noexcept {
    for (std::size_t index = 0; index < count_; ++index) {
      const auto &cell = cells_[index];
      std::uint64_t bits{};
      if (!access_.guarded_read(access_.context,
            reinterpret_cast<const void *>(cell.address), &bits, cell.size) ||
          bits != cell.bits)
        return false;
    }
    return true;
  }

private:
  const ChildCourtOwnerReadAccess12004 &access_;
  std::array<Cell, 64> cells_{};
  std::size_t count_{};
};

// Existing actual4 Core current-character selection, including all ID bits.
// This validates the caller's actual child and a returned positive owner;
// it does not substitute the fallback object for a current character.
inline bool CurrentCharacter(Reader &read, std::uintptr_t storage,
    std::uint32_t id, std::uintptr_t &address) noexcept {
  if (id == 0xFFFFFFFFU || storage == 0) return false;
  std::int32_t capacity{};
  std::uintptr_t slots{};
  if (!read.At(storage, 0x2C, capacity) || capacity <= 0 ||
      !read.At(storage, 0x20, slots) || slots == 0)
    return false;
  const auto index = id & 0x00FFFFFFU;
  if (index >= static_cast<std::uint32_t>(capacity) ||
      !read.At(slots, static_cast<std::uintptr_t>(index) * 0x10U + 8U,
               address) || address == 0)
    return false;
  std::uint32_t observed{};
  return read.At(address, 0x18, observed) && observed == id;
}

inline void Unavailable(CurrentChildCourtOwnerRead12004 &out,
                        std::string_view reason) noexcept {
  out.status = "unavailable";
  out.unavailable_reason = reason;
  out.court_owner_present.reset();
  out.court_owner_id.reset();
  out.court_owner_address.reset();
  out.source_qualified = false;
}

inline void KnownNull(CurrentChildCourtOwnerRead12004 &out) noexcept {
  out.status = "known_null";
  out.unavailable_reason = {};
  out.court_owner_present = false;
  out.court_owner_id.reset();
  out.court_owner_address.reset();
}

inline void Positive(Reader &read, std::uintptr_t storage,
    std::uintptr_t returned, std::uint32_t id,
    CurrentChildCourtOwnerRead12004 &out) noexcept {
  out.getter_return_address = returned;
  out.getter_projection_complete = true;
  std::uintptr_t selected{};
  if (!CurrentCharacter(read, storage, id, selected) || selected != returned) {
    out.identity_round_trip = false;
    Unavailable(out, "court_owner_current_full_id_unavailable");
    return;
  }
  out.status = "resolved";
  out.unavailable_reason = {};
  out.court_owner_present = true;
  out.court_owner_id = id;
  out.court_owner_address = returned;
}

inline void Fallback(Reader &read,
                     CurrentChildCourtOwnerRead12004 &out) noexcept {
  out.fallback_reached = true;
  std::uintptr_t fallback{};
  if (!read.Rva(0x5C67570, fallback)) {
    Unavailable(out, "court_owner_fallback_unreadable");
    return;
  }
  out.fallback_address = fallback;
  out.getter_return_address = fallback;
  out.getter_projection_complete = true;
  if (fallback == 0) {
    KnownNull(out);
    return;
  }
  // Core rejects fullIDFFFFFFFF before storage lookup. This is a copied
  // invalid Character sentinel, not a failed read or a guessed role absence.
  std::uint32_t id{};
  if (!read.At(fallback, 0x18, id)) {
    Unavailable(out, "court_owner_fallback_identity_unreadable");
    return;
  }
  out.fallback_full_id_raw = id;
  if (id == 0xFFFFFFFFU) {
    KnownNull(out);
    return;
  }
  Unavailable(out, "court_owner_fallback_character_semantics_unclosed");
}

inline void Project(Reader &read, std::uintptr_t identity_storage,
    std::uintptr_t child, CurrentChildCourtOwnerRead12004 &out) noexcept {
  std::uintptr_t landed{}, relation{};
  // The literal getter loads both fields before its landed branch.
  if (!read.At(child, 0x1C0, landed) || !read.At(child, 0x1B8, relation)) {
    Unavailable(out, "child_court_owner_branch_inputs_unreadable");
    return;
  }
  if (landed != 0) {
    std::uintptr_t context{}, candidate{};
    std::uint32_t tag{};
    if (!read.At(landed, 0x1C0, context) ||
        !read.At(context, 0x28, candidate) ||
        !read.At(candidate, 0x1C, tag)) {
      Unavailable(out, "landed_court_owner_context_unreadable");
      return;
    }
    if (tag != 0x43686172U) {
      out.source_path = "landed_noncharacter_context_returns_child";
      Positive(read, identity_storage, child, out.child_character_id, out);
      return;
    }
    std::uint32_t id{};
    if (!read.At(candidate, 0x18, id)) {
      Unavailable(out, "landed_court_owner_full_id_unreadable");
      return;
    }
    if (id == 0xFFFFFFFFU) {
      out.source_path = "landed_invalid_context_returns_child";
      Positive(read, identity_storage, child, out.child_character_id, out);
      return;
    }
    out.source_path = "landed_character_context";
    Positive(read, identity_storage, candidate, id, out);
    return;
  }
  if (relation == 0) {
    out.source_path = "unlanded_relation_absent_fallback";
    Fallback(read, out);
    return;
  }
  // Literal getter's storage load occurs before relation+C8. Failure of a
  // read is unavailable; an observed native branch condition stays distinct.
  std::uintptr_t storage{};
  if (!read.Rva(0x5C67568, storage)) {
    Unavailable(out, "court_owner_storage_unreadable");
    return;
  }
  if (storage == 0) {
    out.source_path = "unlanded_storage_null_fallback";
    Fallback(read, out);
    return;
  }
  std::uint32_t id{}, capacity{};
  if (!read.At(relation, 0xC8, id) || !read.At(storage, 0x2C, capacity)) {
    Unavailable(out, "court_owner_relation_lookup_inputs_unreadable");
    return;
  }
  out.relation_owner_id_raw = id;
  const auto index = id & 0x00FFFFFFU;
  if (index >= capacity) {
    out.source_path = "unlanded_index_out_of_bounds_fallback";
    Fallback(read, out);
    return;
  }
  std::uintptr_t slots{}, owner{};
  if (!read.At(storage, 0x20, slots) ||
      !read.At(slots, static_cast<std::uintptr_t>(index) * 0x10U + 8U, owner)) {
    Unavailable(out, "court_owner_slot_unreadable");
    return;
  }
  if (owner == 0) {
    out.source_path = "unlanded_object_null_fallback";
    Fallback(read, out);
    return;
  }
  std::uint32_t observed{};
  if (!read.At(owner, 0x18, observed)) {
    Unavailable(out, "court_owner_generation_unreadable");
    return;
  }
  if (observed != id) {
    out.source_path = "unlanded_generation_mismatch_fallback";
    Fallback(read, out);
    return;
  }
  out.source_path = "unlanded_current_relation_owner";
  Positive(read, identity_storage, owner, id, out);
}

} // namespace child_court_owner_readonly_detail

inline CurrentChildCourtOwnerRead12004 ReadCurrentChildCourtOwnerReadonly12004(
    const ChildCourtOwnerReadAccess12004 &access,
    std::uint32_t child_full_id, std::uint64_t native_revision) noexcept {
  using namespace child_court_owner_readonly_detail;
  CurrentChildCourtOwnerRead12004 out{};
  out.child_character_id = child_full_id;
  out.native_revision = native_revision;
  if (!access.exact_12004_bound || access.module_base == 0 ||
      access.guarded_read == nullptr) {
    Unavailable(out, "child_court_owner_reader_unavailable");
    return out;
  }
  if (native_revision == 0) {
    Unavailable(out, "current_child_query_revision_unavailable");
    return out;
  }
  Reader read(access);
  std::uintptr_t storage{}, child{};
  if (!read.Rva(0x5C67568, storage) ||
      !CurrentCharacter(read, storage, child_full_id, child)) {
    Unavailable(out, "current_child_full_id_unavailable");
    return out;
  }
  out.child_address = child;
  out.identity_round_trip = true;
  Project(read, storage, child, out);
  out.sample_stable = read.Stable();
  if (!out.sample_stable) {
    out.identity_round_trip = false;
    Unavailable(out, "child_court_owner_reached_inputs_changed");
    return out;
  }
  out.source_qualified = out.status == "resolved" || out.status == "known_null";
  return out;
}

inline void AppendCurrentChildCourtOwnerReadonly12004Json(
    std::ostream &stream, const CurrentChildCourtOwnerRead12004 &out) {
  const auto boolean = [&stream](bool value) { stream << (value ? "true" : "false"); };
  const auto optional = [&stream](const auto &value) {
    if (value) stream << *value; else stream << "null";
  };
  stream << "{\"schema\":\"xar.ck3.current-child-court-owner-readonly/1.20.0.4/v1\""
         << ",\"status\":\"" << out.status << "\",\"unavailable_reason\":\""
         << out.unavailable_reason << "\",\"child_character_id\":" << out.child_character_id
         << ",\"native_revision\":" << out.native_revision << ",\"court_owner_present\":";
  if (out.court_owner_present) boolean(*out.court_owner_present); else stream << "null";
  stream << ",\"court_owner_id\":"; optional(out.court_owner_id);
  stream << ",\"child_address\":"; optional(out.child_address);
  stream << ",\"court_owner_address\":"; optional(out.court_owner_address);
  stream << ",\"getter_return_address\":"; optional(out.getter_return_address);
  stream << ",\"fallback_address\":"; optional(out.fallback_address);
  stream << ",\"fallback_full_id_raw\":"; optional(out.fallback_full_id_raw);
  stream << ",\"relation_owner_id_raw\":"; optional(out.relation_owner_id_raw);
  stream << ",\"source_path\":\"" << out.source_path << "\",\"fallback_reached\":";
  boolean(out.fallback_reached);
  stream << ",\"getter_projection_complete\":"; boolean(out.getter_projection_complete);
  stream << ",\"identity_round_trip\":"; boolean(out.identity_round_trip);
  stream << ",\"sample_stable\":"; boolean(out.sample_stable);
  stream << ",\"source_qualified\":"; boolean(out.source_qualified);
  stream << '}';
}

} // namespace xar::ck3_12004
