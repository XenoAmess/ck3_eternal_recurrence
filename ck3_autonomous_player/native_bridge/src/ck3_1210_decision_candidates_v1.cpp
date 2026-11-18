#include "xar_bridge/ck3_1210_decision_candidates_v1.hpp"
#include <array>
#include <cstring>
#include <limits>
#include <set>
#include <type_traits>
#include <utility>

namespace xar::ck3_1210 {
namespace {
constexpr std::uint64_t kDatabaseSlot = 0x6A66790, kGuiActorSlot = 0x5D50448;
constexpr std::uint64_t kGuiVtable = 0x4BFAB30, kGuiCol = 0x52EEC58, kGuiType = 0x62225F0;
constexpr std::uint64_t kDatabaseVtable = 0x4FCD288, kDatabaseCol = 0x5776DC0, kDatabaseType = 0x5F4A6E8;
constexpr std::uint64_t kDefinitionVtable = 0x5000638, kDefinitionCol = 0x57E2B60, kDefinitionType = 0x5EBEB80;
constexpr std::size_t kMaximumRows = 4096, kMaximumGroups = 64, kMaximumGroupRows = 2048;
constexpr std::size_t kMaximumTranscript = 2 * 1024 * 1024, kMaximumWire = 262144;
constexpr std::uint64_t kMaximumSafeInteger = 9007199254740991ULL;
bool AsciiAlphaNum(char c) noexcept {
  return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9');
}
bool Utf8(std::string_view value) noexcept {
  for (std::size_t i = 0; i < value.size();) {
    const auto first = static_cast<unsigned char>(value[i++]);
    if (first < 0x80) continue;
    unsigned count = 0; std::uint32_t code = 0, minimum = 0;
    if (first >= 0xC2 && first <= 0xDF) { count = 1; code = first & 31; minimum = 0x80; }
    else if (first >= 0xE0 && first <= 0xEF) { count = 2; code = first & 15; minimum = 0x800; }
    else if (first >= 0xF0 && first <= 0xF4) { count = 3; code = first & 7; minimum = 0x10000; }
    else return false;
    if (count > value.size() - i) return false;
    while (count--) {
      const auto next = static_cast<unsigned char>(value[i++]);
      if ((next & 0xC0) != 0x80) return false;
      code = (code << 6) | (next & 63);
    }
    if (code < minimum || code > 0x10FFFF || (code >= 0xD800 && code <= 0xDFFF)) return false;
  }
  return true;
}
std::string_view Reason(DecisionCandidateReasonV1 value) noexcept {
  switch (value) {
  case DecisionCandidateReasonV1::native_producer_not_installed: return "native_producer_not_installed";
  case DecisionCandidateReasonV1::owner_not_held: return "owner_not_held";
  case DecisionCandidateReasonV1::frame_not_current: return "frame_not_current";
  case DecisionCandidateReasonV1::source_pins_unavailable: return "source_pins_unavailable";
  case DecisionCandidateReasonV1::gui_actor_differs_from_snapshot: return "gui_actor_differs_from_snapshot";
  case DecisionCandidateReasonV1::native_read_unavailable: return "native_read_unavailable";
  case DecisionCandidateReasonV1::not_queried: return "not_queried";
  case DecisionCandidateReasonV1::parameter_scope_unverified: return "parameter_scope_unverified";
  }
  return {};
}
bool ValidMetadata(const DecisionCandidateCaptureV1 &capture) noexcept {
  const auto &f = capture.frame; const auto &r = capture.producer_source;
  if (f.machine_id.empty() || f.machine_id.size() > 64 || f.session_id.empty() || f.session_id.size() > 128 ||
      !f.game_pid || !f.game_creation_filetime || !f.connection_generation || !f.native_revision ||
      f.snapshot_actor_character_id == -1 || r.path.empty() || r.path.size() > 2048 || !Utf8(r.path) ||
      !r.bytes || r.bytes > kMaximumSafeInteger || r.sha256.size() != 64) return false;
  if (!AsciiAlphaNum(f.machine_id.front()) || !AsciiAlphaNum(f.session_id.front())) return false;
  for (char c : f.machine_id) if (!((c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c == '-')) return false;
  for (char c : f.session_id) if (!(AsciiAlphaNum(c) || c == '.' || c == '_' || c == ':' || c == '-')) return false;
  for (char c : r.sha256) if (!((c >= '0' && c <= '9') || (c >= 'a' && c <= 'f'))) return false;
  if (capture.source != DecisionCandidateSourceV1::gui_cache && capture.source != DecisionCandidateSourceV1::database_pool) return false;
  return !capture.owner_held || (capture.owner_thread_id && capture.capture_epoch && capture.owner_address);
}
bool ExactHash(std::string_view hash) noexcept {
  const std::string_view expected(kExecutableSha256);
  if (hash.size() != expected.size()) return false;
  for (std::size_t i = 0; i < hash.size(); ++i) {
    char value = hash[i]; if (value >= 'a' && value <= 'f') value = static_cast<char>(value - 'a' + 'A');
    if (value != expected[i]) return false;
  }
  return true;
}
bool Fail(DecisionCandidatesObservationV1 &out, DecisionCandidateReasonV1 reason) noexcept {
  out.completed = false; out.candidates.clear(); out.unavailable_reason = reason;
  return false;
}
struct Vector {
  std::uint64_t data = 0, allocator = 0;
  std::int32_t capacity = 0, count = 0;
};
struct Pass {
  const DecisionCandidateBindingsV1 &bindings;
  const DecisionCandidateReadContextV1 &context;
  DecisionCandidateAccessV1 access;
  std::vector<std::byte> transcript;
  std::vector<DecisionCandidateRowV1> rows;
  std::optional<std::int32_t> gui_actor;
  DecisionCandidateReasonV1 reason = DecisionCandidateReasonV1::native_read_unavailable;
  std::uint64_t character_slots = 0;
  std::int32_t character_capacity = 0;

  bool Bytes(std::uint64_t address, void *output, std::size_t size) {
    if (!address || !size || size > kMaximumTranscript || address > UINT64_MAX - (size - 1) ||
        transcript.size() > kMaximumTranscript - size ||
        transcript.size() + size > kMaximumTranscript - sizeof(address) - sizeof(std::uint64_t)) return false;
    if (!access.copy(access.context, address, output, size)) return false;
    const auto append = [this](const void *value, std::size_t bytes) {
      const auto *begin = static_cast<const std::byte *>(value);
      transcript.insert(transcript.end(), begin, begin + bytes);
    };
    append(&address, sizeof address); const std::uint64_t length = size;
    append(&length, sizeof length); append(output, size); return true;
  }
  template <class T> bool Read(std::uint64_t base, std::uint64_t offset, T &value) {
    static_assert(std::is_trivially_copyable_v<T>);
    return base && offset <= UINT64_MAX - base && Bytes(base + offset, &value, sizeof value);
  }
  bool Typed(std::uint64_t object, std::uint64_t vtable, std::uint64_t col, std::uint64_t type) {
    const auto base = bindings.image_base;
    std::uint64_t actual_vtable = 0, actual_col = 0; std::array<std::uint32_t,6> locator{};
    return object && Read(object, 0, actual_vtable) && actual_vtable == base + vtable &&
        Read(base, vtable - 8, actual_col) && actual_col == base + col &&
        Read(base, col, locator) && locator[0] == 1 && locator[1] == 0 &&
        locator[2] == 0 && locator[3] == type && locator[5] == col;
  }
  bool Header(std::uint64_t base, std::uint64_t offset, std::size_t bound, Vector &v) {
    return Read(base, offset, v.data) && Read(base, offset + 8, v.capacity) &&
        Read(base, offset + 12, v.count) && Read(base, offset + 16, v.allocator) &&
        v.capacity >= 0 && v.capacity <= 1'048'576 && v.count >= 0 &&
        static_cast<std::size_t>(v.count) <= bound && v.count <= v.capacity && (!v.count || v.data);
  }
  bool Character(std::int32_t full_id, bool alive) {
    const auto index = static_cast<std::uint32_t>(full_id) & 0xFFFFFFU;
    if (full_id == -1 || index >= static_cast<std::uint32_t>(character_capacity)) return false;
    std::uint64_t object = 0, death = 0; std::int32_t observed = -1; std::uint32_t tag = 0;
    if (!Read(character_slots, static_cast<std::uint64_t>(index) * 0x10 + 8, object) || !object ||
        !Read(object, 0x18, observed) || observed != full_id || !Read(object, 0x1C, tag) || tag != 0x43686172) return false;
    return !alive || (Read(object, 0x1D0, death) && !death);
  }
  bool Characters() {
    std::uint64_t storage = 0;
    return Read(bindings.image_base, kCharacterStorageSlotRva, storage) && storage &&
        Read(storage, 0x20, character_slots) && character_slots &&
        Read(storage, 0x2C, character_capacity) && character_capacity > 0 && character_capacity <= 0x1000000 &&
        Character(context.expected.frame.snapshot_actor_character_id, true);
  }
  bool Definition(std::uint64_t address, DecisionCandidateDefinitionV1 &out) {
    std::uint32_t tag = 0;
    if (!Typed(address, kDefinitionVtable, kDefinitionCol, kDefinitionType) ||
        !Read(address, 0x38, tag) || tag != 0x4744624F) return false;
    out.address = address; out.key.reset(); return true;
  }
  bool Database() {
    std::uint64_t database = 0; Vector definitions{};
    if (!Read(bindings.image_base, kDatabaseSlot, database) || database != context.expected.owner_address ||
        !Typed(database, kDatabaseVtable, kDatabaseCol, kDatabaseType) ||
        !Header(database, 0x50, kMaximumRows, definitions)) return false;
    rows.reserve(static_cast<std::size_t>(definitions.count));
    for (std::int32_t i = 0; i < definitions.count; ++i) {
      DecisionCandidateRowV1 row{}; std::uint64_t definition = 0;
      if (!Read(definitions.data, static_cast<std::uint64_t>(i) * 8, definition) || !Definition(definition, row.definition)) return false;
      row.database_index = static_cast<std::uint32_t>(i);
      row.command_unobserved_reason = DecisionCandidateReasonV1::not_queried;
      rows.push_back(std::move(row));
    }
    return true;
  }
  bool Gui() {
    const auto list = context.expected.owner_address;
    std::int32_t actor = -1;
    if (!Read(bindings.image_base, kGuiActorSlot, actor)) return false;
    gui_actor = actor;
    if (actor != context.expected.frame.snapshot_actor_character_id) {
      reason = DecisionCandidateReasonV1::gui_actor_differs_from_snapshot; return false;
    }
    if (!Character(actor, true) || !Typed(list, kGuiVtable, kGuiCol, kGuiType)) return false;
    Vector groups{};
    if (!Header(list, 0x260, kMaximumGroups, groups)) return false;
    for (std::int32_t g = 0; g < groups.count; ++g) {
      const auto group_offset = static_cast<std::uint64_t>(g) * 0x20;
      std::uint64_t group_definition = 0; Vector members{};
      if (!Read(groups.data, group_offset, group_definition) || !group_definition ||
          !Header(groups.data, group_offset + 8, kMaximumGroupRows, members) ||
          static_cast<std::size_t>(members.count) > kMaximumRows - rows.size()) return false;
      for (std::int32_t r = 0; r < members.count; ++r) {
        const auto offset = static_cast<std::uint64_t>(r) * 0x20;
        DecisionCandidateRowV1 row{}; std::uint64_t definition = 0;
        if (!Read(members.data, offset, definition) || !Definition(definition, row.definition) ||
            !Read(members.data, offset + 8, row.parameter_address) ||
            !Read(members.data, offset + 0x10, row.row_actor_character_id) ||
            !Read(members.data, offset + 0x14, row.cached_enabled_byte) ||
            !Read(members.data, offset + 0x18, row.gui_owner_address) || row.gui_owner_address != list ||
            !Character(row.row_actor_character_id, false)) return false;
        row.group_index = static_cast<std::uint32_t>(g); row.row_index = static_cast<std::uint32_t>(r);
        row.command_unobserved_reason = DecisionCandidateReasonV1::parameter_scope_unverified;
        rows.push_back(std::move(row));
      }
    }
    return true;
  }
  bool Run() { return Characters() && (context.expected.source == DecisionCandidateSourceV1::gui_cache ? Gui() : Database()); }
};
bool Current(const DecisionCandidateReadContextV1 &context) noexcept {
  DecisionCandidateCaptureV1 current{};
  return context.read_current_capture(context.current_capture_context, current) && current == context.expected;
}
void Quote(std::string &out, std::string_view value) {
  static constexpr char digits[] = "0123456789abcdef";
  out.push_back(static_cast<char>(34));
  for (unsigned char c : value) {
    if (c == 34 || c == 92) { out.push_back(static_cast<char>(92)); out.push_back(static_cast<char>(c)); }
    else if (c < 32) { out.push_back(static_cast<char>(92)); out += "u00"; out.push_back(digits[c >> 4]); out.push_back(digits[c & 15]); }
    else out.push_back(static_cast<char>(c));
  }
  out.push_back(static_cast<char>(34));
}
void Decimal(std::string &out, std::uint64_t value) { Quote(out, std::to_string(value)); }
bool ValidRows(const DecisionCandidatesObservationV1 &value) {
  if (!value.capture.owner_held || !value.capture.paused_application_main_owner_held || value.candidates.size() > kMaximumRows) return false;
  const bool gui = value.capture.source == DecisionCandidateSourceV1::gui_cache;
  if ((gui && value.gui_global_actor_character_id != value.capture.frame.snapshot_actor_character_id) ||
      (!gui && value.gui_global_actor_character_id)) return false;
  std::set<std::uint64_t> positions;
  for (const auto &row : value.candidates) {
    if (!row.definition.address || Reason(row.command_unobserved_reason).empty()) return false;
    if (row.definition.key) {
      if (row.definition.key->empty() || row.definition.key->size() > 192) return false;
      for (char c : *row.definition.key) if (!(AsciiAlphaNum(c) || c == '_')) return false;
    }
    if (gui) {
      if (row.group_index >= kMaximumGroups || row.row_index >= kMaximumGroupRows || row.row_actor_character_id == -1 ||
          row.gui_owner_address != value.capture.owner_address ||
          !positions.insert((static_cast<std::uint64_t>(row.group_index) << 32) | row.row_index).second) return false;
    } else if (row.database_index > INT32_MAX || !positions.insert(row.database_index).second) return false;
  }
  return true;
}
std::string Packet(const DecisionCandidatesObservationV1 &value, bool complete, DecisionCandidateReasonV1 reason) {
  const auto &c = value.capture; const auto &f = c.frame;
  const bool gui = c.source == DecisionCandidateSourceV1::gui_cache;
  std::string out; out.reserve(2048 + (complete ? value.candidates.size() : 0) * 300);
  out += "{\"schema\":\"ck3_1210_decision_candidates_data_v1\",\"game_version\":\"1.21.0\",\"executable_sha256\":";
  Quote(out, kExecutableSha256);
  out += ",\"read_only\":true,\"action_qualified\":false,\"complete_snapshot\":false,\"status\":";
  Quote(out, complete ? "candidate_data" : "unavailable");
  out += ",\"binding\":{\"machine_id\":"; Quote(out, f.machine_id);
  out += ",\"game\":{\"pid\":" + std::to_string(f.game_pid) + ",\"creation_filetime\":";
  Decimal(out, f.game_creation_filetime); out += "},\"session_id\":"; Quote(out, f.session_id);
  out += ",\"connection_generation\":"; Decimal(out, f.connection_generation);
  out += ",\"native_revision\":"; Decimal(out, f.native_revision);
  out += ",\"date_raw\":" + std::to_string(f.date_raw) + ",\"snapshot_actor_character_id\":" + std::to_string(f.snapshot_actor_character_id) + "}";
  out += ",\"source\":{\"kind\":"; Quote(out, gui ? "gui_cache_0x260" : "database_definitions_0x50_count_0x5c");
  out += ",\"producer_source\":{\"path\":"; Quote(out, c.producer_source.path);
  out += ",\"bytes\":" + std::to_string(c.producer_source.bytes) + ",\"sha256\":"; Quote(out, c.producer_source.sha256);
  out += "},\"owner\":{\"status\":"; Quote(out, c.owner_held ? "held" : "not_held");
  if (c.owner_held) {
    out += ",\"thread_id\":" + std::to_string(c.owner_thread_id) + ",\"capture_epoch\":"; Decimal(out, c.capture_epoch);
    out += ",\"owner_address\":"; Decimal(out, c.owner_address);
  } else out += ",\"reason\":\"owner_not_held\"";
  out += "},\"gui_global_actor_character_id\":";
  if (gui && value.gui_global_actor_character_id) out += std::to_string(*value.gui_global_actor_character_id); else out += "null";
  out += "},\"candidates\":";
  if (!complete) out += "null";
  else {
    out += '[';
    bool first = true;
    for (const auto &row : value.candidates) {
      if (!first) out += ',';
      first = false;
      if (gui) out += "{\"group_index\":" + std::to_string(row.group_index) + ",\"row_index\":" + std::to_string(row.row_index);
      else out += "{\"database_index\":" + std::to_string(row.database_index);
      out += ",\"definition\":{\"address\":"; Decimal(out, row.definition.address); out += ",\"key\":";
      if (row.definition.key) Quote(out, *row.definition.key); else out += "null";
      out += '}';
      if (gui) {
        out += ",\"parameter_address\":"; Decimal(out, row.parameter_address);
        out += ",\"row_actor_character_id\":" + std::to_string(row.row_actor_character_id);
        out += ",\"cached_enabled_byte\":" + std::to_string(static_cast<unsigned>(row.cached_enabled_byte));
        out += ",\"gui_owner_address\":"; Decimal(out, row.gui_owner_address);
      }
      out += ",\"command_availability\":{\"status\":\"unobserved\",\"reason\":";
      Quote(out, Reason(row.command_unobserved_reason)); out += "}}";
    }
    out += ']';
  }
  out += ",\"unavailable_reason\":";
  if (complete) out += "null"; else Quote(out, Reason(reason));
  out += '}'; return out;
}
} // namespace
DecisionCandidateBindingsV1 BindDecisionCandidateImageV1(std::uint64_t base, std::string_view hash) noexcept {
  if (!base || base > UINT64_MAX - 0x7000000 || !ExactHash(hash)) return {};
  return {true, base};
}
bool ReadDecisionCandidatesV1(const DecisionCandidateBindingsV1 &bindings,
    const DecisionCandidateReadContextV1 &context, DecisionCandidateAccessV1 access,
    DecisionCandidatesObservationV1 &out) noexcept {
  try {
    out = {}; out.capture = context.expected;
    if (!ValidMetadata(context.expected)) return Fail(out, DecisionCandidateReasonV1::native_read_unavailable);
    if (!bindings.exact_build_admitted || !bindings.image_base || bindings.image_base > UINT64_MAX - 0x7000000 || !context.source_pins_admitted)
      return Fail(out, DecisionCandidateReasonV1::source_pins_unavailable);
    if (!context.expected.owner_held || !context.expected.paused_application_main_owner_held)
      return Fail(out, DecisionCandidateReasonV1::owner_not_held);
    if (!access.copy || !context.read_current_capture) return Fail(out, DecisionCandidateReasonV1::native_read_unavailable);
    if (!Current(context)) return Fail(out, DecisionCandidateReasonV1::frame_not_current);
    Pass first{bindings, context, access};
    if (!first.Run()) { out.gui_global_actor_character_id = first.gui_actor; return Fail(out, first.reason); }
    out.gui_global_actor_character_id = first.gui_actor;
    if (!Current(context)) return Fail(out, DecisionCandidateReasonV1::frame_not_current);
    Pass second{bindings, context, access};
    if (!second.Run()) { out.gui_global_actor_character_id = second.gui_actor; return Fail(out, second.reason); }
    if (!Current(context) || first.transcript != second.transcript || first.rows != second.rows || first.gui_actor != second.gui_actor)
      return Fail(out, DecisionCandidateReasonV1::frame_not_current);
    out.gui_global_actor_character_id = first.gui_actor;
    out.candidates = std::move(first.rows); out.completed = true; return true;
  } catch (...) { return Fail(out, DecisionCandidateReasonV1::native_read_unavailable); }
}
bool SerializeDecisionCandidatesV1(const DecisionCandidatesObservationV1 &value, std::string &output) noexcept {
  output.clear();
  try {
    if (!ValidMetadata(value.capture) || Reason(value.unavailable_reason).empty()) return false;
    const bool complete = value.completed && ValidRows(value);
    auto reason = value.completed && !complete ? DecisionCandidateReasonV1::native_read_unavailable : value.unavailable_reason;
    output = Packet(value, complete, reason);
    if (output.size() > kMaximumWire) output = Packet(value, false, DecisionCandidateReasonV1::native_read_unavailable);
    if (output.size() > kMaximumWire) { output.clear(); return false; }
    return true;
  } catch (...) { output.clear(); return false; }
}
} // namespace xar::ck3_1210
