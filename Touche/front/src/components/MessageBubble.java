package components;

import utils.Colors;
import utils.Responsive;
import javax.microedition.lcdui.Graphics;
import models.Message;
import java.util.Vector;

public class MessageBubble {
    public static int paint(Graphics g, Message m, int x, int y, int maxW) {
        int pad = Responsive.scale(6);
        int fh = g.getFont().getHeight();
        // wrap text
        Vector words = new Vector();
        StringBuffer w = new StringBuffer();
        for (int i = 0; i < m.text.length(); i++) {
            char c = m.text.charAt(i);
            if (c == ' ') {
                if (w.length() > 0) { words.addElement(w.toString()); w.setLength(0); }
            } else {
                w.append(c);
            }
        }
        if (w.length() > 0) words.addElement(w.toString());
        Vector lines = new Vector();
        String line = "";
        int maxLineW = 0;
        for (int i = 0; i < words.size(); i++) {
            String word = (String) words.elementAt(i);
            String test = (line.length() == 0) ? word : line + " " + word;
            if (g.getFont().stringWidth(test) <= maxW - pad * 2) {
                line = test;
            } else {
                if (line.length() > 0) {
                    lines.addElement(line);
                    int lw = g.getFont().stringWidth(line);
                    if (lw > maxLineW) maxLineW = lw;
                    line = word;
                } else {
                    lines.addElement(word);
                    int lw = g.getFont().stringWidth(word);
                    if (lw > maxLineW) maxLineW = lw;
                    line = "";
                }
            }
        }
        if (line.length() > 0) {
            lines.addElement(line);
            int lw = g.getFont().stringWidth(line);
            if (lw > maxLineW) maxLineW = lw;
        }
        if (lines.size() == 0) {
            lines.addElement(m.text);
            maxLineW = g.getFont().stringWidth(m.text);
        }
        int bubbleW = Math.min(maxLineW + pad * 2, maxW);
        int bubbleH = lines.size() * (fh + 2) + pad * 2;
        int bx = m.fromUser ? (x + maxW - bubbleW) : x;
        g.setColor(m.fromUser ? Colors.TURQUOISE : Colors.LIGHT_GRAY);
        g.fillRoundRect(bx, y, bubbleW, bubbleH, Responsive.scale(8), Responsive.scale(8));
        if (!m.fromUser) {
            g.setColor(Colors.SECONDARY_GRAY);
            g.drawRoundRect(bx, y, bubbleW, bubbleH, Responsive.scale(8), Responsive.scale(8));
        }
        g.setColor(m.fromUser ? Colors.WHITE : Colors.BLACK);
        int ty = y + pad;
        for (int i = 0; i < lines.size(); i++) {
            g.drawString((String) lines.elementAt(i), bx + pad, ty, Graphics.TOP | Graphics.LEFT);
            ty += fh + 2;
        }
        return bubbleH;
    }
}
