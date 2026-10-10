#pragma once

#include <cstddef>
#include <cstdint>
#include <limits>
#include <optional>
#include <string>
#include <vector>

#define XAR_HAS_PRISONER_QUOTE_READONLY_SOURCE_12004 1

namespace xar::ck3_12004 {
inline constexpr char kPrisonerQuoteSourceExecutableSha25612004[] =
    "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";

using PrisonerQuoteGuardedRead12004 = bool (*)(void *, const void *, void *, std::size_t) noexcept;
struct PrisonerQuoteReadOnlyAccess12004 {
  void *context = nullptr;
  PrisonerQuoteGuardedRead12004 read_memory = nullptr;
  std::size_t maximum_modifier_occurrences = 4096;
};

// These are copied existing query identities, never a new clock or a historical
// native-entry claim. Context roles and the surrounding frame are independent
// facts supplied by the current collection producer.
struct PrisonerQuoteSourceFrame12004 {
  std::string executable_sha256;
  std::uintptr_t module_base = 0;
  std::uint64_t native_revision = 0, query_sequence = 0, proof_epoch = 0;
  std::optional<std::int32_t> date_raw;
  std::optional<std::uint32_t> jailer_full_id, prisoner_full_id, recipient_full_id;
  std::uintptr_t definition_identity = 0, interaction_context_identity = 0;
  std::uintptr_t original_scope_identity = 0;
  bool roles_verified_in_owned_context = false;
  bool same_frame_confirmed = false;
  friend bool operator==(const PrisonerQuoteSourceFrame12004 &,
                         const PrisonerQuoteSourceFrame12004 &) = default;
};
inline bool PrisonerQuoteSourceFrameReady12004(const PrisonerQuoteSourceFrame12004 &frame) noexcept {
  return frame.executable_sha256 == kPrisonerQuoteSourceExecutableSha25612004 &&
      frame.module_base != 0 && frame.native_revision != 0 && frame.query_sequence != 0 &&
      frame.proof_epoch != 0 && frame.date_raw.has_value() && frame.jailer_full_id.has_value() &&
      frame.prisoner_full_id.has_value() && frame.recipient_full_id.has_value() &&
      frame.definition_identity != 0 && frame.interaction_context_identity != 0 &&
      frame.original_scope_identity != 0 && frame.roles_verified_in_owned_context && frame.same_frame_confirmed;
}

// Actual native internal layout: QWORD aliases+0/+8/+10/+18 and BYTE+20.
// Optional zero means a read null; nullopt means unavailable. No padding is read.
// A source-defined copied shape may have no physical internal/support address.
struct PrisonerQuoteInternalAliases12004 {
  std::optional<std::uintptr_t> internal_identity;
  std::optional<std::uintptr_t> primary_scope, secondary_scope, tertiary_scope, support118_identity;
  std::optional<std::uint8_t> evaluation_flag_raw_u8;
  std::optional<std::uint16_t> primary_scope_root_word;
  bool physical_aliases_copied = false;
  friend bool operator==(const PrisonerQuoteInternalAliases12004 &,
                         const PrisonerQuoteInternalAliases12004 &) = default;
};

template <typename T>
inline std::optional<T> ReadPrisonerQuoteSource12004(const PrisonerQuoteReadOnlyAccess12004 &access,
    std::uintptr_t receiver, std::size_t offset = 0) noexcept {
  if (!access.read_memory || receiver == 0 ||
      receiver > (std::numeric_limits<std::uintptr_t>::max)() - offset ||
      receiver + offset > (std::numeric_limits<std::uintptr_t>::max)() - sizeof(T)) return {};
  T value{};
  if (!access.read_memory(access.context, reinterpret_cast<const void *>(receiver + offset),
                          &value, sizeof(value))) return {};
  return value;
}
inline PrisonerQuoteInternalAliases12004 ReadPrisonerQuoteInternalAliases12004(
    const PrisonerQuoteReadOnlyAccess12004 &access, std::uintptr_t internal) noexcept {
  PrisonerQuoteInternalAliases12004 out{};
  if (internal == 0) return out;
  out.internal_identity = internal;
  out.primary_scope = ReadPrisonerQuoteSource12004<std::uintptr_t>(access, internal);
  out.secondary_scope = ReadPrisonerQuoteSource12004<std::uintptr_t>(access, internal, 8);
  out.tertiary_scope = ReadPrisonerQuoteSource12004<std::uintptr_t>(access, internal, 0x10);
  out.support118_identity = ReadPrisonerQuoteSource12004<std::uintptr_t>(access, internal, 0x18);
  out.evaluation_flag_raw_u8 = ReadPrisonerQuoteSource12004<std::uint8_t>(access, internal, 0x20);
  out.physical_aliases_copied = out.primary_scope.has_value() && out.secondary_scope.has_value() &&
      out.tertiary_scope.has_value() && out.support118_identity.has_value() && out.evaluation_flag_raw_u8.has_value();
  if (out.primary_scope && *out.primary_scope != 0)
    out.primary_scope_root_word = ReadPrisonerQuoteSource12004<std::uint16_t>(access, *out.primary_scope);
  return out;
}

// Reuses the closed393B actual37542D0 numerical contract from12c. The named
// lookup, descriptor/interning and source scope still belong to their callers.
// A dynamic slot address is an input identity, never its returned value.
struct PrisonerNamedFixedReadonly12004 {
  std::uintptr_t definition_identity = 0;
  std::optional<std::uintptr_t> expression_identity, expression_receiver_identity, expression_vtable, expression_slot30;
  std::optional<std::uint8_t> constant_enabled_raw_u8;
  std::optional<std::int64_t> constant_raw_q64, returned_q64;
  bool numeric_source_ready = false;
  std::string unavailable_reason;
};
inline PrisonerNamedFixedReadonly12004 ReadPrisonerNamedFixedReadonly12004(
    const PrisonerQuoteReadOnlyAccess12004 &access, std::uintptr_t definition) {
  PrisonerNamedFixedReadonly12004 out{}; out.definition_identity = definition;
  out.expression_identity = ReadPrisonerQuoteSource12004<std::uintptr_t>(access, definition, 0x70);
  if (!out.expression_identity) { out.unavailable_reason = "named_expression_pointer_unavailable"; return out; }
  if (*out.expression_identity != 0) {
    if (*out.expression_identity <= (std::numeric_limits<std::uintptr_t>::max)() - 8) {
      out.expression_receiver_identity = *out.expression_identity + 8;
      out.expression_vtable = ReadPrisonerQuoteSource12004<std::uintptr_t>(access, *out.expression_receiver_identity);
      if (out.expression_vtable && *out.expression_vtable != 0)
        out.expression_slot30 = ReadPrisonerQuoteSource12004<std::uintptr_t>(access, *out.expression_vtable, 0x30);
    }
    out.unavailable_reason = "named_dynamic_post_output_witness_unavailable"; return out;
  }
  out.constant_enabled_raw_u8 = ReadPrisonerQuoteSource12004<std::uint8_t>(access, definition, 0x7B);
  if (!out.constant_enabled_raw_u8) { out.unavailable_reason = "named_constant_flag_unavailable"; return out; }
  if (*out.constant_enabled_raw_u8 == 0) out.returned_q64 = std::int64_t{0};
  else {
    out.constant_raw_q64 = ReadPrisonerQuoteSource12004<std::int64_t>(access, definition, 0x68);
    out.returned_q64 = out.constant_raw_q64;
  }
  out.numeric_source_ready = out.returned_q64.has_value();
  if (!out.numeric_source_ready) out.unavailable_reason = "named_constant_q64_unavailable";
  return out;
}
} // namespace xar::ck3_12004
