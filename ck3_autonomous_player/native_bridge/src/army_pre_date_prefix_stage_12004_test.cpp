#include "xar_bridge/army_pre_date_prefix_stage_12004.hpp"

#include <cstring>
#include <iostream>
#include <limits>
#include <stdexcept>

namespace stage = xar::ck3_12004::army_pre_date_prefix_stage;

namespace {
struct SyntheticMemory {
  std::uintptr_t primary = 0x10000;
  std::int32_t count = 0;
  int reads = 0;
  bool fail = false;
};

bool ReadSynthetic(void *context, std::uintptr_t address,
    void *destination, std::size_t count) {
  auto &memory = *static_cast<SyntheticMemory *>(context);
  ++memory.reads;
  if (address != memory.primary + stage::kSourceCountOffset ||
      count != sizeof(memory.count)) {
    throw std::runtime_error("Undemanded queue/date/roster read or wrong source offset");
  }
  if (memory.fail) return false;
  std::memcpy(destination, &memory.count, sizeof(memory.count));
  return true;
}

void Require(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}
} // namespace

int main() {
  int cases = 0;
  for (const auto count : {std::int32_t{0}, std::int32_t{-1},
                           std::numeric_limits<std::int32_t>::min()}) {
    SyntheticMemory memory{};
    memory.count = count;
    const auto frame = stage::ObserveCurrentHeader(stage::kExecutableSha256,
        memory.primary, ReadSynthetic, &memory);
    const auto result = stage::ProjectCurrentHeader(frame);
    Require(memory.reads == 1, "No-work arm must read only primaryD4 once");
    Require(frame.source_count_d4 == count, "Signed raw count must survive observation");
    Require(result.verdict == stage::Verdict::no_work && result.complete_no_work_arm &&
        result.primary_state_preserved_by_prefix, "Nonpositive arm must preserve state");
    Require(!result.historical_invocation_reconstructed, "Current header is not old CALL evidence");
    ++cases;
  }
  for (const auto count : {std::int32_t{1},
                           std::numeric_limits<std::int32_t>::max()}) {
    SyntheticMemory memory{};
    memory.count = count;
    const auto result = stage::ProjectCurrentHeader(stage::ObserveCurrentHeader(
        stage::kExecutableSha256, memory.primary, ReadSynthetic, &memory));
    Require(memory.reads == 1 && result.source_count_ready, "Positive header is independently ready");
    Require(result.verdict == stage::Verdict::positive_occurrence_inputs_required &&
        !result.complete_no_work_arm && !result.primary_state_preserved_by_prefix,
        "Positive arm needs actual ordered occurrence/stage inputs");
    Require(!result.historical_invocation_reconstructed, "Positive header is not old CALL evidence");
    ++cases;
  }
  {
    SyntheticMemory memory{};
    memory.fail = true;
    const auto frame = stage::ObserveCurrentHeader(stage::kExecutableSha256,
        memory.primary, ReadSynthetic, &memory);
    const auto result = stage::ProjectCurrentHeader(frame);
    Require(memory.reads == 1 && !frame.source_count_d4 &&
        result.verdict == stage::Verdict::unavailable && !result.complete_no_work_arm,
        "Failed raw read must remain absent, without retry or fabricated zero");
    ++cases;
  }
  {
    SyntheticMemory memory{};
    const auto result = stage::ProjectCurrentHeader(stage::ObserveCurrentHeader(
        "old-or-wrong-build", memory.primary, ReadSynthetic, &memory));
    Require(memory.reads == 0 && result.verdict == stage::Verdict::unavailable,
        "Wrong build must not invoke raw memory reader");
    ++cases;
  }
  {
    SyntheticMemory memory{};
    const auto result = stage::ProjectCurrentHeader(stage::ObserveCurrentHeader(
        stage::kExecutableSha256, 0, ReadSynthetic, &memory));
    Require(memory.reads == 0 && result.verdict == stage::Verdict::unavailable,
        "Missing primary must not read a guessed receiver");
    ++cases;
  }
  {
    SyntheticMemory memory{};
    const auto result = stage::ProjectCurrentHeader(stage::ObserveCurrentHeader(
        stage::kExecutableSha256, std::numeric_limits<std::uintptr_t>::max(),
        ReadSynthetic, &memory));
    Require(memory.reads == 0 && result.verdict == stage::Verdict::unavailable,
        "Overflowing source address must not become a wrapped receiver");
    ++cases;
  }
  std::cout << "SYNTHETIC conditional prefix header cases=" << cases
            << "; historical CALL evidence=0; game execution=0\n";
}
