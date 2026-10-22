package org.xar.ck3.control.contracts;

public final class ContractViolationException extends IllegalArgumentException {
    private static final long serialVersionUID = 1L;
    public ContractViolationException(String message) { super(message); }
    public ContractViolationException(String message, Throwable cause) { super(message, cause); }
}
