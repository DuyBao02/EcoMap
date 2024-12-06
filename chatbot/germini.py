# gemini.py
import pandas as pd
import numpy as np
import faiss, os
from sentence_transformers import SentenceTransformer
import google.generativeai as genai

# Định nghĩa lớp RAG
class RAG:
    def __init__(   self, excel_file: str, 
                    sheet_name: str, 
                    llmApiKey: str, 
                    llmName: str = 'gemini-1.5-pro',
                    embedding_file: str = "chatbot/embeddings.npy"):
        
        # Đọc dữ liệu từ file Excel
        df = pd.read_excel(excel_file, sheet_name=sheet_name)
        self.id = df['id'].tolist()
        self.ten_don_vi = df['ten_don_vi'].tolist()
        self.them_dac_trung = df['them_dac_trung'].tolist()
        self.mo_ta = df['mo_ta'].tolist()
        self.dien_tich = df['dien_tich'].tolist()
        self.mat_do_dan_so = df['mat_do_dan_so'].tolist()
        self.dia_diem_du_lich = df['dia_diem_du_lich'].tolist()
        self.hinh_anh = df['hinh_anh'].tolist()
        self.link = df['link'].tolist()

        self.embedding_model = SentenceTransformer("keepitreal/vietnamese-sbert")
        self.embedding_file = embedding_file

        if os.path.exists(self.embedding_file):
            print(f"Tải embeddings từ {self.embedding_file}")
            self.embeddings = np.load(self.embedding_file)
        else:
            print("Tạo embeddings và lưu vào file.")
            self.embeddings = np.vstack(self.embedding_model.encode(self.them_dac_trung))
            np.save(self.embedding_file, self.embeddings)

        # Cấu hình LLM
        genai.configure(api_key=llmApiKey)
        self.llm = genai.GenerativeModel(llmName)

    def get_embedding(self, text):
        return self.embedding_model.encode([text])[0]

    def vector_search(self, user_query: str, limit=6):
        query_embedding = self.get_embedding(user_query)
        if not query_embedding.size:
            return []

        # Sử dụng FAISS để tìm kiếm vector gần nhất
        index = faiss.IndexFlatL2(self.embeddings.shape[1])
        index.add(self.embeddings)
        D, I = index.search(np.array([query_embedding]), limit)

        results = []
        for dist, idx in zip(D[0], I[0]):
            dia_diem_du_lich = str(self.dia_diem_du_lich[idx]).split("; ")
            hinh_anh = str(self.hinh_anh[idx]).split("; ")
            link = str(self.link[idx]).split("; ")

            # Đảm bảo rằng số lượng địa điểm và hình ảnh và url là tương đương
            if len(dia_diem_du_lich) == len(hinh_anh) == len(link):
                dia_diem_hinh_anh_link = [{"dia_diem": dia_diem, "hinh_anh": hinh_anh[i], "link": link[i]} 
                                          for i, dia_diem in enumerate(dia_diem_du_lich)]
            else: 
                dia_diem_hinh_anh_link = []

            result = {
                "id": self.id[idx],
                "ten_don_vi": self.ten_don_vi[idx],
                "mo_ta": self.mo_ta[idx],
                "dien_tich": self.dien_tich[idx],
                "mat_do_dan_so": self.mat_do_dan_so[idx],
                "dia_diem_hinh_anh_link": dia_diem_hinh_anh_link,
                "distance": dist
            }
            results.append(result)

        # Sắp xếp kết quả theo khoảng cách từ gần nhất đến xa nhất
        results = sorted(results, key=lambda x: x['distance'])

        print(50*('-'))
        print(f"Câu hỏi đầu vào: {user_query}")
        print(50*('-'))
        print("Vector gần nhất sau khi tính toán:")
        for res in results[:limit]:
            print({
                "id": res["id"],
                "ten_don_vi": res["ten_don_vi"],
                "distance": res["distance"]
            })

        return results

    def enhance_prompt(self, query):
        get_knowledge = self.vector_search(query, 6)
        if not get_knowledge:
            return "Không tìm thấy thông tin liên quan."

        enhanced_prompt = ""
        for i, result in enumerate(get_knowledge, 1):
            enhanced_prompt += f"\n{i}) Tên đơn vị: {result.get('ten_don_vi', 'N/A')}"
            enhanced_prompt += f", Mô tả: {result.get('mo_ta', 'N/A')}"
            enhanced_prompt += f", Diện tích: {result.get('dien_tich', 'N/A')} km²"
            enhanced_prompt += f", Mật độ dân số: {result.get('mat_do_dan_so', 'N/A')} người/km²"
            enhanced_prompt += ", Các địa điểm du lịch: " + ", ".join(
                [f"{item['dia_diem']} (Hình: {item['hinh_anh']}) (Đường dẫn: {item['link']})" for item in result.get('dia_diem_hinh_anh_link', [])]
            )

        return enhanced_prompt

    def generate_content(self, prompt):
        return self.llm.generate_content(prompt)
