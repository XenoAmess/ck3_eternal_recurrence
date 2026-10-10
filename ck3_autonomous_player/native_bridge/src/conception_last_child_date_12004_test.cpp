#include "xar_bridge/conception_last_child_date_12004.hpp"

#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>

#include <array>
#include <algorithm>
#include <bit>
#include <cstring>
#include <fstream>
#include <iostream>
#include <iterator>
#include <limits>
#include <map>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace leaf = xar::ck3_12004::conception_last_child_date;

namespace {
void Check(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}

std::vector<std::uint8_t> Load(const char *path, std::size_t expected) {
  std::ifstream file(path, std::ios::binary);
  Check(file.is_open(), "retained source file cannot be opened");
  std::vector<std::uint8_t> bytes(expected);
  file.read(reinterpret_cast<char *>(bytes.data()),
            static_cast<std::streamsize>(expected));
  Check(file.gcount() == static_cast<std::streamsize>(expected),
        "retained source file length is short");
  char extra = 0;
  Check(!file.get(extra), "retained source file length exceeds source packet");
  return bytes;
}

struct Fixture {
  static constexpr std::uintptr_t kBase = 0x100000000ULL;
  static constexpr std::uintptr_t kClock = 0x1000;
  static constexpr std::uintptr_t kChild = 0x2000;
  static constexpr std::uintptr_t kFirst = 0x3000;
  static constexpr std::uintptr_t kFamily = 0x4000;
  static constexpr std::uintptr_t kIds = 0x5000;
  static constexpr std::uintptr_t kFallback = 0x6000;
  static constexpr std::uintptr_t kStore = 0x7000;
  std::map<std::uintptr_t, std::vector<std::uint8_t>> blocks;
  std::vector<std::pair<std::uintptr_t, std::size_t>> reads;
  std::optional<std::uintptr_t> denied{};
  bool deny_all = false;
  std::uintptr_t resolved = kChild;
  std::size_t resolver_calls = 0;
  std::optional<std::uint32_t> resolver_requested{};

  void PutBytes(std::uintptr_t address, const void *value, std::size_t count) {
    auto &bytes = blocks[address];
    bytes.resize(count);
    std::memcpy(bytes.data(), value, count);
  }
  template <typename T>
  void Put(std::uintptr_t address, const T &value) {
    PutBytes(address, &value, sizeof(value));
  }
  static bool Read(void *context, std::uintptr_t address, void *out,
                   std::size_t count) noexcept {
    auto &self = *static_cast<Fixture *>(context);
    self.reads.emplace_back(address, count);
    if (self.deny_all ||
        (self.denied.has_value() && address <= *self.denied &&
         *self.denied - address < count)) return false;
    auto after = self.blocks.upper_bound(address);
    if (after == self.blocks.begin()) return false;
    const auto &entry = *std::prev(after);
    const auto offset = address - entry.first;
    if (offset > entry.second.size() || count > entry.second.size() - offset)
      return false;
    std::memcpy(out, entry.second.data() + offset, count);
    return true;
  }
  static void *Resolve(void *context, std::int32_t id) noexcept {
    auto &self = *static_cast<Fixture *>(context);
    ++self.resolver_calls;
    self.resolver_requested = std::bit_cast<std::uint32_t>(id);
    return reinterpret_cast<void *>(self.resolved);
  }
  leaf::Access Access() {
    return {true, xar::ck3_12004::kExecutableSha256, kBase, this, &Read, &Resolve};
  }
  leaf::CurrentHouseholdSourceInputs Inputs() {
    leaf::CurrentHouseholdSourceInputs input;
    input.first_character_id = 10026;
    input.provider_mode_raw = 3;
    input.first_family_present = true;
    input.child_count_raw = 2;
    input.last_requested_full_id_raw = 0xAA003101U;
    input.selected_full_id_raw = 0xAA003101U;
    input.selected_is_native_fallback = false;
    input.selected_character = kChild;
    return input;
  }
};

class NativeDateBody {
public:
  using Function = void(__fastcall *)(std::uint64_t *, std::int32_t);
  NativeDateBody(const std::vector<std::uint8_t> &shift,
                 const std::vector<std::uint8_t> &adjust,
                 const std::vector<std::uint8_t> &prefix,
                 const std::array<std::uint8_t, 365> &months,
                 const std::array<std::uint8_t, 365> &days,
                 const std::vector<std::uint8_t> &lengths) {
    base_ = static_cast<std::uint8_t *>(
        VirtualAlloc(nullptr, 0x4520000, MEM_RESERVE, PAGE_NOACCESS));
    Check(base_ != nullptr, "offline synthetic image reservation failed");
    try {
      Commit(0xFF6000);
      Commit(0x444C000);
      Commit(0x4513000);
      std::memcpy(base_ + 0xFF6670, shift.data(), shift.size());
      std::memcpy(base_ + 0xFF65B0, adjust.data(), adjust.size());
      std::memcpy(base_ + 0xFF64C0, prefix.data(), prefix.size());
      std::memcpy(base_ + 0x444C340, months.data(), months.size());
      std::memcpy(base_ + 0x444C4B0, days.data(), days.size());
      std::memcpy(base_ + 0x4513BD0, lengths.data(), lengths.size());
      DWORD old = 0;
      Check(VirtualProtect(base_ + 0xFF6000, 0x1000, PAGE_EXECUTE_READ, &old) != 0,
            "offline date body execute protection failed");
      Check(FlushInstructionCache(GetCurrentProcess(), base_ + 0xFF6000,
                                   0x1000) != 0,
            "offline date body instruction cache flush failed");
    } catch (...) {
      VirtualFree(base_, 0, MEM_RELEASE);
      base_ = nullptr;
      throw;
    }
  }
  NativeDateBody(const NativeDateBody &) = delete;
  NativeDateBody &operator=(const NativeDateBody &) = delete;
  ~NativeDateBody() {
    if (base_ != nullptr) VirtualFree(base_, 0, MEM_RELEASE);
  }
  std::uint64_t Run(std::uint64_t storage, std::int32_t shift) const {
    const auto function = reinterpret_cast<Function>(base_ + 0xFF6670);
    function(&storage, shift);
    return storage;
  }
private:
  void Commit(std::uintptr_t page) {
    Check(VirtualAlloc(base_ + page, 0x1000, MEM_COMMIT, PAGE_READWRITE) ==
              base_ + page,
          "offline sparse image page commit failed");
  }
  std::uint8_t *base_ = nullptr;
};

std::int32_t WrapAdd(std::int32_t a, std::int32_t b) {
  return std::bit_cast<std::int32_t>(std::bit_cast<std::uint32_t>(a) +
                                    std::bit_cast<std::uint32_t>(b));
}

} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 5, "expected retained306B,178B,233B and12B source paths");
    const auto shift_body = Load(argv[1], 306);
    const auto adjust_body = Load(argv[2], 178);
    const auto prefix_body = Load(argv[3], 233);
    const auto lengths = Load(argv[4], 12);
    const std::array<std::uint8_t, 12> expected_lengths =
        {31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};
    Check(std::equal(lengths.begin(), lengths.end(), expected_lengths.begin()),
          "actual12B monthlength source differs");
    std::array<std::uint8_t, 365> months{};
    std::array<std::uint8_t, 365> days{};
    std::size_t day_index = 0;
    for (std::size_t month = 0; month < lengths.size(); ++month) {
      for (std::uint8_t day = 0; day < lengths[month]; ++day) {
        months[day_index] = static_cast<std::uint8_t>(month);
        days[day_index] = day;
        ++day_index;
      }
    }
    Check(day_index == 365, "synthetic consistent calendar must cover365days");
    // These365B arrays are explicit fixture data derived from the actual12B
    // lengths, not an observation of the game's current calendar tables.
    NativeDateBody native(shift_body, adjust_body, prefix_body, months, days,
                          lengths);
    Fixture fixture;
    fixture.PutBytes(Fixture::kBase + leaf::kMonthTableRva,
                      months.data(), months.size());
    fixture.PutBytes(Fixture::kBase + leaf::kDayTableRva,
                      days.data(), days.size());
    fixture.PutBytes(Fixture::kBase + leaf::kMonthLengthTableRva,
                      lengths.data(), lengths.size());
    fixture.Put(Fixture::kBase + xar::ck3_12004::kGameStateSlotRva,
                 Fixture::kClock);
    const auto input = fixture.Inputs();
    const auto access = fixture.Access();
    constexpr auto lo = std::numeric_limits<std::int32_t>::min();
    constexpr auto hi = std::numeric_limits<std::int32_t>::max();
    const std::array<std::pair<std::int32_t, std::int32_t>, 16> cases = {{
        {43800000 + 30 * 24 + 17, 1}, {43800000 + 58 * 24 + 17, -1},
        {43800000 + 364 * 24 + 5, 1}, {43800000 + 23, -1},
        {43800000 - 24, 0}, {43800000 - 1, 1}, {lo, hi}, {hi, lo},
        {0, 0}, {-1, -1}, {1, 12}, {hi, 12}, {lo, -12},
        {43800000 + 365 * 24, 25}, {43800000 + 17, -25},
        {43800000 + 200 * 24, hi}
    }};
    std::size_t native_calls = 0;
    std::size_t comparisons = 0;
    for (const auto &entry : cases) {
      const auto raw = entry.first;
      const auto shift = entry.second;
      const std::array<std::uint64_t, 2> upper_caches =
          {0x0000000000000000ULL, 0xFFFFFEFD00000000ULL};
      std::optional<std::uint64_t> previous_result;
      for (const auto upper : upper_caches) {
        const auto storage = upper |
            static_cast<std::uint64_t>(std::bit_cast<std::uint32_t>(raw));
        const auto native_storage = native.Run(storage, shift);
        ++native_calls;
        if (previous_result.has_value()) {
          Check(*previous_result == native_storage,
                "actual helper must ignore original upper date caches");
        }
        previous_result = native_storage;
        const auto native_raw = std::bit_cast<std::int32_t>(
            static_cast<std::uint32_t>(native_storage));
        const std::array<std::int32_t, 5> clocks =
            {native_raw, WrapAdd(native_raw, 1), WrapAdd(native_raw, -1), lo, hi};
        fixture.Put(Fixture::kChild + leaf::kSelectedCharacterDateOffset,
                     std::bit_cast<std::int64_t>(storage));
        fixture.Put(Fixture::kBase + leaf::kLoadedMonthShiftSlotRva, shift);
        for (const auto current : clocks) {
          fixture.Put(Fixture::kClock + xar::ck3_12004::kGameStateDateOffset,
                       current);
          fixture.reads.clear();
          const auto result = leaf::Read(access, input);
          Check(result.date_inputs_available, "date comparison input unavailable");
          Check(result.adjusted_date_storage_raw64 ==
                    std::bit_cast<std::int64_t>(native_storage),
                "conditional leaf differs from actual three-body execution");
          Check(result.adjusted_date_raw_i32 == native_raw,
                "native lowDWORD differs");
          Check(result.recent_child_branch_passed == (current > native_raw),
                "signed greater/equality/wrap comparison differs");
          Check(result.source.last_requested_full_id_raw ==
                    input.last_requested_full_id_raw,
                "source final fullID lost");
          for (const auto &read : fixture.reads) {
            Check(read.second <= 12, "reader exceeds selected source footprint");
          }
          ++comparisons;
        }
      }
    }
    fixture.deny_all = true;
    for (std::size_t bypass = 0; bypass < 3; ++bypass) {
      auto no_date = input;
      no_date.selected_character = 0;
      no_date.selected_is_native_fallback.reset();
      if (bypass == 0) {
        no_date.provider_mode_raw = 2;
        no_date.first_family_present.reset();
        no_date.child_count_raw.reset();
      } else if (bypass == 1) {
        no_date.first_family_present = false;
        no_date.child_count_raw.reset();
      } else {
        no_date.child_count_raw = 0;
      }
      fixture.reads.clear();
      const auto result = leaf::Read(access, no_date);
      Check(result.date_inputs_available && result.recent_child_branch_passed == true,
            "actual empty/mode bypass is not retained");
      Check(!result.date_helper_demanded && fixture.reads.empty(),
            "actual bypass demands unused date input");
    }
    auto negative = input;
    negative.child_count_raw = -1;
    fixture.reads.clear();
    Check(!leaf::Read(access, negative).date_inputs_available,
          "negative child count became known empty");
    Check(fixture.reads.empty(), "invalid negative count demands date reads");
    fixture.deny_all = false;
    auto fallback = input;
    fallback.selected_is_native_fallback = true;
    fallback.selected_full_id_raw = 0xFFFFFFFFU;
    const auto retained_fallback = leaf::Read(access, fallback);
    Check(retained_fallback.date_inputs_available &&
              retained_fallback.source.selected_is_native_fallback == true &&
              retained_fallback.source.selected_full_id_raw == 0xFFFFFFFFU &&
              retained_fallback.source.last_requested_full_id_raw == 0xAA003101U,
          "actual fallback and requested fullID were collapsed");
    const std::array<std::uintptr_t, 5> failures = {
        Fixture::kChild + leaf::kSelectedCharacterDateOffset,
        Fixture::kBase + leaf::kLoadedMonthShiftSlotRva,
        Fixture::kClock + xar::ck3_12004::kGameStateDateOffset,
        Fixture::kBase + leaf::kMonthLengthTableRva,
        Fixture::kBase + leaf::kMonthTableRva + 200
    };
    // Reset to a source with demanded initial month index200.
    const std::int64_t plain = 43800000 + 200 * 24;
    const std::int32_t one = 1;
    fixture.Put(Fixture::kChild + leaf::kSelectedCharacterDateOffset, plain);
    fixture.Put(Fixture::kBase + leaf::kLoadedMonthShiftSlotRva, one);
    for (const auto address : failures) {
      fixture.denied = address;
      const auto unavailable = leaf::Read(access, input);
      Check(!unavailable.date_inputs_available &&
                !unavailable.recent_child_branch_passed.has_value(),
            "missing source read became false, zero or permission");
      Check(!unavailable.unavailable_reason.empty(),
            "missing source read lost concrete reason");
    }
    fixture.denied.reset();
    // New current-household input join: actual final ordered ID and the
    // owner's existing resolver, followed by the actual loaded fallback.
    const std::uint32_t first_id = 10026;
    const std::uint32_t selected_id = 0xAA003101U;
    const std::uint32_t fallback_id = 0xFFFFFFFFU;
    const std::array<std::uint32_t, 2> final_ordered_ids =
        {0xBB004202U, selected_id};
    const std::int32_t two = 2;
    fixture.Put(Fixture::kFirst + xar::ck3_12004::kCharacterFullIdOffset, first_id);
    fixture.Put(Fixture::kFirst + leaf::kCharacterFamilyOffset, Fixture::kFamily);
    fixture.Put(Fixture::kFamily + leaf::kFamilyChildCountOffset, two);
    fixture.Put(Fixture::kFamily + leaf::kFamilyChildIdsOffset, Fixture::kIds);
    fixture.PutBytes(Fixture::kIds, final_ordered_ids.data(), sizeof(final_ordered_ids));
    fixture.Put(Fixture::kBase + xar::ck3_12004::kCharacterStorageSlotRva,
                 Fixture::kStore);
    fixture.Put(Fixture::kBase + leaf::kCharacterFallbackSlotRva,
                 Fixture::kFallback);
    fixture.Put(Fixture::kChild + xar::ck3_12004::kCharacterFullIdOffset, selected_id);
    fixture.Put(Fixture::kFallback + xar::ck3_12004::kCharacterFullIdOffset, fallback_id);
    fixture.Put(Fixture::kFallback + leaf::kSelectedCharacterDateOffset, plain);
    const auto first_pointer = reinterpret_cast<void *>(Fixture::kFirst);
    const auto normal_input = leaf::ReadCurrentHouseholdSourceInputs(
        access, first_pointer, static_cast<std::int32_t>(first_id));
    Check(normal_input.source_inputs_available && fixture.resolver_calls == 1 &&
              fixture.resolver_requested == selected_id &&
              normal_input.source.last_requested_full_id_raw == selected_id &&
              normal_input.source.selected_full_id_raw == selected_id &&
              normal_input.source.selected_is_native_fallback == false &&
              normal_input.source.selected_character == Fixture::kChild,
          "current input does not preserve exact last ordered generationID");
    Check(leaf::Read(access, normal_input.source).date_inputs_available,
          "new current input does not reach conditional date reader");
    fixture.resolved = 0;
    const auto generation_miss = leaf::ReadCurrentHouseholdSourceInputs(
        access, first_pointer, static_cast<std::int32_t>(first_id));
    Check(generation_miss.source_inputs_available &&
              generation_miss.source.selected_is_native_fallback == true &&
              generation_miss.source.last_requested_full_id_raw == selected_id &&
              generation_miss.source.selected_full_id_raw == fallback_id &&
              generation_miss.source.selected_character == Fixture::kFallback,
          "generation miss lost actual loaded fallback");
    Check(leaf::Read(access, generation_miss.source).date_inputs_available,
          "actual fallback date cannot reach conditional reader");
    fixture.resolved = Fixture::kChild;
    const std::uint32_t mismatched = 0xCC003101U;
    fixture.Put(Fixture::kChild + xar::ck3_12004::kCharacterFullIdOffset, mismatched);
    const auto generation_mismatch = leaf::ReadCurrentHouseholdSourceInputs(
        access, first_pointer, static_cast<std::int32_t>(first_id));
    Check(generation_mismatch.source_inputs_available &&
              generation_mismatch.source.selected_is_native_fallback == true &&
              generation_mismatch.source.selected_full_id_raw == fallback_id,
          "full generation mismatch did not select native fallback");
    const std::uintptr_t zero_pointer = 0;
    fixture.Put(Fixture::kBase + xar::ck3_12004::kCharacterStorageSlotRva,
                 zero_pointer);
    fixture.denied = Fixture::kIds + sizeof(std::uint32_t);
    const auto calls_before = fixture.resolver_calls;
    const auto store_absent = leaf::ReadCurrentHouseholdSourceInputs(
        access, first_pointer, static_cast<std::int32_t>(first_id));
    Check(store_absent.source_inputs_available &&
              !store_absent.source.last_requested_full_id_raw.has_value() &&
              store_absent.source.selected_is_native_fallback == true &&
              fixture.resolver_calls == calls_before,
          "store-absent branch demanded unused finalID or resolver");
    fixture.denied.reset();
    const std::int32_t empty = 0;
    fixture.Put(Fixture::kFamily + leaf::kFamilyChildCountOffset, empty);
    fixture.denied = Fixture::kFamily + leaf::kFamilyChildIdsOffset;
    const auto empty_current = leaf::ReadCurrentHouseholdSourceInputs(
        access, first_pointer, static_cast<std::int32_t>(first_id));
    Check(empty_current.source_inputs_available &&
              empty_current.source.child_count_raw == 0 &&
              leaf::Read(access, empty_current.source).recent_child_branch_passed == true,
          "zero-count current input demanded an unused array");
    fixture.denied.reset();
    fixture.Put(Fixture::kFirst + leaf::kCharacterFamilyOffset, zero_pointer);
    const auto absent_current = leaf::ReadCurrentHouseholdSourceInputs(
        access, first_pointer, static_cast<std::int32_t>(first_id));
    Check(absent_current.source_inputs_available &&
              absent_current.source.first_family_present == false &&
              !absent_current.source.child_count_raw.has_value() &&
              leaf::Read(access, absent_current.source).recent_child_branch_passed == true,
          "null-Family current input was changed into a date or empty count");
    fixture.Put(Fixture::kFirst + leaf::kCharacterFamilyOffset, Fixture::kFamily);
    const std::int32_t negative_count = -1;
    fixture.Put(Fixture::kFamily + leaf::kFamilyChildCountOffset, negative_count);
    const auto negative_current = leaf::ReadCurrentHouseholdSourceInputs(
        access, first_pointer, static_cast<std::int32_t>(first_id));
    Check(!negative_current.source_inputs_available &&
              negative_current.source.child_count_raw == -1,
          "negative current count became an empty native branch");
    fixture.Put(Fixture::kFamily + leaf::kFamilyChildCountOffset, two);
    fixture.Put(Fixture::kBase + leaf::kCharacterFallbackSlotRva, zero_pointer);
    const auto absent_fallback = leaf::ReadCurrentHouseholdSourceInputs(
        access, first_pointer, static_cast<std::int32_t>(first_id));
    Check(!absent_fallback.source_inputs_available &&
              !absent_fallback.unavailable_reason.empty(),
          "unreadable/null native fallback supplied invented default date");
    auto wrong_access = access;
    wrong_access.executable_sha256 = "wrong";
    fixture.reads.clear();
    Check(!leaf::Read(wrong_access, input).date_inputs_available &&
              fixture.reads.empty(),
          "wrong exact build reached native layout reads");
    std::cout << "GREEN one focused qualification: native_calls=" << native_calls
              << " conditional_comparisons=" << comparisons
              << " bypasses=3 read_failures=5 negative_count=1 fallback=1"
              << " current_input_cases=8"
              << " new_game_calls=0 source_exe_reads=0 committed_pages=3\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "RED " << error.what() << '\n';
    return 1;
  }
}
