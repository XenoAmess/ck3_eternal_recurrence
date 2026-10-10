#include "xar_bridge/conception_extended_gate_12004.hpp"
#include "xar_bridge/ck3_12004.hpp"

#include <array>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <utility>
#include <vector>

namespace {

using namespace xar::ck3_12004;
struct OwnedMemory {
  std::array<std::byte, 0x1B8> first{};
  std::array<std::byte, 0x1B8> second{};
  std::array<std::byte, 0x290> first_extended{};
  std::array<std::byte, 0x290> second_extended{};
  std::uintptr_t denied = 0;
  std::vector<std::pair<std::uintptr_t, std::size_t>> copies;
};

template <std::size_t N, typename T>
void Store(std::array<std::byte, N> &memory, std::size_t offset, T value) {
  std::memcpy(memory.data() + offset, &value, sizeof(value));
}

template <std::size_t N>
bool Contains(const std::array<std::byte, N> &memory,
              std::uintptr_t address, std::size_t size) {
  const auto begin = reinterpret_cast<std::uintptr_t>(memory.data());
  return address >= begin && address - begin <= N &&
      size <= N - static_cast<std::size_t>(address - begin);
}

bool CopyOwned(void *context, const void *address, void *output,
               std::size_t size) noexcept {
  auto &memory = *static_cast<OwnedMemory *>(context);
  const auto raw = reinterpret_cast<std::uintptr_t>(address);
  memory.copies.emplace_back(raw, size);
  if (raw == memory.denied ||
      !(Contains(memory.first, raw, size) || Contains(memory.second, raw, size) ||
        Contains(memory.first_extended, raw, size) ||
        Contains(memory.second_extended, raw, size))) return false;
  std::memcpy(output, address, size);
  return true;
}

void Require(bool condition, const char *reason) {
  if (!condition) throw std::runtime_error(reason);
}

void RequireCopyPlan(const OwnedMemory &memory, std::uintptr_t character,
                     std::uintptr_t extended) {
  const std::vector<std::pair<std::uintptr_t, std::size_t>> expected =
      extended == 0 ?
      std::vector<std::pair<std::uintptr_t, std::size_t>>{
          {character + 0x1C, 4}, {character + 0x18, 4},
          {character + 0x1B0, 8}} :
      std::vector<std::pair<std::uintptr_t, std::size_t>>{
          {character + 0x1C, 4}, {character + 0x18, 4},
          {character + 0x1B0, 8}, {extended + 0x288, 8}};
  Require(memory.copies == expected,
          "copy widths/addresses differ from the qualified gate operands");
}

void RunOwnedMemoryCheck() {
  OwnedMemory memory;
  const auto first = reinterpret_cast<std::uintptr_t>(memory.first.data());
  const auto second = reinterpret_cast<std::uintptr_t>(memory.second.data());
  const auto first_extended =
      reinterpret_cast<std::uintptr_t>(memory.first_extended.data());
  const auto second_extended =
      reinterpret_cast<std::uintptr_t>(memory.second_extended.data());
  Store(memory.first, 0x18, std::uint32_t{38822});
  Store(memory.second, 0x18, std::uint32_t{38718});
  Store(memory.first, 0x1C, std::uint32_t{0x43686172U});
  Store(memory.second, 0x1C, std::uint32_t{0x43686172U});
  Store(memory.first, 0x1B0, first_extended);
  Store(memory.second, 0x1B0, second_extended);
  // DWORD288 is zero; only the upper half makes the actual QWORD nonzero.
  constexpr std::uint64_t high_half_only = std::uint64_t{1} << 40;
  Store(memory.first_extended, 0x288, high_half_only);
  Store(memory.second_extended, 0x288, std::uint64_t{0});
  const auto original_first = memory.first;
  const auto original_second = memory.second;
  const auto original_first_extended = memory.first_extended;
  const auto original_second_extended = memory.second_extended;
  const auto bindings = BindConceptionExtendedGate12004(
      kGameVersion, kExecutableSha256, CopyOwned, &memory);
  const auto first_read = ReadConceptionExtendedGateForCharacter12004(
      bindings, first, 38822);
  Require(first_read.status == "available" &&
      first_read.extended_data_present == true &&
      first_read.extended_288_raw_u64 == high_half_only &&
      first_read.blocks_pair_conception == true,
      "first-role high-half nonzero qword did not block");
  RequireCopyPlan(memory, first, first_extended);
  memory.copies.clear();
  const auto second_read = ReadConceptionExtendedGateForCharacter12004(
      bindings, second, 38718);
  Require(second_read.status == "available" &&
      second_read.extended_data_present == true &&
      second_read.extended_288_raw_u64 == 0 &&
      second_read.blocks_pair_conception == false,
      "second-role zero qword was not an independent known-false gate");
  RequireCopyPlan(memory, second, second_extended);
  Require(memory.first == original_first && memory.second == original_second &&
      memory.first_extended == original_first_extended &&
      memory.second_extended == original_second_extended,
      "observer changed owned source memory");

  Store(memory.first, 0x1B0, std::uintptr_t{0});
  memory.copies.clear();
  const auto null_read = ReadConceptionExtendedGateForCharacter12004(
      bindings, first, 38822);
  Require(null_read.status == "available" &&
      null_read.extended_data_present == false &&
      !null_read.extended_288_raw_u64.has_value() &&
      null_read.blocks_pair_conception == false,
      "native null-extended skip was not known false");
  RequireCopyPlan(memory, first, 0);

  Store(memory.first, 0x1B0, first_extended);
  memory.denied = first_extended + 0x288;
  memory.copies.clear();
  const auto unread = ReadConceptionExtendedGateForCharacter12004(
      bindings, first, 38822);
  Require(unread.status == "unavailable" &&
      unread.unavailable_reason == "native_conception_extended_288_unread" &&
      unread.extended_data_present == true &&
      !unread.extended_288_raw_u64.has_value() &&
      !unread.blocks_pair_conception.has_value(),
      "failed qword read became a false gate");
  memory.copies.clear();
  const auto independent = ReadConceptionExtendedGateForCharacter12004(
      bindings, second, 38718);
  Require(independent.status == "available" &&
      independent.blocks_pair_conception == false,
      "first-role failure contaminated the second-role gate");
  RequireCopyPlan(memory, second, second_extended);

  memory.denied = first + 0x1B0;
  const auto pointer_unread = ReadConceptionExtendedGateForCharacter12004(
      bindings, first, 38822);
  Require(pointer_unread.status == "unavailable" &&
      pointer_unread.unavailable_reason == "native_conception_extended_pointer_unread" &&
      !pointer_unread.extended_data_present.has_value() &&
      !pointer_unread.blocks_pair_conception.has_value(),
      "failed extended pointer read became a null-extended skip");

  memory.denied = 0;
  const auto stale_identity = ReadConceptionExtendedGateForCharacter12004(
      bindings, first, 38718);
  Require(stale_identity.status == "unavailable" &&
      stale_identity.unavailable_reason ==
          "native_conception_extended_character_identity_mismatch" &&
      !stale_identity.blocks_pair_conception.has_value(),
      "mismatched household full ID yielded a gate value");
  memory.copies.clear();
  const auto wrong_build = BindConceptionExtendedGate12004(
      kGameVersion, "wrong-sha256", CopyOwned, &memory);
  const auto wrong_read = ReadConceptionExtendedGateForCharacter12004(
      wrong_build, first, 38822);
  Require(!wrong_build.enabled && wrong_read.status == "unavailable" &&
      memory.copies.empty(), "wrong exact build performed a memory read");
  Require(memory.first == original_first && memory.second == original_second &&
      memory.first_extended == original_first_extended &&
      memory.second_extended == original_second_extended,
      "failed read changed owned source memory");
}

} // namespace

int main() {
  try {
    RunOwnedMemoryCheck();
    std::cout << "{\"check\":\"conception_extended_gate_12004_owned_memory\","
        "\"status\":\"GREEN\",\"native_gate_width\":8,"
        "\"role_independent\":true,\"read_failures_distinct\":true,"
        "\"source_memory_unchanged\":true,\"game_or_sdk\":false}\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
