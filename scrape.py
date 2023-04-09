from bs4 import BeautifulSoup
from requests import get
import csv
import sqlite3

# Popular languages for 2023 taken from: "https://www.simplilearn.com/best-programming-languages-start-learning-today-article"
languages = ["javascript", "python", "golang", "java", "kotlin", "php", "c#", "swift", "r", "ruby", "c", "c++", "matlab", "typescript", "scala", "sql", "html", "css", "mysql", "nosql", "rust", "perl"]

# Database filename
database = "jobs.db"


def main():

    # Creates blank jobs table in the database with headers based on the languages listed above
    initialise_database()

    # Prompts the user for an integer number of pages to scrape from reed
    number_of_pages = get_number_of_pages()

    # Generates a list of every job posting URL that is scraped
    job_urls = get_all_job_urls(number_of_pages)

    # Loops through each job posting and appends the job summary (title, location, languages etc) to a list
    # Writes each job posting summary to the database
    job_summary_list = []
    for job_url in job_urls:
        job_summary = get_job_summary(job_url)
        job_summary_list.append(job_summary)
        write_to_database(job_summary)

    # Also writes the summary data to csv
    write_to_csv(job_summary_list)
    
    # Prints the number of unique job postings found
    print("Number of job results: " + str(len(job_summary_list)))


# Function used to connect to database and initialise blank jobs table
# Clears jobs table of all data if it already exists
def initialise_database():

    db_connect = sqlite3.connect(database)
    db = db_connect.cursor()

    # Headers variable is used to create the table headings with their associated data types
    # Programming languages are numeric (0 if they do not exist in a job description, 1 if they do) and the remaining columns are text
    # The formatting of c# and c++ are changed for SQL compatibility
    headers = " NUMERIC NOT NULL DEFAULT 0, ".join(languages)
    headers += " NUMERIC NOT NULL DEFAULT 0, title TEXT, location TEXT, url TEXT"
    headers = headers.replace("c#", "c_sharp")
    headers = headers.replace("c++", "cpp")

    db.execute(f"CREATE TABLE IF NOT EXISTS jobs ({headers})")
    db.execute("DELETE FROM jobs;")

    # Commit changes and close database
    db_connect.commit()
    db.close()
    db_connect.close()


# Gets user input for number of pages to scrape
# Input must be positive integer
def get_number_of_pages():

    while(True):
        try:
            number_of_pages = int(input("How many pages do you want to scrape? "))
            if number_of_pages > 0:
                break
            else:
                print("Please enter a positive integer value...")
                continue
        except ValueError:
            print("Please enter a positive integer value...")
            continue
    
    return number_of_pages


# Function takes in an integer number of pages that the user wants to scrape and returns a list of every job url that is found
def get_all_job_urls(number_of_pages):

    job_urls = []

    for i in range(number_of_pages):
        # Get information from page and create BeautifulSoup object
        current_url = "https://www.reed.co.uk/jobs/software-engineer-jobs?pageno=" + str(i + 1)
        current_page = get(current_url)
        current_soup = BeautifulSoup(current_page.content, 'html.parser')

        # Create temporary list of job posting URLs for the current page and append to the list containing every job posting URL
        tmp_urls = get_page_urls(current_soup)
        job_urls.extend(tmp_urls)

    # Remove any duplicates
    unique_job_urls = [*set(job_urls)]

    return unique_job_urls


# Function takes in the current page's soup object as an argument and returns a list of all job posting URLs on the current page
def get_page_urls(current_soup):

    a_tags = current_soup.body.find_all('a', attrs={"class": "job-result-card__block-link"})

    job_urls=[]
    for tag in a_tags:
        job_urls.append(tag["href"])

    # Remove promoted jobs from list as these appear on every page
    del job_urls[0:2]

    return job_urls


# Function takes in a job posting URL as an argument and returns a dictionary containing a summary of the job title, location and languages used
def get_job_summary(url):

    # Get information from page and create BeautifulSoup object
    job_url = "https://www.reed.co.uk" + url
    page = get(job_url)
    soup = BeautifulSoup(page.content, 'html.parser')

    # Scrape job summary information from web page
    job_title = soup.body.find('h1').get_text()
    job_location = soup.body.find('span', attrs={"itemprop": "addressLocality"}).get_text()
    job_description = soup.body.find('span', attrs={"itemprop": "description"})
    

    # Search main body text and extract the programming languages
    description_text = text_splitter(job_description.get_text())
    main_body_languages = get_languages(description_text)

    # Search <li> list items and extract the programming languages
    description_list_items = job_description.find_all('li')

    list_languages = []
    for list_item in description_list_items:
        list_item_text = text_splitter(list_item.get_text())
        tmp_languages = get_languages(list_item_text)
        list_languages.extend(tmp_languages)
  
    # Combine the two lists and remove duplicate languages
    job_languages = main_body_languages + list_languages
    unique_languages = [*set(job_languages)]
    
    job_summary = job_to_dictionary(job_title, job_location, unique_languages, job_url)

    return job_summary


# Function takes in a list of strings and checks if any of the strings are programming languages, then returns any languages found
def get_languages(list_of_strings):

    tmp_languages = []

    for string in list_of_strings:
        if string in languages:
            tmp_languages.append(string)

    return tmp_languages


# Function takes in a body of text and splits all of the text into a list of individual words based on various separator parameters
def text_splitter(text):
    return text.lower().replace(",", " ").replace(".", " ").replace(":", " ").replace("(", " ").replace(")", " ").replace("/", " ").replace("*", " ").split()


# Function returns a dictionary summarising the job description
def job_to_dictionary(job_title, job_location, languages_list, job_url):

        # Initialises a dictionary containing all possible programming languages as keys with a starting value of 0
        summary = dict.fromkeys(languages, 0)

        for language in languages_list:
            summary[language] = 1

        # Replace c# with c_sharp, and c++ with cpp to ensure viable SQL header formatting
        summary["c_sharp"] = summary.pop("c#")
        summary["cpp"] = summary.pop("c++")

        # Append the job title, location and url
        summary["title"] = job_title
        summary["location"] = job_location
        summary["url"] = job_url

        return summary


# Function takes in a job posting as a dictionary and writes it to the database table
def write_to_database(job_summary):

    db_connect = sqlite3.connect(database)
    db = db_connect.cursor()
    
    # Prepares the query formatting
    columns = ", ".join(job_summary.keys())
    placeholders = ", ".join(["?"] * len(job_summary))
    query = f"INSERT INTO jobs ({columns}) VALUES ({placeholders})"

    db.execute(query, tuple(job_summary.values()))

    db_connect.commit()
    db.close()
    db_connect.close()


# Writes job summary list to CSV
def write_to_csv(job_summary_list):

    keys = job_summary_list[0].keys()
    file = open('jobs.csv', 'w', newline='')

    dict_writer = csv.DictWriter(file, keys)
    dict_writer.writeheader()
    dict_writer.writerows(job_summary_list)

    file.close()


if __name__=="__main__":
    main()