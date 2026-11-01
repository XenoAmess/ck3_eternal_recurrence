#include "Native204Api.hpp"
#include <iostream>
#include <string>
#include <vector>

int main(int argc, char* argv[]) {
    if (argc != 5) {
        std::cerr << "Usage: " << argv[0] << " <upper_path> <range_path> <add_path> <literal_path>" << std::endl;
        return 1;
    }

    try {
        std::filesystem::path upperPath(argv[1]);
        std::filesystem::path rangePath(argv[2]);
        std::filesystem::path addPath(argv[3]);
        std::filesystem::path literalPath(argv[4]);

        auto upper = upper172knownadd204::readUpper(upperPath);
        auto range = upper172knownadd204::readRange(rangePath);
        auto add = upper172knownadd204::readAdd(addPath);
        auto literal = upper172knownadd204::readLiteral(literalPath);
        auto cases = upper172knownadd204::frozenCases();

        auto result = upper172knownadd204::executeOriginal(upper, range, add, literal, cases);

        upper172knownadd204::writeRun(std::cout, result);
        std::cout << std::endl;

        return 0;
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }
}