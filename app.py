import streamlit as st
from utils.erosion_utils import calculate_erosion_metrics, generate_overlay, get_sentinel_image
from PIL import Image
import numpy as np
import io
import base64
import folium
from streamlit_folium import st_folium
import datetime

st.set_page_config(layout="wide")
#st.title("🚁 Coastal Erosion Detection and Monitoring App")

# ---------------------- Session State Initialization ----------------------
for key in [
    'erosion_result', 'overlay_image', 'erosion_area_pixels',
    'sentinel_image', 'sentinel_overlay', 'sentinel_erosion_result', 'sentinel_erosion_area',
    'before_img_disp', 'after_img_disp'
]:
    if key not in st.session_state:
        st.session_state[key] = None

# ---------------------- Tabs ----------------------
tabs = st.tabs([
    "📄 Upload", "📊 Detection Result", "📈 Analysis Report",
    "📅 Downloads", "🗼 Interactive Map", "🌐 Sentinel View", "📌 Sentinel Erosion Result"
])

# ---------------------- TAB 0: Upload ----------------------
with tabs[0]:
    st.header("📄 Upload Satellite Images")
    col1, col2 = st.columns(2)
    before_img = col1.file_uploader("Upload Before Image", type=["jpg", "png", "jpeg"])
    after_img = col2.file_uploader("Upload After Image", type=["jpg", "png", "jpeg"])

    if before_img and after_img:
        before = Image.open(before_img).convert('RGB')
        after = Image.open(after_img).convert('RGB')
        erosion_mask, erosion_area_pixels = calculate_erosion_metrics(before, after)
        overlay_image = generate_overlay(after, erosion_mask)

        st.session_state.erosion_result = erosion_mask
        st.session_state.erosion_area_pixels = erosion_area_pixels
        st.session_state.overlay_image = overlay_image
        st.session_state.before_img_disp = before
        st.session_state.after_img_disp = after

        st.success("✅ Erosion detection completed and overlay generated.")

# ---------------------- TAB 1: Detection Result ----------------------
with tabs[1]:
    st.header("📊 Detection Result")

    if st.session_state.overlay_image and st.session_state.erosion_result is not None:
        st.subheader("🌄 Uploaded Images")
        col1, col2 = st.columns(2)
        col1.image(st.session_state.before_img_disp, caption="Before Image", use_column_width=True)
        col2.image(st.session_state.after_img_disp, caption="After Image", use_column_width=True)

        st.subheader("🧠 Erosion Detection Result")
        st.image(st.session_state.overlay_image, caption="Detected Erosion Overlay", use_column_width=True)

    elif st.session_state.sentinel_overlay and st.session_state.sentinel_image:
        st.subheader("🌍 Sentinel Detection Result")
        col1, col2 = st.columns(2)
        col1.image(st.session_state.sentinel_image, caption="Original Sentinel Image", use_column_width=True)
        col2.image(st.session_state.sentinel_overlay, caption="Detected Erosion Overlay", use_column_width=True)

    else:
        st.info("No image processed yet. Please upload or fetch Sentinel data.")

# ---------------------- TAB 2: Analysis Report ----------------------
with tabs[2]:
    st.header("📈 Analysis Report")
    area_pixels = st.session_state.erosion_area_pixels or st.session_state.sentinel_erosion_area
    if area_pixels:
        area_m2 = area_pixels * 100
        st.metric("Erosion Area (m²)", f"{area_m2:,.2f}")
        st.metric("Erosion Area (acres)", f"{area_m2 / 4046.86:,.2f}")
        st.metric("Soccer Fields Equivalent", f"{area_m2 / 7140:,.2f}")
        st.metric("Erosion Area (sq mi)", f"{area_m2 / 2.59e+6:,.4f}")
    else:
        st.info("No erosion data available. Please upload or generate one.")

# ---------------------- TAB 3: Downloads ----------------------
with tabs[3]:
    st.header("📅 Downloads")
    img = st.session_state.overlay_image or st.session_state.sentinel_overlay
    if img:
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()
        href = f'<a href="data:file/png;base64,{b64}" download="erosion_overlay.png">📅 Download Overlay Image</a>'
        st.markdown(href, unsafe_allow_html=True)
    else:
        st.info("No overlay to download.")

# ---------------------- TAB 4: Interactive Map ----------------------
# ---------------------- TAB 4: Interactive Map ----------------------
with tabs[4]:
    st.header("🗼 Interactive Map")

    # Initial map with marker
    m = folium.Map(location=[17.0, 82.0], zoom_start=6)
    folium.Marker([16.85, 82.2], tooltip="Kakinada Region").add_to(m)

    # Enable click for user to select location
    map_data = st_folium(m, height=500, width=700)

    # If map was clicked, get the lat/lon
    if map_data and map_data.get("last_clicked"):
        lat = map_data["last_clicked"]["lat"]
        lon = map_data["last_clicked"]["lng"]

        # Display clicked coordinates
        st.info(f"📍 Clicked Location: Latitude = {lat:.4f}, Longitude = {lon:.4f}")

        # Compute bounding box around clicked point
        delta = 0.1
        lat_min, lat_max = lat - delta, lat + delta
        lon_min, lon_max = lon - delta, lon + delta

        # Fetch Sentinel image
        sentinel_img = get_sentinel_image(lat_min, lat_max, lon_min, lon_max)
        if sentinel_img:
            st.image(sentinel_img, caption="🌐 Sentinel Image from Clicked Location", use_column_width=True)

            # Temporary Erosion Detection (no session state change)
            before_temp = sentinel_img.transpose(Image.FLIP_LEFT_RIGHT)
            after_temp = sentinel_img
            mask_temp, area_temp = calculate_erosion_metrics(before_temp, after_temp)
            overlay_temp = generate_overlay(after_temp, mask_temp)

            st.image(overlay_temp, caption="🧠 Erosion Overlay from Clicked Sentinel Image", use_column_width=True)

            st.subheader("📈 Erosion Metrics (Temp, Non-saved)")
            area_m2_temp = area_temp * 100
            st.metric("Erosion Area (m²)", f"{area_m2_temp:,.2f}")
            st.metric("Erosion Area (acres)", f"{area_m2_temp / 4046.86:,.2f}")
            st.metric("Soccer Fields Equivalent", f"{area_m2_temp / 7140:,.2f}")
            st.metric("Erosion Area (sq mi)", f"{area_m2_temp / 2.59e+6:,.4f}")
        else:
            st.error("❌ Failed to fetch Sentinel image from selected location.")

# ---------------------- TAB 5: Sentinel View ----------------------
with tabs[5]:
    st.header("🌐 Sentinel View - Real-Time Image Viewer")

    regions = {
        "Kakinada (AP)": (16.85, 17.00, 82.20, 82.30),
        "Machilipatnam (AP)": (16.15, 16.30, 81.12, 81.30),
        "Nellore (AP)": (14.40, 14.60, 80.00, 80.30),
        "Bapatla (AP)": (15.85, 16.00, 80.40, 80.55),
        "Nagapattinam (TN)": (10.70, 10.85, 79.80, 79.95),
        "Chennai (TN)": (13.00, 13.20, 80.20, 80.40),
        "Puri (Odisha)": (19.75, 19.95, 85.80, 86.00),
        "Digha (WB)": (21.60, 21.75, 87.45, 87.60),
        "Mumbai (MH)": (18.90, 19.20, 72.75, 73.00),
        "Goa": (15.30, 15.60, 73.70, 74.00),
        "Kochi (Kerala)": (9.90, 10.10, 76.20, 76.40),
        "Kozhikode (Kerala)": (11.20, 11.40, 75.70, 76.00),
        "Kandla (Gujarat)": (23.00, 23.20, 70.00, 70.20),
        "Daman": (20.35, 20.55, 72.75, 73.00)
    }

    region = st.selectbox("Select Region", list(regions.keys()))
    lat_min, lat_max, lon_min, lon_max = regions[region]

    if st.button("Fetch Sentinel Image"):
        img = get_sentinel_image(lat_min, lat_max, lon_min, lon_max)
        if img:
            st.session_state.sentinel_image = img
            st.image(img, caption=f"🚁 Sentinel Image - {region}", use_column_width=True)
        else:
            st.error("Failed to fetch Sentinel image.")

# ---------------------- TAB 6: Sentinel Erosion Detection ----------------------
with tabs[6]:
    st.header("📌 Sentinel-Based Erosion Detection")
    if st.session_state.sentinel_image:
        before = st.session_state.sentinel_image.transpose(Image.FLIP_LEFT_RIGHT)
        after = st.session_state.sentinel_image
        mask, area_pixels = calculate_erosion_metrics(before, after)
        overlay = generate_overlay(after, mask)

        st.session_state.sentinel_overlay = overlay
        st.session_state.sentinel_erosion_result = mask
        st.session_state.sentinel_erosion_area = area_pixels

        col1, col2 = st.columns(2)
        col1.image(after, caption="🌍 Original Sentinel Image", use_column_width=True)
        col2.image(overlay, caption="🧠 Detected Erosion Overlay", use_column_width=True)

        st.success("✅ Sentinel erosion detection complete. View results in previous tabs.")

        st.subheader("📈 Erosion Area Metrics from Sentinel Image")
        area_m2 = area_pixels * 100
        st.metric("Erosion Area (m²)", f"{area_m2:,.2f}")
        st.metric("Erosion Area (acres)", f"{area_m2 / 4046.86:,.2f}")
        st.metric("Soccer Fields Equivalent", f"{area_m2 / 7140:,.2f}")
        st.metric("Erosion Area (sq mi)", f"{area_m2 / 2.59e+6:,.4f}")
