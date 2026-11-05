"use strict";
import { FilesetResolver, HandLandmarker } from "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.22/vision_bundle.mjs";
let landmarker = null;
let busy = false;
let lastTimestamp = 0;
self.onmessage = async (event) => {
  const data = event.data || {};
  if (data.type === "init") {
    try {
      const vision = await FilesetResolver.forVisionTasks("https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.22/wasm");
      landmarker = await HandLandmarker.createFromOptions(vision, {
        baseOptions: {
          modelAssetPath: "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
          delegate: "CPU"
        },
        runningMode: "VIDEO",
        numHands: 2,
        minHandDetectionConfidence: 0.55,
        minHandPresenceConfidence: 0.50,
        minTrackingConfidence: 0.50
      });
      self.postMessage({type:"ready"});
    } catch (error) {
      self.postMessage({type:"error", message:String(error && (error.stack || error.message) || error)});
    }
    return;
  }
  if (data.type !== "frame" || !landmarker || busy || !data.bitmap) {
    if (data.bitmap) { try { data.bitmap.close(); } catch (_) {} }
    return;
  }
  busy = true;
  const bitmap = data.bitmap;
  try {
    const timestamp = Math.max(performance.now(), lastTimestamp + 1);
    lastTimestamp = timestamp;
    const result = landmarker.detectForVideo(bitmap, timestamp);
    const hands = (result.landmarks || []).map(points => points.map(point => ({
      x: Math.max(0, Math.min(1, point.x)),
      y: Math.max(0, Math.min(1, point.y)),
      z: Number.isFinite(point.z) ? point.z : 0
    })));
    self.postMessage({type:"result", hands, handedness:result.handedness || [], points:hands.reduce((n, hand) => n + hand.length, 0)});
  } catch (error) {
    self.postMessage({type:"error", message:String(error && (error.stack || error.message) || error)});
  } finally {
    try { bitmap.close(); } catch (_) {}
    busy = false;
  }
};
self.addEventListener("close", () => { try { if (landmarker) landmarker.close(); } catch (_) {} });
