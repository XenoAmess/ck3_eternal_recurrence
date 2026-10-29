package org.xar.ck3.control.application.checkpoint;

import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** The common loop never guesses a SAVE primitive, eligibility or expected native values. */
public final class CheckpointRequestFactory {
    public static final String OBSERVER_SCHEMA = "xar.java-checkpoint-poststate/v1";
    private final Path savePath; private final CheckpointRequest.ObservationPort observations;
    public CheckpointRequestFactory(Path savePath, CheckpointRequest.ObservationPort observations) { this.savePath = savePath; this.observations = observations; }
    public CheckpointRequest prepare(ObservationIdentity before, G2Source source, String sessionId, Optional<CheckpointPair> baseline, Instant deadline) throws InterruptedException {
        return prepare(before,source,sessionId,baseline,deadline,"save-"+UUID.randomUUID());
    }
    /** The actual planner supplies its retained decision ID; only this factory constructs the original command. */
    public CheckpointRequest prepare(ObservationIdentity before,G2Source source,String sessionId,Optional<CheckpointPair> baseline,
            Instant deadline,String originalActionId)throws InterruptedException {
        var ready = observations.observeForPreparation(before, deadline);
        StrictJson.require(ready.observed().equals(before) && ready.source().equals(source) && ready.sessionId().equals(sessionId)
                && ready.mapReady() && ready.paused() && ready.saveEligible(), "fresh native SAVE readiness changed or unresolved player/lifecycle decision");
        List<ExpectedValue> expected = List.of(new ExpectedInteger(new FieldKey("date_raw"), before.frame().identity().dateRaw()),
                new ExpectedInteger(new FieldKey("played_character_id"), before.frame().identity().player()), new ExpectedBoolean(new FieldKey("checkpoint_pair_verified"), true));
        ActionCommand command = new ActionCommand(originalActionId, before, source, sessionId, new OperationKey("save-checkpoint"),
                new OpportunityJson.Obj(Map.of()), new ExpectedPostcondition(1, before, source, OBSERVER_SCHEMA, expected),
                new Claims(Set.of(), Set.of(), Set.of(), Set.of()), deadline);
        return new CheckpointRequest(command, savePath, ready.lineageId(), baseline);
    }
}
