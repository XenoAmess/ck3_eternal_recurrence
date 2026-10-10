#include "xar_bridge/ck3_12004_army_late_context_builder_inputs.hpp"
#include "xar_bridge/army_late_context_copy12004_serializer.hpp"

#include <array>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
using namespace xar::ck3_12004;
std::size_t checks = 0;
void Check(bool value, const char *name) {
  ++checks;
  if (!value) throw std::runtime_error(name);
}
template <typename T, std::size_t N>
void Put(std::array<std::byte, N> &data, std::size_t offset, T value) {
  std::memcpy(data.data() + offset, &value, sizeof(value));
}
struct Reader {
  std::size_t reads = 0;
  const void *denied = nullptr;
  const void *header = nullptr;
  std::size_t header_reads = 0;
  bool change_header = false;
  static bool Read(void *context, const void *address, void *out, std::size_t bytes) noexcept {
    auto &self = *static_cast<Reader *>(context);
    ++self.reads;
    if (address == self.denied) return false;
    std::memcpy(out, address, bytes);
    if (address == self.header && ++self.header_reads == 2 && self.change_header) {
      const std::int32_t changed = 4;
      std::memcpy(static_cast<std::byte *>(out) + 12, &changed, sizeof(changed));
    }
    return true;
  }
};
struct Inputs {
  Reader reader;
  std::array<std::byte, 0x130> army{};
  std::array<std::byte, 0x180> unit{}, fallback_unit{};
  std::array<std::byte, 0x740> province{}, fallback_province{};
  std::array<std::byte, 0x110> title{}, fallback_title{};
  std::array<std::byte, 0x30> unit_registry{}, title_registry{};
  std::array<std::byte, 0x40> unit_rows{}, title_rows{};
  const void *unit_store = unit_registry.data(), *unit_fallback = fallback_unit.data();
  const void *title_store = title_registry.data(), *title_fallback = fallback_title.data();
  const void *province_fallback = fallback_province.data();
  std::array<std::uint32_t, 3> keys{0xF0000001U, 0U, 0x80000002U};
  ArmyLateContextBuilderBindings12004 bindings{};
  Inputs() {
    Put(army, 0x10, std::uint32_t{0xF1000009U});
    Put(army, 0x124, std::uint32_t{0xD0000001U});
    Put(unit_registry, 0x20, static_cast<const void *>(unit_rows.data()));
    Put(unit_registry, 0x2C, std::uint32_t{4U});
    Put(unit_rows, 0x18, static_cast<const void *>(unit.data()));
    Put(unit, 0x10, std::uint32_t{0xD0000001U});
    Put(unit, 0x174, std::uint32_t{0xF8000007U});
    Put(unit, 0x20, static_cast<const void *>(province.data()));
    Put(fallback_unit, 0x174, std::uint32_t{0U});
    Put(fallback_unit, 0x20, static_cast<const void *>(province.data()));
    Put(province, 0x738, std::uint32_t{0xA0000002U});
    Put(fallback_province, 0x738, std::uint32_t{0xA0000002U});
    Put(title_registry, 0x20, static_cast<const void *>(title_rows.data()));
    Put(title_registry, 0x2C, std::uint32_t{4U});
    Put(title_rows, 0x28, static_cast<const void *>(title.data()));
    Put(title, 0x10, std::uint32_t{0xA0000002U});
    Put(title, 0x108, std::uint32_t{0xFFFFFFFFU});
    Put(fallback_title, 0x10, std::uint32_t{0U});
    Put(fallback_title, 0x108, std::uint32_t{0xFF000005U});
    bindings.enabled = true;
    bindings.unit_registry_slot = &unit_store; bindings.unit_fallback_slot = &unit_fallback;
    bindings.province_fallback_slot = &province_fallback;
    bindings.title_registry_slot = &title_store; bindings.title_fallback_slot = &title_fallback;
    bindings.named_key_slots = {&keys[0], &keys[1], &keys[2]};
    bindings.read_memory = &Reader::Read; bindings.read_context = &reader;
  }
  auto Observe(bool demanded = true) { return ObserveArmyLateContextBuilderInputs12004(bindings, army.data(), demanded); }
};
struct Context {
  Reader reader;
  std::array<std::byte, 0x28> incoming{};
  std::array<std::byte, 0x18 * 33> rows{};
  std::array<std::uint32_t, 3> keys{0xF0000001U, 0U, 0x80000002U};
  Context() {
    Put(incoming, 0, std::uint16_t{27}); Put(incoming, 2, std::uint16_t{0});
    Put(incoming, 8, std::uint64_t{0xF1000009U}); Put(incoming, 0x10, std::uint32_t{0xA1234567U});
    Put(incoming, 0x18, reinterpret_cast<std::uintptr_t>(rows.data()));
    Put(incoming, 0x20, std::int32_t{33}); Put(incoming, 0x24, std::int32_t{3});
    for (std::size_t i = 0; i < 3; ++i) {
      Put(rows, i * 0x18, keys[i]);
      Put(rows, i * 0x18 + 8, i == 0 ? std::uint16_t{4} : std::uint16_t{5});
      Put(rows, i * 0x18 + 10, std::uint16_t{0});
      Put(rows, i * 0x18 + 16, i == 0 ? std::uint64_t{0xF8000007U} : std::uint64_t{0xFFFFFFFFU});
    }
    reader.header = incoming.data() + 0x18;
  }
  auto Copy() { return CopyActualArmyLateContext12004(incoming.data(), &Reader::Read, &reader); }
};
} // namespace
int main() {
  try {
    {
      Inputs f; const auto out = f.Observe();
      Check(out.inputs_ready, "registry input shape");
      Check(out.root_kind == 27 && out.root_army_full_id_raw_u64 == 0xF1000009ULL, "root Army ID bits");
      Check(out.named_inputs[0].kind == 4 && out.named_inputs[0].payload_raw_u64 == 0xF8000007ULL, "owner full ID zero extension");
      Check(out.named_inputs[1].kind == 5 && out.named_inputs[1].payload_raw_u64 == 0xA0000002ULL, "Title full ID zero extension");
      Check(out.named_inputs[2].payload_raw_u64 == 0xFFFFFFFFULL, "Title108 full bits");
      Check(out.named_inputs[1].name_key_raw_u32 == 0U, "legal loaded key zero");
      Check(out.units[0].used_fallback == false && out.units[1].used_fallback == false, "two independent selections");
      Check(!out.historical_execution_observed, "current never history");
    }
    {
      Inputs f; f.unit_store = nullptr; f.reader.denied = f.army.data() + 0x124;
      const auto out = f.Observe();
      Check(out.inputs_ready && out.named_inputs[0].payload_raw_u64 == 0ULL, "null registry fallback and legal owner zero");
      Check(!out.units[0].requested_full_id_u32 && !out.units[1].requested_full_id_u32, "native null registry skips124");
    }
    {
      Inputs f; Put(f.unit, 0x10, std::uint32_t{0xC0000001U});
      const auto out = f.Observe();
      Check(out.inputs_ready && out.units[0].used_fallback == true, "generation mismatch fallback");
      Check(out.named_inputs[0].payload_raw_u64 == 0ULL, "fallback owner payload");
    }
    {
      Inputs f; Put(f.unit, 0x20, static_cast<const void *>(nullptr));
      const auto out = f.Observe();
      Check(out.inputs_ready && out.position_province_used_fallback == true, "null Province position fallback");
    }
    {
      Inputs f; f.title_store = nullptr; f.reader.denied = f.province.data() + 0x738;
      const auto out = f.Observe();
      Check(out.inputs_ready && out.title.used_fallback == true, "null Title registry fallback");
      Check(!out.title.requested_full_id_u32 && out.named_inputs[1].payload_raw_u64 == 0ULL, "native skip738 and real fallback Title ID");
    }
    {
      Inputs f; f.reader.denied = &f.keys[2]; const auto out = f.Observe();
      Check(!out.inputs_ready && !out.named_inputs[2].payload_raw_u64, "missing loaded key remains unknown");
      Check(out.root_army_full_id_raw_u64.has_value() && out.named_inputs[1].payload_raw_u64.has_value(), "partial source facts retained");
    }
    {
      Inputs f; const auto out = f.Observe(false);
      Check(!out.inputs_ready && f.reader.reads == 0 && !out.root_army_full_id_raw_u64, "not demanded does not read");
    }
    {
      const auto b = BindArmyLateContextBuilderInputs12004(0x10000000U, kExecutableSha256);
      Check(b.enabled && b.named_key_slots[0] == reinterpret_cast<const void *>(0x15D4C27CU), "exact4 loaded key binder");
      Check(!BindArmyLateContextBuilderInputs12004(0x10000000U, "different").enabled, "different image unbound");
    }
    {
      Context f; const auto copy = f.Copy(); const auto roles = ClassifyActualArmyLateContextRoles12004(copy, f.keys);
      Check(copy.root_copy_ready && copy.named_header_unchanged && copy.named_rows_copy_ready, "actual context copy");
      Check(copy.context_seed_10_raw_u32 == 0xA1234567U && copy.copied_row_count == 3, "raw seed and rows");
      Check(roles.complete_named_input_shape_matches && roles.roles[0].payload_raw_u64 == 0xF8000007ULL, "source role shape");
      Check(!copy.builder_called && !copy.builder_callsite_rva && !copy.parent_pc_rva, "builder and parent remain unknown");
      const auto json = SerializeActualArmyLateContextCopy12004(copy, roles);
      Check(json.find("\"builder_called\":null") != std::string::npos && json.find("4294967295") != std::string::npos, "serialized null and full payload");
    }
    {
      Context f; Put(f.incoming, 0x24, std::int32_t{33}); const auto copy = f.Copy();
      Check(copy.named_rows_copy_ready && copy.named_rows_truncated && copy.copied_row_count == 32, "bounded33 row truncation");
      Check(!ClassifyActualArmyLateContextRoles12004(copy, f.keys).complete_named_input_shape_matches, "truncated not complete shape");
    }
    {
      Context f; f.reader.change_header = true; const auto copy = f.Copy();
      Check(!copy.named_header_unchanged && !copy.named_rows_copy_ready && copy.copied_row_count == 3, "header change preserves partial copied rows");
      Check(!ClassifyActualArmyLateContextRoles12004(copy, f.keys).roles[0].payload_raw_u64, "changed header roles unknown");
    }
    {
      Context f; f.reader.denied = f.rows.data() + 0x18; const auto copy = f.Copy();
      Check(!copy.named_rows_copy_ready && copy.copied_row_count == 1, "actual row copy partial");
      Check(copy.root_payload_raw_u64 == 0xF1000009ULL, "partial retains observed root");
    }
    {
      Context f; Put(f.rows, 10, std::uint16_t{1}); const auto copy = f.Copy();
      const auto roles = ClassifyActualArmyLateContextRoles12004(copy, f.keys);
      Check(roles.roles[0].token_kind_and_subtype_match == false && !roles.complete_named_input_shape_matches, "source subtype compared");
      Check(roles.roles[0].payload_raw_u64 == 0xF8000007ULL, "mismatching actual token still copied");
    }
    {
      Context f; Put(f.incoming, 0x24, std::int32_t{0}); const auto copy = f.Copy();
      Check(copy.named_rows_copy_ready && copy.copied_row_count == 0, "actual empty rows legal");
      Check(!ClassifyActualArmyLateContextRoles12004(copy, f.keys).complete_named_input_shape_matches, "empty rows not inferred source roles");
    }
    std::cout << "{\"status\":\"GREEN\",\"checks\":" << checks << ",\"cases\":14,\"scope\":\"new-production-context-input-reader-and-actual-context-copy-offline-fixture\",\"game_calls\":0}\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
