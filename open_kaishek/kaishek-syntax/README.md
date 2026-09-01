# kaishek-syntax

Dependency-free Java 21 lossless lexer and concrete syntax tree for Paradox
script files. `Parser.parse(byte[])` copies the input, retains byte offsets,
comments, whitespace/newline style, duplicate keys and source order, and emits
the exact original bytes through `ParseResult.emit()`. Parsing is deliberately
syntax-only; profile validation belongs to the validator module.

Malformed strings, unmatched braces and missing operators/values are recovered
in-place and reported as `Diagnostic` values. A block's children include its
brace tokens and trivia, while list items without an operator are represented by
`SyntaxKind.LIST_ITEM`.

Run the dependency-free smoke test after compiling with JDK 21:

```text
javac -d target/classes $(find src/main/java src/test/java -name '*.java')
java -cp target/classes com.xenoamess.kaishek.syntax.ParserSelfTest
```

To exercise the checked-in mod corpus (when it is available), run the
byte-preserving corpus smoke test from the repository root:

```text
java -cp 'open_kaishek/kaishek-syntax/target/classes;open_kaishek/kaishek-syntax/target/test-classes' \
  com.xenoamess.kaishek.syntax.ParserCorpusRoundTripSelfTest --root mod_zhongguo_style
```

The test also covers CK3 GUI declaration forms and expected recovery
diagnostics.  An absent corpus is reported as `SKIP`; use `--require-corpus`
when the corpus is a required input for CI.
