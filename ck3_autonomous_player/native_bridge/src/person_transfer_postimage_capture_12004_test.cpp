#include "xar_bridge/person_transfer_postimage_capture_12004.hpp"

#include <array>
#include <cassert>
#include <cstring>
#include <iostream>
#include <map>
#include <set>
#include <utility>
#include <vector>

using namespace xar::ck3_12004;
namespace {
constexpr std::uintptr_t kA = 0x10000, kB = 0x20000;
constexpr std::string_view kHash =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
constexpr std::array<std::uintptr_t, 4> kOffsets{0x10,0x78,0xE0,0x248};
constexpr std::array<std::size_t, 4> kStrides{16,2,8,8};

struct Memory {
  std::map<std::uintptr_t, std::vector<std::uint8_t>> chunks;
  std::set<std::uintptr_t> unread;
  std::map<std::uintptr_t, std::size_t> reads;
  template <class T> void Put(std::uintptr_t at, const T &value) {
    auto &bytes = chunks[at]; bytes.resize(sizeof(value));
    std::memcpy(bytes.data(), &value, sizeof(value));
  }
  template <class T> void PutArray(std::uintptr_t at, const std::vector<T> &value) {
    auto &bytes = chunks[at]; bytes.resize(value.size()*sizeof(T));
    if (!bytes.empty()) std::memcpy(bytes.data(), value.data(), bytes.size());
  }
  static bool Read(void *context, std::uintptr_t at, void *out, std::size_t bytes) noexcept {
    auto &memory = *static_cast<Memory *>(context);
    try {
      ++memory.reads[at];
      if (memory.unread.contains(at)) return false;
      const auto it = memory.chunks.find(at);
      if (it == memory.chunks.end() || it->second.size() != bytes) return false;
      if (bytes) std::memcpy(out,it->second.data(),bytes);
      return true;
    } catch (...) { return false; }
  }
  template <class T> T Get(std::uintptr_t at) const {
    T value{}; const auto &bytes = chunks.at(at);
    assert(bytes.size() == sizeof(value));
    std::memcpy(&value,bytes.data(),sizeof(value)); return value;
  }
};

struct Fixture {
  Memory memory;
  PersonInstalledTransferStage12004 stage;
  PersonTransferPostimageBindings12004 bindings;
  std::size_t supplied_original_calls = 0;
  Fixture() {
    stage.observed = true;
    stage.model_a_identity = kA; stage.model_b_identity = kB;
    stage.original_return_rva = kPersonInstalledTransferCallerReturnRva12004;
    stage.before_event = {0xCAFE,100,77};
    stage.preparation.observed = true;
    stage.preparation.preparation_capture_complete = true;
    stage.preparation.preparation_capture_sequence = 9000000;
    stage.preparation.preparation_capture_thread_id = 77;
    stage.preparation.preparation_completion_thread_id = 77;
    stage.preparation.preparation_model_identity = kB;
    stage.preparation.preparation_context_identity = kB+0x10;
    stage.preparation_owner_matches_before = true;
    for (const auto model : {kA,kB}) {
      for (std::size_t block=0; block<4; ++block) {
        const auto address = model+kOffsets[block];
        const auto data = model+0x1000+block*0x100;
        memory.Put(address,data);
        memory.Put(address+8,std::int32_t{8});
        memory.Put(address+0xC,std::int32_t{3});
        if (block == 3) {
          memory.Put(address+0x10,std::uintptr_t{0xABCD});
          memory.Put(address+0x18,std::uintptr_t{0xBCDE});
        }
      }
      std::vector<PersonTransferBlock10Row12004> rows(3);
      const std::array<std::uint64_t,3> pointers{0,model+0x4000,model+0x4000};
      const std::array<std::uint64_t,3> weights{0x8000000000000000ULL,0xFFFFFFFFFFFFFFFFULL,0};
      for (std::size_t row=0;row<3;++row) {
        std::memcpy(rows[row].data(),&pointers[row],8);
        std::memcpy(rows[row].data()+8,&weights[row],8);
      }
      memory.PutArray(model+0x1000,rows);
      memory.PutArray(model+0x1100,model==kA ? std::vector<std::uint16_t>{1,1,0} :
          std::vector<std::uint16_t>{65535,0,65535});
      memory.PutArray(model+0x1200,model==kA ? std::vector<std::uint64_t>{1,2,3} :
          std::vector<std::uint64_t>{0x8000000000000000ULL,0x7FFFFFFFFFFFFFFFULL,0});
      memory.PutArray(model+0x1300,model==kA ? std::vector<std::uint64_t>{0,0,7} :
          std::vector<std::uint64_t>{0x7FF8000000000042ULL,0xFFFFFFFFFFFFFFFFULL,0});
    }
    bindings=BindPersonTransferPostimageInputs12004("1.20.0.4",kHash,Memory::Read,&memory);
  }
  PersonTransferPhysicalPair12004 Before() {
    return CapturePersonTransferPhysicalPair12004(bindings,stage,
        PersonTransferSnapshotPhase12004::before_original);
  }
  void SuppliedOriginal(bool descriptors=false) {
    ++supplied_original_calls;
    for (std::size_t block=0;block<4;++block) {
      const auto a = kA+kOffsets[block], b = kB+kOffsets[block];
      if (descriptors) {
        std::swap(memory.chunks[a],memory.chunks[b]);
        std::swap(memory.chunks[a+8],memory.chunks[b+8]);
        std::swap(memory.chunks[a+0xC],memory.chunks[b+0xC]);
      } else {
        const auto adata=memory.Get<std::uintptr_t>(a);
        const auto bdata=memory.Get<std::uintptr_t>(b);
        std::swap(memory.chunks[adata],memory.chunks[bdata]);
      }
    }
    stage.original_called = true; stage.original_returned = true;
    stage.completed_event = {0xCAFE,101,77};
    stage.event_clock_and_thread_match = true;
    stage.completion_ordered_after_begin = true;
  }
  PersonTransferPhysicalPair12004 After() {
    return CapturePersonTransferPhysicalPair12004(bindings,stage,
        PersonTransferSnapshotPhase12004::after_original);
  }
};

void InPlaceFullAndOwned() {
  Fixture f; auto before=f.Before();
  assert(before.b.four_operands_copy_complete);
  f.SuppliedOriginal(); auto after=f.After();
  auto result=JoinPersonTransferPhysicalPostimage12004(f.stage,std::move(before),std::move(after));
  assert(f.supplied_original_calls==1);
  assert(result.comparison.four_block_operand_copies_complete);
  assert(result.comparison.four_block_payload_exchange_observed);
  assert(result.comparison.block10_rows.descriptor_cross_equal==false);
  assert(result.comparison.block78_keys.descriptor_cross_equal==false);
  assert(result.comparison.blocke0_values.descriptor_cross_equal==false);
  assert(result.comparison.block248_raw64.descriptor_cross_equal==false);
  assert(result.comparison.preparation_descriptor_matches_before_b==true);
  assert(result.comparison.preparation_threads_match_original==true);
  assert(result.before.b.block78_keys.raw.keys_u16==std::vector<std::uint16_t>({65535,0,65535}));
  assert(result.before.b.blocke0_values.values_q64_raw_bits==
      std::vector<std::uint64_t>({0x8000000000000000ULL,0x7FFFFFFFFFFFFFFFULL,0}));
  f.memory.PutArray(kB+0x1100,std::vector<std::uint16_t>{9,9,9});
  assert(result.before.b.block78_keys.raw.keys_u16->at(0)==65535);
  assert(result.after.a.block10_rows.rows==result.before.b.block10_rows.rows);
}

void DescriptorSwapFull() {
  Fixture f; auto before=f.Before(); f.SuppliedOriginal(true); auto after=f.After();
  const auto result=ComparePersonTransferPhysicalPostimage12004(f.stage,before,after);
  assert(result.four_block_payload_exchange_observed);
  assert(result.block10_rows.descriptor_cross_equal==true);
  assert(result.block78_keys.descriptor_cross_equal==true);
  assert(result.blocke0_values.descriptor_cross_equal==true);
  assert(result.block248_raw64.descriptor_cross_equal==true);
}

void DescriptorPartialDoesNotErasePayload() {
  Fixture f; f.memory.unread.insert(kB+0xE8); auto before=f.Before();
  assert(!before.b.blocke0_values.descriptor_copy_complete);
  assert(before.b.blocke0_values.payload_copy_complete);
  f.memory.unread.clear(); f.SuppliedOriginal(); const auto after=f.After();
  const auto result=ComparePersonTransferPhysicalPostimage12004(f.stage,before,after);
  assert(result.four_block_payload_exchange_observed);
  assert(!result.four_block_operand_copies_complete);
  assert(result.blocke0_values.a_descriptor_equals_b_before==std::nullopt);
  assert(result.blocke0_values.b_descriptor_equals_a_before.has_value());
  assert(result.blocke0_values.payload_cross_equal==true);
}

void DirectionalPartial() {
  Fixture f; f.memory.unread.insert(kA+0x1300); auto before=f.Before();
  f.memory.unread.clear(); f.SuppliedOriginal(); const auto after=f.After();
  const auto result=ComparePersonTransferPhysicalPostimage12004(f.stage,before,after);
  assert(result.block248_raw64.a_payload_equals_b_before==true);
  assert(!result.block248_raw64.b_payload_equals_a_before);
  assert(!result.block248_raw64.payload_cross_equal);
  assert(result.blocke0_values.payload_cross_equal==true);
  assert(!result.four_block_payload_exchange_observed);
}

void FourBoundedOperandsKeepActualCounts() {
  Fixture f;
  f.bindings.limits={1,1,1,1};
  const auto before=f.Before();
  assert(before.b.four_descriptors_copy_complete);
  assert(!before.b.four_payloads_copy_complete);
  assert(before.b.block10_rows.count_i32==3);
  assert(before.b.block78_keys.raw.count_i32==3);
  assert(before.b.blocke0_values.raw.count_i32==3);
  assert(before.b.block248_raw64.raw.count_i32==3);
  assert(before.b.block78_keys.raw.reason=="key_payload_budget_exceeded");
  assert(before.b.blocke0_values.raw.values_reason=="values_payload_budget_exceeded");
  assert(before.b.block248_raw64.raw.reason=="block248_payload_budget_exceeded");
  for (const auto model : {kA,kB}) {
    for (std::size_t block=0;block<4;++block) {
      assert(f.memory.reads[model+kOffsets[block]+0xC]==1);
      assert(f.memory.reads[model+0x1000+block*0x100]==0);
    }
  }
}

void EmptyUnknownAndNegativeRemainDifferent() {
  Fixture f;
  for (std::size_t block=0;block<4;++block) f.memory.Put(kB+kOffsets[block]+0xC,std::int32_t{0});
  f.bindings.limits={0,0,0,0};
  f.memory.unread.insert(kB+0x248); f.memory.unread.insert(kB+0x258);
  const auto empty=f.Before();
  assert(empty.b.four_payloads_copy_complete);
  assert(!empty.b.four_descriptors_copy_complete);
  assert(empty.b.block248_raw64.raw.ordered_payload_raw64->empty());
  f.memory.unread.insert(kB+0xEC);
  const auto unknown=f.Before();
  assert(!unknown.b.blocke0_values.raw.count_i32);
  assert(!unknown.b.blocke0_values.values_q64_raw_bits);
  f.memory.unread.erase(kB+0xEC); f.memory.Put(kB+0xEC,std::int32_t{-1});
  const auto negative=f.Before();
  assert(negative.b.blocke0_values.raw.count_i32==-1);
  assert(!negative.b.blocke0_values.payload_copy_complete);
}

void WrongOccurrenceCannotBorrowArrays() {
  Fixture f; auto before=f.Before(); f.SuppliedOriginal(); auto after=f.After();
  ++after.a.blocke0_values.scope.occurrence.sequence;
  const auto result=ComparePersonTransferPhysicalPostimage12004(f.stage,before,after);
  assert(!result.snapshot_scopes_match_transfer);
  assert(result.four_block_operand_copies_complete);
  assert(!result.four_block_payloads_cross_equal);
  assert(!result.four_block_payload_exchange_observed);
}

void ClockAndThreadAreIndependentOfEquality() {
  Fixture f; const auto before=f.Before(); f.SuppliedOriginal();
  f.stage.completed_event.thread_id.reset(); const auto after=f.After();
  const auto result=ComparePersonTransferPhysicalPostimage12004(f.stage,before,after);
  assert(result.four_block_payloads_cross_equal==true);
  assert(!result.same_clock_and_thread);
  assert(!result.same_original_observation_ready);
  assert(!result.four_block_payload_exchange_observed);
}

void DifferingValuesAndIndependentCounts() {
  Fixture f; const auto before=f.Before(); f.SuppliedOriginal();
  f.memory.Put(kA+0xEC,std::int32_t{2});
  f.memory.PutArray(kA+0x1200,std::vector<std::uint64_t>{0x8000000000000000ULL,42});
  const auto after=f.After();
  const auto result=ComparePersonTransferPhysicalPostimage12004(f.stage,before,after);
  assert(result.block78_keys.payload_cross_equal==true);
  assert(result.blocke0_values.a_payload_equals_b_before==false);
  assert(result.blocke0_values.b_payload_equals_a_before==true);
  assert(result.a_after_pc_key_value_counts_equal==false);
  assert(result.b_before_pc_key_value_counts_equal==true);
  assert(result.four_block_payloads_cross_equal==false);
}

void WrongBindingOrBoundaryReadsNothing() {
  Fixture f;
  f.bindings=BindPersonTransferPostimageInputs12004("1.20.0.3",kHash,Memory::Read,&f.memory);
  auto before=f.Before(); assert(!before.configured); assert(f.memory.reads.empty());
  f.bindings=BindPersonTransferPostimageInputs12004("1.20.0.4",kHash,Memory::Read,&f.memory);
  f.stage.original_return_rva=1; before=f.Before(); assert(f.memory.reads.empty());
  f.stage.original_return_rva=kPersonInstalledTransferCallerReturnRva12004;
  const auto after=f.After(); assert(f.memory.reads.empty());
  assert(after.a.reason=="physical_original_boundary_unobserved");
}
} // namespace

namespace xar::ck3_12004 {
void RunPersonTransferPostimageCrossblockCases12004() {
  InPlaceFullAndOwned(); DescriptorSwapFull(); DescriptorPartialDoesNotErasePayload();
  DirectionalPartial(); FourBoundedOperandsKeepActualCounts(); EmptyUnknownAndNegativeRemainDifferent();
  WrongOccurrenceCannotBorrowArrays(); ClockAndThreadAreIndependentOfEquality();
  DifferingValuesAndIndependentCounts(); WrongBindingOrBoundaryReadsNothing();
  std::cout << "PASS person_transfer_postimage_capture_12004 ten crossblock cases; "
               "new joined owned-memory observations only, no live/native/game or old fixture replay\n";
}
} // namespace xar::ck3_12004
