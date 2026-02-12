import SwiftUI

struct MainTabView: View {
    var body: some View {
        TabView {
            HomeView()
                .tabItem { Label("Home", systemImage: "house") }
            InsightsListView()
                .tabItem { Label("Insights", systemImage: "sparkles") }
            GoalsListView()
                .tabItem { Label("Goals", systemImage: "target") }
            SettingsView()
                .tabItem { Label("Settings", systemImage: "gear") }
        }
    }
}
