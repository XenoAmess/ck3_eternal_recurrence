package org.xar.ck3.control.service.root;

import java.math.BigInteger;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;

/** Read-only counterpart of driver_state_wal_v1.replay. Data validation cannot admit a Game or history owner. */
public final class OriginalDriverJournal {
    public static final String JOURNAL_FILENAME="driver-state.wal-v1.json";
    public static final String JOURNAL_SCHEMA="xar.ck3.driver-state-wal/v1";
    public static final String SEALED_SCHEMA="xar.ck3.driver-state-sealed-base/v1";
    public static final int MAXIMUM_DRIVER_BYTES=256*1024*1024;
    public static final int MAXIMUM_JOURNAL_BYTES=8*1024*1024;
    private static final long MAXIMUM_VALUES=16_000_000;
    private static final Set<String> META=Set.of("format_version","pipe_name","bridge_pid","episode_character_id",
            "episode_run_id","last_checkpoint","rollback_war_failure","managed_restore_transaction",
            "succession_expectation","succession_lifecycle","campaign_goal");
    private static final Set<String> HEADER=Set.of("schema","base_sha256","base_history_rows","entries","consolidated_sha256");
    private static final Set<String> ENTRY=Set.of("sequence","previous_sha256","history_rows","state_fields","sha256");
    private OriginalDriverJournal(){ }
    public enum Status { BASE_ONLY,ALREADY_CONSOLIDATED,REPLAYED }
    public record Replayed(Status status,ObjectValue payload) {
        public Replayed {Objects.requireNonNull(status);Objects.requireNonNull(payload);}
    }
    /** Only this explicit WAL semantic failure maps to Python JournalInvalid. General I/O is outside this codec. */
    public static final class JournalInvalid extends IllegalArgumentException {
        public JournalInvalid(String detail){super(detail);}
        public JournalInvalid(String detail,Throwable cause){super(detail,cause);}
    }
    /** A stricter Java JSON boundary or resource lease is not one of the original Python WAL refusal reasons. */
    public static final class InputRejected extends IllegalArgumentException {
        private InputRejected(String detail,Throwable cause){super(detail,cause);}
    }
    public static Replayed replay(byte[] originalBase,Optional<byte[]> originalJournal) {
        Objects.requireNonNull(originalJournal);
        final ObjectValue base;
        try {base=object(parse(originalBase,MAXIMUM_DRIVER_BYTES),"base state is not an object");}
        catch(InputRejected strict){throw strict;}
        catch(IllegalArgumentException bad){throw new JournalInvalid("base state is not valid original JSON",bad);}
        if(originalJournal.isEmpty()) {
            if(integerEquals(base.get("format_version"),3))throw new JournalInvalid("sealed Driver baseline is missing its journal");
            // Exact WAL metadata does not apply to pre-WAL full v1/v2. The sole canonical resume consumer decides it.
            return new Replayed(Status.BASE_ONLY,base);
        }
        try {
            if(originalJournal.orElseThrow().length>MAXIMUM_JOURNAL_BYTES)throw new JournalInvalid("journal exceeds original bounded reader capacity");
            ObjectValue journal=object(parse(originalJournal.orElseThrow(),MAXIMUM_JOURNAL_BYTES),"journal is not an object");
            exact(journal,HEADER,"journal header fields changed");
            require(textEquals(journal.get("schema"),JOURNAL_SCHEMA),"journal schema changed");
            String previous=digest(journal.get("base_sha256"));
            BigInteger baseRows=integer(journal.get("base_history_rows"),"base history count must be an exact integer");
            require(baseRows.signum()>=0,"negative base history count");
            Value marker=journal.get("consolidated_sha256");
            if(!(marker instanceof NullValue))digest(marker);
            List<Value> entries=array(journal.get("entries"),"journal entries must be an array").values();
            BigInteger index=baseRows.add(BigInteger.ONE);
            for(int sequence=0;sequence<entries.size();sequence++) {
                ObjectValue entry=object(entries.get(sequence),"journal entry must be an object");
                exact(entry,ENTRY,"journal entry fields changed");
                require(integer(entry.get("sequence"),"sequence must be an exact integer").equals(BigInteger.valueOf(sequence+1L))
                        &&textEquals(entry.get("previous_sha256"),previous),"journal entries missing, duplicated or out of order");
                List<Value> rows=array(entry.get("history_rows"),"journal history rows must be an array").values();
                require(!rows.isEmpty(),"empty committed delta");
                ObjectValue scalar=object(entry.get("state_fields"),"journal scalar state must be an object");
                // Python overwrites a possible command_history key before checking _meta. Preserve that exact behavior.
                meta(scalar.with("command_history",new ArrayValue(List.of())));
                require(integerEquals(scalar.get("format_version"),2),"delta scalar state is not v2");
                for(Value value:rows) {
                    ObjectValue row=object(value,"journal row must be an object");
                    require(integer(row.get("index"),"history index must be an exact integer").equals(index),"journal history gap or duplicate");
                    index=index.add(BigInteger.ONE);
                }
                var body=new LinkedHashMap<>(entry.fields());body.remove("sha256");
                String expected=digest(entry.get("sha256"));
                require(canonical(new ObjectValue(body),MAXIMUM_JOURNAL_BYTES).sha256().equals(expected),"journal entry checksum mismatch");
                previous=expected;
            }
            String current=sha256(originalBase);
            if(textEquals(marker,current)) {
                require(integerEquals(base.get("format_version"),2),"consolidated base is not v2");meta(base);
                return new Replayed(Status.ALREADY_CONSOLIDATED,base);
            }
            require(current.equals(digest(journal.get("base_sha256"))),"base SHA does not match journal");
            exact(base,Set.of("format_version","schema","sealed_full_state"),"journal baseline lacks its sealed envelope");
            require(integerEquals(base.get("format_version"),3)&&textEquals(base.get("schema"),SEALED_SCHEMA),"journal baseline envelope changed");
            ObjectValue full=object(base.get("sealed_full_state"),"sealed full state must be an object");meta(full);
            require(integerEquals(full.get("format_version"),2),"sealed full state is not v2");
            var history=new ArrayList<>(array(full.get("command_history"),"base history unavailable").values());
            require(BigInteger.valueOf(history.size()).equals(baseRows),"base history count does not match journal");
            for(Value value:entries) {
                ObjectValue entry=object(value,"journal entry");history.addAll(array(entry.get("history_rows"),"journal history").values());
                full=object(entry.get("state_fields"),"journal scalar state");
            }
            full=full.with("command_history",new ArrayValue(history)).with("format_version",new IntegerValue(BigInteger.TWO));
            return new Replayed(Status.REPLAYED,full);
        }catch(InputRejected strict){throw strict;}
        catch(JournalInvalid original){throw original;}
        catch(IllegalArgumentException|ArithmeticException bad){throw new JournalInvalid("journal validation failed",bad);}
    }
    public static Value parse(byte[] original,int maximum) {
        if(original!=null&&original.length>maximum)throw new InputRejected("original exceeds the complete Java parser resource lease",null);
        try{return RetainedJson.parse(original,new ParseBudget(maximum,MAXIMUM_VALUES,128));}
        catch(IllegalArgumentException invalid) {
            for(Throwable cause=invalid;cause!=null;cause=cause.getCause()) {
                String message=Objects.toString(cause.getMessage(),"");
                if(cause.getClass().getName().endsWith("StreamConstraintsException")||message.contains("resource lease")
                        ||message.contains("retained JSON depth")||message.contains("Duplicate field")||message.contains("unpaired")
                        ||message.contains("NaN")||message.contains("Infinity"))
                    throw new InputRejected("original rejected by the stricter Java JSON/resource boundary",invalid);
            }
            throw invalid;
        }
    }
    public static CanonicalForm canonical(Value value,int maximum) {
        try{return RetainedJson.pythonCanonical(value,new CanonicalBudget(maximum,MAXIMUM_VALUES,128));}
        catch(IllegalArgumentException unavailable){throw new InputRejected("complete Python canonicalization exceeded its Java value/resource boundary",unavailable);}
    }
    private static void meta(ObjectValue full) {
        var fields=new HashSet<>(full.fields().keySet());fields.remove("command_history");
        var plural=new HashSet<>(META);plural.add("rollback_war_failures");
        require(fields.equals(META)||fields.equals(plural),"full-state scalar schema requires a barrier");
    }
    static void exact(ObjectValue value,Set<String> expected,String detail){require(value.fields().keySet().equals(expected),detail);}
    static ObjectValue object(Value value,String detail){if(value instanceof ObjectValue object)return object;throw new JournalInvalid(detail);}
    static ArrayValue array(Value value,String detail){if(value instanceof ArrayValue array)return array;throw new JournalInvalid(detail);}
    static BigInteger integer(Value value,String detail){if(value instanceof IntegerValue integer)return integer.value();throw new JournalInvalid(detail);}
    static boolean integerEquals(Value value,long expected){return value instanceof IntegerValue integer&&integer.value().equals(BigInteger.valueOf(expected));}
    static boolean textEquals(Value value,String expected){return value instanceof StringValue text&&text.value().equals(expected);}
    private static String digest(Value value){if(value instanceof StringValue text&&text.value().matches("[0-9a-f]{64}"))return text.value();throw new JournalInvalid("lowercase SHA-256 required");}
    static void require(boolean condition,String detail){if(!condition)throw new JournalInvalid(detail);}
    static String sha256(byte[] bytes){try{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));}catch(NoSuchAlgorithmException impossible){throw new AssertionError(impossible);}}
}
