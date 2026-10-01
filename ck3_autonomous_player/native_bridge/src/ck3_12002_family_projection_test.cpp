#include "xar_bridge/ck3_12002_family_projection.hpp"
#include "xar_bridge/ck3_12002.hpp"
#include "xar_bridge/ck3_12002_family_query_abi.hpp"

#include <cstring>
#include <iostream>

namespace {
using namespace xar::ck3_12002;
using Failure = xar::bridge::MarriageCandidateAllianceProjectionFailureV1;
alignas(8) std::array<std::byte, 0x240> actor{}, recipient{}, subject{}, candidate{};
alignas(8) std::array<std::byte, 0x338> context{};
std::uint32_t option_id = 42;
bool option_selected = false, option_selectable = true;
std::int32_t row_count = 3;
bool mutate_context = false;
bool wrong_subject = false;
unsigned project_calls = 0, allied_calls = 0, assertions = 0;

template <typename T> void Store(void *base, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(base) + offset, &value, sizeof(value));
}
bool Read(void *, std::uintptr_t address, void *out, std::size_t size) noexcept {
  if (address == 0 || out == nullptr) return false;
  std::memcpy(out, reinterpret_cast<const void *>(address), size);
  return true;
}
bool ReadOption(const void *observed, std::uint32_t id) {
  return observed == context.data() && id == option_id && option_selected;
}
void SetOption(void *observed, std::uint32_t id, bool selected) {
  if (observed == context.data() && id == option_id && option_selectable)
    option_selected = selected;
}
bool Allied(const void *first, const void *second) {
  ++allied_calls;
  return first == actor.data() && second == candidate.data();
}
struct Header { void *data; std::int32_t capacity, count; void *owner; };
struct Row { const void *first, *second, *subject, *candidate; };
void Project(const void *observed, void *out) {
  ++project_calls;
  auto &v = *static_cast<Header *>(out);
  if (observed != context.data()) { v.count = -1; return; }
  const void *secondary = wrong_subject ? actor.data() : subject.data();
  const std::array<Row, 3> rows{{
      {actor.data(), recipient.data(), secondary, candidate.data()},
      {actor.data(), candidate.data(), secondary, candidate.data()},
      {subject.data(), recipient.data(), secondary, candidate.data()}}};
  if (row_count >= 0 && row_count <= 3)
    std::memcpy(v.data, rows.data(), static_cast<std::size_t>(row_count) * sizeof(Row));
  v.count = row_count;
  if (mutate_context)
    Store(context.data(), family_query_abi::kContextSecondaryRecipientIdOffset,
          std::uint32_t{999});
}
bool Check(bool okay, const char *reason) {
  ++assertions;
  if (!okay) std::cerr << reason << '\n';
  return okay;
}
} // namespace

int main() {
  using namespace xar::ck3_12002;
  using Output = xar::bridge::MarriageCandidateAllianceProjectionV1;
  const std::array<std::uint32_t, 4> ids{29829, 38713, 38822, 16778038};
  const std::array<void *, 4> characters{
      actor.data(), recipient.data(), subject.data(), candidate.data()};
  const std::array<std::size_t, 4> offsets{
      family_query_abi::kContextActorIdOffset,
      family_query_abi::kContextRecipientIdOffset,
      family_query_abi::kContextSecondaryActorIdOffset,
      family_query_abi::kContextSecondaryRecipientIdOffset};
  for (std::size_t i = 0; i < ids.size(); ++i) {
    Store(characters[i], 0x18, ids[i]);
    Store(characters[i], kFamilyProjectionRealmDataOffset, std::uintptr_t{1});
    Store(context.data(), offsets[i], ids[i]);
  }
  FamilyProjectionBindings b{};
  b.exact_build_admitted = true;
  b.admitted_executable_sha256 = kExecutableSha256;
  b.offline_fixture = true;
  b.read_memory = Read;
  b.project_pairs = Project;
  b.read_boolean_option = ReadOption;
  b.set_boolean_option = SetOption;
  b.is_allied = Allied;
  b.matrilineal_option_id_slot = reinterpret_cast<std::uintptr_t>(&option_id);
  b.native_owner_vtable = 1;
  Output out{};
  const auto read = [&] {
    return ReadFamilyAllianceProjectionV1(b, context.data(), ids[0], ids[1],
                                          ids[2], ids[3], out);
  };
  if (!Check(read() == Failure::none, "three-pair read unavailable") ||
      !Check(project_calls == 1 && allied_calls == 3, "native callbacks not used") ||
      !Check(out.pair_count == 3, "native three-row cardinality lost") ||
      !Check(!out.matrilineal_option_selected, "lineality did not read native option") ||
      !Check(out.pairs[0].first_character_id == ids[0] &&
             out.pairs[0].second_character_id == ids[1] &&
             out.pairs[0].would_attempt_if_accepted, "first authored pair lost") ||
      !Check(out.pairs[1].already_allied &&
             !out.pairs[1].would_attempt_if_accepted, "native allied result lost") ||
      !Check(out.pairs[2].first_character_id == ids[2] &&
             out.pairs[2].second_character_id == ids[1], "secondary pair lost")) return 1;
  Store(recipient.data(), kFamilyProjectionRealmDataOffset, std::uintptr_t{0});
  // Prove that the old offset cannot supply a false new-build realm result.
  Store(recipient.data(), 0x1B8, std::uintptr_t{1});
  if (!Check(read() == Failure::none && !out.pairs[0].both_have_realm_data &&
             !out.pairs[0].would_attempt_if_accepted,
             "new native realm offset was not consumed")) return 1;
  Store(recipient.data(), kFamilyProjectionRealmDataOffset, std::uintptr_t{1});
  if (!Check(SelectFamilyMatrilinealOptionV1(b, context.data()) && option_selected,
             "stock disposable option setter failed") ||
      !Check(read() == Failure::none && out.matrilineal_option_selected,
             "selected native lineality lost")) return 1;
  option_selected = false; option_selectable = false;
  if (!Check(!SelectFamilyMatrilinealOptionV1(b, context.data()) && !option_selected,
             "rejected native option reported selected")) return 1;
  option_selectable = true;
  row_count = 0;
  if (!Check(read() == Failure::none && out.pair_count == 0,
             "native empty result reported unavailable")) return 1;
  row_count = 3; wrong_subject = true;
  if (!Check(read() == Failure::row_identity_mismatch && out.pair_count == 0 &&
             !out.matrilineal_option_selected,
             "candidate-bound row identity was not observed")) return 1;
  wrong_subject = false; mutate_context = true;
  if (!Check(read() == Failure::context_roles_mismatch && out.pair_count == 0 &&
             !out.matrilineal_option_selected,
             "drifting finalized context was published")) return 1;
  mutate_context = false;
  Store(context.data(), offsets[3], ids[3]);
  b.admitted_executable_sha256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
  if (!Check(read() == Failure::exact_build_not_admitted,
             "old executable was admitted")) return 1;
  const auto bound = BindFamilyProjectionImage(0x140000000, kExecutableSha256);
  if (!Check(bound.exact_build_admitted &&
             reinterpret_cast<std::uintptr_t>(bound.project_pairs) ==
               0x140000000 + kFamilyProjectionPairWrapperRva &&
             bound.matrilineal_option_id_slot ==
               0x140000000 + kFamilyProjectionMatrilinealSlotRva,
             "actual new-build addresses not bound") ||
      !Check(!BindFamilyProjectionImage(0x140000000, "old").exact_build_admitted,
             "hash-mismatched image was bound")) return 1;
  std::cout << "CK3 1.20.0.2 family projection GREEN (" << assertions
            << " functional checks; no process access)\n";
  return 0;
}
