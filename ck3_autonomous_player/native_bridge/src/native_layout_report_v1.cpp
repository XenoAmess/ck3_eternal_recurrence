// Header-only ABI measurements. No Game/DLL symbols are linked or called.
#include "xar_bridge/game_contract.hpp"
#include "xar_bridge/player_faction_alerts_v1.hpp"
#include "xar_bridge/player_faction_alerts_v1_mailbox.hpp"
#include "xar_bridge/ck3_12002_faction_mailbox.hpp"
#include "xar_bridge/ck3_12004_faction_mailbox.hpp"
#include "native_layout_flags_v1.hpp"
#include <iostream>
#include <string_view>
#include <type_traits>

#define XAR_LAYOUT_STR_I(x) #x
#define XAR_LAYOUT_STR(x) XAR_LAYOUT_STR_I(x)
namespace {
void Quote(std::string_view text) {
  constexpr char hex[] = "0123456789abcdef";
  std::cout << '"';
  for (unsigned char c : text) {
    if (c == '"' || c == '\\') std::cout << '\\' << static_cast<char>(c);
    else if (c < 32) std::cout << "\\u00" << hex[c >> 4] << hex[c & 15];
    else std::cout << static_cast<char>(c);
  }
  std::cout << '"';
}
void Macro(std::string_view name, const char *value, bool &first) {
  if (!first) std::cout << ',';
  first = false; Quote(name); std::cout << ':';
  if (value) Quote(value); else std::cout << "null";
}
template<class T> void Layout(std::string_view name, bool last = false) {
  Quote(name);
  std::cout << ":{\"sizeof\":" << sizeof(T) << ",\"alignof\":" << alignof(T)
            << ",\"standard_layout\":" << (std::is_standard_layout_v<T> ? "true" : "false")
            << '}' << (last ? "\n" : ",\n");
}
}
int main(int argc, char **argv) {
  if (argc != 5 || std::string_view(argv[1]) != "--machine-id" ||
      std::string_view(argv[3]) != "--observed-at-utc" ||
      !*argv[2] || !*argv[4]) {
    std::cerr << "usage: native_layout_report_v1 --machine-id ID --observed-at-utc UTC\n";
    return 64;
  }
  std::cout << "{\"schema\":\"xar.ck3.native-header-layout/v1\",\"machine_id\":";
  Quote(argv[2]); std::cout << ",\"observed_at_utc\":"; Quote(argv[4]);
  std::cout << ",\"metadata_provenance\":\"caller must retain fresh machine tool and UTC evidence\""
               ",\"scope\":\"header_layout_only_not_Game_qualification\","
               "\"current_pragma_pack\":null,\"pointer_bytes\":" << sizeof(void *)
            << ",\"cplusplus\":" << __cplusplus << ",\"preprocessor\":{";
  bool first = true;
#ifdef _MSC_VER
  Macro("_MSC_VER", XAR_LAYOUT_STR(_MSC_VER), first);
#else
  Macro("_MSC_VER", nullptr, first);
#endif
#ifdef _MSC_FULL_VER
  Macro("_MSC_FULL_VER", XAR_LAYOUT_STR(_MSC_FULL_VER), first);
#else
  Macro("_MSC_FULL_VER", nullptr, first);
#endif
#ifdef _MSVC_LANG
  Macro("_MSVC_LANG", XAR_LAYOUT_STR(_MSVC_LANG), first);
#else
  Macro("_MSVC_LANG", nullptr, first);
#endif
#ifdef _MSVC_STL_VERSION
  Macro("_MSVC_STL_VERSION", XAR_LAYOUT_STR(_MSVC_STL_VERSION), first);
#else
  Macro("_MSVC_STL_VERSION", nullptr, first);
#endif
#ifdef _MSVC_STL_UPDATE
  Macro("_MSVC_STL_UPDATE", XAR_LAYOUT_STR(_MSVC_STL_UPDATE), first);
#else
  Macro("_MSVC_STL_UPDATE", nullptr, first);
#endif
#ifdef _ITERATOR_DEBUG_LEVEL
  Macro("_ITERATOR_DEBUG_LEVEL", XAR_LAYOUT_STR(_ITERATOR_DEBUG_LEVEL), first);
#else
  Macro("_ITERATOR_DEBUG_LEVEL", nullptr, first);
#endif
#ifdef _CRT_PACKING
  Macro("_CRT_PACKING", XAR_LAYOUT_STR(_CRT_PACKING), first);
#else
  Macro("_CRT_PACKING", nullptr, first);
#endif
#ifdef _MT
  Macro("_MT", XAR_LAYOUT_STR(_MT), first);
#else
  Macro("_MT", nullptr, first);
#endif
#ifdef _DLL
  Macro("_DLL", XAR_LAYOUT_STR(_DLL), first);
#else
  Macro("_DLL", nullptr, first);
#endif
#ifdef _DEBUG
  Macro("_DEBUG", XAR_LAYOUT_STR(_DEBUG), first);
#else
  Macro("_DEBUG", nullptr, first);
#endif
  std::cout << "},\"packing_note\":\"_CRT_PACKING is only a CRT header macro;"
               " current pragma state is not inferred\","
               "\"source_flags\":";
  Quote(kXarNativeLayoutSourceFlagsV1);
  std::cout << ",\"types\":{\n";
  Layout<xar::game::Snapshot>("xar::game::Snapshot");
  Layout<xar::game::PlayerFactionAlertsV1>("xar::game::PlayerFactionAlertsV1");
  Layout<xar::ck3_11906::PlayerFactionAlertsSourceSampleV1>(
      "xar::ck3_11906::PlayerFactionAlertsSourceSampleV1");
  Layout<xar::ck3_11906::MainThreadQueryMailboxV1>(
      "xar::ck3_11906::MainThreadQueryMailboxV1");
  Layout<xar::ck3_11906::PlayerFactionAlertsMailboxContextV1>(
      "xar::ck3_11906::PlayerFactionAlertsMailboxContextV1");
  Layout<xar::ck3_12002::QueryMailboxEnvelope>("xar::ck3_12002::QueryMailboxEnvelope");
  Layout<xar::ck3_12002::PlayerFactionAlertsMailboxContext12002>(
      "xar::ck3_12002::PlayerFactionAlertsMailboxContext12002");
  Layout<xar::ck3_12004::PlayerFactionAlertsMailboxContext12004>(
      "xar::ck3_12004::PlayerFactionAlertsMailboxContext12004", true);
  std::cout << "}}\n";
  return std::cout.good() ? 0 : 2;
}

