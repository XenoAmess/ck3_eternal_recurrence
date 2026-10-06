#include "xar_bridge/ck3_12003_mercenary_position.hpp"

namespace xar::ck3_12003 {
namespace {
template <class T> bool ReadAt(const MercenaryPositionWorldV1 &world,
    const void *object, std::size_t offset, T &value) noexcept {
  return object != nullptr && world.read_memory != nullptr &&
      world.read_memory(world.context,
          static_cast<const std::byte *>(object) + offset, &value, sizeof(value));
}
bool ProvinceIdentity(const MercenaryPositionWorldV1 &world,
    const void *province, std::int32_t &id) noexcept {
  std::uint32_t tag = 0;
  return ReadAt(world, province, 0x85C, tag) && tag == 0x50726F76 &&
      ReadAt(world, province, 0x10, id) && id > 0 &&
      world.resolve_province != nullptr &&
      world.resolve_province(world.context, id) == province;
}
} // namespace

bool ReadMercenaryPositionV1(const MercenaryPositionBindingsV1 &bindings,
    const MercenaryPositionWorldV1 &world, const void *actor,
    const void *company, MercenaryPositionObservationV1 &output) noexcept {
  output = {};
  std::uint32_t company_tag = 0;
  if (actor == nullptr || company == nullptr || world.read_memory == nullptr ||
      !ReadAt(world, company, 0x14, company_tag) || company_tag != 0x4D657263) {
    output.company_home_failure = "actor_or_company_unavailable";
    output.hire_auto_raise_position_failure = "actor_or_company_unavailable";
    return false;
  }
  std::int32_t title_id = -1;
  if (!ReadAt(world, company, 0x24, title_id) || title_id == -1 ||
      world.resolve_title == nullptr || bindings.get_title_province == nullptr) {
    output.company_home_failure = "company_title_unavailable";
  } else {
    output.company_home_title_id = title_id;
    const void *title = world.resolve_title(world.context, title_id);
    std::int32_t identity = -1;
    if (!ReadAt(world, title, 0x10, identity) || identity != title_id) {
      output.company_home_failure = "company_title_unavailable";
    } else {
      const void *province = bindings.get_title_province(title);
      std::int32_t province_id = -1;
      if (!ProvinceIdentity(world, province, province_id)) {
        output.company_home_failure = "company_home_province_unavailable";
      } else {
        output.company_home_province_id = province_id;
        output.company_home_ready = true;
        output.company_home_failure = "none";
      }
    }
  }
  const void *realm = nullptr;
  std::int32_t war_count = 0;
  if (!ReadAt(world, actor, 0x1C0, realm) || realm == nullptr ||
      !ReadAt(world, realm, 0x324, war_count) || war_count < 0 ||
      bindings.select_hire_raise_province == nullptr ||
      world.resolve_province == nullptr) {
    output.hire_auto_raise_position_failure = "actor_hire_raise_inputs_unavailable";
    return false;
  }
  // Active wars are realm+0x318 vector, whose count is vector+0x0C.
  output.actor_active_war_count = war_count;
  output.hire_auto_raise_attempted_in_active_war = war_count > 0;
  if (war_count == 0 && bindings.skip_selector_when_no_active_wars) {
    output.hire_auto_raise_position_ready = true;
    output.hire_auto_raise_position_failure = "none";
    return output.company_home_ready;
  }
  const auto selected_id = bindings.select_hire_raise_province(actor);
  const void *province = world.resolve_province(world.context, selected_id);
  std::int32_t identity = -1;
  if (selected_id <= 0 || !ProvinceIdentity(world, province, identity) ||
      identity != selected_id) {
    output.hire_auto_raise_position_failure = "native_hire_raise_province_unavailable";
    return false;
  }
  output.hire_auto_raise_province_id = selected_id;
  output.hire_auto_raise_position_ready = true;
  output.hire_auto_raise_position_failure = "none";
  return output.company_home_ready;
}
} // namespace xar::ck3_12003
