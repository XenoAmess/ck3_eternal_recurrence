#pragma once

#include "xar_bridge/ck3_12002_phase_culture.hpp"
#include <array>
#include <bit>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <ostream>

namespace xar::ck3_12004 {

// Trusted same-query access. The ordinary caller wraps guarded full-generation
// Resolve and ReadEducationField. The optional total-martial callback uses an
// independently guarded actual4 native API; no education script getter is asserted.
struct RequestGuardianSkillAccess12004 {
  void *context = nullptr;
  void *(*resolve_character)(void *, std::uint32_t) noexcept = nullptr;
  bool (*read_int32)(void *, const void *, std::size_t,
                    std::int32_t &) noexcept = nullptr;
  std::uintptr_t trait_module_base = 0;
  bool (*read_trait)(std::uintptr_t, const void *, const char *,
                     bool &) noexcept = nullptr;
  bool (*read_education_culture)(std::uintptr_t, const void *, std::uint32_t,
      ck3_12002::phase_culture::CharacterCultureParameterObservation &) noexcept = nullptr;
  bool (*read_total_martial)(std::uintptr_t, const void *, std::uint32_t,
                              std::int32_t &) noexcept = nullptr;
};

struct RequestGuardianSkillValue12004 {
  bool available = false;
  std::optional<std::int32_t> value;
  const char *unavailable_reason = "guardian_skill_not_observed";
};

// Independent native total-skill callback observation, owned by the same request.
struct CharacterTotalMartialCallbackValue12004V1 {
  std::optional<std::uint32_t> target_character_id;
  bool available = false;
  std::optional<std::int32_t> value;
  const char *unavailable_reason = "total_martial_callback_not_observed";
};

inline constexpr std::array<const char *, 4> kRequestGuardianEducationTraitKeys12004{
    "intellect_good_3", "intellect_good_2", "intellect_good_1", "shrewd"};
struct RequestGuardianTraitValue12004 {
  bool available = false;
  std::optional<bool> value;
  const char *unavailable_reason = "guardian_trait_not_observed";
};

struct RequestGuardianSkillInputs12004 {
  std::optional<std::uint32_t> child_character_id;
  std::optional<std::uint32_t> character_id;
  std::uint64_t owning_native_revision = 0;
  const char *binding_status = "unavailable";
  const char *unavailable_reason = "guardian_skill_binding_not_observed";
  RequestGuardianSkillValue12004 diplomacy{};
  RequestGuardianSkillValue12004 martial{};
  RequestGuardianSkillValue12004 stewardship{};
  RequestGuardianSkillValue12004 intrigue{};
  RequestGuardianSkillValue12004 learning{};
  std::optional<CharacterTotalMartialCallbackValue12004V1> total_martial_callback_v1;
  std::optional<std::array<RequestGuardianTraitValue12004, 4>> education_traits;
  std::optional<ck3_12002::phase_culture::CharacterCultureParameterObservation>
      education_culture_parameters;
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
  for (auto *field : std::array<RequestGuardianSkillValue12004 *, 5>{
           &out.diplomacy, &out.martial, &out.stewardship, &out.intrigue,
           &out.learning}) {
    field->available = false;
    field->value.reset();
    field->unavailable_reason = reason;
  }
  if (out.total_martial_callback_v1) {
    auto &field = *out.total_martial_callback_v1;
    field.available = false;
    field.value.reset();
    field.unavailable_reason = reason;
  }
  if (out.education_traits) for (auto &field : *out.education_traits) {
    field.available = false;
    field.value.reset();
    field.unavailable_reason = reason;
  }
  if (out.education_culture_parameters) {
    auto &field = *out.education_culture_parameters;
    field.available = false;
    field.value.reset();
    field.unavailable_reason = reason;
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
  if (access.read_total_martial != nullptr) {
    out.total_martial_callback_v1.emplace();
    out.total_martial_callback_v1->target_character_id = final_secondary_actor_full_id;
  }
  if (access.read_trait != nullptr) out.education_traits.emplace();
  if (access.read_education_culture != nullptr)
    out.education_culture_parameters.emplace();
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
  // Martial enum1 is the current total-skill cache, DWORD[Character+DC].
  // Commander base quality 2C0B250 separately adds modifier19B to this cache.
  constexpr std::array<std::size_t, 5> offsets{0xD8, 0xDC, 0xE0, 0xE4, 0xE8};
  std::array<RequestGuardianSkillValue12004 *, 5> fields{
      &out.diplomacy, &out.martial, &out.stewardship, &out.intrigue,
      &out.learning};
  std::array<std::int32_t, 5> first{};
  std::array<bool, 5> first_read{};
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
  if (out.total_martial_callback_v1) {
    auto &field = *out.total_martial_callback_v1;
    std::int32_t first_value = 0, second_value = 0;
    const bool first_ok = access.read_total_martial(
        access.trait_module_base, guardian, *final_secondary_actor_full_id, first_value);
    const bool second_ok = access.read_total_martial(
        access.trait_module_base, guardian, *final_secondary_actor_full_id, second_value);
    if (!first_ok || !second_ok) {
      field.unavailable_reason = "total_martial_callback_read_unavailable";
    } else if (first_value != second_value) {
      field.unavailable_reason = "total_martial_callback_value_changed";
    } else {
      field.available = true;
      field.value = second_value; // Preserve signed raw integer, including zero.
      field.unavailable_reason = nullptr;
    }
  }
  if (out.education_traits) {
    for (std::size_t index = 0; index < out.education_traits->size(); ++index) {
      auto &field = (*out.education_traits)[index];
      bool first_value = false, second_value = false;
      const auto key = kRequestGuardianEducationTraitKeys12004[index];
      const bool first_ok = access.read_trait(
          access.trait_module_base, guardian, key, first_value);
      const bool second_ok = access.read_trait(
          access.trait_module_base, guardian, key, second_value);
      if (!first_ok || !second_ok) {
        field.unavailable_reason = "guardian_trait_read_unavailable";
      } else if (first_value != second_value) {
        field.unavailable_reason = "guardian_trait_values_changed";
      } else {
        field.available = true;
        field.value = second_value;
        field.unavailable_reason = nullptr;
      }
    }
  }
  if (out.education_culture_parameters && !access.read_education_culture(
      access.trait_module_base, guardian, *final_secondary_actor_full_id,
      *out.education_culture_parameters)) {
    auto &field = *out.education_culture_parameters;
    field.available = false;
    field.value.reset();
    if (field.unavailable_reason == nullptr)
      field.unavailable_reason = "guardian_culture_read_unavailable";
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
  stream << '}';
  if (value.education_traits) {
    stream << ",\"education_traits\":{";
    for (std::size_t index = 0; index < value.education_traits->size(); ++index) {
      if (index != 0) stream << ',';
      const auto &field = (*value.education_traits)[index];
      text(kRequestGuardianEducationTraitKeys12004[index]);
      stream << ":{\"available\":" << (field.available ? "true" : "false")
             << ",\"value\":";
      stream << (field.available && field.value.has_value() ?
          (*field.value ? "true" : "false") : "null");
      stream << ",\"unavailable_reason\":";
      text(field.unavailable_reason);
      stream << '}';
    }
    stream << '}';
  }
  if (value.education_culture_parameters) {
    const auto &field = *value.education_culture_parameters;
    stream << ",\"education_culture_parameters\":{\"culture_full_id\":";
    id(field.culture_full_id);
    stream << ",\"available\":" << (field.available ? "true" : "false")
           << ",\"better_ward_education\":";
    stream << (field.available && field.value.has_value() ?
        (*field.value ? "true" : "false") : "null");
    stream << ",\"unavailable_reason\":";
    text(field.unavailable_reason);
    stream << '}';
  }
  if (value.total_martial_callback_v1) {
    const auto &field = *value.total_martial_callback_v1;
    stream << ",\"total_martial_callback_v1\":{"
           << "\"source\":\"native_character_total_skill_callback\","
           << "\"target_character_id\":";
    id(field.target_character_id);
    stream << ",\"available\":" << (field.available ? "true" : "false")
           << ",\"value\":";
    if (field.available && field.value.has_value()) stream << *field.value;
    else stream << "null";
    stream << ",\"unavailable_reason\":";
    text(field.available ? nullptr : field.unavailable_reason);
    stream << '}';
  }
  stream << '}';
}

} // namespace xar::ck3_12004
