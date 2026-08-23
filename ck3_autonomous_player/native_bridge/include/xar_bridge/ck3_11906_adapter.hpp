#pragma once

#include "xar_bridge/game_adapter.hpp"

#include <memory>

namespace xar::game {

const AdapterDescriptor &Ck3_11906AdapterDescriptor() noexcept;
std::unique_ptr<GameAdapter>
CreateCk3_11906Adapter(std::string_view executable_sha256) noexcept;

} // namespace xar::game
