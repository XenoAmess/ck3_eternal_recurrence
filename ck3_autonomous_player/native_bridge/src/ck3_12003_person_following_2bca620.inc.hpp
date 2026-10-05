// Included after AfterPc/AfterFinish physical helpers. Only the source-closed
// nonnegative-balance classifier branch is implemented in this minimum.
game::ContextSourceFollowing2bca620BalanceV1 Following2bca620Balance(
    const ContextSourceBindingsV1 &b, const void *character) {
  game::ContextSourceFollowing2bca620BalanceV1 out{};
  const auto component = Read<const void *>(b, character, 0x1B0);
  if (!component) { out.reason = "following2bca620_balance_component_unavailable"; return out; }
  out.component_present = *component != nullptr;
  if (!*component) out.numeric_balance_q64 = 0;
  else {
    out.balance_raw_q64 = Read<std::int64_t>(b, *component, 0x100);
    out.numeric_balance_q64 = out.balance_raw_q64;
    if (!out.balance_raw_q64) out.reason = "following2bca620_balance_unavailable";
  }
  return out;
}
game::ContextSourceFollowing2bca620ClassifierV1 Following2bca620Classifier(
    const game::ContextSourceFollowing2bca620BalanceV1 &balance) {
  game::ContextSourceFollowing2bca620ClassifierV1 out{};
  if (!balance.numeric_balance_q64) out.reason = balance.reason;
  else if (*balance.numeric_balance_q64 < 0) {
    out.selection = "negative_balance_income_unobserved";
    out.reason = "negative_balance_income_2bca4e0";
  } else {
    out.selection = "nonnegative_balance_minus_one";
    out.index_raw_i32 = -1;
  }
  AfterFinish(out);
  return out;
}
game::ContextSourceFollowing2bca620ProviderV1 Following2bca620Provider(
    const ContextSourceBindingsV1 &b, const std::optional<const void *> &provider,
    const game::ContextSourceFollowing2bca620ClassifierV1 &classifier) {
  game::ContextSourceFollowing2bca620ProviderV1 out{};
  if (provider) out.provider_loaded = *provider != nullptr;
  const auto fail = [&](const char *reason) {
    out.reason = reason; AfterFinish(out); return out;
  };
  if (!classifier.ready) return fail(classifier.reason.c_str());
  if (!provider || !*provider) return fail("following2bca620_loaded_provider_unavailable");
  out.count_raw = Read<std::int32_t>(b, *provider, 0x126C);
  if (!out.count_raw) return fail("following2bca620_provider_count_unavailable");
  std::optional<const void *> selected;
  // Equality with the signed sentinel count precedes the negative-index
  // fallback. The indexed1260 branch is unreachable in this minimum.
  if (*classifier.index_raw_i32 == *out.count_raw) {
    out.selection = "provider_1690_equality_sentinel";
    selected = Read<const void *>(b, *provider, 0x1690);
  } else {
    out.selection = "global_fallback_5d1e0b0";
    selected = Read<const void *>(b, b.following_2bca620.provider_fallback_slot);
  }
  if (!selected || !*selected) return fail("following2bca620_selected_definition_unavailable");
  out.definition_identity = TraitStageIdentity(*selected);
  out.definition_magic_u32 = Read<std::uint32_t>(b, *selected, 0x38);
  if (!out.definition_magic_u32) return fail("following2bca620_definition_magic_unavailable");
  out.admitted = *out.definition_magic_u32 == 0x4744624FU;
  if (*out.admitted) {
    out.pc = AfterPc(b, Offset(*selected, 0x40));
    out.reason = out.pc.reason;
  }
  AfterFinish(out);
  return out;
}
game::ContextSourceFollowing2bca620InputsV1 Following2bca620Inputs(
    const ContextSourceBindingsV1 &b, const void *character, std::int32_t id) {
  game::ContextSourceFollowing2bca620InputsV1 out{};
  out.character_id = id;
  // The caller snapshots this loaded provider before the classifier. No
  // native getter, initializer, income producer or cached2B0 is invoked.
  const auto provider = Read<const void *>(b, b.following_2bca620.provider_slot);
  out.balance_source = Following2bca620Balance(b, character);
  out.classifier = Following2bca620Classifier(out.balance_source);
  out.provider_selection = Following2bca620Provider(b, provider, out.classifier);
  if (!out.classifier.ready) out.reason = out.classifier.reason;
  else if (!out.provider_selection.ready) out.reason = out.provider_selection.reason;
  AfterFinish(out);
  return out;
}
