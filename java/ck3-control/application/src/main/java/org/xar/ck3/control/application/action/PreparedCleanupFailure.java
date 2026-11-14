package org.xar.ck3.control.application.action;

import java.io.PrintWriter;
import java.io.StringWriter;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Objects;
import java.util.function.Supplier;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Full actual Throwable chain archive. This DATA does not infer a dispatch stage:
 * only a source-owned before-call checkpoint or the SDK's real typed endpoint
 * result can supply BEFORE_WRITE. An arbitrary exception remains UNKNOWN. */
public final class PreparedCleanupFailure {
    private PreparedCleanupFailure() { }
    public static ExactRef preserve(Throwable actual,Instant capturedAt,ActionPorts.OutcomeArchive archive) {
        Objects.requireNonNull(actual);
        return retainingOriginal(actual,()->{
            Objects.requireNonNull(capturedAt);Objects.requireNonNull(archive);
            StringWriter text=new StringWriter();actual.printStackTrace(new PrintWriter(text));
            byte[] complete=text.toString().getBytes(StandardCharsets.UTF_8);
            StrictJson.require(complete.length>0&&complete.length<=StrictJson.EXPLICIT_MAX_BYTES,
                    "complete prepared cleanup failure exceeds its bounded original archive; do not classify it as zero-write");
            var row=StrictJson.object();row.put("schema","xar.prepared-cleanup-actual-throwable/v1");
            row.put("java_type",actual.getClass().getName());
            if(actual.getMessage()==null)row.putNull("message");else row.put("message",actual.getMessage());
            row.put("captured_at",capturedAt.toString());row.put("complete_java_stacktrace",text.toString());
            row.put("stacktrace_sha256",ActionCodec.sha256(complete));
            return archive.preserveMaterial(RawJson.fullMaterial(StrictJson.canonical(row,StrictJson.EXPLICIT_MAX_BYTES)));
        });
    }
    /** Every failure-publication stage uses this boundary. A failed diagnostic
     * never replaces its original Throwable, original cause or suppressed tree.
     * This does not infer any native dispatch stage or grant retry authority. */
    static <T>T retainingOriginal(Throwable actual,Supplier<T> publication) {
        Objects.requireNonNull(actual);
        try{return Objects.requireNonNull(publication).get();}
        catch(RuntimeException|Error diagnostic){
            // Nested publication may already retain this identical original.
            // Do not create a cyclic suppressed/cause graph or replace it again.
            if(diagnostic==actual||diagnostic.getCause()==actual)throw diagnostic;
            var retained=new IllegalStateException("complete actual prepared cleanup failure could not be archived",actual);
            retained.addSuppressed(diagnostic);throw retained;
        }
    }
    /** Only the common action package records an actual, closed pre-world-write checkpoint. */
    static NativeActionPort.RejectedBeforeDispatch beforeNativeCall(String requestId,Throwable actual,
            Instant capturedAt,ExactRef fullFailure) {
        var diagnostic=StrictJson.object();diagnostic.put("schema","xar.prepared-cleanup-source-before-write/v1");
        diagnostic.put("captured_at",capturedAt.toString());diagnostic.set("complete_failure",fullFailure.toJson());
        diagnostic.put("java_type",actual.getClass().getName());
        return new NativeActionPort.RejectedBeforeDispatch(requestId,new NativeActionPort.ZeroDispatchProof(
                NativeActionPort.ZeroDispatchStage.BEFORE_WRITE,0,"actual source checkpoint before the sole prepared world-submit call",
                java.util.Optional.of(new RawJson(StrictJson.canonical(diagnostic)))));
    }
}
