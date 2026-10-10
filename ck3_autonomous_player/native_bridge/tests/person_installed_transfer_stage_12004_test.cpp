#include "xar_bridge/person_installed_transfer_stage_12004.hpp"

#include <array>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <utility>
#include <vector>

namespace {
using namespace xar::ck3_12004;

void Require(bool value, const char *message) {
  if (!value)
    throw std::runtime_error(message);
}

struct World {
  std::array<std::byte, 0x2F8> a{}, b{}, other_model{};
  std::array<std::byte, 0x1B8> owner{}, other_owner{};
  std::array<std::byte, 0x260> carrier{};
  std::vector<std::pair<std::uintptr_t, std::size_t>> reads;
  std::uintptr_t unread_address = 0;
  std::uint32_t original_calls = 0;
  std::uint64_t event_sequence = 100;
  bool change_generation = false;
  bool mismatch_clock = false;
  bool exchange_owner = false;
  PersonInstalledTransferPreparation12004 preparation;

  template <class T, std::size_t N>
  void Put(std::array<std::byte, N> &block, std::size_t offset, T value) {
    std::memcpy(block.data() + offset, &value, sizeof(value));
  }
  template <std::size_t N>
  std::uintptr_t Address(std::array<std::byte, N> &block) {
    return reinterpret_cast<std::uintptr_t>(block.data());
  }
  World() {
    Put(owner, 0x18, std::uint32_t{0xAB007485});
    Put(other_owner, 0x18, std::uint32_t{0xCD007485});
    Put(owner, 0x1B0, Address(carrier));
    Put(carrier, 0x258, Address(a));
    Put(a, 0x8, Address(owner));
    Put(b, 0x8, Address(owner));
    Put(other_model, 0x8, Address(owner));
    preparation.observed = true;
    preparation.preparation_capture_complete = true;
    preparation.preparation_capture_sequence = 7;
    preparation.preparation_capture_thread_id = 44;
    preparation.preparation_completion_thread_id = 44;
    preparation.preparation_character_identity = Address(owner);
    preparation.preparation_model_identity = Address(b);
    preparation.preparation_context_identity = Address(b) + 0x10;
    preparation.preparation_owner_character_identity = Address(owner);
    preparation.preparation_owner_character_id = 0xAB007485;
  }
  bool Read(std::uintptr_t address, void *output, std::size_t size) noexcept {
    reads.emplace_back(address, size);
    if (address == unread_address)
      return false;
    for (const auto &block : {
             std::pair{Address(a), a.size()}, std::pair{Address(b), b.size()},
             std::pair{Address(other_model), other_model.size()},
             std::pair{Address(owner), owner.size()},
             std::pair{Address(other_owner), other_owner.size()},
             std::pair{Address(carrier), carrier.size()}}) {
      if (address >= block.first && address - block.first <= block.second &&
          size <= block.second - (address - block.first)) {
        std::memcpy(output, reinterpret_cast<const void *>(address), size);
        return true;
      }
    }
    return false;
  }
  PersonInstalledTransferBindings12004 Bindings() {
    PersonInstalledTransferBindings12004 result;
    result.read_context = this;
    result.read = [](void *context, std::uintptr_t address, void *output,
                     std::size_t size) noexcept {
      return static_cast<World *>(context)->Read(address, output, size);
    };
    result.preparation_context = this;
    result.read_preparation = [](void *context, std::uintptr_t,
                                 std::uint32_t) noexcept {
      return static_cast<World *>(context)->preparation;
    };
    result.event_context = this;
    result.next_event = [](void *context) noexcept {
      auto &world = *static_cast<World *>(context);
      const auto sequence = ++world.event_sequence;
      return PersonInstalledTransferEvent12004{
          sequence == 102 && world.mismatch_clock ? 2U : 1U, sequence, 44};
    };
    return result;
  }
};

World *active_world = nullptr;
#if defined(_MSC_VER)
std::uintptr_t __fastcall Original(void *a, void *b) {
#else
std::uintptr_t Original(void *a, void *b) {
#endif
  auto &world = *active_world;
  Require(a == world.a.data() && b == world.b.data(),
          "original arguments must be the actual A/B addresses");
  ++world.original_calls;
  // Only identity mutation is modelled. No generic PC exchange is simulated.
  if (world.exchange_owner) {
    std::uintptr_t owner_a = 0, owner_b = 0;
    std::memcpy(&owner_a, world.a.data() + 0x8, sizeof(owner_a));
    std::memcpy(&owner_b, world.b.data() + 0x8, sizeof(owner_b));
    world.Put(world.a, 0x8, owner_b);
    world.Put(world.b, 0x8, owner_a);
  }
  if (world.change_generation)
    world.Put(world.owner, 0x18, std::uint32_t{0xCD007485});
  world.preparation.preparation_model_identity = world.Address(world.other_model);
  world.preparation.preparation_owner_character_id = 0;
  return std::uintptr_t{0xFEDCBA9876543210ULL};
}

PersonInstalledTransferInvocation12004 Run(World &world,
                                           std::uintptr_t return_rva) {
  active_world = &world;
  return InvokePersonInstalledTransferStage12004(
      world.Bindings(), Original, world.a.data(), world.b.data(), return_rva);
}

void Compound() {
  World positive;
  const auto captured = Run(positive, kPersonInstalledTransferCallerReturnRva12004);
  Require(positive.original_calls == 1 && captured.stage.original_returned,
          "natural original must run once and return");
  Require(captured.raw_return_bits == 0xFEDCBA9876543210ULL,
          "all original return bits must survive");
  Require(captured.stage.preparation_model_is_b == true &&
              captured.stage.after.installed_model_is_a == true &&
              captured.stage.after.installed_model_is_b == false &&
              captured.stage.after.installed_owner_matches_observed_owner == true,
          "prepared B and installed A are distinct actual identities");
  Require(captured.stage.preparation.preparation_capture_sequence == 7 &&
              captured.stage.preparation.preparation_capture_complete &&
              captured.stage.preparation.preparation_completion_thread_id == std::uint32_t{44} &&
              captured.stage.preparation.preparation_character_identity ==
                  positive.Address(positive.owner) &&
              captured.stage.preparation.preparation_model_identity ==
                  positive.Address(positive.b) &&
              captured.stage.preparation_owner_matches_before == true &&
              captured.stage.preparation_owner_matches_after == true,
          "preparation lineage copy must survive original mutation");
  Require(captured.stage.completion_ordered_after_begin == true,
          "one supplied clock must order the original completion");
  positive.Put(positive.carrier, 0x258, positive.Address(positive.other_model));
  Require(captured.stage.after.installed_model_identity == positive.Address(positive.a),
          "query must use the immutable captured installed identity");

  World owner_exchange;
  owner_exchange.exchange_owner = true;
  owner_exchange.Put(owner_exchange.a, 0x8,
                     owner_exchange.Address(owner_exchange.other_owner));
  const auto exchanged =
      Run(owner_exchange, kPersonInstalledTransferCallerReturnRva12004);
  Require(exchanged.stage.before.installed_owner_matches_observed_owner == false &&
              exchanged.stage.after.installed_owner_matches_observed_owner == true &&
              exchanged.stage.after.model_b_owner_identity ==
                  owner_exchange.Address(owner_exchange.other_owner) &&
              exchanged.stage.after.observed_owner_identity ==
                  owner_exchange.Address(owner_exchange.owner) &&
              exchanged.stage.preparation_owner_matches_after == true,
          "after snapshot must retain original B owner when native owner exchange changes B");

  World same_owner;
  same_owner.preparation.preparation_model_identity =
      same_owner.Address(same_owner.other_model);
  const auto mismatch = Run(same_owner, kPersonInstalledTransferCallerReturnRva12004);
  Require(mismatch.stage.preparation_owner_matches_before == true &&
              mismatch.stage.preparation_model_is_b == false,
          "same full owner does not establish preparation Model equality");

  World partial;
  partial.unread_address = partial.Address(partial.b) + 0x8;
  const auto unread = Run(partial, kPersonInstalledTransferCallerReturnRva12004);
  Require(partial.original_calls == 1 && unread.stage.original_returned &&
              !unread.stage.preparation_model_is_b &&
              !unread.stage.before.observed_owner_identity &&
              unread.stage.before.model_a_owner_identity.has_value(),
          "unread B owner must stay missing without blocking the original or A");

  World no_carrier;
  no_carrier.Put(no_carrier.owner, 0x1B0, std::uintptr_t{0});
  const auto absent = Run(no_carrier, kPersonInstalledTransferCallerReturnRva12004);
  Require(no_carrier.original_calls == 1 &&
              absent.stage.after.installed_model_identity == std::uintptr_t{0} &&
              absent.stage.after.installed_model_is_a == false &&
              absent.stage.after.installed_model_is_b == false &&
              !absent.stage.after.installed_owner_matches_observed_owner,
          "known absent carrier is null without acquiring a Model association");

  World generation;
  generation.change_generation = true;
  generation.mismatch_clock = true;
  const auto changed = Run(generation, kPersonInstalledTransferCallerReturnRva12004);
  Require(changed.stage.before_after_owner_generation_equal == false &&
              changed.stage.preparation_owner_matches_after == false &&
              changed.stage.event_clock_and_thread_match == false &&
              !changed.stage.completion_ordered_after_begin,
          "generation and clock mismatches must not acquire lineage/order");

  World other_caller;
  const auto ignored = Run(other_caller, kPersonInstalledTransferCallerReturnRva12004 + 1);
  Require(other_caller.original_calls == 1 && other_caller.reads.empty() &&
              !ignored.stage.observed && ignored.stage.original_returned,
          "another natural caller still runs once without identity capture");
}
} // namespace

int main() {
  try {
    Compound();
    std::cout << "GREEN: installed-transfer identity compound, synthetic memory only\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "RED: " << error.what() << '\n';
    return 1;
  }
}
