import SwiftUI

struct DSSeparator: View {
    var body: some View {
        Rectangle()
            .fill(DS.Color.separator.opacity(0.35))
            .frame(height: 0.5)
    }
}
