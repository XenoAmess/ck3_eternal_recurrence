#pragma once

inline int CharacterPublicCase14(int argc, char **argv) {
  if (argc != 5) return 90;
  actor_id = static_cast<std::uint32_t>(std::stoull(argv[1]));
  recipient_id = static_cast<std::uint32_t>(std::stoull(argv[2]));
  const std::string_view role = argv[3];
  const bool member_only = role == "member";
  const bool expect_reject = role == "stale-actor" || role == "stale-recipient" ||
      role == "absent-actor" || role == "absent-member" || role == "duplicate-member";
  if (!member_only && !expect_reject && role != "leader" && role != "mixed-members") return 92;
  const std::filesystem::path out = argv[4];
  std::filesystem::create_directories(out);
  if ((actor_id & 0x00FFFFFFU) >= 8 || (recipient_id & 0x00FFFFFFU) >= 8 ||
      (actor_id & 0x00FFFFFFU) == (recipient_id & 0x00FFFFFFU)) return 91;
  World09 w(static_cast<std::uint32_t>(source_id), false, false);
  if (member_only) Put(w.fixture.faction.data(), 0x44, std::uint32_t{UINT32_MAX});
  std::array<std::byte, 3 * 0x20> member_rows{};
  std::array<std::array<std::byte, 0x1D8>, 2> extra_characters{};
  std::vector<std::int32_t> expected_members{std::bit_cast<std::int32_t>(recipient_id)};
  if (role == "stale-actor") Put(w.fixture.characters[0].data(), 0x18, actor_id ^ 0x01000000U);
  if (role == "stale-recipient") Put(w.fixture.characters[1].data(), 0x18, recipient_id ^ 0x01000000U);
  if (role == "absent-actor") {
    Put(w.fixture.player_entry.data(), 0xB0, std::uint32_t{UINT32_MAX});
    Put(w.fixture.characters[0].data(), 0x18, std::uint32_t{UINT32_MAX});
    Put(w.fixture.faction.data(), 0x40, std::uint32_t{UINT32_MAX});
  }
  if (role == "absent-member") Put(w.fixture.faction_member.data(), 8, std::uint32_t{UINT32_MAX});
  if (role == "duplicate-member" || role == "mixed-members") {
    std::memcpy(member_rows.data(), w.fixture.faction_member.data(), 0x20);
    if (role == "duplicate-member") {
      std::memcpy(member_rows.data() + 0x20, member_rows.data(), 0x20);
      Put(w.fixture.faction.data(), 0x54, std::int32_t{2});
    } else {
      if (actor_id != 0x03000001U || recipient_id != 0x80000000U) return 93;
      const std::array<std::uint32_t, 2> ids{0xFF000002U, 3U};
      for (std::size_t i = 0; i < ids.size(); ++i) {
        Put(extra_characters[i].data(), 0x18, ids[i]);
        Put(w.fixture.slots.data(), (ids[i] & 0x00FFFFFFU) * 0x10ULL + 8, extra_characters[i].data());
        Put(member_rows.data(), (i + 1) * 0x20 + 8, ids[i]);
        Put(member_rows.data(), (i + 1) * 0x20 + 0x0C, source_id);
        expected_members.push_back(std::bit_cast<std::int32_t>(ids[i]));
      }
      Put(w.fixture.faction.data(), 0x54, std::int32_t{3});
      std::sort(expected_members.begin(), expected_members.end());
    }
    Put(w.fixture.faction.data(), 0x48, member_rows.data());
  }
  const auto actor_signed = std::bit_cast<std::int32_t>(actor_id);
  const auto recipient_signed = std::bit_cast<std::int32_t>(recipient_id);
  const game::PlayerFactionAlertsFrameV1 frame{1, 53175816, true, true, true, true, actor_signed};
  CoreSnapshotPrefix core{};
  const bool core_ok = ck3_12004::ReadCoreSnapshot(w.fixture.b.interaction.core, core) &&
      core.played_character_id == actor_signed;
  game::PlayerFactionAlertsV1 alerts{};
  const bool reader_ok = Alerts09(&w, frame, alerts);
  const std::string wire = SerializePlayerFactionAlerts12004(alerts);
  WriteWire(out, "public-alerts.json", wire);
  RouterAdapter adapter;
  WriteWire(out, "public-alerts-whole.json", SerializePlayerFactionAlertsWhole12004(
      alerts, 1, "character-public14", adapter.descriptor()));
  game::PlayerTargetingFactionV1 entity{};
  const bool entity_ok = ReadFactionEntity12004(w.fixture.factions, w.fixture.faction_access,
      source_id, entity) == ReadFactionEntityResult12004::available;
  const bool roles_ok = reader_ok && alerts.player_character_id == actor_signed &&
      alerts.targeting_factions.size() == 1 &&
      alerts.targeting_factions[0].target_character_id == actor_signed &&
      (member_only ? !alerts.targeting_factions[0].leader_character_id.has_value()
                   : alerts.targeting_factions[0].leader_character_id == recipient_signed) &&
      alerts.targeting_factions[0].character_member_ids == expected_members;
  std::string expected_wire_members = "\"character_member_ids\":[";
  for (const auto id : expected_members) {
    if (expected_wire_members.back() != '[') expected_wire_members += ',';
    expected_wire_members += std::to_string(id);
  }
  expected_wire_members += ']';
  const bool wire_ok = reader_ok && !wire.empty() &&
      wire.find("\"player_character_id\":" + std::to_string(actor_signed)) != std::string::npos &&
      wire.find("\"target_character_id\":" + std::to_string(actor_signed)) != std::string::npos &&
      wire.find(expected_wire_members) != std::string::npos;
  const bool pass = core_ok && reader_ok && entity_ok && roles_ok && wire_ok;
  const bool control_pass = !reader_ok && !entity_ok;
  std::ofstream(out/"SUMMARY14.json") << "{\"machine_id\":\"xenoamess-full-tower-eb9d2c1186\","
      "\"actual_Core_alerts_projector_serializer\":true,\"authored_alerts_DTO\":false,"
      "\"Character_ID_memory_authored\":true,\"Character_allocator_machinecode_executed_here\":false,"
      "\"private_Handler_executed\":false,\"public_Handle_executed\":false,\"query_sequence_authored\":true,"
      "\"actor_raw\":" << actor_id << ",\"actor_signed\":" << actor_signed
      << ",\"recipient_raw\":" << recipient_id << ",\"recipient_signed\":" << recipient_signed
      << ",\"member_only\":" << member_only << ",\"Core\":" << core_ok << ",\"reader\":" << reader_ok
      << ",\"entity\":" << entity_ok << ",\"roles\":" << roles_ok << ",\"wire\":" << wire_ok
      << ",\"full_pass\":" << pass << ",\"control_pass\":" << control_pass << "}\n";
  std::cout << "actor=" << actor_signed << " recipient=" << recipient_signed
      << " Core=" << core_ok << " reader=" << reader_ok << " entity=" << entity_ok
      << " roles=" << roles_ok << " wire=" << wire_ok << '\n';
  return (expect_reject ? control_pass : pass) ? 0 : 1;
}
