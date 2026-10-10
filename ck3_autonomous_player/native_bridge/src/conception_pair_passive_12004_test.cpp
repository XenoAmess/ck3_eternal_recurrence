#include "xar_bridge/conception_pair_passive_12004.hpp"
#include "xar_bridge/conception_pair_threshold_consumer_12004.hpp"
#include "xar_bridge/ck3_12004.hpp"

#include <array>
#include <cstring>
#include <iostream>
#include <stdexcept>

namespace xar::ck3_12004 {
namespace {
constexpr std::uintptr_t kOwnedBase = 0x180000000ULL;
constexpr std::uint64_t kAcceptedRax = 0xA4B3C2D1E0F98701ULL;
constexpr std::uint64_t kRejectedRax = 0xABCDEFA0B1234500ULL;
struct Owned {
  std::array<std::byte, 0x1B8> first{}, second{};
  std::array<std::byte, 0x3F8> first_extended{}, second_extended{};
  std::array<std::uint32_t, 2> sample_state{17, 61};
  std::int64_t provider_output = 0;
  std::int64_t scalar = 100000, lower = 0, upper = 10000000;
  std::uint32_t parent_calls = 0, provider_calls = 0, sample_calls = 0;
  std::uint64_t reads = 0;
};
Owned *g_owned = nullptr;
template <std::size_t N, typename T>
void Store(std::array<std::byte, N> &memory, std::size_t offset, T value) {
  std::memcpy(memory.data() + offset, &value, sizeof(value));
}
void Require(bool condition, const char *reason) {
  if (!condition) throw std::runtime_error(reason);
}
template <typename T>
bool Contains(const T &memory, std::uintptr_t address, std::size_t bytes) noexcept {
  const auto begin = reinterpret_cast<std::uintptr_t>(&memory);
  return address >= begin && address - begin <= sizeof(memory) &&
      bytes <= sizeof(memory) - static_cast<std::size_t>(address - begin);
}
bool ReadOwned(void *context, const void *address, void *output,
               std::size_t bytes) noexcept {
  auto &memory = *static_cast<Owned *>(context);
  ++memory.reads;
  const auto raw = reinterpret_cast<std::uintptr_t>(address);
  if (raw == kOwnedBase + 0x5C69EC8 && bytes == 8) {
    std::memcpy(output, &memory.scalar, bytes); return true;
  }
  if (raw == kOwnedBase + 0x5C69F00 && bytes == 8) {
    std::memcpy(output, &memory.lower, bytes); return true;
  }
  if (raw == kOwnedBase + 0x5C69F10 && bytes == 8) {
    std::memcpy(output, &memory.upper, bytes); return true;
  }
  if (!(Contains(memory.first, raw, bytes) || Contains(memory.second, raw, bytes) ||
        Contains(memory.first_extended, raw, bytes) || Contains(memory.second_extended, raw, bytes) ||
        Contains(memory.sample_state, raw, bytes) || Contains(memory.provider_output, raw, bytes)))
    return false;
  std::memcpy(output, address, bytes);
  return true;
}
void *__fastcall ProviderOriginal(void *output, void *first, void *second,
                                   std::uint32_t mode, void *fifth) {
  auto &owned = *g_owned;
  ++owned.provider_calls;
  Require(output == &owned.provider_output && first == owned.first.data() &&
      second == owned.second.data() && mode == 3 && fifth == nullptr,
      "provider original arguments changed");
  *static_cast<std::int64_t *>(output) = 3000000;
  return output;
}
std::int64_t __fastcall SampleOriginal(void *receiver, std::int64_t lower,
                                      std::int64_t upper) {
  auto &owned = *g_owned;
  ++owned.sample_calls;
  Require(receiver == owned.sample_state.data() && lower == 0 && upper == 10000000,
      "sample original arguments changed");
  auto *state = static_cast<std::uint32_t *>(receiver);
  state[0] += 2;
  return 1000000;
}
std::uint64_t __fastcall PairOriginal(void *first, void *second,
                                     void *sample_receiver, std::int64_t modifier) {
  auto &owned = *g_owned;
  ++owned.parent_calls;
  Require(first == owned.first.data() && second == owned.second.data() &&
      sample_receiver == owned.sample_state.data(), "parent original arguments changed");
  ConceptionSampleParentScope12004 parent;
  Require(ReadConceptionPairParentScope12004(nullptr, parent) && parent.active &&
      parent.first_character == reinterpret_cast<std::uintptr_t>(first) &&
      parent.second_character == reinterpret_cast<std::uintptr_t>(second) &&
      parent.first_full_id == 38718 && parent.second_full_id == 38822 &&
      parent.sample_receiver == reinterpret_cast<std::uintptr_t>(sample_receiver),
      "natural original did not have its actual native-oriented parent extent");
  if (modifier == -1) return kRejectedRax;
  Require(modifier == 100000, "parent original R9 modifier changed");
  Require(InvokeConceptionPairProviderFixture12004(0x2929C30,
      &owned.provider_output, first, second, 3, nullptr) == &owned.provider_output,
      "provider original return bits changed");
  Require(InvokeConceptionSampleFixture12004(0x2929D99, sample_receiver,
      0, 10000000, std::int64_t{3000000}) == 1000000,
      "sample original return changed");
  // This owned stand-in original writes its own source memory. The observer
  // only copies it; no CK3 body, candidate or RNG is called or replayed.
  Store(owned.first_extended, 0x3E8, std::uint8_t{1});
  Store(owned.first_extended, 0x3F0, reinterpret_cast<std::uintptr_t>(second));
  return kAcceptedRax;
}
ConceptionThresholdParentKey12004 Key(const ConceptionPairPassiveEvent12004 &event) {
  return {event.before_event.clock_identity, event.before_event.sequence,
      event.before_event.sequence, event.thread_id, event.first_character,
      event.second_character, *event.first_before.full_id,
      *event.second_before.full_id, event.sample_receiver, event.source_pin};
}
ConceptionThresholdInputs12004 Inputs(const ConceptionPairPassiveEvent12004 &event) {
  ConceptionThresholdInputs12004 input;
  input.executable_sha256 = kExecutableSha256;
  input.parent = Key(event);
  input.provider_first_qword = {event.provider->output_after, input.parent,
      event.provider->actual_caller_input_ready};
  input.sample = {event.sample->returned_rax, input.parent, event.sample->causal_sample_ready};
  input.original_comparison_threshold = {event.sample->threshold_at_sample,
      input.parent, event.sample->threshold_capture_ready};
  input.monthly_scalar = {event.source_before.scalar_5c69ec8_raw, input.parent, false};
  input.lower_clamp = {event.source_before.lower_5c69f00_raw, input.parent, false};
  input.upper_clamp = {event.source_before.upper_5c69f10_raw, input.parent, false};
  input.original_r9_modifier = {event.original_r9_modifier, input.parent, true};
  input.completion = ConceptionThresholdCompletion12004{input.parent,
      event.original_called_once, event.original_returned, event.original_al,
      event.generation_unchanged, event.first_before.extended_pointer,
      event.first_after.extended_pointer, event.first_after.pending_3e8_raw,
      event.first_after.pending_3f0_raw};
  return input;
}
}

bool RunConceptionPairPassiveOwnedFixture12004() noexcept {
  try {
    Owned owned;
    g_owned = &owned;
    const auto first_extended = reinterpret_cast<std::uintptr_t>(owned.first_extended.data());
    const auto second_extended = reinterpret_cast<std::uintptr_t>(owned.second_extended.data());
    Store(owned.first, 0x18, std::uint32_t{38718});
    Store(owned.second, 0x18, std::uint32_t{38822});
    Store(owned.first, 0x1C, std::uint32_t{0x43686172U});
    Store(owned.second, 0x1C, std::uint32_t{0x43686172U});
    Store(owned.first, 0x1A1, std::uint8_t{1});
    Store(owned.second, 0x1A1, std::uint8_t{0});
    Store(owned.first, 0x1B0, first_extended);
    Store(owned.second, 0x1B0, second_extended);

    auto parent_bindings = BindConceptionPairPassiveImage12004(
        kOwnedBase, kExecutableSha256, ReadOwned, &owned);
    auto provider_bindings = BindConceptionPairProviderImage12004(kOwnedBase, kExecutableSha256);
    provider_bindings.read_memory = ReadOwned;
    provider_bindings.read_context = &owned;
    provider_bindings.read_parent = ReadConceptionPairParentScope12004;
    provider_bindings.child_return = AttachConceptionPairProviderFacts12004;
    auto sample_bindings = BindConceptionSampleImage12004(kOwnedBase, kExecutableSha256);
    sample_bindings.read_memory = ReadOwned;
    sample_bindings.read_context = &owned;
    sample_bindings.read_parent = ReadConceptionPairParentScope12004;
    sample_bindings.child_return = AttachConceptionPairSampleFacts12004;
    Require(InitializeConceptionPairProviderFixture12004(provider_bindings, ProviderOriginal),
        "provider fixture original unavailable");
    Require(InitializeConceptionSampleFixture12004(sample_bindings, SampleOriginal),
        "sample fixture original unavailable");
    Require(InitializeConceptionPairPassiveFixture12004(parent_bindings, PairOriginal),
        "pair fixture original unavailable");
    ConceptionSampleParentScope12004 inactive;
    Require(!ReadConceptionPairParentScope12004(nullptr, inactive), "parent active outside original");
    Require(InvokeConceptionPairPassiveFixture12004(kOwnedBase + 0x11111,
        owned.first.data(), owned.second.data(), owned.sample_state.data(), 100000) == kAcceptedRax,
        "parent full RAX bits changed");
    Require(owned.parent_calls == 1 && owned.provider_calls == 1 && owned.sample_calls == 1,
        "connected parent/provider/sample original call count differs from one each");
    Require(!ReadConceptionPairParentScope12004(nullptr, inactive), "parent extent leaked after original");
    auto journal = ReadConceptionPairPassiveForPair12004(38822, 38718);
    Require(journal && journal->events.size() == 1, "same-household opposite orientation lost parent");
    const auto event = journal->events[0];
    Require(event.first_before.full_id == 38718 && event.second_before.full_id == 38822 &&
        event.original_rax_bits == kAcceptedRax && event.original_al == 1 &&
        event.generation_unchanged == true && event.first_post_pending_matches_write_pattern == true &&
        event.provider && event.provider->actual_caller_input_ready &&
        event.sample && event.sample->causal_sample_ready && event.event_clock_and_thread_match,
        "connected actual original facts are incomplete");
    Require(event.provider->parent.parent_scope_id == event.before_event.sequence &&
        event.sample->parent.parent_scope_id == event.before_event.sequence &&
        event.provider->parent.clock_identity == event.before_event.clock_identity &&
        event.sample->parent.clock_identity == event.before_event.clock_identity &&
        event.provider->returned_event.sequence < event.sample->before_event.sequence &&
        event.sample->returned_event.sequence < event.completed_event.sequence,
        "child facts failed shared parent/process-clock ordering");
    const auto threshold = EvaluateConceptionThreshold12004(Inputs(event));
    Require(threshold.conditional_available && threshold.conditional_accepts == true &&
        threshold.threshold_raw == 3000000 && threshold.native_parent_accepted == true &&
        threshold.observed_write_pair_matches == true && !threshold.accepted_causal &&
        threshold.original_compare_available && threshold.original_threshold_raw == 3000000 &&
        threshold.original_sample_below_threshold == true && threshold.original_compare_causal &&
        threshold.non_consumed_original_inputs_mask ==
            (conception_threshold_scalar | conception_threshold_lower | conception_threshold_upper),
        "bookend values were upgraded to actual consumed inputs");
    const auto read_count = owned.reads;
    auto filtered = ReadConceptionPairPassiveForPair12004(38822, 38718, event.journal_sequence);
    Require(filtered && filtered->events.empty() && owned.reads == read_count &&
        filtered->latest_sequence == journal->latest_sequence,
        "journal query performed a new source read or event capture");

    // The rejected invocation starts with the old pending pattern still present.
    // A copied pattern does not override the actual returned AL0.
    Require(InvokeConceptionPairPassiveFixture12004(kOwnedBase + 0x22222,
        owned.first.data(), owned.second.data(), owned.sample_state.data(), -1) == kRejectedRax,
        "rejected parent RAX bits changed");
    journal = ReadConceptionPairPassiveForPair12004(38822, 38718);
    Require(journal && journal->events.size() == 2 &&
        journal->events[1].original_al == 0 &&
        journal->events[1].first_post_pending_matches_write_pattern == true &&
        !journal->events[1].provider && !journal->events[1].sample &&
        owned.parent_calls == 2 && owned.provider_calls == 1 && owned.sample_calls == 1,
        "rejected parent was conflated with stale pending pattern or child execution");
    std::cout << SerializeConceptionPairPassiveJournal12004(*journal) << '\n';
    g_owned = nullptr;
    return true;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    g_owned = nullptr;
    return false;
  }
}
} // namespace xar::ck3_12004
