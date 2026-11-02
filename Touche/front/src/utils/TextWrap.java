package utils;

import javax.microedition.lcdui.Graphics;
import java.util.Vector;

public class TextWrap {
    public static int draw(Graphics g, String text, int x, int y, int maxW) {
        int fh = g.getFont().getHeight();
        Vector words = new Vector();
        StringBuffer w = new StringBuffer();
        for (int i = 0; i < text.length(); i++) {
            char c = text.charAt(i);
            if (c == ' ') {
                if (w.length() > 0) { words.addElement(w.toString()); w.setLength(0); }
            } else {
                w.append(c);
            }
        }
        if (w.length() > 0) words.addElement(w.toString());
        int lineY = y;
        String line = "";
        for (int i = 0; i < words.size(); i++) {
            String word = (String) words.elementAt(i);
            String test = (line.length() == 0) ? word : line + " " + word;
            if (g.getFont().stringWidth(test) <= maxW) {
                line = test;
            } else {
                if (line.length() > 0) {
                    g.drawString(line, x, lineY, Graphics.TOP | Graphics.LEFT);
                    lineY += fh + 2;
                }
                line = word;
            }
        }
        if (line.length() > 0) {
            g.drawString(line, x, lineY, Graphics.TOP | Graphics.LEFT);
            lineY += fh + 2;
        }
        if (words.size() == 0) {
            g.drawString(text, x, lineY, Graphics.TOP | Graphics.LEFT);
            lineY += fh + 2;
        }
        return lineY - y;
    }
}
