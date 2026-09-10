package com.xenoamess.ck3coa;

public final class McpGatewayException extends RuntimeException {
    public McpGatewayException(String message) {
        super(message);
    }

    public McpGatewayException(String message, Throwable cause) {
        super(message, cause);
    }
}
