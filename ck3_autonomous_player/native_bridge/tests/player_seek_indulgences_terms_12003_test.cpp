#include "xar_bridge/ck3_12003_player_seek_indulgences_mailbox.hpp"

#include <array>
#include <cstddef>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <utility>

namespace {
namespace terms = xar::ck3_12003::religion::seek_indulgences;
constexpr std::int32_t kActor = 29829;
constexpr std::uint32_t kRequestedRecipient = 0xF00001F5;
constexpr std::int32_t kEffectiveRecipient = 777;
constexpr std::int32_t kDate = 53226000;
constexpr std::uint64_t kEpoch = 41;
constexpr std::uint64_t kRevision = 701;
constexpr std::int32_t kDefinitionHash = 0x0BAD1234;
constexpr std::uint32_t kOfferPilgrimageFlag = 17;
std::array<std::byte, 0x2270> definition{};
std::array<std::byte, 0x730> option_row{};
std::array<std::byte, 0x30> player{};
void *active_context = nullptr;
bool selected = true, refreshed = false, finalized = false;
bool shown_value = true, can_send_value = false;
int constructed_count = 0, destroyed_count = 0;
int shown_count = 0, can_send_count = 0, option_set_count = 0;

void Require(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}
template <typename T>
void Write(void *object, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
}
void *GetDatabase() { return definition.data(); }
std::int32_t Hash(void *database, const char *key, std::uint32_t size) {
  Require(database == definition.data(), "wrong definition database");
  Require(std::string_view(key, size) == terms::kInteractionKey, "wrong fixed key");
  return kDefinitionHash;
}
void *Lookup(void *database, std::int32_t hash) {
  Require(database == definition.data() && hash == kDefinitionHash,
          "wrong definition lookup");
  return definition.data();
}
void *Construct(void *context, void *def, std::int32_t actor,
                std::int32_t recipient, void *special, bool resolve_defaults) {
  Require(def == definition.data() && actor == kActor,
          "wrong actor or interaction definition");
  Require(static_cast<std::uint32_t>(recipient) == kRequestedRecipient,
          "requested full-generation recipient was not preserved");
  Require(special == nullptr && resolve_defaults, "wrong two-role constructor profile");
  active_context = context;
  ++constructed_count;
  selected = true;
  refreshed = finalized = false;
  Write(context, 0, def);
  Write(context, 0x2D8, actor);
  Write(context, 0x2DC, kEffectiveRecipient);
  Write(context, 0x2E0, std::int32_t{-1});
  Write(context, 0x2E4, std::int32_t{888});
  Write(context, 0x2E8, std::int32_t{-1});
  Write(context, 0x2EC, actor);
  return context;
}
void SetOption(void *context, std::uint32_t flag, bool value) {
  Require(context == active_context && !refreshed && !value &&
          flag == kOfferPilgrimageFlag, "ordinary option was not unset before refresh");
  selected = value;
  ++option_set_count;
}
void Refresh(void *context, bool recompute) {
  Require(context == active_context && recompute && !selected,
          "refresh did not receive ordinary unselected profile");
  refreshed = true;
}
void Finalize(void *context) {
  Require(context == active_context && refreshed, "finalize preceded refresh");
  finalized = true;
}
bool ReadOption(void *context, std::uint32_t flag) {
  Require(context == active_context && finalized && flag == kOfferPilgrimageFlag,
          "option readback preceded finalization");
  return selected;
}
void Destroy(void *context) {
  Require(context == active_context && finalized, "wrong disposable context destruction");
  ++destroyed_count;
  active_context = nullptr;
}
bool Shown(void *context) {
  Require(context == active_context && finalized, "shown preceded finalization");
  ++shown_count;
  return shown_value;
}
bool CanSend(void *context, void *errors) {
  Require(context == active_context && finalized && errors == nullptr,
          "can_send did not use final native context");
  ++can_send_count;
  return can_send_value;
}
terms::Bindings FixtureBindings() {
  terms::Bindings bindings{};
  bindings.enabled = true;
  bindings.module_base = 0x10000000;
  bindings.get_database = &GetDatabase;
  bindings.stable_hash = &Hash;
  bindings.lookup_definition = &Lookup;
  bindings.construct_two_role = &Construct;
  bindings.set_option = &SetOption;
  bindings.read_option = &ReadOption;
  bindings.is_shown = &Shown;
  bindings.interaction.enabled = true;
  bindings.interaction.refresh = &Refresh;
  bindings.interaction.finalize = &Finalize;
  bindings.interaction.destroy = &Destroy;
  bindings.interaction.validate = &CanSend;
  return bindings;
}
xar::ck3_12003::PlayerSeekIndulgencesMailboxContext12003 Wrap(
    const terms::Context &observation) {
  xar::ck3_12003::PlayerSeekIndulgencesMailboxContext12003 query{};
  query.completed = true;
  query.envelope.frame_stable = true;
  query.envelope.expected_snapshot_revision = kRevision;
  auto &frame = query.envelope.expected_snapshot;
  frame.date_raw = kDate;
  frame.paused = true;
  frame.map_ready = true;
  frame.has_played_character = true;
  frame.played_character_alive = true;
  frame.played_character_id = kActor;
  query.requested_recipient_character_id = kRequestedRecipient;
  query.observation = observation;
  return query;
}
void RequireOrdinaryProfile(const terms::Context &observation) {
  Require(observation.identity.available &&
          observation.identity.requested_recipient_character_id == kRequestedRecipient &&
          observation.identity.effective_actor_id == kActor &&
          observation.identity.effective_recipient_id == kEffectiveRecipient &&
          observation.identity.secondary_actor_id == std::int32_t{-1} &&
          observation.identity.secondary_recipient_id == std::int32_t{888} &&
          observation.identity.intermediary_id == std::int32_t{-1} &&
          observation.identity.sixth_role_id == kActor,
          "six redirected native signed roles were not preserved");
  Require(observation.options.available && observation.options.declared_count == std::uint32_t{1} &&
          observation.options.selected_count == std::uint32_t{0} && observation.options.all_unselected == true,
          "stock declared option was confused with selected options");
  Require(observation.definition_stable_hash == static_cast<std::uint32_t>(kDefinitionHash),
          "definition provenance was lost");
}
void SaveSyntheticSession(const std::filesystem::path &directory) {
  // Session setup is explicitly synthetic, separate from the four complete
  // command_result frames produced by the real collector and wire serializer.
  const std::string hello =
      "{\"type\":\"hello\",\"protocol_version\":1,\"fixture_synthetic\":true,"
      "\"bridge_version\":\"0.1.0\",\"pid\":1,\"connection_generation\":1,"
      "\"game_version\":\"1.20.0.3\",\"executable_sha256\":\"" +
      std::string(terms::kExecutableSha256) +
      "\",\"capabilities\":[\"game.state.snapshot\"]}";
  const std::string snapshot =
      "{\"type\":\"state_snapshot\",\"protocol_version\":1,\"fixture_synthetic\":true,"
      "\"snapshot_id\":\"native:" + std::to_string(kRevision) +
      "\",\"revision\":" + std::to_string(kRevision) + ",\"state\":{"
      "\"phase\":\"map_hud\",\"date\":\"fixture-synthetic\",\"date_raw\":" +
      std::to_string(kDate) + ",\"speed\":1,\"paused\":true,\"map_ready\":true,"
      "\"history\":[],\"active_event\":null,\"pending_character_interaction\":null,"
      "\"played_character\":{\"character_id\":" + std::to_string(kActor) +
      ",\"alive\":true},\"one_life_settlement\":null,\"active_wars\":[],\"player_armies\":[]}}";
  for (const auto &entry : {std::pair{"hello.json", hello},
                           std::pair{"semantic-snapshot.json", snapshot}}) {
    std::ofstream stream(directory / entry.first, std::ios::binary);
    stream << entry.second << '\n';
    Require(stream.good(), "could not write synthetic session metadata");
  }
}
} // namespace

int main(int argc, char **argv) {
  try {
    Require(argc == 2, "usage: player_seek_indulgences_terms_12003_test OUTPUT_DIRECTORY");
    const std::filesystem::path output_directory(argv[1]);
    std::filesystem::create_directories(output_directory);
    SaveSyntheticSession(output_directory);
    Write(player.data(), 0x18, kActor);
    Write(definition.data(), 0x14, kDefinitionHash);
    Write(definition.data(), 0x18, terms::kInteractionKey.data());
    Write(definition.data(), 0x28, static_cast<std::uint64_t>(terms::kInteractionKey.size()));
    Write(definition.data(), 0x30, static_cast<std::uint64_t>(terms::kInteractionKey.size()));
    Write(definition.data(), 0x2258, static_cast<void *>(option_row.data()));
    Write(definition.data(), 0x2264, std::int32_t{1});
    Write(option_row.data(), 0x368, kOfferPilgrimageFlag);
    auto bindings = FixtureBindings();
    auto save = [&](const char *filename, const terms::Context &observation) {
      const auto serialized = xar::ck3_12003::SerializePlayerSeekIndulgencesTermsResult12003(
          Wrap(observation), "g2-read-02030000000000000000000000000001");
      Require(!serialized.empty(), "full command_result serializer returned empty bytes");
      std::ofstream stream(output_directory / filename, std::ios::binary);
      stream << serialized << '\n';
      Require(stream.good(), "could not write complete command_result fixture");
    };
    terms::Context observation{};
    Require(terms::ReadSeekIndulgencesTerms12003(bindings, player.data(), kActor,
        kDate, kEpoch, kRequestedRecipient, observation), "native false must remain available");
    RequireOrdinaryProfile(observation);
    Require(observation.shown.value == true && observation.can_send.value == false,
            "negative native final result was lost");
    save("negative-final.json", observation);

    can_send_value = true;
    Require(terms::ReadSeekIndulgencesTerms12003(bindings, player.data(), kActor,
        kDate, kEpoch, kRequestedRecipient, observation), "positive terms sample failed");
    RequireOrdinaryProfile(observation);
    Require(observation.shown.value == true && observation.can_send.value == true,
            "positive native booleans were lost");
    save("positive.json", observation);

    shown_value = false;
    Require(terms::ReadSeekIndulgencesTerms12003(bindings, player.data(), kActor,
        kDate, kEpoch, kRequestedRecipient, observation), "shown false must remain available");
    RequireOrdinaryProfile(observation);
    Require(observation.shown.value == false && observation.can_send.value == true,
            "shown and final eligibility were conflated");
    save("shown-false.json", observation);

    shown_value = true;
    bindings.interaction.validate = nullptr;
    Require(!terms::ReadSeekIndulgencesTerms12003(bindings, player.data(), kActor,
        kDate, kEpoch, kRequestedRecipient, observation), "failed native sample was called available");
    RequireOrdinaryProfile(observation);
    Require(observation.shown.available && observation.shown.value == true &&
          !observation.can_send.available && !observation.can_send.value &&
          std::string_view(observation.can_send.reason) == "native_evaluation_unavailable" &&
          std::string_view(observation.unavailable_reason) == "one_or_more_samples_unavailable",
          "sample failure was confused with native false");
    save("sample-failure.json", observation);

    Require(constructed_count == 4 && destroyed_count == 4 && option_set_count == 4 &&
          shown_count == 4 && can_send_count == 3 && active_context == nullptr,
          "disposable native context lifecycle or sample count mismatch");
    std::cout << "GREEN: four callback scenarios; production collector and full command_result serializer; no game contacted\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "RED: " << error.what() << '\n';
    return 1;
  }
}
