#include "xar_bridge/conception_secondary_context_12004.hpp"
#include "xar_bridge/ck3_12004.hpp"

extern "C" __declspec(dllexport) int ReadSecondaryContextFixture(
    std::uintptr_t base, std::uintptr_t character, std::uint32_t full_id,
    xar::ck3_12004::ConceptionSecondaryContext12004ReadMemory copy,
    void *context, std::int32_t *raw, int *predicate, std::uint32_t *fallbacks) {
  using namespace xar::ck3_12004;
  const auto binding = BindConceptionSecondaryContext12004(
      kGameVersion, kExecutableSha256, base, copy, context);
  const auto value = ReadConceptionSecondaryContextForCharacter12004(
      binding, character, full_id);
  *predicate = value.selects_alternate_relation_path.has_value() ?
      (*value.selects_alternate_relation_path ? 1 : 0) : -1;
  *raw = value.context_7d8_raw_i32.value_or(0);
  *fallbacks = 0;
  for (std::size_t i = 0; i < value.resolution.size(); ++i)
    if (value.resolution[i].status == "native_fallback") *fallbacks |= 1U << i;
  return value.status == "available" ? 1 : 0;
}

extern "C" __declspec(dllexport) int SelectSecondaryContextFixture(
    int first, int second) {
  using namespace xar::ck3_12004;
  const auto value = SelectConceptionSecondaryRelationPath12004(
      first < 0 ? std::nullopt : std::optional<bool>{first != 0},
      second < 0 ? std::nullopt : std::optional<bool>{second != 0});
  return value.has_value() ? (*value ? 1 : 0) : -1;
}
