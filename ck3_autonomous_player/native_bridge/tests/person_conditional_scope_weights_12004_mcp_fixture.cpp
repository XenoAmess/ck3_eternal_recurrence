// AUTHORED_NOTRUN. Five NEW offline callback whole-command fixtures.
// Native45 source producers are included only for owned Memory/factory setup;
// their main functions live in Prior45SourceNotExecuted and are never called.
// Fake constructor/getter/destructors model the closed ABI; no actual game
// allocator, row getter, numeric expression or live scope execution is claimed.
#include "xar_bridge/battle_terminal_transition_v1_mailbox.hpp"
#include "xar_bridge/ck3_12004_battle.hpp"
#include "xar_bridge/ck3_12004_person_following_2921a90.hpp"
#include "xar_bridge/ck3_12004_person_conditional_scope_weights.hpp"
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <memory>
#include <string>
#include <string_view>
#include <system_error>
#include <utility>
#include <vector>

// The prior producer renames its own included main and then undefines main.
// A surrounding main macro therefore cannot rename the prior outer main.
// All headers are already included globally; namespace isolation gives that
// prior outer main a distinct symbol without touching qualified Native45 code.
namespace Prior45SourceNotExecuted {
#include "person_conditional_opinion_12004_mcp_fixture.cpp"
}

namespace {
namespace native4 = xar::ck3_12004;
using Prior45SourceNotExecuted::Address;
using Prior45SourceNotExecuted::At;
using Prior45SourceNotExecuted::Fixture;
using Prior45SourceNotExecuted::Memory;
using Prior45SourceNotExecuted::OpinionFixture;
using Prior45SourceNotExecuted::Require;

enum class ScopeCase { dynamic_ready, dynamic_zero, literal_only, family_empty,
                       prior_row_unavailable };
struct ScopeSpec { const char *filename; ScopeCase kind; };
constexpr ScopeSpec kScopeCases[] = {
    {"scope-dynamic-ready.json", ScopeCase::dynamic_ready},
    {"scope-dynamic-zero.json", ScopeCase::dynamic_zero},
    {"scope-literal-only.json", ScopeCase::literal_only},
    {"scope-family-empty.json", ScopeCase::family_empty},
    {"scope-prior-row-unavailable.json", ScopeCase::prior_row_unavailable},
};

template <typename T> T ScopeLoad(const void *base, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(base) + offset, sizeof(value));
  return value;
}
template <typename T> void ScopePut(void *base, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(base) + offset, &value, sizeof(value));
}

struct ScopeFixture;
ScopeFixture *scope_current = nullptr;
void ScopeElementDestroy(void *, std::uint32_t);
void ScopeAllocatorFree(void *, void *, std::uint32_t);
void *ScopeConstruct(void *);
std::int64_t *ScopeReadWeight(const void *, std::int64_t *, const void *);

struct ScopeAllocation {
  std::uintptr_t *vtable = nullptr; // Actual fake allocator receiver ABI.
  ScopeFixture *owner = nullptr;
  std::unique_ptr<std::byte[]> data;
  void *scope = nullptr;
  std::size_t vector_offset = 0;
  std::size_t sample = 0;
  bool element_destroyed = false;
  bool released = false;
};
struct ScopeCleanupEvent {
  std::size_t sample;
  std::size_t vector_offset;
  bool element;
};

struct ScopeFixture {
  static constexpr std::uint32_t kRawPayload = 0xF2345678U;
  OpinionFixture prior;
  ScopeCase kind;
  std::vector<void *> expected_rows;
  std::array<std::uintptr_t, 3> allocator_vtable{
      0U, 0U, reinterpret_cast<std::uintptr_t>(&ScopeAllocatorFree)};
  std::array<std::uintptr_t, 1> element_vtable{
      reinterpret_cast<std::uintptr_t>(&ScopeElementDestroy)};
  std::array<std::byte, 16> fake_inline_support{};
  std::vector<std::unique_ptr<ScopeAllocation>> allocations;
  std::vector<ScopeCleanupEvent> cleanup;
  std::size_t constructor_calls = 0;
  std::size_t getter_calls = 0;
  std::size_t getter_in_sample = 0;
  void *active_scope = nullptr;

  explicit ScopeFixture(ScopeCase selected) : kind(selected) {
    auto &f = prior.f;
    auto &binding = f.bindings.current_person_conditional_scope_weights;
    Require(binding.enabled && binding.module_base == Fixture::kModule &&
        reinterpret_cast<std::uintptr_t>(binding.construct_vector) ==
            Fixture::kModule + native4::kPersonConditionalScopeConstructorRva12004 &&
        reinterpret_cast<std::uintptr_t>(binding.read_weight) ==
            Fixture::kModule + native4::kPersonConditionalScopeRowWeightRva12004,
        "actual4 production scope binder must install8895D0/2872300 before callbacks");
    binding.construct_vector = &ScopeConstruct;
    binding.read_weight = &ScopeReadWeight;
    f.bindings.current_person_conditional_opinion.opinion.read_opinion =
        &Prior45SourceNotExecuted::PairTotal;
    f.memory.Put(f.mapped_object, 0x20, kRawPayload);
    Require(kRawPayload != static_cast<std::uint32_t>(Fixture::kPlayer) &&
        kRawPayload != Fixture::kEnemyUnsigned, "scope payload must not substitute a Character ID");
    if (kind == ScopeCase::family_empty) {
      f.memory.Put(f.definition, 0xB8C, std::int32_t{0});
      f.memory.Put(f.definition, 0xBBC, std::int32_t{0});
      prior.NoSelectedLists();
      return;
    }
    if (kind == ScopeCase::literal_only) {
      f.memory.Put(f.definition, 0xBBC, std::int32_t{3});
      f.memory.Put(prior.selected_list, 0, prior.literal);
      f.memory.Put(prior.selected_list, 8, prior.empty);
      f.memory.Put(prior.selected_list, 16, prior.literal);
      expected_rows = {prior.literal, prior.empty, prior.literal};
      return;
    }
    // Original45 sees these exact dynamic rows as partial; only the NEW sibling
    // receives the observed numerical output from its typed callback seam.
    f.memory.denied.erase(std::remove_if(f.memory.denied.begin(), f.memory.denied.end(),
        [&](const Memory::Interval &interval) {
          return interval.address == Address(prior.literal) + 0x278;
        }), f.memory.denied.end());
    f.memory.Put(prior.literal, 0x280, std::int32_t{1});
    f.memory.Put(prior.literal, 0x278, std::uintptr_t{0x12345678U});
    expected_rows = {prior.literal, prior.raw, prior.literal, prior.zero, prior.empty};
    if (kind == ScopeCase::dynamic_zero)
      f.memory.NoRead(prior.literal, 0, 0x78); // Actual observed zero skips PC reads.
    if (kind == ScopeCase::prior_row_unavailable) {
      f.memory.Put(prior.selected_list, 0, static_cast<void *>(nullptr));
      f.memory.Put(prior.selected_list, 8, prior.literal);
      f.memory.Put(prior.selected_list, 16, prior.raw);
      expected_rows = {nullptr, prior.literal, prior.raw, prior.zero, prior.empty};
    }
  }

  ScopeAllocation &Vector(void *scope, std::size_t offset,
                          std::size_t stride, bool inline_element) {
    auto allocation = std::make_unique<ScopeAllocation>();
    allocation->vtable = allocator_vtable.data();
    allocation->owner = this;
    allocation->data = std::make_unique<std::byte[]>(stride);
    allocation->scope = scope;
    allocation->vector_offset = offset;
    allocation->sample = constructor_calls;
    auto *const raw = allocation.get();
    ScopePut(scope, offset, static_cast<void *>(raw->data.get()));
    ScopePut(scope, offset + 8,
        inline_element ? std::int32_t{1} : std::int32_t{8});
    ScopePut(scope, offset + 0xC, inline_element ? std::int32_t{1} : std::int32_t{0});
    ScopePut(scope, offset + 0x10, static_cast<void *>(raw));
    if (inline_element)
      ScopePut(raw->data.get(), 0, element_vtable.data());
    allocations.push_back(std::move(allocation));
    return *raw;
  }

  void CheckCleanup() const {
    const bool dynamic = kind == ScopeCase::dynamic_ready || kind == ScopeCase::dynamic_zero;
    const bool prior_missing = kind == ScopeCase::prior_row_unavailable;
    const auto expected_constructors = dynamic || prior_missing ? std::size_t{2} : std::size_t{0};
    Require(constructor_calls == expected_constructors &&
        getter_calls == (dynamic ? std::size_t{10} : std::size_t{0}),
        "two original production samples must use expected constructor/getter counts");
    std::vector<std::size_t> free_order;
    std::vector<std::size_t> element_order;
    for (const auto &event : cleanup) {
      Require(event.sample >= std::size_t{1} && event.sample <= std::size_t{2},
          "cleanup event lost its owned sample identity");
      (event.element ? element_order : free_order).push_back(event.vector_offset);
    }
    if (dynamic) {
      Require(free_order == std::vector<std::size_t>{0x148U, 0x128U, 0x100U, 0x18U,
                                                    0x148U, 0x128U, 0x100U, 0x18U} &&
          element_order == std::vector<std::size_t>{0x148U, 0x128U, 0x100U,
                                                   0x148U, 0x128U, 0x100U},
          "owned inline elements and allocator free order must be148,128,100,18");
      Require(cleanup.size() == std::size_t{14}, "unexpected extra lifecycle callback");
      for (std::size_t index = 0; index < std::size_t{2}; ++index) {
        const auto base = index * std::size_t{7};
        Require(cleanup[base].element && !cleanup[base + 1].element &&
            cleanup[base + 2].element && !cleanup[base + 3].element &&
            cleanup[base + 4].element && !cleanup[base + 5].element &&
            !cleanup[base + 6].element,
            "each tail inline destructor must precede its free callback");
      }
    } else if (prior_missing) {
      Require(free_order == std::vector<std::size_t>{0x18U, 0x18U} && element_order.empty(),
          "lost source prefix must still clean constructor-owned root allocation");
    } else Require(cleanup.empty() && allocations.empty(),
        "literal-only/family-empty cases must not construct or release a scope");
    for (const auto &allocation : allocations)
      Require(allocation->released, "an owned fake vector allocation was not released");
  }
};

void ScopeElementDestroy(void *element, std::uint32_t flags) {
  Require(scope_current && flags == std::uint32_t{0},
      "actual tail destructor flags must be DWORD0");
  auto &c = *scope_current;
  for (const auto &allocation : c.allocations) {
    if (allocation->data.get() == element) {
      Require(allocation->vector_offset != std::size_t{0x18} &&
          !allocation->element_destroyed && !allocation->released,
          "inline element destroyed twice or root data treated as element");
      allocation->element_destroyed = true;
      c.cleanup.push_back({allocation->sample, allocation->vector_offset, true});
      return;
    }
  }
  Require(false, "inline destructor receiver must point into an owned vector block");
}

void ScopeAllocatorFree(void *allocator, void *data, std::uint32_t alignment) {
  Require(scope_current && alignment == std::uint32_t{8},
      "allocator third argument is literal alignment8, not a byte count");
  auto &allocation = *static_cast<ScopeAllocation *>(allocator);
  Require(allocation.owner == scope_current && allocation.data.get() == data &&
      !allocation.released, "allocator receiver/data identity differs or was released twice");
  if (allocation.vector_offset == std::size_t{0x18})
    Require(ScopeLoad<std::int32_t>(allocation.scope, 0x24) == std::int32_t{0},
        "root cleanup must zero its mutable count before allocator callback");
  else Require(allocation.element_destroyed,
      "tail inline element must be destroyed before its allocated block is released");
  allocation.released = true;
  allocation.owner->cleanup.push_back({allocation.sample, allocation.vector_offset, false});
  // The fixture owns backing bytes until packet assertions finish. This is the
  // explicit fake allocator callback seam, not execution of a CK3 allocator.
}

void *ScopeConstruct(void *receiver) {
  Require(scope_current, "constructor callback requires the active offline fixture");
  auto &c = *scope_current;
  auto *const scope = static_cast<std::byte *>(receiver) - 0x18;
  ++c.constructor_calls;
  c.active_scope = scope;
  c.getter_in_sample = 0;
  c.Vector(scope, 0x18, 0x100, false);
  // Closed constructor inline allocator layout: object at receiver+18,
  // vptr at+0 and support pointer at+C8. Root allocator pointer is intentionally
  // the fixture's separate owned allocator seam so cleanup is observable.
  ScopePut(receiver, 0x18, c.allocator_vtable.data());
  ScopePut(receiver, 0x18 + 0xC8, static_cast<void *>(c.fake_inline_support.data()));
  return receiver;
}

std::int64_t *ScopeReadWeight(const void *physical_row, std::int64_t *output,
                             const void *scope) {
  Require(scope_current && output, "row-weight callback needs the current fixture and I64out");
  auto &c = *scope_current;
  Require(scope == c.active_scope && c.getter_in_sample < c.expected_rows.size() &&
      physical_row == c.expected_rows[c.getter_in_sample] && physical_row,
      "actual row order or shared mutable scope identity differs");
  Require(ScopeLoad<std::uint16_t>(scope, 0) == std::uint16_t{4} &&
      ScopeLoad<std::uint64_t>(scope, 8) == static_cast<std::uint64_t>(ScopeFixture::kRawPayload) &&
      ScopeLoad<std::uint32_t>(scope, 0x10) == std::uint32_t{0xFFFFFFFFU},
      "scope kind/root payload/sentinel must use selected linked-object DWORD20");
  const auto prefix = ScopeLoad<std::int32_t>(scope, 0x24);
  Require(prefix == static_cast<std::int32_t>(c.getter_in_sample),
      "each physical row must retain mutations from all preceding scope calls");
  auto *const mutable_scope = const_cast<void *>(scope);
  if (c.getter_in_sample == std::size_t{0}) {
    c.Vector(mutable_scope, 0x148, 0x48, true);
    c.Vector(mutable_scope, 0x128, 0x20, true);
    c.Vector(mutable_scope, 0x100, 0x48, true);
  }
  if (physical_row == c.prior.literal)
    *output = c.kind == ScopeCase::dynamic_zero ? std::int64_t{0}
        : std::int64_t{150'000} + static_cast<std::int64_t>(prefix) * std::int64_t{50'000};
  else if (physical_row == c.prior.raw) *output = std::int64_t{-150'000};
  else if (physical_row == c.prior.zero) *output = std::int64_t{0};
  else {
    Require(physical_row == c.prior.empty, "unknown physical row supplied to scope getter");
    *output = std::int64_t{100'000};
  }
  ScopePut(mutable_scope, 0x24, static_cast<std::int32_t>(prefix + std::int32_t{1}));
  ++c.getter_in_sample;
  ++c.getter_calls;
  return output;
}

void ProduceScopePacket(const std::filesystem::path &directory,
                        const ScopeSpec &spec, std::uint64_t sequence) {
  ScopeFixture c(spec.kind);
  scope_current = &c;
  Prior45SourceNotExecuted::opinion_current = &c.prior;
  auto &f = c.prior.f;
  const auto snapshot = f.Observe();
  const auto &person = *snapshot.character_observations->front().current_person_state;
  Require(person.following_2921a90_conditional && person.following_2921a90_opinion &&
      person.following_2921a90_scope_weights,
      "production whole packet must retain old44/45 and new scope-weight siblings");
  const auto &source = *person.following_2921a90_conditional;
  const auto &opinion = *person.following_2921a90_opinion;
  const auto &d = *person.following_2921a90_scope_weights;
  Require(opinion.source_inputs == source && d.character_id == Fixture::kEnemyUnsigned &&
      d.build_version == native4::kGameVersion &&
      d.executable_sha256 == native4::kExecutableSha256 &&
      d.rows.size() == opinion.rows.size(),
      "scope observer must preserve exact4 full enemy identity and old source contracts");
  for (std::size_t index = 0; index < d.rows.size(); ++index)
    Require(d.rows[index].native_index == static_cast<std::uint32_t>(index) &&
        d.rows[index].source_inputs == opinion.rows[index],
        "new evaluation must retain each original45 row unchanged");
  if (spec.kind == ScopeCase::family_empty) {
    Require(source.ready && opinion.ready && d.ready && d.rows.empty() &&
        d.occurrence_count == std::uint32_t{0} && !d.scope_initialized &&
        !d.scope_kind_u16 && !d.scope_payload_u32 &&
        c.prior.reads_a == std::size_t{0} && c.prior.reads_b == std::size_t{0},
        "observed empty family must not borrow a classifier vote or construct a scope");
  } else {
    Require(!source.ready && !source.classifier_ready && !source.classifier_result_i32 &&
        source.rows.empty() && source.reason == "classifier_25a1220_directional_opinion_unobserved" &&
        opinion.classifier_ready && opinion.classifier_result_i32 == std::int32_t{0} &&
        d.classifier_ready && d.classifier_result_i32 == std::int32_t{0} &&
        d.selected_family == "bb0_bbc" &&
        d.selected_object_identity == Address(f.mapped_object) &&
        d.selected_array_identity == Address(c.prior.selected_list) &&
        c.prior.reads_a == std::size_t{8} && c.prior.reads_b == std::size_t{4},
        "source44 partial, actual pair direction, selected family or provider counts changed");
    if (spec.kind == ScopeCase::literal_only) {
      Require(opinion.ready && d.ready && !d.scope_initialized &&
          !d.scope_kind_u16 && !d.scope_payload_u32 && d.rows.size() == std::size_t{3} &&
          d.selected_count_i32 == std::int32_t{3} &&
          d.occurrence_count == std::uint32_t{3},
          "three literal occurrences must stay ready without scope callbacks");
      for (const auto &row : d.rows)
        Require(!row.weight_call_ordinal && row.evaluated_inputs && row.evaluated_inputs->ready &&
            row.evaluated_inputs->weight_q64 == std::int64_t{100'000},
            "literal-only row must retain observed source weight and no getter call");
    } else {
      Require(d.scope_initialized && d.scope_kind_u16 == std::uint16_t{4} &&
          d.scope_payload_u32 == ScopeFixture::kRawPayload &&
          d.selected_count_i32 == std::int32_t{5} && d.rows.size() == std::size_t{5} &&
          !opinion.ready && !opinion.occurrence_count,
          "new scope provenance must remain separate from old45 dynamic partial");
      if (spec.kind == ScopeCase::prior_row_unavailable) {
        Require(!d.ready && !d.occurrence_count &&
            d.reason == "scope_weight_source_row_unavailable" &&
            !d.rows[0].scope_prefix_ready && !d.rows[0].weight_call_ordinal &&
            !d.rows[1].scope_prefix_ready && !d.rows[1].weight_call_ordinal &&
            d.rows[1].evaluated_inputs && !d.rows[1].evaluated_inputs->ready &&
            d.rows[1].evaluated_inputs->reason == "scope_weight_source_prefix_unavailable",
            "missing first physical source must suppress all later dynamic getter calls");
        const std::array<std::int64_t, 3> later{std::int64_t{-150'000}, std::int64_t{0},
                                              std::int64_t{100'000}};
        for (std::size_t index = 0; index < later.size(); ++index) {
          const auto &row = d.rows[index + 2];
          Require(!row.weight_call_ordinal && row.evaluated_inputs &&
              row.evaluated_inputs->ready && row.evaluated_inputs->weight_q64 == later[index],
              "unavailable scope prefix must preserve independently ready later source rows");
        }
      } else {
        Require(d.ready && d.occurrence_count ==
                (spec.kind == ScopeCase::dynamic_zero ? std::uint32_t{2} : std::uint32_t{4}) &&
            !opinion.rows[0].ready && !opinion.rows[2].ready &&
            opinion.rows[0].reason == "weight_virtual_expression_9d7060_unobserved" &&
            d.rows[0].source_inputs.object_identity == d.rows[2].source_inputs.object_identity,
            "new observed dynamic values must not repair old45 or collapse duplicate occurrences");
        const std::array<std::int64_t, 5> expected{
            spec.kind == ScopeCase::dynamic_zero ? std::int64_t{0} : std::int64_t{150'000},
            std::int64_t{-150'000},
            spec.kind == ScopeCase::dynamic_zero ? std::int64_t{0} : std::int64_t{250'000},
            std::int64_t{0}, std::int64_t{100'000}};
        for (std::size_t index = 0; index < d.rows.size(); ++index) {
          const auto &row = d.rows[index];
          Require(row.scope_prefix_ready &&
              row.weight_call_ordinal == static_cast<std::uint32_t>(index) &&
              row.evaluated_inputs && row.evaluated_inputs->ready &&
              row.evaluated_inputs->weight_q64 == expected[index],
              "each physical row must carry its native getter ordinal and I64 observed weight");
          if (expected[index] == std::int64_t{0})
            Require(!row.evaluated_inputs->properties,
                "actual observed zero weight must skip property collection reads");
        }
      }
    }
  }
  c.CheckCleanup();
  const auto request_id = std::string("person-conditional-scope-") + spec.filename;
  const auto packet = xar::ck3_11906::SerializeBattleTerminalTransitionCommandResultV1(
      request_id, Fixture::kStep, sequence, snapshot);
  Require(packet.find("\"following_2921a90_scope_weights\":{") != std::string::npos &&
      packet.find("\"following_2921a90_opinion\":{") != std::string::npos &&
      packet.find("\"following_2921a90_conditional\":{") != std::string::npos,
      "production shared formatter omitted new sibling or unchanged old whole source");
  std::ofstream output(directory / spec.filename, std::ios::binary);
  output << packet;
  output.close();
  Require(static_cast<bool>(output), "cannot write NEW original offline scope whole packet");
  Prior45SourceNotExecuted::opinion_current = nullptr;
  scope_current = nullptr;
}
} // namespace

int main(int argc, char **argv) {
  if (argc != 2) return 2;
  const std::filesystem::path directory(argv[1]);
  std::error_code error;
  std::filesystem::create_directories(directory, error);
  Require(!error, "cannot create NEW offline scope whole output directory");
  std::uint64_t sequence = 0;
  for (const auto &spec : kScopeCases) ProduceScopePacket(directory, spec, ++sequence);
  std::cout << "person conditional scope: five NEW offline callback whole-command packets\n";
  return 0;
}
