#include "xar_bridge/piety_price_named_definition_37540b0_readonly_12004.hpp"

#include <array>
#include <cstdlib>
#include <cstring>
#include <limits>

namespace {
using namespace xar::ck3_12004::piety_price_raw_inputs;

struct NamedDefinitionFixture {
  std::array<std::uint8_t, 0x80> bytes{};
  bool deny_value = false;
  bool deny_provider = false;
  bool change_provider_bookend = false;
  unsigned provider_reads = 0;
  unsigned enabled_reads = 0;
  unsigned value_reads = 0;

  template<class T> void Store(std::size_t offset, T value) {
    std::memcpy(bytes.data() + offset, &value, sizeof(value));
  }
  std::uintptr_t Identity() const noexcept {
    return reinterpret_cast<std::uintptr_t>(bytes.data());
  }
  static bool Read(void *context, const void *address, void *out,
                   std::size_t size) noexcept {
    auto &f = *static_cast<NamedDefinitionFixture *>(context);
    const auto raw_address = reinterpret_cast<std::uintptr_t>(address);
    if (raw_address < f.Identity()) return false;
    const auto offset = raw_address - f.Identity();
    if (offset >= f.bytes.size() || size > f.bytes.size() - offset) return false;
    if (offset == 0x70 && size == sizeof(std::uintptr_t)) {
      ++f.provider_reads;
      if (f.deny_provider) return false;
      if (f.change_provider_bookend && f.provider_reads == 2)
        f.Store<std::uintptr_t>(0x70, 0x1234);
    }
    if (offset == 0x7A && size == 1) ++f.enabled_reads;
    if (offset == 0x60 && size == 4) {
      ++f.value_reads;
      if (f.deny_value) return false;
    }
    std::memcpy(out, f.bytes.data() + offset, size);
    return true;
  }
  auto Project() noexcept {
    PietyPriceNumericAccess12004 access{};
    access.module_base = 0x140000000ULL;
    access.context = this;
    access.guarded_read = Read;
    access.exact_12004_bound = true;
    return ReadPietyPriceNamedDefinition37540B0Readonly12004(
        access, Identity(), 0xFEDCBA9876543210ULL);
  }
};

void Require(bool condition) { if (!condition) std::abort(); }
} // namespace

// New fragment only. The numeric connection owner supplies the sole main.
void RunPietyPriceNamedDefinition37540B0Focus12004() {
  {
    NamedDefinitionFixture f{};
    f.deny_value = true;
    const auto result = f.Project();
    Require(result.eax_raw_i32 == std::optional<std::int32_t>{0});
    Require(result.unchanged_snapshot_revision == 0xFEDCBA9876543210ULL);
    Require(f.provider_reads == 2 && f.enabled_reads == 2 && f.value_reads == 0);
  }
  {
    NamedDefinitionFixture f{};
    f.Store<std::uint8_t>(0x7A, 0x80);
    f.Store<std::int32_t>(0x60, (std::numeric_limits<std::int32_t>::min)());
    const auto result = f.Project();
    Require(result.eax_raw_i32 ==
        std::optional<std::int32_t>{(std::numeric_limits<std::int32_t>::min)()});
    Require(f.value_reads == 2 && result.unavailable_reason.empty());
  }
  {
    NamedDefinitionFixture f{};
    f.Store<std::uintptr_t>(0x70, 0x1234);
    const auto result = f.Project();
    Require(!result.eax_raw_i32 && f.enabled_reads == 0 && f.value_reads == 0);
    Require(result.unavailable_reason ==
        "piety_named_definition_virtual_variant_37498a0_unavailable");
  }
  {
    NamedDefinitionFixture f{};
    f.change_provider_bookend = true;
    Require(!f.Project().eax_raw_i32);
    NamedDefinitionFixture unreadable{};
    unreadable.deny_provider = true;
    const auto unknown = unreadable.Project();
    Require(!unknown.eax_raw_i32 && !unknown.provider_first_raw);
    Require(unreadable.enabled_reads == 0 && unreadable.value_reads == 0);
  }
}
