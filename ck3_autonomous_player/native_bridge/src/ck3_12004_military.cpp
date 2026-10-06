#include "xar_bridge/ck3_12004_military.hpp"

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12004_commands.hpp"

namespace xar::ck3_12004 {

ck3_12002::MilitaryBindings BindMilitaryImage12004(
    std::uintptr_t base, std::string_view sha,
    const ck3_12002::CommandBindings &commands) noexcept {
  ck3_12002::MilitaryBindings bindings{};
  if (!base || sha != kExecutableSha256 || !commands.enabled) return bindings;

  // Existing software copies synchronously through the caller's actual .4
  // command bundle. The adapter repairs this context after moving its bundle.
  bindings.submit_context = const_cast<ck3_12002::CommandBindings *>(&commands);
  bindings.submit_copy = &ck3_12002::SubmitCommandCopyCompat;

  // Each pair is an actual RIP target in its native constructor or clone.
  // Selected primary slots 0/+40 have separate finite dispatch receipts.
  bindings.raise_primary = base + 0x45345D0;
  bindings.raise_secondary = base + 0x4534668;
  bindings.move_primary = base + 0x476B178;
  bindings.move_secondary = base + 0x476B148;
  bindings.halt_primary = base + 0x476B080;
  bindings.halt_secondary = base + 0x476B118;
  bindings.disband_primary = base + 0x476AE58;
  bindings.disband_secondary = base + 0x476AE28;
  bindings.split_primary = base + 0x476AF20;
  bindings.split_secondary = base + 0x476AEF0;
  bindings.merge_primary = base + 0x476AB30;
  bindings.merge_secondary = base + 0x476ABC8;
  bindings.start_primary = base + 0x476A298;
  bindings.start_secondary = base + 0x476A330;
  bindings.stop_primary = base + 0x476A040;
  bindings.stop_secondary = base + 0x476A010;

  // ArmyWorld capital/default-raise and Supply route-progress bodies are
  // reused from their already closed actual .4 profiles.
  bindings.get_character_capital =
      reinterpret_cast<decltype(bindings.get_character_capital)>(base + 0x28B1CB0);
  bindings.resolve_raise_province =
      reinterpret_cast<decltype(bindings.resolve_raise_province)>(base + 0x24A5190);
  bindings.construct_raise =
      reinterpret_cast<decltype(bindings.construct_raise)>(base + 0x298C110);
  bindings.validate_raise =
      reinterpret_cast<decltype(bindings.validate_raise)>(base + 0x298C2A0);
  bindings.destroy_raise =
      reinterpret_cast<decltype(bindings.destroy_raise)>(base + 0x11F2DE0);
  bindings.move_mode =
      reinterpret_cast<decltype(bindings.move_mode)>(base + 0x296A080);
  bindings.character_command_allowed =
      reinterpret_cast<decltype(bindings.character_command_allowed)>(base + 0x29675D0);
  bindings.army_move_allowed =
      reinterpret_cast<decltype(bindings.army_move_allowed)>(base + 0x24AC190);
  bindings.move_allowed =
      reinterpret_cast<decltype(bindings.move_allowed)>(base + 0x2969550);
  bindings.construct_move_path =
      reinterpret_cast<decltype(bindings.construct_move_path)>(base + 0xD1A0B0);
  bindings.destroy_move =
      reinterpret_cast<decltype(bindings.destroy_move)>(base + 0x2969600);
  bindings.construct_halt =
      reinterpret_cast<decltype(bindings.construct_halt)>(base + 0x296A190);
  bindings.validate_halt =
      reinterpret_cast<decltype(bindings.validate_halt)>(base + 0x296A2D0);
  bindings.destroy_halt =
      reinterpret_cast<decltype(bindings.destroy_halt)>(base + 0x296A200);
  bindings.read_move_progress =
      reinterpret_cast<decltype(bindings.read_move_progress)>(base + 0x24AB2D0);
  bindings.read_route_first =
      reinterpret_cast<decltype(bindings.read_route_first)>(base + 0x24AA7B0);
  bindings.read_route_last =
      reinterpret_cast<decltype(bindings.read_route_last)>(base + 0x24AA800);
  bindings.move_progress_cutoff = reinterpret_cast<const std::int64_t *>(
      base + 0x5C699E8);
  bindings.construct_path_context =
      reinterpret_cast<decltype(bindings.construct_path_context)>(base + 0x2648040);
  bindings.build_route =
      reinterpret_cast<decltype(bindings.build_route)>(base + 0x2648130);
  bindings.validate_disband =
      reinterpret_cast<decltype(bindings.validate_disband)>(base + 0x296A600);
  bindings.validate_split =
      reinterpret_cast<decltype(bindings.validate_split)>(base + 0x296CF40);
  bindings.destroy_split =
      reinterpret_cast<decltype(bindings.destroy_split)>(base + 0x9D1560);
  bindings.create_merge =
      reinterpret_cast<decltype(bindings.create_merge)>(base + 0x297BCD0);
  // HolyWar's retained prefix25 + continuation364 close the full389B body.
  bindings.append_int_range =
      reinterpret_cast<decltype(bindings.append_int_range)>(base + 0x9E3790);
  bindings.validate_merge =
      reinterpret_cast<decltype(bindings.validate_merge)>(base + 0x296EF70);
  bindings.destroy_merge =
      reinterpret_cast<decltype(bindings.destroy_merge)>(base + 0x296A200);
  // Province owns both full validator bodies and Siege occurrence fields.
  bindings.validate_start =
      reinterpret_cast<decltype(bindings.validate_start)>(base + 0x29738A0);
  bindings.validate_stop =
      reinterpret_cast<decltype(bindings.validate_stop)>(base + 0x2973A50);
  bindings.destroy_assault =
      reinterpret_cast<decltype(bindings.destroy_assault)>(base + 0x9D1560);
  bindings.enabled = true;
  return bindings;
}

ck3_12003::NativeMaaRecruitmentBindings BindNativeMaaRecruitmentImage12004(
    std::uintptr_t base, std::string_view sha) noexcept {
  ck3_12003::NativeMaaRecruitmentBindings bindings{};
  if (!base || sha != kExecutableSha256) return bindings;
  bindings.character_storage_slot = reinterpret_cast<void **>(base + 0x5C67568);
  bindings.public_unit_storage_slot = reinterpret_cast<void **>(base + 0x5D1E380);
  bindings.type_registry_slot = reinterpret_cast<void **>(base + 0x5C67558);
  bindings.regular_personal_can_create =
      reinterpret_cast<ck3_12003::NativeMaaRegularPersonalCanCreate>(
          base + 0x296F9D0);
  bindings.regular_final_raw_quote =
      reinterpret_cast<ck3_12003::NativeMaaRegularFinalRawQuote>(
          base + 0x30BCE00);
  bindings.enabled = true;
  return bindings;
}

ck3_12003::NativeMaaCreateBindings BindNativeMaaCreateImage12004(
    std::uintptr_t base, std::string_view sha) noexcept {
  ck3_12003::NativeMaaCreateBindings bindings{};
  if (!base || sha != kExecutableSha256) return bindings;
  bindings.current_player_full_id_slot = reinterpret_cast<const std::int32_t *>(
      base + 0x54DBC00);
  bindings.type_registry_slot = reinterpret_cast<void **>(base + 0x5C67558);
  bindings.type_lookup = reinterpret_cast<ck3_12003::NativeMaaCreateTypeLookup>(
      base + 0x1AD5520);
  bindings.regular_personal_constructor =
      reinterpret_cast<ck3_12003::NativeMaaCreateConstructor>(base + 0x1338F70);
  bindings.regular_personal_can_create =
      reinterpret_cast<ck3_12003::NativeMaaCreateCanCreate>(base + 0x296F9D0);
  bindings.command_manager = reinterpret_cast<void *>(base + kCommandManagerRva12004);
  bindings.submit = reinterpret_cast<ck3_12003::NativeMaaCreateSubmit>(
      base + kQueueOwnedCommandRva12004);
  bindings.enabled = true;
  return bindings;
}

} // namespace xar::ck3_12004
