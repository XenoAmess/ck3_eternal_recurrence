package org.xar.ck3.control.contracts;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Set;

/** OS inode and Unix nanoseconds; never interpreted as custody FILE_ID_INFO or FILETIME. */
public record FileStatIdentity(BigInteger bytes, String fileId, String mtimeNs) {
    public static final String SCHEMA = "xar.file-stat-identity.os-ns-decimal.v1";
    public FileStatIdentity {
        StrictJson.require(bytes != null && bytes.signum() >= 0, "nonnegative exact OS size");
        decimal(fileId, false); decimal(mtimeNs, true);
    }
    private static void decimal(String value, boolean signed) {
        StrictJson.require(value != null && value.length() <= 64
                && value.matches(signed ? "0|-?[1-9][0-9]*" : "0|[1-9][0-9]*"),
                "canonical OS decimal text required");
    }
    public static FileStatIdentity fromJson(JsonNode value, String schema) {
        StrictJson.require(SCHEMA.equals(schema), "explicit OS stat/ns-decimal schema required");
        ObjectNode row = StrictJson.object(value, Set.of("bytes", "file_id", "mtime_ns"));
        JsonNode size = row.get("bytes");
        StrictJson.require(size != null && size.isIntegralNumber() && size.bigIntegerValue().signum() >= 0,
                "nonnegative exact OS integer size");
        return new FileStatIdentity(size.bigIntegerValue(), StrictJson.text(row.get("file_id")),
                StrictJson.text(row.get("mtime_ns")));
    }
    public ObjectNode toJson() {
        ObjectNode row = StrictJson.object();
        row.put("bytes", bytes); row.put("file_id", fileId); row.put("mtime_ns", mtimeNs);
        return row;
    }
}
