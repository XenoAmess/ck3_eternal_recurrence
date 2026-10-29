package org.xar.ck3.control.application.history;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.*;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.history.DriverPublicExecuteFailureMaterial.InvocationData;
import org.xar.ck3.control.application.history.DriverPublicExecuteFailureMaterial.OriginalError;
import org.xar.ck3.control.application.history.DriverPublicExecuteFailureRowProducer.RawHistoryRow;
import org.xar.ck3.control.application.history.DriverPublicExecuteFailureRowProducer.Source;
import org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.PublicNumbers;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/**
 * Actual software Native/Driver/Known originals and canonical archive, then unqualified invocation DATA.
 * No Source implementation, private Root invocation, Candidate, publication, current/cold authority or
 * successful native operation is manufactured. The actual Root prepare path requires its own test.
 */
public final class DriverPublicExecuteFailureRowProducerTest {
    @TempDir Path directory;
    private static final String LOGICAL="query-zhongguo-case-snapshot-v1";
    private static final String COMMAND=LOGICAL+"-b1-73-0-61";
    private static final BigInteger U64_MAX=BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
    private record DataRow(RawHistoryRow row,ExactRef archivedRow,InvocationData invocation) { }
    private record FileBytes(long bytes,String sha256) { }

    private static DataRow captureData(ActionWriterIntegrationFixture fixture,Optional<Obj> report,String tag)throws Exception {
        return captureData(fixture,report,tag,new OriginalError("StepPostconditionError","actual rejected report DATA"));
    }
    private static DataRow captureData(ActionWriterIntegrationFixture fixture,Optional<Obj> report,String tag,OriginalError error)throws Exception {
        var initial=fixture.command(tag);
        return fixture.writer.locked(same->fixture.collector.current(same,initial.before(),Instant.now().plusSeconds(20),lease->
                fixture.driverAuthority().withFrozenFacts(same,frozen->fixture.archive.inSession(same,bound->{
            var actual=assertInstanceOf(DriverSnapshotFacts.Known.class,frozen.state());
            var frame=lease.frame();
            ExactRef manifest=DriverObservationEvidenceReader.reference(frame.semantic().get("java_driver_facts_evidence"));
            assertEquals(manifest,actual.observation().orElseThrow().semanticFactsEvidence());
            RawJson manifestBytes=bound.loadFullMaterial(manifest);
            ExactRef driver=DriverObservationEvidenceReader.currentDriverReference(manifest,manifestBytes);
            assertArrayEquals(actual.driver().encode(),bound.loadFullMaterial(driver).bytes());
            ExactRef originalKnown=bound.preserveMaterial(DriverSnapshotFacts.encodeKnownOriginal(actual));
            // These two artifacts are explicitly DATA. They are not an issued Root caller or epoch permission.
            ExactRef caller=bound.preserveMaterial(RawJson.fullMaterial(DriverJson.encode(new Obj(Map.of()).with("step",new Text(COMMAND))
                    .with("arguments",new Obj(Map.of())).with("test_scope",new Text("unqualified-invocation-data")))));
            ExactRef epoch=bound.preserveMaterial(RawJson.fullMaterial(DriverJson.encode(new Obj(Map.of())
                    .with("schema",new Text("unqualified-test-epoch-original"))
                    .with("episode_epoch",number(actual.stamp().episodeEpoch())))));
            ExactRef producer=bound.preserveMaterial(new RawJson(DriverJson.encode(new Obj(Map.of())
                    .with("test_scope",new Text("source-data-is-not-loaded-code-or-root-authority")))));
            Optional<ExactRef> result=report.map(value->bound.preserveMaterial(RawJson.fullMaterial(DriverJson.encode(value))));
            Optional<PublicNumbers> roles=report.map(value->PublicNumbers.fromResults(new RawJson(DriverJson.encode(value)),
                    new RawJson(DriverJson.encode(value.with("queried_revision",new Text(U64_MAX.toString()))))));
            InvocationData data;
            try {
                data=new InvocationData(new OperationKey(COMMAND),error,
                        result,roles,driver,originalKnown,frame.originalEvidence(),manifest,caller,epoch,
                        Optional.empty(),Optional.empty(),same.head().state().sequence(),same.head().digest(),List.of(producer));
            } catch(java.io.IOException failure) {
                throw new java.io.UncheckedIOException(failure);
            }
            ExactRef invocation=bound.preserveMaterial(RawJson.fullMaterial(DriverJson.encode(
                    DriverPublicExecuteFailureRowProducer.invocationJson(data))));
            var source=new Source(COMMAND,data.error(),result,roles,driver,originalKnown,frame.originalEvidence(),manifest,
                    invocation,caller,epoch,Optional.empty(),Optional.empty(),data.headSequence(),data.headDigest(),List.of(producer));
            var row=new RawHistoryRow(actual.driver().commandHistory().size()+1L,source,report);
            ExactRef retained=bound.preserveMaterial(RawJson.fullMaterial(row.encode()));
            return new DataRow(row,retained,data);
        }))));
    }
    private static IntegerValue number(long value){return new IntegerValue(BigInteger.valueOf(value));}
    private static Obj result(){return new Obj(Map.of()).with("step",new Text(LOGICAL)).with("accepted",new Bool(false))
            .with("status",new Text("blocked")).with("queried_revision",new IntegerValue(U64_MAX));}
    private static Obj without(Obj original,String key){var fields=new LinkedHashMap<String,Value>(original.members());fields.remove(key);return new Obj(fields);}
    private static Map<String,FileBytes> files(Path root)throws Exception {
        var result=new TreeMap<String,FileBytes>();
        try(var paths=Files.walk(root)){
            for(Path path:paths.filter(Files::isRegularFile).toList()){
                byte[] original=Files.readAllBytes(path);result.put(root.relativize(path).toString(),new FileBytes(original.length,DriverJson.sha256(original)));
            }
        }
        return Map.copyOf(result);
    }

    @Test public void actualNativeDriverKnownAndArchiveReopenDataWithoutResultOrNewQueries()throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(directory.resolve("no-result"),false)){
            var data=captureData(fixture,Optional.empty(),"observe-failure-data");
            assertFalse(data.row().ok());assertTrue(data.row().result().isEmpty());
            assertFalse(data.row().toJson().members().containsKey("result"));
            assertEquals(COMMAND,data.row().command());assertEquals("StepPostconditionError: actual rejected report DATA",data.row().error());
            assertEquals(data.row(),DriverPublicExecuteFailureRowProducer.decode(data.row().encode()));
            assertArrayEquals(data.row().encode(),data.row().historyEntry().originalRow().json());
            Map<String,FileBytes> before=files(fixture.root.resolve("artifacts"));int reads=fixture.scenarioReadWrites();
            fixture.writer.locked(same->{
                var head=same.head();
                return fixture.archive.inSession(same,bound->{
                    RawHistoryRow cold=DriverPublicExecuteFailureRowProducer.decode(bound.loadFullMaterial(data.archivedRow()).bytes());
                    assertEquals(data.row(),DriverPublicExecuteFailureRowProducer.replayOriginals(bound,cold));
                    assertEquals(data.invocation().originalKnown(),cold.source().originalKnown());
                    try {
                        assertEquals(head.digest(),same.head().digest());
                    } catch(java.io.IOException failure) {
                        throw new java.io.UncheckedIOException(failure);
                    }
                    return null;
                });
            });
            assertEquals(reads,fixture.scenarioReadWrites());assertEquals(before,files(fixture.root.resolve("artifacts")));
        }
    }
    @Test public void originalErrorResultHasItsFixedNativeStepAndOwningPublicNumberRoles()throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(directory.resolve("with-result"),false)){
            var data=captureData(fixture,Optional.of(result()),"observe-result-data");
            assertFalse(data.row().ok());assertEquals(COMMAND,data.row().command());
            assertEquals(LOGICAL,text(data.row().result().orElseThrow().get("step"),"step"));
            assertEquals(result(),data.row().result().orElseThrow());
            var roles=DriverPublicExecuteFailureRowProducer.publicNumbersFromSource(
                    data.row().toJson().get(DriverPublicExecuteFailureRowProducer.SOURCE_FIELD)).orElseThrow();
            Obj encoded=roles.toPublic(result());assertEquals(new Text(U64_MAX.toString()),encoded.get("queried_revision"));
            assertEquals(result(),roles.fromPublic(encoded));
            fixture.writer.locked(same->fixture.archive.inSession(same,bound->{
                assertEquals(data.row(),DriverPublicExecuteFailureRowProducer.replayOriginals(bound,data.row()));return null;
            }));
            // A null result is not the original Python absent-result row; no alias is admitted.
            var noResult=new RawHistoryRow(data.row().index(),new Source(COMMAND,data.row().source().error(),Optional.empty(),Optional.empty(),
                    data.row().source().beforeDriver(),data.row().source().originalKnown(),data.row().source().nativeFrame(),data.row().source().driverFacts(),
                    data.row().source().invocation(),data.row().source().caller(),data.row().source().epochManifest(),
                    data.row().source().unsupportedCapabilities(),data.row().source().unresolvedAction(),data.row().source().headSequence(),data.row().source().headDigest(),data.row().source().producerSources()),Optional.empty());
            assertThrows(IllegalArgumentException.class,()->DriverPublicExecuteFailureRowProducer.decode(
                    DriverJson.encode(noResult.toJson().with("result",Nil.INSTANCE))));
            fixture.writer.locked(same->fixture.archive.inSession(same,bound->{
                assertThrows(RuntimeException.class,()->DriverPublicExecuteFailureRowProducer.replayOriginals(bound,noResult));return null;
            }));
        }
    }
    @Test public void sourceAndRowFieldTypesPresenceAndPublicRolesRejectBeforeAnyOriginalLookup()throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(directory.resolve("invalid-fields"),false)){
            var data=captureData(fixture,Optional.of(result()),"observe-shape-data");Obj row=data.row().toJson();
            for(String key:List.of("index","command","ok","error",DriverPublicExecuteFailureRowProducer.SOURCE_FIELD)){
                assertThrows(IllegalArgumentException.class,()->DriverPublicExecuteFailureRowProducer.decode(DriverJson.encode(without(row,key))));
            }
            for(Value wrong:List.<Value>of(new Bool(true),new DecimalValue("1.0"),new Text("1"),Nil.INSTANCE)){
                assertThrows(IllegalArgumentException.class,()->DriverPublicExecuteFailureRowProducer.decode(DriverJson.encode(row.with("index",wrong))));
            }
            assertThrows(IllegalArgumentException.class,()->DriverPublicExecuteFailureRowProducer.decode(DriverJson.encode(row.with("ok",new Bool(true)))));
            assertThrows(IllegalArgumentException.class,()->DriverPublicExecuteFailureRowProducer.decode(DriverJson.encode(row.with("error",new Text("changed")))));
            assertThrows(IllegalArgumentException.class,()->DriverPublicExecuteFailureRowProducer.decode(DriverJson.encode(without(row,"result"))));
            Obj source=object(row.get(DriverPublicExecuteFailureRowProducer.SOURCE_FIELD),"source");
            for(String key:List.of("caller","epoch_manifest","head_digest","original_known","result","public_number_roles","unsupported_capabilities","unresolved_action")){
                Obj malformed=without(source,key);
                assertThrows(IllegalArgumentException.class,()->DriverPublicExecuteFailureRowProducer.decode(DriverJson.encode(
                        row.with(DriverPublicExecuteFailureRowProducer.SOURCE_FIELD,malformed))));
            }
            assertThrows(IllegalArgumentException.class,()->DriverPublicExecuteFailureRowProducer.decode(DriverJson.encode(
                    row.with(DriverPublicExecuteFailureRowProducer.SOURCE_FIELD,source.with("public_number_roles",Nil.INSTANCE)))));
            assertThrows(IllegalArgumentException.class,()->new OriginalError("injected.class","message"));
            assertThrows(NullPointerException.class,()->new OriginalError("ValueError",null));
            assertEquals("ValueError: ",new OriginalError("ValueError","").recorded());
        }
    }

    @Test public void actualArchiveNamespaceRejectsEvenOtherwiseEqualForeignOriginals()throws Exception {
        try(var first=new ActionWriterIntegrationFixture(directory.resolve("first-archive"),false);
                var second=new ActionWriterIntegrationFixture(directory.resolve("second-archive"),false)){
            var original=captureData(first,Optional.empty(),"first-native");
            second.command("second-native");
            var firstFiles=files(first.root.resolve("artifacts"));var secondFiles=files(second.root.resolve("artifacts"));int reads=second.scenarioReadWrites();
            second.writer.locked(same->second.archive.inSession(same,bound->{
                assertThrows(RuntimeException.class,()->DriverPublicExecuteFailureRowProducer.replayOriginals(bound,original.row()));return null;
            }));
            assertEquals(reads,second.scenarioReadWrites());assertEquals(firstFiles,files(first.root.resolve("artifacts")));assertEquals(secondFiles,files(second.root.resolve("artifacts")));
        }
    }
    @Test public void changingExceptionOrOriginalCommandDoesNotRewriteTheRetainedInvocation()throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(directory.resolve("tampered-invocation"),false)){
            var data=captureData(fixture,Optional.empty(),"original-native");Obj row=data.row().toJson();
            Obj source=object(row.get(DriverPublicExecuteFailureRowProducer.SOURCE_FIELD),"source");
            var commandRow=DriverPublicExecuteFailureRowProducer.decode(DriverJson.encode(row.with("command",new Text(COMMAND+"-changed"))
                    .with(DriverPublicExecuteFailureRowProducer.SOURCE_FIELD,source.with("command",new Text(COMMAND+"-changed")))));
            var errorRow=DriverPublicExecuteFailureRowProducer.decode(DriverJson.encode(row.with("error",new Text("StepPostconditionError: changed"))
                    .with(DriverPublicExecuteFailureRowProducer.SOURCE_FIELD,source.with("exception_message",new Text("changed")))));
            var before=files(fixture.root.resolve("artifacts"));int reads=fixture.scenarioReadWrites();
            fixture.writer.locked(same->fixture.archive.inSession(same,bound->{
                for(var changed:List.of(commandRow,errorRow)){
                    assertThrows(IllegalArgumentException.class,()->DriverPublicExecuteFailureRowProducer.replayOriginals(bound,changed));
                }
                return null;
            }));
            assertEquals(reads,fixture.scenarioReadWrites());assertEquals(before,files(fixture.root.resolve("artifacts")));
        }
    }
    @Test public void actualMissingRetainedEpochArtifactIsNotSilentlyAcceptedOrRecreated()throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(directory.resolve("missing-epoch-original"),false)){
            var data=captureData(fixture,Optional.empty(),"original-epoch-data");
            Path original=Path.of(data.row().source().epochManifest().orElseThrow().path()).toAbsolutePath().normalize();
            Path allowed=fixture.root.toAbsolutePath().normalize();
            assertTrue(original.startsWith(allowed),"only this actual TempDir fixture artifact may be moved");
            assertTrue(Files.isRegularFile(original));Path withheld=allowed.resolve("withheld-epoch-original");
            assertFalse(Files.exists(withheld));var before=files(fixture.root.resolve("artifacts"));int reads=fixture.scenarioReadWrites();
            Files.move(original,withheld);
            try{
                fixture.writer.locked(same->fixture.archive.inSession(same,bound->{
                    assertThrows(RuntimeException.class,()->DriverPublicExecuteFailureRowProducer.replayOriginals(bound,data.row()));return null;
                }));
                assertFalse(Files.exists(original),"readonly replay must not recreate a missing original");
            }finally{
                assertTrue(Files.isRegularFile(withheld));assertFalse(Files.exists(original));Files.move(withheld,original);
            }
            assertEquals(reads,fixture.scenarioReadWrites());assertEquals(before,files(fixture.root.resolve("artifacts")));
        }
    }
    @Test public void optionalEpochManifestRoundtripsAbsentNullAndPresentWithoutCrossingStrictFields()throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(directory.resolve("optional-epoch"),false)){
            var data=captureData(fixture,Optional.empty(),"present-epoch");
            var source=data.row().source();
            var present=new Source(source.command(),source.error(),source.result(),source.publicNumbers(),source.beforeDriver(),
                    source.originalKnown(),source.nativeFrame(),source.driverFacts(),source.invocation(),source.caller(),source.epochManifest(),
                    source.unsupportedCapabilities(),source.unresolvedAction(),source.headSequence(),source.headDigest(),source.producerSources());
            var absent=fixture.writer.locked(same->fixture.archive.inSession(same,bound->{
                var old=data.invocation();
                var missing=new InvocationData(old.originalCommand(),old.error(),old.result(),old.publicNumbers(),old.beforeDriver(),old.originalKnown(),
                        old.nativeFrame(),old.driverFacts(),old.caller(),Optional.<ExactRef>empty(),old.unsupportedCapabilities(),old.unresolvedAction(),old.headSequence(),old.headDigest(),old.producerSources());
                ExactRef invocation=bound.preserveMaterial(RawJson.fullMaterial(DriverJson.encode(DriverPublicExecuteFailureRowProducer.invocationJson(missing))));
                return new Source(source.command(),source.error(),source.result(),source.publicNumbers(),source.beforeDriver(),
                        source.originalKnown(),source.nativeFrame(),source.driverFacts(),invocation,source.caller(),Optional.<ExactRef>empty(),
                        source.unsupportedCapabilities(),source.unresolvedAction(),source.headSequence(),source.headDigest(),source.producerSources());
            }));
            java.util.function.Function<Obj,Source> decodeSource=payload->DriverPublicExecuteFailureRowProducer.decode(DriverJson.encode(
                    data.row().toJson().with(DriverPublicExecuteFailureRowProducer.SOURCE_FIELD,payload))).source();
            assertEquals(present,decodeSource.apply(DriverPublicExecuteFailureRowProducer.sourceJson(present)));
            assertEquals(absent,decodeSource.apply(DriverPublicExecuteFailureRowProducer.sourceJson(absent)));
            var obj=DriverPublicExecuteFailureRowProducer.sourceJson(absent);
            var nullEpoch=obj.with("epoch_manifest",Nil.INSTANCE);
            assertEquals(absent,decodeSource.apply(nullEpoch));
            var missingEpoch=new LinkedHashMap<String,Value>(obj.members());missingEpoch.remove("epoch_manifest");
            assertEquals(absent,decodeSource.apply(new Obj(missingEpoch)));
            for(Value bad:List.<Value>of(new Bool(true),new Text("epoch"),new IntegerValue(BigInteger.ONE),new Arr(List.of()),new DecimalValue("1.0"),new Obj(Map.of())))
                assertThrows(IllegalArgumentException.class,()->decodeSource.apply(obj.with("epoch_manifest",bad)));
            var absentRow=new RawHistoryRow(data.row().index(),absent,data.row().result());
            fixture.writer.locked(same->fixture.archive.inSession(same,bound->{
                ExactRef retained=bound.preserveMaterial(RawJson.fullMaterial(absentRow.encode()));
                int reads=fixture.scenarioReadWrites();var files=files(fixture.root.resolve("artifacts"));
                var cold=DriverPublicExecuteFailureRowProducer.decode(bound.loadFullMaterial(retained).bytes());
                assertEquals(absentRow,DriverPublicExecuteFailureRowProducer.replayOriginals(bound,cold));
                assertEquals(reads,fixture.scenarioReadWrites());assertEquals(files,files(fixture.root.resolve("artifacts")));return null;
            }));
        }
    }

    @Test public void observationAbsentKnownStillCannotCrossTheNativeProcessBirthInDataReplay()throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(directory.resolve("same-pid-foreign-birth"),false)){
            var data=captureData(fixture,Optional.empty(),"original-birth-data");
            RawHistoryRow changed=fixture.writer.locked(same->fixture.archive.inSession(same,bound->{
                var source=data.row().source();RawJson manifest=bound.loadFullMaterial(source.driverFacts());
                var nativeFrame=DriverObservationEvidenceReader.nativeFrame(source.driverFacts(),manifest,bound.loadNativeFrame(source.nativeFrame()));
                var facts=DriverObservationEvidenceReader.decode(source.driverFacts(),manifest,bound.loadFullMaterial(source.beforeDriver()),nativeFrame);
                var actual=DriverSnapshotFacts.decodeKnownOriginal(bound.loadFullMaterial(source.originalKnown()),Optional.of(facts));
                var game=actual.stamp().game();BigInteger originalBirth=game.creationFiletime().value();
                BigInteger otherBirth=originalBirth.equals(U64_MAX)?originalBirth.subtract(BigInteger.ONE):originalBirth.add(BigInteger.ONE);
                var otherGame=new GameGeneration(game.pid(),new PythonOnlyUInt64(otherBirth));
                var stamp=new DriverSnapshotFacts.Stamp(actual.stamp().driverVersion(),actual.stamp().episodeEpoch(),otherGame,
                        actual.stamp().episodeRunId(),actual.stamp().driverSha256());
                // Same complete Driver/PID/version/epoch and a valid DATA Known, but no observation to check birth for it.
                var foreign=new DriverSnapshotFacts.Known(actual.driver(),stamp,actual.originalHistoryBasis(),actual.actionRows(),
                        actual.auxiliary(),actual.loop(),Optional.empty());
                ExactRef known=bound.preserveMaterial(DriverSnapshotFacts.encodeKnownOriginal(foreign));
                var old=data.invocation();
                var altered=new InvocationData(old.originalCommand(),old.error(),old.result(),old.publicNumbers(),old.beforeDriver(),known,
                        old.nativeFrame(),old.driverFacts(),old.caller(),old.epochManifest(),old.unsupportedCapabilities(),old.unresolvedAction(),
                        old.headSequence(),old.headDigest(),old.producerSources());
                ExactRef invocation=bound.preserveMaterial(RawJson.fullMaterial(DriverJson.encode(
                        DriverPublicExecuteFailureRowProducer.invocationJson(altered))));
                var modified=new Source(source.command(),source.error(),source.result(),source.publicNumbers(),source.beforeDriver(),known,
                        source.nativeFrame(),source.driverFacts(),invocation,source.caller(),source.epochManifest(),source.unsupportedCapabilities(),source.unresolvedAction(),
                        source.headSequence(),source.headDigest(),source.producerSources());
                return new RawHistoryRow(data.row().index(),modified,Optional.empty());
            }));
            var before=files(fixture.root.resolve("artifacts"));int reads=fixture.scenarioReadWrites();
            fixture.writer.locked(same->fixture.archive.inSession(same,bound->{
                assertThrows(IllegalArgumentException.class,()->DriverPublicExecuteFailureRowProducer.replayOriginals(bound,changed));return null;
            }));
            assertEquals(reads,fixture.scenarioReadWrites());assertEquals(before,files(fixture.root.resolve("artifacts")));
        }
    }

    @Test public void originalTwoHireUnsupportedBranchesKeepCapabilityPriorityWithoutClassifyingOtherProducts() {
        for(String step:List.of("hire-mercenary-v1","hire-holy-order-v1")){
            Obj absent=new Obj(Map.of()).with("action_steps",new Arr(List.of()));
            Obj composite=absent.with("composite_action_steps",new Arr(List.of(new Text(step))));
            Obj primitive=composite.with("action_steps",new Arr(List.of(new Text(step))));
            assertTrue(DriverPublicExecuteFailureRowProducer.fixedUnsupportedHire(step));
            assertEquals("UnsupportedStepError: native DLL does not implement gameplay step "+step,
                    DriverPublicExecuteFailureRowProducer.unsupportedHireError(step,absent).recorded());
            assertEquals("UnsupportedStepError: native Python bridge does not implement composite step "+step,
                    DriverPublicExecuteFailureRowProducer.unsupportedHireError(step,composite).recorded());
            assertEquals("UnsupportedStepError: native Python bridge does not implement war step "+step,
                    DriverPublicExecuteFailureRowProducer.unsupportedHireError(step,primitive).recorded());
            assertThrows(IllegalArgumentException.class,()->DriverPublicExecuteFailureRowProducer.unsupportedHireError(step,
                    absent.with("action_steps",new Bool(false))));
        }
        assertFalse(DriverPublicExecuteFailureRowProducer.fixedUnsupportedHire(COMMAND));
        assertThrows(IllegalArgumentException.class,()->DriverPublicExecuteFailureRowProducer.unsupportedHireError(COMMAND,
                new Obj(Map.of()).with("action_steps",new Arr(List.of()))));
    }
    @Test public void emptyOriginalExceptionMessageStillRoundTripsWithActualArchivedOriginals()throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(directory.resolve("empty-error-message"),false)){
            var data=captureData(fixture,Optional.empty(),"empty-message-native",new OriginalError("RuntimeError",""));
            assertEquals("RuntimeError: ",data.row().error());
            assertEquals(data.row(),DriverPublicExecuteFailureRowProducer.decode(data.row().encode()));
            var before=files(fixture.root.resolve("artifacts"));int reads=fixture.scenarioReadWrites();
            fixture.writer.locked(same->fixture.archive.inSession(same,bound->{
                assertEquals(data.row(),DriverPublicExecuteFailureRowProducer.replayOriginals(bound,data.row()));return null;
            }));
            assertEquals(reads,fixture.scenarioReadWrites());assertEquals(before,files(fixture.root.resolve("artifacts")));
        }
    }

}
