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

/** Signed CharacterID consumer regression; no live-engine credit. */
final class NativePietyRootConsumerTest {
    private static final long[] CHARACTER_VALUES = {0, -2, Integer.MIN_VALUE, Integer.MAX_VALUE};
    private static Binding binding() {
        return new Binding("native-piety-software-fixture", BigInteger.ONE, BigInteger.ONE, 1, BigInteger.ONE);
    }
    private static Progress progress() { return new Progress(ProgressKind.INFINITE, null, null); }

    @Test void councilOwnerAndIncumbentPreserveSignedCharacterValues() {
        for (long value : CHARACTER_VALUES) {
            int id = Math.toIntExact(value);
            CouncilPosition position = new CouncilPosition("councillor_chancellor", id,
                    "task_foreign_affairs", TaskKind.GENERAL, null, false, progress());
            Council council = new Council(Status.AVAILABLE, "standard_landed_non_nomadic_core_v1",
                    id, List.of(position), false, null);
            assertEquals(id, council.ownerCharacterId());
            assertEquals(id, council.positions().getFirst().incumbentCharacterId().intValue());
        }
    }
    @Test void absentSentinelIsRejectedWhileNullRemainsVacancy() {
        assertThrows(IllegalArgumentException.class, () -> new Council(Status.AVAILABLE,
                "standard_landed_non_nomadic_core_v1", -1, List.of(), false, null));
        assertThrows(IllegalArgumentException.class, () -> new CouncilPosition("councillor_chancellor", -1,
                "task_foreign_affairs", TaskKind.GENERAL, null, false, progress()));
        assertNull(new CouncilPosition("councillor_chancellor", null, null, null, null, null, null).incumbentCharacterId());
    }
    @Test void nonCharacterIdentityDomainsStayPositive() {
        for (int value : new int[]{0, -2, Integer.MIN_VALUE}) {
            assertThrows(IllegalArgumentException.class, () -> new ProvinceTarget(value));
            assertThrows(IllegalArgumentException.class, () -> new Title(value, 2, "county"));
            assertThrows(IllegalArgumentException.class, () -> new War(value, Side.DEFENDER, 12, BigInteger.ZERO));
        }
        for (long value : CHARACTER_VALUES) {
            int id = Math.toIntExact(value);
            assertEquals(id, new CharacterTarget(id).characterId());
            assertEquals(id, new War(12, Side.DEFENDER, id, BigInteger.ZERO).primaryOpponentCharacterId().intValue());
        }
    }
    @Test void snapshotPreservesSignedActorWithoutChangingNullMissingSemantics() {
        for (long value : CHARACTER_VALUES) {
            int id = Math.toIntExact(value);
            Snapshot<String,String> snapshot = new Snapshot<>(binding(), true, id, true,
                    Component.unavailable("stress_unavailable"), Component.unavailable("gold_unavailable"),
                    new Missing<>(), new NullValue<>(), new Present<>(List.of()), "native-headless");
            assertEquals(id, snapshot.playerCharacterId());
            assertInstanceOf(Missing.class, snapshot.activeEvent());
            assertInstanceOf(NullValue.class, snapshot.pendingCharacterInteraction());
        }
    }
    @Test void relatedHeirAndCharacterVectorsUseTheSameSignedDomain() {
        Title title = new Title(12, 2, "county");
        for (long value : CHARACTER_VALUES) {
            int id = Math.toIntExact(value);
            assertEquals(id, new Related(id, Relation.DIRECT_LANDED_VASSAL, title, 12, 34, id).characterId());
            assertEquals(id, new PartitionRow(title, id, 12, false, false, null).firstHeirCharacterId().intValue());
        }
        List<Integer> sorted = List.of(Integer.MIN_VALUE, -2, 0, Integer.MAX_VALUE);
        assertEquals(sorted, ids(sorted, true));
        assertThrows(IllegalArgumentException.class, () -> ids(List.of(-1), false));
        assertThrows(IllegalArgumentException.class, () -> ids(List.of(0, -2), true));
    }
}
