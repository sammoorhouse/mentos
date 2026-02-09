import SwiftUI

struct InsightRowModel: Identifiable {
    let id = UUID()
    let title: String
    let preview: String
    let group: String
}

struct InsightsListView: View {
    let rows = [
        InsightRowModel(title: "Coffee spending dipped", preview: "You spent 18% less than last week.", group: "Today"),
        InsightRowModel(title: "Transport spike", preview: "A train pass renewal increased travel spend.", group: "Yesterday"),
        InsightRowModel(title: "Savings streak", preview: "Three weekly transfers in a row.", group: "Earlier")
    ]

    var body: some View {
        ScrollView {
            DSConstrainedContent {
                if rows.isEmpty {
                    DSEmptyState(icon: "tray", title: "No insights yet", message: "Connect Monzo to start receiving weekly insights.")
                        .padding(DSSpacing.l)
                } else {
                    LazyVStack(alignment: .leading, spacing: DSSpacing.l) {
                        ForEach(grouped.keys.sorted(by: sectionSort), id: \.self) { key in
                            VStack(alignment: .leading, spacing: .zero) {
                                DSSectionHeader(title: key)
                                ForEach(grouped[key] ?? []) { row in
                                    NavigationLink {
                                        InsightDetailView(title: row.title, bodyText: row.preview + "\n\nEvidence sample data.")
                                    } label: {
                                        DSRow(icon: "sparkles", title: row.title, subtitle: row.preview)
                                    }
                                    .buttonStyle(.plain)
                                }
                            }
                        }
                    }
                    .padding(DSSpacing.l)
                }
            }
        }
        .background(DS.Color.background)
        .navigationTitle("Insights")
    }

    private var grouped: [String: [InsightRowModel]] { Dictionary(grouping: rows, by: \.group) }
    private func sectionSort(_ a: String, _ b: String) -> Bool {
        let rank = ["Today": 0, "Yesterday": 1, "Earlier": 2]
        return rank[a, default: 10] < rank[b, default: 10]
    }
}
