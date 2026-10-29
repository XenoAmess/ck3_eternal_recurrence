package org.xar.ck3.control.nativebridge.capabilities.publicmethods.gui;

import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.gui.GuiModels;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.gui.GuiContract.*;

/** Sole pure DATA binder between the real Root producers and source-owned public formatters. */
public final class GuiPublicBinder {
    private GuiPublicBinder() { }

    /** The snapshot and diagnostics come from the identical retained Complete, never a later READ. */
    public record Before(GuiModels.Context context, RawJson source) {
        public Before {
            Objects.requireNonNull(context); Objects.requireNonNull(source);
            GuiPublicMetadata.queryFrame(StrictJson.object(), context, source);
        }
    }

    public static RawJson read(Request request, ReadReply original, Optional<Before> before) {
        Objects.requireNonNull(request); Objects.requireNonNull(original); Objects.requireNonNull(before);
        before.ifPresent(value -> requireBefore(original.beforeSnapshot(), value));
        Optional<GuiModels.Context> context = before.map(Before::context);
        if (ArmyGuiPublicFormatter.supports(request.method()))
            return ArmyGuiPublicFormatter.read(request, original, context);
        if (GuiDecisionPublicFormatter.supports(request.method()))
            return GuiDecisionPublicFormatter.read(request, original, context);
        if (GuiFaithWhitePublicFormatter.supports(request.method())) {
            Before actual = before.orElseThrow(() -> new IllegalArgumentException("actual Faith/White before source required"));
            return GuiFaithWhitePublicFormatter.read(request, original, actual.context(), actual.source());
        }
        return GuiCodec.encode(original);
    }

    public static RawJson action(Request request, ActionReply original, Before before,
            Optional<RawJson> actualLaterObservation, Optional<RawJson> actualSnapshotAfter,
            Optional<GuiFaithWhitePublicFormatter.WhiteEvidence> whiteEvidence) {
        Objects.requireNonNull(request); Objects.requireNonNull(original); Objects.requireNonNull(before);
        Objects.requireNonNull(actualLaterObservation); Objects.requireNonNull(actualSnapshotAfter);
        Objects.requireNonNull(whiteEvidence);
        StrictJson.require(GuiFaithWhitePublicFormatter.white(request.method()) || whiteEvidence.isEmpty(), "foreign GUI cannot consume White observations");
        requireBefore(original.beforeSnapshot(), before);
        var command = original.receipt().command();
        StrictJson.require(command.before().equals(before.context().before())
                && command.source().equals(before.context().source())
                && command.sessionId().equals(before.context().sessionId()), "GUI formatter crossed retained before context");
        if (ArmyGuiPublicFormatter.supports(request.method()))
            return ArmyGuiPublicFormatter.action(request, original, before.context(), actualLaterObservation, actualSnapshotAfter);
        if (GuiDecisionPublicFormatter.supports(request.method()))
            return GuiDecisionPublicFormatter.action(request, original, before.context(), actualLaterObservation, actualSnapshotAfter);
        if (GuiFaithWhitePublicFormatter.supports(request.method())) {
            StrictJson.require(actualLaterObservation.isEmpty() && actualSnapshotAfter.isEmpty(), "Faith/White uses only its actual source-owned observations");
            return GuiFaithWhitePublicFormatter.action(request, original, before.context(), before.source(), whiteEvidence);
        }
        StrictJson.require(whiteEvidence.isEmpty(), "foreign GUI cannot consume White observations");
        return GuiCodec.encode(original);
    }

    private static void requireBefore(Optional<RawJson> supplied, Before actual) {
        StrictJson.require(supplied.isPresent()
                && java.util.Arrays.equals(supplied.orElseThrow().bytes(), actual.source().bytes()),
                "GUI public reply must retain its identical actual before source");
    }
}
