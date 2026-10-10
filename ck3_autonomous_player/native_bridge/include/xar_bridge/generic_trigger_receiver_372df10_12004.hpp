#pragma once

#include "xar_bridge/source_read_leaf_frame_12004.hpp"
#include "xar_bridge/trigger_scope_table_provider_3795a60_12004.hpp"
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
#include <string>

namespace xar::ck3_12004 {
enum class GenericTriggerScopeStorage12004 : std::uint8_t {
  source_projection, borrowed_current_scope,
};

// Borrowed for this call only. A projected scope must use its actual owned
// storage address and its source-defined mask; unread holes cannot fall back
// to the native reader. Caller copies are input facts, not return witnesses.
struct GenericTriggerRootScopeView12004 {
  std::uintptr_t identity = 0;
  GenericTriggerScopeStorage12004 storage = GenericTriggerScopeStorage12004::source_projection;
  std::span<const std::byte> owned_bytes{};
  std::span<const std::uint8_t> defined_bytes{};
  std::optional<std::uint16_t> copied_root_word;
  std::optional<std::uint64_t> copied_full_id_payload;
};

struct GenericTriggerReceiver372DF10Result12004 {
  SourceReadFrame12004 read_frame;
  std::uintptr_t receiver_identity = 0;
  // Only a caller-supplied current physical scope may appear here. Software
  // projection addresses and descendant physical aliases are never retained.
  std::optional<std::uintptr_t> current_scope_identity;
  std::optional<std::uint16_t> scope_root_word;
  std::optional<std::uint64_t> scope_full_id_payload;
  std::optional<std::uint8_t> evaluation_flag_raw_u8;
  std::optional<std::uintptr_t> trigger_vtable_raw, slot58_raw, slot60_raw, slotc8_raw;
  std::optional<TriggerScopeTableProviderRaw3795A6012004> descriptor_provider;
  std::optional<std::uint8_t> raw_al;
  bool scope_is_source_projection = false;
  bool copied_frame_ready = false, copied_inputs_ready = false;
  bool source_value_ready = false;
  bool native_callback_executed = false, actual_trigger_evaluation_observed = false;
  std::string unavailable_reason;
};

// Actual 372DF10 RCX is supplied directly. No Perk offset, prisoner roles,
// frame/counter or native function binding is manufactured by this adapter.
// A present zero evaluation byte is observed zero; absence demands one copy.
GenericTriggerReceiver372DF10Result12004 ReadGenericTriggerReceiver372DF1012004(
    const SourceLeafReadOnlyAccess12004 &, const SourceReadFrame12004 &,
    std::uintptr_t receiver_identity, const GenericTriggerRootScopeView12004 &,
    std::optional<std::uint8_t> copied_evaluation_flag = {}) noexcept;

// Reuse source-closed 15f initializer, then literal caller WORD/QWORD stores.
// This is software input projection only. Its physical address is not
// exported, retained or admitted as an original native call witness.
GenericTriggerReceiver372DF10Result12004 ProjectGenericTriggerOwnerScope372DF1012004(
    const SourceLeafReadOnlyAccess12004 &, const SourceReadFrame12004 &,
    std::uintptr_t receiver_identity, std::uint16_t root_word,
    std::uint64_t full_id_payload,
    std::optional<std::uint8_t> copied_evaluation_flag = {}) noexcept;

// Borrow the already existing actual query carrier only during the child call.
// Current26 does not supply this carrier; a null pointer stays unavailable.
// The optional diagnostic destination receives the SAME result, never a
// second projection/read. No frame is inferred from Task/module/owner values.
struct GenericTriggerOwnerScopeChildContext12004 {
  const SourceReadFrame12004 *current_query_frame = nullptr;
  std::optional<std::uint8_t> copied_evaluation_flag;
  GenericTriggerReceiver372DF10Result12004 *copied_result = nullptr;
};
bool TryReadGenericTriggerOwnerScope372DF1012004(
    void *child_context, SourceLeafGuardedRead12004 read_memory, void *read_context,
    std::uintptr_t original_receiver, std::uint16_t root_word,
    std::uint64_t full_id_payload, std::uint8_t &raw_al) noexcept;
} // namespace xar::ck3_12004
