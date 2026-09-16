#include "player_world_building_definition_source_v1_process.hpp"

#include <cstdint>
#include <cstdlib>
#include <array>
#include <cstring>
#include <iostream>

namespace {

constexpr std::uintptr_t kPredicateRva = 0x295CD60;
constexpr std::uintptr_t kCostRva = 0x29190F0;
bool g_called = false;
bool g_cost_called = false;
std::array<std::uint8_t, 0x6F5A0> g_definition{};
std::array<std::uint8_t, 0x20> g_province{};

template <typename T>
void Put(std::uint8_t *data, std::size_t offset, T value) {
  std::memcpy(data + offset, &value, sizeof(value));
}

std::int64_t *FakeStockBuildingCost(std::int64_t *output,
                                    const void *province,
                                    const void *cost_field,
                                    const void *building_context) {
  g_cost_called = province == g_province.data() &&
      cost_field == g_definition.data() + 0x6F590 &&
      building_context == reinterpret_cast<const void *>(0xABC000);
  for (std::int64_t index = 0; index < 10; ++index) {
    output[index] = (index + 1) * 100000;
  }
  return output;
}

bool FakeStockPlayerCanConstruct(std::int32_t actor, std::int32_t province,
                                 const void *definition, std::int32_t slot,
                                 bool stock_flag, const void *stock_context) {
  g_called = true;
  return actor == 29829 && province == 2619 &&
         reinterpret_cast<std::uintptr_t>(definition) == 0xB10000 &&
         slot == 1 && stock_flag && stock_context == nullptr;
}

void Require(bool value, const char *name) {
  if (!value) {
    std::cerr << "RED " << name << '\n';
    std::abort();
  }
}

} // namespace

int main() {
  using namespace xar::ck3_11906;
  PlayerWorldBuildingNativeCallAccessV1 native{};
  Require(BindCurrentProcessPlayerWorldBuildingFinalLegalityV1(native) ==
              nullptr,
          "default_unbound");
  native.module_base = reinterpret_cast<std::uintptr_t>(
                           &FakeStockPlayerCanConstruct) -
                       kPredicateRva;
  native.exact_build_admitted = true;
  auto callback = BindCurrentProcessPlayerWorldBuildingFinalLegalityV1(native);
  Require(callback != nullptr, "exact_binding_available");
  bool allowed = false;
  Require(callback(&native, 29829, 2619, 0xB10000, 1, allowed) &&
              allowed && g_called,
          "stock_six_arguments_and_true_result");
  native.exact_build_admitted = false;
  allowed = true;
  Require(!callback(&native, 29829, 2619, 0xB10000, 1, allowed) &&
              !allowed,
          "no_call_without_exact_build_admission");
  Put(g_province.data(), 0x10, std::int32_t{2619});
  Put(g_definition.data(), 0x10, std::int32_t{22});
  Put(g_definition.data(), 0x6F588, std::uintptr_t{0xABC000});
  PlayerWorldBuildingNativeCallAccessV1 cost_native{};
  Require(BindCurrentProcessPlayerWorldBuildingCostV1(cost_native) == nullptr,
          "default_cost_unbound");
  cost_native.module_base = reinterpret_cast<std::uintptr_t>(
                                &FakeStockBuildingCost) - kCostRva;
  cost_native.exact_build_admitted = true;
  auto cost_callback = BindCurrentProcessPlayerWorldBuildingCostV1(cost_native);
  Require(cost_callback != nullptr, "exact_cost_binding_available");
  std::array<std::int64_t, 10> raw_native{};
  Require(cost_callback(&cost_native, 29829, 2619,
                        reinterpret_cast<std::uintptr_t>(g_province.data()),
                        22,
                        reinterpret_cast<std::uintptr_t>(g_definition.data()),
                        1, raw_native) && g_cost_called &&
              raw_native == std::array<std::int64_t, 10>{
                  100000, 200000, 300000, 400000, 500000,
                  600000, 700000, 800000, 900000, 1000000},
          "stock_cost_four_arguments_and_complete_native_eighty_bytes");
  cost_native.exact_build_admitted = false;
  raw_native.fill(-1);
  Require(!cost_callback(&cost_native, 29829, 2619,
                         reinterpret_cast<std::uintptr_t>(g_province.data()),
                         22,
                         reinterpret_cast<std::uintptr_t>(g_definition.data()),
                         1, raw_native) && raw_native ==
                             std::array<std::int64_t, 10>{},
          "no_cost_call_without_exact_build_admission");
  std::cout << "GREEN private stock player final legality process binding\n";
  return 0;
}
