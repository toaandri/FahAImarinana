package screens;

import utils.Colors;
import utils.Responsive;
import utils.ScreenManager;
import components.NavigationBar;
import components.MessageBubble;
import components.CustomButton;
import models.Message;
import screens.SmsNewsScreen;
import screens.PublicationScreen;
import screens.LoginScreen;
import javax.microedition.lcdui.Canvas;
import javax.microedition.lcdui.Graphics;
import java.util.Vector;

public class ChatScreen extends Canvas implements javax.microedition.lcdui.CommandListener {
    private Vector messages = new Vector();
    private String input = "";
    private NavigationBar nav = new NavigationBar();
    private CustomButton backBtn;
    private int scrollY = 0;
    private int lastDragY = 0;
    private int maxScroll = 0;

    public ChatScreen() {
        setFullScreenMode(true);
        messages.addElement(new Message("Bonjour ! Comment puis-je vous aider ?", false));
        javax.microedition.lcdui.Command backCmd = new javax.microedition.lcdui.Command("Retour", javax.microedition.lcdui.Command.BACK, 0);
        addCommand(backCmd);
        setCommandListener(this);
    }

    protected void paint(Graphics g) {
        Responsive.init(this);
        int w = getWidth();
        int h = getHeight();
        g.setColor(Colors.WHITE);
        g.fillRect(0, 0, w, h);
        // top bar
        int barH = Responsive.scale(32);
        g.setColor(Colors.PETROL_BLUE);
        g.fillRect(0, 0, w, barH);
        g.setColor(Colors.WHITE);
        g.drawString("FA AI MARINANA", w / 2, barH / 2, Graphics.BASELINE | Graphics.HCENTER);
        backBtn = new CustomButton("Retour", Responsive.scale(4), Responsive.scale(4), Responsive.scale(52), barH - Responsive.scale(8));
        backBtn.paint(g);
        // messages area
        int navH = nav.getBarHeight();
        int inputH = Responsive.scale(30);
        int areaTop = barH + Responsive.scale(4);
        int areaBottom = h - navH - inputH - Responsive.scale(4);
        int y = areaTop - scrollY;
        for (int i = 0; i < messages.size(); i++) {
            Message m = (Message) messages.elementAt(i);
            int bh = MessageBubble.paint(g, m, Responsive.scale(8), y, w - Responsive.scale(16));
            y += bh + Responsive.scale(4);
        }
        maxScroll = Math.max(0, y + scrollY - areaBottom);
        if (scrollY > maxScroll) scrollY = maxScroll;
        // input
        int inputY = h - navH - inputH;
        g.setColor(Colors.LIGHT_GRAY);
        g.fillRect(Responsive.scale(8), inputY, w - Responsive.scale(60), inputH);
        g.setColor(Colors.SECONDARY_GRAY);
        g.drawRect(Responsive.scale(8), inputY, w - Responsive.scale(60), inputH);
        g.setColor(Colors.BLACK);
        if (input.length() == 0) {
            g.setColor(Colors.SECONDARY_GRAY);
            g.drawString("Ecrire un message...", Responsive.scale(12), inputY + 4, Graphics.TOP | Graphics.LEFT);
            g.setColor(Colors.BLACK);
        } else {
            g.drawString(input, Responsive.scale(12), inputY + 4, Graphics.TOP | Graphics.LEFT);
        }
        // send button
        g.setColor(Colors.TURQUOISE);
        g.fillRoundRect(w - Responsive.scale(48), inputY, Responsive.scale(40), inputH, 6, 6);
        g.setColor(Colors.WHITE);
        g.drawString(">", w - Responsive.scale(28), inputY + inputH / 2, Graphics.BASELINE | Graphics.HCENTER);
        nav.paint(g, w, h);
    }

    protected void keyPressed(int keyCode) {
        if (keyCode == -6 || keyCode == -7) {
            ScreenManager.show(new LoginScreen());
            return;
        }
        int action = getGameAction(keyCode);
        if (action == UP) { scrollY = Math.max(0, scrollY - Responsive.scale(20)); repaint(); return; }
        if (action == DOWN) { scrollY = Math.min(maxScroll, scrollY + Responsive.scale(20)); repaint(); return; }
        if (keyCode == -8 || keyCode == 8) {
            if (input.length() > 0) input = input.substring(0, input.length() - 1);
            repaint(); return;
        }
        if (action == FIRE) { sendMessage(); return; }
        char c = (char) keyCode;
        if (c >= 32 && c < 127) { input += c; repaint(); }
    }

    protected void pointerPressed(int x, int y) {
        lastDragY = y;
        int w = getWidth();
        int h = getHeight();
        int navH = nav.getBarHeight();
        if (backBtn != null && backBtn.contains(x, y)) {
            backBtn.pressed = true;
            repaint(); return;
        }
        int idx = nav.hitTest(x, y, w, h);
        if (idx >= 0) {
            nav.selected = idx;
            navigate(idx);
            repaint(); return;
        }
        int inputY = h - navH - Responsive.scale(30);
        if (x >= w - Responsive.scale(48) && y >= inputY) {
            sendMessage();
        }
    }

    protected void pointerReleased(int x, int y) {
        if (backBtn != null && backBtn.contains(x, y)) {
            backBtn.pressed = false;
            ScreenManager.show(new LoginScreen());
            repaint(); return;
        }
    }

    protected void pointerDragged(int x, int y) {
        int delta = lastDragY - y;
        scrollY = Math.max(0, Math.min(maxScroll, scrollY + delta));
        lastDragY = y;
        repaint();
    }

    private void sendMessage() {
        if (input.trim().length() == 0) return;
        messages.addElement(new Message(input, true));
        messages.addElement(new Message("Reponse fictive de l'IA.", false));
        input = "";
        scrollY = maxScroll;
        repaint();
    }

    private void navigate(int idx) {
        if (idx == 1) ScreenManager.show(new SmsNewsScreen());
        else if (idx == 2) ScreenManager.show(new PublicationScreen());
    }

    public void commandAction(javax.microedition.lcdui.Command c, javax.microedition.lcdui.Displayable d) {
        ScreenManager.show(new LoginScreen());
    }
}
