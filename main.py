import requests
from bs4 import BeautifulSoup
import pandas as pd
from lxml import etree
from time import sleep
import streamlit as st
import plotly.express as px

#PAGE LAYOUT AND SETUP

st.set_page_config(page_title="E-Shopping Dashboard", page_icon=":bar_chart:", layout="wide")
print('libraries imported')

st.title(":bar_chart: Products Dashboard")
st.write('We need your user-agent to scrape data, you can copy it from google after searching for \"my user agent\"')
user_agent = st.text_input('User agent : ')
items = []
joblist = []
headers = {
        'User-Agent': user_agent,
        'Accept-Language': 'en-US, en;q=0.5'}

website = st.selectbox(
"Website: ",
('amazon', 'ebay'))
nbp = st.selectbox(
"Number of pages: keep in mind, the more the pages, the more time it takes to load data",
(1,2,3,4,5,6,7))

sear = st.text_input('Your search: ')
# EXTRACTION

@st.cache
def convert_df(df):
     # IMPORTANT: Cache the conversion to prevent computation on every rerun
     return df.to_csv().encode('utf-8')


def extract_amazon(page, search):
    search = sear
    search = search.replace(" ", "+")
    base_url = 'https://www.amazon.com/s?k={0}'.format(search)
    print('Processing {0}...'.format(base_url + '&page={0}'.format(page)))
    response = requests.get(base_url + '&page={0}'.format(page), headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    return soup

def extract_ebay(page, search):
    search = sear
    search = search.replace(" ", "+")
    #headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36'}
    url = f'https://www.ebay.com/sch/i.html?_from=R40&_nkw={search}&_sacat=0&LH_TitleDesc=0&_pgn={page}'
    r = requests.get(url, headers)
    soup = BeautifulSoup(r.content, 'html.parser')
    print(url)
    return soup

# TRANSFORMATION

def transform_amazon(soup):
    results = soup.find_all('div', {'class': 's-result-item', 'data-component-type': 's-search-result'})

    for result in results:
        product_name = result.h2.text

        try:
            rating = result.find('i', {'class': 'a-icon'}).text
            rating = rating[0:2]
            try:
                rating = float(rating)
                rating = round(rating)
                rating = int(rating)
            except ValueError:
                rating = 0

            rating_count = result.find_all('span', {'aria-label': True})[1].text
            try:
                rating_count = float(rating_count)
                rating_count = round(rating_count)
                rating_count = int(rating_count)
            except ValueError:
                rating_count = 0
        except AttributeError:
            continue

        try:
            price1 = result.find('span', {'class': 'a-price-whole'}).text
            price2 = result.find('span', {'class': 'a-price-fraction'}).text
            price = price1 + price2
            price = price.replace(",", "")
            price = price.replace("$", "")
            price = float(price)
            product_url = 'https://amazon.com' + result.h2.a['href']
            # print(rating_count, product_url)
            items.append([product_name, rating, rating_count, price, product_url])
        except AttributeError:
            continue
    sleep(1.5)
    return


def transform_ebay(soup):
    doc = etree.HTML(str(soup))
    for i in range(0, 61):
        title = doc.xpath('//*[contains(concat( " ", @class, " " ), concat( " ", "s-item__title", " " ))]')[i].text
        price = doc.xpath('//*[contains(concat( " ", @class, " " ), concat( " ", "s-item__price", " " ))]')[i].text
        if title == 'Shop on eBay' and price == '$20.00':
            continue

        job = {
            'Title': title, 'Price': price}

        joblist.append(job)
    return

button = st.button('Search')

if website == "amazon" and button:
    st.write('Fetching the data...')
    for i in range(0, nbp):

        c = extract_amazon(i, sear)
        transform_amazon(c)
    df = pd.DataFrame(items, columns=['product', 'rating', 'rating count', 'price', 'product url'])
    desc = df.describe()
    left_column, right_column = st.columns(2)
    left_column.dataframe(df)
    right_column.dataframe(desc)
    fig = px.box(df, x=df['rating'], y='price', color=df['rating'],
                     labels=dict(x="Ratings by stars", y="Price $"))

    csv = convert_df(df)
    st.download_button(
        label="Download data as CSV",
        data=csv,
        file_name='data.csv',
        mime='text/csv',
    )
    left_column, right_column = st.columns(2)
    desc1 = desc[1:].reset_index()
    fig1 = px.bar(desc1, x='index', y='price')
    right_column.plotly_chart(fig1)
    left_column.plotly_chart(fig)

elif website == "ebay" and button:
    st.write('Fetching the data...')
    for i in range(0, nbp):
        c = extract_ebay(i, sear)
        transform_ebay(c)
    df = pd.DataFrame(joblist)
    df.Price = df['Price'].apply(lambda x: x.replace("$", ""))
    df.Price = df['Price'].apply(lambda x: x.replace(",", ""))
    df.Price = df['Price'].apply(lambda x: int(float(x)))
    desc = df.describe()
    left_column, right_column = st.columns(2)
    left_column.dataframe(df)
    right_column.dataframe(desc)
    csv = convert_df(df)

    st.download_button(
        label="Download data as CSV",
        data=csv,
        file_name='data.csv',
        mime='text/csv',
    )
    desc1 = desc[1:].reset_index()
    fig1 = px.bar(desc1, x='index', y='Price')
    st.plotly_chart(fig1)



