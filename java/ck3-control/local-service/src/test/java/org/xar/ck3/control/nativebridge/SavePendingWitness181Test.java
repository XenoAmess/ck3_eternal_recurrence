package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneId;
import java.time.ZoneOffset;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.checkpoint.CheckpointPairCodec;
import org.xar.ck3.control.application.checkpoint.CheckpointResult;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.StrictJson;

/** First actual software SAVE already large before ACK; no cold context, extra collection or Game permission is manufactured. */
final class SavePendingWitness181Test {
    @TempDir Path temporary;
    private static final long LARGE_BYTES = 68_690_729L;
    private static final class FiniteClock extends Clock {
        private final AtomicReference<Instant> now = new AtomicReference<>(Instant.now());
        private final AtomicReference<Instant> next = new AtomicReference<>();
        @Override public ZoneId getZone() { return ZoneOffset.UTC; }
        @Override public Clock withZone(ZoneId zone) {
            if (!ZoneOffset.UTC.equals(zone)) throw new IllegalArgumentException("fixture clock remains UTC");
            return this;
        }
        @Override public Instant instant() {
            Instant observed=now.get(), after=next.getAndSet(null);
            if(after!=null) now.set(after);
            return observed;
        }
        void expireAfterOriginalEntry(Instant deadline) { now.set(Instant.now());next.set(deadline.plusSeconds(1)); }
    }
    private static void writeLarge(Path save) throws java.io.IOException {
        byte[] block=new byte[65_536];Arrays.fill(block,(byte)0x5a);
        try(var output=Files.newOutputStream(save)) {
            for(long remaining=LARGE_BYTES;remaining>0;) {
                int count=(int)Math.min(remaining,block.length);output.write(block,0,count);remaining-=count;
            }
        }
    }
    @Test void firstLargeSavePendingRetainsSmallDiagnosticWithoutAnotherSave() throws Exception {
        var clock=new FiniteClock();
        Path profile=temporary.resolve("physical-profile"),save=profile.resolve("save games").resolve("xar_checkpoint.ck3");
        try(var f=new CheckpointSourceCompositionTest.Fixture(temporary.resolve("large-pending"),false,clock,
                Optional.empty(),Optional.empty(),List.of(),java.time.Duration.ofSeconds(30),profile,Optional.of(()->writeLarge(save)))) {
            assertEquals(save,f.request.expectedSavePath());
            clock.expireAfterOriginalEntry(f.request.saveCommand().deadline());
            var first=assertInstanceOf(CheckpointResult.Unknown.class,f.service.checkpoint(f.request));
            assertEquals(1,f.actual.nativeActionWrites());
            assertTrue(first.action().isPresent(),first::reason);
            var current=first.action().orElseThrow();
            var pending=assertInstanceOf(ActionState.Unknown.class,current.state());
            assertTrue(current.ack().orElseThrow().nativeOk());
            assertEquals("SAVE awaits second stable physical observation",pending.reason());
            assertArrayEquals(ActionCodec.encodeCommand(f.request.saveCommand()),ActionCodec.encodeCommand(current.command()));
            assertEquals("save-checkpoint",org.xar.ck3.control.application.action.ActionTransitions.attempt(current.state()).orElseThrow().preparedRequest().step());
            byte[] block=new byte[65_536];
            var hash=MessageDigest.getInstance("SHA-256");
            try(var input=Files.newInputStream(save)) {
                for(int count;(count=input.read(block))>=0;) if(count>0)hash.update(block,0,count);
            }
            String expectedSha=HexFormat.of().formatHex(hash.digest());
            var physical=f.files.observe(save).orElseThrow();
            assertEquals(LARGE_BYTES,physical.reference().bytes());
            assertEquals(expectedSha,physical.reference().sha256());
            assertTrue(LARGE_BYTES>WriterContracts.MAX_PIN_BYTES);

            assertEquals(1,f.actual.nativeActionWrites(),"pending diagnostics must not submit SAVE again");
            assertEquals(1,pending.evidence().size());
            var diagnostic=pending.evidence().getFirst();
            assertNotEquals(physical.reference(),diagnostic);
            assertTrue(diagnostic.bytes()>0 && diagnostic.bytes()<=65_536);
            f.actual.writer.locked(same->{
                var archive=f.actual.archive.withSession(same);
                var raw=archive.loadMaterial(diagnostic).bytes();
                assertEquals(diagnostic.bytes(),raw.length);
                assertEquals(diagnostic.sha256(),ActionCodec.sha256(raw));
                var row=ContinuityJson.parseObject(raw,65_536);
                assertEquals("xar.java-checkpoint-diagnostic-witness/v1",StrictJson.text(row.get("schema")));
                assertEquals(current.command().actionId(),StrictJson.text(row.get("action_id")));
                assertEquals(current.bodySha256(),StrictJson.text(row.get("action_body_sha256")));
                assertEquals("first_stable_observation",StrictJson.text(row.get("phase")));
                assertEquals(physical,CheckpointPairCodec.fileWitnessFromJson(row.get("witness")));
                assertEquals(current,org.xar.ck3.control.application.action.ContinuityActionJournal.lookup(
                        same.head().state(),first.actionId(),archive).orElseThrow());
                return null;
            });
        }
    }
}
