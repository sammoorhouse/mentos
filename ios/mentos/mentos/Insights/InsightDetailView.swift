import SwiftUI

struct InsightDetailView: View {
    let insight: Insight

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                Text(insight.headline)
                    .font(.title.bold())
                Text(insight.message)
                    .font(.body)
                if let severity = insight.severity {
                    Text("Severity: \(severity)")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            .padding()
        }
        .navigationTitle("Insight")
        .navigationBarTitleDisplayMode(.inline)
    }
}
