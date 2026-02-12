import SwiftUI

struct DSWeeklyScore: Identifiable {
    let weekStart: Date
    let score: Int
    var id: Date { weekStart }
}

struct DSProgressDots: View {
    var weeks: [DSWeeklyScore]

    var body: some View {
        HStack(spacing: DSSpacing.m) {
            ForEach(weeks.suffix(6)) { week in
                VStack(spacing: DSSpacing.xs) {
                    Circle()
                        .stroke(Color.accentColor.opacity(0.35), lineWidth: week.score == 0 ? 1 : 0)
                        .background(Circle().fill(fill(for: week.score)))
                        .frame(width: 12, height: 12)
                    Text(week.weekStart, format: .dateTime.weekday(.narrow))
                        .font(.caption2)
                        .foregroundStyle(DS.Color.textSecondary)
                }
            }
        }
        .accessibilityElement(children: .combine)
        .accessibilityLabel("Weekly progress")
    }

    private func fill(for score: Int) -> Color {
        switch score {
        case 2: return .accentColor
        case 1: return Color.accentColor.opacity(0.45)
        default: return .clear
        }
    }
}
