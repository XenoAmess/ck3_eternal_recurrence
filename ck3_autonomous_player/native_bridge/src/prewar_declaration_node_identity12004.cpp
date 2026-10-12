#include "xar_bridge/prewar_declaration_node_identity12004.hpp"

#include <algorithm>
#include <cstring>
#include <limits>
#include <type_traits>

#if defined(_MSC_VER) && defined(_WIN32)
#include <windows.h>
#endif

namespace xar::ck3_12004 {
namespace {
using ReadStatus = PrewarNodeReadStatus12004;
using Status = PrewarNodeStatus12004;
using RefStatus = PrewarNodeReferenceStatus12004;
using Layout = PrewarNodeLayout12004;
constexpr std::uintptr_t kSequenceVptrRva = 0x492E2E0;
constexpr std::uintptr_t kSequenceInvokeRva = 0x3766300;
constexpr std::uintptr_t kOnActionManagerRva = 0x5D1F6C8;
constexpr std::size_t kCbStartEffectOffset = 0x870;
constexpr std::array<std::size_t, 3> kIdentitySlotOffsets{0x28, 0x30, 0xB0};
constexpr std::array<std::size_t, 3> kDefinitionOffsets{0x300, 0x310, 0x308};

// Kept trivial: MSVC /EHsc outer catch does not catch an access violation.
bool CopyScalarLeaf(const void *source, void *destination,
                    std::size_t length) noexcept {
#if defined(_MSC_VER) && defined(_WIN32)
  __try {
    std::memcpy(destination, source, length);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  (void)source;
  (void)destination;
  (void)length;
  return false;
#endif
}

bool Span(std::uintptr_t base, std::size_t offset, std::size_t size,
          std::uintptr_t &address) noexcept {
  constexpr auto max = std::numeric_limits<std::uintptr_t>::max();
  if (offset > max - base) return false;
  address = base + offset;
  return size != 0 && size - 1 <= max - address;
}
bool Product(std::size_t count, std::size_t stride,
             std::size_t &bytes) noexcept {
  if (stride != 0 && count > std::numeric_limits<std::size_t>::max() / stride)
    return false;
  bytes = count * stride;
  return true;
}
bool InModule(const PrewarDeclarationNodeIdentityBindings12004 &bindings,
              std::uintptr_t address, std::size_t size) noexcept {
  if (address < bindings.image_base || size == 0) return false;
  const auto offset = address - bindings.image_base;
  return offset < bindings.runtime_image_size &&
         size <= bindings.runtime_image_size - offset;
}
bool ReadSucceeded(ReadStatus status) noexcept {
  return status == ReadStatus::observed || status == ReadStatus::observed_null;
}
Status StatusFromRead(ReadStatus status) noexcept {
  switch (status) {
  case ReadStatus::address_overflow: return Status::address_overflow;
  case ReadStatus::byte_cap: return Status::byte_cap;
  case ReadStatus::attempt_cap: return Status::attempt_cap;
  default: return Status::unreadable;
  }
}
RefStatus ReferenceFromRead(ReadStatus status) noexcept {
  switch (status) {
  case ReadStatus::observed: return RefStatus::captured;
  case ReadStatus::observed_null: return RefStatus::observed_null;
  case ReadStatus::address_overflow: return RefStatus::address_overflow;
  case ReadStatus::byte_cap: return RefStatus::byte_cap;
  case ReadStatus::attempt_cap: return RefStatus::attempt_cap;
  case ReadStatus::unobserved: return RefStatus::unobserved;
  default: return RefStatus::unreadable;
  }
}
std::string_view Reason(Status status) noexcept {
  switch (status) {
  case Status::captured: return "captured";
  case Status::known_empty: return "known_empty";
  case Status::unsupported_layout: return "unsupported_layout";
  case Status::unreadable: return "unreadable";
  case Status::address_overflow: return "address_overflow";
  case Status::negative_count: return "negative_count";
  case Status::null_nonzero_data: return "null_nonzero_data";
  case Status::null_child: return "null_child";
  case Status::node_cap: return "node_cap";
  case Status::edge_cap: return "edge_cap";
  case Status::depth_cap: return "depth_cap";
  case Status::byte_cap: return "byte_cap";
  case Status::attempt_cap: return "attempt_cap";
  case Status::cycle: return "cycle";
  case Status::invalid_binding: return "invalid_binding";
  case Status::invalid_selection: return "invalid_selection";
  case Status::invalid_frame: return "invalid_frame";
  case Status::role_identity: return "role_identity";
  case Status::clock_changed: return "clock_changed";
  case Status::allocation_failure: return "allocation_failure";
  case Status::unqualified_roles: return "unqualified_roles";
  default: return "unobserved";
  }
}

class Capture {
 public:
  Capture(const PrewarDeclarationNodeIdentityBindings12004 &bindings,
          PrewarDeclarationNodeIdentity12004 &output)
      : bindings_(bindings), output_(output), raw_(output.private_identity) {}

  template <class T>
  bool Scalar(std::uintptr_t base, std::size_t offset, T &value,
              ReadStatus &status) noexcept {
    static_assert(std::is_trivially_copyable_v<T>);
    std::uintptr_t address = 0;
    if (!Span(base, offset, sizeof(T), address)) {
      status = ReadStatus::address_overflow;
      return false;
    }
    if (raw_.read_attempts >= kPrewarNodeReadAttemptLimit12004) {
      status = ReadStatus::attempt_cap;
      return false;
    }
    if (sizeof(T) > kPrewarNodeReadByteLimit12004 - raw_.read_bytes) {
      status = ReadStatus::byte_cap;
      return false;
    }
    ++raw_.read_attempts;
    raw_.read_bytes += static_cast<std::uint32_t>(sizeof(T));
    if (address == 0 || !CopyScalarLeaf(reinterpret_cast<const void *>(address),
                                       &value, sizeof(T))) {
      status = ReadStatus::unreadable;
      return false;
    }
    status = ReadStatus::observed;
    return true;
  }

  void Pointer(std::uintptr_t base, std::size_t offset,
               PrewarNodeRawField12004 &field) noexcept {
    if (Scalar(base, offset, field.value, field.status) && field.value == 0)
      field.status = ReadStatus::observed_null;
  }

  bool Role(std::int32_t id, const void *supplied,
            PrewarDeclarationNodeRoleWitness12004 &role,
            bool require_supplied) noexcept {
    role.supplied_address = reinterpret_cast<std::uintptr_t>(supplied);
    if (id == -1 || (require_supplied && !supplied)) return false;
    Pointer(reinterpret_cast<std::uintptr_t>(bindings_.core.character_storage_slot),
            0, role.storage);
    if (role.storage.status != ReadStatus::observed) return false;
    Pointer(role.storage.value, kCharacterStorageSlotsOffset, role.slots);
    Scalar(role.storage.value, kCharacterStorageCapacityOffset,
           role.capacity_raw, role.capacity_status);
    const auto index = static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
    if (role.slots.status != ReadStatus::observed ||
        role.capacity_status != ReadStatus::observed ||
        role.capacity_raw <= 0 || index >= static_cast<std::uint32_t>(role.capacity_raw))
      return false;
    std::size_t slot_offset = 0;
    if (!Product(index, kCharacterStorageSlotStride, slot_offset) ||
        slot_offset > std::numeric_limits<std::size_t>::max() -
                          kCharacterStorageObjectOffset) return false;
    Pointer(role.slots.value, slot_offset + kCharacterStorageObjectOffset,
            role.resolved_address);
    if (role.resolved_address.status != ReadStatus::observed) return false;
    Scalar(role.resolved_address.value, kCharacterFullIdOffset,
           role.full_id_raw, role.id_status);
    Pointer(role.resolved_address.value, kCharacterDeathDataOffset, role.death_data);
    role.verified_alive = role.id_status == ReadStatus::observed &&
        role.full_id_raw == static_cast<std::uint32_t>(id) &&
        role.death_data.status == ReadStatus::observed_null &&
        (!require_supplied || role.resolved_address.value == role.supplied_address);
    return role.verified_alive;
  }

  bool Clock(const CoreSnapshotPrefix &frame, bool after) noexcept {
    auto &game = after ? raw_.clock_after_roots[0] : raw_.game_state;
    auto &jomini = after ? raw_.clock_after_roots[1] : raw_.jomini_state;
    auto &statuses = after ? raw_.clock_after_read_status : raw_.clock_read_status;
    auto &date = after ? raw_.date_after_raw : raw_.date_raw;
    auto &speed = after ? raw_.native_speed_after_raw : raw_.native_speed_raw;
    auto &paused = after ? raw_.paused_after_raw : raw_.paused_raw;
    Pointer(reinterpret_cast<std::uintptr_t>(bindings_.core.game_state_slot), 0, game);
    Pointer(reinterpret_cast<std::uintptr_t>(bindings_.core.jomini_state_slot), 0, jomini);
    if (game.status != ReadStatus::observed || jomini.status != ReadStatus::observed)
      return false;
    Scalar(game.value, kGameStateDateOffset, date, statuses[0]);
    Scalar(game.value, kGameStateSpeedOffset, speed, statuses[1]);
    Scalar(jomini.value, kJominiPausedOffset, paused, statuses[2]);
    return statuses[0] == ReadStatus::observed &&
        statuses[1] == ReadStatus::observed && statuses[2] == ReadStatus::observed &&
        date == frame.clock.date_raw && speed >= 0 && speed < 5 &&
        speed + 1 == frame.clock.speed && paused != 0;
  }

  Status ClockFailure(bool after) const noexcept {
    const auto &game = after ? raw_.clock_after_roots[0] : raw_.game_state;
    const auto &jomini = after ? raw_.clock_after_roots[1] : raw_.jomini_state;
    const auto &statuses = after ? raw_.clock_after_read_status : raw_.clock_read_status;
    if (game.status != ReadStatus::observed) return StatusFromRead(game.status);
    if (jomini.status != ReadStatus::observed) return StatusFromRead(jomini.status);
    for (const auto status : statuses)
      if (status != ReadStatus::observed) return StatusFromRead(status);
    return Status::clock_changed;
  }

  void Mark(Status status, std::uint16_t node = kPrewarNodeNoIndex12004,
            std::uint32_t ordinal = 0) noexcept {
    complete_ = false;
    if (output_.status == Status::unobserved || output_.status == Status::captured ||
        output_.status == Status::unqualified_roles) {
      output_.status = status;
      raw_.failure_node = node;
      raw_.failure_ordinal = ordinal;
    }
  }

  std::uint16_t Node(std::uintptr_t address, Layout requested,
                     std::size_t depth, RefStatus &reference) {
    if (address == 0) {
      reference = RefStatus::observed_null;
      return kPrewarNodeNoIndex12004;
    }
    for (std::size_t i = 0; i < raw_.nodes.size(); ++i) {
      if (raw_.nodes[i].address != address) continue;
      // The same address reached with a different qualified receiver layout
      // is unsupported, rather than silently reusing an incompatible view.
      if (output_.rows[i].layout != requested &&
          !(requested == Layout::unknown_compiled &&
            output_.rows[i].layout == Layout::sequence_list)) {
        reference = RefStatus::shared_node;
        Mark(Status::unsupported_layout, static_cast<std::uint16_t>(i));
      } else if (active_[i]) {
        reference = RefStatus::cycle;
        Mark(Status::cycle, static_cast<std::uint16_t>(i));
      } else {
        reference = RefStatus::shared_node;
      }
      return static_cast<std::uint16_t>(i);
    }
    if (depth >= kPrewarNodeDepthLimit12004) {
      reference = RefStatus::depth_cap;
      Mark(Status::depth_cap);
      return kPrewarNodeNoIndex12004;
    }
    if (raw_.nodes.size() >= kPrewarNodeLimit12004) {
      reference = RefStatus::node_cap;
      Mark(Status::node_cap);
      return kPrewarNodeNoIndex12004;
    }
    const auto index = static_cast<std::uint16_t>(raw_.nodes.size());
    raw_.nodes.emplace_back();
    raw_.nodes[index].address = address;
    output_.rows.emplace_back();
    output_.rows[index].layout = requested;
    output_.rows[index].status = Status::captured;
    active_[index] = true;
    reference = RefStatus::captured;
    if (requested == Layout::opaque_payload) {
      output_.rows[index].status = Status::unsupported_layout;
      Mark(Status::unsupported_layout, index);
    } else if (requested == Layout::on_action_definition) {
      Definition(index, depth);
    } else {
      Compiled(index, depth);
    }
    active_[index] = false;
    return index;
  }

  void Roots(const void *cb) {
    std::uintptr_t root = 0;
    if (!Span(reinterpret_cast<std::uintptr_t>(cb), kCbStartEffectOffset,
              sizeof(std::uintptr_t), root)) {
      Mark(Status::address_overflow);
    } else {
      RefStatus reference = RefStatus::unobserved;
      output_.cb_root_index = Node(root, Layout::unknown_compiled, 0, reference);
    }
    Pointer(bindings_.image_base, kOnActionManagerRva, raw_.on_action_manager);
    if (raw_.on_action_manager.status != ReadStatus::observed) {
      Mark(StatusFromRead(raw_.on_action_manager.status));
      return;
    }
    Pointer(raw_.on_action_manager.value, 0x38, raw_.on_action_table);
    if (raw_.on_action_table.status != ReadStatus::observed) {
      Mark(StatusFromRead(raw_.on_action_table.status));
      return;
    }
    Pointer(raw_.on_action_table.value, 0x2D8, raw_.on_action_definition);
    output_.on_action_definition_observed = ReadSucceeded(raw_.on_action_definition.status);
    output_.on_action_definition_known_null =
        raw_.on_action_definition.status == ReadStatus::observed_null;
    if (!output_.on_action_definition_observed) {
      Mark(StatusFromRead(raw_.on_action_definition.status));
    } else if (!output_.on_action_definition_known_null) {
      RefStatus reference = RefStatus::unobserved;
      output_.on_action_root_index = Node(raw_.on_action_definition.value,
          Layout::on_action_definition, 0, reference);
    }
  }

  bool Complete() const noexcept { return complete_; }

 private:
  PrewarNodeRva12004 Rva(const PrewarNodeRawField12004 &field) const noexcept {
    PrewarNodeRva12004 result;
    result.observed = ReadSucceeded(field.status);
    if (result.observed && field.value != 0 && InModule(bindings_, field.value, 1)) {
      const auto offset = field.value - bindings_.image_base;
      if (offset <= std::numeric_limits<std::uint32_t>::max()) {
        result.in_module = true;
        result.value = static_cast<std::uint32_t>(offset);
      }
    }
    return result;
  }

  std::size_t ReserveEdges(std::uint16_t node, std::size_t wanted) {
    const auto begin = raw_.edges.size();
    const auto available = kPrewarNodeEdgeLimit12004 - begin;
    const auto accepted = std::min(available, wanted);
    output_.rows[node].edge_begin = static_cast<std::uint16_t>(begin);
    output_.rows[node].edge_count = static_cast<std::uint16_t>(accepted);
    for (std::size_t ordinal = 0; ordinal < accepted; ++ordinal) {
      PrewarDeclarationNodeRawEdge12004 edge;
      edge.parent_index = node;
      edge.ordinal = static_cast<std::uint32_t>(ordinal);
      raw_.edges.push_back(edge);
      output_.ordered_edges.emplace_back();
    }
    if (accepted != wanted) {
      output_.rows[node].status = Status::edge_cap;
      Mark(Status::edge_cap, node, static_cast<std::uint32_t>(accepted));
    }
    return accepted;
  }

  void Follow(std::size_t edge_index, Layout layout, std::size_t depth,
              bool null_is_error) {
    const auto target = raw_.edges[edge_index].target;
    output_.ordered_edges[edge_index].status = ReferenceFromRead(target.status);
    if (!ReadSucceeded(target.status)) {
      Mark(StatusFromRead(target.status), raw_.edges[edge_index].parent_index,
           raw_.edges[edge_index].ordinal);
      return;
    }
    if (target.value == 0) {
      if (null_is_error) {
        output_.rows[raw_.edges[edge_index].parent_index].status = Status::null_child;
        Mark(Status::null_child, raw_.edges[edge_index].parent_index,
             raw_.edges[edge_index].ordinal);
      }
      return;
    }
    RefStatus reference = RefStatus::unobserved;
    const auto child = Node(target.value, layout, depth + 1, reference);
    output_.ordered_edges[edge_index].target_index = child;
    output_.ordered_edges[edge_index].status = reference;
    if (reference == RefStatus::cycle || reference == RefStatus::node_cap ||
        reference == RefStatus::depth_cap) {
      // Preserve the originating ordered occurrence, including cap position.
      if (raw_.failure_node == kPrewarNodeNoIndex12004) {
        raw_.failure_node = raw_.edges[edge_index].parent_index;
        raw_.failure_ordinal = raw_.edges[edge_index].ordinal;
      }
    }
  }

  void Compiled(std::uint16_t index, std::size_t depth) {
    auto &raw_node = raw_.nodes[index];
    const auto address = raw_node.address;
    Pointer(address, 0, raw_node.identity[0]);
    if (raw_node.identity[0].status == ReadStatus::observed) {
      for (std::size_t slot = 0; slot < kIdentitySlotOffsets.size(); ++slot)
        Pointer(raw_node.identity[0].value, kIdentitySlotOffsets[slot],
                raw_node.identity[slot + 1]);
    }
    auto &row = output_.rows[index];
    for (std::size_t field = 0; field < raw_node.identity.size(); ++field) {
      row.identity_read_status[field] = raw_node.identity[field].status;
      if (raw_node.identity[field].status != ReadStatus::observed) {
        row.status = StatusFromRead(raw_node.identity[field].status);
        Mark(row.status, index, static_cast<std::uint32_t>(field));
      }
    }
    row.vptr = Rva(raw_node.identity[0]);
    row.scope_kind_callee = Rva(raw_node.identity[1]);
    row.scope_mask_callee = Rva(raw_node.identity[2]);
    row.invoke_callee = Rva(raw_node.identity[3]);
    const bool sequence = row.vptr.in_module && row.vptr.value == kSequenceVptrRva &&
        row.invoke_callee.in_module && row.invoke_callee.value == kSequenceInvokeRva;
    if (!sequence) {
      row.status = Status::unsupported_layout;
      Mark(Status::unsupported_layout, index);
      return;
    }
    row.layout = Layout::sequence_list;
    Pointer(address, 0x30, raw_node.child_data);
    Scalar(address, 0x3C, raw_node.child_count_raw, raw_node.child_count_status);
    row.child_count_observed = raw_node.child_count_status == ReadStatus::observed;
    row.child_count_raw = raw_node.child_count_raw;
    if (!ReadSucceeded(raw_node.child_data.status) || !row.child_count_observed) {
      row.status = !ReadSucceeded(raw_node.child_data.status)
          ? StatusFromRead(raw_node.child_data.status)
          : StatusFromRead(raw_node.child_count_status);
      Mark(row.status, index);
      return;
    }
    if (raw_node.child_count_raw < 0) {
      row.status = Status::negative_count;
      Mark(row.status, index);
      return;
    }
    if (raw_node.child_count_raw == 0) {
      // Only this qualified native sequence layout admits known empty.
      if (row.status == Status::captured) row.status = Status::known_empty;
      return;
    }
    if (raw_node.child_data.value == 0) {
      row.status = Status::null_nonzero_data;
      Mark(row.status, index);
      return;
    }
    const auto count = static_cast<std::size_t>(raw_node.child_count_raw);
    std::size_t bytes = 0;
    std::uintptr_t array_start = 0;
    if (!Product(count, sizeof(std::uintptr_t), bytes) ||
        !Span(raw_node.child_data.value, 0, bytes, array_start)) {
      row.status = Status::address_overflow;
      Mark(row.status, index);
      return;
    }
    const auto data = raw_node.child_data.value;
    const auto begin = raw_.edges.size();
    const auto accepted = ReserveEdges(index, count);
    // Reserve the entire parent's edge range before descending, preserving
    // contiguous ordered ranges even when children create their own edges.
    for (std::size_t ordinal = 0; ordinal < accepted; ++ordinal) {
      std::size_t offset = 0;
      if (!Product(ordinal, sizeof(std::uintptr_t), offset)) {
        raw_.edges[begin + ordinal].target.status = ReadStatus::address_overflow;
      } else {
        Pointer(data, offset, raw_.edges[begin + ordinal].target);
      }
    }
    for (std::size_t ordinal = 0; ordinal < accepted; ++ordinal)
      Follow(begin + ordinal, Layout::unknown_compiled, depth, true);
  }

  void Definition(std::uint16_t index, std::size_t depth) {
    const auto address = raw_.nodes[index].address;
    // +300/+310 are opaque references; no payload is treated as a list.
    // +308 is the only source-qualified recursive definition reference.
    for (std::size_t field = 0; field < kDefinitionOffsets.size(); ++field) {
      Pointer(address, kDefinitionOffsets[field], raw_.nodes[index].definition_fields[field]);
      if (!ReadSucceeded(raw_.nodes[index].definition_fields[field].status)) {
        output_.rows[index].status =
            StatusFromRead(raw_.nodes[index].definition_fields[field].status);
        Mark(output_.rows[index].status, index, static_cast<std::uint32_t>(field));
      }
    }
    const auto begin = raw_.edges.size();
    const auto accepted = ReserveEdges(index, kDefinitionOffsets.size());
    for (std::size_t field = 0; field < accepted; ++field)
      raw_.edges[begin + field].target = raw_.nodes[index].definition_fields[field];
    for (std::size_t field = 0; field < accepted; ++field)
      Follow(begin + field, field == 2 ? Layout::on_action_definition
                                      : Layout::opaque_payload, depth, false);
  }

  const PrewarDeclarationNodeIdentityBindings12004 &bindings_;
  PrewarDeclarationNodeIdentity12004 &output_;
  PrewarDeclarationNodeIdentityPrivateWitness12004 &raw_;
  std::array<bool, kPrewarNodeLimit12004> active_{};
  bool complete_ = true;
};

PrewarDeclarationNodeFrame12004 FrameCopy(const CoreSnapshotPrefix &frame) noexcept {
  return {frame.clock.date_raw, frame.clock.speed, frame.clock.paused,
          frame.local_player_id, frame.map_ready, frame.has_played_character,
          frame.played_character_id, frame.played_character_alive};
}
bool FrameAdmitted(const CoreSnapshotPrefix &frame) noexcept {
  return frame.clock.paused && frame.clock.speed >= 1 && frame.clock.speed <= 5 &&
      frame.map_ready && frame.has_played_character && frame.played_character_alive &&
      frame.played_character_id != -1 && frame.local_player_id >= 0;
}
} // namespace

PrewarDeclarationNodeIdentityBindings12004
BindPrewarDeclarationNodeIdentityImage12004(
    const CoreBindings &actual_core, std::uintptr_t image_base,
    std::size_t runtime_image_size, std::string_view executable_sha256) noexcept {
  PrewarDeclarationNodeIdentityBindings12004 bindings;
  bindings.core = actual_core;
  bindings.image_base = image_base;
  bindings.runtime_image_size = runtime_image_size;
  std::uintptr_t last = 0;
  if (!actual_core.enabled || image_base == 0 || runtime_image_size == 0 ||
      runtime_image_size - 1 > std::numeric_limits<std::uint32_t>::max() ||
      executable_sha256 != kExecutableSha256 ||
      !Span(image_base, 0, runtime_image_size, last)) return bindings;
  constexpr std::array<std::uintptr_t, 6> rvas{
      kGameStateSlotRva, kJominiStateSlotRva, kCharacterStorageSlotRva,
      kSequenceVptrRva, kSequenceInvokeRva, kOnActionManagerRva};
  for (const auto rva : rvas) {
    std::uintptr_t address = 0;
    if (!Span(image_base, rva, sizeof(std::uintptr_t), address) ||
        !InModule(bindings, address, sizeof(std::uintptr_t))) return bindings;
  }
  if (reinterpret_cast<std::uintptr_t>(actual_core.game_state_slot) !=
          image_base + kGameStateSlotRva ||
      reinterpret_cast<std::uintptr_t>(actual_core.jomini_state_slot) !=
          image_base + kJominiStateSlotRva ||
      reinterpret_cast<std::uintptr_t>(actual_core.character_storage_slot) !=
          image_base + kCharacterStorageSlotRva) return bindings;
#if defined(_MSC_VER) && defined(_WIN64)
  bindings.enabled = true;
#endif
  return bindings;
}

bool ReadPrewarDeclarationNodeIdentity12004(
    const PrewarDeclarationNodeIdentityBindings12004 &bindings,
    const PrewarDeclarationNodeIdentityNativeScope12004 &selected_scope,
    const PrewarDeclarationNodeSelectionObservation12004 &observation,
    PrewarDeclarationNodeIdentity12004 &output, std::string_view *reason) noexcept {
  output = {};
  if (reason) *reason = {};
  auto reject = [&](Status status) noexcept {
    output.status = status;
    output.structural_capture_complete = false;
    if (reason) *reason = Reason(status);
    return false;
  };
  try {
    output.query_ticket = observation.query_ticket;
    output.epoch = observation.epoch;
    output.native_revision = observation.native_revision;
    output.public_revision = observation.public_revision;
    output.frame = FrameCopy(observation.frame);
    output.selection = observation.selection; // Full ordered tuple, no truncation.
    output.finalized_selection_ready = observation.finalized_selection_ready;
    output.named_roles_ready = observation.named_roles_ready;
    output.private_identity.source_module_base = bindings.image_base;
    output.private_identity.source_module_size = bindings.runtime_image_size;
    output.private_identity.source_core_slot_addresses = {
        reinterpret_cast<std::uintptr_t>(bindings.core.game_state_slot),
        reinterpret_cast<std::uintptr_t>(bindings.core.jomini_state_slot),
        reinterpret_cast<std::uintptr_t>(bindings.core.character_storage_slot)};
    output.private_identity.actual_cb_address =
        reinterpret_cast<std::uintptr_t>(selected_scope.actual_cb);
    if (!bindings.enabled) return reject(Status::invalid_binding);
    if (!selected_scope.actual_cb || !selected_scope.actual_actor ||
        !selected_scope.actual_target || observation.query_ticket == 0 ||
        observation.selection.actor_character_id == -1 ||
        observation.selection.target_character_id == -1 ||
        observation.selection.cb_key.empty() || observation.selection.casus_belli_index < 0 ||
        observation.selection.cb_config_index < -1)
      return reject(Status::invalid_selection);
    if (!FrameAdmitted(observation.frame)) return reject(Status::invalid_frame);
    output.rows.reserve(kPrewarNodeLimit12004);
    output.ordered_edges.reserve(kPrewarNodeEdgeLimit12004);
    output.private_identity.nodes.reserve(kPrewarNodeLimit12004);
    output.private_identity.edges.reserve(kPrewarNodeEdgeLimit12004);
    Capture capture(bindings, output);
    if (!capture.Clock(observation.frame, false)) return reject(capture.ClockFailure(false));
    auto &roles = output.private_identity.roles;
    roles[1].supplied_address = reinterpret_cast<std::uintptr_t>(selected_scope.primary_attacker);
    roles[2].supplied_address = reinterpret_cast<std::uintptr_t>(selected_scope.primary_defender);
    if (!capture.Role(observation.selection.actor_character_id,
                      selected_scope.actual_actor, roles[0], true) ||
        !capture.Role(observation.selection.target_character_id,
                      selected_scope.actual_target, roles[3], true) ||
        !capture.Role(observation.frame.played_character_id, nullptr, roles[4], false))
      return reject(Status::role_identity);
    if (observation.named_roles_ready) {
      if (!capture.Role(observation.selection.primary_attacker_character_id,
                        selected_scope.primary_attacker, roles[1], true) ||
          !capture.Role(observation.selection.primary_defender_character_id,
                        selected_scope.primary_defender, roles[2], true))
        return reject(Status::role_identity);
    }
    output.status = observation.finalized_selection_ready && observation.named_roles_ready
        ? Status::captured : Status::unqualified_roles;
    output.sampled = true;
    capture.Roots(selected_scope.actual_cb);
    output.structural_capture_complete = capture.Complete();
    const bool clock_after_matches = capture.Clock(observation.frame, true);
    if (!clock_after_matches ||
        output.private_identity.game_state != output.private_identity.clock_after_roots[0] ||
        output.private_identity.jomini_state != output.private_identity.clock_after_roots[1]) {
      const auto failure = clock_after_matches ? Status::clock_changed
                                               : capture.ClockFailure(true);
      capture.Mark(failure);
      output.structural_capture_complete = false;
      // An unproved or changed frame revokes availability, retaining diagnostics.
      output.sampled = false;
      output.status = failure;
      if (reason) *reason = Reason(output.status);
      return false;
    }
    // Unknown helper/trigger/layout/context/role transforms remain unknown even
    // if every observed sequence and definition reference is empty.
    output.participant_coverage_complete = false;
    output.war_permission = false;
    if (reason) *reason = Reason(output.status);
    return true;
  } catch (...) {
    output.sampled = false;
    return reject(Status::allocation_failure);
  }
}
} // namespace xar::ck3_12004
