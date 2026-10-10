#include "army_monthfirst_cleanup_stage_12004.hpp"

#include <algorithm>
#include <cstdlib>
#include <iostream>
#include <stdexcept>
#include <string_view>
#include <unordered_map>

namespace {
using namespace xar::game;
constexpr std::uintptr_t kBase = 0x140000000ULL;
constexpr std::uintptr_t kPrimary = 0x100000U, kBuffer = 0x200000U;
constexpr std::uintptr_t kRegi = 0x500000U;
constexpr std::uintptr_t kCallback = kBase + 0x8863D0U;
constexpr std::uint32_t kA = 0xAA000001U, kB = 0xBB000002U, kC = 0xCC000003U;
constexpr std::uint64_t kSentinel = 0xFFFFFFFF029C77F8ULL;
constexpr std::string_view kSha =
    "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";

void Require(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}

ArmyMonthfirstCleanupInputs12004 Entry() {
  ArmyMonthfirstCleanupInputs12004 in{};
  in.frame = ArmyMonthfirstCleanupFrame12004::conditional_cleanup_entry;
  in.exact_build_enabled = in.queue_capture_bounded = true;
  in.primary_address = kPrimary;
  in.known_mode0_callback = kCallback;
  in.saved_mask2 = std::uint8_t{2};
  in.passed_date_raw64 = std::uint64_t{100};
  in.queue.buffer_address = kBuffer;
  in.queue.count = std::int32_t{0};
  return in;
}

void Record(ArmyMonthfirstCleanupInputs12004 &in, std::uint32_t owner,
            std::int32_t ordinal, std::optional<std::uintptr_t> target = kCallback) {
  const auto index = in.queue.records.size();
  ArmyMonthfirstCleanupRecord12004 record{};
  record.record_address = kBuffer + index * 16;
  record.vtable_address = 0x700000U + index * 8;
  record.actual_slot0_target = target;
  record.requested_full_id = owner;
  record.ordinal = ordinal;
  in.queue.records.push_back(record);
  in.queue.count = static_cast<std::int32_t>(in.queue.records.size());
}

void Regi(ArmyMonthfirstCleanupInputs12004 &in, std::uint32_t owner,
          std::uintptr_t object, bool fallback = false) {
  ArmyMonthfirstCleanupRegi12004 regi{};
  regi.requested_full_id = owner;
  regi.selection_ready = true;
  regi.used_native_fallback = fallback;
  regi.selected_address = object;
  regi.indexed_full_id = fallback ? std::uint32_t{0xDD000099U} : owner;
  regi.selected_full_id = fallback ? std::uint32_t{0xEE000077U} : owner;
  regi.magic_14 = std::uint32_t{0x52656769U};
  in.regi.push_back(regi);
}

void Chunk(ArmyMonthfirstCleanupInputs12004 &in, std::uint32_t owner,
           std::int32_t ordinal, std::uintptr_t object, std::uint64_t date) {
  ArmyMonthfirstCleanupChunk12004 chunk{};
  chunk.requested_full_id = owner;
  chunk.ordinal = ordinal;
  chunk.computed_address = object + std::uintptr_t{0x18} +
      static_cast<std::uintptr_t>(static_cast<std::int64_t>(ordinal) * 36);
  chunk.date_1c_raw64 = date;
  in.chunks.push_back(chunk);
}

void ReverseSwapFullDate() {
  auto in = Entry();
  Record(in, kA, 0); Record(in, kB, 0); Record(in, kA, 0); Record(in, kC, 0);
  Regi(in, kA, kRegi); Regi(in, kB, kRegi + 0x1000); Regi(in, kC, kRegi + 0x2000);
  Chunk(in, kA, 0, kRegi, 0x123456780000000AULL);
  Chunk(in, kB, 0, kRegi + 0x1000, std::uint64_t{120});
  Chunk(in, kC, 0, kRegi + 0x2000, std::uint64_t{120});
  const auto out = EvaluateArmyMonthfirstCleanupStage12004(in);
  Require(out.ready && out.returned_count == std::int32_t{2}, "due duplicate pair removal");
  Require(out.visited_outer_physical_indices == std::vector<std::int32_t>{3,2,1,0},
          "fixed initial physical cursor survives queue shrink");
  Require(out.backing_records_after_prefix.size() == std::size_t{4}, "backing slots retained");
  Require(out.backing_records_after_prefix[0].requested_full_id == kC &&
          out.backing_records_after_prefix[1].requested_full_id == kB, "native swap-last order");
  Require(out.backing_records_after_prefix[0].vtable_address == in.queue.records[0].vtable_address,
          "vtable not swapped with pair");
  Require(out.completed_mode0_callback_physical_indices == std::vector<std::int32_t>{2,3},
          "callbacks use removed physical slots");
  Require(out.date_writes_before_block.size() == std::size_t{1} &&
          out.date_writes_before_block[0].after_raw64 == kSentinel,
          "entire sentinel QWORD including high DWORD");
  Require(out.other_fields_unchanged && !out.actual_poststage_observed && !out.whole_daily_monthly,
          "conditional stage scope");
}

void UnknownPhysicalCallbackKeepsPrefix() {
  auto in = Entry();
  Record(in, kA, 0); Record(in, kB, 0, std::uintptr_t{0xDEADBEEFU});
  Regi(in, kA, kRegi); Regi(in, kB, kRegi + 0x1000);
  Chunk(in, kA, 0, kRegi, std::uint64_t{10});
  Chunk(in, kB, 0, kRegi + 0x1000, std::uint64_t{120});
  const auto out = EvaluateArmyMonthfirstCleanupStage12004(in);
  Require(!out.ready && !out.returned && !out.returned_count && !out.other_fields_unchanged,
          "other slot0 never becomes known no-op");
  Require(out.blocked_callback_physical_index == std::int32_t{1},
          "physical B slot callback reached after swapping B pair into A slot");
  Require(out.count_after_known_prefix == std::int32_t{2} &&
          out.date_writes_before_block.size() == std::size_t{1},
          "date precedes unresolved callback, count store follows it");
  Require(out.backing_records_after_prefix[0].requested_full_id == kB &&
          out.backing_records_after_prefix[0].vtable_address == in.queue.records[0].vtable_address,
          "exact pair swap prefix retained");
}

void SignedLowDateAndUnreachedCallback() {
  auto in = Entry();
  Record(in, kA, 0, std::nullopt);
  Regi(in, kA, kRegi);
  Chunk(in, kA, 0, kRegi, 0x11111111FFFFFFFFULL);
  in.passed_date_raw64 = 0x77777777FFFFFFFEULL;
  const auto out = EvaluateArmyMonthfirstCleanupStage12004(in);
  Require(out.ready && out.returned_count == std::int32_t{1} &&
          out.date_writes_before_block.empty() && out.completed_mode0_callback_physical_indices.empty(),
          "signed -2 < -1; high DWORD and unreached callback do not gate");
}

void FallbackAliasChangesLaterDuePredicate() {
  auto in = Entry();
  Record(in, kA, 0); Record(in, kB, 0);
  Regi(in, kA, kRegi, true); Regi(in, kB, kRegi, true);
  Chunk(in, kA, 0, kRegi, std::uint64_t{10});
  Chunk(in, kB, 0, kRegi, std::uint64_t{10});
  const auto out = EvaluateArmyMonthfirstCleanupStage12004(in);
  Require(out.ready && out.returned_count == std::int32_t{1} &&
          out.backing_records_after_prefix[0].requested_full_id == kA,
          "native fallback accepts different selected FullID, physical date alias changes A predicate");
  Require(out.date_writes_before_block.size() == std::size_t{1}, "shared physical date folded once");
}

void InvalidRemovalAndEmptySkippedMissing() {
  auto invalid = Entry();
  Record(invalid, kA, -1);
  Regi(invalid, kA, kRegi, true);
  invalid.regi[0].magic_14 = std::uint32_t{0};
  invalid.regi[0].selected_full_id.reset();
  invalid.passed_date_raw64.reset();
  auto out = EvaluateArmyMonthfirstCleanupStage12004(invalid);
  Require(out.ready && out.returned_count == std::int32_t{0} && out.date_writes_before_block.empty(),
          "invalid magic removes raw pair without date/fullID read");
  auto empty = Entry();
  empty.queue.buffer_address = std::uintptr_t{0};
  empty.passed_date_raw64.reset();
  out = EvaluateArmyMonthfirstCleanupStage12004(empty);
  Require(out.ready && out.returned_count == std::int32_t{0}, "true empty no date read");
  auto skipped = Entry();
  skipped.saved_mask2 = std::uint8_t{0};
  skipped.queue = {};
  skipped.queue_capture_bounded = false;
  skipped.passed_date_raw64.reset();
  out = EvaluateArmyMonthfirstCleanupStage12004(skipped);
  Require(out.ready && out.caller_skipped && !out.queue_postimage_ready && !out.returned_count,
          "skipped unread queue is not fabricated empty");
  auto missing = Entry();
  Record(missing, kA, 0); Regi(missing, kA, kRegi);
  Chunk(missing, kA, 0, kRegi, std::uint64_t{10});
  missing.passed_date_raw64.reset();
  out = EvaluateArmyMonthfirstCleanupStage12004(missing);
  Require(!out.ready && out.date_writes_before_block.empty(), "missing passed date not zero");
  missing.frame = ArmyMonthfirstCleanupFrame12004::captured_current_context;
  out = EvaluateArmyMonthfirstCleanupStage12004(missing);
  Require(!out.ready && out.unavailable_reason == "cleanup_current_context_is_not_entry_frame",
          "current capture not relabeled cleanup entry");
}

struct Memory {
  std::unordered_map<std::uintptr_t, std::uint8_t> bytes;
  std::vector<std::uintptr_t> reads;
  template<class T> void Put(std::uintptr_t address, const T &value) {
    const auto *source = reinterpret_cast<const std::uint8_t *>(&value);
    for (std::size_t i = 0; i < sizeof(T); ++i) bytes[address+i] = source[i];
  }
  static bool Read(void *context, std::uintptr_t address, void *destination, std::size_t count) {
    auto &memory = *static_cast<Memory *>(context);
    memory.reads.push_back(address);
    auto *out = static_cast<std::uint8_t *>(destination);
    for (std::size_t i = 0; i < count; ++i) {
      const auto found = memory.bytes.find(address+i);
      if (found == memory.bytes.end()) return false;
      out[i] = found->second;
    }
    return true;
  }
};

void BoundedCaptureGenerationFallbackSeedAndSignedOrdinal() {
  using namespace xar::ck3_12004;
  const auto binding = BindArmyMonthfirstCleanupStage12004(kBase, kSha);
  Memory memory{};
  constexpr std::uintptr_t registry = 0x400000U, table = 0x410000U;
  constexpr std::uintptr_t indexed = 0x500000U, fallback = 0x600000U, vtable = 0x700000U;
  memory.Put(kPrimary + 0x468, kBuffer);
  memory.Put(kPrimary + 0x474, std::int32_t{1});
  memory.Put(kBuffer, vtable);
  memory.Put(vtable, kCallback);
  memory.Put(kBuffer + 8, kA);
  memory.Put(kBuffer + 0xC, std::int32_t{-2});
  memory.Put(binding.regi_registry_slot, registry);
  memory.Put(binding.regi_fallback_slot, fallback);
  memory.Put(registry + 0x2C, std::uint32_t{2});
  memory.Put(registry + 0x20, table);
  memory.Put(table + 16 + 8, indexed);
  memory.Put(indexed + 0x10, std::uint32_t{0xDD000001U});
  memory.Put(fallback + 0x10, std::uint32_t{0xEE000005U});
  memory.Put(fallback + 0x14, std::uint32_t{0x52656769U});
  constexpr auto signed_chunk = fallback + std::uintptr_t{0x18} - std::uintptr_t{72};
  memory.Put(signed_chunk + 0x1C, std::uint64_t{120});
  const auto original_bytes = memory.bytes;
  ArmyMonthfirstCleanupEntry12004 entry{};
  entry.frame = ArmyMonthfirstCleanupFrame12004::conditional_cleanup_entry;
  entry.primary_address = kPrimary;
  entry.saved_mask2 = std::uint8_t{2};
  entry.passed_date_raw64 = std::uint64_t{100};
  const ArmyMonthfirstCleanupReadView12004 read_view{&memory, &Memory::Read};
  auto raw = ReadArmyMonthfirstCleanupStage12004(binding, read_view, entry);
  Require(raw.regi.size() == std::size_t{1} && raw.regi[0].used_native_fallback &&
          raw.regi[0].indexed_full_id == std::uint32_t{0xDD000001U}, "generation mismatch selects native fallback");
  Require(raw.chunks.size() == std::size_t{1} && raw.chunks[0].computed_address == signed_chunk,
          "signed ordinal preserved, no seven-slot clamp");
  Require(EvaluateArmyMonthfirstCleanupStage12004(raw).ready, "not-due signed ordinal capture available");
  memory.reads.clear();
  auto reused = ReadArmyMonthfirstCleanupStage12004(binding, read_view, entry, &raw.queue);
  Require(reused.reused_same_frame_queue_seed &&
          std::find(memory.reads.begin(), memory.reads.end(), kPrimary + 0x468) == memory.reads.end() &&
          std::find(memory.reads.begin(), memory.reads.end(), kBuffer) == memory.reads.end(),
          "same-frame existing pending seed avoids duplicate queue capture");
  memory.Put(kPrimary + 0x474, std::int32_t{257});
  memory.reads.clear();
  auto bounded = ReadArmyMonthfirstCleanupStage12004(binding, read_view, entry);
  Require(!bounded.queue_capture_bounded && bounded.queue.records.empty() &&
          memory.reads.size() == std::size_t{2}, "overbound queue stops before record/registry reads");
  memory.Put(kPrimary + 0x474, std::int32_t{1});
  Require(memory.bytes == original_bytes, "readonly capture and evaluation preserve native bytes");
  auto wrong = BindArmyMonthfirstCleanupStage12004(kBase, "wrong-build");
  memory.reads.clear();
  raw = ReadArmyMonthfirstCleanupStage12004(wrong, read_view, entry);
  Require(!raw.exact_build_enabled && memory.reads.empty(), "exact build gate before capture");
}
} // namespace

int main(int argc, char **argv) {
  if (argc != 2 || std::string_view{argv[1]} != "monthfirst-cleanup-actual4-stage") return 2;
  try {
    ReverseSwapFullDate();
    UnknownPhysicalCallbackKeepsPrefix();
    SignedLowDateAndUnreachedCallback();
    FallbackAliasChangesLaterDuePredicate();
    InvalidRemovalAndEmptySkippedMissing();
    BoundedCaptureGenerationFallbackSeedAndSignedOrdinal();
    std::cout << "GREEN monthfirst-cleanup-actual4-stage 6 source-specific cases\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "RED " << error.what() << '\n';
    return 1;
  }
}
