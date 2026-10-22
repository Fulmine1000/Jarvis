"use strict";
let detector = null;
let busy = false;

self.onmessage = async (event) => {
  const data = event.data || {};
  if (data.type === "init") {
    try {
      importScripts(
        "https://cdn.jsdelivr.net/npm/@tensorflow/tfjs-core@4.17.0/dist/tf-core.min.js",
        "https://cdn.jsdelivr.net/npm/@tensorflow/tfjs-converter@4.17.0/dist/tf-converter.min.js",
        "https://cdn.jsdelivr.net/npm/@tensorflow/tfjs-backend-cpu@4.17.0/dist/tf-backend-cpu.min.js",
        "https://cdn.jsdelivr.net/npm/@tensorflow-models/hand-pose-detection@2.0.1/dist/hand-pose-detection.min.js"
      );
      await self.tf.setBackend("cpu");
      await self.tf.ready();
      detector = await self.handPoseDetection.createDetector(
        self.handPoseDetection.SupportedModels.MediaPipeHands,
        {
          runtime: "tfjs",
          modelType: "lite",
          maxHands: 2,
          detectorModelUrl: "/models/detector/model.json",
          landmarkModelUrl: "/models/landmark/model.json"
        }
      );
      self.postMessage({type:"ready"});
    } catch (error) {
      self.postMessage({type:"error", message:String(error && (error.stack || error.message) || error)});
    }
    return;
  }

  if (data.type === "frame" && detector && !busy && data.bitmap) {
    busy = true;
    const bitmap = data.bitmap;
    try {
      const predictions = await detector.estimateHands(bitmap, {flipHorizontal:false});
      const order = ["wrist","thumb_cmc","thumb_mcp","thumb_ip","thumb_tip",
        "index_finger_mcp","index_finger_pip","index_finger_dip","index_finger_tip",
        "middle_finger_mcp","middle_finger_pip","middle_finger_dip","middle_finger_tip",
        "ring_finger_mcp","ring_finger_pip","ring_finger_dip","ring_finger_tip",
        "pinky_finger_mcp","pinky_finger_pip","pinky_finger_dip","pinky_finger_tip"];
      const hands = predictions.map(hand => {
        const points = hand.keypoints || [];
        const byName = Object.fromEntries(points.filter(p => p.name).map(p => [p.name,p]));
        return order.map((name,index) => {
          const p = byName[name] || points[index];
          if (!p || !Number.isFinite(p.x) || !Number.isFinite(p.y)) return {x:0,y:0};
          return {
            x: Math.max(0,Math.min(1,p.x / bitmap.width)),
            y: Math.max(0,Math.min(1,p.y / bitmap.height))
          };
        });
      });
      self.postMessage({type:"result", hands, points: predictions[0] && predictions[0].keypoints ? predictions[0].keypoints.length : 0});
    } catch (error) {
      self.postMessage({type:"error", message:String(error && (error.stack || error.message) || error)});
    } finally {
      try { bitmap.close(); } catch (_) {}
      busy = false;
    }
  } else if (data.bitmap) {
    try { data.bitmap.close(); } catch (_) {}
  }
};
