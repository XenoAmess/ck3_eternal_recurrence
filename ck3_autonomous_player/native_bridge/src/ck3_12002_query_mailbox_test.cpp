#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/ck3_12002.hpp"

#include <cassert>
#include <string>

// This fixture contains no native state reader. It checks identity projection
// over the actual shared wire rendering helper, including escaped user text.
int main() {
  const std::string old_sha =
      "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
  const std::string external =
      "\"title\":\"user says \\\"version\\\":\\\"1.19.0.6\\\"\"";
  const std::string input =
      "{\"game_version\":\"1.19.0.6\",\"build\":{\"version\":\"1.19.0.6\","
      "\"exe_sha256\":\"" + old_sha + "\"}," + external +
      ",\"source\":{\"backend_id\":\"ck3-1.19.0.6-native-event-window-v1\"}}";
  const auto result = xar::ck3_12002::RenderQueryBuildIdentity(input);
  assert(result.find("\"game_version\":\"1.20.0.2\"") != std::string::npos);
  assert(result.find("\"version\":\"1.20.0.2\"") != std::string::npos);
  assert(result.find(xar::ck3_12002::kExecutableSha256) != std::string::npos);
  assert(result.find("ck3-1.20.0.2-native-event-window-v1") != std::string::npos);
  assert(result.find(external) != std::string::npos);
  assert(xar::ck3_12002::RenderQueryBuildIdentity("{\"date_raw\":42}") ==
         "{\"date_raw\":42}");
  return 0;
}
