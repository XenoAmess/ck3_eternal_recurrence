package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.action.ActionTransitions;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.session.ContinuityBatchJournal;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Completes only the authenticated interrupted event from its archived observation. No Native request is made. */
final class RootArchivedFull111EventRecovery {
    private RootArchivedFull111EventRecovery() { }

    record Originals(ExactRef capturedReceipt, ExactRef freshRead, ExactRef afterNativeFrame, ExactRef afterDriverFacts) {
        static Originals read(Path path) throws IOException {
            byte[] bytes;
            try (var stream = Files.newInputStream(path)) {
                bytes = stream.readNBytes(8193);
            }
            if (bytes.length > 8192) throw new IOException("Archived Full111 event input exceeds its typed bound");
            var fields = StrictJson.object(StrictJson.parse(bytes),
                    Set.of("schema", "captured_receipt", "fresh_read", "after_native_frame", "after_driver_facts"));
            StrictJson.require("xar.root-archived-full111-event/v1".equals(StrictJson.text(fields.get("schema"))),
                    "Archived Full111 event input version differs");
            return new Originals(ExactRef.fromJson(fields.get("captured_receipt")), ExactRef.fromJson(fields.get("fresh_read")),
                    ExactRef.fromJson(fields.get("after_native_frame")), ExactRef.fromJson(fields.get("after_driver_facts")));
        }
    }

    static ActionReceipt publish(RootApplicationAssembly.Core core, ContinuityBatchJournal.PreparedExternalSave original,
            ContinuityBatchJournal.UnresolvedSameGameData restored, Originals data) throws IOException {
        var pending = original.pendingFull111Event().orElseThrow();
        StrictJson.require(restored.unresolvedActions().equals(java.util.List.of(pending)),
                "Archived Full111 closure is not the exact restored unresolved action");
        try {
            return core.writer().locked(same -> core.journal().locked(same, locked -> {
                try {
                    var current = locked.find(pending.command().actionId()).orElseThrow();
                    StrictJson.require(current.equals(pending), "Archived Full111 closure no longer owns the current action");
                    var archive = core.archive().withSession(same);
                    var capture = archive.loadReceipt(data.capturedReceipt());
                    StrictJson.require(archive.receiptReferenceOf(capture).equals(data.capturedReceipt())
                            && original.full111EventCaptures().contains(capture)
                            && capture.state() instanceof ActionState.Unknown unknown
                            && unknown.evidence().containsAll(java.util.List.of(data.freshRead(), data.afterNativeFrame())),
                            "Archived Full111 closure lost its real canonical capture and original wire references");
                    var attempt = ActionTransitions.attempt(current.state()).orElseThrow();
                    var ack = current.ack().orElseThrow();
                    StrictJson.require(capture.command().equals(current.command())
                            && ActionTransitions.attempt(capture.state()).filter(attempt::equals).isPresent()
                            && capture.ack().filter(ack::equals).isPresent(),
                            "Archived Full111 closure differs from the current original command, attempt or SELECT");
                    var before = RootGuardEvidence.loadFrame(attempt.guard(), archive, core.frameLoader());
                    var after = core.frameLoader().load(new NativeEffectEvidence.FrameBasis(data.afterNativeFrame(),
                            data.afterDriverFacts()), archive);
                    var result = RootFull111EventOptionEffects.settleArchivedZeroQueue(capture, data.freshRead(), before, after, archive);
                    if (!(result.result() instanceof ActionPorts.EffectObserved applied))
                        throw new IOException("Archived Full111 original returned no independently verified option effect");
                    return locked.append(current.command(), current.bodySha256(),
                            new ActionState.Settled(attempt, ack, new ActionState.Applied(applied.observation())));
                } catch (IOException failure) {
                    throw new UncheckedIOException(failure);
                }
            }));
        } catch (UncheckedIOException failure) {
            throw failure.getCause();
        }
    }
}
