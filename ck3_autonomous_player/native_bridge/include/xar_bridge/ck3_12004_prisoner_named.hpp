#pragma once

#include "xar_bridge/ck3_12004.hpp"

#include <cstdint>
#include <string_view>

namespace xar::ck3_12004 {

// Actual .3 -> .4 named-map01/FAMILY-MAP.json: complete instruction spans,
// retained member/argument operands and actual ordered rel/RIP targets.
inline constexpr std::uintptr_t kPrisonerNamedDatabaseRva12004 = 0xA07970;
inline constexpr std::uintptr_t kPrisonerNamedLookupRva12004 = 0xA07830;
inline constexpr std::uintptr_t kPrisonerNamedFixedRva12004 = 0x37542D0;
inline constexpr std::uintptr_t kPrisonerNamedCloneScopeRva12004 = 0x373ACF0;
inline constexpr std::uintptr_t kPrisonerNamedSupport118Rva12004 = 0x3736040;
inline constexpr std::uintptr_t kPrisonerNamedSupport2a8Rva12004 = 0x3735F90;
inline constexpr std::uintptr_t kPrisonerNamedDestroyTailRva12004 = 0x889700;
inline constexpr std::uintptr_t kPrisonerNamedDestroyScopeRowsRva12004 = 0x889780;
inline constexpr std::uintptr_t kPrisonerNamedDestroySupportRowsRva12004 = 0x9D7340;
inline constexpr std::uintptr_t kPrisonerNamedInternDatabaseRva12004 = 0x3F79B00;
inline constexpr std::uintptr_t kPrisonerNamedInternStringRva12004 = 0x3F79DD0;
// Constructor371D100 RIP operands at +0xA3/+0xBC identify these vptrs.
// They are compared as class identity; no native virtual slot is invoked.
// Actual vbtable4884EF8 is [-8,128]: named-vbtable01/VBTABLE-RECEIPT.json
// confirms the secondary vptr at object+128+8, namely +0x88.
inline constexpr std::uintptr_t kPrisonerNamedPrimaryVtableRva12004 = 0x49290B0;
inline constexpr std::uintptr_t kPrisonerNamedSecondaryVtableRva12004 = 0x49290C0;
inline constexpr std::uintptr_t kPrisonerNamedEvaluationFlagRva12004 = 0x5D1DADC;

using PrisonerNamedDatabase12004 = void *(*)();
using PrisonerLookupNamed12004 = const void *(*)(void *, std::uint32_t);
using PrisonerCloneScope12004 = void *(*)(void *, const void *);
using PrisonerConstructSupport12004 = void *(*)(void *);
using PrisonerInternString12004 = const void *(*)(void *, const void *);
using PrisonerEvaluateNamedFixed12004 = std::int64_t *(*)(const void *,
    std::int64_t *, void *, void *, const void *);
using PrisonerDestroyScopePart12004 = void (*)(void *);

struct PrisonerNamedBindings12004 {
  bool enabled = false;
  std::uintptr_t module_base = 0;
  CoreBindings core{};
  PrisonerNamedDatabase12004 named_database = nullptr;
  PrisonerLookupNamed12004 lookup_named = nullptr;
  PrisonerCloneScope12004 clone_scope = nullptr;
  PrisonerConstructSupport12004 construct_support_118 = nullptr;
  PrisonerConstructSupport12004 construct_support_2a8 = nullptr;
  PrisonerNamedDatabase12004 intern_database = nullptr;
  PrisonerInternString12004 intern_string = nullptr;
  PrisonerEvaluateNamedFixed12004 evaluate_fixed = nullptr;
  PrisonerDestroyScopePart12004 destroy_scope_tail = nullptr;
  PrisonerDestroyScopePart12004 destroy_scope_rows = nullptr;
  PrisonerDestroyScopePart12004 destroy_support_rows = nullptr;
  const std::uint8_t *evaluation_flag = nullptr;
  std::uintptr_t named_primary_vtable = 0;
  std::uintptr_t named_secondary_vtable = 0;
};

PrisonerNamedBindings12004 BindPrisonerNamedImage12004(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

// Borrows a prepared interaction scope, clones only scratch state, and
// returns native Q100000. The ordinary ransom caller supplies prisoner root,
// jailer actor and the actual redirected payer; this never sends an offer.
bool ReadNamedInteractionFixed12004(
    const PrisonerNamedBindings12004 &bindings,
    const void *character_interaction_scope, std::uint32_t root_character_id,
    std::uint32_t actor_character_id, std::uint32_t recipient_character_id,
    std::string_view canonical_key, std::uint32_t stable_hash,
    std::int64_t &output) noexcept;

} // namespace xar::ck3_12004
