# kaishek-cli

纯 Java/JVM 的批处理入口，不加载 Quarkus。构建：

```text
mvn -q package
java -jar target/kaishek-cli-0.1.0-SNAPSHOT.jar profile
java -jar target/kaishek-cli-0.1.0-SNAPSHOT.jar parse --file path/to/script.txt
java -jar target/kaishek-cli-0.1.0-SNAPSHOT.jar validate --profile ck3-1.19.0.6 --file path/to/script.txt
java -jar target/kaishek-cli-0.1.0-SNAPSHOT.jar hash --file path/to/script.txt
java -jar target/kaishek-cli-0.1.0-SNAPSHOT.jar corpus path/to/mod
```

所有命令输出稳定 JSON（`--help` 除外）。`parse` 保留输入字节并报告基础括号/字符串诊断；输出中的 `tokens` 是递归 CST 节点数（不是 lexer token 数）。`validate` 在提供已知 profile 与文件路径时执行当前静态 schema 检查，否则以 `semantic: "UNSUPPORTED"` 明示。`ck3-1.19.0.6-zg361` 目前只是 361 schema-only 别名，尚未接入语义验证。未知 profile、命令或尚未认证的语义返回 `status: "UNSUPPORTED"` 和非零退出码。`hash` 对单文件输出 SHA-256，对目录输出包含相对路径的确定性 corpus hash；`parse`/`hash` 的非现有位置参数按 UTF-8 内联文本处理，省略输入时读取 stdin。
