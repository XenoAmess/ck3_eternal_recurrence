#include <filesystem>
#include <iostream>

void RunPersonTailDirectSources12003(const std::filesystem::path &);
void RunTailPrefixFixture(const std::filesystem::path &);
int RunMiddleHelpersFixture(const std::filesystem::path &);
void RunTraitStage291d460Fixture(const std::filesystem::path &);
void RunAbsentRecipientFixture(const std::filesystem::path &);

int main(int argc, char **argv) {
  if (argc != 2) return 2;
  const std::filesystem::path directory(argv[1]);
  std::filesystem::create_directories(directory);
  const char *subdirectories[] = {"tail-direct", "tail-prefix", "middle", "trait", "absent"};
  for (const auto *name : subdirectories)
    std::filesystem::create_directories(directory / name);
  RunPersonTailDirectSources12003(directory / "tail-direct");
  RunTailPrefixFixture(directory / "tail-prefix");
  if (RunMiddleHelpersFixture(directory / "middle") != 0) return 1;
  RunTraitStage291d460Fixture(directory / "trait");
  RunAbsentRecipientFixture(directory / "absent");
  std::cout << "person tail source fixtures GREEN\n";
  return 0;
}
