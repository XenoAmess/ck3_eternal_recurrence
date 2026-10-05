#include <filesystem>
#include <iostream>

void RunFollowing312a950Fixture(const std::filesystem::path &);

int main(int argc, char **argv) {
  if (argc != 2) return 2;
  const std::filesystem::path directory(argv[1]);
  std::filesystem::create_directories(directory);
  RunFollowing312a950Fixture(directory);
  std::cout << "person government and first-Land312A950 minimum fixtures GREEN\n";
  return 0;
}
