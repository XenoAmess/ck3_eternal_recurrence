#include "ghw_variable_observer_12004.hpp"
#include <cstring>
#include <limits>

namespace xar::ck3_12004::religion::ghw_variables_candidate {
namespace {
bool Add(std::uintptr_t base, std::size_t delta, std::uintptr_t &out) noexcept {
  if (!base || delta > std::numeric_limits<std::uintptr_t>::max() - base)
    return false;
  out = base + delta;
  return true;
}
template<class T>
bool Load(const Access &a, std::uintptr_t base, std::size_t delta,
          T &out) noexcept {
  std::uintptr_t address = 0;
  return Add(base, delta, address) &&
      a.read_memory(a.context, address, &out, sizeof(out));
}
bool AdmitFrame(const BoundFrame &f) noexcept {
  return f.capture_epoch && f.played_character_id > 0 &&
      f.faith_id != kNullReference && f.religion_id != kNullReference &&
      f.faith_object && f.religion_object && f.paused && f.map_ready &&
      f.actor_alive;
}
bool Identity(const Access &a, const BoundFrame &f) noexcept {
  std::uint32_t faith_id = 0, faith_tag = 0, religion_id = 0;
  std::uint32_t religion_tag = 0, linked_religion = 0;
  // Exact current Faith/Religion provider callbacks and GetReligion close
  // +08 fullID, +0C magic, Faith+8C linked Religion; not an old-image binder.
  return Load(a, f.faith_object, 8, faith_id) && faith_id == f.faith_id &&
      Load(a, f.faith_object, 0x0C, faith_tag) && faith_tag == 0x46616974U &&
      Load(a, f.faith_object, 0x8C, linked_religion) &&
      linked_religion == f.religion_id &&
      Load(a, f.religion_object, 8, religion_id) &&
      religion_id == f.religion_id &&
      Load(a, f.religion_object, 0x0C, religion_tag) &&
      religion_tag == 0x52656c67U;
}
std::int32_t Subtract(std::int32_t expiry, std::int32_t clock) noexcept {
  const auto bits = static_cast<std::uint32_t>(expiry) -
                    static_cast<std::uint32_t>(clock);
  std::int32_t result = 0;
  std::memcpy(&result, &bits, sizeof(result));
  return result;
}
Scalar Unavailable(Failure failure) noexcept {
  Scalar out{};
  out.failure = failure;
  return out;
}
struct Pass {
  std::array<std::uintptr_t, 4> contexts{};
  std::array<std::int32_t, 4> tokens{};
  std::array<Scalar, 4> fields{};
  bool operator==(const Pass &) const = default;
};
Scalar ReadScalar(const Access &a, std::uintptr_t context,
                  std::int32_t token) noexcept {
  std::uintptr_t rows = 0, later_rows = 0;
  std::int32_t count = 0, later_count = 0, clock = 0, later_clock = 0;
  if (!Load(a, context, 0x10, rows) || !Load(a, context, 0x1C, count) ||
      !Load(a, context, 0x28, clock))
    return Unavailable(Failure::memory_unreadable);
  if (count < 0 || count > 65536)
    return Unavailable(Failure::count_invalid);
  if (count && !rows) return Unavailable(Failure::rows_unavailable);
  Scalar out{};
  out.current_counter_raw = clock;
  bool found = false;
  for (std::int32_t i = 0; i < count; ++i) {
    std::uintptr_t row = 0;
    if (!Add(rows, static_cast<std::size_t>(i) * 0x20U, row))
      return Unavailable(Failure::arithmetic_overflow);
    std::int32_t key = -1;
    if (!Load(a, row, 8, key)) return Unavailable(Failure::memory_unreadable);
    if (key != token) continue;
    if (found) return Unavailable(Failure::duplicate_key);
    found = true;
    std::int32_t expiry = 0;
    std::uint16_t kind = 0;
    if (!Load(a, row, 0x0C, expiry) || !Load(a, row, 0x10, kind))
      return Unavailable(Failure::memory_unreadable);
    out.expiry_raw = expiry;
    out.value_kind_raw = kind;
    out.timed = expiry >= 0;
    out.remaining_raw = expiry >= 0 ? Subtract(expiry, clock) : -1;
    if (kind == 1) {
      std::int64_t value = 0;
      if (!Load(a, row, 0x18, value))
        return Unavailable(Failure::memory_unreadable);
      out.numeric_value_raw = value;
    }
  }
  if (!Load(a, context, 0x10, later_rows) ||
      !Load(a, context, 0x1C, later_count) ||
      !Load(a, context, 0x28, later_clock))
    return Unavailable(Failure::memory_unreadable);
  if (rows != later_rows || count != later_count || clock != later_clock)
    return Unavailable(Failure::collection_changed);
  out.read_available = true;
  out.present = found;
  if (!found) {
    out.timed = false;
    out.remaining_raw = -1; // Same native helper sentinel; presence stays separate.
  }
  return out;
}
Pass ReadPass(const Access &a, const BoundFrame &frame) noexcept {
  Pass pass{};
  pass.tokens.fill(-1);
  for (std::size_t i = 0; i < kKeys.size(); ++i) {
    std::int32_t token = -1;
    if (!a.resolve_identifier(a.context, kKeys[i], token) || token < 0) {
      pass.fields[i] = Unavailable(Failure::identifier_unavailable);
      continue;
    }
    pass.tokens[i] = token;
    const auto scope = kScopes[i];
    const auto id = scope == Scope::faith ? frame.faith_id :
        (scope == Scope::religion ? frame.religion_id : 0U);
    std::uintptr_t context = 0;
    if (!a.resolve_context(a.context, scope, id, context) || !context) {
      pass.fields[i] = Unavailable(Failure::context_unavailable);
      continue;
    }
    pass.contexts[i] = context;
    pass.fields[i] = ReadScalar(a, context, token);
  }
  return pass;
}
} // namespace

bool ReadCurrentPlayerGhwVariables12004(const Access &a,
                                      Observation &out) noexcept {
  out = {};
  const auto fail = [&](Failure failure) {
    out = {};
    out.failure = failure;
    for (auto &field : out.fields) field = Unavailable(failure);
    return false;
  };
  if (a.executable_sha256 != kExactSha || !a.read_memory ||
      !a.read_bound_frame || !a.resolve_identifier || !a.resolve_context)
    return fail(Failure::input_not_admitted);
  BoundFrame before{}, after{};
  if (!a.read_bound_frame(a.context, before) || !AdmitFrame(before))
    return fail(Failure::frame_unavailable);
  if (!Identity(a, before)) return fail(Failure::object_identity_mismatch);
  const auto first = ReadPass(a, before);
  const auto second = ReadPass(a, before);
  if (first != second) return fail(Failure::observations_changed);
  if (!a.read_bound_frame(a.context, after) || before != after ||
      !AdmitFrame(after) || !Identity(a, after))
    return fail(Failure::identity_changed);
  out.capture_epoch = before.capture_epoch;
  out.date_raw = before.date_raw;
  out.played_character_id = before.played_character_id;
  out.faith_id = before.faith_id;
  out.religion_id = before.religion_id;
  out.fields = first.fields;
  out.frame_verified = true;
  out.stable_two_pass = true;
  out.all_fields_observed = true;
  for (const auto &field : out.fields) {
    out.available_any = out.available_any || field.read_available;
    out.all_fields_observed = out.all_fields_observed && field.read_available;
  }
  return out.available_any;
}

const char *FailureKey(Failure failure) noexcept {
  switch (failure) {
  case Failure::none: return "none";
  case Failure::input_not_admitted: return "input_not_admitted";
  case Failure::frame_unavailable: return "frame_unavailable";
  case Failure::identity_changed: return "identity_changed";
  case Failure::memory_unreadable: return "memory_unreadable";
  case Failure::arithmetic_overflow: return "arithmetic_overflow";
  case Failure::object_identity_mismatch: return "object_identity_mismatch";
  case Failure::identifier_unavailable: return "identifier_unavailable";
  case Failure::context_unavailable: return "context_unavailable";
  case Failure::count_invalid: return "count_invalid";
  case Failure::rows_unavailable: return "rows_unavailable";
  case Failure::duplicate_key: return "duplicate_key";
  case Failure::collection_changed: return "collection_changed";
  case Failure::observations_changed: return "observations_changed";
  }
  return "unknown_failure";
}
} // namespace xar::ck3_12004::religion::ghw_variables_candidate
