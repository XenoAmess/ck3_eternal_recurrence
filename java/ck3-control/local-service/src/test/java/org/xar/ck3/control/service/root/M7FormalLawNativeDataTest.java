package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityNativeWire;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityNativeWire.*;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityPolicy.TitleSuccessors;

/** Software native corpus to the actual shared Crown decoder and M7 callback DATA hook. No private Root fixture. */
public final class M7FormalLawNativeDataTest {
    public static final String SCRATCH_PROPERTY="xar.m7.formalNativeWireScratch";

    @Test public void actualFourNativeProductsReachTheSameRootCallbackDataConsumer() throws Exception {
        var input=M7RootEpisodeChainAssertions.requireFormalLawNativeDataInputs();
        assertEquals(4,input.originals().size());assertEquals("unknown",input.nativeProducerMachineId());
        for(var original:input.originals()){
            var value=original.envelope();
            assertEquals(value,CrownAuthorityNativeWire.decode(CrownAuthorityNativeWire.encode(value)));
            assertEquals(StrictJson.parse(original.bytes()),StrictJson.parse(CrownAuthorityNativeWire.encode(value)));
            assertEquals(Relation.UNKNOWN,value.currentMembership());assertFalse(value.currentRootQualification());
        }
        assertEquals(Effect.PENDING,CrownAuthorityNativeWire.effect(input.pending().envelope()));
        assertEquals(Effect.NOT_ENACTED,CrownAuthorityNativeWire.effect(input.unchanged().envelope()));
        assertEquals(Effect.NATIVE_ENACTED_UNBOUND,CrownAuthorityNativeWire.effect(input.enacted().envelope()));
        assertEquals(Relation.UNKNOWN,CrownAuthorityNativeWire.querySubmitRelation(
                input.query().envelope(),input.pending().envelope()));
        assertFalse(input.currentRootQualification());
    }

    @Test public void canonicalPersistencePreservesAllFourOriginalBranches() throws Exception {
        var input=M7FormalLawNativeFixture.retainOriginals();
        String configured=System.getProperty(SCRATCH_PROPERTY);
        if(configured==null||configured.isBlank())throw new IOException("MISSING_M7_NATIVE_LAW_SCRATCH: "+SCRATCH_PROPERTY);
        Path parent=Path.of(configured);
        if(!parent.isAbsolute()||!Files.isDirectory(parent))throw new IOException("M7 owned data-volume scratch must already exist");
        Path actualParent=parent.toRealPath();
        Path originalRoot=Path.of(System.getProperty(M7FormalLawNativeFixture.DIRECTORY_PROPERTY)).toRealPath();
        if(actualParent.startsWith(originalRoot))throw new IOException("M7 scratch cannot be inside immutable native originals");
        Path root=Files.createTempDirectory(actualParent,"m7-native-law-");
        try {
            for(var original:input.originals()){
                Path file=root.resolve(original.pin().filename());
                byte[] persisted=CrownAuthorityNativeWire.encode(original.envelope());
                Files.write(file,persisted,StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE);
                byte[] read=Files.readAllBytes(file);
                assertArrayEquals(persisted,read);
                assertEquals(original.envelope(),CrownAuthorityNativeWire.decode(read));
                assertEquals(StrictJson.parse(original.bytes()),StrictJson.parse(read));
            }
            var context=M7FormalLawNativeFixture.originalSoftwareQueryContext(input);
            var readback=org.xar.ck3.control.governance.crownauthority.CrownAuthorityNativeQuery.onReturned(
                    context,input.query().envelope(),context.before());
            Path contextFile=root.resolve("same-query-context.json");
            Path readbackFile=root.resolve("typed-readback.json");
            Files.write(contextFile,org.xar.ck3.control.governance.crownauthority.CrownAuthorityNativeQuery.encodeContext(context),
                    StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE);
            Files.write(readbackFile,org.xar.ck3.control.governance.crownauthority.CrownAuthorityCodec.encodeReadback(readback),
                    StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE);
            assertEquals(context,org.xar.ck3.control.governance.crownauthority.CrownAuthorityNativeQuery.decodeContext(Files.readAllBytes(contextFile)));
            assertEquals(readback,org.xar.ck3.control.governance.crownauthority.CrownAuthorityCodec.decodeReadback(Files.readAllBytes(readbackFile)));
            var consumer=new org.xar.ck3.control.governance.crownauthority.CrownAuthorityCodec.Request(readback,Map.of());
            Path consumerFile=root.resolve("typed-consumer-request.json");
            Files.write(consumerFile,org.xar.ck3.control.governance.crownauthority.CrownAuthorityCodec.encodeRequest(consumer),
                    StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE);
            assertEquals(consumer,org.xar.ck3.control.governance.crownauthority.CrownAuthorityCodec.decodeRequest(Files.readAllBytes(consumerFile)));

            assertEquals(Relation.UNKNOWN,CrownAuthorityNativeWire.decode(Files.readAllBytes(
                    root.resolve(input.enacted().pin().filename()))).currentMembership());
        } finally {
            // Only these seven exact test-owned files and their newly created directory are removed.
            for(var original:input.originals())Files.deleteIfExists(root.resolve(original.pin().filename()));
            Files.deleteIfExists(root.resolve("same-query-context.json"));
            Files.deleteIfExists(root.resolve("typed-readback.json"));
            Files.deleteIfExists(root.resolve("typed-consumer-request.json"));
            Files.delete(root);
        }
    }

    @Test public void sourceIdentityAndMembershipNeverComeFromMatchingNativeNumbers() throws Exception {
        var input=M7FormalLawNativeFixture.retainOriginals();var query=input.query().envelope();
        var observation=((Query)query.payload()).observation();var actor=observation.frame().playerCharacterId();
        assertUnknown(Missing.SOURCE_MISMATCH,CrownAuthorityNativeWire.consume(query,
                new Source(query.source().gameVersion(),"0".repeat(64)),actor,Optional.empty(),Optional.empty(),Map.of()));
        assertUnknown(Missing.IDENTITY_MISMATCH,CrownAuthorityNativeWire.consume(query,query.source(),actor.add(BigInteger.ONE),
                Optional.empty(),Optional.empty(),Map.of()));
        assertUnknown(Missing.MEMBERSHIP_UNOBSERVED,CrownAuthorityNativeWire.consume(query,query.source(),actor,
                Optional.empty(),Optional.empty(),Map.of()));
        var titles=observation.fields().titleSuccessors();
        // Deliberately different DATA is a negative input, never selected current membership.
        var changed=new TitleSuccessors(titles.primaryTitleId(),List.of(titles.heldTitles().getFirst()));
        assertUnknown(Missing.MEMBERSHIP_MISMATCH,CrownAuthorityNativeWire.consume(query,query.source(),actor,
                Optional.of(changed),Optional.empty(),Map.of()));
        assertUnknown(Missing.CURRENT_REQUEST_FRAME,CrownAuthorityNativeWire.consume(query,query.source(),actor,
                Optional.of(titles),Optional.empty(),Map.of()));
        assertEquals(Relation.UNKNOWN,CrownAuthorityNativeWire.querySubmitRelation(query,input.pending().envelope()));
        assertThrows(IOException.class,()->M7FormalLawNativeFixture.retainOriginals(Path.of("relative-corpus")));
    }

    @Test public void malformedFieldsAndAnUnchangedReceiptCannotBecomeEnacted() throws Exception {
        var input=M7FormalLawNativeFixture.retainOriginals();
        ObjectNode boolRevision=object(input.query().bytes());
        object(object(boolRevision,"result"),"observation").put("snapshot_revision",true);
        rejects(boolRevision);
        ObjectNode floatRevision=object(input.query().bytes());
        object(object(floatRevision,"result"),"observation").put("snapshot_revision",40.0);
        rejects(floatRevision);
        ObjectNode stringActor=object(input.query().bytes());
        object(object(stringActor,"result"),"observation").put("player_character_id","29829");
        rejects(stringActor);
        ObjectNode absent=object(input.query().bytes());
        object(object(absent,"result"),"observation").remove("title_successors");rejects(absent);
        ObjectNode nullable=object(input.query().bytes());
        object(object(nullable,"result"),"observation").putNull("title_successors");rejects(nullable);
        ObjectNode protocol=object(input.query().bytes());protocol.put("protocol_version",true);rejects(protocol);
        ObjectNode pending=object(input.pending().bytes());object(pending,"result").putNull("ack");rejects(pending);
        ObjectNode branch=object(input.query().bytes());object(branch,"result").putObject("ack");rejects(branch);

        ObjectNode renamedUnchanged=object(input.unchanged().bytes());
        object(renamedUnchanged,"result").put("status","enacted");
        var stillUnchanged=CrownAuthorityNativeWire.decode(StrictJson.canonical(renamedUnchanged));
        assertEquals(Effect.NOT_ENACTED,CrownAuthorityNativeWire.effect(stillUnchanged));
        assertEquals(Relation.UNKNOWN,stillUnchanged.currentMembership());assertFalse(stillUnchanged.currentRootQualification());
        ObjectNode unverified=object(input.enacted().bytes());
        object(object(unverified,"result"),"receipt").put("resources_verified",false);
        assertEquals(Effect.NOT_ENACTED,CrownAuthorityNativeWire.effect(
                CrownAuthorityNativeWire.decode(StrictJson.canonical(unverified))));
        ObjectNode wrongReceiptType=object(input.enacted().bytes());
        object(object(wrongReceiptType,"result"),"receipt").put("effective_law_verified",1);rejects(wrongReceiptType);
    }

    @Test public void originalOuterRequestContextReachesExistingTypedConsumer() throws Exception {
        var input=M7RootEpisodeChainAssertions.requireFormalLawNativeDataInputs();
        var context=M7FormalLawNativeFixture.originalSoftwareQueryContext(input);
        var query=input.query().envelope();
        var read=org.xar.ck3.control.governance.crownauthority.CrownAuthorityNativeQuery.onReturned(context,query,context.before());
        assertEquals(BigInteger.valueOf(41),read.sourceFrame().queriedRevision());
        assertEquals(BigInteger.valueOf(40),read.sourceFrame().queriedNativeRevision());
        assertEquals("compiled-fixture-native:40",read.sourceFrame().queriedSnapshotId());
        var before=context.before();
        var later=new org.xar.ck3.control.governance.crownauthority.CrownAuthorityNativeQuery.Snapshot(
                before.source(),Optional.of("later-software-frame"),BigInteger.valueOf(42),BigInteger.valueOf(41),
                before.dateRaw(),before.playedCharacter(),true,true);
        assertEquals(read,org.xar.ck3.control.governance.crownauthority.CrownAuthorityNativeQuery.onReturned(context,query,later));

        assertEquals(context,org.xar.ck3.control.governance.crownauthority.CrownAuthorityNativeQuery.decodeContext(
                org.xar.ck3.control.governance.crownauthority.CrownAuthorityNativeQuery.encodeContext(context)));
        assertEquals(read,org.xar.ck3.control.governance.crownauthority.CrownAuthorityCodec.decodeReadback(
                org.xar.ck3.control.governance.crownauthority.CrownAuthorityCodec.encodeReadback(read)));
        var choice=org.xar.ck3.control.governance.crownauthority.CrownAuthorityProjectionCatalog.projectNativeQuery(
                context,query,context.before(),Map.of());
        assertEquals(org.xar.ck3.control.governance.crownauthority.CrownAuthorityPolicy.Status.READY,choice.status());
        assertEquals("crown_authority_1",choice.lawKey());
        var consumer=org.xar.ck3.control.governance.crownauthority.CrownAuthorityNativeQuery.consumerRequest(
                context,query,context.before(),Map.of());
        assertEquals(choice,CrownAuthorityNativeRead.project(consumer));
        assertEquals(consumer,org.xar.ck3.control.governance.crownauthority.CrownAuthorityCodec.decodeRequest(
                org.xar.ck3.control.governance.crownauthority.CrownAuthorityCodec.encodeRequest(consumer)));

        var reserves=Map.of(org.xar.ck3.control.governance.crownauthority.CrownAuthorityPolicy.Currency.PRESTIGE,BigInteger.ONE);
        assertEquals(reserves,CrownAuthorityNativeRead.decodeArguments(CrownAuthorityNativeRead.arguments(reserves)));
        ObjectNode wrongReserve=StrictJson.object();wrongReserve.putObject("reserves_raw").put("prestige",true);
        var malformedArgs=org.xar.ck3.control.planning.opportunity.OpportunityJson.object(
                org.xar.ck3.control.planning.opportunity.OpportunityJson.parse(StrictJson.canonical(wrongReserve)),"negative reserve fixture");
        assertThrows(IllegalArgumentException.class,()->CrownAuthorityNativeRead.decodeArguments(malformedArgs));


        assertEquals(query,CrownAuthorityNativeWire.decodeResult(query.requestId(),
                StrictJson.canonical(object(object(input.query().bytes()),"result"))));
        assertThrows(IllegalArgumentException.class,()->org.xar.ck3.control.governance.crownauthority.CrownAuthorityNativeQuery.onReturned(
                context,new Envelope(query.source(),"different-original-request",query.payload()),context.before()));
        assertThrows(IllegalArgumentException.class,()->org.xar.ck3.control.governance.crownauthority.CrownAuthorityNativeQuery.onReturned(
                context,input.pending().envelope(),context.before()));
        for(String changed:List.of("source","played_character","date_raw","paused","map_ready")){
            ObjectNode after=object(org.xar.ck3.control.governance.crownauthority.CrownAuthorityNativeQuery.encodeSnapshot(context.before()));
            switch(changed){
                case "source" -> object(after,"source").put("executable_sha256","0".repeat(64));
                case "played_character" -> object(after,"played_character").put("actual_added_field",true);
                case "date_raw" -> after.put("date_raw",context.before().dateRaw().add(BigInteger.ONE));
                default -> after.put(changed,false);
            }
            var changedAfter=org.xar.ck3.control.governance.crownauthority.CrownAuthorityNativeQuery.decodeSnapshot(StrictJson.canonical(after));
            assertThrows(IllegalArgumentException.class,()->org.xar.ck3.control.governance.crownauthority.CrownAuthorityNativeQuery.onReturned(
                    context,query,changedAfter));
        }
        ObjectNode disabled=object(org.xar.ck3.control.governance.crownauthority.CrownAuthorityNativeQuery.encodeContext(context));
        disabled.put("private_law_enabled",false);
        var noPermission=org.xar.ck3.control.governance.crownauthority.CrownAuthorityNativeQuery.decodeContext(StrictJson.canonical(disabled));
        assertThrows(IllegalArgumentException.class,()->org.xar.ck3.control.governance.crownauthority.CrownAuthorityNativeQuery.onReturned(
                noPermission,query,context.before()));
        for(String field:List.of("revision","native_revision")){
            ObjectNode malformed=object(org.xar.ck3.control.governance.crownauthority.CrownAuthorityNativeQuery.encodeContext(context));
            object(malformed,"before").put(field,true);
            assertThrows(IllegalArgumentException.class,()->org.xar.ck3.control.governance.crownauthority.CrownAuthorityNativeQuery.decodeContext(
                    StrictJson.canonical(malformed)));
        }
        ObjectNode differentActor=object(org.xar.ck3.control.governance.crownauthority.CrownAuthorityNativeQuery.encodeContext(context));
        object(object(differentActor,"before"),"played_character").put("character_id",BigInteger.valueOf(29830));
        var wrongActor=org.xar.ck3.control.governance.crownauthority.CrownAuthorityNativeQuery.decodeContext(StrictJson.canonical(differentActor));
        assertThrows(IllegalArgumentException.class,()->org.xar.ck3.control.governance.crownauthority.CrownAuthorityNativeQuery.onReturned(
                wrongActor,query,wrongActor.before()));
        ObjectNode publicDrift=object(org.xar.ck3.control.governance.crownauthority.CrownAuthorityNativeQuery.encodeContext(context));
        publicDrift.put("expected_public_revision",BigInteger.valueOf(40));
        assertThrows(IllegalArgumentException.class,()->org.xar.ck3.control.governance.crownauthority.CrownAuthorityNativeQuery.decodeContext(
                StrictJson.canonical(publicDrift)));
        ObjectNode missing=object(org.xar.ck3.control.governance.crownauthority.CrownAuthorityNativeQuery.encodeContext(context));
        object(missing,"before").remove("snapshot_id");
        assertThrows(IllegalArgumentException.class,()->org.xar.ck3.control.governance.crownauthority.CrownAuthorityNativeQuery.decodeContext(
                StrictJson.canonical(missing)));
        assertEquals(Relation.UNKNOWN,CrownAuthorityNativeWire.querySubmitRelation(query,input.pending().envelope()));
        assertFalse(input.currentRootQualification());
    }
    private static ObjectNode object(byte[] bytes){return assertInstanceOf(ObjectNode.class,StrictJson.parse(bytes));}
    private static ObjectNode object(ObjectNode row,String field){return assertInstanceOf(ObjectNode.class,row.get(field));}
    private static void rejects(ObjectNode value){
        assertThrows(IllegalArgumentException.class,()->CrownAuthorityNativeWire.decode(StrictJson.canonical(value)));
    }
    private static void assertUnknown(Missing reason,Decision actual){
        Unknown missing=assertInstanceOf(Unknown.class,actual);assertEquals(reason,missing.reason());
        assertEquals(Relation.UNKNOWN,missing.membership());
    }
}
