#include "xar_bridge/marriage_candidate_alliance_projection_v1.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>

namespace {

using xar::bridge::MarriageCandidateAllianceProjectionEnvironmentV1;
using xar::bridge::MarriageCandidateAllianceProjectionFailureV1;
using xar::bridge::MarriageCandidateAllianceProjectionV1;

alignas(8) std::array<std::byte, 0x200> actor{};
alignas(8) std::array<std::byte, 0x200> recipient{};
alignas(8) std::array<std::byte, 0x200> heir{};
alignas(8) std::array<std::byte, 0x200> candidate{};
bool emit_pair = true;
std::uint32_t option_seen = 0;

template <typename Value>
void WriteAt(void *base, std::size_t offset, Value value) {
  std::memcpy(static_cast<std::byte *>(base) + offset, &value, sizeof(value));
}

bool ReadMemory(void *, std::uintptr_t address, void *output,
                std::size_t size) noexcept {
  if (address == 0 || output == nullptr) return false;
  std::memcpy(output, reinterpret_cast<const void *>(address), size);
  return true;
}

bool ReadOption(const void *, std::uint32_t option_id) {
  option_seen = option_id;
  return option_id == 42;
}

bool IsAllied(const void *, const void *) { return false; }

struct VectorHeader {
  void *data;
  std::int32_t capacity;
  std::int32_t count;
  void *owner;
};

struct PairRow {
  const void *first;
  const void *second;
  const void *secondary_actor;
  const void *secondary_recipient;
};

void Project(const void *, void *native_vector) {
  if (!emit_pair) return;
  auto &vector = *static_cast<VectorHeader *>(native_vector);
  const PairRow row{actor.data(), recipient.data(), heir.data(),
                    candidate.data()};
  std::memcpy(vector.data, &row, sizeof(row));
  vector.count = 1;
}

bool Check(bool condition, const char *message) {
  if (condition) return true;
  std::cerr << message << '\n';
  return false;
}

} // namespace

int main() {
  using namespace xar::bridge;
  alignas(8) std::array<std::byte, kMarriageInteractionContextSizeV1> context{};
  WriteAt(actor.data(), kMarriageCharacterIdOffsetV1, std::uint32_t{29829});
  WriteAt(recipient.data(), kMarriageCharacterIdOffsetV1,
          std::uint32_t{38713});
  WriteAt(heir.data(), kMarriageCharacterIdOffsetV1, std::uint32_t{38822});
  WriteAt(candidate.data(), kMarriageCharacterIdOffsetV1,
          std::uint32_t{16778038});
  WriteAt(actor.data(), kMarriageCandidateRealmDataOffsetV1,
          std::uintptr_t{1});
  WriteAt(recipient.data(), kMarriageCandidateRealmDataOffsetV1,
          std::uintptr_t{1});
  WriteAt(context.data(), kMarriageContextActorIdOffsetV1,
          std::uint32_t{29829});
  WriteAt(context.data(), kMarriageContextRecipientIdOffsetV1,
          std::uint32_t{38713});
  WriteAt(context.data(), kMarriageContextSecondaryActorIdOffsetV1,
          std::uint32_t{38822});
  WriteAt(context.data(), kMarriageContextSecondaryRecipientIdOffsetV1,
          std::uint32_t{16778038});
  std::uint32_t option_id = 42;
  MarriageCandidateAllianceProjectionEnvironmentV1 env{};
  env.exact_build_admitted = true;
  env.admitted_executable_sha256 =
      kMarriageMatchmakingSourceAdapterExecutableSha256V1;
  env.offline_fixture = true;
  env.read_memory = &ReadMemory;
  env.project_pairs = &Project;
  env.read_boolean_option = &ReadOption;
  env.is_allied = &IsAllied;
  env.matrilineal_option_id_slot =
      reinterpret_cast<std::uintptr_t>(&option_id);
  env.native_owner_vtable = 1;

  MarriageCandidateAllianceProjectionV1 projection{};
  auto result = ReadMarriageCandidateAllianceProjectionV1(
      env, context.data(), 29829, 38713, 38822, 16778038, projection);
  if (!Check(result == MarriageCandidateAllianceProjectionFailureV1::none,
             "candidate projection unexpectedly unavailable") ||
      !Check(option_seen == 42 && projection.matrilineal_option_selected,
             "lineality option was not read from the candidate context") ||
      !Check(projection.pair_count == 1 &&
                 projection.pairs[0].first_character_id == 29829 &&
                 projection.pairs[0].second_character_id == 38713 &&
                 projection.pairs[0].would_attempt_if_accepted,
             "candidate-bound alliance pair was lost"))
    return 1;

  emit_pair = false;
  projection = {};
  result = ReadMarriageCandidateAllianceProjectionV1(
      env, context.data(), 29829, 38713, 38822, 16778038, projection);
  if (!Check(result == MarriageCandidateAllianceProjectionFailureV1::none &&
                 projection.pair_count == 0,
             "empty native projection must remain a valid empty result"))
    return 1;

  result = ReadMarriageCandidateAllianceProjectionV1(
      env, context.data(), 29829, 38713, 38822, 16778252, projection);
  if (!Check(result == MarriageCandidateAllianceProjectionFailureV1::
                           context_roles_mismatch,
             "stale candidate identity was accepted"))
    return 1;
  std::cout << "marriage candidate alliance projection v1 GREEN\n";
  return 0;
}
