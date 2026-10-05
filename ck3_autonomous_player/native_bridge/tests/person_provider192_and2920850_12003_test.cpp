#include <filesystem>
#include <iostream>

void RunProvider192And2920850Fixture(const std::filesystem::path &);

int main(int argc, char **argv) {
  if (argc != 2) return 2;
  const std::filesystem::path directory(argv[1]);
  std::filesystem::create_directories(directory);
  RunProvider192And2920850Fixture(directory);
  std::cout << "person provider192 and2920850 fixtures GREEN\n";
  return 0;
}
