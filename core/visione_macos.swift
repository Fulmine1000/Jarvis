import Foundation
import Vision

struct JarvisVisionDetection: Codable {
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
let handler = VNImageRequestHandler(url: imageURL, options: [:])
var detections: [JarvisVisionDetection] = []

let faceRequest = VNDetectFaceRectanglesRequest()
let rectangleRequest = VNDetectRectanglesRequest()
rectangleRequest.maximumObservations = 8
let barcodeRequest = VNDetectBarcodesRequest()

do {
    try handler.perform([faceRequest, rectangleRequest, barcodeRequest])

    let faces = (faceRequest.results ?? []).compactMap { $0 as? VNFaceObservation }
    for observation in faces {
        detections.append(
            JarvisVisionDetection(
                label: "volto rilevato",
                confidence: observation.confidence
            )
        )
    }

    let rectangles = (rectangleRequest.results ?? []).compactMap { $0 as? VNRectangleObservation }
    for observation in rectangles {
        detections.append(
            JarvisVisionDetection(
                label: "forma rettangolare",
                confidence: observation.confidence
            )
        )
    }

    let barcodes = (barcodeRequest.results ?? []).compactMap { $0 as? VNBarcodeObservation }
    for observation in barcodes {
        let label = observation.payloadStringValue.map {
            "codice a barre/QR: " + $0
        } ?? "codice a barre/QR"

        detections.append(
            JarvisVisionDetection(
                label: label,
                confidence: observation.confidence
            )
        )
    }

    if detections.isEmpty {
        detections.append(JarvisVisionDetection(label: "nessun volto, rettangolo o codice riconosciuto", confidence: 1.0))
    }

    let data = try JSONEncoder().encode(Array(detections.prefix(8)))
    guard let output = String(data: data, encoding: .utf8) else {
        fail("Impossibile codificare il risultato di Apple Vision.")
    }
    print(output)
} catch {
    fail("Errore Vision: \(error.localizedDescription)")
}
