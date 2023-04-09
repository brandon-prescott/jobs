# Jobs

This program is a web scraper that is able to extract summary information from software related job postings, such as the job title, location and programming languages required. This program could also be generalised to search for any key words in other types of job postings.

The scrape.py file starts by asking the user how many pages it wants them to scrape (it takes ~ 10 seconds per page). It then starts looping through all of the job posting URLs and uses BeautifulSoup to extract information from each page. Once it has extracted the text from the job posting in a form that is usable, it checks each string against a global languages array that contains a list of all the programming languages to check for (web frameworks were not added to this list, as I wanted to keep it specific to core programming languages and database tools).

It then produces a dictionary summary for each job posting, containing: Job title, location, programming languages and the URL. The programming language data is stored as a 0 or 1 depending on whether the language exists in the posting or not. The data is then written to both an SQL database and CSV file, depending on how someone might want to use the data for post-processing i.e. producing summary graphs in Excel or embedding the results in a web application using SQL. The steps below assume you are running the program on Linux.

**Build**

Ensure Python 3 is installed on your system, along with the following libraries (use pip install):

* bs4
* requests

Ensure SQLite3 is installed on your system by running
```shell
$ sudo apt install sqlite3
```

**Usage**
```shell
$ python3 scrape.py
```
The summary data can be viewed in the output CSV file or in the database by running
```shell
$ sqlite3 jobs.db
```
