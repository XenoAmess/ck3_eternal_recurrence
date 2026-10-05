#include <filesystem>
#include <iostream>

void RunHelper2922070Fixture(const std::filesystem::path &);
void RunConference24b1d00Fixture(const std::filesystem::path &);
void RunUncachedRecipientFixture(const std::filesystem::path &);

int main(int argc, char **argv) {
  if (argc != 2) return 2;
  const std::filesystem::path directory(argv[1]);
  std::filesystem::create_directories(directory / "helper-2922070");
  std::filesystem::create_directories(directory / "conference");
  std::filesystem::create_directories(directory / "uncached");
  RunHelper2922070Fixture(directory / "helper-2922070");
  RunConference24b1d00Fixture(directory / "conference");
  RunUncachedRecipientFixture(directory / "uncached");
  std::cout << "person tail continuation fixtures GREEN\n";
  return 0;
}
