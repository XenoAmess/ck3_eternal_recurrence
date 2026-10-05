#include <filesystem>
#include <iostream>

void RunListPredicate2530dd0Fixture(const std::filesystem::path &);

int main(int argc, char **argv) {
  if (argc != 2) return 2;
  const std::filesystem::path directory(argv[1]);
  std::filesystem::create_directories(directory);
  RunListPredicate2530dd0Fixture(directory);
  std::cout << "person list predicate fixtures GREEN\n";
  return 0;
}
