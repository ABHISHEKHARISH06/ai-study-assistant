import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle, FancyArrowPatch
import numpy as np
from io import BytesIO
import pdfplumber
from collections import Counter
import math
import re
import textwrap

def show():
    """Clean & Professional Mind Map Visualizer"""
    st.title("🎨 Clean Mind Map Visualizer")
    st.markdown("### Beautiful, Readable Mind Maps")
    
    st.markdown("---")
    
    st.subheader("📄 Upload Your PDF")
    uploaded_file = st.file_uploader("Upload PDF Document", type=['pdf'])
    
    if uploaded_file:
        with st.spinner("Extracting content..."):
            try:
                # Extract text
                with pdfplumber.open(uploaded_file) as pdf:
                    text = ""
                    for page in pdf.pages[:5]:
                        text += page.extract_text() or ""
                
                st.success(f"✅ Extracted {len(text)} characters")
                
                # Smart keyword extraction
                keywords = extract_keywords(text)
                
                st.subheader("🔑 Key Topics Found")
                cols = st.columns(4)
                for i, (word, freq) in enumerate(keywords[:8]):
                    cols[i % 4].metric(word.upper(), f"{freq}×")
                
                st.markdown("---")
                
                # Configuration
                col1, col2, col3 = st.columns(3)
                with col1:
                    num_topics = st.slider("Topics", 3, 6, 5)
                with col2:
                    content_density = st.select_slider(
                        "Content Detail",
                        options=["Minimal", "Moderate"], # REMOVED "Detailed"
                        value="Moderate"
                    )
                with col3:
                    layout_style = st.selectbox(
                        "Layout",
                        ["Radial", "Tree Structure"] # REPLACED "Circular"
                    )
                
                if st.button("🎨 Generate Clean Mind Map", type="primary", use_container_width=True):
                    with st.spinner("Creating your mind map..."):
                        # Generate content
                        content = generate_content(keywords[:num_topics], text, content_density)
                        
                        # Create visualization
                        fig = create_clean_mindmap(content, layout_style, content_density)
                        
                        st.pyplot(fig)
                        
                        # Download
                        buf = BytesIO()
                        fig.savefig(buf, format='png', dpi=300, bbox_inches='tight',
                                   facecolor='white', edgecolor='none')
                        buf.seek(0)
                        
                        st.download_button(
                            label="📥 Download High Quality PNG",
                            data=buf,
                            file_name="clean_mindmap.png",
                            mime="image/png",
                            use_container_width=True
                        )
                        
            except Exception as e:
                st.error(f"Error: {str(e)}")
    else:
        st.info("👆 Upload a PDF to start")
        
        st.markdown("---")
        if st.button("📊 View Demo", use_container_width=True):
            demo_content = create_demo_content()
            fig = create_clean_mindmap(demo_content, "Tree Structure", "Moderate")
            st.pyplot(fig)


def extract_keywords(text):
    """Extract meaningful keywords"""
    text = text.lower()
    words = text.split()
    
    stop_words = {
        'the', 'and', 'for', 'that', 'this', 'with', 'from', 'have',
        'are', 'was', 'were', 'been', 'will', 'would', 'could', 'into',
        'about', 'which', 'their', 'there', 'these', 'those', 'when',
        'also', 'been', 'than', 'them', 'then', 'more', 'some', 'such'
    }
    
    filtered = []
    for w in words:
        clean = w.strip('.,!?;:()[]{}\'\"')
        if len(clean) > 4 and clean not in stop_words and clean.isalpha():
            filtered.append(clean)
    
    freq = Counter(filtered)
    return freq.most_common(50)


def generate_content(keywords, text, density):
    """Generate structured content for each keyword"""
    content = []
    
    for keyword, freq in keywords:
        context = extract_keyword_context(keyword, text)
        
        if density == "Minimal":
            item = {
                'title': keyword.upper(),
                'points': generate_points(keyword, context, 3)
            }
        else: # Moderate (Default/Fallback)
            item = {
                'title': keyword.upper(),
                'subtitle': f"Key concept with {freq} occurrences",
                'points': generate_points(keyword, context, 4)
            }
        
        content.append(item)
    
    return content


def extract_keyword_context(keyword, text):
    sentences = text.split('.')
    relevant = []
    
    for sent in sentences:
        if keyword.lower() in sent.lower():
            clean = sent.strip()
            if len(clean) > 20:
                relevant.append(clean)
                if len(relevant) >= 2:
                    break
    
    return ' '.join(relevant)


def generate_points(keyword, context, num_points):
    points = []
    templates = [
        f"Core {keyword} methodology",
        f"Improves system performance",
        f"Handles complex scenarios",
        f"Scalable architecture",
        f"Robust implementation",
        f"Efficient processing",
        f"Proven effectiveness"
    ]
    for i in range(num_points):
        points.append(templates[i % len(templates)])
    return points


def create_demo_content():
    return [
        {
            'title': 'MACHINE LEARNING',
            'subtitle': 'Algorithms that learn from data',
            'points': ['Supervised learning methods', 'Unsupervised clustering', 'Deep neural networks', 'Model optimization']
        },
        {
            'title': 'DATA SCIENCE',
            'subtitle': 'Statistical analysis and insights',
            'points': ['Data preprocessing', 'Statistical modeling', 'Visualization techniques', 'Predictive analytics']
        },
        {
            'title': 'ARTIFICIAL INTELLIGENCE',
            'subtitle': 'Intelligent system design',
            'points': ['Natural language processing', 'Computer vision', 'Expert systems', 'Knowledge representation']
        },
        {
            'title': 'BIG DATA',
            'subtitle': 'Large-scale data processing',
            'points': ['Distributed computing', 'Real-time processing', 'Data warehousing', 'Scalable infrastructure']
        },
        {
            'title': 'CLOUD COMPUTING',
            'subtitle': 'Scalable cloud infrastructure',
            'points': ['Infrastructure as a Service', 'Platform as a Service', 'Serverless architecture', 'Cost optimization']
        }
    ]


def create_clean_mindmap(content, layout, density):
    """Create a CLEAN, READABLE mind map"""
    
    # Canvas
    fig, ax = plt.subplots(figsize=(40, 32), facecolor='white')
    ax.set_xlim(-15, 55)
    ax.set_ylim(-15, 45)
    ax.axis('off')
    
    # Colors
    colors = [
        {'bg': '#FFF3E0', 'border': '#FF6F00', 'text': '#E65100'},  # Deep Orange
        {'bg': '#E8F5E9', 'border': '#2E7D32', 'text': '#1B5E20'},  # Green
        {'bg': '#E3F2FD', 'border': '#1565C0', 'text': '#0D47A1'},  # Blue
        {'bg': '#F3E5F5', 'border': '#7B1FA2', 'text': '#4A148C'},  # Purple
        {'bg': '#FCE4EC', 'border': '#C2185B', 'text': '#880E4F'},  # Pink
        {'bg': '#FFF9C4', 'border': '#F57F17', 'text': '#F57F17'},  # Yellow
    ]
    
    # CENTER CIRCLE
    cx, cy = 20, 15
    center_r = 5.5
    
    # Center glow
    ax.add_patch(Circle((cx, cy), center_r + 0.8,
                        facecolor='#37474F', alpha=0.1, zorder=1))
    # Main center
    ax.add_patch(Circle((cx, cy), center_r,
                        facecolor='#263238',
                        edgecolor='#000000',
                        linewidth=4,
                        zorder=5))
    # Center text
    ax.text(cx, cy + 1.5, "MIND MAP",
            ha='center', va='center',
            fontsize=68, fontweight='bold',
            color='white', zorder=10,
            family='sans-serif')
    
    ax.text(cx, cy - 1.5, "OVERVIEW",
            ha='center', va='center',
            fontsize=52, fontweight='normal',
            color='#ECEFF1', zorder=10,
            family='sans-serif')
    
    ax.text(cx, cy - 4.0, "",
            ha='center', va='center',
            fontsize=64, zorder=10)
    
    # DRAW TOPIC BOXES
    num_topics = len(content)
    
    # Box size settings
    if density == "Minimal":
        w, h = 16, 11
    else: # Moderate
        w, h = 18, 13

    # Calculate Positions
    positions = []
    
    if layout == "Radial":
        # Original Radial Layout
        for i in range(num_topics):
            angle = 2 * math.pi * i / num_topics - math.pi / 2
            distance = 22
            bx = cx + distance * math.cos(angle)
            by = cy + distance * math.sin(angle)
            positions.append((bx, by, angle))
            
    else: # Tree Structure (Left/Right)
        # Split topics: Left and Right
        left_count = math.ceil(num_topics / 2)
        right_count = num_topics - left_count
        
        # Vertical spacing
        y_gap = 16
        x_dist = 24
        
        # Right Side Loop
        for i in range(right_count):
            # Center the vertical stack relative to cy
            total_h = (right_count - 1) * y_gap
            start_y = cy + (total_h / 2)
            
            bx = cx + x_dist
            by = start_y - (i * y_gap)
            
            # Angle for connector (approx 0 for right)
            angle = 0
            positions.append((bx, by, angle))
            
        # Left Side Loop
        for i in range(left_count):
            total_h = (left_count - 1) * y_gap
            start_y = cy + (total_h / 2)
            
            bx = cx - x_dist
            by = start_y - (i * y_gap)
            
            # Angle for connector (approx pi for left)
            angle = math.pi
            positions.append((bx, by, angle))

    # Draw Elements
    for i, item in enumerate(content):
        color = colors[i % len(colors)]
        bx, by, angle_hint = positions[i]
        
        # Refine connector angle for Tree view
        # We calculate exact angle from center to box to make the curve smooth
        dx = bx - cx
        dy = by - cy
        exact_angle = math.atan2(dy, dx)
        
        # Draw the topic box
        draw_clean_box(ax, bx, by, w, h, item, color, i+1, density)
        
        # Draw connector
        draw_simple_connector(ax, cx, cy, center_r, bx, by, w, h, 
                             color['border'], exact_angle)
    
    plt.tight_layout(pad=2)
    return fig


def draw_clean_box(ax, cx, cy, w, h, content, color, number, density):
    """Draw a clean, readable content box"""
    
    # Shadow
    shadow_offset = 0.3
    ax.add_patch(FancyBboxPatch(
        (cx - w/2 + shadow_offset, cy - h/2 - shadow_offset),
        w, h,
        boxstyle="round,pad=0.4",
        facecolor='#000000',
        alpha=0.08,
        zorder=10
    ))
    
    # Main box
    ax.add_patch(FancyBboxPatch(
        (cx - w/2, cy - h/2),
        w, h,
        boxstyle="round,pad=0.4",
        facecolor=color['bg'],
        edgecolor=color['border'],
        linewidth=5,
        zorder=15
    ))
    
    # Number badge
    badge_r = 1.1
    badge_x = cx + w/2 - 1.8 
    badge_y = cy + h/2 - 1.8 
    
    ax.add_patch(Circle((badge_x, badge_y), badge_r,
                        facecolor=color['border'],
                        edgecolor='white',
                        linewidth=4,
                        zorder=20))
    
    ax.text(badge_x, badge_y, str(number),
            ha='center', va='center',
            fontsize=42, fontweight='bold',
            color='white', zorder=21)
    
    # Content Formatting
    left = cx - w/2 + 1.5
    top = cy + h/2 - 1.5
    current_y = top
    
    # Title
    title_text = "\n".join(textwrap.wrap(content['title'], width=15))
    ax.text(left, current_y, title_text,
            ha='left', va='top',
            fontsize=32, fontweight='bold',
            color=color['text'], zorder=20,
            family='sans-serif')
    
    title_lines = title_text.count('\n') + 1
    current_y -= (2.0 + (title_lines - 1) * 1.5)
    
    # Subtitle
    if 'subtitle' in content:
        sub_text = "\n".join(textwrap.wrap(content['subtitle'], width=35))
        ax.text(left, current_y, sub_text,
                ha='left', va='top',
                fontsize=18,
                color=color['text'],
                alpha=0.7,
                zorder=20,
                style='italic')
        sub_lines = sub_text.count('\n') + 1
        current_y -= (1.4 * sub_lines)
    
    # Points
    current_y -= 0.8
    wrap_width = 30 if density == "Minimal" else 35
    
    for point in content.get('points', []):
        wrapped_point = textwrap.fill(point, width=wrap_width)
        
        ax.add_patch(Circle((left + 0.35, current_y - 0.3), 0.25,
                            facecolor=color['border'],
                            zorder=20))
        
        ax.text(left + 1.0, current_y, wrapped_point,
                ha='left', va='top',
                fontsize=17,
                color='#37474F',
                zorder=20)
        
        lines = wrapped_point.count('\n') + 1
        drop = 1.2 + (lines - 1) * 0.8
        current_y -= drop


def draw_simple_connector(ax, cx, cy, cr, bx, by, w, h, color, angle):
    """Draw clean, simple connector lines"""
    
    # Start point (on circle edge)
    start_x = cx + (cr + 0.5) * math.cos(angle)
    start_y = cy + (cr + 0.5) * math.sin(angle)
    
    # End point (on box edge)
    dx = bx - cx
    dy = by - cy
    dist = math.sqrt(dx**2 + dy**2)
    
    # Adjust end point to stop at box edge
    end_x = bx - (w/2 + 0.5) * (dx/dist)
    end_y = by - (h/2 + 0.5) * (dy/dist)
    
    # Control point for curve
    mid_x = (start_x + end_x) / 2
    mid_y = (start_y + end_y) / 2
    
    # Curve amount depends on layout. 
    # For horizontal tree, we want curves that go up/down then horizontal
    ctrl_off = 4.0
    # Use perpendicular angle for curve control
    ctrl_x = mid_x + ctrl_off * math.cos(angle + math.pi/2)
    ctrl_y = mid_y + ctrl_off * math.sin(angle + math.pi/2)
    
    t = np.linspace(0, 1, 100)
    curve_x = (1-t)**2 * start_x + 2*(1-t)*t * ctrl_x + t**2 * end_x
    curve_y = (1-t)**2 * start_y + 2*(1-t)*t * ctrl_y + t**2 * end_y
    
    ax.plot(curve_x, curve_y,
            color=color,
            linewidth=6,
            alpha=0.6,
            zorder=8,
            solid_capstyle='round')
    
    ax.add_patch(Circle((start_x, start_y), 0.5,
                        facecolor=color,
                        edgecolor='white',
                        linewidth=3,
                        zorder=12))
    
    ax.add_patch(Circle((end_x, end_y), 0.5,
                        facecolor=color,
                        edgecolor='white',
                        linewidth=3,
                        zorder=12))

if __name__ == "__main__":
    show()