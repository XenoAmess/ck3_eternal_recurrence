#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace xar::ck3_12004 { struct SourceReadFrame12004; }

namespace xar::ck3_12004::religion::clergy {
struct ClergyMode0SourceFrameFacts12004 {
  std::optional<std::uint64_t> frame_identity;
  std::optional<std::string> snapshot_identity;
  std::uint64_t native_revision = 0, query_sequence = 0, proof_epoch = 0;
  std::int32_t date_raw = 0;
  bool caller_snapshot_confirmed = false, ready = false;
};
struct ClergyMode0GenericFacts12004 {
  bool software_adapter_invoked = false;
  bool copied_frame_ready = false, copied_inputs_ready = false, source_value_ready = false;
  std::optional<std::uint16_t> scope_root_word;
  std::optional<std::uint64_t> scope_full_id_payload;
  std::optional<std::uint8_t> evaluation_flag_raw_u8, raw_al;
  std::string unavailable_input;
};
struct ClergyMode0SourcePacket12004 {
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0, owner_character_id = -1, candidate_character_id = -1;
  std::optional<std::int32_t> active_task_id, incumbent_character_id;
  std::string capture_scope = "seat_absent";
  bool input_scope_confirmed = false, source_projected = false, source_ready = false;
  ClergyMode0SourceFrameFacts12004 source_read_frame;
  std::optional<std::uint32_t> owner_id_raw32, incumbent_id_raw32, compared_id_raw32;
  std::optional<std::uint8_t> initial_raw_al, position_raw_al, final_raw_al, raw_al;
  std::string branch = "unavailable", unavailable_input;
  ClergyMode0GenericFacts12004 generic_trigger;
};

// Borrowed only while the already existing paused query reads its actual seat.
// Zero/empty original identity is not replaced by revision, ticket, pump or a
// pointer. The result holds owned facts only; it never retains borrowed_frame.
struct ClergyMode0SourceCapture12004 {
  std::uint64_t native_revision = 0, query_sequence = 0, proof_epoch = 0;
  const SourceReadFrame12004 *borrowed_frame = nullptr;
  std::optional<ClergyMode0SourcePacket12004> packet;
};
struct ClergyMode0SourceAccess12004 {
  void *read_context = nullptr;
  bool (*read_memory)(void *, const void *, void *, std::size_t) noexcept = nullptr;
  std::uintptr_t module_base = 0;
  std::string_view executable_sha256;
};
struct ClergyMode0SourceSeat12004 {
  std::uintptr_t actual_task = 0, actual_position = 0;
  std::int32_t task_id = -1, incumbent_id = -1;
};

ClergyMode0SourcePacket12004 ReadClergyMode0SourcePacket12004(
    const ClergyMode0SourceAccess12004 &, const ClergyMode0SourceSeat12004 &,
    const ClergyMode0SourceCapture12004 &, std::uint64_t capture_epoch,
    std::int32_t date_raw, std::int32_t owner_id, std::int32_t candidate_id) noexcept;
std::string SerializeClergyMode0SourcePacket12004(const ClergyMode0SourcePacket12004 &);
} // namespace xar::ck3_12004::religion::clergy
