#include "xar_bridge/person_transfer_block10_12004.hpp"
#include "xar_bridge/ck3_12004.hpp"

#include <cstring>
#include <iostream>
#include <stdexcept>
#include <string>
#include <utility>

using namespace xar::ck3_12004;

namespace {

void Require(bool value, const char *message) {
  if (!value) throw std::runtime_error(message);
}

struct Segment {
  std::uintptr_t address = 0;
  std::vector<std::uint8_t> bytes;
};
struct Read {
  std::uintptr_t address = 0;
  std::size_t bytes = 0;
};
struct Memory {
  std::vector<Segment> segments;
  std::vector<std::uintptr_t> denied;
  std::vector<Read> reads;

  void Set(std::uintptr_t address, const void *input, std::size_t size) {
    std::vector<std::uint8_t> data(size);
    if (size != 0) std::memcpy(data.data(), input, size);
    for (auto &segment : segments) {
      if (segment.address == address) {
        segment.bytes = std::move(data);
        return;
      }
    }
    segments.push_back({address, std::move(data)});
  }

  void Descriptor(std::uintptr_t model, std::uintptr_t data,
                  std::int32_t capacity, std::int32_t count) {
    std::array<std::uint8_t, 0x20> bytes{};
    bytes.fill(0xCE);
    std::memcpy(bytes.data(), &data, sizeof(data));
    std::memcpy(bytes.data() + 8, &capacity, sizeof(capacity));
    std::memcpy(bytes.data() + 0xC, &count, sizeof(count));
    Set(model + 0x10, bytes.data(), bytes.size());
  }

  void Rows(std::uintptr_t data,
            const std::vector<PersonTransferBlock10Row12004> &rows) {
    Set(data, rows.data(), rows.size() * kPersonTransferBlock10RowBytes12004);
  }

  static bool Copy(void *context, const void *address, void *output,
                   std::size_t size) noexcept {
    auto &memory = *static_cast<Memory *>(context);
    const auto at = reinterpret_cast<std::uintptr_t>(address);
    try {
      memory.reads.push_back({at, size});
      for (const auto denied_address : memory.denied)
        if (at == denied_address) return false;
      for (const auto &segment : memory.segments) {
        if (at < segment.address) continue;
        const auto offset = static_cast<std::size_t>(at - segment.address);
        if (offset > segment.bytes.size() || size > segment.bytes.size() - offset)
          continue;
        if (size != 0) std::memcpy(output, segment.bytes.data() + offset, size);
        return true;
      }
    } catch (...) {
      return false;
    }
    return false;
  }
};

PersonTransferBlock10Row12004 Row(std::uint64_t first, std::uint64_t second) {
  PersonTransferBlock10Row12004 row{};
  std::memcpy(row.data(), &first, sizeof(first));
  std::memcpy(row.data() + 8, &second, sizeof(second));
  return row;
}

PersonTransferBlock10Bindings12004 Bind(Memory &memory) {
  return BindPersonTransferBlock10Inputs12004(
      kGameVersion, kExecutableSha256, Memory::Copy, &memory);
}

void DescriptorSwapAndOwnership() {
  Memory memory;
  constexpr std::uintptr_t a = 0x1000, b = 0x2000;
  constexpr std::uintptr_t da = 0x3000, db = 0x4000;
  const std::vector<PersonTransferBlock10Row12004> rows_a{
      Row(0xABCDEF0000000010ULL, 0x8000000000000000ULL),
      Row(0xABCDEF0000000010ULL, 0xFFFFFFFFFFFFFFFFULL),
      Row(0, 0x7FFFFFFFFFFFFFFFULL)};
  const std::vector<PersonTransferBlock10Row12004> rows_b{
      Row(0xDEADBEEF00000010ULL, 0), Row(0xDEADBEEF00000010ULL, 0x100000001ULL)};
  memory.Descriptor(a, da, 8, 3);
  memory.Descriptor(b, db, 6, 2);
  memory.Rows(da, rows_a);
  memory.Rows(db, rows_b);
  const auto original_segments = memory.segments;
  const auto bindings = Bind(memory);
  const auto before_a = ReadPersonTransferBlock10ForModel12004(bindings, a, 8);
  const auto before_b = ReadPersonTransferBlock10ForModel12004(bindings, b, 8);
  Require(before_a.rows_ready && before_b.rows_ready, "before rows unavailable");
  Require(*before_a.rows == rows_a && *before_b.rows == rows_b,
          "raw row bits/order/duplicates were altered");
  Require(memory.segments.size() == original_segments.size(), "observer added memory");
  for (std::size_t i = 0; i < memory.segments.size(); ++i)
    Require(memory.segments[i].bytes == original_segments[i].bytes,
            "observer mutated source memory");
  Require(memory.reads.size() == 8, "unexpected snapshot read count");
  Require(memory.reads[0].address == a + 0x10 && memory.reads[0].bytes == 8 &&
          memory.reads[1].address == a + 0x18 && memory.reads[1].bytes == 4 &&
          memory.reads[2].address == a + 0x1C && memory.reads[2].bytes == 4 &&
          memory.reads[3].address == da && memory.reads[3].bytes == 48,
          "snapshot did not use pointer/capacity/count and exact16B rows");
  memory.Descriptor(a, db, 6, 2);
  memory.Descriptor(b, da, 8, 3);
  const auto after_a = ReadPersonTransferBlock10ForModel12004(bindings, a, 8);
  const auto after_b = ReadPersonTransferBlock10ForModel12004(bindings, b, 8);
  // The supplied postimages are independent inputs, not an emulation of CK3.
  const auto comparison = ComparePersonTransferBlock10Postimage12004(
      before_a, before_b, after_a, after_b);
  Require(comparison.row_comparison_ready &&
          comparison.row_postimage_matches_exchange == true,
          "independent exchanged row postimages did not compare equal");
  Require(comparison.descriptor_comparison_ready &&
          comparison.descriptor_postimage_matches_swap == true,
          "independent descriptor swap did not compare equal");
  memory.Rows(da, {Row(1, 2)});
  memory.Rows(db, {Row(3, 4)});
  Require(*before_a.rows == rows_a && *before_b.rows == rows_b &&
          *after_a.rows == rows_b && *after_b.rows == rows_a,
          "owned historical snapshot changed after source mutation");
}

void InPlaceRowsAndMismatch() {
  Memory memory;
  constexpr std::uintptr_t a = 0x1000, b = 0x2000, da = 0x3000, db = 0x4000;
  const std::vector<PersonTransferBlock10Row12004> rows_a{Row(10, 20), Row(10, 30)};
  const std::vector<PersonTransferBlock10Row12004> rows_b{
      Row(40, 50), Row(60, 70), Row(80, 90)};
  memory.Descriptor(a, da, 6, 2);
  memory.Descriptor(b, db, 6, 3);
  memory.Rows(da, rows_a);
  memory.Rows(db, rows_b);
  const auto bindings = Bind(memory);
  const auto before_a = ReadPersonTransferBlock10ForModel12004(bindings, a, 6);
  const auto before_b = ReadPersonTransferBlock10ForModel12004(bindings, b, 6);
  memory.Descriptor(a, da, 6, 3);
  memory.Descriptor(b, db, 6, 2);
  memory.Rows(da, rows_b);
  memory.Rows(db, rows_a);
  const auto after_a = ReadPersonTransferBlock10ForModel12004(bindings, a, 6);
  const auto after_b = ReadPersonTransferBlock10ForModel12004(bindings, b, 6);
  const auto comparison = ComparePersonTransferBlock10Postimage12004(
      before_a, before_b, after_a, after_b);
  Require(comparison.row_postimage_matches_exchange == true,
          "in-place supplied row postimages incorrectly demand pointer swap");
  Require(comparison.descriptor_postimage_matches_swap == false,
          "in-place descriptors were misreported as swapped");
  memory.Rows(da, {rows_b[2], rows_b[1], rows_b[0]});
  const auto reordered_after_a = ReadPersonTransferBlock10ForModel12004(bindings, a, 6);
  const auto reordered = ComparePersonTransferBlock10Postimage12004(
      before_a, before_b, reordered_after_a, after_b);
  Require(reordered.row_comparison_ready &&
          reordered.a_after_rows_equal_b_before == false &&
          reordered.b_after_rows_equal_a_before == true &&
          reordered.row_postimage_matches_exchange == false,
          "row order mismatch was collapsed or unavailable");
  auto wrong_receiver = after_a;
  wrong_receiver.model_identity = 0x9000;
  const auto rejected = ComparePersonTransferBlock10Postimage12004(
      before_a, before_b, wrong_receiver, after_b);
  Require(!rejected.receiver_pair_matches && !rejected.row_postimage_matches_exchange,
          "different original receiver pair was joined");
}

void IndependentPartialCopies() {
  Memory memory;
  constexpr std::uintptr_t a = 0x1000, b = 0x2000, da = 0x3000, db = 0x4000;
  memory.Descriptor(a, da, 4, 1);
  memory.Descriptor(b, db, 4, 1);
  memory.Rows(da, {Row(10, 20)});
  memory.Rows(db, {Row(30, 40)});
  const auto bindings = Bind(memory);
  memory.denied = {a + 0x18}; // Capacity is optional for row postimage.
  const auto before_a = ReadPersonTransferBlock10ForModel12004(bindings, a, 4);
  memory.denied.clear();
  const auto before_b = ReadPersonTransferBlock10ForModel12004(bindings, b, 4);
  Require(before_a.rows_ready && !before_a.descriptor_ready &&
          !before_a.capacity_i32, "capacity failure suppressed copied rows");
  memory.Descriptor(a, db, 4, 1);
  memory.Descriptor(b, da, 4, 1);
  const auto after_a = ReadPersonTransferBlock10ForModel12004(bindings, a, 4);
  memory.denied = {da};
  const auto after_b = ReadPersonTransferBlock10ForModel12004(bindings, b, 4);
  const auto partial = ComparePersonTransferBlock10Postimage12004(
      before_a, before_b, after_a, after_b);
  Require(partial.receiver_pair_matches &&
          partial.a_after_rows_equal_b_before == true &&
          !partial.b_after_rows_equal_a_before &&
          !partial.row_postimage_matches_exchange &&
          !partial.descriptor_comparison_ready,
          "unread reverse direction erased independent ready direction");
  Require(after_b.reason == "person_block10_rows_unread" && !after_b.rows,
          "unread demanded rows were manufactured");
}

void EmptyNegativeAndBudget() {
  Memory memory;
  constexpr std::uintptr_t model = 0x1000, data = 0x3000;
  const auto bindings = Bind(memory);
  memory.Descriptor(model, 0, 0, 0);
  memory.denied = {model + 0x10, model + 0x18};
  const auto empty = ReadPersonTransferBlock10ForModel12004(bindings, model, 0);
  Require(empty.rows_ready && empty.rows && empty.rows->empty() &&
          !empty.descriptor_ready && memory.reads.size() == 3,
          "zero count demanded a pointer or payload");
  memory.denied.clear();
  memory.Descriptor(model, data, 0, -1);
  const auto negative = ReadPersonTransferBlock10ForModel12004(bindings, model, 8);
  Require(!negative.rows_ready && negative.count_i32 == -1 &&
          negative.reason == "person_block10_count_negative",
          "negative signed count was treated as an empty container");
  memory.Descriptor(model, data, 8, 2);
  const auto limited = ReadPersonTransferBlock10ForModel12004(bindings, model, 1);
  Require(!limited.rows_ready && limited.descriptor_ready && limited.row_copy_budget == 1 &&
          limited.reason == "person_block10_row_copy_budget_exceeded",
          "observer copy budget was treated as a native zero/count rule");
  memory.Descriptor(model, 0, 4, 1);
  const auto missing = ReadPersonTransferBlock10ForModel12004(bindings, model, 4);
  Require(!missing.rows_ready && missing.data_identity == 0 &&
          missing.reason == "person_block10_row_pointer_unavailable",
          "positive-count null data was treated as empty");
}

void ExactBindingAndNullReceiver() {
  Memory memory;
  const auto wrong = BindPersonTransferBlock10Inputs12004(
      "1.20.0.3", kExecutableSha256, Memory::Copy, &memory);
  const auto wrong_hash = BindPersonTransferBlock10Inputs12004(
      kGameVersion, "old", Memory::Copy, &memory);
  const auto first = ReadPersonTransferBlock10ForModel12004(wrong, 0x1000, 4);
  const auto second = ReadPersonTransferBlock10ForModel12004(wrong_hash, 0x1000, 4);
  Require(!first.configured && !second.configured && memory.reads.empty(),
          "wrong exact binding performed memory copies");
  const auto null_model = ReadPersonTransferBlock10ForModel12004(Bind(memory), 0, 4);
  Require(null_model.configured && !null_model.rows_ready &&
          null_model.reason == "person_block10_model_unavailable" && memory.reads.empty(),
          "null receiver read a replacement model");
}

} // namespace

int main() {
  try {
    DescriptorSwapAndOwnership();
    InPlaceRowsAndMismatch();
    IndependentPartialCopies();
    EmptyNegativeAndBudget();
    ExactBindingAndNullReceiver();
    std::cout << "PASS person_transfer_block10_12004 focused compound; "
                 "owned supplied postimages only, no native/game execution\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL person_transfer_block10_12004: " << error.what() << '\n';
    return 1;
  }
}
