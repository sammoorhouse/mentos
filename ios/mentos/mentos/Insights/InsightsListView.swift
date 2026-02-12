import SwiftUI

struct InsightsListView: View {
    @State private var insights: [Insight] = []
    @State private var isLoading = false

    var body: some View {
        NavigationView {
            List {
                ForEach(insights) { insight in
                    NavigationLink(destination: InsightDetailView(insight: insight)) {
                        VStack(alignment: .leading, spacing: 6) {
                            Text(insight.headline)
                                .font(.headline)
                            Text(insight.message)
                                .font(.caption)
                                .foregroundColor(.secondary)
                                .lineLimit(2)
                        }
                        .padding(.vertical, 4)
                    }
                }
            }
            .navigationTitle("Insights")
            .task { await loadInsights() }
            .refreshable { await loadInsights() }
        }
    }

    private func loadInsights() async {
        guard !isLoading else { return }
        isLoading = true
        do {
            insights = try await APIClient.shared.getInsights()
        } catch {
            insights = []
        }
        isLoading = false
    }
}
