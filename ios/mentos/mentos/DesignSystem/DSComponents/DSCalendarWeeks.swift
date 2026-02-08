import SwiftUI

struct DSCalendarWeeks: View {
    var weeks: [DSWeeklyScore]
    private var calendar = Calendar.current

    var body: some View {
        ScrollView {
            LazyVStack(alignment: .leading, spacing: DSSpacing.m) {
                ForEach(Array(weeks.enumerated()), id: \.element.id) { idx, week in
                    if shouldShowMonthHeader(index: idx) {
                        Text(monthHeader(for: week.weekStart))
                            .font(.dsCaption)
                            .foregroundStyle(DS.Color.textSecondary)
                    }
                    HStack {
                        Text(week.weekStart, format: .dateTime.month(.abbreviated).day())
                            .font(.dsCaption)
                            .foregroundStyle(DS.Color.textSecondary)
                            .frame(width: 70, alignment: .leading)
                        Circle()
                            .fill(dotColor(for: week.score))
                            .frame(width: 10, height: 10)
                        Spacer()
                    }
                }
            }
        }
    }

    private func shouldShowMonthHeader(index: Int) -> Bool {
        guard index > 0 else { return true }
        let current = weeks[index].weekStart
        let previous = weeks[index - 1].weekStart
        return calendar.component(.month, from: current) != calendar.component(.month, from: previous)
    }

    private func monthHeader(for date: Date) -> String {
        date.formatted(.dateTime.month(.wide))
    }

    private func dotColor(for score: Int) -> Color {
        score == 2 ? .accent : (score == 1 ? .accent.opacity(0.45) : DS.Color.separator)
    }
}
