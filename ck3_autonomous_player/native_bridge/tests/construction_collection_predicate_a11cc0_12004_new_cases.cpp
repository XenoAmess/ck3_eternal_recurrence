#include "xar_bridge/construction_collection_predicate_a11cc0_12004.hpp"

#include <array>
#include <cstring>
#include <limits>
#include <stdexcept>
#include <string>

namespace {
using namespace xar::ck3_12004::construction_owner_mode3;

void require(bool passed, const char *name) {
  if (!passed) throw std::runtime_error(name);
}

struct Memory {
  std::array<unsigned char, 16> header{};
  std::array<std::uintptr_t, 6> list{
      0x11223344AABBCCDDULL, 0x99887766AABBCCDDULL,
      0x99887766AABBCCDDULL, 0, 5, 6};
  std::int32_t initial_count = 3;
  std::int32_t final_count = 3;
  std::uintptr_t initial_buffer = 0;
  std::uintptr_t final_buffer = 0;
  int count_reads = 0;
  int array_reads = 0;
  int denied_index = -1;
  bool deny_initial_count = false;
  bool deny_initial_buffer = false;
  bool deny_final_count = false;
  bool deny_final_buffer = false;
  bool throw_reader = false;

  Memory() {
    initial_buffer = final_buffer = reinterpret_cast<std::uintptr_t>(list.data());
  }
  std::uintptr_t collection() const {
    return reinterpret_cast<std::uintptr_t>(header.data());
  }
  ContextPredicateInputsV1 inputs(std::uintptr_t key = 0x99887766AABBCCDDULL) const {
    return {0x123456789ABCDEF0ULL, 0x11000, key, 0x22000, 0x33000};
  }
  static bool read(void *opaque, const void *source, void *destination,
                   std::size_t size) {
    auto &self = *static_cast<Memory *>(opaque);
    if (self.throw_reader) throw std::runtime_error("copied memory unavailable");
    const auto address = reinterpret_cast<std::uintptr_t>(source);
    if (address == self.collection() + 12 && size == sizeof(std::int32_t)) {
      ++self.count_reads;
      const bool final = self.count_reads > 1;
      if (final ? self.deny_final_count : self.deny_initial_count) return false;
      const auto value = final ? self.final_count : self.initial_count;
      std::memcpy(destination, &value, size);
      return true;
    }
    if (address == self.collection() && size == sizeof(std::uintptr_t)) {
      const bool final = self.count_reads > 1;
      if (final ? self.deny_final_buffer : self.deny_initial_buffer) return false;
      const auto value = final ? self.final_buffer : self.initial_buffer;
      std::memcpy(destination, &value, size);
      return true;
    }
    const auto buffer = reinterpret_cast<std::uintptr_t>(self.list.data());
    if (size == sizeof(std::uintptr_t) && address >= buffer &&
        address - buffer < sizeof(self.list) && (address - buffer) % 8 == 0) {
      const auto index = static_cast<std::size_t>((address - buffer) / 8);
      ++self.array_reads;
      if (self.denied_index >= 0 &&
          index == static_cast<std::size_t>(self.denied_index)) return false;
      std::memcpy(destination, &self.list[index], size);
      return true;
    }
    return false;
  }
  RawReceiverAccessV1 access() { return {this, read, 0, true}; }
};
} // namespace

//18 new source-model cases, no standalone main, Game or native execution.
// Central03/10 calls this export once in the first new M4 compound.
bool RunConstructionCollectionPredicateA11CC0NewCases12004(std::string &failure) {
  try {
    {
      Memory m;
      const auto in = m.inputs();
      const auto r = ReadConstructionCollectionPredicateA11CC0V1(
          m.access(), in, m.collection(), in.first_pointer);
      require(r.value == true && r.ordered_qwords_complete &&
              r.ordered_qwords.size() == 3 && r.first_match_index == std::uint32_t{1} &&
              r.ordered_qwords[1] == r.ordered_qwords[2] &&
              r.header_unchanged == true && r.inputs.frame_key == in.frame_key &&
              r.inputs.raw_receiver_pointer == in.raw_receiver_pointer &&
              r.inputs.selector_object_pointer == in.selector_object_pointer,
              "full64 comparison, first occurrence, duplicates and same frame Inputs");
    }
    {
      Memory m;
      m.initial_count = m.final_count = 1;
      const auto in = m.inputs();
      const auto r = ReadConstructionCollectionPredicateA11CC0V1(
          m.access(), in, m.collection(), in.first_pointer);
      require(r.value == false && !r.first_match_index &&
              r.found_pointer == r.initial_end_pointer,
              "same low32 with different high32 is known false");
    }
    {
      Memory m;
      m.initial_count = m.final_count = 0;
      m.initial_buffer = m.final_buffer = 0;
      const auto in = m.inputs(0);
      const auto r = ReadConstructionCollectionPredicateA11CC0V1(
          m.access(), in, m.collection(), 0, 0);
      require(r.value == false && r.initial_count_raw == 0 &&
              r.initial_buffer_pointer == std::uintptr_t{0} && r.ordered_qwords_complete &&
              r.found_pointer == std::uintptr_t{0} && m.array_reads == 0,
              "known null empty array and zero copy budget preserve false");
    }
    {
      Memory m;
      m.initial_count = m.final_count = 1;
      m.list[0] = 0;
      const auto in = m.inputs(0);
      const auto r = ReadConstructionCollectionPredicateA11CC0V1(
          m.access(), in, m.collection(), 0);
      require(r.value == true && r.first_match_index == std::uint32_t{0},
              "zero qword key is a legal match");
    }
    {
      Memory m;
      m.initial_count = -7;
      const auto in = m.inputs();
      const auto r = ReadConstructionCollectionPredicateA11CC0V1(
          m.access(), in, m.collection(), in.first_pointer);
      require(!r.value && r.initial_count_raw == -7 &&
              r.failure == CollectionPredicateA11CC0FailureV1::negative_initial_count &&
              m.array_reads == 0,
              "negative initial count remains raw and unavailable");
    }
    {
      Memory m;
      const auto in = m.inputs();
      const auto r = ReadConstructionCollectionPredicateA11CC0V1(
          m.access(), in, m.collection(), in.first_pointer, 2);
      require(!r.value && r.initial_count_raw == 3 && m.array_reads == 0 &&
              r.failure == CollectionPredicateA11CC0FailureV1::copy_bound,
              "exceeded copier bound is unavailable rather than false");
    }
    {
      Memory m;
      m.denied_index = 2;
      const auto in = m.inputs();
      const auto r = ReadConstructionCollectionPredicateA11CC0V1(
          m.access(), in, m.collection(), in.first_pointer);
      require(!r.value && r.ordered_qwords.size() == 2 &&
              !r.ordered_qwords_complete && r.first_match_index == std::uint32_t{1} &&
              r.failure == CollectionPredicateA11CC0FailureV1::array_read,
              "partial copied extent preserves prefix without AL credit");
    }
    {
      Memory m;
      m.deny_initial_count = true;
      const auto in = m.inputs();
      const auto r = ReadConstructionCollectionPredicateA11CC0V1(
          m.access(), in, m.collection(), in.first_pointer);
      require(!r.value && !r.initial_count_raw && !r.initial_buffer_pointer,
              "missing count is not manufactured from empty vector");
    }
    {
      Memory m;
      m.initial_count = 0;
      m.deny_initial_buffer = true;
      const auto in = m.inputs();
      const auto r = ReadConstructionCollectionPredicateA11CC0V1(
          m.access(), in, m.collection(), in.first_pointer);
      require(!r.value && r.initial_count_raw == 0 && !r.initial_buffer_pointer &&
              r.failure == CollectionPredicateA11CC0FailureV1::header_buffer,
              "missing empty-array pointer differs from observed null pointer");
    }
    {
      Memory m;
      m.initial_count = m.final_count = 0;
      m.final_buffer += 8;
      const auto in = m.inputs();
      const auto r = ReadConstructionCollectionPredicateA11CC0V1(
          m.access(), in, m.collection(), in.first_pointer);
      require(r.value == true && !r.first_match_index && r.header_unchanged == false,
              "changed header preserves literal AL even without a match");
    }
    {
      Memory m;
      m.final_count = 0;
      m.final_buffer += 8;
      const auto in = m.inputs();
      const auto r = ReadConstructionCollectionPredicateA11CC0V1(
          m.access(), in, m.collection(), in.first_pointer);
      require(r.value == false && r.first_match_index == std::uint32_t{1} &&
              r.found_pointer == r.reloaded_end_pointer && r.header_unchanged == false,
              "matched pointer equal to reloaded end produces literal false");
    }
    {
      Memory m;
      m.initial_count = 1;
      m.final_count = -1;
      m.final_buffer = m.initial_buffer + 16;
      const auto in = m.inputs();
      const auto r = ReadConstructionCollectionPredicateA11CC0V1(
          m.access(), in, m.collection(), in.first_pointer);
      require(r.value == false && r.reloaded_count_raw == -1 &&
              r.reloaded_end_pointer == r.initial_end_pointer,
              "negative reloaded count is literal address arithmetic");
    }
    {
      Memory m;
      m.final_count = 1;
      m.final_buffer = std::numeric_limits<std::uintptr_t>::max() - 7;
      const auto in = m.inputs();
      const auto r = ReadConstructionCollectionPredicateA11CC0V1(
          m.access(), in, m.collection(), in.first_pointer);
      require(r.value == true && r.reloaded_end_pointer == std::uintptr_t{0} &&
              r.failure == CollectionPredicateA11CC0FailureV1::none,
              "final LEA address wrap is preserved without dereference");
    }
    {
      Memory m;
      m.deny_final_count = true;
      const auto in = m.inputs();
      const auto r = ReadConstructionCollectionPredicateA11CC0V1(
          m.access(), in, m.collection(), in.first_pointer);
      require(!r.value && r.ordered_qwords_complete && !r.reloaded_count_raw &&
              r.failure == CollectionPredicateA11CC0FailureV1::reloaded_count,
              "missing final header prevents AL rather than repairing it");
    }
    {
      Memory m;
      const auto in = m.inputs();
      ConstructionCollectionPredicateA11CC0V1 trace;
      CollectionPredicateA11CC0ReadContextV1 context{4096, &trace};
      bool value = true;
      require(!ReadConstructionCollectionPredicateA11CC0ChildV1(
                  &context, m.access(), in, m.collection(), in.first_pointer + 8, value) &&
              value && trace.failure == CollectionPredicateA11CC0FailureV1::copied_key_binding,
              "adapter unavailable leaves bool output and rejects observer key alias");
      m.initial_count = m.final_count = 1;
      require(ReadConstructionCollectionPredicateA11CC0ChildV1(
                  &context, m.access(), in, m.collection(), in.first_pointer, value) &&
              !value && trace.value == false,
              "adapter observed false differs from callback unavailable");
    }
    {
      Memory m;
      m.initial_count = 1;
      m.initial_buffer = 0;
      const auto in = m.inputs();
      const auto r = ReadConstructionCollectionPredicateA11CC0V1(
          m.access(), in, m.collection(), in.first_pointer);
      require(!r.value && r.initial_buffer_pointer == std::uintptr_t{0} &&
              r.failure == CollectionPredicateA11CC0FailureV1::array_pointer,
              "positive null array is unavailable rather than empty");
    }
    {
      Memory m;
      m.initial_count = 2;
      m.initial_buffer = std::numeric_limits<std::uintptr_t>::max() - 7;
      const auto in = m.inputs();
      const auto r = ReadConstructionCollectionPredicateA11CC0V1(
          m.access(), in, m.collection(), in.first_pointer);
      require(!r.value && r.initial_count_raw == 2 &&
              r.failure == CollectionPredicateA11CC0FailureV1::initial_extent_overflow,
              "unrepresentable initial read extent is unavailable");
    }
    {
      Memory m;
      const auto in = m.inputs();
      auto access = m.access();
      access.exact_12004_bound = false;
      const auto r = ReadConstructionCollectionPredicateA11CC0V1(
          access, in, m.collection(), in.first_pointer);
      require(!r.value && m.count_reads == 0 &&
              r.failure == CollectionPredicateA11CC0FailureV1::exact_build,
              "unbound exact build does not read memory");
      m.throw_reader = true;
      const auto thrown = ReadConstructionCollectionPredicateA11CC0V1(
          m.access(), in, m.collection(), in.first_pointer);
      require(!thrown.value &&
              thrown.failure == CollectionPredicateA11CC0FailureV1::header_count,
              "read callback exception remains unavailable");
    }
    failure.clear();
    return true;
  } catch (const std::exception &error) {
    failure = std::string("27c A11CC0: ") + error.what();
  } catch (...) {
    failure = "27c A11CC0 unexpected copied-case failure";
  }
  return false;
}
