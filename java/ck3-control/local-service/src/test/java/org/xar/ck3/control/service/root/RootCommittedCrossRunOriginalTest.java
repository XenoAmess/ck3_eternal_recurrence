package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.planning.campaign.CrossRunPlanning;
import org.xar.ck3.control.application.planning.campaign.CrossRunPlanningDomain;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.continuity.writer.ImmutableArtifactStore;
import org.xar.ck3.control.continuity.writer.StorageWriteGuardTestSupport;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

final class RootCommittedCrossRunOriginalTest {
    @TempDir Path root;

    @Test void readsOnlyTheExactRetainedStrategyAndCannotInitializeOrOverwrite() throws IOException {
        String machine = "cross-run-ordinary-resume-fixture";
        var initial = StrictJson.object().put("schema", "root.ck3.continuity-window/v1").put("machine_id", machine)
                .put("sequence", 0).put("window_id", 1).put("status", "running").put("target_days", 365)
                .put("start_date_raw", 1008).put("target_date_raw", 9768).put("last_settled_date_raw", 1008)
                .put("last_settled_cycles", 1);
        var snapshot = root.resolve("continuity.json");
        byte[] bytes = ContinuityJson.canonical(initial);
        Files.write(snapshot, bytes);
        var anchor = write(root.resolve("anchor.json"), bytes);
        var source = write(root.resolve("source.json"), new byte[] {7});
        Files.createDirectories(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
        Path artifacts = Files.createDirectory(root.resolve("artifacts"));
        var layout = new WriterContracts.Layout(snapshot, anchor, machine);
        Files.createFile(layout.lock());
        try (var guard = StorageWriteGuardTestSupport.create(layout)) {
            var archive = new ImmutableArtifactStore(new ImmutableArtifactStore.Config(artifacts, layout.lock(), 1_048_576), guard);
            var registration = new DomainBodies.Registration(DomainBodies.Slot.CROSS_RUN_PLANNING, CrossRunPlanningDomain.CONTRACT_SCHEMA,
                    1_048_576, List.of(source), (head, previous, request, original) -> {
                        CrossRunPlanning.decodeState(original);
                        return ActionCodec.sha256(original);
                    });
            var writer = new ContinuityWriter(layout, List.of(source), new WriterContracts.TransitionAuthority() {
                @Override public String revalidate(ContinuityState head, WriterContracts.Request request) {
                    throw new AssertionError("unexpected ordinary canonical write");
                }
                @Override public ContinuityState reduce(ContinuityState head, WriterContracts.Request request) {
                    throw new AssertionError("unexpected ordinary canonical write");
                }
            }, Clock.systemUTC(), new ContinuityWriter.Extensions(List.of(registration), Optional.of(archive), Optional.empty()), guard);
            var domain = new CrossRunPlanningDomain(writer::borrowedSession, (same, head, input) -> {
                throw new AssertionError("committed ordinary read cannot authorize a strategy producer");
            });
            writer.locked(same -> {
                var during = same.head();
                assertThrows(IOException.class, () -> RootCrossRunPlanning.requireRetainedOrdinary(domain, same, during.state()));
                assertEquals(during.digest(), same.head().digest());
                return null;
            });

            var original = CrossRunPlanning.empty();
            var attachment = publish(writer, source, root.resolve("strategy-original.json"), original);
            writer.locked(same -> {
                var before = same.head();
                var retained = RootCrossRunPlanning.requireRetainedOrdinary(domain, same, attachment.head());
                assertEquals(original, retained.state());
                assertEquals(DomainBodies.reference(attachment.head(), DomainBodies.Slot.CROSS_RUN_PLANNING).orElseThrow(),
                        retained.body());
                assertEquals(before.digest(), same.head().digest());
                return null;
            });

            var changed = new CrossRunPlanning.State(original.episodes(), original.nextRunPlan(), Optional.of(Instant.EPOCH));
            publish(writer, source, root.resolve("strategy-changed.json"), changed);
            writer.locked(same -> {
                var before = same.head();
                assertThrows(IOException.class, () -> RootCrossRunPlanning.requireRetainedOrdinary(domain, same, attachment.head()));
                assertEquals(changed, ((CrossRunPlanningDomain.KnownState) domain.read(same)).state());
                assertEquals(before.digest(), same.head().digest());
                return null;
            });
        }
    }

    private static WriterContracts.Receipt publish(ContinuityWriter writer, ExactRef source, Path path, CrossRunPlanning.State state)
            throws IOException {
        var artifact = write(path, CrossRunPlanning.encodeState(state));
        var request = new DomainBodies.ImportRequest(DomainBodies.Slot.CROSS_RUN_PLANNING, CrossRunPlanningDomain.CONTRACT_SCHEMA, artifact,
                ContinuityJson.canonical(StrictJson.object().put("fixture", path.getFileName().toString())), List.of(source), path.getFileName().toString());
        return writer.commitImport(writer.previewImport(request));
    }

    private static ExactRef write(Path path, byte[] bytes) throws IOException {
        Files.write(path, bytes);
        return new ExactRef(path.toString(), bytes.length, ActionCodec.sha256(bytes));
    }
}
