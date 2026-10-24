package org.xar.ck3.control.build;

import com.fasterxml.jackson.core.JsonGenerator;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.JsonToken;
import com.fasterxml.jackson.databind.DeserializationContext;
import com.fasterxml.jackson.databind.JsonDeserializer;
import com.fasterxml.jackson.databind.JsonSerializer;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializerProvider;
import com.fasterxml.jackson.databind.module.SimpleModule;
import java.io.IOException;
import java.time.Duration;
import java.time.Instant;
import java.time.format.DateTimeParseException;

/** Shared strict temporal wire for the actual finite Map/native input producers and consumers. */
public final class RootNativePlanJson {
    private RootNativePlanJson() { }

    /** Returns an independent mapper; the global SDK/build receipt mapper is unchanged. */
    public static ObjectMapper mapper() {
        SimpleModule temporal = new SimpleModule("xar-root-native-plan-iso-time-v1");
        temporal.addSerializer(Instant.class,new JsonSerializer<Instant>() {
            @Override public void serialize(Instant value,JsonGenerator output,SerializerProvider provider) throws IOException {
                output.writeString(value.toString());
            }
        });
        temporal.addDeserializer(Instant.class,new JsonDeserializer<Instant>() {
            @Override public Instant deserialize(JsonParser input,DeserializationContext context) throws IOException {
                String value=string(input,context,Instant.class);
                if(!value.matches("[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\\.[0-9]{1,9})?Z"))
                    throw context.weirdStringException(value,Instant.class,"Explicit UTC ISO instant required");
                try { return Instant.parse(value); }
                catch(DateTimeParseException invalid) { throw context.weirdStringException(value,Instant.class,"Invalid UTC ISO instant"); }
            }
        });
        temporal.addSerializer(Duration.class,new JsonSerializer<Duration>() {
            @Override public void serialize(Duration value,JsonGenerator output,SerializerProvider provider) throws IOException {
                output.writeString(value.toString());
            }
        });
        temporal.addDeserializer(Duration.class,new JsonDeserializer<Duration>() {
            @Override public Duration deserialize(JsonParser input,DeserializationContext context) throws IOException {
                String value=string(input,context,Duration.class);
                try { return Duration.parse(value); }
                catch(DateTimeParseException invalid) { throw context.weirdStringException(value,Duration.class,"ISO duration string required"); }
            }
        });
        return ControlBuild.strictMapper().copy().registerModule(temporal);
    }
    private static String string(JsonParser input,DeserializationContext context,Class<?> type) throws IOException {
        if(input.currentToken()!=JsonToken.VALUE_STRING)
            throw context.wrongTokenException(input,type,JsonToken.VALUE_STRING,"Temporal fields accept ISO strings only");
        return input.getText();
    }
}
