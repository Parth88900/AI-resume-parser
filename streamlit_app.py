import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from resume_parser import ResumeParser
import tempfile
import os
import base64

# Page configuration
st.set_page_config(
    page_title="AI Resume Parser",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
    }
    .skill-category {
        background-color: #f8f9fa;
        border-left: 4px solid #007bff;
        padding: 10px;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Header
    st.markdown('<h1 class="main-header">🤖 AI Resume Parser</h1>', unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.title("About")
    st.sidebar.info(
        "This AI-powered resume parser extracts key information from resumes including:\n"
        "- Contact Information\n- Skills\n- Education\n- Work Experience\n- Years of Experience"
    )
    
    st.sidebar.title("Instructions")
    st.sidebar.write("""
    1. Upload a resume file (PDF or DOCX)
    2. The parser will automatically extract information
    3. View results in organized sections
    4. Download the parsed data if needed
    """)
    
    # File upload
    uploaded_file = st.file_uploader(
        "📤 Upload Resume (PDF or DOCX)", 
        type=['pdf', 'docx'],
        help="Supported formats: PDF, DOCX"
    )
    
    if uploaded_file is not None:
        # Save uploaded file to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name
        
        # Initialize parser
                # Parse resume
        with st.spinner('🔍 Analyzing resume... This may take a few seconds.'):
            result = parser.parse_resume(tmp_file_path)
        
        # Clean up temporary file
        os.unlink(tmp_file_path)
        
        if not result.get('success', False):
            st.error(f"❌ {result.get('error', 'Unknown error occurred')}")
            st.info("💡 **Tips for better results:**\n- Use text-based PDFs (not scanned images)\n- Ensure the resume has sufficient text content\n- Try a different file format (DOCX often works better)")
            return
        
        if not result.get('success', False):
            st.error(f"❌ {result.get('error', 'Unknown error occurred')}")
            return
        
        # Display results
        st.success("✅ Resume parsed successfully!")
        
        # Create two columns for layout
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Personal Information
            st.subheader("👤 Personal Information")
            st.markdown(f"**Name:** {result['name']}")
            st.markdown(f"**Email:** {result['contact_info']['email']}")
            st.markdown(f"**Phone:** {result['contact_info']['phone']}")
            st.markdown(f"**LinkedIn:** {result['contact_info']['linkedin']}")
            
            # Experience
            st.subheader("💼 Work Experience")
            st.markdown(f"**Years of Experience:** {result['experience']['years']}")
            
            if result['experience']['companies']:
                st.write("**Companies/organizations found:**")
                for company in result['experience']['companies']:
                    st.write(f"- {company}")
            else:
                st.write("No companies found in resume")
        
        with col2:
            # Education
            st.subheader("🎓 Education")
            if result['education']:
                for i, edu in enumerate(result['education'][:3], 1):
                    st.write(f"{i}. {edu}")
            else:
                st.write("No education information found")
            
            # Document Info
            st.subheader("📊 Document Analysis")
            st.metric("Text Length", f"{result['text_length']} characters")
        
        # Skills Section
        st.subheader("🛠️ Skills Analysis")
        
        if result['skills']:
            # Create skills visualization
            skill_categories = list(result['skills'].keys())
            skill_counts = [len(skills) for skills in result['skills'].values()]
            
            # Skills bar chart
            fig = px.bar(
                x=skill_counts,
                y=skill_categories,
                orientation='h',
                title="Skills by Category",
                labels={'x': 'Number of Skills', 'y': 'Category'}
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Display skills by category
            for category, skills in result['skills'].items():
                with st.expander(f"📁 {category.replace('_', ' ').title()} ({len(skills)} skills)"):
                    cols = st.columns(3)
                    for i, skill in enumerate(skills):
                        cols[i % 3].markdown(f"- {skill}")
        else:
            st.warning("No skills detected in the resume")
        
        # Raw text preview (collapsible)
        with st.expander("📝 View Extracted Text Preview"):
            st.text_area("", result.get('raw_text', 'No text extracted')[:2000] + "...", height=200)
        
        # Download results
        st.subheader("📥 Export Results")
        
        # Convert results to DataFrame for download
        if result['skills']:
            skills_data = []
            for category, skills in result['skills'].items():
                for skill in skills:
                    skills_data.append({'Category': category, 'Skill': skill})
            
            skills_df = pd.DataFrame(skills_data)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Download as CSV
                csv = skills_df.to_csv(index=False)
                st.download_button(
                    label="📊 Download Skills as CSV",
                    data=csv,
                    file_name="resume_skills.csv",
                    mime="text/csv"
                )
            
            with col2:
                # Summary report
                summary = f"""
                RESUME ANALYSIS REPORT
                =====================
                Name: {result['name']}
                Email: {result['contact_info']['email']}
                Phone: {result['contact_info']['phone']}
                Experience: {result['experience']['years']}
                
                SKILLS SUMMARY:
                """
                for category, skills in result['skills'].items():
                    summary += f"\n{category.upper()}:\n"
                    for skill in skills:
                        summary += f"  - {skill}\n"
                
                st.download_button(
                    label="📄 Download Summary Report",
                    data=summary,
                    file_name="resume_summary.txt",
                    mime="text/plain"
                )
        
        # Batch processing section
        st.sidebar.markdown("---")
        st.sidebar.subheader("Batch Processing")
        st.sidebar.warning("Coming soon: Batch processing multiple resumes")
    
    else:
        # Show demo when no file is uploaded
        st.info("👆 Please upload a resume file to get started")
        
        # Demo section
        st.markdown("---")
        st.subheader("🎯 What this parser extracts:")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            **👤 Personal Info**
            - Name
            - Email
            - Phone
            - LinkedIn
            """)
        
        with col2:
            st.markdown("""
            **🛠️ Skills**
            - Programming Languages
            - Frameworks
            - Tools & Technologies
            - Soft Skills
            """)
        
        with col3:
            st.markdown("""
            **🎓 Education**
            - Degrees
            - Universities
            - Certifications
            - Courses
            """)
        
        with col4:
            st.markdown("""
            **💼 Experience**
            - Years of Experience
            - Companies
            - Positions
            - Achievements
            """)

if __name__ == "__main__":
    main()
