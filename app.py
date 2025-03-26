import streamlit as st
import os
from openai import OpenAI
from google import genai
from google.genai import types
from PIL import Image
import base64
import io
from datetime import datetime


GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
OPENAI_KEY = st.secrets["OPENAI_API_KEY"]

genai_client = genai.Client(api_key=GEMINI_KEY)
chatgpt_client = OpenAI(api_key=OPENAI_KEY)

def poem_to_imagefx_prompt(poem: str) -> str:
    template = (
        "Convert the following poem into a detailed, vivid, concise English prompt optimized for high-quality AI image generation. "
        "The image should visually interpret the poem's emotion, theme, and setting. "
        "DO NOT INCLUDE any text from the poem in the image. Only describe visually expressive elements, colors, style, and scenes."
        f"\n\nPoem:\n{poem}\n\nPrompt:"
    )
    response = chatgpt_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": template}],
        max_tokens=500,
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

def copy_button(text):
    copy_code = f"""
    <button onclick="navigator.clipboard.writeText(`{text}`).then(()=>alert('✅ 하이쿠가 복사되었습니다!'))"
        style='
            padding: 8px 16px;
            background-color: #D7CCC8;
            color: #5C4033;
            border-radius: 10px;
            border: none;
            cursor: pointer;
            font-family: "Noto Serif KR";
        '>📋 하이쿠 복사</button>
    """
    st.markdown(copy_code, unsafe_allow_html=True)

# 이미지 다운로드 버튼 추가 함수
def download_image_button(image, filename_prefix="haiku_image"):
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_bytes = buffered.getvalue()

    filename = f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

    st.download_button(
        label="📥 이미지 저장",
        data=img_bytes,
        file_name=filename,
        mime="image/png"
    )



def generate_image_with_gemini(prompt: str):
    response = genai_client.models.generate_content(
        model="gemini-2.0-flash-exp-image-generation",
        contents=prompt,
        config=types.GenerateContentConfig(response_modalities=["Image", "Text"])
    )

    if response and response.candidates:
        content_parts = response.candidates[0].content.parts
        if content_parts and content_parts[0].inline_data:
            img_bytes = content_parts[0].inline_data.data
            return Image.open(io.BytesIO(img_bytes))
    return None

# 이미지 → 하이쿠 변환

# 이미지 → 하이쿠 변환
def image_to_haiku(image: Image.Image) -> str:
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    img_bytes = buffered.getvalue()

    prompt = ("제공된 이미지를 바탕으로 동양적 감성이 담긴 한국어 하이쿠를 창작해줘. "
             "반드시 5-7-5 음절의 3행 구조로 하이쿠를 구성해야 하고, 각 행은 명확한 띄어쓰기로 줄바꿈해서 제시해줘. "
             "이미지의 직접적인 묘사보다는 자연과 인간의 감정이 은은하게 어우러진 간결하고 함축적인 표현으로, "
             "하이쿠 특유의 절제된 아름다움과 여운을 느낄 수 있도록 작성해줘. "
             "반드시 한국어로만 작성하고, 다른 설명이나 부가적인 말은 덧붙이지 마.")

    response = genai_client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[
            types.Part(inline_data=types.Blob(mime_type="image/jpeg", data=img_bytes)),
            prompt
        ],
    )
    return response.text.strip()


# CSS 스타일
def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+KR&display=swap');
    html, body, [class*="css"] {
        font-family: 'Noto Serif KR', serif;
        background-color: #FFFCF5;
        color: #3C3C3C;
    }
    h1, h2, h3 {
        color: #5C4033;
    }
    .stButton button {
        background-color: #D7CCC8;
        color: #5C4033;
        border-radius: 20px;
    }
    .stButton button:hover {
        background-color: #A1887F;
        color: white;
    }
    textarea {
        background-color: #FAF5E9 !important;
    }
    </style>
    """, unsafe_allow_html=True)

def main():
    st.set_page_config(layout="wide", page_title="🌸 하이쿠 ↔ 시화 번안기")
    inject_css()
    st.title("🌸 하이쿠 ↔ 시화 번안기")

    mode = st.radio("모드를 선택하세요", ["✒️ 하이쿠 → 🖼️ 시화", "🖼️ 이미지 → ✒️ 하이쿠"], horizontal=True)

    if mode == "✒️ 하이쿠 → 🖼️ 시화":
        poem = st.text_area("✒️ 하이쿠를 입력하세요", height=200, value="고요한 연못\n개구리 뛰어들자\n물소리 일다\n\n— 마츠오 바쇼")
        if st.button("✨ 시화 생성"):
            with st.spinner("프롬프트 생성 중..."):
                optimized_prompt = poem_to_imagefx_prompt(poem)
                st.subheader("🖌️ 생성된 프롬프트")
                st.markdown(f"> {optimized_prompt}")

            with st.spinner("시화 이미지 생성 중..."):
                generated_image = generate_image_with_gemini(optimized_prompt)
                if generated_image:
                    st.subheader("🖼️ 생성된 시화")
                    st.image(generated_image, use_column_width=True)
                
                    # 이미지 저장 버튼 추가
                    download_image_button(generated_image)
                else:
                    st.error("이미지 생성에 실패했습니다.")

    else:  # 이미지 → 하이쿠
        uploaded_img = st.file_uploader("🎑 이미지를 업로드하세요", type=["jpg", "jpeg", "png"])
        if uploaded_img:
            image = Image.open(uploaded_img)
            st.image(image, use_column_width=True)

            with st.spinner("하이쿠 생성 중..."):
                    st.markdown("""
                        <style>
                        @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+KR&display=swap');
                        .haiku-box {
                            font-family: 'Noto Serif KR', serif;
                            font-size: 22px;
                            background-color: #FAF5E9;
                            color: #3C3C3C;
                            padding: 20px;
                            border-radius: 15px;
                            line-height: 1.6;
                            text-align: center;
                            white-space: pre-line;
                        }
                        .stButton button {
                            margin-top: 10px;
                            background-color: #D7CCC8;
                            color: #5C4033;
                            border-radius: 20px;
                        }
                        .stButton button:hover {
                            background-color: #A1887F;
                            color: white;
                        }
                        </style>
                    """, unsafe_allow_html=True)
                    
                   # 하이쿠 결과 표시
                    haiku = image_to_haiku(image)
                    
                    if haiku:
                        st.markdown(
                            f"""
                            <div class='haiku-box' style="
                                font-family: 'Noto Serif KR'; 
                                white-space: pre-line; 
                                font-size: 20px; 
                                padding: 20px; 
                                border-radius: 15px; 
                                background-color: #FAF5E9; 
                                color: #5C4033; 
                                margin-bottom: 10px;
                                text-align: center;">
                                {haiku}
                            </div>
                            """, unsafe_allow_html=True)
                    
                        # 복사 버튼 추가
                        copy_button(haiku)

if __name__ == "__main__":
    main()
