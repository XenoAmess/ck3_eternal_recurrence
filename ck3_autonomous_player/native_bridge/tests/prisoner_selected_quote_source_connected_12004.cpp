#include "xar_bridge/prisoner_selected_quote_query_capture_12004.hpp"
#include "xar_bridge/ck3_12004_prisoner_collection_result.hpp"
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <string_view>

void RunPrisonerCostLane9D7060ReadonlyNewCases12004();
void RunPrisonerMode0ScopeCleanupFocus12004();
void RunPrisonerAnswerHelpersSourceFocus12004();
int RunPrisonerCostVariant3755500Readonly12004Cases();
namespace xar::ck3_12004 {
void RunPrisonerAutoAcceptTriggerConditionFocus12004();
void RunPrisonerTriggerRootScopeGate12004Cases();
int RunPrisonerAnswerControl12004NewCases();
int RunNegotiatedReplyReporterNullPath12004NewCases();
int RunPrisonerMode0Scalar307C34012004NewCases();
void RunPrisonerScopeVectorCopy260E04012004Cases();
void RunPrisonerScopeCloneVector10012004Cases();
void RunPrisonerScopeCloneSupport11812004Cases();
void RunPrisonerRansomScopeClone373ACF012004Cases();
namespace new_cases { bool RunPrisonerAnswerPredicate3148BB012004NewCases(); }
}
namespace {
using namespace xar::ck3_12004;
void Check(bool value, const char *message) { if (!value) throw std::runtime_error(message); }
struct Graph {
  std::array<std::byte, 0x2800> definition{};
  std::array<std::byte, 0x338> context{};
  std::array<std::byte, 0x80> modifier{}, vtable{};
  std::array<std::uintptr_t, 2> rows{};
  std::array<std::int64_t, 10> output{};
  std::array<std::uint8_t, 4> lookup{0, 1, 2, 3};
  std::uint8_t global_flag = 0;
  std::uint32_t calls = 0;
  std::uint32_t cost_calls = 0;
  bool deny_output = false, wrong_return = false;
  void *seen_context = nullptr;
  std::int64_t *seen_output = nullptr;
  template<class T, std::size_t N> static void Put(std::array<std::byte, N> &data, std::size_t offset, T value) {
    std::memcpy(data.data() + offset, &value, sizeof(value));
  }
  Graph() {
    Put(context, 0, reinterpret_cast<std::uintptr_t>(definition.data()));
    Put(context, 8, std::uint16_t{4});
    Put(context, 0x2D8, std::uint32_t{0x41000001});
    Put(context, 0x2DC, std::uint32_t{0x41000003});
    Put(context, 0x2E4, std::uint32_t{0x41000002});
    Put(context, 0x2E8, UINT32_MAX);
    Put(definition, 0x1918 + 0x28, std::int64_t{-123456});
    Put(definition, 0x1918 + 0x30, std::uintptr_t{0});
    Put(definition, 0x1918 + 0x3C, std::int32_t{0});
    Put(definition, 0x2290, std::uintptr_t{0});
    Put(definition, 0x2718, std::uint8_t{1});
    Put(modifier, 0, reinterpret_cast<std::uintptr_t>(vtable.data()));
    Put(vtable, 0x30, std::uintptr_t{0x72000000});
    rows.fill(reinterpret_cast<std::uintptr_t>(modifier.data()));
  }
  PrisonerQuoteSourceFrame12004 Seed() const {
    PrisonerQuoteSourceFrame12004 f{}; f.executable_sha256 = kPrisonerQuoteSourceExecutableSha25612004;
    f.module_base = 0x10000000; f.native_revision = 17; f.query_sequence = 23; f.proof_epoch = 29;
    f.date_raw = std::int32_t{0}; f.jailer_full_id = std::uint32_t{0x41000001}; f.prisoner_full_id = std::uint32_t{0x41000002};
    f.same_frame_confirmed = true; return f;
  }
  static bool Read(void *opaque, const void *address, void *out, std::size_t size) noexcept {
    auto &g = *static_cast<Graph *>(opaque); const auto a = reinterpret_cast<std::uintptr_t>(address);
    const auto copy = [&](const void *begin, std::size_t length) {
      const auto b = reinterpret_cast<std::uintptr_t>(begin);
      if (a < b || a-b > length || size > length-(a-b)) return false;
      std::memcpy(out, reinterpret_cast<const void *>(a), size); return true;
    };
    if (a == 0x10000000 + 0x5D1DADC && size == 1) { std::memcpy(out, &g.global_flag, 1); return true; }
    if (a >= 0x10000000 + 0x48B57EC && a < 0x10000000 + 0x48B57F0 && size == 1) {
      std::memcpy(out, &g.lookup[a-(0x10000000 + 0x48B57EC)], 1); return true;
    }
    if (copy(g.definition.data(), g.definition.size()) || copy(g.context.data(), g.context.size()) ||
        copy(g.modifier.data(), g.modifier.size()) || copy(g.vtable.data(), g.vtable.size()) ||
        copy(g.rows.data(), sizeof(g.rows))) return true;
    return !g.deny_output && copy(g.output.data(), sizeof(g.output));
  }
};
Graph *original_graph = nullptr;
std::string cost_wire;
std::int64_t *OriginalScore(void *context, std::int64_t *output) {
  auto &g = *original_graph; ++g.calls; g.seen_context = context; g.seen_output = output;
  *output = -123456; return g.wrong_return ? output + 1 : output;
}
void OriginalCosts(const void *block, const void *scope, std::int64_t *output) {
  auto &g = *original_graph; ++g.cost_calls;
  Check(block == g.definition.data()+0x40 && scope == g.context.data()+8 && output == g.output.data(), "cost original arguments");
  constexpr std::array<std::int64_t,10> expected{-100000,0,100000,0,200000,-200000,0,100000,-100000,0};
  std::memcpy(output, expected.data(), sizeof(expected));
}
std::string RunRemainingWire() {
  Graph g{}; original_graph = &g;
  const PrisonerQuoteReadOnlyAccess12004 access{&g, &Graph::Read, 4096};
  auto seed = g.Seed(); seed.date_raw = std::int32_t{1};
  auto sample = CopyPrisonerQuoteSourceSample12004(access, seed, reinterpret_cast<std::uintptr_t>(g.context.data()), true);
  (void)ObservePrisonerExistingScoreQuery12004(access, sample, &OriginalScore, g.context.data(), g.output.data());
  sample.native_answer_raw_u8 = std::uint8_t{0};
  FinishPrisonerQuoteSourceSample12004(sample, true);
  const auto accepted_sample = sample;
  PrisonerSelectedQuoteSource12004 source{}; source.quote_kind = "ordinary_ransom";
  source.samples.push_back(accepted_sample); source.selected_query_completed = true; source.unavailable_reason.clear();
  xar::bridge::PlayerPrisonerCollectionSnapshotV1 collection{};
  collection.available = true; collection.failure = xar::bridge::PlayerPrisonerCollectionFailureV1::none;
  collection.collection_complete = true; collection.total_count = collection.returned_count = 1;
  collection.frame.public_revision = collection.frame.native_revision = 17;
  collection.frame.proof_epoch = 29; collection.frame.date_raw = 1;
  collection.frame.paused = collection.frame.map_ready = collection.frame.played_character_alive = true;
  collection.frame.played_character_identity_round_trip = true; collection.frame.played_character_id = 0x41000001;
  collection.rows[0].source_ordinal = 0; collection.rows[0].full_character_id = 0x41000002;
  collection.rows[0].jailer_character_id = 0x41000001; collection.rows[0].primary_title_tier_raw = 1;
  std::array<PlayerPrisonerRansomQuoteV1, xar::bridge::kPlayerPrisonerMaximumRowsV1> quotes{};
  auto &quote = quotes[0]; quote.available = true; quote.failure = PlayerPrisonerRansomQuoteFailureV1::none;
  quote.jailer_character_id = 0x41000001; quote.prisoner_character_id = 0x41000002; quote.payer_character_id = 0x41000003;
  quote.selected_option = "gold"; quote.quoted_gold_raw = 200000; quote.recipient_acceptance_raw = -123456;
  quote.recipient_answer_status_raw = 0; quote.would_accept_now = true;
  auto wire = SerializePrisonerCollectionCommandResult12004("fresh-selected-source", "query-player-prisoner-collection-private-v1",
      23, 29, 17, collection, quotes, true, nullptr, nullptr);
  Check(!wire.empty(), "existing whole collection positive-date serializer");
  Check(AppendPrisonerSelectedQuoteSource12004(wire, source), "real whole collection command result source attachment");
  Graph::Put(g.context, 0x2DC, std::uint32_t{0x41000002});
  constexpr std::array<std::int64_t,10> raw{-50000,-49999,50000,49999,150000,-150000,0,100000,-100000,1};
  g.output.fill(0);
  Graph::Put(g.definition, 0x40 + 0x9C0, std::uint8_t{1});
  Graph::Put(g.definition, 0x40 + 0x9C1, std::uint8_t{0});
  for (std::size_t i = 0; i < raw.size(); ++i) {
    Graph::Put(g.definition, 0x40 + 0x40 + i*0xF0 + 0xC0, std::int32_t{0});
    Graph::Put(g.definition, 0x40 + 0x40 + i*0xF0 + 0x98, raw[i]);
  }
  auto cost_sample = CopyPrisonerQuoteSourceSample12004(access, seed, reinterpret_cast<std::uintptr_t>(g.context.data()), false);
  ObservePrisonerExistingCostQuery12004(access, cost_sample, &OriginalCosts,
      g.definition.data()+0x40, g.context.data()+8, g.output.data());
  FinishPrisonerQuoteSourceSample12004(cost_sample, true);
  Check(g.cost_calls == 1 && cost_sample.actor_on_send_costs->projected_q64 == cost_sample.actor_on_send_costs->native_final_q64 &&
      cost_sample.actor_on_send_costs->numeric_source_ready, "new cost parent actual originalonce/known static lanes/round");
  PrisonerSelectedQuoteSource12004 cost_source{}; cost_source.quote_kind = "negotiated_preview";
  cost_source.selected_query_completed = true; cost_source.unavailable_reason.clear(); cost_source.samples.push_back(cost_sample);
  cost_wire = SerializePrisonerSelectedQuoteSource12004(cost_source);
  return wire;
}
}
int main(int argc, char **argv) {
  if (argc != 2 || std::string_view(argv[1]) != "--prisoner-selected-quote-source-wire-repair-12004") return 64;
  try {
    const auto wire = RunRemainingWire();
    std::cout << "SOURCE_WIRE_BEGIN\n" << wire << "\nSOURCE_WIRE_END\n";
    std::cout << "SOURCE_COST_BEGIN\n" << cost_wire << "\nSOURCE_COST_END\n";
    return 0;
  } catch (const std::exception &error) { std::cerr << error.what() << '\n'; return 1; }
}
