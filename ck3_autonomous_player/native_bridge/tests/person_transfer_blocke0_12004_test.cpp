#include "xar_bridge/person_transfer_blocke0_12004.hpp"

#include <cstring>
#include <limits>
#include <map>
#include <stdexcept>
#include <vector>

using namespace xar::ck3_12004;
namespace {
constexpr std::uintptr_t kA = 0x100000;
constexpr std::uintptr_t kB = 0x200000;
constexpr std::uintptr_t kAData = 0xA000;
constexpr std::uintptr_t kBData = 0xB000;
constexpr const char *kPin =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";

void Require(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}

struct Memory {
  std::map<std::uintptr_t, std::vector<std::byte>> fields;
  std::vector<std::uintptr_t> reads;
  template <typename T> void Put(std::uintptr_t address, const T &value) {
    auto &bytes = fields[address];
    bytes.resize(sizeof(value));
    std::memcpy(bytes.data(), &value, sizeof(value));
  }
  void Values(std::uintptr_t address, const std::vector<std::int64_t> &values) {
    auto &bytes = fields[address];
    bytes.resize(values.size() * sizeof(std::int64_t));
    if (!bytes.empty()) std::memcpy(bytes.data(), values.data(), bytes.size());
  }
  void Header(std::uintptr_t model, std::uintptr_t data,
              std::int32_t capacity, std::int32_t count) {
    Put(model + 0xE0, data);
    Put(model + 0xE8, capacity);
    Put(model + 0xEC, count);
  }
};

bool Read(void *context, const void *address, void *output,
          std::size_t size) noexcept {
  auto &memory = *static_cast<Memory *>(context);
  const auto identity = reinterpret_cast<std::uintptr_t>(address);
  memory.reads.push_back(identity);
  const auto found = memory.fields.find(identity);
  if (found == memory.fields.end() || found->second.size() != size) return false;
  if (size != 0) std::memcpy(output, found->second.data(), size);
  return true;
}

PersonTransferBlockE0Bindings12004 Bind(Memory &memory) {
  return BindPersonTransferBlockE0Memory12004("1.20.0.4", kPin, Read, &memory);
}

struct Before {
  PersonTransferBlockE0Copy12004 a;
  PersonTransferBlockE0Copy12004 b;
};
Before Populate(Memory &memory) {
  memory.Header(kA, kAData, 40, 4);
  memory.Header(kB, kBData, 80, 3);
  memory.Values(kAData, {std::numeric_limits<std::int64_t>::min(), -1, 0, -1});
  memory.Values(kBData, {std::numeric_limits<std::int64_t>::max(), 0, 17});
  const auto binding = Bind(memory);
  return {CopyPersonTransferBlockE0Storage12004(binding, kA),
          CopyPersonTransferBlockE0Storage12004(binding, kB)};
}

int Focused() {
  // 1. Whole bit-preserving copies and same-pair observed cross equality.
  Memory memory;
  const auto before = Populate(memory);
  const auto frozen_before = before;
  memory.Header(kA, kBData, 80, 3);
  memory.Header(kB, kAData, 40, 4);
  const auto binding = Bind(memory);
  const auto post_a = CopyPersonTransferBlockE0Storage12004(binding, kA);
  const auto post_b = CopyPersonTransferBlockE0Storage12004(binding, kB);
  const auto full = ComparePersonTransferBlockE0Copies12004(
      before.a, before.b, post_a, post_b);
  Require(full.model_pair_matches && full.copied_values_cross_equal == true &&
              full.entry_headers_cross_equal == true,
          "whole copied cross equality");
  Require(before.a.allocator_receiver_identity == kA + 0xF8 &&
              before.b.allocator_receiver_identity == kB + 0xF8,
          "allocator receiver is block+18, not a copied allocator result");
  for (const auto address : memory.reads)
    Require(address != kA + 0xF8 && address != kB + 0xF8,
            "no allocator virtual dispatch or vtable read");

  // 2. Material copied sequence equality is independent of pointer/capacity
  // changes. This supplies after observations; no reserve is executed here.
  constexpr std::uintptr_t changed_a = 0xC000;
  constexpr std::uintptr_t changed_b = 0xD000;
  memory.Values(changed_a, *before.b.values_q64);
  memory.Values(changed_b, *before.a.values_q64);
  memory.Header(kA, changed_a, 100, 3);
  memory.Header(kB, changed_b, 200, 4);
  const auto relocated_a = CopyPersonTransferBlockE0Storage12004(binding, kA);
  const auto relocated_b = CopyPersonTransferBlockE0Storage12004(binding, kB);
  const auto relocated = ComparePersonTransferBlockE0Copies12004(
      before.a, before.b, relocated_a, relocated_b);
  Require(relocated.copied_values_cross_equal == true &&
              relocated.entry_headers_cross_equal == false,
          "copied values do not require entry header exchange");

  // 3. An unread diagnostic capacity does not hide complete numerical facts.
  memory.fields.erase(kA + 0xE8);
  const auto no_capacity = CopyPersonTransferBlockE0Storage12004(binding, kA);
  const auto independent = ComparePersonTransferBlockE0Copies12004(
      before.a, before.b, no_capacity, relocated_b);
  Require(!no_capacity.capacity_i32 && no_capacity.values_q64 &&
              no_capacity.values_reason.empty() &&
              independent.copied_values_cross_equal == true &&
              !independent.entry_headers_cross_equal,
          "independent numerical copy during missing header field");

  // 4. One failed Q64 copy preserves the other independently proved side.
  memory.fields.erase(changed_a);
  const auto partial_a = CopyPersonTransferBlockE0Storage12004(binding, kA);
  const auto partial = ComparePersonTransferBlockE0Copies12004(
      before.a, before.b, partial_a, relocated_b);
  Require(partial_a.values_reason == "value_array_unread" &&
              !partial.a_values_equal_pre_b &&
              partial.b_values_equal_pre_a == true &&
              !partial.copied_values_cross_equal &&
              partial.reason == "copied_value_sequences_partial",
          "partial copied values remain partial");

  // 5. Unequal sequences are a resolved false fact; a wrong Model pair remains
  // unattributed rather than being made true by matching values alone.
  auto unequal = relocated_a;
  (*unequal.values_q64)[0] = 55;
  const auto mismatch = ComparePersonTransferBlockE0Copies12004(
      before.a, before.b, unequal, relocated_b);
  Require(mismatch.copied_values_cross_equal == false && mismatch.reason.empty(),
          "resolved false material fact");
  auto wrong_model = relocated_a;
  wrong_model.model_identity = 0x300000;
  const auto wrong_pair = ComparePersonTransferBlockE0Copies12004(
      before.a, before.b, wrong_model, relocated_b);
  Require(!wrong_pair.model_pair_matches &&
              !wrong_pair.copied_values_cross_equal &&
              wrong_pair.reason == "copied_model_pair_mismatch",
          "pair attribution is not inferred from values");

  // 6. Zero and negative counts retain distinct meanings; entry snapshots are
  // immutable after the backing source is changed or removed.
  memory.Header(kA, 0, 0, 0);
  const auto zero = CopyPersonTransferBlockE0Storage12004(binding, kA);
  Require(zero.values_q64 && zero.values_q64->empty() &&
              zero.values_reason.empty(), "zero count is a copied empty value set");
  memory.Header(kA, kAData, 5, -3);
  const auto negative = CopyPersonTransferBlockE0Storage12004(binding, kA);
  Require(!negative.values_q64 && negative.count_i32 == -3 &&
              negative.values_reason == "value_count_negative",
          "negative count is not an empty result");
  memory.fields.clear();
  Require(before.a == frozen_before.a && before.b == frozen_before.b,
          "source mutation cannot rewrite owned history");

  // 7. The direct-store model only exchanges the three source-written header
  // fields. Raw DWORDs and pointer bits survive without allocator semantics.
  const PersonTransferBlockE0Header12004 header_a{
      0x1000, 0xA000, -7, std::numeric_limits<std::int32_t>::min(), 0x1018};
  const PersonTransferBlockE0Header12004 header_b{
      0x2000, 0xB000, 93, std::numeric_limits<std::int32_t>::max(), 0x2018};
  const auto direct = ProjectPersonTransferBlockE0DirectHeaderStores12004(
      header_a, header_b);
  Require(direct.a == PersonTransferBlockE0Header12004{
                          0x1000, 0xB000, 93,
                          std::numeric_limits<std::int32_t>::max(), 0x1018} &&
              direct.b == PersonTransferBlockE0Header12004{
                          0x2000, 0xA000, -7,
                          std::numeric_limits<std::int32_t>::min(), 0x2018},
          "direct stores preserve local block and allocator receivers");

  // 8. Only the actual build is bound; no current-Model resolver or old alias.
  const auto old = BindPersonTransferBlockE0Memory12004("1.20.0.3", kPin, Read,
                                                      &memory);
  Require(!old.enabled &&
              CopyPersonTransferBlockE0Storage12004(old, kA).values_reason ==
                  "exact_build_binding_unavailable",
          "exact build binding");
  Require(CopyPersonTransferBlockE0Storage12004(binding, 0).values_reason ==
              "actual_model_unavailable", "absent actual model");
  return 0;
}
} // namespace

extern "C" __declspec(dllexport) int PersonTransferBlockE0Focused12004() {
  try { return Focused(); }
  catch (...) { return 1; }
}
