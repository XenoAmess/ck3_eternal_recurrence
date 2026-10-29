package org.xar.ck3.control.g2.context;

/** One finite semantic/MCP envelope contract. A frame body and its full wire/owner containers have separate limits. */
public final class RootMcpEnvelope {
    public static final int SEMANTIC_BODY_MAX_BYTES = 8 * 1024 * 1024;
    public static final int CAPABILITIES_BODY_MAX_BYTES = 8 * 1024 * 1024;
    /** Includes the terminating LF. Pretty text and structured content can duplicate or expand the frame body. */
    public static final int RPC_LINE_MAX_BYTES = 32 * 1024 * 1024;
    public static final int OWNER_ROW_MAX_BYTES = G2RetainedNativeSourceProvider.MAX_NATIVE_ARTIFACT_BYTES;
    public static final long SESSION_RECEIVED_MAX_BYTES = 64L * 1024 * 1024;
    public static final long SESSION_SENT_MAX_BYTES = 64L * 1024 * 1024;
    private RootMcpEnvelope() { }

    public static void requireSemanticBody(int bytes) {
        require(bytes > 0 && bytes <= SEMANTIC_BODY_MAX_BYTES, "semantic structured-content token exceeds the finite 8 MiB body contract");
    }
    public static void requireCapabilitiesBody(int bytes) {
        require(bytes > 0 && bytes <= CAPABILITIES_BODY_MAX_BYTES, "capabilities structured-content token exceeds the finite 8 MiB body contract");
    }
    public static void requireRpcLine(int bytes) {
        require(bytes > 1 && bytes <= RPC_LINE_MAX_BYTES, "whole MCP line exceeds the finite 32 MiB contract including LF");
    }
    public static void requireOwnerRow(int bytes) {
        require(bytes > 0 && bytes <= OWNER_ROW_MAX_BYTES, "complete owner row exceeds the finite 32 MiB contract");
    }
    private static void require(boolean condition, String message) {
        if (!condition) { throw new IllegalArgumentException(message); }
    }
}
