import { createWorker } from "tesseract.js";

export async function recognizeExamImage(file) {
  const worker = await createWorker("eng");
  try {
    const result = await worker.recognize(file);
    return result.data.text || "";
  } finally {
    await worker.terminate();
  }
}
