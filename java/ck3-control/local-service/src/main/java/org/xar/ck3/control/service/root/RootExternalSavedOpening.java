package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Instant;
import java.util.Objects;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort;
import org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort.Received;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.platform.ManagedGameSession;
import org.xar.ck3.control.platform.NativeLaunchPlan;
import org.xar.ck3.control.platform.NativeSavedGameClone;

/** Actual named-save opening DATA. The writer separately admits the predecessor and the gameplay branch. */
public final class RootExternalSavedOpening {
    record Read(ExactRef acknowledgement, ExactRef nativeFrame, String receiveOrder, Instant receivedAt) { }
    record Originals(FileWitness namedSave, FileWitness loadedCopy, Read first, Read second) { }

    private final ManagedGameSession owner;
    private final NativeSavedGameClone.Observation clone;
    private final Received first;
    private final Received second;

    private RootExternalSavedOpening(ManagedGameSession owner, NativeSavedGameClone.Observation clone,
            Received first, Received second) {
        this.owner = owner;
        this.clone = clone;
        this.first = first;
        this.second = second;
    }

    static RootExternalSavedOpening capture(ManagedGameSession owner, GameGeneration departed,
            FileWitness namedSave, long rawDate, NativeCharacterId actor, Instant deadline)
            throws IOException, InterruptedException {
        Objects.requireNonNull(owner);
        Objects.requireNonNull(departed);
        Objects.requireNonNull(namedSave);
        Objects.requireNonNull(actor);
        Objects.requireNonNull(deadline);
        StrictJson.require(!owner.generation().equals(departed)
                && owner.launchPlan().preparedProfile().declaration() instanceof NativeLaunchPlan.PreparedProfile.NoMods,
                "named save requires its replacement Game and explicit vanilla profile");
        owner.verify();
        var transport = owner.nativeTransport();
        var clone = NativeSavedGameClone.observe(owner.launchPlan(), namedSave);
        StrictJson.require(!clone.inPlace(), "named save requires a distinct materialized load copy");
        var session = transport.awaitHello(deadline);
        var first = read(transport, deadline);
        var second = read(transport, deadline);
        NativeFreshSnapshotPort.verifyOriginal(first.acknowledgement(), first.originalFrame(), first.snapshotReceived());
        NativeFreshSnapshotPort.verifyAfter(first.acknowledgement(), second);
        RestoreCheckpointService.requireStableReadProgression(first.originalFrame(), second.originalFrame());
        StrictJson.require(first.originalFrame().session().equals(session)
                && session.game().equals(owner.generation()) && session.machineId().equals(owner.machineId())
                && session.sessionId().equals(owner.sessionId()), "named save frame crossed its actual successor");
        requireMap(second.originalFrame(), rawDate, actor);
        var opening = new RootExternalSavedOpening(owner, clone, first, second);
        opening.requireCurrent(transport);
        return opening;
    }

    private static Received read(NativeGameTransport transport, Instant deadline) throws IOException, InterruptedException {
        if (transport.readFreshFullState(deadline) instanceof Received actual) return actual;
        throw new IOException("named save opening requires an independent original Full READ");
    }

    private static void requireMap(ObservedFrame frame, long rawDate, NativeCharacterId actor) {
        var state = FullJsonTree.parse(frame.state().bytes(), FullJsonTree.MAXIMUM_BYTES);
        var character = state.path("played_character");
        StrictJson.require(state.path("map_ready").isBoolean() && state.path("map_ready").booleanValue()
                && state.path("paused").isBoolean() && state.path("paused").booleanValue()
                && character.path("alive").isBoolean() && character.path("alive").booleanValue()
                && StrictJson.integer(state.get("date_raw"), 0, StrictJson.MAX_SAFE_INTEGER) == rawDate
                && NativeCharacterId.fromJson(character.get("character_id")).equals(actor),
                "named save opening requires its observed paused living actor and exact date");
    }

    public ObservedFrame frame() { return second.originalFrame(); }

    public void requireCurrent(NativeGameTransport actual) throws IOException {
        owner.verify();
        StrictJson.require(owner.nativeTransport() == actual
                && frame().session().connectionGeneration().equals(actual.originalHello().connectionGeneration()),
                "named save opening crossed its held successor and connection");
        clone.requireCurrent(owner.launchPlan(), clone.originalSave());
    }

    Originals preserve(Session same, ActionPorts.OutcomeArchive archive) throws IOException {
        requireCurrent(owner.nativeTransport());
        var bound = archive.withSession(same);
        var firstRead = preserve(bound, first);
        var secondRead = preserve(bound, second);
        return new Originals(clone.originalSave(), clone.actualSave(), firstRead, secondRead);
    }

    private static Read preserve(ActionPorts.OutcomeArchive archive, Received received) {
        return new Read(archive.preserve(received.acknowledgement()),
                archive.preserveNativeFrame(received.originalFrame()),
                received.snapshotReceived().order().toString(), received.snapshotReceived().observedAt());
    }
}
