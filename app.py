import io
import zipfile
import json
import pandas as pd
from pathlib import Path
import streamlit as st

from src.parser import parse_screenplay
from src.candidate_generator import generate_candidates


# -----------------------------------------
# PAGE CONFIGURATION
# -----------------------------------------

st.set_page_config(
    page_title="Kuku Promo Finder",
    page_icon="🎬",
    layout="wide"
)

OUTPUT_DIR = Path("data/outputs")

RANKED_PATH = OUTPUT_DIR / "ranked_promos.json"
SELECTED_PATH = OUTPUT_DIR / "selected_promos.json"


# -----------------------------------------
# LOAD DATA
# -----------------------------------------

def load_json(path):

    if not path.exists():
        return []

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


ranked_candidates = load_json(RANKED_PATH)
selected_candidates = load_json(SELECTED_PATH)


# -----------------------------------------
# HEADER
# -----------------------------------------

st.title("🎬 Kuku Promo Finder")

st.markdown(
    "### AI-powered Promotional Clip Discovery System"
)

st.caption(
    "Discover, evaluate, rank and select promotional "
    "clips from screenplay episodes."
)

st.divider()


# -----------------------------------------
# SIDEBAR
# -----------------------------------------

st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "Select a page",
    [
        "Dashboard",
        "Upload Episodes",
        "Selected Promos",
        "About Project"
    ]
)


# -----------------------------------------
# DASHBOARD
# -----------------------------------------

if page == "Dashboard":

    st.header("Project Dashboard")

    total_ranked = len(ranked_candidates)
    total_selected = len(selected_candidates)

    strong_count = sum(
        1 for c in ranked_candidates
        if c.get("recommendation") == "strong"
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Ranked Candidates",
        total_ranked
    )

    col2.metric(
        "Selected Promos",
        total_selected
    )

    col3.metric(
        "Strong Recommendations",
        strong_count
    )

    st.divider()

    st.subheader("Top 5 Promotional Clips")

    if ranked_candidates:

        top_candidates = ranked_candidates[:5]

        for candidate in top_candidates:

            with st.container(border=True):

                st.markdown(
                    f"### Rank {candidate.get('rank', '-')}: "
                    f"{candidate['candidate_id']}"
                )

                col1, col2, col3 = st.columns(3)

                col1.metric(
                    "Combined Score",
                    candidate.get("combined_score", 0)
                )

                col2.metric(
                    "AI Score",
                    candidate.get("ai_score", 0)
                )

                col3.metric(
                    "Recommendation",
                    candidate.get("recommendation", "N/A")
                )

                st.write(
                    f"Episode: {candidate['episode_number']}"
                )

                st.write(
                    f"Duration: {candidate['duration_seconds']} seconds"
                )

                st.write(
                    candidate.get(
                        "why_it_works",
                        "Explanation unavailable"
                    )
                )

    else:

        st.info(
            "No ranked candidates found. Run the ranking pipeline first."
        )


# -----------------------------------------
# RANKED CANDIDATES
# -----------------------------------------


# -----------------------------------------
# UPLOAD EPISODES
# -----------------------------------------


# -----------------------------------------
# UPLOAD AND ANALYZE EPISODES
# -----------------------------------------



elif page == "Upload Episodes":

    st.header("📂 Upload & Analyze Screenplay Episodes")

    st.write(
        "Upload TXT files, upload a ZIP archive, or paste screenplay text directly."
    )

    RAW_DIR = Path("data/raw")
    OUTPUT_DIR = Path("data/outputs")

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------
    # INPUT METHOD 1: Upload TXT or ZIP
    # --------------------------------------------------

    st.subheader("1. Upload Screenplay Files")

    uploaded_files = st.file_uploader(
        "Upload TXT files or a ZIP containing TXT files",
        type=["txt", "zip"],
        accept_multiple_files=True
    )

    # --------------------------------------------------
    # INPUT METHOD 2: Paste screenplay text
    # --------------------------------------------------

    st.subheader("2. Or Paste Screenplay Text")

    pasted_text = st.text_area(
        "Paste your screenplay here",
        height=250,
        placeholder="Paste the complete screenplay text here..."
    )

    pasted_filename = st.text_input(
        "Episode filename",
        value="pasted_episode.txt"
    )

    st.divider()

    # --------------------------------------------------
    # RUN ANALYSIS
    # --------------------------------------------------

    if st.button("🚀 Run Analysis", type="primary"):

        input_files = []

        # Collect uploaded TXT and ZIP files
        for uploaded_file in uploaded_files or []:

            if uploaded_file.name.lower().endswith(".txt"):

                input_files.append((
                    uploaded_file.name,
                    uploaded_file.getvalue()
                ))

            elif uploaded_file.name.lower().endswith(".zip"):

                try:
                    with zipfile.ZipFile(
                        io.BytesIO(uploaded_file.getvalue())
                    ) as archive:

                        for member in archive.infolist():

                            if (
                                not member.is_dir()
                                and member.filename.lower().endswith(".txt")
                            ):
                                # Read TXT directly from ZIP.
                                # Do not extract arbitrary archive paths.
                                content = archive.read(member)

                                filename = Path(member.filename).name

                                if filename:
                                    input_files.append((
                                        filename,
                                        content
                                    ))

                except zipfile.BadZipFile:
                    st.error(
                        f"{uploaded_file.name} is not a valid ZIP file."
                    )

        # Add pasted text
        if pasted_text.strip():

            filename = Path(pasted_filename).name

            if not filename.lower().endswith(".txt"):
                filename += ".txt"

            input_files.append((
                filename,
                pasted_text.encode("utf-8")
            ))

        if not input_files:
            st.warning("Please upload files or paste screenplay text.")

        else:

            all_candidates = []
            successful_files = 0
            failed_files = []

            progress_bar = st.progress(0)
            status_text = st.empty()

            for index, (filename, content) in enumerate(input_files):

                try:

                    status_text.write(
                        f"Processing {filename}..."
                    )

                    # Save with a unique filename to avoid overwriting
                    # another input file with the same name.
                    safe_name = Path(filename).name
                    file_path = RAW_DIR / f"run_{index + 1}_{safe_name}"

                    file_path.write_bytes(content)

                    # Step 1: Parse screenplay
                    episode = parse_screenplay(file_path)

                    # Step 2: Generate candidates
                    candidates = generate_candidates(episode)

                    all_candidates.extend(candidates)
                    successful_files += 1

                except Exception as e:

                    failed_files.append({
                        "file": filename,
                        "error": str(e)
                    })

                progress_bar.progress(
                    (index + 1) / len(input_files)
                )

            # Save results separately from the original candidate file
            output_file = OUTPUT_DIR / "selected_run_candidates.json"

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(
                    all_candidates,
                    f,
                    indent=4,
                    ensure_ascii=False
                )

            st.session_state["analysis_candidates"] = all_candidates

            progress_bar.empty()
            status_text.empty()

            # Results
            st.divider()
            st.subheader("📊 Analysis Summary")

            col1, col2, col3 = st.columns(3)

            col1.metric("Input Files", len(input_files))
            col2.metric("Successfully Processed", successful_files)
            col3.metric("Candidates Generated", len(all_candidates))

            if failed_files:

                st.error("Some files could not be processed.")

                for failure in failed_files:
                    st.write(
                        f"**{failure['file']}**: {failure['error']}"
                    )

            if all_candidates:

                st.success("Analysis completed successfully!")

                st.subheader("🎬 Generated Promo Candidates")

                results_df = pd.DataFrame(all_candidates)

                # Hide context_events from the Streamlit display only
                results_df = results_df.drop(columns=["context_events"],errors="ignore")

                st.dataframe(
                    results_df,
                    use_container_width=True
                )

                st.download_button(
                    "⬇️ Download Candidates JSON",
                    data=json.dumps(
                        all_candidates,
                        indent=4,
                        ensure_ascii=False
                    ),
                    file_name="promo_candidates.json",
                    mime="application/json"
                )

   




# -----------------------------------------
# SELECTED PROMOS
# -----------------------------------------

elif page == "Selected Promos":

    st.header("Selected Promotional Clips")

    if selected_candidates:

        for candidate in selected_candidates:

            with st.expander(
                f"Rank {candidate.get('selection_rank', '-')} - "
                f"{candidate['candidate_id']}"
            ):

                st.write(
                    f"Episode: {candidate['episode_number']}"
                )

                st.write(
                    f"Duration: {candidate['duration_seconds']} seconds"
                )

                st.write(
                    f"Combined Score: {candidate['combined_score']}"
                )

                st.write(
                    f"Recommendation: {candidate['recommendation']}"
                )

                st.write(
                    candidate.get("why_it_works", "")
                )

        selected_json = json.dumps(
            selected_candidates,
            indent=2,
            ensure_ascii=False
        )

        st.download_button(
            "Download Selected Promos JSON",
            selected_json,
            file_name="selected_promos.json",
            mime="application/json"
        )

    else:

        st.warning("No selected promos available.")


# -----------------------------------------
# ABOUT PROJECT
# -----------------------------------------

elif page == "About Project":

    st.header("About Kuku Promo Finder")

    st.write(
        """
        Kuku Promo Finder is an AI-powered system designed
        to identify promising promotional clips from
        screenplay episodes.

        ### Pipeline

        1. Screenplay Parsing
        2. Candidate Generation
        3. LLM-based Evaluation
        4. Candidate Ranking
        5. Promotional Report Generation
        6. Performance Validation
        """
    )

st.divider()

st.caption(
    "Kuku Promo Finder | AI-powered screenplay analysis"
)
