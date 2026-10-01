#include "xar_bridge/religion_doctrine12002_numeric_final.hpp"

// Reuse frozen memory layout only. The old 15-check main is never executed.
#define main NumericSpecialFixtureLibraryMain
#include "religion_doctrine12002_numeric_test.cpp"
#undef main

namespace {
std::int64_t native_define = 2500000;
int threshold_calls = 0;
bool bad_return = false, threshold_drift = false;
template <typename T> T FinalLoad(const void *object, std::size_t at) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + at, sizeof(value));
  return value;
}
std::int64_t *Threshold(const void *faith, std::int64_t *output) {
  ++threshold_calls;
  if (faith != f->faith.data() ||
      FinalLoad<std::uint32_t>(faith, r::kFaithMainRiteIdOffset) != Fixture::main_id || bad_return)
    return nullptr;
  const auto adjustment = FinalLoad<std::int64_t>(f->main_rite.data(),
      d::kRiteNumericSpecialOffset + d::kNumericHeresyThresholdOffset);
  *output = native_define + adjustment;
  if (threshold_drift && threshold_calls == 2) ++*output;
  return output;
}
void FinalWire(const std::filesystem::path &directory, const char *name, const d::FaithNumericFinalContext &out) {
  if (!directory.empty()) std::ofstream(directory / name) << d::SerializeFaithNumericFinal12002(out) << '\n';
}
} // namespace

int main(int argc, char **argv) {
  const auto directory = argc > 1 ? std::filesystem::path(argv[1]) : std::filesystem::path{};
  Fixture q; const auto rbind = Bind(q);
  const d::NumericSpecialBindings numeric{true};
  const d::FaithNumericFinalBindings final_bind{true, &Threshold, &native_define};
  d::FaithNumericFinalContext out{};
  if (!Check(d::ReadPlayedFaithNumericFinal12002(rbind, numeric, final_bind, 101, out), "actual Faith final provider") ||
      !Check(out.available && out.capture_epoch == 101 && out.date_raw == 53175816 &&
             out.played_character_id == Fixture::character_id && out.current_rite_id == 0U &&
             out.faith_id == Fixture::faith_id && out.main_rite_id == Fixture::main_id,
             "actual current/main full scope identity") ||
      !Check(out.main_rite_adjustment_raw == 500000 && out.native_define_raw == 2500000 &&
             out.final_heresy_threshold_raw == 3000000 && threshold_calls == 2,
             "two actual native callbacks final30 with main+5 not actor-5")) return 1;
  FinalWire(directory, "final-threshold-versus-adjustment.json", out);
  native_define = -500000;
  if (!Check(d::ReadPlayedFaithNumericFinal12002(rbind, numeric, final_bind, 102, out) &&
             out.final_heresy_threshold_raw == 0 && out.final_heresy_threshold_raw.has_value(),
             "actual native zero final value remains present")) return 2;
  FinalWire(directory, "known-zero-final.json", out); native_define = 2500000;
  Put(q.rite, r::kRiteFaithIdOffset, r::kAbsentReference); threshold_calls = 0;
  if (!Check(d::ReadPlayedFaithNumericFinal12002(rbind, numeric, final_bind, 103, out) &&
             !out.faith_id && !out.final_heresy_threshold_raw && threshold_calls == 0,
             "legal absent Faith uses no fallback callback")) return 3;
  FinalWire(directory, "legal-absent-faith.json", out);
  Put(q.rite, r::kRiteFaithIdOffset, Fixture::faith_id);
  Put(q.faith, r::kFaithMainRiteIdOffset, r::kAbsentReference);
  if (!Check(d::ReadPlayedFaithNumericFinal12002(rbind, numeric, final_bind, 104, out) &&
             out.faith_id && !out.main_rite_id && !out.final_heresy_threshold_raw && threshold_calls == 0,
             "legal absent main Rite has no native comparison value")) return 4;
  FinalWire(directory, "legal-absent-main-rite.json", out);
  Put(q.faith, r::kFaithMainRiteIdOffset, Fixture::main_id); bad_return = true;
  if (!Check(!d::ReadPlayedFaithNumericFinal12002(rbind, numeric, final_bind, 105, out) &&
             !out.available && out.failure == "native_threshold_unavailable", "actual callback result required")) return 5;
  FinalWire(directory, "native-threshold-unavailable.json", out); bad_return = false;
  threshold_calls = 0; threshold_drift = true;
  if (!Check(!d::ReadPlayedFaithNumericFinal12002(rbind, numeric, final_bind, 106, out) &&
             out.failure == "state_changed", "native comparison samples differ")) return 6;
  FinalWire(directory, "state-changed.json", out); threshold_drift = false;
  const auto actual = d::BindFaithNumericFinal12002(0x140000000, c::kExecutableSha256);
  if (!Check(actual.enabled && reinterpret_cast<std::uintptr_t>(actual.faith_heresy_threshold) == 0x142440920 &&
             reinterpret_cast<std::uintptr_t>(actual.heresy_threshold_define) == 0x145C68D88,
             "exact native callback and define binding") ||
      !Check(!d::BindFaithNumericFinal12002(0x140000000, "old").enabled &&
             !d::BindFaithNumericFinal12002(0, c::kExecutableSha256).enabled, "exact build final binder")) return 7;
  std::cout << "PASS checks=" << checks << " actual_provider=true actual_native_callback=true actual_serializer=true live=false old_main_executed=false\n";
  return 0;
}
