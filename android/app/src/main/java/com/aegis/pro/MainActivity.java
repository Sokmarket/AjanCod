package com.aegis.pro;

import android.app.Activity;
import android.os.Bundle;
import android.graphics.Color;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import com.chaquo.python.AndroidPlatform;
import com.chaquo.python.PyObject;
import com.chaquo.python.Python;

import org.json.JSONArray;
import org.json.JSONObject;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public final class MainActivity extends Activity {
    private final ExecutorService executor = Executors.newSingleThreadExecutor();
    private TextView output;
    private String workspace;

    @Override
    public void onCreate(Bundle state) {
        super.onCreate(state);
        workspace = getFilesDir().getAbsolutePath() + "/workspace";

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(32, 36, 32, 24);
        root.setBackgroundColor(Color.rgb(12, 20, 38));

        TextView title = new TextView(this);
        title.setText("AEGIS PRO");
        title.setTextColor(Color.rgb(120, 190, 255));
        title.setTextSize(28);
        title.setPadding(0, 0, 0, 8);
        root.addView(title);

        TextView subtitle = new TextView(this);
        subtitle.setText("Yerel mühendislik çekirdeği · v0.3.0");
        subtitle.setTextColor(Color.LTGRAY);
        subtitle.setTextSize(14);
        root.addView(subtitle);

        addButton(root, "Sistem tanılaması", new String[]{"doctor"});
        addButton(root, "Çalışma alanını oluştur",
                new String[]{"init", "--workspace", workspace});
        addButton(root, "Python projesini incele",
                new String[]{"inspect", "--workspace", workspace});
        addButton(root, "Ekran izni durumu",
                new String[]{"screen-permission", "status",
                             "--workspace", workspace});

        ScrollView scroll = new ScrollView(this);
        output = new TextView(this);
        output.setTextColor(Color.WHITE);
        output.setTextSize(13);
        output.setText("Hazır. Bir işlem seçin.");
        output.setPadding(0, 24, 0, 24);
        scroll.addView(output);
        root.addView(scroll, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 0, 1));

        setContentView(root);

        if (!Python.isStarted()) {
            Python.start(new AndroidPlatform(this));
        }
    }

    private void addButton(LinearLayout root, String label, String[] args) {
        Button button = new Button(this);
        button.setText(label);
        button.setAllCaps(false);
        root.addView(button);
        button.setOnClickListener(v -> execute(args));
    }

    private void execute(String[] args) {
        output.setText("İşlem çalıştırılıyor…");
        executor.execute(() -> {
            String result;
            try {
                JSONArray list = new JSONArray();
                for (String arg : args) list.put(arg);

                PyObject bridge = Python.getInstance()
                        .getModule("android_bridge");
                String raw = bridge.callAttr(
                        "run_command_json", list.toString()).toString();

                JSONObject data = new JSONObject(raw);
                result = "Çıkış kodu: " + data.optInt("exit_code") + "\n\n"
                        + data.optString("stdout") + "\n"
                        + data.optString("stderr");
            } catch (Exception e) {
                result = "İşlem hatası: " + e.getClass().getSimpleName()
                        + "\n" + String.valueOf(e.getMessage());
            }

            final String shown = result;
            runOnUiThread(() -> output.setText(shown));
        });
    }

    @Override
    protected void onDestroy() {
        executor.shutdownNow();
        super.onDestroy();
    }
}
