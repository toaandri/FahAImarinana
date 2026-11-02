package network;

import java.util.Hashtable;
import java.util.Vector;
import java.util.Enumeration;

/** Small bounded JSON codec using only CLDC 1.1 collections. */
public final class Json {
    public static final Object NULL = new Object();
    private String text;
    private int at;
    private Json(String value) { text = value; }
    public static Object parse(String text) {
        if (text == null || text.length() > 262144) throw new IllegalArgumentException("JSON trop volumineux");
        Json parser = new Json(text);
        Object value = parser.read(0);
        parser.space();
        if (parser.at != text.length()) throw new IllegalArgumentException("JSON incomplet");
        return value;
    }
    public static Hashtable object() { return new Hashtable(); }
    public static String str(Hashtable data, String key) {
        Object value = data.get(key);
        return value == null || value == NULL ? "" : value.toString();
    }
    public static String encode(Object value) {
        if (value == null || value == NULL) return "null";
        if (value instanceof String) return quote((String)value);
        if (value instanceof Hashtable) {
            StringBuffer out = new StringBuffer("{");
            Enumeration keys = ((Hashtable)value).keys();
            boolean first = true;
            while (keys.hasMoreElements()) {
                String key = (String)keys.nextElement();
                if (!first) out.append(',');
                first = false;
                out.append(quote(key)).append(':').append(encode(((Hashtable)value).get(key)));
            }
            return out.append('}').toString();
        }
        if (value instanceof Vector) {
            StringBuffer out = new StringBuffer("[");
            for (int i = 0; i < ((Vector)value).size(); i++) {
                if (i > 0) out.append(',');
                out.append(encode(((Vector)value).elementAt(i)));
            }
            return out.append(']').toString();
        }
        if (value instanceof Boolean || value instanceof Long || value instanceof Integer || value instanceof Double) return value.toString();
        throw new IllegalArgumentException("Type JSON non pris en charge");
    }
    private static String quote(String text) {
        StringBuffer out = new StringBuffer("\"");
        for (int i = 0; i < text.length(); i++) {
            char ch = text.charAt(i);
            if (ch == '"' || ch == '\\') out.append('\\').append(ch);
            else if (ch < 32) {
                String hex = Integer.toHexString(ch);
                out.append("\\u");
                for (int j = hex.length(); j < 4; j++) out.append('0');
                out.append(hex);
            } else out.append(ch);
        }
        return out.append('"').toString();
    }
    private void space() { while (at < text.length() && " \n\r\t".indexOf(text.charAt(at)) >= 0) at++; }
    private Object read(int depth) {
        if (depth > 32) throw new IllegalArgumentException("JSON trop imbrique");
        space();
        if (at >= text.length()) throw new IllegalArgumentException("JSON vide");
        char ch = text.charAt(at++);
        if (ch == '"') return string();
        if (ch == '{') {
            Hashtable value = object(); space();
            if (take('}')) return value;
            do {
                space(); need('"'); String key = string(); space(); need(':');
                if (value.containsKey(key)) throw new IllegalArgumentException("Cle JSON dupliquee");
                value.put(key,read(depth+1)); space();
                if (take('}')) return value;
                need(',');
            } while (true);
        }
        if (ch == '[') {
            Vector value = new Vector(); space();
            if (take(']')) return value;
            do {
                value.addElement(read(depth+1)); space();
                if (take(']')) return value;
                need(',');
            } while (true);
        }
        at--;
        if (literal("true")) return Boolean.TRUE;
        if (literal("false")) return Boolean.FALSE;
        if (literal("null")) return NULL;
        int start = at;
        take('-');
        if (!take('0')) { digits(); }
        boolean decimal = false;
        if (take('.')) { decimal = true; digits(); }
        if (take('e') || take('E')) { decimal = true; if (!take('+')) take('-'); digits(); }
        if (start == at) throw new IllegalArgumentException("Valeur JSON invalide");
        String number = text.substring(start,at);
        if (decimal) return Double.valueOf(number);
        return Long.valueOf(number);
    }
    private void digits() {
        int start = at;
        while (at < text.length() && text.charAt(at) >= '0' && text.charAt(at) <= '9') at++;
        if (start == at) throw new IllegalArgumentException("Nombre JSON invalide");
    }
    private boolean literal(String token) {
        if (!text.startsWith(token,at)) return false;
        at += token.length(); return true;
    }
    private boolean take(char ch) {
        if (at < text.length() && text.charAt(at) == ch) { at++; return true; }
        return false;
    }
    private void need(char ch) { if (!take(ch)) throw new IllegalArgumentException("JSON invalide"); }
    private String string() {
        StringBuffer value = new StringBuffer();
        while (at < text.length()) {
            char ch = text.charAt(at++);
            if (ch == '"') return value.toString();
            if (ch < 32) throw new IllegalArgumentException("Chaine JSON invalide");
            if (ch == '\\') {
                if (at >= text.length()) break;
                ch = text.charAt(at++);
                if (ch == 'n') ch = '\n'; else if (ch == 'r') ch = '\r';
                else if (ch == 't') ch = '\t'; else if (ch == 'b') ch = '\b';
                else if (ch == 'f') ch = '\f';
                else if (ch == 'u') {
                    if (at+4 > text.length()) break;
                    ch = (char)Integer.parseInt(text.substring(at,at+4),16); at += 4;
                } else if (ch != '"' && ch != '\\' && ch != '/') throw new IllegalArgumentException("Echappement JSON invalide");
            }
            value.append(ch);
        }
        throw new IllegalArgumentException("Chaine JSON incomplete");
    }
}
