import SwiftUI

struct DSSectionHeader: View {
    var title: String
    var subtitle: String? = nil

    var body: some View {
        VStack(alignment: .leading, spacing: DSSpacing.xs) {
            Text(title).font(.dsHeadline)
            if let subtitle {
                Text(subtitle).font(.dsCaption).foregroundStyle(DS.Color.textSecondary)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}
