#include "xar_bridge/person_transfer_block248_12004.hpp"
#include "xar_bridge/person_installed_transfer_stage_12004.hpp"

#include <array>
#include <cassert>
#include <cstring>
#include <iostream>
#include <limits>
#include <utility>
#include <vector>

using namespace xar::ck3_12004;

namespace {

struct Model {
  alignas(8) std::array<std::byte, 0x280> bytes{};
  std::uintptr_t identity() const {
    return reinterpret_cast<std::uintptr_t>(bytes.data());
  }
};

template <class T>
void Put(Model &model, std::size_t offset, T value) {
  assert(offset + sizeof(value) <= model.bytes.size());
  std::memcpy(model.bytes.data() + offset, &value, sizeof(value));
}

struct Memory {
  std::vector<std::pair<std::uintptr_t, std::size_t>> ranges;
  std::optional<std::uintptr_t> fail_address;
  std::vector<std::pair<std::uintptr_t, std::size_t>> reads;

  template <class T>
  void Add(const T &object) {
    ranges.emplace_back(reinterpret_cast<std::uintptr_t>(&object), sizeof(object));
  }

  static bool Read(void *context, std::uintptr_t address, void *output,
                   std::size_t size) noexcept {
    auto &memory = *static_cast<Memory *>(context);
    memory.reads.emplace_back(address, size);
    if (memory.fail_address && address == *memory.fail_address)
      return false;
    for (const auto &[base, length] : memory.ranges) {
      if (address >= base && address - base <= length &&
          size <= length - static_cast<std::size_t>(address - base)) {
        std::memcpy(output, reinterpret_cast<const void *>(address), size);
        return true;
      }
    }
    return false;
  }
};

void Header(Model &model, std::uintptr_t data, std::int32_t capacity,
            std::int32_t count, std::uintptr_t allocator) {
  Put(model, 0x248, data);
  Put(model, 0x250, capacity);
  Put(model, 0x254, count);
  Put(model, 0x258, allocator);
  Put(model, 0x260, std::uintptr_t{0x123456789ABCDEF0});
}

PersonInstalledTransferStage12004 Completed(const Model &a, const Model &b) {
  PersonInstalledTransferStage12004 result;
  result.observed = true;
  result.original_called = true;
  result.original_returned = true;
  result.model_a_identity = a.identity();
  result.model_b_identity = b.identity();
  result.event_clock_and_thread_match = true;
  result.completion_ordered_after_begin = true;
  return result;
}

} // namespace

int main() {
  Model a, b;
  std::array<std::uint64_t, 4> values_a{
      7, 7, std::numeric_limits<std::uint64_t>::max(), 0};
  std::array<std::uint64_t, 4> values_b{11, 12, 0, 0};
  Memory memory;
  memory.Add(a);
  memory.Add(b);
  memory.Add(values_a);
  memory.Add(values_b);
  const PersonTransferBlock248Bindings12004 bindings{&memory, &Memory::Read};
  const auto pointer_a = reinterpret_cast<std::uintptr_t>(values_a.data());
  const auto pointer_b = reinterpret_cast<std::uintptr_t>(values_b.data());
  Header(a, pointer_a, 4, 3, 0xAA);
  Header(b, pointer_b, 4, 2, 0xBB);
  auto transfer = Completed(a, b);
  const auto pre_a = ReadPersonTransferBlock24812004(bindings, a.identity());
  const auto pre_b = ReadPersonTransferBlock24812004(bindings, b.identity());
  assert(pre_a.payload_ready && pre_b.payload_ready);
  assert(pre_a.allocator_identity == std::uintptr_t{0xAA});
  assert(pre_a.allocator_dispatch_vtable_identity ==
         std::uintptr_t{0x123456789ABCDEF0});
  assert((*pre_a.ordered_payload_raw64 == std::vector<std::uint64_t>{
      7, 7, std::numeric_limits<std::uint64_t>::max()}));

  // Original-in-place outcome: pointer/capacity stay, actual payload/count swap.
  values_a = {11, 12, 99, 0};
  values_b = {7, 7, std::numeric_limits<std::uint64_t>::max(), 0};
  Put(a, 0x254, std::int32_t{2});
  Put(b, 0x254, std::int32_t{3});
  auto post_a = ReadPersonTransferBlock24812004(bindings, a.identity());
  auto post_b = ReadPersonTransferBlock24812004(bindings, b.identity());
  auto comparison = ComparePersonTransferBlock24812004(
      transfer, pre_a, pre_b, post_a, post_b);
  assert(comparison.payload_comparison_ready);
  assert(comparison.two_way_payload_equality == true);
  assert(comparison.completion_event_order_proven == true);
  assert(post_a.data_identity == pre_a.data_identity);
  assert((*pre_a.ordered_payload_raw64)[0] == 7); // immutable copied preimage

  // Pointer-exchange outcome is checked by the same actual sequence contract.
  values_a = {7, 7, std::numeric_limits<std::uint64_t>::max(), 0};
  values_b = {11, 12, 0, 0};
  Header(a, pointer_b, 2, 2, 0xAA);
  Header(b, pointer_a, 3, 3, 0xBB);
  post_a = ReadPersonTransferBlock24812004(bindings, a.identity());
  post_b = ReadPersonTransferBlock24812004(bindings, b.identity());
  comparison = ComparePersonTransferBlock24812004(
      transfer, pre_a, pre_b, post_a, post_b);
  assert(comparison.two_way_payload_equality == true);
  assert(post_a.data_identity == pre_b.data_identity);
  assert(post_a.capacity_i32 == 2);
  assert(post_a.allocator_identity == pre_a.allocator_identity);

  // A changed payload remains an available false comparison, not unavailable.
  values_b[1] = 123;
  post_a = ReadPersonTransferBlock24812004(bindings, a.identity());
  comparison = ComparePersonTransferBlock24812004(
      transfer, pre_a, pre_b, post_a, post_b);
  assert(comparison.payload_comparison_ready);
  assert(comparison.post_a_equals_pre_b == false);
  assert(comparison.post_b_equals_pre_a == true);
  assert(comparison.two_way_payload_equality == false);

  // Missing capacity and allocator provenance do not erase copied payload.
  memory.fail_address = a.identity() + 0x250;
  auto partial_header = ReadPersonTransferBlock24812004(bindings, a.identity());
  assert(!partial_header.capacity_i32 && partial_header.payload_ready);
  memory.fail_address = a.identity() + 0x258;
  partial_header = ReadPersonTransferBlock24812004(bindings, a.identity());
  assert(!partial_header.allocator_identity && partial_header.payload_ready);

  // Unknown count preserves the independent raw fields and the other side.
  memory.fail_address = b.identity() + 0x254;
  const auto partial_b = ReadPersonTransferBlock24812004(bindings, b.identity());
  assert(!partial_b.count_i32 && partial_b.data_identity);
  comparison = ComparePersonTransferBlock24812004(
      transfer, pre_a, pre_b, post_a, partial_b);
  assert(comparison.post_a_equals_pre_b == false);
  assert(!comparison.post_b_equals_pre_a && !comparison.payload_comparison_ready);

  // Signed negatives remain raw and cannot be silently converted to empty.
  memory.fail_address.reset();
  Put(b, 0x254, std::int32_t{-1});
  const auto negative = ReadPersonTransferBlock24812004(bindings, b.identity());
  assert(negative.count_i32 == -1 && !negative.payload_ready);
  assert(!negative.ordered_payload_raw64);

  // Count zero supplies known empty payload even when the pointer copy fails.
  Put(b, 0x254, std::int32_t{0});
  memory.fail_address = b.identity() + 0x248;
  const auto empty = ReadPersonTransferBlock24812004(bindings, b.identity());
  assert(!empty.data_identity && empty.payload_ready);
  assert(empty.ordered_payload_raw64->empty());

  // A demanded positive payload cannot be replaced by zero-filled copy data.
  memory.fail_address = pointer_b;
  Put(a, 0x254, std::int32_t{2});
  const auto unread = ReadPersonTransferBlock24812004(bindings, a.identity());
  assert(unread.count_i32 == 2 && !unread.payload_ready);
  assert(!unread.ordered_payload_raw64);
  assert(unread.reason == "ordered_payload_unread");
  memory.fail_address.reset();

  // Copied payload equality does not synthesize original return or same pair.
  transfer.original_returned = false;
  comparison = ComparePersonTransferBlock24812004(
      transfer, pre_a, pre_b, post_a, post_b);
  assert(!comparison.original_transfer_returned);
  assert(!comparison.two_way_payload_equality);
  transfer.original_returned = true;
  transfer.model_b_identity = a.identity();
  comparison = ComparePersonTransferBlock24812004(
      transfer, pre_a, pre_b, post_a, post_b);
  assert(!comparison.copied_model_pair_matches_transfer);
  assert(!comparison.two_way_payload_equality);

  // Missing causal clock proof stays unknown while the copied values survive.
  transfer = Completed(a, b);
  transfer.event_clock_and_thread_match.reset();
  comparison = ComparePersonTransferBlock24812004(
      transfer, pre_a, pre_b, post_a, post_b);
  assert(comparison.payload_comparison_ready);
  assert(!comparison.completion_event_order_proven);
  transfer.event_clock_and_thread_match = false;
  comparison = ComparePersonTransferBlock24812004(
      transfer, pre_a, pre_b, post_a, post_b);
  assert(comparison.completion_event_order_proven == false);

  // Exact read plan covers only the declared Model fields and raw payload.
  const auto absent = ReadPersonTransferBlock24812004(bindings, 0);
  assert(!absent.block_identity && !absent.payload_ready);
  const auto overflow = ReadPersonTransferBlock24812004(
      bindings, std::numeric_limits<std::uintptr_t>::max());
  assert(!overflow.block_identity && !overflow.payload_ready);
  const auto a_begin = a.identity() + 0x248;
  const auto b_begin = b.identity() + 0x248;
  for (const auto &[address, size] : memory.reads) {
    const bool header = (address >= a_begin && address < a_begin + 0x20) ||
                        (address >= b_begin && address < b_begin + 0x20);
    assert(header || address == pointer_a || address == pointer_b);
    if (header) assert(size == 4 || size == 8);
  }
  std::cout << "person_transfer_block248_12004: 11 owned-memory scenes PASS\n";
}
