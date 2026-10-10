#include "xar_bridge/person_installed_transfer_capture_12004.hpp"
#include "xar_bridge/ck3_12004_person_six_stage_capture.hpp"
#include "xar_bridge/ck3_12004_knight_stat_consumption.hpp"
#include "xar_bridge/ck3_12004.hpp"

#include <array>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <utility>

namespace xar::ck3_12004 {
void RunPersonTransferPostimageCrossblockCases12004();
}

namespace {
using namespace xar::ck3_12004;
constexpr std::uintptr_t kCallRva = 0x2A3DC44;
constexpr std::uintptr_t kReturnBits = 0xFEDCBA9876543210ULL;
constexpr std::array<std::uint8_t, 15> kAnchor{
    0x48,0x89,0x5C,0x24,0x10,0x48,0x89,0x6C,0x24,0x18,
    0x48,0x89,0x74,0x24,0x20};
void Require(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}
struct World {
  std::array<std::byte, 0x2F8> a{}, b{};
  std::array<std::byte, 0x1D0> owner{}, other_owner{};
  std::array<std::byte, 0x260> carrier{};
  std::array<PersonTransferBlock10Row12004, 3> rows_a{}, rows_b{};
  std::array<std::uint16_t, 3> keys_a{}, keys_b{};
  std::array<std::uint64_t, 3> values_a{}, values_b{}, tail_a{}, tail_b{};
  std::array<std::byte, 0x10> game_state{};
  std::array<std::byte, 0x38> output{};
  void *game_state_pointer = game_state.data();
  std::int32_t damage_multiplier = 100, toughness_multiplier = 10;
  std::uintptr_t image_base = 0;
  std::uint64_t preparation_sequence = 0;
  std::uint32_t preparation_original_calls = 0;
  std::uint32_t wrapper_original_calls = 0, getter_original_calls = 0;
  PersonInstalledTransferRead12004 guarded_read = nullptr;
  std::uintptr_t unread_before_address = 0;
  bool original_returned = false;
  std::uint32_t original_calls = 0;
  std::uint32_t physical_reads = 0;
  template<class T, std::size_t N>
  void Put(std::array<std::byte, N> &block, std::size_t offset, T value) {
    std::memcpy(block.data() + offset, &value, sizeof(value));
  }
  template<class T, std::size_t N>
  std::uintptr_t Address(std::array<T, N> &block) {
    return reinterpret_cast<std::uintptr_t>(block.data());
  }
  template<std::size_t N>
  void Header(std::array<std::byte, N> &model, std::size_t offset,
              std::uintptr_t data) {
    Put(model, offset, data);
    Put(model, offset + 8, std::int32_t{4});
    Put(model, offset + 0xC, std::int32_t{3});
  }
  void Reset() {
    original_returned = false;
    unread_before_address = 0;
    physical_reads = 0;
    rows_a = {}; rows_b = {};
    for (std::size_t i = 0; i != rows_a.size(); ++i) {
      const auto a_weight = static_cast<std::uint64_t>(i + 1);
      const auto b_weight = std::uint64_t{0x8000000000000000ULL} + i;
      std::memcpy(rows_a[i].data() + 8, &a_weight, sizeof(a_weight));
      std::memcpy(rows_b[i].data() + 8, &b_weight, sizeof(b_weight));
    }
    keys_a = {0, 1, 1}; keys_b = {65535, 65535, 0};
    values_a = {1, 2, 3};
    values_b = {0x8000000000000000ULL, 0xFFFFFFFFFFFFFFFFULL, 0x7FFFFFFFFFFFFFFFULL};
    tail_a = {7, 0, 0}; tail_b = {0x7FF8000000000042ULL, 0x8000000000000000ULL, 0};
    Header(a, 0x10, Address(rows_a)); Header(b, 0x10, Address(rows_b));
    Header(a, 0x78, Address(keys_a)); Header(b, 0x78, Address(keys_b));
    Header(a, 0xE0, Address(values_a)); Header(b, 0xE0, Address(values_b));
    Header(a, 0x248, Address(tail_a)); Header(b, 0x248, Address(tail_b));
    Put(a, 0x258, std::uintptr_t{0xA110}); Put(b, 0x258, std::uintptr_t{0xB110});
    Put(a, 0x260, std::uintptr_t{0xA118}); Put(b, 0x260, std::uintptr_t{0xB118});
    Put(owner, 0x18, std::uint32_t{0xAB007485});
    Put(other_owner, 0x18, std::uint32_t{0xCD007485});
    Put(owner, 0x1B0, Address(carrier)); Put(carrier, 0x258, Address(a));
    Put(a, 8, Address(other_owner)); Put(b, 8, Address(owner));
  }
  static bool Read(void *context, std::uintptr_t source,
                   void *destination, std::size_t bytes) noexcept {
    auto &world = *static_cast<World *>(context);
    // Synthetic backing for the existing Native65 reached property-key table.
    // No image byte is loaded or read, and no threshold table is fabricated.
    for (std::size_t index = 0; index != 6; ++index) {
      if (source == world.image_base + 0x4807608 + index * 8 &&
          bytes == sizeof(std::uint16_t)) {
        const auto key = static_cast<std::uint16_t>(0xC1 + index);
        std::memcpy(destination, &key, sizeof(key));
        return true;
      }
    }
    if ((source >= world.Address(world.a) + 0x10 && source < world.Address(world.a) + 0x278) ||
        (source >= world.Address(world.b) + 0x10 && source < world.Address(world.b) + 0x278) ||
        source == world.Address(world.values_a) || source == world.Address(world.values_b))
      ++world.physical_reads;
    if (!world.original_returned && world.unread_before_address == source) return false;
    return world.guarded_read(nullptr, source, destination, bytes);
  }
  static bool NativeRead(void *context, const void *source,
                         void *destination, std::size_t bytes) noexcept {
    return Read(context, reinterpret_cast<std::uintptr_t>(source), destination, bytes);
  }
};
World *g_world = nullptr;
std::uintptr_t __fastcall Original(void *a, void *b) {
  auto &world = *g_world;
  Require(a == world.a.data() && b == world.b.data(), "original receivers remain exact");
  ++world.original_calls;
  std::uintptr_t owner_a = 0, owner_b = 0;
  std::memcpy(&owner_a, world.a.data() + 8, sizeof(owner_a));
  std::memcpy(&owner_b, world.b.data() + 8, sizeof(owner_b));
  world.Put(world.a, 8, owner_b); world.Put(world.b, 8, owner_a);
  std::swap(world.rows_a, world.rows_b);
  std::swap(world.keys_a, world.keys_b);
  std::swap(world.values_a, world.values_b);
  std::swap(world.tail_a, world.tail_b);
  world.original_returned = true;
  return kReturnBits;
}
std::uintptr_t __fastcall PreparationOriginal(void *character, void *context,
                                             std::uint32_t index) {
  auto &world = *g_world;
  Require(character == world.owner.data() && context == world.b.data() + 0x10 &&
          index == world.preparation_original_calls,
          "new coupled preparation callback receives exact owner/B/index");
  ++world.preparation_original_calls;
  return 42;
}
std::uintptr_t __fastcall AppendOriginal(void *, void *, std::int64_t) { return 0; }
void *__fastcall GetterOriginal(void *character) {
  auto &world = *g_world;
  Require(character == world.owner.data(), "actual Ci getter receives exact selected owner");
  ++world.getter_original_calls;
  return world.a.data() + 0x10;
}
void *__fastcall WrapperOriginal(void *output, void *linked) {
  auto &world = *g_world;
  Require(output == world.output.data() && linked == world.owner.data(),
          "actual wrapper preserves output/linked receiver");
  ++world.wrapper_original_calls;
  Require(InvokeKnightStatContext12004(linked,
          world.image_base + kKnightStatContextReturns12004.front()) == world.a.data() + 0x10,
          "same Ci getter return preserved");
  return output;
}
void Jump(std::uint8_t *output, std::uintptr_t target) {
  constexpr std::array<std::uint8_t, 6> prefix{0xFF,0x25,0,0,0,0};
  std::memcpy(output, prefix.data(), prefix.size());
  std::memcpy(output + prefix.size(), &target, sizeof(target));
}
struct Arena {
  void *reservation = nullptr;
  std::uintptr_t base = 0;
  std::uint8_t *target = nullptr;
  PersonInstalledTransferOriginal12004 caller = nullptr;
  Arena() {
    reservation = VirtualAlloc(nullptr, 0x2A3E000, MEM_RESERVE, PAGE_NOACCESS);
    Require(reservation != nullptr, "reserve synthetic actual-RVA arena");
    base = reinterpret_cast<std::uintptr_t>(reservation);
    target = reinterpret_cast<std::uint8_t *>(base + kPersonInstalledTransferRva12004);
    for (const auto page : {base + 0x291C000, base + 0x2A3D000})
      Require(VirtualAlloc(reinterpret_cast<void *>(page), 0x1000, MEM_COMMIT,
                           PAGE_READWRITE) != nullptr, "commit two synthetic code pages");
    std::memcpy(target, kAnchor.data(), kAnchor.size());
    Jump(target + 15, reinterpret_cast<std::uintptr_t>(&Original));
    auto *entry = reinterpret_cast<std::uint8_t *>(base + kCallRva - 4);
    constexpr std::array<std::uint8_t, 4> sub{0x48,0x83,0xEC,0x28};
    constexpr std::array<std::uint8_t, 5> finish{0x48,0x83,0xC4,0x28,0xC3};
    std::memcpy(entry, sub.data(), sub.size()); entry[4] = 0xE8;
    const auto relative = static_cast<std::int32_t>(
        static_cast<std::intptr_t>(base + kPersonInstalledTransferRva12004) -
        static_cast<std::intptr_t>(base + kCallRva + 5));
    std::memcpy(entry + 5, &relative, sizeof(relative));
    std::memcpy(entry + 9, finish.data(), finish.size());
    for (const auto page : {base + 0x291C000, base + 0x2A3D000}) {
      DWORD previous = 0;
      Require(VirtualProtect(reinterpret_cast<void *>(page), 0x1000,
              PAGE_EXECUTE_READ, &previous) != FALSE, "protect synthetic code");
      Require(FlushInstructionCache(GetCurrentProcess(), reinterpret_cast<void *>(page),
              0x1000) != FALSE, "flush synthetic code");
    }
    caller = reinterpret_cast<PersonInstalledTransferOriginal12004>(entry);
  }
  ~Arena() { if (reservation) VirtualFree(reservation, 0, MEM_RELEASE); }
};
void ConnectedPhysicalCapture() {
  World world; world.Reset(); g_world = &world;
  Arena arena;
  PersonInstalledTransferCaptureInstall12004 environment;
  environment.primary_thread_suspended_proven = true;
  environment.offline_fixture = true;
  environment.module_base = arena.base;
  environment.bindings = BindPersonInstalledTransferCaptureImage12004(
      arena.base, kPersonInstalledTransferCaptureExeSha12004);
  world.guarded_read = environment.bindings.read;
  environment.bindings.read = World::Read;
  environment.bindings.read_context = &world;
  world.image_base = arena.base;
  // Prepare using the qualified Native65 producer on the same fixture thread.
  // Its synthetic source property keys are bounded above; Character extension
  // is known null during capture, then the transfer carrier is published.
  world.Put(world.owner, 0x1B0, std::uintptr_t{0});
  PersonSixStageCaptureBindings12004 preparation;
  preparation.memory = BindPersonCarrierDirect12004(
      arena.base, kGameVersion, kExecutableSha256, World::NativeRead, &world);
  preparation.game_state_slot = &world.game_state_pointer;
  Require(InitializePersonSixStageCaptureFixture12004(
          preparation, PreparationOriginal, AppendOriginal), "bind existing owned Native65 producer");
  for (std::uint32_t index = 0; index != 6; ++index)
    Require(InvokePersonSixStageCapture12004(world.owner.data(), world.b.data() + 0x10,
            index, arena.base + kPersonSixStageReturnRva12004) == std::uintptr_t{42},
            "new coupled preparation preserves original result");
  CompletePersonSixStageCapture12004(world.Address(world.owner), 0xAB007485,
                                     world.Address(world.b) + 0x10);
  const auto completed = ReadPersonSixStageCaptureForCharacter12004(
      world.Address(world.owner), 0xAB007485);
  Require(completed.capture_observed && completed.capture_complete &&
          completed.post_six_aggregate.observed && completed.post_six_aggregate.pc.ready,
          "actual owned completed preparation contains copied post-PC");
  world.preparation_sequence = completed.capture_sequence;
  world.Put(world.owner, 0x1B0, world.Address(world.carrier));
  auto knight = BindKnightStatConsumptionImage12004(arena.base, kExecutableSha256);
  knight.game_state_slot = &world.game_state_pointer;
  knight.damage_multiplier = &world.damage_multiplier;
  knight.toughness_multiplier = &world.toughness_multiplier;
  knight.read_context = &world; knight.read_memory = World::NativeRead;
  Require(InitializeKnightStatConsumptionFixture12004(knight, WrapperOriginal, GetterOriginal),
          "bind new consumed physical record path");
  PersonInstalledTransferCaptureState12004 state;
  Require(InstallPersonInstalledTransferCapture12004(state, environment,
          kPersonInstalledTransferCaptureExeSha12004), "install connected physical observer");
  Require(arena.caller(world.a.data(), world.b.data()) == kReturnBits && world.original_calls == 1,
          "installed same original executes once and preserves raw return");
  auto owned = ReadPersonInstalledTransferCaptureForOwner12004(
      world.Address(world.owner), 0xAB007485);
  Require(owned && owned->physical_postimage, "retained owner record owns physical copies");
  const auto &physical = *owned->physical_postimage;
  Require(physical.comparison.same_original_observation_ready &&
          physical.comparison.four_block_payload_exchange_observed &&
          physical.comparison.four_block_operand_copies_complete,
          "actual installed before/return snapshots compose same occurrence across four blocks");
  Require(physical.comparison.block78_keys.descriptor_cross_equal == false &&
          physical.comparison.blocke0_values.descriptor_cross_equal == false,
          "in-place payload exchange does not require descriptor swap");
  Require(physical.before.b.block78_keys.raw.keys_u16 ==
          std::vector<std::uint16_t>({65535, 65535, 0}) &&
          physical.after.a.blocke0_values.values_q64_raw_bits ==
          std::vector<std::uint64_t>({0x8000000000000000ULL, 0xFFFFFFFFFFFFFFFFULL,
                                      0x7FFFFFFFFFFFFFFFULL}),
          "ordered keys and exact Q64 bits survive original boundary");
  Require(physical.before.b.scope.occurrence.sequence == owned->stage.before_event.sequence &&
          physical.after.a.scope.event.sequence == owned->stage.completed_event.sequence &&
          owned->stage.preparation.preparation_capture_sequence == world.preparation_sequence,
          "same shared events and immutable borrowed preparation remain separate domains");
  PersonInstalledTransferCaptureQuery12004 local;
  local.records.push_back(*owned);
  auto wire = SerializePersonInstalledTransferCapture12004(local);
  Require(wire.find("\"physical_postimage\":{") != std::string::npos &&
          wire.find("\"0x8000000000000000\"") != std::string::npos &&
          wire.find("\"four_block_payload_exchange_observed\":true") != std::string::npos &&
          wire.find("\"retained_preparation_numeric_payload_compared\":false") != std::string::npos,
          "actual copied full wire preserves exact bits and qualification");
  std::cout << "WIRE_PHYSICAL_FULL " << wire << '\n';
  {
    KnightStatBridgeQueryScope12004 scope(world.output.data(), 1, 2);
    Require(InvokeKnightStatWrapper12004(world.output.data(), world.owner.data(),
            arena.base) == world.output.data(), "preserve wrapper output with newly owned physical Ci");
  }
  const std::array regiments{std::int32_t{1}};
  const std::array linked{static_cast<std::int32_t>(std::uint32_t{0xAB007485})};
  const auto consumption = ReadKnightStatConsumptionQuery12004(regiments, linked);
  Require(consumption && consumption->events.size() == 1 &&
          consumption->events.front().contexts.size() == 1 &&
          world.wrapper_original_calls == 1 && world.getter_original_calls == 1,
          "same production consumption path retains exactly one new Ci");
  const auto &ci = consumption->events.front().contexts.front();
  Require(ci.installed_transfer_lineage &&
          ci.installed_transfer_lineage->physical_postimage_owned_at_consumption == true &&
          ci.installed_transfer_lineage->installed_identity_associated &&
          ci.installed_transfer_lineage->capture_at_consumption &&
          ci.installed_transfer_lineage->capture_at_consumption->find(
              "\"physical_postimage\":{") != std::string::npos &&
          ci.preparation_capture_at_consumption &&
          ci.preparation_capture_at_consumption->capture_sequence == world.preparation_sequence &&
          ci.preparation_capture_at_consumption->post_six_aggregate.pc.ready && ci.consumed_pc.ready,
          "new57c presence marker and full physical wire come from same before-getter owned record");
  Require(ci.consumed_pc.properties == completed.post_six_aggregate.pc.properties &&
          ci.consumed_pc.count_i32 == completed.post_six_aggregate.pc.count_i32 &&
          ci.consumed_pc.identity != completed.post_six_aggregate.pc.identity &&
          ci.preparation_stage_lineage &&
          !ci.preparation_stage_lineage->completed_preparation_lineage_proven,
          "copied numeric PC survives transfer without relabeling historical B context as direct A");
  const auto consumption_wire = SerializeKnightStatConsumptionQuery12004(*consumption);
  std::cout << "WIRE_CONSUMPTION_PHYSICAL " << consumption_wire << '\n';
  world.values_a.fill(42); world.keys_b.fill(9);
  Require(owned->physical_postimage->after.a.blocke0_values.values_q64_raw_bits->front() ==
          0x8000000000000000ULL, "retained physical copies are immutable after later memory mutation");

  world.Reset(); world.unread_before_address = world.Address(world.b) + 0xE8;
  Require(arena.caller(world.a.data(), world.b.data()) == kReturnBits && world.original_calls == 2,
          "partial descriptor remains original-once");
  owned = ReadPersonInstalledTransferCaptureForOwner12004(world.Address(world.owner), 0xAB007485);
  Require(owned && owned->physical_postimage &&
          !owned->physical_postimage->before.b.blocke0_values.raw.capacity_i32 &&
          owned->physical_postimage->comparison.four_block_payload_exchange_observed &&
          !owned->physical_postimage->comparison.four_block_operand_copies_complete,
          "missing capacity preserves full independently read ordered payload exchange");
  local.records.clear(); local.records.push_back(*owned);
  std::cout << "WIRE_PHYSICAL_DESCRIPTOR_PARTIAL "
            << SerializePersonInstalledTransferCapture12004(local) << '\n';

  world.Reset(); world.unread_before_address = world.Address(world.values_b);
  Require(arena.caller(world.a.data(), world.b.data()) == kReturnBits && world.original_calls == 3,
          "partial payload remains original-once");
  owned = ReadPersonInstalledTransferCaptureForOwner12004(world.Address(world.owner), 0xAB007485);
  Require(owned && owned->physical_postimage &&
          owned->physical_postimage->before.b.blocke0_values.raw.count_i32 == std::int32_t{3} &&
          !owned->physical_postimage->before.b.blocke0_values.values_q64_raw_bits &&
          owned->physical_postimage->comparison.blocke0_values.a_payload_equals_b_before == std::nullopt &&
          owned->physical_postimage->comparison.blocke0_values.b_payload_equals_a_before == true &&
          owned->physical_postimage->comparison.block78_keys.payload_cross_equal == true,
          "one unread payload preserves opposite known direction and independent keys/count");
  local.records.clear(); local.records.push_back(*owned);
  std::cout << "WIRE_PHYSICAL_PAYLOAD_PARTIAL "
            << SerializePersonInstalledTransferCapture12004(local) << '\n';

  world.Reset();
  const auto count = ReadPersonInstalledTransferCapture12004().records.size();
  const auto direct = reinterpret_cast<PersonInstalledTransferOriginal12004>(arena.target);
  Require(direct(world.a.data(), world.b.data()) == kReturnBits && world.original_calls == 4 &&
          world.physical_reads == 0 && ReadPersonInstalledTransferCapture12004().records.size() == count,
          "other native caller does not borrow physical snapshots or retain a paired occurrence");
  const auto retained_consumption = ReadKnightStatConsumptionQuery12004(regiments, linked);
  Require(retained_consumption &&
          SerializeKnightStatConsumptionQuery12004(*retained_consumption) == consumption_wire,
          "later physical transfer records do not rewrite owned Ci payload");
  Require(UninstallPersonInstalledTransferCapture12004(state, true), "close synthetic installed observer");
}
} // namespace

int main() {
  try {
    xar::ck3_12004::RunPersonTransferPostimageCrossblockCases12004();
    ConnectedPhysicalCapture();
    std::cout << "GREEN: new crossblock10 plus installed physical capture/wire compound; synthetic memory only\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "RED: " << error.what() << '\n';
    return 1;
  }
}
