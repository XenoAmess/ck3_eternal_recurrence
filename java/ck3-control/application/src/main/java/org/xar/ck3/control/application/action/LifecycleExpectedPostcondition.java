package org.xar.ck3.control.application.action;

import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;

/** A canonical lifecycle composite's expectation cannot be an ordinary gameplay/day/SAVE claim. */
public record LifecycleExpectedPostcondition(LifecycleIdentity before, G2Source source, String observerSchema,
        Operation operation, List<ExpectedValue> values) {
    public static final String SCHEMA = "xar.java.lifecycle-terminal-expectation/v1";
    public enum Operation {
        DEATH_TERMINAL("death-terminal"), CONTINUE_SUCCESSOR("continue-as-reconciled-successor"), START_NEXT_EPISODE("start-next-episode"),
        CLOSE_DEATH_MODAL("continue-death-succession-modal-v1");
        private final OperationKey key;
        Operation(String key) { this.key = new OperationKey(key); }
        public OperationKey key() { return key; }
    }
    public LifecycleExpectedPostcondition {
        Objects.requireNonNull(before); Objects.requireNonNull(source); StrictJson.text(observerSchema); Objects.requireNonNull(operation);
        StrictJson.require(before.machineId().equals(source.machineId()), "lifecycle expectation source machine drift");
        values = List.copyOf(values); var keys = new HashSet<FieldKey>();
        for (ExpectedValue value : values) StrictJson.require(keys.add(value.field()), "duplicate lifecycle expected field");
        for (String field : List.of("native.gameplay_verified", "timeline.advance_verified", "timeline.checkpoint_eligible"))
            StrictJson.require(values.contains(new ExpectedBoolean(new FieldKey(field), false)), "lifecycle expectation must explicitly decline ordinary gameplay, day and SAVE credit");
        StrictJson.require(operation != Operation.CONTINUE_SUCCESSOR && operation != Operation.CLOSE_DEATH_MODAL || before.terminalReason() == LifecycleIdentity.TerminalReason.CHANGED
                && before.currentPlayer() instanceof LifecycleIdentity.Character player && player.alive(), "natural continuation needs an actual distinct living current player");
        StrictJson.require(operation != Operation.CLOSE_DEATH_MODAL || observerSchema.equals("xar.java.native-death-modal-close/v1")
                && values.contains(new ExpectedBoolean(new FieldKey("lifecycle.death_modal_cleared"), true)),
                "the one terminal native child requires its exact independently observed modal closure expectation");
    }
}
