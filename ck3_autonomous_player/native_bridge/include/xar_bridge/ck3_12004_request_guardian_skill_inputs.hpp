#pragma once

#include <array>
#include <bit>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <ostream>

namespace xar::ck3_12004 {

// Trusted same-query access. The ordinary caller wraps its existing guarded
// full-generation Resolve and ReadEducationField; this leaf invokes no getter.
struct RequestGuardianSkillAccess12004 {
  void *context = nullptr;
  void *(*resolve_character)(void *, std::uint32_t) noexcept = nullptr;
  bool (*read_int32)(void *, const void *, std::size_t,
                    std::int32_t &) noexcept = nullptr;
};

struct RequestGuardianSkillValue12004 {
  bool available = false;
  std::optional<std::int32_t> value;
  const char *unavailable_reason = "guardian_skill_not_observed";
};

struct RequestGuardianSkillInputs12004 {
  std::optional<std::uint32_t> child_character_id;
  std::optional<std::uint32_t> character_id;
  std::uint64_t owning_native_revision = 0;
  const char *binding_status = "unavailable";
  const char *unavailable_reason = "guardian_skill_binding_not_observed";
  RequestGuardianSkillValue12004 diplomacy{};
  RequestGuardianSkillValue12004 martial{
      false, std::nullopt, "actual4_martial_name_enum_unqualified"};
  RequestGuardianSkillValue12004 stewardship{};
  RequestGuardianSkillValue12004 intrigue{};
  RequestGuardianSkillValue12004 learning{};
};

namespace request_guardian_skill_detail_12004 {
inline bool ValidFullID(std::uint32_t id) noexcept {
  return id != 0 && id != UINT32_MAX;
}
inline bool Identity(const RequestGuardianSkillAccess12004 &access,
                     const void *character, std::uint32_t full_id) noexcept {
  std::int32_t observed = -1;
  return character != nullptr &&
      access.read_int32(access.context, character, 0x18, observed) &&
      std::bit_cast<std::uint32_t>(observed) == full_id;
}
inline void Invalidate(RequestGuardianSkillInputs12004 &out,
                       const char *reason) noexcept {
  out.binding_status = "unavailable";
  out.unavailable_reason = reason;
  for (auto *field : std::array<RequestGuardianSkillValue12004 *, 4>{
           &out.diplomacy, &out.stewardship, &out.intrigue, &out.learning}) {
    field->available = false;
    field->value.reset();
    field->unavailable_reason = reason;
  }
}
} // namespace request_guardian_skill_detail_12004

// Invoke only for an exact .4 educate_child_interaction after final roles were
// actually copied. IDs are the final secondary_recipient / secondary_actor,
// not the original requested candidate. Null is final-role -1, not read failure.
// The outer query owns thread/build/frame checks and final role bookends.
// This profile is request-guardian evidence; it does not observe scope:educator.
inline RequestGuardianSkillInputs12004 ReadRequestGuardianSkillInputs12004(
    const RequestGuardianSkillAccess12004 &access,
    std::optional<std::uint32_t> final_child_full_id,
    std::optional<std::uint32_t> final_secondary_actor_full_id,
    std::uint64_t owning_native_revision) noexcept {
  using namespace request_guardian_skill_detail_12004;
  RequestGuardianSkillInputs12004 out{};
  out.child_character_id = final_child_full_id;
  out.character_id = final_secondary_actor_full_id;
  out.owning_native_revision = owning_native_revision;
  if (!final_secondary_actor_full_id) {
    Invalidate(out, "request_guardian_role_known_null");
    out.binding_status = "known_null";
    return out;
  }
  if (!final_child_full_id || !ValidFullID(*final_child_full_id) ||
      !ValidFullID(*final_secondary_actor_full_id)) {
    Invalidate(out, "final_role_full_id_unavailable");
    return out;
  }
  if (access.resolve_character == nullptr || access.read_int32 == nullptr) {
    Invalidate(out, "guardian_skill_access_unavailable");
    return out;
  }
  void *child = access.resolve_character(access.context, *final_child_full_id);
  void *guardian = access.resolve_character(
      access.context, *final_secondary_actor_full_id);
  if (!Identity(access, child, *final_child_full_id) ||
      !Identity(access, guardian, *final_secondary_actor_full_id)) {
    Invalidate(out, "final_role_generation_mismatch");
    return out;
  }

  // Actual4 28B1690 valid enum arm: DWORD[Character+D8+enum*4].
  // Current four named council profiles prove enums 0,2,3,4. No enum1 guess.
  constexpr std::array<std::size_t, 4> offsets{0xD8, 0xE0, 0xE4, 0xE8};
  std::array<RequestGuardianSkillValue12004 *, 4> fields{
      &out.diplomacy, &out.stewardship, &out.intrigue, &out.learning};
  std::array<std::int32_t, 4> first{};
  std::array<bool, 4> first_read{};
  for (std::size_t index = 0; index < fields.size(); ++index)
    first_read[index] = access.read_int32(
        access.context, guardian, offsets[index], first[index]);
  for (std::size_t index = 0; index < fields.size(); ++index) {
    std::int32_t second = 0;
    const bool second_read = access.read_int32(
        access.context, guardian, offsets[index], second);
    auto &field = *fields[index];
    if (!first_read[index] || !second_read) {
      field.unavailable_reason = "guardian_skill_read_unavailable";
    } else if (first[index] != second) {
      field.unavailable_reason = "guardian_skill_value_changed";
    } else {
      field.available = true;
      field.value = second; // Preserve signed raw DWORD, including zero.
      field.unavailable_reason = nullptr;
    }
  }
  if (access.resolve_character(access.context, *final_child_full_id) != child ||
      access.resolve_character(access.context, *final_secondary_actor_full_id) != guardian ||
      !Identity(access, child, *final_child_full_id) ||
      !Identity(access, guardian, *final_secondary_actor_full_id)) {
    Invalidate(out, "final_role_generation_changed");
    return out;
  }
  out.binding_status = "resolved";
  out.unavailable_reason = nullptr;
  return out;
}

// Append only this object; the caller owns the optional key
// request_guardian_skill_inputs_v1 and enclosing native frame serialization.
inline void WriteRequestGuardianSkillInputs12004(
    std::ostream &stream, const RequestGuardianSkillInputs12004 &value) {
  auto id = [&](const std::optional<std::uint32_t> &full_id) {
    if (full_id) stream << *full_id; else stream << "null";
  };
  // All reason/status literals are emitted by this source reader.
  auto text = [&](const char *literal) {
    if (literal) stream << '"' << literal << '"'; else stream << "null";
  };
  auto skill = [&](const RequestGuardianSkillValue12004 &field) {
    stream << "{\"available\":" << (field.available ? "true" : "false")
           << ",\"value\":";
    if (field.available && field.value) stream << *field.value;
    else stream << "null";
    stream << ",\"unavailable_reason\":";
    text(field.unavailable_reason);
    stream << '}';
  };
  stream << "{\"schema\":\"request_guardian_skill_inputs_v1\","
         << "\"role_source\":\"request_guardian_secondary_actor\","
         << "\"child_character_id\":";
  id(value.child_character_id);
  stream << ",\"character_id\":";
  id(value.character_id);
  stream << ",\"owning_native_revision\":" << value.owning_native_revision
         << ",\"binding_status\":";
  text(value.binding_status);
  stream << ",\"unavailable_reason\":";
  text(value.unavailable_reason);
  stream << ",\"skills\":{\"diplomacy\":";
  skill(value.diplomacy);
  stream << ",\"martial\":";
  skill(value.martial);
  stream << ",\"stewardship\":";
  skill(value.stewardship);
  stream << ",\"intrigue\":";
  skill(value.intrigue);
  stream << ",\"learning\":";
  skill(value.learning);
  stream << "}}";
}

} // namespace xar::ck3_12004
