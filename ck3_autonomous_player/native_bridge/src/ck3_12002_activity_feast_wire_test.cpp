#include "activity_feast_stage5_start_private_transport_v1.hpp"
#include <fstream>
#include <cstring>
#include <cstdlib>

int main(int argc, char **argv) {
  if (argc != 2) return 2;
  using namespace xar;
  ck3_11906::ActivityFeastStage5PrivateQueryV1 query{};
  query.completed = true;
  query.mode = ck3_11906::ActivityFeastStage5PrivateModeV1::hosted_post;
  query.post.frame = {12, 53220000, 29829, true, true, true, true};
  query.post.balances.frame = query.post.frame;
  query.post.balances.available = {true, false, true, false};
  query.post.balances.raw = {110644281, 0, 4000000, 0};
  query.post.hosted_identities_observed = true;
  query.post.hosted_count = 1;
  query.post.outcome_values.frame = query.post.frame;
  query.post.outcome_values.prestige_available = true;
  query.post.outcome_values.prestige_raw = 25000000;
  query.post.outcome_values.stress_available = true;
  query.post.outcome_values.stress_points = 42;
  query.post.outcome_values.reveler_available = true;
  query.post.outcome_values.reveler_present = false;
  auto &identity = query.post.hosted[0];
  identity.activity_id = 0x01000012;
  identity.host_character_id = 29829;
  std::memcpy(identity.type_key.data(), "activity_feast", 14);
  identity.type_key_size = 14;
  identity.terminal_flags_observed = true;
  std::ofstream output(argv[1], std::ios::binary);
  if (!output) return 3;
  output << "[";
  for (int phase = 0; phase < 3; ++phase) {
    identity.native_completed = phase == 1;
    identity.native_invalidated = phase == 2;
    const auto serialized = ck3_11906::SerializeActivityFeastStage5PrivateV1(query);
    if (serialized.empty()) return 4;
    if (phase) output << ",";
    output << serialized;
  }
  output << "]\n";
  return output.good() ? 0 : 5;
}
