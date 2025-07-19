import requests
import json
from PIL import Image
from io import BytesIO
import streamlit as st
from deep_translator import GoogleTranslator  # 使用兼容库代替 googletrans
import re

# 设置API URL和密钥
API_KEY = 'sk-nYciZMCu6LEopaRB2c332630A312443eAeC569Aa4855B5Bf'

# 页面设置
st.set_page_config(page_title="AI大模型工程师体验", page_icon=":robot_face:", layout="wide")

# 页面背景
page_bg = '''
<style>
body {
    background-color: #1e1e1e;
    color: #fff;
    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    background-image: linear-gradient(to right, #2c3e50, #34495e);
    background-size: cover;
}
h1 {
    text-align: center;
    color: #f39c12;
    font-size: 3rem;
    margin-top: 30px;
}
h2 {
    color: #ecf0f1;
    font-size: 1.5rem;
    text-align: center;
}
.stButton>button {
    background-color: #f39c12;
    color: #fff;
    border-radius: 50px;
    padding: 15px 50px;
    font-size: 1.2rem;
    font-weight: bold;
    border: none;
    cursor: pointer;
    transition: 0.3s ease;
}
.stButton>button:hover {
    background-color: #e67e22;
}
.stTextInput input {
    border-radius: 10px;
    padding: 10px;
    font-size: 1rem;
    border: 1px solid #f39c12;
    background-color: transparent;
    color: #fff;
}
.stTextInput input:focus {
    border-color: #e67e22;
}
</style>
'''
st.markdown(page_bg, unsafe_allow_html=True)

# 页面标题
st.title("AI大模型工程师体验")

# 子页面选项卡
tab1, tab2 = st.tabs(["🎨 魔法画笔：用你的话变出画来！", "🚀 穿越未来：AI职业体验馆"])

### ------------------ 第一部分：文本生成图像 ------------------ ###
with tab1:
    # 用户输入中文 prompt
    prompt_chinese = st.text_input("请输入描述信息 (Prompt)", "一只猫在沙发上睡觉。")

    # 翻译中文为英文
    def translate_to_english(text):
        return GoogleTranslator(source='auto', target='en').translate(text)
    def generate_image(prompt):
        url = "https://api.lightai.io/ideogram/generate"
        payload = json.dumps({
           "image_request": {
              "aspect_ratio": "ASPECT_4_3",
              "magic_prompt_option": "AUTO",
              "model": "V_1_TURBO",
              "prompt": prompt,
              "style_type": "REALISTIC",
              "negative_prompt": "none",
              "resolution": "1024x1024",
              "color_palette": "VIBRANT"
           }
        })

        headers = {
           'accept': 'application/json',
           'Authorization': f'Bearer {API_KEY}',
           'content-type': 'application/json'
        }

        response = requests.post(url, headers=headers, data=payload)

        if response.status_code == 200:
            response_data = response.json()
            image_url = response_data['data'][0]['url']
            image_response = requests.get(image_url)
            img = Image.open(BytesIO(image_response.content))
            return img
        else:
            st.error("请求失败，请检查API密钥或其他参数")
            return None

    if st.button("生成图像", key="generate_text"):
        prompt_english = translate_to_english(prompt_chinese)
        st.write(f"中文描述: {prompt_chinese}")
        st.write(f"翻译后的英文描述: {prompt_english}")
        img = generate_image(prompt_english)
        if img:
            with st.container():
                cols = st.columns([1, 3, 1])
                with cols[1]:
                    st.image(img, caption="生成的图像", use_container_width=True)

### ------------------ 第二部分：上传图像 + 编辑 ------------------ ###
with tab2:
    st.write("上传图片并输入未来设想")
    uploaded_file = st.file_uploader("上传一张图片", type=["png", "jpg", "jpeg"])
    job_cn = st.text_input("请输入你想体验的未来职业", "宇航员")

    image_prompt = f"修改图片为正在从事未来的{job_cn}职业，高清插画，保留部分原图片中人物特征"

    if uploaded_file:
        st.success("图片上传成功！")
    else:
        st.info("请上传一张图片以继续。")

    if st.button("编辑图像", key="edit_image"):
        if not uploaded_file:
            st.error("请先上传图片！")
        elif not image_prompt.strip():
            st.error("请输入未来职业描述！")
        else:
            import base64
            image_bytes = uploaded_file.read()
            image_base64 = base64.b64encode(image_bytes).decode("utf-8")

            # 判断 mime type
            if uploaded_file.type in ["image/png", "image/x-png"]:
                mime_type = "image/png"
            else:
                mime_type = "image/jpeg"

            data_url = f"data:{mime_type};base64,{image_base64}"

            url_chat = "https://api.lightai.io/v1/chat/completions"
            headers = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {API_KEY}',
                'Content-Type': 'application/json'
            }

            payload = json.dumps({
                "model": "sora_image",
                "stream": False,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": image_prompt},
                            {"type": "image_url", "image_url": {"url": data_url}}
                        ]
                    }
                ]
            })

            response = requests.post(url_chat, headers=headers, data=payload)

            if response.status_code == 200:
                content = response.json()['choices'][0]['message'].get('content', '')
                match = re.search(r'https://[\S]+\.(jpg|jpeg|png|gif)', content)
                if match:
                    result_url = match.group(0)
                    result_img_response = requests.get(result_url)
                    result_img = Image.open(BytesIO(result_img_response.content))
                    cols = st.columns([1, 3, 1])
                    with cols[1]:
                        st.image(result_img, caption="未来职业", use_container_width=True)
                else:
                    st.warning("未返回图像链接。")
            else:
                st.error("图像编辑请求失败。")
