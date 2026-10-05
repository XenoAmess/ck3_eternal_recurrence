// Included inside the current-person collector anonymous namespace after the
// paired Properties reader. No native predicate, initializer or append is called.
using Qualifier28bc0d0InputsV1 = game::ContextSourceQualifier28bc0d0InputsV1;
struct Qualifier28bc0d0ReadState {
  bool fallback_sampled = false;
};
const void *Qualifier28bc0d0Pointer(std::uint64_t value) noexcept {
  return reinterpret_cast<const void *>(static_cast<std::uintptr_t>(value));
}
std::optional<bool> Qualifier28bc0d0Candidate(
    const ContextSourceBindingsV1 &b, const void *candidate,
    std::uint64_t requested, Qualifier28bc0d0InputsV1 &out,
    Qualifier28bc0d0ReadState &state,
    game::ContextSourceQualifier28bc0d0CandidateV1 &row,
    std::string &reason) {
  row.definition_object = Read<std::uint64_t>(b, candidate);
  if (!row.definition_object) {
    Reason(reason, "qualifier_candidate_definition_unavailable");
    return std::nullopt;
  }
  // 25942D0 direct pointer equality returns before the relationship header.
  if (*row.definition_object == requested) return true;
  const auto *definition = Qualifier28bc0d0Pointer(*row.definition_object);
  const auto data = Read<const void *>(b, definition, 0x220);
  if (data) row.relationship_array_present = *data != nullptr;
  row.relationship_count_raw_i32 = Read<std::int32_t>(b, definition, 0x22C);
  if (!data || !row.relationship_count_raw_i32) {
    Reason(reason, "qualifier_relationship_header_unavailable");
    return std::nullopt;
  }
  if (*row.relationship_count_raw_i32 < 0) {
    Reason(reason, "qualifier_negative_relationship_count_unrepresentable");
    return std::nullopt;
  }
  row.relationships.emplace();
  if (*row.relationship_count_raw_i32 == 0) return false;
  if (!*data) {
    Reason(reason, "qualifier_positive_relationship_count_null_array");
    return std::nullopt;
  }
  // 25942F2 prefetches the actual global before the first relationship. An
  // unread prefetch is only a readiness dependency if a non2 marker uses it.
  if (!state.fallback_sampled) {
    out.fallback_definition_object = Read<std::uint64_t>(
        b, b.qualifier_28bc0d0.fallback_definition_slot);
    state.fallback_sampled = true;
  }
  for (std::int32_t i = 0; i < *row.relationship_count_raw_i32; ++i) {
    game::ContextSourceQualifier28bc0d0RelationshipV1 relation{};
    relation.native_index = static_cast<std::uint32_t>(i);
    const auto *source = Offset(*data, static_cast<std::size_t>(i) * 16);
    relation.marker_u8 = Read<std::uint8_t>(b, source, 0xC);
    if (!relation.marker_u8) {
      row.relationships->push_back(std::move(relation));
      Reason(reason, "qualifier_relationship_marker_unavailable");
      return std::nullopt;
    }
    std::optional<std::uint64_t> effective;
    if (*relation.marker_u8 == 2) {
      relation.definition_object = Read<std::uint64_t>(b, source);
      effective = relation.definition_object;
    } else {
      effective = out.fallback_definition_object;
    }
    row.relationships->push_back(std::move(relation));
    if (!effective) {
      Reason(reason, "qualifier_relationship_effective_definition_unavailable");
      return std::nullopt;
    }
    if (*effective == requested) return true;
  }
  return false;
}
std::optional<bool> Qualifier28bc0d0Evaluate(
    const ContextSourceBindingsV1 &b, const void *scratch_row,
    std::uint64_t requested, Qualifier28bc0d0InputsV1 &out,
    Qualifier28bc0d0ReadState &state,
    game::ContextSourceQualifier28bc0d0EvaluationV1 &evaluation,
    std::string &reason) {
  evaluation.object = Read<std::uint64_t>(b, scratch_row, 8);
  if (!evaluation.object) {
    Reason(reason, "qualifier_scratch_object_unavailable");
    return std::nullopt;
  }
  const auto *object = Qualifier28bc0d0Pointer(*evaluation.object);
  // 2596950 consumes +20 before +2C even when the count is zero.
  const auto data = Read<const void *>(b, object, 0x20);
  if (data) evaluation.candidate_array_present = *data != nullptr;
  evaluation.candidate_count_raw_i32 = Read<std::int32_t>(b, object, 0x2C);
  if (!data || !evaluation.candidate_count_raw_i32) {
    Reason(reason, "qualifier_candidate_header_unavailable");
    return std::nullopt;
  }
  if (*evaluation.candidate_count_raw_i32 < 0) {
    Reason(reason, "qualifier_negative_candidate_count_unrepresentable");
    return std::nullopt;
  }
  evaluation.candidates.emplace();
  if (*evaluation.candidate_count_raw_i32 == 0) return false;
  if (!*data) {
    Reason(reason, "qualifier_positive_candidate_count_null_array");
    return std::nullopt;
  }
  for (std::int32_t i = 0; i < *evaluation.candidate_count_raw_i32; ++i) {
    game::ContextSourceQualifier28bc0d0CandidateV1 row{};
    row.native_index = static_cast<std::uint32_t>(i);
    const auto accepted = Qualifier28bc0d0Candidate(b,
        Offset(*data, static_cast<std::size_t>(i) * 40), requested, out,
        state, row, reason);
    evaluation.candidates->push_back(std::move(row));
    if (!accepted) return std::nullopt;
    if (*accepted) return true;
  }
  return false;
}
Qualifier28bc0d0InputsV1 Qualifier28bc0d0Inputs(
    const ContextSourceBindingsV1 &b, const void *character,
    std::int32_t character_id) {
  Qualifier28bc0d0InputsV1 out{};
  out.character_id = character_id;
  out.manager_object = Read<std::uint64_t>(b, b.qualifier_28bc0d0.manager_slot);
  if (!out.manager_object || *out.manager_object == 0) {
    out.reason = out.manager_object ? "qualifier_manager_uninitialized"
                                   : "qualifier_manager_pointer_unavailable";
    return out;
  }
  const auto *manager = Qualifier28bc0d0Pointer(*out.manager_object);
  const auto definitions = Read<const void *>(b, manager, 0x50);
  if (definitions) out.definition_array_present = *definitions != nullptr;
  out.definition_count_raw_i32 = Read<std::int32_t>(b, manager, 0x5C);
  if (!definitions || !out.definition_count_raw_i32) {
    out.reason = "qualifier_definition_header_unavailable";
    return out;
  }
  if (*out.definition_count_raw_i32 < 0) {
    out.reason = "qualifier_negative_definition_count_unrepresentable";
    return out;
  }
  out.definitions.emplace();
  if (*out.definition_count_raw_i32 == 0) {
    out.ready = true;
    out.status = "available";
    return out;
  }
  if (!*definitions) {
    out.reason = "qualifier_positive_definition_count_null_array";
    return out;
  }
  bool scratch_sampled = false;
  std::optional<const void *> scratch;
  std::optional<const void *> scratch_data;
  Qualifier28bc0d0ReadState state{};
  bool all_ready = true;
  for (std::int32_t i = 0; i < *out.definition_count_raw_i32; ++i) {
    game::ContextSourceQualifier28bc0d0DefinitionV1 row{};
    row.native_index = static_cast<std::uint32_t>(i);
    row.definition_object = Read<std::uint64_t>(
        b, *definitions, static_cast<std::size_t>(i) * 8);
    if (row.definition_object && !scratch_sampled) {
      scratch = Read<const void *>(b, character, 0x1B0);
      if (scratch) out.scratch_present = *scratch != nullptr;
      if (scratch && *scratch) {
        out.scratch_count_raw_i32 = Read<std::int32_t>(b, *scratch, 0x14);
        if (out.scratch_count_raw_i32 && *out.scratch_count_raw_i32 > 0)
          scratch_data = Read<const void *>(b, *scratch, 8);
      }
      scratch_sampled = true;
    }
    bool count_ready = true;
    if (!row.definition_object) {
      row.reason = "qualifier_requested_definition_unavailable";
      count_ready = false;
    } else if (!scratch) {
      row.reason = "qualifier_scratch_pointer_unavailable";
      count_ready = false;
    } else if (*scratch && !out.scratch_count_raw_i32) {
      row.reason = "qualifier_scratch_count_unavailable";
      count_ready = false;
    } else if (*scratch && *out.scratch_count_raw_i32 > 0 &&
               (!scratch_data || !*scratch_data)) {
      row.reason = "qualifier_scratch_array_unavailable";
      count_ready = false;
    }
    std::vector<std::uint32_t> accepted_ids;
    if (count_ready) {
      row.scratch_evaluations.emplace();
      if (*scratch && *out.scratch_count_raw_i32 > 0) {
        for (std::int32_t j = 0; j < *out.scratch_count_raw_i32; ++j) {
          game::ContextSourceQualifier28bc0d0EvaluationV1 evaluation{};
          evaluation.native_index = static_cast<std::uint32_t>(j);
          const auto *source = Offset(*scratch_data,
              static_cast<std::size_t>(j) * 16);
          const auto accepted = Qualifier28bc0d0Evaluate(b, source,
              *row.definition_object, out, state, evaluation, row.reason);
          if (!accepted) count_ready = false;
          else if (*accepted) {
            evaluation.id_u32 = Read<std::uint32_t>(b, source);
            if (!evaluation.id_u32) {
              Reason(row.reason, "qualifier_accepted_id_unavailable");
              count_ready = false;
            } else if (*evaluation.id_u32 != 0xFFFFFFFFU &&
                std::find(accepted_ids.begin(), accepted_ids.end(),
                    *evaluation.id_u32) == accepted_ids.end()) {
              accepted_ids.push_back(*evaluation.id_u32);
            }
          }
          row.scratch_evaluations->push_back(std::move(evaluation));
          if (!count_ready) break;
        }
      }
    }
    if (count_ready) {
      row.accepted_ids_u32 = std::move(accepted_ids);
      row.repeat_count = static_cast<std::int32_t>(row.accepted_ids_u32->size());
      row.ready = true;
      if (*row.repeat_count > 0) {
        row.properties = Properties(b,
            Offset(Qualifier28bc0d0Pointer(*row.definition_object), 0x40));
        row.ready = PropertiesReady(*row.properties);
        if (!row.ready) Reason(row.reason, "qualifier_consumed_properties_unavailable");
      }
    }
    if (!row.ready) {
      all_ready = false;
      Reason(out.reason, row.reason.c_str());
    }
    out.definitions->push_back(std::move(row));
  }
  out.ready = all_ready;
  out.status = all_ready ? "available" : "partial";
  return out;
}
