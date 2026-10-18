#pragma once
// Exact .4 read-only diagnostic publication. No game memory or getter access.
#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <limits>

namespace xar::ck3_12004::refill_carrier {
inline constexpr char kExportName[] = "XarRefillCoreCarrier12004";
inline constexpr std::uint64_t kMagic = 0x3152303643524158ULL;
inline constexpr std::uint64_t kAbi = 1, kSourceEpoch = 20261018;
inline constexpr std::size_t kSlots = 16, kHeaderWords = 8;
enum Word : std::size_t {
  sequence, owner_tid, active, invocation_token, parent_invocation_token,
  nesting_depth, core_clock_identity, core_entry_sequence, core_thread_id,
  natural_clock_identity, natural_entry_sequence, natural_thread_id,
  date_raw, manager_identity, secondary_manager_identity, game_state_identity,
  caller_return_rva, natural_entry_rva, entry_provenance_complete,
  saved_mask02_admitted, invocation_kind, kWords
};
inline constexpr std::array<const char *, kWords> kWordNames{
  "sequence", "owner_tid", "active", "invocation_token", "parent_invocation_token",
  "nesting_depth", "core_clock_identity", "core_entry_sequence", "core_thread_id",
  "natural_clock_identity", "natural_entry_sequence", "natural_thread_id",
  "date_raw", "manager_identity", "secondary_manager_identity", "game_state_identity",
  "caller_return_rva", "natural_entry_rva", "entry_provenance_complete",
  "saved_mask02_admitted", "invocation_kind"};
using Words = std::array<std::uint64_t, kWords>;
using Header = std::array<std::uint64_t, kHeaderWords>;
inline constexpr Header kHeader{kMagic, kAbi, kSourceEpoch, kSlots, kWords,
  kHeaderWords, 0x98702F88A547CDE2ULL, 0};
struct alignas(8) Slot {
  std::array<std::atomic<std::uint64_t>, kWords> words{};
};
struct alignas(8) Directory {
  Header header = kHeader;
  std::array<Slot, kSlots> slots{};
};
static_assert(std::atomic<std::uint64_t>::is_always_lock_free);
static_assert(sizeof(std::atomic<std::uint64_t>) == 8);
static_assert(sizeof(Slot) == kWords * 8);
static_assert(offsetof(Directory, slots) == kHeaderWords * 8);
static_assert(sizeof(Directory) == (kHeaderWords + kSlots * kWords) * 8);

inline Words LoadLocal(const Slot &slot) noexcept {
  Words out{};
  for (std::size_t i = 0; i != kWords; ++i)
    out[i] = slot.words[i].load(std::memory_order_seq_cst);
  return out;
}
inline bool ValidActiveFrame(const Words &w, std::uint64_t tid) noexcept {
  return w[sequence] != 0 && (w[sequence] & 1) == 0 && tid != 0 &&
    w[owner_tid] == tid && w[active] == 1 && w[invocation_token] != 0 &&
    w[nesting_depth] != 0 && w[core_clock_identity] != 0 &&
    w[core_clock_identity] == w[natural_clock_identity] &&
    w[core_thread_id] == tid && w[natural_thread_id] == tid &&
    w[natural_entry_sequence] != 0 &&
    w[core_entry_sequence] > w[natural_entry_sequence] &&
    w[date_raw] != 0 && w[manager_identity] != 0 &&
    w[manager_identity] <= UINT64_MAX - 8 &&
    w[secondary_manager_identity] == w[manager_identity] + 8 &&
    w[game_state_identity] != 0 && w[caller_return_rva] == 0x2A9A8E2 &&
    w[natural_entry_rva] == 0x2A9A570 && w[entry_provenance_complete] == 1 &&
    w[saved_mask02_admitted] == 1 && w[invocation_kind] == 3;
}
inline bool StableActivePair(const Words &a, const Words &b,
                             std::uint64_t tid) noexcept {
  return a == b && ValidActiveFrame(a, tid);
}

// Each slot has exactly one owner TID for this process lifetime. Concurrent
// owners use distinct slots; a full directory is unavailable, never a fallback.
// Recursive calls on the same actual thread save/restore the enclosing payload.
// Even an invalid nested entry publishes inactive while its original executes,
// so a nested writer cannot borrow the enclosing invocation's identity.
class Publication final {
 public:
  Publication(Directory &directory, std::uint32_t tid, Words payload) noexcept {
    if (tid == 0) return;
    for (auto &candidate : directory.slots) {
      auto owner = candidate.words[owner_tid].load(std::memory_order_acquire);
      if (owner == 0) {
        auto empty = std::uint64_t{0};
        if (candidate.words[owner_tid].compare_exchange_strong(
              empty, tid, std::memory_order_seq_cst)) owner = tid;
        else owner = empty;
      }
      if (owner == tid) { slot_ = &candidate; break; }
    }
    if (slot_ == nullptr) return;
    previous_ = LoadLocal(*slot_);
    payload[owner_tid] = tid;
    published_ = Write(payload) && ValidActiveFrame(LoadLocal(*slot_), tid);
  }
  Publication(const Publication &) = delete;
  Publication &operator=(const Publication &) = delete;
  ~Publication() noexcept {
    if (slot_ != nullptr) (void)Write(previous_);
  }
  bool published() const noexcept { return published_; }
 private:
  bool Write(const Words &payload) noexcept {
    const auto value = slot_->words[sequence].load(std::memory_order_seq_cst);
    if ((value & 1) != 0 || value > UINT64_MAX - 4) {
      // Fail closed even at theoretical sequence exhaustion. Never wrap or
      // restore an active parent after the fence has exhausted its identity.
      slot_->words[active].store(0, std::memory_order_seq_cst);
      return false;
    }
    slot_->words[sequence].store(value + 1, std::memory_order_seq_cst);
    for (std::size_t i = 2; i != kWords; ++i)
      slot_->words[i].store(payload[i], std::memory_order_seq_cst);
    slot_->words[sequence].store(value + 2, std::memory_order_seq_cst);
    return true;
  }
  Slot *slot_ = nullptr;
  Words previous_{};
  bool published_ = false;
};
} // namespace xar::ck3_12004::refill_carrier
