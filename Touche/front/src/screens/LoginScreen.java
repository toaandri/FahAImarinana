package screens;

import utils.Colors;
import utils.Responsive;
import utils.ScreenManager;
import components.CustomButton;
import javax.microedition.lcdui.Canvas;
import javax.microedition.lcdui.Graphics;

public class LoginScreen extends Canvas {
    private String code = "";
    private CustomButton loginBtn;
    private String message = "";
    private int animFrame = 0;
    private Thread animThread;

    public LoginScreen() {
        setFullScreenMode(true);
        animThread = new Thread(new Runnable() {
            public void run() {
                while (true) {
                    animFrame = (animFrame + 1) % 4;
                    try { Thread.sleep(250); } catch (InterruptedException e) { }
                    repaint();
                }
            }
        });
        animThread.start();
    }

    protected void paint(Graphics g) {
        Responsive.init(this);
        int w = getWidth();
        int h = getHeight();
        g.setColor(Colors.PETROL_BLUE);
        g.fillRect(0, 0, w, h);
        // logo circle
        int logoSize = Responsive.scale(48);
        int logoX = (w - logoSize) / 2;
        int logoY = Responsive.scale(30);
        g.setColor(Colors.TURQUOISE);
        g.fillRoundRect(logoX, logoY, logoSize, logoSize, logoSize, logoSize);
        g.setColor(Colors.WHITE);
        g.drawString("F", logoX + logoSize / 2, logoY + logoSize / 2, Graphics.BASELINE | Graphics.HCENTER);
        g.drawString("FA AI MARINANA", w / 2, logoY + logoSize + Responsive.scale(8), Graphics.TOP | Graphics.HCENTER);
        g.setColor(Colors.WHITE);
        g.drawString("Entrez le code d'acces", w / 2, logoY + logoSize + Responsive.scale(28), Graphics.TOP | Graphics.HCENTER);
        int fieldW = (int)(w * 0.7);
        int fieldH = Responsive.scale(28);
        int x = (w - fieldW) / 2;
        int y = logoY + logoSize + Responsive.scale(52);
        // field shadow
        g.setColor(Colors.SECONDARY_GRAY);
        g.fillRoundRect(x + 2, y + 2, fieldW, fieldH, 6, 6);
        g.setColor(Colors.WHITE);
        g.fillRoundRect(x, y, fieldW, fieldH, 6, 6);
        g.setColor(Colors.PETROL_BLUE);
        g.drawRoundRect(x, y, fieldW, fieldH, 6, 6);
        g.setColor(Colors.BLACK);
        g.drawString(code, x + Responsive.scale(8), y + Responsive.scale(6), Graphics.TOP | Graphics.LEFT);
        if (code.length() == 0) {
            g.setColor(Colors.SECONDARY_GRAY);
            g.drawString("****", x + Responsive.scale(8), y + Responsive.scale(6), Graphics.TOP | Graphics.LEFT);
        }
        int btnY = y + fieldH + Responsive.scale(16);
        loginBtn = new CustomButton("ENTRER", x, btnY, fieldW, Responsive.scale(32));
        loginBtn.paint(g);
        if (message.length() > 0) {
            g.setColor(Colors.TURQUOISE);
            g.drawString(message, w / 2, btnY + Responsive.scale(40), Graphics.TOP | Graphics.HCENTER);
        }
        // animation dots
        int dotY = h - Responsive.scale(24);
        int dotX = w / 2 - Responsive.scale(18);
        for (int i = 0; i < 4; i++) {
            if (i < animFrame) g.setColor(Colors.TURQUOISE);
            else g.setColor(Colors.SECONDARY_GRAY);
            g.fillRoundRect(dotX + i * Responsive.scale(12), dotY, Responsive.scale(8), Responsive.scale(8), 4, 4);
        }
    }

    protected void keyPressed(int keyCode) {
        if (keyCode == -8 || keyCode == 8) {
            if (code.length() > 0) code = code.substring(0, code.length() - 1);
            repaint(); return;
        }
        int action = getGameAction(keyCode);
        if (action == FIRE) { handleLogin(); return; }
        char c = (char) keyCode;
        if (c >= '0' && c <= '9') { code += c; repaint(); }
    }

    protected void pointerPressed(int x, int y) {
        if (loginBtn != null && loginBtn.contains(x, y)) {
            loginBtn.pressed = true;
            repaint();
        }
    }

    protected void pointerReleased(int x, int y) {
        if (loginBtn != null && loginBtn.contains(x, y)) {
            loginBtn.pressed = false;
            handleLogin();
        }
        repaint();
    }

    private void handleLogin() {
        if ("1234".equals(code)) {
            message = "Acces autorise";
            repaint();
            ScreenManager.show(new ChatScreen());
        } else {
            message = "Code incorrect";
            code = "";
            repaint();
        }
    }
}
