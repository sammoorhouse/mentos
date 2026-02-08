import SwiftUI

struct BreakthroughsListView: View {
    var body: some View {
        ScrollView {
            DSConstrainedContent {
                DSEmptyState(icon: "sparkles", title: "No breakthroughs yet", message: "Keep going — major wins will appear here.")
                    .padding(DSSpacing.l)
            }
        }
        .background(DS.Color.background)
        .navigationTitle("Breakthroughs")
    }
}
