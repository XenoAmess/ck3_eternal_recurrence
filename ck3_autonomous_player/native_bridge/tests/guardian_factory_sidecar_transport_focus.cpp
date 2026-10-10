#include "xar_bridge/guardian_factory_discovery_job_v1.hpp"
#include "xar_bridge/protocol.hpp"

#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <optional>
#include <string>

namespace {
std::string Read(const char *path) {
  std::ifstream input(path, std::ios::binary);
  if (!input) return {};
  return {std::istreambuf_iterator<char>{input},
          std::istreambuf_iterator<char>{}};
}
}

// One new boundary regression. It supplies no actual factory/vtable facts and
// does not rerun the qualified metadata/lookup fixtures or call native CK3.
int main(int argc, char **argv) {
  if (argc != 4) return 2;
  const auto old_request = Read(argv[1]);
  const auto fixed_request = Read(argv[2]);
  const auto family_frame = Read(argv[3]);
  if (old_request.empty() || fixed_request.empty() || family_frame.empty()) return 3;
  std::string old_path;
  if (xar::bridge::JsonStringField(old_request, "guardian_factory_sidecar_path",
                                  old_path, 32768) || !old_path.empty()) return 4;
  std::string fixed_path;
  if (!xar::bridge::JsonStringField(fixed_request, "guardian_factory_sidecar_path",
                                   fixed_path, 32768) || fixed_path.empty()) return 5;
  std::string step;
  if (!xar::bridge::JsonStringField(fixed_request, "step", step, 128) ||
      step != "query-current-first-heir-relationship-v1-private") return 6;
  const auto path = std::filesystem::path(std::u8string(
      fixed_path.begin(), fixed_path.end()));
  if (!path.is_absolute() || std::filesystem::exists(path)) return 7;

  std::optional<xar::bridge::GuardianFactoryDiscoveryJobV1> job;
  if (!fixed_path.empty()) job.emplace(); // Same production admission seam.
  if (!job) return 8;
  job->request_id = "fixture-path-boundary";
  job->unavailable_reason = "fixture_metadata_not_acquired";
  job->expected_snapshot.paused = true;
  job->expected_snapshot.date_raw = 53290128;
  job->expected_snapshot.played_character_id = 29829;
  job->native_revision = 2;
  job->heir_character_id = 38822;
  job->executable_sha256 = xar::ck3_12004::kExecutableSha256;

  xar::bridge::GuardianFactoryDiscoveryExportV1 exported{};
  exported.requested = true;
  exported.path_parsed = true;
  exported.job_created = true;
  exported.job_reclaimed = true;
  exported.completion_attempted = true;
  exported.sidecar_written = xar::bridge::CompleteGuardianFactoryDiscoveryJobV1(
      *job, job->expected_snapshot, path, exported.error);
  if (!exported.sidecar_written || !exported.error.empty()) return 9;
  const auto sidecar = Read(path.string().c_str());
  if (sidecar.find("\"qualified\":false") == std::string::npos ||
      sidecar.find("\"key\":\"has_relation_guardian\"") == std::string::npos ||
      sidecar.find("\"key\":\"has_relation_ward\"") == std::string::npos) return 10;
  xar::bridge::GuardianFactoryDiscoveryExportV1 ordinary{};
  if (xar::bridge::AppendGuardianFactoryDiscoveryExportV1(family_frame, ordinary)
      != family_frame) return 11;
  std::string failure;
  const auto missing_parent = path.parent_path() / "fixture-parent-absent" / "sidecar.json";
  if (xar::bridge::CompleteGuardianFactoryDiscoveryJobV1(
          *job, job->expected_snapshot, missing_parent, failure) ||
      failure != "guardian_factory_sidecar_open_failed") return 12;
  auto failed = exported;
  failed.sidecar_written = false;
  failed.error = failure;
  const auto failed_frame = xar::bridge::AppendGuardianFactoryDiscoveryExportV1(
      family_frame, failed);
  if (failed_frame.find("guardian_factory_sidecar_open_failed") == std::string::npos ||
      failed_frame.find("\"sidecar_written\":false") == std::string::npos) return 13;
  std::cout << xar::bridge::AppendGuardianFactoryDiscoveryExportV1(
      family_frame, exported) << '\n';
  return 0;
}
