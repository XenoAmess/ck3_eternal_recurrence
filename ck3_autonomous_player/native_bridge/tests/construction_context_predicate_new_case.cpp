#include "xar_bridge/construction_context_predicate_2c25010_12004.hpp"

#include <cstring>
#include <string>
#include <unordered_map>

namespace xar::ck3_12004::construction_owner_mode3 {
namespace {
struct PredicateFixture {
  static constexpr std::uintptr_t module = 0x100000000ULL;
  static constexpr std::uintptr_t slots = 0x200000;
  static constexpr std::uintptr_t first = 0x210000;
  static constexpr std::uintptr_t receiver = 0x220000;
  static constexpr std::uintptr_t selector = 0x230000;
  static constexpr std::uintptr_t storage = 0x240000;
  static constexpr std::uintptr_t table = 0x250000;
  static constexpr std::uintptr_t candidate = 0x260000;
  static constexpr std::uintptr_t fallback = 0x270000;
  static constexpr std::uintptr_t late_receiver = 0x280000;
  static constexpr std::uintptr_t late_context = 0x290000;
  static constexpr std::uintptr_t singleton = 0x2A0000;
  static constexpr std::uint64_t frame = 19;
  std::unordered_map<std::uintptr_t, unsigned char> bytes;
  bool first_value = false;
  bool membership_value = false;
  bool last_value = true;
  bool first_available = true;
  bool membership_available = true;
  std::uintptr_t expected_collection = candidate + 0x8D8;
  unsigned first_calls = 0, membership_calls = 0, late_calls = 0;
  unsigned singleton_calls = 0, last_calls = 0, reads = 0;
  bool arguments_match = true;

  template<class T> void Put(std::uintptr_t address, T value) {
    const auto *data = reinterpret_cast<const unsigned char *>(&value);
    for (std::size_t i = 0; i < sizeof(value); ++i) bytes[address + i] = data[i];
  }
  PredicateFixture() {
    Put(slots, first);
    Put(module + 0x5D1E2F8, storage);
    Put(receiver + 0xB4, std::uint32_t{0xA1000002u});
    Put(storage + 0x2C, std::uint32_t{3});
    Put(storage + 0x20, table);
    Put(table + 2 * 16 + 8, candidate);
    Put(candidate + 8, std::uint32_t{0xA1000002u});
    Put(module + 0x5C67670, fallback);
    Put(late_receiver + 0x1C0, late_context);
    Put(late_context + 0x1B8, std::uint32_t{0x82000007u});
    Put(receiver + 0x18, std::uint32_t{0x82000007u});
  }
  bool Inputs(const ContextPredicateInputsV1 &in) {
    return in.frame_key == frame && in.slots_pointer == slots &&
           in.first_pointer == first && in.raw_receiver_pointer == receiver &&
           in.selector_object_pointer == selector;
  }
};

bool Copy(void *opaque, const void *pointer, void *output, std::size_t size) {
  auto &f = *static_cast<PredicateFixture *>(opaque);
  ++f.reads;
  const auto address = reinterpret_cast<std::uintptr_t>(pointer);
  auto *data = static_cast<unsigned char *>(output);
  for (std::size_t i = 0; i < size; ++i) {
    const auto it = f.bytes.find(address + i);
    if (it == f.bytes.end()) return false;
    data[i] = it->second;
  }
  return true;
}
bool First(void *opaque, const RawReceiverAccessV1 &,
           const ContextPredicateInputsV1 &in, std::uintptr_t rcx,
           std::uintptr_t rdx, bool &value) noexcept {
  auto &f = *static_cast<PredicateFixture *>(opaque);
  ++f.first_calls;
  f.arguments_match &= f.Inputs(in) && rcx == f.selector && rdx == f.first;
  value = f.first_value;
  return f.first_available;
}
bool Membership(void *opaque, const RawReceiverAccessV1 &,
                const ContextPredicateInputsV1 &in, std::uintptr_t rcx,
                std::uintptr_t key_value, bool &value) noexcept {
  auto &f = *static_cast<PredicateFixture *>(opaque);
  ++f.membership_calls;
  f.arguments_match &= f.Inputs(in) && rcx == f.expected_collection &&
                       key_value == f.first;
  value = f.membership_value;
  return f.membership_available;
}
bool Late(void *opaque, const RawReceiverAccessV1 &,
          const ContextPredicateInputsV1 &in, std::uintptr_t rcx,
          std::uintptr_t &value) noexcept {
  auto &f = *static_cast<PredicateFixture *>(opaque);
  ++f.late_calls;
  f.arguments_match &= f.Inputs(in) && rcx == f.receiver;
  value = f.late_receiver;
  return true;
}
bool Singleton(void *opaque, const RawReceiverAccessV1 &,
               const ContextPredicateInputsV1 &in,
               std::uintptr_t &value) noexcept {
  auto &f = *static_cast<PredicateFixture *>(opaque);
  ++f.singleton_calls;
  f.arguments_match &= f.Inputs(in);
  value = f.singleton;
  return true;
}
bool Last(void *opaque, const RawReceiverAccessV1 &,
          const ContextPredicateInputsV1 &in, std::uintptr_t rcx,
          std::uintptr_t rdx, bool &value) noexcept {
  auto &f = *static_cast<PredicateFixture *>(opaque);
  ++f.last_calls;
  f.arguments_match &= f.Inputs(in) && rcx == f.singleton && rdx == f.first;
  value = f.last_value;
  return true;
}
ConstructionContextPredicateV1 Run(PredicateFixture &f,
                                  bool selector_matches = true) {
  RawReceiverAccessV1 access{&f, Copy, f.module, true};
  AggregateRawReceiverV1 receiver{};
  receiver.observed = true;
  receiver.slots_pointer = f.slots;
  receiver.returned_receiver_pointer = f.receiver;
  ReturnedObject28C2DF0Result12004 selector{};
  selector.input_receiver = f.receiver;
  selector.frame_key = selector_matches ? f.frame : f.frame + 1;
  selector.returned_object = f.selector;
  selector.source_ready = true;
  ReadContextPredicateChildrenV1 children{&f, First, Membership, Late,
                                        Singleton, Last};
  return ReadConstructionContextPredicate2C25010V1(
      access, receiver, selector, f.frame, children);
}
} // namespace

// No main: only the new 03/10 actual compound fixture invokes this export.
// Synthetic child results exercise this leaf's 205-byte control flow; they
// do not qualify the separate child memory models or a native runtime.
bool ExerciseConstructionContextPredicate2C25010NewCaseV1(std::string &failure) {
  const auto require = [&](bool ok, const char *message) {
    if (!ok) failure = message;
    return ok;
  };
  {
    PredicateFixture f;
    f.first_value = true;
    const auto r = Run(f);
    if (!require(r.value == true && r.path == ContextPredicatePathV1::first_child_true &&
                 f.arguments_match && f.reads == 1 && f.membership_calls == 0 &&
                 f.late_calls == 0, "first true preserves actual operands and short circuit")) return false;
  }
  {
    PredicateFixture f;
    f.membership_value = true;
    const auto r = Run(f);
    if (!require(r.value == true && r.registry_full_id_matched &&
                 r.registry_full_id_raw == 0xA1000002u && f.arguments_match &&
                 f.late_calls == 0, "full uint32 generation match and collection short circuit")) return false;
  }
  {
    PredicateFixture f;
    f.Put(f.candidate + 8, std::uint32_t{0xA2000002u});
    f.expected_collection = f.fallback + 0x8D8;
    f.membership_value = true;
    const auto r = Run(f);
    if (!require(r.value == true && !r.registry_full_id_matched &&
                 r.selected_registry_object_pointer == f.fallback &&
                 f.arguments_match, "same low24 stale generation selects actual fallback")) return false;
  }
  {
    PredicateFixture f;
    f.Put(f.module + 0x5D1E2F8, std::uintptr_t{0});
    f.expected_collection = f.fallback + 0x8D8;
    f.membership_value = true;
    const auto r = Run(f);
    if (!require(r.value == true && !r.registry_full_id_raw.has_value() &&
                 f.arguments_match, "null storage bypasses receiver B4 ID read")) return false;
  }
  {
    PredicateFixture f;
    f.Put(f.late_context + 0x1B8, std::uint32_t{0x83000007u});
    const auto r = Run(f);
    if (!require(r.value == false &&
                 r.path == ContextPredicatePathV1::late_id_mismatch_false &&
                 f.singleton_calls == 0 && f.last_calls == 0 && f.arguments_match,
                 "different full late ID returns false without singleton or final child")) return false;
  }
  {
    PredicateFixture f;
    f.Put(f.late_receiver + 0x1C0, std::uintptr_t{0});
    f.Put(f.receiver + 0x18, std::uint32_t{0xFFFFFFFFu});
    const auto r = Run(f);
    if (!require(r.value == true && r.late_context_id_raw == 0xFFFFFFFFu &&
                 r.raw_receiver_id_raw == 0xFFFFFFFFu && f.last_calls == 1 &&
                 f.arguments_match, "native null context minus-one branch can match all-ones ID")) return false;
  }
  {
    PredicateFixture f;
    f.last_value = false;
    const auto r = Run(f);
    if (!require(r.value == false && r.path == ContextPredicatePathV1::last_child_false &&
                 f.last_calls == 1 && f.arguments_match, "known final child false remains known false")) return false;
  }
  {
    PredicateFixture f;
    f.membership_available = false;
    const auto r = Run(f);
    if (!require(!r.value.has_value() &&
                 r.failure == ContextPredicateFailureV1::child_a11cc0 &&
                 f.late_calls == 0, "missing reached child remains unknown and does not evaluate later branch")) return false;
  }
  {
    PredicateFixture f;
    const auto r = Run(f, false);
    if (!require(!r.value.has_value() &&
                 r.failure == ContextPredicateFailureV1::copied_operand_binding &&
                 f.reads == 0 && f.first_calls == 0,
                 "different selector snapshot rejects attribution before memory or child work")) return false;
  }
  failure.clear();
  return true;
}
} // namespace xar::ck3_12004::construction_owner_mode3
