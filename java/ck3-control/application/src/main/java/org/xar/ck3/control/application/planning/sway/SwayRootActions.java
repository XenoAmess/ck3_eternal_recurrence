package org.xar.ck3.control.application.planning.sway;

import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** One actual dynamic Start family and one selected Stop action/replay pair for the Root inventory. */
public final class SwayRootActions {
    public record Target(long characterId) { public Target { SwayNativeWire.actionCharacter(characterId); } }
    public record Sources(ExactRef preparation, ExactRef decoder, ExactRef observerAndReplay) {
        public Sources { for (ExactRef source : List.of(preparation, decoder, observerAndReplay)) StrictJson.require(source.bytes() > 0, "actual Sway executable source closure required"); }
    }
    private final RootExecutableBindings.Family<Target> starts;
    private final RootExecutableBindings.ActionBinding stop;
    private final NativeRecordedEvidenceVerifier.Binding stopReplay;
    private RootExecutableBindings catalog;
    public SwayRootActions(SwayActionLifecycle lifecycle, Sources sources) {
        Objects.requireNonNull(lifecycle); Objects.requireNonNull(sources);
        starts = new RootExecutableBindings.Family<>("sway-start-actual4/v1", Target.class, ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, Optional.empty(), sources.preparation(), sources.decoder(), sources.observerAndReplay(),
                value -> { var row = StrictJson.object(); row.put("target_character_id", value.characterId()); return new RawJson(StrictJson.canonical(row)); },
                value -> new OperationKey(SwayNativeWire.START + value.characterId()), value -> {
                    OperationKey operation = new OperationKey(SwayNativeWire.START + value.characterId());
                    return new RootExecutableBindings.IssuedAction(new RootExecutableBindings.ActionBinding(lifecycle.start(operation, sources.preparation()), ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, Optional.empty(), sources.decoder()), lifecycle.recorded(operation, sources.observerAndReplay()));
                });
        stop = new RootExecutableBindings.ActionBinding(lifecycle.stop(sources.preparation()), ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, Optional.empty(), sources.decoder());
        stopReplay = lifecycle.recorded(new OperationKey(SwayNativeWire.STOP), sources.observerAndReplay());
    }
    public RootExecutableBindings.Family<Target> startFamily() { return starts; }
    public RootExecutableBindings.ActionBinding selectedStop() { return stop; }
    public NativeRecordedEvidenceVerifier.Binding selectedStopReplay() { return stopReplay; }
    public synchronized void attach(RootExecutableBindings actual) {
        Objects.requireNonNull(actual); StrictJson.require(catalog == null || catalog == actual, "Sway action catalog cannot be rebound");
        StrictJson.require(actual.families().stream().anyMatch(family -> family == starts) && actual.actionBindings().stream().anyMatch(binding -> binding == stop)
                && actual.archivedBindings().stream().anyMatch(binding -> binding == stopReplay), "actual frozen Root lacks the identical Sway executable/replay objects"); catalog = actual;
    }
    public synchronized RootExecutableBindings.ActionBinding issueStart(long target) {
        if (catalog == null) throw new IllegalStateException("actual Sway action inventory is not attached"); return catalog.issue(starts, new Target(target));
    }
    public synchronized RootExecutableBindings.ActionBinding issueStop() {
        if (catalog == null) throw new IllegalStateException("actual Sway action inventory is not attached"); return stop;
    }
}
