# Document Intelligence Project

The purpose of building this project is to understand how documents
being processed in intelligent systems and how the processed information
being used to take business decisions. For the sake of learning, this
project will focus on a specific industry such as education. This
project will process documents that are given and answer questions
according to the information presented in the documents provided.

- Author: Poorna Rajapaksha

- Start Date: 22 September 2026

This document has been used to document the learning process and
experience.

---

At this moment, I don't understand how this whole system works. But I
have a general understanding of what should be happening in this system.

![](media/image1.png)

Therefore, according to the above illustrations I can identify 2
different processes such as,

1.  Document Processing Process

2.  User Interaction Process

These are **not** **independent processes**. They are processes that
happen one after another and have a strong dependency on each other to
function as a proper system. Because the document processing is useless
if there are no user interactions to answer questions. Also, the user
interaction process cannot be accurate if there are no accurate data
extractions from the given sources.

# Phase 1 - Understanding Documents

A pdf document can be categorized into 2 groups,

1.  **Text Documents** - Easy to process

2.  **Scanned Documents** - Now the computer sees the document as images.
    To process those documents, we need OCR (Optical Character
    Recognition).

![](media/image2.png)

But for the initial phase, this project will only focus on text documents.

Right now I have implement text based pdf text extractions. This also have proper exceptions without exposing low-level system exceptions. 

I have also implement a basic `CI` action in github to check weather all tests are being passed during commits and pull requests.

> Now we should think what should happen after text extraction before chunking and storing

![](media/image3.png)

We need to do this cleaning process just to remove and clean structural issues in a document. We should not do a hard cleaning process because that might destroy the useful context of the document.

Therefore, the system have a simple cleaning process which includes,
- Normalize line endings
- Remove leading/trailing whitespace from the entire text
- Remove leading/trailing whitespace from each line
- Normalize repeated spaces/tabs within each line
- Collapse 3+ consecutive newlines into 2

# Phase 2 - Chunking

> Chunking means breaking a large document into **smaller meaningful pieces of text**

Let's say we have a document, and we ask a specific question based on that document. The system should not send the entire document for the LLM as **context**. This will be fine if the document is small but for larger document it's not practical.

With chunking we brake large documents into meaningful groups. And when a question is asked, we retrieves only the required chunks and send them as the **context** for the LLM.

There are few different `chunking-strategies`:

![](media/image4.png)

The **agentic** and **semantic chunking** offers **better results** compared to rest of the chunking strategies. But between **agentic** and **semantic**, **agentic** provides better results.

But for this project we will use **semantic chunking** rather than **agentic chunking** in the V1. Because, with semantic chunking, I will get a better exposure on embeddings.

## Embeddings

> Embedding is a means of representing objects like text, images and audio as points in a continuous vector space.

Text can be converted to vectors using few different methods, 

![](media/image5.png)

Each of these methods converts text into vectors in different methods. But after we convert the sentences to vectors we should calculate and group the sentences based on the similarities. To calculate the similarities between sentences, we use `cosine similarity` method.

At the moment chunking works on page by page. Using `cosine similarity` method we collect relevant sentences together and create chunks from them. Since we are using page by page chunking, there will be some redundancy chunks. But at this phase they are ignored.

![](media/image6.png)

### Embedding Storage

Before going into vector databases, we should be able to convert text to vectors. Then we should test weather a **chunk** shows higher similarity score to a related question.

First we need the model class to store vector data. But we should't combined it with `chunk` model. Because there could be chunks that might not need this conversion.

![](media/image7.png)

### Vector Database

A vector database is a database designed to store and search vector embeddings efficiently.

A normal SQL database isn't designed to efficiently answer:

> "Find the vectors that are most semantically similar to this vector."

A vector database is.

A normal database might do:

```sql
SELECT * FROM students
WHERE attendance >= 80;
```

That's an exact/structured query.

A vector database does something more like:

![](media/image8.png)

It isn't necessarily looking for the same words.

It's looking for similar meaning.

## Retrieving Engine

Now we implement the system to convert user input into a vector and search and retrieve the similar chunks from the vector database.

Now we have to test our retrieval system. For that we can use few metrics,
1. Recall@k
2. MRR

### Recall@k

> `k` can mean a any numeric value. But what we looking from this test is, **did the correct chunk appear within the $k^{th}$ chunk**.

For example if we are looking for `Recall@1`, we are checking weather the correct chunk come back as the #1 result.

For our current version we got below results,

- Recall@1: 60.00%
- Recall@3: 100.00%
- Recall@5: 100.00%

This means our retrieval engine is good for a some extend but there is more room to improve.

### MRR

> MRR - Mean Reciprocal Rank
>
> This means "On average, how high was the first correct result".

The current stage of `MRR` value of **0.767** shows that **relevant results generally rank fairly high**.