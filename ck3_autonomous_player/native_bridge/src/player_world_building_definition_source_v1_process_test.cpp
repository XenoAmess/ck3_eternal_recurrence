#include "player_world_building_definition_source_v1_process.hpp"

#include <cstdint>
#include <cstdlib>
#include <iostream>

namespace {

constexpr std::uintptr_t kPredicateRva = 0x295CD60;
bool g_called = false;

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
  std::cout << "GREEN private stock player final legality process binding\n";
  return 0;
}
