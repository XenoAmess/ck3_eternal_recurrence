package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Full stable named-root census. Observation order never selects a reply target. */
public record CurrentLetterSetSource(int residentCount,int namedRootCount,boolean censusComplete,List<CurrentLetterSource> letters) {
    public CurrentLetterSetSource {
        Objects.requireNonNull(letters);letters=List.copyOf(letters);
        StrictJson.require(residentCount>=0&&residentCount<=32&&namedRootCount>=0&&namedRootCount<=32
                &&namedRootCount==letters.size()&&namedRootCount<=residentCount&&censusComplete,"Complete bounded actual letter census required");
        var identities=new HashSet<Integer>();
        for(var row:letters)StrictJson.require(row.letterFound()&&row.namedRootBound()&&row.residentCount()==residentCount
                &&identities.add(row.instanceId().orElseThrow()),"Letter-set rows must include every bound root and distinct actual instance");
    }
    public CurrentLetterSource exactInstance(int actualInstanceId)throws IOException {
        if(actualInstanceId<=0)throw new IOException("Positive actual letter instance DATA required");
        CurrentLetterSource selected=null;
        for(var row:letters)if(row.instanceId().orElseThrow()==actualInstanceId){if(selected!=null)throw new IOException("Ambiguous actual instance in full census");selected=row;}
        if(selected==null)throw new IOException("Desired actual instance absent from original full census");
        return selected;
    }
    static CurrentLetterSetSource decode(JsonNode value)throws IOException {
        var r=StrictJson.object(value,Set.of("schema","resident_count","named_root_count","census_complete","letters"));
        if(!NativeWire.text(r.get("schema")).equals(CurrentLetterSet.SOURCE_SCHEMA))throw new IOException("Exact current letter-set source schema required");
        if(!r.get("letters").isArray()||r.get("letters").size()>32)throw new IOException("Bounded full letter census array required");
        var rows=new ArrayList<CurrentLetterSource>();for(var row:r.get("letters"))rows.add(CurrentLetterSource.decode(row));
        return new CurrentLetterSetSource(i32(r.get("resident_count")),i32(r.get("named_root_count")),bool(r,"census_complete"),rows);
    }
    ObjectNode encode() {
        var r=StrictJson.object().put("schema",CurrentLetterSet.SOURCE_SCHEMA).put("resident_count",residentCount)
                .put("named_root_count",namedRootCount).put("census_complete",censusComplete);
        var rows=r.putArray("letters");for(var row:letters)rows.add(row.encode());return r;
    }
    private static int i32(JsonNode value)throws IOException{return NativeWire.integer(value,BigInteger.valueOf(Integer.MIN_VALUE),BigInteger.valueOf(Integer.MAX_VALUE)).intValueExact();}
    private static boolean bool(ObjectNode object,String key)throws IOException {var value=object.get(key);if(value==null||!value.isBoolean())throw new IOException("Actual census bool required: "+key);return value.booleanValue();}
}
