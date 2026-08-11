import { GoogleGenerativeAI } from "@google/generative-ai";

/**
 * Validate that the provided credential is a proper API Key.
 */
function validateApiKey(apiKey) {
  if (!apiKey) {
    throw new Error("Vui lòng cung cấp Gemini API Key!");
  }

  const cleanKey = apiKey.trim();
  return cleanKey;
}

export async function analyzeScheduleWithGemini(surveyData, apiKey) {
  const cleanKey = validateApiKey(apiKey);

  const prompt = `
Bạn là một chuyên gia y tế và tối ưu hóa hiệu suất học tập cho học sinh/sinh viên.
Hãy phân tích lịch sinh hoạt dưới đây, chỉ ra các nguy cơ sức khỏe tiềm ẩn (suy thận, đột quỵ, cận thị, đau dạ dày...) và đề xuất lịch trình mới khỏe mạnh hơn.
Ở các khung giờ học tập trong lịch trình mới, chia thành các phiên "Focus Mode" 45 phút, chèn xen kẽ 5 phút giải lao với các hoạt động bảo vệ mắt và cơ thể.

Dữ liệu sinh hoạt:
- Giờ đi ngủ: ${surveyData.sleepTime}
- Giờ thức dậy: ${surveyData.wakeTime}
- Lượng nước uống: ${surveyData.waterIntake} lít/ngày
- Số bữa ăn: ${surveyData.meals} bữa/ngày
- Giờ tắm: ${surveyData.showerTime}
- Thời gian nhìn màn hình: ${surveyData.screenTime} giờ/ngày

Yêu cầu trả về BẮT BUỘC định dạng JSON hợp lệ theo cấu trúc:
{
  "score": 45,
  "risks": [
    { "name": "Tên bệnh/Nguy cơ", "probability": "Cao/Trung bình/Thấp", "reason": "Giải thích ngắn gọn" }
  ],
  "advice": "Lời khuyên tổng quan từ chuyên gia",
  "schedule": [
    { "id": 1, "time": "06:00", "activity": "Nội dung hoạt động", "type": "health" }
  ]
}
Chú ý: "type" chỉ gồm: health, work, meal, relax.
  `;

  try {
    const genAI = new GoogleGenerativeAI(cleanKey);
    
    // Primary model: gemini-3.5-flash with JSON mode
    let model;
    let result;

    try {
      model = genAI.getGenerativeModel({
        model: "gemini-3.5-flash",
        generationConfig: {
          responseMimeType: "application/json"
        }
      });
      result = await model.generateContent(prompt);
    } catch (fallbackError) {
      console.warn("Retrying with gemini-2.0-flash fallback...", fallbackError);
      model = genAI.getGenerativeModel({
        model: "gemini-2.0-flash",
        generationConfig: {
          responseMimeType: "application/json"
        }
      });
      result = await model.generateContent(prompt);
    }

    const responseText = result.response.text();
    if (!responseText) {
      throw new Error("Không nhận được phản hồi từ Gemini API");
    }

    // Clean potential markdown formatting
    const cleanedText = responseText.replace(/```json/gi, '').replace(/```/gi, '').trim();
    return JSON.parse(cleanedText);

  } catch (error) {
    // Handle specific Gemini API errors
    if (error.status === 401 || (error.message && error.message.includes("401"))) {
      throw new Error(
        "Lỗi xác thực (401): API Key không hợp lệ hoặc đã hết hạn. " +
        "Vui lòng kiểm tra lại Key trên https://aistudio.google.com/app/apikey"
      );
    }
    if (error.message && error.message.includes("API key not valid")) {
      throw new Error("Gemini API Key không hợp lệ. Vui lòng kiểm tra lại Key trên https://aistudio.google.com/app/apikey");
    }
    console.error("Gemini Request Error:", error.message || error);
    throw new Error(error.message || "Lỗi không xác định khi kết nối tới Gemini API");
  }
}