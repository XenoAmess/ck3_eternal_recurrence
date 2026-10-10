#include "xar_bridge/religion_owned_edit_dynamic_base_price_12004.hpp"
#include "xar_bridge/religion_owned_edit_dynamic_base_price_12004_focus.hpp"

#include <array>
#include <cstring>
#include <vector>

namespace xar::ck3_12004::piety_price_raw_inputs {
namespace {
constexpr std::uint64_t kRevision = 0xFEDCBA9876543210ULL;
struct Region { const void *data; std::size_t bytes; };

struct Fixture {
  std::array<unsigned char, 0x80> draft{};
  std::array<unsigned char, 0x800> rite{};
  std::array<unsigned char, 0x830> first_definition{};
  std::array<unsigned char, 0x400> second_definition{};
  std::array<unsigned char, 0x90> named_definition{};
  std::array<unsigned char, 16> root{};
  std::array<unsigned char, 32> original_r9_tuple{};
  std::array<unsigned char, 8> list_row{};
  std::array<unsigned char, 8> provider{};
  std::array<unsigned char, 0x38> vtable{};
  std::array<std::uint64_t, 1> first_array{};
  std::array<std::uint64_t, 1> second_array{};
  std::vector<Region> regions;
  std::vector<std::uintptr_t> resolved_definitions;
  bool wrong_operand = false;
  bool rite_scope_read = false;
  bool original_r9_copied = false;
  bool positive = false;

  template <typename T, std::size_t N>
  static void Put(std::array<unsigned char, N> &block,
                  std::size_t offset, T value) noexcept {
    std::memcpy(block.data() + offset, &value, sizeof(value));
  }
  template <typename T>
  static std::uintptr_t Address(const T &value) noexcept {
    return reinterpret_cast<std::uintptr_t>(value.data());
  }
  void Seal() {
    first_array[0] = Address(first_definition);
    second_array[0] = Address(second_definition);
    Put(draft, 8, Address(first_array));
    Put(draft, 0x14, std::int32_t{1});
    Put(draft, 0x50, Address(second_array));
    Put(draft, 0x5C, std::int32_t{1});
    // Both actual membership collections are known empty. Their distinct
    // existing production readers remain on the real parent path.
    Put(rite, 0x758, std::uintptr_t{0});
    Put(rite, 0x764, std::int32_t{0});
    Put(rite, 0x7A0, std::uintptr_t{0});
    Put(rite, 0x7AC, std::int32_t{0});

    // First real dynamic expression: named constant, not literal mode0.
    Put(first_definition, 0x818, std::int32_t{1});
    Put(first_definition, 0x810, std::uintptr_t{0});
    Put(first_definition, 0x800, Address(named_definition));
    Put(named_definition, 0x70, std::uintptr_t{0});
    Put(named_definition, 0x7A, std::uint8_t{1});
    Put(named_definition, 0x60, std::int32_t{-9});

    // Second uses the actual+2A8 selector, provider0, named0 and root pack.
    Put(second_definition, 0x360, std::int32_t{1});
    Put(second_definition, 0x358, std::uintptr_t{0});
    Put(second_definition, 0x348, std::uintptr_t{0});
    Put(second_definition, 0x2BC, positive ? std::int32_t{1} : std::int32_t{-1});
    Put(second_definition, 0x340, std::int32_t{4});
    // Actual2BD7C80's Rite-context root tag; the copied payload stays supplied.
    Put(root, 0, std::uint16_t{0x2A});
    Put(root, 8, std::int64_t{77700000});
    // Observed synthetic32B fixture tuple. Production never synthesizes these
    // bytes or padding from the source-defined key-layout description.
    Put(original_r9_tuple, 0, std::uintptr_t{0x123456789ABCDEF0ULL});
    Put(original_r9_tuple, 8, std::uintptr_t{0});
    Put(original_r9_tuple, 0x10, std::uint32_t{0});
    Put(original_r9_tuple, 0x14, std::uint8_t{1});
    Put(original_r9_tuple, 0x18, std::uint32_t{0xFFFFFFFFU});
    Put(original_r9_tuple, 0x1C, std::uint32_t{0});
    if (positive) {
      Put(second_definition, 0x2B0, Address(list_row));
      Put(second_definition, 0x320, std::uintptr_t{0}); // list+70 selects R9.
      Put(list_row, 0, Address(provider));
      Put(provider, 0, Address(vtable));
      Put(vtable, 0x20, std::uintptr_t{0x14000AB20ULL});
      Put(vtable, 0x30, std::uintptr_t{0x14000AB30ULL});
    }
    regions = {
        {draft.data(), draft.size()}, {rite.data(), rite.size()},
        {first_definition.data(), first_definition.size()},
        {second_definition.data(), second_definition.size()},
        {named_definition.data(), named_definition.size()},
        {root.data(), root.size()}, {original_r9_tuple.data(), original_r9_tuple.size()},
        {list_row.data(), list_row.size()}, {provider.data(), provider.size()},
        {vtable.data(), vtable.size()}, {first_array.data(), sizeof(first_array)},
        {second_array.data(), sizeof(second_array)},
    };
  }
  OwnedEditDynamicBasePriceBindings12004 Bindings() noexcept;
};

bool Read(void *opaque, const void *source, void *out,
          std::size_t size) noexcept {
  auto &f = *static_cast<Fixture *>(opaque);
  const auto address = reinterpret_cast<std::uintptr_t>(source);
  const auto scope = Fixture::Address(f.rite) + 8;
  if (address == scope) {
    f.rite_scope_read = true;
    return false;
  }
  if (address == Fixture::Address(f.original_r9_tuple) && size == 32)
    f.original_r9_copied = true;
  for (const auto &region : f.regions) {
    const auto begin = reinterpret_cast<std::uintptr_t>(region.data);
    if (address >= begin && address - begin <= region.bytes &&
        size <= region.bytes - (address - begin)) {
      std::memcpy(out, source, size);
      return true;
    }
  }
  return false;
}

bool DynamicInputs(void *opaque, const PietyPriceNumericAccess12004 &access,
                   std::uintptr_t definition, std::uintptr_t rite,
                   std::uint64_t revision,
                   PietyPriceA0F0B0DynamicInputs12004 &out) noexcept {
  auto &f = *static_cast<Fixture *>(opaque);
  if (!access.exact_12004_bound || access.module_base != 0x140000000ULL ||
      !access.guarded_read || rite != Fixture::Address(f.rite) ||
      revision != kRevision) {
    f.wrong_operand = true;
    return false;
  }
  // Probe the provided bridge with a real current draft byte. The stale access
  // embedded in the typed binding is deliberately unusable in this fixture.
  unsigned char byte = 0;
  if (!access.guarded_read(access.context, f.draft.data(), &byte, 1)) {
    f.wrong_operand = true;
    return false;
  }
  try {
    f.resolved_definitions.push_back(definition);
  } catch (...) {
    return false;
  }
  if (definition == Fixture::Address(f.first_definition)) {
    out.expression_identity = definition + 0x760;
    // No copied pack/R9/provider is needed by the named constant branch.
  } else if (definition == Fixture::Address(f.second_definition)) {
    out.expression_identity = definition + 0x2A8;
    out.copied_pack.primary_scope_identity = Fixture::Address(f.root);
    if (f.positive)
      out.original_named_tuple_identity = Fixture::Address(f.original_r9_tuple);
  } else {
    f.wrong_operand = true;
    return false;
  }
  out.unchanged_snapshot_revision = revision;
  return true;
}

OwnedEditDynamicBasePriceBindings12004 Fixture::Bindings() noexcept {
  OwnedEditDynamicBasePriceBindings12004 b{};
  b.access.context = this;
  b.access.read_memory = Read;
  b.access.module_base = 0x140000000ULL;
  b.access.exact_12004_bound = true;
  // Neither stale per-child access grants readiness or supplies current reads.
  // The production adapter must use the passed parent RawAccess instead.
  b.first.dynamic_context = this;
  b.first.read_dynamic_inputs = DynamicInputs;
  b.second.dynamic_context = this;
  b.second.read_dynamic_inputs = DynamicInputs;
  return b;
}
} // namespace

bool RunOwnedEditDynamicBasePriceFocus12004() noexcept {
  try {
    Fixture known;
    known.Seal();
    const auto a = ReadOwnedEditDynamicBasePrice2C6471012004(
        known.Bindings(), Fixture::Address(known.draft),
        Fixture::Address(known.rite), kRevision);
    if (!a.complete || a.base_price_raw_q64 != -500000 ||
        a.reached_occurrences.size() != 2 ||
        a.reached_occurrences[0].scalar_native_eax_raw != -9 ||
        a.reached_occurrences[1].scalar_native_eax_raw != 4 ||
        a.unchanged_snapshot_revision != kRevision ||
        known.wrong_operand || known.rite_scope_read || known.original_r9_copied ||
        known.resolved_definitions != std::vector<std::uintptr_t>{
            Fixture::Address(known.first_definition),
            Fixture::Address(known.second_definition)}) return false;

    // Actual positive-list R9 input is copied by64's existing producer seam;
    // unavailable virtual numerical output still stops with the first prefix.
    Fixture opaque;
    opaque.positive = true;
    opaque.Seal();
    const auto b = ReadOwnedEditDynamicBasePrice2C6471012004(
        opaque.Bindings(), Fixture::Address(opaque.draft),
        Fixture::Address(opaque.rite), kRevision);
    if (b.complete || b.base_price_raw_q64 ||
        b.failure != OwnedEditBasePriceFailure12004::scalar_31df3b0 ||
        b.completed_prefix_sum_bits != static_cast<std::uint64_t>(-900000LL) ||
        b.reached_occurrences.size() != 2 ||
        b.reached_occurrences[1].scalar_native_eax_raw ||
        !opaque.original_r9_copied || opaque.wrong_operand || opaque.rite_scope_read ||
        opaque.resolved_definitions != std::vector<std::uintptr_t>{
            Fixture::Address(opaque.first_definition),
            Fixture::Address(opaque.second_definition)}) return false;
    return true;
  } catch (...) {
    return false;
  }
}
} // namespace xar::ck3_12004::piety_price_raw_inputs
