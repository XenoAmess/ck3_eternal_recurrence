package org.xar.ck3.control.wave3.runtime.timelineowner;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.ServiceLoader;
import java.util.stream.Stream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionCall;
import org.xar.ck3.control.contracts.projection.ProjectionError;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.ProjectionResult;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;

final class TimelineOwnerProjectionPortTest {
    @TestFactory
    Stream<DynamicTest> actualOriginalCorpusTraversesRegisteredTypedPort() throws IOException {
        JsonNode golden = golden();
        List<DynamicTest> tests = new ArrayList<>();
        RegisteredProjection registration = RegisteredProjection.of(new TimelineOwnerProjectionPort());
        for (JsonNode row : golden.get("cases")) {
            tests.add(DynamicTest.dynamicTest(row.get("id").textValue(), () -> {
                byte[] raw = row.get("input_json").textValue().getBytes(StandardCharsets.UTF_8);
                ProjectionCall call = call(row.get("id").textValue(), raw);
                ProjectionResult actual = registration.execute(call);
                if (row.get("java_expected").textValue().equals("rejected")) {
                    ProjectionResult.Rejected rejected = assertInstanceOf(ProjectionResult.Rejected.class, actual);
                    assertEquals(ProjectionError.Code.INVALID_PAYLOAD, rejected.error().code());
                    assertEquals(call.identity(), rejected.identity().orElseThrow());
                    assertThrows(IllegalArgumentException.class, () -> TimelineOwnerCodec.assess(raw));
                } else {
                    ProjectionResult.Succeeded succeeded = assertInstanceOf(ProjectionResult.Succeeded.class, actual);
                    assertEquals(call.identity(), succeeded.identity());
                    assertArrayEquals(TimelineOwnerCodec.encode(TimelineOwnerCodec.assess(raw)), succeeded.result().bytes());
                    var facts = TimelineOwnerCodec.decode(succeeded.result().bytes());
                    assertFalse(facts.replayAllowed()); assertFalse(facts.actionAdmissionGranted());
                    assertFalse(facts.sourceAdmissionGranted()); assertEquals(0, facts.savedDayCredit());
                }
            }));
        }
        assertEquals(38, tests.size());
        return tests.stream();
    }

    @Test
    void actualServiceLoaderDiscoversTheDomainCatalogAndCanonicalOperation() {
        List<ProjectionPortCatalog> catalogs = ServiceLoader.load(ProjectionPortCatalog.class).stream()
                .map(ServiceLoader.Provider::get).filter(TimelineOwnerProjectionCatalog.class::isInstance).toList();
        assertEquals(1, catalogs.size(), "actual module service resource must contain this catalog exactly once");
        List<RegisteredProjection> registrations = catalogs.getFirst().registrations();
        assertEquals(1, registrations.size());
        assertEquals(ProjectionOperation.TIMELINE_OWNER_PROJECT, registrations.getFirst().operation());
        assertEquals("timeline-owner-project", registrations.getFirst().operation().wire());
    }

    @Test
    void wrongOperationAndMalformedFieldsCannotBecomeSuccessfulDomainResults() {
        RegisteredProjection registration = RegisteredProjection.of(new TimelineOwnerProjectionPort());
        ProjectionJson value = ProjectionJson.object("{}".getBytes(StandardCharsets.UTF_8), 65_536);
        assertThrows(IllegalArgumentException.class, () -> registration.execute(new ProjectionCall(
                new ProjectionCall.Identity("wrong-operation", ProjectionOperation.MAP_ADMISSION_COMPOSE), value)));
        ProjectionResult.Rejected rejected = assertInstanceOf(ProjectionResult.Rejected.class,
                registration.execute(new ProjectionCall(new ProjectionCall.Identity("malformed", ProjectionOperation.TIMELINE_OWNER_PROJECT), value)));
        assertEquals(ProjectionError.Code.INVALID_PAYLOAD, rejected.error().code());
    }

    @Test
    void portRetainsTheExistingSeparatePayloadAndResultBudgets() {
        TimelineOwnerProjectionPort port = new TimelineOwnerProjectionPort();
        assertEquals(65_536, port.inputMaximumBytes()); assertEquals(65_536, port.outputMaximumBytes());
        assertThrows(IllegalArgumentException.class, () -> port.decode(new byte[65_537]));
    }

    private static ProjectionCall call(String id, byte[] raw) {
        return new ProjectionCall(new ProjectionCall.Identity(id, ProjectionOperation.TIMELINE_OWNER_PROJECT),
                ProjectionJson.object(raw, 65_536));
    }

    private static JsonNode golden() throws IOException {
        try (InputStream input = TimelineOwnerProjectionPortTest.class.getResourceAsStream("/timelineowner/producer-golden.json")) {
            if (input == null) { throw new AssertionError("actual original producer corpus missing; not skipped"); }
            JsonNode golden = StrictJson.parse(input.readNBytes(98_305), 98_304);
            TimelineOwnerSourceView.readProvenance(golden);
            return golden;
        }
    }
}
