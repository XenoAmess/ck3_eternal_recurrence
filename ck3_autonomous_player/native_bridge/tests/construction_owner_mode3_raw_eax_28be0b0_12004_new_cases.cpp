#include "xar_bridge/construction_owner_mode3_raw_eax_28be0b0_12004.hpp"

#include <cstddef>
#include <cstdint>
#include <map>
#include <vector>

namespace xar::ck3_12004::construction_owner_mode3 {
namespace {

constexpr std::uintptr_t module = 0x10000000;
constexpr std::uintptr_t receiver = 0x23456789;
constexpr std::uintptr_t carrier = 0x34567890;
constexpr std::uintptr_t thresholds = 0x45678901;
constexpr std::uint64_t frame = 0xFEDCBA9876543210ULL;

struct Fixture {
  std::map<std::uintptr_t, std::uint8_t> bytes;
  std::vector<std::uintptr_t> reads;
  int missing_reads = 0;

  template <typename T>
  void Put(std::uintptr_t address, const T &value) {
    const auto *source = reinterpret_cast<const std::uint8_t *>(&value);
    for (std::size_t i = 0; i < sizeof(value); ++i)
      bytes[address + i] = source[i];
  }

  void Remove(std::uintptr_t address, std::size_t size) {
    for (std::size_t i = 0; i < size; ++i) bytes.erase(address + i);
  }

  Fixture() {
    Put(receiver + 0x1B0, carrier);
    Put(module + 0x54582E4, std::int32_t{3});
    Put(carrier + 0x120, std::int32_t{-1});
    Put(carrier + 0x118, std::int64_t{20});
    Put(module + 0x54582D8, thresholds);
    Put(thresholds, std::int64_t{10});
    Put(thresholds + 8, std::int64_t{20});
    Put(thresholds + 16, std::int64_t{30});
  }

  static bool Read(void *opaque, const void *source, void *destination,
                   std::size_t size) {
    auto &f = *static_cast<Fixture *>(opaque);
    const auto address = reinterpret_cast<std::uintptr_t>(source);
    f.reads.push_back(address);
    auto *out = static_cast<std::uint8_t *>(destination);
    for (std::size_t i = 0; i < size; ++i) {
      const auto found = f.bytes.find(address + i);
      if (found == f.bytes.end()) {
        ++f.missing_reads;
        return false;
      }
      out[i] = found->second;
    }
    return true;
  }

  RawReceiverAccessV1 Access(std::uintptr_t base = module) {
    return RawReceiverAccessV1{this, Read, base, true};
  }

  Raw28BE0B0Eax12004 Run() {
    return ReadRaw28BE0B0Eax12004(Access(), receiver, frame);
  }
};

} // namespace

int ConstructionMode3Raw28BE0B0Eax12004NewCaseCount() noexcept { return 12; }

// Central10 invokes this new fragment once in the M4 compound. No main,
// native calls, existing receiver qualification or Native65 replay.
int RunConstructionMode3Raw28BE0B0Eax12004NewCases() {
  int failures = 0;
  const auto require = [&](bool condition) {
    if (!condition) ++failures;
  };
  {
    Fixture f;
    f.bytes.clear();
    f.Put(receiver + 0x1B0, std::uintptr_t{0});
    const auto r = ReadRaw28BE0B0Eax12004(f.Access(0), receiver, frame);
    require(r.observed && r.eax_signed == 0 && r.carrier_pointer == 0 &&
            r.receiver_pointer == receiver && r.snapshot_revision == frame &&
            r.source_return_rva == 0x28BE105 && !r.threshold_count &&
            !r.observed_native_producer_call && f.reads.size() == 1 &&
            f.missing_reads == 0);
  }
  {
    Fixture f;
    f.Remove(receiver + 0x1B0, sizeof(std::uintptr_t));
    std::int32_t out = -77;
    const bool ok = ReadRaw28BE0B0EaxAdapter12004(
        nullptr, f.Access(), receiver, frame, out);
    require(!ok && out == -77 && f.reads.size() == 1);
  }
  {
    Fixture f;
    f.Put(module + 0x54582E4, std::int32_t{0});
    f.Remove(module + 0x54582D8, sizeof(std::uintptr_t));
    const auto r = f.Run();
    require(r.observed && r.eax_signed == 0 && !r.threshold_array_pointer &&
            r.score_signed == 20 && r.cap_signed == -1 &&
            f.reads == std::vector<std::uintptr_t>{receiver + 0x1B0,
                module + 0x54582E4, carrier + 0x120, carrier + 0x118} &&
            f.missing_reads == 0);
  }
  {
    Fixture f;
    f.Put(module + 0x54582E4, std::int32_t{-3});
    f.Remove(module + 0x54582D8, sizeof(std::uintptr_t));
    f.Put(carrier + 0x120, std::int32_t{2});
    const auto r = f.Run();
    require(r.observed && r.eax_signed == 0 && r.threshold_reads == 0 &&
            f.missing_reads == 0);
  }
  {
    Fixture f;
    f.Put(module + 0x54582E4, std::int32_t{4});
    f.Put(carrier + 0x118, std::int64_t{-3});
    f.Put(thresholds, std::int64_t{-7});
    f.Put(thresholds + 8, std::int64_t{-3});
    f.Put(thresholds + 16, std::int64_t{1});
    const auto r = f.Run();
    require(r.observed && r.eax_signed == 2 && r.threshold_reads == 3 &&
            r.last_threshold_signed == 1 && f.missing_reads == 0);
  }
  {
    Fixture f;
    f.Put(carrier + 0x118, std::int64_t{0});
    f.Put(thresholds, std::int64_t{5});
    f.Put(thresholds + 8, std::int64_t{-100});
    const auto r = f.Run();
    require(r.observed && r.eax_signed == 0 && r.threshold_reads == 1 &&
            f.missing_reads == 0);
  }
  {
    Fixture f;
    f.Put(module + 0x54582E4, std::int32_t{2});
    f.Remove(thresholds + 16, sizeof(std::int64_t));
    std::int32_t out = -77;
    const bool ok = ReadRaw28BE0B0EaxAdapter12004(
        &f, f.Access(), receiver, frame, out);
    require(ok && out == 2 && f.missing_reads == 0);
  }
  {
    Fixture f;
    f.Put(carrier + 0x120, std::int32_t{0});
    const auto r = f.Run();
    require(r.observed && r.eax_signed == 0 && r.threshold_reads == 3);
  }
  {
    Fixture f;
    f.Put(carrier + 0x120, std::int32_t{1});
    f.Put(carrier + 0x118, std::int64_t{30});
    const auto r = f.Run();
    require(r.observed && r.eax_signed == 1 && r.threshold_reads == 3);
  }
  {
    Fixture f;
    f.Put(carrier + 0x120, std::int32_t{0});
    f.Remove(thresholds + 8, sizeof(std::int64_t));
    const auto r = f.Run();
    require(!r.observed && !r.eax_signed &&
            r.failure == Raw28BE0B0Failure12004::threshold_element &&
            r.threshold_reads == 1 && r.last_threshold_signed == 10);
  }
  {
    for (int missing = 0; missing < 4; ++missing) {
      Fixture f;
      const std::uintptr_t address[] = {module + 0x54582E4,
          carrier + 0x120, carrier + 0x118, module + 0x54582D8};
      const std::size_t size[] = {sizeof(std::int32_t), sizeof(std::int32_t),
          sizeof(std::int64_t), sizeof(std::uintptr_t)};
      const Raw28BE0B0Failure12004 reason[] = {
          Raw28BE0B0Failure12004::threshold_count,
          Raw28BE0B0Failure12004::carrier_cap,
          Raw28BE0B0Failure12004::carrier_score,
          Raw28BE0B0Failure12004::threshold_array};
      f.Remove(address[missing], size[missing]);
      const auto r = f.Run();
      require(!r.observed && !r.eax_signed && r.failure == reason[missing] &&
              f.reads.back() == address[missing]);
    }
  }
  {
    Fixture f;
    auto access = f.Access();
    access.exact_12004_bound = false;
    const auto r = ReadRaw28BE0B0Eax12004(access, receiver, frame);
    require(!r.observed && r.failure == Raw28BE0B0Failure12004::exact_build &&
            r.snapshot_revision == frame && f.reads.empty());
  }
  return failures;
}

} // namespace xar::ck3_12004::construction_owner_mode3
