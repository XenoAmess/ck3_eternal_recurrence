#include "xar_bridge/conception_pair_value_inputs_12004.hpp"

namespace xar::ck3_12004::conception_pair_value_inputs {

LoadedReadResult ReadLoadedNumericInputs(const Bindings& bindings) {
    if (bindings.executable_sha256 != kExecutableSha256) {
        return {LoadedReadStatus::actual_build_unavailable, {}, 0};
    }
    if (bindings.module_base == 0) {
        return {LoadedReadStatus::module_base_unavailable, {}, 0};
    }
    if (bindings.read_memory == nullptr) {
        return {LoadedReadStatus::memory_reader_unavailable, {}, 0};
    }

    std::array<std::int64_t, kLoadedNumericSlotRvas.size()> values{};
    for (std::size_t index = 0; index < values.size(); ++index) {
        const auto rva = kLoadedNumericSlotRvas[index];
        if (!bindings.read_memory(bindings.context, bindings.module_base + rva,
                                  &values[index], sizeof(values[index]))) {
            return {LoadedReadStatus::slot_read_failed, {}, rva};
        }
    }
    return {LoadedReadStatus::available,
            LoadedNumericInputs{values[0], values[1], values[2], values[3],
                                values[4], values[5], values[6]}, 0};
}

}  // namespace xar::ck3_12004::conception_pair_value_inputs
