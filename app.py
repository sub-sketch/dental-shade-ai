import streamlit as st
import numpy as np
from PIL import Image, ImageDraw
from streamlit_image_coordinates import streamlit_image_coordinates

# --- 전문 데이터베이스 (브랜드별/방식별) ---
DATA_SHEET = {
    "Noritake (EX-3/CZR)": {
        "Build-up": {
            "Base": "Body (Dentin) + Opacious Body (Base layer)",
            "Cervical": "Body + CV1/CV2 (20%) + External Stain A+",
            "Body": "Body (Main Shade) + Internal Stain (A-shade)",
            "Incisal": "E2 + LT1 (1:1) + Opal Effect"
        },
        "Coloring": {
            "Cervical": "Chroma Liquid (A3/A4) -> 2 Layers / Margin: Orange Effect",
            "Body": "Main Shade Liquid (A-series) -> 1 Layer brush stroke",
            "Incisal": "Incisal Gray + Blue Liquid (Top 2mm) -> Incisal Shadow"
        }
    },
    "VITA (VM9/VM13)": {
        "Build-up": {
            "Base": "Base Dentine (Main Shade)",
            "Cervical": "Base Dentine + Neck Powder (NP)",
            "Body": "Base Dentine + Effect Chroma",
            "Incisal": "Enamel (EN) + Effect Enamel (EE)"
        },
        "Coloring": {
            "Cervical": "Cervical Liquid (C1, C2) -> Deep infiltration",
            "Body": "Base Fluid (Main Shade) -> Surface coating",
            "Incisal": "Incisal Liquid (Violet/Blue) -> 1.5mm dipping/brush"
        }
    },
    "Ivoclar (IPS e.max Ceram)": {
        "Build-up": {
            "Base": "Dentin + Deep Dentin",
            "Cervical": "Dentin + Deep Dentin (1:1) / Essence: Sunset",
            "Body": "Dentin (Main Shade) + Mamelon Light",
            "Incisal": "Transpa Incisal (TI1) + Opal Effect (OE1)"
        },
        "Coloring": {
            "Cervical": "Dentin Liquid (A-series) + Essence Copper (Margin line)",
            "Body": "Dentin Liquid (Main Shade) -> Uniform infiltration",
            "Incisal": "Incisal Liquid (Blue) + Transpa Liquid (Clear)"
        }
    }
}

st.set_page_config(page_title="Dental Tech Master", layout="wide")
st.title("🦷 기공 설계 가이드: 컬러링 설계도 및 빌드업 레시피")

# --- 사이드바 설정 ---
brand = st.sidebar.selectbox("브랜드 선택", list(DATA_SHEET.keys()))
method = st.sidebar.radio("작업 방식", ["Coloring (지르코니아 컬러링)", "Build-up (도재 축성)"])
method_key = "Coloring" if "Coloring" in method else "Build-up"

if 'points' not in st.session_state:
    st.session_state.points = []

if st.sidebar.button("작업 초기화"):
    st.session_state.points = []
    st.rerun()

uploaded_file = st.sidebar.file_uploader("사진 업로드", type=["jpg", "png", "jpeg"])

if uploaded_file:
    raw_img = Image.open(uploaded_file).convert("RGB")
    img_array = np.array(raw_img)
    h, w, _ = img_array.shape
    
    # 1. 자동 쉐이드 판별
    center_color = img_array[h//2-20:h//2+20, w//2-20:w//2+20].mean(axis=(0,1))
    auto_shade = "A1" if center_color[0] > 215 else ("A2" if center_color[0] > 195 else "A3")
    
    col_left, col_right = st.columns([1.5, 1])

    with col_left:
        st.subheader("📍 분석 위치 지정 (클릭)")
        display_img = raw_img.copy()
        draw = ImageDraw.Draw(display_img)
        
        # 이미지에 포인트 표시
        for i, pt in enumerate(st.session_state.points):
            nx, ny = pt["x"], pt["y"]
            r = w // 60
            draw.ellipse([nx-r, ny-r, nx+r, ny+r], outline="red", width=int(w/150))
            draw.text((nx-5, ny-15), str(i+1), fill="red")

        value = streamlit_image_coordinates(display_img, key="dental_map")
        if value:
            new_point = {"x": value["x"], "y": value["y"]}
            if not st.session_state.points or st.session_state.points[-1] != new_point:
                st.session_state.points.append(new_point)
                st.rerun()

    with col_right:
        # --- 방식에 따른 우측 표기 방식 변경 ---
        if method_key == "Coloring":
            st.subheader("🎨 지르코니아 컬러링 설계도")
            st.warning(f"메인 타겟: {auto_shade} 블록/리퀴드 기준")
            
            st.markdown("### [전체 도포 설계]")
            st.code(f"1. 전체: {auto_shade} Main Liquid 1회 도포\n2. 건조: 자연건조 5분 (Sintering 전)")
            
            st.markdown("### [포인트별 침투 가이드]")
            for i, pt in enumerate(st.session_state.points):
                y_ratio = pt["y"] / h
                zone = "Cervical" if y_ratio < 0.35 else ("Body" if y_ratio < 0.7 else "Incisal")
                guide = DATA_SHEET[brand]["Coloring"][zone]
                st.info(f"📍 지점 {i+1} ({zone}):\n\n{guide}")

        else:  # Build-up
            st.subheader("🏗️ 도재 축성(Build-up) 가이드")
            base_powder = DATA_SHEET[brand]["Build-up"]["Base"]
            st.success(f"💎 베이스 파우더: {auto_shade} {base_powder}")
            
            st.markdown("### [세부 레이어링 레시피]")
            for i, pt in enumerate(st.session_state.points):
                y_ratio = pt["y"] / h
                zone = "Cervical" if y_ratio < 0.35 else ("Body" if y_ratio < 0.7 else "Incisal")
                recipe = DATA_SHEET[brand]["Build-up"][zone]
                
                with st.expander(f"🔴 {i+1}번 지점 상세 배합 ({zone})", expanded=True):
                    st.write(f"**배합비:** {recipe}")
                    if zone == "Incisal":
                        st.caption("팁: 절단연은 투명도 재현을 위해 얇게 여러번 나누어 축성하세요.")