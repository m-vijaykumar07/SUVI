package com.suvi.voice;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.BatteryManager;
import android.os.Vibrator;
import android.webkit.JavascriptInterface;
import android.widget.Toast;

import java.net.URLEncoder;

public class SuviBridge {
    private final Activity activity;

    public SuviBridge(Activity activity) {
        this.activity = activity;
    }

    @JavascriptInterface
    public void toast(String message) {
        activity.runOnUiThread(() -> Toast.makeText(activity, message, Toast.LENGTH_SHORT).show());
    }

    @JavascriptInterface
    public void vibrate(long ms) {
        Vibrator v = (Vibrator) activity.getSystemService(Context.VIBRATOR_SERVICE);
        if (v != null) {
            v.vibrate(ms);
        }
    }

    @JavascriptInterface
    public void makeCall(String phoneNumber) {
        try {
            Intent intent = new Intent(Intent.ACTION_CALL, Uri.parse("tel:" + phoneNumber));
            if (activity.checkSelfPermission(android.Manifest.permission.CALL_PHONE) == PackageManager.PERMISSION_GRANTED) {
                activity.startActivity(intent);
            } else {
                Intent dialIntent = new Intent(Intent.ACTION_DIAL, Uri.parse("tel:" + phoneNumber));
                activity.startActivity(dialIntent);
            }
        } catch (Exception e) {
            toast("Error dialing call: " + e.getMessage());
        }
    }

    @JavascriptInterface
    public void sendWhatsApp(String phoneNumber, String message) {
        try {
            String encoded = URLEncoder.encode(message, "UTF-8");
            String url = "https://api.whatsapp.com/send?phone=" + phoneNumber + "&text=" + encoded;
            Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(url));
            activity.startActivity(intent);
        } catch (Exception e) {
            toast("WhatsApp error: " + e.getMessage());
        }
    }

    @JavascriptInterface
    public void openApp(String packageName) {
        try {
            Intent launchIntent = activity.getPackageManager().getLaunchIntentForPackage(packageName);
            if (launchIntent != null) {
                activity.startActivity(launchIntent);
            } else {
                toast("Application not installed: " + packageName);
            }
        } catch (Exception e) {
            toast("Error opening app: " + e.getMessage());
        }
    }

    @JavascriptInterface
    public int getBatteryLevel() {
        BatteryManager bm = (BatteryManager) activity.getSystemService(Context.BATTERY_SERVICE);
        if (bm != null) {
            return bm.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY);
        }
        return -1;
    }
}
