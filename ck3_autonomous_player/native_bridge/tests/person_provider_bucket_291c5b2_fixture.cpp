#include "xar_bridge/battle_context_source_inputs_v1_serializer.hpp"
#include "xar_bridge/ck3_12003.hpp"
#include "xar_bridge/ck3_12003_context_sources.hpp"

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <limits>
#include <memory>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace {
void ProviderBucketRequire(bool value, const char *label) {
  if (!value) throw std::runtime_error(label);
}

struct ProviderBucketMemory {
  struct Region { std::unique_ptr<std::byte[]> data; std::size_t size; };
  struct Denied { std::uintptr_t begin; std::size_t size; std::size_t attempts = 0; };
  struct ReadEvent { std::uintptr_t begin; std::size_t size; };
  std::vector<Region> regions;
  std::vector<Denied> denied;
  std::vector<ReadEvent> reads;

  void *Allocate(std::size_t size) {
    auto data = std::make_unique<std::byte[]>(size);
    void *pointer = data.get();
    regions.push_back({std::move(data), size});
    return pointer;
  }
  template <typename T> void Put(void *pointer, std::size_t offset, T value) {
    std::memcpy(static_cast<std::byte *>(pointer) + offset, &value, sizeof(value));
  }
  void Deny(const void *pointer, std::size_t offset, std::size_t bytes) {
    denied.push_back({reinterpret_cast<std::uintptr_t>(pointer) + offset, bytes});
  }
  std::size_t CountReads(const void *pointer, std::size_t offset,
                         std::size_t bytes) const {
    const auto begin = reinterpret_cast<std::uintptr_t>(pointer) + offset;
    std::size_t count = 0;
    for (const auto &read : reads)
      if (read.begin == begin && read.size == bytes) ++count;
    return count;
  }
  void RequireUnused() const {
    for (const auto &range : denied)
      ProviderBucketRequire(range.attempts == 0,
                            "provider bucket demanded an unused branch");
  }
  static bool Read(void *context, const void *pointer, void *output,
                   std::size_t bytes) noexcept {
    auto &memory = *static_cast<ProviderBucketMemory *>(context);
    const auto begin = reinterpret_cast<std::uintptr_t>(pointer);
    memory.reads.push_back({begin, bytes});
    for (auto &range : memory.denied) {
      if (begin < range.begin + range.size && range.begin < begin + bytes) {
        ++range.attempts;
        return false;
      }
    }
    for (const auto &region : memory.regions) {
      const auto base = reinterpret_cast<std::uintptr_t>(region.data.get());
      if (begin >= base && begin - base <= region.size &&
          bytes <= region.size - static_cast<std::size_t>(begin - base)) {
        std::memcpy(output, pointer, bytes);
        return true;
      }
    }
    return false;
  }
};

void *ProviderBucketAt(void *pointer, std::size_t offset) {
  return static_cast<std::byte *>(pointer) + offset;
}

struct ProviderBucketFixture {
  ProviderBucketMemory memory;
  xar::ck3_12002::ContextSourceBindingsV1 bindings{};
  void *character = memory.Allocate(0x1D0);
  void *carrier = memory.Allocate(0x300);
  void *provider_slot = memory.Allocate(8);
  void *denominator_slot = memory.Allocate(4);
  void *fallback_slot = memory.Allocate(8);
  void *provider = memory.Allocate(0x1208);
  void *buckets = memory.Allocate(16);
  void *first = memory.Allocate(0xB8);
  void *second = memory.Allocate(0xB8);
  void *fallback = memory.Allocate(0xB8);

  void Property(void *definition, std::int64_t value) {
    void *pc = ProviderBucketAt(definition, 0x40);
    void *keys = memory.Allocate(2);
    void *values = memory.Allocate(8);
    memory.Put(pc, 0, keys);
    memory.Put(pc, 0xC, std::int32_t{1});
    memory.Put(pc, 0x68, values);
    // +74 is provenance. The native paired append consumes one value for +C=1.
    memory.Put(pc, 0x74, std::int32_t{2});
    memory.Put(keys, 0, std::uint16_t{7U});
    memory.Put(values, 0, value);
  }
  void Ratio(std::int32_t numerator, std::int32_t denominator) {
    memory.Put(character, 0x1B0, carrier);
    memory.Put(carrier, 0x2F8, numerator);
    memory.Put(denominator_slot, 0, denominator);
  }
  ProviderBucketFixture() {
    bindings.enabled = true;
    bindings.read_memory = &ProviderBucketMemory::Read;
    bindings.read_context = &memory;
    auto &leaf = bindings.provider_bucket_291c5b2;
    leaf.enabled = true;
    leaf.provider_slot = provider_slot;
    leaf.factor_denominator_slot = denominator_slot;
    leaf.native_fallback_slot = fallback_slot;
    memory.Put(character, 0x18, std::int32_t{29829});
    memory.Put(provider_slot, 0, provider);
    memory.Put(denominator_slot, 0, std::int32_t{100000});
    memory.Put(fallback_slot, 0, fallback);
    memory.Put(provider, 0x11F8, buckets);
    memory.Put(provider, 0x1204, std::int32_t{2});
    memory.Put(buckets, 0, first);
    memory.Put(buckets, 8, second);
    for (void *definition : {first, second, fallback}) {
      memory.Put(definition, 0x38, std::uint32_t{0x4744624FU});
      // This source has no selected full-ID operand.
      memory.Deny(definition, 0x10, 4);
    }
    Property(first, 301);
    Property(second, -302);
    // The initialized fallback PC stays empty with the actual +C=0 bytes.
  }
  xar::game::BattleCurrentPersonContextSourceInputsSnapshotV1 Observe() {
    ProviderBucketRequire(!bindings.provider && !bindings.government &&
                          !bindings.existing_token_lookup,
                          "provider bucket native callback assigned");
    const auto first_snapshot = xar::ck3_12002::ReadCurrentContextSourceInputs12003(
        bindings, character, 29829);
    const auto second_snapshot = xar::ck3_12002::ReadCurrentContextSourceInputs12003(
        bindings, character, 29829);
    ProviderBucketRequire(first_snapshot == second_snapshot,
                          "provider bucket whole-query samples differ");
    ProviderBucketRequire(first_snapshot.provider_bucket_291c5b2.has_value(),
                          "provider bucket leaf omitted");
    ProviderBucketRequire(!first_snapshot.pre_291e210_1640 &&
                          !first_snapshot.post_291d7e0_sources &&
                          !first_snapshot.later_direct_291c3fb_44c &&
                          !first_snapshot.helper_291f0a0 &&
                          !first_snapshot.later_helpers_291f550_291f940 &&
                          !first_snapshot.tail_direct_291c5b7_291cc49 &&
                          !first_snapshot.middle_helpers_291f260_291fb10 &&
                          !first_snapshot.tail_prefix_2753860_2922530 &&
                          !first_snapshot.trait_stage_291d460 &&
                          !first_snapshot.absent_recipient_inputs &&
                          !first_snapshot.uncached_recipient_inputs &&
                          !first_snapshot.helper_2922070 &&
                          !first_snapshot.conference_24b1d00,
                          "provider bucket enabled another optional source");
    ProviderBucketRequire(!first_snapshot.ready && first_snapshot.status == "partial",
                          "provider bucket fabricated whole-source readiness");
    return first_snapshot;
  }
};

void ProviderBucketSave(const std::filesystem::path &directory, const char *name,
    const xar::game::BattleCurrentPersonContextSourceInputsSnapshotV1 &snapshot) {
  if (directory.empty()) return;
  std::ofstream output(directory / (std::string(name) + ".json"), std::ios::binary);
  output << xar::bridge::SerializeBattleCurrentPersonContextSourceInputsV1(snapshot);
  ProviderBucketRequire(static_cast<bool>(output), "provider bucket wire write failed");
}

void ProviderBucketAdmitted(const xar::game::ContextSourceProviderBucket291c5b2V1 &leaf,
                            std::int64_t value) {
  ProviderBucketRequire(leaf.character_id == 29829 && leaf.ready &&
                        leaf.status == "available" && leaf.reason.empty() &&
                        leaf.provider_present == true && leaf.provider_identity == "provider0" &&
                        leaf.selected_definition_identity == "provider1" &&
                        leaf.property_identity == "provider2" &&
                        leaf.property_identity != leaf.selected_definition_identity &&
                        leaf.selected_magic_raw == 0x4744624FU && leaf.admitted == true &&
                        leaf.property_block,
                        "provider bucket admitted actual inline PC provenance");
  const auto &pc = *leaf.property_block;
  ProviderBucketRequire(pc.keys_count == 1 && pc.values_count == 2 &&
                        pc.keys_u16 && *pc.keys_u16 == std::vector<std::uint16_t>{7U} &&
                        pc.values_q64 && *pc.values_q64 == std::vector<std::int64_t>{value},
                        "provider bucket paired PC consumed key-count values");
}
} // namespace

void RunProviderBucket291c5b2Fixture(const std::filesystem::path &directory) {
  if (!directory.empty()) std::filesystem::create_directories(directory);
  constexpr std::uintptr_t image_base = 0x140000000ULL;
  const auto exact = xar::ck3_12002::BindContextSourceInputs12003(
      image_base, xar::ck3_12003::kExecutableSha256);
  const auto &bound = exact.provider_bucket_291c5b2;
  ProviderBucketRequire(bound.enabled &&
                        bound.provider_slot == reinterpret_cast<const void *>(image_base + 0x5C670F8) &&
                        bound.factor_denominator_slot == reinterpret_cast<const void *>(image_base + 0x5C68CE8) &&
                        bound.native_fallback_slot == reinterpret_cast<const void *>(image_base + 0x5D1E0B0),
                        "provider bucket exact-build slot bindings");
  ProviderBucketRequire(!xar::ck3_12002::BindContextSourceInputs12003(
                            image_base, "other-build").provider_bucket_291c5b2.enabled,
                        "provider bucket wrong-build binding enabled");
  {
    ProviderBucketFixture fixture;
    fixture.memory.Deny(fixture.carrier, 0x2F8, 4);
    fixture.memory.Deny(fixture.denominator_slot, 0, 4);
    fixture.memory.Deny(fixture.fallback_slot, 0, 8);
    fixture.memory.Deny(fixture.buckets, 8, 8);
    const auto snapshot = fixture.Observe();
    const auto &leaf = *snapshot.provider_bucket_291c5b2;
    ProviderBucketAdmitted(leaf, 301);
    ProviderBucketRequire(leaf.carrier_present == false && !leaf.key_2f8_raw &&
                          !leaf.denominator_5c68ce8_raw && leaf.bucket_index_raw == 0 &&
                          leaf.provider_count_1204_raw == 2 &&
                          leaf.provider_array_present == true &&
                          leaf.selection == "provider_bucket_11f8",
                          "provider bucket null carrier chooses bucket zero");
    fixture.memory.RequireUnused();
    ProviderBucketSave(directory, "provider-null-carrier-bucket0", snapshot);
  }
  {
    ProviderBucketFixture fixture;
    fixture.Ratio(-199999, -100000);
    fixture.memory.Deny(fixture.fallback_slot, 0, 8);
    fixture.memory.Deny(fixture.buckets, 0, 8);
    const auto snapshot = fixture.Observe();
    const auto &leaf = *snapshot.provider_bucket_291c5b2;
    ProviderBucketAdmitted(leaf, -302);
    ProviderBucketRequire(leaf.carrier_present == true && leaf.key_2f8_raw == -199999 &&
                          leaf.denominator_5c68ce8_raw == -100000 &&
                          leaf.bucket_index_raw == 1 && leaf.provider_count_1204_raw == 2 &&
                          leaf.provider_array_present == true &&
                          leaf.selection == "provider_bucket_11f8",
                          "provider bucket signed ratio truncates toward zero");
    fixture.memory.RequireUnused();
    ProviderBucketSave(directory, "provider-signed-ratio-bucket1", snapshot);
  }
  {
    ProviderBucketFixture fixture;
    fixture.Ratio(std::numeric_limits<std::int32_t>::min(), -1);
    fixture.memory.Deny(fixture.provider, 0x1204, 4);
    fixture.memory.Deny(fixture.provider, 0x11F8, 8);
    fixture.memory.Deny(fixture.buckets, 0, 16);
    fixture.memory.Deny(fixture.fallback, 0x40, 8);
    fixture.memory.Deny(fixture.fallback, 0xA8, 0x10);
    const auto snapshot = fixture.Observe();
    const auto &leaf = *snapshot.provider_bucket_291c5b2;
    ProviderBucketRequire(leaf.ready && leaf.status == "available" &&
                          leaf.bucket_index_raw == std::numeric_limits<std::int32_t>::min() &&
                          leaf.key_2f8_raw == std::numeric_limits<std::int32_t>::min() &&
                          leaf.denominator_5c68ce8_raw == -1 &&
                          !leaf.provider_count_1204_raw && !leaf.provider_array_present &&
                          leaf.selection == "native_fallback_5d1e0b0" &&
                          leaf.selected_definition_identity && leaf.property_identity &&
                          leaf.selected_magic_raw == 0x4744624FU && leaf.admitted == true &&
                          leaf.property_block && leaf.property_block->keys_count == 0 &&
                          !leaf.property_block->values_count &&
                          leaf.property_block->keys_u16 && leaf.property_block->keys_u16->empty() &&
                          leaf.property_block->values_q64 && leaf.property_block->values_q64->empty(),
                          "provider bucket promoted quotient wraps and selects valid empty fallback PC");
    fixture.memory.RequireUnused();
    ProviderBucketSave(directory, "provider-intmin-wrap-fallback", snapshot);
  }
  {
    ProviderBucketFixture fixture;
    fixture.Ratio(123, 0);
    fixture.memory.Put(fixture.provider, 0x1204, std::int32_t{-1});
    fixture.memory.Put(fixture.fallback, 0x38, std::uint32_t{0});
    fixture.memory.Deny(fixture.provider, 0x11F8, 8);
    fixture.memory.Deny(fixture.buckets, 0, 16);
    fixture.memory.Deny(fixture.fallback, 0x40, 0x78);
    const auto snapshot = fixture.Observe();
    const auto &leaf = *snapshot.provider_bucket_291c5b2;
    ProviderBucketRequire(leaf.ready && leaf.status == "available" && leaf.key_2f8_raw == 123 &&
                          leaf.denominator_5c68ce8_raw == 0 && leaf.bucket_index_raw == 42949 &&
                          leaf.provider_count_1204_raw == -1 && !leaf.provider_array_present &&
                          leaf.selection == "native_fallback_5d1e0b0" &&
                          leaf.selected_definition_identity && leaf.selected_magic_raw == 0U &&
                          leaf.admitted == false && !leaf.property_identity && !leaf.property_block,
                          "provider bucket zero divisor and negative native count select wrong-magic skip");
    fixture.memory.RequireUnused();
    ProviderBucketSave(directory, "provider-denzero-negative-count-skip", snapshot);
  }
  {
    ProviderBucketFixture selected_null;
    selected_null.Ratio(-199999, -100000);
    selected_null.memory.Put(selected_null.buckets, 8, static_cast<void *>(nullptr));
    selected_null.memory.Deny(selected_null.fallback_slot, 0, 8);
    const auto selected_snapshot = selected_null.Observe();
    const auto &selected = *selected_snapshot.provider_bucket_291c5b2;
    ProviderBucketRequire(!selected.ready && selected.status == "partial" &&
                          selected.bucket_index_raw == 1 && selected.provider_count_1204_raw == 2 &&
                          selected.provider_array_present == true &&
                          selected.selection == "provider_bucket_11f8" &&
                          !selected.selected_definition_identity && !selected.selected_magic_raw &&
                          !selected.admitted && !selected.property_identity && !selected.property_block &&
                          selected.reason == "provider_bucket_selected_definition_null",
                          "provider bucket demanded native null does not take fallback");
    selected_null.memory.RequireUnused();
    ProviderBucketSave(directory, "provider-selected-null-partial", selected_snapshot);

    ProviderBucketFixture loaded_null;
    loaded_null.Ratio(-199999, -100000);
    loaded_null.memory.Put(loaded_null.provider_slot, 0, static_cast<void *>(nullptr));
    loaded_null.memory.Deny(loaded_null.carrier, 0x2F8, 4);
    loaded_null.memory.Deny(loaded_null.denominator_slot, 0, 4);
    loaded_null.memory.Deny(loaded_null.provider, 0x11F8, 0x10);
    loaded_null.memory.Deny(loaded_null.fallback_slot, 0, 8);
    const auto loaded_snapshot = loaded_null.Observe();
    const auto &loaded = *loaded_snapshot.provider_bucket_291c5b2;
    ProviderBucketRequire(!loaded.ready && loaded.status == "partial" &&
                          loaded.provider_present == false && !loaded.provider_identity &&
                          !loaded.carrier_present && !loaded.key_2f8_raw &&
                          !loaded.denominator_5c68ce8_raw && !loaded.bucket_index_raw &&
                          !loaded.provider_count_1204_raw && !loaded.provider_array_present &&
                          !loaded.selection && !loaded.selected_definition_identity &&
                          !loaded.selected_magic_raw && !loaded.admitted &&
                          !loaded.property_identity && !loaded.property_block &&
                          loaded.reason == "provider_bucket_provider_initializer_required",
                          "provider bucket unloaded provider remains partial before carrier demand");
    // Branch A/B each retain one Character+1B0 read per whole query.
    ProviderBucketRequire(loaded_null.memory.CountReads(loaded_null.character, 0x1B0, 8) == 4U,
                          "provider bucket unloaded provider demanded carrier or called initializer");
    loaded_null.memory.RequireUnused();
    ProviderBucketSave(directory, "provider-loaded-null-partial", loaded_snapshot);
  }
}
