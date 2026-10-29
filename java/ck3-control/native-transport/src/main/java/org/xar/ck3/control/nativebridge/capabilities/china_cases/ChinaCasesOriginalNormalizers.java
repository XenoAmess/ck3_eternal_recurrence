package org.xar.ck3.control.nativebridge.capabilities.china_cases;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.china_cases.CasesNormalizerValues.*;
import org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesCodec.Family;

/** The original pure normalizers, statically ported to Java. This class accepts the held original
 * receipt; it issues no observation, capability, READ, action, archive token or gameplay result. */
public final class ChinaCasesOriginalNormalizers {
    private ChinaCasesOriginalNormalizers() {}
    public record Normalized(Family family,ObjectNode fields) {
        public Normalized {Objects.requireNonNull(family);fields=Objects.requireNonNull(fields).deepCopy();}
        @Override public ObjectNode fields(){return fields.deepCopy();}
    }
    public static final class NormalizationFailure extends IllegalArgumentException {
        private static final long serialVersionUID=1L;
        private final Family family;
        private NormalizationFailure(Family family,String message,Rejected original){
            super(message,original);this.family=Objects.requireNonNull(family);
        }
        public Family family(){return family;}
        public String originalErrorClass(){return "ValueError";}
    }
    public static Normalized normalize(PlanningReadReceipt receipt,Family family) {
        Objects.requireNonNull(receipt);Objects.requireNonNull(family);
        StrictJson.require(family!=Family.PROGRESS,"PROGRESS is not an original Cases10 normalizer");
        StrictJson.require(receipt.original().nativeOk(),"normalizer requires the original successful native ACK");
        ObjectNode envelope=ChinaCasesCodec.parse(receipt.original().originalResultToken().orElseThrow());
        StrictJson.require(envelope.has(family.payload),"original normalizer payload key is missing");
        ObjectNode query=(ObjectNode)OpportunityJson.toNode(receipt.request().arguments());
        // The actual CASE primitive represents an absent optional owner as0; the original query
        // dataclass carries None. Keep that one established wire-to-memory conversion explicit.
        if(family==Family.CASE&&query.path("owner_character_id").isIntegralNumber()
                &&query.path("owner_character_id").bigIntegerValue().signum()==0)
            query.putNull("owner_character_id");
        var identity=receipt.request().before().frame().identity();
        return normalizeData(family,envelope.get(family.payload),query,
                identity.nativeRevision(),identity.dateRaw(),identity.player());
    }
    static Normalized normalizeData(Family family,JsonNode payload,ObjectNode query,
            BigInteger revision,BigInteger date,BigInteger player) {
        Objects.requireNonNull(family);Objects.requireNonNull(payload);Objects.requireNonNull(query);
        List<Kw> keywords=new ArrayList<>();
        keywords.add(new Kw("expected_query",fromJson(query)));
        keywords.add(new Kw("expected_snapshot_revision",new Num(Objects.requireNonNull(revision))));
        keywords.add(new Kw("expected_date_raw",new Num(Objects.requireNonNull(date))));
        keywords.add(new Kw("expected_player_character_id",new Num(Objects.requireNonNull(player))));
        Args args=new Args(List.of(fromJson(payload)),keywords);
        try {
            V normalized=switch(family) {
                case B1->CasesB1OriginalNormalizer.run(args);
                case CASE->CasesCASEOriginalNormalizer.run(args);
                case AIOWNED->CasesAIOWNEDOriginalNormalizer.run(args);
                case RESULT->CasesRESULTOriginalNormalizer.run(args);
                case PIP->CasesPIPOriginalNormalizer.run(args);
                case PROMOTION->CasesPROMOTIONOriginalNormalizer.run(args);
                case AF5->CasesAF5OriginalNormalizer.run(args);
                case PROJECTS->CasesPROJECTSOriginalNormalizer.run(args);
                case INCIDENT->CasesINCIDENTOriginalNormalizer.run(args);
                case SCOREBOARD->CasesSCOREBOARDOriginalNormalizer.run(args);
                case PROGRESS->throw new IllegalArgumentException("PROGRESS has no Cases10 normalizer");
            };
            JsonNode encoded=toJson(normalized);
            StrictJson.require(encoded instanceof ObjectNode,"original normalizer result must be an object");
            return new Normalized(family,(ObjectNode)encoded);
        } catch(Rejected original) {
            throw new NormalizationFailure(family,original.getMessage(),original);
        }
    }
}
