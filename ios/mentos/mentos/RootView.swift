import SwiftUI

struct RootView: View {
    var body: some View {
        TabView {
            Text("Home").tabItem { Label("Home", systemImage: "house") }
            Text("Insights").tabItem { Label("Insights", systemImage: "list.bullet") }
            Text("Goals").tabItem { Label("Goals", systemImage: "target") }
            Text("Breakthroughs").tabItem { Label("Breakthroughs", systemImage: "sparkles") }
            Text("Settings").tabItem { Label("Settings", systemImage: "gear") }
        }
    }
}
