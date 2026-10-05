#include <filesystem>
#include <iostream>

void RunProviderBucket291c5b2Fixture(const std::filesystem::path &);
void RunQualifier28bc0d0Fixture(const std::filesystem::path &);

int main(int argc, char **argv) {
  if (argc != 2) return 2;
  const std::filesystem::path directory(argv[1]);
  std::filesystem::create_directories(directory / "provider-bucket");
  std::filesystem::create_directories(directory / "qualifier");
  RunProviderBucket291c5b2Fixture(directory / "provider-bucket");
  RunQualifier28bc0d0Fixture(directory / "qualifier");
  std::cout << "person provider and qualifier fixtures GREEN\n";
  return 0;
}
