#include <filesystem>
#include <iostream>

void RunFollowing2920b50Fixture(const std::filesystem::path &);

int main(int argc, char **argv) {
  if (argc != 2) return 2;
  const std::filesystem::path directory(argv[1]);
  std::filesystem::create_directories(directory);
  RunFollowing2920b50Fixture(directory);
  std::cout << "person following2920B50 fixtures GREEN\n";
  return 0;
}
