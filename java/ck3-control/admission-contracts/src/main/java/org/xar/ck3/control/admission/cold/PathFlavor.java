package org.xar.ck3.control.admission.cold;

import org.xar.ck3.control.contracts.StrictJson;

/** Explicit source-platform pathlib semantics, independent of the executing JVM filesystem. */
public enum PathFlavor {
    WINDOWS, POSIX;

    public boolean isAbsolute(String path) {
        StrictJson.require(path != null, "source path required");
        if (this == POSIX) { return path.startsWith("/"); }
        String normalized = path.replace('/', '\\');
        if (normalized.length() >= 3 && normalized.charAt(1) == ':'
                && normalized.charAt(2) == '\\') { return true; }
        if (!normalized.startsWith("\\\\")) { return false; }
        int serverStart = normalized.regionMatches(true, 0, "\\\\?\\UNC\\", 0, 8) ? 8 : 2;
        int serverEnd = normalized.indexOf('\\', serverStart);
        if (serverEnd <= serverStart) { return false; }
        int shareEnd = normalized.indexOf('\\', serverEnd + 1);
        if (shareEnd < 0) { shareEnd = normalized.length(); }
        return shareEnd > serverEnd + 1;
    }
}
