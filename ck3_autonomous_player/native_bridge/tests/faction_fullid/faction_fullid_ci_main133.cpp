#include <string_view>
#include "county_fullid_cases09.hpp"

int FactionFullIdTargetingMain09(int argc, char **argv);
int FactionFullIdCharacterPublicMain14(int argc, char **argv);
int FactionFullIdSurrenderMain15(int argc, char **argv);

int main(int argc, char **argv) {
  if (argc > 1 && std::string_view(argv[1]) == "--county")
    return m1_county_fullid13::RunCountyFullId13(argc - 1, argv + 1);
  if (argc > 1 && std::string_view(argv[1]) == "--character-public")
    return FactionFullIdCharacterPublicMain14(argc - 1, argv + 1);
  if (argc > 1 && std::string_view(argv[1]) == "--character-surrender")
    return FactionFullIdSurrenderMain15(argc - 1, argv + 1);
  return FactionFullIdTargetingMain09(argc, argv);
}
