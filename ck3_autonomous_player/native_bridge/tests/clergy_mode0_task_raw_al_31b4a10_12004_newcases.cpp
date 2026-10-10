#include "xar_bridge/clergy_mode0_task_raw_al_31b4a10_12004.hpp"

#include <cstring>
#include <vector>

namespace {
using namespace xar::ck3_12004::religion::clergy;
constexpr std::uintptr_t kTask = 0x10000;
constexpr std::uintptr_t kType = 0x20000;
constexpr std::uintptr_t kPosition = 0x30000;
constexpr std::uintptr_t kModule = 0x140000000ULL;

struct Fixture {
  std::uint8_t initial{}, precheck{2}, final{0x80};
  bool initial_available{true}, precheck_available{true}, final_available{true};
  std::uint32_t owner{0x01000123}, incumbent{0x02000456}, compared{0x02000456};
  std::uintptr_t denied_address{};
  int initial_calls{}, precheck_calls{}, final_calls{}, literal_errors{};
  std::vector<std::uintptr_t> reads;
};

bool Memory(void *opaque, const void *raw_address, void *output,
            std::size_t size) noexcept {
  auto &f = *static_cast<Fixture *>(opaque);
  const auto address = reinterpret_cast<std::uintptr_t>(raw_address);
  f.reads.push_back(address);
  if (address == f.denied_address) return false;
  if (address == kTask + 0x18 && size == sizeof(kType)) {
    std::memcpy(output, &kType, size); return true;
  }
  if (address == kType + 0x40 && size == sizeof(kPosition)) {
    std::memcpy(output, &kPosition, size); return true;
  }
  const std::uint32_t *value = nullptr;
  if (address == kTask + 0x44) value = &f.owner;
  if (address == kTask + 0x40) value = &f.incumbent;
  if (address == kTask + 0x30) value = &f.compared;
  if (value && size == sizeof(*value)) {
    std::memcpy(output, value, size); return true;
  }
  return false;
}

bool Initial(void *opaque, std::uintptr_t task, std::uint8_t &raw) noexcept {
  auto &f = *static_cast<Fixture *>(opaque);
  ++f.initial_calls;
  if (task != kTask) { ++f.literal_errors; return false; }
  if (!f.initial_available) return false;
  raw = f.initial;
  return true;
}

bool Position(void *opaque, std::uint32_t owner, std::uintptr_t byte_input,
              std::uintptr_t predicate, std::uint8_t &raw) noexcept {
  auto &f = *static_cast<Fixture *>(opaque);
  ++f.precheck_calls;
  if (owner != f.owner || byte_input != kPosition + 0x2377 ||
      predicate != kPosition + 0x20A8) {
    ++f.literal_errors; return false;
  }
  if (!f.precheck_available) return false;
  raw = f.precheck;
  return true;
}

bool Final(void *opaque, std::uintptr_t position, std::uint32_t owner,
           std::uintptr_t task_28, std::uint32_t comparison,
           std::uintptr_t argument5, std::uint8_t &raw) noexcept {
  auto &f = *static_cast<Fixture *>(opaque);
  ++f.final_calls;
  if (position != kPosition || owner != f.owner || task_28 != kTask + 0x28 ||
      comparison != (f.compared != f.incumbent ? 1U : 0U) ||
      argument5 != kModule + kClergyMode0StaticArgumentRva12004) {
    ++f.literal_errors; return false;
  }
  if (!f.final_available) return false;
  raw = f.final;
  return true;
}

ClergyMode0TaskRawAlReaders12004 Readers(Fixture &f) {
  return {&f, Initial, &f, Position, &f, Final};
}

} // namespace

// New source-boundary compound cases only. No main, native calls, old fixture,
// game frame or appointment assertion. Root's sole new validation owns execution.
// Return value is the number of failures, so zero means success.
int RunClergyMode0TaskRawAl12004NewCases() {
  using namespace xar::ck3_12004::religion::clergy;
  int failures = 0;
  const std::vector<std::uintptr_t> field_order{
      kTask + 0x18, kTask + 0x44, kType + 0x40,
      kTask + 0x40, kTask + 0x30};
  {
    Fixture f; f.initial = 2;
    auto readers = Readers(f); readers.position = nullptr; readers.final = nullptr;
    const auto result = ReadClergyMode0TaskRawAl12004(nullptr, nullptr, kTask, 0, readers);
    failures += !(result.raw_al == 0 && f.reads.empty() &&
        f.precheck_calls == 0 && f.final_calls == 0 && !result.position);
  }
  {
    Fixture f; f.precheck = 0;
    auto readers = Readers(f); readers.final = nullptr;
    const auto result = ReadClergyMode0TaskRawAl12004(&f, Memory, kTask, 0, readers);
    failures += !(result.raw_al == 0 && f.reads == field_order &&
        f.precheck_calls == 1 && f.final_calls == 0 && f.literal_errors == 0);
  }
  {
    Fixture f;
    const auto result = ReadClergyMode0TaskRawAl12004(&f, Memory, kTask, kModule, Readers(f));
    failures += !(result.raw_al == 0x80 && result.position_raw_al == 2 &&
        f.final_calls == 1 && f.reads == field_order && f.literal_errors == 0);
  }
  {
    Fixture f; f.precheck = 255; f.final = 0; f.compared ^= 0x01000000;
    const auto result = ReadClergyMode0TaskRawAl12004(&f, Memory, kTask, kModule, Readers(f));
    failures += !(result.raw_al == 0 && result.position_raw_al == 255 &&
        result.branch == ClergyMode0TaskRawAlBranch12004::final_raw_al &&
        f.final_calls == 1 && f.literal_errors == 0);
  }
  {
    Fixture f; f.initial_available = false;
    const auto result = ReadClergyMode0TaskRawAl12004(&f, Memory, kTask, kModule, Readers(f));
    failures += !(!result.raw_al && f.reads.empty() && f.precheck_calls == 0);
  }
  {
    Fixture f; f.denied_address = kTask + 0x40;
    const auto result = ReadClergyMode0TaskRawAl12004(&f, Memory, kTask, kModule, Readers(f));
    failures += !(!result.raw_al && f.precheck_calls == 0 && f.final_calls == 0 &&
        result.failure == ClergyMode0TaskRawAlFailure12004::incumbent_raw32_unavailable);
  }
  {
    Fixture f; f.final_available = false;
    const auto result = ReadClergyMode0TaskRawAl12004(&f, Memory, kTask, kModule, Readers(f));
    failures += !(!result.raw_al && result.position_raw_al == 2 &&
        result.failure == ClergyMode0TaskRawAlFailure12004::final_source_unavailable &&
        f.final_calls == 1 && f.literal_errors == 0);
  }
  return failures;
}
