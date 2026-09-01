package com.xenoamess.kaishek.runtime;

public final class DrawTapeExhaustedException extends RuntimeException {
    private static final long serialVersionUID = 1L;
    public DrawTapeExhaustedException(int position) { super("draw tape exhausted at position " + position); }
}
