#include "xar_bridge/ck3_12003_pilgrimage_activity_terms.hpp"

#include <cstring>
#include <sstream>
#include <utility>

namespace xar::ck3_12003::religion::pilgrimage_activity_terms {
namespace {
namespace factory = pilgrimage_candidate_factory;

template <typename T> T Load(const void *object, std::size_t offset = 0) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value));
  return value;
}
template <typename T> void Store(void *object, std::size_t offset, T value) noexcept {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
}

bool ActivityKeyEquals(const void *definition) noexcept {
  const auto *key = static_cast<const std::byte *>(definition) + 0x18;
  const auto size = Load<std::size_t>(key, 0x10);
  const auto capacity = Load<std::size_t>(key, 0x18);
  if (size != kActivityId.size() || capacity < size) return false;
  const char *text = capacity < 16 ? reinterpret_cast<const char *>(key)
                                 : Load<const char *>(key);
  return text && std::memcmp(text, kActivityId.data(), size) == 0;
}
const void *FindPilgrimage(const pilgrimage::Bindings &b) noexcept {
  const void *database = *b.activity_type_database;
  if (!database) return nullptr;
  const auto *rows = Load<const void *const *>(database, 0x50);
  const auto count = Load<std::int32_t>(database, 0x5C);
  if (count > 0 && !rows) return nullptr;
  for (std::int32_t i = 0; i < count; ++i) {
    if (rows[i] && Load<std::uintptr_t>(rows[i]) == b.activity_type_vtable &&
        ActivityKeyEquals(rows[i])) return rows[i];
  }
  return nullptr;
}

class OwnedActivityConfig {
public:
  explicit OwnedActivityConfig(const Bindings &b) noexcept : b_(b) {}
  ~OwnedActivityConfig() { if (initialized_) b_.config_destroy(bytes_.data()); }
  bool initialize(const void *type, std::int32_t actor) {
    void *result = b_.config_initialize(bytes_.data(), type, actor);
    initialized_ = result != nullptr;
    return result == bytes_.data();
  }
  void *get() noexcept { return bytes_.data(); }
  const void *get() const noexcept { return bytes_.data(); }
  factory::PhaseRowView phases() const noexcept {
    return {Load<const std::byte *>(get(), 0xB0), Load<std::int32_t>(get(), 0xBC)};
  }
  OwnedActivityConfig(const OwnedActivityConfig &) = delete;
  OwnedActivityConfig &operator=(const OwnedActivityConfig &) = delete;
private:
  alignas(8) std::array<std::byte, 0x550> bytes_{};
  const Bindings &b_;
  bool initialized_ = false;
};

class NativeReason {
public:
  explicit NativeReason(const Bindings &b) noexcept : b_(b) {
    Store<std::uint64_t>(bytes_.data(), 0x18, 15);
  }
  ~NativeReason() { b_.reason_destroy(bytes_.data()); }
  void *get() noexcept { return bytes_.data(); }
  bool copy(std::string &out) const {
    const auto size = Load<std::uint64_t>(bytes_.data(), 0x10);
    const auto capacity = Load<std::uint64_t>(bytes_.data(), 0x18);
    if (size > capacity) return false;
    const char *text = capacity < 16 ? reinterpret_cast<const char *>(bytes_.data())
                                   : Load<const char *>(bytes_.data());
    if (size && !text) return false;
    if (size == 0) out.clear();
    else out.assign(text, static_cast<std::size_t>(size));
    return true;
  }
  NativeReason(const NativeReason &) = delete;
  NativeReason &operator=(const NativeReason &) = delete;
private:
  alignas(8) std::array<std::byte, 0x20> bytes_{};
  const Bindings &b_;
};

bool CaptureOptions(const Bindings &b, const OwnedActivityConfig &config,
                    std::vector<DefaultOptionTerms> &out) {
  out.clear();
  const auto *rows = Load<const std::byte *>(config.get(), 0x98);
  const auto count = Load<std::int32_t>(config.get(), 0xA4);
  if (count < 0 || (count > 0 && !rows)) return false;
  const void *special = b.selected_special(config.get());
  for (std::int32_t i = 0; i < count; ++i) {
    const auto *row = rows + static_cast<std::size_t>(i) * 0x10;
    const void *category = Load<const void *>(row);
    const void *option = Load<const void *>(row, 8);
    if (!category || !option) return false;
    out.push_back({Load<std::int32_t>(category, 8), Load<std::int32_t>(option, 8),
                   option == special});
  }
  return true;
}
bool CapturePhases(const OwnedActivityConfig &config,
                   std::vector<ConfiguredPhaseTerms> &out) {
  out.clear();
  const auto view = config.phases();
  if (view.count < 0 || (view.count > 0 && !view.data)) return false;
  for (std::int32_t i = 0; i < view.count; ++i) {
    const auto *row = view.data + static_cast<std::size_t>(i) * view.stride;
    ConfiguredPhaseTerms phase{};
    const void *definition = Load<const void *>(row);
    phase.province_id = Load<std::int32_t>(row, 8);
    if (definition) {
      phase.phase_definition_index = Load<std::int32_t>(definition, 8);
      phase.native_default_phase = Load<std::uint8_t>(definition, 0x69C) != 0;
      phase.native_phase_order_raw = Load<std::int32_t>(definition, 0x698);
    }
    out.push_back(std::move(phase));
  }
  return true;
}

bool NativeInsertionIndex(const void *type, factory::PhaseRowView view,
                          std::int32_t &index) noexcept {
  // Exact11B3D80 ordering block, without its planner receiver. The original
  // wrapper is entered only when the type's ordinary-phase array is nonempty.
  const auto count = Load<std::int32_t>(type, 0x98C);
  const auto *ordinary = Load<const void *const *>(type, 0x980);
  if (count <= 0 || !ordinary || !ordinary[0] || view.count < 0 ||
      (view.count > 0 && !view.data)) return false;
  const auto threshold = Load<std::int32_t>(ordinary[0], 0x698);
  index = view.count;
  for (std::int32_t i = 0; i < view.count; ++i) {
    const void *definition = Load<const void *>(
        view.data + static_cast<std::size_t>(i) * view.stride);
    if (definition && Load<std::uint8_t>(definition, 0x69C) != 0 &&
        Load<std::int32_t>(definition, 0x698) > threshold) {
      index = i;
      break;
    }
  }
  return true;
}

bool CaptureActivityQuote(const Bindings &b, OwnedActivityConfig &config,
                          void *actor, ActivityQuoteTerms &out,
                          std::string &failure) {
  if (!CaptureOptions(b, config, out.default_options_used) ||
      !CapturePhases(config, out.configured_phases)) {
    failure = "native_config_readback_unavailable"; return false;
  }
  out.native_config_date_raw = Load<std::int32_t>(config.get(), 0x20);
  out.activity_cost_raw_slots = {};
  b.activity_cost(config.get(), out.activity_cost_raw_slots.data());
  NativeReason reason(b);
  out.affordable = b.activity_affordable(out.activity_cost_raw_slots.data(), actor,
                                       reason.get());
  std::string literal;
  out.affordability_reasons_available = reason.copy(literal);
  if (!out.affordability_reasons_available) {
    failure = "native_activity_affordability_reasons_unavailable"; return false;
  }
  out.affordability_reasons = std::move(literal);
  return true;
}

bool BuildActivityQuote(const Bindings &b, const void *type, void *actor,
                        std::int32_t actor_id, const factory::PhaseChoice &phase,
                        ActivityQuoteTerms &out, std::string &failure) {
  OwnedActivityConfig config(b);
  if (!config.initialize(type, actor_id)) {
    failure = "native_local_config_unavailable"; return false;
  }
  std::int32_t index = 0;
  if (!NativeInsertionIndex(type, config.phases(), index)) {
    failure = "native_phase_insertion_anchor_unavailable"; return false;
  }
  auto *array = static_cast<std::byte *>(config.get()) + 0xB0;
  void *row = b.phase_insert(array, index, type);
  if (!row) { failure = "native_phase_insert_unavailable"; return false; }
  // Only genuine factory offers supply these world-owned definitions/IDs.
  Store<const void *>(row, 0, phase.phase_definition);
  Store<std::int32_t>(row, 8, phase.province_id);
  b.config_normalize(config.get());
  return CaptureActivityQuote(b, config, actor, out, failure);
}

bool BuildDefaultActivityQuote(const Bindings &b, const void *type, void *actor,
    std::int32_t actor_id, std::int32_t province_id,
    ActivityQuoteTerms &out, std::string &failure) {
  // Exact11B4CF0 does not insert a placeholder when ordinary phase count is
  // zero. The genuine single-location caller selects an existing default row.
  if (Load<std::uint8_t>(type, 0x3BED) == 0 || Load<std::int32_t>(type, 0x98C) != 0) {
    failure = "native_default_only_location_configuration_unavailable"; return false;
  }
  OwnedActivityConfig config(b);
  if (!config.initialize(type, actor_id)) {
    failure = "native_local_config_unavailable"; return false;
  }
  const auto view = config.phases();
  if (view.count <= 0 || !view.data) {
    failure = "native_default_pickable_phase_unavailable"; return false;
  }
  void *selected = nullptr;
  for (std::int32_t i = 0; i < view.count; ++i) {
    auto *row = const_cast<std::byte *>(view.data) + static_cast<std::size_t>(i) * view.stride;
    const void *definition = Load<const void *>(row);
    // Exact11B5950 skips only predefined rows whose location source is not
    // pickable. Retain its first-row ordering rather than choosing by an ID.
    if (definition && Load<std::int32_t>(definition, 0x1160) != 0 &&
        Load<std::uint8_t>(definition, 0x69C) != 0) continue;
    if (!definition || Load<std::uint8_t>(definition, 0x69C) == 0 ||
        Load<std::int32_t>(definition, 0x1160) != 0) {
      failure = "native_default_pickable_phase_unavailable"; return false;
    }
    selected = row;
    break;
  }
  if (!selected) { failure = "native_default_pickable_phase_unavailable"; return false; }
  // Exact11B6C80 writes the already selected row+8, then23FC580 propagates
  // native single-location defaults. No ordinary offer or new phase is made.
  Store<std::int32_t>(selected, 8, province_id);
  b.config_normalize(config.get());
  return CaptureActivityQuote(b, config, actor, out, failure);
}

PredicateTerms CopyPredicate(const factory::PredicateResult &value) {
  PredicateTerms result{value.value, value.reasons_available, std::nullopt};
  if (value.reasons_available) result.reasons = value.reasons;
  return result;
}

std::string Quote(std::string_view text) {
  static constexpr char hex[] = "0123456789abcdef";
  std::string result = "\"";
  for (const unsigned char byte : text) {
    if (byte == '"' || byte == '\\') { result += '\\'; result += static_cast<char>(byte); }
    else if (byte < 0x20) { result += "\\u00"; result += hex[byte >> 4]; result += hex[byte & 15]; }
    else result += static_cast<char>(byte);
  }
  return result + '"';
}
template <typename T>
void WriteOptional(std::ostringstream &out, const std::optional<T> &value) {
  if (value) out << *value;
  else out << "null";
}
void WriteOptional(std::ostringstream &out, const std::optional<std::string> &value) {
  if (value) out << Quote(*value);
  else out << "null";
}
void WritePredicate(std::ostringstream &out, const PredicateTerms &value) {
  out << "{\"value\":" << value.value
      << ",\"reasons_available\":" << value.reasons_available << ",\"reasons\":";
  WriteOptional(out, value.reasons);
  out << '}';
}
void WriteOptions(std::ostringstream &out, const std::vector<DefaultOptionTerms> &options) {
  out << '[';
  bool first = true;
  for (const auto &option : options) {
    if (!first) out << ',';
    first = false;
    out << "{\"category_definition_index\":" << option.category_definition_index
        << ",\"option_definition_index\":" << option.option_definition_index
        << ",\"selected_special\":" << option.selected_special << '}';
  }
  out << ']';
}
void WritePhases(std::ostringstream &out, const std::vector<ConfiguredPhaseTerms> &phases) {
  out << '[';
  bool first = true;
  for (const auto &phase : phases) {
    if (!first) out << ',';
    first = false;
    out << "{\"phase_definition_index\":";
    WriteOptional(out, phase.phase_definition_index);
    out << ",\"province_id\":" << phase.province_id << ",\"native_default_phase\":";
    WriteOptional(out, phase.native_default_phase);
    out << ",\"native_phase_order_raw\":";
    WriteOptional(out, phase.native_phase_order_raw);
    out << '}';
  }
  out << ']';
}
void WriteActivityQuote(std::ostringstream &out, const ActivityQuoteTerms &quote) {
  out << "{\"native_config_date_raw\":" << quote.native_config_date_raw
      << ",\"quote_scope\":" << Quote(kQuoteScope)
      << ",\"journey_cost_included\":false,\"activity_cost_raw_slots\":[";
  for (std::size_t i = 0; i < quote.activity_cost_raw_slots.size(); ++i) {
    if (i != 0) out << ',';
    out << quote.activity_cost_raw_slots[i];
  }
  out << "],\"activity_gold_cost_raw\":" << quote.activity_cost_raw_slots[0]
      << ",\"activity_treasury_cost_raw\":" << quote.activity_cost_raw_slots[6]
      << ",\"gold_treasury_scale\":" << Terms::gold_treasury_scale
      << ",\"affordable\":" << quote.affordable
      << ",\"affordability_reasons_available\":" << quote.affordability_reasons_available
      << ",\"affordability_reasons\":";
  WriteOptional(out, quote.affordability_reasons);
  out << ",\"default_options_used\":";
  WriteOptions(out, quote.default_options_used);
  out << ",\"configured_phases\":";
  WritePhases(out, quote.configured_phases);
  out << '}';
}
} // namespace

Bindings BindPlayerPilgrimageActivityTermsImage12003(
    std::uintptr_t base, std::string_view sha) noexcept {
  Bindings b{};
  if (base == 0 || sha != kExecutableSha256) return b;
  b.activity_type = pilgrimage::BindPlayerPilgrimageActivityTypeTermsImage12003(base, sha);
  b.candidates = factory::BindPlayerPilgrimageCandidateFactoryImage12003(base, sha);
  b.config_initialize = reinterpret_cast<ConfigInitialize>(base + 0x23FB450);
  b.selected_special = reinterpret_cast<SelectedSpecial>(base + 0x23FC800);
  b.phase_insert = reinterpret_cast<PhaseInsert>(base + 0x11BF720);
  b.config_normalize = reinterpret_cast<ConfigNormalize>(base + 0x23FC580);
  b.activity_cost = reinterpret_cast<ActivityCost>(base + 0x2BBE710);
  b.activity_affordable = reinterpret_cast<ActivityAffordable>(base + 0x310E710);
  b.config_destroy = reinterpret_cast<Destroy>(base + 0x11B3100);
  b.reason_destroy = reinterpret_cast<Destroy>(base + 0x856050);
  b.enabled = b.activity_type.enabled && b.candidates.enabled;
  return b;
}

bool ReadPlayerPilgrimageActivityTerms12003(const Bindings &b, void *actor,
    const ck3_12002::religion::Context &context, Terms &out) noexcept {
  out = {};
  out.capture_epoch = context.capture_epoch;
  out.date_raw = context.date_raw;
  out.played_character_id = context.played_character_id;
  if (!b.enabled || !b.activity_type.enabled || !b.activity_type.activity_type_database ||
      !b.activity_type.activity_type_vtable || !b.config_initialize ||
      !b.selected_special || !b.phase_insert || !b.config_normalize ||
      !b.activity_cost || !b.activity_affordable || !b.config_destroy || !b.reason_destroy)
    return false;
  if (!actor || context.played_character_id <= 0 ||
      Load<std::int32_t>(actor, 0x18) != context.played_character_id) {
    out.unavailable_reason = "played_character_unavailable"; return false;
  }
  try {
    const void *type = FindPilgrimage(b.activity_type);
    if (!type) { out.unavailable_reason = "activity_type_definition_unavailable"; return false; }
    OwnedActivityConfig baseline(b);
    if (!baseline.initialize(type, context.played_character_id)) {
      out.unavailable_reason = "native_local_config_unavailable"; return false;
    }
    const void *special = b.selected_special(baseline.get());
    if (special) out.selected_special_definition_index = Load<std::int32_t>(special, 8);
    if (!CaptureOptions(b, baseline, out.default_options) ||
        !CapturePhases(baseline, out.initial_configured_phases)) {
      out.unavailable_reason = "native_config_readback_unavailable"; return false;
    }
    factory::Candidates candidates;
    if (!factory::CollectPlayerPilgrimageCandidates12003(b.candidates, actor,
          context.played_character_id, type, special, baseline.phases(), candidates)) {
      out.unavailable_reason = candidates.unavailable_reason; return false;
    }
    out.rite_id = candidates.rite_id; out.faith_id = candidates.faith_id;
    out.native_filter = candidates.native_filter;
    out.configured_phase_count = candidates.configured_phase_count;
    out.total_phase_cap = candidates.total_phase_cap;
    out.single_location = candidates.single_location;
    out.resolved_location_phase_count = candidates.resolved_location_phase_count;
    bool all_quotes_available = true;
    for (const auto &candidate : candidates.candidates) {
      CandidateTerms result;
      result.holy_site_id = candidate.holy_site_id; result.title_id = candidate.title_id;
      result.province_id = candidate.province_id;
      result.location_predicate = CopyPredicate(candidate.location_predicate);
      result.same_province_phase_count = candidate.same_province_phase_count;
      result.same_province_cap_applies = candidate.same_province_cap_applies;
      result.same_province_phase_cap = candidate.same_province_phase_cap;
      result.same_province_cap_allows = candidate.same_province_cap_allows;
      result.total_cap_applies = candidate.total_cap_applies;
      result.total_cap_allows = candidate.total_cap_allows;
      result.can_select = candidate.can_select;
      if (!candidate.phase_choices.empty()) {
        result.default_quote_unavailable_reason = "native_optional_phase_choices_present";
      } else if (!candidate.can_select || !*candidate.can_select) {
        result.default_quote_unavailable_reason = "native_destination_not_selectable";
      } else {
        ActivityQuoteTerms quote;
        std::string failure;
        if (BuildDefaultActivityQuote(b, type, actor, context.played_character_id,
              candidate.province_id, quote, failure)) result.default_activity_quote = std::move(quote);
        else {
          result.default_quote_unavailable_reason = std::move(failure);
          all_quotes_available = false;
        }
      }
      for (const auto &choice : candidate.phase_choices) {
        PhaseTerms phase;
        phase.phase_definition_index = choice.phase_definition_index;
        phase.province_id = choice.province_id;
        phase.native_ai_choice_score_raw = choice.native_ai_choice_score;
        phase.shown = CopyPredicate(choice.shown); phase.location = CopyPredicate(choice.location);
        phase.can_select_phase = choice.can_select;
        if (!candidate.can_select || !*candidate.can_select) {
          phase.quote_unavailable_reason = "native_destination_not_selectable";
        } else if (!choice.can_select) {
          phase.quote_unavailable_reason = "native_phase_not_selectable";
        } else {
          ActivityQuoteTerms quote;
          std::string failure;
          if (BuildActivityQuote(b, type, actor, context.played_character_id, choice,
                                 quote, failure)) phase.activity_quote = std::move(quote);
          else {
            phase.quote_unavailable_reason = std::move(failure);
            all_quotes_available = false;
          }
        }
        result.phase_choices.push_back(std::move(phase));
      }
      out.candidates.push_back(std::move(result));
    }
    out.available = all_quotes_available;
    out.unavailable_reason = all_quotes_available ? "" : "native_activity_quote_unavailable";
    return out.available;
  } catch (...) {
    out.unavailable_reason = "native_activity_terms_exception"; return false;
  }
}

std::string SerializePlayerPilgrimageActivityTerms12003(const Terms &t) {
  std::ostringstream out;
  out << std::boolalpha << "{\"schema\":" << Quote(kSchema)
      << ",\"read_only\":true,\"available\":" << t.available
      << ",\"unavailable_reason\":" << (t.available ? "null" : Quote(t.unavailable_reason))
      << ",\"capture_epoch\":" << t.capture_epoch << ",\"date_raw\":" << t.date_raw
      << ",\"played_character_id\":" << t.played_character_id
      << ",\"activity_id\":" << Quote(kActivityId) << ",\"quote_scope\":" << Quote(kQuoteScope)
      << ",\"journey_cost_included\":false,\"default_options_provenance\":\"native_actual_actor_default\""
      << ",\"phase_choice_provenance\":\"native_mode1_offers_independent_predicates\""
      << ",\"rite_id\":";
  WriteOptional(out, t.rite_id);
  out << ",\"faith_id\":"; WriteOptional(out, t.faith_id);
  out << ",\"native_filter\":"; WriteOptional(out, t.native_filter);
  out << ",\"configured_phase_count\":"; WriteOptional(out, t.configured_phase_count);
  out << ",\"total_phase_cap\":"; WriteOptional(out, t.total_phase_cap);
  out << ",\"single_location\":"; WriteOptional(out, t.single_location);
  out << ",\"resolved_location_phase_count\":"; WriteOptional(out, t.resolved_location_phase_count);
  out << ",\"selected_special_definition_index\":"; WriteOptional(out, t.selected_special_definition_index);
  out << ",\"default_options\":"; WriteOptions(out, t.default_options);
  out << ",\"initial_configured_phases\":"; WritePhases(out, t.initial_configured_phases);
  out << ",\"candidates\":[";
  bool first_candidate = true;
  for (const auto &candidate : t.candidates) {
    if (!first_candidate) out << ',';
    first_candidate = false;
    out << "{\"holy_site_id\":" << candidate.holy_site_id
        << ",\"title_id\":" << candidate.title_id << ",\"province_id\":" << candidate.province_id
        << ",\"location_predicate\":";
    WritePredicate(out, candidate.location_predicate);
    out << ",\"same_province_phase_count\":" << candidate.same_province_phase_count
        << ",\"same_province_cap_applies\":" << candidate.same_province_cap_applies
        << ",\"same_province_phase_cap\":"; WriteOptional(out, candidate.same_province_phase_cap);
    out << ",\"same_province_cap_allows\":" << candidate.same_province_cap_allows
        << ",\"total_cap_applies\":" << candidate.total_cap_applies
        << ",\"total_cap_allows\":"; WriteOptional(out, candidate.total_cap_allows);
    out << ",\"can_select\":"; WriteOptional(out, candidate.can_select);
    out << ",\"default_quote_unavailable_reason\":";
    WriteOptional(out, candidate.default_quote_unavailable_reason);
    out << ",\"default_activity_quote\":";
    if (candidate.default_activity_quote) WriteActivityQuote(out, *candidate.default_activity_quote);
    else out << "null";
    out << ",\"phase_choices\":[";
    bool first_phase = true;
    for (const auto &phase : candidate.phase_choices) {
      if (!first_phase) out << ',';
      first_phase = false;
      out << "{\"phase_definition_index\":" << phase.phase_definition_index
          << ",\"province_id\":" << phase.province_id
          << ",\"native_ai_choice_score_raw\":" << phase.native_ai_choice_score_raw
          << ",\"shown\":"; WritePredicate(out, phase.shown);
      out << ",\"location\":"; WritePredicate(out, phase.location);
      out << ",\"can_select_phase\":" << phase.can_select_phase
          << ",\"quote_unavailable_reason\":"; WriteOptional(out, phase.quote_unavailable_reason);
      out << ",\"activity_quote\":";
      if (phase.activity_quote) WriteActivityQuote(out, *phase.activity_quote);
      else out << "null";
      out << '}';
    }
    out << "]}";
  }
  out << "]}";
  return out.str();
}

} // namespace xar::ck3_12003::religion::pilgrimage_activity_terms
