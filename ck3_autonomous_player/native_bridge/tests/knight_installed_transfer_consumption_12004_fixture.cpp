// New 57b compound: actual transfer dispatch -> owned-before-getter join -> retained wire.
#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12004_knight_stat_consumption.hpp"
#include "xar_bridge/ck3_12004_person_six_stage_capture.hpp"
#include "xar_bridge/person_installed_transfer_capture_12004.hpp"
#include <thread>

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace {
namespace native = xar::ck3_12004;
constexpr std::uintptr_t kImage = 0x140000000ULL;
constexpr std::int32_t kDate = 53236632;
constexpr std::uint32_t kLinked = 0x03000001;
constexpr std::uint32_t kSelectedA = 0x04000002;
constexpr std::uint32_t kSelectedB = 0x05000003;
constexpr std::int32_t kRegiment = 0x06000004;
constexpr std::int32_t kTarget = 101;
constexpr std::uintptr_t kWrapperReturn = 0x2634509;
constexpr std::array<std::size_t, 6> kSkillOffsets{0xEC, 0xD8, 0xE4, 0xE8, 0xDC, 0xE0};
constexpr std::array<std::int32_t, 6> kSkills{-2, -3, 0, 4, -5, 6};
constexpr std::array<std::int64_t, 9> kOperands{
    100000, 0, 0, -200000, -300000, 0, 400000, -500000, 600000};
constexpr std::array<std::int64_t, 9> kMainModifiers{
    -25000, 0, 0, -10000, 0, 0, 0, 0, 0};
constexpr std::uintptr_t kCountReturn = 0xF123456700000000ULL;

void Require(bool value, const char *message) {
  if (!value) throw std::runtime_error(message);
}
template <typename Pointer>
std::uintptr_t Identity(Pointer value) noexcept {
  return reinterpret_cast<std::uintptr_t>(value);
}
void *Offset(void *value, std::size_t offset) noexcept {
  return static_cast<std::byte *>(value) + offset;
}

class Memory {
  struct Block {
    std::unique_ptr<std::byte[]> data;
    std::size_t size = 0;
    std::uintptr_t mapped_address = 0;
  };
  std::vector<Block> blocks_;
public:
  const void *refused_values = nullptr;
  std::size_t refused_reads = 0;
  std::size_t unexpected_reads = 0;
  std::size_t mapped_reads = 0;
  void *Allocate(std::size_t size) {
    auto data = std::make_unique<std::byte[]>(size);
    auto *address = data.get();
    blocks_.push_back({std::move(data), size});
    return address;
  }
  void *AllocateMapped(std::uintptr_t address, std::size_t size) {
    auto *backing = Allocate(size);
    blocks_.back().mapped_address = address;
    return backing;
  }
  template <typename Value>
  void Put(void *base, std::size_t offset, Value value) {
    std::memcpy(Offset(base, offset), &value, sizeof(value));
  }
  template <typename Value>
  Value Get(const void *base, std::size_t offset = 0) const {
    Value result{};
    std::memcpy(&result, static_cast<const std::byte *>(base) + offset, sizeof(result));
    return result;
  }
  static bool Copy(void *context, const void *address, void *output,
                   std::size_t size) noexcept {
    auto &memory = *static_cast<Memory *>(context);
    if (address == memory.refused_values && memory.refused_values != nullptr) {
      ++memory.refused_reads;
      return false;
    }
    const auto requested = Identity(address);
    for (const auto &block : memory.blocks_) {
      const auto base = block.mapped_address != 0
          ? block.mapped_address : Identity(block.data.get());
      if (requested >= base && requested - base <= block.size &&
          size <= block.size - (requested - base)) {
        std::memcpy(output, block.data.get() + (requested - base), size);
        if (block.mapped_address != 0) ++memory.mapped_reads;
        return true;
      }
    }
    ++memory.unexpected_reads;
    return false;
  }
};

struct Context {
  void *model = nullptr;
  void *context = nullptr;
  void *keys = nullptr;
  void *values = nullptr;
};

struct World {
  Memory memory;
  void *linked = memory.Allocate(0x1D0);
  void *selected_a = memory.Allocate(0x1D0);
  void *selected_b = memory.Allocate(0x1D0);
  void *game_state = memory.Allocate(0x10);
  void *game_slot = memory.Allocate(sizeof(void *));
  void *damage_coefficient = memory.Allocate(sizeof(std::int32_t));
  void *toughness_coefficient = memory.Allocate(sizeof(std::int32_t));
  void *query_output = memory.Allocate(0x38);
  void *native_output = memory.Allocate(0x38);
  void *piety_property_keys = memory.AllocateMapped(kImage + 0x4807608, 6 * 8);
  Context primary, alternate, second, installed_first, installed_second;
  void *carrier = memory.Allocate(0x260);
  std::size_t transfer_original_calls = 0;
  std::size_t preparation_original_calls = 0;
  std::size_t preparation_append_calls = 0;
  std::size_t wrapper_original_calls = 0;
  std::size_t context_original_calls = 0;
  std::size_t active_wrapper = 0;
  std::size_t active_key = 0;
  bool abi_matches = true;
  std::array<std::uintptr_t, 27> actual_context_returns{};

  World() {
    memory.Put(linked, 0x18, kLinked);
    memory.Put(linked, 0xEC, std::int32_t{3});
    memory.Put(selected_a, 0x18, kSelectedA);
    memory.Put(selected_b, 0x18, kSelectedB);
    for (auto *selected : {selected_a, selected_b}) {
      memory.Put(selected, 0x1C0, static_cast<void *>(nullptr));
      for (std::size_t index = 0; index < kSkillOffsets.size(); ++index)
        memory.Put(selected, kSkillOffsets[index], kSkills[index]);
    }
    memory.Put(game_slot, 0, game_state);
    memory.Put(game_state, 0x08, kDate);
    memory.Put(damage_coefficient, 0, std::int32_t{100});
    memory.Put(toughness_coefficient, 0, std::int32_t{10});
    // Native71 CopyPietyCategory owns this exact image-relative U16 table.
    // The fixture backs only the reached six keys, at native stride eight.
    for (std::size_t index = 0; index < 6; ++index)
      memory.Put(piety_property_keys, 8 * index, static_cast<std::uint16_t>(0xC1 + index));
    primary = MakeContext(selected_a, false);
    alternate = MakeContext(selected_a, true);
    second = MakeContext(selected_b, false);
    installed_first = MakeContext(linked, false);
    installed_second = MakeContext(linked, false);
  }

  Context MakeContext(void *owner, bool alternate_c5) {
    Context result;
    result.model = memory.Allocate(0x100);
    result.context = Offset(result.model, 0x10);
    result.keys = memory.Allocate(9 * sizeof(std::uint16_t));
    result.values = memory.Allocate(9 * sizeof(std::int64_t));
    memory.Put(result.model, 0x08, owner);
    auto *pc = Offset(result.context, 0x68);
    memory.Put(pc, 0x00, result.keys);
    memory.Put(pc, 0x0C, std::int32_t{9});
    memory.Put(pc, 0x68, result.values);
    for (std::size_t index = 0; index < 9; ++index) {
      memory.Put(result.keys, index * sizeof(std::uint16_t),
                 static_cast<std::uint16_t>(0xC1 + index));
      memory.Put(result.values, index * sizeof(std::int64_t),
                 alternate_c5 && index == 4 ? std::int64_t{15000}
                                            : kMainModifiers[index]);
    }
    return result;
  }
  Context &ReturnedContext() {
    if (active_wrapper >= 1) return second;
    return active_key == 4 ? alternate : primary;
  }
};

World *active = nullptr;
std::uintptr_t __fastcall TransferOriginal(void *a, void *b) {
  auto &world = *active;
  Require(b == world.primary.model &&
              (a == world.installed_first.model || a == world.installed_second.model),
          "transfer original A/B changed");
  ++world.transfer_original_calls;
  const auto owner_a = world.memory.Get<void *>(a, 8);
  const auto owner_b = world.memory.Get<void *>(b, 8);
  world.memory.Put(a, 8, owner_b);
  world.memory.Put(b, 8, owner_a);
  return 0xFEDCBA9876543210ULL;
}

void Jump(std::uint8_t *output, std::uintptr_t target) {
  constexpr std::array<std::uint8_t, 6> prefix{0xFF, 0x25, 0, 0, 0, 0};
  std::memcpy(output, prefix.data(), prefix.size());
  std::memcpy(output + prefix.size(), &target, sizeof(target));
}
struct TransferArena {
  void *reservation = nullptr;
  std::uintptr_t base = 0;
  native::PersonInstalledTransferOriginal12004 caller = nullptr;
  native::PersonInstalledTransferCaptureState12004 state;
  TransferArena() {
    reservation = VirtualAlloc(nullptr, 0x2A3E000, MEM_RESERVE, PAGE_NOACCESS);
    Require(reservation != nullptr, "reserve synthetic actual-RVA arena");
    base = Identity(reservation);
    for (const auto page : {base + 0x291C000, base + 0x2A3D000})
      Require(VirtualAlloc(reinterpret_cast<void *>(page), 0x1000, MEM_COMMIT,
                           PAGE_READWRITE) != nullptr, "commit synthetic code pages");
    auto *target = reinterpret_cast<std::uint8_t *>(base + native::kPersonInstalledTransferRva12004);
    constexpr std::array<std::uint8_t, 15> anchor{
        0x48,0x89,0x5C,0x24,0x10,0x48,0x89,0x6C,0x24,0x18,0x48,0x89,0x74,0x24,0x20};
    std::memcpy(target, anchor.data(), anchor.size());
    Jump(target + anchor.size(), Identity(&TransferOriginal));
    auto *entry = reinterpret_cast<std::uint8_t *>(base + 0x2A3DC44 - 4);
    constexpr std::array<std::uint8_t, 4> sub{0x48,0x83,0xEC,0x28};
    constexpr std::array<std::uint8_t, 5> finish{0x48,0x83,0xC4,0x28,0xC3};
    std::memcpy(entry, sub.data(), sub.size());
    entry[4] = 0xE8;
    const auto relative = static_cast<std::int32_t>(native::kPersonInstalledTransferRva12004 - 0x2A3DC49);
    std::memcpy(entry + 5, &relative, sizeof(relative));
    std::memcpy(entry + 9, finish.data(), finish.size());
    for (const auto page : {base + 0x291C000, base + 0x2A3D000}) {
      DWORD previous = 0;
      Require(VirtualProtect(reinterpret_cast<void *>(page), 0x1000,
                  PAGE_EXECUTE_READ, &previous) != FALSE, "protect synthetic actual CALL");
      Require(FlushInstructionCache(GetCurrentProcess(), reinterpret_cast<void *>(page), 0x1000) != FALSE,
              "flush synthetic actual CALL");
    }
    caller = reinterpret_cast<native::PersonInstalledTransferOriginal12004>(entry);
    native::PersonInstalledTransferCaptureInstall12004 environment;
    environment.primary_thread_suspended_proven = true;
    environment.offline_fixture = true;
    environment.module_base = base;
    environment.bindings = native::BindPersonInstalledTransferCaptureImage12004(
        base, native::kPersonInstalledTransferCaptureExeSha12004);
    Require(native::InstallPersonInstalledTransferCapture12004(
        state, environment, native::kPersonInstalledTransferCaptureExeSha12004),
        "install natural transfer on owned synthetic code");
  }
  ~TransferArena() {
    native::UninstallPersonInstalledTransferCapture12004(state, true);
    if (reservation) VirtualFree(reservation, 0, MEM_RELEASE);
  }
};
TransferArena *transfer_arena = nullptr;
void Transfer(Context &installed) {
  auto &world = *active;
  world.memory.Put(installed.model, 8, world.linked);
  world.memory.Put(world.primary.model, 8, world.selected_a);
  world.memory.Put(world.carrier, 0x258, installed.model);
  const auto calls = world.transfer_original_calls;
  Require(transfer_arena->caller(installed.model, world.primary.model) == 0xFEDCBA9876543210ULL &&
              world.transfer_original_calls == calls + 1,
          "new compound natural transfer changed original count or raw return");
}

std::uintptr_t __fastcall PreparationOriginal(void *character, void *context, std::uint32_t index) {
  auto &world = *active;
  world.abi_matches &= character == world.selected_a && context == world.primary.context &&
      index == world.preparation_original_calls;
  ++world.preparation_original_calls;
  return kCountReturn;
}
std::uintptr_t __fastcall PreparationAppendOriginal(void *, void *, std::int64_t) {
  ++active->preparation_append_calls;
  return 0;
}
Context &ExpectedContext() {
  auto &world = *active;
  if (world.active_key == 1) return world.alternate;
  if (world.active_key == 4) return world.second;
  return world.active_key == 0 || world.active_key == 8
      ? world.installed_first : world.installed_second;
}
void *__fastcall ContextOriginal(void *character) {
  auto &world = *active;
  ++world.context_original_calls;
  world.abi_matches &= character == (world.active_key == 4 ? world.selected_b : world.selected_a);
  if (world.active_key == 2) Transfer(world.installed_second);
  return ExpectedContext().context;
}
void *__fastcall WrapperOriginal(void *output, void *linked) {
  auto &world = *active;
  ++world.wrapper_original_calls;
  world.abi_matches &= output == world.query_output && linked == world.linked;
  for (std::size_t i = 0; i != 9; ++i) {
    world.active_key = i;
    if (i == 6) {
      std::thread other_thread([&]() { Transfer(world.installed_second); });
      other_thread.join();
    }
    if (i == 8) Transfer(world.installed_first);
    auto *selected = i == 4 ? world.selected_b : world.selected_a;
    if (i == 5) world.memory.Put(selected, 0x18, std::uint32_t{0x07000002});
    const auto before_calls = world.context_original_calls;
    auto *returned = native::InvokeKnightStatContext12004(
        selected, kImage + native::kKnightStatContextReturns12004[i]);
    Require(world.context_original_calls == before_calls + 1 && returned == ExpectedContext().context,
            "actual getter was repeated or its return changed");
    world.actual_context_returns[i] = Identity(returned);
    if (i == 5) world.memory.Put(selected, 0x18, kSelectedA);
  }
  world.memory.Put(output, 8, std::int32_t{0});
  for (std::size_t offset = 0x10; offset != 0x38; offset += 8)
    world.memory.Put(output, offset, std::int64_t{0});
  return output;
}
void Configure(World &world) {
  auto bindings = native::BindKnightStatConsumptionImage12004(kImage, native::kExecutableSha256);
  bindings.game_state_slot = reinterpret_cast<void **>(world.game_slot);
  bindings.damage_multiplier = static_cast<const std::int32_t *>(world.damage_coefficient);
  bindings.toughness_multiplier = static_cast<const std::int32_t *>(world.toughness_coefficient);
  bindings.read_context = &world.memory;
  bindings.read_memory = &Memory::Copy;
  native::PersonSixStageCaptureBindings12004 preparation;
  preparation.memory = native::BindPersonCarrierDirect12004(kImage,
      native::kGameVersion, native::kExecutableSha256, &Memory::Copy, &world.memory);
  preparation.game_state_slot = reinterpret_cast<void **>(world.game_slot);
  Require(native::InitializePersonSixStageCaptureFixture12004(preparation,
              &PreparationOriginal, &PreparationAppendOriginal), "initialize real preparation support");
  for (std::uint32_t i = 0; i != 6; ++i)
    Require(native::InvokePersonSixStageCapture12004(world.selected_a, world.primary.context,
        i, kImage + native::kPersonSixStageReturnRva12004) == kCountReturn,
        "new compound preparation returned wrong bits");
  native::CompletePersonSixStageCapture12004(Identity(world.selected_a), kSelectedA,
                                            Identity(world.primary.context));
  Require(native::InitializeKnightStatConsumptionFixture12004(bindings,
              &WrapperOriginal, &ContextOriginal), "initialize existing consumption dispatch");
}
void Write(const std::filesystem::path &path, std::string_view text) {
  Require(!std::filesystem::exists(path), "new output already exists");
  std::ofstream stream(path, std::ios::binary);
  stream << text << '\n';
  Require(static_cast<bool>(stream), "persist new output");
}
} // namespace
int main(int argc, char **argv) {
  try {
    Require(argc == 2, "usage: installed transfer consumption compound <fresh output directory>");
    const std::filesystem::path directory = argv[1];
    std::filesystem::create_directories(directory);
    World world;
    active = &world;
    Configure(world);
    // The transfer carrier is installed after the preparation callback setup.
    // Before this point the selected Character has the inherited known-null
    // piety extension; no unrelated image threshold table is claimed/backed.
    world.memory.Put(world.selected_a, 0x1B0, world.carrier);
    TransferArena arena;
    transfer_arena = &arena;
    Transfer(world.installed_first);
    {
      native::KnightStatBridgeQueryScope12004 scope(world.query_output, kRegiment, kTarget);
      Require(native::InvokeKnightStatWrapper12004(world.query_output, world.linked,
                  kImage + kWrapperReturn) == world.query_output,
              "existing original wrapper output changed");
    }
    const std::array regiment_ids{kRegiment};
    const std::array linked_ids{static_cast<std::int32_t>(kLinked)};
    const auto query = native::ReadKnightStatConsumptionQuery12004(regiment_ids, linked_ids);
    Require(query && query->events.size() == 1 && query->events.front().contexts.size() == 9,
            "compound retained consumption missing");
    const auto &event = query->events.front();
    Require(!event.entry_association_proven, "installed Ci association promoted physical Entry");
    for (std::size_t i = 0; i != 9; ++i) {
      const auto &context = event.contexts[i];
      Require(context.installed_transfer_lineage && context.preparation_stage_lineage &&
                  !context.preparation_stage_lineage->completed_preparation_lineage_proven &&
                  context.context_identity == world.actual_context_returns[i] &&
                  context.consumed_pc.identity == world.actual_context_returns[i] + 0x68,
              "new identity join relabeled direct preparation B or altered consumed PC");
      const auto &lineage = *context.installed_transfer_lineage;
      const bool positive = i == 0 || i == 3 || i == 8;
      Require(lineage.installed_identity_associated == positive &&
                  lineage.getter_begin_event.thread_id == event.thread_id &&
                  lineage.getter_completed_event.thread_id == event.thread_id &&
                  lineage.getter_begin_event.clock_identity != 0 &&
                  lineage.getter_begin_event.clock_identity == lineage.getter_completed_event.clock_identity &&
                  lineage.getter_begin_event.sequence < lineage.getter_completed_event.sequence,
              "clock/owner/context association did not match actual Ci case");
      if (i == 4 || i == 5)
        Require(!lineage.capture_at_consumption && !lineage.transfer_completed_before_getter,
                "different receiver or full generation borrowed older transfer record");
      else Require(lineage.capture_at_consumption.has_value(), "owned transfer sidecar missing");
      if (i == 1 || i == 2)
        Require(lineage.getter_matches_installed_context == false,
                "unrelated getter return borrowed latest installed context");
      if (i == 2)
        Require(lineage.capture_at_consumption->find("\"record_sequence\":1,") != std::string::npos,
                "transfer completed during getter replaced its before-getter record");
      if (i == 6 || i == 7)
        Require(lineage.transfer_completed_before_getter == false,
                "cross-thread completion became same-thread temporal evidence");
      if (i != 4 && i != 5)
        Require(context.preparation_capture_at_consumption &&
                    context.preparation_capture_at_consumption->context_identity == Identity(world.primary.context),
                "transfer erased owned B preparation capture");
    }
    const auto counters = std::string("new compound actual counters: wrapper=") +
        std::to_string(world.wrapper_original_calls) + " getter=" + std::to_string(world.context_original_calls) +
        " transfer=" + std::to_string(world.transfer_original_calls) +
        " preparation=" + std::to_string(world.preparation_original_calls) +
        " append=" + std::to_string(world.preparation_append_calls) +
        " reached_piety_key_reads=" + std::to_string(world.memory.mapped_reads) +
        " unexpected=" + std::to_string(world.memory.unexpected_reads) +
        " abi=" + std::to_string(world.abi_matches);
    Require(world.wrapper_original_calls == 1 && world.context_original_calls == 9 &&
                world.transfer_original_calls == 4 && world.preparation_original_calls == 6 &&
                world.preparation_append_calls == 0 && world.memory.mapped_reads == 6 &&
                world.memory.unexpected_reads == 0 && world.abi_matches, counters.c_str());
    std::cout << counters << '\n';
    const auto body = native::SerializeKnightStatConsumptionQuery12004(*query);
    // A later natural dispatch must not change the already retained event.
    Transfer(world.installed_second);
    const auto later = native::ReadKnightStatConsumptionQuery12004(regiment_ids, linked_ids);
    Require(later && *later == *query &&
                native::SerializeKnightStatConsumptionQuery12004(*later) == body,
            "later natural transfer rewrote owned historical Ci sidecar");
    native::KnightStatConsumptionQuery12004 legacy;
    legacy.events.emplace_back().contexts.emplace_back();
    Require(native::SerializeKnightStatConsumptionQuery12004(legacy).find("installed_transfer_lineage") == std::string::npos,
            "legacy absence changed");
    Write(directory / "knight-installed-transfer-consumption-12004.json", body);
    Write(directory / "knight-installed-transfer-consumption-12004-receipt.json",
        "{\"status\":\"GREEN\",\"new_compound_only\":true,\"positive_contexts\":3,"
        "\"unassociated_contexts\":6,\"during_getter_record_not_borrowed\":true,"
        "\"cross_thread_rejected\":true,\"full_generation_rejected\":true,"
        "\"original_getter_calls\":9,\"original_wrapper_calls\":1,"
        "\"natural_transfer_original_calls_before_query\":4,"
        "\"later_transfer_original_calls\":1,\"generic_postimage_credit\":false,"
        "\"physical_entry_credit\":false,\"old_GREEN_replayed\":false}");
    Require(native::UninstallPersonInstalledTransferCapture12004(arena.state, true),
            "close owned synthetic transfer installer");
    transfer_arena = nullptr;
    active = nullptr;
    std::cout << "GREEN: transfer -> actual getter -> owned Ci wire; positive3 unrelated6; no numeric credit\n";
    return 0;
  } catch (const std::exception &error) {
    transfer_arena = nullptr;
    active = nullptr;
    std::cerr << error.what() << '\n';
    return 1;
  }
}
