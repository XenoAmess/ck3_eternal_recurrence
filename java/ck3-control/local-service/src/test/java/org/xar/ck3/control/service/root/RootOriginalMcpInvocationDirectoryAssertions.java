package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneId;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.RawJson;
import java.util.concurrent.atomic.AtomicReference;
import org.xar.ck3.control.service.mcp.McpExecutableDirectory;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory;
import static org.junit.jupiter.api.Assertions.*;

/**
 * Assertions for the real Root public-host fixture. The caller supplies its actual
 * complete directory; this class creates no Root inputs or authority. Legacy fixture
 * entry names/signatures remain for their caller, but Inputs/ProbeClock no longer
 * qualify directory binding. Actual route validation and failure identity remain strict.
 */
public final class RootOriginalMcpInvocationDirectoryAssertions {
    private RootOriginalMcpInvocationDirectoryAssertions() { }

    public static void metadataRetainsActualDirectory(McpExecutableDirectory.Complete actualComplete,
            RootRuntimeDefinitions.Inputs identicalInputs, Clock actualClock) throws IOException {
        var checked = RootOriginalMcpInvocationDirectory.bind(actualComplete);
        assertSame(actualComplete, checked);
        assertThrows(NullPointerException.class, () -> RootOriginalMcpInvocationDirectory.bind(null));
        assertSame(actualComplete.coverage(), checked.coverage());
        assertEquals(actualComplete.directory().scope(), checked.directory().scope());
        assertEquals(actualComplete.directory().tools(), checked.directory().tools());
        assertEquals(actualComplete.directory().resources(), checked.directory().resources());
    }

    public static void expiredInputsRejectBeforeDispatch(McpExecutableDirectory.Complete actualComplete,
            RootRuntimeDefinitions.Inputs identicalInputs, Clock actualClock,
            PublicMcpDirectory.ToolCall actualSnapshotCall, PublicMcpDirectory.ResourceCall actualResourceCall)
            throws IOException {
        requireSnapshot(actualSnapshotCall);
        var clock = new ProbeClock(actualClock);
        var probe = new Probe(actualComplete.directory(), clock, false, false);
        var checked = RootOriginalMcpInvocationDirectory.bind(
                new McpExecutableDirectory.Complete(probe, actualComplete.coverage()));
        clock.expire();
        assertSame(probe, checked.directory());
        var toolResult = assertDoesNotThrow(() -> checked.directory().invoke(actualSnapshotCall));
        assertSame(probe.originalToolResult, toolResult);
        var resourceResult = assertDoesNotThrow(() -> checked.directory().read(actualResourceCall));
        assertSame(probe.originalResourceResult, resourceResult);
        assertNotNull(assertDoesNotThrow(() -> checked.directory().tools()));
        assertNotNull(assertDoesNotThrow(() -> checked.directory().resources()));
        assertEquals(1, probe.toolsInvoked);
        assertEquals(1, probe.resourcesRead);
        assertEquals(1, probe.toolLists);
        assertEquals(1, probe.resourceLists);
    }

    public static void expiryAfterActualSnapshotDoesNotAcceptOrRepeatTheResult(
            McpExecutableDirectory.Complete actualComplete, RootRuntimeDefinitions.Inputs identicalInputs,
            Clock actualClock, PublicMcpDirectory.ToolCall actualSnapshotCall) throws IOException {
        requireSnapshot(actualSnapshotCall);
        var clock = new ProbeClock(actualClock);
        var probe = new Probe(actualComplete.directory(), clock, true, false);
        var checked = RootOriginalMcpInvocationDirectory.bind(
                new McpExecutableDirectory.Complete(probe, actualComplete.coverage()));
        assertSame(probe, checked.directory());
        var result = assertDoesNotThrow(() -> checked.directory().invoke(actualSnapshotCall));
        assertSame(probe.originalToolResult, result);
        assertEquals(Instant.MAX, clock.instant());
        assertEquals(1, probe.toolsInvoked);
        assertEquals(0, probe.resourcesRead);
    }

    public static void expiryAfterActualResourceReadDoesNotAcceptOrRepeatTheResult(
            McpExecutableDirectory.Complete actualComplete, RootRuntimeDefinitions.Inputs identicalInputs,
            Clock actualClock, PublicMcpDirectory.ResourceCall actualResourceCall) throws IOException {
        var clock = new ProbeClock(actualClock);
        var probe = new Probe(actualComplete.directory(), clock, false, true);
        var checked = RootOriginalMcpInvocationDirectory.bind(
                new McpExecutableDirectory.Complete(probe, actualComplete.coverage()));
        assertSame(probe, checked.directory());
        var result = assertDoesNotThrow(() -> checked.directory().read(actualResourceCall));
        assertSame(probe.originalResourceResult, result);
        assertEquals(Instant.MAX, clock.instant());
        assertEquals(0, probe.toolsInvoked);
        assertEquals(1, probe.resourcesRead);
    }

    public static void expiryAfterRejectedInvocationIsVisibleAndPreservesItsOriginalCause(
            McpExecutableDirectory.Complete actualComplete, RootRuntimeDefinitions.Inputs identicalInputs,
            Clock actualClock, PublicMcpDirectory.ToolCall actualSnapshotCall) throws IOException {
        requireSnapshot(actualSnapshotCall);
        var rejected = new PublicMcpDirectory.ToolCall(actualSnapshotCall.name(),
                new PublicMcpDirectory.Arguments(PublicMcpDirectory.Presence.VALUE, Optional.of(
                        new RawJson("{\"include_native_command_history\":null}".getBytes(StandardCharsets.UTF_8)))),
                actualSnapshotCall.meta(), actualSnapshotCall.cancellation());
        var clock = new ProbeClock(actualClock);
        var probe = new Probe(actualComplete.directory(), clock, true, false);
        var checked = RootOriginalMcpInvocationDirectory.bind(
                new McpExecutableDirectory.Complete(probe, actualComplete.coverage()));
        var failure = assertThrows(PublicMcpDirectory.ToolFailure.class,
                () -> checked.directory().invoke(rejected));
        assertNotNull(probe.originalFailure, "the actual snapshot decoder must reject null before application work");
        assertSame(probe.originalFailure, failure, "the actual decoder failure must propagate without an expiry wrapper");
        assertEquals(Instant.MAX, clock.instant());
        assertEquals(1, probe.toolsInvoked);
    }

    private static void requireSnapshot(PublicMcpDirectory.ToolCall call) {
        assertEquals("ck3_take_snapshot", Objects.requireNonNull(call).name(),
                "the actual Root fixture must supply the original read-only snapshot invocation");
    }

    /** Observation only: every operation still forwards to the supplied actual production directory. */
    private static final class Probe implements PublicMcpDirectory {
        private final PublicMcpDirectory actual;
        private final ProbeClock clock;
        private final boolean expireAfterTool, expireAfterResource;
        private int toolsInvoked, resourcesRead, toolLists, resourceLists;
        private Throwable originalFailure;
        private CallResult originalToolResult;
        private ResourceResult originalResourceResult;

        private Probe(PublicMcpDirectory actual, ProbeClock clock, boolean expireAfterTool, boolean expireAfterResource) {
            this.actual = Objects.requireNonNull(actual); this.clock = clock;
            this.expireAfterTool = expireAfterTool; this.expireAfterResource = expireAfterResource;
        }
        @Override public Scope scope() { return actual.scope(); }
        @Override public List<ToolDescriptor> tools() { toolLists++; return actual.tools(); }
        @Override public List<ResourceDescriptor> resources() { resourceLists++; return actual.resources(); }
        @Override public CallResult invoke(ToolCall call) throws ToolFailure, RpcFailure {
            toolsInvoked++;
            final CallResult result;
            try { result = actual.invoke(call); }
            catch (ToolFailure | RpcFailure failure) {
                originalFailure = failure; if (expireAfterTool) clock.expire(); throw failure;
            } catch (RuntimeException failure) {
                originalFailure = failure; if (expireAfterTool) clock.expire(); throw failure;
            }
            originalToolResult = result;
            if (expireAfterTool) clock.expire();
            return result;
        }
        @Override public ResourceResult read(ResourceCall call) throws ToolFailure, RpcFailure {
            resourcesRead++; var result = actual.read(call); originalResourceResult = result;
            if (expireAfterResource) clock.expire();
            return result;
        }
    }

    /** Only this wrapper's clock changes; the real Root/Native clock and source files are never modified. */
    private static final class ProbeClock extends Clock {
        private final AtomicReference<Instant> instant;
        private final ZoneId zone;
        private ProbeClock(Clock actual) { this(new AtomicReference<>(actual.instant()), actual.getZone()); }
        private ProbeClock(AtomicReference<Instant> instant, ZoneId zone) { this.instant = instant; this.zone = zone; }
        private void expire() { instant.set(Instant.MAX); }
        @Override public ZoneId getZone() { return zone; }
        @Override public Clock withZone(ZoneId requested) { return new ProbeClock(instant, Objects.requireNonNull(requested)); }
        @Override public Instant instant() { return instant.get(); }
    }
}


