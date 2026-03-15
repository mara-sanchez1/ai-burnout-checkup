# AI Usage & Burnout Checkup (Streamlit)

This project is a simplified Streamlit implementation of the **AI Usage & Burnout Checkup dashboard** originally developed as part of a group project.

The dashboard allows users to explore how **AI usage, workload, and job characteristics relate to employee burnout and productivity**.

## Live Application

You can access the deployed dashboard here:

https://mara-sanchez1-ai-burnout-checkup.share.connect.posit.cloud 

---

## Dashboard Features

The dashboard includes:

- **Interactive filters**
  - Job role
  - AI usage band
  - Experience (years)
  - Weekly AI usage
  - Manual work hours
  - Tasks automated (%)
  - Deadline pressure

- **Key metrics**
  - Median burnout risk
  - High burnout percentage
  - Median productivity
  - Median work-life balance

- **Visualizations**
  - AI usage vs burnout scatterplot
  - Burnout risk by job role
  - Weekly work hours breakdown

- **Filtered data preview**
  - Table view of filtered data
  - CSV download option

## Installation

Clone the repository with the following command:

```bash
git clone https://github.com/mara-sanchez1/ai-burnout-checkup.git
```

You can install the dependencies using either **pip** or **conda**.

### Option 1 — pip

```bash
pip install -r requirements.txt
```

### Option 2 - conda

```bash
conda env create -f environment.yml
conda activate burnout_streamlit 
```

## Running the Application

To start the Streamlit dashboard locally:

```bash
streamlit run app_streamlit.py
```

The application will open in your browser at: `http://localhost:8501`