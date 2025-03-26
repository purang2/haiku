import streamlit as st
import os
from openai import OpenAI
from google import genai
from google.genai import types
from PIL import Image
import base64
import io

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
def image_to_haiku(image: Image.Image) -> str:
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    img_bytes = buffered.getvalue()

    response = genai_client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[types.Part(inline_data=types.Blob(mime_type="image/jpeg", data=img_bytes)),
                  "Describe this image poetically as a Haiku in Korean(=한국어)"]
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
                else:
                    st.error("이미지 생성 실패.")

    else:  # 이미지 → 하이쿠
        uploaded_img = st.file_uploader("🎑 이미지를 업로드하세요", type=["jpg", "jpeg", "png"])
        if uploaded_img:
            image = Image.open(uploaded_img)
            st.image(image, use_column_width=True)

            if st.button("✒️ 하이쿠 생성"):
                with st.spinner("하이쿠 생성 중..."):
                    haiku = image_to_haiku(image)
                    st.subheader("📜 생성된 하이쿠")
                    st.markdown(f"_{haiku}_")

if __name__ == "__main__":
    main()
