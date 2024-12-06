import streamlit as st
import random
import time
import requests
from bs4 import BeautifulSoup
import pandas as pd
import webbrowser


# Function to fetch job listings
def fetch_jobs(domain):
    """
    Fetch jobs from LinkedIn using retry logic and user-agent rotation to handle HTTP 429.
    """
    job_listings = []
    url = f"https://www.linkedin.com/jobs/search?keywords={domain}&location=Worldwide"
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36 Brave/96',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0'
    ]

    retries = 3
    for i in range(retries):
        headers = {'User-Agent': random.choice(user_agents)}
        response = requests.get(url, headers=headers)

        if response.status_code == 429:  # Too Many Requests
            wait_time = 2 ** i  # Exponential backoff
            st.warning(f"Rate limit exceeded. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
        elif response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            job_cards = soup.find_all('div', class_='base-card')

            for job in job_cards:
                try:
                    # Extract job details
                    title = job.find('h3', class_='base-search-card__title')
                    company = job.find('h4', class_='base-search-card__subtitle')
                    link = job.find('a', class_='base-card__full-link')

                    # Clean and validate the data
                    title = title.text.strip() if title else "No Title"
                    company = company.text.strip() if company else "No Company"
                    link = link['href'] if link else "#"

                    if title and company and link:
                        job_listings.append({"Title": title, "Company": company, "Link": link})
                except Exception as e:
                    st.warning(f"Error parsing a job entry: {e}")
            return pd.DataFrame(job_listings)
        else:
            st.error(f"Failed to fetch jobs. HTTP Status Code: {response.status_code}")
            break
    return pd.DataFrame(job_listings)


# Match jobs to skills
def match_jobs_to_profile(jobs, skills):
    """
    Match jobs to user profile based on skills.
    """
    jobs['Match Score'] = jobs['Title'].apply(
        lambda x: sum(skill.lower() in x.lower() for skill in skills.split(","))
    )
    matched_jobs = jobs.sort_values(by='Match Score', ascending=False).head(10)
    return matched_jobs


# Streamlit App
st.title("💼 LinkedIn Job Finder")
st.write("Discover your next opportunity with tailored job matches!")

# User Inputs
name = st.text_input("Enter your name:")
domain = st.text_input("Enter your domain (e.g., Data Science, Marketing):")
skills = st.text_input("Enter your skills (comma-separated):")
experience = st.number_input("Enter your work experience (in years):", min_value=0)

if st.button("Find Jobs"):
    if domain and skills:
        st.info(f"Searching for jobs in {domain} for {name}...")
        jobs = fetch_jobs(domain)

        if not jobs.empty:
            matched_jobs = match_jobs_to_profile(jobs, skills)
            st.success("Here are the top job matches for you:")

            job_links = []
            for idx, row in matched_jobs.iterrows():
                st.markdown(
                    f"""
                    <div class="job-card">
                        <h3>{row['Title']}</h3>
                        <p><strong>Company:</strong> {row['Company']}</p>
                        <p><a href="{row['Link']}" target="_blank" style="color: #00BFFF;">Apply Here</a></p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                job_links.append(row['Link'])

            # Apply at Once Button
            if st.button("Apply at Once"):
                for link in job_links:
                    webbrowser.open_new_tab(link)
        else:
            st.warning("No jobs found. Try a different domain or add more skills.")
    else:
        st.error("Please fill in all required fields.")
