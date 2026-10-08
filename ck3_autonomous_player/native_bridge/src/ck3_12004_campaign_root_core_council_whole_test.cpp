// Unique new core-Council scene. Engine objects/callbacks are synthetic; the
// actual4 new reader and full Root serializer are real linked production code.
// Non-Council Root DTO fields are an explicit synthetic serialization baseline;
// this target does not replay the full Root native getter qualification.
#include "xar_bridge/ck3_12004_campaign.hpp"

#include <algorithm>
#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace xar::ck3_12004::campaign_root_detail {
bool ReadCouncilProjection(const CampaignRootNativeEnvironmentV1 &,
    const CampaignRootAccessV1 &, void *, std::int32_t, bool,
    game::CampaignRootCouncilV1 &, std::string_view &) noexcept;
}

namespace {
namespace actual = xar::ck3_12004;
namespace game = xar::game;
constexpr std::int32_t kOwner = 29829;
constexpr std::int32_t kChaplain = 56513;
constexpr std::int32_t kDate = 53222304;
constexpr std::uint64_t kRevision = 9;
constexpr std::string_view kNonce = "root-read-00000000000000000000000000000071";
constexpr std::array<std::string_view, 5> kKeys{
    "councillor_chancellor", "councillor_court_chaplain", "councillor_marshal",
    "councillor_spymaster", "councillor_steward"};
constexpr std::array<std::int32_t, 5> kTaskIds{7160,7162,7163,7164,7161};
constexpr std::array<std::int32_t, 5> kIncumbents{-1,kChaplain,1003,1004,1002};
constexpr std::array<std::string_view, 5> kTaskKeys{
    "task_foreign_affairs", "task_religious_relations", "task_organize_levies",
    "task_support_schemes", "task_develop_county"};
unsigned checks{};
void Check(bool value, const char *message) {
  ++checks;
  if (!value) throw std::runtime_error(message);
}
template<std::size_t N> using Bytes = std::array<std::byte,N>;
template<class Buffer, class T> void Put(Buffer &buffer, std::size_t offset, T value) {
  std::memcpy(buffer.data()+offset,&value,sizeof(value));
}
struct Fixture {
  Bytes<0x1D8> owner{};
  Bytes<0x240> landed{};
  std::array<Bytes<0x30>,5> characters{};
  std::array<Bytes<0x60>,5> tasks{}, types{};
  // No Position string exists here. The new reader must join pointer identity
  // from a typed requested-key lookup rather than dereference Position+18.
  std::array<Bytes<0x10>,5> positions{};
  Bytes<0x30> character_storage{}, task_storage{};
  std::vector<std::byte> character_slots = std::vector<std::byte>(60000U*0x10U);
  std::vector<std::byte> task_slots = std::vector<std::byte>(7300U*0x10U);
  std::array<std::int32_t,5> owner_task_ids{7164,7162,7160,7163,7161};
  Bytes<0xA8> state{};
  Bytes<0x150> data{};
  Bytes<0x860> province{};
  std::array<void*,100> provinces{};
  void *characters_ptr = character_storage.data(), *tasks_ptr = task_storage.data();
  void *character_fallback = nullptr, *task_fallback = nullptr;
  void *state_ptr = state.data();
  unsigned lookup_calls{}, task_key_reads{}, current_calls{}, maximum_calls{}, raw_position_reads{};
  bool native_arguments_valid = true;
  actual::CampaignRootNativeEnvironmentV1 environment{};
  actual::CampaignRootAccessV1 access{};
  Fixture();
};
Fixture *active{};
bool Memory(void *raw, const void *source, void *output, std::size_t bytes) noexcept {
  auto &f = *static_cast<Fixture*>(raw);
  const auto address = reinterpret_cast<std::uintptr_t>(source);
  for (const auto &p : f.positions) {
    const auto begin = reinterpret_cast<std::uintptr_t>(p.data());
    if (address >= begin && address < begin+p.size()) {
      ++f.raw_position_reads;
      return false;
    }
  }
  if (!source || !output || bytes == 0) return false;
  std::memcpy(output,source,bytes); return true;
}
bool String(void *raw, const void *native_string, std::string &out) noexcept {
  auto &f = *static_cast<Fixture*>(raw);
  for (std::size_t i=0; i<f.types.size(); ++i) {
    if (native_string == f.types[i].data()+0x18) {
      ++f.task_key_reads;
      out.assign(kTaskKeys[i]); return true;
    }
  }
  return false;
}
const void *Lookup(const void *owner, const std::string *key) {
  ++active->lookup_calls;
  active->native_arguments_valid &= owner == active->owner.data() && key != nullptr;
  if (!key) return nullptr;
  for (std::size_t i=0; i<kKeys.size(); ++i)
    if (*key == kKeys[i]) return active->tasks[i].data();
  active->native_arguments_valid = false;
  return nullptr;
}
std::int64_t *Current(void *type, std::int64_t *out, void *scopes) {
  ++active->current_calls;
  active->native_arguments_valid &= type == active->types[4].data() &&
      scopes == active->tasks[4].data()+0x40 && out != nullptr;
  *out = 500000; return out;
}
std::int64_t *Maximum(void *type, std::int64_t *out, void *scopes) {
  ++active->maximum_calls;
  active->native_arguments_valid &= type == active->types[4].data() &&
      scopes == active->tasks[4].data()+0x40 && out != nullptr;
  *out = 2000000; return out;
}
Fixture::Fixture() {
  active = this;
  Put(owner,0x18,kOwner); Put(owner,0x1C0,landed.data());
  Put(landed,0x230,owner_task_ids.data()); Put(landed,0x23C,std::int32_t{5});
  Put(character_storage,0x20,character_slots.data()); Put(character_storage,0x2C,std::int32_t{60000});
  Put(task_storage,0x20,task_slots.data()); Put(task_storage,0x2C,std::int32_t{7300});
  Put(character_slots,static_cast<std::size_t>(kOwner)*0x10+8,owner.data());
  constexpr std::array<std::int32_t,5> character_ids{kChaplain,1003,1004,1002,1005};
  for (std::size_t i=0; i<characters.size(); ++i) {
    Put(characters[i],0x18,character_ids[i]);
    Put(character_slots,static_cast<std::size_t>(character_ids[i])*0x10+8,characters[i].data());
  }
  for (std::size_t i=0; i<tasks.size(); ++i) {
    Put(task_slots,static_cast<std::size_t>(kTaskIds[i])*0x10+8,tasks[i].data());
    Put(tasks[i],0x10,kTaskIds[i]); Put(tasks[i],0x18,types[i].data());
    Put(tasks[i],0x40,kIncumbents[i]); Put(tasks[i],0x44,kOwner);
    Put(types[i],0x40,positions[i].data());
    Put(types[i],0x48,std::int32_t{0}); Put(types[i],0x54,std::int32_t{0});
  }
  // Real task objects encode all three existing native task/progress kinds.
  Put(types[3],0x48,std::int32_t{2}); Put(types[3],0x54,std::int32_t{1});
  Put(tasks[3],0x48,std::uint16_t{4}); Put(tasks[3],0x50,std::int32_t{1005});
  Put(tasks[3],0x20,std::int64_t{2500000}); tasks[3][0x39] = std::byte{1};
  Put(types[4],0x48,std::int32_t{1}); Put(types[4],0x54,std::int32_t{2});
  Put(tasks[4],0x48,std::uint16_t{8}); Put(tasks[4],0x50,std::int32_t{77});
  Put(state,0xA0,data.data()); provinces[77] = province.data();
  Put(data,0x140,provinces.data()); Put(data,0x14C,std::int32_t{100});
  Put(province,0x10,std::int32_t{77}); Put(province,0x85C,std::uint32_t{0x50726F76});
  environment.exact_build_admitted = true;
  environment.offline_fixture_function_overrides = true;
  environment.character_storage_slot = &characters_ptr;
  environment.character_fallback_slot = &character_fallback;
  environment.active_council_task_storage_slot = &tasks_ptr;
  environment.active_council_task_fallback_slot = &task_fallback;
  environment.game_state_slot = &state_ptr;
  environment.council_position_lookup = &Lookup;
  environment.council_value_progress_current = &Current;
  environment.council_value_progress_maximum = &Maximum;
  access.context = this; access.read_memory = &Memory; access.read_string = &String;
}
game::CampaignRootContextV1 SyntheticNonCouncilBaseline(game::CampaignRootCouncilV1 council) {
  game::CampaignRootContextV1 root{};
  root.status = game::CampaignRootContextStatusV1::available;
  root.snapshot_revision = kRevision; root.date_raw = kDate;
  root.local_player_id = 7; root.player_character_id = kOwner; root.player_character_alive = true;
  root.player_monthly_gold_income = game::FixedPointValue{500000,100000};
  root.player_health = game::FixedPointValue{600000,100000};
  root.player_legitimacy_v1 = game::CampaignRootLegitimacyV1{std::nullopt,"data_absent"};
  root.player_domain_size = 3; root.player_domain_limit = 7; root.player_targeting_faction_count = 0;
  root.primary_title = game::CampaignRootTitleV1{300,3,"duchy"};
  root.primary_title_succession_character_ids = {1001};
  game::CampaignRootHeldTitleSuccessionV1 held{};
  held.title = *root.primary_title; held.first_heir_character_id = 1001; held.primary = true;
  root.held_title_partition.push_back(std::move(held));
  root.capital_province_id = 77; root.top_liege_character_id = kOwner; root.independent = true;
  root.government = game::CampaignRootGovernmentV1{"feudal_government",
      {"government_is_feudal","government_uses_domain_limit"},2};
  root.council = std::move(council);
  // These non-Council readiness fields belong to the disclosed synthetic DTO
  // baseline. Only council_ready is derived from the new actual reader output.
  root.readiness = {true,true,true,true,true,true,true,true,
      root.council->status == game::CampaignRootCouncilStatusV1::available,
      true,true,true,true,true,true,true,true,true};
  return root;
}
void CheckCouncil(const Fixture &f, const game::CampaignRootCouncilV1 &out) {
  Check(out.status == game::CampaignRootCouncilStatusV1::available &&
      out.owner_character_id == kOwner && out.positions.size() == 5 &&
      !out.auxiliary_vacancies_complete && out.unavailable_reason.empty(),
      "real new reader publishes ordinary core roles in its existing coverage");
  for (std::size_t i=0; i<out.positions.size(); ++i)
    Check(out.positions[i].position_key == kKeys[i], "core keys come from typed lookup and sort canonically");
  const auto &vacant = out.positions[0];
  Check(!vacant.incumbent_character_id && !vacant.task_key && !vacant.task_type &&
      !vacant.target && !vacant.frozen && !vacant.progress,
      "actual valid Chancellor task with incumbent -1 retains legitimate vacancy nulls");
  const auto &chaplain = out.positions[1];
  Check(chaplain.incumbent_character_id == kChaplain && chaplain.task_key == "task_religious_relations" &&
      chaplain.task_type == game::CampaignRootCouncilTaskTypeV1::general && !chaplain.target &&
      chaplain.frozen == false && chaplain.progress &&
      chaplain.progress->kind == game::CampaignRootCouncilProgressKindV1::infinite &&
      !chaplain.progress->current && !chaplain.progress->maximum,
      "current Chaplain RR incumbent and all occupied fields are actually projected");
  const auto &court = out.positions[3], &county = out.positions[4];
  Check(court.task_type == game::CampaignRootCouncilTaskTypeV1::court && court.target &&
      court.target->character_id == 1005 && court.frozen == true && court.progress &&
      court.progress->current == game::FixedPointValue{2500000,100000} &&
      court.progress->maximum == game::FixedPointValue{10000000,100000},
      "court target full-ID and native percentage progress retain their typed values");
  Check(county.task_type == game::CampaignRootCouncilTaskTypeV1::county && county.target &&
      county.target->province_id == 77 && county.progress &&
      county.progress->kind == game::CampaignRootCouncilProgressKindV1::value &&
      county.progress->current == game::FixedPointValue{500000,100000} &&
      county.progress->maximum == game::FixedPointValue{2000000,100000},
      "actual county target and value progress callbacks retain their source operands");
  Check(f.native_arguments_valid && f.lookup_calls == 5 && f.task_key_reads == 4 &&
      f.current_calls == 1 && f.maximum_calls == 1 && f.raw_position_reads == 0,
      "five native typed seat requests consume no unproved raw Position key");
}
void Save(const std::filesystem::path &directory, const char *file, const std::string &bytes) {
  std::ofstream output(directory/file,std::ios::binary);
  output << bytes << '\n'; Check(static_cast<bool>(output),"save new whole production envelope");
}
} // namespace

int main(int argc, char **argv) {
  if (argc != 2) { std::cerr << "usage: root-core-council-whole OUTPUT_DIR\n"; return 2; }
  try {
    Fixture f;
    game::CampaignRootCouncilV1 council{};
    std::string_view failure;
    Check(actual::campaign_root_detail::ReadCouncilProjection(f.environment,f.access,
        f.owner.data(),kOwner,true,council,failure) && failure.empty(),
        "linked actual4 ReadCouncilProjection executes the new provider");
    CheckCouncil(f,council);
    const auto root = SyntheticNonCouncilBaseline(std::move(council));
    const auto body = actual::SerializeCampaignRootContextV1(root);
    Check(!body.empty(),"actual4 full Root serializer accepts the real new Council DTO");
    const std::string whole = "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"" +
        std::string(kNonce) + "\",\"ok\":true,\"result\":{\"step\":\"query-campaign-root-context-v1\","
        "\"accepted\":true,\"status\":\"available\",\"query_sequence\":1,\"snapshot_revision\":9,"
        "\"campaign_root_context\":" + body + ",\"backend_id\":\"native-headless\"}}";
    const std::filesystem::path directory = argv[1];
    std::filesystem::create_directories(directory);
    Save(directory,"full-root-core-council.json",whole);
    const std::string receipt = "{\"schema\":\"xar.ck3.root-core-council-12004-native-whole-fixture/v1\","
        "\"status\":\"GREEN\",\"packet_file\":\"full-root-core-council.json\",\"request_id\":\"" +
        std::string(kNonce) + "\",\"exact_build\":{\"game_version\":\"1.20.0.4\",\"executable_sha256\":\"" +
        std::string(actual::kExecutableSha256) + "\"},\"frame\":{\"owner_character_id\":29829,"
        "\"public_revision\":9,\"native_revision\":9,\"date_raw\":53222304,\"paused\":true,\"map_ready\":true},"
        "\"expected_core_keys\":[\"councillor_chancellor\",\"councillor_court_chaplain\",\"councillor_marshal\","
        "\"councillor_spymaster\",\"councillor_steward\"],\"expected_chaplain_incumbent\":56513,"
        "\"expected_chaplain_task\":\"task_religious_relations\",\"new_reader_calls\":1,\"native_lookup_callbacks\":5,"
        "\"occupied_task_key_reads\":4,\"current_progress_callbacks\":1,\"maximum_progress_callbacks\":1,"
        "\"raw_Position_key_reads\":0,\"whole_packets\":1,\"synthetic_engine_objects_callbacks\":true,"
        "\"synthetic_nonCouncil_Root_DTO_baseline\":true,\"actual4_new_council_reader\":true,"
        "\"actual4_full_root_serializer\":true,\"full_root_getter_loop_executed\":false,"
        "\"production_replacement_definitions\":false,\"game_operations\":0,\"game_days\":0,"
        "\"old_candidate_action_receipt_replays\":0,\"production_live\":false,\"g2_credit\":0,\"checks\":" +
        std::to_string(checks) + "}";
    Save(directory,"native-root-council-receipt.json",receipt);
    active = nullptr;
    std::cout << "actual4 Root core Council: one new reader scene and whole packet\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n'; return 1;
  }
}
