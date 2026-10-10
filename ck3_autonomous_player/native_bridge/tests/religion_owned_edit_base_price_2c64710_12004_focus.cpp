#include "xar_bridge/religion_owned_edit_base_price_2c64710_12004.hpp"
#include "xar_bridge/religion_owned_edit_base_price_2c64710_12004_focus.hpp"

#include <array>
#include <cstring>
#include <limits>
#include <vector>

namespace xar::ck3_12004::piety_price_raw_inputs {
namespace {
constexpr std::uint64_t kRevision = 0x12345678ABCDEF90ULL;
constexpr std::uint64_t kA = 0x1000000000000011ULL;
constexpr std::uint64_t kB = 0x2000000000000011ULL;
constexpr std::uint64_t kC = 0x3000000000000022ULL;

struct MemoryRegion {
  const void *pointer;
  std::size_t bytes;
};

struct Fixture {
  std::array<unsigned char, 0x80> draft{};
  std::array<unsigned char, 0x800> rite{};
  std::vector<std::uint64_t> first;
  std::vector<std::uint64_t> second;
  std::vector<std::uint64_t> existing_first;
  std::vector<std::uint64_t> existing_second;
  std::vector<MemoryRegion> regions;
  std::vector<std::uint64_t> scalar_keys;
  bool wrong_operand = false;
  bool fail_second_scalar = false;
  bool fail_first_scalar = false;
  bool second_draft_header_read = false;

  template <typename T, std::size_t N>
  static void Put(std::array<unsigned char, N> &block,
                  std::size_t offset, T value) noexcept {
    std::memcpy(block.data() + offset, &value, sizeof(value));
  }
  static std::uintptr_t Pointer(const std::vector<std::uint64_t> &v) noexcept {
    return v.empty() ? 0 : reinterpret_cast<std::uintptr_t>(v.data());
  }
  void Seal() {
    Put(draft, 8, Pointer(first));
    Put(draft, 0x14, static_cast<std::int32_t>(first.size()));
    Put(draft, 0x50, Pointer(second));
    Put(draft, 0x5C, static_cast<std::int32_t>(second.size()));
    Put(rite, 0x758, Pointer(existing_first));
    Put(rite, 0x764, static_cast<std::int32_t>(existing_first.size()));
    Put(rite, 0x7A0, Pointer(existing_second));
    Put(rite, 0x7AC, static_cast<std::int32_t>(existing_second.size()));
    regions = {{draft.data(), draft.size()}, {rite.data(), rite.size()}};
    for (const auto *values : {&first, &second, &existing_first, &existing_second})
      if (!values->empty())
        regions.push_back({values->data(), values->size() * sizeof(std::uint64_t)});
  }
  OwnedEditBasePriceBindings12004 Bindings() noexcept;
};

bool ReadMemory(void *opaque, const void *source, void *out,
                std::size_t bytes) noexcept {
  auto &f = *static_cast<Fixture *>(opaque);
  const auto address = reinterpret_cast<std::uintptr_t>(source);
  if (address == reinterpret_cast<std::uintptr_t>(f.draft.data()) + 0x50)
    f.second_draft_header_read = true;
  for (const auto &region : f.regions) {
    const auto begin = reinterpret_cast<std::uintptr_t>(region.pointer);
    if (address >= begin && address - begin <= region.bytes &&
        bytes <= region.bytes - (address - begin)) {
      std::memcpy(out, source, bytes);
      return true;
    }
  }
  return false;
}

bool Scalar(Fixture &f, const OwnedEditReadAccess12004 &access,
            std::uintptr_t definition, std::uintptr_t rite,
            std::uint64_t revision, std::int32_t &raw, bool second) noexcept {
  if (access.context != &f || access.module_base != 0x140000000ULL ||
      !access.exact_12004_bound ||
      rite != reinterpret_cast<std::uintptr_t>(f.rite.data()) ||
      revision != kRevision) {
    f.wrong_operand = true;
    return false;
  }
  try {
    f.scalar_keys.push_back(static_cast<std::uint64_t>(definition));
  } catch (...) {
    return false;
  }
  if (second ? f.fail_second_scalar : f.fail_first_scalar) {
    raw = 123456789; // Unavailable child output must never enter the prefix.
    return false;
  }
  if (!second && definition == kA) raw = -7;
  else if (!second && definition == kB) raw = 123;
  else if (second && definition == kC) raw = 5;
  else {
    f.wrong_operand = true;
    return false;
  }
  return true;
}

bool FirstScalar(void *opaque, const OwnedEditReadAccess12004 &access,
                 std::uintptr_t definition, std::uintptr_t rite,
                 std::uint64_t revision, std::int32_t &raw) noexcept {
  return Scalar(*static_cast<Fixture *>(opaque), access, definition, rite,
                revision, raw, false);
}

bool SecondScalar(void *opaque, const OwnedEditReadAccess12004 &access,
                  std::uintptr_t definition, std::uintptr_t rite,
                  std::uint64_t revision, std::int32_t &raw) noexcept {
  return Scalar(*static_cast<Fixture *>(opaque), access, definition, rite,
                revision, raw, true);
}

OwnedEditBasePriceBindings12004 Fixture::Bindings() noexcept {
  OwnedEditBasePriceBindings12004 b{};
  b.access.context = this;
  b.access.read_memory = ReadMemory;
  b.access.module_base = 0x140000000ULL;
  b.access.exact_12004_bound = true;
  b.first_scalar_context = this;
  b.read_31d9930 = FirstScalar;
  b.second_scalar_context = this;
  b.read_31df3b0 = SecondScalar;
  return b;
}

OwnedEditBasePrice12004 Run(Fixture &f,
                          const OwnedEditBasePriceBindings12004 &b) noexcept {
  return ReadOwnedEditBasePrice2C6471012004(
      b, reinterpret_cast<std::uintptr_t>(f.draft.data()),
      reinterpret_cast<std::uintptr_t>(f.rite.data()), kRevision);
}
} // namespace

bool RunOwnedEditBasePriceFocus12004() noexcept {
  try {
    // One connected parent fixture: exact full64 input routing, order and
    // duplicate occurrence preservation through both distinct child seams.
    Fixture ordered;
    ordered.first = {kA, kB, kA};
    ordered.second = {kC, kB, kC};
    ordered.existing_first = {kB};
    ordered.existing_second = {kB};
    ordered.Seal();
    const auto a = Run(ordered, ordered.Bindings());
    if (!a.complete || a.base_price_raw_q64 != -400000 ||
        a.reached_occurrences.size() != 6 || ordered.wrong_operand ||
        ordered.scalar_keys != std::vector<std::uint64_t>{kA, kA, kC, kC} ||
        a.unchanged_snapshot_revision != kRevision ||
        a.reached_occurrences[1].skip != true ||
        a.reached_occurrences[4].skip != true ||
        a.reached_occurrences[0].definition_qword == kB ||
        a.reached_occurrences[3].array != OwnedEditPriceArray12004::second)
      return false;

    // A reached unavailable second scalar cannot overwrite known prefix or
    // produce a complete quotation; unchanged original scalar operands stay.
    Fixture partial;
    partial.first = {kA};
    partial.second = {kC};
    partial.fail_second_scalar = true;
    partial.Seal();
    const auto b = Run(partial, partial.Bindings());
    if (b.complete || b.base_price_raw_q64 ||
        b.failure != OwnedEditBasePriceFailure12004::scalar_31df3b0 ||
        b.completed_prefix_sum_bits != static_cast<std::uint64_t>(-700000LL) ||
        b.reached_occurrences.back().scalar_native_eax_raw ||
        partial.scalar_keys != std::vector<std::uint64_t>{kA, kC} ||
        partial.wrong_operand) return false;

    // First reached unknown prevents even loading the later draft collection.
    Fixture early;
    early.first = {kA};
    early.second = {kC};
    early.fail_first_scalar = true;
    early.Seal();
    const auto c = Run(early, early.Bindings());
    if (c.complete || c.base_price_raw_q64 || early.second_draft_header_read ||
        c.completed_prefix_sum_bits != 0 ||
        c.failure != OwnedEditBasePriceFailure12004::scalar_31d9930)
      return false;

    // Empty and matched-only branches do not demand scalar callbacks.
    Fixture empty;
    empty.Seal();
    auto empty_bindings = empty.Bindings();
    empty_bindings.read_31d9930 = nullptr;
    empty_bindings.read_31df3b0 = nullptr;
    const auto d = Run(empty, empty_bindings);
    if (!d.complete || d.base_price_raw_q64 != 0 ||
        !d.reached_occurrences.empty()) return false;
    Fixture skipped;
    skipped.first = {kA};
    skipped.second = {kC};
    skipped.existing_first = {kA};
    skipped.existing_second = {kC};
    skipped.Seal();
    auto skipped_bindings = skipped.Bindings();
    skipped_bindings.read_31d9930 = nullptr;
    skipped_bindings.read_31df3b0 = nullptr;
    const auto e = Run(skipped, skipped_bindings);
    if (!e.complete || e.base_price_raw_q64 != 0 ||
        e.reached_occurrences.size() != 2 ||
        e.reached_occurrences[0].skip != true ||
        e.reached_occurrences[1].skip != true) return false;
    return true;
  } catch (...) {
    return false;
  }
}
} // namespace xar::ck3_12004::piety_price_raw_inputs
