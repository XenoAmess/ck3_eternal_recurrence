# kaishek-syntax

Dependency-free Java 17 lossless lexer and concrete syntax tree for Paradox
script files. `Parser.parse(byte[])` copies the input, retains byte offsets,
comments, whitespace/newline style, duplicate keys and source order, and emits
the exact original bytes through `ParseResult.emit()`. Parsing is deliberately
syntax-only; profile validation belongs to the validator module.

Malformed strings, unmatched braces and missing operators/values are recovered
in-place and reported as `Diagnostic` values. A block's children include its
brace tokens and trivia, while list items without an operator are represented by
`SyntaxKind.LIST_ITEM`.

Run the dependency-free smoke test after compiling with JDK 17:

```text
javac -d target/classes $(find src/main/java src/test/java -name '*.java')
java -cp target/classes com.xenoamess.kaishek.syntax.ParserSelfTest
```
