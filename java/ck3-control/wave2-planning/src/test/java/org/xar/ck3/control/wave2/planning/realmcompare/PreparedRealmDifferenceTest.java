package org.xar.ck3.control.wave2.planning.realmcompare;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.io.InputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

final class PreparedRealmDifferenceTest {
    @Test void completeCapturedRealmObservationsUseTheSamePreparedCountySet() throws IOException {
        JsonNode golden;
        try (InputStream stream = getClass().getResourceAsStream("/realmcompare/producer-golden.json")) {
            if (stream == null) { throw new IOException("actual realm producer corpus required; never skip"); }
            golden = StrictJson.parse(stream.readAllBytes(), 1_048_576);
        }
        int available = 0, rejected = 0;
        for (JsonNode row : golden.path("cases")) {
            JsonNode request = row.get("request");
            RealmDifference direct = RealmDifference.compare(request.get("previous"), request.get("observation"));
            RealmObservation observation;
            try { observation = RealmObservation.parse(request.get("observation")); }
            catch (IllegalArgumentException failure) {
                assertInstanceOf(RealmDifference.Unavailable.class, direct);
                rejected++;
                continue;
            }
            RealmDifference.PreparedCurrent prepared = RealmDifference.prepare(observation);
            assertSame(observation, prepared.observation());
            assertEquals(direct.toJson(), RealmDifference.comparePrepared(request.get("previous"), prepared).toJson());
            assertEquals(direct.toJson(), RealmDifference.compareObservation(request.get("previous"), observation).toJson());
            available++;
        }
        assertEquals(24, available);
        assertEquals(golden.path("cases").size(), available + rejected);
    }
}
