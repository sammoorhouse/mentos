import SwiftUI

/// Legacy shim kept to avoid breaking references while the app transitions to timeline-first navigation.
struct MainTabView: View {
    var body: some View {
        NavigationStack {
            TimelineView()
        }
    }
}
