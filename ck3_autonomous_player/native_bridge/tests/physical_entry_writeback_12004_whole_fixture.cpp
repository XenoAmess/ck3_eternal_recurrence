// AUTHOR_NOT_RUN: one new physical-writer -> wrapper/context -> whole V2 packet.
// The renamed entry point is never invoked. Reuse only its memory/world/wire helpers.
#define main XarUnusedKnightStatConsumptionFixtureMain12004
#include "knight_stat_consumption_12004_whole_fixture.cpp"
#undef main

#include "xar_bridge/ck3_12004_physical_entry_writeback.hpp"

namespace {
constexpr std::int32_t kTransferMaxSize = 17;
constexpr std::int64_t kTransferSiege = -111;
constexpr std::int64_t kTransferDamage = 28500000;
constexpr std::int64_t kTransferToughness = 2850000;
constexpr std::int64_t kTransferPursuit = 222;
constexpr std::int64_t kTransferScreen = -333;
constexpr std::uint64_t kTransferReturnBits = 18446744073709551283ULL;

struct PhysicalWorld {
  World world;
  void *entry = world.memory.Allocate(0x60);
  void *province = world.memory.Allocate(0x20);
  std::size_t writer_original_calls = 0;
  bool inside_writer = false;

  PhysicalWorld() {
    world.memory.Put(entry, 0x08, static_cast<std::uint32_t>(kRegiment));
    world.memory.Put(province, 0x10, kTarget);
    world.memory.Put(entry, 0x30, std::int32_t{-99});
    for (const auto offset : {0x38, 0x40, 0x48, 0x50, 0x58})
      world.memory.Put(entry, offset, std::int64_t{-999});
  }
};
PhysicalWorld *physical_active = nullptr;

void *__fastcall PhysicalContextOriginal(void *selected) {
  auto &world = physical_active->world;
  ++world.context_original_calls;
  world.abi_matches &= selected == world.selected_a;
  return world.primary.context;
}

void *__fastcall PhysicalWrapperOriginal(void *output, void *linked) {
  auto &fixture = *physical_active;
  auto &world = fixture.world;
  ++world.wrapper_original_calls;
  Require(world.wrapper_original_calls <= 2, "new wrapper original replayed");
  world.abi_matches &= linked == world.linked && output ==
      (fixture.inside_writer ? world.native_output : world.query_output);
  std::int64_t effectiveness = 100000;
  for (std::size_t index = 0; index < 9; ++index) {
    const auto calls_before = world.context_original_calls;
    auto *returned = native::InvokeKnightStatContext12004(world.selected_a,
        kImage + native::kKnightStatContextReturns12004[index]);
    Require(returned == world.primary.context &&
                world.context_original_calls == calls_before + 1,
            "natural wrapper changed a context result or invoked it twice");
    const auto modifier = world.memory.Get<std::int64_t>(
        world.primary.values, index * sizeof(std::int64_t));
    effectiveness += modifier * kOperands[index] / 100000;
  }
  const auto prowess = world.memory.Get<std::int32_t>(linked, 0xEC);
  const auto damage = world.memory.Get<std::int32_t>(world.damage_coefficient);
  const auto toughness = world.memory.Get<std::int32_t>(world.toughness_coefficient);
  const auto common = effectiveness * (prowess < 1 ? 1 : prowess);
  Require(effectiveness == 95000 && common * damage == kTransferDamage &&
              common * toughness == kTransferToughness,
          "new fixture changed its actual consumed effectiveness operands");
  // These four values are synthetic transfer/ABI diagnostics. The source-shaped
  // native knight projector keeps max/siege/pursuit/screen zero. Its mismatch
  // with this typed original remains data; it must not erase Entry association.
  world.memory.Put(output, 0x08, kTransferMaxSize);
  world.memory.Put(output, 0x10, kTransferSiege);
  world.memory.Put(output, 0x18, common * damage);
  world.memory.Put(output, 0x20, common * toughness);
  world.memory.Put(output, 0x28, kTransferPursuit);
  world.memory.Put(output, 0x30, kTransferScreen);
  return output;
}

std::uint64_t __fastcall PhysicalWriterOriginal(void *entry, void *province) {
  auto &fixture = *physical_active;
  auto &world = fixture.world;
  ++fixture.writer_original_calls;
  world.abi_matches &= entry == fixture.entry && province == fixture.province;
  Require(fixture.writer_original_calls == 1 && !fixture.inside_writer,
          "physical writer original replayed or nested");
  fixture.inside_writer = true;
  auto *output = native::InvokeKnightStatWrapper12004(world.native_output,
      world.linked, kImage + kWrapperReturn);
  fixture.inside_writer = false;
  Require(output == world.native_output && world.wrapper_original_calls == 1 &&
              world.context_original_calls == 9,
          "physical writer changed the original wrapper result or call count");
  world.memory.Put(entry, 0x30, world.memory.Get<std::int32_t>(output, 0x08));
  constexpr std::array<std::size_t, 5> output_offsets{0x10, 0x18, 0x20, 0x28, 0x30};
  constexpr std::array<std::size_t, 5> entry_offsets{0x38, 0x40, 0x48, 0x50, 0x58};
  for (std::size_t index = 0; index < entry_offsets.size(); ++index)
    world.memory.Put(entry, entry_offsets[index],
        world.memory.Get<std::int64_t>(output, output_offsets[index]));
  // The actual writer leaves the last screen load in RAX. Preserve its complete
  // unsigned register bits rather than converting a signed scalar to a pointer.
  return world.memory.Get<std::uint64_t>(entry, 0x58);
}

void ConfigurePhysical(PhysicalWorld &fixture) {
  auto &world = fixture.world;
  auto bindings = native::BindKnightStatConsumptionImage12004(
      kImage, native::kExecutableSha256);
  Require(bindings.enabled && bindings.image_base == kImage,
          "physical writeback fixture lost the exact actual4 observer binding");
  bindings.game_state_slot = reinterpret_cast<void **>(world.game_slot);
  bindings.damage_multiplier = static_cast<const std::int32_t *>(world.damage_coefficient);
  bindings.toughness_multiplier = static_cast<const std::int32_t *>(world.toughness_coefficient);
  bindings.read_context = &world.memory;
  bindings.read_memory = &Memory::Copy;
  // Configure the shared aggregate copier without observing a preparation or
  // invoking either preparation original. This whole owns no prior history.
  native::PersonSixStageCaptureBindings12004 preparation;
  preparation.memory = native::BindPersonCarrierDirect12004(kImage,
      native::kGameVersion, native::kExecutableSha256, &Memory::Copy, &world.memory);
  preparation.game_state_slot = reinterpret_cast<void **>(world.game_slot);
  Require(native::InitializePersonSixStageCaptureFixture12004(preparation,
              &PreparationOriginal, &PreparationAppendOriginal),
          "physical writer aggregate PC copier initialization failed");
  Require(native::InitializeKnightStatConsumptionFixture12004(
              bindings, &PhysicalWrapperOriginal, &PhysicalContextOriginal),
          "new physical writer wrapper/context initialization failed");
  Require(native::InitializePhysicalEntryWritebackFixture12004(&PhysicalWriterOriginal),
          "new physical writer initialization failed");
}

void AssertPhysicalTrampoline() {
  const auto code = native::BuildPhysicalEntryWriterTrampoline12004(kImage);
  constexpr std::array<std::uint8_t, 36> expected{
      0x40, 0x53, 0x48, 0x83, 0xEC, 0x60,
      0x49, 0xB8, 0x40, 0xF3, 0xD1, 0x45, 0x01, 0x00, 0x00, 0x00,
      0x4D, 0x8B, 0x00, 0x4C, 0x8B, 0xCA,
      0xFF, 0x25, 0x00, 0x00, 0x00, 0x00,
      0xB0, 0x7A, 0x65, 0x42, 0x01, 0x00, 0x00, 0x00};
  std::uintptr_t slot = 0, continuation = 0;
  std::memcpy(&slot, code.data() + 8, sizeof(slot));
  std::memcpy(&continuation, code.data() + 28, sizeof(continuation));
  Require(native::kPhysicalEntryWriterPatchBytes12004 == 16 &&
              native::kPhysicalEntryWriterTrampolineBytes12004 == 36 &&
              code == expected &&
              slot == kImage + native::kPhysicalEntryWriterRegimentSlotRva12004 &&
              continuation == kImage + native::kPhysicalEntryWriterRva12004 + 16,
          "RIP-relative Entry registry load was raw-copied or the jump/stack/register recipe changed");
}

void AssertTransferOutput(const native::KnightConsumedOutput12004 &output) {
  Require(output.ready && output.reason.empty() && output.max_size == kTransferMaxSize &&
              output.siege_value_raw == kTransferSiege && output.damage_raw == kTransferDamage &&
              output.toughness_raw == kTransferToughness &&
              output.pursuit_raw == kTransferPursuit && output.screen_raw == kTransferScreen,
          "owned wrapper/physical cache lost a signed field or replaced diagnostics by projector zeros");
}

void AssertPhysicalQuery(const PhysicalWorld &fixture,
                         const native::KnightStatConsumptionQuery12004 &query) {
  const auto &world = fixture.world;
  Require(query.configured && !query.observer_installed && query.events.size() == 2 &&
              query.oldest_available_sequence == 1 && query.latest_sequence == 2 &&
              query.overwritten_events == 0,
          "new whole packet lost its two distinct natural/scratch observations");
  for (std::size_t index = 0; index < query.events.size(); ++index) {
    const auto &event = query.events[index];
    Require(event.sequence == index + 1 && event.observed_date_raw == kDate &&
                event.wrapper_caller_return_rva == kWrapperReturn &&
                event.regiment_id == kRegiment && event.target_province_id == kTarget &&
                event.linked_character_id == kLinked &&
                event.linked_character_identity == Identity(world.linked) &&
                event.linked_prowess_points == 3 && event.loaded_damage_multiplier == 100 &&
                event.loaded_toughness_multiplier == 10 && event.contexts.size() == 9 &&
                event.output_cache_identity == Identity(index == 0 ?
                    world.native_output : world.query_output) &&
                event.native_return_identity == event.output_cache_identity,
            "physical/scratch wrapper lost its linked owner, exact output or operands");
    AssertTransferOutput(event.observed_output);
    for (std::size_t key_index = 0; key_index < event.contexts.size(); ++key_index) {
      const auto &context = event.contexts[key_index];
      Require(context.property_key == static_cast<std::uint16_t>(0xC1U + key_index) &&
                  context.caller_return_rva == native::kKnightStatContextReturns12004[key_index] &&
                  context.selected_character_id == kSelectedA &&
                  context.selected_character_identity == Identity(world.selected_a) &&
                  context.context_identity == Identity(world.primary.context) &&
                  context.operand_raw == kOperands[key_index] &&
                  context.consumed_pc.ready && context.consumed_pc.count_i32 == 9 &&
                  context.consumed_pc.identity == Identity(world.primary.context) + 0x68 &&
                  context.consumed_pc.properties &&
                  context.consumed_pc.properties->keys_u16 &&
                  *context.consumed_pc.properties->keys_u16 ==
                      std::vector<std::uint16_t>({0xC1, 0xC2, 0xC3, 0xC4, 0xC5, 0xC6, 0xC7, 0xC8, 0xC9}) &&
                  context.consumed_pc.properties->values_q64 &&
                  *context.consumed_pc.properties->values_q64 ==
                      std::vector<std::int64_t>(kMainModifiers.begin(), kMainModifiers.end()) &&
                  !context.preparation_capture_sequence &&
                  !context.preparation_model_identity && !context.preparation_context_identity &&
                  !context.preparation_owner_character_id,
              "new writer context was replaced by another PC or fabricated preparation history");
    }
  }
  const auto &event = query.events[0];
  Require(event.origin == "native_physical_entry_writer" && event.entry_association_proven &&
              event.physical_entry_writeback.has_value(),
          "natural Entry writer did not attach its owned physical sidecar");
  const auto &writeback = *event.physical_entry_writeback;
  Require(writeback.writer_sequence == 1 && writeback.entry_identity == Identity(fixture.entry) &&
              writeback.province_identity == Identity(fixture.province) &&
              writeback.regiment_id == static_cast<std::uint32_t>(kRegiment) &&
              writeback.province_id == kTarget &&
              writeback.original_return_value == kTransferReturnBits &&
              !writeback.output_cache_identity_matches_entry &&
              writeback.wrapper_output_comparison_ready &&
              writeback.wrapper_output_matches_entry_cache == true &&
              writeback.regiment_member_at_query == true && writeback.reason.empty(),
          "physical receiver, Province, full Regiment ID, unsigned RAX or honest scratch identity changed");
  AssertTransferOutput(writeback.entry_cache);
  for (const auto &matches : writeback.wrapper_output_field_matches)
    Require(matches == true, "one of the six actual copied fields was not compared independently");
  Require(query.events[1].origin == "bridge_query_scratch" &&
              !query.events[1].entry_association_proven &&
              !query.events[1].physical_entry_writeback,
          "writer scope leaked into a later direct query scratch event");
}
} // namespace

int main(int argc, char **argv) {
  try {
    Require(argc == 2, "usage: xar_physical_entry_writeback_12004_whole <fresh output directory>");
    const std::filesystem::path directory = argv[1];
    std::filesystem::create_directories(directory);
    AssertPhysicalTrampoline();
    PhysicalWorld fixture;
    physical_active = &fixture;
    auto &world = fixture.world;
    ConfigurePhysical(fixture);
    const auto returned = native::InvokePhysicalEntryWriter12004(fixture.entry, fixture.province);
    Require(returned == kTransferReturnBits && fixture.writer_original_calls == 1 &&
                world.wrapper_original_calls == 1 && world.context_original_calls == 9 &&
                world.memory.Get<std::int64_t>(fixture.entry, 0x58) == kTransferScreen,
            "new natural writer changed the original call count or signed-screen unsigned return bits");
    {
      native::KnightStatBridgeQueryScope12004 query_scope(world.query_output, kRegiment, kTarget);
      auto *scratch = native::InvokeKnightStatWrapper12004(world.query_output,
          world.linked, kImage + kWrapperReturn);
      Require(scratch == world.query_output,
              "scope-free direct query changed its original scratch result");
    }
    Require(fixture.writer_original_calls == 1 && world.wrapper_original_calls == 2 &&
                world.context_original_calls == 18 && world.abi_matches &&
                world.preparation_original_calls == 0 && world.preparation_append_calls == 0 &&
                world.memory.refused_reads == 0 && world.memory.unexpected_reads == 0,
            "new fixture replayed an old producer or altered original execution");
    const std::array regiment_ids{kRegiment};
    const std::array linked_ids{static_cast<std::int32_t>(kLinked)};
    auto query = native::ReadKnightStatConsumptionQuery12004(regiment_ids, linked_ids);
    Require(query.has_value(), "configured physical-entry whole observer absent");
    AssertPhysicalQuery(fixture, *query);
    auto snapshot = Snapshot(std::move(*query));
    snapshot.armies[0].regiments[0].effective_stats.damage_raw = kTransferDamage;
    snapshot.armies[0].regiments[0].effective_stats.toughness_raw = kTransferToughness;
    snapshot.armies[0].knights.members[0].knight_effectiveness_raw = 95000;
    snapshot.armies[0].knights.members[0].effective_damage_raw = kTransferDamage;
    snapshot.armies[0].knights.members[0].effective_toughness_raw = kTransferToughness;
    const auto body = xar::bridge::SerializeCombatSimulationInputsV2(snapshot);
    Require(body.find("\"physical_entry_writeback\":{") != std::string::npos &&
                body.find("\"origin\":\"native_physical_entry_writer\"") != std::string::npos &&
                body.find("\"original_return_value\":\"18446744073709551283\"") != std::string::npos,
            "actual whole V2 serializer omitted the source-associated writer or unsigned return");
    const std::string packet =
        "{\"type\":\"command_result\",\"protocol_version\":1,"
        "\"request_id\":\"physical-entry-writeback-12004-whole\",\"ok\":true,"
        "\"result\":{\"step\":\"query-combat-simulation-inputs-v2-101-100-a-1-16777217-d-1-16777218\","
        "\"accepted\":true,\"status\":\"partial\",\"query_sequence\":1,"
        "\"combat_simulation_inputs\":" + body + "}}";
    Write(directory / "physical-entry-writeback-12004-whole.json", packet);
    Write(directory / "physical-entry-writeback-12004-fixture-receipt.json",
        "{\"status\":\"PASS\",\"original_target_kind\":\"typed_fixture_callbacks\","
        "\"native_EXE_invoked\":false,\"entry_installer_executed\":false,"
        "\"old_fixture_replayed\":false,\"writer_original_calls\":1,"
        "\"wrapper_original_calls\":2,\"context_original_calls\":18,"
        "\"preparation_original_calls\":0,\"trampoline_36B_recipe_checked\":true,"
        "\"physical_entry_association_proven\":true,\"query_scratch_associated\":false,"
        "\"wrapper_and_entry_all_six_fields_match\":true,"
        "\"synthetic_ancillary_transfer_and_unsigned_return_diagnostics\":true,"
        "\"synthetic_values_are_native_knight_arithmetic_qualification\":false,"
        "\"screen_raw\":-333,\"writer_return_u64\":18446744073709551283,"
        "\"date_raw\":53236632}");
    physical_active = nullptr;
    std::cout << "one physical Entry whole packet: typed writer 1, wrapper/context 2/18\n";
    return 0;
  } catch (const std::exception &error) {
    physical_active = nullptr;
    std::cerr << error.what() << '\n';
    return 1;
  }
}
