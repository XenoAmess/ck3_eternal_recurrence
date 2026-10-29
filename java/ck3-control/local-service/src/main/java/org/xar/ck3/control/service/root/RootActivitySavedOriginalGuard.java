package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionEffects;
import org.xar.ck3.control.application.checkpoint.SavedAttachmentSourceStore;
import org.xar.ck3.control.application.checkpoint.SavedCheckpointMaterial;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.continuity.writer.WriterContracts.Pin;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.m6.ActivityFinalState;

/**
 * Reads the FEAST member of the genuinely restored ordinary Saved Head.
 * FIRST_BASELINE material is explicitly unavailable until its native continuity is proved.
 * A SavedOrigin proves historical custody only. It grants no native instance adoption,
 * new terminal observation, effect, retry, current readiness or replacement Game authority.
 */
public final class RootActivitySavedOriginalGuard {
    private static final int MAX_BYTES = 1_048_576;
    private RootActivitySavedOriginalGuard() { }

    public static SavedOrigin require(RootRuntimeContext context, Session same,
            RootRestorationOriginalProof.Original original, FeastDomainRuntime domain,
            FeastFinalSettlement settlement) throws IOException {
        Objects.requireNonNull(context); Objects.requireNonNull(original);
        Objects.requireNonNull(domain); Objects.requireNonNull(settlement);
        context.writer().requireSession(same);
        context.game().verify();
        requireRestoration(context, same, original);
        SavedBody saved = readSavedBody(same, original.originalSavedHead(), domain.registration().producerSources());
        var resolved = saved.ledger().resolved().orElseThrow(() ->
                new IOException("saved canonical FEAST member has no resolved original Start"));
        var origin = resolved.activity().orElseThrow(() ->
                new IOException("saved canonical FEAST member has no actual Activity origin"));
        ActionReceipt start = settlement.requireStart(same, origin.originalStart());
        var startAfter = ActionEffects.observation(start).orElseThrow();
        var savedFrame = original.pair().frame();
        StrictJson.require(startAfter.after().machineId().equals(savedFrame.machineId())
                && startAfter.after().game().equals(savedFrame.game())
                && startAfter.after().observationVersion() == savedFrame.observationVersion()
                && startAfter.after().frame().episodeRunId().equals(savedFrame.frame().episodeRunId())
                && startAfter.after().frame().identity().player().equals(savedFrame.frame().identity().player())
                && startAfter.after().frame().revision().compareTo(savedFrame.frame().revision()) <= 0
                && startAfter.after().frame().identity().nativeRevision().compareTo(savedFrame.frame().identity().nativeRevision()) <= 0
                && startAfter.after().frame().identity().dateRaw().compareTo(savedFrame.frame().identity().dateRaw()) <= 0,
                "saved FEAST Start differs from the actual SAVE Game/player/episode or occurs after SAVE");
        Optional<ActivityFinalState.State> retained = origin.finalState().isPresent()
                ? Optional.of(settlement.restore(same, origin)) : Optional.empty();
        saved.requireUnchanged(same);
        requireRestoration(context, same, original);
        return new SavedOrigin(original, saved, origin, start, retained);
    }

    private static void requireRestoration(RootRuntimeContext context, Session same,
            RootRestorationOriginalProof.Original original) throws IOException {
        context.writer().requireSession(same);
        StrictJson.require(original.game().equals(context.game().generation())
                && original.sessionId().equals(context.game().sessionId())
                && original.source().equals(context.source()),
                "saved FEAST proof crossed the actual replacement Game/session/source");
        original.requireImportPredecessor(same, same.head());
        var attachment = original.attachmentHead();
        same.requireDomainImportContinuation(attachment.sequence(), ContinuityJson.digest(attachment.toJson()));
        SavedCheckpointMaterial declared = original.material();
        if (declared.kind() != SavedCheckpointMaterial.Kind.ORDINARY
                || !(declared instanceof SavedAttachmentSourceStore.SavedMaterial material)) {
            throw new IOException("ordinary Saved FEAST original required; FIRST_BASELINE grants no native adoption");
        }
        material.requireRetained(same);
        var historical = same.requireHistoricalState(material.originalHeadSequence(), material.originalHeadDigest());
        StrictJson.require(historical.toJson().equals(original.originalSavedHead().toJson()),
                "saved FEAST Head differs from the privately retained original material");
    }

    /** Package boundary for actual store regressions; this read does not mint a SavedOrigin. */
    static SavedBody readSavedBody(Session same, ContinuityState claimedSavedHead,
            List<ExactRef> installedProducers) throws IOException {
        Objects.requireNonNull(same); Objects.requireNonNull(claimedSavedHead);
        // Current code references are trace metadata; saved member and payload identity remain authoritative.
        installedProducers = List.copyOf(installedProducers);
        String digest = ContinuityJson.digest(claimedSavedHead.toJson());
        ContinuityState actual = same.requireHistoricalState(claimedSavedHead.sequence(), digest);
        StrictJson.require(actual.toJson().equals(claimedSavedHead.toJson()), "actual saved FEAST Head differs");
        var body = DomainBodies.reference(actual, DomainBodies.Slot.FEAST).orElseThrow(() ->
                new IOException("saved original FEAST member is absent; absence cannot initialize or adopt"));
        StrictJson.require(FeastDomainRuntime.SCHEMA.equals(body.contractSchema()),
                "saved original FEAST schema differs");
        var pins = new ArrayList<Pin>();
        Pin payload = same.capturePin(body.payload(), MAX_BYTES);
        StrictJson.require(payload.identity().equals(body.identity()),
                "saved original FEAST physical FileIdentity changed despite equal bytes");
        byte[] raw = same.readPinned(payload, MAX_BYTES);
        byte[] canonical = StrictJson.canonical(StrictJson.parse(raw));
        StrictJson.require(Arrays.equals(raw, canonical), "saved original FEAST body is not its exact canonical document");
        var ledger = FeastDomainRuntime.decode(raw);
        pins.add(payload);
        SavedBody result = new SavedBody(actual, body, ledger, List.copyOf(pins));
        result.requireUnchanged(same);
        return result;
    }

    static final class SavedBody {
        private final ContinuityState head;
        private final DomainBodies.BodyRef reference;
        private final FeastDomainRuntime.Ledger ledger;
        private final List<Pin> pins;
        private SavedBody(ContinuityState head, DomainBodies.BodyRef reference,
                FeastDomainRuntime.Ledger ledger, List<Pin> pins) {
            this.head = head; this.reference = reference; this.ledger = ledger; this.pins = pins;
        }
        FeastDomainRuntime.Ledger ledger() { return ledger; }
        DomainBodies.BodyRef reference() { return reference; }
        void requireUnchanged(Session same) throws IOException {
            same.requireHistoricalState(head.sequence(), ContinuityJson.digest(head.toJson()));
            for (Pin pin : pins) same.verifyPin(pin);
        }
    }

    public static final class SavedOrigin {
        private final RootRestorationOriginalProof.Original restoration;
        private final SavedBody saved;
        private final FeastDomainRuntime.ActivityOrigin origin;
        private final ActionReceipt start;
        private final Optional<ActivityFinalState.State> retained;
        private SavedOrigin(RootRestorationOriginalProof.Original restoration, SavedBody saved,
                FeastDomainRuntime.ActivityOrigin origin, ActionReceipt start,
                Optional<ActivityFinalState.State> retained) {
            this.restoration = restoration; this.saved = saved; this.origin = origin;
            this.start = start; this.retained = retained;
        }
        public ExactRef restorationBasis() { return restoration.basis(); }
        public DomainBodies.BodyRef savedFeastMember() { return saved.reference(); }
        public FeastDomainRuntime.ActivityOrigin originalOrigin() { return origin; }
        public ActionReceipt originalStart() { return start; }
        public Optional<ActivityFinalState.State> retainedOriginalFinal() { return retained; }
        public void requireUnchanged(RootRuntimeContext context, Session same) throws IOException {
            requireRestoration(context, same, restoration);
            saved.requireUnchanged(same);
        }
    }
}


