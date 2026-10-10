// AUTHOR_NOT_RUN: new focused same-Ci lineage and owned capture wiring fixture.
#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12004_knight_stat_consumption.hpp"
#include "xar_bridge/ck3_12004_person_six_stage_capture.hpp"

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
  Context primary, alternate, second;
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

std::uintptr_t __fastcall PreparationOriginal(
    void *character, void *context, std::uint32_t index) {
  auto &world = *active;
  const bool first = world.preparation_original_calls < 6;
  world.abi_matches &= character == (first ? world.selected_a : world.selected_b) &&
      context == (first ? world.primary.context : world.second.context) &&
      index == (first ? world.preparation_original_calls : 0);
  ++world.preparation_original_calls;
  return kCountReturn;
}
std::uintptr_t __fastcall PreparationAppendOriginal(void *, void *, std::int64_t) {
  ++active->preparation_append_calls;
  return 0xAABBCCDD12345678ULL;
}

void *__fastcall ContextOriginal(void *character) {
  auto &world = *active;
  ++world.context_original_calls;
  world.abi_matches &= character ==
      (world.active_wrapper == 0 ? world.selected_a : world.selected_b);
  auto &context = world.ReturnedContext();
  if (world.active_wrapper == 1 && world.active_key == 3)
    world.memory.refused_values = context.values;
  return context.context;
}

void *__fastcall WrapperOriginal(void *output, void *linked) {
  auto &world = *active;
  world.active_wrapper = world.wrapper_original_calls++;
  Require(world.active_wrapper < 3, "wrapper original replayed");
  world.abi_matches &= linked == world.linked && output ==
      (world.active_wrapper == 0 ? world.query_output : world.native_output);
  auto *selected = world.active_wrapper == 0 ? world.selected_a : world.selected_b;
  std::int64_t effectiveness = 100000;
  for (std::size_t index = 0; index < 9; ++index) {
    world.active_key = index;
    auto &expected = world.ReturnedContext();
    const auto calls_before = world.context_original_calls;
    auto *context = native::InvokeKnightStatContext12004(selected,
        kImage + native::kKnightStatContextReturns12004[index]);
    Require(world.context_original_calls == calls_before + 1 &&
                context == expected.context,
            "context dispatch changed original result or exact call count");
    world.actual_context_returns[world.active_wrapper * 9 + index] = Identity(context);
    world.memory.refused_values = nullptr;
    // Deterministic typed original target reads its real returned PC and
    // operand independently of the auxiliary guarded-copy failure.
    const auto modifier = world.memory.Get<std::int64_t>(
        expected.values, index * sizeof(std::int64_t));
    effectiveness += modifier * kOperands[index] / 100000;
  }
  const auto prowess = world.memory.Get<std::int32_t>(linked, 0xEC);
  const auto damage = world.memory.Get<std::int32_t>(world.damage_coefficient);
  const auto toughness = world.memory.Get<std::int32_t>(world.toughness_coefficient);
  const auto common = effectiveness * (prowess < 1 ? 1 : prowess);
  world.memory.Put(output, 0x08, std::int32_t{0});
  world.memory.Put(output, 0x10, std::int64_t{0});
  world.memory.Put(output, 0x18, common * damage);
  world.memory.Put(output, 0x20, common * toughness);
  world.memory.Put(output, 0x28, std::int64_t{0});
  world.memory.Put(output, 0x30, std::int64_t{0});
  return output;
}

void Configure(World &world) {
  auto bindings = native::BindKnightStatConsumptionImage12004(
      kImage, native::kExecutableSha256);
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
              &PreparationOriginal, &PreparationAppendOriginal),
          "Native65 production PC-copy/preparation fixture initialization failed");
  for (std::uint32_t index = 0; index < 6; ++index) {
    const auto bits = native::InvokePersonSixStageCapture12004(world.selected_a,
        world.primary.context, index, kImage + native::kPersonSixStageReturnRva12004);
    Require(bits == kCountReturn && world.preparation_original_calls == index + 1,
            "new connected preparation setup changed original count or full return bits");
  }
  native::CompletePersonSixStageCapture12004(Identity(world.selected_a), kSelectedA,
                                            Identity(world.primary.context));
  const auto historical = native::ReadPersonSixStageCaptureForCharacter12004(
      Identity(world.selected_a), kSelectedA);
  Require(historical.capture_complete && historical.capture_sequence == 1 &&
              historical.preparation_model.ready &&
              historical.preparation_model.owner_matches_capture == true &&
              historical.post_six_aggregate.pc.ready &&
              historical.post_six_aggregate.pc.properties &&
              historical.post_six_aggregate.pc.properties->values_q64 ==
                  std::vector<std::int64_t>(kMainModifiers.begin(), kMainModifiers.end()),
          "connected preparation did not own the actual historical aggregate/postimage");
  Require(native::InitializeKnightStatConsumptionFixture12004(
              bindings, &WrapperOriginal, &ContextOriginal),
          "production knight wrapper/context fixture initialization failed");
}


void AssertLineage(const World &world,
                   const native::KnightStatConsumptionQuery12004 &query) {
  Require(query.events.size() == 3, "new focused wiring events missing");
  for (std::size_t event_index = 0; event_index < query.events.size(); ++event_index) {
    const auto &event = query.events[event_index];
    Require(event.contexts.size() == 9 && !event.entry_association_proven,
            "context lineage became physical Entry association");
    for (std::size_t index = 0; index < event.contexts.size(); ++index) {
      const auto &context = event.contexts[index];
      Require(context.preparation_stage_lineage.has_value(),
              "actual consumed-Ci omitted new lineage object");
      const auto &stage = *context.preparation_stage_lineage;
      Require(stage.property_key == context.property_key &&
                  stage.consumed_return_rva == context.caller_return_rva &&
                  stage.exact_consumed_callsite &&
                  stage.selected_character_id == context.selected_character_id &&
                  stage.selected_character_identity == context.selected_character_identity &&
                  stage.getter_context_identity == context.context_identity &&
                  stage.linked_character_id == event.linked_character_id &&
                  stage.linked_character_identity == event.linked_character_identity &&
                  stage.consumption_thread_id == event.thread_id &&
                  context.operand_raw == kOperands[index],
              "lineage changed exact consumed receiver, parent event or signed operand");
      if (event_index == 0) {
        Require(context.preparation_capture_at_consumption.has_value(),
                "completed same-Ci capture payload omitted");
        const auto &capture = *context.preparation_capture_at_consumption;
        Require(capture.capture_complete && capture.capture_sequence == 1 &&
                    capture.preparation_model.model_identity == Identity(world.primary.model) &&
                    stage.preparation_capture_complete && stage.preparation_stage_observed_mask == 0x3F &&
                    stage.preparation_source_return_rva == native::kPersonSixStageReturnRva12004 &&
                    stage.preparation_capture_sequence == *context.preparation_capture_sequence &&
                    stage.completion_on_consumption_thread == true &&
                    stage.preparation_owner_character_identity == Identity(world.selected_a) &&
                    stage.completed_preparation_lineage_proven == (index != 4),
                "completed same-thread capture/owner lineage was not copied at exact Ci");
        if (index == 4)
          Require(stage.getter_matches_capture_context == false &&
                      context.consumed_pc.identity == Identity(world.alternate.context) + 0x68,
                  "same selected Character borrowed another receiver's preparation");
      } else if (event_index == 1) {
        Require(context.preparation_capture_at_consumption.has_value(),
                "open capture payload discarded");
        const auto &capture = *context.preparation_capture_at_consumption;
        Require(capture.capture_observed && !capture.capture_complete &&
                    capture.capture_sequence == 2 && stage.preparation_capture_observed &&
                    !stage.preparation_capture_complete && stage.preparation_stage_observed_mask == 1 &&
                    !stage.completed_preparation_lineage_proven &&
                    stage.reason == "preparation_capture_open_at_consumption" &&
                    !stage.preparation_completion_thread_id,
                "partial capture was promoted to completion or dropped");
        if (index == 3)
          Require(!context.consumed_pc.ready && context.consumed_pc.properties &&
                      !context.consumed_pc.properties->values_q64 &&
                      context.consumed_pc.reason == "pc_values_unread",
                  "partial consumed PC replaced raw unknown values");
      } else {
        Require(!context.preparation_capture_at_consumption &&
                    !context.preparation_capture_sequence &&
                    !stage.preparation_capture_observed &&
                    !stage.completed_preparation_lineage_proven &&
                    stage.reason == "preparation_capture_unobserved",
                "changed full Character ID borrowed an older pointer's capture");
      }
    }
  }
}

void Write(const std::filesystem::path &path, std::string_view text) {
  Require(!std::filesystem::exists(path), "fresh focused output already exists");
  std::ofstream stream(path, std::ios::binary);
  stream << text << '\n';
  Require(static_cast<bool>(stream), "cannot persist new focused output");
}
} // namespace

int main(int argc, char **argv) {
  try {
    Require(argc == 2, "usage: knight stage lineage focused fixture <fresh output directory>");
    const std::filesystem::path directory = argv[1];
    std::filesystem::create_directories(directory);
    World world;
    active = &world;
    Configure(world);
    {
      native::KnightStatBridgeQueryScope12004 scope(world.query_output, kRegiment, kTarget);
      Require(native::InvokeKnightStatWrapper12004(world.query_output, world.linked,
                  kImage + kWrapperReturn) == world.query_output,
              "completed preparation observer changed original output identity");
    }
    // One reached typed callback leaves this different selected Character's
    // capture open. This is a new partial wiring case, not an old FIRST gate.
    Require(native::InvokePersonSixStageCapture12004(world.selected_b,
                world.second.context, 0, kImage + native::kPersonSixStageReturnRva12004) == kCountReturn,
            "open capture callback return bits changed");
    Require(native::InvokeKnightStatWrapper12004(world.native_output, world.linked,
                kImage + kWrapperReturn) == world.native_output,
            "open preparation observer changed original output identity");
    world.memory.Put(world.selected_b, 0x18, std::uint32_t{0x07000003});
    Require(native::InvokeKnightStatWrapper12004(world.native_output, world.linked,
                kImage + kWrapperReturn) == world.native_output,
            "unobserved full-ID observer changed original output identity");
    const std::array regiment_ids{kRegiment};
    const std::array linked_ids{static_cast<std::int32_t>(kLinked)};
    const auto query = native::ReadKnightStatConsumptionQuery12004(regiment_ids, linked_ids);
    const auto execution_counts = std::string("new connected fixture execution counters: wrapper=") +
        std::to_string(world.wrapper_original_calls) + " context=" + std::to_string(world.context_original_calls) +
        " preparation=" + std::to_string(world.preparation_original_calls) +
        " append=" + std::to_string(world.preparation_append_calls) + " abi=" +
        std::to_string(world.abi_matches) + " refused=" + std::to_string(world.memory.refused_reads) +
        " unexpected=" + std::to_string(world.memory.unexpected_reads) +
        " reached_piety_key_reads=" + std::to_string(world.memory.mapped_reads);
    Require(query && world.wrapper_original_calls == 3 && world.context_original_calls == 27 &&
                world.preparation_original_calls == 7 && world.preparation_append_calls == 0 &&
                world.abi_matches && world.memory.refused_reads == 1 && world.memory.unexpected_reads == 0 &&
                world.memory.mapped_reads == 7,
            execution_counts.c_str());
    AssertLineage(world, *query);
    world.memory.Put(world.primary.values, 0, std::int64_t{999999});
    world.memory.Put(world.primary.model, 0x08, world.selected_b);
    const auto later = native::ReadKnightStatConsumptionQuery12004(regiment_ids, linked_ids);
    Require(later && *later == *query && world.wrapper_original_calls == 3 &&
                world.context_original_calls == 27,
            "historical same-Ci capture payload was replaced by later source memory");
    const auto body = native::SerializeKnightStatConsumptionQuery12004(*query);
    Require(body.find("\"preparation_stage_lineage\":{") != std::string::npos &&
                body.find("\"preparation_capture_at_consumption\":{") != std::string::npos &&
                body.find(native::kEntrySelectedReceiverStageSchema12004) != std::string::npos &&
                body.find(native::kPersonSixStageCaptureSchema12004) != std::string::npos,
            "production serializer omitted lineage or full capture wire");
    native::KnightStatConsumptionQuery12004 legacy;
    legacy.events.emplace_back().contexts.emplace_back();
    const auto legacy_body = native::SerializeKnightStatConsumptionQuery12004(legacy);
    Require(legacy_body.find("preparation_stage_lineage") == std::string::npos &&
                legacy_body.find("preparation_capture_at_consumption") == std::string::npos &&
                legacy_body.find("\"preparation_capture_sequence\":null") != std::string::npos,
            "legacy absence/optional sequence wire changed");
    Write(directory / "knight-stage-lineage-12004.json", body);
    Write(directory / "knight-stage-lineage-12004-receipt.json",
        "{\"status\":\"GREEN\",\"scope\":\"new_connected_same_ci_lineage_wire_fixture\","
        "\"wrapper_original_calls\":3,\"context_original_calls\":27,"
        "\"preparation_original_calls\":7,\"append_original_calls\":0,"
        "\"reached_piety_key_reads\":7,\"unexpected_reads\":0,"
        "\"completed_positive_contexts\":8,\"completed_receiver_mismatch_contexts\":1,"
        "\"open_capture_contexts\":9,\"unobserved_full_id_contexts\":9,"
        "\"one_partial_pc_preserved\":true,\"same_ci_payload_immutable\":true,"
        "\"legacy_optional_fields_omitted\":true,\"native_EXE_invoked\":false,"
        "\"hook_installer_executed\":false,\"old_FIRST_replayed\":false}");
    active = nullptr;
    std::cout << "new connected stage lineage wire: completed 8/9, open 9, unobserved 9\n";
    return 0;
  } catch (const std::exception &error) {
    active = nullptr;
    std::cerr << error.what() << '\n';
    return 1;
  }
}
