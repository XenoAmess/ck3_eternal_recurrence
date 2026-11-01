#include "Native201Api.hpp"
#include <iostream>
#include <string>
#include <exception>
#include <filesystem>

int main(int argc, char* argv[]) {
    if (argc != 2) {
        std::cerr << "Usage: Native201Main <rawpath>\n";
        return 1;
    }
    try {
        std::filesystem::path rawPath(argv[1]);
        auto raw = range9d201::readRaw(rawPath);
        auto cases = range9d201::frozenCases();
        auto result = range9d201::executeOriginal(raw, cases);
        range9d201::writeRun(std::cout, result);
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << "\n";
        return 1;
    }
    return 0;
}
