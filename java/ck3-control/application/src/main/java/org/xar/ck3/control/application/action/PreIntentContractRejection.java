package org.xar.ck3.control.application.action;

import java.util.Objects;

/** Typed signal for a proven pre-Intent preparation contract rejection. */
@SuppressWarnings("serial")
public final class PreIntentContractRejection extends RuntimeException {
    private static final long serialVersionUID = 1L;
    private final ActionCommand command;

    PreIntentContractRejection(ActionCommand command, IllegalArgumentException cause) {
        super(ActionCoordinator.diagnostic("pre-intent preparation contract rejection", cause), cause);
        this.command = Objects.requireNonNull(command);
    }

    public ActionCommand command() { return command; }
}