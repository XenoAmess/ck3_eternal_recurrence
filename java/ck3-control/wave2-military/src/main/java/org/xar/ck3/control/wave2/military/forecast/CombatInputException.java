package org.xar.ck3.control.wave2.military.forecast;

/** A malformed or source-inconsistent combat input, distinct from an unresolved trial. */
public final class CombatInputException extends IllegalArgumentException {
    private static final long serialVersionUID = 1L;
    public CombatInputException(String message) { super(message); }
    public CombatInputException(String message, Throwable cause) { super(message, cause); }
}
