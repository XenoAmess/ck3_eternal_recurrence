package org.xar.ck3.control.application.driver;

import java.io.IOException;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Original history DATA and its canonical action membership. This codec grants no current owner or effect permission. */
public final class DriverActionHistoryCodec {
    public static final String SCHEMA="xar.java.original-action-history-source/v1";
    public static final String GIFT_SCHEMA="xar.java.original-action-history-source/v2";
    public static final String SOURCE_FIELD="java_action_history_source";
    public static final String PART_FIELD="java_action_history_part";
    public static final String GIFT_SUBMIT_OPERATION="private-submit-faction-gift-member-v1";
    public static final String GIFT_RECEIPT_OPERATION="private-query-faction-gift-receipt-v1";
    public static final int MAX_SOURCE_BYTES=262144;
    private DriverActionHistoryCodec() { }
    public enum Recording { RETURNED, ACCEPTED_RETURN, RAISED }
    public enum CanonicalReason { DIRECT_API_WITHOUT_LEGACY_RECORDER, RECONCILED_WITHOUT_ORIGINAL_REPORT }
    public enum EvidenceKind { MATERIAL, NATIVE_FRAME, READ, ACTION_RECEIPT, ACTION_RECORD }
    public record Evidence(EvidenceKind kind,ExactRef reference) {
        public Evidence { Objects.requireNonNull(kind);nonempty(reference); }
    }
    public sealed interface OriginalMaterial permits Legacy,CanonicalOnly,GiftLegacyPair {
        List<Evidence> evidence();
        List<ExactRef> producers();
    }
    /** The source owner selects the actual original recording path; ok is not an APPLIED alias. */
    public record Legacy(Recording recording,Optional<ExactRef> result,Optional<String> error,
            List<Evidence> evidence,List<ExactRef> producers) implements OriginalMaterial {
        public Legacy {
            Objects.requireNonNull(recording);Objects.requireNonNull(result);Objects.requireNonNull(error);
            result.ifPresent(DriverActionHistoryCodec::nonempty);error.ifPresent(StrictJson::text);
            StrictJson.require(recording==Recording.RAISED?error.isPresent():result.isPresent()&&error.isEmpty(),
                    "actual returned result or raised original error required; no invented empty result");
            evidence=checkedEvidence(evidence);producers=checkedSources(producers);
        }
    }
    /** No legacy row is invented for an interface which did not call the original recorder. */
    public record CanonicalOnly(CanonicalReason reason,List<Evidence> evidence,List<ExactRef> producers) implements OriginalMaterial {
        public CanonicalOnly { Objects.requireNonNull(reason);evidence=checkedEvidence(evidence);producers=checkedSources(producers); }
    }
    /** Exactly the two original recorder calls of a real submitted Gift and its independently observed receipt. */
    public record GiftLegacyPair(ExactRef originals,ExactRef submitResult,ExactRef receiptResult,
            org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.PublicNumbers submitNumbers,
            org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.PublicNumbers receiptNumbers,
            List<Evidence> evidence,List<ExactRef> producers) implements OriginalMaterial {
        public GiftLegacyPair {
            nonempty(originals);nonempty(submitResult);nonempty(receiptResult);Objects.requireNonNull(submitNumbers);Objects.requireNonNull(receiptNumbers);
            evidence=checkedEvidence(evidence);producers=checkedSources(producers);
            StrictJson.require(evidence.containsAll(List.of(new Evidence(EvidenceKind.MATERIAL,originals),new Evidence(EvidenceKind.MATERIAL,submitResult),
                    new Evidence(EvidenceKind.MATERIAL,receiptResult)))&&evidence.stream().anyMatch(value->value.kind()==EvidenceKind.READ),
                    "Gift pair requires its exact actual originals, both returned results and the independent original read");
        }
    }
    public record Source(String actionId,String bodySha256,long durableSequence,ExactRef receipt,ExactRef record,
            ActionReceipt.Outcome outcome,OriginalMaterial material) {
        public Source {
            StrictJson.text(actionId);StrictJson.require(bodySha256!=null&&bodySha256.matches("[0-9a-f]{64}"),"exact action body SHA required");
            StrictJson.safe(durableSequence,1);nonempty(receipt);nonempty(record);Objects.requireNonNull(outcome);Objects.requireNonNull(material);
            StrictJson.require(outcome!=ActionReceipt.Outcome.UNRESOLVED,"UNKNOWN or ACK has no completed history coverage");
        }
    }
    public static Source source(ActionReceipt actual,ExactRef canonicalRecord,ExactRef originalReceipt,OriginalMaterial material) {
        Objects.requireNonNull(actual);StrictJson.require(actual.settled(),"only an actual completed canonical action can have history coverage");
        return new Source(actual.command().actionId(),actual.bodySha256(),actual.sequence(),originalReceipt,canonicalRecord,actual.outcome(),material);
    }
    public static RawJson encode(Source source) {
        var row=new LinkedHashMap<String,Value>();row.put("schema",new Text(source.material() instanceof GiftLegacyPair?GIFT_SCHEMA:SCHEMA));row.put("action_id",new Text(source.actionId()));
        row.put("body_sha256",new Text(source.bodySha256()));row.put("durable_sequence",number(source.durableSequence()));
        row.put("receipt",ref(source.receipt()));row.put("record",ref(source.record()));row.put("outcome",new Text(source.outcome().name()));
        if(source.material() instanceof Legacy legacy) {
            row.put("representation",new Text("LEGACY_ROW"));row.put("recording",new Text(legacy.recording().name()));row.put("canonical_reason",Nil.INSTANCE);
            row.put("result",legacy.result().<Value>map(DriverActionHistoryCodec::ref).orElse(Nil.INSTANCE));
            row.put("error",legacy.error().<Value>map(Text::new).orElse(Nil.INSTANCE));
        } else if(source.material() instanceof GiftLegacyPair pair) {
            row.put("representation",new Text("LEGACY_GIFT_PAIR"));row.put("recording",new Text(Recording.RETURNED.name()));row.put("canonical_reason",Nil.INSTANCE);
            row.put("result",ref(pair.submitResult()));row.put("error",Nil.INSTANCE);row.put("gift_originals",ref(pair.originals()));
            row.put("receipt_result",ref(pair.receiptResult()));row.put("submit_public_numbers",pair.submitNumbers().toJson());row.put("receipt_public_numbers",pair.receiptNumbers().toJson());
        } else {
            var only=(CanonicalOnly)source.material();row.put("representation",new Text("CANONICAL_ONLY"));row.put("recording",Nil.INSTANCE);
            row.put("canonical_reason",new Text(only.reason().name()));row.put("result",Nil.INSTANCE);row.put("error",Nil.INSTANCE);
        }
        row.put("evidence",new Arr(source.material().evidence().stream().map(e->(Value)new Obj(Map.of("kind",new Text(e.kind().name()),"reference",ref(e.reference())))).toList()));
        row.put("producers",new Arr(source.material().producers().stream().map(r->(Value)ref(r)).toList()));
        byte[] bytes=DriverJson.encode(new Obj(row));StrictJson.require(bytes.length<=MAX_SOURCE_BYTES,"finite original action history source required");
        return new RawJson(bytes);
    }
    public static Source decode(RawJson raw) {
        Obj row=DriverJson.object(raw.bytes(),MAX_SOURCE_BYTES);
        boolean gift=new Text(GIFT_SCHEMA).equals(row.get("schema"));
        var fields=new java.util.HashSet<>(Set.of("schema","action_id","body_sha256","durable_sequence","receipt","record","outcome",
                "representation","recording","canonical_reason","result","error","evidence","producers"));
        if(gift)fields.addAll(Set.of("gift_originals","receipt_result","submit_public_numbers","receipt_public_numbers"));
        StrictJson.require(row.members().keySet().equals(fields),"closed original action history source fields required");
        StrictJson.require(gift||text(row.get("schema"),"schema").equals(SCHEMA),"original action history source schema required");
        var evidence=new ArrayList<Evidence>();for(Value value:array(row.get("evidence"),"evidence")) {
            Obj item=object(value,"evidence item");StrictJson.require(item.members().keySet().equals(Set.of("kind","reference")),"closed evidence role required");
            evidence.add(new Evidence(EvidenceKind.valueOf(text(item.get("kind"),"evidence kind")),reference(item.get("reference"))));
        }
        var producers=new ArrayList<ExactRef>();for(Value value:array(row.get("producers"),"producers"))producers.add(reference(value));
        OriginalMaterial material;
        String representation=text(row.get("representation"),"representation");
        if(gift) {
            StrictJson.require(representation.equals("LEGACY_GIFT_PAIR")&&new Text(Recording.RETURNED.name()).equals(row.get("recording"))
                    &&row.get("canonical_reason")==Nil.INSTANCE&&row.get("error")==Nil.INSTANCE,"Gift pair cannot change its actual returned recording path");
            material=new GiftLegacyPair(reference(row.get("gift_originals")),reference(row.get("result")),reference(row.get("receipt_result")),
                    org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.PublicNumbers.fromJson(row.get("submit_public_numbers")),
                    org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.PublicNumbers.fromJson(row.get("receipt_public_numbers")),evidence,producers);
        }else if(representation.equals("LEGACY_ROW")) {
            StrictJson.require(row.get("canonical_reason")==Nil.INSTANCE,"legacy row cannot claim canonical-only origin");
            material=new Legacy(Recording.valueOf(text(row.get("recording"),"recording")),nullableRef(row.get("result")),nullableText(row.get("error")),evidence,producers);
        } else {
            StrictJson.require(representation.equals("CANONICAL_ONLY")&&row.get("recording")==Nil.INSTANCE&&row.get("result")==Nil.INSTANCE&&row.get("error")==Nil.INSTANCE,
                    "canonical-only source cannot manufacture a legacy result or recording status");
            material=new CanonicalOnly(CanonicalReason.valueOf(text(row.get("canonical_reason"),"canonical reason")),evidence,producers);
        }
        return new Source(text(row.get("action_id"),"action id"),text(row.get("body_sha256"),"body SHA"),integer(row.get("durable_sequence"),"durable sequence").longValueExact(),
                reference(row.get("receipt")),reference(row.get("record")),ActionReceipt.Outcome.valueOf(text(row.get("outcome"),"outcome")),material);
    }
    /** Pure projection of already validated original material. It never resolves a missing result through Native. */
    public static Obj legacyRow(long index,ActionReceipt actual,Source source,ActionPorts.OutcomeArchive originals) throws IOException {
        StrictJson.safe(index,1);requireSource(actual,source,originals);
        if(source.material() instanceof GiftLegacyPair pair) {
            requireGiftOperation(actual);return giftRow(index,actual.command().operation().value(),pair.submitResult(),source,false,originals);
        }
        StrictJson.require(source.material() instanceof Legacy,"canonical-only action has no legacy history row");var legacy=(Legacy)source.material();
        var row=new LinkedHashMap<String,Value>();row.put("index",number(index));row.put("command",new Text(actual.command().operation().value()));
        row.put("ok",new Bool(recordedOk(legacy,originals)));
        legacy.result().ifPresent(reference->row.put("result",loadObject(reference,originals)));
        legacy.error().ifPresent(error->row.put("error",new Text(error)));
        row.put(SOURCE_FIELD,DriverJson.object(encode(source).bytes(),MAX_SOURCE_BYTES));return new Obj(row);
    }
    public static List<Obj> legacyRows(long firstIndex,ActionReceipt actual,Source source,ActionPorts.OutcomeArchive originals) throws IOException {
        Obj primary=legacyRow(firstIndex,actual,source,originals);
        if(!(source.material() instanceof GiftLegacyPair pair))return List.of(primary);
        return List.of(primary,giftRow(Math.addExact(firstIndex,1),GIFT_RECEIPT_OPERATION,pair.receiptResult(),source,true,originals));
    }
    private static Obj giftRow(long index,String operation,ExactRef result,Source source,boolean receiptPart,ActionPorts.OutcomeArchive originals) {
        StrictJson.safe(index,1);var row=new LinkedHashMap<String,Value>();row.put("index",number(index));row.put("command",new Text(operation));
        row.put("ok",new Bool(true));row.put("result",loadObject(result,originals));row.put(SOURCE_FIELD,DriverJson.object(encode(source).bytes(),MAX_SOURCE_BYTES));
        if(receiptPart)row.put(PART_FIELD,new Text("GIFT_RECEIPT"));return new Obj(row);
    }
    public static void verifyLegacy(ActionReceipt actual,Obj row,ActionPorts.OutcomeArchive originals) throws IOException {
        Objects.requireNonNull(row);Source source=decode(new RawJson(DriverJson.encode(object(row.get(SOURCE_FIELD),SOURCE_FIELD))));
        requireSource(actual,source,originals);StrictJson.require(source.material() instanceof Legacy||source.material() instanceof GiftLegacyPair,"actual original legacy row source required");
        long index=integer(row.get("index"),"history index").longValueExact();StrictJson.safe(index,1);
        Obj expected;
        if(source.material() instanceof GiftLegacyPair pair) {
            giftPublicNumbers(row).orElseThrow();
            expected=row.members().containsKey(PART_FIELD)?giftRow(index,GIFT_RECEIPT_OPERATION,pair.receiptResult(),source,true,originals)
                    :legacyRow(index,actual,source,originals);
        }else expected=legacyRow(index,actual,source,originals);
        StrictJson.require(row.equals(expected),"legacy row differs from its complete original producer/material/recording path");
    }
    /** Projection of already issuer-qualified coverage only; this data check does not replace verifyLegacy archive/source validation. */
    public static boolean recordedOk(ActionReceipt actual,Obj row) {
        Source source=decode(new RawJson(DriverJson.encode(object(row.get(SOURCE_FIELD),SOURCE_FIELD))));
        StrictJson.require(source.actionId().equals(actual.command().actionId())&&source.bodySha256().equals(actual.bodySha256())
                &&source.durableSequence()==actual.sequence()&&source.outcome()==actual.outcome()
                &&(source.material() instanceof Legacy||source.material() instanceof GiftLegacyPair),
                "history recording path crossed its actual covered action");
        if(source.material() instanceof GiftLegacyPair){requireGiftOperation(actual);return true;}
        var legacy=(Legacy)source.material();
        if(legacy.recording()==Recording.RAISED)return false;
        if(legacy.recording()==Recording.RETURNED)return true;
        return bool(object(row.get("result"),"actual recorded result").get("accepted"),"original accepted-return status");
    }
    public static void verifyCanonicalOnly(ActionReceipt actual,ExactRef originalSource,ActionPorts.OutcomeArchive originals) throws IOException {
        Source source=decode(load(originalSource,originals));requireSource(actual,source,originals);
        StrictJson.require(source.material() instanceof CanonicalOnly,"actual canonical-only original interface source required");
    }
    /** The single pure public-role router. This DATA operation grants no canonical membership or current readiness. */
    public static Optional<org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.PublicNumbers> giftPublicNumbers(Obj rawRow) {
        Objects.requireNonNull(rawRow);
        if(!rawRow.members().containsKey(SOURCE_FIELD)) {StrictJson.require(!rawRow.members().containsKey(PART_FIELD),"Gift part requires its explicit original source");return Optional.empty();}
        var source=decode(new RawJson(DriverJson.encode(object(rawRow.get(SOURCE_FIELD),SOURCE_FIELD))));
        if(!(source.material() instanceof GiftLegacyPair pair)) {StrictJson.require(!rawRow.members().containsKey(PART_FIELD),"non-Gift source cannot claim a Gift part");return Optional.empty();}
        StrictJson.require(source.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED&&new Bool(true).equals(rawRow.get("ok")),"Gift original recorder returned true only for its actual complete pair");
        if(!rawRow.members().containsKey(PART_FIELD)) {
            StrictJson.require(new Text(GIFT_SUBMIT_OPERATION).equals(rawRow.get("command")),"Gift primary row must retain its original submit command");return Optional.of(pair.submitNumbers());
        }
        StrictJson.require(new Text("GIFT_RECEIPT").equals(rawRow.get(PART_FIELD))&&new Text(GIFT_RECEIPT_OPERATION).equals(rawRow.get("command")),"Gift receipt part must retain its exact original query command");
        return Optional.of(pair.receiptNumbers());
    }
    /** The Bootstrap/current publication consumer must also use its actual borrowed writer, never a detached matching record. */
    public static void verifyLegacy(Session same,ActionReceipt actual,Obj row,ActionPorts.OutcomeArchive originals) throws IOException {
        verifyLegacy(actual,row,originals);
        requireCanonicalMembership(same,actual,decode(new RawJson(DriverJson.encode(object(row.get(SOURCE_FIELD),SOURCE_FIELD)))),originals);
    }
    public static void verifyCanonicalOnly(Session same,ActionReceipt actual,ExactRef originalSource,ActionPorts.OutcomeArchive originals) throws IOException {
        verifyCanonicalOnly(actual,originalSource,originals);requireCanonicalMembership(same,actual,decode(load(originalSource,originals)),originals);
    }
    /** Exact original no-recorder operator policy; the canonical typed receipt already retains its full identity evidence. */
    public static void verifyOperator(Session same,ActionReceipt actual,ActionPorts.OutcomeArchive originals) throws IOException {
        String head=same.head().digest();
        StrictJson.require(originals.loadReceipt(originals.receiptReferenceOf(actual)).equals(actual),"actual operator receipt/source/outbound differs");
        var record=org.xar.ck3.control.application.action.ContinuityActionJournal.requireHistoricalReceipt(same.head().state(),actual,originals);
        StrictJson.require(originals.loadRecord(record).receipt().equals(actual),"operator is not the original canonical action record");
        DriverOperatorRebindOriginals.requireCanonical(same,actual,originals);
        var completion=DriverOperatorRebindOriginals.requireOriginals(actual,originals);
        for(ExactRef ref:completion.references()){var pin=same.capturePin(ref,WriterContracts.MAX_PIN_BYTES);same.verifyPin(pin);}
        StrictJson.require(same.head().digest().equals(head),"operator archive verification changed the actual writer head");
    }
    public static void requireCanonicalMembership(Session same,ActionReceipt actual,Source source,ActionPorts.OutcomeArchive originals) throws IOException {
        String head=same.head().digest();
        StrictJson.require(ContinuityActionJournal.requireHistoricalReceipt(same.head().state(),actual,originals).equals(source.record()),
                "original action source record is not the actual retained canonical writer member");
        if(source.material() instanceof GiftLegacyPair pair) {
            requireGiftOperation(actual);
            var captured=org.xar.ck3.control.application.planning.finance.GiftActionHistoryEvidence.verifyArchived(same,actual,pair.originals(),originals);
            StrictJson.require(DriverJson.object(captured.submitResult().bytes(),DriverJson.MAX_NATIVE_BYTES).equals(loadObject(pair.submitResult(),originals))
                    &&DriverJson.object(captured.receiptResult().bytes(),DriverJson.MAX_NATIVE_BYTES).equals(loadObject(pair.receiptResult(),originals)),"Gift pair changed either actual original returned result");
            StrictJson.require(pair.submitNumbers().equals(org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.PublicNumbers.fromResults(captured.submitResult(),captured.submitPublic()))
                    &&pair.receiptNumbers().equals(org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.PublicNumbers.fromResults(captured.receiptResult(),captured.receiptPublic())),"Gift pair changed its owning public integer roles");
        }
        var pin=same.capturePin(source.record(),WriterContracts.MAX_PIN_BYTES);same.verifyPin(pin);
        StrictJson.require(same.head().digest().equals(head),"original action source writer changed during archive verification");
    }
    public static void requireSource(ActionReceipt actual,Source source,ActionPorts.OutcomeArchive originals) throws IOException {
        Objects.requireNonNull(actual);Objects.requireNonNull(source);Objects.requireNonNull(originals);
        StrictJson.require(!(actual.command().expectation() instanceof org.xar.ck3.control.application.action.CommandExpectation.OperatorRebind),
                "operator identity settlement uses its exact canonical receipt and cannot manufacture a separate ACTION history publication");
        StrictJson.require(actual.settled()&&source.actionId().equals(actual.command().actionId())&&source.bodySha256().equals(actual.bodySha256())
                &&source.durableSequence()==actual.sequence()&&source.outcome()==actual.outcome(),"original history source crossed its exact canonical action/outcome");
        StrictJson.require(source.receipt().equals(originals.receiptReferenceOf(actual))&&originals.loadReceipt(source.receipt()).equals(actual)
                &&originals.loadRecord(source.record()).receipt().equals(actual),"original history source lost its original canonical record or receipt");
        for(Evidence item:source.material().evidence())verifyEvidence(item,originals);
        if(source.material() instanceof Legacy legacy)legacy.result().ifPresent(reference->loadObject(reference,originals));
        if(source.material() instanceof GiftLegacyPair pair){requireGiftOperation(actual);load(pair.originals(),originals);loadObject(pair.submitResult(),originals);loadObject(pair.receiptResult(),originals);}
    }
    private static void requireGiftOperation(ActionReceipt actual) {
        StrictJson.require(actual.command().operation().value().equals(GIFT_SUBMIT_OPERATION)
                &&actual.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED,"Gift pair requires its actual confirmed submit action and independent receipt material");
    }
    private static boolean recordedOk(Legacy legacy,ActionPorts.OutcomeArchive originals) {
        if(legacy.recording()==Recording.RAISED)return false;
        if(legacy.recording()==Recording.RETURNED)return true;
        return bool(loadObject(legacy.result().orElseThrow(),originals).get("accepted"),"actual original accepted-return status");
    }
    private static void verifyEvidence(Evidence item,ActionPorts.OutcomeArchive originals) {
        switch(item.kind()) {
            case MATERIAL -> {RawJson raw=originals.loadFullMaterial(item.reference());exact(item.reference(),raw.bytes());}
            case NATIVE_FRAME -> exact(item.reference(),originals.loadNativeFrame(item.reference()));
            case READ -> {var read=originals.loadRead(item.reference());StrictJson.require(originals.readReferenceOf(read).equals(item.reference()),"original read reference differs");}
            case ACTION_RECEIPT -> {var receipt=originals.loadReceipt(item.reference());StrictJson.require(originals.receiptReferenceOf(receipt).equals(item.reference()),"original action receipt reference differs");}
            case ACTION_RECORD -> originals.loadRecord(item.reference());
        }
    }
    private static RawJson load(ExactRef reference,ActionPorts.OutcomeArchive originals) {
        RawJson raw=originals.loadMaterial(reference);exact(reference,raw.bytes());return raw;
    }
    private static Obj loadObject(ExactRef reference,ActionPorts.OutcomeArchive originals) {return DriverJson.object(load(reference,originals).bytes(),DriverJson.MAX_NATIVE_BYTES);}
    private static void exact(ExactRef reference,byte[] bytes) {StrictJson.require(reference.bytes()==bytes.length&&reference.sha256().equals(DriverJson.sha256(bytes)),"exact original history material bytes/SHA changed");}
    private static List<Evidence> checkedEvidence(List<Evidence> input) {
        var items=List.copyOf(input);StrictJson.require(!items.isEmpty()&&items.size()<=128&&new java.util.HashSet<>(items).size()==items.size()
                &&items.stream().anyMatch(e->e.kind()!=EvidenceKind.ACTION_RECEIPT&&e.kind()!=EvidenceKind.ACTION_RECORD),
                "independent original material is mandatory; a receipt/record alone is not Driver history material");return items;
    }
    private static List<ExactRef> checkedSources(List<ExactRef> input) {
        var sources=List.copyOf(input);StrictJson.require(!sources.isEmpty()&&sources.size()<=64&&new java.util.HashSet<>(sources).size()==sources.size(),"finite exact original producer sources required");sources.forEach(DriverActionHistoryCodec::nonempty);return sources;
    }
    private static void nonempty(ExactRef reference) {Objects.requireNonNull(reference);StrictJson.require(reference.bytes()>0,"nonempty original reference required");}
    private static Obj ref(ExactRef reference) {return DriverJson.object(StrictJson.canonical(reference.toJson()),MAX_SOURCE_BYTES);}
    private static ExactRef reference(Value value) {return ExactRef.fromJson(DriverJson.toNode(object(value,"reference")));}
    private static Optional<ExactRef> nullableRef(Value value) {Objects.requireNonNull(value);return value==Nil.INSTANCE?Optional.empty():Optional.of(reference(value));}
    private static Optional<String> nullableText(Value value) {Objects.requireNonNull(value);return value==Nil.INSTANCE?Optional.empty():Optional.of(text(value,"original error"));}
    private static IntegerValue number(long value) {return new IntegerValue(BigInteger.valueOf(value));}
    private static Obj object(Value value,String name) {return OpportunityJson.object(value,name);}
    private static List<Value> array(Value value,String name) {return OpportunityJson.array(value,name);}
    private static String text(Value value,String name) {return OpportunityJson.text(value,name);}
    private static BigInteger integer(Value value,String name) {return OpportunityJson.integer(value,name);}
    private static boolean bool(Value value,String name) {return OpportunityJson.bool(value,name);}
}
