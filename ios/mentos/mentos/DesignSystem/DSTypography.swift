import SwiftUI

extension Font {
    static let dsTitle = Font.custom("SF Pro", size: 28, relativeTo: .title2).weight(.semibold)
    static let dsHeadline = Font.custom("SF Pro", size: 20, relativeTo: .title3).weight(.semibold)
    static let dsBody = Font.custom("SF Pro", size: 16, relativeTo: .body)
    static let dsCaption = Font.custom("SF Pro", size: 13, relativeTo: .caption).weight(.medium)
    static let dsMonospace = Font.system(.body, design: .monospaced)
}
