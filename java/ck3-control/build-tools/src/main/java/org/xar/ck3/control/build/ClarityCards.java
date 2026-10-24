package org.xar.ck3.control.build;

import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.awt.Color;
import java.awt.Font;
import java.awt.FontMetrics;
import java.awt.Graphics2D;
import java.awt.RenderingHints;
import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import javax.imageio.ImageIO;

/** Bounded, source-bound explanatory pages. It never creates voice or game evidence. */
public final class ClarityCards {
    private static final ObjectMapper JSON = new ObjectMapper()
            .enable(JsonParser.Feature.STRICT_DUPLICATE_DETECTION);
    private static final Color BG = new Color(0x241b15);
    private static final Color PANEL = new Color(0x30251c);
    private static final Color FG = new Color(0xeee1c5);
    private static final Color MUTED = new Color(0xb6a98e);
    private static final Color GOLD = new Color(0xd6b464);
    private static final Set<String> CARD_FIELDS = Set.of("id", "cue", "anchor_zh", "title", "kicker",
            "lines", "rows", "result", "note", "icon", "highlight");

    private ClarityCards() { }

    public record Pin(String path, long bytes, String sha256) {
        public Path verify() throws Exception {
            Path file = Path.of(path).toAbsolutePath().normalize();
            require(Files.isRegularFile(file) && !Files.isSymbolicLink(file), "regular input required");
            require(Files.size(file) == bytes && digest(file).equals(sha256), "input changed: " + file);
            return file;
        }
    }
    public record Row(String label, String value) { }
    public record Card(String id, String cue, String anchorZh, String title, String kicker,
                       List<String> lines, List<Row> rows, String result, String note, Pin icon, int highlight) { }
    public record Specification(String machineId, Pin ffmpeg, List<Card> cards) { }
    public record TextBox(String text, int x, int y, int width, int height, int fontPixels) { }
    public record Rendered(String id, String cue, String anchorZh, Pin image, List<TextBox> text,
                           boolean subtitleAreaClear, boolean decodedAfterSave, Pin icon) { }
    public record Receipt(String schema, String machineId, String observedAtUtc, Pin specification,
                          List<Rendered> cards, boolean voiceCreated, boolean gameAccessed,
                          boolean humanVideoSignoff) { }

    public static void main(String[] args) throws Exception {
        require(args.length == 3, "spec.json output-directory receipt.json required");
        Path specification = Path.of(args[0]).toAbsolutePath().normalize();
        Path directory = Path.of(args[1]).toAbsolutePath().normalize();
        Path receipt = Path.of(args[2]).toAbsolutePath().normalize();
        require(!Files.exists(receipt) && !Files.exists(directory), "create-only output required");
        Specification spec = parse(specification);
        spec.ffmpeg().verify();
        require(Files.getFileStore(directory.getParent()).getUsableSpace() > 2L * 1024 * 1024 * 1024,
                "caller storage admission plus live space required");
        Files.createDirectory(directory);
        List<Rendered> rendered = new ArrayList<>();
        for (Card card : spec.cards()) rendered.add(render(card, spec.ffmpeg(), directory));
        Receipt actual = new Receipt("xar.clarity-cards.actual/v1", spec.machineId(), Instant.now().toString(),
                pin(specification), List.copyOf(rendered), false, false, false);
        Files.write(receipt, JSON.writerWithDefaultPrettyPrinter().writeValueAsBytes(actual), StandardOpenOption.CREATE_NEW);
        System.out.println(JSON.writeValueAsString(pin(receipt)));
    }

    public static Specification parse(Path file) throws IOException {
        require(Files.size(file) <= 1024 * 1024, "bounded specification required");
        JsonNode root = JSON.readTree(Files.readAllBytes(file));
        fields(root, Set.of("schema", "machine_id", "ffmpeg", "cards"));
        require(text(root, "schema").equals("xar.clarity-cards.spec/v1"), "unsupported schema");
        JsonNode cards = root.get("cards");
        require(cards.isArray() && cards.size() > 0 && cards.size() <= 160, "1..160 pages required");
        Set<String> ids = new HashSet<>();
        List<Card> result = new ArrayList<>();
        for (JsonNode item : cards) {
            fields(item, CARD_FIELDS);
            String id = text(item, "id");
            require(id.matches("[A-Za-z0-9._-]{1,100}") && ids.add(id), "unique safe page id required");
            String cue = text(item, "cue");
            require(cue.matches("E02-V6-N[0-9]{2}"), "stable cue id required");
            List<String> lines = strings(item.get("lines"), 6);
            JsonNode rows = item.get("rows");
            require(rows.isArray() && rows.size() <= 8 && (rows.isEmpty() || lines.isEmpty()), "one bounded layout required");
            List<Row> parsedRows = new ArrayList<>();
            for (JsonNode row : rows) {
                fields(row, Set.of("label", "value"));
                parsedRows.add(new Row(text(row, "label"), text(row, "value")));
            }
            JsonNode active = item.get("highlight");
            require(active.isIntegralNumber() && active.canConvertToInt(), "integer highlight required");
            int highlight = active.intValue();
            require(highlight >= -1 && highlight < Math.max(lines.size(), parsedRows.size()), "highlight out of range");
            JsonNode icon = item.get("icon");
            result.add(new Card(id, cue, text(item, "anchor_zh"), text(item, "title"), text(item, "kicker"),
                    lines, List.copyOf(parsedRows), text(item, "result"), text(item, "note"),
                    icon.isNull() ? null : parsePin(icon), highlight));
        }
        return new Specification(text(root, "machine_id"), parsePin(root.get("ffmpeg")), List.copyOf(result));
    }

    private static Rendered render(Card card, Pin ffmpeg, Path directory) throws Exception {
        BufferedImage image = new BufferedImage(2560, 1440, BufferedImage.TYPE_INT_RGB);
        Graphics2D g = image.createGraphics();
        List<TextBox> boxes = new ArrayList<>();
        try {
            g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
            g.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_ON);
            g.setColor(BG); g.fillRect(0, 0, 2560, 1440);
            draw(g, boxes, "信仰引擎  /  朝圣在奖励什么？", 120, 66, 28, MUTED, 1950);
            draw(g, boxes, "规则图解", 2280, 66, 28, GOLD, 160);
            draw(g, boxes, card.title(), 120, 176, 54, FG, 2300);
            g.setColor(GOLD); g.fillRect(120, 220, 240, 3);
            draw(g, boxes, card.kicker(), 120, 290, 32, GOLD, 2140);
            if (card.icon() != null) {
                BufferedImage icon = decodeIcon(card.icon(), ffmpeg);
                double scale = Math.min(76.0 / icon.getWidth(), 76.0 / icon.getHeight());
                int w = (int) Math.round(icon.getWidth() * scale), h = (int) Math.round(icon.getHeight() * scale);
                g.setColor(new Color(0xe8d8b5)); g.fillRoundRect(2330, 246, 90, 90, 10, 10);
                g.drawImage(icon, 2337 + (76 - w) / 2, 253 + (76 - h) / 2, w, h, null);
            }
            g.setColor(PANEL); g.fillRoundRect(120, 350, 2320, 590, 18, 18);
            int count = Math.max(card.lines().size(), card.rows().size());
            int spacing = count > 6 ? 64 : count > 4 ? 88 : 112;
            int top = count > 6 ? 404 : 440;
            for (int i = 0; i < count; i++) {
                int baseline = top + i * spacing;
                boolean active = i == card.highlight();
                if (active) { g.setColor(new Color(0x4b3b22)); g.fillRoundRect(145, baseline - 48, 2270, 66, 10, 10); }
                Color color = active ? GOLD : FG;
                if (!card.lines().isEmpty()) {
                    draw(g, boxes, card.lines().get(i), 176, baseline, 46, color, 2200);
                } else {
                    Row row = card.rows().get(i);
                    draw(g, boxes, row.label(), 176, baseline, count > 6 ? 34 : 40, color, 1220);
                    draw(g, boxes, row.value(), 1450, baseline, count > 6 ? 34 : 40, color, 900);
                }
            }
            if (!card.result().isEmpty()) draw(g, boxes, card.result(), 176, 906, 58, GOLD, 2140);
            wrap(g, boxes, card.note(), 120, 1026, 30, MUTED, 2300, 2);
            for (int i = 0; i < boxes.size(); i++) for (int j = i + 1; j < boxes.size(); j++) {
                TextBox a = boxes.get(i), b = boxes.get(j);
                require(a.x() + a.width() <= b.x() || b.x() + b.width() <= a.x()
                        || a.y() + a.height() <= b.y() || b.y() + b.height() <= a.y(),
                        "text collision in " + card.id() + ": " + a.text() + " / " + b.text());
            }
        } finally { g.dispose(); }
        Path output = directory.resolve(card.id() + ".png");
        try (var stream = Files.newOutputStream(output, StandardOpenOption.CREATE_NEW)) {
            require(ImageIO.write(image, "png", stream), "PNG encoder unavailable");
        }
        BufferedImage decoded = ImageIO.read(output.toFile());
        require(decoded != null && decoded.getWidth() == 2560 && decoded.getHeight() == 1440, "PNG readback failed");
        require(Files.size(output) <= 512 * 1024, "page byte cap exceeded");
        return new Rendered(card.id(), card.cue(), card.anchorZh(), pin(output), List.copyOf(boxes), true, true, card.icon());
    }

    private static BufferedImage decodeIcon(Pin input, Pin ffmpeg) throws Exception {
        Path source = input.verify();
        if (source.toString().endsWith(".png")) {
            BufferedImage image = ImageIO.read(source.toFile());
            require(image != null, "icon decode failed"); return image;
        }
        Process process = new ProcessBuilder(ffmpeg.path(), "-v", "error", "-i", source.toString(),
                "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "pipe:1")
                .redirectError(ProcessBuilder.Redirect.INHERIT).start();
        byte[] bytes = process.getInputStream().readNBytes(1024 * 1024 + 1);
        boolean finished = process.waitFor(30, TimeUnit.SECONDS);
        if (!finished) process.destroyForcibly();
        require(finished && process.exitValue() == 0 && bytes.length <= 1024 * 1024, "bounded icon conversion failed");
        BufferedImage decoded = ImageIO.read(new ByteArrayInputStream(bytes));
        require(decoded != null, "converted icon decode failed"); return decoded;
    }

    private static void draw(Graphics2D g, List<TextBox> boxes, String text, int x, int baseline,
                             int pixels, Color color, int width) {
        if (text.isEmpty()) return;
        Font font = new Font("Microsoft YaHei", Font.PLAIN, pixels);
        require(font.canDisplayUpTo(text) == -1, "font lacks a required character: " + text);
        g.setFont(font); FontMetrics metrics = g.getFontMetrics();
        require(metrics.stringWidth(text) <= width, "text exceeds line: " + text);
        int y = baseline - metrics.getAscent();
        require(y >= 0 && baseline + metrics.getDescent() <= 1120, "text enters subtitle region");
        boxes.add(new TextBox(text, x, y, metrics.stringWidth(text), metrics.getHeight(), pixels));
        g.setColor(color); g.drawString(text, x, baseline);
    }

    private static void wrap(Graphics2D g, List<TextBox> boxes, String text, int x, int baseline,
                             int pixels, Color color, int width, int maxLines) {
        g.setFont(new Font("Microsoft YaHei", Font.PLAIN, pixels));
        FontMetrics metrics = g.getFontMetrics(); StringBuilder line = new StringBuilder(); int lineCount = 0;
        for (int offset = 0; offset < text.length();) {
            int cp = text.codePointAt(offset); String next = new String(Character.toChars(cp));
            if (!line.isEmpty() && metrics.stringWidth(line + next) > width) {
                draw(g, boxes, line.toString(), x, baseline + lineCount * 44, pixels, color, width);
                lineCount++; line.setLength(0); require(lineCount < maxLines, "note exceeds page");
            }
            line.append(next); offset += Character.charCount(cp);
        }
        draw(g, boxes, line.toString(), x, baseline + lineCount * 44, pixels, color, width);
    }

    private static List<String> strings(JsonNode node, int max) {
        require(node.isArray() && node.size() <= max, "bounded string array required");
        List<String> result = new ArrayList<>();
        for (JsonNode value : node) { require(value.isTextual(), "string required"); result.add(value.textValue()); }
        return List.copyOf(result);
    }
    private static Pin parsePin(JsonNode node) {
        fields(node, Set.of("path", "bytes", "sha256"));
        JsonNode size = node.get("bytes");
        require(size.isIntegralNumber() && size.canConvertToLong() && size.longValue() >= 0, "exact integer bytes required");
        String digest = text(node, "sha256"); require(digest.matches("[0-9a-f]{64}"), "canonical SHA required");
        String path = text(node, "path"); require(Path.of(path).isAbsolute(), "absolute source path required");
        return new Pin(path, size.longValue(), digest);
    }
    private static String text(JsonNode node, String field) {
        JsonNode value = node.get(field); require(value != null && value.isTextual(), "string required: " + field);
        return value.textValue();
    }
    private static void fields(JsonNode node, Set<String> expected) {
        require(node != null && node.isObject(), "object required");
        Set<String> actual = new HashSet<>(); node.fieldNames().forEachRemaining(actual::add);
        require(actual.equals(expected), "missing or extra fields: " + actual);
    }
    private static Pin pin(Path file) throws Exception { return new Pin(file.toString(), Files.size(file), digest(file)); }
    private static String digest(Path file) throws Exception {
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        try (var stream = Files.newInputStream(file)) { byte[] chunk = new byte[65536]; int count;
            while ((count = stream.read(chunk)) != -1) digest.update(chunk, 0, count); }
        return HexFormat.of().formatHex(digest.digest());
    }
    private static void require(boolean condition, String message) {
        if (!condition) throw new IllegalArgumentException(message);
    }
}
