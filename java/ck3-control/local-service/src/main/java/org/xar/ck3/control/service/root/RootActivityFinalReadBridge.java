package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.g2.m6.ActivityFinalState;
import org.xar.ck3.control.g2.m6.ActivityFinalState.*;
import org.xar.ck3.control.g2.m6.ActivityFinalStateCodec;
import org.xar.ck3.control.g2.m6.M6SourceProducer;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.capabilities.activity.ActivityNativeContracts;
import org.xar.ck3.control.nativebridge.capabilities.activity.ActivityPayload;
import org.xar.ck3.control.nativebridge.capabilities.activity.ActivityTerminalJournal;

/**
 * Root-only bridge from the unique private-minted Activity packet. It uses the
 * same held writer archive, installed decoder and original guard frame loader
 * for live consumption and cold replay. No second query, native codec or
 * collector is introduced, and application gains no reverse dependency on the Activity adapter.
 */
public final class RootActivityFinalReadBridge {
    private final ActivityNativeContracts.Installation installed;
    private final OutcomeArchive archive;
    private final NativeEffectEvidence.FrameLoader frames;

    public RootActivityFinalReadBridge(ActivityNativeContracts.Installation installed,
            OutcomeArchive archive, NativeEffectEvidence.FrameLoader frames) {
        this.installed = Objects.requireNonNull(installed);
        this.archive = Objects.requireNonNull(archive);
        this.frames = Objects.requireNonNull(frames);
    }

    /** Only this bridge can return this provenance-bearing wrapper. */
    public static final class Observed {
        private final State state;
        private final PlanningReadReceipt originalReceipt;
        private final Provenance provenance;
        private Observed(State state, PlanningReadReceipt originalReceipt, Provenance provenance) {
            this.state = state; this.originalReceipt = originalReceipt; this.provenance = provenance;
        }
        public State state() { return state; }
        public PlanningReadReceipt originalReceipt() { return originalReceipt; }
        public Provenance provenance() { return provenance; }
    }

    /** Caller already holds its canonical FEAST origin, after real Start replay. */
    public Observed observe(State before, ActivityNativeContracts.Packet packet,
            ObservationIdentity current, Session same) throws IOException {
        Objects.requireNonNull(before); Objects.requireNonNull(packet); Objects.requireNonNull(current);
        OutcomeArchive actual = archive.withSession(Objects.requireNonNull(same));
        Sample sample = sample(before.identity(), packet, current, same, actual,
                installed.contract(ActivityNativeContracts.Query.HOSTED).sourceRef());
        State state = ActivityFinalState.observe(before, sample);
        return new Observed(state, packet.receipt(), sample.provenance());
    }

    /** Every persisted sample is rebuilt from its actual original receipt; metadata cannot qualify itself. */
    public State restore(byte[] encoded, Session same) throws IOException {
        Objects.requireNonNull(same); OutcomeArchive actual = archive.withSession(same);
        try {
            return ActivityFinalStateCodec.decode(encoded, (identity, queried, provenance) -> {
                try {
                    PlanningReadReceipt original = actual.loadRead(provenance.originalRead());
                    StrictJson.require(actual.readReferenceOf(original).equals(provenance.originalRead()),
                            "Activity final archive locator changed");
                    var packet = installed.contract(ActivityNativeContracts.Query.HOSTED).decode(original);
                    Sample result = sample(identity, packet, queried, same, actual, provenance.producerSource());
                    StrictJson.require(result.provenance().equals(provenance), "Activity final source references changed");
                    return result;
                } catch (IOException failure) { throw new UncheckedIOException(failure); }
            });
        } catch (UncheckedIOException failure) { throw failure.getCause(); }
    }

    private Sample sample(Identity expected, ActivityNativeContracts.Packet packet,
            ObservationIdentity current, Session same, OutcomeArchive actual, ExactRef producerSource) throws IOException {
        PlanningReadReceipt read = packet.receipt();
        var contract = installed.contract(ActivityNativeContracts.Query.HOSTED);
        StrictJson.require(read.contractId().equals(contract.contractId())
                && read.request().operation().equals(contract.operation())
                && read.request().before().equals(current), "Activity final read is not the exact installed current hosted query");
        StrictJson.require(same.head().state().machineId().equals(current.machineId()),
                "Activity final observation belongs to another canonical writer machine");
        NativeRecordedEvidenceVerifier.requireRead(read, actual);
        // Preserve the original producer locator as DATA on restore; it is not a current-code qualification.
        Provenance provenance = new Provenance(actual.readReferenceOf(read), producerSource,
                read.before().binding().capabilityEvidence());
        var readPin = same.capturePin(provenance.originalRead(), StrictJson.EXPLICIT_MAX_BYTES);
        var helloPin = same.capturePin(provenance.helloSource(), StrictJson.EXPLICIT_MAX_BYTES);
        for (var guard : List.of(read.before(), read.after())) {
            RootGuardEvidence.requireHistory(guard.binding(), actual, same);
            var original = RootGuardEvidence.loadFrame(guard.binding(), actual, frames);
            StrictJson.require(original.identity().equals(current)
                    && original.fullBindingSha256().equals(guard.originalBindingSha256()),
                    "Activity final guard did not reconstruct the complete original frame");
        }
        var hello = ActivityNativeContracts.actualSource(packet);
        StrictJson.require(hello.gameSha256().equalsIgnoreCase(M6SourceProducer.EXE),
                "Activity final source is not the exact current .4 executable");
        StrictJson.require(packet.payload() instanceof ActivityPayload.Hosted,
                "typed Activity hosted payload required");
        ActivityPayload.Hosted hosted = (ActivityPayload.Hosted) packet.payload();
        var rows = hosted.hosted().stream().filter(row -> row.fullId() == expected.activityFullId()).toList();
        StrictJson.require(rows.size() <= 1, "duplicate complete Activity ID in the actual native enumeration");
        Instance instance;
        if (rows.isEmpty()) instance = retained(expected, hosted).orElseGet(Missing::new);
        else {
            var row = rows.getFirst();
            StrictJson.require(row.hostId() == expected.hostCharacterId() && row.typeKey().equals(expected.typeKey()),
                    "retained Activity full ID changed host or type");
            StrictJson.require(row.completed().isPresent() == row.invalidated().isPresent(),
                    "partial native Activity flag observation cannot qualify a final state");
            instance = row.completed().isPresent()
                    ? new Flags(row.completed().orElseThrow(), row.invalidated().orElseThrow(), row.completionStamp())
                    : new FlagsUnavailable(row.completionStamp());
        }
        same.verifyPin(readPin); same.verifyPin(helloPin);
        return new Sample(expected, current, instance, provenance);
    }

    /** Reuse only the existing decoded journal when the current full instance is absent.
     * Current hosted flags (including false/false) and unread hosted flags keep their own branches. */
    private static java.util.Optional<Instance> retained(Identity expected, ActivityPayload.Hosted hosted) {
        var observation = hosted.terminalJournal().orElse(null);
        if (!(observation instanceof ActivityTerminalJournal.Known known) || !known.journal().available())
            return java.util.Optional.empty();
        var records = known.journal().records();
        for (int index = records.size() - 1; index >= 0; index--) {
            var row = records.get(index);
            if (row.fullActivityId() != expected.activityFullId() || row.generation() != expected.generation()
                    || Integer.toUnsignedLong(row.hostId()) != expected.hostCharacterId()
                    || !new org.xar.ck3.control.planning.opportunity.OpportunityJson.Text(expected.typeKey())
                            .equals(row.original().get("type_key"))) continue;
            var fields = row.fields();
            if (fields.completed().filter(value -> value != 0).isEmpty()
                    && fields.invalidated().filter(value -> value != 0).isEmpty()) continue;
            return java.util.Optional.of(new RetainedFlags(fields.completed(), fields.invalidated(), fields.stamp(),
                    row.sequence(), row.frame().dateRaw()));
        }
        return java.util.Optional.empty();
    }
}
