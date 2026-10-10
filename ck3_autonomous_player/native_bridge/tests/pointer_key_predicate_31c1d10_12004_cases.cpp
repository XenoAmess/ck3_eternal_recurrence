#include "xar_bridge/pointer_key_predicate_31c1d10_12004.hpp"

#include <cstring>
#include <limits>
#include <map>
#include <stdexcept>

namespace xar::ck3_12004::construction_owner_mode3 {
namespace {
struct CopiedMemory {
  std::map<std::uintptr_t, unsigned char> bytes;
  std::map<std::uintptr_t, std::size_t> reads;
  std::uintptr_t deny_second_read = 0;
  template<class T> void Put(std::uintptr_t address, T value) {
    const auto *raw = reinterpret_cast<const unsigned char *>(&value);
    for (std::size_t i = 0; i < sizeof(T); ++i) bytes[address + i] = raw[i];
  }
  static bool Read(void *context, const void *source, void *out, std::size_t size) {
    auto &memory = *static_cast<CopiedMemory *>(context);
    const auto address = reinterpret_cast<std::uintptr_t>(source);
    const auto count = ++memory.reads[address];
    if (address == memory.deny_second_read && count > 1) return false;
    auto *target = static_cast<unsigned char *>(out);
    for (std::size_t i = 0; i < size; ++i) {
      auto found = memory.bytes.find(address + i);
      if (found == memory.bytes.end()) return false;
      target[i] = found->second;
    }
    return true;
  }
};
constexpr std::uintptr_t kSingleton = 0x10000;
constexpr std::uintptr_t kEntries = 0x40000;
RawReceiverAccessV1 Access(CopiedMemory &memory) {
  return {&memory, &CopiedMemory::Read, 0, true};
}
void Header(CopiedMemory &memory, std::uintptr_t entries = kEntries, std::int32_t mask = 0) {
  memory.Put(kSingleton + 0xF08, entries);
  memory.Put(kSingleton + 0xF14, mask);
}
void Slot(CopiedMemory &memory, std::uintptr_t record, std::uint8_t control, std::uintptr_t key) {
  memory.Put(record + 4, control);
  memory.Put(record + 8, key);
}
void Require(bool value, const char *reason) {
  if (!value) throw std::runtime_error(reason);
}
} // namespace

// Only exported into03's one newly connected compound; no standalone main.
void RunPointerKeyPredicate31C1D10FreshCases12004() {
  {
    CopiedMemory m; Header(m); Slot(m, kEntries, 1, 0);
    auto r = ReadPointerKeyPredicate31C1D10V1(Access(m), kSingleton, 0);
    Require(r.value == true && r.pointer_hash_raw_u32 == 0x9BE17165u,
            "zero raw key/eight-byte FNV hash was replaced by pointer validity");
    Require(r.path == PointerKeyPredicatePathV1::copied_key_match &&
            r.copied_probe_key_count == 1 && !r.end_tail_raw_u8 && m.reads[kSingleton + 0xF18] == 0,
            "matched branch read an unreached tail");
  }
  {
    CopiedMemory m; Header(m); Slot(m, kEntries, 0xFF, 0x8000000000000000ULL);
    auto r = ReadPointerKeyPredicate31C1D10V1(Access(m), kSingleton, 0x8000000000000000ULL);
    Require(r.pointer_hash_raw_u32 == 0x1BE23AE5u && r.value == false &&
            r.path == PointerKeyPredicatePathV1::copied_key_match,
            "high-byte key lost or key match incorrectly became native AL");
  }
  {
    CopiedMemory m; Header(m); Slot(m, kEntries, 1, 7); Slot(m, kEntries + 16, 2, 0);
    auto r = ReadPointerKeyPredicate31C1D10V1(Access(m), kSingleton, 0);
    Require(r.value == true && r.copied_probe_key_count == 2 &&
            r.probe_distance_raw_u8 == 2 && r.selected_record_pointer == kEntries + 16,
            "collision probe did not retain source order");
  }
  {
    CopiedMemory m; Header(m); Slot(m, kEntries, 1, 9);
    m.Put(kEntries + 16 + 4, std::uint8_t{1});
    m.Put(kSingleton + 0xF18, std::uint8_t{1});
    m.Put(kEntries + 32 + 4, std::uint8_t{0xFF});
    auto r = ReadPointerKeyPredicate31C1D10V1(Access(m), kSingleton, 0);
    Require(r.value == false && r.path == PointerKeyPredicatePathV1::copied_end_record &&
            r.end_slot_index_i32 == 2 && r.copied_probe_key_count == 1 && m.reads[kEntries + 24] == 0,
            "unsigned probe-distance stop did not select the literal end record");
  }
  {
    CopiedMemory m; Header(m); m.Put(kEntries + 4, std::uint8_t{0});
    m.Put(kSingleton + 0xF18, std::uint8_t{1}); m.Put(kEntries + 36, std::uint8_t{7});
    auto r = ReadPointerKeyPredicate31C1D10V1(Access(m), kSingleton, 0, 0);
    Require(r.value == true && r.path == PointerKeyPredicatePathV1::copied_end_record &&
            r.copied_probe_key_count == 0,
            "non-FF end control was silently replaced by absent-key false");
  }
  {
    CopiedMemory m; Header(m); Slot(m, kEntries, 1, 0); m.deny_second_read = kEntries + 4;
    auto r = ReadPointerKeyPredicate31C1D10V1(Access(m), kSingleton, 0);
    Require(!r.value && r.failure == PointerKeyPredicateFailureV1::selected_control &&
            r.path == PointerKeyPredicatePathV1::copied_key_match,
            "literal final selected-control reread was assumed known");
  }
  {
    CopiedMemory m; Header(m); m.Put(kEntries + 4, std::uint8_t{1});
    auto r = ReadPointerKeyPredicate31C1D10V1(Access(m), kSingleton, 0);
    Require(!r.value && r.failure == PointerKeyPredicateFailureV1::probe_key &&
            r.copied_probe_key_count == 0 && m.reads[kSingleton + 0xF18] == 0,
            "unread key was converted to known mismatch/AL false");
  }
  {
    CopiedMemory m; Header(m); Slot(m, kEntries, 1, 9); Slot(m, kEntries + 16, 2, 0);
    auto r = ReadPointerKeyPredicate31C1D10V1(Access(m), kSingleton, 0, 1);
    Require(!r.value && r.failure == PointerKeyPredicateFailureV1::probe_budget &&
            r.copied_probe_key_count == 1 && m.reads[kEntries + 24] == 0 &&
            m.reads[kSingleton + 0xF18] == 0,
            "observer budget became native termination/false");
  }
  {
    constexpr std::uintptr_t entries = 0x100000000000ULL;
    CopiedMemory m; Header(m, entries, std::numeric_limits<std::int32_t>::max());
    m.Put(entries + 0x1BE17165ULL * 16 + 4, std::uint8_t{0});
    m.Put(kSingleton + 0xF18, std::uint8_t{0});
    m.Put(entries - 0x800000000ULL + 4, std::uint8_t{0xFF});
    auto r = ReadPointerKeyPredicate31C1D10V1(Access(m), kSingleton, 0);
    Require(r.value == false && r.end_slot_index_i32 == std::numeric_limits<std::int32_t>::min() &&
            r.selected_record_pointer == entries - 0x800000000ULL,
            "signed32 wrapped end index was changed to positive widening");
  }
  {
    constexpr std::uintptr_t entries = 0x100000000000ULL;
    constexpr std::int64_t index = -1679724187;
    CopiedMemory m; Header(m, entries, -1);
    Slot(m, entries - static_cast<std::uint64_t>(-index) * 16, 1, 0);
    auto r = ReadPointerKeyPredicate31C1D10V1(Access(m), kSingleton, 0);
    Require(r.value == true && r.initial_slot_index_i64 == index,
            "sign-extended hash/mask index was rejected or truncated");
  }
  {
    CopiedMemory m; Header(m);
    for (std::size_t index = 0; index != 255; ++index)
      Slot(m, kEntries + index * 16, index == 0 ? 1 : 0xFF, index + 1);
    Slot(m, kEntries + 255 * 16, 0, 0);
    auto r = ReadPointerKeyPredicate31C1D10V1(Access(m), kSingleton, 0, 256);
    Require(r.value == true && r.copied_probe_key_count == 256 && r.probe_distance_raw_u8 == 0 &&
            r.path == PointerKeyPredicatePathV1::copied_key_match,
            "CL wrapping8 was replaced by an unbounded integer/control-zero gate");
  }
  {
    CopiedMemory m; auto access = Access(m); access.exact_12004_bound = false;
    auto r = ReadPointerKeyPredicate31C1D10V1(access, kSingleton, 0);
    Require(!r.value && r.failure == PointerKeyPredicateFailureV1::exact_build && m.reads.empty(),
            "unbound build consumed memory");
    access.exact_12004_bound = true;
    r = ReadPointerKeyPredicate31C1D10V1(access, std::numeric_limits<std::uintptr_t>::max(), 0);
    Require(!r.value && r.failure == PointerKeyPredicateFailureV1::entries_pointer && m.reads.empty(),
            "unrepresentable source address became native AL false or a wrapped observer read");
  }
}

} // namespace xar::ck3_12004::construction_owner_mode3
