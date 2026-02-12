import SwiftUI

struct HomeView: View {
    @EnvironmentObject private var session: SessionStore
    @State private var insights: [Insight] = []
    @State private var isLoading = false

    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 20) {
                    statusCard
                    latestInsightCard
                    weeklyProgressCard
                }
                .padding()
            }
            .navigationTitle("Home")
            .task { await loadInsights() }
            .refreshable { await loadInsights() }
        }
    }

    private var statusCard: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Connection status")
                .font(.headline)
            Text(session.monzoStatus?.connected == true ? "Monzo connected" : "Not connected")
                .font(.subheadline)
                .foregroundColor(session.monzoStatus?.connected == true ? .green : .secondary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .background(RoundedRectangle(cornerRadius: 16).fill(Color(.secondarySystemBackground)))
    }

    private var latestInsightCard: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Latest insight")
                .font(.headline)
            if let insight = insights.first {
                Text(insight.headline)
                    .font(.subheadline)
                Text(insight.message)
                    .font(.footnote)
                    .foregroundColor(.secondary)
            } else {
                Text("No insights yet")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .background(RoundedRectangle(cornerRadius: 16).fill(Color(.secondarySystemBackground)))
    }

    private var weeklyProgressCard: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("This week")
                .font(.headline)
            HStack(spacing: 8) {
                ForEach(0..<7, id: \.self) { _ in
                    Circle()
                        .fill(Color.accentColor.opacity(0.2))
                        .frame(width: 12, height: 12)
                }
            }
            Text("Weekly progress placeholder")
                .font(.footnote)
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .background(RoundedRectangle(cornerRadius: 16).fill(Color(.secondarySystemBackground)))
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
