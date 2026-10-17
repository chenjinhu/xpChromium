// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

package com.xpchromium;

import android.os.Looper;
import android.webkit.WebView;

import java.lang.reflect.InvocationTargetException;

/** Copy into the host app. Call on the main thread before any WebView startup. */
public final class Fingerprint {
    private Fingerprint() {}

    public static void configure(String json) {
        if (Looper.myLooper() != Looper.getMainLooper()) {
            throw new IllegalStateException("Configure fingerprint on the main thread");
        }
        try {
            Class<?> api = WebView.getWebViewClassLoader()
                    .loadClass("com.android.webview.chromium.FingerprintConfig");
            String error = (String) api.getMethod("configure", String.class).invoke(null, json);
            if (error == null || !error.isEmpty()) {
                throw new IllegalStateException("Fingerprint configuration rejected: " + error);
            }
        } catch (InvocationTargetException e) {
            throw new IllegalStateException("Fingerprint provider call failed", e.getCause());
        } catch (ReflectiveOperationException e) {
            throw new IllegalStateException("Install the xpChromium unified-config WebView", e);
        }
    }
}
