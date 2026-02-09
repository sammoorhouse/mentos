import SwiftUI

struct MainTabView: View {
    var body: some View {
        TabView {
            NavigationStack { HomeView() }
                .tabItem { Label("Home", systemImage: "house") }
            NavigationStack { InsightsListView() }
                .tabItem { Label("Insights", systemImage: "tray") }
            NavigationStack { GoalsListView() }
                .tabItem { Label("Goals", systemImage: "target") }
            NavigationStack { BreakthroughsListView() }
                .tabItem { Label("Breakthroughs", systemImage: "sparkles") }
            NavigationStack { SettingsView() }
                .tabItem { Label("Settings", systemImage: "gear") }
        }
    }
}
