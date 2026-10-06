#include "xar_bridge/ck3_12004_frontend_bookmark.hpp"
#include "xar_bridge/ck3_12004.hpp"

namespace xar::ck3_12004 {
namespace {

// Frontend owner code, named RTTI and leaf setter bodies are frozen in
// frontend-bookmark-12004/{primary-map,owner-map,db-map,leaf-map,NAMED-RTTI.json}.
// These addresses are independently bound; no data-table delta is inferred.
constexpr ck3_11906::FrontendModelAbiV1 kFrontendAbi{
    0x449BDB8, {0x44D5F40, 0x4500670, 0x45008C0}, 0x451B948,
    0x5702BC0, 0x57201F8, 0x60, 0xD8, 0x18, 0x120, 0x128, 0x12C,
    0x40, 0x160, 0x321D180, 0x1060A90, 0x1060950, 0xC0,
    0x1060090, 0x5C67210, 0x48D0210};

bool SameExecutableIdentity(std::string_view actual) noexcept {
  constexpr std::string_view expected{kExecutableSha256};
  if (actual.size() != expected.size()) return false;
  for (std::size_t i = 0; i < actual.size(); ++i) {
    const char normalized = actual[i] >= 'a' && actual[i] <= 'f'
                                ? static_cast<char>(actual[i] - 'a' + 'A')
                                : actual[i];
    if (normalized != expected[i]) return false;
  }
  return true;
}

} // namespace

const ck3_11906::FrontendModelAbiV1 *BindFrontendBookmarkModel12004(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept {
  return module_base != 0 && SameExecutableIdentity(executable_sha256)
             ? &kFrontendAbi : nullptr;
}

} // namespace xar::ck3_12004
