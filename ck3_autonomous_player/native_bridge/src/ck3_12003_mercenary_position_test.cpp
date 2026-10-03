#include "xar_bridge/ck3_12003_mercenary_position.hpp"
#include <array>
#include <cstring>
#include <iostream>
#include <stdexcept>
using namespace xar::ck3_12003;
namespace {
struct Scene {
  std::array<std::byte, 0x200> actor{}, company{}, title{};
  std::array<std::byte, 0x400> realm{};
  std::array<std::byte, 0x900> home{}, raised{};
  std::int32_t selected = 2641;
  int selector_calls = 0;
};
Scene *scene = nullptr;
template <class T, std::size_t N> void Store(std::array<std::byte, N> &o,
    std::size_t offset, T value) {
  std::memcpy(o.data() + offset, &value, sizeof(value));
}
void Require(bool value, const char *reason) {
  if (!value) throw std::runtime_error(reason);
}
bool Read(void *, const void *p, void *out, std::size_t n) {
  if (p == nullptr) return false;
  std::memcpy(out, p, n);
  return true;
}
const void *Title(void *opaque, std::int32_t id) {
  return id == 16777260 ? static_cast<Scene *>(opaque)->title.data() : nullptr;
}
const void *Province(void *opaque, std::int32_t id) {
  auto &s = *static_cast<Scene *>(opaque);
  if (id == 2700) return s.home.data();
  return id == 2641 ? s.raised.data() : nullptr;
}
const void *Home(const void *title) {
  Require(title == scene->title.data(), "resolved company title not used");
  return scene->home.data();
}
std::int32_t Select(const void *actor) {
  Require(actor == scene->actor.data(), "selector did not receive actual actor");
  ++scene->selector_calls;
  return scene->selected;
}
} // namespace
int main() {
  try {
    Scene s;
    scene = &s;
    Store(s.company, 0x14, std::uint32_t{0x4D657263});
    Store(s.company, 0x24, std::int32_t{16777260});
    Store(s.title, 0x10, std::int32_t{16777260});
    Store(s.actor, 0x1C0, static_cast<const void *>(s.realm.data()));
    Store(s.realm, 0x324, std::int32_t{3});
    Store(s.home, 0x10, std::int32_t{2700});
    Store(s.home, 0x85C, std::uint32_t{0x50726F76});
    Store(s.raised, 0x10, std::int32_t{2641});
    Store(s.raised, 0x85C, std::uint32_t{0x50726F76});
    const MercenaryPositionBindingsV1 b{&Home, &Select};
    const MercenaryPositionWorldV1 w{&s, &Read, &Title, &Province};
    MercenaryPositionObservationV1 o;
    Require(ReadMercenaryPositionV1(b, w, s.actor.data(), s.company.data(), o),
        "current-war location reader failed");
    Require(o.company_home_province_id == 2700 && o.hire_auto_raise_province_id == 2641,
        "company home replaced actual spawn selector");
    Require(o.hire_auto_raise_attempted_in_active_war == true &&
        o.actor_active_war_count == 3 && s.selector_calls == 1,
        "native auto-raise active-war branch missing");
    Store(s.realm, 0x324, std::int32_t{0});
    Require(ReadMercenaryPositionV1(b, w, s.actor.data(), s.company.data(), o) &&
        o.hire_auto_raise_attempted_in_active_war == false &&
        o.hire_auto_raise_province_id == 2641,
        "peace frame lost native selection or fabricated auto-raise");
    s.selected = -1;
    Require(!ReadMercenaryPositionV1(b, w, s.actor.data(), s.company.data(), o) &&
        !o.hire_auto_raise_position_ready && !o.hire_auto_raise_province_id &&
        o.company_home_ready, "unavailable selection replaced with company home");
    s.selected = 2641;
    Store(s.company, 0x24, std::int32_t{-1});
    Require(!ReadMercenaryPositionV1(b, w, s.actor.data(), s.company.data(), o) &&
        o.hire_auto_raise_position_ready && !o.company_home_ready,
        "independent real spawn selection masked by absent home");
    std::cout << "GREEN: 4 production-reader location cases\n";
    return 0;
  } catch (const std::exception &e) {
    std::cerr << e.what() << '\n';
    return 1;
  }
}
