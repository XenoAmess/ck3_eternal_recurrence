#include "ck3_121003_full111_event_renderer_v1.hpp"

#include <array>
#include <cstring>
#include <iostream>
#include <map>
#include <stdexcept>
#include <type_traits>

using namespace xar::ck3_121003::build26785313;
using namespace xar::ck3_121003::build26785313::full111_event_renderer;

namespace {
constexpr Address image = 0x140000000, root = 0x1000, grid = 0x2000, creation = 0x3000, model = 0x4000;
constexpr Address cells = 0x5000, placements = 0x6000, first = 0x7000, second = 0x8000, one = 0x9000, four = one + 0x1B8;
constexpr Address actor_data = 0xB000, sibling_data = 0xC000, one_thunk = 0xD000, four_thunk = 0xE000;
constexpr Address first_context = 0xF000, second_context = 0x10000, first_variant = 0x11000, second_variant = 0x12000;
constexpr Address app_context = 0x13000;
constexpr std::int32_t type_id = 72;
constexpr std::int32_t player = 314;

void Require(bool result, const char *case_name) {
    if (!result) throw std::runtime_error(case_name);
    std::cout << "PASS " << case_name << '\n';
}

struct Fixture {
    LydEventRawRow267V1 material;
    LydEventRow267V1 event;
    std::array<GuiWindowNodeV1, 4> nodes;
    std::map<Address, std::byte> ram;
    CopyReader reader{this, &Copy};

    static bool Copy(void *context, Address address, void *out, std::size_t count) noexcept {
        const auto &bytes = static_cast<Fixture *>(context)->ram;
        auto *dest = static_cast<std::byte *>(out);
        for (std::size_t i = 0; i < count; ++i) {
            const auto found = bytes.find(address + i);
            if (found == bytes.end()) return false;
            dest[i] = found->second;
        }
        return true;
    }

    template<class T> void Put(Address address, const T &value) {
        static_assert(std::is_trivially_copyable_v<T>);
        std::array<std::byte, sizeof(T)> bytes{};
        std::memcpy(bytes.data(), &value, bytes.size());
        for (std::size_t i = 0; i < bytes.size(); ++i) ram[address + i] = bytes[i];
    }

    void Variant(Address variant, Address thunk, Address option) {
        Put(variant + 0x48, type_id);
        Put(variant + 0x40, std::uint8_t{3});
        Put(variant + 0x38, thunk);
        Put(variant + 0x4C, std::uint8_t{1});
        Put(thunk, image + context_thunk_vtable);
        Put(thunk + 0x10, image + option_any_holder);
        Put(thunk + 0x18, option);
    }

    void Node(std::size_t i, Address id, Address parent, Address vt, const char *name) {
        auto &node = nodes[i];
        node.widget = id;
        node.context = app_context;
        node.parent = parent;
        node.vtable = image + vt;
        node.name = name;
    }

    Fixture() {
        material.instance_id = event.instance_id = 41;
        material.root = root;
        material.data = actor_data;
        material.option_data = one;
        material.options = {one, four};
        event.window_visible = event.window_enabled = event.named_root_bound = true;
        event.recipient_character_id = player;
        event.authored_option_count = 6;
        event.options = {{1, true, "Option one", "", {}, {}}, {4, false, "Option four", "", {}, {}}};
        Node(0, root, 0, 0, "character_event");
        Node(1, grid, root, grid_vtable, "option_grid");
        Node(2, first, grid, button_vtable, "event_option_button");
        Node(3, second, grid, button_vtable, "event_option_button");
        Put(image + option_type_id_slot, type_id);
        Put(image + option_any_holder, image + option_any_vtable);
        Put(grid + 0x438, creation);
        Put(creation + 0xE0, grid);
        Put(creation, model);
        Put(model + 0xD0, type_id);
        Put(creation + 0x90, NativeArray{cells, 2, 2});
        Put(grid + 0x3F8, NativeArray{placements, 2, 2});
        Put(placements, Placement{0, 0, first});
        Put(placements + 0x10, Placement{0, 1, second});
        Put(cells, first);
        Put(cells + 0x68, second);
        Put(cells + 0x60, std::uint8_t{1});
        Put(cells + 0x68 + 0x60, std::uint8_t{1});
        Variant(cells + 0x10, four_thunk, four);
        Variant(cells + 0x68 + 0x10, one_thunk, one);
        Put(first + 0xE0, first_context);
        Put(second + 0xE0, second_context);
        Put(first_context + 0xA8, NativeArray{first_variant, 1, 1});
        Put(second_context + 0xA8, NativeArray{second_variant, 1, 1});
        Variant(first_variant, four_thunk, four);
        Variant(second_variant, one_thunk, one);
        Put(actor_data, material.instance_id);
        Put(actor_data + 0x10, NativeArray{one, 2, 2});
        Put(four + 0x160, actor_data);
        Put(one + 0x160, actor_data);
        Put(four + 0x1B0, std::int32_t{4});
        Put(one + 0x1B0, std::int32_t{1});
    }

    std::optional<Snapshot> Read() {
        return Capture(reader, image, root, player, material, event, nodes);
    }
};
}

int main() {
    Fixture exact;
    const auto first_read = exact.Read();
    Require(first_read && first_read->renderer_order.size() == 2 &&
            first_read->renderer_order[0].authored_index == 4 && !first_read->renderer_order[0].native_valid &&
            first_read->renderer_order[1].authored_index == 1 && first_read->renderer_order[1].native_valid &&
            AcceptStable(first_read, exact.Read()).has_value(), "stock pointer join preserves non-authored layout order");
    Fixture wrong_event;
    wrong_event.Put(four + 0x160, sibling_data);
    Require(!wrong_event.Read(), "same index borrowed from wrong event rejected");
    Fixture changed_order;
    const auto original = changed_order.Read();
    changed_order.Put(placements, Placement{0, 0, second});
    changed_order.Put(placements + 0x10, Placement{0, 1, first});
    const auto changed = changed_order.Read();
    Require(changed && changed->renderer_order[0].authored_index == 1 &&
            !AcceptStable(original, changed), "valid associations follow widget reorder and stale double-read rejects");
    Fixture disabled;
    disabled.nodes[3].flags = 0x04;
    const auto disabled_read = disabled.Read();
    Require(disabled_read && disabled_read->renderer_order[1].native_valid &&
            !disabled_read->renderer_order[1].widget_enabled && disabled_read->renderer_order[1].widget_visible,
            "stock-valid item is not renderer-enabled when the widget is disabled");
    Fixture hidden;
    hidden.nodes[2].flags = 0x10;
    const auto hidden_read = hidden.Read();
    Require(hidden_read && !hidden_read->renderer_order[0].widget_visible && hidden_read->renderer_order[1].widget_visible,
            "hidden widget is preserved and cannot become a shown option");
    Fixture inherited;
    inherited.nodes[1].flags = 0x12;
    const auto inherited_read = inherited.Read();
    Require(inherited_read && !inherited_read->renderer_order[1].widget_visible && !inherited_read->renderer_order[1].widget_enabled,
            "hidden and disabled ancestor states are effective");
    Fixture wrong_type;
    wrong_type.Put(four_thunk + 0x10, image + 0x5D4D178);
    Require(!wrong_type.Read(), "reason-item CopyableAny rejected as EventOption");
    Fixture stale_context;
    stale_context.Variant(first_variant, one_thunk, one);
    Require(!stale_context.Read(), "same-type widget context drifting from its grid cell rejected");
    Fixture missing;
    missing.Put(cells + 0x60, std::uint8_t{0});
    Require(!missing.Read(), "incomplete materialization rejected");
    Fixture untracked_cell;
    untracked_cell.Put(creation + 0x90, NativeArray{cells, 3, 3});
    untracked_cell.Put(cells + 2 * 0x68, Address{0xDEADBEEF});
    untracked_cell.Put(cells + 2 * 0x68 + 0x60, std::uint8_t{1});
    Require(!untracked_cell.Read(), "third active widget cannot disappear from placement census");
    Fixture bound_overflow;
    bound_overflow.Put(creation + 0x90, NativeArray{(std::numeric_limits<Address>::max)() - 5, 2, 2});
    Require(!bound_overflow.Read(), "overflowing active table address rejected");
    Fixture transitioned;
    const auto before_transition = transitioned.Read();
    transitioned.Put(actor_data, std::int32_t{42});
    Require(!AcceptStable(before_transition, transitioned.Read()), "stale instance after context still matches is rejected");
}
