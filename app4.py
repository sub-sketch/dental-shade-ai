import streamlit as st
import numpy as np
from PIL import Image, ImageDraw
from streamlit_image_coordinates import streamlit_image_coordinates

# --- 정밀 데이터베이스 (기본값) ---
DATA_SHEET = {
    "Noritake (EX-3/CZR)": {
        "Build-up": {"Base": "B (Body)", "CV_Type": "CV1/CV2", "Stain": "External Stain A+"},
        "Coloring": {"Main": "Main Liquid", "Effect": "Chroma Liquid"}
    },
    "VITA (VM9/VM13)": {
        "Build-up": {"Base": "Base Dentine", "CV_Type": "Neck Powder (NP)", "Stain": "Stain 03/05"},
        "Coloring": {"Main": "Base Fluid", "Effect": "Cervical Liquid"}
    },
    "Ivoclar (IPS e.max Ceram)": {
        "Build-up": {"Base": "Dentin", "CV_Type": "Deep Dentin", "Stain": "Essence Sunset"},
        "Coloring": {"Main": "Dentin Liquid", "Effect": "Essence Liquid"}
    }
}

def get_color_intensity(img_array, point, window=5):
    """지정한 좌표 주변의 평균 색상값(밝기 기반)을 추출"""
    x, y = int(point['x']), int(point['y'])
    sample = img_array[y-window:y+window, x-window:x+window]
    # 밝기(Luminance) 계산 (0에 가까울수록 진함)
    avg_rgb = np.mean(sample, axis=(0, 1))
    luminance = 0.299*avg_rgb[0] + 0.587*avg_rgb[1] + 0.114*avg_rgb[2]
    return luminance

def resize_image(image, max_width=1000):
    w, h = image.size
    if w > max_width:
        new_h = int(h * (max_width / w))
        return image.resize((max_width, new_h), Image.LANCZOS)
    return image

st.set_page_config(page_title="Dental AI Intelligence", layout="wide")
st.title("🦷 지능형 정밀 조색 및 설계 시스템 (Ver 2.0)")

if 'ref_point' not in st.session_state: st.session_state.ref_point = None
if 'ref_shade' not in st.session_state: st.session_state.ref_shade = ""
if 'target_points' not in st.session_state: st.session_state.target_points = []

# --- 사이드바 ---
brand = st.sidebar.selectbox("브랜드 선택", list(DATA_SHEET.keys()))
method = st.sidebar.radio("작업 방식", ["Coloring (지르코니아)", "Build-up (도재)"])
method_key = "Coloring" if "Coloring" in method else "Build-up"

if st.sidebar.button("데이터 초기화"):
    st.session_state.ref_point = None
    st.session_state.target_points = []
    st.rerun()

uploaded_file = st.sidebar.file_uploader("사진 업로드", type=["jpg", "png", "jpeg"])

if uploaded_file:
    raw_img = Image.open(uploaded_file).convert("RGB")
    raw_img = resize_image(raw_img)
    img_array = np.array(raw_img)
    h, w, _ = img_array.shape

    col_left, col_right = st.columns([1.6, 1])

    with col_left:
        display_img = raw_img.copy()
        draw = ImageDraw.Draw(display_img)
        
        if st.session_state.ref_point:
            rx, ry = st.session_state.ref_point["x"], st.session_state.ref_point["y"]
            draw.rectangle([rx-15, ry-15, rx+15, ry+15], outline="cyan", width=5)
        
        for i, pt in enumerate(st.session_state.target_points):
            nx, ny = pt["x"], pt["y"]
            draw.ellipse([nx-15, ny-15, nx+15, ny+15], outline="red", width=5)
            draw.text((nx-5, ny-35), str(i+1), fill="red")

        value = streamlit_image_coordinates(display_img, key="dental_map")
        if value:
            if st.session_state.ref_point is None:
                st.session_state.ref_point = {"x": value["x"], "y": value["y"]}
                st.rerun()
            else:
                new_pt = {"x": value["x"], "y": value["y"]}
                if not st.session_state.target_points or st.session_state.target_points[-1] != new_pt:
                    st.session_state.target_points.append(new_pt)
                    st.rerun()

    with col_right:
        st.subheader("📋 실시간 정밀 분석 레시피")
        
        if st.session_state.ref_point:
            st.session_state.ref_shade = st.text_input("📍 가이드 탭 쉐이드 입력 (예: A2)", st.session_state.ref_shade).upper()
            
            if st.session_state.ref_shade and st.session_state.target_points:
                # 1. 기준점 밝기 측정
                ref_lum = get_color_intensity(img_array, st.session_state.ref_point)
                
                for i, pt in enumerate(st.session_state.target_points):
                    # 2. 타겟점 밝기 측정 및 비교
                    tar_lum = get_color_intensity(img_array, pt)
                    diff = ref_lum - tar_lum # 양수면 타겟이 더 진함
                    
                    y_ratio = pt["y"] / h
                    zone = "Cervical" if y_ratio < 0.35 else ("Body" if y_ratio < 0.7 else "Incisal")
                    
                    with st.expander(f"🔴 지점 {i+1} 상세 분석 ({zone})", expanded=True):
                        if method_key == "Build-up":
                            base = f"{st.session_state.ref_shade}{DATA_SHEET[brand]['Build-up']['Base']}"
                            cv_p = DATA_SHEET[brand]['Build-up']['CV_Type']
                            stain = DATA_SHEET[brand]['Build-up']['Stain']
                            
                            # 차이에 따른 동적 비율 계산
                            if diff > 30: # 매우 진함
                                ratio, s_int = "40%", "강함"
                            elif diff > 10: # 보통 진함
                                ratio, s_int = "25%", "중간"
                            elif diff > -10: # 기준과 비슷
                                ratio, s_int = "10%", "약함"
                            else: # 기준보다 밝음
                                ratio, s_int = "0% (Body 단독)", "없음"
                            
                            if zone == "Cervical":
                                st.write(f"**추천 배합:** {base} + {cv_p} ({ratio})")
                                st.write(f"**스테인:** {stain} ({s_int})")
                            elif zone == "Body":
                                st.write(f"**추천 배합:** {base} (Main)")
                                st.write(f"**내부 스테인:** {stain} (미량)")
                            else:
                                st.write(f"**추천 배합:** Enamel + Luster (명도 조절용)")

                        else: # Coloring
                            main_l = DATA_SHEET[brand]['Coloring']['Main']
                            eff_l = DATA_SHEET[brand]['Coloring']['Effect']
                            
                            if diff > 30: times = "3회 집중 도포"
                            elif diff > 10: times = "2회 도포"
                            else: times = "1회 도포"
                            
                            st.write(f"**리퀴드 설계:** {eff_l} ({times})")
                            st.caption("※ 신터링 후 채도 강화를 위해 침투 깊이를 조절하세요.")
            else:
                st.warning("가이드 탭 입력 후 치아를 클릭하세요.")