package org.xar.ck3.control.application.history;

import java.math.BigInteger;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.ExecuteProjection;

/** Closed original execute-query DATA roles. This registry grants no source, archive, writer or current authority.
 * Full encoded-command/argument correspondence is rebuilt by the identical installed source-owned pure formatter;
 * this registry checks the finite exact logical operation, finite encoded grammar and original result-step role.
 */
public final class DriverExecuteReadHistoryRegistry {
    private DriverExecuteReadHistoryRegistry() { }
    public enum Family { CHINA_CASES,CHINA_CAREER }
    public enum ReportStepRule { FIXED_LOGICAL }
    private enum Encoding { CASE,PAIR,ONE,INCIDENT,HEX_NONCE,PORTABLE_NONCE,DIFFERENT_PAIR }
    public enum Entry {
        CASES_AI_OWNED(Family.CHINA_CASES,"ai-owned-case-snapshot",Encoding.PAIR),
        CASES_B1(Family.CHINA_CASES,"b1-cycle-snapshot",Encoding.HEX_NONCE),
        CASES_PIP(Family.CHINA_CASES,"b2-pip-snapshot",Encoding.ONE),
        CASES_CASE(Family.CHINA_CASES,"case-snapshot",Encoding.CASE),
        CASES_AF5(Family.CHINA_CASES,"compensation-af5-snapshot",Encoding.ONE),
        CASES_INCIDENT(Family.CHINA_CASES,"incident-snapshot",Encoding.INCIDENT),
        CASES_PROJECTS(Family.CHINA_CASES,"projects-metrics-postcondition",Encoding.DIFFERENT_PAIR),
        CASES_PROMOTION(Family.CHINA_CASES,"promotion-compensation-postcondition",Encoding.ONE),
        CASES_RESULT(Family.CHINA_CASES,"result-case-snapshot",Encoding.ONE),
        CASES_SCOREBOARD(Family.CHINA_CASES,"scoreboard-state",Encoding.PORTABLE_NONCE),
        CAREER_HC(Family.CHINA_CAREER,"career-hc-workforce-postcondition",Encoding.ONE),
        CAREER_GOVERNANCE(Family.CHINA_CAREER,"manager-governance-snapshot",Encoding.PAIR),
        CAREER_SELECTOR(Family.CHINA_CAREER,"manager-subordinate-selector",Encoding.HEX_NONCE),
        CAREER_COLLECTIVE(Family.CHINA_CAREER,"workforce-collective-snapshot",Encoding.ONE),
        CAREER_NORMAL_EXIT(Family.CHINA_CAREER,"workforce-normal-exit-snapshot",Encoding.ONE),
        CAREER_OWNER(Family.CHINA_CAREER,"workforce-owner-snapshot",Encoding.ONE);
        private final Family family;private final OperationKey operation;private final Encoding encoding;
        Entry(Family family,String originalSuffix,Encoding encoding){this.family=family;this.operation=new OperationKey("query-zhongguo-"+originalSuffix+"-v1");this.encoding=encoding;}
        public Family family(){return family;}
        public OperationKey logicalOperation(){return operation;}
        public ReportStepRule reportStepRule(){return ReportStepRule.FIXED_LOGICAL;}
        private void requireEncoded(OperationKey original) {
            String prefix=operation.value()+"-",value=original.value();
            StrictJson.require(value.startsWith(prefix)&&value.length()<=prefix.length()+256,"original command is outside its finite encoded operation domain");
            String tail=value.substring(prefix.length());
            if(encoding==Encoding.PORTABLE_NONCE){portableNonce(tail);return;}
            String[] parts=tail.split("-",-1);
            switch(encoding) {
                case CASE -> {requireParts(parts,4);StrictJson.require(parts[0].equals("b1"),"original Case mode must be b1");id(parts[1],false);id(parts[2],true);hexNonce(parts[3]);}
                case PAIR -> {requireParts(parts,3);id(parts[0],false);id(parts[1],false);hexNonce(parts[2]);}
                case DIFFERENT_PAIR -> {requireParts(parts,3);id(parts[0],false);id(parts[1],false);StrictJson.require(!parts[0].equals(parts[1]),"Projects owner and subject must differ");hexNonce(parts[2]);}
                case ONE -> {requireParts(parts,2);id(parts[0],false);hexNonce(parts[1]);}
                case INCIDENT -> {requireParts(parts,3);id(parts[0],false);StrictJson.require(List.of("x","y","z").contains(parts[1]),"original incident profile must be x/y/z");hexNonce(parts[2]);}
                case HEX_NONCE -> {requireParts(parts,1);hexNonce(parts[0]);}
                case PORTABLE_NONCE -> throw new IllegalStateException("portable nonce branch already handled");
            }
        }
    }
    public static List<Entry> entries(){return List.of(Entry.values());}
    public static Entry requireRow(OperationKey logicalOperation,OperationKey originalCommand,Obj fullReport) {
        Objects.requireNonNull(logicalOperation);Objects.requireNonNull(originalCommand);Objects.requireNonNull(fullReport);
        Entry entry=Arrays.stream(Entry.values()).filter(value->value.logicalOperation().equals(logicalOperation)).findFirst()
                .orElseThrow(()->new IllegalArgumentException("no original execute-query history policy for this exact logical operation"));
        entry.requireEncoded(originalCommand);
        StrictJson.require(new Text(entry.logicalOperation().value()).equals(fullReport.get("step")),"original numeric report step changed its fixed logical role");
        return entry;
    }
    public static Entry require(PlanningReadReceipt receipt,ExecuteProjection projection) {
        Objects.requireNonNull(receipt);Objects.requireNonNull(projection);
        StrictJson.require(receipt.request().operation().equals(projection.logicalOperation()),"source-owned execute report changed its actual logical request operation");
        return requireRow(projection.logicalOperation(),projection.originalCommand(),DriverJson.object(projection.fullResult().bytes(),org.xar.ck3.control.application.action.RawJson.MAXIMUM_BYTES));
    }
    private static void requireParts(String[] parts,int expected){StrictJson.require(parts.length==expected,"original command changed its finite argument count");}
    private static void id(String value,boolean zeroAllowed) {
        StrictJson.require(value.matches(zeroAllowed?"0|[1-9][0-9]{0,9}":"[1-9][0-9]{0,9}"),"canonical original character ID required");
        BigInteger number=new BigInteger(value);StrictJson.require(number.compareTo(BigInteger.valueOf(Integer.MAX_VALUE))<=0,"original positive int32 character ID required");
    }
    private static void hexNonce(String value) {
        StrictJson.require(value.matches("(?:[0-9a-f]{2}){1,64}"),"original lowercase even ASCII nonce hex required");
        byte[] bytes=java.util.HexFormat.of().parseHex(value);String nonce=new String(bytes,java.nio.charset.StandardCharsets.US_ASCII);
        StrictJson.require(Arrays.equals(bytes,nonce.getBytes(java.nio.charset.StandardCharsets.US_ASCII)),"original nonce is not portable ASCII");portableNonce(nonce);
    }
    private static void portableNonce(String value){StrictJson.require(value.matches("[A-Za-z0-9][A-Za-z0-9._:-]{0,63}"),"original portable nonce required");}
}
