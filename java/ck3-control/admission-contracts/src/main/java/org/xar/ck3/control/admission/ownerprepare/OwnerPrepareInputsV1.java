package org.xar.ck3.control.admission.ownerprepare;

import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.control.contracts.StrictJson;

/**
 * Validated preparation inputs only. Construction grants no Task, OS, recovery,
 * reducer, Game, source-file or persistence qualification.
 *
 * <p>The nullable pythonpath is required on the JSON boundary. Empty arguments
 * and an empty pythonpath are legal; argument boundaries and text are preserved.
 */
public record OwnerPrepareInputsV1(
        String machineId,
        OwnerRoleV1 role,
        List<String> stageArgs,
        String pythonpath,
        boolean enableDriverStateWal) {

    public static final int MAX_STAGE_ARGUMENTS = 128;

    public OwnerPrepareInputsV1 {
        StrictJson.require(machineId != null && !pythonWhitespaceOnly(machineId)
                && machineId.indexOf('\0') < 0,
                "owner machine_id must be a nonempty string");
        unicode(machineId);
        StrictJson.require(role != null, "exact admitted production role required");
        StrictJson.require(stageArgs != null && stageArgs.size() <= MAX_STAGE_ARGUMENTS,
                "owner stage_args must be a bounded list or tuple of strings");
        List<String> snapshot = new ArrayList<>(stageArgs);
        StrictJson.require(snapshot.size() <= MAX_STAGE_ARGUMENTS,
                "owner stage_args must be a bounded list or tuple of strings");
        for (String argument : snapshot) {
            StrictJson.require(argument != null && argument.indexOf('\0') < 0,
                    "owner stage_args must contain only strings without NUL");
            unicode(argument);
        }
        stageArgs = List.copyOf(snapshot);
        StrictJson.require(pythonpath == null || pythonpath.indexOf('\0') < 0,
                "owner pythonpath must be a string or None");
        if (pythonpath != null) {
            unicode(pythonpath);
        }
        StrictJson.require(!enableDriverStateWal || role == OwnerRoleV1.SDK_OWNER,
                "WAL opt-in requires a boolean and the sdk_owner role");
    }

    private static void unicode(String value) {
        for (int index = 0; index < value.length(); index++) {
            char current = value.charAt(index);
            if (Character.isHighSurrogate(current)) {
                StrictJson.require(index + 1 < value.length()
                        && Character.isLowSurrogate(value.charAt(index + 1)),
                        "well-formed Unicode required on the JSON boundary");
                index++;
            } else {
                StrictJson.require(!Character.isLowSurrogate(current),
                        "well-formed Unicode required on the JSON boundary");
            }
        }
    }

    // Python str.strip() recognizes these additional separators beyond Java's
    // Character.isWhitespace; preserve the actual producer's blankness rule.
    private static boolean pythonWhitespaceOnly(String value) {
        return value.codePoints().allMatch(OwnerPrepareInputsV1::pythonWhitespace);
    }

    private static boolean pythonWhitespace(int codePoint) {
        return codePoint >= 0x09 && codePoint <= 0x0d
                || codePoint >= 0x1c && codePoint <= 0x20
                || codePoint == 0x85 || codePoint == 0xa0 || codePoint == 0x1680
                || codePoint >= 0x2000 && codePoint <= 0x200a
                || codePoint == 0x2028 || codePoint == 0x2029 || codePoint == 0x202f
                || codePoint == 0x205f || codePoint == 0x3000;
    }
}
