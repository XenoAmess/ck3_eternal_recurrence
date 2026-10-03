#include "xar_bridge/ck3_12003_county_conversion.hpp"

#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>

namespace c = xar::ck3_12002;
namespace r = c::religion::clergy;
namespace q = xar::ck3_12003::religion::county_conversion;
namespace {
template <std::size_t N> using Bytes = std::array<std::byte, N>;
template <typename Buffer, typename T>
void Put(Buffer &b, std::size_t at, T value) {
  std::memcpy(b.data() + at, &value, sizeof(value));
}
template <typename T> T Load(const void *b, std::size_t at) {
  T result{};
  std::memcpy(&result, static_cast<const std::byte *>(b) + at, sizeof(result));
  return result;
}
template <typename Buffer>
void Key(Buffer &b, std::size_t at, std::string_view key) {
  Put(b, at, key.data()); Put(b, at + 0x10, std::uint64_t{key.size()});
  Put(b, at + 0x18, std::uint64_t{key.size() > 15 ? key.size() : 31});
}

struct Fixture {
  static constexpr std::int32_t owner_id = 0x03000004;
  static constexpr std::int32_t incumbent_id = 0x06000005;
  static constexpr std::int32_t other_holder_id = 0x02000007;
  static constexpr std::int32_t task_id = 0x02000006;
  static constexpr std::array<std::int32_t, 3> title_ids{
      0x06000001, 0x04000002, 0x01000003};
  static constexpr std::array<std::int32_t, 3> province_ids{3, 1, 2};
  static constexpr std::array<std::uint32_t, 3> rite_ids{153, 0, 0x83000003};
  static constexpr std::array<std::int64_t, 3> rates{500000, 125000, 350000};
  Bytes<0xA8> state{};
  Bytes<0x28> jomini{};
  Bytes<0x1F8> players{};
  Bytes<0x78> player{};
  std::vector<std::byte> data = std::vector<std::byte>(0x22350);
  Bytes<0xE0> entry{};
  std::array<void *, 1> entries{entry.data()};
  Bytes<0x30> characters{}, tasks{}, titles{};
  Bytes<0xA0> character_slots{}, task_slots{}, title_slots{};
  Bytes<0x1D8> owner{}, incumbent{}, other_holder{};
  Bytes<0x240> landed{};
  Bytes<0x68> task{}, rr_type{}, conversion_type{};
  Bytes<0x60> position{};
  std::array<std::int32_t, 1> task_ids{task_id};
  std::array<Bytes<0x860>, 3> provinces{};
  std::array<Bytes<0x390>, 3> counties{};
  std::array<Bytes<0x130>, 3> title_objects{};
  std::array<Bytes<0x10>, 3> rites{};
  std::array<void *, 3> target_pointers{};
  Bytes<0x100> map{};
  std::array<void *, 4> province_pointers{};
  std::array<Bytes<0x20>, 4> province_entries{};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data();
  void *characters_ptr = characters.data(), *tasks_ptr = tasks.data();
  void *titles_ptr = titles.data(), *database_ptr = conversion_type.data(), *fallback_ptr = nullptr;
  bool shown_value = true, valid_value = true, empty_targets = false;
  int rejected_ordinal = -1, rate_failure_ordinal = -1, rite_failure_ordinal = -1;
  bool bad_arguments = false;
  int shown_calls = 0, valid_calls = 0, producer_calls = 0, target_calls = 0;
  int candidate_rate_calls = 0, current_rate_calls = 0, rite_calls = 0;
  int allocations = 0, releases = 0;

  Fixture() {
    Put(state, 8, std::int32_t{53230008}); Put(state, 0x70, std::int32_t{2});
    Put(state, 0xA0, data.data());
    Put(jomini, 0x18, players.data()); jomini[0x20] = std::byte{1};
    Put(players, 0x1F0, std::int32_t{7}); Put(player, 0x70, std::int32_t{7});
    Put(data, c::kPlayerCharacterManagerOffset + 0x58, entries.data());
    Put(data, c::kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(entry, 0xD8, std::int32_t{7}); Put(entry, 0xB0, owner_id);
    Put(characters, 0x20, character_slots.data()); Put(characters, 0x2C, std::int32_t{10});
    Put(character_slots, 4 * 0x10 + 8, owner.data()); Put(owner, 0x18, owner_id);
    Put(character_slots, 5 * 0x10 + 8, incumbent.data()); Put(incumbent, 0x18, incumbent_id);
    Put(character_slots, 7 * 0x10 + 8, other_holder.data()); Put(other_holder, 0x18, other_holder_id);
    Put(owner, r::kCharacterRiteOffset, std::uint32_t{152});
    Put(incumbent, r::kCharacterRiteOffset, std::uint32_t{152});
    Put(owner, r::kLandedOffset, landed.data());
    Put(landed, r::kTaskIdsOffset, task_ids.data());
    Put(landed, r::kTaskCountOffset, std::int32_t{1});
    Put(tasks, 0x20, task_slots.data()); Put(tasks, 0x2C, std::int32_t{10});
    Put(task_slots, 6 * 0x10 + 8, task.data()); Put(task, r::kTaskIdentityOffset, task_id);
    Put(task, r::kTaskTypeOffset, rr_type.data()); Put(task, r::kTaskOwnerOffset, owner_id);
    Put(task, r::kTaskIncumbentOffset, incumbent_id);
    Put(task, 0x20, std::int64_t{8750000}); Put(task, 0x48, std::uint32_t{0});
    Put(task, 0x50, std::int32_t{-1});
    Key(rr_type, 0x18, "task_religious_relations");
    Key(conversion_type, 0x18, q::kTaskKey);
    Put(rr_type, 0x40, position.data()); Put(conversion_type, 0x40, position.data());
    Put(rr_type, 0x48, std::int32_t{0}); Put(conversion_type, 0x48, std::int32_t{1});
    Put(rr_type, 0x54, std::int32_t{0}); Put(conversion_type, 0x54, std::int32_t{1});
    Key(position, r::kPositionKeyOffset, r::kPositionKey);
    Put(titles, 0x20, title_slots.data()); Put(titles, 0x2C, std::int32_t{10});
    for (std::size_t i = 0; i < 3; ++i) {
      Put(provinces[i], 0x10, province_ids[i]);
      Put(provinces[i], 0x85C, std::uint32_t{0x50726F76});
      Put(provinces[i], 0x848, counties[i].data());
      Put(counties[i], 0x18, title_ids[i]); Put(counties[i], 0x384, rite_ids[i]);
      Put(title_objects[i], 0x10, title_ids[i]);
      Put(title_objects[i], 0x128, i == 1 ? owner_id : other_holder_id);
      const auto index = static_cast<std::uint32_t>(title_ids[i]) & 0xFFFFFFU;
      Put(title_slots, static_cast<std::size_t>(index) * 0x10 + 8, title_objects[i].data());
      Put(rites[i], 8, rite_ids[i]); target_pointers[i] = provinces[i].data();
      province_pointers[static_cast<std::size_t>(province_ids[i])] = provinces[i].data();
    }
    Put(data, 0x140, province_pointers.data()); Put(data, 0x14C, std::int32_t{4});
  }
};
Fixture *f = nullptr;
void *Player(void *) { return f->player.data(); }
bool Read(void *, const void *address, void *out, std::size_t size) noexcept {
  if (f->rite_failure_ordinal >= 0 && address == f->counties[static_cast<std::size_t>(f->rite_failure_ordinal)].data() + 0x384)
    return false;
  std::memcpy(out, address, size); return true;
}
bool UnusedPositionPredicate(void *, std::int32_t) { f->bad_arguments = true; return false; }
bool UnusedTaskPredicate(void *, void *) { f->bad_arguments = true; return false; }
bool UnusedCanFire(void *, void *, void *, std::uint32_t, void *) { f->bad_arguments = true; return false; }
void *UnusedCourtOwner(void *) { f->bad_arguments = true; return nullptr; }
std::int32_t Hash(void *, const char *key, std::uint32_t) {
  if (std::string_view{key} != q::kTaskKey) f->bad_arguments = true;
  return 0x123456;
}
const void *Lookup(const void *database, std::int32_t hash) {
  if (database != f->database_ptr || hash != 0x123456) f->bad_arguments = true;
  return f->conversion_type.data();
}
bool Shown(const void *type, const void *scopes) {
  ++f->shown_calls;
  if (type != f->conversion_type.data() ||
      Load<std::int32_t>(scopes, 0) != Fixture::incumbent_id ||
      Load<std::int32_t>(scopes, 4) != Fixture::owner_id) f->bad_arguments = true;
  return f->shown_value;
}
bool Valid(const void *type, const void *scopes, void *breakdown) {
  ++f->valid_calls;
  if (type != f->conversion_type.data() || breakdown != nullptr ||
      Load<std::int32_t>(scopes, 0) != Fixture::incumbent_id ||
      Load<std::int32_t>(scopes, 4) != Fixture::owner_id) f->bad_arguments = true;
  return f->valid_value;
}
int Ordinal(const void *province) {
  for (int i = 0; i < 3; ++i)
    if (province == f->provinces[static_cast<std::size_t>(i)].data()) return i;
  f->bad_arguments = true; return -1;
}
bool TargetValid(const void *type, const void *incumbent, const void *province, void *breakdown) {
  ++f->target_calls;
  if (type != f->conversion_type.data() || breakdown != nullptr ||
      incumbent != f->incumbent.data()) f->bad_arguments = true;
  return Ordinal(province) != f->rejected_ordinal;
}
void Initialize(void *allocator, std::uintptr_t *address, std::int32_t *capacity) {
  ++f->allocations; *address = reinterpret_cast<std::uintptr_t>(allocator) + 8; *capacity = 64;
}
void Produce(const void *incumbent, const void *type, bool expand_court,
             q::NativeVector *out, bool first_only) {
  ++f->producer_calls;
  if (type != f->conversion_type.data() || expand_court || first_only ||
      incumbent != f->incumbent.data()) f->bad_arguments = true;
  out->data_address = reinterpret_cast<std::uintptr_t>(f->target_pointers.data());
  out->capacity = 3; out->count = f->empty_targets ? 0 : 3;
}
void Release(void *, void *address, std::size_t size) {
  ++f->releases;
  if (address != f->target_pointers.data() || size != sizeof(std::uintptr_t)) f->bad_arguments = true;
}
std::int64_t *MonthlyRate(const void *type, std::int64_t *out, const void *scopes,
                        void *breakdown, bool frozen) {
  if (type != f->conversion_type.data() || breakdown != nullptr ||
      Load<std::int32_t>(scopes, 0) != Fixture::incumbent_id ||
      Load<std::int32_t>(scopes, 4) != Fixture::owner_id) f->bad_arguments = true;
  if (scopes == f->task.data() + 0x40) {
    ++f->current_rate_calls;
    if (!frozen) f->bad_arguments = true;
    *out = 777000; return out;
  }
  ++f->candidate_rate_calls;
  if (frozen || Load<std::uint32_t>(scopes, 8) != 8U) f->bad_arguments = true;
  const auto id = Load<std::int32_t>(scopes, 0x10);
  for (int i = 0; i < 3; ++i) {
    if (id != Fixture::province_ids[static_cast<std::size_t>(i)]) continue;
    if (i == f->rate_failure_ordinal) return nullptr;
    *out = Fixture::rates[static_cast<std::size_t>(i)]; return out;
  }
  f->bad_arguments = true; return nullptr;
}
const void *CountyRite(const void *county) {
  ++f->rite_calls;
  for (std::size_t i = 0; i < 3; ++i)
    if (county == f->counties[i].data()) return f->rites[i].data();
  f->bad_arguments = true; return nullptr;
}
q::Environment Bind(Fixture &fixture) {
  f = &fixture;
  q::Environment e{}; e.exact_build_admitted = true; e.offline_fixture = true;
  e.executable_sha256 = xar::ck3_12003::kExecutableSha256;
  e.clergy.enabled = true; e.clergy.offline_fixture = true;
  e.clergy.executable_sha256 = c::kExecutableSha256;
  e.clergy.core = {true, &f->state_ptr, &f->jomini_ptr, &f->characters_ptr, &Player};
  e.clergy.task_storage_slot = &f->tasks_ptr; e.clergy.read_memory = &Read;
  // The shared clergy Exact() requires its established appointment bindings.
  // County observations must never invoke these fixture-only link callbacks.
  e.clergy.valid_position = &UnusedPositionPredicate;
  e.clergy.valid_character = &UnusedPositionPredicate;
  e.clergy.can_reassign = &UnusedTaskPredicate; e.clergy.can_fire = &UnusedCanFire;
  e.clergy.court_owner = &UnusedCourtOwner;
  e.allocator.exact_build_admitted = true;
  e.allocator.offline_fixture_function_overrides = true;
  e.allocator.admitted_executable_sha256 = c::kExecutableSha256;
  e.allocator.initialize_vector = &Initialize; e.allocator.release_allocation = &Release;
  e.game_state_slot = &f->state_ptr; e.title_storage_slot = &f->titles_ptr;
  e.title_fallback_slot = &f->fallback_ptr;
  e.task_type_database_slot = &f->database_ptr; e.task_type_fallback_slot = &f->fallback_ptr;
  e.hash_key = &Hash; e.lookup_type = &Lookup; e.shown = &Shown; e.valid = &Valid;
  e.target_valid = &TargetValid; e.produce_targets = &Produce;
  e.monthly_rate = &MonthlyRate; e.county_rite = &CountyRite;
  return e;
}
int checks = 0;
bool Check(bool value, const char *label) {
  ++checks; if (!value) std::cerr << "FAIL " << label << '\n'; return value;
}
void Wire(const std::filesystem::path &dir, const char *name, const q::Observation &out) {
  std::ofstream(dir / name) << q::SerializeCountyConversion12003(out) << '\n';
}
} // namespace

int main(int argc, char **argv) {
  if (argc != 2) return 100;
  const std::filesystem::path dir{argv[1]};
  Fixture fixture; auto environment = Bind(fixture); q::Observation out{};
  if (!Check(q::ReadCountyConversion12003(environment, 101, out), "RR current task with legal county collection") ||
      !Check(out.available && out.position_present && out.incumbent_character_id == Fixture::incumbent_id,
             "actual owner and incumbent") ||
      !Check(out.current_task_key == "task_religious_relations" && !out.current_target_province_id &&
             !out.current_conversion_monthly_rate_raw, "RR has no actual county or conversion monthly rate") ||
      !Check(!out.current_percentage_progress_raw && out.candidates.size() == 3,
             "current progress separate from candidate rates") ||
      !Check(out.candidate_collection_evaluated && out.candidate_collection_complete &&
             out.native_task_shown == true && out.native_task_valid == true, "complete final native result") ||
      !Check(out.candidates[0].county_title_id == Fixture::title_ids[2] &&
             out.candidates[1].county_title_id == Fixture::title_ids[1] &&
             out.candidates[2].county_title_id == Fixture::title_ids[0], "sort by full TitleID not monthly rate") ||
      !Check(out.candidates[0].native_collection_ordinal == 2 && out.candidates[1].native_collection_ordinal == 1 &&
             out.candidates[2].native_collection_ordinal == 0, "retain native collection order") ||
      !Check(out.candidates[0].county_rite_id == Fixture::rite_ids[2] && out.candidates[1].county_rite_id == 0U &&
             out.candidates[2].county_rite_id == Fixture::rite_ids[0], "full county Rites including legitimate zero") ||
      !Check(out.candidates[0].native_monthly_rate_raw == 350000 && out.candidates[1].native_monthly_rate_raw == 125000 &&
             out.candidates[2].native_monthly_rate_raw == 500000, "distinct native final county monthly rates") ||
      !Check(out.candidates[1].directly_held_by_player && !out.candidates[0].directly_held_by_player,
             "native title holder identity") ||
      !Check(!fixture.bad_arguments && fixture.allocations == 1 && fixture.releases == 1 &&
             fixture.candidate_rate_calls == 3 && fixture.current_rate_calls == 0, "candidate native ABI and allocation release")) return 1;
  Wire(dir, "rr-current-with-candidates.json", out);

  Put(fixture.task, 0x18, fixture.conversion_type.data());
  Put(fixture.task, 0x48, std::uint32_t{8}); Put(fixture.task, 0x50, Fixture::province_ids[1]);
  fixture.task[0x39] = std::byte{1};
  if (!Check(q::ReadCountyConversion12003(environment, 102, out), "real current conversion query") ||
      !Check(out.current_target_province_id == Fixture::province_ids[1] &&
             out.current_target_county_title_id == Fixture::title_ids[1] && out.current_target_county_rite_id == 0U,
             "actual current county target identity and Rite") ||
      !Check(out.current_task_frozen == true && out.current_percentage_progress_raw == 8750000 &&
             out.current_conversion_monthly_rate_raw == 777000, "current percentage and monthly rate distinct") ||
      !Check(fixture.current_rate_calls == 1 && fixture.candidate_rate_calls == 6 && !fixture.bad_arguments,
             "actual current scopes/frozen and prospective scopes/unfrozen")) return 2;
  Wire(dir, "real-current-conversion.json", out);

  Put(fixture.task, 0x18, fixture.rr_type.data()); Put(fixture.task, 0x48, std::uint32_t{0});
  Put(fixture.task, 0x50, std::int32_t{-1}); fixture.task[0x39] = std::byte{0};
  fixture.shown_value = false;
  const int producer_before = fixture.producer_calls;
  if (!Check(q::ReadCountyConversion12003(environment, 103, out) && out.native_task_shown == false &&
             out.candidates.empty() && fixture.producer_calls == producer_before, "native not shown skips collection without unavailable")) return 3;
  fixture.shown_value = true; fixture.empty_targets = true;
  if (!Check(q::ReadCountyConversion12003(environment, 104, out) && out.candidates.empty() &&
             out.candidate_collection_complete && !out.current_target_province_id,
             "legal empty collection and null current target") ||
      !Check(fixture.allocations == fixture.releases && !fixture.bad_arguments, "empty collection releases allocation")) return 4;
  Wire(dir, "legal-empty-and-not-shown.json", out);

  fixture.empty_targets = false; fixture.valid_value = false;
  if (!Check(q::ReadCountyConversion12003(environment, 105, out) && out.available && out.native_task_valid == false &&
             out.candidates.empty(), "native task rejection is available false")) return 5;
  Wire(dir, "native-task-rejected.json", out); fixture.valid_value = true;

  fixture.rejected_ordinal = 1;
  if (!Check(q::ReadCountyConversion12003(environment, 106, out) && out.candidates.size() == 3,
             "candidate rejection retains native collection") ||
      !Check(!out.candidates[1].native_target_valid && !out.candidates[1].native_monthly_rate_raw &&
             out.candidates[1].county_title_id == Fixture::title_ids[1], "false target retains identity and null predicted rate") ||
      !Check(!fixture.bad_arguments && fixture.allocations == fixture.releases, "rejected target no invented monthly rate")) return 6;
  Wire(dir, "native-candidate-rejected.json", out); fixture.rejected_ordinal = -1;

  fixture.rate_failure_ordinal = 1;
  if (!Check(!q::ReadCountyConversion12003(environment, 107, out) && !out.available &&
             out.failure == q::Failure::native_evaluation_unavailable, "actual monthly callback failure") ||
      !Check(out.candidates.empty() && !out.current_conversion_monthly_rate_raw &&
             !out.native_task_shown && !out.native_task_valid, "failure clears result rather than zero rate") ||
      !Check(fixture.allocations == fixture.releases && !fixture.bad_arguments, "allocation released after monthly failure")) return 7;
  Wire(dir, "native-monthly-evaluation-failed.json", out); fixture.rate_failure_ordinal = -1;

  fixture.rite_failure_ordinal = 1;
  if (!Check(!q::ReadCountyConversion12003(environment, 108, out) && !out.available &&
             out.failure == q::Failure::county_rite_unavailable, "actual county Rite read failure") ||
      !Check(out.candidates.empty() && !out.current_conversion_monthly_rate_raw,
             "county read failure discards rates rather than fake zero") ||
      !Check(fixture.allocations == fixture.releases && !fixture.bad_arguments, "allocation released after county failure")) return 8;
  Wire(dir, "county-rite-read-failed.json", out);
  std::cout << "PASS checks=" << checks << " cases=7 actual_reader=true actual_serializer=true live=false\n";
  return 0;
}
