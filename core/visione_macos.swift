import Foundation
import Vision

struct JarvisVisionClassification: Codable {
    let label: String
    let confidence: Float
}

func fail(_ message: String) -> Never {
    FileHandle.standardError.write((message + "\n").data(using: .utf8)!)
    exit(1)
}

guard CommandLine.arguments.count >= 2 else {
    fail("Uso: swift visione_macos.swift /percorso/immagine")
}

let imageURL = URL(fileURLWithPath: CommandLine.arguments[1])
let request = VNClassifyImageRequest()
request.maximumObservations = 8

do {
    let handler = VNImageRequestHandler(url: imageURL, options: [:])
    try handler.perform([request])
    let classifications = (request.results ?? []).map {
        JarvisVisionClassification(label: $0.identifier, confidence: $0.confidence)
    }
    let data = try JSONEncoder().encode(classifications)
    guard let output = String(data: data, encoding: .utf8) else {
        fail("Impossibile codificare il risultato di Apple Vision.")
    }
    print(output)
} catch {
    fail("Errore Vision: \(error.localizedDescription)")
}
