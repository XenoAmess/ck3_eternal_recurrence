#include "xar_bridge/activity_feast_guest_opinion_v1.hpp"

#include <cstdio>

namespace {

using namespace xar::bridge;

struct Fixture {
  ActivityFeastGuestOpinionFrameV1 frame{4, 10000, 31000, true, true,
                                         true};
  std::int32_t expected_guest_id = 32000;
  std::int32_t expected_actor_id = 31000;
  std::int32_t opinion = -25;
  bool fail_opinion = false;
  bool change_after_read = false;
  int frame_reads = 0;
  int opinion_reads = 0;
};

bool ReadFrame(void *opaque, ActivityFeastGuestOpinionFrameV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  ++fixture.frame_reads;
  output = fixture.frame;
  if (fixture.change_after_read && fixture.frame_reads > 1)
    ++output.date_raw;
  return true;
}

bool ReadOpinion(void *opaque, std::uint32_t guest_id,
                 std::uint32_t actor_id, std::int32_t &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  ++fixture.opinion_reads;
  if (fixture.fail_opinion ||
      guest_id != static_cast<std::uint32_t>(fixture.expected_guest_id) ||
      actor_id != static_cast<std::uint32_t>(fixture.expected_actor_id))
    return false;
  output = fixture.opinion;
  return true;
}

bool Expect(bool ok, const char *message) {
  if (!ok) std::fprintf(stderr, "%s\n", message);
  return ok;
}

} // namespace

int main() {
  Fixture fixture{};
  const ActivityFeastGuestOpinionEnvironmentV1 environment{
      &fixture, &ReadFrame, &ReadOpinion};
  const auto expected = fixture.frame;
  auto result = ReadActivityFeastGuestOpinionV1(environment, expected, 32000);
  if (!Expect(result.status == ActivityFeastGuestOpinionStatusV1::observed &&
                  result.guest_opinion_of_actor == -25 &&
                  fixture.opinion_reads == 1,
              "negative opinion is a valid observed value"))
    return 1;

  fixture.frame_reads = fixture.opinion_reads = 0;
  fixture.change_after_read = true;
  result = ReadActivityFeastGuestOpinionV1(environment, expected, 32000);
  if (!Expect(result.status == ActivityFeastGuestOpinionStatusV1::frame_changed &&
                  fixture.opinion_reads == 1,
              "frame movement after the native opinion rejects publication"))
    return 1;

  fixture.frame_reads = fixture.opinion_reads = 0;
  fixture.change_after_read = false;
  fixture.fail_opinion = true;
  result = ReadActivityFeastGuestOpinionV1(environment, expected, 32000);
  if (!Expect(result.status ==
                  ActivityFeastGuestOpinionStatusV1::opinion_unavailable &&
                  fixture.opinion_reads == 1,
              "native opinion failure stays unknown, not zero"))
    return 1;

  fixture.frame_reads = fixture.opinion_reads = 0;
  result = ReadActivityFeastGuestOpinionV1(environment, expected, 31000);
  if (!Expect(result.status == ActivityFeastGuestOpinionStatusV1::invalid_request &&
                  fixture.frame_reads == 0 && fixture.opinion_reads == 0,
              "host is not a guest"))
    return 1;
  return 0;
}
