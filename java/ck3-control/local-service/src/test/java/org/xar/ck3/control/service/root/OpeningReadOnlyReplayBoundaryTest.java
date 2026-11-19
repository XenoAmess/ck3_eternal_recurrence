package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.continuity.writer.NativeArchiveDataCodec;
import org.xar.ck3.control.nativebridge.capabilities.governance.GovernancePlanningReads.OpeningReadProfile;

/** Actual frozen C++ DATA for pure replay boundaries. It never invents an application-main ticket or Root. */
@org.junit.jupiter.api.condition.EnabledIfSystemProperty(named="xar.opening56.replay.inputs",matches=".+")
final class OpeningReadOnlyReplayBoundaryTest {
    private static OpeningReadProfile profile() {
        return new OpeningReadProfile(new OpeningReadProfile.SourcePins("856a95114bd5e70ab50bef77d26a27035552b77df1c3bf79467d1c5b50839102",
                "31fe8e38eaa822edb8cb63606ee9c1c630657af8f41cd25f7ccb6319e65901f8"));
    }
    private static byte[] original(String name)throws Exception {
        var index=StrictJson.parse(Files.readAllBytes(Path.of(System.getProperty("xar.opening56.replay.inputs"))));
        var ref=ExactRef.fromJson(index.get(name));byte[] raw=Files.readAllBytes(Path.of(ref.path()));
        assertEquals(ref.bytes(),raw.length);assertEquals(ref.sha256(),ActionCodec.sha256(raw));return raw;
    }
    private static OpeningReadProfile.Frame frame()throws Exception {
        var full=StrictJson.parse(original("full"));var state=full.get("state");
        return new OpeningReadProfile.Frame(full.get("revision").bigIntegerValue(),state.get("date_raw").bigIntegerValue(),state.get("played_character").get("character_id").bigIntegerValue());
    }
    @Test void pureCurrentFactsRequireTheirExactFrameAndNeverSubstituteScopeOrUnavailable()throws Exception {
        var expected=frame();var current=profile().decodeData(OpeningReadProfile.Kind.CURRENT,new RawJson(original("current")),expected);
        assertTrue(OpeningTransitions.readOnlyExistingMatches(current,expected));
        assertFalse(OpeningTransitions.readOnlyExistingMatches(current,new OpeningReadProfile.Frame(expected.nativeRevision().add(BigInteger.ONE),expected.dateRaw(),expected.playerCharacterId())));
        assertFalse(OpeningTransitions.readOnlyExistingMatches(current,new OpeningReadProfile.Frame(expected.nativeRevision(),expected.dateRaw(),BigInteger.ZERO)));
        var scope=profile().decodeData(OpeningReadProfile.Kind.SCOPE,new RawJson(original("scope")),expected);
        assertFalse(OpeningTransitions.readOnlyExistingMatches(scope,expected));
        var unknown=profile().decodeData(OpeningReadProfile.Kind.CURRENT,new RawJson(original("unavailable")),expected);
        assertFalse(OpeningTransitions.readOnlyExistingMatches(unknown,expected));
    }
    @Test void realOfflineCppFactsCannotAuthorizeExistingGatePublication()throws Exception {
        var expected=frame();var current=profile().decodeData(OpeningReadProfile.Kind.CURRENT,new RawJson(original("current")),expected);
        assertEquals(OpeningReadProfile.SourceKind.OFFLINE_FIXTURE,current.origin().kind());
        assertThrows(IllegalArgumentException.class,()->OpeningTransitions.requireReadOnlyExistingData(current,expected));
        var unavailable=profile().decodeData(OpeningReadProfile.Kind.CURRENT,new RawJson(original("unavailable")),expected);
        assertThrows(IllegalArgumentException.class,()->OpeningTransitions.requireReadOnlyExistingData(unavailable,expected));
    }
    @Test void actualMainTicketReadReplaysWithoutNativeOrRootAndScopeCannotReplaceCurrent()throws Exception {
        var index=StrictJson.parse(Files.readAllBytes(Path.of(System.getProperty("xar.opening56.replay.inputs"))));
        var codec=NativeArchiveDataCodec.retainedFiles();
        var read=codec.readData(ExactRef.fromJson(index.get("actual_current_read"))).receipt();
        var scope=codec.readData(ExactRef.fromJson(index.get("actual_scope_read"))).receipt();
        var selected=OpeningReadProfile.selectQualified(OpeningReadProfile.VERSION,OpeningReadProfile.EXECUTABLE,ExactRef.fromJson(index.get("actual_dll"))).orElseThrow();
        var definitions=new OpeningReadProfile.Bindings(selected,ExactRef.fromJson(index.get("actual_dll")));
        OpeningTransitions.requireReadOnlyExisting(read,definitions.current());
        var data=definitions.current().replay(read);assertEquals(OpeningReadProfile.SourceKind.APPLICATION_MAIN_TICKET,data.origin().kind());
        assertEquals("martial_authority_focus",data.progress().orElseThrow().focusKey().orElseThrow());
        assertEquals(BigInteger.valueOf(78750000),data.progress().orElseThrow().xpTotalRaw().orElseThrow());
        assertEquals(BigInteger.ZERO,data.progress().orElseThrow().unspentPerkPoints().orElseThrow());
        assertEquals(BigInteger.valueOf(14),data.progress().orElseThrow().usedPerkPoints().orElseThrow());
        assertEquals(OpeningReadProfile.SourceKind.APPLICATION_MAIN_TICKET,definitions.scope().replay(scope).origin().kind());
        assertThrows(IllegalArgumentException.class,()->OpeningTransitions.requireReadOnlyExisting(scope,definitions.current()));
    }
}
