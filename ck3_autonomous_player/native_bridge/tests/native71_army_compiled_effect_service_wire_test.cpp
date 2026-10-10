#include "xar_bridge/actual_army_compiled_effect_observer_12004.hpp"
#include "xar_bridge/army_strength_v1_serializer.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include <array>
#include <cstring>
#include <fstream>
#include <iostream>
#include <stdexcept>

namespace {
std::array<std::byte, 0x168> scope{};
std::array<std::byte, 0x30> receiver{};
std::array<std::byte, 24> named_row{};
std::uint32_t original_calls = 0;
constexpr std::uintptr_t image_base = 0x100000;
constexpr std::uint64_t return_bits = 0xF123456789ABCDEFULL;
template <typename T, std::size_t N> void Put(std::array<std::byte, N> &object, std::size_t offset, T value) {
  std::memcpy(object.data() + offset, &value, sizeof(value));
}
template <std::size_t N> bool Owns(const std::array<std::byte, N> &object, std::uintptr_t address, std::size_t size) {
  const auto start = reinterpret_cast<std::uintptr_t>(object.data());
  return address >= start && size <= N && address - start <= N - size;
}
bool Read(void *, const void *address, void *output, std::size_t size) noexcept {
  const auto raw = reinterpret_cast<std::uintptr_t>(address);
  if (raw == image_base + 0x5D1DADC && size == 1) {
    const std::uint8_t flag = 0xA5;
    std::memcpy(output, &flag, 1);
    return true;
  }
  if (!(Owns(scope, raw, size) || Owns(receiver, raw, size) || Owns(named_row, raw, size))) return false;
  std::memcpy(output, address, size);
  return true;
}
std::uint64_t __fastcall Original(const void *actual_receiver, const void *actual_scope) {
  if (actual_receiver != receiver.data() || actual_scope != scope.data())
    throw std::runtime_error("compiled effect original arguments changed");
  ++original_calls;
  Put(scope, 0x10, std::uint32_t{29});
  return return_bits;
}
} // namespace

int main(int argc, char **argv) {
  try {
    if (argc != 2) throw std::runtime_error("new compiled-effect whole query wire needs one output path");
    constexpr std::int32_t native_carmy_id = -2130706399; // Full generation0x81000021.
    Put(scope, 0, std::uint16_t{27});
    Put(scope, 8, std::uint64_t{0x81000021U});
    Put(scope, 0x10, std::uint32_t{17});
    Put(scope, 0x18, reinterpret_cast<std::uintptr_t>(named_row.data()));
    Put(scope, 0x20, std::int32_t{1}); Put(scope, 0x24, std::int32_t{1});
    Put(named_row, 0, std::uint32_t{7}); Put(named_row, 8, std::uint16_t{4});
    Put(named_row, 16, std::uint64_t{100});
    Put(receiver, 0, std::uint64_t{0x1122334455667788ULL});
    Put(receiver, 0x2C, std::uint32_t{0x76543210U});
    auto bindings = xar::ck3_12004::BindActualArmyCompiledEffectImage12004(image_base, xar::ck3_12004::kExecutableSha256);
    bindings.read_memory = &Read;
    if (!xar::ck3_12004::InitializeActualArmyCompiledEffectFixture12004(bindings, &Original))
      throw std::runtime_error("new compiled-effect owned input initialization failed");
    if (xar::ck3_12004::InvokeActualArmyCompiledEffectFixture12004(0x2639CA4, receiver.data(), scope.data()) != return_bits)
      throw std::runtime_error("positive wrapper changed original raw RAX");
    Put(scope, 0x10, std::uint32_t{0x80000009U});
    if (xar::ck3_12004::InvokeActualArmyCompiledEffectFixture12004(0x24DD7B6, receiver.data(), scope.data()) != return_bits)
      throw std::runtime_error("flag30 wrapper changed original raw RAX");
    xar::game::ArmyStrengthSnapshot strength{};
    strength.available = true; strength.army_id = 11;
    strength.native_carmy_id_observable = true; strength.native_carmy_id = native_carmy_id;
    strength.scope_role = xar::game::ArmyStrengthScopeRole::player;
    strength.current_soldiers = 160; strength.maximum_soldiers = 200;
    auto number = [](auto value) { return std::to_string(value); };
    auto string = [](std::string &out, std::string_view text) {
      out += '"';
      for (const auto c : text) { if (c == '"' || c == '\\') out += '\\'; out += c; }
      out += '"';
    };
    auto array = [](std::string &out, const auto &values) {
      out += '['; bool first = true;
      for (const auto value : values) { if (!first) out += ','; first = false; out += std::to_string(value); }
      out += ']';
    };
    std::string row;
    xar::game::AppendArmyStrengthV1WithManagerInputsMode(row, strength, number, array, string,
        xar::game::ArmyStrengthManagerInputsModeV1::inline_values);
    if (original_calls != 2) throw std::runtime_error("whole Army query executed compiled effects again");
    if (row.find("\"source\":\"native_natural_compiled_effect_entry_return\"") == std::string::npos)
      throw std::runtime_error("production whole Army serializer missed owned compiled-effect journal");
    std::ofstream output(argv[1], std::ios::binary);
    output << "{\"status\":\"available\",\"query_sequence\":59,\"source\":{\"game_version\":\"1.20.0.4\","
        "\"executable_sha256\":\"98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518\"},"
        "\"native_readiness\":{\"current_strength\":true,\"full_monthly\":false},\"army_strengths\":["
           << row << "]}\n";
    if (!output) throw std::runtime_error("compiled-effect new whole query wire write failed");
    std::cout << "new compiled-effect journal to production Army query wire GREEN; synthetic offline; original_calls=2\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
