#include "xar_bridge/character_skill_effect12004.hpp"
#include <limits>

namespace xar::bridge::character_skill_effect12004 {
namespace {
constexpr std::uint32_t absent = 0xFFFFFFFFU;
template<class T> bool At(const Environment &e, std::uintptr_t p,
    std::size_t offset, T &out) noexcept {
  return p != 0 && offset <= (std::numeric_limits<std::uintptr_t>::max)() - p &&
      e.read_memory != nullptr && e.read_memory(e.context, p + offset, &out, sizeof(out));
}
bool FrameValid(const Frame &f) noexcept {
  return f.revision != 0 && f.played_character_id != absent &&
      f.owner_thread && f.paused && f.map_ready;
}
bool Resolve(const Environment &e, std::uintptr_t storage_rva,
    std::uint32_t id, std::size_t id_offset, std::uintptr_t &object) noexcept {
  std::uintptr_t storage = 0, rows = 0;
  std::uint32_t count = 0, physical = absent;
  return id != absent && At(e,e.image_base,storage_rva,storage) && storage != 0 &&
      At(e,storage,0x20,rows) && rows != 0 && At(e,storage,0x2C,count) &&
      count <= 0x01000000U && (id & 0xFFFFFFU) < count &&
      At(e,rows,static_cast<std::size_t>(id & 0xFFFFFFU)*16U+8U,object) && object != 0 &&
      At(e,object,id_offset,physical) && physical == id;
}
struct Sample {
  std::uintptr_t actor = 0, values = 0, rite = 0, faith = 0;
  std::uint32_t rite_id = absent, faith_id = absent;
  std::array<std::int32_t,6> skills{};
  std::int64_t devotion_total = 0;
  std::int32_t level = 0;
  std::string breakdown{};
  friend bool operator==(const Sample &, const Sample &) = default;
};
bool One(const Environment &e, const Request &r, Sample &s) noexcept {
  std::uint32_t magic = 0;
  if (!Resolve(e,0x5C67568,r.character_id,0x18,s.actor) ||
      !At(e,s.actor,0x1C,magic) || magic != 0x43686172U ||
      !At(e,s.actor,0x1B0,s.values) || s.values == 0 ||
      !At(e,s.actor,0xB4,s.rite_id) ||
      !Resolve(e,0x5D1E2F8,s.rite_id,8,s.rite) ||
      !At(e,s.rite,0x4B8,s.faith_id) ||
      !Resolve(e,0x5D1E300,s.faith_id,8,s.faith)) return false;
  for (std::size_t i=0;i<s.skills.size();++i) {
    if (!At(e,s.actor,0xD8+i*4,s.skills[i])) return false;
    // Preserve signed native points. A surprising negative is not rounded or
    // silently replaced with zero; the consumer may reject it for its purpose.
  }
  if (!At(e,s.values,0x118,s.devotion_total)) return false;
  // A source-qualified leaf must only call GetPietyLevel on an actual actor
  // with a non-null values pointer; its null-values native branch is undefined.
  if (!e.read_level(e.context,s.actor,s.level) ||
      !e.read_breakdown(e.context,SkillItem{r.skill,r.character_id},s.breakdown) ||
      s.breakdown.size() > kMaxBreakdownBytes) return false;
  return true;
}
} // namespace
bool Read(const Environment &e, const Request &r, Result &out) noexcept {
  out = {}; out.frame = r.expected; out.character_id = r.character_id;
  out.requested_skill = r.skill; out.callback_provenance = e.callback_provenance;
  const auto fail = [&out](const char *reason) noexcept {
    out.available = false; out.two_pass_stable = false;
    // This also covers an exception while publishing the final owned string:
    // no earlier optional field may survive as a partial actor observation.
    out.rite_id.reset(); out.faith_id.reset(); out.current_skill_points.reset();
    out.effective_devotion_level.reset(); out.devotion_total_raw.reset();
    out.actual_skill_breakdown.reset(); out.selected_site_contribution_raw.reset();
    out.site_attribution_observed = false;
    out.unavailable_reason = reason; return false;
  };
  try {
    if (!e.enabled || e.executable_sha256 != kExeSha || e.image_base == 0)
      return fail("exact4_bindings_unavailable");
    if (e.read_memory == nullptr || e.read_frame == nullptr || e.read_level == nullptr ||
        e.read_breakdown == nullptr ||
        (e.callback_provenance != CallbackProvenance::exact4_native &&
         !(e.allow_owned_fixture && e.callback_provenance == CallbackProvenance::owned_fixture)))
      return fail("source_bound_leaf_callbacks_unavailable");
    if (!FrameValid(r.expected) || r.character_id == absent || r.skill < 0 || r.skill >= 6)
      return fail("request_or_owner_frame_invalid");
    Frame before{}, middle{}, after{};
    if (!e.read_frame(e.context,before) || before != r.expected)
      return fail("owner_frame_changed_before");
    Sample first{},second{};
    if (!One(e,r,first)) return fail("first_actor_value_or_native_breakdown_unavailable");
    if (!e.read_frame(e.context,middle) || middle != r.expected)
      return fail("owner_frame_changed_between");
    if (!One(e,r,second)) return fail("second_actor_value_or_native_breakdown_unavailable");
    if (!e.read_frame(e.context,after) || after != r.expected || first != second)
      return fail("actor_values_or_source_text_changed");
    out.rite_id = first.rite_id; out.faith_id = first.faith_id;
    out.current_skill_points = first.skills; out.effective_devotion_level = first.level;
    out.devotion_total_raw = first.devotion_total; out.actual_skill_breakdown = first.breakdown;
    out.available = true; out.two_pass_stable = true; out.unavailable_reason.clear();
    return true;
  } catch (...) { return fail("owned_copy_exception"); }
}
} // namespace xar::bridge::character_skill_effect12004
