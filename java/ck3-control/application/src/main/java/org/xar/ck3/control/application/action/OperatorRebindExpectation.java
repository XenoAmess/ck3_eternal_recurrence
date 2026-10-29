package org.xar.ck3.control.application.action;

import java.util.Objects;
import org.xar.ck3.control.application.planning.identity.OperatorPlayerSwitch;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;

/** Identity-only expectation. DATA does not qualify a source, persist a rebind or grant a native permit. */
public record OperatorRebindExpectation(CommandOrigin origin, G2Source source,
        OperatorPlayerSwitch.Request request, String episodeRunId, long episodeEpoch, ExactRef beforeDriver) {
    public static final String SCHEMA = "xar.java.operator-rebind-expectation/v1";
    public OperatorRebindExpectation {
        Objects.requireNonNull(origin); Objects.requireNonNull(source); Objects.requireNonNull(request);
        StrictJson.text(episodeRunId); StrictJson.safe(episodeEpoch, 0); Objects.requireNonNull(beforeDriver);
        StrictJson.require(beforeDriver.bytes() > 0 && origin.machineId().equals(source.machineId()), "actual same-machine operator before/source required");
        if (origin instanceof CommandOrigin.Gameplay gameplay) {
            StrictJson.require(gameplay.before().frame().episodeRunId().equals(episodeRunId)
                    && gameplay.before().frame().revision().equals(request.expectedRevision()), "operator gameplay before revision/run mismatch");
        } else {
            StrictJson.require(origin instanceof CommandOrigin.LifecycleTerminal, "operator requires an actual gameplay or terminal source, never frontend/reconciliation");
            var identity = origin.requireLifecycleTerminal();
            StrictJson.require(identity.subject().episodeRunId().equals(episodeRunId)
                    && identity.subject().episodeEpoch() == episodeEpoch && identity.frame().revision().equals(request.expectedRevision())
                    && identity.evidence().originalDriver().equals(beforeDriver), "operator terminal before driver/revision/run/epoch mismatch");
        }
    }
    public void validateCommand(ActionCommand command) {
        StrictJson.require(command.origin().equals(origin) && command.source().equals(source)
                && command.expectation().equals(new CommandExpectation.OperatorRebind(this))
                && command.operation().value().equals(request.step())
                && command.protocolIdentity() instanceof ProtocolRequestIdentity.BodyDerived,
                "operator changed its exact original command/source/request/expectation");
        StrictJson.require(command.claims().armyIds().isEmpty() && command.claims().allyCharacterIds().isEmpty()
                && command.claims().characterIds().isEmpty() && command.claims().commitmentKeys().isEmpty(), "operator rebind has no ordinary gameplay resource claims");
    }
    public void validateCompletion(OperatorPlayerSwitch.Completion actual) {
        StrictJson.require(actual.request().equals(request) && actual.source().equals(source)
                && actual.episodeRunId().equals(episodeRunId) && actual.episodeEpoch() == episodeEpoch
                && actual.originals().beforeDriver().equals(beforeDriver)
                && (!actual.rebindPerformed() || actual.beforeDriverVersion() < StrictJson.MAX_SAFE_INTEGER)
                && actual.afterDriverVersion() == actual.beforeDriverVersion() + (actual.rebindPerformed() ? 1 : 0),
                "operator completion changed its request, original driver, episode/epoch or exact version transition");
    }
}
