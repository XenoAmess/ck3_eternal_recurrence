package org.xar.ck3.control.nativebridge.capabilities.registry;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.registry.CampaignProjection.*;

import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.capabilities.CampaignRootContextJson;
import org.xar.ck3.control.application.driver.DriverJson;

/** Actual Native software read/serialize originals; bindings/scopes are fixture DATA, with no live-engine credit. */
final class NativePietyRootOriginalsTest {
    @Test void nativeFullRootSerializerBytesReachStrictDecoderAndRegistry() throws Exception {
        String configured = System.getProperty("xar.m3.piety.manifest");
        Path manifestPath = configured == null ? null : Path.of(configured);
        Obj manifest = DriverJson.object(manifestPath == null ? resource("manifest.json") : Files.readAllBytes(manifestPath), 1_048_576);
        List<Value> cases = array(manifest.get("cases"), "native producer cases");
        assertFalse(cases.isEmpty(), "actual Native serialized Root originals required");
        boolean zero = false, negative = false, positive = false, unavailable = false, signedOwner = false;
        for (Value item : cases) {
            Obj expected = object(item, "native producer case");
            String original = text(expected.get("path"), "original path");
            byte[] originalBytes = manifestPath == null ? resource(original) : Files.readAllBytes(manifestPath.getParent().resolve(original).normalize());
            Obj outer = DriverJson.object(originalBytes, 1_048_576);
            assertEquals(new Text("command_result"), outer.get("type"));
            assertEquals(new Bool(true), outer.get("ok"));
            Obj wire = object(outer.get("result"), "actual Native command result");
            Obj root = object(wire.get("campaign_root_context"), "actual serialized Root");
            BigInteger date = integer(root.get("date_raw"), "date_raw");
            BigInteger revision = integer(root.get("snapshot_revision"), "snapshot_revision");
            assertEquals(root, CampaignRootContextJson.normalize(root, date, revision), "strict decoder preserves complete Native DATA");
            assertEquals(root, CampaignRootContextJson.normalizeNativeResult(wire, date, revision).get("campaign_root_context"));
            AvailableRoot projected = assertInstanceOf(AvailableRoot.class, RegistryCampaignProjection.root(wire,
                    new Binding("native-piety-software-fixture", BigInteger.ONE, revision, date.intValueExact(), BigInteger.ONE)));
            int actor = integer(expected.get("owner"), "expected owner").intValueExact();
            assertEquals(actor, projected.playerCharacterId());
            assertEquals(actor, projected.council().ownerCharacterId());
            var directory = EntityDirectory.build(projected, new EntityDirectory.Request(Relation.SELF, null, 50));
            assertEquals(List.of(actor), directory.entities().stream().map(EntityDirectory.Entity::characterId).toList());
            var publicDirectory = RegistryWire.encodePublicDirectory(directory);
            Obj directoryBody = DriverJson.object(publicDirectory.bytes(), 1_048_576);
            assertEquals(new IntegerValue(BigInteger.valueOf(actor)),
                    object(array(directoryBody.get("entities"), "public entities").getFirst(), "public entity").get("character_id"));
            assertEquals(RegistryJson.object(RegistryWire.encodeDirectory(directory)),
                    RegistryJson.object(RegistryPublicProfile.decode(RegistryPublicProfile.Profile.ENTITY_DIRECTORY, publicDirectory)));
            assertTrue(EntityDirectory.build(projected, new EntityDirectory.Request(Relation.SELF, actor, 50)).entities().isEmpty());

            signedOwner |= actor <= 0;
            String key = text(expected.get("position"), "expected position");
            Obj seat = array(object(root.get("council"), "council").get("positions"), "positions").stream()
                    .map(row -> object(row, "position"))
                    .filter(row -> new Text(key).equals(row.get("position_key"))).findFirst().orElseThrow();
            CouncilPosition typed = projected.council().positions().stream()
                    .filter(row -> row.positionKey().equals(key)).findFirst().orElseThrow();
            assertEquals(expected.get("incumbent") == Nil.INSTANCE ? null : integer(expected.get("incumbent"), "expected incumbent").intValueExact(), typed.incumbentCharacterId());
            assertEquals(seat.get("frozen") == Nil.INSTANCE ? null : bool(seat.get("frozen"), "frozen"), typed.frozen());
            Obj metric = object(seat.get("task_owner_monthly_piety_v1"), "actual owner metric");
            String status = text(expected.get("metric_status"), "expected metric status");
            assertEquals(new Text(status), metric.get("status"));
            if (status.equals("available")) {
                BigInteger raw = integer(expected.get("raw"), "expected raw");
                assertEquals(raw, integer(object(metric.get("value"), "actual metric").get("raw"), "actual raw"));
                assertEquals(BigInteger.valueOf(100000), integer(object(metric.get("value"), "actual metric").get("scale"), "actual scale"));
                assertSame(Nil.INSTANCE, metric.get("unavailable_reason"));
                zero |= raw.signum() == 0; negative |= raw.signum() < 0; positive |= raw.signum() > 0;
            } else {
                assertEquals("unavailable", status); assertSame(Nil.INSTANCE, metric.get("value"));
                assertEquals(new Text("task_owner_monthly_piety_unavailable"), metric.get("unavailable_reason"));
                unavailable = true;
            }
        }
        assertTrue(zero && negative && positive && unavailable, "Native fixtures must cover 0, negative, positive and unavailable");
        if (bool(manifest.get("require_signed_owner"), "require_signed_owner")) assertTrue(signedOwner, "signed Native owner required");
    }
    @Test void frozenOriginalChangesOnlyFlagAndRetainsOwnerComponent() throws Exception {
        Obj before = DriverJson.object(resource("positive-four-components.json"), 1_048_576);
        Obj after = DriverJson.object(resource("freeze-after.json"), 1_048_576);
        Obj result = object(before.get("result"), "before result");
        Obj root = object(result.get("campaign_root_context"), "before root");
        Obj council = object(root.get("council"), "before council");
        var positions = new java.util.ArrayList<Value>(array(council.get("positions"), "before positions"));
        int found = -1;
        for (int index = 0; index < positions.size(); index++)
            if (new Text("councillor_court_chaplain").equals(object(positions.get(index), "position").get("position_key"))) found = index;
        assertTrue(found >= 0, "original chaplain position required");
        Obj originalSeat = object(positions.get(found), "original chaplain");
        assertEquals(new Bool(false), originalSeat.get("frozen"));
        positions.set(found, originalSeat.with("frozen", new Bool(true)));
        Obj expected = before.with("result", result.with("campaign_root_context",
                root.with("council", council.with("positions", new Arr(positions)))));
        assertEquals(expected, after, "actual frozen toggle changes only its flag, retaining the evaluated component");
        Obj metric = object(originalSeat.get("task_owner_monthly_piety_v1"), "owner component");
        assertEquals(BigInteger.valueOf(45000), integer(object(metric.get("value"), "value").get("raw"), "raw"));
    }
    private static byte[] resource(String name) throws java.io.IOException {
        String path = "/registry/native-piety66/" + name;
        try (java.io.InputStream input = NativePietyRootOriginalsTest.class.getResourceAsStream(path)) {
            if (input == null) throw new java.io.IOException("Required actual Native software producer resource missing: " + path);
            return input.readAllBytes();
        }
    }

}
