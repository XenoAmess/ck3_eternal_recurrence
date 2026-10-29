package org.xar.ck3.control.application.planning.finance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.effects.FinanceEvidenceArchive;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Public quote ingress: malformed metadata cannot reach Root intent preparation or Native submission. */
final class FinanceQuoteEvidenceBoundaryTest {
    private static Obj objectValue(String json) { return object(parse(json.getBytes(java.nio.charset.StandardCharsets.UTF_8)),"quote arguments"); }
    private static Obj reference(long bytes) {
        ExactRef ref=new ExactRef(Path.of("target","original-finance-quote.json").toAbsolutePath().toString(),bytes,"a".repeat(64));
        return object(parse(StrictJson.canonical(ref.toJson(),4096)),"fixture quote reference");
    }
    @Test void commandQuoteRequiresExactNonemptyAbsoluteOriginalReference() {
        Obj original=new Obj(Map.of("company_id",new IntegerValue(BigInteger.ZERO),FinanceEvidenceArchive.ARGUMENT,reference(1)));
        assertEquals(1,FinanceEvidenceArchive.reference(original).bytes());
        assertThrows(IllegalArgumentException.class,()->FinanceEvidenceArchive.reference(new Obj(Map.of())));
        for(Value wrong:List.<Value>of(Nil.INSTANCE,new Bool(true),new IntegerValue(BigInteger.ONE),new Arr(List.of()),new Obj(Map.of())))
            assertThrows(IllegalArgumentException.class,()->FinanceEvidenceArchive.reference(new Obj(Map.of(FinanceEvidenceArchive.ARGUMENT,wrong))));
        for(String wrong:List.of("{\"path\":\"relative.json\",\"bytes\":1,\"sha256\":\""+"a".repeat(64)+"\"}",
                "{\"path\":\"relative.json\",\"bytes\":true,\"sha256\":\""+"a".repeat(64)+"\"}",
                "{\"path\":\"relative.json\",\"bytes\":1.0,\"sha256\":\""+"a".repeat(64)+"\"}"))
            assertThrows(IllegalArgumentException.class,()->FinanceEvidenceArchive.reference(new Obj(Map.of(FinanceEvidenceArchive.ARGUMENT,objectValue(wrong)))));
        assertThrows(IllegalArgumentException.class,()->FinanceEvidenceArchive.reference(new Obj(Map.of(FinanceEvidenceArchive.ARGUMENT,reference(0)))));
    }
    @Test void evidenceExclusionPreservesOriginalArgumentTokenDomainAndRoundtrip() {
        var fields=new LinkedHashMap<String,Value>();fields.put("company_id",new IntegerValue(BigInteger.ZERO));fields.put("actual_optional",Nil.INSTANCE);
        fields.put("empty_list",new Arr(List.of()));fields.put(FinanceEvidenceArchive.ARGUMENT,reference(12));Obj original=new Obj(fields);
        Obj removed=FinanceEvidenceArchive.withoutEvidence(original);
        assertFalse(removed.members().containsKey(FinanceEvidenceArchive.ARGUMENT));assertFalse(removed.members().containsKey("missing_optional"));
        assertSame(Nil.INSTANCE,removed.get("actual_optional"));assertEquals(new Arr(List.of()),removed.get("empty_list"));
        assertEquals(removed,parse(encode(removed)));assertEquals(original,removed.with(FinanceEvidenceArchive.ARGUMENT,reference(12)));
        assertNotEquals(ActionCodec.sha256(encode(original)),ActionCodec.sha256(encode(removed)));
    }
}
