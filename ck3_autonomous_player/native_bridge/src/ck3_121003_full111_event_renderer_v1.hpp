#pragma once

#include "xar_bridge/ck3_121003_gui_window26785313_v1.hpp"
#include "xar_bridge/ck3_121003_lyd26785313_raw_v1.hpp"

#include <algorithm>
#include <cstdint>
#include <limits>
#include <optional>
#include <span>
#include <tuple>
#include <utility>
#include <vector>

namespace xar::ck3_121003::build26785313::full111_event_renderer {
using Address = std::uintptr_t;

// Exact 26785313 stock CPdxGuiFixedGridBox and CPdxGuiDataManager descriptors.
constexpr Address grid_vtable = 0x50DB900;
constexpr Address button_vtable = 0x50BFB80;
constexpr Address context_thunk_vtable = 0x50C1C30;
constexpr Address option_any_holder = 0x5D4D1B0;
constexpr Address option_any_vtable = 0x4C5D248;
constexpr Address option_type_id_slot = 0x6A6B3D8;
constexpr std::size_t maximum_rows = 64;

struct NativeArray {
    Address rows = 0;
    std::int32_t capacity = 0;
    std::int32_t count = 0;
    friend bool operator==(const NativeArray &, const NativeArray &) = default;
};
static_assert(sizeof(NativeArray) == 0x10);

struct Placement {
    std::int32_t column = 0;
    std::int32_t row = 0;
    Address widget = 0;
    friend bool operator==(const Placement &, const Placement &) = default;
};
static_assert(sizeof(Placement) == 0x10);

struct CopyReader {
    void *context = nullptr;
    bool (*copy)(void *, Address, void *, std::size_t) noexcept = nullptr;

    template<class T>
    bool field(Address object, std::size_t offset, T &result) const noexcept {
        return copy && object && offset <= (std::numeric_limits<Address>::max)() - object
            && copy(context, object + offset, &result, sizeof(result));
    }
};

struct Row {
    Placement placement;
    Address option = 0;
    Address context_thunk = 0;
    std::int32_t authored_index = -1;
    bool native_valid = false;
    bool widget_visible = false;
    bool widget_enabled = false;
    friend bool operator==(const Row &, const Row &) = default;
};

struct Snapshot {
    Address event_root = 0;
    Address grid = 0;
    Address creation = 0;
    Address model = 0;
    std::int32_t instance_id = 0;
    std::int32_t option_type_id = -1;
    NativeArray cells, placements;
    std::vector<Address> materialized_options;
    std::vector<Row> renderer_order;
    friend bool operator==(const Snapshot &, const Snapshot &) = default;
};

inline bool BoundedArray(const NativeArray &value, std::size_t stride) noexcept {
    return value.count >= 0 && static_cast<std::size_t>(value.count) <= maximum_rows &&
        value.capacity >= value.count && value.capacity <= 0x1000000 &&
        (!value.count || (value.rows && static_cast<std::size_t>(value.count) * stride <=
            (std::numeric_limits<Address>::max)() - value.rows));
}

inline std::optional<Address> TypedOptionPointer(const CopyReader &read, Address image,
    Address variant, std::int32_t type_id, Address *thunk_out = nullptr) noexcept {
    Address thunk = 0, vtable = 0, holder = 0, pointer = 0;
    std::uint8_t alternative = 0;
    std::int32_t key = -1;
    // Stock StoreDataContext's value-present, typed wrapper case only.
    if (!read.field(variant, 0x48, key) || key != type_id ||
        !read.field(variant, 0x40, alternative) || alternative != 3 ||
        !read.field(variant, 0x38, thunk) ||
        !read.field(thunk, 0, vtable) || vtable != image + context_thunk_vtable ||
        !read.field(thunk, 0x10, holder) || holder != image + option_any_holder ||
        !read.field(holder, 0, vtable) || vtable != image + option_any_vtable ||
        !read.field(thunk, 0x18, pointer) || !pointer) return {};
    if (thunk_out) *thunk_out = thunk;
    return pointer;
}

inline std::optional<Address> ReadWidgetOption(const CopyReader &read, Address image,
    Address widget, std::int32_t type_id) noexcept {
    Address contexts = 0, option = 0;
    NativeArray entries;
    if (!read.field(widget, 0xE0, contexts) ||
        !read.field(contexts, 0xA8, entries) || !BoundedArray(entries, 0x50)) return {};
    for (std::int32_t i = 0; i < entries.count; ++i) {
        const auto entry = entries.rows + static_cast<std::size_t>(i) * 0x50;
        std::int32_t key = -1;
        if (!read.field(entry, 0x48, key)) return {};
        if (key != type_id) continue;
        std::uint8_t set = 0;
        if (option || !read.field(entry, 0x4C, set) || set != 1) return {};
        const auto pointer = TypedOptionPointer(read, image, entry, type_id);
        if (!pointer) return {};
        option = *pointer;
    }
    if (!option) return {};
    return option;
}

// Caller supplies one owner's complete, typed GUI subtree for the already-proven foreground.
// Invoke on two current captures. Ages, image admission and owner/ticket lifetime remain with that reader.
inline std::optional<Snapshot> Capture(const CopyReader &read, Address image, Address foreground,
    std::int32_t actor, const LydEventRawRow267V1 &material, const LydEventRow267V1 &event,
    std::span<const GuiWindowNodeV1> nodes) {
    if (!image || !foreground || material.root != foreground || material.instance_id <= 0 ||
        material.instance_id != event.instance_id || event.recipient_character_id != actor ||
        !event.window_visible || !event.named_root_bound || !material.data ||
        !material.option_data || event.options.empty() || event.options.size() > maximum_rows ||
        material.options.size() != event.options.size()) return {};

    NativeArray options;
    std::int32_t active_instance = 0;
    if (!read.field(material.data, 0, active_instance) || active_instance != event.instance_id ||
        !read.field(material.data, 0x10, options) || !BoundedArray(options, 0x1B8) ||
        options.rows != material.option_data || static_cast<std::size_t>(options.count) != material.options.size()) return {};
    for (std::size_t i = 0; i < material.options.size(); ++i) {
        if (material.options[i] != options.rows + i * 0x1B8) return {};
    }

    const auto find = [&](Address widget) -> const GuiWindowNodeV1 * {
        const GuiWindowNodeV1 *node = nullptr;
        for (const auto &next : nodes) {
            if (next.widget == widget) {
                if (node) return nullptr;
                node = &next;
            }
        }
        return node;
    };
    const auto *root = find(foreground);
    const GuiWindowNodeV1 *grid = nullptr;
    if (!root || root->name != "character_event" || !root->context || (root->flags & 0x19U)) return {};
    for (const auto &node : nodes) {
        if (node.name != "option_grid") continue;
        // The supplied subtree must be complete and rooted at the exact foreground.
        if (grid || node.vtable != image + grid_vtable || node.context != root->context) return {};
        grid = &node;
    }
    if (!grid) return {};

    bool grid_visible = event.window_visible, grid_enabled = event.window_enabled && (root->flags & 0x06U) == 0;
    const auto *ancestor = grid;
    for (unsigned depth = 0; ancestor != root; ++depth) {
        if (!ancestor || depth >= kGuiWindowMaxDepthV1 || !ancestor->parent ||
            (ancestor->flags & 1U) || ancestor->context != root->context) return {};
        grid_visible = grid_visible && (ancestor->flags & 0x18U) == 0;
        grid_enabled = grid_enabled && (ancestor->flags & 0x06U) == 0;
        ancestor = find(ancestor->parent);
    }

    Snapshot snapshot;
    snapshot.event_root = foreground;
    snapshot.grid = grid->widget;
    snapshot.instance_id = event.instance_id;
    snapshot.materialized_options = material.options;
    Address back = 0;
    std::int32_t declared_type = -1;
    NativeArray placements, cells;
    if (!read.field(image, option_type_id_slot, snapshot.option_type_id) || snapshot.option_type_id < 0 ||
        !read.field(grid->widget, 0x438, snapshot.creation) ||
        !read.field(snapshot.creation, 0xE0, back) || back != grid->widget ||
        !read.field(snapshot.creation, 0, snapshot.model) ||
        !read.field(snapshot.model, 0xD0, declared_type) || declared_type != snapshot.option_type_id ||
        !read.field(snapshot.creation, 0x90, cells) || !BoundedArray(cells, 0x68) ||
        !read.field(grid->widget, 0x3F8, placements) || !BoundedArray(placements, sizeof(Placement)) ||
        placements.count != static_cast<std::int32_t>(event.options.size())) return {};
    snapshot.placements = placements;
    snapshot.cells = cells;

    std::vector<std::pair<Address, Address>> active_cells;
    for (std::int32_t i = 0; i < cells.count; ++i) {
        const auto cell = cells.rows + static_cast<std::size_t>(i) * 0x68;
        Address widget = 0;
        std::uint8_t attached = 0;
        if (!read.field(cell, 0, widget) || !read.field(cell, 0x60, attached) || attached > 1) return {};
        if (attached) {
            if (!widget || std::any_of(active_cells.begin(), active_cells.end(),
                    [widget](const auto &other) { return other.first == widget; })) return {};
            active_cells.emplace_back(widget, cell);
        }
    }
    if (active_cells.size() != static_cast<std::size_t>(placements.count)) return {};

    std::vector<bool> matched(event.options.size(), false);
    for (std::int32_t i = 0; i < placements.count; ++i) {
        Row row;
        if (!read.field(placements.rows, static_cast<std::size_t>(i) * 0x10, row.placement)) return {};
        const auto &p = row.placement;
        if (!snapshot.renderer_order.empty()) {
            const auto &previous = snapshot.renderer_order.back().placement;
            if (!(std::tie(previous.row, previous.column) < std::tie(p.row, p.column))) return {};
        }
        const auto *button = find(p.widget);
        if (!button || button->name != "event_option_button" || button->vtable != image + button_vtable ||
            button->parent != grid->widget || button->context != grid->context || (button->flags & 1U)) return {};
        const auto widget_option = ReadWidgetOption(read, image, p.widget, snapshot.option_type_id);
        if (!widget_option) return {};

        const auto active = std::find_if(active_cells.begin(), active_cells.end(),
            [&p](const auto &cell) { return cell.first == p.widget; });
        if (active == active_cells.end()) return {};
        const auto cell_option = TypedOptionPointer(read, image, active->second + 0x10,
            snapshot.option_type_id, &row.context_thunk);
        if (!cell_option || *cell_option != *widget_option) return {};
        row.option = *widget_option;
        const auto expected = std::find(material.options.begin(), material.options.end(), row.option);
        if (expected == material.options.end()) return {};
        const auto index = static_cast<std::size_t>(expected - material.options.begin());
        Address owner = 0;
        if (matched[index] || !read.field(row.option, 0x160, owner) || owner != material.data ||
            !read.field(row.option, 0x1B0, row.authored_index) ||
            row.authored_index != event.options[index].authored_option_index) return {};
        matched[index] = true;
        row.native_valid = event.options[index].native_can_select;
        row.widget_visible = grid_visible && (button->flags & 0x18U) == 0;
        row.widget_enabled = grid_enabled && (button->flags & 0x06U) == 0;
        snapshot.renderer_order.push_back(row);
    }
    return snapshot;
}

inline std::optional<Snapshot> AcceptStable(const std::optional<Snapshot> &before, std::optional<Snapshot> after) {
    if (!before || !after || *before != *after) return {};
    return after;
}
}
