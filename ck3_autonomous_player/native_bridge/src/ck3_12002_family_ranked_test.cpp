#include "xar_bridge/ck3_12002_family_ranked.hpp"
#include "xar_bridge/ck3_12002_family_ranked_abi.hpp"
#include "xar_bridge/ck3_12002_query_mailbox.hpp"

#include <algorithm>
#include <array>
#include <cstring>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <vector>

namespace {
using namespace xar::ck3_12002;
namespace bridge = xar::bridge;
constexpr std::int32_t player_id = 0x03000001, candidate_a = 0x03000002,
    candidate_b = 0x03000003, candidate_c = 0x03000004, recipient_id = 0x0300003F;
constexpr std::uintptr_t candidate_owner = 0x12002001, scored_owner = 0x12002002,
    row_vtable = 0x12002003, candidate_allocator = 0x12002004, scored_allocator = 0x12002005;
template <typename T> void Put(void *base, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(base) + offset, &value, sizeof(T));
}
template <typename T> T Load(const void *base, std::size_t offset) {
  T value{}; std::memcpy(&value, static_cast<const std::byte *>(base) + offset, sizeof(T)); return value;
}
void Check(bool condition, const char *message) { if (!condition) throw std::runtime_error(message); }
struct Header { void *data; std::int32_t capacity, count; void *owner; };
struct Row { std::uintptr_t vtable; std::uint32_t id; std::int32_t score; };
static_assert(sizeof(Header) == 0x18 && sizeof(Row) == 0x10);
void *local_player = nullptr, *definition = nullptr, *subject_pointer = nullptr,
    *strategy_pointer = nullptr, *living_pointer = nullptr;
bool main_thread = true, legal = true, grand = false, wrong_actor = false,
    drift_scores = false, corrupt_row = false, duplicate_row = false, empty_rows = false;
std::int64_t acceptance = 1'600'000;
std::uint8_t answer_status = 0;
std::int32_t tier = 2, pool_size = 3, row_size = 3;
int enumerations = 0, scorings = 0, sorts = 0, row_destroys = 0,
    context_destroys = 0, scored_initializations = 0, heap_scored_releases = 0,
    heap_candidate_releases = 0, frame_reads = 0;
bool date_drift = false;
std::int32_t seen_native_cap = 0;
void *original_scored_heap = nullptr, *original_candidate_heap = nullptr;
bridge::MarriageMatchmakingFrameV1 published_frame{};
void *LocalPlayer(void *) { return local_player; }
bool IsMain(void *) noexcept { return main_thread; }
bool Frame(void *, bridge::MarriageMatchmakingFrameV1 &out) noexcept {
  ++frame_reads; out = published_frame;
  if (date_drift && frame_reads == 2) ++out.date_raw;
  return true;
}
std::int32_t Tier(void *subject) { Check(subject == subject_pointer, "native tier subject"); return tier; }
void Release(void *owner, void *data, std::size_t alignment) {
  Check(alignment == 8, "native release alignment");
  if (data == nullptr || data == static_cast<std::byte *>(owner) + 8) return;
  const auto table = Load<std::uintptr_t>(owner, 0);
  if (table == scored_owner) {
    Check(data == original_scored_heap, "scored cleanup retains original heap pointer");
    delete[] static_cast<Row *>(data); original_scored_heap = nullptr; ++heap_scored_releases;
  } else {
    Check(table == candidate_owner && data == original_candidate_heap, "candidate cleanup retains original heap pointer");
    delete[] static_cast<void **>(data); original_candidate_heap = nullptr; ++heap_candidate_releases;
  }
}
void InitializeCandidates(void *owner, void **data, std::int32_t *capacity) {
  Check(Load<std::uintptr_t>(owner, 0) == candidate_owner &&
      Load<std::uintptr_t>(owner, 0x408) == candidate_allocator, "actual candidate owner layout");
  *data = static_cast<std::byte *>(owner) + 8; *capacity = 0x80;
}
void *InitializeScored(void *value) {
  ++scored_initializations;
  auto &header = *static_cast<Header *>(value);
  Check(header.data == nullptr && header.count == 0 && header.capacity == 0,
      "constructor must not be used to discard populated scored buffer");
  header.owner = static_cast<std::byte *>(value) + 0x18;
  Put(header.owner, 0, scored_owner); Put(header.owner, 0x208, scored_allocator);
  header.data = static_cast<std::byte *>(header.owner) + 8; header.capacity = 0x20;
  return value;
}
void *DestroyRow(void *row, std::uint32_t flags) {
  Check(flags == 0 && Load<std::uintptr_t>(row, 0) == row_vtable,
      "native nondeleting scored row destructor");
  ++row_destroys; return row;
}
void Enumerate(void *strategy, std::int32_t selector, bool mode, std::int32_t cap, void *value) {
  Check(strategy == strategy_pointer && selector == 0 && mode, "exact native candidate producer arguments");
  ++enumerations; seen_native_cap = cap;
  auto &header = *static_cast<Header *>(value);
  Check(header.count == 0 && header.capacity == 0x80, "initialized native candidate header");
  if (pool_size > header.capacity) {
    header.data = new void *[static_cast<std::size_t>(pool_size)]{};
    original_candidate_heap = header.data; header.capacity = pool_size;
  }
  header.count = pool_size;
}
void Score(void *strategy, const void *parameters, void *pool, void *value) {
  Check(strategy == strategy_pointer && Load<void *>(parameters, 0) == definition &&
      Load<void *>(parameters, 8) == subject_pointer && Load<void *>(parameters, 0x10) == subject_pointer &&
      Load<bool>(parameters, 0x18) && Load<std::int32_t>(parameters, 0x1C) == 1 &&
      static_cast<Header *>(pool)->count == pool_size, "native scorer parameter structure");
  ++scorings;
  auto &header = *static_cast<Header *>(value);
  const auto count = empty_rows ? 0 : row_size;
  if (count > header.capacity) {
    header.data = new Row[static_cast<std::size_t>(count)]{};
    original_scored_heap = header.data; header.capacity = count;
  }
  auto *rows = static_cast<Row *>(header.data); header.count = count;
  for (std::int32_t index = 0; index < count; ++index) {
    const auto score = index == 0 || index == 2 ? 200 : 100 - index;
    rows[index] = {row_vtable, static_cast<std::uint32_t>(0x03000002 + index), score};
  }
  if (count != 0 && drift_scores && scorings % 2 == 0) ++rows[0].score;
  if (count != 0 && corrupt_row) rows[0].vtable = 0;
  if (count > 1 && duplicate_row) rows[1].id = rows[0].id;
}
void Sort(void *value, void *functor) {
  Check(functor != nullptr && Load<std::uint8_t>(functor, 0) == 0,
      "native stateless comparator argument");
  ++sorts;
  auto &header = *static_cast<Header *>(value);
  auto *rows = static_cast<Row *>(header.data);
  // Fixture callback mirrors the frozen native comparator solely to verify
  // that production invokes the sorting entry after score and before rank.
  std::sort(rows, rows + header.count, [](const Row &a, const Row &b) {
    return a.score > b.score || (a.score == b.score && a.id > b.id);
  });
}
void Redirect(void *def, std::int32_t *actor, std::int32_t *recipient,
    std::int32_t *subject, std::int32_t *candidate, std::int32_t *intermediary, std::int32_t *added) {
  Check(def == definition && *actor == player_id && *subject == player_id &&
      *recipient == *candidate && *intermediary == -1 && *added == -1,
      "new six-role direct player marriage redirect");
  *recipient = recipient_id; if (wrong_actor) *actor = recipient_id;
}
void *Construct(void *context, void *def, std::int32_t actor, std::int32_t recipient,
    std::int32_t subject, std::int32_t candidate, std::int32_t intermediary, void *extra) {
  Check(extra == nullptr, "ordinary all-role context");
  Put(context, 0, def); Put(context, 0x2D8, actor); Put(context, 0x2DC, recipient);
  Put(context, 0x2E0, subject); Put(context, 0x2E4, candidate); Put(context, 0x2E8, intermediary);
  return context;
}
void Refresh(void *, bool full) { Check(full, "full native context refresh"); }
void Finalize(void *) {}
bool Validate(void *, void *error) { Check(error == nullptr, "full CanSend"); return legal; }
std::int64_t *Acceptance(void *, std::int64_t *out) { *out = acceptance; return out; }
std::uint8_t Answer(void *, std::uint8_t mode, std::uint8_t final, void *a, void *b) {
  Check(mode == 1 && final == 1 && a == nullptr && b == nullptr, "actual final native answer"); return answer_status;
}
void Cost(const void *, const void *, std::int64_t *out) { std::fill_n(out, 10, std::int64_t{0}); }
bool Option(const void *, std::uint32_t id) { return id == 1 && grand; }
void DestroyContext(void *) { ++context_destroys; }
struct Fixture {
  std::array<std::byte, 0xA8> state{}; std::array<std::byte, 0x28> jomini{};
  std::array<std::byte, 0x1F8> players{}; std::array<std::byte, 0x78> local{};
  std::vector<std::byte> game = std::vector<std::byte>(0x36780);
  std::array<std::byte, 0xE0> entry{}; std::array<void *, 1> entries{entry.data()};
  std::array<std::byte, 0x30> store{}; std::array<std::byte, 64 * 0x10> slots{};
  std::array<std::array<std::byte, 0x1D8>, 42> characters{};
  std::array<std::byte, 0x1D8> recipient{};
  std::array<std::byte, 0x318> living{}; std::array<std::byte, 0x28> strategy{};
  std::array<std::byte, 4> age{};
  std::array<std::byte, 0x1000> database{}; std::array<std::byte, 0x80> interaction{};
  std::array<std::int32_t, 5> cap_table{8, 16, 130, 256, 512};
  const std::int32_t *cap_ptr = cap_table.data();
  void *state_ptr = state.data(), *jomini_ptr = jomini.data(), *store_ptr = store.data(),
      *database_ptr = database.data();
  std::int32_t threshold_zero = 16, threshold_one = 18;
  std::uint32_t grand_option = 1, matri_option = 2;
  FamilyRankedBindings bindings{}; FamilyRankedAccessV1 access{nullptr, &Frame, &IsMain};
  bridge::MarriageMatchmakingObserverRequestV1 request{"native:7", 7, 7, 53220000,
      player_id, player_id, 8, 0};
  Fixture() {
    main_thread = legal = true; grand = wrong_actor = drift_scores = corrupt_row =
        duplicate_row = empty_rows = date_drift = false;
    acceptance = 1'600'000; answer_status = 0; tier = 2; pool_size = row_size = 3;
    enumerations = scorings = sorts = row_destroys = context_destroys =
        scored_initializations = heap_scored_releases = heap_candidate_releases = frame_reads = 0;
    original_scored_heap = original_candidate_heap = nullptr;
    Put(state.data(), 8, std::int32_t{53220000}); Put(state.data(), 0x70, std::int32_t{2});
    Put(state.data(), 0xA0, game.data()); Put(jomini.data(), 0x18, players.data()); jomini[0x20] = std::byte{1};
    Put(players.data(), 0x1F0, std::int32_t{7}); Put(local.data(), 0x70, std::int32_t{7}); local_player = local.data();
    Put(game.data(), 0x222E8 + 0x58, entries.data()); Put(game.data(), 0x222E8 + 0x64, std::int32_t{1});
    Put(entry.data(), 0xD8, std::int32_t{7}); Put(entry.data(), 0xB0, player_id);
    Put(store.data(), 0x20, slots.data()); Put(store.data(), 0x2C, std::int32_t{64});
    for (std::size_t index = 0; index < characters.size(); ++index) {
      const auto id = static_cast<std::int32_t>(0x03000001 + index);
      Put(characters[index].data(), 0x18, id); Put(characters[index].data(), 0x68, std::int16_t{21});
      Put(slots.data(), (index + 1) * 0x10 + 8, characters[index].data());
    }
    Put(characters[1].data(), 0x68, std::int16_t{14});
    Put(characters[1].data(), 0x1A1, std::uint8_t{1});
    Put(recipient.data(), 0x18, recipient_id); Put(slots.data(), 63 * 0x10 + 8, recipient.data());
    subject_pointer = characters[0].data(); living_pointer = living.data(); strategy_pointer = strategy.data();
    Put(subject_pointer, kFamilyRankedCharacterLivingOffset, living.data());
    Put(living.data(), kFamilyRankedLivingStrategyOffset, strategy.data());
    Put(living.data(), kFamilyRankedLivingAgeDataOffset, age.data()); Put(age.data(), 2, std::int8_t{21});
    Put(strategy.data(), kFamilyRankedStrategySourceCharacterOffset, subject_pointer);
    Put(strategy.data(), kFamilyRankedStrategyReadyOwnerOffset, living.data());
    Put(database.data(), 0xF30, interaction.data()); definition = interaction.data();
    published_frame = {}; std::memcpy(published_frame.snapshot_id.data(), "native:7", 8);
    published_frame.public_revision = published_frame.native_revision = 7; published_frame.proof_epoch = 9;
    published_frame.date_raw = 53220000; published_frame.paused = published_frame.map_ready =
        published_frame.has_played_character = published_frame.played_character_alive =
        published_frame.played_character_identity_round_trip = true; published_frame.played_character_id = player_id;
    bindings.enabled = bindings.family.enabled = bindings.family.context.enabled = true;
    auto &c = bindings.family.context;
    c.core = {true, &state_ptr, &jomini_ptr, &store_ptr, &LocalPlayer}; c.interaction_database_slot = &database_ptr;
    c.redirect_roles = &Redirect; c.construct_all_roles = &Construct; c.refresh = &Refresh; c.finalize = &Finalize;
    c.validate = &Validate; c.destroy = &DestroyContext; c.recipient_answer_score = &Acceptance; c.evaluate_cost = &Cost;
    bindings.family.evaluate_answer = &Answer; bindings.family.read_boolean_option = &Option;
    bindings.family.adult_threshold_zero = &threshold_zero; bindings.family.adult_threshold_one = &threshold_one;
    bindings.family.grand_wedding_option = &grand_option; bindings.family.matrilineal_option = &matri_option;
    bindings.read_native_tier = &Tier; bindings.native_cap_table_slot = &cap_ptr;
    bindings.enumerate_candidates = &Enumerate; bindings.score_candidates = &Score; bindings.sort_scored_candidates = &Sort;
    bindings.destroy_scored_row = &DestroyRow; bindings.initialize_scored_container = &InitializeScored;
    bindings.release_native_buffer = &Release; bindings.initialize_candidate_buffer = &InitializeCandidates;
    bindings.candidate_owner_vtable = candidate_owner; bindings.scored_owner_vtable = scored_owner;
    bindings.scored_row_vtable = row_vtable; bindings.candidate_backing_allocator = candidate_allocator;
    bindings.scored_backing_allocator = scored_allocator;
  }
  bool Read(bridge::MarriageMatchmakingObservationV1 &out, FamilyRankedDiagnosticsV1 *diag = nullptr) {
    frame_reads = 0; return ReadMarriageMatchmakingObservationV1(bindings, access, request, out, diag);
  }
};
} // namespace

int main() {
  try {
    const auto admitted = BindFamilyRankedImage(0x140000000, kExecutableSha256);
    Check(admitted.enabled && reinterpret_cast<std::uintptr_t>(admitted.sort_scored_candidates) ==
        0x140000000 + kFamilyRankedSortScoredRva, "new ranked exact native binding");
    Check(!BindFamilyRankedImage(0x140000000, "1.19.0.6").enabled, "old ranked native binder never reused");
    Fixture f; bridge::MarriageMatchmakingObservationV1 out{}; FamilyRankedDiagnosticsV1 diag{};
    Check(f.Read(out, &diag) && out.candidate_count == 3 && out.candidates[0].candidate_character_id == candidate_c &&
        out.candidates[1].candidate_character_id == candidate_a && out.candidates[2].candidate_character_id == candidate_b &&
        out.candidates[0].rank == 1 && out.candidates[1].rank == 2 && out.candidates[0].native_candidate_score == 200 &&
        enumerations == 2 && sorts == 2 && scored_initializations == 2 && row_destroys == 6 && context_destroys == 6 &&
        seen_native_cap == 130 && diag.native_scored_count == 3 && out.readiness.native_score_ready,
        "native producer, explicit native sort, unsigned full-ID tie, runtime cap and same-frame sample");
    const auto serialized = RenderQueryBuildIdentity(bridge::SerializeMarriageMatchmakingObservationV1(out));
    Check(serialized.find("1.20.0.2") != std::string::npos &&
        serialized.find("1.19.0.6") == std::string::npos,
        "central pure serializer renders the admitted new build identity");
    std::cout << "XAR_FAMILY_RANKED_WIRE " << serialized << '\n';
    Check(out.candidates[1].evaluation.predicted_outcome == bridge::MarriagePredictedOutcomeV1::betrothal &&
        out.candidates[0].evaluation.predicted_outcome == bridge::MarriagePredictedOutcomeV1::marriage &&
        out.candidates[0].evaluation.roles.recipient_character_id == recipient_id &&
        out.candidates[0].evaluation.roles.intermediary_character_id == 0xFFFFFFFFU,
        "actual redirected recipient, native runtime adult result and role sentinel");
    f.request.candidate_character_id = candidate_a;
    Check(f.Read(out) && out.candidate_count == 1 && out.candidates[0].rank == 2,
        "candidate filter preserves original native rank");
    f.request.limit = 1;
    Check(f.Read(out) && out.candidate_count == 0 && out.readiness.ranked_candidates_ready,
        "filter is bounded to requested native prefix");
    f.request.candidate_character_id = 0; f.request.limit = 8;
    legal = false; answer_status = 2; acceptance = -300'000;
    Check(f.Read(out) && !out.candidates[0].evaluation.complete_can_send &&
        !out.candidates[0].evaluation.recipient_answer_allows_send && out.candidates[0].evaluation.recipient_ai_accept_raw == -300'000,
        "negative native legality and acceptance are observations, not dropped rows");
    legal = true; answer_status = 0; acceptance = 1'600'000;
    Put(f.living.data(), kFamilyRankedLivingStrategyOffset, static_cast<void *>(nullptr));
    const auto old_calls = enumerations;
    Check(!f.Read(out, &diag) && out.unavailable_reason == bridge::MarriageMatchmakingObserverFailureV1::ranked_source_unavailable &&
        diag.source_failure == bridge::MarriageMatchmakingSourceAdapterFailureV1::strategy_unavailable && enumerations == old_calls &&
        out.candidate_count == 0 && !out.readiness.ranked_candidates_ready,
        "player native Strategy absence remains unavailable, never an empty ranked success");
    Put(f.living.data(), kFamilyRankedLivingStrategyOffset, f.strategy.data());
    Put(f.strategy.data(), kFamilyRankedStrategySourceCharacterOffset, f.characters[1].data());
    Check(!f.Read(out, &diag) && diag.source_failure == bridge::MarriageMatchmakingSourceAdapterFailureV1::strategy_identity_mismatch,
        "another character Strategy cannot score the played subject");
    Put(f.strategy.data(), kFamilyRankedStrategySourceCharacterOffset, subject_pointer);
    empty_rows = true;
    Check(f.Read(out) && out.candidate_count == 0 && out.readiness.same_frame_ready,
        "actual available native zero-row source is distinct");
    empty_rows = false; pool_size = 130; row_size = 40;
    const auto prior_destroy = row_destroys;
    Check(f.Read(out) && out.candidate_count == 8 && heap_scored_releases == 2 && heap_candidate_releases == 2 &&
        row_destroys == prior_destroy + 80 && original_scored_heap == nullptr && original_candidate_heap == nullptr,
        "spilled native buffers retain original pointer, destroy all rows, release both owners");
    pool_size = row_size = 3; acceptance = (std::numeric_limits<std::int64_t>::max)();
    Check(!f.Read(out, &diag) && diag.source_failure == bridge::MarriageMatchmakingSourceAdapterFailureV1::acceptance_score_overflow,
        "signed native acceptance cannot silently truncate to wire int32");
    acceptance = 1'600'000; wrong_actor = true;
    Check(!f.Read(out), "native redirect cannot replace current played actor"); wrong_actor = false;
    drift_scores = true;
    Check(!f.Read(out) && out.unavailable_reason == bridge::MarriageMatchmakingObserverFailureV1::native_sample_drift,
        "native two-sample score drift remains unavailable"); drift_scores = false;
    date_drift = true;
    Check(!f.Read(out) && out.unavailable_reason == bridge::MarriageMatchmakingObserverFailureV1::date_drift,
        "published frame drift cannot complete read"); date_drift = false;
    main_thread = false;
    Check(!f.Read(out) && out.unavailable_reason == bridge::MarriageMatchmakingObserverFailureV1::application_main_thread_required,
        "owning application thread required"); main_thread = true;
    f.request.subject_character_id = f.request.matchmaker_character_id = candidate_a;
    Check(!f.Read(out) && out.unavailable_reason == bridge::MarriageMatchmakingObserverFailureV1::player_unavailable,
        "ranked subject is actual played character, not an inherited subject");
    std::cout << "PASS CK3 1.20 ranked marriage: native sort/cap, actual Strategy absence, native roles/outcome, limit/filter, spilled lifecycle, same frame\n";
    return 0;
  } catch (const std::exception &error) { std::cerr << "FAIL " << error.what() << '\n'; return 1; }
}
