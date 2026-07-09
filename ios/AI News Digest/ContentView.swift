import SwiftUI

struct NewsItem: Identifiable, Codable {
    let id = UUID()
    let title: String
    let link: String
    let source: String
    let category: String
    let ai_summary: String
    let importance: Int

    enum CodingKeys: String, CodingKey {
        case title, link, source, category, ai_summary, importance
    }
}

struct DigestResponse: Codable {
    let date: String
    let items: [NewsItem]
}

struct ContentView: View {
    @State private var items: [NewsItem] = []
    @State private var selectedCategory = "商业"

    var filtered: [NewsItem] {
        items.filter { $0.category == selectedCategory }
    }

    var body: some View {
        NavigationStack {
            VStack {
                Picker("分类", selection: $selectedCategory) {
                    Text("商业").tag("商业")
                    Text("科技").tag("科技")
                }
                .pickerStyle(.segmented)
                .padding(.horizontal)

                List(filtered) { item in
                    NavigationLink(destination: DetailView(item: item)) {
                        VStack(alignment: .leading, spacing: 8) {
                            Text(item.title).font(.headline)
                            Text(item.ai_summary).font(.subheadline)
                            Text(item.source).font(.caption)
                        }
                    }
                }
            }
            .navigationTitle("今日摘要")
            .toolbar {
                NavigationLink("历史") {
                    HistoryView()
                }
            }
            .task {
                await fetchToday()
            }
        }
    }

    func fetchToday() async {
        guard let url = URL(string: "http://127.0.0.1:7800/digest/today") else { return }
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            let decoded = try JSONDecoder().decode(DigestResponse.self, from: data)
            await MainActor.run {
                items = decoded.items
            }
        } catch {
            print("fetch failed: \(error)")
        }
    }
}

struct DetailView: View {
    let item: NewsItem

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(item.title).font(.title3).bold()
            Text("分类：\(item.category)  重要性：\(item.importance)")
            Text(item.ai_summary)
            Link("查看原文", destination: URL(string: item.link)!)
            Spacer()
        }
        .padding()
        .navigationTitle("详情")
    }
}

struct HistoryView: View {
    var body: some View {
        Text("历史页（可按日期扩展）")
            .navigationTitle("历史")
    }
}

