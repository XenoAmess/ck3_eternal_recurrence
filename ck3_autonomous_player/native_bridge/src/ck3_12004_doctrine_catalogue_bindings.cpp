#include "xar_bridge/ck3_12004_doctrine_catalogue_bindings.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12004_religion_profile.hpp"

namespace xar::ck3_12004::religion::doctrine_catalogue {
namespace {
namespace software = ck3_12002::religion::doctrine12002;

enum class FrameFailure { none, bindings, played, paused };
FrameFailure SelectPlayedFrame(const CoreBindings &core,
    CoreSnapshotPrefix &frame) noexcept {
  if (!core.enabled) return FrameFailure::bindings;
#if defined(_WIN32) && defined(_MSC_VER)
  __try {
#endif
    if (!ck3_12004::ReadCoreSnapshot(core, frame) || !frame.map_ready ||
        !frame.has_played_character || !frame.played_character_alive)
      return FrameFailure::played;
    return frame.clock.paused ? FrameFailure::none : FrameFailure::paused;
#if defined(_WIN32) && defined(_MSC_VER)
  } __except (1) { return FrameFailure::played; }
#endif
}

const char *FrameReason(FrameFailure failure) noexcept {
  switch (failure) {
  case FrameFailure::none: return "none";
  case FrameFailure::bindings: return "bindings_unavailable";
  case FrameFailure::played: return "played_character_unavailable";
  case FrameFailure::paused: return "frame_not_paused";
  }
  return "played_character_unavailable";
}
} // namespace

CatalogueBindings BindDoctrineCatalogueImage12004(std::uintptr_t base,
    std::string_view sha) noexcept {
  CatalogueBindings b{};
  if (base == 0 || sha != ck3_12004::kExecutableSha256) return b;
  b.core = ck3_12004::BindCoreImage(base, sha);
  b.database_slot = reinterpret_cast<void **>(
      base + profile::kDoctrineDatabaseSlotRva);
  b.enabled = b.core.enabled;
  return b;
}

bool ReadPlayedDoctrineCatalogue12004(const CatalogueBindings &b,
    std::uint64_t epoch, DoctrineCatalogue &out) noexcept {
  out = {};
  out.capture_epoch = epoch;
  if (!b.enabled) return false;
  CoreSnapshotPrefix frame{};
  const auto failure = SelectPlayedFrame(b.core, frame);
  if (failure != FrameFailure::none) {
    out.unavailable_reason = FrameReason(failure);
    return false;
  }
  // The existing software reader keeps the registry reread and two-copy frame
  // contract. Its Core callbacks and loaded DB slot were bound above for .4.
  // It never invokes the native database getter or initializes the database.
  return software::ReadPlayedDoctrineCatalogue12002(b, epoch, out);
}

} // namespace xar::ck3_12004::religion::doctrine_catalogue
