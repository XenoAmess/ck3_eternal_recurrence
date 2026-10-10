#include "xar_bridge/loaded_singleton_d2be00_12004.hpp"
#include "xar_bridge/construction_context_predicate_2c25010_12004.hpp"
#include <cstring>
#include <stdexcept>

namespace {
using namespace xar::ck3_12004::construction_owner_mode3;
struct OwnedSingletonSlot {
  std::uintptr_t address = 0;
  std::uintptr_t pointer = 0;
  std::size_t read_count = 0;
  bool readable = true;
  static bool Read(void *context, const void *source, void *output, std::size_t bytes) {
    auto &self = *static_cast<OwnedSingletonSlot *>(context);
    ++self.read_count;
    if (!self.readable || reinterpret_cast<std::uintptr_t>(source) != self.address
        || bytes != sizeof(self.pointer)) return false;
    std::memcpy(output, &self.pointer, bytes);
    return true;
  }
};
void Require(bool condition, const char *reason) {
  if (!condition) throw std::runtime_error(reason);
}
} // namespace

// Sole fresh 03/10 compound export. No main, native getter, diagnostic or old case.
void RunLoadedD2BE00SingletonNewCase12004() {
  constexpr std::uintptr_t image = 0x100000000ULL;
  constexpr std::uintptr_t singleton = 0x12345000;
  OwnedSingletonSlot memory{image + kLoadedSingletonSlotRva12004, singleton};
  RawReceiverAccessV1 access;
  access.context = &memory;
  access.read_memory = &OwnedSingletonSlot::Read;
  access.module_base = image;
  access.exact_12004_bound = true;
  const auto loaded = ReadLoadedD2BE00Singleton12004(access, 77);
  Require(loaded.source_ready && loaded.frame_key == 77
      && loaded.singleton_slot_raw == singleton
      && loaded.nonnull_branch_admitted == true
      && loaded.conditional_return_pointer == singleton && memory.read_count == 1
      && !loaded.native_function_invoked && !loaded.diagnostic_or_initializer_invoked,
      "loaded singleton must preserve one guarded source-slot copy in its supplied frame");
  ContextPredicateInputsV1 inputs;
  inputs.frame_key = 77;
  inputs.first_pointer = 0x123;
  inputs.raw_receiver_pointer = 0x456;
  inputs.selector_object_pointer = 0x789;
  std::uintptr_t copied_return = 0xAA;
  Require(ReadLoadedD2BE00ContextChild12004(nullptr, access, inputs, copied_return)
      && copied_return == singleton, "21c child must receive the copied loaded branch return");
  memory.pointer = 0;
  const auto empty = ReadLoadedD2BE00Singleton12004(access, 78);
  Require(empty.singleton_slot_raw == 0 && empty.nonnull_branch_admitted == false
      && !empty.source_ready && !empty.conditional_return_pointer
      && empty.failure == LoadedSingletonFailure12004::singleton_not_loaded
      && !empty.native_function_invoked && !empty.diagnostic_or_initializer_invoked,
      "readable zero must stay raw and cannot become a fabricated post-diagnostic return");
  copied_return = 0xAA;
  Require(!ReadLoadedD2BE00ContextChild12004(nullptr, access, inputs, copied_return)
      && copied_return == 0xAA, "unloaded 21c child must preserve unavailable output");
  memory.readable = false;
  const auto unreadable = ReadLoadedD2BE00Singleton12004(access, 79);
  Require(!unreadable.singleton_slot_raw && !unreadable.nonnull_branch_admitted
      && !unreadable.source_ready && !unreadable.conditional_return_pointer,
      "missing singleton source must not become a copied null or initialized object");
  access.exact_12004_bound = false;
  const auto previous_reads = memory.read_count;
  const auto wrong_build = ReadLoadedD2BE00Singleton12004(access, 80);
  Require(wrong_build.failure == LoadedSingletonFailure12004::exact_build
      && !wrong_build.singleton_slot_raw && memory.read_count == previous_reads,
      "unbound image must fail before reading singleton memory");
}
