import SwiftUI

struct InsightDetailView: View {
    var title: String
    var bodyText: String
    @State private var showEvidence = false

    var body: some View {
        ScrollView {
            DSConstrainedContent {
                VStack(alignment: .leading, spacing: DSSpacing.l) {
                    Text(title).font(.dsTitle)
                    Text(bodyText).font(.dsBody)
                    DSCard(title: "Evidence", actionTitle: showEvidence ? "Hide" : "Show", action: {
                        withAnimation(DS.Animation.spring) { showEvidence.toggle() }
                    }) {
                        if showEvidence {
                            Text("Weekly scores and transaction changes are used to summarize this pattern.")
                                .font(.dsCaption)
                                .foregroundStyle(DS.Color.textSecondary)
                                .transition(.opacity.combined(with: .move(edge: .top)))
                        }
                    }
                }
                .padding(DSSpacing.l)
            }
        }
        .background(DS.Color.background)
    }
}
