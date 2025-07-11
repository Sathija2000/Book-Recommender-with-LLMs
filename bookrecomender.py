# -*- coding: utf-8 -*-
"""BookRecomender.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1KB_1ot6wzfQbryke8I89ZYKffwseHQB_
"""

try:
  import kagglehub
except ImportError:
  !pip install kagglehub
  import kagglehub

try:
  import pandas as pd
except ImportError:
  !pip install pandas
  import pandas as pd

try:
  import matplotlib.pyplot as plt
except ImportError:
  !pip install matplotlib
  import matplotlib.pyplot as plt

try:
  import seaborn as sns
except ImportError:
  !pip install seaborn
  import seaborn as sns

try:
  from dotenv import load_dotenv
except ImportError:
  !pip install python-dotenv
  from dotenv import load_dotenv

try:
  from langchain_community.llms import Ollama
except ImportError:
  !pip install langchain-community
  from langchain_community.llms import Ollama

try:
  from langchain_community.document_loaders import WebBaseLoader
except ImportError:
  !pip install langchain-community
  from langchain_community.document_loaders import WebBaseLoader

try:
  from langchain_community.embeddings import OllamaEmbeddings
except ImportError:
  !pip install langchain-community
  from langchain_community.embeddings import OllamaEmbeddings


try:
  from langchain_chroma import Chroma
except ImportError:
  !pip install langchain-chroma
  from langchain_chroma import Chroma

try:
  from langchain_openai import OpenAIEmbeddings
except ImportError:
  !pip install langchain-openai
  from langchain_openai import OpenAIEmbeddings

try:
  from transformers import AutoTokenizer, AutoModelForCausalLM
except ImportError:
  !pip install transformers
  from transformers import AutoTokenizer, AutoModelForCausalLM

try:
  import gradio as gr
except ImportError:
  !pip install gradio
  import gradio as gr

print("Packages installed/imported successfully.")

import kagglehub

# Download latest version
path = kagglehub.dataset_download("dylanjcastillo/7k-books-with-metadata")

print("Path to dataset files:", path)

ls root/.cache/kagglehub/datasets/dylanjcastillo/7k-books-with-metadata/versions/3

books = pd.read_csv(f"{path}/books.csv")

books.head()

books.describe()
# books.describe(include='all')

books.info()

# Function to display detailed column information including missing values
def display_column_details(df):
    print("Column Details:")
    print(df.info())
    print("\nMissing Values:")
    print(df.isnull().sum())
    print("\nUnique Values:")
    for col in df.columns:
        print(f"{col}: {df[col].nunique()} unique values")

display_column_details(books)

# books['categories'].unique()
books['categories'].nunique()    # Count of unique values for one column

"""Need to find if there is any pattern in the missing values."""

ax = plt.axes()
sns.heatmap(books.isna().transpose(), cbar=False, ax=ax)

plt.xlabel("Columns")
plt.ylabel("Missing Values")
plt.title("Missing Values Heatmap")
plt.show()

"""That average rating, num pages, rating count are show soma pattern. may be that data from the another dataset. (need to find have any biases here)


"""

import numpy as np

books['missing_description'] = np.where(books['description'].isna(), 1, 0)
books['age_of_book'] = 2025-books['published_year']

columns_of_interest = ['num_pages', 'average_rating', 'ratings_count', 'missing_description']

correlation_heatmap = books[columns_of_interest].corr(method='spearman')        # mostly continous values -> pearson and non-continous values -> spearman

sns.set_theme(style='white')
plt.figure(figsize=(8, 6))
sns.heatmap(correlation_heatmap, annot=True, fmt='.2f', cmap='coolwarm', linewidths=0.5)
plt.title('Correlation Heatmap')
plt.show()

"""Consider with the missing description these are not very strong correlations. (Strong correlation -->> 1 or -1 )"""

# Looks how many missing values have the book details and if there not have over 5% then better to delete.
books[(books['description'].isna()) |
      (books['num_pages'].isna()) |
      (books['average_rating'].isna()) |
      (books['published_year'].isna())
      ]

# Create new dataset
books_missing =  books[~(books['description'].isna()) &
      ~(books['num_pages'].isna()) &
      ~(books['average_rating'].isna()) &
      ~(books['published_year'].isna())
      ]

books_missing

books_missing['categories'].value_counts().reset_index().sort_values('count', ascending=False)

# books_missing['words_in_description'] = books_missing['description'].str.split().str.len()
books_missing.loc[:, 'words_in_description'] = books_missing['description'].str.split().str.len()

books_missing

books_missing.loc[books_missing['words_in_description'].between(1,4),'description']

books_missing.loc[books_missing['words_in_description'].between(5,15),'description']

"""Below 25 words descriptions does not give very good idea about that movies. So better to use above 25 words descriptions (Remove that below descriptions).


"""

books_missing.loc[books_missing['words_in_description'].between(25,35),'description']

books_missing_25_words = books_missing.loc[books_missing['words_in_description'] >= 25]

books_missing_25_words

books_missing_25_words['title_and_subtitle'] = (
    np.where(books_missing_25_words['subtitle'].isna(), books_missing_25_words['title'],
             books_missing_25_words[['title', 'subtitle']].astype(str).agg(': '.join, axis=1))
)

books_missing_25_words

books_missing_25_words['tagged_description'] = books_missing_25_words[['isbn13', 'description']].astype(str).agg(' '.join, axis=1)

books_missing_25_words

# prompt: drop the subtitle, missing_description, age_of_book and words_in_description. and save new dataset to the books_cleaned.csv file

books_cleaned = books_missing_25_words.drop(columns=['subtitle', 'missing_description', 'age_of_book', 'words_in_description'], axis=1)
books_cleaned.to_csv('books_cleaned.csv', index=False)

from langchain_community.document_loaders import TextLoader    # Load raw document
from langchain_text_splitters import CharacterTextSplitter     # Split into small chunks
from langchain_openai import OpenAIEmbeddings                  # Convert chunks into vectors
from langchain_chroma import Chroma                            # Store and retrieve vectors for user queries

from dotenv import load_dotenv

load_dotenv()

books = pd.read_csv('books_cleaned.csv')

books

books['tagged_description']

books['tagged_description'].to_csv('tagged_description.txt',
                                   sep= '\n',
                                   index= False,
                                   header= False)

raw_document = TextLoader('tagged_description.txt').load()
text_splitter = CharacterTextSplitter(chunk_size=0, chunk_overlap=0, separator='\n')
documents = text_splitter.split_documents(raw_document)

documents[0]

from langchain.embeddings import HuggingFaceEmbeddings
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

db_books = Chroma.from_documents(documents, embedding=embeddings)

query = 'A book to teach children about nature'
docs = db_books.similarity_search(query, k=10)     # This searches for the top k most similar documents (books) in the database
docs

books[books['isbn13'] == int(docs[0].page_content.split()[0].strip())]

"""1. docs[0] → Gets the top matching book from your search.

2. docs[0].page_content → Gets the text of that book (e.g., "9780140328721 The Wind in the Willows...").

3. .split()[0] → Picks the first word, which is the ISBN13 number.

4. int(...) → Converts that ISBN from text to number.

5. books[books['isbn13'] == ...] → Looks inside your original books data to find the row with that ISBN13.
"""

def retrieve_semantic_recommendations(
    query: str,
    top_k: int = 10,
) -> pd.DataFrame:
  recs = db_books.similarity_search(query, k=50)

  books_list = []

  for i in range(0, len(recs)):
    books_list += [int(recs[i].page_content.strip('"').split()[0])]

  return books[books['isbn13'].isin(books_list)].head(top_k)

retrieve_semantic_recommendations('A book to teach children about nature')

"""**Text Classification**

In this project use the zero shot for the Text Classifications.
"""

books['categories'].value_counts().reset_index()

books['categories'].value_counts().reset_index().query('count > 50')

books[books['categories'] == 'Juvenile Fiction']

category_mapping = {'Fiction' : "Fiction",
                    'Juvenile Fiction' : "Children's Fiction",
                    'Biography & Autobiography' : "Nonfiction",
                    'History' : "Nonfiction",
                    'Literary Criticism' : "Nonfiction",
                    'Philosophy' : "Nonfiction",
                    'Religion' : 'Nonfiction',
                    'Comics & Graphic Novels' : "Fiction",
                    'Drama' : "Fiction",
                    'Juvenile Nonfiction' : "Children's Nonfiction",
                    'Science' : "Nonfiction",
                    'Poetry' : "Fiction"}

books["simple_categories"] = books["categories"].map(category_mapping)

books

books[~(books["simple_categories"].isna())]

from transformers import pipeline

# Load the zero-shot classification pipeline
pipe = pipeline("zero-shot-classification",
                model="facebook/bart-large-mnli")

books.loc[books['simple_categories'] == "Fiction", "description"].reset_index(drop=True)[1]    # [1] give the second result

sequence = books.loc[books['simple_categories'] == "Fiction", "description"].reset_index(drop=True)[0]

fiction_categories = ['Fiction', 'Nonfiction', 'Children\'s Fiction', 'Children\'s Nonfiction']

pipe(sequence, fiction_categories)

fiction_categories = ['Fiction', 'Nonfiction']

pipe(sequence, fiction_categories)

max_index = np.argmax(pipe(sequence, fiction_categories)['scores'])       # gives the index of the highest score
                                                                          # 'scores': a list of probabilities for each label.
                                                                          # 'labels': the list of labels (like "Fantasy", "Mystery" etc.).
max_label = pipe(sequence, fiction_categories)['labels'][max_index]
max_label

def generate_predictions(sequence, categories):
  predictions = pipe(sequence, categories)
  max_index = np.argmax(predictions['scores'])
  max_label = predictions['labels'][max_index]
  return max_label

"""Purpose of this code:
1. Running zero-shot classification on 300 fiction book descriptions.
2. Saving the model’s predicted categories.
3. Saving the actual category ("Fiction") for each.

This setup is commonly used to later evaluate the model using metrics like accuracy, confusion matrix, etc.


"""

# This code is performing batch prediction using your zero-shot classification model on book descriptions
from tqdm import tqdm

actual_cats = []
predicted_cats = []

for i in tqdm(range(0, 300)):
  sequence = books.loc[books['simple_categories'] == "Fiction", "description"].reset_index(drop=True)[i]
  predicted_cats += [generate_predictions(sequence, fiction_categories)]            # Calls your prediction function generate_predictions(...).  Appends the result to the predicted_cats list.
  actual_cats += ['Fiction']          # Keeps track of the true label ("Fiction") for later comparison (like accuracy).

for i in tqdm(range(0, 300)):
  sequence = books.loc[books['simple_categories'] == "Nonfiction", "description"].reset_index(drop=True)[i]
  predicted_cats += [generate_predictions(sequence, fiction_categories)]
  actual_cats += ['Nonfiction']

predictions_df = pd.DataFrame({'actual_category': actual_cats, 'predicted_category': predicted_cats})

predictions_df

predictions_df['correct_prediction'] = (
    np.where(predictions_df['actual_category'] == predictions_df['predicted_category'], 1, 0)
)

predictions_df['correct_prediction'].sum() / len(predictions_df)

isbns = []
predicted_cats = []

missing_cats = books.loc[books['simple_categories'].isna(), ['isbn13', 'description']].reset_index(drop=True)

for i in tqdm(range(0, len(missing_cats))):
  sequence = missing_cats['description'][i]
  predicted_cats += [generate_predictions(sequence, fiction_categories)]
  isbns += [missing_cats['isbn13'][i]]

missing_predicted_df = pd.DataFrame({'isbn13': isbns, 'predicted_category': predicted_cats})

missing_predicted_df

# Joins two DataFrames: books and missing_predicted_df using the common column isbn13.
# This adds the 'predicted_category' column from missing_predicted_df to the books DataFrame.
books = pd.merge(books, missing_predicted_df, on='isbn13', how='left')

# If simple_categories is missing (NaN) for a book, replace it with the predicted category
# from the newly added 'predicted_category' column.
# If not missing, keep the original simple_categories.
books['simple_categories'] = np.where(books['simple_categories'].isna(), books['predicted_category'], books['simple_categories'])

# remove the predicted_category column (no longer needed) after using it.
books = books.drop('predicted_category', axis=1) # Ensure axis=1 for dropping a column

books = books.drop(columns=['predicted_category_x', 'predicted_category_y'])

books

# isin -> Checks if the lowercase category value exists in the list of genres provided.
books[books['categories'].str.lower().isin([
    'romance',
    'science fiction',
    'scifi',
    'fantasy',
    'horror',
    'mystery',
    'thriller',
    'comedy',
    'crime',
    'historical'
])]

books.to_csv('books_with_categories.csv', index=False)

"""**Sentiment Analysis**"""

books = pd.read_csv('books_with_categories.csv')

from transformers import pipeline
classifier = pipeline("text-classification",
                      model="j-hartmann/emotion-english-distilroberta-base",
                      top_k=None)
classifier("I love this!")

books['description'][0]

classifier(books['description'][0])

classifier(books['description'][0].split('.'))

sentences = books['description'][0].split('.')
predictions = classifier(sentences)

sentences[0]

predictions[0]

sentences[3]

predictions[3]

sorted_predictions = sorted(predictions[0], key=lambda x: x['label'])   # Sorts that list from highest to lowest score (i.e., most confident label first).
sorted_predictions

predictions

emotion_labels = ["anger", "disgust", "fear", "joy", "sadness", "surprise", "neutral"]
isbn = []
emotion_scores = {label: [] for label in emotion_labels}      #  A dictionary like Used to collect scores of each emotion from all predictions.

def calculate_max_emotion_scores(predictions):
    per_emotion_scores = {label: [] for label in emotion_labels}
    for prediction in predictions:
        sorted_predictions = sorted(prediction, key=lambda x: x["label"])   # For each prediction result, it sorts the emotions by score (from lowest to highest).
        for index, label in enumerate(emotion_labels):
            per_emotion_scores[label].append(sorted_predictions[index]["score"])      # It adds the score for each emotion into the respective list in emotion_scores.
    return {label: max(scores) for label, scores in per_emotion_scores.items()}     # picks the highest score seen across all predictions.

# To analyze the first 10 book descriptions, predict the emotions sentence by sentence,
# and then save the maximum emotion score for each emotion per book.
import numpy as np

for i in range(10):
    isbn.append(books["isbn13"][i])
    sentences = books["description"][i].split(".")
    predictions = classifier(sentences)
    max_scores = calculate_max_emotion_scores(predictions)
    for label in emotion_labels:
        emotion_scores[label].append(max_scores[label])   # For each emotion, append the max score for this book to the main emotion_scores dictionary.

emotion_scores

from tqdm import tqdm

emotion_labels = ['sadness', 'joy', 'disgust', 'anger', 'fear', 'surprise', 'neutral']
isbn = []
emotion_scores = {label: [] for label in emotion_labels}

for i in tqdm(range(len(books))):
    isbn.append(books["isbn13"][i])
    sentences = books["description"][i].split(".")
    predictions = classifier(sentences)
    max_scores = calculate_max_emotion_scores(predictions)
    for label in emotion_labels:
        emotion_scores[label].append(max_scores[label])

emotions_df = pd.DataFrame(emotion_scores)
emotions_df["isbn13"] = isbn

emotions_df

books = pd.merge(books, emotions_df, on='isbn13')

books

books.to_csv('books_with_emotions.csv', index=False)



"""**Gradio Dashboard**"""

import pandas as pd
import numpy as np
from dotenv import load_dotenv

from langchain_community.document_loaders import TextLoader
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter
from langchain_chroma import Chroma

import gradio as gr

books = pd.read_csv("books_with_emotions.csv")
# This creates a new column called large_thumbnail.
# It takes the existing thumbnail URL (image link) and adds &fife=w800 to the end.
# This extra part likely tells the server to return a larger-sized image (width 800px).
books["large_thumbnail"] = books["thumbnail"] + "&fife=w800"
books["large_thumbnail"] = np.where(
    books["large_thumbnail"].isna(),
    "cover_not_found.jpg",
    books["large_thumbnail"],
)

raw_document = TextLoader('tagged_description.txt').load()
text_splitter = CharacterTextSplitter(chunk_size=0, chunk_overlap=0, separator='\n')
documents = text_splitter.split_documents(raw_document)

from langchain.embeddings import HuggingFaceEmbeddings
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

db_books = Chroma.from_documents(documents, embedding=embeddings)

def retrieve_semantic_recommendations(
        query: str,                 # What the user is searching for (e.g., "adventure in space")
        category: str = None,       # Category filter (optional)
        tone: str = None,           # Emotion filter (optional)
        initial_top_k: int = 50,    # First select top 50 similar books
        final_top_k: int = 16,      # Then return final top 16 results
) -> pd.DataFrame:

    recs = db_books.similarity_search(query, k=initial_top_k)     # finds books whose descriptions are similar in meaning to the query.
    books_list = [int(rec.page_content.strip('"').split()[0]) for rec in recs]    # From each result in recs, it extracts the isbn13 (book ID).
    book_recs = books[books["isbn13"].isin(books_list)].head(initial_top_k)   # This filters the books dataset to keep only the books from the search results.

    if category != "All":
        book_recs = book_recs[book_recs["simple_categories"] == category].head(final_top_k)
    else:
        book_recs = book_recs.head(final_top_k)

    if tone == "Happy":
        book_recs.sort_values(by="joy", ascending=False, inplace=True)
    elif tone == "Surprising":
        book_recs.sort_values(by="surprise", ascending=False, inplace=True)
    elif tone == "Angry":
        book_recs.sort_values(by="anger", ascending=False, inplace=True)
    elif tone == "Suspenseful":
        book_recs.sort_values(by="fear", ascending=False, inplace=True)
    elif tone == "Sad":
        book_recs.sort_values(by="sadness", ascending=False, inplace=True)

    return book_recs

def recommend_books(
        query: str,
        category: str,
        tone: str
):
    recommendations = retrieve_semantic_recommendations(query, category, tone)
    results = []

    for _, row in recommendations.iterrows():
        description = row["description"]
        truncated_desc_split = description.split()
        truncated_description = " ".join(truncated_desc_split[:30]) + "..."

        authors_split = row["authors"].split(";")
        if len(authors_split) == 2:
            authors_str = f"{authors_split[0]} and {authors_split[1]}"
        elif len(authors_split) > 2:
            authors_str = f"{', '.join(authors_split[:-1])}, and {authors_split[-1]}"
        else:
            authors_str = row["authors"]

        caption = f"{row['title']} by {authors_str}: {truncated_description}"
        results.append((row["large_thumbnail"], caption))
    return results

# You get a list of unique categories from your books DataFrame.
# Add "All" at the top so the user can skip filtering.
# You also create a fixed list of emotional tones with "All".
categories = ["All"] + sorted(books["simple_categories"].unique())
tones = ["All"] + ["Happy", "Surprising", "Angry", "Suspenseful", "Sad"]

with gr.Blocks(theme=gr.themes.Glass()) as dashboard:
    gr.Markdown("# 📚 Semantic Book Recommender")

    with gr.Accordion("🔧 Advanced Search Options", open=True):
        user_query = gr.Textbox(label="Book Description")
        category_dropdown = gr.Dropdown(choices=categories, label="Category", value="All")
        tone_dropdown = gr.Dropdown(choices=tones, label="Tone", value="All")
        submit_button = gr.Button("Get Recommendations")

    gr.Markdown("## 🎯 Results")
    output = gr.Gallery(label="", columns=6, rows=3)

    submit_button.click(fn=recommend_books,
                        inputs=[user_query, category_dropdown, tone_dropdown],
                        outputs=output)

if __name__ == "__main__":
    dashboard.launch()

