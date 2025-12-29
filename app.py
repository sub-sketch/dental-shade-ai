import streamlit as st
import numpy as np
from PIL import Image, ImageDraw
from streamlit_image_coordinates import streamlit_image_coordinates

# --- 전문 데이터베이스 (쉐이드별 베이스 파우더 매칭 로직 포함) ---
DATA_SHEET = {
    "Noritake (EX-3/CZR)": {
        "Build-up": {
            "Base_Suffix": "B (Body) + Opacious Body",
            "Cervical": "Body + CV1/CV2 (20%) + External Stain A+",
            "Body": "Body (Main Shade) + Internal Stain (A-shade)",
            "Incisal": "E2 + LT1 (1:1) + Opal Effect"
        },
        "Coloring": {
            "Cervical": "Chroma Liquid (A3/A4) 2회 도포 / Margin: Orange Effect",
            "Body": "Main Shade Liquid 1회 도포 (Brush Stroke)",
            "Incisal": "Incisal Gray + Blue Liquid (Top 2mm) / Shadow 효과"
        }
    },
    "VITA (VM9/VM13)": {
        "Build-up": { 
            "Base_Suffix": "Base Dentine", 
            "Cervical": "Base Dentine + NP", 
            "Body": "Base Dentine", 
            "Incisal": "EN + EE" 
        },
        "Coloring": { "Cervical": "Cervical Liquid C1/C2", "Body": "Base Fluid (Main)", "Incisal": "Incisal Fluid (Blue)" }
    },
    "Ivoclar (IPS e.max Ceram)": {
        "Build-up": { 
            "Base_Suffix": "Dentin", 
            "Cervical": "Dentin + Deep Dentin / Stain: Sunset", 
            "Body": "Dentin (Main)", 
            "Incisal": "TI1 + OE1" 
        },
        "Coloring": { "Cervical": "Dentin Liquid + Essence Copper", "Body": "Dentin Liquid (Main)", "Incisal": "Incisal Blue + Clear" }
    }
}

st.set_page_config(page_title="Dental AI Calibration Master", layout="wide")
st.title("🦷 가이드 기준 정밀 조색 및 설계 시스템")

# --- 세션 상태 초기화 ---
if 'ref_point' not in st.session_state: st.session_state.ref_point = None
if 'ref_shade' not in st.session_state: st.session_state.ref_shade = ""
if 'target_points' not in st.session_state: st.session_state.target_points = []

# --- 사이드바 ---
st.sidebar.header("🛠 시스템 설정")
brand = st.sidebar.selectbox("브랜드 선택", list(DATA_SHEET.keys()))
method = st.sidebar.radio("작업 방식", ["Coloring (지르코니아)", "Build-up (도재)"])
method_key = "Coloring" if "Coloring" in method else "Build-up"

if st.sidebar.button("데이터 초기화"):
    st.session_state.ref_point = None
    st.session_state.ref_shade = ""
    st.session_state.target_points = []
    st.rerun()

uploaded_file = st.sidebar.file_uploader("사진 업로드", type=["jpg", "png", "jpeg"])

if uploaded_file:
    raw_img = Image.open(uploaded_file).convert("RGB")
    img_array = np.array(raw_img)
    h, w, _ = img_array.shape

    col_left, col_right = st.columns([1.5, 1])

    with col_left:
        display_img = raw_img.copy()
        draw = ImageDraw.Draw(display_img)
        
        # 1. 가이드(기준점) 표시
        if st.session_state.ref_point:
            rx, ry = st.session_state.ref_point["x"], st.session_state.ref_point["y"]
            draw.rectangle([rx-15, ry-15, rx+15, ry+15], outline="cyan", width=5)
            if st.session_state.ref_shade:
                draw.text((rx-10, ry-35), f"REF: {st.session_state.ref_shade}", fill="cyan")

        # 2. 타겟 치아 마킹 표시
        for i, pt in enumerate(st.session_state.target_points):
            nx, ny = pt["x"], pt["y"]
            draw.ellipse([nx-15, ny-15, nx+15, ny+15], outline="red", width=5)
            draw.text((nx-5, ny-35), str(i+1), fill="red")

        st.subheader("📍 1. 가이드 탭 클릭 -> 2. 치아 부위 클릭")
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
        st.subheader("📝 분석 및 설계 가이드")
        
        if st.session_state.ref_point:
            # 쉐이드 입력창 (KeyError 방지를 위해 기본값 빈칸 설정)
            st.session_state.ref_shade = st.text_input("📍 클릭한 가이드 탭의 쉐이드를 입력하세요 (예: A2, A3)", st.session_state.ref_shade).upper()
            
            if st.session_state.ref_shade:
                main_shade = st.session_state.ref_shade
                
                if method_key == "Coloring":
                    st.markdown(f"### 🎨 [{main_shade}] 지르코니아 컬러링 설계도")
                else:
                    st.markdown(f"### 🏗️ [{main_shade}] 도재 빌드업 레시피")
                    # 수정된 참조 방식: Base_Suffix를 사용하여 KeyError 해결
                    base_info = DATA_SHEET[brand]["Build-up"]["Base_Suffix"]
                    st.success(f"💎 베이스 파우더: {main_shade} {base_info}")

                for i, pt in enumerate(st.session_state.target_points):
                    y_ratio = pt["y"] / h
                    zone = "Cervical" if y_ratio < 0.35 else ("Body" if y_ratio < 0.7 else "Incisal")
                    guide = DATA_SHEET[brand][method_key][zone]
                    
                    with st.expander(f"🔴 지점 {i+1} 상세 분석 ({zone})", expanded=True):
                        st.write(f"**지침:** {guide}")
            else:
                st.warning("쉐이드 이름을 입력해 주세요 (예: A2)")
        else:
            st.warning("먼저 사진 속 '쉐이드 가이드 탭'의 중앙을 클릭해 주세요.")