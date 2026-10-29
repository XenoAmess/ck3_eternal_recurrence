package org.xar.ck3.control.contracts.projection;

public final class ProjectionProtocolException extends IllegalArgumentException {
    private static final long serialVersionUID = 1L;
    private final ProjectionError.Code code;
    public ProjectionProtocolException(ProjectionError.Code code, String message) { super(message); this.code = code; }
    public ProjectionError.Code code() { return code; }
}
