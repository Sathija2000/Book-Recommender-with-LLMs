#  Semantic Book Recommender with LLMs

This project is a **semantic book recommendation system** that uses **natural language processing (NLP)** to suggest books based on a user's input description. It also allows filtering by **category** and **emotional tone** such as joy, sadness, or suspense.

##  Features

-  Recommend books based on a description (e.g., "a story about forgiveness").
-  Filter recommendations by:
  - Book category (e.g., Fiction, Romance, Horror)
  - Emotional tone (e.g., Joy, Sadness, Surprise)
-  Uses **zero-shot classification** and **emotion detection** models.
-  Interactive UI built with **Gradio**.


##  Technologies Used

- **Python**
- **Transformers (Hugging Face)** – for emotion classification
- **Pandas, NumPy** – for data manipulation
- **Gradio** – to build the interactive UI
- **Models Used**:
     **facebook/bart-large-mnli** – for zero-shot classification of book categories.
     **j-hartmann/emotion-english-distilroberta-base** – for detecting emotional tone in book descriptions.


##  Dataset

- Contains metadata and descriptions of thousands of books.
- Some columns include: `isbn13`, `title`, `description`, `categories`, `thumbnail`, etc.
