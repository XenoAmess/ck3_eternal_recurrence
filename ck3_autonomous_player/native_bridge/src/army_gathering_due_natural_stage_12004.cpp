#include "xar_bridge/army_gathering_due_natural_stage_12004.hpp"
#include <limits>
#include <mutex>
#include <cstring>
#include <algorithm>
#include <utility>
#if defined(_WIN32)
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <intrin.h>
#endif

namespace xar::ck3_12004 {
namespace {
constexpr std::string_view kSha = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
std::mutex journal_mutex;
std::vector<ArmyGatheringDueNaturalStage12004> journal;
constexpr std::size_t kJournalLimit = 64;

struct Capture {
  const ArmyGatheringDueNaturalBindings12004 &b;
  ArmyGatheringDueSnapshot12004 &out;
  std::size_t read_operations = 0;
  void Missing(const char *field) {
    if (std::find(out.missing_fields.begin(), out.missing_fields.end(), field) == out.missing_fields.end())
      out.missing_fields.emplace_back(field);
  }
  template<class T> std::optional<T> Read(std::uintptr_t address, std::size_t offset, const char *field) {
    T value{};
    if (read_operations >= b.maximum_read_operations) { Missing("snapshot.read_operation_bound"); Missing(field); return std::nullopt; }
    ++read_operations;
    if (!address || offset > std::numeric_limits<std::uintptr_t>::max() - address || !b.read ||
        !b.read(b.read_context, address + offset, &value, sizeof(value))) {
      Missing(field); return std::nullopt;
    }
    return value;
  }
  ArmyGatheringDueNativeList12004 List(std::uintptr_t owner, std::size_t offset) {
    ArmyGatheringDueNativeList12004 row;
    row.buffer_identity = Read<std::uintptr_t>(owner, offset, "list.buffer");
    row.capacity = Read<std::int32_t>(owner, offset + 8, "list.capacity");
    row.count = Read<std::int32_t>(owner, offset + 12, "list.count");
    if (!row.count) return row;
    if (*row.count <= 0) { row.complete = true; return row; }
    if (!row.buffer_identity || !*row.buffer_identity) { Missing("list.nonempty_buffer"); return row; }
    const auto n = static_cast<std::size_t>(*row.count);
    const auto limit = n < b.maximum_occurrences ? n : b.maximum_occurrences;
    bool complete = limit == n;
    if (!complete) Missing("list.capture_bound");
    for (std::size_t i = 0; i < limit; ++i) {
      auto id = Read<std::uint32_t>(*row.buffer_identity, i * 4, "list.full_id");
      if (!id) { complete = false; break; }
      row.ordered_full_ids.push_back(*id);
    }
    row.complete = complete;
    return row;
  }
  ArmyGatheringDuePhysical12004 Resolve(std::uint32_t raw, std::uintptr_t registry_rva,
      std::uintptr_t fallback_rva, std::size_t id_offset, std::size_t magic_offset) {
    ArmyGatheringDuePhysical12004 row; row.requested_full_id = raw;
    auto store = Read<std::uintptr_t>(b.image_base, registry_rva, "registry.slot");
    if (!store) return row;
    std::uintptr_t selected = 0;
    if (*store) {
      auto count = Read<std::uint32_t>(*store, 0x2C, "registry.slot_limit");
      if (!count) return row;
      auto index = raw & 0xFFFFFF;
      if (index < *count) {
        auto slots = Read<std::uintptr_t>(*store, 0x20, "registry.table");
        if (!slots) return row;
        if (!*slots) { Missing("registry.nonempty_table"); return row; }
        auto candidate = Read<std::uintptr_t>(*slots, static_cast<std::size_t>(index) * 16 + 8, "registry.payload");
        if (!candidate) return row;
        if (*candidate) {
          auto id = Read<std::uint32_t>(*candidate, id_offset, "registry.candidate_generation");
          if (!id) return row;
          if (*id == raw) selected = *candidate;
        }
      }
    }
    if (!selected) {
      auto fallback = Read<std::uintptr_t>(b.image_base, fallback_rva, "registry.fallback");
      if (!fallback) return row;
      if (!*fallback) { Missing("registry.nonnull_fallback"); return row; }
      selected = *fallback; row.used_native_fallback = true;
    }
    row.physical_identity = selected;
    row.selected_full_id = Read<std::uint32_t>(selected, id_offset, "receiver.full_id");
    row.magic = Read<std::uint32_t>(selected, magic_offset, "receiver.magic");
    row.resolution_complete = row.selected_full_id.has_value();
    return row;
  }
  ArmyGatheringDuePhysical12004 Regi(std::uint32_t raw) { return Resolve(raw, 0x5D1EB68, 0x5D1EB58, 0x10, 0x14); }
  ArmyGatheringDueChunk12004 Chunk(std::uintptr_t receiver, std::int32_t ordinal) {
    ArmyGatheringDueChunk12004 row; row.ordinal = ordinal;
    const auto delta = std::int64_t{0x18} + std::int64_t{36} * ordinal;
    if ((delta >= 0 && static_cast<std::uint64_t>(delta) > std::numeric_limits<std::uintptr_t>::max() - receiver) ||
        (delta < 0 && static_cast<std::uint64_t>(-delta) > receiver)) {
      Missing("chunk.computed_address_overflow"); return row;
    }
    row.physical_identity = delta >= 0 ? receiver + static_cast<std::uintptr_t>(delta) : receiver - static_cast<std::uintptr_t>(-delta);
    auto p = row.physical_identity;
    row.maximum = Read<std::int32_t>(p, 0, "chunk.maximum00");
    row.current = Read<std::int32_t>(p, 4, "chunk.current04");
    row.owner_full_id = Read<std::uint32_t>(p, 8, "chunk.owner08");
    row.stored_ordinal = Read<std::int32_t>(p, 0xC, "chunk.ordinal0c");
    row.association_full_id = Read<std::uint32_t>(p, 0x10, "chunk.association10");
    row.byte14 = Read<std::uint8_t>(p, 0x14, "chunk.byte14");
    row.state = Read<std::int32_t>(p, 0x18, "chunk.state18");
    row.date_raw64 = Read<std::uint64_t>(p, 0x1C, "chunk.date1c");
    return row;
  }
  ArmyGatheringDueReference12004 Ref(std::uintptr_t ptr) {
    ArmyGatheringDueReference12004 row; row.source_ref_identity = ptr;
    row.owner_full_id = Read<std::uint32_t>(ptr, 8, "source_ref.owner08");
    row.ordinal = Read<std::int32_t>(ptr, 0xC, "source_ref.ordinal0c");
    if (row.owner_full_id) row.receiver = Regi(*row.owner_full_id);
    if (row.ordinal && row.receiver.resolution_complete && row.receiver.magic == 0x52656769U &&
        row.receiver.selected_full_id && *row.receiver.selected_full_id != 0xFFFFFFFF)
      row.chunk = Chunk(row.receiver.physical_identity, *row.ordinal);
    return row;
  }
  void Refs(std::uintptr_t owner, std::size_t pointer_offset, std::size_t count_offset,
      std::optional<std::uintptr_t> &pointer, std::optional<std::int32_t> &count,
      std::vector<ArmyGatheringDueReference12004> &rows, bool &complete) {
    pointer = Read<std::uintptr_t>(owner, pointer_offset, "refs.buffer");
    count = Read<std::int32_t>(owner, count_offset, "refs.count");
    if (!count) return;
    if (*count <= 0) { complete = true; return; }
    if (!pointer || !*pointer) { Missing("refs.nonempty_buffer"); return; }
    const auto n = static_cast<std::size_t>(*count);
    const auto bound = n < b.maximum_records ? n : b.maximum_records;
    complete = bound == n;
    if (!complete) Missing("refs.capture_bound");
    for (std::size_t i = 0; i < bound; ++i) {
      if (i * 16 > (std::numeric_limits<std::uintptr_t>::max)() - *pointer) {
        Missing("refs.physical_address_overflow"); complete = false; break;
      }
      auto row = Ref(*pointer + i * 16);
      if (!row.owner_full_id || !row.ordinal) { complete = false; rows.push_back(std::move(row)); break; }
      rows.push_back(std::move(row));
    }
  }
  ArmyGatheringDueArRg12004 ArRg(std::uint32_t raw) {
    ArmyGatheringDueArRg12004 row;
    row.receiver = Resolve(raw, 0x5D1F340, 0x5D1F338, 0x10, 0x14);
    auto p = row.receiver.physical_identity;
    if (!p) return row;
    row.current38 = Read<std::int32_t>(p, 0x38, "arrg.current38");
    row.maximum3c = Read<std::int32_t>(p, 0x3C, "arrg.maximum3c");
    row.army140 = Read<std::uint32_t>(p, 0x140, "arrg.army140");
    row.owner144 = Read<std::uint32_t>(p, 0x144, "arrg.owner144");
    row.character148 = Read<std::uint32_t>(p, 0x148, "arrg.character148");
    row.state14c = Read<std::int32_t>(p, 0x14C, "arrg.state14c");
    Refs(p, 0x20, 0x2C, row.source_refs_identity, row.source_ref_count, row.source_refs, row.source_refs_complete);
    return row;
  }
  ArmyGatheringDueArmy12004 Army(std::uint32_t raw) {
    ArmyGatheringDueArmy12004 row;
    row.receiver = Resolve(raw, 0x5D1DE48, 0x5D1DE50, 0x10, 0x14);
    auto p = row.receiver.physical_identity;
    if (!p) return row;
    row.unit124 = Read<std::uint32_t>(p, 0x124, "army.unit124");
    row.combat128 = Read<std::uint32_t>(p, 0x128, "army.combat128");
    if (row.combat128) {
      row.combat_receiver = Resolve(*row.combat128, 0x5D1DE70, 0x5D1DE18, 8, 0xC);
      if (row.combat_receiver.magic && row.combat_receiver.selected_full_id)
        row.source_combat_skip = *row.combat_receiver.magic == 0x436F6D62 && *row.combat_receiver.selected_full_id != 0xFFFFFFFF;
    }
    row.finished_date190 = Read<std::uint64_t>(p, 0x190, "army.finished_date190");
    row.statistics130 = Read<std::array<std::uint8_t, 80>>(p, 0x130, "army.statistics130");
    row.arrg_roster = List(p, 0x38);
    for (auto id : row.arrg_roster.ordered_full_ids) row.arrg.push_back(ArRg(id));
    row.gathering_buffer_identity = Read<std::uintptr_t>(p, 0x50, "gathering.buffer50");
    row.gathering_count = Read<std::int32_t>(p, 0x5C, "gathering.count5c");
    if (!row.gathering_count) return row;
    if (*row.gathering_count <= 0) { row.gathering_records_complete = true; return row; }
    if (!row.gathering_buffer_identity || !*row.gathering_buffer_identity) { Missing("gathering.nonempty_buffer"); return row; }
    const auto n = static_cast<std::size_t>(*row.gathering_count);
    const auto bound = n < b.maximum_records ? n : b.maximum_records;
    row.gathering_records_complete = n == bound;
    if (n != bound) Missing("gathering.capture_bound");
    for (std::size_t i = 0; i < bound; ++i) {
      auto record = Read<std::uintptr_t>(*row.gathering_buffer_identity, i * 8, "gathering.record_pointer");
      if (!record || !*record) { row.gathering_records_complete = false; continue; }
      ArmyGatheringDueRecord12004 item; item.physical_identity = *record;
      item.date_low32 = Read<std::int32_t>(*record, 0, "gathering.date_low32");
      std::optional<std::uintptr_t> refs;
      Refs(*record, 8, 0x14, refs, item.pending_count, item.pending_refs, item.pending_refs_complete);
      auto chars = Read<std::uintptr_t>(*record, 0x20, "gathering.character_buffer20");
      item.character_count = Read<std::int32_t>(*record, 0x2C, "gathering.character_count2c");
      if (item.character_count && *item.character_count <= 0) item.character_ids_complete = true;
      else if (item.character_count && chars && *chars) {
        auto cn = static_cast<std::size_t>(*item.character_count);
        auto cb = cn < b.maximum_records ? cn : b.maximum_records;
        item.character_ids_complete = cn == cb;
        if (cn != cb) Missing("gathering.characters_bound");
        for (std::size_t j = 0; j < cb; ++j) {
          auto id = Read<std::uint32_t>(*chars, j * 4, "gathering.character_full_id");
          if (!id) { item.character_ids_complete = false; break; }
          item.character_full_ids.push_back(*id);
        }
      } else if (item.character_count) Missing("gathering.characters_nonempty_buffer");
      row.gathering_records.push_back(std::move(item));
    }
    return row;
  }
  void Snapshot(std::uintptr_t primary, std::uintptr_t date, const ArmyNaturalPhaseScope12004 &parent) {
    out.primary_identity = primary; out.date_pointer_identity = date;
    out.event = NextArmyNaturalPhaseEvent12004();
    out.passed_date_raw64 = Read<std::uint64_t>(date, 0, "passed_date.raw64");
    out.game_state_date_raw64 = Read<std::uint64_t>(parent.game_state_identity, 8, "game_state.date_raw64");
    out.absolute_day_raw = Read<std::uint32_t>(parent.game_state_identity, 0x9C, "game_state.absolute_day_raw");
    out.current_c0_raw = Read<std::uint8_t>(parent.game_state_identity, 0xC0, "game_state.current_c0_raw");
    out.queue158 = List(primary, 0x158);
    out.persistent_roster30 = List(primary, 0x30);
    out.army_roster50 = List(primary, 0x50);
    for (auto id : out.queue158.ordered_full_ids) out.queued_armies.push_back(Army(id));
    for (auto id : out.army_roster50.ordered_full_ids) out.roster_armies.push_back(Army(id));
    for (auto id : out.persistent_roster30.ordered_full_ids) {
      ArmyGatheringDuePersistent12004 row; row.receiver = Regi(id);
      if (auto p = row.receiver.physical_identity) {
        row.prepared148 = Read<std::int64_t>(p, 0x148, "regi.prepared148");
        for (std::int32_t i = 0; i < 7; ++i) row.chunks.push_back(Chunk(p, i));
      }
      out.persistent.push_back(std::move(row));
    }
    out.all_declared_reads_complete = out.missing_fields.empty();
  }
};

std::optional<bool> Ordered(const ArmyGatheringDueNaturalStage12004 &s) {
  const auto &p = s.parent.entry_event; const auto &e = s.entry.event; const auto &r = s.returned.event;
  if (!p.clock_identity || !e.clock_identity || !r.clock_identity || !p.thread_id || !e.thread_id || !r.thread_id)
    return std::nullopt;
  return p.clock_identity == e.clock_identity && e.clock_identity == r.clock_identity &&
      p.thread_id == e.thread_id && e.thread_id == r.thread_id && p.sequence < e.sequence && e.sequence < r.sequence;
}
} // namespace

ArmyGatheringDueNaturalBindings12004 BindArmyGatheringDueNaturalStage12004(
    std::uintptr_t base, std::string_view sha, void *context, ArmyNaturalPhaseRead12004 reader) noexcept {
  ArmyGatheringDueNaturalBindings12004 b;
  b.exact_build_enabled = base != 0 && sha == kSha; b.image_base = base;
  b.read_context = context; b.read = reader; return b;
}
ArmyGatheringDueNaturalStage12004 InvokeArmyGatheringDueNatural12004(
    const ArmyGatheringDueNaturalBindings12004 &b, ArmyGatheringDueNaturalOriginal12004 original,
    void *primary_arg, const void *date_arg, std::uintptr_t pc, std::optional<std::uint8_t> mask) noexcept {
  ArmyGatheringDueNaturalStage12004 out; out.actual_return_rva = pc; out.actual_saved_mask = mask;
  auto primary = reinterpret_cast<std::uintptr_t>(primary_arg);
  auto date = reinterpret_cast<std::uintptr_t>(date_arg);
  try {
    if (b.exact_build_enabled && pc == kArmyGatheringDueNaturalReturnRva12004 && mask && primary <= std::numeric_limits<std::uintptr_t>::max() - 8)
      out.saved_mask_parent_observation_admitted = ObserveArmyNaturalPhaseSavedMask12004(primary + 8, pc, *mask);
    out.parent = CopyActiveArmyNaturalPhaseScope12004();
    out.actual_boundary_admitted = b.exact_build_enabled && pc == kArmyGatheringDueNaturalReturnRva12004 &&
        out.parent.observed && out.parent.phase == ArmyNaturalPhaseKind12004::post_date &&
        out.parent.actual_entry_rva == kArmyNaturalPostDateRva12004 &&
        primary <= (std::numeric_limits<std::uintptr_t>::max)() - 8 &&
        out.parent.primary_manager_identity == primary && out.parent.secondary_manager_identity == primary + 8 &&
        out.parent.game_state_identity && out.parent.game_state_identity <= (std::numeric_limits<std::uintptr_t>::max)() - 8 &&
        date == out.parent.game_state_identity + 8;
    if (out.actual_boundary_admitted) { Capture c{b, out.entry}; c.Snapshot(primary, date, out.parent); out.observed = true; }
    else out.unavailable_reason = "literal_due_entry_or_full_active_postdate_parent_unavailable";
  } catch (...) { out.unavailable_reason = "entry_capture_failed"; }
  // Capture failure never suppresses the intercepted native call.
  if (!original) { out.unavailable_reason = "original_callback_missing"; return out; }
  out.original_called = true; out.raw_return_bits = original(primary_arg, date_arg); out.original_returned = true;
  try {
    if (out.actual_boundary_admitted) {
      Capture c{b, out.returned}; c.Snapshot(primary, date, out.parent);
      // The source consumes a fixed initial queue extent. Copy that many current
      // backing slots at return even when live164 has become0; report clipping.
      if (out.entry.queue158.count && out.returned.queue158.buffer_identity) {
        auto count = *out.entry.queue158.count;
        if (count <= 0) out.returned.entry_queue_extent_backing_complete = true;
        else if (*out.returned.queue158.buffer_identity) {
          auto n = static_cast<std::size_t>(count), bound = n < b.maximum_occurrences ? n : b.maximum_occurrences;
          out.returned.entry_queue_extent_backing_complete = n == bound;
          if (n != bound) c.Missing("return.entry_queue_extent_capture_bound");
          for (std::size_t i = 0; i < bound; ++i) {
            auto id = c.Read<std::uint32_t>(*out.returned.queue158.buffer_identity, i * 4, "return.entry_queue_extent_full_id");
            if (!id) { out.returned.entry_queue_extent_backing_complete = false; break; }
            out.returned.entry_queue_extent_backing_full_ids.push_back(*id);
          }
        } else c.Missing("return.entry_queue_extent_nonempty_buffer");
      }
      for (const auto &army : out.entry.queued_armies)
        for (const auto &record : army.gathering_records)
          for (const auto &ref : record.pending_refs) {
            ArmyGatheringDueReference12004 row;
            row.source_ref_identity = ref.source_ref_identity;
            row.owner_full_id = ref.owner_full_id; row.ordinal = ref.ordinal;
            if (row.owner_full_id) row.receiver = c.Regi(*row.owner_full_id);
            if (row.ordinal && row.receiver.resolution_complete && row.receiver.magic == 0x52656769U &&
                row.receiver.selected_full_id && *row.receiver.selected_full_id != 0xFFFFFFFF)
              row.chunk = c.Chunk(row.receiver.physical_identity, *row.ordinal);
            out.returned.entry_due_refs_at_return.push_back(std::move(row));
          }
      out.returned.all_declared_reads_complete = out.returned.missing_fields.empty();
      out.actual_poststage_observed = true;
      auto active = CopyActiveArmyNaturalPhaseScope12004();
      out.active_parent_unchanged = active.observed && active.entry_event.clock_identity == out.parent.entry_event.clock_identity &&
          active.entry_event.sequence == out.parent.entry_event.sequence && active.entry_event.thread_id == out.parent.entry_event.thread_id &&
          active.primary_manager_identity == primary && active.secondary_manager_identity == out.parent.secondary_manager_identity;
      out.same_clock_thread_order = Ordered(out);
    }
    std::lock_guard<std::mutex> lock(journal_mutex);
    if (journal.size() == kJournalLimit) journal.erase(journal.begin());
    journal.push_back(out);
  } catch (...) { out.unavailable_reason = "returned_capture_or_journal_failed"; }
  return out;
}
std::vector<ArmyGatheringDueNaturalStage12004> ReadArmyGatheringDueNaturalJournal12004() {
  std::lock_guard<std::mutex> lock(journal_mutex); return journal;
}
std::vector<ArmyGatheringDueNaturalStage12004> ReadArmyGatheringDueNaturalForArmy12004(std::uint32_t full_id) {
  if (full_id == 0xFFFFFFFF) return {};
  auto all = ReadArmyGatheringDueNaturalJournal12004(); std::vector<ArmyGatheringDueNaturalStage12004> out;
  for (auto &s : all) {
    bool matched = false;
    for (const auto *snapshot : {&s.entry, &s.returned})
      for (const auto *rows : {&snapshot->queued_armies, &snapshot->roster_armies})
        for (const auto &row : *rows)
          if (row.receiver.resolution_complete && row.receiver.selected_full_id == full_id) matched = true;
    if (matched) out.push_back(std::move(s));
  }
  return out;
}
void ClearArmyGatheringDueNaturalJournal12004() noexcept {
  try { std::lock_guard<std::mutex> lock(journal_mutex); journal.clear(); } catch (...) {}
}

namespace {
#if defined(_WIN32) && defined(_MSC_VER) && defined(_M_X64)
ArmyGatheringDueNaturalBindings12004 installed_binding;
ArmyGatheringDueNaturalOriginal12004 installed_original = nullptr;
bool GuardedRead(void *, std::uintptr_t address, void *destination, std::size_t size) noexcept {
  SIZE_T copied = 0;
  return address && ReadProcessMemory(GetCurrentProcess(), reinterpret_cast<const void *>(address),
      destination, size, &copied) && copied == size;
}
std::uintptr_t __fastcall DueGate(void *primary, const void *date, std::uint8_t saved_mask) noexcept {
  const auto pc = reinterpret_cast<std::uintptr_t>(_ReturnAddress());
  const auto rva = pc >= installed_binding.image_base ? pc - installed_binding.image_base : 0;
  auto stage = InvokeArmyGatheringDueNatural12004(installed_binding, installed_original,
      primary, date, rva, saved_mask);
  return stage.raw_return_bits;
}
void AbsoluteJump(std::uint8_t *bytes, std::uintptr_t target) noexcept {
  bytes[0] = 0xFF; bytes[1] = 0x25; std::memset(bytes + 2, 0, 4);
  std::memcpy(bytes + 6, &target, 8);
}
#endif
}
ArmyGatheringDueNaturalHook12004 BindArmyGatheringDueNaturalHook12004(std::uintptr_t base, std::string_view sha) noexcept {
  ArmyGatheringDueNaturalHook12004 out;
#if defined(_WIN32) && defined(_MSC_VER) && defined(_M_X64)
  out.bindings = BindArmyGatheringDueNaturalStage12004(base, sha, nullptr, GuardedRead);
#else
  out.bindings = BindArmyGatheringDueNaturalStage12004(base, sha);
#endif
  // Complete source evidence: closed actual main [AF20,B579), including literal
  // caller678/return67D, split bytes/pin in continuation42 SOURCE-CLOSED. The
  // runtime small anchor below verifies the indivisible16B relocatable prologue.
  out.complete_source_proof = out.bindings.exact_build_enabled;
  return out;
}
bool InstallArmyGatheringDueNaturalHook12004(ArmyGatheringDueNaturalHook12004 &hook) noexcept {
#if defined(_WIN32) && defined(_MSC_VER) && defined(_M_X64)
  if (hook.installed) return true;
  if (!hook.complete_source_proof || !hook.bindings.exact_build_enabled || !hook.primary_thread_suspended_proven || installed_original) {
    hook.unavailable_reason = "exact_source_pin_paused_startup_proof_or_single_installer_unavailable"; return false;
  }
  // No RIP-relative instruction/branch in these four complete instructions.
  constexpr std::array<std::uint8_t, 16> source = {0x4C,0x8B,0xDC,0x49,0x89,0x53,0x10,0x41,0x54,0x48,0x81,0xEC,0x80,0,0,0};
  const auto entry = hook.bindings.image_base + kArmyGatheringDueNaturalRva12004;
  std::array<std::uint8_t, 16> observed{};
  if (!GuardedRead(nullptr, entry, observed.data(), observed.size()) || observed != source) {
    hook.unavailable_reason = "literal_entry_anchor_mismatch"; return false;
  }
  auto *code = static_cast<std::uint8_t *>(VirtualAlloc(nullptr, 64, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE));
  if (!code) { hook.unavailable_reason = "trampoline_allocation_failed"; return false; }
  std::memcpy(code, source.data(), 16); AbsoluteJump(code + 16, entry + 16);
  // mov r8b,r13b; absolute jmp Gate. Return PC remains actual caller67D.
  code[32] = 0x45; code[33] = 0x88; code[34] = 0xE8;
  AbsoluteJump(code + 35, reinterpret_cast<std::uintptr_t>(&DueGate));
  DWORD previous = 0;
  if (!VirtualProtect(code, 64, PAGE_EXECUTE_READ, &previous)) {
    VirtualFree(code, 0, MEM_RELEASE); hook.unavailable_reason = "trampoline_protection_failed"; return false;
  }
  FlushInstructionCache(GetCurrentProcess(), code, 64);
  std::array<std::uint8_t, 16> patch{}; patch.fill(0x90);
  AbsoluteJump(patch.data(), reinterpret_cast<std::uintptr_t>(code + 32));
  DWORD old = 0;
  if (!VirtualProtect(reinterpret_cast<void *>(entry), 16, PAGE_EXECUTE_READWRITE, &old)) {
    VirtualFree(code, 0, MEM_RELEASE); hook.unavailable_reason = "entry_protection_failed"; return false;
  }
  // Root installs at its proved paused startup boundary. Publish original before
  // changing entry; copied-prologue tail resumes the original body atAF30.
  installed_binding = hook.bindings;
  installed_original = reinterpret_cast<ArmyGatheringDueNaturalOriginal12004>(code);
  std::memcpy(reinterpret_cast<void *>(entry), patch.data(), patch.size());
  DWORD ignored = 0;
  const bool restored = VirtualProtect(reinterpret_cast<void *>(entry), 16, old, &ignored) != 0;
  FlushInstructionCache(GetCurrentProcess(), reinterpret_cast<const void *>(entry), 16);
  hook.installed = true; hook.entry_trampoline_identity = reinterpret_cast<std::uintptr_t>(code);
  hook.entry_thunk_identity = reinterpret_cast<std::uintptr_t>(code + 32);
  if (!restored) hook.unavailable_reason = "installed_entry_protection_restore_failed";
  return restored;
#else
  hook.unavailable_reason = "msvc_windows_x64_installer_required"; return false;
#endif
}
} // namespace xar::ck3_12004
