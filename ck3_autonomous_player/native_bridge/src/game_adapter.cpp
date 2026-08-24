#include "xar_bridge/game_adapter.hpp"

#include "xar_bridge/ck3_11906_adapter.hpp"

#include <windows.h>
#include <bcrypt.h>

#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

namespace xar::game {
namespace {

std::string CurrentExecutableSha256() noexcept {
  std::array<wchar_t, 32'768> path{};
  const DWORD path_length =
      GetModuleFileNameW(nullptr, path.data(), static_cast<DWORD>(path.size()));
  if (path_length == 0 || path_length >= path.size()) {
    return {};
  }

  HANDLE file = CreateFileW(path.data(), GENERIC_READ, FILE_SHARE_READ, nullptr,
                            OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);
  if (file == INVALID_HANDLE_VALUE) {
    return {};
  }

  BCRYPT_ALG_HANDLE algorithm = nullptr;
  BCRYPT_HASH_HANDLE hash = nullptr;
  std::vector<std::uint8_t> object;
  std::array<std::uint8_t, 32> digest{};
  bool ok = false;
  do {
    if (BCryptOpenAlgorithmProvider(&algorithm, BCRYPT_SHA256_ALGORITHM,
                                    nullptr, 0) < 0) {
      break;
    }
    DWORD object_size = 0;
    DWORD copied = 0;
    if (BCryptGetProperty(algorithm, BCRYPT_OBJECT_LENGTH,
                          reinterpret_cast<PUCHAR>(&object_size),
                          sizeof(object_size), &copied, 0) < 0 ||
        object_size == 0) {
      break;
    }
    object.resize(object_size);
    if (BCryptCreateHash(algorithm, &hash, object.data(), object_size, nullptr,
                         0, 0) < 0) {
      break;
    }

    std::array<std::uint8_t, 64U * 1024U> buffer{};
    while (true) {
      DWORD read = 0;
      if (!ReadFile(file, buffer.data(), static_cast<DWORD>(buffer.size()),
                    &read, nullptr)) {
        break;
      }
      if (read == 0) {
        ok = BCryptFinishHash(hash, digest.data(),
                              static_cast<ULONG>(digest.size()), 0) >= 0;
        break;
      }
      if (BCryptHashData(hash, buffer.data(), read, 0) < 0) {
        break;
      }
    }
  } while (false);

  if (hash != nullptr) {
    BCryptDestroyHash(hash);
  }
  if (algorithm != nullptr) {
    BCryptCloseAlgorithmProvider(algorithm, 0);
  }
  CloseHandle(file);
  if (!ok) {
    return {};
  }

  constexpr char digits[] = "0123456789ABCDEF";
  std::array<char, 65> encoded{};
  for (std::size_t index = 0; index < digest.size(); ++index) {
    encoded[index * 2] = digits[digest[index] >> 4U];
    encoded[index * 2 + 1] = digits[digest[index] & 0x0fU];
  }
  return encoded.data();
}

} // namespace

bool GameAdapter::supports(std::string_view capability) const noexcept {
  if (!enabled()) {
    return false;
  }
  for (const auto candidate : descriptor().capabilities) {
    if (candidate == capability) {
      return true;
    }
  }
  return false;
}

bool GameAdapter::supports_snapshot() const noexcept {
  return supports("game.state.snapshot");
}

bool GameAdapter::supports_step(std::string_view step) const noexcept {
  std::string_view capability;
  if (step == "pause-map") {
    capability = "game.command.pause-map";
  } else if (step == "resume-map") {
    capability = "game.command.resume-map";
  } else if (step == "save-checkpoint") {
    capability = "game.command.save-checkpoint";
  } else if (step == "accept-pending-character-interaction") {
    capability = "game.command.accept-pending-character-interaction";
  } else if (step == "reject-pending-character-interaction") {
    capability = "game.command.reject-pending-character-interaction";
  } else if (step == "query-arrange-marriage-choices") {
    capability = "game.command.query-arrange-marriage-choices";
  } else if (step.starts_with("arrange-marriage-")) {
    capability = "game.command.arrange-marriage-N";
  } else if (step == "query-declarable-wars") {
    capability = "game.command.query-declarable-wars";
  } else if (step.starts_with("declare-war-")) {
    capability = "game.command.declare-war-N";
  } else if (step.starts_with("enforce-demands-")) {
    capability = "game.command.enforce-demands-N";
  } else if (step == "raise-troops-default") {
    capability = "game.command.raise-troops-default";
  } else if (step.starts_with("preview-move-army-")) {
    capability = "game.command.preview-move-army-N-to-N";
  } else if (step.starts_with("move-army-")) {
    capability = "game.command.move-army-N-to-N";
  } else if (step.starts_with("disband-army-")) {
    capability = "game.command.disband-army-N";
  } else if (step.starts_with("split-army-half-")) {
    capability = "game.command.split-army-half-N";
  } else if (step.starts_with("merge-armies-")) {
    capability = "game.command.merge-armies-N-with-N";
  } else if (step.starts_with("start-assault-")) {
    capability = "game.command.start-assault-N";
  } else if (step.starts_with("stop-assault-")) {
    capability = "game.command.stop-assault-N";
  } else if (step.starts_with("select-event-option-")) {
    capability = "game.command.select-event-option-N";
  } else if (step.size() == 11 && step.starts_with("set-speed-") &&
             step.back() >= '1' && step.back() <= '5') {
    constexpr std::array<std::string_view, 5> speed_capabilities{
        "game.command.set-speed-1", "game.command.set-speed-2",
        "game.command.set-speed-3", "game.command.set-speed-4",
        "game.command.set-speed-5"};
    capability = speed_capabilities[static_cast<std::size_t>(step.back() - '1')];
  }
  return !capability.empty() && supports(capability);
}

const AdapterDescriptor &PreferredAdapterDescriptor() noexcept {
  return Ck3_11906AdapterDescriptor();
}

std::unique_ptr<GameAdapter>
SelectAdapter(std::string_view executable_sha256,
              std::span<const AdapterFactory> factories) noexcept {
  std::unique_ptr<GameAdapter> preferred;
  for (const auto factory : factories) {
    auto candidate = factory(executable_sha256);
    if (candidate == nullptr) {
      continue;
    }
    if (candidate->enabled()) {
      return candidate;
    }
    if (preferred == nullptr) {
      preferred = std::move(candidate);
    }
  }
  return preferred;
}

std::unique_ptr<GameAdapter> SelectCurrentProcessAdapter() noexcept {
  // Add one factory for each exact CK3 build. Order controls the preferred
  // diagnostic descriptor only; the first exact enabled match always wins.
  constexpr std::array<AdapterFactory, 1> factories{
      &CreateCk3_11906Adapter,
  };
  const std::string executable_sha256 = CurrentExecutableSha256();
  return SelectAdapter(executable_sha256, factories);
}

} // namespace xar::game
