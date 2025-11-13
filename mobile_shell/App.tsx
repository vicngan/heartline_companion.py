import { StatusBar } from "expo-status-bar";
import Constants from "expo-constants";
import React from "react";
import { Platform, SafeAreaView, StyleSheet, Text, View } from "react-native";
import WebView from "react-native-webview";

const HEARTLINE_URL =
  (Constants?.expoConfig?.extra?.heartlineUrl as string) ?? "http://localhost:8501";

export default function App() {
  const isEmulator = HEARTLINE_URL.includes("localhost") && Platform.OS !== "web";

  return (
    <SafeAreaView style={styles.container}>
      {isEmulator && (
        <View style={styles.banner}>
          <Text style={styles.bannerText}>
            Update `extra.heartlineUrl` in app.json to your deployed Streamlit URL before shipping.
          </Text>
        </View>
      )}
      <WebView
        source={{ uri: HEARTLINE_URL }}
        style={styles.webView}
        startInLoadingState
        allowsBackForwardNavigationGestures
        incognito={false}
      />
      <StatusBar style="dark" />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#fbeff4",
  },
  webView: {
    flex: 1,
  },
  banner: {
    padding: 8,
    backgroundColor: "#f9ddea",
  },
  bannerText: {
    textAlign: "center",
    color: "#7a3c58",
    fontSize: 12,
  },
});
