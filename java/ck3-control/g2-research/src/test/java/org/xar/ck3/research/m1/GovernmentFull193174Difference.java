package org.xar.ck3.research.m1;

import java.io.BufferedReader;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.regex.Pattern;

public class GovernmentFull193174Difference {

    private static final String[] CASE_IDS = {"inline80", "heap4"};

    private static final String[] COMMON_FIELDS = {
        "ret.rip", "ret.rsp",
        "v.rax", "v.rcx", "v.rdx", "v.r8", "v.r9", "v.r10", "v.r11",
        "xmm0.lo", "xmm0.hi", "xmm1.lo", "xmm1.hi", "xmm2.lo", "xmm2.hi", "xmm3.lo", "xmm3.hi", "xmm4.lo", "xmm4.hi", "xmm5.lo", "xmm5.hi",
        "n.rbx", "n.rbp", "n.rsi", "n.rdi", "n.r12", "n.r13", "n.r14", "n.r15", "xmm6.lo", "xmm6.hi",
        "mem.row.q0", "mem.row.d8", "mem.row.dc", "mem.manager.q30", "mem.manager.d3c", "mem.manager.d48",
        "mem.string.q10", "mem.string.q18", "mem.string.data", "mem.context.mode", "mem.context.mask", "mem.context.table", "mem.hit.magic",
        "stack.ret", "stack.m08", "stack.p08", "stack.p10", "stack.m30", "stack.m28", "stack.m38", "stack.m60", "stack.m58", "stack.m50", "stack.m48", "stack.m40", "stack.m18"
    };

    private static final String[] INLINE80_ONLY_FIELDS = {
        "bucket0.d4", "bucket0.d8", "bucket0.dc", "bucket0.q10"
    };

    private static final String[] HEAP4_ONLY_FIELDS = {
        "mem.context.counter", "bucket0.d4", "bucket0.d8", "bucket0.dc", "bucket0.q10", "bucket1.d4", "bucket1.d8", "bucket1.dc", "bucket1.q10"
    };

    // Pointer-capable fields (can be symbols or 16 hex)
    private static final Set<String> POINTER_CAPABLE_FIELDS = Set.of(
        "ret.rip", "ret.rsp",
        "v.r10",
        "mem.row.q0", "mem.manager.q30", "mem.context.table",
        "bucket0.q10", "bucket1.q10",
        "stack.ret", "stack.m30", "stack.m60", "stack.m50", "stack.m48"
    );

    // Vector fields (always 16 hex)
    private static final Set<String> VECTOR_FIELDS = Set.of(
        "xmm0.lo", "xmm0.hi", "xmm1.lo", "xmm1.hi", "xmm2.lo", "xmm2.hi", "xmm3.lo", "xmm3.hi", "xmm4.lo", "xmm4.hi", "xmm5.lo", "xmm5.hi", "xmm6.lo", "xmm6.hi"
    );

    // Non-pointer hex fields with specific widths
    // 16 hex: mem.string.q10, mem.string.q18, v.rax, v.rcx, v.rdx, v.r8, v.r9, v.r11, n.rbx, n.rbp, n.rsi, n.rdi, n.r12, n.r13, n.r14, n.r15, stack.m08, stack.p08, stack.p10, stack.m28, stack.m38, stack.m58, stack.m40
    // 8 hex: mem.row.d8, mem.row.dc, mem.manager.d3c, mem.manager.d48, mem.context.mask, mem.hit.magic, stack.m18, bucket0.d4, bucket0.d8, bucket0.dc, bucket1.d4, bucket1.d8, bucket1.dc, mem.context.counter
    // 2 hex: mem.context.mode
    // mem.string.data: 2 hex (inline80) or 8 hex (heap4)

    private static final Set<String> HEX16_FIELDS = Set.of(
        "v.rax", "v.rcx", "v.rdx", "v.r8", "v.r9", "v.r11",
        "n.rbx", "n.rbp", "n.rsi", "n.rdi", "n.r12", "n.r13", "n.r14", "n.r15",
        "mem.string.q10", "mem.string.q18",
        "stack.m08", "stack.p08", "stack.p10", "stack.m28", "stack.m38", "stack.m58", "stack.m40"
    );

    private static final Set<String> HEX8_FIELDS = Set.of(
        "mem.row.d8", "mem.row.dc", "mem.manager.d3c", "mem.manager.d48",
        "mem.context.mask", "mem.hit.magic",
        "stack.m18", "bucket0.d4", "bucket0.d8", "bucket0.dc", "bucket1.d4", "bucket1.d8", "bucket1.dc",
        "mem.context.counter"
    );

    private static final Set<String> HEX2_FIELDS = Set.of(
        "mem.context.mode"
    );

    private static final String STRING_DATA_FIELD = "mem.string.data";

    private static final Set<String> SYMBOLS = Set.of(
        "ROW", "CTX", "MGR", "ROWS", "Q", "DATA", "TABLE", "HIT", "RETURN", "BUCKET0", "BUCKET1", "OTHER"
    );

    private static final Pattern IMG_PATTERN = Pattern.compile("^IMG\\+[0-9A-F]+$");
    private static final Pattern SP_PATTERN = Pattern.compile("^SP[+-][0-9A-F]+$");
    private static final Pattern HEX16_PATTERN = Pattern.compile("^[0-9A-F]{16}$");
    private static final Pattern HEX8_PATTERN = Pattern.compile("^[0-9A-F]{8}$");
    private static final Pattern HEX2_PATTERN = Pattern.compile("^[0-9A-F]{2}$");

    public static void main(String[] args) {
        if (args.length != 2) {
            throw new IllegalArgumentException("Usage: GovernmentFull193174Difference <native.wire> <java.wire>");
        }

        String nativePath = args[0];
        String javaPath = args[1];

        Map<String, Map<String, String>> nativeData = parseWire(nativePath);
        Map<String, Map<String, String>> javaData = parseWire(javaPath);

        validateAndCompare(nativeData, javaData);

        System.out.println("OK: 2 cases, " + totalFieldsCompared + " fields compared");
    }

    private static int totalFieldsCompared = 0;

    private static Map<String, Map<String, String>> parseWire(String path) {
        Map<String, Map<String, String>> data = new HashMap<>();
        try {
            Path p = Path.of(path);
            try (BufferedReader br = Files.newBufferedReader(p, StandardCharsets.UTF_8)) {
                String line;
                while ((line = br.readLine()) != null) {
                    if(!line.equals(line.strip())||line.contains("  "))throw new IllegalArgumentException("Noncanonical whitespace");
                    if (line.isEmpty()) {
                        throw new IllegalArgumentException("Blank line in input");
                    }
                    String[] tokens = line.split(" ", -1);
                    if(!tokens[0].equals("case="+CASE_IDS[data.size()<2?data.size():1])||data.size()>=2)throw new IllegalArgumentException("Exact ordered cases required");
                    if (tokens.length < 1) {
                        throw new IllegalArgumentException("Empty line");
                    }
                    String caseId = null;
                    Map<String, String> caseMap = new HashMap<>();
                    for (String token : tokens) {
                        int eqIdx = token.indexOf('=');
                        if (eqIdx < 0) {
                            throw new IllegalArgumentException("Malformed token: " + token);
                        }
                        String key = token.substring(0, eqIdx);
                        String value = token.substring(eqIdx + 1);
                        if (key.equals("case")) {
                            if (caseId != null) {
                                throw new IllegalArgumentException("Duplicate case id in line");
                            }
                            caseId = value;
                        } else {
                            if (caseMap.containsKey(key)) {
                                throw new IllegalArgumentException("Duplicate field: " + key);
                            }
                            caseMap.put(key, value);
                        }
                    }
                    if (caseId == null) {
                        throw new IllegalArgumentException("Missing case id in line");
                    }
                    if (!Set.of(CASE_IDS[0], CASE_IDS[1]).contains(caseId)) {
                        throw new IllegalArgumentException("Unknown case id: " + caseId);
                    }
                    if (data.containsKey(caseId)) {
                        throw new IllegalArgumentException("Duplicate case id: " + caseId);
                    }
                    data.put(caseId, caseMap);
                }
            }
        } catch (IOException e) {
            throw new RuntimeException("IO Error: " + e.getMessage());
        }
        return data;
    }

    private static void validateAndCompare(Map<String, Map<String, String>> nativeData, Map<String, Map<String, String>> javaData) {
        // Check case presence
        for (String caseId : CASE_IDS) {
            if (!nativeData.containsKey(caseId)) {
                throw new IllegalArgumentException("Missing case in native: " + caseId);
            }
            if (!javaData.containsKey(caseId)) {
                throw new IllegalArgumentException("Missing case in java: " + caseId);
            }
        }

        // Check for extra cases
        if (nativeData.size() != CASE_IDS.length) {
            throw new IllegalArgumentException("Extra cases in native");
        }
        if (javaData.size() != CASE_IDS.length) {
            throw new IllegalArgumentException("Extra cases in java");
        }

        for (String caseId : CASE_IDS) {
            Map<String, String> nativeCase = nativeData.get(caseId);
            Map<String, String> javaCase = javaData.get(caseId);

            // Determine expected fields for this case
            Set<String> expectedFields = new HashSet<>(Set.of(COMMON_FIELDS));
            if (caseId.equals("inline80")) {
                expectedFields.addAll(Set.of(INLINE80_ONLY_FIELDS));
            } else if (caseId.equals("heap4")) {
                expectedFields.addAll(Set.of(HEAP4_ONLY_FIELDS));
            }

            // Check for missing fields
            for (String field : expectedFields) {
                if (!nativeCase.containsKey(field)) {
                    throw new IllegalArgumentException("Missing field in native: " + caseId + "," + field);
                }
                if (!javaCase.containsKey(field)) {
                    throw new IllegalArgumentException("Missing field in java: " + caseId + "," + field);
                }
            }

            // Check for extra fields
            for (String field : nativeCase.keySet()) {
                if (!expectedFields.contains(field)) {
                    throw new IllegalArgumentException("Unknown field in native: " + caseId + "," + field);
                }
            }
            for (String field : javaCase.keySet()) {
                if (!expectedFields.contains(field)) {
                    throw new IllegalArgumentException("Unknown field in java: " + caseId + "," + field);
                }
            }

            // Compare values
            for (String field : expectedFields) {
                String nativeVal = nativeCase.get(field);
                String javaVal = javaCase.get(field);

                // Validate syntax
                validateValue(field, nativeVal, caseId);
                validateValue(field, javaVal, caseId);

                // Compare
                if (!nativeVal.equals(javaVal)) {
                    throw new IllegalArgumentException("Mismatch: " + caseId + "," + field + " native=" + nativeVal + " java=" + javaVal);
                }
                totalFieldsCompared++;
            }
        }
    }

    private static void validateValue(String field, String value, String caseId) {
        if (value == null || value.isEmpty()) {
            throw new IllegalArgumentException("Empty value for " + field);
        }

        if (POINTER_CAPABLE_FIELDS.contains(field)) {
            if (SYMBOLS.contains(value)) {
                // Valid symbol
            } else if (IMG_PATTERN.matcher(value).matches()) {
                // Valid IMG symbol
            } else if (SP_PATTERN.matcher(value).matches()) {
                // Valid SP symbol
            } else if (HEX16_PATTERN.matcher(value).matches()) {
                // Valid hex
            } else {
                throw new IllegalArgumentException("Invalid pointer value for " + field + ": " + value);
            }
        } else if (VECTOR_FIELDS.contains(field)) {
            if (!HEX16_PATTERN.matcher(value).matches()) {
                throw new IllegalArgumentException("Invalid vector value for " + field + ": " + value);
            }
        } else if (HEX16_FIELDS.contains(field)) {
            if (!HEX16_PATTERN.matcher(value).matches()) {
                throw new IllegalArgumentException("Invalid hex16 value for " + field + ": " + value);
            }
        } else if (HEX8_FIELDS.contains(field)) {
            if (!HEX8_PATTERN.matcher(value).matches()) {
                throw new IllegalArgumentException("Invalid hex8 value for " + field + ": " + value);
            }
        } else if (HEX2_FIELDS.contains(field)) {
            if (!HEX2_PATTERN.matcher(value).matches()) {
                throw new IllegalArgumentException("Invalid hex2 value for " + field + ": " + value);
            }
        } else if (field.equals(STRING_DATA_FIELD)) {
            if (caseId.equals("inline80")) {
                if (!HEX2_PATTERN.matcher(value).matches()) {
                    throw new IllegalArgumentException("Invalid string.data value for inline80: " + value);
                }
            } else if (caseId.equals("heap4")) {
                if (!HEX8_PATTERN.matcher(value).matches()) {
                    throw new IllegalArgumentException("Invalid string.data value for heap4: " + value);
                }
            }
        } else {
            throw new IllegalArgumentException("Unclassified field: " + field);
        }
    }
}
