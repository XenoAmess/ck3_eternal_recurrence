#include "player_world_building_definition_source_v1.hpp"

#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <unordered_map>

namespace {

constexpr std::uintptr_t kModule = 0x100000000ULL;
constexpr std::int32_t kActor = 29829;
constexpr std::int32_t kCounty = 2142;
constexpr std::int32_t kBarony = 2143;
constexpr std::int32_t kProvince = 2619;

struct Fixture {
  std::unordered_map<std::uintptr_t, std::uint8_t> bytes;
  xar::game::CampaignRootFrameV1 frame{
      3, 53178312, true, true, true, true, kActor};
  bool main_thread = true;
  bool change_final_frame = false;
  bool validator_fails = false;
  std::int32_t native_checks = 0;
  std::int32_t frame_reads = 0;

  template <typename T>
  void Put(std::uintptr_t address, T value) {
    const auto *raw = reinterpret_cast<const std::uint8_t *>(&value);
    for (std::size_t index = 0; index < sizeof(T); ++index) {
      bytes[address + index] = raw[index];
    }
  }

  static bool Read(void *context, const void *address, void *output,
                   std::size_t size) noexcept {
    auto &self = *static_cast<Fixture *>(context);
    const auto base = reinterpret_cast<std::uintptr_t>(address);
    auto *raw = static_cast<std::uint8_t *>(output);
    for (std::size_t index = 0; index < size; ++index) {
      const auto found = self.bytes.find(base + index);
      if (found == self.bytes.end()) return false;
      raw[index] = found->second;
    }
    return true;
  }

  static bool Capture(void *context,
                      xar::game::CampaignRootFrameV1 &output) noexcept {
    auto &self = *static_cast<Fixture *>(context);
    output = self.frame;
    if (self.change_final_frame && ++self.frame_reads == 4) {
      ++output.snapshot_revision;
    }
    return true;
  }

  static bool IsMain(void *context) noexcept {
    return static_cast<Fixture *>(context)->main_thread;
  }

  static bool Validate(void *context, std::int32_t actor,
                       std::int32_t province, std::uintptr_t definition,
                       std::int32_t slot, bool &allowed) noexcept {
    auto &self = *static_cast<Fixture *>(context);
    ++self.native_checks;
    std::int32_t type = -1;
    if (self.validator_fails || actor != kActor || province != kProvince ||
        slot < 0 || slot >= 2 ||
        !Read(context, reinterpret_cast<const void *>(definition + 0x10),
              &type, sizeof(type))) {
      return false;
    }
    allowed = type == 22 && slot == 1;
    return true;
  }

  xar::ck3_11906::PlayerWorldBuildingSourceAccessV1 Access(
      bool enable_final = true) {
    xar::ck3_11906::PlayerWorldBuildingSourceAccessV1 result{};
    result.campaign = {this, Capture, IsMain, Read, nullptr};
    if (enable_final) {
      result.final_legality = &Validate;
      result.final_legality_context = this;
    }
    return result;
  }
};

void Require(bool condition, const char *name) {
  if (!condition) {
    std::cerr << "RED " << name << '\n';
    std::abort();
  }
}

Fixture Scene() {
  Fixture f;
  f.Put(kModule + 0x570E068, std::uintptr_t{0x100000});
  f.Put(kModule + 0x570F7B8, std::uintptr_t{0x110000});
  f.Put(kModule + 0x570C130, std::uintptr_t{0x400000});
  f.Put(kModule + 0x570C138, std::uintptr_t{0x410000});
  f.Put(kModule + 0x570C410, std::uintptr_t{0x500000});
  f.Put(kModule + 0x570C3F8, std::uintptr_t{0x510000});
  f.Put(kModule + 0x57BFBA8, std::uintptr_t{0x900000});
  f.Put(kModule + 0x570C108, std::uintptr_t{0xD00000});
  f.Put(kModule + 0x57BFFF8, std::uintptr_t{0xA00000});
  f.Put(kModule + 0x57BFFD0, std::uintptr_t{0xC00000});
  f.Put(kModule + 0x4FE7EE0, kActor);
  f.Put(0x100000 + 0xA0, std::uintptr_t{0x200000});
  f.Put(0x110000 + 0x18, std::uintptr_t{0x120000});
  f.Put(0x120000 + 0x1F0, std::int32_t{7});
  f.Put(0x200000 + 0x1D4F0 + 0x58, std::uintptr_t{0x300000});
  f.Put(0x200000 + 0x1D4F0 + 0x64, std::int32_t{1});
  f.Put(0x300000, std::uintptr_t{0x310000});
  f.Put(0x310000 + 0xD8, std::int32_t{7});
  f.Put(0x310000 + 0xB0, kActor);
  f.Put(0x400000 + 0x20, std::uintptr_t{0x400020});
  f.Put(0x400000 + 0x2C, std::int32_t{30000});
  f.Put(0x400020 + static_cast<std::uintptr_t>(kActor) * 0x10 + 8,
        std::uintptr_t{0x420000});
  f.Put(0x420000 + 0x18, kActor);
  f.Put(0x420000 + 0x1C8, std::uintptr_t{0});
  f.Put(0x420000 + 0x1B8, std::uintptr_t{0x430000});
  f.Put(0x430000 + 0x1E0, std::uintptr_t{0x440000});
  f.Put(0x430000 + 0x1E8, std::int32_t{2});
  f.Put(0x430000 + 0x1EC, std::int32_t{2});
  f.Put(0x440000, kCounty);
  f.Put(0x440004, kBarony);
  f.Put(0x500000 + 0x20, std::uintptr_t{0x500020});
  f.Put(0x500000 + 0x2C, std::int32_t{4000});
  f.Put(0x500020 + kCounty * 0x10 + 8, std::uintptr_t{0x600000});
  f.Put(0x500020 + kBarony * 0x10 + 8, std::uintptr_t{0x620000});
  f.Put(0x600000 + 0x10, kCounty);
  f.Put(0x600000 + 0x160, std::uintptr_t{0x610000});
  f.Put(0x610000 + 0x5C, std::int32_t{2});
  f.Put(0x600000 + 0x258, kActor);
  f.Put(0x620000 + 0x10, kBarony);
  f.Put(0x620000 + 0x160, std::uintptr_t{0x630000});
  f.Put(0x630000 + 0x5C, std::int32_t{1});
  f.Put(0x620000 + 0x258, kActor);
  f.Put(0x620000 + 0x460, std::uintptr_t{0x700000});
  f.Put(0x200000 + 0x140, std::uintptr_t{0x720000});
  f.Put(0x200000 + 0x14C, std::int32_t{4000});
  f.Put(0x720000 + kProvince * 8, std::uintptr_t{0x700000});
  f.Put(0x700000 + 0x10, kProvince);
  f.Put(0x700000 + 0x620 + 0x24, std::int32_t{2});
  // The R722-style CHoldingView mode-0 list is empty although the stock
  // CBuildingType manager vector contains two definitions.
  f.Put(0x900000 + 0x628, std::uintptr_t{0x910000});
  f.Put(0x910000 + 0x60, std::uintptr_t{0});
  f.Put(0x910000 + 0x6C, std::int32_t{0});
  f.Put(0xD00000 + 0x68, std::uintptr_t{0xD10000});
  f.Put(0xD00000 + 0x70, std::int32_t{2});
  f.Put(0xD00000 + 0x74, std::int32_t{2});
  f.Put(0xD10000, std::uintptr_t{0xB00000});
  f.Put(0xD10008, std::uintptr_t{0xB10000});
  f.Put(0xB00000, kModule + 0x44046C0);
  f.Put(0xB00000 + 0x10, std::int32_t{11});
  f.Put(0xB10000, kModule + 0x44046C0);
  f.Put(0xB10000 + 0x10, std::int32_t{22});
  // R735's wrong registry is a CCourtTypeSetting peer. Its first type
  // cannot replace the manager's typed CBuildingType definitions.
  f.Put(0xA00000 + 0x68, std::uintptr_t{0xA10000});
  f.Put(0xA00000 + 0x70, std::int32_t{7});
  f.Put(0xA00000 + 0x74, std::int32_t{7});
  f.Put(0xA10000, std::uintptr_t{0xA20000});
  f.Put(0xA20000, kModule + 0x441EF38);
  // R730's other wrong registry contains a CDomicileBuildingType peer.
  f.Put(0xC00000 + 0x68, std::uintptr_t{0xC10000});
  f.Put(0xC00000 + 0x70, std::int32_t{1});
  f.Put(0xC00000 + 0x74, std::int32_t{1});
  f.Put(0xC10000, std::uintptr_t{0xC20000});
  f.Put(0xC20000, kModule + 0x4172FA8);
  f.Put(0xC20000 + 0x10, std::int32_t{7});
  return f;
}

} // namespace

int main() {
  using namespace xar::ck3_11906;
  {
    auto f = Scene();
    f.Put(kModule + 0x4FE7EE0, std::int32_t{30097});
    auto r = ReadPlayerWorldBuildingDefinitionSourcesV1(
        kModule, true, f.Access(), {3, kProvince, 512, 8});
    Require(!r.source_available && r.failure ==
                PlayerWorldBuildingFailureV1::player_actor_binding,
            "stock_gui_player_must_match_campaign_actor");
  }
  {
    auto f = Scene();
    auto r = ReadPlayerWorldBuildingDefinitionSourcesV1(
        kModule, true, f.Access(), {3, kProvince, 512, 8});
    Require(r.source_available && r.failure ==
                PlayerWorldBuildingFailureV1::none &&
                r.definition_source_count == 2 &&
                r.directly_held_barony_provinces ==
                    std::vector<PlayerHeldHoldingSourceV1>{{kBarony, kProvince}},
            "world_definitions_independent_of_closed_gui");
    Require(r.native_final_legality_evaluated &&
                r.final_legality_checks == 4 && !r.checks_truncated &&
                r.legal_samples ==
                    std::vector<PlayerWorldBuildingLegalSampleV1>{
                        {kBarony, kProvince, 22, 1}} &&
                !r.cost_ready && f.native_checks == 4,
            "same_frame_player_final_legality_sample_not_cost_or_action");
  }
  {
    auto f = Scene();
    f.Put(kModule + 0x570C108, std::uintptr_t{0});
    auto r = ReadPlayerWorldBuildingDefinitionSourcesV1(
        kModule, true, f.Access(), {3, kProvince, 512, 8});
    Require(!r.source_available && r.failure ==
                PlayerWorldBuildingFailureV1::registry_source &&
                r.definition_identity_diagnostic.registry_count == -1 &&
                f.native_checks == 0,
            "court_and_domicile_peers_cannot_substitute_manager_source");
  }
  {
    auto f = Scene();
    f.Put(0xD10000, std::uintptr_t{0xA20000});
    auto r = ReadPlayerWorldBuildingDefinitionSourcesV1(
        kModule, true, f.Access(), {3, kProvince, 512, 8});
    Require(!r.source_available && r.failure ==
                PlayerWorldBuildingFailureV1::definition_identity &&
                r.definition_identity_diagnostic.registry_count == 2 &&
                r.definition_identity_diagnostic.failed_index == 0 &&
                r.definition_identity_diagnostic.stage ==
                    PlayerWorldDefinitionIdentityStageV1::vtable_mismatch &&
                r.definition_identity_diagnostic.observed_vtable_rva ==
                    0x441EF38 && f.native_checks == 0,
            "court_type_peer_in_manager_is_red_not_building_legality");
  }
  {
    auto f = Scene();
    auto r = ReadPlayerWorldBuildingDefinitionSourcesV1(
        kModule, true, f.Access(false), {3, kProvince, 0, 0});
    Require(r.source_available && r.definition_source_count == 2 &&
                !r.native_final_legality_evaluated && r.legal_samples.empty(),
            "registry_only_does_not_claim_legality");
  }
  {
    auto f = Scene();
    auto r = ReadPlayerWorldBuildingDefinitionSourcesV1(
        kModule, true, f.Access(), {3, kProvince, 2, 8});
    Require(r.source_available && r.final_legality_checks == 2 &&
                r.checks_truncated && r.legal_samples.empty(),
            "bounded_sample_is_not_all_legal_candidates");
  }
  {
    auto f = Scene();
    f.Put(0xB10000, kModule + std::uintptr_t{0x44046D0});
    auto r = ReadPlayerWorldBuildingDefinitionSourcesV1(
        kModule, true, f.Access(), {3, kProvince, 512, 8});
    Require(!r.source_available && r.failure ==
                PlayerWorldBuildingFailureV1::definition_identity &&
                r.definition_source_count == 0 &&
                r.definition_identity_diagnostic.registry_count == 2 &&
                r.definition_identity_diagnostic.failed_index == 1 &&
                r.definition_identity_diagnostic.stage ==
                    PlayerWorldDefinitionIdentityStageV1::vtable_mismatch &&
                r.definition_identity_diagnostic.has_observed_vtable_rva &&
                r.definition_identity_diagnostic.observed_vtable_rva ==
                    0x44046D0 &&
                !r.definition_identity_diagnostic.has_observed_building_type_id,
            "definition_vtable_mismatch_keeps_red_with_pointer_free_rva");
  }
  {
    auto f = Scene();
    f.Put(0xD10008, std::uintptr_t{0});
    auto r = ReadPlayerWorldBuildingDefinitionSourcesV1(
        kModule, true, f.Access(), {3, kProvince, 512, 8});
    Require(!r.source_available && r.failure ==
                PlayerWorldBuildingFailureV1::definition_identity &&
                r.definition_identity_diagnostic.failed_index == 1 &&
                r.definition_identity_diagnostic.stage ==
                    PlayerWorldDefinitionIdentityStageV1::element_null &&
                !r.definition_identity_diagnostic.has_observed_vtable_rva,
            "null_world_element_is_not_zero_legal_buildings");
  }
  {
    auto f = Scene();
    f.Put(0xB10000, kModule + std::uintptr_t{0x6000000});
    auto r = ReadPlayerWorldBuildingDefinitionSourcesV1(
        kModule, true, f.Access(), {3, kProvince, 512, 8});
    Require(!r.source_available && r.failure ==
                PlayerWorldBuildingFailureV1::definition_identity &&
                r.definition_identity_diagnostic.stage ==
                    PlayerWorldDefinitionIdentityStageV1::vtable_mismatch &&
                !r.definition_identity_diagnostic.has_observed_vtable_rva,
            "out_of_image_pointer_has_no_receipt_address");
  }
  {
    auto f = Scene();
    f.Put(0xB10000 + 0x10, std::int32_t{-3});
    auto r = ReadPlayerWorldBuildingDefinitionSourcesV1(
        kModule, true, f.Access(), {3, kProvince, 512, 8});
    Require(!r.source_available && r.failure ==
                PlayerWorldBuildingFailureV1::definition_identity &&
                r.definition_identity_diagnostic.stage ==
                    PlayerWorldDefinitionIdentityStageV1::building_type_id_negative &&
                r.definition_identity_diagnostic.has_observed_building_type_id &&
                r.definition_identity_diagnostic.observed_building_type_id == -3,
            "negative_building_type_id_has_distinct_read_only_diagnostic");
  }
  {
    auto f = Scene();
    f.Put(0xB10000 + 0x10, std::int32_t{11});
    auto r = ReadPlayerWorldBuildingDefinitionSourcesV1(
        kModule, true, f.Access(), {3, kProvince, 512, 8});
    Require(!r.source_available && r.failure ==
                PlayerWorldBuildingFailureV1::definition_identity &&
                r.definition_identity_diagnostic.stage ==
                    PlayerWorldDefinitionIdentityStageV1::building_type_id_duplicate &&
                r.definition_identity_diagnostic.observed_building_type_id == 11,
            "duplicate_building_type_id_not_inferred_as_legality");
  }
  {
    auto f = Scene();
    f.validator_fails = true;
    auto r = ReadPlayerWorldBuildingDefinitionSourcesV1(
        kModule, true, f.Access(), {3, kProvince, 512, 8});
    Require(!r.source_available && r.failure ==
                PlayerWorldBuildingFailureV1::native_final_legality,
            "failed_validator_is_not_native_rejection");
  }
  {
    auto f = Scene();
    f.change_final_frame = true;
    auto r = ReadPlayerWorldBuildingDefinitionSourcesV1(
        kModule, true, f.Access(), {3, kProvince, 512, 8});
    Require(!r.source_available && r.failure ==
                PlayerWorldBuildingFailureV1::frame_changed,
            "same_paused_revision_after_native_checks");
  }
  std::cout << "GREEN player world building definitions and bounded player legality\n";
  return 0;
}
