#include "Native200Api.hpp"
#include <iostream>
#include <exception>
#include <string>
#include <vector>

int main(int argc, char* argv[]) {
    if (argc != 3) {
        std::cerr << "Usage: " << argv[0] << " <raw351.bin> <literal4.bin>" << std::endl;
        return 1;
    }

    try {
        std::filesystem::path rawPath(argv[1]);
        std::filesystem::path literalPath(argv[2]);

        auto raw = copy4add200::readRaw(rawPath);
        auto literal = copy4add200::readLiteral(literalPath);
        auto cases = copy4add200::frozenCases();

        auto result = copy4add200::executeOriginal(raw, literal, cases);

        copy4add200::writeRun(std::cout, result);
        std::cout << std::endl;

        return 0;
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }
}